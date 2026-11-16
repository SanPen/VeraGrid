# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydroDD double-derivative governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.common.speed_deadband import (
    build_intentional_speed_deadband,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


class GovHydroDDParameters:
    """CGMES GovHydroDD parameters for its controller and turbine."""

    __slots__ = (
        'mwbase', 'pmax', 'pmin', 'r', 'td', 'tf', 'tp', 'velop', 'velcl',
        'k1', 'k2', 'ki', 'kg', 'tturb', 'aturb', 'bturb', 'tt', 'db1',
        'eps', 'db2', 'gv_points', 'pgv_points', 'gmax', 'gmin', 'input_signal',
        'nominal_frequency',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            pmax: float = 1.0,
            pmin: float = 0.0,
            r: float = 0.05,
            td: float = 0.1,
            tf: float = 0.1,
            tp: float = 0.1,
            velop: float = 0.2,
            velcl: float = 0.2,
            k1: float = 1.0,
            k2: float = 0.2,
            ki: float = 0.5,
            kg: float = 1.0,
            tturb: float = 1.0,
            aturb: float = -1.0,
            bturb: float = 0.5,
            tt: float = 0.5,
            db1: float = 0.0,
            eps: float = 0.0,
            db2: float = 0.0,
            gv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            pgv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            gmax: float = 1.0,
            gmin: float = 0.0,
            input_signal: bool = True,
            nominal_frequency: float = 50.0,
    ) -> None:
        """Store imported values in MWbase, Hz, seconds, and per unit.

        :param mwbase: Governor active-power base in MW.
        :param pmax: Upper CV integrator limit.
        :param pmin: Lower CV integrator limit.
        :param r: Permanent feedback gain.
        :param td: Speed measurement filter time in seconds.
        :param tf: Derivative filter time in seconds.
        :param tp: Gate-servo lag time in seconds.
        :param velop: Maximum gate opening rate in pu/s.
        :param velcl: Positive maximum gate closing rate magnitude in pu/s.
        :param k1: Filtered first derivative coefficient.
        :param k2: Filtered second derivative coefficient.
        :param ki: CV integrator gain.
        :param kg: Gate servo gain.
        :param tturb: Turbine lead-lag time in seconds.
        :param aturb: Turbine numerator multiplier.
        :param bturb: Turbine denominator multiplier.
        :param tt: Electrical power feedback filter time in seconds.
        :param db1: Intentional speed deadband in Hz.
        :param eps: Intentional deadband hysteresis in Hz.
        :param db2: Mechanical-power deadband in MW.
        :param gv_points: Six gate curve coordinates.
        :param pgv_points: Six paired power curve coordinates.
        :param gmax: Upper gate travel limit.
        :param gmin: Lower gate travel limit.
        :param input_signal: True selects filtered electrical power, false CV feedback.
        :param nominal_frequency: Circuit frequency for converting Hz to pu.
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
        self.k1: float = k1
        self.k2: float = k2
        self.ki: float = ki
        self.kg: float = kg
        self.tturb: float = tturb
        self.aturb: float = aturb
        self.bturb: float = bturb
        self.tt: float = tt
        self.db1: float = db1
        self.eps: float = eps
        self.db2: float = db2
        self.gv_points: tuple[float, float, float, float, float, float] = gv_points
        self.pgv_points: tuple[float, float, float, float, float, float] = pgv_points
        self.gmax: float = gmax
        self.gmin: float = gmin
        self.input_signal: bool = input_signal
        self.nominal_frequency: float = nominal_frequency


def build_gov_hydro_d_d_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroDDParameters | None = None,
) -> RmsModelTemplate:
    """Build the filtered double-derivative governor and turbine equations.

    :param vfactory: Factory owning symbolic variables.
    :param name: Optional unique runtime template name.
    :param parameters: Imported CGMES coefficients and selector.
    :return: Executable governor with speed, reference, Pe and Pm ports.
    :raises ValueError: Invalid limits, transfer times, or curve.
    """
    settings: GovHydroDDParameters = (
        GovHydroDDParameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.pmax, settings.pmin, settings.r, settings.td,
        settings.tf, settings.tp, settings.velop, settings.velcl, settings.k1,
        settings.k2, settings.ki, settings.kg, settings.tturb, settings.aturb,
        settings.bturb, settings.tt, settings.db1, settings.eps, settings.db2,
        settings.gmax, settings.gmin, settings.nominal_frequency,
        *settings.gv_points, *settings.pgv_points,
    )
    curve_default: bool = all(
        value == 0.0 for value in settings.gv_points + settings.pgv_points
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovHydroDD parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.nominal_frequency <= 0.0:
        raise ValueError('GovHydroDD requires positive MWBASE and nominal frequency')
    elif settings.pmin >= settings.pmax or settings.gmin >= settings.gmax:
        raise ValueError('GovHydroDD requires increasing CV and gate limits')
    elif min(settings.td, settings.tf, settings.tp, settings.tt, settings.tturb) < 0.0:
        raise ValueError('GovHydroDD transfer times must be nonnegative')
    elif settings.tturb > 0.0 and settings.bturb <= 0.0:
        raise ValueError('GovHydroDD positive turbine time requires positive BTURB')
    elif settings.velop < 0.0 or settings.velcl < 0.0 or settings.ki < 0.0:
        raise ValueError('GovHydroDD gate rates and integrator gain must be nonnegative')
    elif min(settings.db1, settings.eps, settings.db2) < 0.0:
        raise ValueError('GovHydroDD deadband values must be nonnegative')
    elif not curve_default and not all(
            settings.gv_points[index] < settings.gv_points[index + 1]
            and settings.pgv_points[index] <= settings.pgv_points[index + 1]
            for index in range(5)
    ):
        raise ValueError('GovHydroDD curve gates must increase and power cannot decrease')
    else:
        pass

    template_name: str = 'GovHydroDD' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    mwbase: Var = control.parameter('GovHydroDD.mwbase', settings.mwbase)
    pmax: Var = control.parameter('GovHydroDD.pmax', settings.pmax)
    pmin: Var = control.parameter('GovHydroDD.pmin', settings.pmin)
    r: Var = control.parameter('GovHydroDD.r', settings.r)
    td: Var = control.parameter('GovHydroDD.td', settings.td)
    tf: Var = control.parameter('GovHydroDD.tf', settings.tf)
    tp: Var = control.parameter('GovHydroDD.tp', settings.tp)
    velop: Var = control.parameter('GovHydroDD.velop', settings.velop)
    velcl: Var = control.parameter('GovHydroDD.velcl', settings.velcl)
    k1: Var = control.parameter('GovHydroDD.k1', settings.k1)
    k2: Var = control.parameter('GovHydroDD.k2', settings.k2)
    ki: Var = control.parameter('GovHydroDD.ki', settings.ki)
    kg: Var = control.parameter('GovHydroDD.kg', settings.kg)
    tturb: Var = control.parameter('GovHydroDD.tturb', settings.tturb)
    aturb: Var = control.parameter('GovHydroDD.aturb', settings.aturb)
    bturb: Var = control.parameter('GovHydroDD.bturb', settings.bturb)
    tt: Var = control.parameter('GovHydroDD.tt', settings.tt)
    db1: Var = control.parameter('GovHydroDD.db1', settings.db1)
    eps: Var = control.parameter('GovHydroDD.eps', settings.eps)
    db2: Var = control.parameter('GovHydroDD.db2', settings.db2)
    gv_points: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        control.parameter(f'GovHydroDD.gv{index + 1}', settings.gv_points[index])
        for index in range(6)
    )
    pgv_points: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        control.parameter(f'GovHydroDD.pgv{index + 1}', settings.pgv_points[index])
        for index in range(6)
    )
    gmax: Var = control.parameter('GovHydroDD.gmax', settings.gmax)
    gmin: Var = control.parameter('GovHydroDD.gmin', settings.gmin)

    # The filter and double-derivative paths operate on the same deadbanded speed error.
    speed: Var = control.input('OmegaPu', Const(1.0))
    power_reference: Var = control.input('PRefPu', Const(0.5))
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
        control,
        speed_deviation,
        db1 / Const(settings.nominal_frequency),
        eps / Const(settings.nominal_frequency),
    )
    filtered_speed: Var = control.lag(
        'FilteredSpeedPu', deadbanded_speed, td, settings.td, Const(0.0),
    )
    if settings.tf > 0.0:
        first_derivative: Var = control.washout(
            'FirstDerivativePu', filtered_speed, tf, settings.tf, Const(1.0),
            Const(0.0),
        )
        second_derivative: Var = control.washout(
            'SecondDerivativePu', first_derivative, tf, settings.tf, Const(1.0),
            Const(0.0),
        )
    else:
        if settings.k1 == 0.0 and settings.k2 == 0.0:
            first_derivative = control.algebraic(
                'FirstDerivativePu', Const(0.0), Const(0.0),
            )
            second_derivative = control.algebraic(
                'SecondDerivativePu', Const(0.0), Const(0.0),
            )
        else:
            # RMS problem registration replaces this fallback with its configured step.
            integration_step: Var = control.parameter('IntegrationStepSec', 0.001)
            effective_tf: Expr = Const(4.0) * integration_step
            first_derivative_memory: Var = vfactory.add_var(
                f'FirstDerivativeMemoryPu_{template_name}',
            )
            control.differential(
                first_derivative_memory,
                (filtered_speed - first_derivative_memory) / effective_tf,
                Const(0.0),
            )
            first_derivative = control.algebraic(
                'FirstDerivativePu', filtered_speed - first_derivative_memory,
                Const(0.0),
            )
            second_derivative_memory: Var = vfactory.add_var(
                f'SecondDerivativeMemoryPu_{template_name}',
            )
            control.differential(
                second_derivative_memory,
                (first_derivative - second_derivative_memory) / effective_tf,
                Const(0.0),
            )
            second_derivative = control.algebraic(
                'SecondDerivativePu', first_derivative - second_derivative_memory,
                Const(0.0),
            )
    controller_signal: Var = control.algebraic(
        'ControllerSignalPu', filtered_speed + k1 * first_derivative
        + k2 * second_derivative, Const(0.0),
    )

    # The RDF switch selects filtered Pe or the CV loop's direct feedback.
    cv_state: Var = vfactory.add_var(f'ControlValvePu_{template_name}')
    if settings.input_signal:
        feedback_signal: Expr = control.lag(
            'FilteredElectricalPowerPu', electrical_power, tt, settings.tt,
            Const(0.5),
        )
    else:
        feedback_signal = cv_state
    control.differential(
        cv_state,
        ki * (power_reference - controller_signal - r * feedback_signal),
        Const(0.5), pmin, pmax,
    )
    gate_position: Var = vfactory.add_var(f'GatePositionPu_{template_name}')
    gate_servo: Var = control.lag(
        'GateServoPu', kg * (cv_state - gate_position), tp, settings.tp,
        Const(0.0),
    )
    gate_rate: Var = control.algebraic(
        'GateRatePuPerSecond', sym.hard_sat(gate_servo, -velcl, velop),
        Const(0.0),
    )
    control.differential(gate_position, gate_rate, Const(0.5), gmin, gmax)

    # Curve power is the gate axis for the turbine lead-lag and DB2 uses MWBASE.
    if curve_default:
        curve_expression: Expr = gate_position
        initial_curve: float = 0.5
    else:
        curve_expression = build_gov_hydro_dd_curve(gate_position, gv_points, pgv_points)
        initial_curve = get_gov_hydro_dd_curve_value(settings, 0.5)
    curve_power: Var = control.algebraic(
        'CurvePowerPu', curve_expression, Const(initial_curve),
    )
    power_deadband: Expr = db2 / mwbase
    deadbanded_power: Expr = (
        sym.max(curve_power - power_deadband, Const(0.0))
        + sym.min(curve_power + power_deadband, Const(0.0))
    )
    if settings.tturb > 0.0:
        turbine_memory: Var = control.lag(
            'TurbineMemoryPu', deadbanded_power, bturb * tturb,
            settings.bturb * settings.tturb, Const(initial_curve),
        )
        turbine_power: Expr = turbine_memory + aturb / bturb * (
            deadbanded_power - turbine_memory
        )
    else:
        turbine_power = deadbanded_power
    mechanical_power: Var = control.algebraic(
        'PmPu', turbine_power, Const(initial_curve),
    )
    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovHydroDD filtered double-derivative hydro governor',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    template.comment = 'CGMES GovHydroDD equations with inputSignal-selected feedback.'
    for parameter_name in (
            'enabled', 'mwbase', 'pmax', 'pmin', 'r', 'td', 'tf', 'tp',
            'velop', 'velcl', 'k1', 'k2', 'ki', 'kg', 'tturb', 'aturb',
            'bturb', 'tt', 'db1', 'eps', 'db2', 'gv1', 'pgv1', 'gv2',
            'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6',
            'pgv6', 'gmax', 'gmin', 'inputSignal',
    ):
        parameter_variable: Var = vfactory.add_var(
            f'GovHydroDD.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template


def build_gov_hydro_dd_curve(
        gate: Expr,
        gate_points: tuple[Var, Var, Var, Var, Var, Var],
        power_points: tuple[Var, Var, Var, Var, Var, Var],
) -> Expr:
    """Build the six-point gate-to-power curve from the RDF record.

    :param gate: Gate position signal.
    :param gate_points: Strictly increasing gate coordinates.
    :param power_points: Paired turbine-power coordinates.
    :return: Piecewise-linear power curve with endpoint extension.
    """
    expression: Expr = power_points[0]
    for point_index in range(5):
        lower_gate: Var = gate_points[point_index]
        upper_gate: Var = gate_points[point_index + 1]
        lower_power: Var = power_points[point_index]
        upper_power: Var = power_points[point_index + 1]
        span: Expr = upper_gate - lower_gate
        segment: Expr = sym.min(sym.max(gate - lower_gate, Const(0.0)), span)
        expression = expression + (upper_power - lower_power) * segment / span
    return expression


def get_gov_hydro_dd_curve_value(parameters: GovHydroDDParameters, gate: float) -> float:
    """Evaluate the curve for a consistent turbine state initialization.

    :param parameters: Imported curve parameters.
    :param gate: Initial gate position.
    :return: Curve power at the given gate.
    """
    if all(value == 0.0 for value in parameters.gv_points + parameters.pgv_points):
        return gate
    else:
        curve_value: float = parameters.pgv_points[0]
        for point_index in range(5):
            lower_gate: float = parameters.gv_points[point_index]
            upper_gate: float = parameters.gv_points[point_index + 1]
            lower_power: float = parameters.pgv_points[point_index]
            upper_power: float = parameters.pgv_points[point_index + 1]
            segment: float = min(max(gate - lower_gate, 0.0), upper_gate - lower_gate)
            curve_value += (upper_power - lower_power) * segment / (upper_gate - lower_gate)
        return curve_value


def get_gov_hydro_dd_gate_for_power(
        parameters: GovHydroDDParameters,
        target_power: float,
) -> float | None:
    """Invert the monotone gate curve for an imported generator operating point.

    :param parameters: Imported curve and gate limits.
    :param target_power: Desired turbine power in per unit.
    :return: Gate position, or ``None`` if the curve cannot reach the target.
    """
    if all(value == 0.0 for value in parameters.gv_points + parameters.pgv_points):
        return min(max(target_power, parameters.gmin), parameters.gmax)
    elif target_power < parameters.pgv_points[0] or target_power > parameters.pgv_points[-1]:
        return None
    else:
        gate_result: float | None = None
        for point_index in range(5):
            lower_power: float = parameters.pgv_points[point_index]
            upper_power: float = parameters.pgv_points[point_index + 1]
            if gate_result is None and lower_power <= target_power <= upper_power:
                lower_gate: float = parameters.gv_points[point_index]
                upper_gate: float = parameters.gv_points[point_index + 1]
                if upper_power > lower_power:
                    fraction: float = (target_power - lower_power) / (upper_power - lower_power)
                    gate_result = lower_gate + fraction * (upper_gate - lower_gate)
                else:
                    gate_result = lower_gate
            else:
                pass
        if gate_result is None:
            return None
        else:
            return min(max(gate_result, parameters.gmin), parameters.gmax)
