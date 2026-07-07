from __future__ import annotations

from typing import Sequence

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import _build_unclipped_lookup_expression
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import _validate_lookup_points
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import _attach_combo_editor_diagram
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import _build_external_mapping
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_ground_emt_template
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp, Comparison, Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


def get_nonlinear_resistor_emt_template(
    vf: VarFactory,
    voltage_points: Sequence[float],
    current_points: Sequence[float],
    name: str = "nonlinear_resistor_emt",
) -> EmtModelTemplate:
    """Build one ATP-like one-terminal nonlinear resistor EMT block.

    The block uses an odd-symmetric piecewise-linear `|v| -> |i|` curve and
    grounds the opposite terminal internally.

    :param vf: EMT variable factory.
    :param voltage_points: Non-negative voltage magnitudes.
    :param current_points: Matching current magnitudes.
    :param name: Symbolic block name.
    :return: Materialized EMT template.
    """
    _validate_lookup_points(x_points=voltage_points, y_points=current_points)

    if float(voltage_points[0]) == 0.0 and float(current_points[0]) == 0.0:
        pass
    else:
        raise ValueError("Nonlinear resistor EMT requires the first V-I point to be (0, 0)")

    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.LoadDevice
    template.name = name
    template.block.name = name

    node_voltage_var: Var = vf.add_var(name=f"v_N", reference=VarPowerFlowReferenceType.v_N)
    current_var: Var = vf.add_var(name=f"i_N", reference=VarPowerFlowReferenceType.i_N)
    ground_node_var: Var = vf.add_var(name=f"v_gnd")
    abs_voltage_var: Var = vf.add_var(name=f"v_abs")
    one_const: Const = Const(1.0)
    zero_const: Const = Const(0.0)

    ground_template: EmtModelTemplate = get_ground_emt_template(vf=vf, name=name + "_ground")
    vf.add_connections(ground_template.block.in_vars, [ground_node_var])
    ground_current_var: Var = ground_template.block.out_vars[0]

    voltage_drop: Expr = node_voltage_var - ground_node_var
    sign_selector: Expr = Comparison(lhs=voltage_drop, op=CmpOp.GE, rhs=zero_const).to_expression()
    x_vars: list[Var] = list()
    y_vars: list[Var] = list()
    point_index: int

    for point_index in range(len(voltage_points)):
        x_var = vf.add_var(name=f"arr_v{point_index + 1}")
        y_var = vf.add_var(name=f"arr_i{point_index + 1}")
        template.block.event_dict[x_var] = vf.add_const(float(voltage_points[point_index]), name=f"arr_v{point_index + 1}")
        template.block.event_dict[y_var] = vf.add_const(float(current_points[point_index]), name=f"arr_i{point_index + 1}")
        x_vars.append(x_var)
        y_vars.append(y_var)

    magnitude_expr: Expr = _build_unclipped_lookup_expression(yi_var=abs_voltage_var, x_vars=x_vars, y_vars=y_vars)
    signed_current_expr: Expr = magnitude_expr * (sign_selector - (one_const - sign_selector))

    template.block.in_vars = [node_voltage_var]
    template.block.out_vars = [current_var]
    template.block.algebraic_vars = [ground_node_var, abs_voltage_var, current_var]
    template.block.init_eqs[ground_node_var] = zero_const
    template.block.init_eqs[abs_voltage_var] = sym.abs(voltage_drop)
    template.block.init_eqs[current_var] = signed_current_expr
    template.block.algebraic_eqs = [
        abs_voltage_var - sym.abs(voltage_drop),
        current_var - signed_current_expr,
        ground_current_var + current_var,
    ]
    template.block.add(ground_template.block)
    template.block.external_mapping = _build_external_mapping(
        voltage_vars=dict(),
        current_vars=dict(),
        neutral_voltage_var=node_voltage_var,
        neutral_current_var=current_var,
    )
    _attach_combo_editor_diagram(
        root_block=template.block,
        input_vars=[node_voltage_var],
        output_vars=[current_var],
        ground_block=ground_template.block,
        neutral_input_var=node_voltage_var,
    )
    return template
