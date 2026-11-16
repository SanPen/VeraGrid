# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydro4 hydro governor and turbine."""

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.speed_deadband import (
    build_intentional_speed_deadband,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydro4TurbineKind(Enum):
    """Equation selector mapped from the canonical CGMES model enumeration."""

    simple = 'simple'
    francis_pelton = 'francisPelton'
    kaplan = 'kaplan'


class GovHydro4Parameters:
    """CGMES GovHydro4 coefficients, model selector, and turbine curves."""

    __slots__ = (
        'mwbase', 'tg', 'tp', 'uo', 'uc', 'gmax', 'gmin', 'rperm', 'rtemp',
        'tr', 'tw', 'at', 'dturb', 'hdam', 'qnl', 'db1', 'eps', 'db2',
        'gv_points', 'pgv_points', 'bgv_points', 'bmax', 'tblade', 'model',
        'nominal_frequency',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            tg: float = 0.5,
            tp: float = 0.1,
            uo: float = 0.2,
            uc: float = -0.2,
            gmax: float = 1.0,
            gmin: float = 0.0,
            rperm: float = 0.05,
            rtemp: float = 0.3,
            tr: float = 5.0,
            tw: float = 1.0,
            at: float = 1.2,
            dturb: float = 0.5,
            hdam: float = 1.0,
            qnl: float = 0.08,
            db1: float = 0.0,
            eps: float = 0.0,
            db2: float = 0.0,
            gv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            pgv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            bgv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            bmax: float = 0.0,
            tblade: float = 100.0,
            model: GovHydro4TurbineKind = GovHydro4TurbineKind.simple,
            nominal_frequency: float = 50.0,
    ) -> None:
        """Store parameters with their CGMES units and selector.

        :param mwbase: Governor active-power base in MW.
        :param tg: Gate servo time in seconds.
        :param tp: Pilot lag time in seconds.
        :param uo: Gate opening rate in pu/s.
        :param uc: Gate closing rate in pu/s.
        :param gmax: Maximum gate position.
        :param gmin: Minimum gate position.
        :param rperm: Permanent droop.
        :param rtemp: Temporary droop.
        :param tr: Dashpot time in seconds.
        :param tw: Water inertia time in seconds.
        :param at: Turbine gain.
        :param dturb: Turbine damping.
        :param hdam: Dam head.
        :param qnl: No-load flow.
        :param db1: Frequency deadband in Hz.
        :param eps: Frequency deadband hysteresis in Hz.
        :param db2: Power deadband in MW.
        :param gv_points: Six gate/power curve input points.
        :param pgv_points: Six turbine power curve output points.
        :param bgv_points: Six Kaplan gate/blade curve output points.
        :param bmax: Maximum Kaplan blade adjustment factor.
        :param tblade: Blade servo time in seconds.
        :param model: Canonical CGMES turbine selector.
        :param nominal_frequency: Circuit frequency used for Hz conversion.
        """
        self.mwbase: float = mwbase
        self.tg: float = tg
        self.tp: float = tp
        self.uo: float = uo
        self.uc: float = uc
        self.gmax: float = gmax
        self.gmin: float = gmin
        self.rperm: float = rperm
        self.rtemp: float = rtemp
        self.tr: float = tr
        self.tw: float = tw
        self.at: float = at
        self.dturb: float = dturb
        self.hdam: float = hdam
        self.qnl: float = qnl
        self.db1: float = db1
        self.eps: float = eps
        self.db2: float = db2
        self.gv_points: tuple[float, float, float, float, float, float] = gv_points
        self.pgv_points: tuple[float, float, float, float, float, float] = pgv_points
        self.bgv_points: tuple[float, float, float, float, float, float] = bgv_points
        self.bmax: float = bmax
        self.tblade: float = tblade
        self.model: GovHydro4TurbineKind = model
        self.nominal_frequency: float = nominal_frequency


def build_gov_hydro4_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydro4Parameters | None = None,
) -> RmsModelTemplate:
    """Build the IEC hydro dashpot governor and selected turbine equations.

    :param vfactory: Factory owning symbolic variables.
    :param name: Optional unique runtime template name.
    :param parameters: Parsed model coefficients and selector.
    :return: Executable governor with speed/reference and Pm ports.
    :raises ValueError: Invalid model selector, curve, or physical limits.
    """
    settings: GovHydro4Parameters = (
        GovHydro4Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.tg, settings.tp, settings.uo, settings.uc,
        settings.gmax, settings.gmin, settings.rperm, settings.rtemp, settings.tr,
        settings.tw, settings.at, settings.dturb, settings.hdam, settings.qnl,
        settings.db1, settings.eps, settings.db2, settings.bmax, settings.tblade,
        settings.nominal_frequency, *settings.gv_points, *settings.pgv_points,
        *settings.bgv_points,
    )
    default_curve: bool = settings.gv_points[0] < 0.0 or all(
        value == 0.0 for value in settings.gv_points + settings.pgv_points
    )
    blade_default: bool = all(value == 0.0 for value in settings.bgv_points)
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovHydro4 parameters must be finite')
    elif not isinstance(settings.model, GovHydro4TurbineKind):
        raise ValueError('GovHydro4 requires a canonical turbine model selector')
    elif settings.mwbase <= 0.0 or settings.nominal_frequency <= 0.0:
        raise ValueError('GovHydro4 requires positive MWBASE and nominal frequency')
    elif settings.tg <= 0.0 or settings.tw <= 0.0 or settings.tr <= 0.0:
        raise ValueError('GovHydro4 requires positive TG, TW, and TR')
    elif min(settings.tp, settings.tblade) < 0.0:
        raise ValueError('GovHydro4 pilot and blade times must be nonnegative')
    elif (
            settings.gmin < 0.0 or settings.gmax > 1.0
            or settings.gmin >= settings.gmax
            or settings.uo <= 0.0 or settings.uc >= 0.0
    ):
        raise ValueError('GovHydro4 gate limits and rates are invalid')
    elif min(settings.rperm, settings.rtemp, settings.db1, settings.eps, settings.db2) < 0.0:
        raise ValueError('GovHydro4 droops and deadbands must be nonnegative')
    elif settings.at <= 0.0 or settings.hdam <= 0.0:
        raise ValueError('GovHydro4 requires positive turbine gain and dam head')
    elif not default_curve and (
            settings.gv_points[0] < 0.0
            or settings.gv_points[-1] >= 1.0
            or settings.pgv_points[-1] >= 1.0
            or not all(
                settings.gv_points[index] < settings.gv_points[index + 1]
                and settings.pgv_points[index] < settings.pgv_points[index + 1]
                for index in range(5)
            )
    ):
        raise ValueError('GovHydro4 curve points must increase below the full-open endpoint')
    elif settings.model == GovHydro4TurbineKind.kaplan and settings.bmax <= 0.0:
        raise ValueError('GovHydro4 Kaplan selector requires positive BMAX')
    elif (
            settings.model == GovHydro4TurbineKind.kaplan
            and not blade_default and default_curve
    ):
        raise ValueError('GovHydro4 Kaplan BGV points require the GV gate axis')
    else:
        pass

    template_name: str = 'GovHydro4' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    mwbase: Var = control.parameter('GovHydro4.mwbase', settings.mwbase)
    tp: Var = control.parameter('GovHydro4.tp', settings.tp)
    tg: Var = control.parameter('GovHydro4.tg', settings.tg)
    uo: Var = control.parameter('GovHydro4.uo', settings.uo)
    uc: Var = control.parameter('GovHydro4.uc', settings.uc)
    gmax: Var = control.parameter('GovHydro4.gmax', settings.gmax)
    gmin: Var = control.parameter('GovHydro4.gmin', settings.gmin)
    rperm: Var = control.parameter('GovHydro4.rperm', settings.rperm)
    rtemp: Var = control.parameter('GovHydro4.rtemp', settings.rtemp)
    tr: Var = control.parameter('GovHydro4.tr', settings.tr)
    tw: Var = control.parameter('GovHydro4.tw', settings.tw)
    at: Var = control.parameter('GovHydro4.at', settings.at)
    dturb: Var = control.parameter('GovHydro4.dturb', settings.dturb)
    hdam: Var = control.parameter('GovHydro4.hdam', settings.hdam)
    qnl: Var = control.parameter('GovHydro4.qnl', settings.qnl)
    db1: Var = control.parameter('GovHydro4.db1', settings.db1)
    eps: Var = control.parameter('GovHydro4.eps', settings.eps)
    db2: Var = control.parameter('GovHydro4.db2', settings.db2)
    gv_points: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        control.parameter(f'GovHydro4.gv{index}', settings.gv_points[index])
        for index in range(6)
    )
    pgv_points: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        control.parameter(f'GovHydro4.pgv{index}', settings.pgv_points[index])
        for index in range(6)
    )
    bgv_points: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        control.parameter(f'GovHydro4.bgv{index}', settings.bgv_points[index])
        for index in range(6)
    )
    bmax: Var = control.parameter('GovHydro4.bmax', settings.bmax)
    tblade: Var = control.parameter('GovHydro4.tblade', settings.tblade)

    speed: Var = control.input('OmegaPu', Const(1.0))
    power_reference: Var = control.input('PRefPu', Const(0.0))
    speed_deviation: Var = control.algebraic('SpeedDeviationPu', speed - Const(1.0), Const(0.0))
    deadbanded_speed: Expr = build_intentional_speed_deadband(
        control=control,
        speed_deviation=speed_deviation,
        deadband_threshold=db1 / Const(settings.nominal_frequency),
        hysteresis_width=eps / Const(settings.nominal_frequency),
    )
    initial_gate: float = min(max(0.5, settings.gmin), settings.gmax)
    gate_state: Var = vfactory.add_var(f'GateOpeningPu_{template_name}')
    gate_feedback: Var = control.algebraic(
        'PermanentDroopPu', rperm * gate_state, Const(settings.rperm * initial_gate),
    )
    temporary_feedback: Var = control.washout(
        'TemporaryDroopPu', gate_state, tr, settings.tr, rtemp,
        Const(initial_gate),
    )
    governor_error: Var = control.algebraic(
        'GovernorErrorPu', power_reference - deadbanded_speed
        - gate_feedback - temporary_feedback, Const(0.0),
    )
    pilot: Var = control.lag('PilotValvePu', governor_error, tp, settings.tp, Const(0.0))
    gate_rate: Var = control.algebraic(
        'GateRatePuPerSecond',
        sym.hard_sat(pilot / tg, uc, uo), Const(0.0),
    )
    control.differential(gate_state, gate_rate, Const(initial_gate), gmin, gmax)

    if default_curve:
        turbine_curve: Expr = gate_state
    else:
        turbine_curve = build_gov_hydro4_curve(gate_state, gv_points, pgv_points)
    curve_power_initial: float = (
        get_gov_hydro4_curve_value(
            settings.gv_points,
            settings.pgv_points,
            initial_gate,
        )
        if not default_curve
        else initial_gate
    )
    curve_power: Var = control.algebraic(
        'CurvePowerPu', turbine_curve,
        Const(curve_power_initial),
    )
    power_deadband: Expr = db2 / mwbase
    if settings.model == GovHydro4TurbineKind.kaplan:
        if blade_default:
            blade_curve: Var = control.algebraic(
                'BladeCurvePu', Const(0.0), Const(0.0),
            )
            initial_blade_curve: float = 0.0
        else:
            blade_curve_expression: Expr = build_gov_hydro4_curve(
                gate_state,
                gv_points,
                bgv_points,
            )
            initial_blade_curve = get_gov_hydro4_curve_value(
                settings.gv_points,
                settings.bgv_points,
                initial_gate,
            )
            blade_curve = control.algebraic(
                'BladeCurvePu',
                blade_curve_expression,
                Const(initial_blade_curve),
            )
        blade_position: Var = control.lag(
            'BladePositionPu',
            blade_curve,
            tblade,
            settings.tblade,
            Const(initial_blade_curve),
        )
        turbine_gate: Var = control.algebraic(
            'AdjustedTurbineGainPu',
            curve_power * (Const(1.0) + blade_position / bmax)
            / (Const(1.0) + blade_curve / bmax),
            Const(curve_power_initial),
        )
    elif settings.model == GovHydro4TurbineKind.simple:
        turbine_gate = gate_state
    else:
        turbine_gate = curve_power
    initial_turbine_gate: float = (
        initial_gate if settings.model == GovHydro4TurbineKind.simple
        else curve_power_initial
    )
    turbine_flow: Var = vfactory.add_var(f'TurbineFlowPu_{template_name}')
    turbine_head: Var = control.algebraic(
        'TurbineHeadPu', sym.safe_divide(turbine_flow, turbine_gate,
                                        math.sqrt(settings.hdam)) ** Const(2.0),
        Const(settings.hdam),
    )
    control.differential(
        turbine_flow, (hdam - turbine_head) / tw,
        Const(initial_turbine_gate * math.sqrt(settings.hdam)),
    )
    turbine_flow_power: Expr = at * (turbine_flow - qnl) * turbine_head
    turbine_power_deadbanded: Expr = (
        sym.max(turbine_flow_power - power_deadband, Const(0.0))
        + sym.min(turbine_flow_power + power_deadband, Const(0.0))
    )
    mechanical_power: Var = control.algebraic(
        'PmPu', turbine_power_deadbanded - dturb * speed_deviation,
        Const(settings.at * (initial_turbine_gate * math.sqrt(settings.hdam) - settings.qnl)
              * settings.hdam),
    )
    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovHydro4 selected hydro turbine and dashpot governor',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    template.comment = 'CGMES GovHydro4 simple/Francis-Pelton/Kaplan hydro equations.'
    for parameter_name in (
            'enabled', 'mwbase', 'tg', 'tp', 'uo', 'uc', 'gmax', 'gmin',
            'rperm', 'rtemp', 'tr', 'tw', 'at', 'dturb', 'hdam', 'qnl',
            'db1', 'eps', 'db2', 'gv0', 'pgv0', 'gv1', 'pgv1', 'gv2',
            'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'bgv0',
            'bgv1', 'bgv2', 'bgv3', 'bgv4', 'bgv5', 'bmax', 'tblade', 'model',
    ):
        parameter_variable: Var = vfactory.add_var(
            f'GovHydro4.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template


def build_gov_hydro4_curve(
        input_value: Expr,
        input_points: tuple[Var, Var, Var, Var, Var, Var],
        output_points: tuple[Var, Var, Var, Var, Var, Var],
) -> Expr:
    """Build the six-point curve with sourced lower and upper continuations.

    :param input_value: Gate or blade-axis signal.
    :param input_points: Increasing curve input coordinates.
    :param output_points: Paired curve outputs.
    :return: Piecewise-linear curve, extrapolated below point zero and joined to (1, 1).
    """
    first_span: Expr = input_points[1] - input_points[0]
    first_slope: Expr = (output_points[1] - output_points[0]) / first_span
    lower_extension: Expr = sym.min(input_value - input_points[0], Const(0.0))
    expression: Expr = output_points[0] + first_slope * lower_extension
    for point_index in range(5):
        lower_input: Var = input_points[point_index]
        upper_input: Var = input_points[point_index + 1]
        lower_output: Var = output_points[point_index]
        upper_output: Var = output_points[point_index + 1]
        span: Expr = upper_input - lower_input
        segment: Expr = sym.min(sym.max(input_value - lower_input, Const(0.0)), span)
        expression = expression + (upper_output - lower_output) * segment / span
    final_input: Var = input_points[-1]
    final_output: Var = output_points[-1]
    upper_extension: Expr = sym.min(
        sym.max(input_value - final_input, Const(0.0)),
        Const(1.0) - final_input,
    )
    expression = expression + (
        (Const(1.0) - final_output) * upper_extension
        / (Const(1.0) - final_input)
    )
    return expression


def get_gov_hydro4_curve_value(
        input_points: tuple[float, float, float, float, float, float],
        output_points: tuple[float, float, float, float, float, float],
        input_value: float,
) -> float:
    """Evaluate the sourced six-point curve for operating-point initialization.

    :param input_points: Increasing curve input coordinates.
    :param output_points: Paired curve outputs.
    :param input_value: Input coordinate to evaluate.
    :return: Curve output with first-segment lower extrapolation and the (1, 1) endpoint.
    """
    first_span: float = input_points[1] - input_points[0]
    first_slope: float = (output_points[1] - output_points[0]) / first_span
    result: float = output_points[0] + first_slope * min(
        input_value - input_points[0], 0.0,
    )
    for point_index in range(5):
        lower_input: float = input_points[point_index]
        upper_input: float = input_points[point_index + 1]
        lower_output: float = output_points[point_index]
        upper_output: float = output_points[point_index + 1]
        segment: float = min(max(input_value - lower_input, 0.0), upper_input - lower_input)
        result += (upper_output - lower_output) * segment / (upper_input - lower_input)
    final_input: float = input_points[-1]
    final_output: float = output_points[-1]
    upper_extension: float = min(max(input_value - final_input, 0.0), 1.0 - final_input)
    result += (1.0 - final_output) * upper_extension / (1.0 - final_input)
    return result


def get_gov_hydro4_gate_for_power(
        parameters: GovHydro4Parameters,
        target_power: float,
) -> float | None:
    """Invert the selected gate/power curve for generator operating-point seeding.

    :param parameters: Imported CGMES governor and curve values.
    :param target_power: Required final turbine-gate ordinate in per unit.
    :return: Gate position within the configured stops, or ``None`` outside
        the source-defined curve range.
    """
    default_curve: bool = parameters.gv_points[0] < 0.0 or all(
        value == 0.0 for value in parameters.gv_points + parameters.pgv_points
    )
    if parameters.model == GovHydro4TurbineKind.simple or default_curve:
        gate_value: float = target_power
    elif target_power < parameters.pgv_points[0]:
        first_power_span: float = parameters.pgv_points[1] - parameters.pgv_points[0]
        gate_value = parameters.gv_points[0] + (
            (target_power - parameters.pgv_points[0])
            * (parameters.gv_points[1] - parameters.gv_points[0])
            / first_power_span
        )
    elif target_power > parameters.pgv_points[-1] and target_power <= 1.0:
        last_power_span: float = 1.0 - parameters.pgv_points[-1]
        gate_value = parameters.gv_points[-1] + (
            (target_power - parameters.pgv_points[-1])
            * (1.0 - parameters.gv_points[-1]) / last_power_span
        )
    elif target_power < parameters.pgv_points[0] or target_power > 1.0:
        return None
    else:
        gate_value = 0.0
        for point_index in range(5):
            lower_power: float = parameters.pgv_points[point_index]
            upper_power: float = parameters.pgv_points[point_index + 1]
            if lower_power <= target_power <= upper_power:
                power_fraction: float = (
                    (target_power - lower_power) / (upper_power - lower_power)
                )
                gate_value = parameters.gv_points[point_index] + power_fraction * (
                    parameters.gv_points[point_index + 1]
                    - parameters.gv_points[point_index]
                )
            else:
                pass
    if gate_value < parameters.gmin or gate_value > parameters.gmax:
        return None
    else:
        return gate_value
