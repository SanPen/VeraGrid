# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovSteam1 steam-turbine governor model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.governors.govsteam1 import (
    build_govsteam1_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovSteam1Settings:
    """Topology and valve-curve values needed while building GovSteam1 equations."""

    __slots__ = ("times", "valve", "gv_points", "pgv_points")

    def __init__(
            self,
            times: tuple[float, float, float, float, float, float, float],
            valve: bool,
            gv_points: tuple[float, float, float, float, float, float],
            pgv_points: tuple[float, float, float, float, float, float],
    ) -> None:
        """Store time constants and six paired gate/power curve points.

        :param times: CGMES T1 through T7 values in seconds.
        :param valve: Whether to use the imported nonlinear valve characteristic.
        :param gv_points: Six CGMES valve positions.
        :param pgv_points: Six CGMES power values paired with ``gv_points``.
        """
        self.times: tuple[float, float, float, float, float, float, float] = times
        self.valve: bool = valve
        self.gv_points: tuple[float, float, float, float, float, float] = gv_points
        self.pgv_points: tuple[float, float, float, float, float, float] = pgv_points


def build_gov_steam1_template(
        vfactory: VarFactory,
        name: str | None = None,
        settings: GovSteam1Settings | None = None,
) -> RmsModelTemplate:
    """Build the CGMES GovSteam1 equations with imported curve and exact zero-time stages.

    :param vfactory: Factory used to allocate the template symbols.
    :param name: Optional runtime model name.
    :param settings: Imported stage times, valve selector, and curve points.
    :return: Equation-backed template retaining every CGMES GovSteam1 scalar field.
    :raises ValueError: Invalid time constants or an unordered nonlinear valve curve.
    """
    active_settings: GovSteam1Settings = (
        GovSteam1Settings(
            times=(0.0, 0.0, 0.1, 0.3, 5.0, 0.5, 0.0),
            valve=True,
            gv_points=(0.0, 0.25, 0.5, 0.75, 1.0, 1.25),
            pgv_points=(0.0, 0.25, 0.5, 0.75, 1.0, 1.25),
        )
        if settings is None
        else settings
    )
    template_name: str = "GovSteam1" if name is None else name
    if not all(math.isfinite(value) for value in active_settings.times):
        raise ValueError("CGMES GovSteam1 time constants must be finite")
    elif min(active_settings.times) < 0.0 or active_settings.times[2] <= 0.0:
        raise ValueError("CGMES GovSteam1 times must be nonnegative and T3 positive")
    elif active_settings.times[0] == 0.0 and active_settings.times[1] != 0.0:
        raise ValueError("CGMES GovSteam1 T1=0 requires T2=0 for a proper transfer")
    elif active_settings.valve and not all(
            active_settings.gv_points[index] < active_settings.gv_points[index + 1]
            for index in range(5)
    ):
        raise ValueError("CGMES GovSteam1 valve points must increase strictly")
    else:
        pass

    # Start from the shipped governor graph, then repair the CGMES-specific curve
    # and zero-time stages in this package without mutating the RMS implementation.
    template: RmsModelTemplate = build_govsteam1_template(
        vf=vfactory,
        name=template_name,
    )
    block: Block = template.block
    parameter_names: tuple[str, ...] = (
        "enabled", "mwbase", "k", "t1", "t2", "t3", "uo", "uc", "pmax", "pmin",
        "t4", "k1", "k2", "t5", "k3", "k4", "t6", "k5", "k6", "t7", "k7", "k8",
        "db1", "eps", "sdb1", "sdb2", "db2", "valve", "gv1", "pgv1", "gv2", "pgv2",
        "gv3", "pgv3", "gv4", "pgv4", "gv5", "pgv5", "gv6", "pgv6",
    )
    for parameter_name in parameter_names:
        parameter_variable: Var = vfactory.add_var(
            f"GovSteam1.{parameter_name}_{template_name}"
        )
        if parameter_name.startswith("gv"):
            point_index: int = int(parameter_name[2:]) - 1
            block.event_dict[parameter_variable] = vfactory.add_const(
                active_settings.gv_points[point_index]
            )
        elif parameter_name.startswith("pgv"):
            point_index = int(parameter_name[3:]) - 1
            block.event_dict[parameter_variable] = vfactory.add_const(
                active_settings.pgv_points[point_index]
            )
        else:
            block.event_dict[parameter_variable] = vfactory.add_const(value=None)

    # Restore the exact imported T values after the native builder's small-time
    # numerical substitutions, because zero stages are removed below.
    runtime_times: tuple[tuple[str, float], ...] = (
        ("gov.t1_", active_settings.times[0]),
        ("gov.t2_", active_settings.times[1]),
        ("gov.t3_", active_settings.times[2]),
        ("gov.t4_", active_settings.times[3]),
        ("gov.t5_", active_settings.times[4]),
        ("gov.t6_", active_settings.times[5]),
        ("gov.t7_", active_settings.times[6]),
    )
    for runtime_prefix, time_value in runtime_times:
        for parameter_variable in block.event_dict:
            if parameter_variable.name.startswith(f"{runtime_prefix}{template_name}"):
                block.event_dict[parameter_variable] = vfactory.add_const(
                    time_value,
                    name=parameter_variable.name,
                )
            else:
                pass

    # Replace the fixed RMS valve curve with the six exact CGMES points.
    gate_variable: Var | None = None
    curve_output: Var | None = None
    gate_points: list[Var] = list()
    power_points: list[Var] = list()
    for variable in block.algebraic_vars:
        if variable.name.startswith(f"gov.backlashHysteresis.y_{template_name}"):
            gate_variable = variable
        else:
            pass
    for variable in block.algebraic_vars:
        if variable.name.startswith(f"gov.pgv.y[1]_{template_name}"):
            curve_output = variable
        else:
            pass
    for point_index in range(1, 7):
        point_gate_variable: Var | None = find_variable(
            list(block.event_dict.keys()),
            f"GovSteam1.gv{point_index}_{template_name}",
        )
        power_variable: Var | None = find_variable(
            list(block.event_dict.keys()),
            f"GovSteam1.pgv{point_index}_{template_name}",
        )
        if point_gate_variable is not None and power_variable is not None:
            gate_points.append(point_gate_variable)
            power_points.append(power_variable)
        else:
            pass
    if gate_variable is not None and curve_output is not None and len(gate_points) == 6 and len(power_points) == 6:
        curve_expression: Expr = build_gov_steam1_valve_curve(
            gate=gate_variable,
            gv_points=(gate_points[0], gate_points[1], gate_points[2], gate_points[3], gate_points[4], gate_points[5]),
            pgv_points=(power_points[0], power_points[1], power_points[2], power_points[3], power_points[4], power_points[5]),
        )
        replace_algebraic_equation(
            block=block,
            output_variable=curve_output,
            expression=curve_expression,
        )
    else:
        raise ValueError("CGMES GovSteam1 valve curve variables could not be resolved")

    # Remove each zero-time turbine lag by substituting its exact algebraic limit.
    lag_stages: tuple[tuple[int, str, str], ...] = (
        (6, f"gov.firstOrder3.y_{template_name}", f"gov.firstOrder2.y_{template_name}"),
        (5, f"gov.firstOrder2.y_{template_name}", f"gov.firstOrder1.y_{template_name}"),
        (4, f"gov.firstOrder1.y_{template_name}", f"gov.firstOrder.y_{template_name}"),
        (3, f"gov.firstOrder.y_{template_name}", f"gov.switch2.y_{template_name}"),
    )
    for time_index, state_name, input_name in lag_stages:
        if active_settings.times[time_index] == 0.0:
            state_variable: Var | None = find_variable(block.state_vars, state_name)
            input_variable: Var | None = find_variable(block.algebraic_vars, input_name)
            if input_variable is None:
                input_variable = find_variable(block.state_vars, input_name)
            else:
                pass
            if state_variable is not None and input_variable is not None:
                eliminate_state(block, state_variable, input_variable)
            else:
                raise ValueError("CGMES GovSteam1 zero-time stage ports could not be resolved")
        else:
            pass

    # Event guards use the DAE assignment at initialization, not the native pre-event seed.
    for equation in block.algebraic_eqs:
        if (
                isinstance(equation, BinOp)
                and isinstance(equation.left, Var)
                and equation.left.name.startswith("$whenCondition")
        ):
            block.init_eqs[equation.left] = equation.right
        else:
            pass

    # T1=T2=0 is the exact static gain limit; T1=0 with T2>0 was rejected above.
    if active_settings.times[0] == 0.0:
        transfer_output: Var | None = find_variable(
            block.algebraic_vars,
            f"gov.transferFunction.y_{template_name}",
        )
        transfer_state: Var | None = find_variable(
            block.state_vars,
            f"gov.transferFunction.x_scaled[1]_{template_name}",
        )
        transfer_detail: Var | None = find_variable(
            block.algebraic_vars,
            f"gov.transferFunction.x[1]_{template_name}",
        )
        speed_deadband: Var | None = find_variable(
            block.algebraic_vars,
            f"gov.switch.y_{template_name}",
        )
        governor_gain: Var | None = find_variable(
            list(block.event_dict.keys()),
            f"gov.K_{template_name}",
        )
        if (
                transfer_output is not None
                and transfer_state is not None
                and transfer_detail is not None
                and speed_deadband is not None
                and governor_gain is not None
        ):
            remove_algebraic_variable(block, transfer_output)
            substitute_variable(block, transfer_output, governor_gain * speed_deadband)
            remove_algebraic_variable(block, transfer_detail)
            eliminate_state(block, transfer_state, Const(0.0))
            replace_event_value(block, f"gov.transferFunction.d_{template_name}", 0.0, vfactory)
        else:
            raise ValueError("CGMES GovSteam1 zero-time governor transfer ports could not be resolved")
    else:
        pass

    # Expose total steam power so the importer can attach one mechanical input.
    first_power: Var | None = find_variable(block.out_vars, f"gov.Pm1Pu_{template_name}")
    second_power: Var | None = find_variable(block.out_vars, f"gov.Pm2Pu_{template_name}")
    if first_power is not None and second_power is not None:
        total_power: Var = vfactory.add_var(f"PmPu_{template_name}")
        block.algebraic_vars.append(total_power)
        block.algebraic_eqs.append(total_power - first_power - second_power)
        block.out_vars.append(total_power)
        block.init_eqs[total_power] = (
            block.init_eqs[first_power] + block.init_eqs[second_power]
        )
    else:
        raise ValueError("CGMES GovSteam1 turbine-power ports could not be resolved")

    template.comment = "CGMES GovSteam1 with RDF valve curve and exact zero-time stage limits."
    return template


def build_gov_steam1_valve_curve(
        gate: Expr,
        gv_points: tuple[Var, Var, Var, Var, Var, Var],
        pgv_points: tuple[Var, Var, Var, Var, Var, Var],
) -> Expr:
    """Build the IEC piecewise-linear gate-to-power characteristic.

    :param gate: Backlash-adjusted gate position.
    :param gv_points: Imported gate positions in ascending order.
    :param pgv_points: Imported power values paired to ``gv_points``.
    :return: Piecewise-linear symbolic expression with constant endpoint extension.
    """
    # Clamped segment increments stay continuous at every imported breakpoint.
    expression: Expr = pgv_points[0]
    for point_index in range(5):
        lower_gate: Var = gv_points[point_index]
        upper_gate: Var = gv_points[point_index + 1]
        lower_power: Var = pgv_points[point_index]
        upper_power: Var = pgv_points[point_index + 1]
        slope: Expr = (upper_power - lower_power) / (upper_gate - lower_gate)
        segment_increment: Expr = sym.min(
            sym.max(gate - lower_gate, Const(0.0)),
            upper_gate - lower_gate,
        )
        expression = expression + slope * segment_increment
    return expression


def find_variable(variables: list[Var], name: str) -> Var | None:
    """Find a symbolic variable by its exact runtime name.

    :param variables: Runtime variables exposed by one equation block.
    :param name: Exact symbolic variable name.
    :return: Matching variable, or ``None`` when absent.
    """
    for variable in variables:
        if variable.name == name:
            return variable
        else:
            pass
    return None


def replace_algebraic_equation(block: Block, output_variable: Var, expression: Expr) -> None:
    """Replace the equation defining one algebraic output.

    :param block: GovSteam1 equation block.
    :param output_variable: Variable defined by the equation being replaced.
    :param expression: New right-hand-side expression.
    :return: None.
    """
    equation_index: int | None = None
    for index, equation in enumerate(block.algebraic_eqs):
        if isinstance(equation, BinOp) and isinstance(equation.left, Var):
            if equation.left.uid == output_variable.uid:
                equation_index = index
            else:
                pass
        else:
            pass
    if equation_index is not None:
        block.algebraic_eqs[equation_index] = output_variable - expression
    else:
        raise ValueError(f"GovSteam1 equation for {output_variable.name} is missing")


def remove_algebraic_variable(block: Block, variable: Var) -> None:
    """Remove an algebraic output and its defining equation.

    :param block: GovSteam1 equation block.
    :param variable: Algebraic variable to remove.
    :return: None.
    """
    equation_index: int | None = None
    for index, equation in enumerate(block.algebraic_eqs):
        if isinstance(equation, BinOp) and isinstance(equation.left, Var):
            if equation.left.uid == variable.uid:
                equation_index = index
            else:
                pass
        else:
            pass
    if equation_index is not None:
        block.algebraic_eqs.pop(equation_index)
        for variable_index, algebraic_variable in enumerate(block.algebraic_vars):
            if algebraic_variable.uid == variable.uid:
                block.algebraic_vars.pop(variable_index)
                break
            else:
                pass
    else:
        raise ValueError(f"GovSteam1 algebraic equation for {variable.name} is missing")


def eliminate_state(block: Block, state_variable: Var, replacement: Expr) -> None:
    """Replace one differential state by its exact algebraic limit.

    :param block: GovSteam1 equation block.
    :param state_variable: State variable to remove.
    :param replacement: Algebraic expression equal to the state when its time is zero.
    :return: None.
    """
    state_index: int | None = None
    for index, candidate in enumerate(block.state_vars):
        if candidate.uid == state_variable.uid:
            state_index = index
        else:
            pass
    if state_index is not None:
        block.state_vars.pop(state_index)
        block.state_eqs.pop(state_index)
        substitute_variable(block, state_variable, replacement)
        block.init_eqs.pop(state_variable, None)
        removed_diff_variables: list[Var] = list()
        for diff_variable in block.diff_vars:
            if diff_variable.base_var is not None:
                if diff_variable.base_var.uid == state_variable.uid:
                    removed_diff_variables.append(diff_variable)
                else:
                    pass
            else:
                pass
        for diff_variable in removed_diff_variables:
            for diff_index, candidate in enumerate(block.diff_vars):
                if candidate.uid == diff_variable.uid:
                    block.diff_vars.pop(diff_index)
                    break
                else:
                    pass
            block.diff_init_eqs.pop(diff_variable, None)
    else:
        raise ValueError(f"GovSteam1 state {state_variable.name} is missing")


def substitute_variable(block: Block, variable: Var, replacement: Expr) -> None:
    """Substitute one symbolic variable throughout a block's equations.

    :param block: GovSteam1 equation block.
    :param variable: Variable to replace.
    :param replacement: Replacement expression.
    :return: None.
    """
    substitutions: dict[Var, Expr] = {variable: replacement}
    for index, equation in enumerate(block.state_eqs):
        block.state_eqs[index] = equation.subs(substitutions)
    for index, equation in enumerate(block.algebraic_eqs):
        block.algebraic_eqs[index] = equation.subs(substitutions)
    for event_variable, event_value in list(block.event_dict.items()):
        if isinstance(event_value, Expr):
            block.event_dict[event_variable] = event_value.subs(substitutions)
        else:
            pass
    for mode_variable, mode_value in list(block.mode_dict.items()):
        if isinstance(mode_value, Expr):
            block.mode_dict[mode_variable] = mode_value.subs(substitutions)
        else:
            pass
    for initialized_variable, initial_value in list(block.init_eqs.items()):
        if initialized_variable.uid == variable.uid:
            block.init_eqs.pop(initialized_variable)
        elif isinstance(initial_value, Expr):
            block.init_eqs[initialized_variable] = initial_value.subs(substitutions)
        else:
            pass
    for differential_variable, differential_value in list(block.diff_init_eqs.items()):
        if isinstance(differential_value, Expr):
            block.diff_init_eqs[differential_variable] = differential_value.subs(substitutions)
        else:
            pass


def replace_event_value(
        block: Block,
        name: str,
        value: float,
        vfactory: VarFactory,
) -> None:
    """Set one runtime event to a finite scalar value.

    :param block: GovSteam1 equation block.
    :param name: Exact runtime event name.
    :param value: Replacement scalar event value.
    :param vfactory: Factory that creates the event constant.
    :return: None.
    """
    for event_variable in block.event_dict:
        if event_variable.name == name:
            block.event_dict[event_variable] = vfactory.add_const(
                value=value,
                name=event_variable.name,
            )
        else:
            pass
