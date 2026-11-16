# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna MarketStage schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaMarketStage(Enum):
    """Values declared by the Sienna MarketStage schema."""

    DAY_AHEAD = 'DAY_AHEAD'
    REAL_TIME = 'REAL_TIME'


def parse_sienna_market_stage(data: str) -> SiennaMarketStage:
    """Parse one MarketStage enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaMarketStage(data)


def sienna_market_stage_to_json(value: SiennaMarketStage) -> str:
    """Write one MarketStage enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
