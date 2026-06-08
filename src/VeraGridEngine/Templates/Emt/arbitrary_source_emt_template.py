# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, List, Sequence

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import _get_phase_count_name
from VeraGridEngine.Utils.Symbolic.block import Expr, Var
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp
from VeraGridEngine.Utils.Symbolic.symbolic import Comparison
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


def _get_active_nabc_labels(phN: bool, phA: bool, phB: bool, phC: bool) -> List[str]:
    active_labels: List[str] = list()

    if phN:
        active_labels.append("N")
    if phA:
        active_labels.append("A")
    if phB:
        active_labels.append("B")
    if phC:
        active_labels.append("C")

    if active_labels:
        return active_labels
    else:
        raise ValueError("At least one source terminal must be enabled for an arbitrary EMT source template")


def _get_voltage_reference(phase_label: str) -> VarPowerFlowReferenceType:
    if phase_label == "N":
        return VarPowerFlowReferenceType.v_N
    elif phase_label == "A":
        return VarPowerFlowReferenceType.v_A
    elif phase_label == "B":
        return VarPowerFlowReferenceType.v_B
    elif phase_label == "C":
        return VarPowerFlowReferenceType.v_C
    else:
        raise ValueError(f"Unsupported source phase label '{phase_label}'")


def _get_current_reference(phase_label: str) -> VarPowerFlowReferenceType:
    if phase_label == "N":
        return VarPowerFlowReferenceType.i_N
    elif phase_label == "A":
        return VarPowerFlowReferenceType.i_A
    elif phase_label == "B":
        return VarPowerFlowReferenceType.i_B
    elif phase_label == "C":
        return VarPowerFlowReferenceType.i_C
    else:
        raise ValueError(f"Unsupported source phase label '{phase_label}'")


def _build_external_mapping(voltage_vars: Dict[str, Var], current_vars: Dict[str, Var]) -> Dict[VarPowerFlowReferenceType, Var | None]:
    return dict({
        VarPowerFlowReferenceType.v_N: voltage_vars.get("N", None),
        VarPowerFlowReferenceType.v_A: voltage_vars.get("A", None),
        VarPowerFlowReferenceType.v_B: voltage_vars.get("B", None),
        VarPowerFlowReferenceType.v_C: voltage_vars.get("C", None),
        VarPowerFlowReferenceType.i_N: current_vars.get("N", None),
        VarPowerFlowReferenceType.i_A: current_vars.get("A", None),
        VarPowerFlowReferenceType.i_B: current_vars.get("B", None),
        VarPowerFlowReferenceType.i_C: current_vars.get("C", None),
    })


def _build_template_name(base_name: str,
                         phN: bool,
                         phA: bool,
                         phB: bool,
                         phC: bool,
                         requested_name: str | None) -> str:
    phase_count: int = int(phN) + int(phA) + int(phB) + int(phC)
    return _get_phase_count_name(base_name=base_name, phase_count=phase_count, requested_name=requested_name)


def _build_lookup_comparison(lhs: Expr, op: CmpOp, rhs: Expr) -> Expr:
    return Comparison(lhs=lhs, op=op, rhs=rhs).to_expression()


def _build_segment_expression(coord_var: Var,
                              x_left_var: Var,
                              x_right_var: Var,
                              y_left_var: Var,
                              y_right_var: Var) -> Expr:
    slope_expr: Expr = (y_right_var - y_left_var) / (x_right_var - x_left_var)
    intercept_expr: Expr = y_left_var - slope_expr * x_left_var
    return slope_expr * coord_var + intercept_expr


def _validate_waveform_points(time_points: Sequence[float], value_points: Sequence[float]) -> None:
    point_count: int = len(time_points)
    point_index: int

    if point_count == len(value_points):
        pass
    else:
        raise ValueError("Arbitrary source time/value vectors must have the same size")

    if point_count >= 2:
        pass
    else:
        raise ValueError("Arbitrary source waveform requires at least two points")

    for point_index in range(point_count - 1):
        if float(time_points[point_index + 1]) > float(time_points[point_index]):
            pass
        else:
            raise ValueError("Arbitrary source waveform times must be strictly increasing")


def _build_clipped_lookup_expression(coord_var: Var, x_vars: Sequence[Var], y_vars: Sequence[Var]) -> Expr:
    point_count: int = len(x_vars)
    result_expr: Expr = y_vars[0] * _build_lookup_comparison(coord_var, CmpOp.LT, x_vars[0])
    segment_index: int

    for segment_index in range(point_count - 1):
        segment_expr: Expr = _build_segment_expression(
            coord_var=coord_var,
            x_left_var=x_vars[segment_index],
            x_right_var=x_vars[segment_index + 1],
            y_left_var=y_vars[segment_index],
            y_right_var=y_vars[segment_index + 1],
        )
        lower_expr: Expr = _build_lookup_comparison(coord_var, CmpOp.GE, x_vars[segment_index])
        upper_expr: Expr = _build_lookup_comparison(coord_var, CmpOp.LT, x_vars[segment_index + 1])
        result_expr = result_expr + segment_expr * lower_expr * upper_expr

    result_expr = result_expr + y_vars[point_count - 1] * _build_lookup_comparison(coord_var, CmpOp.GE, x_vars[point_count - 1])
    return result_expr


def _build_waveform_parameters(vf: VarFactory,
                               template: EmtModelTemplate,
                               time_points: Sequence[float],
                               value_points: Sequence[float],
                               name: str) -> tuple[list[Var], list[Var]]:
    x_vars: list[Var] = list()
    y_vars: list[Var] = list()
    point_index: int
    parameter_var: Var

    _validate_waveform_points(time_points, value_points)

    for point_index in range(len(time_points)):
        parameter_var = vf.add_var(f"arr_x{point_index + 1}_{name}")
        template.block.event_dict[parameter_var] = vf.add_const(float(time_points[point_index]), name=f"arr_x{point_index + 1}")
        x_vars.append(parameter_var)

        parameter_var = vf.add_var(f"arr_y{point_index + 1}_{name}")
        template.block.event_dict[parameter_var] = vf.add_const(float(value_points[point_index]), name=f"arr_y{point_index + 1}")
        y_vars.append(parameter_var)

    return x_vars, y_vars


def get_arbitrary_waveform_current_source_emt_template(vf: VarFactory,
                                                       phN: bool = False,
                                                       phA: bool = True,
                                                       phB: bool = False,
                                                       phC: bool = False,
                                                       time_points: Sequence[float] = (0.0, 0.02, 0.04),
                                                       value_points: Sequence[float] = (0.0, 1.0, 0.0),
                                                       name: str | None = "arbitrary_waveform_current_source_emt") -> EmtModelTemplate:
    """
    Build one phase-selective EMT current source driven by one arbitrary time waveform.

    The same time/value waveform is applied to every active phase.
    
    :param vf: EMT variable factory.
    :param phN: Whether neutral is active.
    :param phA: Whether phase A is active.
    :param phB: Whether phase B is active.
    :param phC: Whether phase C is active.
    :param time_points: Strictly increasing waveform times in seconds.
    :param value_points: Matching waveform values.
    :param name: Optional symbolic block name.
    :return: Configured EMT template.
    """
    active_labels: List[str] = _get_active_nabc_labels(phN=phN, phA=phA, phB=phB, phC=phC)
    resolved_name: str = _build_template_name("arbitrary_waveform_current_source_emt", phN, phA, phB, phC, name)
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name

    tau_var: Var = vf.add_var(name=f"t_src_{resolved_name}")
    d_tau_var: Var = vf.add_diff_var(name=f"d_t_src_{resolved_name}", base_var=tau_var)
    x_vars, y_vars = _build_waveform_parameters(vf=vf, template=template, time_points=time_points, value_points=value_points, name=resolved_name)
    waveform_expr: Expr = _build_clipped_lookup_expression(coord_var=tau_var, x_vars=x_vars, y_vars=y_vars)

    voltage_vars: Dict[str, Var] = dict()
    current_vars: Dict[str, Var] = dict()
    in_vars: List[Var] = list()
    algebraic_vars: List[Var] = list()
    algebraic_eqs: List[Expr] = list()
    out_vars: List[Var] = list()
    phase_label: str

    for phase_label in active_labels:
        voltage_var: Var = vf.add_var(name=f"v_{phase_label}_{resolved_name}", reference=_get_voltage_reference(phase_label))
        current_var: Var = vf.add_var(name=f"i_{phase_label}_{resolved_name}", reference=_get_current_reference(phase_label))
        voltage_vars[phase_label] = voltage_var
        current_vars[phase_label] = current_var
        in_vars.append(voltage_var)
        algebraic_vars.append(current_var)
        algebraic_eqs.append(current_var - waveform_expr)
        out_vars.append(current_var)
        template.block.init_eqs[current_var] = y_vars[0]

    template.block.in_vars = in_vars
    template.block.state_vars = [tau_var]
    template.block.diff_vars = [d_tau_var]
    template.block.state_eqs = [sym.Const(1.0)]
    template.block.algebraic_vars = algebraic_vars
    template.block.algebraic_eqs = algebraic_eqs
    template.block.out_vars = out_vars
    template.block.external_mapping = _build_external_mapping(voltage_vars, current_vars)
    template.block.init_eqs[tau_var] = x_vars[0]
    return template


def get_arbitrary_waveform_voltage_source_emt_template(vf: VarFactory,
                                                       phN: bool = False,
                                                       phA: bool = True,
                                                       phB: bool = False,
                                                       phC: bool = False,
                                                       time_points: Sequence[float] = (0.0, 0.02, 0.04),
                                                       value_points: Sequence[float] = (0.0, 1.0, 0.0),
                                                       source_conductance_value: float = 100.0,
                                                       name: str | None = "arbitrary_waveform_voltage_source_emt") -> EmtModelTemplate:
    """
    Build one phase-selective EMT voltage source driven by one arbitrary time waveform.

    The same time/value waveform is applied to every active phase and injected as
    one Norton equivalent ``i = g * (v_src - v_bus)``.

    :param vf: EMT variable factory.
    :param phN: Whether neutral is active.
    :param phA: Whether phase A is active.
    :param phB: Whether phase B is active.
    :param phC: Whether phase C is active.
    :param time_points: Strictly increasing waveform times in seconds.
    :param value_points: Matching waveform values.
    :param source_conductance_value: Norton conductance.
    :param name: Optional symbolic block name.
    :return: Configured EMT template.
    """
    active_labels: List[str] = _get_active_nabc_labels(phN=phN, phA=phA, phB=phB, phC=phC)
    resolved_name: str = _build_template_name("arbitrary_waveform_voltage_source_emt", phN, phA, phB, phC, name)
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = resolved_name
    template.block.name = resolved_name

    tau_var: Var = vf.add_var(name=f"t_src_{resolved_name}")
    d_tau_var: Var = vf.add_diff_var(name=f"d_t_src_{resolved_name}", base_var=tau_var)
    conductance_var: Var = vf.add_var(name=f"g_src_{resolved_name}")
    template.block.event_dict[conductance_var] = vf.add_const(float(source_conductance_value))
    x_vars, y_vars = _build_waveform_parameters(vf=vf, template=template, time_points=time_points, value_points=value_points, name=resolved_name)
    waveform_expr: Expr = _build_clipped_lookup_expression(coord_var=tau_var, x_vars=x_vars, y_vars=y_vars)

    voltage_vars: Dict[str, Var] = dict()
    current_vars: Dict[str, Var] = dict()
    in_vars: List[Var] = list()
    algebraic_vars: List[Var] = list()
    algebraic_eqs: List[Expr] = list()
    out_vars: List[Var] = list()
    phase_label: str

    for phase_label in active_labels:
        voltage_var: Var = vf.add_var(name=f"v_{phase_label}_{resolved_name}", reference=_get_voltage_reference(phase_label))
        current_var: Var = vf.add_var(name=f"i_{phase_label}_{resolved_name}", reference=_get_current_reference(phase_label))
        voltage_vars[phase_label] = voltage_var
        current_vars[phase_label] = current_var
        in_vars.append(voltage_var)
        algebraic_vars.append(current_var)
        algebraic_eqs.append(current_var - conductance_var * (waveform_expr - voltage_var))
        out_vars.append(current_var)
        template.block.init_eqs[current_var] = conductance_var * (y_vars[0] - voltage_var)

    template.block.in_vars = in_vars
    template.block.state_vars = [tau_var]
    template.block.diff_vars = [d_tau_var]
    template.block.state_eqs = [sym.Const(1.0)]
    template.block.algebraic_vars = algebraic_vars
    template.block.algebraic_eqs = algebraic_eqs
    template.block.out_vars = out_vars
    template.block.external_mapping = _build_external_mapping(voltage_vars, current_vars)
    template.block.init_eqs[tau_var] = x_vars[0]
    return template
