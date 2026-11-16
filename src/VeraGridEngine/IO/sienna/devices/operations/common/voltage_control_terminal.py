# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna VoltageControlTerminal schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaVoltageControlTerminal(Enum):
    """Values declared by the Sienna VoltageControlTerminal schema."""

    UNDEFINED = 'UNDEFINED'
    FROM = 'FROM'
    TO = 'TO'


def parse_sienna_voltage_control_terminal(data: str) -> SiennaVoltageControlTerminal:
    """Parse one VoltageControlTerminal enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaVoltageControlTerminal(data)


def sienna_voltage_control_terminal_to_json(value: SiennaVoltageControlTerminal) -> str:
    """Write one VoltageControlTerminal enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
