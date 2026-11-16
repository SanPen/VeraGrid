# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna VSCACControlModes schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaVSCACControlModes(Enum):
    """Values declared by the Sienna VSCACControlModes schema."""

    AC_REACTIVE_POWER = 'AC_REACTIVE_POWER'
    AC_VOLTAGE = 'AC_VOLTAGE'


def parse_sienna_vscac_control_modes(data: str) -> SiennaVSCACControlModes:
    """Parse one VSCACControlModes enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaVSCACControlModes(data)


def sienna_vscac_control_modes_to_json(value: SiennaVSCACControlModes) -> str:
    """Write one VSCACControlModes enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
