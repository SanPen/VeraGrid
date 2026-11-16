# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna MassUnit schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaMassUnit(Enum):
    """Values declared by the Sienna MassUnit schema."""

    KG = 'KG'
    LB = 'LB'
    SHORT_TON = 'SHORT_TON'
    METRIC_TON = 'METRIC_TON'


def parse_sienna_mass_unit(data: str) -> SiennaMassUnit:
    """Parse one MassUnit enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaMassUnit(data)


def sienna_mass_unit_to_json(value: SiennaMassUnit) -> str:
    """Write one MassUnit enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
