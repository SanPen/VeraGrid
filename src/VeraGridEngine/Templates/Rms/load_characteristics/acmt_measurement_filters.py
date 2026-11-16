# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Voltage and frequency filters for the PSS/E ACMT compressor model."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class AcmtMeasurementFilterParameters:
    """Store the ACMT measurement lags and solved initial input values."""

    __slots__ = ('voltage_time', 'frequency_time', 'initial_voltage_pu', 'initial_frequency_pu')

    def __init__(
            self,
            voltage_time: float,
            frequency_time: float,
            initial_voltage_pu: float,
            initial_frequency_pu: float = 1.0,
    ) -> None:
        """Store filter time constants and equilibrium measurements.

        :param voltage_time: Voltage-measurement lag in seconds.
        :param frequency_time: Frequency-measurement lag in seconds.
        :param initial_voltage_pu: Solved initial terminal voltage magnitude.
        :param initial_frequency_pu: Solved initial absolute frequency in per-unit.
        """
        self.voltage_time: float = voltage_time
        self.frequency_time: float = frequency_time
        self.initial_voltage_pu: float = initial_voltage_pu
        self.initial_frequency_pu: float = initial_frequency_pu


def build_acmt_measurement_filters(
        vf: VarFactory,
        name: str,
        parameters: AcmtMeasurementFilterParameters,
) -> RmsModelTemplate:
    """Build the ACMT filtered voltage and absolute-frequency states.

    The second output is filtered ``frequency_pu - 1`` because the ACMT P/Q
    characteristic uses frequency deviation while its source state is absolute
    per-unit bus frequency.

    :param vf: Variable factory owning this component's equations.
    :param name: Unique measurement-filter instance name.
    :param parameters: Source lags and solved initial measurements.
    :return: Component with two host inputs and filtered voltage/deviation outputs.
    :raises ValueError: If time constants or initial measurements are invalid.
    """
    values: tuple[float, ...] = (
        parameters.voltage_time, parameters.frequency_time,
        parameters.initial_voltage_pu, parameters.initial_frequency_pu,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('ACMT measurement filter settings must be finite')
    elif parameters.voltage_time < 0.0 or parameters.frequency_time < 0.0:
        raise ValueError('ACMT measurement filter times must be nonnegative')
    elif parameters.initial_voltage_pu <= 0.0 or parameters.initial_frequency_pu <= 0.0:
        raise ValueError('ACMT initial voltage and frequency must be positive')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    voltage_input: Var = control.input(
        'BusVoltageMagnitudePu', Const(parameters.initial_voltage_pu),
    )
    frequency_input: Var = control.input(
        'BusFrequencyPu', Const(parameters.initial_frequency_pu),
    )
    voltage_time: Var = control.parameter('Tv', parameters.voltage_time)
    frequency_time: Var = control.parameter('Tf', parameters.frequency_time)
    filtered_voltage: Var = control.lag(
        'FilteredVoltageMagnitudePu', voltage_input, voltage_time,
        parameters.voltage_time, Const(parameters.initial_voltage_pu),
    )
    filtered_frequency: Var = control.lag(
        'FilteredFrequencyPu', frequency_input, frequency_time,
        parameters.frequency_time, Const(parameters.initial_frequency_pu),
    )
    frequency_deviation: Var = control.algebraic(
        'FilteredFrequencyDeviationPu', filtered_frequency - Const(1.0),
        Const(parameters.initial_frequency_pu - 1.0),
    )
    return control.finish(
        (filtered_voltage, frequency_deviation),
        'PSS/E ACMT terminal-voltage and bus-frequency measurement filters.',
    )
