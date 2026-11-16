# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna BilateralProduct schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaBilateralProduct(Enum):
    """Values declared by the Sienna BilateralProduct schema."""

    ENERGY = 'ENERGY'
    CAPACITY = 'CAPACITY'
    ANCILLARY_SERVICE = 'ANCILLARY_SERVICE'
    LOAD_OBLIGATION = 'LOAD_OBLIGATION'


def parse_sienna_bilateral_product(data: str) -> SiennaBilateralProduct:
    """Parse one BilateralProduct enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaBilateralProduct(data)


def sienna_bilateral_product_to_json(value: SiennaBilateralProduct) -> str:
    """Write one BilateralProduct enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
