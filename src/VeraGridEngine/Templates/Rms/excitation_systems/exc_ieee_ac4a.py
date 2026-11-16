# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEAC4A thyristor-bridge excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class ExcIEEEAC4AParameters:
    """IEEE AC4A voltage regulator, phase compensation, and loading settings."""

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
        """Store CGMES values in per-unit and seconds.

        :param vimax: Lead-lag output upper bound.
        :param vimin: Lead-lag output lower bound.
        :param tc: Lead-lag numerator time.
        :param tb: Lead-lag denominator time.
        :param ka: Voltage regulator gain.
        :param ta: Regulator time constant.
        :param vrmax: Regulator output upper limit.
        :param vrmin: Regulator output lower limit.
        :param kc: Transient exciter loading coefficient.
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


def build_exc_i_e_e_e_a_c4_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEAC4AParameters | None = None,
) -> RmsModelTemplate:
    """Build the AC4A lead-lag regulator and transient loading equations.

    :param vfactory: Factory that owns the symbolic model.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES values used to select exact stage topology.
    :return: Executable AC4A excitation model with voltage, stabilizer, and Ifd inputs.
    :raises ValueError: Nonfinite values, invalid limits, or improper time constants.
    """
    settings: ExcIEEEAC4AParameters = (
        ExcIEEEAC4AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEAC4A' if name is None else name
    values: tuple[float, ...] = (
        settings.vimax, settings.vimin, settings.tc, settings.tb, settings.ka,
        settings.ta, settings.vrmax, settings.vrmin, settings.kc,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('ExcIEEEAC4A parameters must be finite')
    elif min(settings.tc, settings.tb, settings.ta) < 0.0:
        raise ValueError('ExcIEEEAC4A times must be nonnegative')
    elif settings.vimin >= settings.vimax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcIEEEAC4A lower limits must be below upper limits')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcIEEEAC4A requires zero lead when T_B is zero')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    vimax: Var = builder.parameter('VIMAX', settings.vimax)
    vimin: Var = builder.parameter('VIMIN', settings.vimin)
    tc: Var = builder.parameter('TC', settings.tc)
    tb: Var = builder.parameter('TB', settings.tb)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    kc: Var = builder.parameter('KC', settings.kc)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))

    # The lead-lag output is voltage-regulator input and keeps its own Vimin/Vimax limits.
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer, Const(0.0),
    )
    compensated_error: Var = builder.bounded_lead_lag(
        'LeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb,
        Const(0.0), vimin, vimax,
    )
    # Current-dependent state bounds express transient loading of the exciter alternator.
    field_voltage: Var = builder.lag(
        'EfdPu',
        ka * compensated_error,
        ta,
        settings.ta,
        Const(1.0),
        vrmin - kc * field_current,
        vrmax - kc * field_current,
    )
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcIEEEAC4A controlled-rectifier excitation system',
    )

    # Preserve the canonical RDF field names for event-based scalar updates.
    for parameter_name in (
            'enabled', 'vimax', 'vimin', 'tc', 'tb', 'ka', 'ta', 'vrmax', 'vrmin', 'kc',
    ):
        variable_name: str = f'ExcIEEEAC4A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
    return template
