# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydroPID governor and turbine."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.common.speed_deadband import (
    build_intentional_speed_deadband,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydroPIDParameters:
    """GovHydroPID coefficients retaining their canonical RDF field names."""

    __slots__ = (
        'mwbase', 'pmax', 'pmin', 'r', 'td', 'tf', 'tp', 'velop', 'velcl',
        'kd', 'kp', 'ki', 'kg', 'tturb', 'aturb', 'bturb', 'tt', 'db1',
        'inputSignal', 'eps', 'db2', 'gv_points', 'pgv_points',
        'nominal_frequency',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            pmax: float = 1.0,
            pmin: float = 0.0,
            r: float = 0.05,
            td: float = 0.0,
            tf: float = 0.1,
            tp: float = 0.35,
            velop: float = 0.09,
            velcl: float = -0.14,
            kd: float = 1.11,
            kp: float = 0.1,
            ki: float = 0.36,
            kg: float = 2.5,
            tturb: float = 0.8,
            aturb: float = -1.0,
            bturb: float = 0.5,
            tt: float = 0.02,
            db1: float = 0.0,
            inputSignal: bool = True,
            eps: float = 0.0,
            db2: float = 0.0,
            gv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            pgv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            nominal_frequency: float = 50.0,
    ) -> None:
        """Store parsed values in their CGMES units.

        :param mwbase: Governor active-power base in MW.
        :param pmax: Maximum gate position.
        :param pmin: Minimum gate position.
        :param r: Steady-state droop coefficient.
        :param td: Speed detector time in seconds.
        :param tf: Derivative washout time in seconds.
        :param tp: Gate servo time in seconds.
        :param velop: Maximum positive gate rate in pu/s.
        :param velcl: Maximum negative gate rate in pu/s.
        :param kd: Derivative gain.
        :param kp: Proportional gain.
        :param ki: Integral gain per second.
        :param kg: Gate servo gain.
        :param tturb: Turbine time in seconds.
        :param aturb: Turbine numerator multiplier.
        :param bturb: Turbine denominator multiplier.
        :param tt: Electrical-power feedback time in seconds.
        :param db1: Intentional speed deadband in Hz.
        :param inputSignal: True selects Pe feedback; false selects gate feedback.
        :param eps: Intentional deadband hysteresis width in Hz.
        :param db2: Unintentional turbine-power deadband in MW.
        :param gv_points: Six gate coordinates for the turbine characteristic.
        :param pgv_points: Six power values paired with gate coordinates.
        :param nominal_frequency: System frequency used to convert Hz to pu.
        """
        self.mwbase: float = mwbase
        self.pmax: float = pmax
        self.pmin: float = pmin
        self.r: float = r
        self.td: float = td
        self.tf: float = tf
        self.tp: float = tp
        self.velop: float = velop
        self.velcl: float = velcl
        self.kd: float = kd
        self.kp: float = kp
        self.ki: float = ki
        self.kg: float = kg
        self.tturb: float = tturb
        self.aturb: float = aturb
        self.bturb: float = bturb
        self.tt: float = tt
        self.db1: float = db1
        self.inputSignal: bool = inputSignal
        self.eps: float = eps
        self.db2: float = db2
        self.gv_points: tuple[float, float, float, float, float, float] = gv_points
        self.pgv_points: tuple[float, float, float, float, float, float] = pgv_points
        self.nominal_frequency: float = nominal_frequency


def get_gov_hydro_pid_curve_point_count(
        parameters: GovHydroPIDParameters,
) -> int:
    """Return the number of configured gate/power pairs before zero padding.

    :param parameters: Parsed GovHydroPID curve data.
    :return: Active prefix length, from zero through six points.
    """
    return max(
        (
            point_index + 1
            for point_index in range(6)
            if parameters.gv_points[point_index] != 0.0
            or parameters.pgv_points[point_index] != 0.0
        ),
        default=0,
    )


def get_gov_hydro_pid_curve_value(
        parameters: GovHydroPIDParameters,
        gate: float,
) -> float:
    """Evaluate the scaled turbine curve between its assumed endpoints.

    :param parameters: Parsed curve data.
    :param gate: Gate position in per unit.
    :return: Turbine power in per unit on MWBASE.
    """
    curve_default: bool = parameters.gv_points[0] < 0.0 or all(
        value == 0.0 for value in parameters.gv_points + parameters.pgv_points
    )
    if curve_default:
        return gate
    else:
        pass
    point_count: int = get_gov_hydro_pid_curve_point_count(parameters)
    normalized_gate: float = gate / parameters.pmax
    first_gate: float = parameters.gv_points[0]
    first_power: float = parameters.pgv_points[0]
    if first_gate > 0.0:
        origin_segment: float = min(max(normalized_gate, 0.0), first_gate)
        power: float = first_power * origin_segment / first_gate
    else:
        power = first_power
    for point_index in range(point_count - 1):
        lower_gate: float = parameters.gv_points[point_index]
        upper_gate: float = parameters.gv_points[point_index + 1]
        lower_power: float = parameters.pgv_points[point_index]
        upper_power: float = parameters.pgv_points[point_index + 1]
        segment: float = min(
            max(normalized_gate - lower_gate, 0.0), upper_gate - lower_gate,
        )
        power += (upper_power - lower_power) * segment / (upper_gate - lower_gate)
    final_gate: float = parameters.gv_points[point_count - 1]
    final_power: float = parameters.pgv_points[point_count - 1]
    if final_gate < 1.0:
        upper_segment: float = min(
            max(normalized_gate - final_gate, 0.0), 1.0 - final_gate,
        )
        power += (1.0 - final_power) * upper_segment / (1.0 - final_gate)
    else:
        pass
    return parameters.pmax * power


def get_gov_hydro_pid_gate_for_power(
        parameters: GovHydroPIDParameters,
        target_power: float,
) -> float | None:
    """Invert the scaled curve with assumed endpoints and configured gate stops.

    :param parameters: Parsed gate and power points.
    :param target_power: Required turbine output in per unit on MWBASE.
    :return: Gate position, or ``None`` when the target is outside gate stops.
    """
    curve_default: bool = parameters.gv_points[0] < 0.0 or all(
        value == 0.0 for value in parameters.gv_points + parameters.pgv_points
    )
    if curve_default:
        gate: float = target_power
    else:
        point_count: int = get_gov_hydro_pid_curve_point_count(parameters)
        normalized_target: float = target_power / parameters.pmax
        first_gate: float = parameters.gv_points[0]
        first_power: float = parameters.pgv_points[0]
        final_gate: float = parameters.gv_points[point_count - 1]
        final_power: float = parameters.pgv_points[point_count - 1]
        if normalized_target < 0.0 or normalized_target > 1.0:
            return None
        elif normalized_target == first_power:
            gate = parameters.pmax * first_gate
        elif normalized_target < first_power:
            gate = (
                parameters.pmax * first_gate
                * normalized_target / first_power
            )
        elif normalized_target > final_power:
            gate = parameters.pmax * (
                final_gate + (normalized_target - final_power)
                * (1.0 - final_gate) / (1.0 - final_power)
            )
        else:
            gate_result: float | None = None
            for point_index in range(point_count - 1):
                lower_power: float = parameters.pgv_points[point_index]
                upper_power: float = parameters.pgv_points[point_index + 1]
                if lower_power <= normalized_target <= upper_power:
                    if upper_power > lower_power:
                        fraction: float = (
                            (normalized_target - lower_power)
                            / (upper_power - lower_power)
                        )
                        gate_result = parameters.pmax * (
                            parameters.gv_points[point_index]
                            + fraction * (
                                parameters.gv_points[point_index + 1]
                                - parameters.gv_points[point_index]
                            )
                        )
                    elif normalized_target == lower_power:
                        gate_result = (
                            parameters.pmax * parameters.gv_points[point_index]
                        )
                    else:
                        pass
                else:
                    pass
            if gate_result is None:
                return None
            else:
                gate = gate_result
    if parameters.pmin <= gate <= parameters.pmax:
        return gate
    else:
        return None


def build_gov_hydro_p_i_d_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroPIDParameters | None = None,
) -> RmsModelTemplate:
    """Build the WSHYGP PID governor, gate servo, and water turbine equations.

    :param vfactory: Factory owning the model symbols.
    :param name: Optional unique runtime name.
    :param parameters: Parsed canonical GovHydroPID values.
    :return: Executable template with speed, reference, electrical-power, and Pm ports.
    :raises ValueError: Invalid times, gains, bounds, or nonlinear curve.
    """
    settings: GovHydroPIDParameters = (
        GovHydroPIDParameters() if parameters is None else parameters
    )
    values: tuple[float, ...] = (
        settings.mwbase, settings.pmax, settings.pmin, settings.r,
        settings.td, settings.tf, settings.tp, settings.velop, settings.velcl,
        settings.kd, settings.kp, settings.ki, settings.kg, settings.tturb,
        settings.aturb, settings.bturb, settings.tt, settings.db1, settings.eps,
        settings.db2, settings.nominal_frequency,
        *settings.gv_points, *settings.pgv_points,
    )
    curve_point_count: int = get_gov_hydro_pid_curve_point_count(settings)
    curve_default: bool = settings.gv_points[0] < 0.0 or all(
        value == 0.0 for value in settings.gv_points + settings.pgv_points
    )
    unused_curve_points_are_zero: bool = all(
        settings.gv_points[index] == 0.0
        and settings.pgv_points[index] == 0.0
        for index in range(curve_point_count, 6)
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('GovHydroPID parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.nominal_frequency <= 0.0:
        raise ValueError('GovHydroPID requires positive MWBASE and system frequency')
    elif min(settings.td, settings.tf, settings.tp, settings.tt, settings.tturb) < 0.0:
        raise ValueError('GovHydroPID times must be nonnegative')
    elif (
            settings.pmin < 0.0 or settings.pmin >= settings.pmax
            or settings.velcl > 0.0 or settings.velop < 0.0
    ):
        raise ValueError('GovHydroPID requires ordered gate bounds and signed gate rates')
    elif min(settings.r, settings.kp, settings.ki, settings.kg, settings.db1, settings.eps, settings.db2) < 0.0:
        raise ValueError('GovHydroPID gains and deadbands must be nonnegative')
    elif settings.tturb > 0.0 and settings.bturb <= 0.0:
        raise ValueError('GovHydroPID positive turbine time requires positive BTURB')
    elif not curve_default and (
            not unused_curve_points_are_zero
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
        raise ValueError('GovHydroPID curve points must match assumed endpoints and increase')
    else:
        pass

    template_name: str = 'GovHydroPID' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    droop: Var = control.parameter('GovHydroPID.r', settings.r)
    td: Var = control.parameter('GovHydroPID.td', settings.td)
    tf: Var = control.parameter('GovHydroPID.tf', settings.tf)
    tp: Var = control.parameter('GovHydroPID.tp', settings.tp)
    velop: Var = control.parameter('GovHydroPID.velop', settings.velop)
    velcl: Var = control.parameter('GovHydroPID.velcl', settings.velcl)
    kd: Var = control.parameter('GovHydroPID.kd', settings.kd)
    kp: Var = control.parameter('GovHydroPID.kp', settings.kp)
    ki: Var = control.parameter('GovHydroPID.ki', settings.ki)
    kg: Var = control.parameter('GovHydroPID.kg', settings.kg)
    tturb: Var = control.parameter('GovHydroPID.tturb', settings.tturb)
    aturb: Var = control.parameter('GovHydroPID.aturb', settings.aturb)
    bturb: Var = control.parameter('GovHydroPID.bturb', settings.bturb)
    tt: Var = control.parameter('GovHydroPID.tt', settings.tt)
    db1: Var = control.parameter('GovHydroPID.db1', settings.db1)
    eps: Var = control.parameter('GovHydroPID.eps', settings.eps)
    db2: Var = control.parameter('GovHydroPID.db2', settings.db2)
    pmax: Var = control.parameter('GovHydroPID.pmax', settings.pmax)
    pmin: Var = control.parameter('GovHydroPID.pmin', settings.pmin)
    control.parameter('GovHydroPID.mwbase', settings.mwbase)
    control.parameter('GovHydroPID.inputSignal', float(settings.inputSignal))
    gv_points: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        control.parameter(f'GovHydroPID.gv{index + 1}', settings.gv_points[index])
        for index in range(6)
    )
    pgv_points: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        control.parameter(f'GovHydroPID.pgv{index + 1}', settings.pgv_points[index])
        for index in range(6)
    )

    # The intentional speed deadband precedes its optional detector lag.
    speed: Var = control.input('OmegaPu', Const(1.0))
    power_reference: Var = control.input('PRefPu', Const(settings.r * 0.5))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.5))
    speed_deviation: Var = control.algebraic(
        'SpeedDeviationPu', speed - Const(1.0), Const(0.0),
    )
    deadbanded_speed: Expr = build_intentional_speed_deadband(
        control=control,
        speed_deviation=speed_deviation,
        deadband_threshold=db1 / Const(settings.nominal_frequency),
        hysteresis_width=eps / Const(settings.nominal_frequency),
    )
    filtered_speed: Var = control.lag(
        'SpeedDetectorPu', deadbanded_speed, td, settings.td, Const(0.0),
    )

    # RDF Flag selects electrical power or control-valve feedback into droop.
    gate_position: Var = vfactory.add_var(f'GatePu_{template_name}')
    if settings.inputSignal:
        feedback: Var = control.lag(
            'ElectricalPowerFeedbackPu', electrical_power, tt, settings.tt,
            Const(0.5),
        )
    else:
        feedback = control.algebraic('ControlValveFeedbackPu', gate_position, Const(0.5))
    controller_error: Expr = power_reference - filtered_speed - droop * feedback
    proportional: Expr = kp * controller_error
    integral: Var = control.differential(
        vfactory.add_var(f'IntegralPu_{template_name}'),
        ki * controller_error,
        Const(0.5),
    )
    if settings.tf > 0.0:
        derivative: Var = control.washout(
            'DerivativePu', controller_error, tf, settings.tf,
            kd / tf, Const(0.0),
        )
    elif settings.kd != 0.0:
        # The CGMES EA note sets TF to four integration steps when Kd is active.
        integration_step: Var = control.parameter('IntegrationStepSec', 0.001)
        derivative_time: Expr = Const(4.0) * integration_step
        derivative = control.washout(
            'DerivativePu', controller_error, derivative_time, 0.004,
            kd / derivative_time, Const(0.0),
        )
    else:
        derivative = control.algebraic('DerivativePu', Const(0.0), Const(0.0))
    controller_output: Var = control.algebraic(
        'ControllerOutputPu', proportional + integral + derivative, Const(0.5),
    )

    # The servo limits gate velocity before gate position integrates to its stops.
    servo_output: Var = control.lag(
        'GateServoPu', kg * (controller_output - gate_position),
        tp, settings.tp, Const(0.0),
    )
    gate_rate: Var = control.algebraic(
        'GateRatePuPerSecond', sym.hard_sat(servo_output, velcl, velop), Const(0.0),
    )
    control.differential(gate_position, gate_rate, Const(0.5), pmin, pmax)

    # The CGMES curve uses normalized coordinates and Pmax scales both axes.
    if curve_default:
        curve_expression: Expr = gate_position
        curve_initial: float = 0.5
    else:
        normalized_gate: Expr = gate_position / pmax
        curve_expression = Const(0.0)
        if settings.gv_points[0] > 0.0:
            origin_gate: Expr = sym.min(
                sym.max(normalized_gate, Const(0.0)), gv_points[0],
            )
            curve_expression = curve_expression + pgv_points[0] * origin_gate / gv_points[0]
        else:
            pass
        for curve_index in range(curve_point_count - 1):
            segment_width: Expr = gv_points[curve_index + 1] - gv_points[curve_index]
            segment: Expr = sym.min(
                sym.max(normalized_gate - gv_points[curve_index], Const(0.0)),
                segment_width,
            )
            curve_expression = curve_expression + (
                (pgv_points[curve_index + 1] - pgv_points[curve_index])
                * segment / segment_width
            )
        final_gate: Var = gv_points[curve_point_count - 1]
        final_power: Var = pgv_points[curve_point_count - 1]
        if settings.gv_points[curve_point_count - 1] < 1.0:
            upper_segment: Expr = sym.min(
                sym.max(normalized_gate - final_gate, Const(0.0)),
                Const(1.0) - final_gate,
            )
            curve_expression = curve_expression + (
                (Const(1.0) - final_power) * upper_segment
                / (Const(1.0) - final_gate)
            )
        else:
            pass
        curve_expression = pmax * curve_expression
        curve_initial = get_gov_hydro_pid_curve_value(settings, 0.5)
    curve_power: Var = control.algebraic(
        'CurvePowerPu', curve_expression, Const(curve_initial),
    )
    if settings.db2 > 0.0:
        deadbanded_power: Expr = (
            sym.max(curve_power - db2 / settings.mwbase, Const(0.0))
            + sym.min(curve_power + db2 / settings.mwbase, Const(0.0))
        )
    else:
        deadbanded_power = curve_power
    if curve_initial > 0.0:
        turbine_initial: float = max(curve_initial - settings.db2 / settings.mwbase, 0.0)
    elif curve_initial < 0.0:
        turbine_initial = min(curve_initial + settings.db2 / settings.mwbase, 0.0)
    else:
        turbine_initial = 0.0
    if settings.tturb > 0.0:
        turbine_memory: Var = control.lag(
            'TurbineMemoryPu', deadbanded_power, bturb * tturb,
            settings.bturb * settings.tturb, Const(turbine_initial),
        )
        turbine_power: Expr = turbine_memory + aturb / bturb * (
            deadbanded_power - turbine_memory
        )
    else:
        turbine_power = deadbanded_power
    mechanical_power: Var = control.algebraic('PmPu', turbine_power, Const(turbine_initial))

    template: RmsModelTemplate = control.finish(
        (mechanical_power, gate_position, gate_rate),
        'CGMES GovHydroPID WSHYGP three-term electrohydraulic governor and turbine',
    )
    parameter_only_template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    parameter_only_template.block.children.append(template.block)
    parameter_only_template.block.name = template_name
    parameter_only_template.comment = template.comment
    for parameter_name in (
            'enabled', 'mwbase', 'pmax', 'pmin', 'r', 'td', 'tf', 'tp',
            'velop', 'velcl', 'kd', 'kp', 'ki', 'kg', 'tturb', 'aturb',
            'bturb', 'tt', 'db1', 'inputSignal', 'eps', 'db2', 'gv1',
            'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5',
            'pgv5', 'gv6', 'pgv6',
    ):
        parameter_variable: Var = vfactory.add_var(
            f'GovHydroPID.{parameter_name}_{template_name}'
        )
        parameter_only_template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=parameter_variable.name,
        )
    return parameter_only_template
