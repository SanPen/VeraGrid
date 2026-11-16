# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Ontario Hydro delta-omega stabilizer from PSS/E OSTB2T data sheets."""

from __future__ import annotations

import math

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.Utils.procedural_logic import (
    FlipFlopLogic,
    TimedPulseLogic,
    bool_and,
    bool_or,
)


class Ostb2tParameters:
    """PSS/E OSTB2T constants in the order used by the 33.10 and 35.2 sheets."""

    __slots__ = (
        'gain', 'washout_time', 'lead1_ratio', 'lag1_time', 'lead2_ratio',
        'lag2_time', 'upper_speed', 'lower_speed', 'angle_gain', 'angle_time',
        'negative_voltage_max', 'machine_voltage_max', 'switch_on_time',
        'switch_off_time', 'output_max', 'output_min', 'speed_threshold',
        'terminal_voltage_threshold', 'field_voltage_threshold', 'seal_time',
    )

    def __init__(self, gain: float = 1.0, washout_time: float = 10.0,
                 lead1_ratio: float = 1.0, lag1_time: float = 0.1,
                 lead2_ratio: float = 1.0, lag2_time: float = 0.1,
                 upper_speed: float = 0.1, lower_speed: float = -0.1,
                 angle_gain: float = 1.0, angle_time: float = 0.1,
                 negative_voltage_max: float = 0.0, machine_voltage_max: float = 0.0,
                 switch_on_time: float = 0.1, switch_off_time: float = 1.0,
                 output_max: float = 0.1, output_min: float = -0.1,
                 speed_threshold: float = 0.0, terminal_voltage_threshold: float = 0.9,
                 field_voltage_threshold: float = 0.0, seal_time: float = 0.1) -> None:
        """Store the exact source parameter concepts used in the model equations.

        :param gain: K in the delta-omega washout path.
        :param washout_time: Positive washout time TS in seconds.
        :param lead1_ratio: T1/T3, with T3 supplied by ``lag1_time``.
        :param lag1_time: Positive denominator time T3 in seconds.
        :param lead2_ratio: T2/T4, with T4 supplied by ``lag2_time``.
        :param lag2_time: Positive denominator time T4 in seconds.
        :param upper_speed: HLIM for the switched speed path.
        :param lower_speed: LLIM for the switched speed path.
        :param angle_gain: Positive KANG for the terminal-voltage path.
        :param angle_time: Nonnegative TANG in seconds.
        :param negative_voltage_max: VNGMX upper bound on the voltage path.
        :param machine_voltage_max: VMGMX upper bound on the voltage path.
        :param switch_on_time: Minimum closed duration T-ON in seconds.
        :param switch_off_time: Maximum closed duration T-OFF in seconds.
        :param output_max: VSMX maximum supplementary output.
        :param output_min: VSMN minimum supplementary output.
        :param speed_threshold: Delta-omega switching threshold.
        :param terminal_voltage_threshold: ETHR terminal-voltage threshold.
        :param field_voltage_threshold: EFDTHR field-voltage threshold.
        :param seal_time: TSEAL retrigger interval in seconds.
        """
        self.gain: float = gain
        self.washout_time: float = washout_time
        self.lead1_ratio: float = lead1_ratio
        self.lag1_time: float = lag1_time
        self.lead2_ratio: float = lead2_ratio
        self.lag2_time: float = lag2_time
        self.upper_speed: float = upper_speed
        self.lower_speed: float = lower_speed
        self.angle_gain: float = angle_gain
        self.angle_time: float = angle_time
        self.negative_voltage_max: float = negative_voltage_max
        self.machine_voltage_max: float = machine_voltage_max
        self.switch_on_time: float = switch_on_time
        self.switch_off_time: float = switch_off_time
        self.output_max: float = output_max
        self.output_min: float = output_min
        self.speed_threshold: float = speed_threshold
        self.terminal_voltage_threshold: float = terminal_voltage_threshold
        self.field_voltage_threshold: float = field_voltage_threshold
        self.seal_time: float = seal_time


def build_ostb2t_template(vf: VarFactory, name: str | None = None,
                          parameters: Ostb2tParameters | None = None) -> RmsModelTemplate:
    """Build the OSTB2T switched speed stabilizer and voltage path.

    The speed path uses the documented washout and two lead-lag sections.
    Its S1 switching logic follows the source's voltage/speed pickup, TSEAL
    seal, minimum T-ON and maximum T-OFF behavior. The terminal-voltage path
    and both output limiters follow the printed 33.10/35.2 block diagram.

    :param vf: Shared symbolic variable factory.
    :param name: Optional runtime instance name.
    :param parameters: Source settings; defaults are illustrative only.
    :return: A native three-input, one-output OSTB2T template.
    :raises ValueError: Nonfinite or structurally invalid settings.
    """
    settings: Ostb2tParameters = Ostb2tParameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.gain, settings.washout_time, settings.lead1_ratio, settings.lag1_time,
        settings.lead2_ratio, settings.lag2_time, settings.upper_speed, settings.lower_speed,
        settings.angle_gain, settings.angle_time, settings.negative_voltage_max,
        settings.machine_voltage_max, settings.switch_on_time, settings.switch_off_time,
        settings.output_max, settings.output_min, settings.speed_threshold,
        settings.terminal_voltage_threshold, settings.field_voltage_threshold, settings.seal_time,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('OSTB2T parameters must be finite')
    elif min(settings.washout_time, settings.lag1_time, settings.lag2_time,
             settings.angle_gain) <= 0 or settings.angle_time < 0:
        raise ValueError('OSTB2T filter times and KANG are invalid')
    elif min(settings.switch_on_time, settings.switch_off_time, settings.seal_time) < 0:
        raise ValueError('OSTB2T switching durations must be nonnegative')
    elif settings.switch_off_time < settings.switch_on_time:
        raise ValueError('OSTB2T T-OFF must not be shorter than T-ON')
    elif settings.lower_speed > settings.upper_speed:
        raise ValueError('OSTB2T LLIM must not exceed HLIM')
    elif settings.output_min > settings.output_max:
        raise ValueError('OSTB2T VSMN must not exceed VSMX')
    elif min(settings.negative_voltage_max, settings.machine_voltage_max) < 0:
        raise ValueError('OSTB2T voltage path maxima must be nonnegative')
    else:
        pass

    template_name: str = 'OSTB2T' if name is None else name
    builder: ControlRealization = ControlRealization(vf, template_name)
    speed: Var = builder.input('SpeedDeviationPu', Const(0.0))
    terminal_voltage: Var = builder.input('ETerminalPu', Const(1.0))
    field_voltage: Var = builder.input('EfdPu', Const(1.0))
    gain: Var = builder.parameter('K', settings.gain)
    washout_time: Var = builder.parameter('TS', settings.washout_time)
    lead1_ratio: Var = builder.parameter('T1_T3', settings.lead1_ratio)
    lag1_time: Var = builder.parameter('T3', settings.lag1_time)
    lead2_ratio: Var = builder.parameter('T2_T4', settings.lead2_ratio)
    lag2_time: Var = builder.parameter('T4', settings.lag2_time)
    lower_speed: Var = builder.parameter('LLIM', settings.lower_speed)
    upper_speed: Var = builder.parameter('HLIM', settings.upper_speed)
    angle_gain: Var = builder.parameter('KANG', settings.angle_gain)
    angle_time: Var = builder.parameter('TANG', settings.angle_time)
    negative_voltage_max: Var = builder.parameter('VNGMX', settings.negative_voltage_max)
    machine_voltage_max: Var = builder.parameter('VMGMX', settings.machine_voltage_max)
    switch_on_time: Var = builder.parameter('T_ON', settings.switch_on_time)
    switch_off_time: Var = builder.parameter('T_OFF', settings.switch_off_time)
    output_max: Var = builder.parameter('VSMX', settings.output_max)
    output_min: Var = builder.parameter('VSMN', settings.output_min)
    speed_threshold: Var = builder.parameter('DWTHR', settings.speed_threshold)
    voltage_threshold: Var = builder.parameter('ETHR', settings.terminal_voltage_threshold)
    field_threshold: Var = builder.parameter('EFDTHR', settings.field_voltage_threshold)
    seal_time: Var = builder.parameter('TSEAL', settings.seal_time)

    switch_state: Var = builder.parameter('S1', 0.0)
    seal_state: Var = builder.parameter('TSEALActive', 0.0)
    on_timer_state: Var = builder.parameter('TOnActive', 0.0)
    off_timer_state: Var = builder.parameter('TOffActive', 0.0)

    washout: Var = builder.washout(
        'WashedSpeedPu', speed, washout_time, settings.washout_time,
        gain, speed,
    )
    lead1: Var = builder.lead_lag(
        'LeadLag1Pu', washout, lead1_ratio * lag1_time, lag1_time,
        settings.lead1_ratio * settings.lag1_time, settings.lag1_time, Const(0.0),
    )
    lead2: Var = builder.lead_lag(
        'LeadLag2Pu', lead1, lead2_ratio * lag2_time, lag2_time,
        settings.lead2_ratio * settings.lag2_time, settings.lag2_time, Const(0.0),
    )
    bounded_speed: Var = builder.algebraic(
        'BoundedSpeedPu', sym.hard_sat(lead2, lower_speed, upper_speed), Const(0.0),
    )
    angle_path: Var = builder.lag(
        'FilteredTerminalVoltagePu', terminal_voltage, angle_time, settings.angle_time,
        terminal_voltage,
    )
    angle_path_signal: sym.Expr = sym.hard_sat(
        sym.hard_sat(angle_gain * angle_path, Const(0.0), negative_voltage_max),
        Const(0.0), machine_voltage_max,
    )
    angle_signal: Var = builder.algebraic(
        'BoundedAnglePu',
        angle_path_signal,
        sym.hard_sat(angle_path_signal, Const(0.0), machine_voltage_max),
    )

    under_voltage: sym.Comparison = terminal_voltage < voltage_threshold
    speed_high: sym.Comparison = speed > speed_threshold
    voltage_sealed: sym.Comparison = seal_state > Const(0.5)
    switch_open: sym.Comparison = switch_state < Const(0.5)
    close_condition: sym.Expr = bool_and(speed_high, bool_or(under_voltage, voltage_sealed))
    speed_low: sym.Comparison = speed < speed_threshold
    field_low: sym.Comparison = field_voltage < field_threshold
    switch_closed: sym.Comparison = switch_state > Const(0.5)
    minimum_on_finished: sym.Comparison = on_timer_state < Const(0.5)
    maximum_on_finished: sym.Comparison = off_timer_state < Const(0.5)
    normal_open_condition: sym.Expr = bool_and(bool_or(speed_low, field_low), minimum_on_finished)
    reset_condition: sym.Expr = bool_and(
        switch_closed,
        bool_or(normal_open_condition, maximum_on_finished),
    )
    if settings.switch_on_time == 0.0:
        set_signal: sym.Expr = close_condition
    else:
        set_signal = on_timer_state
    set_condition: sym.Expr = bool_and(set_signal, switch_open, off_timer_state > Const(0.5))

    builder.block.procedural_logic.extend((
        TimedPulseLogic(seal_state.name, under_voltage, seal_time, name=template_name + '_TSEAL'),
        TimedPulseLogic(on_timer_state.name, close_condition, switch_on_time,
                        name=template_name + '_T_ON'),
        TimedPulseLogic(off_timer_state.name, close_condition, switch_off_time,
                        name=template_name + '_T_OFF'),
        FlipFlopLogic(switch_state.name, set_condition, reset_condition,
                      name=template_name + '_S1'),
    ))

    output: Var = builder.algebraic(
        'VOTHSG',
        sym.hard_sat(angle_signal + switch_state * bounded_speed, output_min, output_max),
        sym.hard_sat(angle_signal, output_min, output_max),
    )
    return builder.finish((output,), 'Ontario Hydro delta-omega stabilizer with timed S1 switching')
