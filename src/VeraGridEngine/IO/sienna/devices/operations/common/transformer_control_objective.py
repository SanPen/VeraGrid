# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TransformerControlObjective schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTransformerControlObjective(Enum):
    """Values declared by the Sienna TransformerControlObjective schema."""

    UNDEFINED = 'UNDEFINED'
    VOLTAGE_DISABLED = 'VOLTAGE_DISABLED'
    REACTIVE_POWER_FLOW_DISABLED = 'REACTIVE_POWER_FLOW_DISABLED'
    ACTIVE_POWER_FLOW_DISABLED = 'ACTIVE_POWER_FLOW_DISABLED'
    CONTROL_OF_DC_LINE_DISABLED = 'CONTROL_OF_DC_LINE_DISABLED'
    ASYMMETRIC_ACTIVE_POWER_FLOW_DISABLED = 'ASYMMETRIC_ACTIVE_POWER_FLOW_DISABLED'
    FIXED = 'FIXED'
    VOLTAGE = 'VOLTAGE'
    REACTIVE_POWER_FLOW = 'REACTIVE_POWER_FLOW'
    ACTIVE_POWER_FLOW = 'ACTIVE_POWER_FLOW'
    CONTROL_OF_DC_LINE = 'CONTROL_OF_DC_LINE'
    ASYMMETRIC_ACTIVE_POWER_FLOW = 'ASYMMETRIC_ACTIVE_POWER_FLOW'


def parse_sienna_transformer_control_objective(data: str) -> SiennaTransformerControlObjective:
    """Parse one TransformerControlObjective enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaTransformerControlObjective(data)


def sienna_transformer_control_objective_to_json(value: SiennaTransformerControlObjective) -> str:
    """Write one TransformerControlObjective enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
