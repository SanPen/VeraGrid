# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed standalone template for the CGMES ExcST4B model."""

import math
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st4b import (
    ExcIEEEST4BParameters,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _esst3a_fex
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_exc_s_t4_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEST4BParameters | None = None,
        vgmax: float = 5.8,
        uel: bool = False,
        lvgate: bool = False,
) -> RmsModelTemplate:
    """Build the EA1159 cascaded-PI, compound-source ExcST4B realization.

    :param vfactory: Factory used to allocate the template parameters.
    :param name: Optional runtime model name.
    :param parameters: Parsed common ST4B coefficients or reference defaults.
    :param vgmax: Maximum field feedback voltage; EA1228 typical when absent.
    :param uel: Whether the UEL input participates in the first sum; EA1228 default is false.
    :param lvgate: Whether the OEL low-voltage gate is active; EA1228 default is false.
    :return: Equation-backed template retaining the exact ExcST4B RDF parameters.
    """
    settings: ExcIEEEST4BParameters = (
        ExcIEEEST4BParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcST4B' if name is None else name
    # Reject parameter sets that make the source, PI capability, or Vgmax
    # feedback path undefined before symbolic equations are assembled.
    if min(
            settings.kpr, settings.kir, settings.ta, settings.kpm,
            settings.kim, settings.kg, settings.kp, settings.ki, settings.kc,
            settings.xl,
    ) < 0.0 or settings.vbmax <= 0.0 or vgmax <= 0.0:
        raise ValueError('ExcST4B coefficients must satisfy nonnegative physical domains')
    elif settings.kp + settings.ki == 0.0:
        raise ValueError('ExcST4B requires a potential or current source')
    elif settings.kpr + settings.kir == 0.0 or settings.kpm + settings.kim == 0.0:
        raise ValueError('Each ExcST4B regulator requires proportional or integral action')
    elif settings.vrmax <= settings.vrmin or settings.vmmax <= settings.vmmin:
        raise ValueError('ExcST4B regulator capabilities must be ordered')
    else:
        pass
    # The EA selector booleans insert their signals at distinct diagram stages.
    realization: ControlRealization = ControlRealization(vfactory, template_name)
    sensing_time: Var = realization.parameter('TR', 0.0)
    outer_proportional_gain: Var = realization.parameter('KPR', settings.kpr)
    outer_integral_gain: Var = realization.parameter('KIR', settings.kir)
    outer_maximum: Var = realization.parameter('VRMAX', settings.vrmax)
    outer_minimum: Var = realization.parameter('VRMIN', settings.vrmin)
    regulator_time: Var = realization.parameter('TA', settings.ta)
    inner_proportional_gain: Var = realization.parameter('KPM', settings.kpm)
    inner_integral_gain: Var = realization.parameter('KIM', settings.kim)
    inner_maximum: Var = realization.parameter('VMMAX', settings.vmmax)
    inner_minimum: Var = realization.parameter('VMMIN', settings.vmmin)
    field_feedback_gain: Var = realization.parameter('KG', settings.kg)
    field_feedback_maximum: Var = realization.parameter('VGMAX', vgmax)
    potential_gain: Var = realization.parameter('KP', settings.kp)
    current_gain: Var = realization.parameter('KI', settings.ki)
    supply_maximum: Var = realization.parameter('VBMAX', settings.vbmax)
    commutation_gain: Var = realization.parameter('KC', settings.kc)
    leakage_reactance: Var = realization.parameter('XL', settings.xl)
    potential_angle: Var = realization.parameter('THETAP', settings.thetap)
    field_initial: Var = realization.parameter('Efd0Pu', 1.0)
    voltage_initial: Var = realization.parameter('Us0Pu', 1.0)
    supplement_initial: Var = realization.parameter('Vs0Pu', 0.0)
    uel_initial: Var = realization.parameter('Uel0Pu', 0.0)
    # The compound source is computed from terminal phasors, stator current,
    # field current, and the documented commutation loading curve.
    sensed_voltage: Var = realization.input('UsPu', voltage_initial)
    voltage_reference: Var = realization.input('UsRefPu', voltage_initial)
    supplement: Var = realization.input('VsPu', supplement_initial)
    terminal_real: Var = realization.input('VrPu', Const(1.0))
    terminal_imaginary: Var = realization.input('ViPu', Const(0.0))
    current_real: Var = realization.input('IrPu', Const(0.5))
    current_imaginary: Var = realization.input('IiPu', Const(0.0))
    field_current: Var = realization.input('IfdPu', Const(1.0))
    uel_input: Var = realization.input('UelPu', uel_initial)
    oel_input: Var = realization.input('OelPu', Const(1.0))
    # Rotate and compound the terminal quantities to form the load-dependent
    # rectifier supply before its independent Vbmax ceiling.
    cosine: Expr = sym.cos(potential_angle * Const(math.pi / 180.0))
    sine: Expr = sym.sin(potential_angle * Const(math.pi / 180.0))
    source_real: Expr = potential_gain * (
        cosine * (terminal_real - leakage_reactance * current_imaginary)
        - sine * (terminal_imaginary + leakage_reactance * current_real)
    ) - current_gain * current_imaginary
    source_imaginary: Expr = potential_gain * (
        sine * (terminal_real - leakage_reactance * current_imaginary)
        + cosine * (terminal_imaginary + leakage_reactance * current_real)
    ) + current_gain * current_real
    potential: Var = realization.algebraic(
        'PotentialPu', sym.sqrt(source_real ** 2 + source_imaginary ** 2),
        sym.sqrt(source_real ** 2 + source_imaginary ** 2),
    )
    loading: Expr = sym.safe_divide(commutation_gain * field_current, potential, 1.0)
    supply_expression: Expr = sym.min(
        supply_maximum, potential * _esst3a_fex(loading)
    )
    supply: Var = realization.algebraic('SupplyPu', supply_expression, supply_expression)
    field_loop_initial: Expr = sym.safe_divide(field_initial, supply, 1.0)
    if settings.kim > 0.0:
        inner_error_initial: Expr = Const(0.0)
    else:
        inner_error_initial = field_loop_initial / inner_proportional_gain
    field_feedback_initial: Expr = sym.min(field_initial, field_feedback_maximum)
    regulator_initial: Expr = (
        field_feedback_gain * field_feedback_initial + inner_error_initial
    )
    if settings.kir > 0.0:
        voltage_error_initial: Expr = Const(0.0)
    else:
        voltage_error_initial = regulator_initial / outer_proportional_gain
    reference_initial: Expr = (
        voltage_initial + voltage_error_initial - supplement_initial
    )
    if uel is True:
        reference_initial = reference_initial - uel_initial
    else:
        pass
    realization.block.init_eqs[voltage_reference] = reference_initial
    realization.block.init_eqs[oel_input] = field_loop_initial
    measured_voltage: Var = realization.lag(
        'MeasuredPu', sensed_voltage, sensing_time, 0.0, voltage_initial
    )
    uel_signal: Expr = uel_input if uel is True else Const(0.0)
    outer_error: Expr = voltage_reference + supplement + uel_signal - measured_voltage
    # Each PI integrator uses directional anti-windup at its own CGMES limits;
    # Ta remains an exact algebraic bypass when its imported value is zero.
    outer_integral: Var = realization.differential(
        vfactory.add_var(f'VoltageIntegralPu_{template_name}'),
        outer_integral_gain * outer_error,
        regulator_initial,
        outer_minimum - outer_proportional_gain * outer_error,
        outer_maximum - outer_proportional_gain * outer_error,
    ) if settings.kir > 0.0 else realization.algebraic(
        'VoltageIntegralPu', Const(0.0), Const(0.0)
    )
    outer_demand: Var = realization.algebraic(
        'VoltageDemandPu',
        sym.hard_sat(
            outer_proportional_gain * outer_error + outer_integral,
            outer_minimum,
            outer_maximum,
        ),
        regulator_initial,
    )
    regulator: Var = realization.lag(
        'RegulatorPu', outer_demand, regulator_time, settings.ta, regulator_initial
    )
    field: Var = vfactory.add_var(f'EfdPu_{template_name}')
    limited_feedback: Expr = sym.min(field, field_feedback_maximum)
    inner_error: Expr = regulator - field_feedback_gain * limited_feedback
    inner_integral: Var = realization.differential(
        vfactory.add_var(f'FieldIntegralPu_{template_name}'),
        inner_integral_gain * inner_error,
        field_loop_initial,
        inner_minimum - inner_proportional_gain * inner_error,
        inner_maximum - inner_proportional_gain * inner_error,
    ) if settings.kim > 0.0 else realization.algebraic(
        'FieldIntegralPu', Const(0.0), Const(0.0)
    )
    inner_demand: Var = realization.algebraic(
        'PreMaximumPu',
        sym.hard_sat(
            inner_proportional_gain * inner_error + inner_integral,
            inner_minimum,
            inner_maximum,
        ),
        field_loop_initial,
    )
    if lvgate is True:
        gated_demand: Expr = sym.min(inner_demand, oel_input)
    else:
        gated_demand = inner_demand
    delivered_field: Expr = supply * gated_demand
    realization.block.algebraic_vars.append(field)
    realization.block.algebraic_eqs.append(field - delivered_field)
    realization.block.init_eqs[field] = field_initial
    template: RmsModelTemplate = realization.finish(
        (field, inner_demand),
        'CGMES ExcST4B cascaded PI excitation with Vgmax feedback and compound supply',
    )
    parameter_fields: tuple[str, ...] = (
        'kpr', 'kir', 'ta', 'vrmax', 'vrmin', 'kpm', 'kim', 'vmmax', 'vmmin',
        'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax', 'vgmax', 'uel', 'lvgate',
    )
    for parameter_name in parameter_fields:
        parameter_variable: Var = vfactory.add_var(
            f'ExcST4B.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None)
    return template
