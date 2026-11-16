# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydroIEEE2 governor and hydro turbine."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydroIEEE2Parameters:
    """Scalar settings and paired operating points for GovHydroIEEE2."""

    __slots__ = (
        'mwbase', 'tg', 'tp', 'uo', 'uc', 'pmax', 'pmin', 'rperm', 'rtemp',
        'tr', 'tw', 'kturb', 'aturb', 'bturb', 'gv_points', 'pgv_points',
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
            gv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
            pgv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ),
    ) -> None:
        """Keep values in their CGMES units and source field order.

        :param mwbase: Turbine active-power base in MW.
        :param tg: Gate servo time constant in seconds.
        :param tp: Pilot-valve lag time in seconds.
        :param uo: Maximum positive gate-opening rate in pu/s.
        :param uc: Minimum negative gate-closing rate in pu/s.
        :param pmax: Maximum gate opening in pu.
        :param pmin: Minimum gate opening in pu.
        :param rperm: Permanent speed droop in pu.
        :param rtemp: Temporary speed droop in pu.
        :param tr: Dashpot reset time in seconds.
        :param tw: Water starting time in seconds.
        :param kturb: Turbine power gain in pu.
        :param aturb: Turbine transfer numerator multiplier.
        :param bturb: Turbine transfer denominator multiplier.
        :param gv_points: Six gate positions defining the nonlinear turbine curve.
        :param pgv_points: Six power values paired with ``gv_points``.
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
        self.gv_points: tuple[float, float, float, float, float, float] = gv_points
        self.pgv_points: tuple[float, float, float, float, float, float] = pgv_points


def build_gov_hydro_i_e_e_e2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroIEEE2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the IEEE hydro governor, dashpot, gate, and water turbine.

    :param vfactory: Factory owning this template's symbolic variables.
    :param name: Optional runtime model name.
    :param parameters: Parsed RDF parameters and nonlinear curve points.
    :return: Equation template with speed, reference, and mechanical-power ports.
    :raises ValueError: Invalid rates, limits, transfer coefficients, or curve points.
    """
    settings: GovHydroIEEE2Parameters = (
        GovHydroIEEE2Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.tg, settings.tp, settings.uo, settings.uc,
        settings.pmax, settings.pmin, settings.rperm, settings.rtemp, settings.tr,
        settings.tw, settings.kturb, settings.aturb, settings.bturb,
        *settings.gv_points, *settings.pgv_points,
    )
    curve_unspecified: bool = all(
        settings.gv_points[index] == 0.0 and settings.pgv_points[index] == 0.0
        for index in range(6)
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovHydroIEEE2 parameters must be finite')
    elif settings.mwbase <= 0.0:
        raise ValueError('GovHydroIEEE2 requires a positive MWBASE')
    elif min(settings.tg, settings.tp, settings.tr, settings.tw) < 0.0:
        raise ValueError('GovHydroIEEE2 time constants must be nonnegative')
    elif settings.uo < 0.0 or settings.uc > 0.0:
        raise ValueError('GovHydroIEEE2 gate rates require UO >= 0 and UC <= 0')
    elif settings.pmin >= settings.pmax:
        raise ValueError('GovHydroIEEE2 requires PMIN below PMAX')
    elif settings.rperm < 0.0 or settings.rtemp < 0.0:
        raise ValueError('GovHydroIEEE2 droop values must be nonnegative')
    elif settings.bturb <= 0.0:
        raise ValueError('GovHydroIEEE2 requires positive BTURB')
    elif not curve_unspecified and not all(
            settings.gv_points[index] < settings.gv_points[index + 1]
            and settings.pgv_points[index] <= settings.pgv_points[index + 1]
            for index in range(5)
    ):
        raise ValueError('GovHydroIEEE2 curve gates must increase and powers must not decrease')
    else:
        pass

    template_name: str = 'GovHydroIEEE2' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    tg: Var = control.parameter('GovHydroIEEE2.tg', settings.tg)
    tp: Var = control.parameter('GovHydroIEEE2.tp', settings.tp)
    uo: Var = control.parameter('GovHydroIEEE2.uo', settings.uo)
    uc: Var = control.parameter('GovHydroIEEE2.uc', settings.uc)
    pmax: Var = control.parameter('GovHydroIEEE2.pmax', settings.pmax)
    pmin: Var = control.parameter('GovHydroIEEE2.pmin', settings.pmin)
    rperm: Var = control.parameter('GovHydroIEEE2.rperm', settings.rperm)
    rtemp: Var = control.parameter('GovHydroIEEE2.rtemp', settings.rtemp)
    tr: Var = control.parameter('GovHydroIEEE2.tr', settings.tr)
    tw: Var = control.parameter('GovHydroIEEE2.tw', settings.tw)
    kturb: Var = control.parameter('GovHydroIEEE2.kturb', settings.kturb)
    aturb: Var = control.parameter('GovHydroIEEE2.aturb', settings.aturb)
    bturb: Var = control.parameter('GovHydroIEEE2.bturb', settings.bturb)
    control.parameter('GovHydroIEEE2.mwbase', settings.mwbase)
    gv_points: tuple[Var, Var, Var, Var, Var, Var] = (
        control.parameter('GovHydroIEEE2.gv1', settings.gv_points[0]),
        control.parameter('GovHydroIEEE2.gv2', settings.gv_points[1]),
        control.parameter('GovHydroIEEE2.gv3', settings.gv_points[2]),
        control.parameter('GovHydroIEEE2.gv4', settings.gv_points[3]),
        control.parameter('GovHydroIEEE2.gv5', settings.gv_points[4]),
        control.parameter('GovHydroIEEE2.gv6', settings.gv_points[5]),
    )
    pgv_points: tuple[Var, Var, Var, Var, Var, Var] = (
        control.parameter('GovHydroIEEE2.pgv1', settings.pgv_points[0]),
        control.parameter('GovHydroIEEE2.pgv2', settings.pgv_points[1]),
        control.parameter('GovHydroIEEE2.pgv3', settings.pgv_points[2]),
        control.parameter('GovHydroIEEE2.pgv4', settings.pgv_points[3]),
        control.parameter('GovHydroIEEE2.pgv5', settings.pgv_points[4]),
        control.parameter('GovHydroIEEE2.pgv6', settings.pgv_points[5]),
    )

    # The source diagram normalizes absolute speed before the droop summation.
    speed: Var = control.input('OmegaPu', Const(1.0))
    power_reference: Var = control.input('PRefPu', Const(settings.rperm * 0.5))
    speed_deviation: Var = control.algebraic(
        'SpeedDeviationPu', speed - Const(1.0), Const(0.0),
    )
    gate_initial: float = min(max(0.5, settings.pmin), settings.pmax)
    gate_state: Var = vfactory.add_var(name=f'GateOpeningPu_{template_name}')

    # Permanent and transient gate feedback create the hydraulic dashpot droop.
    permanent_droop: Var = control.algebraic(
        'PermanentDroopPu', rperm * gate_state, Const(settings.rperm * gate_initial),
    )
    if settings.tr > 0.0:
        temporary_droop: Var = control.washout(
            'TemporaryDroopPu', gate_state, tr, settings.tr, rtemp,
            Const(gate_initial),
        )
    else:
        temporary_droop = control.algebraic(
            'TemporaryDroopPu', Const(0.0), Const(0.0),
        )
    feedback: Var = control.algebraic(
        'GovernorFeedbackPu', permanent_droop + temporary_droop,
        Const(settings.rperm * gate_initial),
    )
    governor_error: Var = control.algebraic(
        'GovernorErrorPu', power_reference - speed_deviation - feedback,
        Const(0.0),
    )

    # The pilot lag precedes a gain and asymmetric velocity limiter in the diagram.
    if settings.tp > 0.0:
        pilot_output: Var = control.lag(
            'PilotValvePu', governor_error, tp, settings.tp, Const(0.0),
        )
    else:
        pilot_output = control.algebraic(
            'PilotValvePu', governor_error, Const(0.0),
        )
    if settings.tg > 0.0:
        gate_rate_signal: Expr = pilot_output / tg
        gate_rate_initial: Expr = Const(0.0)
    else:
        gate_rate_signal = (
            uo * sym.heaviside(pilot_output)
            + uc * sym.heaviside(-pilot_output)
        )
        gate_rate_initial = Const(0.0)
    gate_rate: Var = control.algebraic(
        'GateRatePuPerSecond', sym.hard_sat(gate_rate_signal, uc, uo),
        gate_rate_initial,
    )
    control.differential(
        gate_state, gate_rate, Const(gate_initial), pmin, pmax,
    )

    # An absent all-zero characteristic means the standard unit gate-to-power line.
    if curve_unspecified:
        curve_power_expression: Expr = gate_state
        curve_initial: float = gate_initial
    else:
        curve_power_expression = build_gov_hydro_ieee2_curve(
            gate_state, gv_points, pgv_points,
        )
        curve_initial = get_gov_hydro_ieee2_curve_power(settings, gate_initial)
    curve_power: Var = control.algebraic(
        'CurvePowerPu', curve_power_expression, Const(curve_initial),
    )

    # The water transfer preserves its inverse-response zero and exact zero-TW limit.
    if settings.tw > 0.0:
        water_state: Var = control.lag(
            'WaterColumnMemoryPu', curve_power, bturb * tw,
            settings.bturb * settings.tw, Const(curve_initial),
        )
        turbine_shape: Var = control.algebraic(
            'WaterTurbineShapePu',
            water_state + aturb / bturb * (curve_power - water_state),
            Const(curve_initial),
        )
    else:
        turbine_shape = control.algebraic(
            'WaterTurbineShapePu', curve_power, Const(curve_initial),
        )
    mechanical_power: Var = control.algebraic(
        'PmPu', kturb * turbine_shape, Const(settings.kturb * curve_initial),
    )
    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovHydroIEEE2 hydraulic-dashpot governor and turbine',
    )

    # Canonical RDF fields remain visible alongside symbols consumed by equations.
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    template.comment = 'CGMES GovHydroIEEE2 IEEE hydro equations with exact zero-time stages.'
    rdf_parameter_names: tuple[str, ...] = (
        'enabled', 'mwbase', 'tg', 'tp', 'uo', 'uc', 'pmax', 'pmin', 'rperm',
        'rtemp', 'tr', 'tw', 'kturb', 'aturb', 'bturb', 'gv1', 'pgv1', 'gv2',
        'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6',
    )
    for parameter_name in rdf_parameter_names:
        parameter_variable: Var = vfactory.add_var(
            f'GovHydroIEEE2.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template


def build_gov_hydro_ieee2_curve(
        gate: Expr,
        gv_points: tuple[Var, Var, Var, Var, Var, Var],
        pgv_points: tuple[Var, Var, Var, Var, Var, Var],
) -> Expr:
    """Build the imported six-point gate-to-turbine-power curve.

    :param gate: Bounded gate-opening signal.
    :param gv_points: Increasing gate positions from the RDF object.
    :param pgv_points: Nondecreasing powers paired with the gate positions.
    :return: Continuous piecewise-linear characteristic with endpoint extension.
    """
    expression: Expr = pgv_points[0]
    for point_index in range(5):
        lower_gate: Var = gv_points[point_index]
        upper_gate: Var = gv_points[point_index + 1]
        lower_power: Var = pgv_points[point_index]
        upper_power: Var = pgv_points[point_index + 1]
        gate_span: Expr = upper_gate - lower_gate
        power_slope: Expr = (upper_power - lower_power) / gate_span
        segment_gate: Expr = sym.min(
            sym.max(gate - lower_gate, Const(0.0)), gate_span,
        )
        expression = expression + power_slope * segment_gate
    return expression


def get_gov_hydro_ieee2_curve_power(
        parameters: GovHydroIEEE2Parameters,
        gate: float,
) -> float:
    """Evaluate the same piecewise-linear characteristic for initialization.

    :param parameters: Imported nonlinear curve.
    :param gate: Initial gate position in pu.
    :return: Initial turbine-curve power in pu.
    """
    curve_unspecified: bool = all(
        parameters.gv_points[index] == 0.0 and parameters.pgv_points[index] == 0.0
        for index in range(6)
    )
    if curve_unspecified:
        return gate
    else:
        pass
    curve_power: float = parameters.pgv_points[0]
    for point_index in range(5):
        lower_gate: float = parameters.gv_points[point_index]
        upper_gate: float = parameters.gv_points[point_index + 1]
        lower_power: float = parameters.pgv_points[point_index]
        upper_power: float = parameters.pgv_points[point_index + 1]
        segment_gate: float = min(max(gate - lower_gate, 0.0), upper_gate - lower_gate)
        curve_power += (upper_power - lower_power) * segment_gate / (upper_gate - lower_gate)
    return curve_power


def get_gov_hydro_ieee2_gate_for_power(
        parameters: GovHydroIEEE2Parameters,
        target_power: float,
) -> float | None:
    """Invert the monotone turbine curve for an imported operating point.

    :param parameters: Imported model curve and gate limits.
    :param target_power: Turbine-curve power in pu before ``kturb``.
    :return: Gate opening, or ``None`` when the target is outside the curve.
    """
    curve_unspecified: bool = all(
        parameters.gv_points[index] == 0.0 and parameters.pgv_points[index] == 0.0
        for index in range(6)
    )
    if curve_unspecified:
        return min(max(target_power, parameters.pmin), parameters.pmax)
    elif target_power < parameters.pgv_points[0] or target_power > parameters.pgv_points[-1]:
        return None
    else:
        pass
    gate_result: float | None = None
    for point_index in range(5):
        lower_power: float = parameters.pgv_points[point_index]
        upper_power: float = parameters.pgv_points[point_index + 1]
        if gate_result is None and lower_power <= target_power <= upper_power:
            lower_gate: float = parameters.gv_points[point_index]
            upper_gate: float = parameters.gv_points[point_index + 1]
            if upper_power > lower_power:
                power_fraction: float = (target_power - lower_power) / (upper_power - lower_power)
                gate_result = lower_gate + power_fraction * (upper_gate - lower_gate)
            else:
                gate_result = lower_gate
        else:
            pass
    if gate_result is None:
        return parameters.gv_points[-1]
    else:
        return min(max(gate_result, parameters.pmin), parameters.pmax)
