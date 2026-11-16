# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 voltage-fault current injection with recovery hold."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import PickupDropoffLogic
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Reeca1VoltageSupportSettings:
    """Store REECA1 voltage-fault injection thresholds and capabilities."""

    __slots__ = ('vdip', 'vup', 'dbd1', 'dbd2', 'kqv', 'iql1', 'iqh1',
                 'vref0', 'iqfrz', 'thld')

    def __init__(self, vdip: float = .9, vup: float = 1.1,
                 dbd1: float = 0., dbd2: float = 0., kqv: float = 0.,
                 iql1: float = -1., iqh1: float = 1., vref0: float = 0.,
                 iqfrz: float = 0., thld: float = 0.) -> None:
        """Store immediate and positive-hold voltage-support parameters.

        :param vdip: Strict undervoltage fault pickup in per unit.
        :param vup: Strict overvoltage fault pickup in per unit.
        :param dbd1: Nonpositive lower voltage-error deadband edge.
        :param dbd2: Nonnegative upper voltage-error deadband edge.
        :param kqv: Proportional reactive-current injection gain.
        :param iql1: Negative injection-current floor.
        :param iqh1: Positive injection-current ceiling.
        :param vref0: Fixed reference voltage; zero selects solved terminal voltage.
        :param iqfrz: Recovery current held after a cleared fault.
        :param thld: Signed recovery hold duration in seconds.
        :return: None.
        """
        self.vdip: float = vdip
        self.vup: float = vup
        self.dbd1: float = dbd1
        self.dbd2: float = dbd2
        self.kqv: float = kqv
        self.iql1: float = iql1
        self.iqh1: float = iqh1
        self.vref0: float = vref0
        self.iqfrz: float = iqfrz
        self.thld: float = thld


def build_reeca1_voltage_support_template(
        vf: VarFactory,
        name: str = 'REECA1 voltage support',
        settings: Reeca1VoltageSupportSettings | None = None,
) -> RmsModelTemplate:
    """Build immediate reactive-current injection outside the voltage window.

    Positive `Thld` holds Iqfrz; negative `Thld` keeps the live Iqv branch.
    The separate current-limit component owns the `Thld2` active-current hold.
    This component alone cannot activate a complete REECA1 source record.

    :param vf: Shared symbolic variable factory.
    :param name: Unique controller instance name.
    :param settings: Voltage support thresholds, deadband, gain and bounds.
    :return: Controller with live/filtered voltage and reference inputs.
    :raises ValueError: Invalid thresholds, deadband, gain or current bounds.
    """
    selected: Reeca1VoltageSupportSettings = Reeca1VoltageSupportSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.vdip, selected.vup, selected.dbd1,
                                 selected.dbd2, selected.kqv, selected.iql1,
                                 selected.iqh1, selected.vref0,
                                 selected.iqfrz, selected.thld)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('REECA1 voltage-support settings must be finite')
    elif selected.vdip < 0 or selected.vup <= selected.vdip:
        raise ValueError('REECA1 voltage-fault thresholds are invalid')
    elif selected.dbd1 > 0 or selected.dbd2 < 0 or selected.kqv < 0:
        raise ValueError('REECA1 voltage deadband or gain is invalid')
    elif selected.iql1 > 0 or selected.iqh1 < 0 or selected.vref0 < 0:
        raise ValueError('REECA1 injection limits or reference are invalid')
    else:
        pass
    control: ControlRealization = ControlRealization(vf, name)
    voltage: Var = control.input('TerminalVoltagePu', Const(1.))
    filtered: Var = control.input('FilteredVoltagePu', Const(1.))
    reference: Var = control.input('ReferenceVoltagePu', Const(1.))
    vdip: Var = control.parameter('VDIP', selected.vdip)
    vup: Var = control.parameter('VUP', selected.vup)
    dbd1: Var = control.parameter('DBD1', selected.dbd1)
    dbd2: Var = control.parameter('DBD2', selected.dbd2)
    kqv: Var = control.parameter('KQV', selected.kqv)
    iql1: Var = control.parameter('IQL1', selected.iql1)
    iqh1: Var = control.parameter('IQH1', selected.iqh1)
    iqfrz: Var = control.parameter('IQFRZ', selected.iqfrz)
    thld: Var = control.parameter('THLD', selected.thld)

    # Fault pickup sees live Vt. Only the proportional injection magnitude
    # sees the measured Vt state, matching the source's two voltage paths.
    fault: Expr = Const(1.) - sym.heaviside(voltage - vdip) * sym.heaviside(vup - voltage)
    error: Expr = reference - filtered
    outside_deadband: Expr = ((error - dbd1) * sym.heaviside(dbd1 - error)
                              + (error - dbd2) * sym.heaviside(error - dbd2))
    fault_current: Expr = sym.hard_sat(kqv * outside_deadband, iql1, iqh1)
    if selected.thld != 0:
        # A delayed dropoff retains state 1 or 2 after pickup clears.
        held: Var = vf.add_var('VoltageFaultRecoveryHold_' + name)
        control.block.mode_dict[held] = Const(0.)
        control.block.procedural_logic.append(PickupDropoffLogic(
            output_var_name=held.name, bool_expr=fault,
            pickup_delay_expr=Const(0.),
            drop_delay_expr=thld if selected.thld > 0 else -thld,
            name='REECA1 reactive recovery hold ' + name,
        ))
        if selected.thld > 0:
            injection_expr: Expr = fault * fault_current + (held - fault) * iqfrz
        else:
            injection_expr = held * fault_current
    else:
        injection_expr = fault * fault_current
    injection: Var = control.algebraic('FaultReactiveCurrentPu', injection_expr, Const(0.))
    fault_signal: Var = control.algebraic('VoltageDipFlag', fault, Const(0.))
    return control.finish((injection, fault_signal),
                          'REECA1 immediate voltage-fault reactive-current injection')
