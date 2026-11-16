# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PollutantType schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPollutantType(Enum):
    """Values declared by the Sienna PollutantType schema."""

    CO2 = 'CO2'
    CO2E = 'CO2E'
    CH4 = 'CH4'
    N2O = 'N2O'
    NOX = 'NOX'
    SO2 = 'SO2'
    CO = 'CO'
    VOC = 'VOC'
    PM25 = 'PM25'
    PM10 = 'PM10'
    HG = 'HG'
    HAP = 'HAP'
    CUSTOM = 'CUSTOM'


def parse_sienna_pollutant_type(data: str) -> SiennaPollutantType:
    """Parse one PollutantType enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaPollutantType(data)


def sienna_pollutant_type_to_json(value: SiennaPollutantType) -> str:
    """Write one PollutantType enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
