# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TimeSeriesQuadraticFunctionData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTimeSeriesQuadraticFunctionData(SiennaSchemaModel):
    """Expose every declared TimeSeriesQuadraticFunctionData property through fixed slots."""

    __slots__ = ('function_type', 'association_id',)

    def __init__(self, function_type: str, association_id: int) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.function_type: str = function_type
        self.association_id: int = association_id


def parse_sienna_time_series_quadratic_function_data(data: dict[str, Any]) -> SiennaTimeSeriesQuadraticFunctionData:
    """Parse declared TimeSeriesQuadraticFunctionData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TimeSeriesQuadraticFunctionData object.
    """
    return SiennaTimeSeriesQuadraticFunctionData(function_type=get_required_value(data, 'function_type', 'TimeSeriesQuadraticFunctionData'), association_id=get_required_value(data, 'association_id', 'TimeSeriesQuadraticFunctionData'))


def sienna_time_series_quadratic_function_data_to_json(value: SiennaTimeSeriesQuadraticFunctionData) -> dict[str, Any]:
    """Write every TimeSeriesQuadraticFunctionData slot to explicit schema property names.

    :param value: Typed TimeSeriesQuadraticFunctionData object.
    :return: JSON object with declared schema properties.
    """
    return {'function_type': value.function_type, 'association_id': value.association_id}
