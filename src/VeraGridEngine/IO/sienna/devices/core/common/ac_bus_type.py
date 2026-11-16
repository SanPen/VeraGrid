# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ACBusType schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaACBusType(Enum):
    """Values declared by the Sienna ACBusType schema."""

    PQ = 'PQ'
    PV = 'PV'
    REF = 'REF'
    ISOLATED = 'ISOLATED'
    SLACK = 'SLACK'


def parse_sienna_ac_bus_type(data: str) -> SiennaACBusType:
    """Parse one ACBusType enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaACBusType(data)


def sienna_ac_bus_type_to_json(value: SiennaACBusType) -> str:
    """Write one ACBusType enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
