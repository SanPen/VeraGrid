# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna LoadConformity schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaLoadConformity(Enum):
    """Values declared by the Sienna LoadConformity schema."""

    NON_CONFORMING = 'NON_CONFORMING'
    CONFORMING = 'CONFORMING'
    UNDEFINED = 'UNDEFINED'


def parse_sienna_load_conformity(data: str) -> SiennaLoadConformity:
    """Parse one LoadConformity enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaLoadConformity(data)


def sienna_load_conformity_to_json(value: SiennaLoadConformity) -> str:
    """Write one LoadConformity enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
