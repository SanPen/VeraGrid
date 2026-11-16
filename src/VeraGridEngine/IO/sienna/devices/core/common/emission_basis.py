# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EmissionBasis schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEmissionBasis(Enum):
    """Values declared by the Sienna EmissionBasis schema."""

    FUEL_INPUT = 'FUEL_INPUT'
    POWER_OUTPUT = 'POWER_OUTPUT'


def parse_sienna_emission_basis(data: str) -> SiennaEmissionBasis:
    """Parse one EmissionBasis enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaEmissionBasis(data)


def sienna_emission_basis_to_json(value: SiennaEmissionBasis) -> str:
    """Write one EmissionBasis enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
