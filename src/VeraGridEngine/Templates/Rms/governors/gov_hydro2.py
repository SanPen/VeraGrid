# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydro2 governor and penstock model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.common.speed_deadband import (
    build_intentional_speed_deadband,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydro2Parameters:
    """CGMES GovHydro2 settings and six-point gate/power characteristic."""

    __slots__ = (
        'mwbase', 'tg', 'tp', 'uo', 'uc', 'pmax', 'pmin', 'rperm', 'rtemp',
        'tr', 'tw', 'kturb', 'aturb', 'bturb', 'db1', 'eps', 'db2',
        'gv_points', 'pgv_points', 'nominal_frequency',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            tg: float = 0.5,
            tp: float = 0.03,
            uo: float = 0.1,
            uc: float = -0.1,
            pmax: float = 1.0,
            pmin: float = 0.0,
            rperm: float = 0.05,
            rtemp: float = 0.5,
            tr: float = 12.0,
            tw: float = 2.0,
            kturb: float = 1.0,
            aturb: float = -1.0,
            bturb: float = 0.5,
            db1: float = 0.0,
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
        """Store CGMES coefficients in MWbase, seconds, and Hz.

        :param mwbase: Active-power base in MW.
        :param tg: Gate servo time constant in seconds.
        :param tp: Pilot-valve lag time in seconds.
        :param uo: Gate-opening rate limit in pu/s.
        :param uc: Gate-closing rate limit in pu/s.
        :param pmax: Maximum gate opening in pu.
        :param pmin: Minimum gate opening in pu.
        :param rperm: Permanent speed droop in pu.
        :param rtemp: Temporary speed droop in pu.
        :param tr: Dashpot time constant in seconds.
        :param tw: Water inertia time in seconds.
        :param kturb: Turbine power gain in pu.
        :param aturb: Turbine numerator multiplier.
        :param bturb: Turbine denominator multiplier.
        :param db1: Intentional speed deadband threshold in Hz.
        :param eps: Intentional deadband hysteresis width in Hz.
        :param db2: Unintentional mechanical-power deadband in MW.
        :param gv_points: Six increasing gate points for turbine power.
        :param pgv_points: Six nondecreasing power points paired with gates.
        :param nominal_frequency: System frequency used to convert Hz to pu.
        """
        self.mwbase: float = mwbase
        self.tg: float = tg
        self.tp: float = tp
        self.uo: float = uo
        self.uc: float = uc
        self.pmax: float = pmax
        self.pmin: float = pmin
        self.rperm: float = rperm
        self.rtemp: float = rtemp
        self.tr: float = tr
        self.tw: float = tw
        self.kturb: float = kturb
        self.aturb: float = aturb
        self.bturb: float = bturb
        self.db1: float = db1
        self.eps: float = eps
        self.db2: float = db2
        self.gv_points: tuple[float, float, float, float, float, float] = gv_points
        self.pgv_points: tuple[float, float, float, float, float, float] = pgv_points
        self.nominal_frequency: float = nominal_frequency


def build_gov_hydro2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydro2Parameters | None = None,
) -> RmsModelTemplate:
    """Build GovHydro2 control, nonlinear curve, and water-turbine equations.

    The frequency error passes through an intentional deadband, permanent and
    transient droop, pilot lag, asymmetric gate-rate limits, and bounded gate
    travel. Up to six RDF points define gate power between assumed ``(0, 0)``
    and ``(1, 1)`` endpoints, followed by the water-turbine transfer. ``Tp=0``,
    ``Tr=0``, and ``Tw=0`` select their exact static limits.

    :param vfactory: Factory owning this template's symbolic variables.
    :param name: Optional unique runtime template name.
    :param parameters: Imported CGMES scalars and curve points.
    :return: Executable governor with speed, reference, and mechanical-power ports.
    :raises ValueError: Invalid time constants, deadbands, limits, or curve data.
    """
    settings: GovHydro2Parameters = (
        GovHydro2Parameters() if parameters is None else parameters
    )
    curve_point_count: int = sum(
        1 for gate_point in settings.gv_points if gate_point > 0.0
    )
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.tg, settings.tp, settings.uo, settings.uc,
        settings.pmax, settings.pmin, settings.rperm, settings.rtemp, settings.tr,
        settings.tw, settings.kturb, settings.aturb, settings.bturb, settings.db1,
        settings.eps, settings.db2, settings.nominal_frequency,
        *settings.gv_points, *settings.pgv_points,
    )
    curve_default: bool = settings.gv_points[0] <= 0.0
    unused_curve_points_are_zero: bool = all(
        settings.gv_points[index] == 0.0
        for index in range(curve_point_count, 6)
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovHydro2 parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.nominal_frequency <= 0.0:
        raise ValueError('GovHydro2 requires positive MWBASE and nominal frequency')
    elif settings.tg <= 0.0 or min(settings.tp, settings.tr, settings.tw) < 0.0:
        raise ValueError('GovHydro2 requires TG > 0 and other times nonnegative')
    elif settings.uo < 0.0 or settings.uc > 0.0:
        raise ValueError('GovHydro2 gate rates require UO >= 0 and UC <= 0')
    elif settings.pmin >= settings.pmax:
        raise ValueError('GovHydro2 requires PMIN below PMAX')
    elif min(settings.rperm, settings.rtemp, settings.db1, settings.eps, settings.db2) < 0.0:
        raise ValueError('GovHydro2 droops and deadband widths must be nonnegative')
    elif settings.bturb <= 0.0 or settings.kturb < 0.0:
        raise ValueError('GovHydro2 requires positive BTURB and nonnegative KTURB')
    elif not curve_default and (
            not unused_curve_points_are_zero
            or not all(
                0.0 < settings.gv_points[index] <= 1.0
                and 0.0 <= settings.pgv_points[index] <= 1.0
                for index in range(curve_point_count)
            )
            or not all(
                settings.gv_points[index] < settings.gv_points[index + 1]
                and settings.pgv_points[index] <= settings.pgv_points[index + 1]
                for index in range(curve_point_count - 1)
            )
    ):
        raise ValueError('GovHydro2 curve points must increase within [0, 1]')
    else:
        pass

    template_name: str = 'GovHydro2' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)

    # Runtime variables use explicit GovHydro2 field names for RDF event copies.
    mwbase: Var = control.parameter('GovHydro2.mwbase', settings.mwbase)
    tg: Var = control.parameter('GovHydro2.tg', settings.tg)
    tp: Var = control.parameter('GovHydro2.tp', settings.tp)
    uo: Var = control.parameter('GovHydro2.uo', settings.uo)
    uc: Var = control.parameter('GovHydro2.uc', settings.uc)
    pmax: Var = control.parameter('GovHydro2.pmax', settings.pmax)
    pmin: Var = control.parameter('GovHydro2.pmin', settings.pmin)
    rperm: Var = control.parameter('GovHydro2.rperm', settings.rperm)
    rtemp: Var = control.parameter('GovHydro2.rtemp', settings.rtemp)
    tr: Var = control.parameter('GovHydro2.tr', settings.tr)
    tw: Var = control.parameter('GovHydro2.tw', settings.tw)
    kturb: Var = control.parameter('GovHydro2.kturb', settings.kturb)
    aturb: Var = control.parameter('GovHydro2.aturb', settings.aturb)
    bturb: Var = control.parameter('GovHydro2.bturb', settings.bturb)
    db1: Var = control.parameter('GovHydro2.db1', settings.db1)
    eps: Var = control.parameter('GovHydro2.eps', settings.eps)
    db2: Var = control.parameter('GovHydro2.db2', settings.db2)
    gv_points: tuple[Var, Var, Var, Var, Var, Var] = (
        control.parameter('GovHydro2.gv1', settings.gv_points[0]),
        control.parameter('GovHydro2.gv2', settings.gv_points[1]),
        control.parameter('GovHydro2.gv3', settings.gv_points[2]),
        control.parameter('GovHydro2.gv4', settings.gv_points[3]),
        control.parameter('GovHydro2.gv5', settings.gv_points[4]),
        control.parameter('GovHydro2.gv6', settings.gv_points[5]),
    )
    pgv_points: tuple[Var, Var, Var, Var, Var, Var] = (
        control.parameter('GovHydro2.pgv1', settings.pgv_points[0]),
        control.parameter('GovHydro2.pgv2', settings.pgv_points[1]),
        control.parameter('GovHydro2.pgv3', settings.pgv_points[2]),
        control.parameter('GovHydro2.pgv4', settings.pgv_points[3]),
        control.parameter('GovHydro2.pgv5', settings.pgv_points[4]),
        control.parameter('GovHydro2.pgv6', settings.pgv_points[5]),
    )

    # Speed error is expressed in pu; IEC db1 and eps use Hz.
    speed: Var = control.input('OmegaPu', Const(1.0))
    power_reference: Var = control.input('PRefPu', Const(settings.rperm * 0.5))
    speed_deviation: Var = control.algebraic(
        'SpeedDeviationPu', speed - Const(1.0), Const(0.0),
    )
    deadbanded_speed: Expr = build_intentional_speed_deadband(
        control=control,
        speed_deviation=speed_deviation,
        deadband_threshold=db1 / Const(settings.nominal_frequency),
        hysteresis_width=eps / Const(settings.nominal_frequency),
    )
    gate_state: Var = vfactory.add_var(f'GateOpeningPu_{template_name}')
    permanent_droop: Var = control.algebraic(
        'PermanentDroopPu', rperm * gate_state, Const(settings.rperm * 0.5),
    )

    # The transient droop is a washout of gate position and vanishes at equilibrium.
    if settings.tr > 0.0:
        temporary_droop: Var = control.washout(
            'TemporaryDroopPu', gate_state, tr, settings.tr, rtemp, Const(0.5),
        )
    else:
        temporary_droop = control.algebraic(
            'TemporaryDroopPu', Const(0.0), Const(0.0),
        )
    governor_error: Var = control.algebraic(
        'GovernorErrorPu',
        power_reference - deadbanded_speed - permanent_droop - temporary_droop,
        Const(0.0),
    )

    # A zero pilot lag is an exact bypass; the gate servo remains positive by definition.
    if settings.tp > 0.0:
        pilot_output: Var = control.lag(
            'PilotValvePu', governor_error, tp, settings.tp, Const(0.0),
        )
    else:
        pilot_output = control.algebraic('PilotValvePu', governor_error, Const(0.0))
    rate_command: Expr = pilot_output / tg
    gate_rate: Var = control.algebraic(
        'GateRatePuPerSecond', sym.hard_sat(rate_command, uc, uo), Const(0.0),
    )
    control.differential(
        gate_state, gate_rate, Const(0.5), pmin, pmax,
    )

    # A nonpositive first gate point selects the IEC default unit characteristic.
    if curve_default:
        normalized_power: Expr = gate_state / pmax
    else:
        normalized_power = build_gov_hydro2_curve(
            gate_state / pmax, gv_points, pgv_points,
            curve_point_count,
            settings.gv_points[0] > 0.0,
            settings.gv_points[curve_point_count - 1] < 1.0,
        )
    curve_power: Var = control.algebraic(
        'CurvePowerPu', pmax * normalized_power, Const(0.5),
    )
    power_deadband_width: Expr = db2 / mwbase
    deadbanded_power: Expr = (
        sym.max(curve_power - power_deadband_width, Const(0.0))
        + sym.min(curve_power + power_deadband_width, Const(0.0))
    )

    # The inelastic-water lead-lag keeps its inverse response and exact TW=0 limit.
    if settings.tw > 0.0:
        water_memory: Var = control.lag(
            'WaterColumnMemoryPu', deadbanded_power, bturb * tw,
            settings.bturb * settings.tw, Const(0.5),
        )
        turbine_shape: Var = control.algebraic(
            'WaterTurbineShapePu',
            water_memory + aturb / bturb * (deadbanded_power - water_memory),
            Const(0.5),
        )
    else:
        turbine_shape = control.algebraic(
            'WaterTurbineShapePu', deadbanded_power, Const(0.5),
        )
    mechanical_power: Var = control.algebraic(
        'PmPu', kturb * turbine_shape, Const(settings.kturb * 0.5),
    )
    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovHydro2 hydraulic-dashpot governor and turbine',
    )

    # Keep the canonical class surface for parser round trips and direct editing.
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    template.comment = 'CGMES GovHydro2 equations with frequency/power deadbands.'
    for parameter_name in (
            'enabled', 'mwbase', 'tg', 'tp', 'uo', 'uc', 'pmax', 'pmin',
            'rperm', 'rtemp', 'tr', 'tw', 'kturb', 'aturb', 'bturb', 'db1',
            'eps', 'db2', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3',
            'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6',
    ):
        parameter_variable: Var = vfactory.add_var(
            f'GovHydro2.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template


def build_gov_hydro2_curve(
        gate: Expr,
        gv_points: tuple[Var, Var, Var, Var, Var, Var],
        pgv_points: tuple[Var, Var, Var, Var, Var, Var],
        curve_point_count: int,
        include_origin_segment: bool,
        include_full_open_segment: bool,
) -> Expr:
    """Build the gate-to-power curve with IEC-assumed endpoint pairs.

    :param gate: Gate position normalized by PMAX.
    :param gv_points: Six gate-axis parameters.
    :param pgv_points: Six paired turbine-power parameters.
    :param curve_point_count: Number of positive gate points in the active prefix.
    :param include_origin_segment: Whether to connect the first point to ``(0, 0)``.
    :param include_full_open_segment: Whether to connect the last point to ``(1, 1)``.
    :return: Continuous piecewise-linear curve through supplied and assumed points.
    """
    expression: Expr = Const(0.0)
    if include_origin_segment:
        origin_gate: Var = gv_points[0]
        origin_power: Var = pgv_points[0]
        origin_segment_gate: Expr = sym.min(
            sym.max(gate, Const(0.0)), origin_gate,
        )
        expression = expression + origin_power * origin_segment_gate / origin_gate
    else:
        pass
    for point_index in range(curve_point_count - 1):
        lower_gate: Var = gv_points[point_index]
        upper_gate: Var = gv_points[point_index + 1]
        lower_power: Var = pgv_points[point_index]
        upper_power: Var = pgv_points[point_index + 1]
        gate_span: Expr = upper_gate - lower_gate
        segment_gate: Expr = sym.min(
            sym.max(gate - lower_gate, Const(0.0)), gate_span,
        )
        expression = expression + (
            (upper_power - lower_power) * segment_gate / gate_span
        )
    if include_full_open_segment:
        final_gate: Var = gv_points[curve_point_count - 1]
        final_power: Var = pgv_points[curve_point_count - 1]
        final_segment_gate: Expr = sym.min(
            sym.max(gate - final_gate, Const(0.0)), Const(1.0) - final_gate,
        )
        expression = expression + (
            (Const(1.0) - final_power) * final_segment_gate
            / (Const(1.0) - final_gate)
        )
    else:
        pass
    return expression


def get_gov_hydro2_curve_power(parameters: GovHydro2Parameters, gate: float) -> float:
    """Evaluate the same bounded piecewise curve for the operating-point seed.

    :param parameters: Imported GovHydro2 settings.
    :param gate: Gate position in pu.
    :return: Curve power in pu after PMAX scaling and before DB2.
    """
    if parameters.gv_points[0] <= 0.0:
        return gate
    else:
        pass
    normalized_gate: float = gate / parameters.pmax
    curve_point_count: int = sum(
        1 for gate_point in parameters.gv_points if gate_point > 0.0
    )
    first_gate: float = parameters.gv_points[0]
    first_power: float = parameters.pgv_points[0]
    if normalized_gate < first_gate:
        curve_power: float = first_power * normalized_gate / first_gate
    else:
        curve_power = first_power
    for point_index in range(curve_point_count - 1):
        lower_gate: float = parameters.gv_points[point_index]
        upper_gate: float = parameters.gv_points[point_index + 1]
        lower_power: float = parameters.pgv_points[point_index]
        upper_power: float = parameters.pgv_points[point_index + 1]
        segment_gate: float = min(
            max(normalized_gate - lower_gate, 0.0), upper_gate - lower_gate,
        )
        curve_power += (
            (upper_power - lower_power) * segment_gate / (upper_gate - lower_gate)
        )
    final_gate: float = parameters.gv_points[curve_point_count - 1]
    final_power: float = parameters.pgv_points[curve_point_count - 1]
    if normalized_gate > final_gate and final_gate < 1.0:
        final_segment_gate: float = min(
            normalized_gate - final_gate, 1.0 - final_gate,
        )
        curve_power += (
            (1.0 - final_power) * final_segment_gate / (1.0 - final_gate)
        )
    else:
        pass
    return parameters.pmax * curve_power


def get_gov_hydro2_gate_for_power(
        parameters: GovHydro2Parameters,
        target_power: float,
) -> float | None:
    """Invert the monotone curve to seed the gate at the imported power.

    :param parameters: Curve, gate limits, and power deadband settings.
    :param target_power: Desired turbine power in pu before KTURB.
    :return: Gate position, or ``None`` when the curve cannot produce the target.
    """
    if parameters.gv_points[0] <= 0.0:
        return min(max(target_power, parameters.pmin), parameters.pmax)
    else:
        pass
    normalized_target: float = target_power / parameters.pmax
    curve_point_count: int = sum(
        1 for gate_point in parameters.gv_points if gate_point > 0.0
    )
    if normalized_target < 0.0 or normalized_target > 1.0:
        return None
    else:
        pass
    gate_result: float | None = None
    first_power: float = parameters.pgv_points[0]
    if first_power > 0.0 and normalized_target <= first_power:
        gate_result = (
            parameters.pmax * parameters.gv_points[0]
            * normalized_target / first_power
        )
    elif first_power == 0.0 and normalized_target == 0.0:
        gate_result = 0.0
    else:
        pass
    for point_index in range(curve_point_count - 1):
        lower_power: float = parameters.pgv_points[point_index]
        upper_power: float = parameters.pgv_points[point_index + 1]
        if gate_result is None and lower_power <= normalized_target <= upper_power:
            power_span: float = upper_power - lower_power
            if power_span > 0.0:
                power_fraction: float = (normalized_target - lower_power) / power_span
                gate_result = parameters.pmax * (
                    parameters.gv_points[point_index]
                    + power_fraction * (
                        parameters.gv_points[point_index + 1]
                        - parameters.gv_points[point_index]
                    )
                )
            elif normalized_target == lower_power:
                gate_result = parameters.pmax * parameters.gv_points[point_index]
            else:
                pass
        else:
            pass
    final_power: float = parameters.pgv_points[curve_point_count - 1]
    if gate_result is None and normalized_target >= final_power:
        if final_power < 1.0:
            gate_result = parameters.pmax * (
                parameters.gv_points[curve_point_count - 1]
                + (normalized_target - final_power)
                * (1.0 - parameters.gv_points[curve_point_count - 1])
                / (1.0 - final_power)
            )
        elif normalized_target == final_power:
            gate_result = parameters.pmax * parameters.gv_points[curve_point_count - 1]
        else:
            pass
    else:
        pass
    if gate_result is None:
        return None
    else:
        return min(max(gate_result, parameters.pmin), parameters.pmax)
