# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the CGMES GovGAST3 governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_gov_g_a_s_t3_template(
        vfactory: VarFactory,
        name: str | None = None,
        bp: float = 0.05,
        tg: float = 0.05,
        rcmx: float = 1.0,
        rcmn: float = -0.1,
        ky: float = 1.0,
        ty: float = 0.2,
        tac: float = 0.1,
        kac: float = 0.0,
        tc: float = 0.2,
        bca: float = 0.01,
        kca: float = 100.0,
        dtc: float = 390.0,
        ka: float = 0.23,
        tsi: float = 15.0,
        ksi: float = 0.8,
        ttc: float = 2.5,
        tfen: float = 540.0,
        td: float = 3.3,
        tt: float = 250.0,
        mxef: float = 0.05,
        mnef: float = -0.05,
) -> RmsModelTemplate:
    """Build the Gov33TGT acceleration and exhaust-temperature controller.

    :param vfactory: Factory that allocates equation variables.
    :param name: Optional unique runtime model name.
    :param bp: Governor permanent droop.
    :param tg: Speed-governor integrator time constant.
    :param rcmx: Maximum fuel-flow command.
    :param rcmn: Minimum fuel-flow command.
    :param ky: Fuel-valve positioner coefficient.
    :param ty: Fuel-valve positioner time constant.
    :param tac: Fuel-control time constant.
    :param kac: Fuel-system feedback gain.
    :param tc: Compressor-discharge volume time constant.
    :param bca: Acceleration-control set point.
    :param kca: Acceleration-control integrator gain.
    :param dtc: Exhaust-temperature change over the unit fuel-flow range.
    :param ka: Minimum fuel flow used in the exhaust-temperature factor.
    :param tsi: Radiation-shield time constant.
    :param ksi: Radiation-shield direct gain.
    :param ttc: Thermocouple time constant.
    :param tfen: Rated exhaust temperature at unit mechanical power.
    :param td: Temperature-controller derivative time.
    :param tt: Temperature-controller integration time.
    :param mxef: Upper speed-error limit.
    :param mnef: Lower speed-error limit.
    :return: Equation-backed governor with speed, acceleration, and reference ports.
    :raises ValueError: Invalid droop, time constants, gains, or limiter bounds.
    """
    values: tuple[float, ...] = (
        bp, tg, rcmx, rcmn, ky, ty, tac, kac, tc, bca, kca, dtc, ka,
        tsi, ksi, ttc, tfen, td, tt, mxef, mnef,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('GovGAST3 parameters must be finite')
    elif bp <= 0.0 or tg <= 0.0 or ky <= 0.0 or tt <= 0.0 or tfen <= 0.0:
        raise ValueError('GovGAST3 bp, tg, ky, tt, and tfen must be positive')
    elif min(ty, tac, tc, tsi, ttc, td, kac, kca, ka, dtc) < 0.0:
        raise ValueError('GovGAST3 times and nonnegative parameters must not be negative')
    elif rcmn >= rcmx or mnef >= mxef or not 0.0 <= ksi <= 1.0 or not 0.0 <= ka <= 1.0:
        raise ValueError('GovGAST3 limiter bounds or thermal fractions are invalid')
    else:
        pass

    template_name: str = 'GovGAST3' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    speed: Var = model.input('OmegaPu', Const(1.0))
    speed_derivative: Var = model.input('OmegaDerivativePu', Const(0.0))
    power_reference: Var = model.input('PRefPu', Const(0.5))

    # The speed governor integrates reference plus limited droop error, with
    # its own state fed back to form the 1/(s*Tg) block shown in EA968.
    speed_error: Expr = (Const(1.0) - speed) / model.parameter('GovGAST3.bp', bp)
    frequency_correction: Expr = sym.hard_sat(
        speed_error,
        model.parameter('GovGAST3.mnef', mnef),
        model.parameter('GovGAST3.mxef', mxef),
    )
    governor_state: Var = model.vf.add_var(f'GovernorIntegratorPu_{template_name}')
    governor_derivative: Expr = (
        power_reference + frequency_correction - governor_state
    ) / model.parameter('GovGAST3.tg', tg)
    model.differential(governor_state, governor_derivative, power_reference)

    # The acceleration integrator can only reduce fuel flow; stop its state
    # from integrating farther below zero while preserving recovery motion.
    acceleration_state: Var = model.vf.add_var(f'AccelerationFuelReductionPu_{template_name}')
    acceleration_error: Expr = (
        speed_derivative - model.parameter('GovGAST3.bca', bca)
    )
    acceleration_rate: Expr = model.parameter('GovGAST3.kca', kca) * acceleration_error
    acceleration_state_is_positive: Expr = sym.heaviside(acceleration_state)
    acceleration_rate = (
        acceleration_state_is_positive * acceleration_rate
        + (Const(1.0) - acceleration_state_is_positive)
        * sym.max(acceleration_rate, Const(0.0))
    )
    model.differential(acceleration_state, acceleration_rate, Const(0.0))

    # F1 is the documented exhaust-temperature gain; Qc is predeclared so its
    # temperature and fuel-system feedback paths form one closed dynamic loop.
    thermal_fraction: Expr = (
        model.parameter('GovGAST3.dtc', dtc)
        * (Const(1.0) - model.parameter('GovGAST3.ka', ka))
        / model.parameter('GovGAST3.tfen', tfen)
    )
    exhaust_gain: Expr = (Const(1.0) - thermal_fraction) * thermal_fraction
    fuel_control_state: Var = model.vf.add_var(f'FuelControlPu_{template_name}')
    fuel_control_parameter: Var = model.parameter('GovGAST3.tac', tac)
    radiation_time: Var = model.parameter('GovGAST3.tsi', tsi)
    thermocouple_time: Var = model.parameter('GovGAST3.ttc', ttc)
    positioner_time: Var = model.parameter('GovGAST3.ty', ty)
    fuel_control: Var = fuel_control_state

    exhaust_source: Expr = exhaust_gain * fuel_control
    if tsi > 0.0:
        radiation_memory: Var = model.lag(
            'RadiationShieldMemoryPu', exhaust_source,
            radiation_time, tsi, exhaust_source,
        )
        radiation_output: Expr = (
            model.parameter('GovGAST3.ksi', ksi) * exhaust_source
            + (Const(1.0) - model.parameter('GovGAST3.ksi', ksi)) * radiation_memory
        )
    else:
        radiation_output = exhaust_source
    thermocouple: Var = model.lag(
        'ExhaustTemperaturePu', radiation_output,
        thermocouple_time, ttc,
        exhaust_gain * Const(0.5),
    )
    temperature_error: Expr = thermocouple - Const(1.0)

    # The (1+s*Td)/(s*Tt) temperature controller has an integral state and a
    # derivative feed-forward; the EA diagram applies a zero lower stop.
    temperature_integrator: Var = model.vf.add_var(
        f'TemperatureControllerIntegralPu_{template_name}'
    )
    temperature_time: Var = model.parameter('GovGAST3.tt', tt)
    temperature_rate: Expr = temperature_error / temperature_time
    temperature_integrator_is_positive: Expr = sym.heaviside(temperature_integrator)
    temperature_rate = (
        temperature_integrator_is_positive * temperature_rate
        + (Const(1.0) - temperature_integrator_is_positive)
        * sym.max(temperature_rate, Const(0.0))
    )
    model.differential(temperature_integrator, temperature_rate, Const(0.0))
    temperature_controller: Expr = sym.max(
        temperature_integrator
        + model.parameter('GovGAST3.td', td) / temperature_time * temperature_error,
        Const(0.0),
    )

    # The central summer combines speed, temperature, and acceleration controls
    # before the physical fuel-flow limits and fuel-system feedback are applied.
    fuel_command: Expr = sym.hard_sat(
        governor_state + temperature_controller - acceleration_state,
        model.parameter('GovGAST3.rcmn', rcmn),
        model.parameter('GovGAST3.rcmx', rcmx),
    )
    positioner_input: Expr = fuel_command - model.parameter('GovGAST3.kac', kac) * fuel_control
    positioner_state: Var = model.vf.add_var(f'FuelValvePositionPu_{template_name}')
    if ty > 0.0:
        positioner_output: Var = model.differential(
            positioner_state,
            (positioner_input - model.parameter('GovGAST3.ky', ky) * positioner_state)
            / positioner_time,
            Const(0.5),
        )
    else:
        positioner_output = model.algebraic(
            'FuelValvePositionPu',
            positioner_input / model.parameter('GovGAST3.ky', ky),
            Const(0.5),
        )
    if tac > 0.0:
        model.differential(
            fuel_control_state,
            (positioner_output - fuel_control_state) / fuel_control_parameter,
            Const(0.5),
        )
    else:
        model.block.algebraic_vars.append(fuel_control_state)
        model.block.algebraic_eqs.append(fuel_control_state - positioner_output)
        model.block.init_eqs[fuel_control_state] = Const(0.5)

    # Compressor discharge volume is the final first-order turbine fuel-flow stage.
    turbine_flow: Var = model.lag(
        'TurbineFuelFlowPu', fuel_control,
        model.parameter('GovGAST3.tc', tc), tc, Const(0.5),
    )
    mechanical_power: Var = model.algebraic('PmPu', turbine_flow, Const(0.5))
    template: RmsModelTemplate = model.finish(
        (mechanical_power,),
        'CGMES GovGAST3 acceleration and exhaust-temperature limited gas turbine governor',
    )
    template.comment = (
        'GovGAST3 follows the CGMES EA968/EA980 and NEPLAN Gov33TGT diagram. '
        'F1 is the documented gain (1-Kt)*Kt, with Kt=dtc*(1-ka)/tfen.'
    )
    enabled_variable: Var = vfactory.add_var(f'GovGAST3.enabled_{template_name}')
    template.block.event_dict[enabled_variable] = vfactory.add_const(value=None)
    return template
