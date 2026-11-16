# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydro3 modified IEEE hydro governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.common.speed_deadband import (
    build_intentional_speed_deadband,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydro3Parameters:
    """CGMES GovHydro3 scalar fields and turbine gate/power curve."""

    __slots__ = (
        'mwbase', 'pmax', 'pmin', 'governor_control', 'rgate', 'relec', 'td',
        'tf', 'tp', 'velop', 'velcl', 'k1', 'k2', 'ki', 'kg', 'tt', 'db1',
        'eps', 'db2', 'tw', 'at', 'dturb', 'qnl', 'h0', 'gv_points',
        'pgv_points', 'nominal_frequency',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            pmax: float = 1.0,
            pmin: float = 0.0,
            governor_control: bool = True,
            rgate: float = 0.05,
            relec: float = 0.05,
            td: float = 0.05,
            tf: float = 0.05,
            tp: float = 0.05,
            velop: float = 0.1,
            velcl: float = -0.1,
            k1: float = 1.0,
            k2: float = 1.0,
            ki: float = 0.1,
            kg: float = 1.0,
            tt: float = 0.5,
            db1: float = 0.0,
            eps: float = 0.0,
            db2: float = 0.0,
            tw: float = 2.0,
            at: float = 1.2,
            dturb: float = 0.2,
            qnl: float = 0.0,
            h0: float = 1.0,
            gv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            pgv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            nominal_frequency: float = 50.0,
    ) -> None:
        """Store the native RDF values in MWbase, seconds, Hz, and pu.

        :param mwbase: Active power base in MW.
        :param pmax: Upper gate and turbine-power limit.
        :param pmin: Lower gate and turbine-power limit.
        :param governor_control: True selects the PID path, false the double derivative path.
        :param rgate: Gate feedback coefficient.
        :param relec: Filtered electrical-power feedback coefficient.
        :param td: Speed derivative filter time in seconds.
        :param tf: Derivative-path filter time in seconds.
        :param tp: Gate-velocity filter time in seconds.
        :param velop: Maximum gate-opening rate in pu/s.
        :param velcl: Minimum gate-closing rate in pu/s.
        :param k1: Proportional gate-control gain.
        :param k2: Double-derivative path gain.
        :param ki: Gate integrator gain.
        :param kg: Gate servo gain.
        :param tt: Electrical power transducer time in seconds.
        :param db1: Intentional speed deadband in Hz.
        :param eps: Deadband hysteresis in Hz.
        :param db2: Mechanical-power deadband in MW.
        :param tw: Water starting time in seconds.
        :param at: Turbine gain.
        :param dturb: Turbine damping coefficient.
        :param qnl: No-load flow coefficient.
        :param h0: Initial turbine head.
        :param gv_points: Six gate curve points.
        :param pgv_points: Six paired turbine power points.
        :param nominal_frequency: System frequency for Hz to pu conversion.
        """
        self.mwbase: float = mwbase
        self.pmax: float = pmax
        self.pmin: float = pmin
        self.governor_control: bool = governor_control
        self.rgate: float = rgate
        self.relec: float = relec
        self.td: float = td
        self.tf: float = tf
        self.tp: float = tp
        self.velop: float = velop
        self.velcl: float = velcl
        self.k1: float = k1
        self.k2: float = k2
        self.ki: float = ki
        self.kg: float = kg
        self.tt: float = tt
        self.db1: float = db1
        self.eps: float = eps
        self.db2: float = db2
        self.tw: float = tw
        self.at: float = at
        self.dturb: float = dturb
        self.qnl: float = qnl
        self.h0: float = h0
        self.gv_points: tuple[float, float, float, float, float, float] = gv_points
        self.pgv_points: tuple[float, float, float, float, float, float] = pgv_points
        self.nominal_frequency: float = nominal_frequency


def build_gov_hydro3_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydro3Parameters | None = None,
) -> RmsModelTemplate:
    """Build the selectable PID/double-derivative hydro governor equations.

    The two Cflag paths share the gate, water-column, turbine curve, and output
    limits. Up to six curve points are scaled by Pmax between assumed endpoints.
    Zero-time filters become algebraic equations; the mandatory positive turbine
    time remains dynamic as specified by the CGMES documentation.

    :param vfactory: Factory owning symbolic variables.
    :param name: Optional unique runtime name.
    :param parameters: Imported CGMES parameters.
    :return: Executable governor with speed, reference, electrical-power, and Pm ports.
    :raises ValueError: Invalid limits, time constants, or curve data.
    """
    settings: GovHydro3Parameters = (
        GovHydro3Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.pmax, settings.pmin, settings.rgate,
        settings.relec, settings.td, settings.tf, settings.tp, settings.velop,
        settings.velcl, settings.k1, settings.k2, settings.ki, settings.kg,
        settings.tt, settings.db1, settings.eps, settings.db2, settings.tw,
        settings.at, settings.dturb, settings.qnl, settings.h0,
        settings.nominal_frequency, *settings.gv_points, *settings.pgv_points,
    )
    curve_point_count: int = max(
        (
            point_index + 1
            for point_index in range(6)
            if settings.gv_points[point_index] != 0.0
            or settings.pgv_points[point_index] != 0.0
        ),
        default=0,
    )
    curve_default: bool = settings.gv_points[0] < 0.0 or all(
        value == 0.0 for value in settings.gv_points + settings.pgv_points
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovHydro3 parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.nominal_frequency <= 0.0:
        raise ValueError('GovHydro3 requires positive MWBASE and nominal frequency')
    elif (
            settings.pmin < 0.0 or settings.pmin >= settings.pmax
            or settings.velop < 0.0 or settings.velcl > 0.0
    ):
        raise ValueError('GovHydro3 gate limits and rates are invalid')
    elif min(settings.td, settings.tf, settings.tp, settings.tw, settings.tt) < 0.0:
        raise ValueError('GovHydro3 filter and turbine times must be nonnegative')
    elif settings.tt == 0.0 or settings.at <= 0.0 or settings.h0 <= 0.0:
        raise ValueError('GovHydro3 requires positive TT, AT, and H0')
    elif settings.td == 0.0 or settings.tf == 0.0:
        raise ValueError('GovHydro3 requires positive TD and TF for its derivative stages')
    elif min(settings.db1, settings.eps, settings.db2) < 0.0:
        raise ValueError('GovHydro3 deadbands must be nonnegative')
    elif not curve_default and (
            not all(
                settings.gv_points[index] == 0.0
                and settings.pgv_points[index] == 0.0
                for index in range(curve_point_count, 6)
            )
            or not all(
                0.0 <= settings.gv_points[index] <= 1.0
                and 0.0 <= settings.pgv_points[index] <= 1.0
                for index in range(curve_point_count)
            )
            or not all(
                settings.gv_points[index] < settings.gv_points[index + 1]
                and settings.pgv_points[index] <= settings.pgv_points[index + 1]
                for index in range(curve_point_count - 1)
            )
            or (
                settings.gv_points[0] == 0.0
                and settings.pgv_points[0] != 0.0
            )
            or (
                settings.gv_points[curve_point_count - 1] == 1.0
                and settings.pgv_points[curve_point_count - 1] != 1.0
            )
    ):
        raise ValueError('GovHydro3 curve points must match the assumed endpoints and increase')
    else:
        pass

    template_name: str = 'GovHydro3' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    mwbase: Var = control.parameter('GovHydro3.mwbase', settings.mwbase)
    pmax: Var = control.parameter('GovHydro3.pmax', settings.pmax)
    pmin: Var = control.parameter('GovHydro3.pmin', settings.pmin)
    rgate: Var = control.parameter('GovHydro3.rgate', settings.rgate)
    relec: Var = control.parameter('GovHydro3.relec', settings.relec)
    td: Var = control.parameter('GovHydro3.td', settings.td)
    tf: Var = control.parameter('GovHydro3.tf', settings.tf)
    tp: Var = control.parameter('GovHydro3.tp', settings.tp)
    velop: Var = control.parameter('GovHydro3.velop', settings.velop)
    velcl: Var = control.parameter('GovHydro3.velcl', settings.velcl)
    k1: Var = control.parameter('GovHydro3.k1', settings.k1)
    k2: Var = control.parameter('GovHydro3.k2', settings.k2)
    ki: Var = control.parameter('GovHydro3.ki', settings.ki)
    kg: Var = control.parameter('GovHydro3.kg', settings.kg)
    tt: Var = control.parameter('GovHydro3.tt', settings.tt)
    db1: Var = control.parameter('GovHydro3.db1', settings.db1)
    eps: Var = control.parameter('GovHydro3.eps', settings.eps)
    tw: Var = control.parameter('GovHydro3.tw', settings.tw)
    at: Var = control.parameter('GovHydro3.at', settings.at)
    dturb: Var = control.parameter('GovHydro3.dturb', settings.dturb)
    qnl: Var = control.parameter('GovHydro3.qnl', settings.qnl)
    h0: Var = control.parameter('GovHydro3.h0', settings.h0)
    gv_points: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        control.parameter(f'GovHydro3.gv{index + 1}', settings.gv_points[index])
        for index in range(6)
    )
    pgv_points: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        control.parameter(f'GovHydro3.pgv{index + 1}', settings.pgv_points[index])
        for index in range(6)
    )

    # Intentional speed pickup is expressed in pu after converting the RDF Hz fields.
    speed: Var = control.input('OmegaPu', Const(1.0))
    power_reference: Var = control.input('PRefPu', Const(0.0))
    electrical_power: Var = vfactory.add_var(
        f'PePu_{template_name}', reference=VarPowerFlowReferenceType.P,
    )
    control.block.in_vars.append(electrical_power)
    control.block.init_eqs[electrical_power] = Const(0.5)
    control.block.external_mapping[VarPowerFlowReferenceType.P] = electrical_power
    speed_deviation: Var = control.algebraic(
        'SpeedDeviationPu', speed - Const(1.0), Const(0.0),
    )
    deadbanded_speed: Expr = build_intentional_speed_deadband(
        control=control,
        speed_deviation=speed_deviation,
        deadband_threshold=db1 / Const(settings.nominal_frequency),
        hysteresis_width=eps / Const(settings.nominal_frequency),
    )
    initial_gate: float = min(max(0.5, settings.pmin), settings.pmax)
    filtered_power: Var = control.lag(
        'FilteredElectricalPowerPu', electrical_power, tt, settings.tt,
        Const(0.5),
    )
    controller_state: Var = vfactory.add_var(f'GovernorIntegralPu_{template_name}')
    gate_state: Var = control.algebraic(
        'GateOpeningPu', controller_state, Const(initial_gate),
    )
    # The upper branch is the source diagram's PID controller.
    if settings.governor_control:
        controller_input: Var = control.algebraic(
            'PIDControllerInputPu',
            power_reference - deadbanded_speed - rgate * gate_state
            - relec * filtered_power,
            Const(0.0),
        )
        speed_derivative_filter: Var = control.lag(
            'SpeedDerivativeFilterPu', deadbanded_speed, td, settings.td,
            Const(0.0),
        )
        derivative_signal: Var = control.algebraic(
            'SpeedDerivativePu', (deadbanded_speed - speed_derivative_filter) / td,
            Const(0.0),
        )
        derivative_memory: Var = control.lag(
            'PIDDerivativeMemoryPu', derivative_signal, tf, settings.tf,
            Const(0.0),
        )
        filtered_derivative: Expr = (
            derivative_signal - derivative_memory
        ) * Const(settings.tf / settings.td)
        control.differential(
            controller_state,
            controller_input + k2 * filtered_derivative,
            Const(initial_gate), pmin, pmax,
        )
    else:
        # The lower branch uses two filtered derivative stages and integrates their sum.
        speed_filter = control.lag(
            'SpeedDerivativeFilterPu', deadbanded_speed, td, settings.td,
            Const(0.0),
        )
        first_derivative: Var = control.algebraic(
            'SpeedDerivativePu', (deadbanded_speed - speed_filter) / td,
            Const(0.0),
        )
        second_filter: Var = control.lag(
            'SecondDerivativeMemoryPu', first_derivative, tf, settings.tf,
            Const(0.0),
        )
        second_derivative: Expr = (first_derivative - second_filter) / tf
        gate_integrator: Expr = (
            power_reference - k1 * first_derivative
            - k2 * second_derivative - relec * filtered_power
            - rgate * gate_state
        )
        control.differential(controller_state, gate_integrator, Const(initial_gate), pmin, pmax)

    # The source integral state is the commanded gate; the servo applies bounded motion.
    gate_command: Var = control.algebraic(
        'GovernorGateCommandPu', controller_state, Const(initial_gate),
    )
    gate_lag: Var = control.lag(
        'GateVelocityFilterPu', gate_command - gate_state, tp, settings.tp,
        Const(0.0),
    )
    gate_velocity: Var = control.algebraic(
        'GateVelocityPuPerSecond', sym.hard_sat(kg * gate_lag, velcl, velop),
        Const(0.0),
    )
    control.differential(gate_state, gate_velocity, Const(initial_gate), pmin, pmax)
    mechanical_gate: Var = control.algebraic(
        'MechanicalGovernorCommandPu', gate_state, Const(initial_gate),
    )
    curve_power: Var = control.algebraic(
        'CurvePowerPu', pmax * build_gov_hydro3_curve(
            mechanical_gate / pmax, gv_points, pgv_points, curve_default,
            curve_point_count, settings.gv_points[0] > 0.0,
            settings.gv_points[curve_point_count - 1] < 1.0,
        ),
        Const(get_gov_hydro3_curve_power(settings, initial_gate)),
    )

    # The nonlinear turbine follows the CGMES drawing's water-column equations.
    head: Var = control.algebraic(
        'TurbineHeadPu', Const(1.0) + h0 * (mechanical_gate - curve_power),
        Const(1.0),
    )
    flow: Var = control.algebraic(
        'TurbineFlowPu', mechanical_gate * sym.sqrt(head), Const(initial_gate),
    )
    if settings.tw > 0.0:
        water_memory: Var = control.lag(
            'WaterColumnMemoryPu', flow, tw, settings.tw, Const(initial_gate),
        )
        water_flow: Expr = (flow - water_memory) / (Const(settings.tw) * tw)
    else:
        water_memory = control.algebraic(
            'WaterColumnMemoryPu', flow, Const(initial_gate),
        )
        water_flow = flow
    deadband_power_width: Expr = dturb * speed_deviation
    hydraulic_power: Expr = mechanical_gate - water_flow - qnl
    raw_turbine_power: Expr = at * hydraulic_power - deadband_power_width
    power_deadband: Expr = Const(settings.db2 / settings.mwbase)
    nonlinear_turbine: Expr = (
        sym.max(raw_turbine_power - power_deadband, Const(0.0))
        + sym.min(raw_turbine_power + power_deadband, Const(0.0))
    )
    mechanical_power: Var = control.algebraic(
        'PmPu', nonlinear_turbine,
        Const(settings.at * (initial_gate - settings.qnl)),
    )
    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovHydro3 modified IEEE hydro governor and turbine',
    )

    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    template.comment = 'CGMES GovHydro3 selectable PID/double-derivative hydro equations.'
    rdf_parameter_names: tuple[str, ...] = (
        'enabled', 'mwbase', 'pmax', 'pmin', 'governorControl', 'rgate',
        'relec', 'td', 'tf', 'tp', 'velop', 'velcl', 'k1', 'k2', 'ki', 'kg',
        'tt', 'db1', 'eps', 'db2', 'tw', 'at', 'dturb', 'qnl', 'h0', 'gv1',
        'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5',
        'gv6', 'pgv6',
    )
    for parameter_name in rdf_parameter_names:
        parameter_variable: Var = vfactory.add_var(
            f'GovHydro3.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template


def build_gov_hydro3_curve(
        gate: Expr,
        gv_points: tuple[Var, Var, Var, Var, Var, Var],
        pgv_points: tuple[Var, Var, Var, Var, Var, Var],
        curve_default: bool,
        curve_point_count: int,
        include_origin_segment: bool,
        include_full_open_segment: bool,
) -> Expr:
    """Build the six-point gate-to-power curve shown by the CGMES model.

    :param gate: Gate position normalized by Pmax.
    :param gv_points: Gate-axis curve parameters.
    :param pgv_points: Paired turbine-power curve parameters.
    :param curve_default: Whether the RDF selects the standard default curve.
    :param curve_point_count: Number of configured curve points.
    :param include_origin_segment: Whether to connect the first point to ``(0, 0)``.
    :param include_full_open_segment: Whether to connect the last point to ``(1, 1)``.
    :return: Normalized piecewise-linear curve or the assumed unit line.
    """
    if curve_default:
        return gate
    else:
        expression: Expr = Const(0.0)
        if include_origin_segment:
            first_gate: Var = gv_points[0]
            first_power: Var = pgv_points[0]
            origin_gate: Expr = sym.min(
                sym.max(gate, Const(0.0)), first_gate,
            )
            expression = expression + first_power * origin_gate / first_gate
        else:
            pass
        for point_index in range(curve_point_count - 1):
            lower_gate: Var = gv_points[point_index]
            upper_gate: Var = gv_points[point_index + 1]
            lower_power: Var = pgv_points[point_index]
            upper_power: Var = pgv_points[point_index + 1]
            span: Expr = upper_gate - lower_gate
            segment: Expr = sym.min(sym.max(gate - lower_gate, Const(0.0)), span)
            expression = expression + (upper_power - lower_power) * segment / span
        if include_full_open_segment:
            final_gate: Var = gv_points[curve_point_count - 1]
            final_power: Var = pgv_points[curve_point_count - 1]
            upper_gate: Expr = sym.min(
                sym.max(gate - final_gate, Const(0.0)),
                Const(1.0) - final_gate,
            )
            expression = expression + (
                (Const(1.0) - final_power) * upper_gate
                / (Const(1.0) - final_gate)
            )
        else:
            pass
        return expression


def get_gov_hydro3_curve_power(parameters: GovHydro3Parameters, gate: float) -> float:
    """Evaluate the same curve used by the equation block for initialization.

    :param parameters: Imported GovHydro3 curve.
    :param gate: Gate position.
    :return: Turbine power at that gate position.
    """
    curve_default: bool = parameters.gv_points[0] < 0.0 or all(
        value == 0.0 for value in parameters.gv_points + parameters.pgv_points
    )
    if curve_default:
        return gate
    else:
        normalized_gate: float = gate / parameters.pmax
        curve_point_count: int = max(
            (
                point_index + 1
                for point_index in range(6)
                if parameters.gv_points[point_index] != 0.0
                or parameters.pgv_points[point_index] != 0.0
            ),
            default=0,
        )
        first_gate: float = parameters.gv_points[0]
        first_power: float = parameters.pgv_points[0]
        if first_gate > 0.0:
            curve_power: float = first_power * min(normalized_gate, first_gate) / first_gate
        else:
            curve_power = first_power
        for point_index in range(curve_point_count - 1):
            lower_gate: float = parameters.gv_points[point_index]
            upper_gate: float = parameters.gv_points[point_index + 1]
            lower_power: float = parameters.pgv_points[point_index]
            upper_power: float = parameters.pgv_points[point_index + 1]
            segment: float = min(
                max(normalized_gate - lower_gate, 0.0), upper_gate - lower_gate,
            )
            curve_power += (upper_power - lower_power) * segment / (upper_gate - lower_gate)
        final_gate: float = parameters.gv_points[curve_point_count - 1]
        final_power: float = parameters.pgv_points[curve_point_count - 1]
        if final_gate < 1.0:
            upper_segment: float = min(
                max(normalized_gate - final_gate, 0.0), 1.0 - final_gate,
            )
            curve_power += (
                (1.0 - final_power) * upper_segment / (1.0 - final_gate)
            )
        else:
            pass
        return parameters.pmax * curve_power


def get_gov_hydro3_gate_for_power(
        parameters: GovHydro3Parameters,
        target_power: float,
) -> float | None:
    """Invert the monotone turbine curve for the imported operating point.

    :param parameters: Imported GovHydro3 curve and gate limits.
    :param target_power: Desired curve power.
    :return: Gate position or ``None`` when the target is outside its curve.
    """
    curve_default: bool = parameters.gv_points[0] < 0.0 or all(
        value == 0.0 for value in parameters.gv_points + parameters.pgv_points
    )
    if curve_default:
        return min(max(target_power, parameters.pmin), parameters.pmax)
    else:
        normalized_target: float = target_power / parameters.pmax
        curve_point_count: int = max(
            (
                point_index + 1
                for point_index in range(6)
                if parameters.gv_points[point_index] != 0.0
                or parameters.pgv_points[point_index] != 0.0
            ),
            default=0,
        )
        if normalized_target < 0.0 or normalized_target > 1.0:
            return None
        elif normalized_target == parameters.pgv_points[0]:
            gate_result: float = parameters.pmax * parameters.gv_points[0]
        elif normalized_target < parameters.pgv_points[0]:
            normalized_gate: float = parameters.gv_points[0] + (
                normalized_target * parameters.gv_points[0]
                / parameters.pgv_points[0]
            )
            gate_result: float = parameters.pmax * normalized_gate
        elif normalized_target > parameters.pgv_points[curve_point_count - 1]:
            final_power: float = parameters.pgv_points[curve_point_count - 1]
            final_gate: float = parameters.gv_points[curve_point_count - 1]
            normalized_gate = final_gate + (
                (normalized_target - final_power) * (1.0 - final_gate)
                / (1.0 - final_power)
            )
            gate_result = parameters.pmax * normalized_gate
        else:
            gate_result = 0.0
            for point_index in range(curve_point_count - 1):
                lower_power: float = parameters.pgv_points[point_index]
                upper_power: float = parameters.pgv_points[point_index + 1]
                if lower_power <= normalized_target <= upper_power:
                    if upper_power > lower_power:
                        fraction: float = (
                            (normalized_target - lower_power)
                            / (upper_power - lower_power)
                        )
                        normalized_gate = parameters.gv_points[point_index] + fraction * (
                            parameters.gv_points[point_index + 1]
                            - parameters.gv_points[point_index]
                        )
                        gate_result = parameters.pmax * normalized_gate
                    elif normalized_target == lower_power:
                        gate_result = (
                            parameters.pmax * parameters.gv_points[point_index]
                        )
                    else:
                        pass
                else:
                    pass
        if gate_result < parameters.pmin or gate_result > parameters.pmax:
            return None
        else:
            return gate_result
