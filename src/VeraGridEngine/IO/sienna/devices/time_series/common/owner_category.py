# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna OwnerCategory schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaOwnerCategory(Enum):
    """Values declared by the Sienna OwnerCategory schema."""

    COMPONENT = 'Component'
    SUPPLEMENTALATTRIBUTE = 'SupplementalAttribute'


def parse_sienna_owner_category(data: str) -> SiennaOwnerCategory:
    """Parse one OwnerCategory enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaOwnerCategory(data)


def sienna_owner_category_to_json(value: SiennaOwnerCategory) -> str:
    """Write one OwnerCategory enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
