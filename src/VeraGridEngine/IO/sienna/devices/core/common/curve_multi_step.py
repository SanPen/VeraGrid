# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CurveMultiStep schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCurveMultiStep(Enum):
    """Values declared by the Sienna CurveMultiStep schema."""

    VALUE_0 = 0
    VALUE_1 = 1


def parse_sienna_curve_multi_step(data: str) -> SiennaCurveMultiStep:
    """Parse one CurveMultiStep enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaCurveMultiStep(data)


def sienna_curve_multi_step_to_json(value: SiennaCurveMultiStep) -> str:
    """Write one CurveMultiStep enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
