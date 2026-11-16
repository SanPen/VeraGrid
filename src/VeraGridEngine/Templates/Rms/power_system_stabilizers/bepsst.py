# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E transient-excitation-boosting stabilizer's PSS signal path."""

from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.procedural_logic import bool_and


class BepsstParameters:
    """Ordered PSS/E BEPSST settings for the PSS path."""

    __slots__ = ('coefficients',)

    def __init__(self, coefficients: tuple[float, ...] | None = None) -> None:
        """Store the 21 source constants in DYR order.

        :param coefficients: Ordered source constants; neutral PSS path defaults
            are used when omitted.
        :raises ValueError: The source record does not have 21 finite constants.
        """
        default_values: tuple[float, ...] = (
            1.0, 0.0, 0.1, 0.1, 0.1, 0.1, 0.0, 0.1, 0.0, 0.1,
            0.0, 0.1, 0.1, -0.1, 0.0, 0.0, 0.0, 0.1, 0.1, 0.0, 0.0,
        )
        selected: tuple[float, ...] = default_values if coefficients is None else coefficients
        if len(selected) != 21:
            raise ValueError('BEPSST requires exactly 21 source constants')
        elif not all(math.isfinite(value) for value in selected):
            raise ValueError('BEPSST constants must be finite')
        else:
            self.coefficients: tuple[float, ...] = selected


def build_bepsst_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: BepsstParameters | None = None,
) -> RmsModelTemplate:
    """Build the documented BEPSST PSS path with the trip boost disabled.

    Source records with ITS=0 use this six-state PSS path. The TEB branch is
    deliberately excluded until its event trigger and dynamic limiter are
    represented; DYR conversion rejects records with ITS nonzero.

    :param vf: Shared symbolic variable factory.
    :param name: Optional runtime model name.
    :param parameters: Source-order constants, defaulting to a neutral path.
    :return: Native two-input, one-output stabilizer with terminal-voltage gate.
    :raises ValueError: Times, voltage window or output limits are invalid.
    """
    settings: BepsstParameters = BepsstParameters() if parameters is None else parameters
    values: tuple[float, ...] = settings.coefficients
    time_indices: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 17, 18)
    # Reject invalid denominators before they can select singular state equations.
    if values[5] <= 0.0 or any(values[index] < 0.0 for index in time_indices):
        raise ValueError('BEPSST time constants must be nonnegative and T4 positive')
    elif any(values[denominator] == 0.0 and values[numerator] != 0.0
             for numerator, denominator in ((4, 5), (6, 7), (8, 9), (10, 11))):
        raise ValueError('BEPSST zero denominator requires zero lead time')
    elif values[13] > values[12]:
        raise ValueError('BEPSST LSMIN must not exceed LSMAX')
    elif values[14] != 0.0 and values[15] != 0.0 and values[15] >= values[14]:
        raise ValueError('BEPSST VCL must be below VCU when both voltage gates are enabled')
    else:
        pass

    model_name: str = 'BEPSST' if name is None else name
    builder: ControlRealization = ControlRealization(vf, model_name)
    names: tuple[str, ...] = (
        'K1', 'K2', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8',
        'T9', 'T10', 'LSMAX', 'LSMIN', 'VCU', 'VCL', 'TEBK', 'TEBT11',
        'TEBT12', 'CRT', 'CLIM',
    )
    parameters_by_name: tuple[Var, ...] = tuple(
        builder.parameter(parameter_name, value)
        for parameter_name, value in zip(names, values, strict=True)
    )
    signal1: Var = builder.input('Signal1Pu', Const(0.0))
    signal2: Var = builder.input('Signal2Pu', Const(0.0))
    terminal_voltage: Var = builder.input('TerminalVoltagePu', Const(1.0))
    initial_voltage: Var = builder.input('InitialTerminalVoltagePu', Const(1.0))
    # The two weighted transducers shape selected measurements before summation.
    filtered1: Var = builder.lag(
        'Input1FilteredPu', signal1, parameters_by_name[2], values[2], signal1,
    )
    filtered2: Var = builder.lag(
        'Input2FilteredPu', signal2, parameters_by_name[3], values[3], signal2,
    )
    input_sum: Var = builder.algebraic(
        'WeightedInputPu', parameters_by_name[0] * filtered1
        + parameters_by_name[1] * filtered2,
        parameters_by_name[0] * signal1 + parameters_by_name[1] * signal2,
    )
    if values[4] == 0.0:
        # PSS/E replaces the zero sT3 numerator by unity, leaving a simple lag.
        stage: Var = builder.lag(
            'WashoutLeadLagPu', input_sum,
            parameters_by_name[5], values[5], input_sum,
        )
    else:
        # Positive T3 selects the documented high-pass washout realization.
        stage = builder.washout(
            'WashoutLeadLagPu', input_sum, parameters_by_name[5], values[5],
            parameters_by_name[4] / parameters_by_name[5], input_sum,
        )
    # Three cascaded lead-lags provide the source's phase compensation.
    stage_index: int
    for stage_index in (6, 8, 10):
        stage: Var = builder.lead_lag(
            'LeadLag' + str(stage_index) + 'Pu', stage,
            parameters_by_name[stage_index], parameters_by_name[stage_index + 1],
            values[stage_index], values[stage_index + 1], Const(0.0),
        )
    # Apply the signal limiter before the independent terminal-voltage gate.
    limited: Expr = sym.hard_sat(stage, parameters_by_name[13], parameters_by_name[12])
    voltage_conditions: tuple[Expr, ...] = tuple()
    if values[14] == 0.0:
        voltage_conditions = voltage_conditions + (Const(1.0) > Const(0.0),)
    else:
        voltage_conditions = voltage_conditions + (
            terminal_voltage < initial_voltage + parameters_by_name[14],
        )
    if values[15] == 0.0:
        voltage_conditions = voltage_conditions + (Const(1.0) > Const(0.0),)
    else:
        voltage_conditions = voltage_conditions + (
            terminal_voltage > initial_voltage + parameters_by_name[15],
        )
    voltage_gate: Expr = bool_and(voltage_conditions[0], voltage_conditions[1])
    output: Var = builder.algebraic(
        'VOTHSG', limited * voltage_gate, Const(0.0),
    )
    return builder.finish((output,), 'BEPSST PSS path with voltage gate; TEB disabled')
