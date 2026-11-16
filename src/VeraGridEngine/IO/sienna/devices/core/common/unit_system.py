# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna UnitSystem schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaUnitSystem(Enum):
    """Values declared by the Sienna UnitSystem schema."""

    COMPONENT_BASE = 'COMPONENT_BASE'
    NATURAL_UNITS = 'NATURAL_UNITS'


def parse_sienna_unit_system(data: str) -> SiennaUnitSystem:
    """Parse one UnitSystem enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaUnitSystem(data)


def sienna_unit_system_to_json(value: SiennaUnitSystem) -> str:
    """Write one UnitSystem enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
