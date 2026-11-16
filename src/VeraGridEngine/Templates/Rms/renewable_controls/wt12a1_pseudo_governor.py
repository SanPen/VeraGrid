# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Type 1/2 wind pseudo governor from the PSS/E WT12A1 block diagram."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Wt12a1Settings:
    """Hold the eight ordered CON values from the PSS/E 35.2 WT12A1 sheet."""

    __slots__ = ('droop', 'kp', 'ti', 't1', 't2', 'tp', 'limmax', 'limmin')

    def __init__(self, droop: float = 0., kp: float = 1., ti: float = 1.,
                 t1: float = .1, t2: float = .1, tp: float = .1,
                 limmax: float = 1.2, limmin: float = 0.) -> None:
        """Store governor gains, time constants and PI output bounds.

        :param droop: Electrical-power error to speed-reference gain.
        :param kp: Speed-error proportional gain.
        :param ti: Integral time constant in seconds; integral gain is 1/Ti.
        :param t1: First mechanical-power output lag in seconds.
        :param t2: Second mechanical-power output lag in seconds.
        :param tp: Electrical-power measurement lag in seconds.
        :param limmax: Maximum PI command in per unit.
        :param limmin: Minimum PI command in per unit.
        :return: None.
        """
        self.droop: float = droop
        self.kp: float = kp
        self.ti: float = ti
        self.t1: float = t1
        self.t2: float = t2
        self.tp: float = tp
        self.limmax: float = limmax
        self.limmin: float = limmin


def build_wt12a1_pseudo_governor_template(
        vf: VarFactory, name: str = 'WT12A1 pseudo governor',
        settings: Wt12a1Settings | None = None,
) -> RmsModelTemplate:
    """Build the four WT12A1 memories and bounded mechanical-power path.

    The open ports are electrical power, blade-side shaft speed, power reference and
    speed reference. A Type 1/2 induction-machine host must connect them.

    :param vf: Shared symbolic variable factory.
    :param name: Unique model name.
    :param settings: Source-ordered PSS/E constants.
    :return: Stand-alone native pseudo-governor template.
    :raises ValueError: Nonfinite data, negative lag, zero Ti or reversed stops.
    """
    selected: Wt12a1Settings = Wt12a1Settings() if settings is None else settings
    values: tuple[float, ...] = (selected.droop, selected.kp, selected.ti,
                                 selected.t1, selected.t2, selected.tp,
                                 selected.limmax, selected.limmin)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('WT12A1 constants must be finite')
    elif selected.ti <= 0 or min(selected.t1, selected.t2, selected.tp) < 0:
        raise ValueError('WT12A1 time constants are invalid')
    elif selected.limmax <= selected.limmin:
        raise ValueError('WT12A1 PI limits are invalid')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.))
    shaft_speed: Var = control.input('ShaftSpeedPu', Const(1.))
    power_reference: Var = control.input('PowerReferencePu', electrical_power)
    speed_reference: Var = control.input('SpeedReferencePu', shaft_speed)
    droop: Var = control.parameter('DROOP', selected.droop)
    kp: Var = control.parameter('KP', selected.kp)
    ti: Var = control.parameter('TI', selected.ti)
    t1: Var = control.parameter('T1', selected.t1)
    t2: Var = control.parameter('T2', selected.t2)
    tp: Var = control.parameter('TP', selected.tp)
    limmax: Var = control.parameter('LIMMAX', selected.limmax)
    limmin: Var = control.parameter('LIMMIN', selected.limmin)

    # Filter electrical feedback before applying droop to the speed error.
    filtered_power: Var = control.lag('FilteredElectricalPowerPu', electrical_power,
                                      tp, selected.tp, electrical_power)
    speed_error: Expr = speed_reference - shaft_speed + droop * (power_reference - filtered_power)
    integral: Var = vf.add_var('PowerIntegral_' + name)
    # Hold the integral only when the complete PI output pushes farther
    # through a source stop; inward motion remains available immediately.
    control.differential(integral, speed_error / ti, electrical_power,
                         limmin - kp * speed_error, limmax - kp * speed_error)
    pi_command: Var = control.algebraic(
        'PowerCommandPu', sym.hard_sat(kp * speed_error + integral, limmin, limmax),
        electrical_power,
    )
    first_output: Var = control.lag('FirstOutputPu', pi_command, t1, selected.t1, electrical_power)
    mechanical_power: Var = control.lag('MechanicalPowerPu', first_output, t2, selected.t2,
                                        electrical_power)
    return control.finish((mechanical_power, filtered_power, pi_command),
                          'Type 1/2 wind pseudo governor mechanical-power request')
