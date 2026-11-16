# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ShuntAdmittanceUnitBasis schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaShuntAdmittanceUnitBasis(Enum):
    """Values declared by the Sienna ShuntAdmittanceUnitBasis schema."""

    NATURAL_UNITS = 'NATURAL_UNITS'
    COMPONENT_MVAR = 'COMPONENT_MVAR'


def parse_sienna_shunt_admittance_unit_basis(data: str) -> SiennaShuntAdmittanceUnitBasis:
    """Parse one ShuntAdmittanceUnitBasis enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaShuntAdmittanceUnitBasis(data)


def sienna_shunt_admittance_unit_basis_to_json(value: SiennaShuntAdmittanceUnitBasis) -> str:
    """Write one ShuntAdmittanceUnitBasis enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
