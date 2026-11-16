# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native WTPTA1 Type 3 wind pitch controller."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Wtpta1PitchSettings:
    """Store the ten PSS/E pitch-controller CON fields."""

    __slots__ = ('kiw', 'kpw', 'kic', 'kpc', 'kcc', 'tp', 'theta_max', 'theta_min',
                 'rate_max', 'rate_min')

    def __init__(self, kiw: float = .1, kpw: float = 0., kic: float = .1,
                 kpc: float = 0., kcc: float = 0., tp: float = .3,
                 theta_max: float = 30., theta_min: float = 0.,
                 rate_max: float = 5., rate_min: float = -5.) -> None:
        """Store gains, blade time, angle stops and rate stops.

        :param kiw: Speed-error integral gain.
        :param kpw: Speed-error proportional gain.
        :param kic: Power-error integral gain.
        :param kpc: Power-error proportional gain.
        :param kcc: Power-error contribution to speed error.
        :param tp: Blade response time, seconds.
        :param theta_max: Maximum blade angle, degrees.
        :param theta_min: Minimum blade angle, degrees.
        :param rate_max: Maximum blade rate, degrees per second.
        :param rate_min: Minimum blade rate, degrees per second.
        :return: None.
        """
        self.kiw: float = kiw
        self.kpw: float = kpw
        self.kic: float = kic
        self.kpc: float = kpc
        self.kcc: float = kcc
        self.tp: float = tp
        self.theta_max: float = theta_max
        self.theta_min: float = theta_min
        self.rate_max: float = rate_max
        self.rate_min: float = rate_min


def build_wtpta1_pitch_template(
        vf: VarFactory, name: str = 'WTPTA1 pitch',
        settings: Wtpta1PitchSettings | None = None,
        initial_pitch: float = 0.,
) -> RmsModelTemplate:
    """Build the two PI paths and bounded blade response.

    Inputs are turbine speed, speed reference, REECA Pord and plant Pref.
    The initial blade angle comes from the paired WTARA1 record.

    :param vf: Shared symbolic variable factory.
    :param name: Unique controller name.
    :param settings: Ten source parameters.
    :param initial_pitch: WTARA1 equilibrium angle in degrees.
    :return: Stand-alone pitch controller with blade angle output.
    :raises ValueError: Unsupported or inconsistent source parameters.
    """
    selected: Wtpta1PitchSettings = Wtpta1PitchSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.kiw, selected.kpw, selected.kic,
                                 selected.kpc, selected.kcc, selected.tp,
                                 selected.theta_max, selected.theta_min,
                                 selected.rate_max, selected.rate_min, initial_pitch)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('WTPTA1 parameters must be finite')
    elif min(selected.kiw, selected.kpw, selected.kic, selected.kpc, selected.kcc) < 0 or selected.tp <= 0:
        raise ValueError('WTPTA1 gains or blade response time are invalid')
    elif (selected.theta_max <= selected.theta_min
          or not 2. * selected.theta_min <= initial_pitch <= selected.theta_max):
        raise ValueError('WTPTA1 pitch limits cannot hold the initial angle')
    elif selected.rate_min >= 0 or selected.rate_max <= 0:
        raise ValueError('WTPTA1 blade rate limits must straddle zero')
    else:
        pass

    compensation_seed: float = max(0., selected.theta_min)
    speed_seed: float = initial_pitch - compensation_seed
    control: ControlRealization = ControlRealization(vf, name)
    turbine_speed: Var = control.input('TurbineSpeedPu', Const(1.))
    speed_reference: Var = control.input('SpeedReferencePu', turbine_speed)
    pord: Var = control.input('PordPu', Const(0.))
    pref: Var = control.input('PlantPrefPu', pord)
    kiw: Var = control.parameter('KIW', selected.kiw)
    kpw: Var = control.parameter('KPW', selected.kpw)
    kic: Var = control.parameter('KIC', selected.kic)
    kpc: Var = control.parameter('KPC', selected.kpc)
    kcc: Var = control.parameter('KCC', selected.kcc)
    tp: Var = control.parameter('TP', selected.tp)
    theta_max: Var = control.parameter('TETAMAX', selected.theta_max)
    theta_min: Var = control.parameter('TETAMIN', selected.theta_min)
    rate_max: Var = control.parameter('RTETAMAX', selected.rate_max)
    rate_min: Var = control.parameter('RTETAMIN', selected.rate_min)

    power_error: Expr = pord - pref
    speed_error: Expr = turbine_speed - speed_reference + kcc * power_error
    blade: Var = vf.add_var('PitchAngleDeg_' + name)
    speed_memory: Var = vf.add_var('PitchControlIntegral_' + name)
    compensation_memory: Var = vf.add_var('PitchCompIntegral_' + name)
    speed_command: Expr = sym.hard_sat(speed_memory + kpw * speed_error, theta_min, theta_max)
    compensation_command: Expr = sym.hard_sat(compensation_memory + kpc * power_error,
                                               theta_min, theta_max)
    demand: Expr = speed_command + compensation_command
    # The published state order is blade, speed PI, then power PI. Limit
    # each integrator and the blade derivative to prevent stop windup.
    control.differential(blade, sym.hard_sat((demand - blade) / tp, rate_min, rate_max),
                         Const(initial_pitch), theta_min, theta_max)
    control.differential(speed_memory, kiw * speed_error, Const(speed_seed),
                         theta_min, theta_max)
    control.differential(compensation_memory, kic * power_error, Const(compensation_seed),
                         theta_min, theta_max)
    return control.finish((blade,), 'WTPTA1 speed and power pitch controller')
