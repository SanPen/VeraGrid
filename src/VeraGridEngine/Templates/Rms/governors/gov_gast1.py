# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovGAST1 modified single-shaft gas turbine."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.common.speed_deadband import (
    build_intentional_speed_deadband,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovGAST1Parameters:
    """Construction values for the five-state GAST_GE realization."""

    __slots__ = (
        'mwbase', 'r', 't1', 't2', 't3', 'lmax', 'kt', 'vmax', 'vmin', 'fidle',
        'rmax', 'loadinc', 'tltr', 'ltrate', 'a', 'b', 'db1', 'eps', 'db2',
        'gv_points', 'pgv_points', 'ka', 't4', 't5', 'nominal_frequency',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            r: float = 0.04,
            t1: float = 0.5,
            t2: float = 0.5,
            t3: float = 3.0,
            lmax: float = 1.0,
            kt: float = 3.0,
            vmax: float = 1.0,
            vmin: float = 0.0,
            fidle: float = 0.18,
            rmax: float = 1.0,
            loadinc: float = 0.05,
            tltr: float = 10.0,
            ltrate: float = 0.02,
            a: float = 0.8,
            b: float = 1.0,
            db1: float = 0.0,
            eps: float = 0.0,
            db2: float = 0.0,
            gv_points: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            pgv_points: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ka: float = 0.0,
            t4: float = 0.0,
            t5: float = 0.0,
            nominal_frequency: float = 50.0,
    ) -> None:
        """Store the parsed CGMES values used by the GAST_GE equations.

        :param mwbase: Governor rating in MW.
        :param r: Permanent speed droop in per unit.
        :param t1: Valve integrator time in seconds.
        :param t2: Turbine power time in seconds.
        :param t3: Exhaust-temperature/load-limit time in seconds.
        :param lmax: Ambient load limit in per unit.
        :param kt: Temperature feedback gain.
        :param vmax: Maximum valve position.
        :param vmin: Minimum valve position.
        :param fidle: Fuel flow at zero power.
        :param rmax: Fast valve opening-rate limit in per unit per second.
        :param loadinc: Valve-average differential selecting the long-term rate.
        :param tltr: Valve averaging time in seconds.
        :param ltrate: Long-term valve opening-rate limit in per unit per second.
        :param a: Turbine lead numerator scale.
        :param b: Turbine lag denominator scale.
        :param db1: Intentional speed deadband in Hz.
        :param eps: Intentional deadband hysteresis width in Hz.
        :param db2: Unintentional power deadband in MW.
        :param gv_points: Six valve-curve input points.
        :param pgv_points: Six valve-curve output points.
        :param ka: Governor gain.
        :param t4: Governor lead time in seconds.
        :param t5: Governor lag time in seconds.
        :param nominal_frequency: System nominal frequency in Hz.
        """
        self.mwbase: float = mwbase
        self.r: float = r
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.lmax: float = lmax
        self.kt: float = kt
        self.vmax: float = vmax
        self.vmin: float = vmin
        self.fidle: float = fidle
        self.rmax: float = rmax
        self.loadinc: float = loadinc
        self.tltr: float = tltr
        self.ltrate: float = ltrate
        self.a: float = a
        self.b: float = b
        self.db1: float = db1
        self.eps: float = eps
        self.db2: float = db2
        self.gv_points: tuple[float, ...] = gv_points
        self.pgv_points: tuple[float, ...] = pgv_points
        self.ka: float = ka
        self.t4: float = t4
        self.t5: float = t5
        self.nominal_frequency: float = nominal_frequency


def build_gast1_curve(
        gate: Expr,
        gate_points: tuple[Var, ...],
        power_points: tuple[Var, ...],
        gate_values: tuple[float, ...],
        power_values: tuple[float, ...],
        vmax: Var,
        vmax_value: float,
) -> Expr:
    """Build the standard-clamped Gv-to-Pgv curve, including its default.

    :param gate: Governor lead-lag output.
    :param gate_points: Symbolic Gv breakpoints.
    :param power_points: Symbolic Pgv ordinates.
    :param gate_values: Construction values used for default-curve selection and segments.
    :param power_values: Construction values used for default-curve selection.
    :param vmax: Runtime maximum turbine power.
    :param vmax_value: Construction maximum selecting curve scaling.
    :return: Piecewise-linear power expression.
    """
    if vmax_value > 1.0:
        curve_input: Expr = gate / vmax
        output_scale: Expr = vmax
    else:
        curve_input = gate
        output_scale = Const(1.0)

    if all(value == 0.0 for value in gate_values + power_values):
        curve_output: Expr = sym.hard_sat(curve_input, Const(0.0), Const(1.0))
    else:
        curve_output = power_points[0]
        for point_index in range(5):
            lower_gate: Var = gate_points[point_index]
            upper_gate: Var = gate_points[point_index + 1]
            lower_power: Var = power_points[point_index]
            upper_power: Var = power_points[point_index + 1]
            width: float = gate_values[point_index + 1] - gate_values[point_index]
            if width > 0.0:
                increment: Expr = sym.min(
                    sym.max(curve_input - lower_gate, Const(0.0)),
                    upper_gate - lower_gate,
                )
                curve_output = curve_output + (
                    (upper_power - lower_power) / (upper_gate - lower_gate) * increment
                )
            else:
                pass
        curve_output = sym.hard_sat(curve_output, Const(0.0), Const(1.0))
    return output_scale * curve_output


def build_gov_g_a_s_t1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovGAST1Parameters | None = None,
) -> RmsModelTemplate:
    """Build an equation-backed CGMES GAST_GE governor template.

    :param vfactory: Factory used to allocate equation and parameter symbols.
    :param name: Optional unique runtime name.
    :param parameters: Parsed RDF settings used for exact zero-time reductions.
    :return: Governor template with open shaft-speed and power-reference ports.
    :raises ValueError: Invalid time constants, rate limits, or curve data.
    """
    settings: GovGAST1Parameters = GovGAST1Parameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.r, settings.t1, settings.t2, settings.t3,
        settings.lmax, settings.kt, settings.vmax, settings.vmin, settings.fidle,
        settings.rmax, settings.loadinc, settings.tltr, settings.ltrate, settings.a,
        settings.b, settings.db1, settings.eps, settings.db2, settings.ka,
        settings.t4, settings.t5, settings.nominal_frequency,
    ) + settings.gv_points + settings.pgv_points
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovGAST1 parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.r <= 0.0 or settings.b <= 0.0:
        raise ValueError('GovGAST1 MWBASE, droop, and turbine denominator must be positive')
    elif min(settings.t1, settings.t2, settings.t3, settings.tltr, settings.t4, settings.t5) < 0.0:
        raise ValueError('GovGAST1 time constants must be nonnegative')
    elif settings.vmin >= settings.vmax or min(settings.rmax, settings.ltrate, settings.loadinc) < 0.0:
        raise ValueError('GovGAST1 limits and rates are invalid')
    elif settings.nominal_frequency <= 0.0 or len(settings.gv_points) != 6 or len(settings.pgv_points) != 6:
        raise ValueError('GovGAST1 requires a positive nominal frequency and six curve points')
    elif any(settings.gv_points[index] > settings.gv_points[index + 1] for index in range(5)):
        raise ValueError('GovGAST1 Gv curve points must be nondecreasing')
    else:
        pass

    template_name: str = 'GovGAST1' if name is None else name
    builder: ControlRealization = ControlRealization(vfactory, template_name)
    droop: Var = builder.parameter('R', settings.r)
    t1: Var = builder.parameter('T1', settings.t1)
    t2: Var = builder.parameter('T2', settings.t2)
    t3: Var = builder.parameter('T3', settings.t3)
    t4: Var = builder.parameter('T4', settings.t4)
    t5: Var = builder.parameter('T5', settings.t5)
    ka: Var = builder.parameter('KA', settings.ka)
    a: Var = builder.parameter('A', settings.a)
    b: Var = builder.parameter('B', settings.b)
    vmax: Var = builder.parameter('VMAX', settings.vmax)
    vmin: Var = builder.parameter('VMIN', settings.vmin)
    lmax: Var = builder.parameter('LMAX', settings.lmax)
    kt: Var = builder.parameter('KT', settings.kt)
    fidle: Var = builder.parameter('FIDLE', settings.fidle)
    rmax: Var = builder.parameter('RMAX', settings.rmax)
    loadinc: Var = builder.parameter('LOADINC', settings.loadinc)
    ltrate: Var = builder.parameter('LTRATE', settings.ltrate)
    db1: Var = builder.parameter('DB1', settings.db1)
    eps: Var = builder.parameter('EPS', settings.eps)
    db2: Var = builder.parameter('DB2', settings.db2)
    speed: Var = builder.input('OmegaPu', Const(1.0))
    power_reference: Var = builder.input('PRefPu', Const(0.5))

    # Convert the RDF frequency thresholds to pu and retain their source hysteresis modes.
    speed_signal: Expr = speed - Const(1.0)
    deadbanded_speed: Expr = build_intentional_speed_deadband(
        builder,
        speed_signal,
        db1 / Const(settings.nominal_frequency),
        eps / Const(settings.nominal_frequency),
    )
    governor_error: Expr = power_reference - deadbanded_speed / droop
    input_filter: Var = builder.lead_lag(
        'InputLeadLagPu', governor_error, t4, t5,
        0.0 if settings.t5 == 0.0 else settings.t4,
        settings.t5,
        power_reference,
    )
    if settings.t5 == 0.0:
        # The local CGMES EA note explicitly bypasses the complete gain and lead-lag block.
        governor_command: Expr = input_filter
    else:
        governor_command = ka * input_filter
    equilibrium_temperature_ceiling: Expr = fidle + lmax
    valve_initial: Expr = sym.hard_sat(
        sym.min(governor_command, equilibrium_temperature_ceiling), vmin, vmax
    )

    # The valve-position average selects the slower opening-rate regime after
    # a sustained positive valve movement.
    valve_average: Var = vfactory.add_var(name=f'ValveAveragePu_{template_name}')
    valve_average_time: Var = builder.parameter('TLTR', settings.tltr)
    valve_state: Var = vfactory.add_var(name=f'ValvePositionPu_{template_name}')
    builder.lag(
        'ValveAveragePu', valve_state, valve_average_time, settings.tltr,
        valve_initial, output=valve_average,
    )
    valve_deviation: Expr = valve_state - valve_average
    selected_open_rate: Expr = ltrate + (rmax - ltrate) * (
        Const(1.0) - sym.heaviside(valve_deviation - loadinc)
    )
    load_limit_state: Var = vfactory.add_var(name=f'LoadLimitPu_{template_name}')
    temperature_limit: Expr = fidle + lmax - kt * (load_limit_state - lmax)
    valve_target: Expr = sym.min(governor_command, temperature_limit)
    bounded_valve_rate: Expr = sym.hard_sat(
        (valve_target - valve_state) / t1,
        -selected_open_rate,
        selected_open_rate,
    )
    if settings.t1 > 0.0:
        builder.differential(
            valve_state,
            bounded_valve_rate,
            valve_initial,
            vmin,
            vmax,
        )
    else:
        builder.block.algebraic_vars.append(valve_state)
        builder.block.algebraic_eqs.append(
            valve_state - sym.hard_sat(valve_target, vmin, vmax)
        )
        builder.block.init_eqs[valve_state] = valve_initial

    # The turbine lead-lag and tabulated Gv/Pgv characteristic form the
    # governor power path; the zero-time turbine stage is an exact bypass.
    turbine_input: Expr = valve_state - fidle
    turbine_memory: Var = builder.lag(
        'TurbineMemoryPu', turbine_input, t2 * b, settings.t2 * settings.b,
        valve_initial - fidle,
    )
    if settings.t2 > 0.0:
        gate: Var = builder.algebraic(
            'GovernorGatePu', turbine_memory + (a / b) * (turbine_input - turbine_memory),
            valve_initial - fidle,
        )
    else:
        gate = builder.algebraic('GovernorGatePu', turbine_input, valve_initial - fidle)
    gate_points: tuple[Var, ...] = tuple(
        builder.parameter(f'GV{index + 1}', settings.gv_points[index]) for index in range(6)
    )
    power_points: tuple[Var, ...] = tuple(
        builder.parameter(f'PGV{index + 1}', settings.pgv_points[index]) for index in range(6)
    )
    # The integrator output is total fuel flow; Figure 50 removes FIDLE before T2 and Gv/Pgv.
    curve_power: Expr = build_gast1_curve(
        gate=gate,
        gate_points=gate_points,
        power_points=power_points,
        gate_values=settings.gv_points,
        power_values=settings.pgv_points,
        vmax=vmax,
        vmax_value=settings.vmax,
    )

    # Figure 50 applies T3 to net fuel flow and feeds its limit only to the valve selector.
    builder.lag(
        'LoadLimitMemoryPu', gate, t3, settings.t3,
        valve_initial - fidle,
        output=load_limit_state,
    )
    deadband_power: Expr = sym.max(
        curve_power - db2 / Const(settings.mwbase), Const(0.0)
    ) + sym.min(curve_power + db2 / Const(settings.mwbase), Const(0.0))
    mechanical_power: Var = builder.algebraic(
        'PmPu', deadband_power, deadband_power
    )

    runtime_template: RmsModelTemplate = builder.finish(
        (mechanical_power, valve_state),
        'CGMES GovGAST1 five-state GAST_GE governor and nonlinear turbine curve',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime_template.block)
    template.block.name = template_name
    template.comment = 'CGMES GovGAST1 equations using the GAST_GE block topology.'

    # Preserve the exact class-specific RDF fields for editing and round trips.
    rdf_parameter_names: tuple[str, ...] = (
        'enabled', 'mwbase', 'r', 't1', 't2', 't3', 'lmax', 'kt', 'vmax', 'vmin',
        'fidle', 'rmax', 'loadinc', 'tltr', 'ltrate', 'a', 'b', 'db1', 'eps', 'db2',
        'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5',
        'gv6', 'pgv6', 'ka', 't4', 't5',
    )
    for parameter_name in rdf_parameter_names:
        parameter_variable_name: str = f'GovGAST1.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(parameter_variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=parameter_variable_name,
        )
    return template
