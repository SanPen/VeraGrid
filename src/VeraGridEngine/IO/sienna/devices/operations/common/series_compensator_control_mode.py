# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SeriesCompensatorControlMode schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSeriesCompensatorControlMode(Enum):
    """Values declared by the Sienna SeriesCompensatorControlMode schema."""

    FIXED = 'FIXED'
    BYPASSED = 'BYPASSED'
    DISPATCHABLE = 'DISPATCHABLE'
    ACTIVE_POWER_FLOW = 'ACTIVE_POWER_FLOW'


def parse_sienna_series_compensator_control_mode(data: str) -> SiennaSeriesCompensatorControlMode:
    """Parse one SeriesCompensatorControlMode enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaSeriesCompensatorControlMode(data)


def sienna_series_compensator_control_mode_to_json(value: SiennaSeriesCompensatorControlMode) -> str:
    """Write one SeriesCompensatorControlMode enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
