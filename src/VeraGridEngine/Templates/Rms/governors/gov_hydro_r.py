# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES GovHydroR fourth-order lead-lag hydro governor equations."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.common.speed_deadband import (
    build_intentional_speed_deadband,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydroRParameters:
    """Canonical GovHydroR equation parameters and model units."""

    __slots__ = (
        'mwbase', 'pmax', 'pmin', 'r', 'td', 't1', 't2', 't3', 't4', 't5',
        't6', 't7', 't8', 'tp', 'velop', 'velcl', 'ki', 'kg', 'gmax', 'gmin',
        'tt', 'inputSignal', 'db1', 'eps', 'db2', 'tw', 'at', 'dturb', 'qnl',
        'h0', 'gv_points', 'pgv_points', 'nominal_frequency',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            pmax: float = 1.0,
            pmin: float = 0.0,
            r: float = 0.05,
            td: float = 0.05,
            t1: float = 1.5,
            t2: float = 0.1,
            t3: float = 1.5,
            t4: float = 0.1,
            t5: float = 0.0,
            t6: float = 0.05,
            t7: float = 0.0,
            t8: float = 0.05,
            tp: float = 0.05,
            velop: float = 0.0,
            velcl: float = 0.0,
            ki: float = 0.0,
            kg: float = 1.0,
            gmax: float = 1.0,
            gmin: float = 0.0,
            tt: float = 0.0,
            inputSignal: bool = True,
            db1: float = 0.0,
            eps: float = 0.0,
            db2: float = 0.0,
            tw: float = 1.0,
            at: float = 1.0,
            dturb: float = 0.0,
            qnl: float = 0.08,
            h0: float = 1.0,
            gv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.2, 0.4, 0.6, 0.8, 1.0,
            ),
            pgv_points: tuple[float, float, float, float, float, float] = (
                0.0, 0.2, 0.4, 0.6, 0.8, 1.0,
            ),
            nominal_frequency: float = 50.0,
    ) -> None:
        """Store RDF coefficients without renaming their canonical fields.

        :param mwbase: Active power base in MW.
        :param pmax: Maximum integrator output.
        :param pmin: Minimum integrator output.
        :param r: Steady-state droop.
        :param td: Input filter time in seconds.
        :param t1: First lead time in seconds.
        :param t2: First lag time in seconds.
        :param t3: Second lead time in seconds.
        :param t4: Second lag time in seconds.
        :param t5: Third lead time in seconds.
        :param t6: Third lag time in seconds.
        :param t7: Fourth lead time in seconds.
        :param t8: Fourth lag time in seconds.
        :param tp: Gate servo time in seconds.
        :param velop: Gate opening velocity limit in pu/s.
        :param velcl: Gate closing velocity limit in pu/s.
        :param ki: Integral gain.
        :param kg: Gate servo gain.
        :param gmax: Maximum governor integrator output.
        :param gmin: Minimum governor integrator output.
        :param tt: Power feedback filter time in seconds.
        :param inputSignal: True selects gate feedback; false selects power feedback.
        :param db1: Intentional speed deadband width in Hz.
        :param eps: Intentional deadband hysteresis width in Hz.
        :param db2: Turbine power deadband width in pu.
        :param tw: Water inertia time in seconds.
        :param at: Turbine gain.
        :param dturb: Turbine speed damping.
        :param qnl: No-load turbine flow at nominal head.
        :param h0: Nominal head.
        :param gv_points: Six gate coordinates from the RDF fields.
        :param pgv_points: Six turbine powers corresponding to gate coordinates.
        :param nominal_frequency: System frequency in Hz for db1/eps conversion.
        """
        self.mwbase: float = mwbase
        self.pmax: float = pmax
        self.pmin: float = pmin
        self.r: float = r
        self.td: float = td
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.t5: float = t5
        self.t6: float = t6
        self.t7: float = t7
        self.t8: float = t8
        self.tp: float = tp
        self.velop: float = velop
        self.velcl: float = velcl
        self.ki: float = ki
        self.kg: float = kg
        self.gmax: float = gmax
        self.gmin: float = gmin
        self.tt: float = tt
        self.inputSignal: bool = inputSignal
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


def _gov_hydro_r_deadband(signal: Expr, width: float) -> Expr:
    """Apply the symmetric static DB2 deadband shown in the source diagram.

    :param signal: Turbine curve power.
    :param width: Deadband width in per unit.
    :return: Power outside the dead zone.
    """
    positive: Expr = sym.max(signal - width / 2.0, Const(0.0))
    negative: Expr = sym.min(signal + width / 2.0, Const(0.0))
    return positive + negative


def build_gov_hydro_r_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroRParameters | None = None,
) -> RmsModelTemplate:
    """Build the fourth-order lead-lag governor and hydro turbine.

    :param vfactory: Factory owning the symbolic variables.
    :param name: Optional runtime model name.
    :param parameters: Canonical GovHydroR coefficients.
    :return: Equation-backed governor with speed, reference, and power inputs.
    :raises ValueError: Nonfinite or invalid physical settings.
    """
    settings: GovHydroRParameters = (
        GovHydroRParameters() if parameters is None else parameters
    )
    times: tuple[float, ...] = (
        settings.td, settings.t1, settings.t2, settings.t3, settings.t4,
        settings.t5, settings.t6, settings.t7, settings.t8, settings.tp,
        settings.tt, settings.tw,
    )
    values: tuple[float, ...] = (
        settings.mwbase, settings.pmax, settings.pmin, settings.r, settings.velop,
        settings.velcl, settings.ki, settings.kg, settings.gmax, settings.gmin,
        settings.db1, settings.eps, settings.db2, settings.at, settings.dturb,
        settings.qnl, settings.h0, settings.nominal_frequency,
        *settings.gv_points, *settings.pgv_points,
    )
    if not all(math.isfinite(value) for value in (*times, *values)):
        raise ValueError('GovHydroR parameters must be finite')
    elif min(times) < 0.0 or settings.mwbase <= 0.0 or settings.r <= 0.0 or settings.nominal_frequency <= 0.0:
        raise ValueError('GovHydroR times, MWBASE, and droop must be nonnegative/positive')
    elif settings.pmin >= settings.pmax or settings.gmin >= settings.gmax:
        raise ValueError('GovHydroR gate and governor limits must be ordered')
    elif settings.velop < 0.0 or settings.velcl > 0.0 or settings.kg < 0.0:
        raise ValueError('GovHydroR gate rates must be signed and gain nonnegative')
    elif settings.db1 < 0.0 or settings.eps < 0.0 or settings.db2 < 0.0:
        raise ValueError('GovHydroR deadband widths must be nonnegative')
    elif settings.h0 <= 0.0 or settings.at <= 0.0 or settings.tw < 0.0:
        raise ValueError('GovHydroR turbine head/gain/water time are invalid')
    elif any(
            settings.gv_points[index] >= settings.gv_points[index + 1]
            or settings.pgv_points[index] > settings.pgv_points[index + 1]
            for index in range(5)
    ):
        raise ValueError('GovHydroR turbine curve coordinates must be monotone')
    else:
        pass

    template_name: str = 'GovHydroR' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    speed: Var = control.input('OmegaPu', Const(1.0))
    reference: Var = control.input('PRefPu', Const(0.5))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.5))

    # Convert RDF hertz thresholds to pu speed and retain their source hysteresis modes.
    speed_deviation: Expr = Const(1.0) - speed
    deadbanded_speed: Expr = build_intentional_speed_deadband(
        control,
        speed_deviation,
        Const(settings.db1 / settings.nominal_frequency),
        Const(settings.eps / settings.nominal_frequency),
    )
    filtered_speed: Var = control.lag(
        'InputFilterPu', deadbanded_speed,
        control.parameter('TD', settings.td), settings.td, Const(0.0),
    )
    lead_lag_output: Expr = filtered_speed
    lead_lag_settings: tuple[tuple[float, float], ...] = (
        (settings.t1, settings.t2), (settings.t3, settings.t4),
        (settings.t5, settings.t6), (settings.t7, settings.t8),
    )
    for index, lead_lag_setting in enumerate(lead_lag_settings):
        lead_time: float = lead_lag_setting[0]
        lag_time: float = lead_lag_setting[1]
        lead_lag_output = control.lead_lag(
            f'LeadLag{index + 1}Pu',
            lead_lag_output,
            control.parameter(f'T{index * 2 + 1}', lead_time),
            control.parameter(f'T{index * 2 + 2}', lag_time),
            lead_time,
            lag_time,
            Const(0.0),
        )

    # Declare controller states first because gate feedback closes an algebraic loop.
    governor_output: Var = vfactory.add_var(f'GovernorOutputPu_{template_name}')
    gate_state: Var = vfactory.add_var(f'GatePu_{template_name}')

    # Gate feedback uses PI output; power feedback uses the TT-filtered machine signal.
    if settings.inputSignal:
        feedback_value: Expr = governor_output
    elif settings.tt > 0.0:
        filtered_power: Var = control.lag(
            'PowerFeedbackPu', electrical_power,
            control.parameter('TT', settings.tt), settings.tt, Const(0.5),
        )
        feedback_value = filtered_power
    else:
        feedback_value = electrical_power
    governor_error: Expr = reference + lead_lag_output - settings.r * feedback_value
    control.differential(
        governor_output,
        settings.ki * governor_error,
        Const(0.5),
        control.parameter('GMIN', settings.gmin),
        control.parameter('GMAX', settings.gmax),
    )

    # Integrate bounded gate motion after the specified KG/(1+s*TP) servo.
    servo: Var = control.lag(
        'GateServoPu', settings.kg * (governor_output - gate_state),
        control.parameter('TP', settings.tp), settings.tp, Const(0.0),
    )
    gate_rate: Var = control.algebraic(
        'GateRatePuPerSecond', sym.hard_sat(servo, settings.velcl, settings.velop),
        Const(0.0),
    )
    control.differential(
        gate_state,
        gate_rate,
        Const(0.5),
        control.parameter('PMIN', settings.pmin),
        control.parameter('PMAX', settings.pmax),
    )

    # Build the six-point gate curve as continuous, clipped linear segments.
    curve_expression: Expr = Const(settings.pgv_points[0])
    for curve_index in range(5):
        segment_width: float = (
            settings.gv_points[curve_index + 1] - settings.gv_points[curve_index]
        )
        segment: Expr = sym.min(
            sym.max(gate_state - settings.gv_points[curve_index], Const(0.0)),
            Const(segment_width),
        )
        slope: float = (
            settings.pgv_points[curve_index + 1] - settings.pgv_points[curve_index]
        ) / segment_width
        curve_expression = curve_expression + slope * segment
    curve_power: Var = control.algebraic(
        'GateCurvePowerPu', curve_expression, Const(0.5),
    )
    deadband_power: Expr = _gov_hydro_r_deadband(curve_power, settings.db2)
    turbine_power: Var = control.algebraic(
        'TurbinePowerPu', deadband_power, Const(0.5),
    )
    water_power: Var = control.lead_lag(
        'WaterPowerPu',
        turbine_power,
        -control.parameter('TWLead', settings.tw),
        control.parameter('TWHalf', settings.tw / 2.0),
        -settings.tw,
        settings.tw / 2.0,
        Const(0.5),
    ) if settings.tw > 0.0 else control.algebraic(
        'WaterPowerPu', turbine_power, Const(0.5),
    )
    mechanical_power: Var = control.algebraic(
        'PmPu', settings.at * (water_power - settings.qnl) * settings.h0
        - settings.dturb * gate_state * speed_deviation,
        Const(0.5),
    )
    return control.finish(
        (mechanical_power, gate_state, gate_rate),
        'CGMES GovHydroR fourth-order lead-lag governor and hydro turbine',
    )
