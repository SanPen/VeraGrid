# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for canonical CGMES PssIEEE4B."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class PssIEEE4BParameters:
    """Hold PssIEEE4B values grouped by frequency band and function."""

    __slots__ = ('notches', 'low', 'intermediate', 'high', 'band_limits', 'output_limits')

    def __init__(
            self,
            notches: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            low: tuple[float, ...] = (7.5, 66.0, 66.0, 1.0, 1.0, 1.73, 2.075, 0.0, 0.0, 0.0, 0.0, 2.075, 2.491, 0.0, 0.0, 0.0, 0.0),
            intermediate: tuple[float, ...] = (30.0, 66.0, 66.0, 1.0, 1.0, 0.173, 0.2075, 0.0, 0.0, 0.0, 0.0, 0.2075, 0.2491, 0.0, 0.0, 0.0, 0.0),
            high: tuple[float, ...] = (120.0, 66.0, 66.0, 1.0, 1.0, 0.01513, 0.01816, 0.0, 0.0, 0.0, 0.0, 0.01816, 0.02179, 0.0, 0.0, 0.0, 0.0),
            band_limits: tuple[float, ...] = (-0.075, 0.075, -0.6, 0.6, -0.6, 0.6),
            output_limits: tuple[float, float] = (-0.15, 0.15),
    ) -> None:
        """Store notch, band, and output parameters.

        :param notches: Low/high notch (bandwidth, bandwidth, frequency, frequency).
        :param low: Low band gain, branch gains, proportional terms, and 12 times.
        :param intermediate: Intermediate band values in the same order as ``low``.
        :param high: High band values in the same order as ``low``.
        :param band_limits: Low, intermediate, and high lower/upper limits.
        :param output_limits: Final lower/upper output limits.
        """
        self.notches: tuple[float, ...] = notches
        self.low: tuple[float, ...] = low
        self.intermediate: tuple[float, ...] = intermediate
        self.high: tuple[float, ...] = high
        self.band_limits: tuple[float, ...] = band_limits
        self.output_limits: tuple[float, float] = output_limits


def _pss4b_notch(
        builder: ControlRealization,
        signal: Expr,
        bandwidth: float,
        frequency: float,
        suffix: str,
) -> Expr:
    """Realize a second-order notch without adding states for the identity case.

    :param builder: Owner of generated states and algebraic variables.
    :param signal: Signal entering the notch.
    :param bandwidth: Three-decibel bandwidth in radians per second.
    :param frequency: Notch centre frequency in radians per second.
    :param suffix: Unique band/filter label.
    :return: Notched signal or the original signal when the filter is disabled.
    """
    if bandwidth > 0.0 and frequency > 0.0:
        first_state: Var = builder.vf.add_var(f'Notch{suffix}Position_{builder.name}')
        second_state: Var = builder.vf.add_var(f'Notch{suffix}Rate_{builder.name}')
        square_frequency: float = frequency * frequency
        builder.differential(first_state, second_state, signal / square_frequency)
        builder.differential(
            second_state,
            signal - bandwidth * second_state - square_frequency * first_state,
            Const(0.0),
        )
        return builder.algebraic(
            f'Notch{suffix}OutputPu', signal - bandwidth * second_state, signal,
        )
    else:
        return signal


def _pss4b_branch(
        builder: ControlRealization,
        signal: Expr,
        gain: float,
        proportional: float,
        times: tuple[float, ...],
        suffix: str,
) -> Expr:
    """Realize one gain and three lead/lag stages of a PSS4B band.

    :param builder: Owner of controller equations.
    :param signal: Band input.
    :param gain: Positive or negative branch gain.
    :param proportional: Constant term in the first-stage numerator.
    :param times: Six numerator/denominator time-constant pairs.
    :param suffix: Unique branch label.
    :return: Filtered and gain-scaled branch output.
    """
    derivative_time: float = times[0]
    first_lag_time: float = times[1]
    if first_lag_time > 0.0:
        lag_state: Var = builder.vf.add_var(f'{suffix}FirstState_{builder.name}')
        builder.differential(
            lag_state,
            (signal - lag_state) / first_lag_time,
            signal,
        )
        first_output: Expr = (
            proportional * lag_state
            + derivative_time / first_lag_time * (signal - lag_state)
        )
    else:
        if derivative_time == 0.0:
            first_output = proportional * signal
        else:
            raise ValueError('CGMES PssIEEE4B first branch has an improper zero-lag derivative')
    second_output: Var = builder.lead_lag(
        f'{suffix}SecondPu', first_output, Const(times[2]), Const(times[3]),
        times[2], times[3], first_output,
    )
    third_output: Var = builder.lead_lag(
        f'{suffix}ThirdPu', second_output, Const(times[4]), Const(times[5]),
        times[4], times[5], second_output,
    )
    return gain * third_output


def _pss4b_band(
        builder: ControlRealization,
        signal: Expr,
        values: tuple[float, ...],
        lower_value: float,
        upper_value: float,
        suffix: str,
) -> Var:
    """Build the two differential branches, common gain, and band limiter.

    :param builder: Owner of generated equations.
    :param signal: Band-filtered speed deviation.
    :param values: Band gain, branch gains, proportional gains, and 12 times.
    :param lower_value: Band output lower limit.
    :param upper_value: Band output upper limit.
    :param suffix: Low, intermediate, or high band name.
    :return: Limited band output.
    """
    positive: Expr = _pss4b_branch(
        builder, signal, values[1], values[3], values[5:11], suffix + 'Positive',
    )
    negative: Expr = _pss4b_branch(
        builder, signal, values[2], values[4], values[11:17], suffix + 'Negative',
    )
    band_gain: Var = builder.parameter(suffix + 'Gain', values[0])
    lower: Var = builder.parameter(suffix + 'Minimum', lower_value)
    upper: Var = builder.parameter(suffix + 'Maximum', upper_value)
    band_expression: Expr = sym.hard_sat(band_gain * (positive - negative), lower, upper)
    return builder.algebraic(suffix + 'OutputPu', band_expression, Const(0.0))


def build_pss_i_e_e_e4_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssIEEE4BParameters | None = None,
) -> RmsModelTemplate:
    """Build three-band PssIEEE4B equations using the canonical RDF parameters.

    :param vfactory: Factory allocating equation and event symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Optional canonical values grouped by frequency band.
    :return: Standalone PSS template with one open rotor-speed input.
    :raises ValueError: Nonfinite values, invalid times, or unordered limits.
    """
    settings: PssIEEE4BParameters = PssIEEE4BParameters() if parameters is None else parameters
    all_values: tuple[float, ...] = (
        *settings.notches, *settings.low, *settings.intermediate, *settings.high,
        *settings.band_limits, *settings.output_limits,
    )
    if len(settings.notches) != 8 or len(settings.low) != 17 or len(settings.intermediate) != 17 or len(settings.high) != 17 or len(settings.band_limits) != 6:
        raise ValueError('CGMES PssIEEE4B parameter group has an invalid size')
    elif not all(math.isfinite(value) for value in all_values):
        raise ValueError('CGMES PssIEEE4B parameters must be finite')
    elif min((*settings.low[5:], *settings.intermediate[5:], *settings.high[5:])) < 0.0:
        raise ValueError('CGMES PssIEEE4B times must be nonnegative')
    elif any(settings.band_limits[index] >= settings.band_limits[index + 1] for index in (0, 2, 4)) or settings.output_limits[0] >= settings.output_limits[1]:
        raise ValueError('CGMES PssIEEE4B limits must be ordered')
    else:
        pass

    template_name: str = 'PssIEEE4B' if name is None else name
    builder: ControlRealization = ControlRealization(vfactory, template_name)
    speed_deviation: Var = builder.input('SpeedDeviationPu', Const(0.0))
    # The RDF defines one rotor-speed deviation input shared by all frequency bands.
    low_signal: Expr = _pss4b_notch(
        builder, speed_deviation, settings.notches[0], settings.notches[2], 'Low1',
    )
    low_signal = _pss4b_notch(
        builder, low_signal, settings.notches[1], settings.notches[3], 'Low2',
    )
    high_signal: Expr = _pss4b_notch(
        builder, speed_deviation, settings.notches[4], settings.notches[6], 'High1',
    )
    high_signal = _pss4b_notch(
        builder, high_signal, settings.notches[5], settings.notches[7], 'High2',
    )
    low_output: Var = _pss4b_band(
        builder, low_signal, settings.low, settings.band_limits[0], settings.band_limits[1], 'Low',
    )
    intermediate_output: Var = _pss4b_band(
        builder, low_signal, settings.intermediate,
        settings.band_limits[2], settings.band_limits[3], 'Intermediate',
    )
    high_output: Var = _pss4b_band(
        builder, high_signal, settings.high, settings.band_limits[4], settings.band_limits[5], 'High',
    )
    output_lower: Var = builder.parameter('VSTMIN', settings.output_limits[0])
    output_upper: Var = builder.parameter('VSTMAX', settings.output_limits[1])
    output_expression: Expr = sym.hard_sat(
        low_output + intermediate_output + high_output, output_lower, output_upper,
    )
    output: Var = builder.algebraic('VsPu', output_expression, Const(0.0))
    runtime_template: RmsModelTemplate = builder.finish(
        (output,), 'IEEE three-band stabilizer with positive/negative branch compensation',
    )

    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime_template.block)
    template.block.name = template_name
    template.comment = 'CGMES PssIEEE4B: low, intermediate, and high band differential branches with notch and output limits.'
    enabled_variable: Var = vfactory.add_var(f'PssIEEE4B.enabled_{template_name}')
    template.block.event_dict[enabled_variable] = vfactory.add_const(
        value=None, name=f'PssIEEE4B.enabled_{template_name}',
    )
    parameter_values: tuple[tuple[str, float], ...] = (
        ('bwh1', settings.notches[4]), ('bwh2', settings.notches[5]),
        ('bwl1', settings.notches[0]), ('bwl2', settings.notches[1]),
        ('kh', settings.high[0]), ('kh1', settings.high[1]), ('kh11', settings.high[3]),
        ('kh17', settings.high[4]), ('kh2', settings.high[2]),
        ('ki', settings.intermediate[0]), ('ki1', settings.intermediate[1]),
        ('ki11', settings.intermediate[3]), ('ki17', settings.intermediate[4]),
        ('ki2', settings.intermediate[2]), ('kl', settings.low[0]),
        ('kl1', settings.low[1]), ('kl11', settings.low[3]), ('kl17', settings.low[4]),
        ('kl2', settings.low[2]), ('omeganh1', settings.notches[6]),
        ('omeganh2', settings.notches[7]), ('omeganl1', settings.notches[2]),
        ('omeganl2', settings.notches[3]),
        ('th1', settings.high[5]), ('th2', settings.high[6]), ('th3', settings.high[7]),
        ('th4', settings.high[8]), ('th5', settings.high[9]), ('th6', settings.high[10]),
        ('th7', settings.high[11]), ('th8', settings.high[12]), ('th9', settings.high[13]),
        ('th10', settings.high[14]), ('th11', settings.high[15]), ('th12', settings.high[16]),
        ('ti1', settings.intermediate[5]), ('ti2', settings.intermediate[6]),
        ('ti3', settings.intermediate[7]), ('ti4', settings.intermediate[8]),
        ('ti5', settings.intermediate[9]), ('ti6', settings.intermediate[10]),
        ('ti7', settings.intermediate[11]), ('ti8', settings.intermediate[12]),
        ('ti9', settings.intermediate[13]), ('ti10', settings.intermediate[14]),
        ('ti11', settings.intermediate[15]), ('ti12', settings.intermediate[16]),
        ('tl1', settings.low[5]), ('tl2', settings.low[6]), ('tl3', settings.low[7]),
        ('tl4', settings.low[8]), ('tl5', settings.low[9]), ('tl6', settings.low[10]),
        ('tl7', settings.low[11]), ('tl8', settings.low[12]), ('tl9', settings.low[13]),
        ('tl10', settings.low[14]), ('tl11', settings.low[15]), ('tl12', settings.low[16]),
        ('vhmax', settings.band_limits[5]), ('vhmin', settings.band_limits[4]),
        ('vimax', settings.band_limits[3]), ('vimin', settings.band_limits[2]),
        ('vlmax', settings.band_limits[1]), ('vlmin', settings.band_limits[0]),
        ('vstmax', settings.output_limits[1]), ('vstmin', settings.output_limits[0]),
    )
    for parameter_name, parameter_value in parameter_values:
        variable_name: str = f'PssIEEE4B.{parameter_name}_{template_name}'
        event_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[event_variable] = vfactory.add_const(value=parameter_value, name=variable_name)
    return template
