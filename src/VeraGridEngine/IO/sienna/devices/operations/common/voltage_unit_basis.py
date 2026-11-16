# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna VoltageUnitBasis schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaVoltageUnitBasis(Enum):
    """Values declared by the Sienna VoltageUnitBasis schema."""

    NATURAL_UNITS = 'NATURAL_UNITS'
    COMPONENT_BASE = 'COMPONENT_BASE'


def parse_sienna_voltage_unit_basis(data: str) -> SiennaVoltageUnitBasis:
    """Parse one VoltageUnitBasis enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaVoltageUnitBasis(data)


def sienna_voltage_unit_basis_to_json(value: SiennaVoltageUnitBasis) -> str:
    """Write one VoltageUnitBasis enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
