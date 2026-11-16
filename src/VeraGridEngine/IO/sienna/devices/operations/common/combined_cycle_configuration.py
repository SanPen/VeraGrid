# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CombinedCycleConfiguration schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCombinedCycleConfiguration(Enum):
    """Values declared by the Sienna CombinedCycleConfiguration schema."""

    SINGLESHAFTCOMBUSTIONSTEAM = 'SingleShaftCombustionSteam'
    SEPARATESHAFTCOMBUSTIONSTEAM = 'SeparateShaftCombustionSteam'
    DOUBLECOMBUSTIONONESTEAM = 'DoubleCombustionOneSteam'
    TRIPLECOMBUSTIONONESTEAM = 'TripleCombustionOneSteam'
    OTHER = 'Other'


def parse_sienna_combined_cycle_configuration(data: str) -> SiennaCombinedCycleConfiguration:
    """Parse one CombinedCycleConfiguration enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaCombinedCycleConfiguration(data)


def sienna_combined_cycle_configuration_to_json(value: SiennaCombinedCycleConfiguration) -> str:
    """Write one CombinedCycleConfiguration enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
