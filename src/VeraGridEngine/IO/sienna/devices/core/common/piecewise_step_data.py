# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PiecewiseStepData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPiecewiseStepData(SiennaSchemaModel):
    """Expose every declared PiecewiseStepData property through fixed slots."""

    __slots__ = ('function_type', 'x_coords', 'y_coords',)

    def __init__(self, function_type: str, x_coords: list[float], y_coords: list[float]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.function_type: str = function_type
        self.x_coords: list[float] = x_coords
        self.y_coords: list[float] = y_coords


def parse_sienna_piecewise_step_data(data: dict[str, Any]) -> SiennaPiecewiseStepData:
    """Parse declared PiecewiseStepData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PiecewiseStepData object.
    """
    return SiennaPiecewiseStepData(function_type=get_required_value(data, 'function_type', 'PiecewiseStepData'), x_coords=get_required_value(data, 'x_coords', 'PiecewiseStepData'), y_coords=get_required_value(data, 'y_coords', 'PiecewiseStepData'))


def sienna_piecewise_step_data_to_json(value: SiennaPiecewiseStepData) -> dict[str, Any]:
    """Write every PiecewiseStepData slot to explicit schema property names.

    :param value: Typed PiecewiseStepData object.
    :return: JSON object with declared schema properties.
    """
    return {'function_type': value.function_type, 'x_coords': value.x_coords, 'y_coords': value.y_coords}
