# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E GAST2A gas-turbine governor equations."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Gast2aParameters:
    """Store the 31 ordered GAST2A source constants."""

    __slots__ = (
        'w', 'x', 'y', 'z', 'etd', 'tcd', 'trate', 't', 'maximum', 'minimum',
        'ecr', 'k3', 'a', 'b', 'c', 'tauf', 'kf', 'k5', 'k4', 't3', 't4',
        'taut', 't5', 'af1', 'bf1', 'af2', 'bf2', 'cf2', 'tr', 'k6', 'tc',
    )

    def __init__(
            self,
            w: float = 20.0,
            x: float = 0.1,
            y: float = 0.2,
            z: int = 1,
            etd: float = 0.04,
            tcd: float = 0.1,
            trate: float = 100.0,
            t: float = 0.04,
            maximum: float = 1.0,
            minimum: float = 0.0,
            ecr: float = 0.04,
            k3: float = 1.0,
            a: float = 1.0,
            b: float = 0.1,
            c: float = 1.0,
            tauf: float = 0.3,
            kf: float = 0.0,
            k5: float = 0.5,
            k4: float = 0.5,
            t3: float = 0.5,
            t4: float = 0.1,
            taut: float = 0.2,
            t5: float = 0.1,
            af1: float = 0.0,
            bf1: float = 0.0,
            af2: float = 1.6,
            bf2: float = 1.0,
            cf2: float = 0.0,
            tr: float = 1.0,
            k6: float = 0.0,
            tc: float = 1.0,
    ) -> None:
        """Store constants in PSS/E Model Library order.

        :param w: Governor gain on turbine base.
        :param x: Governor lead time in seconds.
        :param y: Governor lag time in seconds.
        :param z: Governor selector, one for droop or zero for isochronous.
        :param etd: Turbine exhaust delay in seconds.
        :param tcd: Gas-turbine dynamic lag in seconds.
        :param trate: Turbine rating in MW.
        :param t: Fuel-controller delay in seconds.
        :param maximum: Speed-governor maximum on turbine base.
        :param minimum: Speed-governor minimum on turbine base.
        :param ecr: Combustor delay in seconds.
        :param k3: Fuel-control gain.
        :param a: Valve-positioner numerator gain.
        :param b: Valve-positioner derivative coefficient.
        :param c: Valve-positioner proportional coefficient.
        :param tauf: Fuel-system lag in seconds.
        :param kf: Fuel-flow feedback gain.
        :param k5: Dynamic radiation-shield gain.
        :param k4: Direct radiation-shield gain.
        :param t3: Radiation-shield lag in seconds.
        :param t4: Thermocouple lag in seconds.
        :param taut: Temperature-controller integral time in seconds.
        :param t5: Temperature-controller lead time in seconds.
        :param af1: Turbine f1 fuel coefficient.
        :param bf1: Turbine f1 speed coefficient.
        :param af2: Turbine f2 fuel intercept.
        :param bf2: Turbine f2 fuel coefficient.
        :param cf2: Turbine f2 speed coefficient.
        :param tr: Rated turbine exhaust temperature.
        :param k6: Minimum fuel-flow term.
        :param tc: Temperature-control reference.
        """
        self.w: float = w
        self.x: float = x
        self.y: float = y
        self.z: int = z
        self.etd: float = etd
        self.tcd: float = tcd
        self.trate: float = trate
        self.t: float = t
        self.maximum: float = maximum
        self.minimum: float = minimum
        self.ecr: float = ecr
        self.k3: float = k3
        self.a: float = a
        self.b: float = b
        self.c: float = c
        self.tauf: float = tauf
        self.kf: float = kf
        self.k5: float = k5
        self.k4: float = k4
        self.t3: float = t3
        self.t4: float = t4
        self.taut: float = taut
        self.t5: float = t5
        self.af1: float = af1
        self.bf1: float = bf1
        self.af2: float = af2
        self.bf2: float = bf2
        self.cf2: float = cf2
        self.tr: float = tr
        self.k6: float = k6
        self.tc: float = tc


def build_gast2a_template(
        vf: VarFactory,
        name: str,
        parameters: Gast2aParameters | None = None,
        initial_mechanical_power_pu: float = 0.8,
        initial_speed_deviation_pu: float = 0.0,
) -> RmsModelTemplate:
    """Build the 13-state GAST2A speed, fuel, temperature and turbine chain.

    The three PSS/E transport-delay blocks are realized as two equal first-order
    stages each, matching the documented pair of delay states. This realization
    remains a source approximation and must be compared with PSS/E before the
    DYR binding is enabled.

    :param vf: Symbol factory owning the model equations.
    :param name: Unique model instance name.
    :param parameters: The 31 source constants; defaults form a test operating point.
    :param initial_mechanical_power_pu: Solved shaft power on turbine rating.
    :param initial_speed_deviation_pu: Solved speed minus synchronous speed.
    :return: A two-input, one-output governor on turbine power base.
    :raises ValueError: Source values or the requested equilibrium are infeasible.
    """
    p: Gast2aParameters = Gast2aParameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        p.w, p.x, p.y, float(p.z), p.etd, p.tcd, p.trate, p.t, p.maximum,
        p.minimum, p.ecr, p.k3, p.a, p.b, p.c, p.tauf, p.kf, p.k5, p.k4,
        p.t3, p.t4, p.taut, p.t5, p.af1, p.bf1, p.af2, p.bf2, p.cf2,
        p.tr, p.k6, p.tc, initial_mechanical_power_pu,
        initial_speed_deviation_pu,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('GAST2A constants and operating point must be finite')
    elif p.w <= 0.0 or p.y <= 0.0 or p.z not in (0, 1):
        raise ValueError('GAST2A requires positive W/Y and Z equal to zero or one')
    elif p.trate <= 0.0 or p.minimum >= p.maximum:
        raise ValueError('GAST2A turbine rating and governor limits are invalid')
    elif min(p.etd, p.tcd, p.t, p.ecr, p.x) < 0.0:
        raise ValueError('GAST2A governor and delay times must be nonnegative')
    elif min(p.k3, p.a, p.b, p.c, p.tauf, p.t3, p.t4, p.taut, p.t5) <= 0.0:
        raise ValueError('GAST2A fuel, valve and temperature time constants must be positive')
    elif initial_mechanical_power_pu <= 0.0 or 1.0 + initial_speed_deviation_pu <= 0.0:
        raise ValueError('GAST2A initial mechanical power and absolute speed must be positive')
    else:
        pass

    # The turbine f2 relation uniquely determines steady fuel when BF2 is nonzero.
    absolute_speed: float = 1.0 + initial_speed_deviation_pu
    if p.bf2 == 0.0:
        if not math.isclose(
                initial_mechanical_power_pu / absolute_speed,
                p.af2 - p.cf2 * initial_speed_deviation_pu,
                rel_tol=0.0, abs_tol=1e-9):
            raise ValueError('GAST2A BF2=0 cannot match the requested shaft power')
        else:
            initial_fuel_flow: float = 1.0
    else:
        initial_fuel_flow = (
            p.af2 - p.cf2 * initial_speed_deviation_pu
            - initial_mechanical_power_pu / absolute_speed
        ) / p.bf2
    if not math.isfinite(initial_fuel_flow) or initial_fuel_flow < 0.0:
        raise ValueError('GAST2A requested power implies an invalid steady fuel flow')
    else:
        pass

    # Back-solve the bounded governor demand through the valve and fuel feedback.
    initial_governor_output: float = (
        initial_fuel_flow * p.c / p.a - p.k6 + p.kf * initial_fuel_flow
    ) / (p.k3 * absolute_speed)
    if not p.minimum <= initial_governor_output <= p.maximum:
        raise ValueError('GAST2A shaft power is outside the source governor limits')
    else:
        pass

    # The steady temperature chain must agree with the recorded TC reference.
    initial_f1: float = (
        p.tr - p.af1 * (1.0 - initial_fuel_flow)
        - p.bf1 * initial_speed_deviation_pu
    )
    initial_temperature: float = (p.k4 + p.k5) * initial_f1
    if not math.isclose(initial_temperature, p.tc, rel_tol=0.0, abs_tol=1e-7):
        raise ValueError('GAST2A initial turbine temperature must match TC')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    speed: Var = control.input('SpeedDeviationPu', Const(initial_speed_deviation_pu))
    reference_value: float = (
        initial_speed_deviation_pu
        if p.z == 0 else initial_speed_deviation_pu + initial_governor_output / p.w
    )
    reference: Var = control.input('GovernorReferencePu', Const(reference_value))
    governor_error: Expr = reference - speed
    if p.z == 0:
        governor_integrator: Var = vf.add_var(f'GAST2AGovernorIntegralPu_{name}')
        control.differential(
            governor_integrator, p.w / p.y * governor_error,
            Const(initial_governor_output), Const(p.minimum), Const(p.maximum),
        )
        governor_output: Var = control.algebraic(
            'SpeedGovernorPu',
            sym.hard_sat(
                governor_integrator + Const(p.w * p.x / p.y) * governor_error,
                Const(p.minimum), Const(p.maximum),
            ),
            Const(initial_governor_output),
        )
    else:
        governor_output = control.bounded_lead_lag(
            'SpeedGovernorPu', Const(p.w) * governor_error,
            Const(p.x), Const(p.y), p.x, p.y,
            Const(initial_governor_output), Const(p.minimum), Const(p.maximum),
        )

    # Temperature control is a feedback override, so declare its memory before
    # the fuel chain that it controls.
    thermocouple: Var = vf.add_var(f'GAST2AThermocoupleTemperature_{name}')
    temperature_integrator: Var = vf.add_var(f'GAST2ATemperatureIntegratorPu_{name}')
    temperature_error: Expr = Const(p.tc) - thermocouple
    control.differential(
        temperature_integrator, temperature_error / Const(p.taut),
        Const(initial_governor_output),
    )
    temperature_command: Expr = sym.min(
        temperature_integrator + Const(p.t5 / p.taut) * temperature_error,
        Const(p.maximum),
    )
    selected_control: Var = control.algebraic(
        'SelectedFuelControlPu', sym.min(governor_output, temperature_command),
        Const(initial_governor_output),
    )

    # GAST2A uses two cascaded lag states for each of its documented delay pairs.
    fuel_control_delay_1: Var = control.lag(
        'FuelControlDelay1Pu',
        selected_control * (Const(1.0) + speed), Const(p.t / 2.0), p.t / 2.0,
        Const(initial_governor_output * absolute_speed),
    )
    fuel_control_delay_2: Var = control.lag(
        'FuelControlDelay2Pu', fuel_control_delay_1,
        Const(p.t / 2.0), p.t / 2.0,
        Const(initial_governor_output * absolute_speed),
    )
    valve_input: Expr = Const(p.k3) * fuel_control_delay_2 + Const(p.k6)
    fuel_flow: Var = vf.add_var(f'FuelFlowPu_{name}')
    valve_input = valve_input - Const(p.kf) * fuel_flow
    valve_positioner: Var = vf.add_var(f'GAST2AValvePositionerPu_{name}')
    control.differential(
        valve_positioner,
        (Const(p.a) * valve_input - Const(p.c) * valve_positioner) / Const(p.b),
        Const(initial_fuel_flow),
    )
    control.lag(
        'FuelFlowPu', valve_positioner, Const(p.tauf), p.tauf,
        Const(initial_fuel_flow), output=fuel_flow,
    )

    combustor_delay_1: Var = control.lag(
        'CombustorDelay1Pu', fuel_flow, Const(p.ecr / 2.0), p.ecr / 2.0,
        Const(initial_fuel_flow),
    )
    combustor_delay_2: Var = control.lag(
        'CombustorDelay2Pu', combustor_delay_1,
        Const(p.ecr / 2.0), p.ecr / 2.0,
        Const(initial_fuel_flow),
    )
    turbine_fuel: Var = control.lag(
        'TurbineDynamicsFuelPu', combustor_delay_2,
        Const(p.tcd), p.tcd, Const(initial_fuel_flow),
    )
    turbine_power_function: Expr = (
        Const(p.af2) - Const(p.bf2) * turbine_fuel
        - Const(p.cf2) * speed
    )
    turbine_output: Var = control.algebraic(
        'TurbinePowerFunctionPu', turbine_power_function,
        Const(initial_mechanical_power_pu / absolute_speed),
    )
    mechanical_power: Var = control.algebraic(
        'MechanicalPowerPu', turbine_output * (Const(1.0) + speed),
        Const(initial_mechanical_power_pu),
    )

    exhaust_delay_1: Var = control.lag(
        'TurbineExhaustDelay1Pu', combustor_delay_2,
        Const(p.etd / 2.0), p.etd / 2.0, Const(initial_fuel_flow),
    )
    exhaust_delay_2: Var = control.lag(
        'TurbineExhaustDelay2Pu', exhaust_delay_1,
        Const(p.etd / 2.0), p.etd / 2.0, Const(initial_fuel_flow),
    )
    turbine_temperature: Var = control.algebraic(
        'TurbineTemperature',
        Const(p.tr) - Const(p.af1) * (Const(1.0) - exhaust_delay_2)
        - Const(p.bf1) * speed,
        Const(initial_f1),
    )
    radiation_memory: Var = control.lag(
        'RadiationShieldMemory', turbine_temperature,
        Const(p.t3), p.t3, Const(initial_f1),
    )
    radiation_temperature: Var = control.algebraic(
        'RadiationShieldTemperature',
        Const(p.k4) * turbine_temperature + Const(p.k5) * radiation_memory,
        Const(initial_temperature),
    )
    control.lag(
        'ThermocoupleTemperature', radiation_temperature,
        Const(p.t4), p.t4, Const(initial_temperature), output=thermocouple,
    )
    return control.finish(
        (mechanical_power,),
        'PSS/E GAST2A gas turbine, fuel control and exhaust-temperature limits.',
    )
