# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES ExcAC4A alternator-supplied rectifier excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAC4AParameters:
    """CGMES ExcAC4A lead-lag, regulator, and current compensation settings."""

    __slots__ = ('vimax', 'vimin', 'tc', 'tb', 'ka', 'ta', 'vrmax', 'vrmin', 'kc')

    def __init__(
            self,
            vimax: float = 10.0,
            vimin: float = -10.0,
            tc: float = 1.0,
            tb: float = 10.0,
            ka: float = 200.0,
            ta: float = 0.015,
            vrmax: float = 5.64,
            vrmin: float = -4.53,
            kc: float = 0.0,
    ) -> None:
        """Store canonical AC4A values.

        :param vimax: Lead-lag output upper limit.
        :param vimin: Lead-lag output lower limit.
        :param tc: Lead-lag numerator time in seconds.
        :param tb: Lead-lag denominator time in seconds.
        :param ka: Regulator gain.
        :param ta: Regulator time in seconds.
        :param vrmax: Regulator upper limit before current compensation.
        :param vrmin: Regulator lower limit before current compensation.
        :param kc: Field-current compensation factor.
        """
        self.vimax: float = vimax
        self.vimin: float = vimin
        self.tc: float = tc
        self.tb: float = tb
        self.ka: float = ka
        self.ta: float = ta
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.kc: float = kc


def build_exc_a_c4_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAC4AParameters | None = None,
) -> RmsModelTemplate:
    """Build AC4A bounded lead-lag, VUEL gate, and field-current limits.

    :param vfactory: Factory that owns the symbolic model.
    :param name: Optional runtime instance name.
    :param parameters: Parsed CGMES values.
    :return: Equation-backed AC4A regulator with explicit machine ports.
    :raises ValueError: Invalid times or bounds.
    """
    settings: ExcAC4AParameters = ExcAC4AParameters() if parameters is None else parameters
    template_name: str = 'ExcAC4A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.vimax, settings.vimin, settings.tc, settings.tb, settings.ka,
        settings.ta, settings.vrmax, settings.vrmin, settings.kc,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAC4A parameters must be finite')
    elif min(settings.tc, settings.tb, settings.ta) < 0.0:
        raise ValueError('ExcAC4A times must be nonnegative')
    elif settings.vimin >= settings.vimax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcAC4A lower limits must be below upper limits')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcAC4A requires zero lead when T_B is zero')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    tc: Var = builder.parameter('TC', settings.tc)
    tb: Var = builder.parameter('TB', settings.tb)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    vimax: Var = builder.parameter('VIMAX', settings.vimax)
    vimin: Var = builder.parameter('VIMIN', settings.vimin)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    kc: Var = builder.parameter('KC', settings.kc)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))
    underexcitation: Var = builder.input('VuelPu', Const(0.0))
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer, Const(0.0),
    )
    compensated_error: Var = builder.bounded_lead_lag(
        'LeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb,
        Const(0.0), vimin, vimax,
    )
    gated_error: Var = builder.algebraic(
        'GatedErrorPu', sym.max(compensated_error, underexcitation), Const(0.0),
    )
    field_voltage: Var = builder.lag(
        'EfdPu',
        ka * gated_error,
        ta,
        settings.ta,
        Const(1.0),
        vrmin - kc * field_current,
        vrmax - kc * field_current,
    )
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcAC4A voltage regulator',
    )
    return template
