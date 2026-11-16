# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FACTSControlDeviceControlMode schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFACTSControlDeviceControlMode(Enum):
    """Values declared by the Sienna FACTSControlDeviceControlMode schema."""

    OOS = 'OOS'
    NML = 'NML'
    BYP = 'BYP'


def parse_sienna_facts_control_device_control_mode(data: str) -> SiennaFACTSControlDeviceControlMode:
    """Parse one FACTSControlDeviceControlMode enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaFACTSControlDeviceControlMode(data)


def sienna_facts_control_device_control_mode_to_json(value: SiennaFACTSControlDeviceControlMode) -> str:
    """Write one FACTSControlDeviceControlMode enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
