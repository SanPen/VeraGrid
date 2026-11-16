# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES GovHydroWEH equations for the Woodward electric hydro governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydroWEHParameters:
    """GovHydroWEH coefficients in their canonical CGMES units."""

    __slots__ = (
        'mwbase', 'rpg', 'rpp', 'tpe', 'kp', 'ki', 'kd', 'td', 'tp', 'tdv',
        'tg', 'gtmxop', 'gtmxcl', 'gmax', 'gmin', 'dturb', 'tw', 'db', 'dpv',
        'dicn', 'feedbackSignal', 'gate_points', 'gate_flow_points',
        'turbine_flow_points', 'mechanical_power_points',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            rpg: float = 0.05,
            rpp: float = 0.05,
            tpe: float = 0.1,
            kp: float = 2.0,
            ki: float = 5.0,
            kd: float = 0.0,
            td: float = 0.05,
            tp: float = 0.1,
            tdv: float = 0.1,
            tg: float = 0.5,
            gtmxop: float = 0.2,
            gtmxcl: float = -0.2,
            gmax: float = 1.0,
            gmin: float = 0.0,
            dturb: float = 0.0,
            tw: float = 1.0,
            db: float = 0.0,
            dpv: float = 0.0,
            dicn: float = 0.0,
            feedbackSignal: bool = False,
            gate_points: tuple[float, float, float, float, float] = (
                0.0, 0.25, 0.5, 0.75, 1.0,
            ),
            gate_flow_points: tuple[float, float, float, float, float] = (
                0.0, 0.25, 0.5, 0.75, 1.0,
            ),
            turbine_flow_points: tuple[
                float, float, float, float, float, float, float, float, float, float
            ] = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0),
            mechanical_power_points: tuple[
                float, float, float, float, float, float, float, float, float, float
            ] = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0),
    ) -> None:
        """Store the CGMES scalars and the two imported characteristics.

        :param mwbase: Governor active-power base in MW.
        :param rpg: Permanent gate-position feedback gain.
        :param rpp: Permanent electrical-power feedback gain.
        :param tpe: Electrical-power transducer time in seconds.
        :param kp: Proportional controller gain.
        :param ki: Integral controller gain.
        :param kd: Derivative controller gain.
        :param td: Derivative filter time in seconds.
        :param tp: Pilot-valve servo time in seconds.
        :param tdv: Distribution-valve time in seconds.
        :param tg: Gate servo time in seconds.
        :param gtmxop: Maximum gate opening speed in pu/s.
        :param gtmxcl: Minimum gate closing speed in pu/s.
        :param gmax: Maximum gate position.
        :param gmin: Minimum gate position.
        :param dturb: Turbine speed damping gain.
        :param tw: Water starting time in seconds.
        :param db: Speed deadband width in pu.
        :param dpv: Pilot-valve travel limit modifier.
        :param dicn: Integral-controller limit modifier.
        :param feedbackSignal: Select PID-output feedback when true.
        :param gate_points: Five gate coordinates.
        :param gate_flow_points: Flow values at the five gate coordinates.
        :param turbine_flow_points: Ten flow coordinates for the power curve.
        :param mechanical_power_points: Mechanical powers at those flow coordinates.
        """
        self.mwbase: float = mwbase
        self.rpg: float = rpg
        self.rpp: float = rpp
        self.tpe: float = tpe
        self.kp: float = kp
        self.ki: float = ki
        self.kd: float = kd
        self.td: float = td
        self.tp: float = tp
        self.tdv: float = tdv
        self.tg: float = tg
        self.gtmxop: float = gtmxop
        self.gtmxcl: float = gtmxcl
        self.gmax: float = gmax
        self.gmin: float = gmin
        self.dturb: float = dturb
        self.tw: float = tw
        self.db: float = db
        self.dpv: float = dpv
        self.dicn: float = dicn
        self.feedbackSignal: bool = feedbackSignal
        self.gate_points: tuple[float, float, float, float, float] = gate_points
        self.gate_flow_points: tuple[float, float, float, float, float] = gate_flow_points
        self.turbine_flow_points: tuple[
            float, float, float, float, float, float, float, float, float, float
        ] = turbine_flow_points
        self.mechanical_power_points: tuple[
            float, float, float, float, float, float, float, float, float, float
        ] = mechanical_power_points


def _gov_hydro_weh_curve(
        control: ControlRealization,
        name: str,
        signal: Expr,
        x_values: tuple[float, ...],
        y_values: tuple[float, ...],
) -> Expr:
    """Build a clipped, piecewise-linear characteristic from RDF points.

    :param control: Model graph receiving the curve's parameter events.
    :param name: Unique event-name prefix.
    :param signal: Curve input signal.
    :param x_values: Strictly increasing input coordinates.
    :param y_values: Monotone output coordinates.
    :return: Continuous piecewise-linear output expression.
    """
    curve_x: list[Var] = list()
    curve_y: list[Var] = list()
    for point_index, coordinate in enumerate(x_values):
        curve_x.append(control.parameter(f'{name}X{point_index + 1}', coordinate))
        curve_y.append(control.parameter(f'{name}Y{point_index + 1}', y_values[point_index]))
    curve_expression: Expr = curve_y[0]
    for segment_index in range(len(curve_x) - 1):
        segment_width: Expr = curve_x[segment_index + 1] - curve_x[segment_index]
        segment_input: Expr = sym.min(
            sym.max(signal - curve_x[segment_index], Const(0.0)),
            segment_width,
        )
        segment_gain: Expr = (
            curve_y[segment_index + 1] - curve_y[segment_index]
        ) / segment_width
        curve_expression = curve_expression + segment_gain * segment_input
    return curve_expression


def get_gov_hydro_weh_operating_gate(
        parameters: GovHydroWEHParameters,
        operating_power: float,
) -> tuple[float, float] | None:
    """Invert the monotone power and gate-flow curves at an operating point.

    :param parameters: Imported GovHydroWEH characteristics.
    :param operating_power: Generator active power on MWBASE.
    :return: Gate and flow coordinates, or ``None`` outside either curve.
    """
    flow_value: float | None = None
    for point_index in range(9):
        lower_power: float = parameters.mechanical_power_points[point_index]
        upper_power: float = parameters.mechanical_power_points[point_index + 1]
        if lower_power <= operating_power <= upper_power:
            if upper_power > lower_power:
                power_fraction: float = (
                    (operating_power - lower_power) / (upper_power - lower_power)
                )
                flow_value = parameters.turbine_flow_points[point_index] + power_fraction * (
                    parameters.turbine_flow_points[point_index + 1]
                    - parameters.turbine_flow_points[point_index]
                )
            else:
                flow_value = parameters.turbine_flow_points[point_index]
        else:
            pass
    if flow_value is None:
        return None
    else:
        pass

    gate_value: float | None = None
    for point_index in range(4):
        lower_flow: float = parameters.gate_flow_points[point_index]
        upper_flow: float = parameters.gate_flow_points[point_index + 1]
        if lower_flow <= flow_value <= upper_flow:
            if upper_flow > lower_flow:
                flow_fraction: float = (flow_value - lower_flow) / (upper_flow - lower_flow)
                gate_value = parameters.gate_points[point_index] + flow_fraction * (
                    parameters.gate_points[point_index + 1]
                    - parameters.gate_points[point_index]
                )
            else:
                gate_value = parameters.gate_points[point_index]
        else:
            pass
    if gate_value is not None and parameters.gmin <= gate_value <= parameters.gmax:
        return gate_value, flow_value
    else:
        return None


def build_gov_hydro_w_e_h_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroWEHParameters | None = None,
) -> RmsModelTemplate:
    """Build the Woodward electric hydro governor and turbine equations.

    :param vfactory: Symbol factory owning all model variables.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical CGMES parameters and characteristics.
    :return: Equation-backed governor with speed, reference, and Pe inputs.
    :raises ValueError: Nonfinite, unordered, or physically invalid parameters.
    """
    settings: GovHydroWEHParameters = (
        GovHydroWEHParameters() if parameters is None else parameters
    )
    coefficients: tuple[float, ...] = (
        settings.mwbase, settings.rpg, settings.rpp, settings.tpe, settings.kp,
        settings.ki, settings.kd, settings.td, settings.tp, settings.tdv,
        settings.tg, settings.gtmxop, settings.gtmxcl, settings.gmax,
        settings.gmin, settings.dturb, settings.tw, settings.db, settings.dpv,
        settings.dicn, *settings.gate_points, *settings.gate_flow_points,
        *settings.turbine_flow_points, *settings.mechanical_power_points,
    )
    if not all(math.isfinite(value) for value in coefficients):
        raise ValueError('GovHydroWEH parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.tg <= 0.0 or settings.td < 0.0:
        raise ValueError('GovHydroWEH MWBASE/TG must be positive and TD nonnegative')
    elif min(settings.tpe, settings.tp, settings.tdv, settings.tw) < 0.0:
        raise ValueError('GovHydroWEH time constants must be nonnegative')
    elif settings.td == 0.0 and settings.kd != 0.0:
        raise ValueError(
            'GovHydroWEH TD=0 with nonzero KD is an ideal derivative and is not representable'
        )
    elif settings.gmin >= settings.gmax or settings.gtmxcl >= settings.gtmxop:
        raise ValueError('GovHydroWEH gate limits and rates must be ordered')
    elif min(settings.db, settings.dpv, settings.dicn, settings.rpg, settings.rpp) < 0.0:
        raise ValueError('GovHydroWEH deadband, modifiers, and droops must be nonnegative')
    elif any(
            settings.gate_points[index] >= settings.gate_points[index + 1]
            or settings.gate_flow_points[index] > settings.gate_flow_points[index + 1]
            for index in range(4)
    ):
        raise ValueError('GovHydroWEH gate-flow curve must be monotone')
    elif any(
            settings.turbine_flow_points[index] >= settings.turbine_flow_points[index + 1]
            or settings.mechanical_power_points[index] > settings.mechanical_power_points[index + 1]
            for index in range(9)
    ):
        raise ValueError('GovHydroWEH flow-power curve must be monotone')
    else:
        pass

    template_name: str = 'GovHydroWEH' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    speed: Var = control.input('OmegaPu', Const(1.0))
    reference: Var = control.input('ReferencePu', Const(0.5))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.5))
    power_filter: Var = control.lag(
        'PowerTransducerPu', electrical_power,
        control.parameter('TPE', settings.tpe), settings.tpe, Const(0.5),
    )

    # The source diagram selects either electrical-power droop and gate droop,
    # or the PID output feedback path with the Boolean feedbackSignal switch.
    controller_output: Var = vfactory.add_var(f'ControllerOutputPu_{template_name}')
    gate_state: Var = vfactory.add_var(f'GatePu_{template_name}')
    if settings.feedbackSignal:
        selected_power_feedback: Expr = Const(0.0)
        selected_gate_feedback: Expr = controller_output
    else:
        selected_power_feedback = power_filter
        selected_gate_feedback = gate_state
    speed_error: Expr = Const(1.0) - speed
    deadbanded_error: Expr = (
        sym.max(speed_error - settings.db / 2.0, Const(0.0))
        + sym.min(speed_error + settings.db / 2.0, Const(0.0))
    )
    controller_error: Expr = (
        deadbanded_error + reference - settings.rpp * selected_power_feedback
        - settings.rpg * selected_gate_feedback
    )
    integral: Var = control.differential(
        vfactory.add_var(f'IntegralControllerPu_{template_name}'),
        settings.ki * controller_error,
        Const(0.0),
        control.parameter('GMIN_DICN', settings.gmin - settings.dicn),
        control.parameter('GMAX_DICN', settings.gmax + settings.dicn),
    )
    derivative_time: Var = control.parameter('TD', settings.td)
    if settings.td > 0.0:
        derivative: Var = control.washout(
            'DerivativeControllerPu', controller_error,
            derivative_time, settings.td,
            settings.kd / settings.td, Const(0.0),
        )
    else:
        derivative = control.algebraic(
            'DerivativeControllerPu', Const(0.0), Const(0.0),
        )
    control.block.algebraic_vars.append(controller_output)
    control.block.algebraic_eqs.append(
        controller_output - settings.kp * controller_error - integral - derivative
    )
    control.block.init_eqs[controller_output] = Const(0.0)

    # Realize the pilot, distribution, and gate servos with explicit rate and
    # position stops; each positive time constant retains its physical state.
    pilot_valve: Var = control.lag(
        'PilotValvePu', controller_output,
        control.parameter('TP', settings.tp), settings.tp, Const(0.5),
        Const(settings.gmin - settings.dpv), Const(settings.gmax + settings.dpv),
    )
    distribution_error: Expr = pilot_valve - gate_state
    distribution_valve: Var = control.lag(
        'DistributionValvePu', distribution_error,
        control.parameter('TDV', settings.tdv), settings.tdv, Const(0.0),
        Const(settings.gtmxcl * settings.tg), Const(settings.gtmxop * settings.tg),
    )
    control.differential(
        gate_state,
        distribution_valve / control.parameter('TG', settings.tg),
        Const(0.5),
        control.parameter('GMIN', settings.gmin),
        control.parameter('GMAX', settings.gmax),
    )

    gate_flow_expression: Expr = _gov_hydro_weh_curve(
        control, 'GateFlowCurve', gate_state,
        settings.gate_points, settings.gate_flow_points,
    )
    gate_flow: Var = control.algebraic('GateFlowPu', gate_flow_expression, Const(0.5))
    turbine_flow: Var = vfactory.add_var(f'TurbineFlowPu_{template_name}')
    safe_gate_flow: Expr = sym.max(gate_flow, Const(1e-6))
    turbine_head: Var = control.algebraic(
        'TurbineHeadPu', (turbine_flow / safe_gate_flow) ** 2, Const(1.0),
    )
    if settings.tw > 0.0:
        control.differential(
            turbine_flow,
            (Const(1.0) - turbine_head)
            / control.parameter('TW', settings.tw),
            Const(0.5),
        )
    else:
        control.block.algebraic_vars.append(turbine_flow)
        control.block.algebraic_eqs.append(turbine_flow - gate_flow)
        control.block.init_eqs[turbine_flow] = Const(0.5)
    # The IEC diagram defines head from actual/steady-state flow and integrates
    # H0-h through 1/(s*TW), so no additional factor of two belongs here.
    mechanical_curve: Expr = _gov_hydro_weh_curve(
        control, 'TurbinePowerCurve', turbine_flow,
        settings.turbine_flow_points, settings.mechanical_power_points,
    )
    mechanical_power: Var = control.algebraic(
        'PmPu', mechanical_curve * turbine_head
        - settings.dturb * (speed - Const(1.0)) * gate_state,
        Const(0.5),
    )
    return control.finish(
        (mechanical_power, gate_state, distribution_valve),
        'CGMES GovHydroWEH Woodward electric hydro governor with imported curves',
    )
