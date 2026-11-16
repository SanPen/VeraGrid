# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Native PSS/E TGOV2 steam turbine governor with fast valving."""

from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.procedural_logic import startup_handover


class TGOV2Parameters:
    """Construction parameters matching PSS/E 35.2 section 7.42."""

    __slots__ = ('r', 't1', 'vmax', 'vmin', 'k', 't3', 'dt', 'tt', 'ta', 'tb', 'tc', 'pm0')

    def __init__(self, r: float = 0.05, t1: float = 0.1, vmax: float = 1.0,
                 vmin: float = 0.0, k: float = 0.3, t3: float = 0.1,
                 dt: float = 0.0, tt: float = 0.5, ta: float = 0.1,
                 tb: float = 0.5, tc: float = 1.0, pm0: float = 0.8) -> None:
        """Store the ordered PSS/E constants and operating-point seed.

        :param r: Governor droop in pu.
        :param t1: Governor lag in seconds.
        :param vmax: Maximum throttle in pu.
        :param vmin: Minimum throttle in pu.
        :param k: Direct turbine power fraction.
        :param t3: Reheat-pressure lag in seconds.
        :param dt: Damping coefficient in pu.
        :param tt: Reheat-power lag in seconds.
        :param ta: Intercept-valve closing duration in seconds.
        :param tb: Seconds until reopening starts.
        :param tc: Seconds until reopening completes.
        :param pm0: Initial mechanical power used to seed the turbine states.
        """
        self.r: float = r
        self.t1: float = t1
        self.vmax: float = vmax
        self.vmin: float = vmin
        self.k: float = k
        self.t3: float = t3
        self.dt: float = dt
        self.tt: float = tt
        self.ta: float = ta
        self.tb: float = tb
        self.tc: float = tc
        self.pm0: float = pm0


def build_tgov2_template(vf: VarFactory, name: str | None = None,
                         parameters: TGOV2Parameters | None = None) -> RmsModelTemplate:
    """Build the four-state steam governor and its TI-relative valve schedule.

    :param vf: Symbol factory owning the RMS equations.
    :param name: Optional unique model instance name.
    :param parameters: PSS/E constants and initial mechanical-power seed.
    :return: Native TGOV2 RMS template.
    :raises ValueError: Parameters violate the documented model domains.
    """
    settings: TGOV2Parameters = TGOV2Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.r, settings.t1, settings.vmax, settings.vmin, settings.k,
        settings.t3, settings.dt, settings.tt, settings.ta, settings.tb,
        settings.tc, settings.pm0,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('PSS/E TGOV2 parameters must be finite')
    elif settings.r <= 0.0 or min(settings.t1, settings.t3, settings.tt) <= 0.0:
        raise ValueError('PSS/E TGOV2 requires positive droop and lag times')
    elif settings.vmin >= settings.vmax or not 0.0 <= settings.k <= 1.0:
        raise ValueError('PSS/E TGOV2 requires ordered valve limits and 0 <= K <= 1')
    elif not settings.vmin <= settings.pm0 <= settings.vmax:
        raise ValueError('PSS/E TGOV2 initial power must lie within throttle limits')
    elif not 0.0 < settings.ta < settings.tb < settings.tc:
        raise ValueError('PSS/E TGOV2 requires 0 < TA < TB < TC')
    else:
        pass

    template_name: str = 'TGOV2' if name is None else name
    control: ControlRealization = ControlRealization(vf, template_name)
    droop: Var = control.parameter('R', settings.r)
    governor_time: Var = control.parameter('T1', settings.t1)
    throttle_max: Var = control.parameter('VMAX', settings.vmax)
    throttle_min: Var = control.parameter('VMIN', settings.vmin)
    direct_fraction: Var = control.parameter('K', settings.k)
    pressure_time: Var = control.parameter('T3', settings.t3)
    damping: Var = control.parameter('DT', settings.dt)
    reheat_time: Var = control.parameter('TT', settings.tt)
    close_time: Var = control.parameter('TA', settings.ta)
    reopen_time: Var = control.parameter('TB', settings.tb)
    full_open_time: Var = control.parameter('TC', settings.tc)
    speed_reference: Var = control.input(
        'SpeedReferencePu', Const(settings.r * settings.pm0),
    )
    speed_deviation: Var = control.input('SpeedDeviationPu', Const(0.0))
    fast_valving_start: Var = control.parameter('FastValvingStartTimeSec', 0.0)
    throttle_demand: Expr = (speed_reference - speed_deviation) / droop
    throttle: Var = control.lag(
        'TGOV2ThrottlePu', throttle_demand, governor_time, settings.t1,
        Const(settings.pm0), throttle_min, throttle_max,
    )
    reheat_pressure: Var = control.lag(
        'TGOV2ReheatPressurePu', (Const(1.0) - direct_fraction) * throttle,
        pressure_time, settings.t3, Const((1.0 - settings.k) * settings.pm0),
    )
    close_started: Var = vf.add_var(f'TGOV2CloseStarted_{template_name}')
    close_finished: Var = vf.add_var(f'TGOV2CloseFinished_{template_name}')
    reopen_started: Var = vf.add_var(f'TGOV2ReopenStarted_{template_name}')
    reopen_finished: Var = vf.add_var(f'TGOV2ReopenFinished_{template_name}')
    close_start_time: Var = vf.add_var(f'TGOV2CloseStartTimeSec_{template_name}')
    close_end_time: Var = vf.add_var(f'TGOV2CloseEndTimeSec_{template_name}')
    reopen_start_time: Var = vf.add_var(f'TGOV2ReopenStartTimeSec_{template_name}')
    reopen_end_time: Var = vf.add_var(f'TGOV2ReopenEndTimeSec_{template_name}')
    control.block.event_dict[close_start_time] = fast_valving_start
    control.block.event_dict[close_end_time] = fast_valving_start + close_time
    control.block.event_dict[reopen_start_time] = fast_valving_start + reopen_time
    control.block.event_dict[reopen_end_time] = fast_valving_start + full_open_time
    for timer_output in (close_started, close_finished, reopen_started, reopen_finished):
        control.block.mode_dict[timer_output] = vf.add_const(0.0)
        control.block.init_eqs[timer_output] = vf.add_const(0.0)
    control.block.procedural_logic.append(startup_handover(close_started, close_start_time))
    control.block.procedural_logic.append(startup_handover(close_finished, close_end_time))
    control.block.procedural_logic.append(startup_handover(reopen_started, reopen_start_time))
    control.block.procedural_logic.append(startup_handover(reopen_finished, reopen_end_time))
    close_window: Expr = close_started - close_finished
    reopen_window: Expr = reopen_started - reopen_finished
    intercept_velocity: Expr = (
        -close_window / close_time
        + reopen_window / (full_open_time - reopen_time)
    )
    intercept_valve: Var = vf.add_var(f'TGOV2InterceptValvePu_{template_name}')
    reheat_power: Var = control.lag(
        'TGOV2ReheatPowerPu', reheat_pressure * intercept_valve,
        reheat_time, settings.tt, Const((1.0 - settings.k) * settings.pm0),
    )
    control.differential(
        intercept_valve, intercept_velocity, Const(1.0), Const(0.0), Const(1.0),
    )
    mechanical_power: Var = control.algebraic(
        'gov.PmPu', direct_fraction * throttle + reheat_power - damping * speed_deviation,
        Const(settings.pm0),
    )
    template: RmsModelTemplate = control.finish(
        (mechanical_power,),
        'PSS/E TGOV2: droop governor, reheat stages, damping, and TI-relative fast valving.',
    )
    return template
