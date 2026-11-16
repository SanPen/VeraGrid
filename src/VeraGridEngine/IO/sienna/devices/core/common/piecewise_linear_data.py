# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PiecewiseLinearData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.two_dimensional_function_point import SiennaTwoDimensionalFunctionPoint

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPiecewiseLinearData(SiennaSchemaModel):
    """Expose every declared PiecewiseLinearData property through fixed slots."""

    __slots__ = ('function_type', 'points',)

    def __init__(self, function_type: str, points: list[SiennaTwoDimensionalFunctionPoint]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.function_type: str = function_type
        self.points: list[SiennaTwoDimensionalFunctionPoint] = points


def parse_sienna_piecewise_linear_data(data: dict[str, Any]) -> SiennaPiecewiseLinearData:
    """Parse declared PiecewiseLinearData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PiecewiseLinearData object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.two_dimensional_function_point import parse_sienna_two_dimensional_function_point
    return SiennaPiecewiseLinearData(function_type=get_required_value(data, 'function_type', 'PiecewiseLinearData'), points=[parse_sienna_two_dimensional_function_point(item) for item in get_required_value(data, 'points', 'PiecewiseLinearData')])

def sienna_piecewise_linear_data_to_json(value: SiennaPiecewiseLinearData) -> dict[str, Any]:
    """Write every PiecewiseLinearData slot to explicit schema property names.

    :param value: Typed PiecewiseLinearData object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.two_dimensional_function_point import sienna_two_dimensional_function_point_to_json
    return {'function_type': value.function_type, 'points': [sienna_two_dimensional_function_point_to_json(item) for item in value.points]}
