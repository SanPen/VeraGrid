# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E TGOV3 steam governor with rate limits and fast intercept valving."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Tgov3Parameters:
    """PSS/E TGOV3 constants and its simulation-time fast-valving reference."""

    __slots__ = ('k', 't1', 't2', 't3', 'uo', 'uc', 'pmax', 'pmin', 't4', 'k1',
                 't5', 'k2', 't6', 'k3', 'ta', 'tb', 'tc', 'prmax', 'ti', 'pm0',
                 'deadband_high', 'deadband_low')

    def __init__(self, k: float = 25.0, t1: float = 0.02, t2: float = 0.0,
                 t3: float = 0.1, uo: float = 1.0, uc: float = -10.0,
                 pmax: float = 1.0, pmin: float = 0.0, t4: float = 0.3,
                 k1: float = 0.2, t5: float = 5.0, k2: float = 0.0,
                 t6: float = 0.5, k3: float = 0.8, ta: float = 0.1,
                 tb: float = 0.5, tc: float = 1.0, prmax: float = 1.2,
                 ti: float = 9999.0, pm0: float = 0.8,
                 deadband_high: float = 0.0, deadband_low: float = 0.0) -> None:
        """Store the ordered source constants and the solved initial power.

        :param k: Governor gain, equal to reciprocal droop.
        :param t1: Speed-path denominator time, seconds.
        :param t2: Speed-path numerator time, seconds.
        :param t3: Governor integrator time, seconds.
        :param uo: Maximum governor output rate, pu/s.
        :param uc: Minimum governor output rate, pu/s.
        :param pmax: Maximum governor output, generator-base pu.
        :param pmin: Minimum governor output, generator-base pu.
        :param t4: First turbine lag time, seconds.
        :param k1: Direct mechanical-power fraction.
        :param t5: Reheat integrator time, seconds.
        :param k2: Intercept-valve mechanical-power fraction.
        :param t6: Final turbine lag time, seconds.
        :param k3: Final-lag mechanical-power fraction.
        :param ta: Time to close the intercept valve, seconds.
        :param tb: Time when reopening starts, seconds after TI.
        :param tc: Time when reopening completes, seconds after TI.
        :param prmax: Maximum reheat flow, generator-base pu.
        :param ti: Absolute simulation time when fast valving starts, seconds.
        :param pm0: Solved initial mechanical power, generator-base pu.
        """
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
        self.ti: float = ti
        self.pm0: float = pm0
        self.deadband_high: float = deadband_high
        self.deadband_low: float = deadband_low


def build_tgov3_template(vf: VarFactory, name: str | None = None,
                         parameters: Tgov3Parameters | None = None) -> RmsModelTemplate:
    """Build the six-memory TGOV3 governor, turbine, and valve schedule.

    The speed path is ``K(1+sT2)/(1+sT1)``. Its output and the power reference
    drive a rate-limited governor integrator with PMIN/PMAX stops. T4, T5 and T6
    form the documented turbine/reheat chain; the clipped T5 output is gated by
    the fast-valve flow characteristic before K2/K3 recombination. The TGOV3
    chart gives flow 0.8 at position 0.3 and unity at full opening. The native
    model linearly interpolates the plotted points (0, 0), (0.3, 0.8), and
    (1, 1); this digitized chart approximation is a documented source limit.

    :param vf: Symbol factory owning the native DAE graph.
    :param name: Optional instance name.
    :param parameters: PSS/E constants and power-flow operating point.
    :return: Native TGOV3 governor template with six documented states.
    :raises ValueError: Constants are nonfinite or violate source limits.
    """
    selected: Tgov3Parameters = Tgov3Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        selected.k, selected.t1, selected.t2, selected.t3, selected.uo,
        selected.uc, selected.pmax, selected.pmin, selected.t4, selected.k1,
        selected.t5, selected.k2, selected.t6, selected.k3, selected.ta,
        selected.tb, selected.tc, selected.prmax, selected.ti, selected.pm0,
        selected.deadband_high, selected.deadband_low,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('PSS/E TGOV3 constants must be finite')
    elif selected.k <= 0.0 or selected.t3 <= 0.0 or selected.t5 <= 0.0:
        raise ValueError('PSS/E TGOV3 requires positive gain, T3 and T5')
    elif min(selected.t1, selected.t2, selected.t4, selected.t6) < 0.0:
        raise ValueError('PSS/E TGOV3 lag times cannot be negative')
    elif selected.t1 == 0.0 and selected.t2 != 0.0:
        raise ValueError('PSS/E TGOV3 zero T1 requires zero T2')
    elif selected.uo <= 0.0 or selected.uc >= 0.0 or selected.uc >= selected.uo:
        raise ValueError('PSS/E TGOV3 governor rates must straddle zero')
    elif selected.pmin >= selected.pmax or not selected.pmin <= selected.pm0 <= selected.pmax:
        raise ValueError('PSS/E TGOV3 power limits must contain the initial power')
    elif (selected.prmax <= 0.0 or selected.pm0 > selected.prmax or selected.ta <= 0.0
          or selected.tb < selected.ta or selected.tc <= selected.tb):
        raise ValueError('PSS/E TGOV3 reheat and valve limits are invalid')
    elif selected.k1 + selected.k2 + selected.k3 <= 0.0:
        raise ValueError('PSS/E TGOV3 turbine power fractions must have positive total gain')
    elif selected.pm0 < 0.0 or selected.ti < 0.0:
        raise ValueError('PSS/E TGOV3 initial power and fast-valving time must be nonnegative')
    elif (selected.pm0 / (selected.k1 + selected.k2 + selected.k3) < selected.pmin
          or selected.pm0 / (selected.k1 + selected.k2 + selected.k3) > selected.pmax
          or selected.pm0 / (selected.k1 + selected.k2 + selected.k3) > selected.prmax):
        raise ValueError('PSS/E TGOV3 initial stage power must fit governor and reheat limits')
    else:
        pass

    if selected.deadband_high < 0.0 or selected.deadband_low > 0.0:
        raise ValueError('PSS/E TGOV3 deadband thresholds must have source signs')
    else:
        pass

    template_name: str = 'TGOV3' if name is None else name
    initial_stage_power: float = selected.pm0 / (selected.k1 + selected.k2 + selected.k3)
    control: ControlRealization = ControlRealization(vf, template_name)
    gain: Var = control.parameter('K', selected.k)
    t1: Var = control.parameter('T1', selected.t1)
    t2: Var = control.parameter('T2', selected.t2)
    t3: Var = control.parameter('T3', selected.t3)
    rate_open: Var = control.parameter('UO', selected.uo)
    rate_close: Var = control.parameter('UC', selected.uc)
    pmax: Var = control.parameter('PMAX', selected.pmax)
    pmin: Var = control.parameter('PMIN', selected.pmin)
    t4: Var = control.parameter('T4', selected.t4)
    k1: Var = control.parameter('K1', selected.k1)
    t5: Var = control.parameter('T5', selected.t5)
    k2: Var = control.parameter('K2', selected.k2)
    t6: Var = control.parameter('T6', selected.t6)
    k3: Var = control.parameter('K3', selected.k3)
    ta: Var = control.parameter('TA', selected.ta)
    tb: Var = control.parameter('TB', selected.tb)
    tc: Var = control.parameter('TC', selected.tc)
    prmax: Var = control.parameter('PRMAX', selected.prmax)
    ti: Var = control.parameter('FastValvingStartTimeSec', selected.ti)

    # The source inputs are speed and power reference; both initialize at the
    # solved operating point so all governor and turbine rates start at zero.
    speed: Var = control.input('SpeedDeviationPu', Const(0.0))
    deadband_low: Var = control.parameter('DBL', selected.deadband_low)
    deadband_high: Var = control.parameter('DBH', selected.deadband_high)
    deadband_speed: Var = control.algebraic(
        'ControlledSpeedDeviationPu',
        sym.max(speed - deadband_high, Const(0.0))
        + sym.min(speed - deadband_low, Const(0.0)),
        Const(0.0),
    )
    reference: Var = control.input('ReferencePu', Const(initial_stage_power))
    speed_filter: Var = control.lag(
        'TGOV3SpeedFilterPu', deadband_speed, t1, selected.t1, Const(0.0),
    )
    compensated_speed: Expr = gain * (speed_filter + (t2 / t1) * (deadband_speed - speed_filter)) if selected.t1 > 0.0 else gain * deadband_speed
    governor_output: Var = vf.add_var(f'TGOV3GovernorOutputPu_{template_name}')
    governor_rate: Expr = sym.hard_sat(
        (reference - compensated_speed - governor_output) / t3,
        rate_close,
        rate_open,
    )
    control.differential(governor_output, governor_rate, Const(initial_stage_power), pmin, pmax)

    turbine_t4: Var = control.lag(
        'TGOV3TurbineT4Pu', governor_output, t4, selected.t4, Const(initial_stage_power),
    )
    reheat_integrator: Var = control.lag(
        'TGOV3ReheatIntegratorPu', turbine_t4, t5, selected.t5,
        Const(initial_stage_power),
    )

    # Interpolate the published chart points without importing another model's law.
    valve_position: Var = vf.add_var(f'TGOV3InterceptValvePositionPu_{template_name}')
    reheat_power: Var = control.algebraic(
        'TGOV3ReheatPowerPu', sym.hard_sat(reheat_integrator, Const(0.0), prmax),
        Const(selected.pm0),
    )
    valve_flow: Var = control.algebraic(
        'TGOV3ValveFlowPu',
        Const(8.0 / 3.0) * sym.min(valve_position, Const(0.3))
        + Const(2.0 / 7.0) * sym.max(valve_position - Const(0.3), Const(0.0)),
        Const(1.0),
    )
    turbine_t6: Var = vf.add_var(f'TGOV3TurbineT6Pu_{template_name}')
    flow: Var = control.algebraic(
        'TGOV3FlowPu', valve_flow * reheat_power, Const(selected.pm0),
    )
    turbine_t6 = control.lag(
        'TGOV3TurbineT6Pu', flow, t6, selected.t6, Const(initial_stage_power), output=turbine_t6,
    )
    global_time: Var = vf.add_var(name='glob_time')
    close_window: Expr = sym.heaviside(global_time - ti) - sym.heaviside(global_time - ti - ta)
    reopen_window: Expr = sym.heaviside(global_time - ti - tb) - sym.heaviside(global_time - ti - tc)
    valve_rate: Expr = -close_window / ta + reopen_window / (tc - tb)
    control.differential(valve_position, valve_rate, Const(1.0), Const(0.0), Const(1.0))
    mechanical_power: Var = control.algebraic(
        'gov.PmPu', k1 * turbine_t4 + k2 * flow + k3 * turbine_t6,
        Const(selected.pm0),
    )
    template: RmsModelTemplate = control.finish(
        (mechanical_power,),
        'PSS/E TGOV3 governor, reheat chain, and time-scheduled intercept valve.',
    )
    return template
