# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""DERA1 terminal-voltage transducer from PSS/E 35.2 §17.1."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class Dera1VoltageMeasurementSettings:
    """Store the voltage transducer time and solved voltage."""

    __slots__ = ('trv', 'initial_voltage')

    def __init__(self, trv: float = 0.02, initial_voltage: float = 1.0) -> None:
        """Store PSS/E voltage measurement settings.

        :param trv: Voltage transducer time constant in seconds.
        :param initial_voltage: Solved terminal-voltage magnitude in pu.
        :return: None.
        """
        self.trv: float = trv
        self.initial_voltage: float = initial_voltage


def build_dera1_voltage_measurement_template(
        vf: VarFactory,
        name: str = 'DERA1 voltage measurement',
        settings: Dera1VoltageMeasurementSettings | None = None,
) -> RmsModelTemplate:
    """Build the PSS/E first-order terminal-voltage measurement lag.

    :param vf: Shared symbolic variable factory.
    :param name: Unique model-component name.
    :param settings: Transducer parameter and solved voltage.
    :return: One-input controller with filtered-voltage output.
    :raises ValueError: Invalid time constant or initial voltage.
    """
    selected: Dera1VoltageMeasurementSettings = (
        Dera1VoltageMeasurementSettings() if settings is None else settings
    )
    if not math.isfinite(selected.trv) or selected.trv < 0.0:
        raise ValueError('DERA1 Trv must be finite and nonnegative')
    elif not math.isfinite(selected.initial_voltage) or selected.initial_voltage <= 0.0:
        raise ValueError('DERA1 initial terminal voltage must be finite and positive')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    terminal_voltage: Var = control.input(
        'TerminalVoltageMagnitudePu', Const(selected.initial_voltage),
    )
    measurement_time: Var = control.parameter('TRV', selected.trv)
    filtered_voltage: Var = control.lag(
        'FilteredTerminalVoltagePu', terminal_voltage, measurement_time,
        selected.trv, Const(selected.initial_voltage),
    )
    return control.finish((filtered_voltage,), 'DERA1 Trv terminal-voltage transducer')
