# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna LCCControlMode schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaLCCControlMode(Enum):
    """Values declared by the Sienna LCCControlMode schema."""

    BLOCKED = 'BLOCKED'
    POWER = 'POWER'
    CURRENT = 'CURRENT'


def parse_sienna_lcc_control_mode(data: str) -> SiennaLCCControlMode:
    """Parse one LCCControlMode enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaLCCControlMode(data)


def sienna_lcc_control_mode_to_json(value: SiennaLCCControlMode) -> str:
    """Write one LCCControlMode enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
