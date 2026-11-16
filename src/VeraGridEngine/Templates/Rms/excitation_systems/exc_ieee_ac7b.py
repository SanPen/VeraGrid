# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEAC7B cascaded brushless excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _anti_windup_state_derivative
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEAC7BParameters:
    """IEEE AC7B settings on the exact CGMES RDF property surface."""

    __slots__ = (
        'kpr', 'kir', 'kdr', 'tdr', 'vrmax', 'vrmin', 'kpa', 'kia', 'vamax',
        'vamin', 'kp', 'kl', 'te', 'vfemax', 'vemin', 'ke', 'kc', 'kd',
        'kf1', 'kf2', 'kf3', 'tf', 've1', 'seve1', 've2', 'seve2',
    )

    def __init__(
            self,
            kpr: float = 4.24,
            kir: float = 4.24,
            kdr: float = 0.0,
            tdr: float = 0.0,
            vrmax: float = 5.79,
            vrmin: float = -5.79,
            kpa: float = 65.36,
            kia: float = 59.69,
            vamax: float = 1.0,
            vamin: float = -0.95,
            kp: float = 4.96,
            kl: float = 10.0,
            te: float = 1.1,
            vfemax: float = 6.9,
            vemin: float = 0.0,
            ke: float = 1.0,
            kc: float = 0.18,
            kd: float = 0.02,
            kf1: float = 0.212,
            kf2: float = 0.0,
            kf3: float = 0.0,
            tf: float = 1.0,
            ve1: float = 6.3,
            seve1: float = 0.44,
            ve2: float = 3.02,
            seve2: float = 0.075,
    ) -> None:
        """Store class-defined values using local EA typicals.

        :param kpr: Regulator proportional gain.
        :param kir: Regulator integral gain.
        :param kdr: Regulator derivative gain.
        :param tdr: Derivative filter time; the local CGMES typical is zero.
        :param vrmax: Voltage PID upper bound.
        :param vrmin: Voltage PID lower bound.
        :param kpa: Field PI proportional gain.
        :param kia: Field PI integral gain.
        :param vamax: Field PI upper bound.
        :param vamin: Field PI lower bound.
        :param kp: Terminal-voltage supply multiplier; zero selects unity.
        :param kl: Negative forcing floor coefficient.
        :param te: Brushless winding integration time.
        :param vfemax: Upper equivalent field-voltage limit.
        :param vemin: Lower winding-voltage limit.
        :param ke: Winding field constant.
        :param kc: Rectifier commutating-reactance coefficient.
        :param kd: Demagnetizing factor.
        :param kf1: Delivered-field feedback gain.
        :param kf2: Winding-voltage feedback gain.
        :param kf3: Winding-voltage rate feedback gain.
        :param tf: Winding-voltage feedback filter time.
        :param ve1: First saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second saturation voltage point.
        :param seve2: Saturation at ``ve2``.
        """
        self.kpr: float = kpr
        self.kir: float = kir
        self.kdr: float = kdr
        self.tdr: float = tdr
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.kpa: float = kpa
        self.kia: float = kia
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.kp: float = kp
        self.kl: float = kl
        self.te: float = te
        self.vfemax: float = vfemax
        self.vemin: float = vemin
        self.ke: float = ke
        self.kc: float = kc
        self.kd: float = kd
        self.kf1: float = kf1
        self.kf2: float = kf2
        self.kf3: float = kf3
        self.tf: float = tf
        self.ve1: float = ve1
        self.seve1: float = seve1
        self.ve2: float = ve2
        self.seve2: float = seve2


def build_exc_i_e_e_e_a_c7_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEAC7BParameters | None = None,
) -> RmsModelTemplate:
    """Build AC7B cascaded bounded regulators, winding, and rectifier equations.

    :param vfactory: Factory owning all runtime variables.
    :param name: Optional unique instance name.
    :param parameters: Parsed RDF settings or EA typicals.
    :return: Equation-backed model with voltage, field-current, and Efd ports.
    :raises ValueError: Invalid bounds, time constants, or saturation data.
    """
    settings: ExcIEEEAC7BParameters = (
        ExcIEEEAC7BParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEAC7B' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.kpr, settings.kir, settings.kdr, settings.tdr, settings.vrmax,
        settings.vrmin, settings.kpa, settings.kia, settings.vamax, settings.vamin,
        settings.kp, settings.kl, settings.te, settings.vfemax, settings.vemin,
        settings.ke, settings.kc, settings.kd, settings.kf1, settings.kf2,
        settings.kf3, settings.tf, settings.ve1, settings.seve1, settings.ve2,
        settings.seve2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcIEEEAC7B parameters must be finite')
    elif min(settings.tdr, settings.te, settings.tf) < 0.0:
        raise ValueError('ExcIEEEAC7B times must be nonnegative')
    elif settings.te <= 0.0:
        raise ValueError('ExcIEEEAC7B TE must be positive')
    elif settings.vrmin >= settings.vrmax or settings.vamin >= settings.vamax:
        raise ValueError('ExcIEEEAC7B controller limits are invalid')
    elif settings.vemin < 0.0 or settings.vfemax <= settings.vemin or settings.ke <= 0.0:
        raise ValueError('ExcIEEEAC7B winding limits and KE are invalid')
    elif settings.kp < 0.0 or settings.kc < 0.0:
        raise ValueError('ExcIEEEAC7B KP and KC must be nonnegative')
    elif settings.ve1 <= 0.0 or settings.ve2 <= 0.0 or settings.ve1 == settings.ve2:
        raise ValueError('ExcIEEEAC7B saturation points must be distinct and positive')
    elif settings.seve1 < 0.0 or settings.seve2 < 0.0:
        raise ValueError('ExcIEEEAC7B saturation values must be nonnegative')
    elif settings.tf == 0.0 and settings.kf3 != 0.0:
        raise ValueError('ExcIEEEAC7B nonzero KF3 requires positive TF')
    elif settings.kdr != 0.0 and settings.tdr <= 0.0:
        raise ValueError('ExcIEEEAC7B nonzero KDR requires positive TDR')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    kpr: Var = builder.parameter('KPR', settings.kpr)
    kir: Var = builder.parameter('KIR', settings.kir)
    kdr: Var = builder.parameter('KDR', settings.kdr)
    tdr: Var = builder.parameter('TDR', settings.tdr)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    kpa: Var = builder.parameter('KPA', settings.kpa)
    kia: Var = builder.parameter('KIA', settings.kia)
    vamax: Var = builder.parameter('VAMAX', settings.vamax)
    vamin: Var = builder.parameter('VAMIN', settings.vamin)
    kp: Var = builder.parameter('KP', settings.kp)
    kl: Var = builder.parameter('KL', settings.kl)
    te: Var = builder.parameter('TE', settings.te)
    vfemax: Var = builder.parameter('VFEMAX', settings.vfemax)
    vemin: Var = builder.parameter('VEMIN', settings.vemin)
    ke: Var = builder.parameter('KE', settings.ke)
    kc: Var = builder.parameter('KC', settings.kc)
    kd: Var = builder.parameter('KD', settings.kd)
    kf1: Var = builder.parameter('KF1', settings.kf1)
    kf2: Var = builder.parameter('KF2', settings.kf2)
    kf3: Var = builder.parameter('KF3', settings.kf3)
    tf: Var = builder.parameter('TF', settings.tf)
    ve1: Var = builder.parameter('VE1', settings.ve1)
    seve1: Var = builder.parameter('SEVE1', settings.seve1)
    ve2: Var = builder.parameter('VE2', settings.ve2)
    seve2: Var = builder.parameter('SEVE2', settings.seve2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))

    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    equivalent_field: Var = vfactory.add_var(f'VfePu_{template_name}')
    delivered_field: Var = vfactory.add_var(f'EfdPu_{template_name}')
    feedback_memory: Var = builder.lag(
        'FeedbackMemoryPu', equivalent_field, tf, settings.tf, Const(1.0),
    )
    equivalent_field_derivative: Expr = (equivalent_field - feedback_memory) / tf
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer
        - kf1 * delivered_field - kf2 * equivalent_field - kf3 * equivalent_field_derivative,
        Const(0.0),
    )

    derivative_term: Expr = Const(0.0)
    if settings.kdr != 0.0:
        derivative_memory: Var = builder.lag(
            'DerivativeMemoryPu', voltage_error, tdr, settings.tdr, Const(0.0),
        )
        derivative_term = kdr * (voltage_error - derivative_memory) / tdr
    else:
        pass

    regulator_integral: Var = vfactory.add_var(f'RegulatorIntegralPu_{template_name}')
    regulator_derivative: Expr = (kir * voltage_error)
    regulator_demand: Expr = kpr * voltage_error + regulator_integral + derivative_term
    bounded_regulator: Var = builder.algebraic(
        'VoltagePIDPu', sym.hard_sat(regulator_demand, vrmin, vrmax), Const(0.0),
    )
    builder.differential(
        regulator_integral,
        _demand_limited_integrator_derivative(
            regulator_derivative, regulator_demand, vrmin, vrmax,
        ),
        Const(0.0), vrmin, vrmax,
    )

    field_integral: Var = vfactory.add_var(f'FieldIntegralPu_{template_name}')
    field_error: Expr = bounded_regulator - field_integral
    field_demand: Expr = kpa * field_error + field_integral
    bounded_field_pi: Var = builder.algebraic(
        'FieldPIPu', sym.hard_sat(field_demand, vamin, vamax), Const(0.0),
    )
    field_pi_derivative: Expr = kia * field_error
    builder.differential(
        field_integral,
        _demand_limited_integrator_derivative(
            field_pi_derivative, field_demand, vamin, vamax,
        ),
        Const(0.0), vamin, vamax,
    )

    terminal_supply: Expr = terminal_voltage * kp
    if settings.kp == 0.0:
        terminal_supply = terminal_voltage
    else:
        pass
    winding_forcing: Expr = terminal_supply * bounded_field_pi
    winding_lower_forcing: Expr = -kl * equivalent_field
    winding_input: Expr = sym.hard_sat(
        winding_forcing, winding_lower_forcing, Const(1e12),
    )
    saturation: Expr = Const(0.0)
    if settings.seve1 != 0.0 and settings.seve2 != 0.0:
        saturation_slope: Expr = sym.log(seve2 / seve1) / (ve2 - ve1)
        saturation_base: Expr = seve1 * sym.exp(-saturation_slope * ve1)
        saturation = saturation_base * sym.exp(saturation_slope * exciter_voltage)
    else:
        pass
    equivalent_field_expression: Expr = (
        ke * exciter_voltage + saturation * exciter_voltage + kd * field_current
    )
    exciter_derivative: Expr = (winding_input - equivalent_field_expression) / te
    builder.differential(
        exciter_voltage,
        _anti_windup_state_derivative(
            exciter_voltage, exciter_derivative, vemin,
            (vfemax - kd * field_current) / ke,
        ),
        Const(1.0), vemin, (settings.vfemax - settings.kd * 0.0) / settings.ke,
    )
    builder.block.algebraic_vars.append(equivalent_field)
    builder.block.algebraic_eqs.append(equivalent_field - equivalent_field_expression)
    builder.block.init_eqs[equivalent_field] = Const(1.0)
    rectifier_loading: Expr = sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0))
    builder.block.algebraic_vars.append(delivered_field)
    builder.block.algebraic_eqs.append(
        delivered_field - exciter_voltage * sym.f_exc(rectifier_loading),
    )
    builder.block.init_eqs[delivered_field] = Const(1.0)

    template: RmsModelTemplate = builder.finish(
        (delivered_field,), 'CGMES ExcIEEEAC7B cascaded brushless excitation system',
    )
    for parameter_name in (
            'enabled', 'kpr', 'kir', 'kdr', 'tdr', 'vrmax', 'vrmin', 'kpa',
            'kia', 'vamax', 'vamin', 'kp', 'kl', 'te', 'vfemax', 'vemin',
            'ke', 'kc', 'kd', 'kf1', 'kf2', 'kf3', 'tf', 've1', 'seve1',
            've2', 'seve2',
    ):
        variable_name: str = f'ExcIEEEAC7B.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=variable_name,
        )
    return template


def _demand_limited_integrator_derivative(
        derivative: Expr,
        demand: Expr,
        lower_limit: Expr,
        upper_limit: Expr,
) -> Expr:
    """Stop integrator motion only when total controller demand is saturated.

    :param derivative: Unconstrained integral derivative.
    :param demand: Sum of proportional, integral, and derivative terms.
    :param lower_limit: Lower controller output limit.
    :param upper_limit: Upper controller output limit.
    :return: Integrator derivative with outward saturation windup removed.
    """
    lower_block: Expr = (Const(1.0) - sym.heaviside(demand - lower_limit))
    upper_block: Expr = (Const(1.0) - sym.heaviside(upper_limit - demand))
    freeze_lower: Expr = lower_block * sym.heaviside(-derivative)
    freeze_upper: Expr = upper_block * sym.heaviside(derivative)
    return derivative * (Const(1.0) - freeze_lower) * (Const(1.0) - freeze_upper)
