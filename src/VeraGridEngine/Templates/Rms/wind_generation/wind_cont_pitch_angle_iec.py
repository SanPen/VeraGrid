# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEC pitch-angle controller."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_wind_cont_pitch_angle_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dthetamax: float = 0.0,
        dthetamin: float = 0.0,
        kic: float = 0.0,
        kiomega: float = 0.0,
        kpc: float = 0.0,
        kpomega: float = 0.0,
        kpx: float = 0.0,
        thetamax: float = 0.0,
        thetamin: float = 0.0,
        ttheta: float = 0.0,
) -> RmsModelTemplate:
    """Build the IEC 61400-27-1 pitch-angle controller and actuator.

    :param vfactory: Factory allocating the model symbols.
    :param name: Optional unique runtime template name.
    :param dthetamax: Positive pitch-rate limit in degrees per second.
    :param dthetamin: Negative pitch-rate limit in degrees per second.
    :param kic: Power-error PI integral gain.
    :param kiomega: Speed-error PI integral gain.
    :param kpc: Power-error PI proportional gain.
    :param kpomega: Speed-error PI proportional gain.
    :param kpx: Power-error to speed-error cross-coupling gain.
    :param thetamax: Maximum blade pitch angle in degrees.
    :param thetamin: Minimum blade pitch angle in degrees.
    :param ttheta: Pitch actuator time constant in seconds.
    :return: Pitch controller with ordered speed, power, and pitch signals.
    :raises ValueError: Invalid finite limits or a negative actuator time.
    """
    values: tuple[float, ...] = (
        dthetamax, dthetamin, kic, kiomega, kpc, kpomega, kpx,
        thetamax, thetamin, ttheta,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindContPitchAngleIEC values must be finite')
    elif dthetamax < 0.0 or dthetamin > 0.0 or dthetamin > dthetamax:
        raise ValueError('CGMES WindContPitchAngleIEC requires ordered pitch-rate limits')
    elif thetamax < thetamin or ttheta < 0.0:
        raise ValueError('CGMES WindContPitchAngleIEC requires ordered pitch limits and nonnegative ttheta')
    else:
        pass

    template_name: str = 'WindContPitchAngleIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    rate_maximum: Var = model.parameter('WindContPitchAngleIEC.dthetamax', dthetamax)
    rate_minimum: Var = model.parameter('WindContPitchAngleIEC.dthetamin', dthetamin)
    power_integral_gain: Var = model.parameter('WindContPitchAngleIEC.kic', kic)
    speed_integral_gain: Var = model.parameter('WindContPitchAngleIEC.kiomega', kiomega)
    power_proportional_gain: Var = model.parameter('WindContPitchAngleIEC.kpc', kpc)
    speed_proportional_gain: Var = model.parameter('WindContPitchAngleIEC.kpomega', kpomega)
    cross_coupling_gain: Var = model.parameter('WindContPitchAngleIEC.kpx', kpx)
    pitch_maximum: Var = model.parameter('WindContPitchAngleIEC.thetamax', thetamax)
    pitch_minimum: Var = model.parameter('WindContPitchAngleIEC.thetamin', thetamin)
    actuator_time: Var = model.parameter('WindContPitchAngleIEC.ttheta', ttheta)
    turbine_speed: Var = model.input('OmegaWtrPu', Const(1.0))
    speed_reference: Var = model.input('OmegaRefPu', Const(1.0))
    active_power_order: Var = model.input('PordPu', Const(0.0))
    wind_power_reference: Var = model.input('PwtRefPu', Const(0.0))

    # The cross-coupling converts active-power error to an equivalent speed error.
    active_power_error: Expr = wind_power_reference - active_power_order
    speed_error: Expr = (
        turbine_speed - speed_reference + cross_coupling_gain * active_power_error
    )
    initial_pitch: float = min(max(0.0, thetamin), thetamax)

    # Declare controller memories first so the IEC output flags can gate both integrators.
    speed_integral: Var = vfactory.add_var(f'SpeedPitchIntegralDeg_{template_name}')
    power_integral: Var = vfactory.add_var(f'PowerPitchIntegralDeg_{template_name}')
    speed_integral_input: Expr = speed_integral_gain * speed_error
    power_integral_input: Expr = power_integral_gain * active_power_error

    # Both PI paths sum before the IEC first-order pitch actuator.
    proportional_pitch: Expr = (
        speed_proportional_gain * speed_error
        + power_proportional_gain * active_power_error
    )
    demanded_pitch: Expr = proportional_pitch + speed_integral + power_integral
    if ttheta == 0.0:
        pitch_output: Var = model.algebraic(
            'ThetaDeg',
            sym.hard_sat(
                demanded_pitch,
                pitch_minimum,
                pitch_maximum,
            ),
            Const(initial_pitch),
        )
        upper_limit_flag: Expr = Const(1.0) - sym.heaviside(
            pitch_maximum - demanded_pitch,
        )
        lower_limit_flag: Expr = Const(1.0) - sym.heaviside(
            demanded_pitch - pitch_minimum,
        )
    else:
        pitch_output: Var = vfactory.add_var(f'ThetaDeg_{template_name}')
        requested_pitch_rate: Expr = (demanded_pitch - pitch_output) / actuator_time
        upper_rate_flag: Expr = Const(1.0) - sym.heaviside(
            rate_maximum - requested_pitch_rate,
        )
        upper_angle_flag: Expr = Const(1.0) - sym.heaviside(
            pitch_maximum - pitch_output,
        )
        upper_limit_flag = sym.max(upper_rate_flag, upper_angle_flag)
        lower_rate_flag: Expr = Const(1.0) - sym.heaviside(
            requested_pitch_rate - rate_minimum,
        )
        lower_angle_flag: Expr = Const(1.0) - sym.heaviside(
            pitch_output - pitch_minimum,
        )
        lower_limit_flag = sym.max(lower_rate_flag, lower_angle_flag)
        actuator_rate: Expr = sym.hard_sat(
            requested_pitch_rate,
            rate_minimum,
            rate_maximum,
        )
        model.differential(
            pitch_output,
            actuator_rate,
            Const(initial_pitch),
            lower=pitch_minimum,
            upper=pitch_maximum,
        )

    # Annex G.8 blocks only the integrator direction driving an active output limit.
    speed_error_direction: Expr = sym.heaviside(speed_integral_input)
    speed_integral_rate: Expr = speed_integral_input * (
        speed_error_direction * (Const(1.0) - upper_limit_flag)
        + (Const(1.0) - speed_error_direction)
        * (Const(1.0) - lower_limit_flag)
    )
    power_error_direction: Expr = sym.heaviside(power_integral_input)
    power_integral_rate: Expr = power_integral_input * (
        power_error_direction * (Const(1.0) - upper_limit_flag)
        + (Const(1.0) - power_error_direction)
        * (Const(1.0) - lower_limit_flag)
    )
    model.differential(speed_integral, speed_integral_rate, Const(initial_pitch))
    model.differential(power_integral, power_integral_rate, Const(0.0))
    return model.finish(
        (pitch_output,),
        'IEC 61400-27-1:2015 Figure 29 dual PI pitch controller with anti-windup limits and limited first-order actuator.',
    )
