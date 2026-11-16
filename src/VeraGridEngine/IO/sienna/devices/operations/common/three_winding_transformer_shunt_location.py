# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ThreeWindingTransformerShuntLocation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaThreeWindingTransformerShuntLocation(Enum):
    """Values declared by the Sienna ThreeWindingTransformerShuntLocation schema."""

    PRIMARY = 'PRIMARY'
    STAR = 'STAR'


def parse_sienna_three_winding_transformer_shunt_location(data: str) -> SiennaThreeWindingTransformerShuntLocation:
    """Parse one ThreeWindingTransformerShuntLocation enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaThreeWindingTransformerShuntLocation(data)


def sienna_three_winding_transformer_shunt_location_to_json(value: SiennaThreeWindingTransformerShuntLocation) -> str:
    """Write one ThreeWindingTransformerShuntLocation enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
