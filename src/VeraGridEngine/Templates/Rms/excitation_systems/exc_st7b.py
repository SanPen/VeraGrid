# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed standalone template for the CGMES ExcST7B model."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st7b import (
    ExcIEEEST7BParameters,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.excitation_systems.self_feedback_exciter import ExcitationLimiterLocation
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import (
    ExcST7BOELselectorKind,
    ExcST7BUELselectorKind,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_exc_s_t7_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEST7BParameters | None = None,
        output_time_constant: float = 0.0,
) -> RmsModelTemplate:
    """Build ExcST7B using its documented ST7B equation graph.

    :param vfactory: Factory used to allocate the template parameters.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical fields or documented defaults.
    :param output_time_constant: Canonical ExcST7B ``ts`` output lag.
    :return: ST7B equations with parameter events named for the ExcST7B RDF class.
    """
    settings: ExcIEEEST7BParameters = (
        ExcIEEEST7BParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcST7B' if name is None else name
    # The two independent RDF enums select where each external limiter enters
    # the diagram; addVref is signed summation and the numbered modes choose gates.
    minimum_location: ExcitationLimiterLocation = ExcitationLimiterLocation.REFERENCE_GATE
    if settings.uelin == ExcST7BUELselectorKind.addVref:
        minimum_location = ExcitationLimiterLocation.REFERENCE_SUM
    elif settings.uelin == ExcST7BUELselectorKind.outputHVgate:
        minimum_location = ExcitationLimiterLocation.OUTPUT_GATE
    else:
        pass
    maximum_location: ExcitationLimiterLocation = ExcitationLimiterLocation.REFERENCE_GATE
    if settings.oelin == ExcST7BOELselectorKind.addVref:
        maximum_location = ExcitationLimiterLocation.REFERENCE_SUM
    elif settings.oelin == ExcST7BOELselectorKind.outputLVgate:
        maximum_location = ExcitationLimiterLocation.OUTPUT_GATE
    else:
        pass
    # Declare equation constants and operating-point seeds before using them so
    # each state has an explicit steady-state value in the assembled graph.
    realization: ControlRealization = ControlRealization(vfactory, template_name)
    transducer_time: Var = realization.parameter('TR', 0.0)
    lead_time: Var = realization.parameter('TG', settings.tg)
    lag_time: Var = realization.parameter('TF', settings.tf)
    reference_maximum: Var = realization.parameter('VMAX', settings.vmax)
    reference_minimum: Var = realization.parameter('VMIN', settings.vmin)
    proportional_gain: Var = realization.parameter('KPA', settings.kpa)
    field_maximum: Var = realization.parameter('VRMAX', settings.vrmax)
    field_minimum: Var = realization.parameter('VRMIN', settings.vrmin)
    lower_feedback_gain: Var = realization.parameter('KH', settings.kh)
    upper_feedback_gain: Var = realization.parameter('KL', settings.kl)
    regulator_lead: Var = realization.parameter('TC', settings.tc)
    regulator_lag: Var = realization.parameter('TB', settings.tb)
    field_feedback_gain: Var = realization.parameter('KIA', settings.kia)
    field_feedback_time: Var = realization.parameter('TIA', settings.tia)
    output_time: Var = realization.parameter('TS', output_time_constant)
    field_initial: Var = realization.parameter('Efd0Pu', 1.0)
    voltage_initial: Var = realization.parameter('Us0Pu', 1.0)
    supplement_initial: Var = realization.parameter('Vs0Pu', 0.0)
    minimum_initial: Var = realization.parameter('Uel0Pu', 0.0)
    maximum_initial: Var = realization.parameter('Oel0Pu', 0.0)
    feedback_initial: Expr = field_feedback_gain * field_initial
    regulator_initial: Expr = field_initial - feedback_initial
    selected_reference_initial: Expr = (
        voltage_initial + regulator_initial / proportional_gain - supplement_initial
    )
    reference_initial: Expr = selected_reference_initial
    if minimum_location == ExcitationLimiterLocation.REFERENCE_SUM:
        reference_initial = reference_initial - minimum_initial
    else:
        pass
    if maximum_location == ExcitationLimiterLocation.REFERENCE_SUM:
        reference_initial = reference_initial - maximum_initial
    else:
        pass
    # Keep the limiter and voltage inputs open for the CGMES graph composer;
    # these initial values only seed standalone equation evaluation.
    sensed_voltage: Var = realization.input('UsPu', voltage_initial)
    reference: Var = realization.input('UsRefPu', reference_initial)
    supplement: Var = realization.input('VsPu', supplement_initial)
    minimum_input_initial: Expr = minimum_initial
    if minimum_location == ExcitationLimiterLocation.REFERENCE_GATE:
        minimum_input_initial = selected_reference_initial
    elif minimum_location == ExcitationLimiterLocation.OUTPUT_GATE:
        minimum_input_initial = field_initial
    else:
        pass
    minimum_input: Var = realization.input('UelPu', minimum_input_initial)
    terminal_voltage: Var = realization.input('VtPu', voltage_initial)
    maximum_input_initial: Expr = maximum_initial
    if maximum_location == ExcitationLimiterLocation.REFERENCE_GATE:
        maximum_input_initial = selected_reference_initial
    elif maximum_location == ExcitationLimiterLocation.OUTPUT_GATE:
        maximum_input_initial = field_initial
    else:
        pass
    maximum_input: Var = realization.input('OelPu', maximum_input_initial)
    sensed: Var = realization.lag(
        'MeasuredPu', sensed_voltage, transducer_time, 0.0, voltage_initial
    )
    shaped: Var = realization.lead_lag(
        'MeasuredShapePu', sensed, lead_time, lag_time, settings.tg, settings.tf,
        voltage_initial,
    )
    field: Var = vfactory.add_var(f'EfdPu_{template_name}')
    feedback: Var = realization.lag(
        'FieldFeedbackPu', field_feedback_gain * field, field_feedback_time,
        settings.tia, feedback_initial,
    )
    reference_sum: Expr = reference
    if minimum_location == ExcitationLimiterLocation.REFERENCE_SUM:
        reference_sum = reference_sum + minimum_input
    else:
        pass
    if maximum_location == ExcitationLimiterLocation.REFERENCE_SUM:
        reference_sum = reference_sum + maximum_input
    else:
        pass
    pre_maximum_reference: Var = realization.algebraic(
        'PreMaximumReferencePu', reference_sum, selected_reference_initial
    )
    pre_minimum_reference_expression: Expr = reference_sum
    if maximum_location == ExcitationLimiterLocation.REFERENCE_GATE:
        pre_minimum_reference_expression = sym.min(reference_sum, maximum_input)
    else:
        pass
    pre_minimum_reference: Var = realization.algebraic(
        'PreMinimumReferencePu', pre_minimum_reference_expression,
        selected_reference_initial,
    )
    selected_reference_expression: Expr = pre_minimum_reference
    if minimum_location == ExcitationLimiterLocation.REFERENCE_GATE:
        selected_reference_expression = sym.max(pre_minimum_reference, minimum_input)
    else:
        pass
    bounded_reference: Expr = sym.hard_sat(
        selected_reference_expression, reference_minimum, reference_maximum
    )
    # Close the voltage regulator and output-feedback loop using the same gate
    # order as EA1163, while retaining the selector-specific pre-gate ports.
    regulator_error: Expr = bounded_reference + supplement - shaped
    lower_capability: Expr = terminal_voltage * field_minimum - lower_feedback_gain * feedback
    upper_capability: Expr = terminal_voltage * field_maximum - upper_feedback_gain * feedback
    regulator: Var = realization.algebraic(
        'LimitedRegulatorPu',
        sym.min(upper_capability, sym.max(lower_capability, proportional_gain * regulator_error)),
        regulator_initial,
    )
    phase_compensated: Var = realization.lead_lag(
        'RegulatorShapePu', regulator, regulator_lead, regulator_lag,
        settings.tc, settings.tb, regulator_initial,
    )
    pre_maximum_output: Var = realization.algebraic(
        'PreMaximumOutputPu', phase_compensated + feedback, field_initial
    )
    pre_minimum_output_expression: Expr = pre_maximum_output
    if maximum_location == ExcitationLimiterLocation.OUTPUT_GATE:
        pre_minimum_output_expression = sym.min(pre_maximum_output, maximum_input)
    else:
        pass
    pre_minimum_output: Var = realization.algebraic(
        'PreMinimumOutputPu', pre_minimum_output_expression, field_initial
    )
    demanded_field: Expr = pre_minimum_output
    if minimum_location == ExcitationLimiterLocation.OUTPUT_GATE:
        demanded_field = sym.max(pre_minimum_output, minimum_input)
    else:
        pass
    limited_demand: Expr = sym.min(
        terminal_voltage * field_maximum,
        sym.max(terminal_voltage * field_minimum, demanded_field),
    )
    # EA1163 places the terminal-scaled static limits before the final Ts lag;
    # the delayed Efd state then feeds the KIA feedback path above.
    pre_lag_field: Var = realization.algebraic(
        'LimitedForcingPu', limited_demand, field_initial
    )
    realization.lag(
        'EfdPu', pre_lag_field, output_time, output_time_constant, field_initial,
        output=field,
    )
    template: RmsModelTemplate = realization.finish(
        (field, pre_maximum_reference, pre_minimum_reference,
         pre_maximum_output, pre_minimum_output),
        'CGMES ExcST7B output-feedback excitation with final field lag',
    )
    parameter_fields: tuple[str, ...] = (
        'kh', 'kia', 'kl', 'kpa', 'oelin', 'tb', 'tc', 'tf', 'tg', 'tia',
        'ts', 'uelin', 'vmax', 'vmin', 'vrmax', 'vrmin',
    )
    for parameter_name in parameter_fields:
        parameter_variable: Var = vfactory.add_var(
            f'ExcST7B.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None)
    return template
