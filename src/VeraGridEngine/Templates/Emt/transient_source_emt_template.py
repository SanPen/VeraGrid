# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, List

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.source_emt_template import _build_external_mapping
from VeraGridEngine.Templates.Emt.source_emt_template import _build_source_template_name
from VeraGridEngine.Templates.Emt.source_emt_template import _get_active_nabc_labels
from VeraGridEngine.Templates.Emt.source_emt_template import _get_current_reference
from VeraGridEngine.Templates.Emt.source_emt_template import _get_voltage_reference
from VeraGridEngine.Templates.template_definition import TemplateDefinition, TemplateProp
from VeraGridEngine.Utils.Symbolic.block import Expr, Var
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp, Comparison
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


def _build_time_state(vf: VarFactory, template: EmtModelTemplate, resolved_name: str) -> Var:
    """
    Build the internal source time state used by transient sources.

    :param vf: EMT variable factory.
    :param template: Target EMT template.
    :param resolved_name: Symbolic block name.
    :return: Internal source-time state variable.
    """
    time_var: Var = vf.add_var(name=f"t_src")
    diff_time_var: Var = vf.add_diff_var(name=f"d_t_src", base_var=time_var)
    template.block.state_vars = [time_var]
    template.block.diff_vars = [diff_time_var]
    template.block.state_eqs = [sym.Const(1.0)]
    template.block.init_eqs[time_var] = sym.Const(0.0)
    return time_var


def _comparison_expr(lhs: Expr, op: CmpOp, rhs: Expr) -> Expr:
    """
    Build one boolean-like expression from one symbolic comparison.

    :param lhs: Left-hand side expression.
    :param op: Comparison operator.
    :param rhs: Right-hand side expression.
    :return: Symbolic 0/1 expression.
    """
    return Comparison(lhs=lhs, op=op, rhs=rhs).to_expression()


def _build_step_expression(time_var: Var,
                           initial_value_var: Var,
                           final_value_var: Var,
                           step_time_var: Var) -> Expr:
    """
    Build one step waveform expression.

    :param time_var: Internal source time state.
    :param initial_value_var: Value before the step.
    :param final_value_var: Value after the step.
    :param step_time_var: Step time in seconds.
    :return: Step waveform expression.
    """
    step_selector: Expr = _comparison_expr(time_var, CmpOp.GE, step_time_var)
    return initial_value_var + step_selector * (final_value_var - initial_value_var)


def _build_ramp_expression(time_var: Var,
                           initial_value_var: Var,
                           final_value_var: Var,
                           start_time_var: Var,
                           end_time_var: Var) -> Expr:
    """
    Build one ramp waveform expression.

    :param time_var: Internal source time state.
    :param initial_value_var: Value before the ramp.
    :param final_value_var: Value after the ramp.
    :param start_time_var: Ramp start time in seconds.
    :param end_time_var: Ramp end time in seconds.
    :return: Ramp waveform expression.
    """
    progress_expr: Expr = sym.hard_sat(
        (time_var - start_time_var) / (end_time_var - start_time_var),
        sym.Const(0.0),
        sym.Const(1.0),
    )
    return initial_value_var + progress_expr * (final_value_var - initial_value_var)


def _build_double_exponential_expression(time_var: Var,
                                         amplitude_var: Var,
                                         alpha_var: Var,
                                         beta_var: Var,
                                         delay_var: Var) -> Expr:
    """
    Build one delayed double-exponential waveform expression.

    :param time_var: Internal source time state.
    :param amplitude_var: Overall amplitude scale.
    :param alpha_var: Slow exponential coefficient.
    :param beta_var: Fast exponential coefficient.
    :param delay_var: Emission delay in seconds.
    :return: Double-exponential waveform expression.
    """
    active_expr: Expr = _comparison_expr(time_var, CmpOp.GE, delay_var)
    delayed_time_expr: Expr = (time_var - delay_var) * active_expr
    return amplitude_var * (sym.exp(-alpha_var * delayed_time_expr) - sym.exp(-beta_var * delayed_time_expr)) * active_expr


def _build_heidler_expression(time_var: Var,
                              peak_var: Var,
                              front_time_var: Var,
                              tail_time_var: Var,
                              order_var: Var,
                              delay_var: Var) -> Expr:
    """
    Build one delayed Heidler current waveform expression.

    :param time_var: Internal source time state.
    :param peak_var: Peak-current scale.
    :param front_time_var: Front-time parameter in seconds.
    :param tail_time_var: Tail-time parameter in seconds.
    :param order_var: Heidler order exponent.
    :param delay_var: Emission delay in seconds.
    :return: Heidler waveform expression.
    """
    active_expr: Expr = _comparison_expr(time_var, CmpOp.GE, delay_var)
    delayed_time_expr: Expr = (time_var - delay_var) * active_expr
    ratio_expr: Expr = delayed_time_expr / front_time_var + sym.Const(1.0e-12)
    numerator_expr: Expr = ratio_expr ** order_var
    denominator_expr: Expr = sym.Const(1.0) + numerator_expr
    return peak_var * (numerator_expr / denominator_expr) * sym.exp(-delayed_time_expr / tail_time_var) * active_expr


def _build_cigre_expression(time_var: Var,
                            a_var: Var,
                            b_var: Var,
                            n_var: Var,
                            tn_var: Var,
                            i1_var: Var,
                            t1_var: Var,
                            i2_var: Var,
                            t2_var: Var,
                            delay_var: Var) -> Expr:
    """
    Build one delayed CIGRE surge waveform expression.

    :param time_var: Internal source time state.
    :param a_var: Front linear coefficient.
    :param b_var: Front nonlinear coefficient.
    :param n_var: Front exponent.
    :param tn_var: Front-to-tail transition time in seconds.
    :param i1_var: First tail amplitude.
    :param t1_var: First tail time constant in seconds.
    :param i2_var: Second tail amplitude.
    :param t2_var: Second tail time constant in seconds.
    :param delay_var: Emission delay in seconds.
    :return: CIGRE waveform expression.
    """
    active_expr: Expr = _comparison_expr(time_var, CmpOp.GE, delay_var)
    delayed_time_expr: Expr = (time_var - delay_var) * active_expr
    front_selector: Expr = _comparison_expr(delayed_time_expr, CmpOp.LT, tn_var)
    tail_selector: Expr = _comparison_expr(delayed_time_expr, CmpOp.GE, tn_var)
    tail_time_expr: Expr = (delayed_time_expr - tn_var) * tail_selector
    front_expr: Expr = a_var * delayed_time_expr + b_var * (delayed_time_expr ** n_var)
    tail_expr: Expr = i1_var * sym.exp(-tail_time_expr / t1_var) - i2_var * sym.exp(-tail_time_expr / t2_var)
    return active_expr * (front_expr * front_selector + tail_expr * tail_selector)


def _build_current_source_template_from_waveform(vf: VarFactory,
                                                 phN: bool,
                                                 phA: bool,
                                                 phB: bool,
                                                 phC: bool,
                                                 waveform_expr: Expr,
                                                 name: str) -> EmtModelTemplate:
    """
    Build one phase-selective EMT current source from one shared waveform expression.

    :param vf: EMT variable factory.
    :param phN: Whether neutral is active.
    :param phA: Whether phase A is active.
    :param phB: Whether phase B is active.
    :param phC: Whether phase C is active.
    :param waveform_expr: Shared waveform expression.
    :param name: Symbolic block name.
    :return: Configured EMT template.
    """
    active_labels: List[str] = _get_active_nabc_labels(phN=phN, phA=phA, phB=phB, phC=phC)
    resolved_name: str = _build_source_template_name(name, phN, phA, phB, phC, name)
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name

    voltage_vars: Dict[str, Var] = dict()
    current_vars: Dict[str, Var] = dict()
    in_vars: List[Var] = list()
    algebraic_vars: List[Var] = list()
    algebraic_eqs: List[Expr] = list()
    out_vars: List[Var] = list()
    phase_label: str

    for phase_label in active_labels:
        voltage_var: Var = vf.add_var(name=f"v_{phase_label}", reference=_get_voltage_reference(phase_label))
        current_var: Var = vf.add_var(name=f"i_{phase_label}", reference=_get_current_reference(phase_label))
        voltage_vars[phase_label] = voltage_var
        current_vars[phase_label] = current_var
        in_vars.append(voltage_var)
        algebraic_vars.append(current_var)
        algebraic_eqs.append(current_var - waveform_expr)
        out_vars.append(current_var)
        template.block.init_eqs[current_var] = sym.Const(0.0)

    template.block.in_vars = in_vars
    template.block.algebraic_vars = algebraic_vars
    template.block.algebraic_eqs = algebraic_eqs
    template.block.out_vars = out_vars
    template.block.external_mapping = _build_external_mapping(voltage_vars, current_vars)
    return template


def _build_voltage_source_template_from_waveform(vf: VarFactory,
                                                 phN: bool,
                                                 phA: bool,
                                                 phB: bool,
                                                 phC: bool,
                                                 waveform_expr: Expr,
                                                 conductance_var: Var,
                                                 name: str) -> EmtModelTemplate:
    """
    Build one phase-selective EMT voltage source from one shared waveform expression.

    :param vf: EMT variable factory.
    :param phN: Whether neutral is active.
    :param phA: Whether phase A is active.
    :param phB: Whether phase B is active.
    :param phC: Whether phase C is active.
    :param waveform_expr: Shared waveform expression.
    :param conductance_var: Shared Norton conductance.
    :param name: Symbolic block name.
    :return: Configured EMT template.
    """
    active_labels: List[str] = _get_active_nabc_labels(phN=phN, phA=phA, phB=phB, phC=phC)
    resolved_name: str = _build_source_template_name(name, phN, phA, phB, phC, name)
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name

    voltage_vars: Dict[str, Var] = dict()
    current_vars: Dict[str, Var] = dict()
    in_vars: List[Var] = list()
    algebraic_vars: List[Var] = list()
    algebraic_eqs: List[Expr] = list()
    out_vars: List[Var] = list()
    phase_label: str

    for phase_label in active_labels:
        voltage_var: Var = vf.add_var(name=f"v_{phase_label}", reference=_get_voltage_reference(phase_label))
        current_var: Var = vf.add_var(name=f"i_{phase_label}", reference=_get_current_reference(phase_label))
        voltage_vars[phase_label] = voltage_var
        current_vars[phase_label] = current_var
        in_vars.append(voltage_var)
        algebraic_vars.append(current_var)
        algebraic_eqs.append(current_var - conductance_var * (waveform_expr - voltage_var))
        out_vars.append(current_var)
        template.block.init_eqs[current_var] = sym.Const(0.0)

    template.block.in_vars = in_vars
    template.block.algebraic_vars = algebraic_vars
    template.block.algebraic_eqs = algebraic_eqs
    template.block.out_vars = out_vars
    template.block.external_mapping = _build_external_mapping(voltage_vars, current_vars)
    return template


class StepCurrentSourceEmtTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="phN", units="", descr="Whether neutral is active.", tpe=bool, value=False),
                TemplateProp(name="phA", units="", descr="Whether phase A is active.", tpe=bool, value=True),
                TemplateProp(name="phB", units="", descr="Whether phase B is active.", tpe=bool, value=False),
                TemplateProp(name="phC", units="", descr="Whether phase C is active.", tpe=bool, value=False),
                TemplateProp(name="initial_value", units="", descr="Value before the step.", tpe=float, value=0.0),
                TemplateProp(name="final_value", units="", descr="Value after the step.", tpe=float, value=1.0),
                TemplateProp(name="step_time_s", units="s", descr="Step time in seconds.", tpe=float, value=0.02),
                TemplateProp(name="name", units="", descr="Symbolic block name.", tpe=str, value="step_current_source_emt"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        phN: bool = self.get_value("phN")
        phA: bool = self.get_value("phA")
        phB: bool = self.get_value("phB")
        phC: bool = self.get_value("phC")
        initial_value: float = self.get_value("initial_value")
        final_value: float = self.get_value("final_value")
        step_time_s: float = self.get_value("step_time_s")
        name: str | None = self.get_value("name")

        return get_step_current_source_emt_template(
            self.vf, phN, phA, phB, phC, initial_value, final_value, step_time_s, name,
        )


def get_step_current_source_emt_template(vf: VarFactory,
                                         phN: bool = False,
                                         phA: bool = True,
                                         phB: bool = False,
                                         phC: bool = False,
                                         initial_value: float = 0.0,
                                         final_value: float = 1.0,
                                         step_time_s: float = 0.02,
                                         name: str | None = "step_current_source_emt") -> EmtModelTemplate:
    """
    Build one phase-selective EMT step current source.

    :param vf: EMT variable factory.
    :param phN: Whether neutral is active.
    :param phA: Whether phase A is active.
    :param phB: Whether phase B is active.
    :param phC: Whether phase C is active.
    :param initial_value: Value before the step.
    :param final_value: Value after the step.
    :param step_time_s: Step time in seconds.
    :param name: Optional symbolic block name.
    :return: Configured EMT template.
    """
    resolved_name: str = _build_source_template_name("step_current_source_emt", phN, phA, phB, phC, name)
    template = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name
    time_var: Var = _build_time_state(vf, template, resolved_name)
    initial_var: Var = vf.add_var(name=f"step_init")
    final_var: Var = vf.add_var(name=f"step_final")
    step_time_var: Var = vf.add_var(name=f"step_time")
    template.block.event_dict[initial_var] = vf.add_const(float(initial_value))
    template.block.event_dict[final_var] = vf.add_const(float(final_value))
    template.block.event_dict[step_time_var] = vf.add_const(float(step_time_s))
    waveform_expr: Expr = _build_step_expression(time_var, initial_var, final_var, step_time_var)
    source_template: EmtModelTemplate = _build_current_source_template_from_waveform(vf, phN, phA, phB, phC, waveform_expr, resolved_name)
    source_template.block.state_vars = template.block.state_vars
    source_template.block.diff_vars = template.block.diff_vars
    source_template.block.state_eqs = template.block.state_eqs
    source_template.block.event_dict.update(template.block.event_dict)
    source_template.block.init_eqs.update(template.block.init_eqs)
    source_template.name = resolved_name
    source_template.block.name = resolved_name
    return source_template


class StepVoltageSourceEmtTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="phN", units="", descr="Whether neutral is active.", tpe=bool, value=False),
                TemplateProp(name="phA", units="", descr="Whether phase A is active.", tpe=bool, value=True),
                TemplateProp(name="phB", units="", descr="Whether phase B is active.", tpe=bool, value=False),
                TemplateProp(name="phC", units="", descr="Whether phase C is active.", tpe=bool, value=False),
                TemplateProp(name="initial_value", units="", descr="Value before the step.", tpe=float, value=0.0),
                TemplateProp(name="final_value", units="", descr="Value after the step.", tpe=float, value=1.0),
                TemplateProp(name="step_time_s", units="s", descr="Step time in seconds.", tpe=float, value=0.02),
                TemplateProp(name="source_conductance_value", units="S", descr="Norton conductance.", tpe=float, value=100.0),
                TemplateProp(name="name", units="", descr="Symbolic block name.", tpe=str, value="step_voltage_source_emt"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        phN: bool = self.get_value("phN")
        phA: bool = self.get_value("phA")
        phB: bool = self.get_value("phB")
        phC: bool = self.get_value("phC")
        initial_value: float = self.get_value("initial_value")
        final_value: float = self.get_value("final_value")
        step_time_s: float = self.get_value("step_time_s")
        source_conductance_value: float = self.get_value("source_conductance_value")
        name: str | None = self.get_value("name")

        return get_step_voltage_source_emt_template(
            self.vf, phN, phA, phB, phC, initial_value, final_value, step_time_s,
            source_conductance_value, name,
        )


def get_step_voltage_source_emt_template(vf: VarFactory,
                                         phN: bool = False,
                                         phA: bool = True,
                                         phB: bool = False,
                                         phC: bool = False,
                                         initial_value: float = 0.0,
                                         final_value: float = 1.0,
                                         step_time_s: float = 0.02,
                                         source_conductance_value: float = 100.0,
                                         name: str | None = "step_voltage_source_emt") -> EmtModelTemplate:
    """
    Build one phase-selective EMT step voltage source.

    :param vf: EMT variable factory.
    :param phN: Whether neutral is active.
    :param phA: Whether phase A is active.
    :param phB: Whether phase B is active.
    :param phC: Whether phase C is active.
    :param initial_value: Value before the step.
    :param final_value: Value after the step.
    :param step_time_s: Step time in seconds.
    :param source_conductance_value: Norton conductance.
    :param name: Optional symbolic block name.
    :return: Configured EMT template.
    """
    resolved_name: str = _build_source_template_name("step_voltage_source_emt", phN, phA, phB, phC, name)
    template = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name
    time_var: Var = _build_time_state(vf, template, resolved_name)
    initial_var: Var = vf.add_var(name=f"step_init")
    final_var: Var = vf.add_var(name=f"step_final")
    step_time_var: Var = vf.add_var(name=f"step_time")
    conductance_var: Var = vf.add_var(name=f"g_src")
    template.block.event_dict[initial_var] = vf.add_const(float(initial_value))
    template.block.event_dict[final_var] = vf.add_const(float(final_value))
    template.block.event_dict[step_time_var] = vf.add_const(float(step_time_s))
    template.block.event_dict[conductance_var] = vf.add_const(float(source_conductance_value))
    waveform_expr: Expr = _build_step_expression(time_var, initial_var, final_var, step_time_var)
    source_template: EmtModelTemplate = _build_voltage_source_template_from_waveform(vf, phN, phA, phB, phC, waveform_expr, conductance_var, resolved_name)
    source_template.block.state_vars = template.block.state_vars
    source_template.block.diff_vars = template.block.diff_vars
    source_template.block.state_eqs = template.block.state_eqs
    source_template.block.event_dict.update(template.block.event_dict)
    source_template.block.init_eqs.update(template.block.init_eqs)
    source_template.name = resolved_name
    source_template.block.name = resolved_name
    return source_template


class RampCurrentSourceEmtTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="phN", units="", descr="Whether neutral is active.", tpe=bool, value=False),
                TemplateProp(name="phA", units="", descr="Whether phase A is active.", tpe=bool, value=True),
                TemplateProp(name="phB", units="", descr="Whether phase B is active.", tpe=bool, value=False),
                TemplateProp(name="phC", units="", descr="Whether phase C is active.", tpe=bool, value=False),
                TemplateProp(name="initial_value", units="", descr="Value before the ramp.", tpe=float, value=0.0),
                TemplateProp(name="final_value", units="", descr="Value after the ramp.", tpe=float, value=1.0),
                TemplateProp(name="start_time_s", units="s", descr="Ramp start time in seconds.", tpe=float, value=0.01),
                TemplateProp(name="end_time_s", units="s", descr="Ramp end time in seconds.", tpe=float, value=0.03),
                TemplateProp(name="name", units="", descr="Symbolic block name.", tpe=str, value="ramp_current_source_emt"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        phN: bool = self.get_value("phN")
        phA: bool = self.get_value("phA")
        phB: bool = self.get_value("phB")
        phC: bool = self.get_value("phC")
        initial_value: float = self.get_value("initial_value")
        final_value: float = self.get_value("final_value")
        start_time_s: float = self.get_value("start_time_s")
        end_time_s: float = self.get_value("end_time_s")
        name: str | None = self.get_value("name")

        return get_ramp_current_source_emt_template(
            self.vf, phN, phA, phB, phC, initial_value, final_value,
            start_time_s, end_time_s, name,
        )


def get_ramp_current_source_emt_template(vf: VarFactory,
                                         phN: bool = False,
                                         phA: bool = True,
                                         phB: bool = False,
                                         phC: bool = False,
                                         initial_value: float = 0.0,
                                         final_value: float = 1.0,
                                         start_time_s: float = 0.01,
                                         end_time_s: float = 0.03,
                                         name: str | None = "ramp_current_source_emt") -> EmtModelTemplate:
    """
    Build one phase-selective EMT ramp current source.
    """
    resolved_name: str = _build_source_template_name("ramp_current_source_emt", phN, phA, phB, phC, name)
    template = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name
    time_var: Var = _build_time_state(vf, template, resolved_name)
    initial_var: Var = vf.add_var(name=f"ramp_init")
    final_var: Var = vf.add_var(name=f"ramp_final")
    start_time_var: Var = vf.add_var(name=f"ramp_start")
    end_time_var: Var = vf.add_var(name=f"ramp_end")
    template.block.event_dict[initial_var] = vf.add_const(float(initial_value))
    template.block.event_dict[final_var] = vf.add_const(float(final_value))
    template.block.event_dict[start_time_var] = vf.add_const(float(start_time_s))
    template.block.event_dict[end_time_var] = vf.add_const(float(end_time_s))
    waveform_expr: Expr = _build_ramp_expression(time_var, initial_var, final_var, start_time_var, end_time_var)
    source_template: EmtModelTemplate = _build_current_source_template_from_waveform(vf, phN, phA, phB, phC, waveform_expr, resolved_name)
    source_template.block.state_vars = template.block.state_vars
    source_template.block.diff_vars = template.block.diff_vars
    source_template.block.state_eqs = template.block.state_eqs
    source_template.block.event_dict.update(template.block.event_dict)
    source_template.block.init_eqs.update(template.block.init_eqs)
    source_template.name = resolved_name
    source_template.block.name = resolved_name
    return source_template


class RampVoltageSourceEmtTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="phN", units="", descr="Whether neutral is active.", tpe=bool, value=False),
                TemplateProp(name="phA", units="", descr="Whether phase A is active.", tpe=bool, value=True),
                TemplateProp(name="phB", units="", descr="Whether phase B is active.", tpe=bool, value=False),
                TemplateProp(name="phC", units="", descr="Whether phase C is active.", tpe=bool, value=False),
                TemplateProp(name="initial_value", units="", descr="Value before the ramp.", tpe=float, value=0.0),
                TemplateProp(name="final_value", units="", descr="Value after the ramp.", tpe=float, value=1.0),
                TemplateProp(name="start_time_s", units="s", descr="Ramp start time in seconds.", tpe=float, value=0.01),
                TemplateProp(name="end_time_s", units="s", descr="Ramp end time in seconds.", tpe=float, value=0.03),
                TemplateProp(name="source_conductance_value", units="S", descr="Norton conductance.", tpe=float, value=100.0),
                TemplateProp(name="name", units="", descr="Symbolic block name.", tpe=str, value="ramp_voltage_source_emt"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        phN: bool = self.get_value("phN")
        phA: bool = self.get_value("phA")
        phB: bool = self.get_value("phB")
        phC: bool = self.get_value("phC")
        initial_value: float = self.get_value("initial_value")
        final_value: float = self.get_value("final_value")
        start_time_s: float = self.get_value("start_time_s")
        end_time_s: float = self.get_value("end_time_s")
        source_conductance_value: float = self.get_value("source_conductance_value")
        name: str | None = self.get_value("name")

        return get_ramp_voltage_source_emt_template(
            self.vf, phN, phA, phB, phC, initial_value, final_value,
            start_time_s, end_time_s, source_conductance_value, name,
        )


def get_ramp_voltage_source_emt_template(vf: VarFactory,
                                         phN: bool = False,
                                         phA: bool = True,
                                         phB: bool = False,
                                         phC: bool = False,
                                         initial_value: float = 0.0,
                                         final_value: float = 1.0,
                                         start_time_s: float = 0.01,
                                         end_time_s: float = 0.03,
                                         source_conductance_value: float = 100.0,
                                         name: str | None = "ramp_voltage_source_emt") -> EmtModelTemplate:
    """
    Build one phase-selective EMT ramp voltage source.
    """
    resolved_name: str = _build_source_template_name("ramp_voltage_source_emt", phN, phA, phB, phC, name)
    template = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name
    time_var: Var = _build_time_state(vf, template, resolved_name)
    initial_var: Var = vf.add_var(name=f"ramp_init")
    final_var: Var = vf.add_var(name=f"ramp_final")
    start_time_var: Var = vf.add_var(name=f"ramp_start")
    end_time_var: Var = vf.add_var(name=f"ramp_end")
    conductance_var: Var = vf.add_var(name=f"g_src")
    template.block.event_dict[initial_var] = vf.add_const(float(initial_value))
    template.block.event_dict[final_var] = vf.add_const(float(final_value))
    template.block.event_dict[start_time_var] = vf.add_const(float(start_time_s))
    template.block.event_dict[end_time_var] = vf.add_const(float(end_time_s))
    template.block.event_dict[conductance_var] = vf.add_const(float(source_conductance_value))
    waveform_expr: Expr = _build_ramp_expression(time_var, initial_var, final_var, start_time_var, end_time_var)
    source_template: EmtModelTemplate = _build_voltage_source_template_from_waveform(vf, phN, phA, phB, phC, waveform_expr, conductance_var, resolved_name)
    source_template.block.state_vars = template.block.state_vars
    source_template.block.diff_vars = template.block.diff_vars
    source_template.block.state_eqs = template.block.state_eqs
    source_template.block.event_dict.update(template.block.event_dict)
    source_template.block.init_eqs.update(template.block.init_eqs)
    source_template.name = resolved_name
    source_template.block.name = resolved_name
    return source_template


class DoubleExponentialCurrentSourceEmtTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="phN", units="", descr="Whether neutral is active.", tpe=bool, value=False),
                TemplateProp(name="phA", units="", descr="Whether phase A is active.", tpe=bool, value=True),
                TemplateProp(name="phB", units="", descr="Whether phase B is active.", tpe=bool, value=False),
                TemplateProp(name="phC", units="", descr="Whether phase C is active.", tpe=bool, value=False),
                TemplateProp(name="amplitude_value", units="", descr="Overall amplitude scale.", tpe=float, value=1.0),
                TemplateProp(name="alpha_value", units="", descr="Slow exponential coefficient.", tpe=float, value=100.0),
                TemplateProp(name="beta_value", units="", descr="Fast exponential coefficient.", tpe=float, value=5000.0),
                TemplateProp(name="delay_s", units="s", descr="Emission delay in seconds.", tpe=float, value=0.0),
                TemplateProp(name="name", units="", descr="Symbolic block name.", tpe=str, value="double_exponential_current_source_emt"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        phN: bool = self.get_value("phN")
        phA: bool = self.get_value("phA")
        phB: bool = self.get_value("phB")
        phC: bool = self.get_value("phC")
        amplitude_value: float = self.get_value("amplitude_value")
        alpha_value: float = self.get_value("alpha_value")
        beta_value: float = self.get_value("beta_value")
        delay_s: float = self.get_value("delay_s")
        name: str | None = self.get_value("name")

        return get_double_exponential_current_source_emt_template(
            self.vf, phN, phA, phB, phC, amplitude_value, alpha_value,
            beta_value, delay_s, name,
        )


def get_double_exponential_current_source_emt_template(vf: VarFactory,
                                                       phN: bool = False,
                                                       phA: bool = True,
                                                       phB: bool = False,
                                                       phC: bool = False,
                                                       amplitude_value: float = 1.0,
                                                       alpha_value: float = 100.0,
                                                       beta_value: float = 5000.0,
                                                       delay_s: float = 0.0,
                                                       name: str | None = "double_exponential_current_source_emt") -> EmtModelTemplate:
    """
    Build one phase-selective EMT double-exponential current source.
    """
    resolved_name: str = _build_source_template_name("double_exponential_current_source_emt", phN, phA, phB, phC, name)
    template = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name
    time_var: Var = _build_time_state(vf, template, resolved_name)
    amplitude_var: Var = vf.add_var(name=f"amp")
    alpha_var: Var = vf.add_var(name=f"alpha")
    beta_var: Var = vf.add_var(name=f"beta")
    delay_var: Var = vf.add_var(name=f"delay")
    template.block.event_dict[amplitude_var] = vf.add_const(float(amplitude_value))
    template.block.event_dict[alpha_var] = vf.add_const(float(alpha_value))
    template.block.event_dict[beta_var] = vf.add_const(float(beta_value))
    template.block.event_dict[delay_var] = vf.add_const(float(delay_s))
    waveform_expr: Expr = _build_double_exponential_expression(time_var, amplitude_var, alpha_var, beta_var, delay_var)
    source_template: EmtModelTemplate = _build_current_source_template_from_waveform(vf, phN, phA, phB, phC, waveform_expr, resolved_name)
    source_template.block.state_vars = template.block.state_vars
    source_template.block.diff_vars = template.block.diff_vars
    source_template.block.state_eqs = template.block.state_eqs
    source_template.block.event_dict.update(template.block.event_dict)
    source_template.block.init_eqs.update(template.block.init_eqs)
    source_template.name = resolved_name
    source_template.block.name = resolved_name
    return source_template


class HeidlerCurrentSourceEmtTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="phN", units="", descr="Whether neutral is active.", tpe=bool, value=False),
                TemplateProp(name="phA", units="", descr="Whether phase A is active.", tpe=bool, value=True),
                TemplateProp(name="phB", units="", descr="Whether phase B is active.", tpe=bool, value=False),
                TemplateProp(name="phC", units="", descr="Whether phase C is active.", tpe=bool, value=False),
                TemplateProp(name="peak_value", units="", descr="Peak-current scale.", tpe=float, value=1.0),
                TemplateProp(name="front_time_s", units="s", descr="Front-time parameter in seconds.", tpe=float, value=1.0e-4),
                TemplateProp(name="tail_time_s", units="s", descr="Tail-time parameter in seconds.", tpe=float, value=5.0e-4),
                TemplateProp(name="order_value", units="", descr="Heidler order exponent.", tpe=float, value=4.0),
                TemplateProp(name="delay_s", units="s", descr="Emission delay in seconds.", tpe=float, value=0.0),
                TemplateProp(name="name", units="", descr="Symbolic block name.", tpe=str, value="heidler_current_source_emt"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        phN: bool = self.get_value("phN")
        phA: bool = self.get_value("phA")
        phB: bool = self.get_value("phB")
        phC: bool = self.get_value("phC")
        peak_value: float = self.get_value("peak_value")
        front_time_s: float = self.get_value("front_time_s")
        tail_time_s: float = self.get_value("tail_time_s")
        order_value: float = self.get_value("order_value")
        delay_s: float = self.get_value("delay_s")
        name: str | None = self.get_value("name")

        return get_heidler_current_source_emt_template(
            self.vf, phN, phA, phB, phC, peak_value, front_time_s,
            tail_time_s, order_value, delay_s, name,
        )


def get_heidler_current_source_emt_template(vf: VarFactory,
                                            phN: bool = False,
                                            phA: bool = True,
                                            phB: bool = False,
                                            phC: bool = False,
                                            peak_value: float = 1.0,
                                            front_time_s: float = 1.0e-4,
                                            tail_time_s: float = 5.0e-4,
                                            order_value: float = 4.0,
                                            delay_s: float = 0.0,
                                            name: str | None = "heidler_current_source_emt") -> EmtModelTemplate:
    """
    Build one phase-selective EMT Heidler current source.
    """
    resolved_name: str = _build_source_template_name("heidler_current_source_emt", phN, phA, phB, phC, name)
    template = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name
    time_var: Var = _build_time_state(vf, template, resolved_name)
    peak_var: Var = vf.add_var(name=f"peak")
    front_time_var: Var = vf.add_var(name=f"front_time")
    tail_time_var: Var = vf.add_var(name=f"tail_time")
    order_var: Var = vf.add_var(name=f"order")
    delay_var: Var = vf.add_var(name=f"delay")
    template.block.event_dict[peak_var] = vf.add_const(float(peak_value))
    template.block.event_dict[front_time_var] = vf.add_const(float(front_time_s))
    template.block.event_dict[tail_time_var] = vf.add_const(float(tail_time_s))
    template.block.event_dict[order_var] = vf.add_const(float(order_value))
    template.block.event_dict[delay_var] = vf.add_const(float(delay_s))
    waveform_expr: Expr = _build_heidler_expression(time_var, peak_var, front_time_var, tail_time_var, order_var, delay_var)
    source_template: EmtModelTemplate = _build_current_source_template_from_waveform(vf, phN, phA, phB, phC, waveform_expr, resolved_name)
    source_template.block.state_vars = template.block.state_vars
    source_template.block.diff_vars = template.block.diff_vars
    source_template.block.state_eqs = template.block.state_eqs
    source_template.block.event_dict.update(template.block.event_dict)
    source_template.block.init_eqs.update(template.block.init_eqs)
    source_template.name = resolved_name
    source_template.block.name = resolved_name
    return source_template


class CigreSurgeCurrentSourceEmtTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="phN", units="", descr="Whether neutral is active.", tpe=bool, value=False),
                TemplateProp(name="phA", units="", descr="Whether phase A is active.", tpe=bool, value=True),
                TemplateProp(name="phB", units="", descr="Whether phase B is active.", tpe=bool, value=False),
                TemplateProp(name="phC", units="", descr="Whether phase C is active.", tpe=bool, value=False),
                TemplateProp(name="a_value", units="", descr="Front linear coefficient.", tpe=float, value=1000.0),
                TemplateProp(name="b_value", units="", descr="Front nonlinear coefficient.", tpe=float, value=10000.0),
                TemplateProp(name="n_value", units="", descr="Front exponent.", tpe=float, value=2.0),
                TemplateProp(name="tn_s", units="s", descr="Front-to-tail transition time in seconds.", tpe=float, value=1.0e-4),
                TemplateProp(name="i1_value", units="", descr="First tail amplitude.", tpe=float, value=1.0),
                TemplateProp(name="t1_s", units="s", descr="First tail time constant in seconds.", tpe=float, value=5.0e-4),
                TemplateProp(name="i2_value", units="", descr="Second tail amplitude.", tpe=float, value=0.5),
                TemplateProp(name="t2_s", units="s", descr="Second tail time constant in seconds.", tpe=float, value=2.0e-4),
                TemplateProp(name="delay_s", units="s", descr="Emission delay in seconds.", tpe=float, value=0.0),
                TemplateProp(name="name", units="", descr="Symbolic block name.", tpe=str, value="cigre_surge_current_source_emt"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        phN: bool = self.get_value("phN")
        phA: bool = self.get_value("phA")
        phB: bool = self.get_value("phB")
        phC: bool = self.get_value("phC")
        a_value: float = self.get_value("a_value")
        b_value: float = self.get_value("b_value")
        n_value: float = self.get_value("n_value")
        tn_s: float = self.get_value("tn_s")
        i1_value: float = self.get_value("i1_value")
        t1_s: float = self.get_value("t1_s")
        i2_value: float = self.get_value("i2_value")
        t2_s: float = self.get_value("t2_s")
        delay_s: float = self.get_value("delay_s")
        name: str | None = self.get_value("name")

        return get_cigre_surge_current_source_emt_template(
            self.vf, phN, phA, phB, phC, a_value, b_value, n_value,
            tn_s, i1_value, t1_s, i2_value, t2_s, delay_s, name,
        )


def get_cigre_surge_current_source_emt_template(vf: VarFactory,
                                                phN: bool = False,
                                                phA: bool = True,
                                                phB: bool = False,
                                                phC: bool = False,
                                                a_value: float = 1000.0,
                                                b_value: float = 10000.0,
                                                n_value: float = 2.0,
                                                tn_s: float = 1.0e-4,
                                                i1_value: float = 1.0,
                                                t1_s: float = 5.0e-4,
                                                i2_value: float = 0.5,
                                                t2_s: float = 2.0e-4,
                                                delay_s: float = 0.0,
                                                name: str | None = "cigre_surge_current_source_emt") -> EmtModelTemplate:
    """
    Build one phase-selective EMT CIGRE surge current source.
    """
    resolved_name: str = _build_source_template_name("cigre_surge_current_source_emt", phN, phA, phB, phC, name)
    template = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name
    time_var: Var = _build_time_state(vf, template, resolved_name)
    a_var: Var = vf.add_var(name=f"a")
    b_var: Var = vf.add_var(name=f"b")
    n_var: Var = vf.add_var(name=f"n")
    tn_var: Var = vf.add_var(name=f"tn")
    i1_var: Var = vf.add_var(name=f"i1")
    t1_var: Var = vf.add_var(name=f"t1")
    i2_var: Var = vf.add_var(name=f"i2")
    t2_var: Var = vf.add_var(name=f"t2")
    delay_var: Var = vf.add_var(name=f"delay")
    template.block.event_dict[a_var] = vf.add_const(float(a_value))
    template.block.event_dict[b_var] = vf.add_const(float(b_value))
    template.block.event_dict[n_var] = vf.add_const(float(n_value))
    template.block.event_dict[tn_var] = vf.add_const(float(tn_s))
    template.block.event_dict[i1_var] = vf.add_const(float(i1_value))
    template.block.event_dict[t1_var] = vf.add_const(float(t1_s))
    template.block.event_dict[i2_var] = vf.add_const(float(i2_value))
    template.block.event_dict[t2_var] = vf.add_const(float(t2_s))
    template.block.event_dict[delay_var] = vf.add_const(float(delay_s))
    waveform_expr: Expr = _build_cigre_expression(time_var, a_var, b_var, n_var, tn_var, i1_var, t1_var, i2_var, t2_var, delay_var)
    source_template: EmtModelTemplate = _build_current_source_template_from_waveform(vf, phN, phA, phB, phC, waveform_expr, resolved_name)
    source_template.block.state_vars = template.block.state_vars
    source_template.block.diff_vars = template.block.diff_vars
    source_template.block.state_eqs = template.block.state_eqs
    source_template.block.event_dict.update(template.block.event_dict)
    source_template.block.init_eqs.update(template.block.init_eqs)
    source_template.name = resolved_name
    source_template.block.name = resolved_name
    return source_template
