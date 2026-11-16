# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna BilateralConfirmation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaBilateralConfirmation(Enum):
    """Values declared by the Sienna BilateralConfirmation schema."""

    DUAL_CONFIRM = 'DUAL_CONFIRM'
    UNILATERAL_BUYER = 'UNILATERAL_BUYER'
    UNILATERAL_SELLER = 'UNILATERAL_SELLER'
    FIRST_REPORTER_DEEMED = 'FIRST_REPORTER_DEEMED'
    EXACT_MATCH_OR_REJECT = 'EXACT_MATCH_OR_REJECT'


def parse_sienna_bilateral_confirmation(data: str) -> SiennaBilateralConfirmation:
    """Parse one BilateralConfirmation enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaBilateralConfirmation(data)


def sienna_bilateral_confirmation_to_json(value: SiennaBilateralConfirmation) -> str:
    """Write one BilateralConfirmation enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
