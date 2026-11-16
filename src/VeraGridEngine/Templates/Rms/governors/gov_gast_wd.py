# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES Woodward gas-turbine governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import aflipflop, delay
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovGASTWDParameters:
    """CGMES GovGASTWD scalar parameters in their declared units."""

    __slots__ = (
        'mwbase', 'kdroop', 'kp', 'ki', 'kd', 'etd', 'tcd', 'trate', 't', 'tmax',
        'tmin', 'ecr', 'k3', 'a', 'b', 'c', 'tf', 'kf', 'k5', 'k4', 't3', 't4',
        'tt', 't5', 'af1', 'bf1', 'af2', 'bf2', 'cf2', 'tr', 'k6', 'tc', 'td',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            kdroop: float = 20.0,
            kp: float = 1.0,
            ki: float = 0.0,
            kd: float = 0.0,
            etd: float = 0.0,
            tcd: float = 0.2,
            trate: float = 100.0,
            t: float = 0.0,
            tmax: float = 1.0,
            tmin: float = 0.0,
            ecr: float = 0.0,
            k3: float = 1.0,
            a: float = 1.0,
            b: float = 0.05,
            c: float = 1.0,
            tf: float = 0.4,
            kf: float = 0.0,
            k5: float = 0.0,
            k4: float = 1.0,
            t3: float = 15.0,
            t4: float = 2.5,
            tt: float = 60.0,
            t5: float = 3.3,
            af1: float = 500.0,
            bf1: float = 500.0,
            af2: float = 0.0,
            bf2: float = 1.0,
            cf2: float = 0.23,
            tr: float = 900.0,
            k6: float = 0.23,
            tc: float = 900.0,
            td: float = 0.0,
    ) -> None:
        """Store the scalar values consumed by the GovGASTWD diagram.

        :param mwbase: Governor power base in MW.
        :param kdroop: Speed-droop gain.
        :param kp: Speed-controller proportional gain.
        :param ki: Speed-controller integral gain.
        :param kd: Speed-controller derivative gain.
        :param etd: Exhaust-temperature fuel transport delay in seconds.
        :param tcd: Turbine power lag in seconds.
        :param trate: Turbine rating in MW.
        :param t: Fuel-control transport delay in seconds.
        :param tmax: Maximum controller output.
        :param tmin: Minimum controller output.
        :param ecr: Combustion fuel transport delay in seconds.
        :param k3: Fuel adjustment gain.
        :param a: Valve positioner numerator coefficient.
        :param b: Valve positioner time coefficient in seconds.
        :param c: Valve positioner denominator coefficient.
        :param tf: Fuel system lag in seconds.
        :param kf: Fuel-flow feedback gain.
        :param k5: Radiation-shield lag gain.
        :param k4: Radiation-shield direct gain.
        :param t3: Radiation-shield lag time in seconds.
        :param t4: Thermocouple lag time in seconds.
        :param tt: Temperature controller integration time in seconds.
        :param t5: Temperature controller lead time in seconds.
        :param af1: Exhaust-temperature fuel coefficient.
        :param bf1: Exhaust-temperature speed coefficient.
        :param af2: Turbine torque offset coefficient.
        :param bf2: Turbine torque fuel coefficient.
        :param cf2: Turbine torque speed coefficient.
        :param tr: Rated turbine temperature.
        :param k6: Minimum fuel flow.
        :param tc: Temperature controller setpoint.
        :param td: Electrical-power transducer lag in seconds.
        """
        self.mwbase: float = mwbase
        self.kdroop: float = kdroop
        self.kp: float = kp
        self.ki: float = ki
        self.kd: float = kd
        self.etd: float = etd
        self.tcd: float = tcd
        self.trate: float = trate
        self.t: float = t
        self.tmax: float = tmax
        self.tmin: float = tmin
        self.ecr: float = ecr
        self.k3: float = k3
        self.a: float = a
        self.b: float = b
        self.c: float = c
        self.tf: float = tf
        self.kf: float = kf
        self.k5: float = k5
        self.k4: float = k4
        self.t3: float = t3
        self.t4: float = t4
        self.tt: float = tt
        self.t5: float = t5
        self.af1: float = af1
        self.bf1: float = bf1
        self.af2: float = af2
        self.bf2: float = bf2
        self.cf2: float = cf2
        self.tr: float = tr
        self.k6: float = k6
        self.tc: float = tc
        self.td: float = td


def build_gov_g_a_s_t_w_d_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovGASTWDParameters | None = None,
) -> RmsModelTemplate:
    """Build the Woodward speed/temperature controller and turbine equations.

    :param vfactory: Factory owning the runtime symbols.
    :param name: Optional instance name.
    :param parameters: CGMES parameters used for algebraic zero-time reductions.
    :return: Equation-backed template with speed, reference, and Pe inputs.
    :raises ValueError: Invalid gains, limits, or time constants.
    """
    settings: GovGASTWDParameters = GovGASTWDParameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.kdroop, settings.kp, settings.ki, settings.kd,
        settings.etd, settings.tcd, settings.trate, settings.t, settings.tmax,
        settings.tmin, settings.ecr, settings.k3, settings.a, settings.b, settings.c,
        settings.tf, settings.kf, settings.k5, settings.k4, settings.t3, settings.t4,
        settings.tt, settings.t5, settings.af1, settings.bf1, settings.af2, settings.bf2,
        settings.cf2, settings.tr, settings.k6, settings.tc, settings.td,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovGASTWD parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.trate <= 0.0:
        raise ValueError('GovGASTWD requires positive MWBASE and TRATE')
    elif min(settings.etd, settings.tcd, settings.t, settings.ecr, settings.b,
             settings.tf, settings.t3, settings.t4, settings.tt, settings.t5,
             settings.td) < 0.0:
        raise ValueError('GovGASTWD time constants must be nonnegative')
    elif settings.tmax <= settings.tmin or (settings.b == 0.0 and settings.c == 0.0):
        raise ValueError('GovGASTWD limits or valve positioner coefficients are invalid')
    elif settings.kp == 0.0 and settings.ki == 0.0:
        raise ValueError('GovGASTWD requires proportional or integral speed control')
    else:
        pass

    template_name: str = 'GovGASTWD' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    speed: Var = control.input('OmegaPu', Const(1.0))
    reference: Var = control.input('PRefPu', Const(0.5))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.5))
    speed_derivative: Var = control.input('OmegaDerivativePu', Const(0.0))
    speed_deviation: Expr = reference - speed
    transducer_power: Expr = electrical_power * control.parameter('mwbase', settings.mwbase) / (
        control.parameter('trate', settings.trate)
    )
    measured_power: Var = control.lag(
        'PowerTransducerPu', transducer_power, control.parameter('td', settings.td),
        settings.td, Const(0.5 * settings.mwbase / settings.trate),
    )
    droop_error: Expr = speed_deviation - control.parameter('kdroop', settings.kdroop) * measured_power

    # The derivative uses the machine-owned speed derivative, keeping the PID ideal.
    controller_integral: Var = control.vf.add_var(name=f'SpeedControllerIntegralPu_{template_name}')
    control.differential(
        controller_integral,
        control.parameter('ki', settings.ki) * droop_error,
        Const(0.0),
    )
    controller_derivative: Expr = -speed_derivative
    speed_control: Expr = control.parameter('kp', settings.kp) * droop_error + controller_integral
    if settings.kd != 0.0:
        speed_control = speed_control + control.parameter('kd', settings.kd) * controller_derivative
    else:
        pass
    speed_limited: Expr = sym.hard_sat(speed_control, control.parameter('tmin', settings.tmin),
                                       control.parameter('tmax', settings.tmax))

    # Temperature feedback limits fuel command; the reset follows the documented WD diagram.
    fuel_flow_state: Var = control.vf.add_var(name=f'FuelFlowPu_{template_name}')
    temperature_state: Var = control.vf.add_var(name=f'ThermocouplePu_{template_name}')
    temperature_error: Expr = control.parameter('tc', settings.tc) - temperature_state
    if settings.tt > 0.0:
        temperature_integral: Var = control.vf.add_var(
            name=f'TemperatureIntegralPu_{template_name}'
        )
        temperature_integral_offset: Var = control.vf.add_var(
            name=f'TemperatureIntegralOffsetPu_{template_name}'
        )
        control.block.mode_dict[temperature_integral_offset] = Const(0.0)
        control.block.init_eqs[temperature_integral_offset] = Const(0.0)
        control.block.procedural_logic.append(
            aflipflop(
                temperature_integral,
                temperature_error < Const(0.0),
                temperature_error >= Const(0.0),
                temperature_integral_offset,
                name='TemperatureControlReset',
            )
        )
        control.differential(
            temperature_integral,
            sym.min(temperature_error, Const(0.0)) / control.parameter('tt', settings.tt),
            Const(0.0),
        )
        temperature_control: Expr = sym.hard_sat(
            speed_limited + temperature_integral - temperature_integral_offset
            + (control.parameter('t5', settings.t5) / control.parameter('tt', settings.tt))
            * sym.min(temperature_error, Const(0.0)),
            control.parameter('tmin', settings.tmin), control.parameter('tmax', settings.tmax),
        )
    else:
        temperature_control = control.parameter('tmax', settings.tmax)
    fuel_control: Expr = sym.min(speed_limited, temperature_control)
    fuel_control_product: Expr = (
        control.parameter('k3', settings.k3) * speed * fuel_control
    )
    if settings.t > 0.0:
        fuel_control_delay: Var = control.vf.add_var(name=f'FuelControlDelayPu_{template_name}')
        control.block.mode_dict[fuel_control_delay] = Const(0.0)
        control.block.init_eqs[fuel_control_delay] = fuel_control_product
        control.block.procedural_logic.append(
            delay(fuel_control_product, control.parameter('t', settings.t), fuel_control_delay)
        )
    else:
        fuel_control_delay = control.algebraic('FuelControlDelayPu', fuel_control_product,
                                               fuel_control_product)
    fuel_demand: Var = control.algebraic(
        'FuelDemandPu', fuel_control_delay + control.parameter('k6', settings.k6)
        - control.parameter('kf', settings.kf) * fuel_flow_state, Const(0.5),
    )
    valve_state: Var = control.vf.add_var(name=f'ValvePositionerPu_{template_name}')
    if settings.b > 0.0:
        control.differential(
            valve_state,
            (control.parameter('a', settings.a) * fuel_demand
             - control.parameter('c', settings.c) * valve_state)
            / control.parameter('b', settings.b),
            Const(0.5),
        )
    elif settings.c != 0.0:
        control.block.algebraic_vars.append(valve_state)
        control.block.algebraic_eqs.append(
            valve_state - settings.a * fuel_demand / settings.c
        )
        control.block.init_eqs[valve_state] = Const(0.5)
    else:
        raise ValueError('GovGASTWD valve positioner cannot have both B and C equal to zero')
    fuel_flow: Var = control.lag(
        'FuelSystemPu', valve_state, control.parameter('tf', settings.tf), settings.tf,
        Const(0.5), output=fuel_flow_state,
    )
    if settings.ecr > 0.0:
        fuel_delayed: Var = control.vf.add_var(name=f'FuelCombustorDelayPu_{template_name}')
        control.block.mode_dict[fuel_delayed] = Const(0.0)
        control.block.init_eqs[fuel_delayed] = fuel_flow
        control.block.procedural_logic.append(
            delay(fuel_flow, control.parameter('ecr', settings.ecr), fuel_delayed,
                  name='CombustionDelay')
        )
    else:
        fuel_delayed = control.algebraic('FuelCombustorDelayPu', fuel_flow, fuel_flow)
    if settings.etd > 0.0:
        exhaust_fuel: Var = control.vf.add_var(name=f'FuelExhaustDelayPu_{template_name}')
        control.block.mode_dict[exhaust_fuel] = Const(0.0)
        control.block.init_eqs[exhaust_fuel] = fuel_flow
        control.block.procedural_logic.append(
            delay(fuel_flow, control.parameter('etd', settings.etd), exhaust_fuel,
                  name='TurbineExhaustDelay')
        )
    else:
        exhaust_fuel = control.algebraic('FuelExhaustDelayPu', fuel_flow, fuel_flow)

    # The EA equations form exhaust temperature, radiation shielding, thermocouple, and torque.
    exhaust_temperature: Expr = control.parameter('tr', settings.tr) - control.parameter(
        'af1', settings.af1
    ) * (Const(1.0) - exhaust_fuel) - control.parameter('bf1', settings.bf1) * (
        speed - Const(1.0)
    )
    radiation: Var = control.lag(
        'RadiationShieldMemory', exhaust_temperature, control.parameter('t3', settings.t3),
        settings.t3, Const(settings.tr - settings.af1),
    )
    radiation_output: Expr = control.parameter('k4', settings.k4) * exhaust_temperature + (
        control.parameter('k5', settings.k5) * radiation
    )
    control.lag(
        'ThermocoupleMemory', radiation_output, control.parameter('t4', settings.t4),
        settings.t4, Const((settings.k4 + settings.k5) * (settings.tr - settings.af1)),
        output=temperature_state,
    )
    turbine_output: Var = control.lag(
        'GasTurbineDynamics', fuel_delayed, control.parameter('tcd', settings.tcd),
        settings.tcd, Const(0.5),
    )
    turbine_factor: Expr = control.parameter('af2', settings.af2) + control.parameter(
        'bf2', settings.bf2
    ) * turbine_output - control.parameter('cf2', settings.cf2) * (speed - Const(1.0))
    mechanical_power: Var = control.algebraic(
        'PmPu', control.parameter('trate', settings.trate)
        / control.parameter('mwbase', settings.mwbase) * speed * turbine_factor,
        Const(settings.trate / settings.mwbase * (settings.af2 + settings.bf2 * 0.5)),
    )
    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovGASTWD Woodward gas-turbine governor and turbine',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    template.comment = 'CGMES GovGASTWD equations with explicit turbine transport delays.'

    # Runtime equation parameters retain the complete canonical RDF parameter surface.
    rdf_parameter_names: tuple[str, ...] = (
        'enabled', 'mwbase', 'kdroop', 'kp', 'ki', 'kd', 'etd', 'tcd', 'trate', 't',
        'tmax', 'tmin', 'ecr', 'k3', 'a', 'b', 'c', 'tf', 'kf', 'k5', 'k4', 't3',
        't4', 'tt', 't5', 'af1', 'bf1', 'af2', 'bf2', 'cf2', 'tr', 'k6', 'tc', 'td',
    )
    for parameter_name in rdf_parameter_names:
        parameter_variable: Var = vfactory.add_var(f'GovGASTWD.{parameter_name}_{template_name}')
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template
