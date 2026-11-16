# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna VSCDCControlModes schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaVSCDCControlModes(Enum):
    """Values declared by the Sienna VSCDCControlModes schema."""

    DC_POWER = 'DC_POWER'
    DC_VOLTAGE = 'DC_VOLTAGE'
    DC_VOLTAGE_DROOP = 'DC_VOLTAGE_DROOP'


def parse_sienna_vscdc_control_modes(data: str) -> SiennaVSCDCControlModes:
    """Parse one VSCDCControlModes enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaVSCDCControlModes(data)


def sienna_vscdc_control_modes_to_json(value: SiennaVSCDCControlModes) -> str:
    """Write one VSCDCControlModes enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
