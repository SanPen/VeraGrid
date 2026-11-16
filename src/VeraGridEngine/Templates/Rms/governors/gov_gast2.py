# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovGAST2 gas turbine governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import aflipflop, delay
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovGAST2Parameters:
    """CGMES GovGAST2 scalar parameters in their declared units."""

    __slots__ = (
        'mwbase', 'w', 'x', 'y', 'z', 'etd', 'tcd', 'trate', 't', 'tmax', 'tmin',
        'ecr', 'k3', 'a', 'b', 'c', 'tf', 'kf', 'k5', 'k4', 't3', 't4', 'tt',
        't5', 'af1', 'bf1', 'af2', 'bf2', 'cf2', 'tr', 'k6', 'tc',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            w: float = 20.0,
            x: float = 0.2,
            y: float = 0.1,
            z: int = 1,
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
    ) -> None:
        """Store the scalar values consumed by the IEC GAST2 diagram.

        :param mwbase: CGMES governor power base in MW.
        :param w: Speed-governor gain on turbine rating.
        :param x: Speed-governor lead time in seconds.
        :param y: Speed-governor lag time in seconds.
        :param z: Governor mode, one for droop or zero for isochronous.
        :param etd: Turbine-exhaust transport delay in seconds.
        :param tcd: Gas-turbine dynamic lag in seconds.
        :param trate: Turbine rating in MW.
        :param t: Fuel-controller transport delay in seconds.
        :param tmax: Maximum turbine control signal in per unit.
        :param tmin: Minimum turbine control signal in per unit.
        :param ecr: Combustion transport delay in seconds.
        :param k3: Fuel-adjustment ratio.
        :param a: Valve-positioner numerator gain.
        :param b: Valve-positioner time coefficient in seconds.
        :param c: Valve-positioner denominator gain.
        :param tf: Fuel-system lag in seconds.
        :param kf: Fuel-flow feedback gain.
        :param k5: Radiation-shield lag gain.
        :param k4: Direct radiation-shield gain.
        :param t3: Radiation-shield lag time in seconds.
        :param t4: Thermocouple lag time in seconds.
        :param tt: Temperature-controller integration time in seconds.
        :param t5: Temperature-controller lead time in seconds.
        :param af1: Exhaust-temperature fuel-flow coefficient.
        :param bf1: Exhaust-temperature speed coefficient.
        :param af2: Turbine-torque offset coefficient.
        :param bf2: Turbine-torque fuel-flow coefficient.
        :param cf2: Turbine-torque speed coefficient.
        :param tr: Rated turbine temperature.
        :param k6: Minimum fuel flow.
        :param tc: Temperature-control setpoint.
        """
        self.mwbase: float = mwbase
        self.w: float = w
        self.x: float = x
        self.y: float = y
        self.z: int = z
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


def build_gov_g_a_s_t2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovGAST2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the GAST2 controller, transport delays, and turbine equations.

    :param vfactory: Factory owning the runtime symbols.
    :param name: Optional instance name.
    :param parameters: CGMES parameter values used for zero-time reductions.
    :return: Equation-backed template with speed and PRef input ports.
    :raises ValueError: Invalid limits, time constants, or turbine coefficients.
    """
    settings: GovGAST2Parameters = GovGAST2Parameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.w, settings.x, settings.y, float(settings.z), settings.etd,
        settings.tcd, settings.trate, settings.t, settings.tmax, settings.tmin, settings.ecr,
        settings.k3, settings.a, settings.b, settings.c, settings.tf, settings.kf, settings.k5,
        settings.k4, settings.t3, settings.t4, settings.tt, settings.t5, settings.af1,
        settings.bf1, settings.af2, settings.bf2, settings.cf2, settings.tr, settings.k6,
        settings.tc,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovGAST2 parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.trate <= 0.0 or settings.y <= 0.0:
        raise ValueError('GovGAST2 requires positive MWBASE, TRATE, and Y')
    elif min(settings.x, settings.etd, settings.tcd, settings.t, settings.ecr, settings.b,
             settings.tf, settings.t3, settings.t4, settings.tt, settings.t5) < 0.0:
        raise ValueError('GovGAST2 time constants must be nonnegative')
    elif settings.tmax <= settings.tmin or (settings.b == 0.0 and settings.c == 0.0):
        raise ValueError('GovGAST2 limits and valve-positioner coefficients are invalid')
    elif settings.z not in (0, 1):
        raise ValueError('GovGAST2 mode Z must be zero or one')
    else:
        pass

    template_name: str = 'GovGAST2' if name is None else name
    nominal_control: float = 0.5 * (settings.tmax + settings.tmin)
    valve_feedback_gain: float = settings.c + settings.a * settings.kf
    if abs(valve_feedback_gain) > 1e-12:
        valve_position_initial: float = (
            settings.a * (settings.k3 * nominal_control + settings.k6) / valve_feedback_gain
        )
        fuel_demand_initial: float = (
            settings.k3 * nominal_control + settings.k6
            - settings.kf * valve_position_initial
        )
    else:
        raise ValueError('GovGAST2 valve positioner and fuel feedback have a singular equilibrium')
    exhaust_initial: float = settings.tr - settings.af1 * (1.0 - valve_position_initial)
    thermocouple_initial: float = (settings.k4 + settings.k5) * exhaust_initial
    control: ControlRealization = ControlRealization(vfactory, template_name)
    w: Var = control.parameter('GovGAST2.w', settings.w)
    x: Var = control.parameter('GovGAST2.x', settings.x)
    y: Var = control.parameter('GovGAST2.y', settings.y)
    control.parameter('GovGAST2.z', float(settings.z))
    tmax: Var = control.parameter('GovGAST2.tmax', settings.tmax)
    tmin: Var = control.parameter('GovGAST2.tmin', settings.tmin)
    etd: Var = control.parameter('GovGAST2.etd', settings.etd)
    tcd: Var = control.parameter('GovGAST2.tcd', settings.tcd)
    t: Var = control.parameter('GovGAST2.t', settings.t)
    ecr: Var = control.parameter('GovGAST2.ecr', settings.ecr)
    k3: Var = control.parameter('GovGAST2.k3', settings.k3)
    a: Var = control.parameter('GovGAST2.a', settings.a)
    b: Var = control.parameter('GovGAST2.b', settings.b)
    c: Var = control.parameter('GovGAST2.c', settings.c)
    tf: Var = control.parameter('GovGAST2.tf', settings.tf)
    kf: Var = control.parameter('GovGAST2.kf', settings.kf)
    k5: Var = control.parameter('GovGAST2.k5', settings.k5)
    k4: Var = control.parameter('GovGAST2.k4', settings.k4)
    t3: Var = control.parameter('GovGAST2.t3', settings.t3)
    t4: Var = control.parameter('GovGAST2.t4', settings.t4)
    tt: Var = control.parameter('GovGAST2.tt', settings.tt)
    t5: Var = control.parameter('GovGAST2.t5', settings.t5)
    af1: Var = control.parameter('GovGAST2.af1', settings.af1)
    bf1: Var = control.parameter('GovGAST2.bf1', settings.bf1)
    af2: Var = control.parameter('GovGAST2.af2', settings.af2)
    bf2: Var = control.parameter('GovGAST2.bf2', settings.bf2)
    cf2: Var = control.parameter('GovGAST2.cf2', settings.cf2)
    tr: Var = control.parameter('GovGAST2.tr', settings.tr)
    trate: Var = control.parameter('GovGAST2.trate', settings.trate)
    mwbase: Var = control.parameter('GovGAST2.mwbase', settings.mwbase)
    k6: Var = control.parameter('GovGAST2.k6', settings.k6)
    tc: Var = control.parameter('GovGAST2.tc', settings.tc)
    speed: Var = control.input('OmegaPu', Const(1.0))
    reference: Var = control.input('PRefPu', Const(1.0))
    speed_error: Expr = reference - speed

    # Z selects a droop lead-lag or the isochronous integral form of the same block.
    if settings.z == 1:
        speed_governor_state: Var = control.lead_lag(
            'SpeedGovernorMemory', speed_error, x, y / Const(float(settings.z)),
            settings.x, settings.y / float(settings.z), speed_error,
        )
        speed_governor: Expr = (w / Const(float(settings.z))) * speed_governor_state
    else:
        speed_governor_state = control.vf.add_var(name=f'SpeedGovernorPu_{template_name}')
        control.differential(
            speed_governor_state,
            (w / y) * speed_error,
            Const(nominal_control),
            tmin,
            tmax,
        )
        speed_governor = speed_governor_state + (w * x / y) * speed_error
    speed_governor_limited: Expr = sym.hard_sat(speed_governor, tmin, tmax)

    # Fuel flow, exhaust temperature, and low-value selection close the two control loops.
    fuel_flow_state: Var = control.vf.add_var(name=f'FuelFlowPu_{template_name}')
    temperature_state: Var = control.vf.add_var(name=f'ThermocouplePu_{template_name}')
    temperature_signal: Expr = tc - temperature_state
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
                temperature_signal < Const(0.0),
                temperature_signal >= Const(0.0),
                temperature_integral_offset,
                name='TemperatureControlReset',
            )
        )
        control.differential(
            temperature_integral,
            sym.min(temperature_signal, Const(0.0)) / tt,
            Const(0.0),
        )
        temperature_control: Expr = sym.hard_sat(
            speed_governor_limited + temperature_integral - temperature_integral_offset
            + (t5 / tt) * sym.min(temperature_signal, Const(0.0)),
            tmin,
            tmax,
        )
    else:
        temperature_control = tmax
    fuel_control: Expr = sym.min(speed_governor_limited, temperature_control)
    fuel_control_product: Expr = k3 * fuel_control
    if settings.t > 0.0:
        fuel_control_delay: Var = control.vf.add_var(name=f'FuelControlDelayPu_{template_name}')
        control.block.mode_dict[fuel_control_delay] = Const(0.0)
        control.block.init_eqs[fuel_control_delay] = fuel_control_product
        control.block.procedural_logic.append(delay(fuel_control_product, t, fuel_control_delay))
    else:
        fuel_control_delay = control.algebraic(
            'FuelControlDelayPu', fuel_control_product, fuel_control_product
        )
    fuel_demand: Var = control.algebraic(
        'FuelDemandPu',
        fuel_control_delay + k6 - kf * fuel_flow_state,
        Const(fuel_demand_initial),
    )
    valve_input: Expr = fuel_demand

    valve_state: Var = control.vf.add_var(name=f'ValvePositionerPu_{template_name}')
    if settings.b > 0.0:
        control.differential(
            valve_state,
            (a * valve_input - c * valve_state) / b,
            Const(valve_position_initial),
        )
    elif settings.c != 0.0:
        control.block.algebraic_vars.append(valve_state)
        control.block.algebraic_eqs.append(valve_state - a * valve_input / c)
        control.block.init_eqs[valve_state] = Const(valve_position_initial)
    else:
        raise ValueError('GovGAST2 valve positioner cannot have both B and C equal to zero')
    fuel_flow: Var = control.lag(
        'FuelSystemPu', valve_state, tf, settings.tf,
        Const(valve_position_initial),
        output=fuel_flow_state,
    )

    # A zero transport delay is an algebraic connection; positive delay uses sample history.
    if settings.ecr > 0.0:
        fuel_delayed: Var = control.vf.add_var(name=f'FuelCombustorDelayPu_{template_name}')
        control.block.mode_dict[fuel_delayed] = Const(0.0)
        control.block.init_eqs[fuel_delayed] = fuel_flow
        control.block.procedural_logic.append(
            delay(fuel_flow, ecr, fuel_delayed, name='CombustionDelay')
        )
    else:
        fuel_delayed = control.algebraic('FuelCombustorDelayPu', fuel_flow, fuel_flow)
    if settings.etd > 0.0:
        fuel_exhaust_delayed: Var = control.vf.add_var(name=f'FuelExhaustDelayPu_{template_name}')
        control.block.mode_dict[fuel_exhaust_delayed] = Const(0.0)
        control.block.init_eqs[fuel_exhaust_delayed] = fuel_flow
        control.block.procedural_logic.append(
            delay(fuel_flow, etd, fuel_exhaust_delayed, name='TurbineExhaustDelay')
        )
    else:
        fuel_exhaust_delayed = control.algebraic(
            'FuelExhaustDelayPu', fuel_flow, fuel_flow
        )

    # Exhaust-temperature protection uses the delayed fuel path, radiation shield, and thermocouple.
    exhaust_temperature: Expr = tr - af1 * (Const(1.0) - fuel_exhaust_delayed) - bf1 * (
        speed - Const(1.0)
    )
    radiation_state: Var = control.lag(
        'RadiationShieldMemory', exhaust_temperature, t3, settings.t3,
        Const(exhaust_initial),
    )
    radiation_output: Expr = k4 * exhaust_temperature + k5 * radiation_state
    control.lag(
        'ThermocoupleMemory', radiation_output, t4, settings.t4,
        Const(thermocouple_initial),
        output=temperature_state,
    )
    if settings.tcd > 0.0:
        gas_turbine_output: Var = control.lag(
            'GasTurbineDynamics', fuel_delayed, tcd, settings.tcd,
            Const(valve_position_initial),
        )
    else:
        gas_turbine_output = control.algebraic(
            'GasTurbineDynamics', fuel_delayed, Const(valve_position_initial)
        )
    turbine_factor: Expr = af2 + bf2 * gas_turbine_output - cf2 * (speed - Const(1.0))
    mechanical_power: Var = control.algebraic(
        'PmPu', (trate / mwbase)
        * speed * turbine_factor,
        Const(settings.trate / settings.mwbase * (settings.af2 + settings.bf2 * valve_position_initial)),
    )

    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovGAST2 gas-turbine governor, temperature control, and turbine',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    template.comment = 'CGMES GovGAST2 equations with explicit turbine transport delays.'

    # Retain every canonical RDF field beside the runtime equation parameters.
    rdf_parameter_names: tuple[str, ...] = (
        'enabled', 'mwbase', 'w', 'x', 'y', 'z', 'etd', 'tcd', 'trate', 't', 'tmax',
        'tmin', 'ecr', 'k3', 'a', 'b', 'c', 'tf', 'kf', 'k5', 'k4', 't3', 't4',
        'tt', 't5', 'af1', 'bf1', 'af2', 'bf2', 'cf2', 'tr', 'k6', 'tc',
    )
    for parameter_name in rdf_parameter_names:
        parameter_variable: Var = vfactory.add_var(f'GovGAST2.{parameter_name}_{template_name}')
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template
