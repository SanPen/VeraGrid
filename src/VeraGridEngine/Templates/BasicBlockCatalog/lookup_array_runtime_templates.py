# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from functools import lru_cache
from typing import Sequence

import numpy as np

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Comparison
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType


def _build_lookup_comparison(lhs: Expr, op: CmpOp, rhs: Expr) -> Expr:
    """
    Build one boolean-like expression used to activate a lookup segment.

    :param lhs: Left-hand side expression.
    :param op: Comparison operator.
    :param rhs: Right-hand side expression.
    :return: Symbolic 0/1 expression.
    """
    comparison: Comparison = Comparison(lhs=lhs, op=op, rhs=rhs)
    return comparison.to_expression()


def _build_interval_selector(value_expr: Expr, lower_var: Var, upper_var: Var | None) -> Expr:
    """
    Build the activation selector for one lookup interval.

    :param value_expr: Evaluated lookup coordinate.
    :param lower_var: Lower interval bound.
    :param upper_var: Optional exclusive upper interval bound.
    :return: Symbolic 0/1 selector.
    """
    lower_expr: Expr = _build_lookup_comparison(value_expr, CmpOp.GE, lower_var)

    if upper_var is None:
        return lower_expr
    else:
        upper_expr: Expr = _build_lookup_comparison(value_expr, CmpOp.LT, upper_var)
        return lower_expr * upper_expr


def _validate_lookup_points(x_points: Sequence[float], y_points: Sequence[float]) -> None:
    """
    Validate one one-dimensional lookup table before building its symbolic block.

    :param x_points: Monotonic abscissa values.
    :param y_points: Ordinated values.
    :return: None.
    :raises ValueError: If the lookup table is not valid.
    """
    point_count: int = len(x_points)
    point_index: int

    if point_count != len(y_points):
        raise ValueError("Lookup table x/y vectors must have the same size")
    else:
        pass

    if point_count < 2:
        raise ValueError("Lookup table requires at least two points")
    else:
        pass

    for point_index in range(point_count - 1):
        if float(x_points[point_index + 1]) > float(x_points[point_index]):
            pass
        else:
            raise ValueError("Lookup table x values must be strictly increasing")


def _normalize_inverse_lookup_points(x_points: Sequence[float], y_points: Sequence[float]) -> tuple[list[float], list[float]]:
    """
    Normalize one inverse lookup table so the driven axis is strictly increasing.

    :param x_points: Original x values.
    :param y_points: Original y values to be inverted.
    :return: Normalized `(x_points, y_points)` where `y_points` are increasing.
    :raises ValueError: If the inverse lookup is not strictly monotonic.
    """
    point_count: int = len(x_points)
    point_index: int
    is_increasing: bool = True
    is_decreasing: bool = True

    if point_count != len(y_points):
        raise ValueError("Inverse lookup x/y vectors must have the same size")
    else:
        pass

    if point_count < 2:
        raise ValueError("Inverse lookup requires at least two points")
    else:
        pass

    for point_index in range(point_count - 1):
        if float(y_points[point_index + 1]) > float(y_points[point_index]):
            is_decreasing = False
        else:
            if float(y_points[point_index + 1]) < float(y_points[point_index]):
                is_increasing = False
            else:
                raise ValueError("Inverse lookup requires strictly monotonic y values")

    if is_increasing:
        return list(float(item) for item in x_points), list(float(item) for item in y_points)
    else:
        if is_decreasing:
            return list(float(item) for item in reversed(x_points)), list(float(item) for item in reversed(y_points))
        else:
            raise ValueError("Inverse lookup requires y values to be strictly monotonic")


def _validate_lookup_matrix(x_points: Sequence[float], y_points: Sequence[float], z_matrix: Sequence[Sequence[float]]) -> None:
    """
    Validate one bilinear lookup matrix before building its symbolic block.

    :param x_points: Strictly increasing x-axis values.
    :param y_points: Strictly increasing y-axis values.
    :param z_matrix: Matrix values indexed as `[y][x]`.
    :return: None.
    :raises ValueError: If the lookup matrix is not valid.
    """
    row_index: int

    _validate_lookup_points(x_points=x_points, y_points=x_points)
    _validate_lookup_points(x_points=y_points, y_points=y_points)

    if len(z_matrix) == len(y_points):
        pass
    else:
        raise ValueError("Lookup matrix row count must match the y-axis size")

    for row_index in range(len(z_matrix)):
        if len(z_matrix[row_index]) == len(x_points):
            pass
        else:
            raise ValueError("Lookup matrix column count must match the x-axis size")


def _build_linear_combination(sample_values: Sequence[Expr], weights: Sequence[float]) -> Expr:
    """
    Build one linear combination of symbolic sample values.

    :param sample_values: Symbolic sample values.
    :param weights: Numeric weights.
    :return: Linear-combination expression.
    """
    result_expr: Expr = Const(0.0)
    sample_index: int

    for sample_index in range(len(sample_values)):
        result_expr = result_expr + sample_values[sample_index] * Const(float(weights[sample_index]))

    return result_expr


def _solve_natural_cubic_second_derivatives(axis_points: Sequence[float], sample_values: np.ndarray) -> np.ndarray:
    """
    Solve the natural cubic spline second derivatives for one numeric surface.

    :param axis_points: Strictly increasing axis values.
    :param sample_values: Numeric sample values on that axis.
    :return: Numeric second-derivative vector.
    """
    point_count: int = len(axis_points)
    second_derivatives: np.ndarray = np.zeros(point_count, dtype=float)
    equation_count: int = point_count - 2
    h_values: np.ndarray = np.diff(np.asarray(axis_points, dtype=float))
    row_index: int

    if point_count <= 2:
        return second_derivatives
    else:
        pass

    matrix_a: np.ndarray = np.zeros((equation_count, equation_count), dtype=float)
    rhs_vector: np.ndarray = np.zeros(equation_count, dtype=float)

    for row_index in range(equation_count):
        if row_index > 0:
            matrix_a[row_index, row_index - 1] = h_values[row_index]
        else:
            pass

        matrix_a[row_index, row_index] = 2.0 * (h_values[row_index] + h_values[row_index + 1])

        if row_index < equation_count - 1:
            matrix_a[row_index, row_index + 1] = h_values[row_index + 1]
        else:
            pass

        rhs_vector[row_index] = 6.0 * (
            (sample_values[row_index + 2] - sample_values[row_index + 1]) / h_values[row_index + 1]
            - (sample_values[row_index + 1] - sample_values[row_index]) / h_values[row_index]
        )

    second_derivatives[1:point_count - 1] = np.linalg.solve(matrix_a, rhs_vector)
    return second_derivatives


@lru_cache(maxsize=32)
def _compute_natural_cubic_segment_weights(axis_points_key: tuple[float, ...]) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], ...]:
    """
    Return linear weights for every natural-cubic spline segment coefficient.

    :param axis_points_key: Hashable axis-point tuple.
    :return: Per-segment coefficient weights `(a, b, c, d)`.
    """
    axis_points: tuple[float, ...] = axis_points_key
    point_count: int = len(axis_points)
    segment_count: int = point_count - 1
    weights_by_segment: list[list[np.ndarray]] = list()
    segment_index: int
    basis_index: int

    for segment_index in range(segment_count):
        weights_by_segment.append(
            list([
                np.zeros(point_count, dtype=float),
                np.zeros(point_count, dtype=float),
                np.zeros(point_count, dtype=float),
                np.zeros(point_count, dtype=float),
            ])
        )

    for basis_index in range(point_count):
        basis_values: np.ndarray = np.zeros(point_count, dtype=float)
        basis_values[basis_index] = 1.0
        second_derivatives: np.ndarray = _solve_natural_cubic_second_derivatives(axis_points, basis_values)

        for segment_index in range(segment_count):
            h_value: float = float(axis_points[segment_index + 1] - axis_points[segment_index])
            a_value: float = float(basis_values[segment_index])
            b_value: float = float(
                (basis_values[segment_index + 1] - basis_values[segment_index]) / h_value
                - h_value * (2.0 * second_derivatives[segment_index] + second_derivatives[segment_index + 1]) / 6.0
            )
            c_value: float = float(second_derivatives[segment_index] / 2.0)
            d_value: float = float((second_derivatives[segment_index + 1] - second_derivatives[segment_index]) / (6.0 * h_value))
            weights_by_segment[segment_index][0][basis_index] = a_value
            weights_by_segment[segment_index][1][basis_index] = b_value
            weights_by_segment[segment_index][2][basis_index] = c_value
            weights_by_segment[segment_index][3][basis_index] = d_value

    output_segments: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = list()
    for segment_index in range(segment_count):
        output_segments.append(
            (
                weights_by_segment[segment_index][0],
                weights_by_segment[segment_index][1],
                weights_by_segment[segment_index][2],
                weights_by_segment[segment_index][3],
            )
        )

    return tuple(output_segments)


def _build_cubic_spline_piecewise_expression(
    coord_expr: Expr,
    axis_points: Sequence[float],
    axis_vars: Sequence[Var],
    sample_values: Sequence[Expr],
) -> Expr:
    """
    Build the clipped natural cubic spline expression for one axis.

    :param coord_expr: Lookup coordinate.
    :param axis_points: Strictly increasing numeric axis values.
    :param axis_vars: Strictly increasing symbolic axis variables.
    :param sample_values: Symbolic sample values aligned with the axis.
    :return: Piecewise cubic spline expression.
    """
    point_count: int = len(axis_vars)
    segment_count: int = point_count - 1
    result_expr: Expr = sample_values[0] * _build_lookup_comparison(coord_expr, CmpOp.LT, axis_vars[0])
    segment_index: int
    segment_weights = _compute_natural_cubic_segment_weights(tuple(float(value) for value in axis_points))

    for segment_index in range(segment_count):
        a_weights, b_weights, c_weights, d_weights = segment_weights[segment_index]
        dx_expr: Expr = coord_expr - axis_vars[segment_index]
        segment_expr: Expr = _build_linear_combination(sample_values, a_weights)
        segment_expr = segment_expr + _build_linear_combination(sample_values, b_weights) * dx_expr
        segment_expr = segment_expr + _build_linear_combination(sample_values, c_weights) * dx_expr * dx_expr
        segment_expr = segment_expr + _build_linear_combination(sample_values, d_weights) * dx_expr * dx_expr * dx_expr

        if segment_index == segment_count - 1:
            upper_axis_var: Var | None = None
        else:
            upper_axis_var = axis_vars[segment_index + 1]

        selector_expr: Expr = _build_interval_selector(coord_expr, axis_vars[segment_index], upper_axis_var)
        result_expr = result_expr + segment_expr * selector_expr

    return result_expr


def _build_segment_expression(
    yi_var: Var,
    x_left_var: Var,
    x_right_var: Var,
    y_left_var: Var,
    y_right_var: Var,
) -> Expr:
    """
    Build one affine interpolation expression between two lookup points.

    :param yi_var: Lookup input variable.
    :param x_left_var: Segment left x value.
    :param x_right_var: Segment right x value.
    :param y_left_var: Segment left y value.
    :param y_right_var: Segment right y value.
    :return: Interpolation expression valid on that segment.
    """
    slope_expr: Expr = (y_right_var - y_left_var) / (x_right_var - x_left_var)
    intercept_expr: Expr = y_left_var - slope_expr * x_left_var
    return slope_expr * yi_var + intercept_expr


def _build_clipped_lookup_expression(yi_var: Var, x_vars: Sequence[Var], y_vars: Sequence[Var]) -> Expr:
    """
    Build the clipped lookup expression for one strictly increasing table.

    :param yi_var: Lookup input variable.
    :param x_vars: Symbolic x-point parameters.
    :param y_vars: Symbolic y-point parameters.
    :return: Piecewise clipped interpolation expression.
    """
    point_count: int = len(x_vars)
    segment_index: int
    result_expr: Expr = y_vars[0] * _build_lookup_comparison(yi_var, CmpOp.LT, x_vars[0])

    for segment_index in range(point_count - 1):
        segment_expr: Expr = _build_segment_expression(
            yi_var=yi_var,
            x_left_var=x_vars[segment_index],
            x_right_var=x_vars[segment_index + 1],
            y_left_var=y_vars[segment_index],
            y_right_var=y_vars[segment_index + 1],
        )

        lower_expr: Expr = _build_lookup_comparison(yi_var, CmpOp.GE, x_vars[segment_index])
        upper_expr: Expr = _build_lookup_comparison(yi_var, CmpOp.LT, x_vars[segment_index + 1])
        result_expr = result_expr + segment_expr * lower_expr * upper_expr

    result_expr = result_expr + y_vars[point_count - 1] * _build_lookup_comparison(
        yi_var,
        CmpOp.GE,
        x_vars[point_count - 1],
    )
    return result_expr


def _build_unclipped_lookup_expression(yi_var: Var, x_vars: Sequence[Var], y_vars: Sequence[Var]) -> Expr:
    """
    Build the non-clipped lookup expression with linear extrapolation.

    :param yi_var: Lookup input variable.
    :param x_vars: Symbolic x-point parameters.
    :param y_vars: Symbolic y-point parameters.
    :return: Piecewise interpolation plus linear extrapolation expression.
    """
    point_count: int = len(x_vars)
    first_segment_expr: Expr = _build_segment_expression(
        yi_var=yi_var,
        x_left_var=x_vars[0],
        x_right_var=x_vars[1],
        y_left_var=y_vars[0],
        y_right_var=y_vars[1],
    )

    if point_count == 2:
        return first_segment_expr
    else:
        pass

    last_segment_expr: Expr = _build_segment_expression(
        yi_var=yi_var,
        x_left_var=x_vars[point_count - 2],
        x_right_var=x_vars[point_count - 1],
        y_left_var=y_vars[point_count - 2],
        y_right_var=y_vars[point_count - 1],
    )
    segment_index: int
    result_expr: Expr = first_segment_expr * _build_lookup_comparison(yi_var, CmpOp.LT, x_vars[1])

    for segment_index in range(1, point_count - 2):
        segment_expr: Expr = _build_segment_expression(
            yi_var=yi_var,
            x_left_var=x_vars[segment_index],
            x_right_var=x_vars[segment_index + 1],
            y_left_var=y_vars[segment_index],
            y_right_var=y_vars[segment_index + 1],
        )
        lower_expr: Expr = _build_lookup_comparison(yi_var, CmpOp.GE, x_vars[segment_index])
        upper_expr: Expr = _build_lookup_comparison(yi_var, CmpOp.LT, x_vars[segment_index + 1])
        result_expr = result_expr + segment_expr * lower_expr * upper_expr

    result_expr = result_expr + last_segment_expr * _build_lookup_comparison(
        yi_var,
        CmpOp.GE,
        x_vars[point_count - 2],
    )
    return result_expr


def _build_bilinear_cell_expression(
    x_expr: Expr,
    y_expr: Expr,
    x_left_var: Var,
    x_right_var: Var,
    y_lower_var: Var,
    y_upper_var: Var,
    z00_var: Var,
    z10_var: Var,
    z01_var: Var,
    z11_var: Var,
) -> Expr:
    """
    Build one bilinear interpolation expression on a single rectangular cell.

    :param x_expr: Clipped x lookup coordinate.
    :param y_expr: Clipped y lookup coordinate.
    :param x_left_var: Left x bound.
    :param x_right_var: Right x bound.
    :param y_lower_var: Lower y bound.
    :param y_upper_var: Upper y bound.
    :param z00_var: Cell value at `(x_left, y_lower)`.
    :param z10_var: Cell value at `(x_right, y_lower)`.
    :param z01_var: Cell value at `(x_left, y_upper)`.
    :param z11_var: Cell value at `(x_right, y_upper)`.
    :return: Bilinear interpolation expression.
    """
    one_const: Const = Const(1.0)
    tx_expr: Expr = (x_expr - x_left_var) / (x_right_var - x_left_var)
    ty_expr: Expr = (y_expr - y_lower_var) / (y_upper_var - y_lower_var)
    return (
        z00_var * (one_const - tx_expr) * (one_const - ty_expr)
        + z10_var * tx_expr * (one_const - ty_expr)
        + z01_var * (one_const - tx_expr) * ty_expr
        + z11_var * tx_expr * ty_expr
    )


def _build_clipped_lookup_matrix_expression(
    x_input_var: Var,
    y_input_var: Var,
    x_vars: Sequence[Var],
    y_vars: Sequence[Var],
    z_vars: Sequence[Sequence[Var]],
) -> Expr:
    """
    Build the clipped bilinear interpolation expression for one lookup matrix.

    :param x_input_var: X-axis input variable.
    :param y_input_var: Y-axis input variable.
    :param x_vars: Symbolic x-axis parameters.
    :param y_vars: Symbolic y-axis parameters.
    :param z_vars: Symbolic matrix values indexed as `[y][x]`.
    :return: Bilinear interpolation expression.
    """
    x_index: int
    y_index: int
    x_clamped_expr: Expr = sym.hard_sat(x_input_var, x_vars[0], x_vars[len(x_vars) - 1])
    y_clamped_expr: Expr = sym.hard_sat(y_input_var, y_vars[0], y_vars[len(y_vars) - 1])
    result_expr: Expr = Const(0.0)

    for y_index in range(len(y_vars) - 1):
        for x_index in range(len(x_vars) - 1):
            cell_expr: Expr = _build_bilinear_cell_expression(
                x_expr=x_clamped_expr,
                y_expr=y_clamped_expr,
                x_left_var=x_vars[x_index],
                x_right_var=x_vars[x_index + 1],
                y_lower_var=y_vars[y_index],
                y_upper_var=y_vars[y_index + 1],
                z00_var=z_vars[y_index][x_index],
                z10_var=z_vars[y_index][x_index + 1],
                z01_var=z_vars[y_index + 1][x_index],
                z11_var=z_vars[y_index + 1][x_index + 1],
            )

            if x_index == len(x_vars) - 2:
                upper_x_var: Var | None = None
            else:
                upper_x_var = x_vars[x_index + 1]

            if y_index == len(y_vars) - 2:
                upper_y_var: Var | None = None
            else:
                upper_y_var = y_vars[y_index + 1]

            selector_expr: Expr = _build_interval_selector(x_clamped_expr, x_vars[x_index], upper_x_var)
            selector_expr = selector_expr * _build_interval_selector(y_clamped_expr, y_vars[y_index], upper_y_var)
            result_expr = result_expr + cell_expr * selector_expr

    return result_expr


def build_lookup_array_linear_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    clip: bool,
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime one-dimensional linear lookup template from explicit points.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Strictly increasing x values.
    :param y_points: Matching y values.
    :param clip: If True, clip outside the table; otherwise extrapolate linearly.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    point_count: int = len(x_points)
    point_index: int
    yi_var: Var
    yo_var: Var
    x_vars: list[Var] = list()
    y_vars: list[Var] = list()
    parameter_var: Var
    lookup_expr: Expr
    template: EmtModelTemplate = EmtModelTemplate()

    _validate_lookup_points(x_points=x_points, y_points=y_points)

    if name is None:
        if clip:
            template_name = f"lookup_array_linear_{point_count}pt"
        else:
            template_name = f"lookup_array_linear_noclipping_{point_count}pt"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    yi_var = vf.add_var("yi_" + template_name)
    yo_var = vf.add_var("yo_" + template_name)

    for point_index in range(point_count):
        parameter_var = vf.add_var("arr_x" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(x_points[point_index]), name="arr_x" + str(point_index + 1))
        x_vars.append(parameter_var)

        parameter_var = vf.add_var("arr_y" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(y_points[point_index]), name="arr_y" + str(point_index + 1))
        y_vars.append(parameter_var)

    if clip:
        lookup_expr = _build_clipped_lookup_expression(yi_var=yi_var, x_vars=x_vars, y_vars=y_vars)
    else:
        lookup_expr = _build_unclipped_lookup_expression(yi_var=yi_var, x_vars=x_vars, y_vars=y_vars)

    template.block = Block(
        algebraic_vars=list([yo_var]),
        algebraic_eqs=list([yo_var - lookup_expr]),
        in_vars=list([yi_var]),
        out_vars=list([yo_var]),
        event_dict=template.block.event_dict,
        name=template_name,
    )
    return template


def build_inverse_lookup_array_linear_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime inverse linear lookup template from explicit points.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Original x values.
    :param y_points: Original y values to invert.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    point_count: int
    point_index: int
    yi_var: Var
    yo_var: Var
    x_vars: list[Var] = list()
    y_vars: list[Var] = list()
    parameter_var: Var
    lookup_expr: Expr
    template: EmtModelTemplate = EmtModelTemplate()
    normalized_x_points: list[float]
    normalized_y_points: list[float]

    normalized_x_points, normalized_y_points = _normalize_inverse_lookup_points(x_points=x_points, y_points=y_points)
    point_count = len(normalized_x_points)

    if name is None:
        template_name = f"inverse_lookup_array_linear_{point_count}pt"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    yi_var = vf.add_var("yi_" + template_name)
    yo_var = vf.add_var("yo_" + template_name)

    for point_index in range(point_count):
        parameter_var = vf.add_var("arr_x" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(normalized_x_points[point_index]), name="arr_x" + str(point_index + 1))
        x_vars.append(parameter_var)

        parameter_var = vf.add_var("arr_y" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(normalized_y_points[point_index]), name="arr_y" + str(point_index + 1))
        y_vars.append(parameter_var)

    lookup_expr = _build_clipped_lookup_expression(yi_var=yi_var, x_vars=y_vars, y_vars=x_vars)
    template.block = Block(
        algebraic_vars=list([yo_var]),
        algebraic_eqs=list([yo_var - lookup_expr]),
        in_vars=list([yi_var]),
        out_vars=list([yo_var]),
        event_dict=template.block.event_dict,
        name=template_name,
    )
    return template


def build_lookup_matrix_linear_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    z_matrix: Sequence[Sequence[float]],
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime bilinear lookup matrix template from explicit axes and values.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Strictly increasing x-axis values.
    :param y_points: Strictly increasing y-axis values.
    :param z_matrix: Matrix values indexed as `[y][x]`.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    x_count: int = len(x_points)
    y_count: int = len(y_points)
    x_index: int
    y_index: int
    x_input_var: Var
    y_input_var: Var
    output_var: Var
    x_axis_vars: list[Var] = list()
    y_axis_vars: list[Var] = list()
    z_value_vars: list[list[Var]] = list()
    parameter_var: Var
    lookup_expr: Expr
    template: EmtModelTemplate = EmtModelTemplate()

    _validate_lookup_matrix(x_points=x_points, y_points=y_points, z_matrix=z_matrix)

    if name is None:
        template_name = f"lookup_matrix_linear_{x_count}x{y_count}"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    x_input_var = vf.add_var("yi1_" + template_name)
    y_input_var = vf.add_var("yi2_" + template_name)
    output_var = vf.add_var("yo_" + template_name)

    for x_index in range(x_count):
        parameter_var = vf.add_var("arr_x" + str(x_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(x_points[x_index]), name="arr_x" + str(x_index + 1))
        x_axis_vars.append(parameter_var)

    for y_index in range(y_count):
        parameter_var = vf.add_var("arr_y" + str(y_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(y_points[y_index]), name="arr_y" + str(y_index + 1))
        y_axis_vars.append(parameter_var)

    for y_index in range(y_count):
        row_vars: list[Var] = list()
        for x_index in range(x_count):
            parameter_var = vf.add_var("arr_z" + str(y_index + 1) + "_" + str(x_index + 1) + "_" + template_name)
            template.block.event_dict[parameter_var] = vf.add_const(
                float(z_matrix[y_index][x_index]),
                name="arr_z" + str(y_index + 1) + "_" + str(x_index + 1),
            )
            row_vars.append(parameter_var)
        z_value_vars.append(row_vars)

    lookup_expr = _build_clipped_lookup_matrix_expression(
        x_input_var=x_input_var,
        y_input_var=y_input_var,
        x_vars=x_axis_vars,
        y_vars=y_axis_vars,
        z_vars=z_value_vars,
    )

    template.block = Block(
        algebraic_vars=list([output_var]),
        algebraic_eqs=list([output_var - lookup_expr]),
        in_vars=list([x_input_var, y_input_var]),
        out_vars=list([output_var]),
        event_dict=template.block.event_dict,
        name=template_name,
    )
    return template


def build_lookup_array_spline_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime one-dimensional spline lookup template from explicit points.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Strictly increasing x values.
    :param y_points: Matching y values.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    point_count: int = len(x_points)
    point_index: int
    yi_var: Var
    yo_var: Var
    x_vars: list[Var] = list()
    y_vars: list[Expr] = list()
    parameter_var: Var
    lookup_expr: Expr
    template: EmtModelTemplate = EmtModelTemplate()

    _validate_lookup_points(x_points=x_points, y_points=y_points)

    if name is None:
        template_name = f"lookup_array_spline_{point_count}pt"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    yi_var = vf.add_var("yi_" + template_name)
    yo_var = vf.add_var("yo_" + template_name)

    for point_index in range(point_count):
        parameter_var = vf.add_var("arr_x" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(x_points[point_index]), name="arr_x" + str(point_index + 1))
        x_vars.append(parameter_var)

        parameter_var = vf.add_var("arr_y" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(y_points[point_index]), name="arr_y" + str(point_index + 1))
        y_vars.append(parameter_var)

    lookup_expr = _build_cubic_spline_piecewise_expression(
        coord_expr=yi_var,
        axis_points=x_points,
        axis_vars=x_vars,
        sample_values=y_vars,
    )

    template.block = Block(
        algebraic_vars=list([yo_var]),
        algebraic_eqs=list([yo_var - lookup_expr]),
        in_vars=list([yi_var]),
        out_vars=list([yo_var]),
        event_dict=template.block.event_dict,
        name=template_name,
    )
    return template


def build_lookup_matrix_spline_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    z_matrix: Sequence[Sequence[float]],
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime two-dimensional spline lookup template from explicit axes and values.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Strictly increasing x-axis values.
    :param y_points: Strictly increasing y-axis values.
    :param z_matrix: Matrix values indexed as `[y][x]`.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    x_count: int = len(x_points)
    y_count: int = len(y_points)
    x_index: int
    y_index: int
    x_input_var: Var
    y_input_var: Var
    output_var: Var
    x_axis_vars: list[Var] = list()
    y_axis_vars: list[Var] = list()
    z_value_vars: list[list[Expr]] = list()
    parameter_var: Var
    row_spline_exprs: list[Expr] = list()
    lookup_expr: Expr
    template: EmtModelTemplate = EmtModelTemplate()

    _validate_lookup_matrix(x_points=x_points, y_points=y_points, z_matrix=z_matrix)

    if name is None:
        template_name = f"lookup_matrix_spline_{x_count}x{y_count}"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    x_input_var = vf.add_var("yi1_" + template_name)
    y_input_var = vf.add_var("yi2_" + template_name)
    output_var = vf.add_var("yo_" + template_name)

    for x_index in range(x_count):
        parameter_var = vf.add_var("arr_x" + str(x_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(x_points[x_index]), name="arr_x" + str(x_index + 1))
        x_axis_vars.append(parameter_var)

    for y_index in range(y_count):
        parameter_var = vf.add_var("arr_y" + str(y_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(y_points[y_index]), name="arr_y" + str(y_index + 1))
        y_axis_vars.append(parameter_var)

    for y_index in range(y_count):
        row_vars: list[Expr] = list()
        for x_index in range(x_count):
            parameter_var = vf.add_var("arr_z" + str(y_index + 1) + "_" + str(x_index + 1) + "_" + template_name)
            template.block.event_dict[parameter_var] = vf.add_const(
                float(z_matrix[y_index][x_index]),
                name="arr_z" + str(y_index + 1) + "_" + str(x_index + 1),
            )
            row_vars.append(parameter_var)
        z_value_vars.append(row_vars)

    for y_index in range(y_count):
        row_spline_exprs.append(
            _build_cubic_spline_piecewise_expression(
                coord_expr=x_input_var,
                axis_points=x_points,
                axis_vars=x_axis_vars,
                sample_values=z_value_vars[y_index],
            )
        )

    lookup_expr = _build_cubic_spline_piecewise_expression(
        coord_expr=y_input_var,
        axis_points=y_points,
        axis_vars=y_axis_vars,
        sample_values=row_spline_exprs,
    )

    template.block = Block(
        algebraic_vars=list([output_var]),
        algebraic_eqs=list([output_var - lookup_expr]),
        in_vars=list([x_input_var, y_input_var]),
        out_vars=list([output_var]),
        event_dict=template.block.event_dict,
        name=template_name,
    )
    return template
