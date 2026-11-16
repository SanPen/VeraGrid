# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovSteamFV3 governor with fast valving."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.governors.gov_steam1 import (
    build_gov_steam1_valve_curve,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Func2, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovSteamFV3Parameters:
    """Construction values for the exact scalar fields in CGMES GovSteamFV3."""

    __slots__ = (
        'mwbase', 'k', 't1', 't2', 't3', 'uo', 'uc', 'pmax', 'pmin', 't4', 'k1',
        't5', 'k2', 't6', 'k3', 'ta', 'tb', 'tc', 'prmax', 'gv1', 'pgv1', 'gv2',
        'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            k: float = 20.0,
            t1: float = 0.0,
            t2: float = 0.0,
            t3: float = 0.1,
            uo: float = 0.1,
            uc: float = -1.0,
            pmax: float = 1.0,
            pmin: float = 0.0,
            t4: float = 0.2,
            k1: float = 0.2,
            t5: float = 0.5,
            k2: float = 0.2,
            t6: float = 10.0,
            k3: float = 0.6,
            ta: float = 0.1,
            tb: float = 0.2,
            tc: float = 0.5,
            prmax: float = 1.0,
            gv1: float = 0.0,
            pgv1: float = 0.0,
            gv2: float = 0.25,
            pgv2: float = 0.25,
            gv3: float = 0.5,
            pgv3: float = 0.5,
            gv4: float = 0.75,
            pgv4: float = 0.75,
            gv5: float = 1.0,
            pgv5: float = 1.0,
            gv6: float = 1.25,
            pgv6: float = 1.25,
    ) -> None:
        """Store governor, fast-valving, and optional valve-curve values.

        :param mwbase: Mechanical-power base in MW.
        :param k: Reciprocal speed droop gain.
        :param t1: Lead time in the speed compensator, seconds.
        :param t2: Lag time in the speed compensator, seconds.
        :param t3: Valve positioner time, seconds.
        :param uo: Maximum valve opening rate, pu/s.
        :param uc: Maximum valve closing rate, pu/s; negative.
        :param pmax: Maximum valve position, pu.
        :param pmin: Minimum valve position, pu.
        :param t4: Steam chest time, seconds.
        :param k1: First turbine power fraction.
        :param t5: Reheater time, seconds.
        :param k2: Reheater power fraction.
        :param t6: Crossover time, seconds.
        :param k3: Crossover power fraction.
        :param ta: Intercept-valve closure duration, seconds.
        :param tb: Time until reopening starts, seconds.
        :param tc: Time until reopening completes, seconds.
        :param prmax: Maximum reheater pressure, pu.
        :param gv1: First optional governor-valve curve point.
        :param pgv1: First optional governor-power curve point.
        :param gv2: Second optional governor-valve curve point.
        :param pgv2: Second optional governor-power curve point.
        :param gv3: Third optional governor-valve curve point.
        :param pgv3: Third optional governor-power curve point.
        :param gv4: Fourth optional governor-valve curve point.
        :param pgv4: Fourth optional governor-power curve point.
        :param gv5: Fifth optional governor-valve curve point.
        :param pgv5: Fifth optional governor-power curve point.
        :param gv6: Sixth optional governor-valve curve point.
        :param pgv6: Sixth optional governor-power curve point.
        """
        self.mwbase: float = mwbase
        self.k: float = k
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.uo: float = uo
        self.uc: float = uc
        self.pmax: float = pmax
        self.pmin: float = pmin
        self.t4: float = t4
        self.k1: float = k1
        self.t5: float = t5
        self.k2: float = k2
        self.t6: float = t6
        self.k3: float = k3
        self.ta: float = ta
        self.tb: float = tb
        self.tc: float = tc
        self.prmax: float = prmax
        self.gv1: float = gv1
        self.pgv1: float = pgv1
        self.gv2: float = gv2
        self.pgv2: float = pgv2
        self.gv3: float = gv3
        self.pgv3: float = pgv3
        self.gv4: float = gv4
        self.pgv4: float = pgv4
        self.gv5: float = gv5
        self.pgv5: float = pgv5
        self.gv6: float = gv6
        self.pgv6: float = pgv6

    @property
    def gv_points(self) -> tuple[float, float, float, float, float, float]:
        """Return the six CGMES valve positions in curve order.

        :return: Valve positions paired with ``pgv_points``.
        """
        return self.gv1, self.gv2, self.gv3, self.gv4, self.gv5, self.gv6

    @property
    def pgv_points(self) -> tuple[float, float, float, float, float, float]:
        """Return the six CGMES valve-power points in curve order.

        :return: Power values paired with ``gv_points``.
        """
        return self.pgv1, self.pgv2, self.pgv3, self.pgv4, self.pgv5, self.pgv6


def build_gov_steam_f_v3_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovSteamFV3Parameters | None = None,
) -> RmsModelTemplate:
    """Build the rate-limited governor, pressure stages, and fast-valving equations.

    :param vfactory: Factory that owns all symbolic variables.
    :param name: Optional unique runtime-template name.
    :param parameters: Canonical GovSteamFV3 scalar values.
    :return: Equation-backed CGMES template with one speed and power reference.
    :raises ValueError: Invalid domains, limits, valve fractions, or curve timing.
    """
    settings: GovSteamFV3Parameters = (
        GovSteamFV3Parameters() if parameters is None else parameters
    )
    values: tuple[float, ...] = (
        settings.mwbase, settings.k, settings.t1, settings.t2, settings.t3,
        settings.uo, settings.uc, settings.pmax, settings.pmin, settings.t4,
        settings.k1, settings.t5, settings.k2, settings.t6, settings.k3,
        settings.ta, settings.tb, settings.tc, settings.prmax,
        settings.gv1, settings.pgv1, settings.gv2, settings.pgv2, settings.gv3,
        settings.pgv3, settings.gv4, settings.pgv4, settings.gv5, settings.pgv5,
        settings.gv6, settings.pgv6,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES GovSteamFV3 parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.k < 0.0:
        raise ValueError('CGMES GovSteamFV3 requires positive mwbase and nonnegative droop gain')
    elif min(settings.t1, settings.t2, settings.t3, settings.t4, settings.t5, settings.t6) < 0.0:
        raise ValueError('CGMES GovSteamFV3 time constants must be nonnegative')
    elif settings.t2 == 0.0 and settings.t1 != 0.0:
        raise ValueError('CGMES GovSteamFV3 zero speed lag requires zero lead')
    elif settings.t3 <= 0.0:
        raise ValueError('CGMES GovSteamFV3 requires positive valve positioner time t3')
    elif settings.uo <= 0.0 or settings.uc >= 0.0 or settings.pmin >= settings.pmax:
        raise ValueError('CGMES GovSteamFV3 requires signed rate limits and ordered valve limits')
    elif min(settings.k1, settings.k2, settings.k3) < 0.0:
        raise ValueError('CGMES GovSteamFV3 turbine fractions must be nonnegative')
    elif settings.k1 + settings.k2 + settings.k3 <= 0.0 or settings.prmax <= 0.0:
        raise ValueError('CGMES GovSteamFV3 needs positive turbine gain and reheater pressure limit')
    elif not 0.0 <= settings.ta < settings.tb < settings.tc:
        raise ValueError('CGMES GovSteamFV3 requires 0 <= ta < tb < tc')
    elif not all(
            settings.gv_points[index] < settings.gv_points[index + 1]
            for index in range(5)
    ):
        raise ValueError('CGMES GovSteamFV3 valve positions must increase strictly')
    else:
        pass

    template_name: str = 'GovSteamFV3' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    curve_gate_variables: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        vfactory.add_var(f'GovSteamFV3.gv{index + 1}_{template_name}')
        for index in range(6)
    )
    curve_power_variables: tuple[Var, Var, Var, Var, Var, Var] = tuple(
        vfactory.add_var(f'GovSteamFV3.pgv{index + 1}_{template_name}')
        for index in range(6)
    )
    curve_gate_values: tuple[float, float, float, float, float, float] = (
        settings.gv1, settings.gv2, settings.gv3,
        settings.gv4, settings.gv5, settings.gv6,
    )
    curve_power_values: tuple[float, float, float, float, float, float] = (
        settings.pgv1, settings.pgv2, settings.pgv3,
        settings.pgv4, settings.pgv5, settings.pgv6,
    )
    for point_index in range(6):
        control.block.event_dict[curve_gate_variables[point_index]] = vfactory.add_const(
            curve_gate_values[point_index],
            name=curve_gate_variables[point_index].name,
        )
        control.block.event_dict[curve_power_variables[point_index]] = vfactory.add_const(
            curve_power_values[point_index],
            name=curve_power_variables[point_index].name,
        )
    speed_gain: Var = control.parameter('k', settings.k)
    speed_lead: Var = control.parameter('t1', settings.t1)
    speed_lag: Var = control.parameter('t2', settings.t2)
    valve_time: Var = control.parameter('t3', settings.t3)
    opening_rate: Var = control.parameter('uo', settings.uo)
    closing_rate: Var = control.parameter('uc', settings.uc)
    valve_maximum: Var = control.parameter('pmax', settings.pmax)
    valve_minimum: Var = control.parameter('pmin', settings.pmin)
    chest_time: Var = control.parameter('t4', settings.t4)
    reheater_time: Var = control.parameter('t5', settings.t5)
    crossover_time: Var = control.parameter('t6', settings.t6)
    first_fraction: Var = control.parameter('k1', settings.k1)
    second_fraction: Var = control.parameter('k2', settings.k2)
    third_fraction: Var = control.parameter('k3', settings.k3)
    power_base: Var = control.parameter('mwbase', settings.mwbase)
    pressure_limit: Var = control.parameter('prmax', settings.prmax)
    close_time: Var = control.parameter('ta', settings.ta)
    reopen_time: Var = control.parameter('tb', settings.tb)
    full_open_time: Var = control.parameter('tc', settings.tc)
    omega: Var = control.input('OmegaPu', Const(1.0))
    omega_reference: Var = control.input('OmegaRefPu', Const(1.0))
    power_reference: Var = control.input('PmRefPu', Const(0.0))
    # The canonical class omits the event time even though its diagram defines a relative schedule.
    fast_valving_start_time: Var = control.input('FastValvingStartTimeSec', Const(0.0))

    # Normalize reference power by the stage fractions, then invert the valve curve.
    total_fraction: Expr = first_fraction + second_fraction + third_fraction
    maximum_flow: Var = curve_power_variables[5]
    initial_flow: Expr = Func2(
        'min',
        Func2('max', power_reference / total_fraction, Const(0.0)),
        maximum_flow,
    )
    initial_valve: Expr = curve_gate_variables[0]
    initial_curve_delta: Expr = initial_flow - curve_power_variables[0]
    for point_index in range(5):
        power_increment: Expr = Func2(
            'min',
            Func2('max', initial_curve_delta, Const(0.0)),
            curve_power_variables[point_index + 1] - curve_power_variables[point_index],
        )
        gate_increment: Expr = (
            (curve_gate_variables[point_index + 1] - curve_gate_variables[point_index])
            / (curve_power_variables[point_index + 1] - curve_power_variables[point_index])
        ) * power_increment
        initial_valve = initial_valve + gate_increment
        initial_curve_delta = initial_curve_delta - power_increment
    speed_error: Expr = omega - omega_reference
    compensated_speed: Var = control.lead_lag(
        'GovSteamFV3SpeedCompensatedPu',
        speed_error,
        speed_lead,
        speed_lag,
        settings.t1,
        settings.t2,
        Const(0.0),
    )
    valve: Var = vfactory.add_var(f'GovSteamFV3ValvePu_{template_name}')
    valve_error: Expr = initial_valve - speed_gain * compensated_speed - valve
    valve_velocity: Expr = sym.hard_sat(
        valve_error / valve_time,
        closing_rate,
        opening_rate,
    )
    valve_velocity_signal: Var = control.algebraic(
        'GovSteamFV3ValveVelocityPu',
        valve_velocity,
        Const(0.0),
    )
    control.differential(
        valve,
        valve_velocity_signal,
        initial_valve,
        valve_minimum,
        valve_maximum,
    )

    valve_power: Var = control.algebraic(
        'GovSteamFV3ValvePowerPu',
        build_gov_steam1_valve_curve(
            gate=valve,
            gv_points=curve_gate_variables,
            pgv_points=curve_power_variables,
        ),
        initial_flow,
    )
    chest_power: Var = control.lag(
        'GovSteamFV3SteamChestPu', valve_power, chest_time, settings.t4, initial_flow,
    )
    reheater_power: Var = control.lag(
        'GovSteamFV3ReheaterPu', chest_power, reheater_time, settings.t5, initial_flow,
    )
    simulation_time: Var = vfactory.add_var('glob_time')
    elapsed_time: Expr = simulation_time - fast_valving_start_time
    if settings.ta > 0.0:
        close_fraction: Expr = sym.hard_sat(
            elapsed_time / close_time,
            Const(0.0),
            Const(1.0),
        )
    else:
        close_fraction = sym.heaviside(elapsed_time)
    if settings.tc > settings.tb:
        reopen_fraction: Expr = sym.hard_sat(
            (elapsed_time - reopen_time) / (full_open_time - reopen_time),
            Const(0.0),
            Const(1.0),
        )
    else:
        reopen_fraction = sym.heaviside(elapsed_time - reopen_time)
    intercept_position: Expr = Const(1.0) - close_fraction + reopen_fraction
    intercept_position = sym.hard_sat(intercept_position, Const(0.0), Const(1.0))
    pressure: Var = control.algebraic(
        'GovSteamFV3ReheaterPressurePu',
        sym.hard_sat(reheater_power * intercept_position, Const(0.0), pressure_limit),
        initial_flow,
    )
    crossover_power: Var = control.lag(
        'GovSteamFV3CrossoverPu', pressure, crossover_time, settings.t6, initial_flow,
    )
    mechanical_power_pu: Var = control.algebraic(
        'gov.PmPu',
        first_fraction * chest_power + second_fraction * pressure + third_fraction * crossover_power,
        power_reference,
    )
    mechanical_power_mw: Var = control.algebraic(
        'gov.PmMW', power_base * mechanical_power_pu, power_base * power_reference,
    )
    template: RmsModelTemplate = control.finish(
        (mechanical_power_pu, mechanical_power_mw),
        'CGMES GovSteamFV3 pressure-limited turbine with fast valving',
    )
    template.comment = (
        'CGMES GovSteamFV3 equations from its diagram: rate-limited valve, three '
        'turbine sections, reheater pressure cap, and fast-valving schedule.'
    )

    # Keep every RDF scalar directly inspectable on the CGMES-owned template.
    rdf_values: tuple[tuple[str, float], ...] = (
        ('mwbase', settings.mwbase), ('k', settings.k), ('t1', settings.t1),
        ('t2', settings.t2), ('t3', settings.t3), ('uo', settings.uo),
        ('uc', settings.uc), ('pmax', settings.pmax), ('pmin', settings.pmin),
        ('t4', settings.t4), ('k1', settings.k1), ('t5', settings.t5),
        ('k2', settings.k2), ('t6', settings.t6), ('k3', settings.k3),
        ('ta', settings.ta), ('tb', settings.tb), ('tc', settings.tc),
        ('prmax', settings.prmax), ('gv1', settings.gv1), ('pgv1', settings.pgv1),
        ('gv2', settings.gv2), ('pgv2', settings.pgv2), ('gv3', settings.gv3),
        ('pgv3', settings.pgv3), ('gv4', settings.gv4), ('pgv4', settings.pgv4),
        ('gv5', settings.gv5), ('pgv5', settings.pgv5), ('gv6', settings.gv6),
        ('pgv6', settings.pgv6),
    )
    for property_name, property_value in rdf_values:
        parameter_variable: Var = vfactory.add_var(
            f'GovSteamFV3.{property_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=property_value,
            name=parameter_variable.name,
        )
    return template
