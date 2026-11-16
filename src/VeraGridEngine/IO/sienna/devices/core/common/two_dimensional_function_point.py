# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TwoDimensionalFunctionPoint schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTwoDimensionalFunctionPoint(SiennaSchemaModel):
    """Expose every declared TwoDimensionalFunctionPoint property through fixed slots."""

    __slots__ = ('x', 'y',)

    def __init__(self, x: float, y: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.x: float = x
        self.y: float = y


def parse_sienna_two_dimensional_function_point(data: dict[str, Any]) -> SiennaTwoDimensionalFunctionPoint:
    """Parse declared TwoDimensionalFunctionPoint properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TwoDimensionalFunctionPoint object.
    """
    return SiennaTwoDimensionalFunctionPoint(x=get_required_value(data, 'x', 'TwoDimensionalFunctionPoint'), y=get_required_value(data, 'y', 'TwoDimensionalFunctionPoint'))


def sienna_two_dimensional_function_point_to_json(value: SiennaTwoDimensionalFunctionPoint) -> dict[str, Any]:
    """Write every TwoDimensionalFunctionPoint slot to explicit schema property names.

    :param value: Typed TwoDimensionalFunctionPoint object.
    :return: JSON object with declared schema properties.
    """
    return {'x': value.x, 'y': value.y}
