# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna IntervalAlignment schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaIntervalAlignment(Enum):
    """Values declared by the Sienna IntervalAlignment schema."""

    PERIOD_BEGINNING = 'PERIOD_BEGINNING'
    PERIOD_MIDPOINT = 'PERIOD_MIDPOINT'
    PERIOD_ENDING = 'PERIOD_ENDING'


def parse_sienna_interval_alignment(data: str) -> SiennaIntervalAlignment:
    """Parse one IntervalAlignment enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaIntervalAlignment(data)


def sienna_interval_alignment_to_json(value: SiennaIntervalAlignment) -> str:
    """Write one IntervalAlignment enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
