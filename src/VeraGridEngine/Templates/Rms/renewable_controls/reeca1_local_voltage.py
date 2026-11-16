# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 local voltage mode for PFFLAG=0, VFLAG=0, QFLAG=1."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_coordinated_qv import add_reeca1_voltage_pi
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class Reeca1LocalVoltageSettings:
    """Store the local voltage PI gains and source Vbias."""

    __slots__ = ('kvp', 'kvi', 'vbias', 'tiq')

    def __init__(self, kvp: float = 1., kvi: float = 1., vbias: float = 0.,
                 tiq: float = .02) -> None:
        """Store the voltage-control parameters.

        :param kvp: Voltage proportional gain.
        :param kvi: Voltage integral gain.
        :param vbias: Additive source voltage-reference bias in per unit.
        :param tiq: Source reactive-current command lag time in seconds.
        :return: None.
        """
        self.kvp: float = kvp
        self.kvi: float = kvi
        self.vbias: float = vbias
        self.tiq: float = tiq


def build_reeca1_local_voltage_template(
        vf: VarFactory,
        name: str = 'REECA1 local voltage',
        settings: Reeca1LocalVoltageSettings | None = None,
) -> RmsModelTemplate:
    """Build QFLAG=1, VFLAG=0 voltage PI after reference-plus-bias selection.

    The connected host must initialize the reference so its sum with Vbias
    equals the solved measured voltage. Current capability and source fault
    flag remain live external inputs, and the source TIQ lag follows the PI.

    :param vf: Shared symbolic variable factory.
    :param name: Unique controller instance name.
    :param settings: Voltage PI gains, source bias and TIQ lag.
    :return: Controller with reference, voltage, fault and capability inputs.
    :raises ValueError: Nonfinite or negative-gain settings.
    """
    selected: Reeca1LocalVoltageSettings = Reeca1LocalVoltageSettings() if settings is None else settings
    if not all(math.isfinite(value) for value in (selected.kvp, selected.kvi, selected.vbias, selected.tiq)):
        raise ValueError('REECA1 local-voltage settings must be finite')
    elif selected.kvp < 0 or selected.kvi < 0 or selected.tiq < 0:
        raise ValueError('REECA1 local-voltage gains and Tiq must be nonnegative')
    else:
        pass
    control: ControlRealization = ControlRealization(vf, name)
    reference: Var = control.input('VoltageReferencePu', Const(1.))
    filtered_voltage: Var = control.input('FilteredVoltagePu', Const(1.))
    fault_flag: Var = control.input('VoltageDipFlag', Const(0.))
    iq_capability: Var = control.input('ReactiveCapabilityPu', Const(1.))
    vbias: Var = control.parameter('VBIAS', selected.vbias)
    kvp: Var = control.parameter('KVP', selected.kvp)
    kvi: Var = control.parameter('KVI', selected.kvi)
    iq_regulator: Var = add_reeca1_voltage_pi(
        control, reference + vbias, filtered_voltage, fault_flag,
        iq_capability, kvp, kvi, Const(0.),
    )
    tiq: Var = control.parameter('TIQ', selected.tiq)
    iq_command: Var = control.lag('ReactiveCurrentCommandPu', iq_regulator, tiq,
                                  selected.tiq, Const(0.))
    return control.finish((iq_command,), 'REECA1 local terminal-voltage PI regulator')
