# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SwitchedAdmittanceControlMode schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSwitchedAdmittanceControlMode(Enum):
    """Values declared by the Sienna SwitchedAdmittanceControlMode schema."""

    UNDEFINED = 'UNDEFINED'
    FIXED = 'FIXED'
    DISCRETE_VOLTAGE = 'DISCRETE_VOLTAGE'
    CONTINUOUS_VOLTAGE = 'CONTINUOUS_VOLTAGE'
    DISCRETE_REACTIVE_PLANT = 'DISCRETE_REACTIVE_PLANT'
    DISCRETE_REACTIVE_VSC = 'DISCRETE_REACTIVE_VSC'
    DISCRETE_ADMITTANCE_REMOTE = 'DISCRETE_ADMITTANCE_REMOTE'
    DISCRETE_REACTIVE_FACTS = 'DISCRETE_REACTIVE_FACTS'


def parse_sienna_switched_admittance_control_mode(data: str) -> SiennaSwitchedAdmittanceControlMode:
    """Parse one SwitchedAdmittanceControlMode enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaSwitchedAdmittanceControlMode(data)


def sienna_switched_admittance_control_mode_to_json(value: SiennaSwitchedAdmittanceControlMode) -> str:
    """Write one SwitchedAdmittanceControlMode enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
