# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Executable CGMES ExcST1A static excitation model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcST1AParameters:
    """RDF parameter values used to select ExcST1A stage topology."""

    __slots__ = (
        'vimax', 'vimin', 'tc', 'tb', 'ka', 'ta', 'vrmax', 'vrmin', 'kc',
        'kf', 'tf', 'tc1', 'tb1', 'vamax', 'vamin', 'ilr', 'klr', 'xe',
    )

    def __init__(
            self,
            vimax: float = 999.0,
            vimin: float = -999.0,
            tc: float = 0.0,
            tb: float = 1.0,
            ka: float = 190.0,
            ta: float = 0.02,
            vrmax: float = 7.8,
            vrmin: float = -6.7,
            kc: float = 0.0,
            kf: float = 0.0,
            tf: float = 1.0,
            tc1: float = 0.0,
            tb1: float = 1.0,
            vamax: float = 999.0,
            vamin: float = -999.0,
            ilr: float = 0.0,
            klr: float = 0.0,
            xe: float = 0.0,
    ) -> None:
        """Store CGMES pu values and time constants.

        :param vimax: Regulator input upper bound.
        :param vimin: Regulator input lower bound.
        :param tc: First lead time constant in seconds.
        :param tb: First lag time constant in seconds.
        :param ka: Regulator gain.
        :param ta: Regulator time constant in seconds.
        :param vrmax: Rectifier/regulator upper bound.
        :param vrmin: Rectifier/regulator lower bound.
        :param kc: Rectifier loading feedback gain.
        :param kf: Excitation stabilizer feedback gain.
        :param tf: Stabilizer feedback time constant in seconds.
        :param tc1: Second lead time constant in seconds.
        :param tb1: Second lag time constant in seconds.
        :param vamax: Regulator output upper bound.
        :param vamin: Regulator output lower bound.
        :param ilr: Exciter current limit reference.
        :param klr: Exciter current limit gain.
        :param xe: Excitation transformer effective reactance.
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
        self.kf: float = kf
        self.tf: float = tf
        self.tc1: float = tc1
        self.tb1: float = tb1
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.ilr: float = ilr
        self.klr: float = klr
        self.xe: float = xe


def build_exc_s_t1_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcST1AParameters | None = None,
) -> RmsModelTemplate:
    """Build CGMES ExcST1A equations and preserve its RDF settings.

    The signal path is compensated terminal-voltage error, two lead-lag stages,
    a bounded regulator, field-current limiting, rectifier loading, and the
    derivative-form stabilizer feedback ``Kf*s/(1+s*Tf)`` from field voltage.
    Zero-time stages reduce algebraically; positive-time stages own real states.

    :param vfactory: Factory that allocates equation symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES values used to select exact zero-time stages.
    :return: Executable excitation model with five host input ports.
    :raises ValueError: Invalid time constants, limits, or nonfinite settings.
    """
    settings: ExcST1AParameters = ExcST1AParameters() if parameters is None else parameters
    template_name: str = 'ExcST1A' if name is None else name
    values: tuple[float, ...] = (
        settings.vimax, settings.vimin, settings.tc, settings.tb, settings.ka,
        settings.ta, settings.vrmax, settings.vrmin, settings.kc, settings.kf,
        settings.tf, settings.tc1, settings.tb1, settings.vamax, settings.vamin,
        settings.ilr, settings.klr, settings.xe,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('ExcST1A parameters must be finite')
    elif min(settings.tc, settings.tb, settings.ta, settings.tf, settings.tc1, settings.tb1) < 0.0:
        raise ValueError('ExcST1A time constants must be nonnegative')
    elif settings.vimin >= settings.vimax or settings.vamin >= settings.vamax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcST1A lower limits must be below upper limits')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcST1A first lead-lag requires zero lead when its lag is zero')
    elif settings.tb1 == 0.0 and settings.tc1 != 0.0:
        raise ValueError('ExcST1A second lead-lag requires zero lead when its lag is zero')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcST1A nonzero Kf requires a positive Tf')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    tc: Var = builder.parameter('TC', settings.tc)
    tb: Var = builder.parameter('TB', settings.tb)
    tc1: Var = builder.parameter('TC1', settings.tc1)
    tb1: Var = builder.parameter('TB1', settings.tb1)
    ta: Var = builder.parameter('TA', settings.ta)
    ka: Var = builder.parameter('KA', settings.ka)
    vimax: Var = builder.parameter('VIMAX', settings.vimax)
    vimin: Var = builder.parameter('VIMIN', settings.vimin)
    vamax: Var = builder.parameter('VAMAX', settings.vamax)
    vamin: Var = builder.parameter('VAMIN', settings.vamin)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    kc: Var = builder.parameter('KC', settings.kc)
    kf: Var = builder.parameter('KF', settings.kf)
    tf: Var = builder.parameter('TF', settings.tf)
    ilr: Var = builder.parameter('ILR', settings.ilr)
    klr: Var = builder.parameter('KLR', settings.klr)
    xe: Var = builder.parameter('XE', settings.xe)
    vt: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))
    terminal_current: Var = builder.input('ItPu', Const(0.0))

    # XE supplies the reactive-current voltage compensation at the input sum.
    compensated_voltage: Var = builder.algebraic(
        'CompensatedVoltagePu', vt + xe * terminal_current, Const(1.0),
    )
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    feedback: Expr = Const(0.0)
    if settings.kf != 0.0:
        feedback = builder.washout(
            'FeedbackPu', field_voltage, tf, settings.tf,
            Const(settings.kf / settings.tf), Const(0.0),
        )
    else:
        pass
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - compensated_voltage + stabilizer - feedback, Const(0.0),
    )
    regulator_input: Var = builder.algebraic(
        'RegulatorInputPu',
        sym.hard_sat(voltage_error - kf * feedback, vimin, vimax),
        Const(0.0),
    )
    lead_lag_1: Var = builder.lead_lag(
        'LeadLag1Pu', regulator_input, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    lead_lag_2: Var = builder.lead_lag(
        'LeadLag2Pu', lead_lag_1, tc1, tb1, settings.tc1, settings.tb1, Const(0.0),
    )
    regulator_demand: Expr = ka * lead_lag_2
    regulator_output: Var = builder.lag(
        'RegulatorOutputPu', regulator_demand, ta, settings.ta, Const(0.0),
        vamin, vamax,
    )
    current_limited: Expr = regulator_output - klr * sym.max(field_current - ilr, Const(0.0))
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(
        field_voltage - sym.hard_sat(current_limited, vt * vrmin, vt * vrmax - kc * field_current)
    )
    builder.block.init_eqs[field_voltage] = Const(0.0)
    template: RmsModelTemplate = builder.finish((field_voltage,), 'CGMES ExcST1A excitation controller')

    # Keep RDF property names alongside runtime equation parameters for import auditing.
    for parameter_name in (
            'enabled', 'vimax', 'vimin', 'tc', 'tb', 'ka', 'ta', 'vrmax',
            'vrmin', 'kc', 'kf', 'tf', 'tc1', 'tb1', 'vamax', 'vamin',
            'ilr', 'klr', 'xe',
    ):
        variable_name: str = f'ExcST1A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
    return template
