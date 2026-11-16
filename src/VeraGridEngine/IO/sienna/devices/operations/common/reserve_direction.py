# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ReserveDirection schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaReserveDirection(Enum):
    """Values declared by the Sienna ReserveDirection schema."""

    UP = 'UP'
    DOWN = 'DOWN'
    SYMMETRIC = 'SYMMETRIC'


def parse_sienna_reserve_direction(data: str) -> SiennaReserveDirection:
    """Parse one ReserveDirection enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaReserveDirection(data)


def sienna_reserve_direction_to_json(value: SiennaReserveDirection) -> str:
    """Write one ReserveDirection enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
