# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AdmittanceUnitBasis schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAdmittanceUnitBasis(Enum):
    """Values declared by the Sienna AdmittanceUnitBasis schema."""

    NATURAL_UNITS = 'NATURAL_UNITS'
    COMPONENT_MVAR = 'COMPONENT_MVAR'
    COMPONENT_BASE = 'COMPONENT_BASE'


def parse_sienna_admittance_unit_basis(data: str) -> SiennaAdmittanceUnitBasis:
    """Parse one AdmittanceUnitBasis enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaAdmittanceUnitBasis(data)


def sienna_admittance_unit_basis_to_json(value: SiennaAdmittanceUnitBasis) -> str:
    """Write one AdmittanceUnitBasis enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
