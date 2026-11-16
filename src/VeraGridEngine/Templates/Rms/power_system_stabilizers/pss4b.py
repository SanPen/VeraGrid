# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""IEEE PSS4B dual-input stabilizer with low, intermediate and high bands."""

from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Pss4bParameters:
    """Ordered PSS/E PSS4B constants from the 33.10 and 35.2 sheets."""

    __slots__ = ('coefficients',)

    def __init__(self, coefficients: tuple[float, ...]) -> None:
        """Store the 75 source constants in DYR order.

        :param coefficients: Exact ordered PSS4B CON values.
        :raises ValueError: The record does not contain 75 finite constants.
        """
        if len(coefficients) != 75:
            raise ValueError('PSS4B requires exactly 75 constants')
        elif not all(math.isfinite(value) for value in coefficients):
            raise ValueError('PSS4B constants must be finite')
        else:
            pass
        self.coefficients: tuple[float, ...] = coefficients


def _second_order_filter(builder: ControlRealization, name: str, signal: Expr,
                         a1: Expr, a0: Expr, a0_value: float, direct: Expr,
                         b1: Expr, b0: Expr, initial_input: Expr,
                         initial_output: Expr) -> Var:
    """Realize ``d + (b1*s+b0)/(s²+a1*s+a0)`` without input derivatives.

    :param builder: Controller that owns the states and algebraic output.
    :param name: Unique stage label.
    :param signal: Stage input and equilibrium value.
    :param a1: First normalized denominator coefficient.
    :param a0: Constant normalized denominator coefficient.
    :param a0_value: Construction value used to initialize the position state.
    :param direct: Direct feedthrough coefficient.
    :param b1: Numerator coefficient multiplying the rate state.
    :param b0: Numerator coefficient multiplying the position state.
    :param initial_input: Constant input at the operating point.
    :param initial_output: Exact DC output for that operating point.
    :return: Filter output signal.
    """
    position: Var = builder.vf.add_var(f'{name}Position_{builder.name}')
    rate: Var = builder.vf.add_var(f'{name}Rate_{builder.name}')
    builder.differential(position, rate, initial_input / Const(a0_value))
    builder.differential(rate, signal - a1 * rate - a0 * position, Const(0.0))
    return builder.algebraic(
        name + 'Output', direct * signal + b1 * rate + b0 * position,
        initial_output,
    )


def _gain_lead_lag(builder: ControlRealization, name: str, signal: Expr,
                   gain: Var, numerator_time: Var, denominator_time: Var,
                   gain_value: float, numerator_value: float,
                   denominator_value: float, initial: Expr) -> Var:
    """Realize ``(gain+s*numerator_time)/(1+s*denominator_time)`` exactly.

    :param builder: Controller that owns the stage.
    :param name: Unique stage label.
    :param signal: Stage input.
    :param gain: Runtime constant numerator gain.
    :param numerator_time: Runtime derivative numerator coefficient.
    :param denominator_time: Runtime denominator time constant.
    :param gain_value: Construction gain, used only for validation/initialization.
    :param numerator_value: Construction numerator time.
    :param denominator_value: Construction denominator time.
    :param initial: Constant input at the operating point.
    :return: Stage output signal.
    :raises ValueError: A zero denominator would leave an unfiltered derivative.
    """
    if denominator_value < 0.0 or numerator_value < 0.0:
        raise ValueError('PSS4B lead-lag times must be nonnegative')
    elif denominator_value == 0.0 and numerator_value != 0.0:
        raise ValueError('PSS4B zero denominator time cannot retain a derivative term')
    elif denominator_value == 0.0:
        return builder.algebraic(name, gain * signal, gain * initial)
    else:
        memory: Var = builder.lag(
            name + 'Memory', signal, denominator_time, denominator_value, initial,
        )
        expression: Expr = gain * memory + numerator_time / denominator_time * (signal - memory)
        return builder.algebraic(name, expression, gain * initial)


def build_pss4b_template(vf: VarFactory, name: str | None = None,
                         parameters: Pss4bParameters | None = None) -> RmsModelTemplate:
    """Build the PSS/E PSS4B 32-state three-band stabilizer.

    The first path filters shaft-speed deviation into low/intermediate
    frequency bands. The second path high-pass filters electrical power and
    feeds the high-frequency band. Each band has two cascaded lead-lag branches
    and its own output limits before the final supplementary-voltage limit.

    :param vf: Shared symbolic variable factory.
    :param name: Optional runtime model name.
    :param parameters: Ordered PSS/E source coefficients; None selects neutral values.
    :return: Native two-input stabilizer with one supplementary-voltage output.
    :raises ValueError: Source constants violate the represented filter domain.
    """
    default_coefficients: list[float] = [0.0] * 75
    default_coefficients[2] = 1.0
    default_coefficients[5] = 1.0
    default_coefficients[7] = 1.0
    default_coefficients[8] = 1.0
    default_coefficients[9] = 1.0
    default_coefficients[11] = 0.1
    default_coefficients[13] = 1.0
    default_coefficients[15] = 1.0
    default_coefficients[33] = 1.0
    default_coefficients[34] = -1.0
    default_coefficients[52] = 1.0
    default_coefficients[53] = -1.0
    default_coefficients[71] = 1.0
    default_coefficients[72] = -1.0
    default_coefficients[73] = 0.1
    default_coefficients[74] = -0.1
    for denominator_index in (19,21,23,27,29,31,38,40,42,46,48,50,57,59,61,65,67,69):
        default_coefficients[denominator_index] = 0.1
    settings: Pss4bParameters = Pss4bParameters(tuple(default_coefficients)) if parameters is None else parameters
    coefficients: tuple[float, ...] = settings.coefficients
    if (coefficients[2] <= 0.0 or coefficients[8] <= 0.0 or coefficients[9] <= 0.0
            or coefficients[11] < 0.0):
        raise ValueError('PSS4B requires AL-I, TH and AH positive and M nonnegative')
    elif any(coefficients[index] < 0.0 for index in (4, 6, 12, 14)):
        raise ValueError('PSS4B notch damping coefficients must be nonnegative')
    elif any(coefficients[index] <= 0.0 for index in (5, 7, 13, 15)):
        raise ValueError('PSS4B notch frequencies must be positive')
    elif any(coefficients[index] < 0.0 for index in
             (18,19,20,21,22,23,26,27,28,29,30,31,37,38,39,40,41,42,
              45,46,47,48,49,50,56,57,58,59,60,61,64,65,66,67,68,69)):
        raise ValueError('PSS4B lead-lag times must be nonnegative')
    elif (coefficients[3] < 0.0 or coefficients[10] < 0.0
          or coefficients[34] >= coefficients[33]
          or coefficients[53] >= coefficients[52]
          or coefficients[72] >= coefficients[71]
          or coefficients[74] >= coefficients[73]):
        raise ValueError('PSS4B damping and output limits are invalid')
    else:
        pass

    model_name: str = 'PSS4B' if name is None else name
    builder: ControlRealization = ControlRealization(vf, model_name)
    names: tuple[str, ...] = (
        'CL_I','DL_I','AL_I','BL_I','BW_L_I1','W_L_I1','BW_L_I2','W_L_I2',
        'TH','AH','BH','M','BW_H1','W_H1','BW_H2','W_H2',
        'KL1','KL11','TL1','TL2','TL3','TL4','TL5','TL6',
        'KL2','KL17','TL7','TL8','TL9','TL10','TL11','TL12',
        'KL','VLmax','VLmin','KI1','KI11','TI1','TI2','TI3','TI4','TI5','TI6',
        'KI2','KI17','TI7','TI8','TI9','TI10','TI11','TI12',
        'KI','VImax','VImin','KH1','KH11','TH1','TH2','TH3','TH4','TH5','TH6',
        'KH2','KH17','TH7','TH8','TH9','TH10','TH11','TH12',
        'KH','VHmax','VHmin','VSTMAX','VSTMIN',
    )
    p: tuple[Var, ...] = tuple(
        builder.parameter(parameter_name, coefficient)
        for parameter_name, coefficient in zip(names, coefficients, strict=True)
    )
    speed_deviation: Var = builder.input('SpeedDeviationPu', Const(0.0))
    electrical_power: Var = builder.input('ElectricalPowerPu', Const(0.0))

    low_transducer: Var = _second_order_filter(
        builder, 'LowTransducer', speed_deviation,
        p[3] / p[2], Const(1.0) / p[2], 1.0 / coefficients[2],
        p[0] / p[2], p[1] / p[2] - (p[0] / p[2]) * (p[3] / p[2]),
        Const(1.0) / p[2] - (p[0] / p[2]) * (Const(1.0) / p[2]),
        speed_deviation, speed_deviation,
    )
    low_notch1: Var = _second_order_filter(
        builder, 'LowNotch1', low_transducer, p[4], p[5] * p[5],
        coefficients[5] * coefficients[5], Const(1.0), -p[4], Const(0.0),
        speed_deviation, speed_deviation,
    )
    low_notch2: Var = _second_order_filter(
        builder, 'LowNotch2', low_notch1, p[6], p[7] * p[7],
        coefficients[7] * coefficients[7], Const(1.0), -p[6], Const(0.0),
        speed_deviation, speed_deviation,
    )

    high_pass: Var = _second_order_filter(
        builder, 'HighPowerTransducer', electrical_power,
        p[10] / p[9], Const(1.0) / p[9], 1.0 / coefficients[9],
        Const(1.0) / p[9], -p[10] / (p[9] * p[9]),
        -Const(1.0) / (p[9] * p[9]), electrical_power, Const(0.0),
    )
    high_transducer: Var = builder.lag(
        'HighPowerTransducerLag', high_pass, p[8], coefficients[8], Const(0.0),
    )
    power_average: Var = builder.lag(
        'HighPowerAverage', high_transducer, Const(coefficients[11]),
        coefficients[11], Const(0.0),
    ) if coefficients[11] > 0.0 else builder.algebraic(
        'HighPowerAverage', high_transducer, Const(0.0),
    )
    high_input: Var = power_average
    high_notch1: Var = _second_order_filter(
        builder, 'HighNotch1', high_input, p[12], p[13] * p[13],
        coefficients[13] * coefficients[13], Const(1.0), -p[12], Const(0.0),
        Const(0.0), Const(0.0),
    )
    high_notch2: Var = _second_order_filter(
        builder, 'HighNotch2', high_notch1, p[14], p[15] * p[15],
        coefficients[15] * coefficients[15], Const(1.0), -p[14], Const(0.0),
        Const(0.0), Const(0.0),
    )

    low1: Var = _gain_lead_lag(builder, 'LowBranch1a', low_notch2, p[17], p[18], p[19],
                              coefficients[17], coefficients[18], coefficients[19], speed_deviation)
    low1 = builder.lead_lag('LowBranch1b', low1, p[20], p[21], coefficients[20], coefficients[21], speed_deviation)
    low1 = builder.lead_lag('LowBranch1c', low1, p[22], p[23], coefficients[22], coefficients[23], speed_deviation)
    low2: Var = _gain_lead_lag(builder, 'LowBranch2a', low_notch2, p[25], p[26], p[27],
                              coefficients[25], coefficients[26], coefficients[27], speed_deviation)
    low2 = builder.lead_lag('LowBranch2b', low2, p[28], p[29], coefficients[28], coefficients[29], speed_deviation)
    low2 = builder.lead_lag('LowBranch2c', low2, p[30], p[31], coefficients[30], coefficients[31], speed_deviation)
    low_output: Var = builder.algebraic(
        'LowBandOutput', sym.hard_sat(p[32] * (p[16] * low1 - p[24] * low2), p[34], p[33]), Const(0.0),
    )

    intermediate1: Var = _gain_lead_lag(builder, 'IntermediateBranch1a', low_notch2, p[36], p[37], p[38],
                                        coefficients[36], coefficients[37], coefficients[38], speed_deviation)
    intermediate1 = builder.lead_lag('IntermediateBranch1b', intermediate1, p[39], p[40], coefficients[39], coefficients[40], speed_deviation)
    intermediate1 = builder.lead_lag('IntermediateBranch1c', intermediate1, p[41], p[42], coefficients[41], coefficients[42], speed_deviation)
    intermediate2: Var = _gain_lead_lag(builder, 'IntermediateBranch2a', low_notch2, p[44], p[45], p[46],
                                        coefficients[44], coefficients[45], coefficients[46], speed_deviation)
    intermediate2 = builder.lead_lag('IntermediateBranch2b', intermediate2, p[47], p[48], coefficients[47], coefficients[48], speed_deviation)
    intermediate2 = builder.lead_lag('IntermediateBranch2c', intermediate2, p[49], p[50], coefficients[49], coefficients[50], speed_deviation)
    intermediate_output: Var = builder.algebraic(
        'IntermediateBandOutput', sym.hard_sat(p[51] * (p[35] * intermediate1 - p[43] * intermediate2), p[53], p[52]), Const(0.0),
    )

    high1: Var = _gain_lead_lag(builder, 'HighBranch1a', high_notch2, p[55], p[56], p[57],
                               coefficients[55], coefficients[56], coefficients[57], Const(0.0))
    high1 = builder.lead_lag('HighBranch1b', high1, p[58], p[59], coefficients[58], coefficients[59], Const(0.0))
    high1 = builder.lead_lag('HighBranch1c', high1, p[60], p[61], coefficients[60], coefficients[61], Const(0.0))
    high2: Var = _gain_lead_lag(builder, 'HighBranch2a', high_notch2, p[63], p[64], p[65],
                               coefficients[63], coefficients[64], coefficients[65], Const(0.0))
    high2 = builder.lead_lag('HighBranch2b', high2, p[66], p[67], coefficients[66], coefficients[67], Const(0.0))
    high2 = builder.lead_lag('HighBranch2c', high2, p[68], p[69], coefficients[68], coefficients[69], Const(0.0))
    high_output: Var = builder.algebraic(
        'HighBandOutput', sym.hard_sat(p[70] * (p[54] * high1 - p[62] * high2), p[72], p[71]), Const(0.0),
    )
    final_output: Var = builder.algebraic(
        'VOTHSG', sym.hard_sat(low_output + intermediate_output + high_output, p[74], p[73]),
        Const(0.0),
    )
    return builder.finish((final_output,), 'IEEE PSS4B three-band dual-input stabilizer')
