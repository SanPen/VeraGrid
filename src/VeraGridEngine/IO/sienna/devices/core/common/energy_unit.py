# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EnergyUnit schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEnergyUnit(Enum):
    """Values declared by the Sienna EnergyUnit schema."""

    MMBTU = 'MMBTU'
    GJ = 'GJ'
    MWH = 'MWH'


def parse_sienna_energy_unit(data: str) -> SiennaEnergyUnit:
    """Parse one EnergyUnit enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaEnergyUnit(data)


def sienna_energy_unit_to_json(value: SiennaEnergyUnit) -> str:
    """Write one EnergyUnit enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
