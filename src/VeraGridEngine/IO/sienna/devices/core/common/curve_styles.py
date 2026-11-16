# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CurveStyles schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCurveStyles(Enum):
    """Values declared by the Sienna CurveStyles schema."""

    VALUE_0 = 0
    VALUE_1 = 1


def parse_sienna_curve_styles(data: str) -> SiennaCurveStyles:
    """Parse one CurveStyles enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaCurveStyles(data)


def sienna_curve_styles_to_json(value: SiennaCurveStyles) -> str:
    """Write one CurveStyles enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
