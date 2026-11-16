# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna StorageTech schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaStorageTech(Enum):
    """Values declared by the Sienna StorageTech schema."""

    PTES = 'PTES'
    LIB = 'LIB'
    LAB = 'LAB'
    FLWB = 'FLWB'
    SIB = 'SIB'
    ZIB = 'ZIB'
    HGS = 'HGS'
    LAES = 'LAES'
    OTHER_CHEM = 'OTHER_CHEM'
    OTHER_MECH = 'OTHER_MECH'
    OTHER_THERM = 'OTHER_THERM'


def parse_sienna_storage_tech(data: str) -> SiennaStorageTech:
    """Parse one StorageTech enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaStorageTech(data)


def sienna_storage_tech_to_json(value: SiennaStorageTech) -> str:
    """Write one StorageTech enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
