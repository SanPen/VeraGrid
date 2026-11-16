# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TimeSeriesIncrementalCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.function_data import SiennaFunctionData

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTimeSeriesIncrementalCurve(SiennaSchemaModel):
    """Expose every declared TimeSeriesIncrementalCurve property through fixed slots."""

    __slots__ = ('curve_type', 'function_data', 'initial_input_association_id', 'input_at_zero_association_id',)

    def __init__(self, curve_type: str, function_data: SiennaFunctionData, initial_input_association_id: int | None, input_at_zero_association_id: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.curve_type: str = curve_type
        self.function_data: SiennaFunctionData = function_data
        self.initial_input_association_id: int | None = initial_input_association_id
        self.input_at_zero_association_id: int | None = input_at_zero_association_id


def parse_sienna_time_series_incremental_curve(data: dict[str, Any]) -> SiennaTimeSeriesIncrementalCurve:
    """Parse declared TimeSeriesIncrementalCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TimeSeriesIncrementalCurve object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.function_data import parse_sienna_function_data
    return SiennaTimeSeriesIncrementalCurve(curve_type=get_required_value(data, 'curve_type', 'TimeSeriesIncrementalCurve'), function_data=parse_sienna_function_data(get_required_value(data, 'function_data', 'TimeSeriesIncrementalCurve')), initial_input_association_id=data.get('initial_input_association_id', None), input_at_zero_association_id=data.get('input_at_zero_association_id', None))

def sienna_time_series_incremental_curve_to_json(value: SiennaTimeSeriesIncrementalCurve) -> dict[str, Any]:
    """Write every TimeSeriesIncrementalCurve slot to explicit schema property names.

    :param value: Typed TimeSeriesIncrementalCurve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.function_data import sienna_function_data_to_json
    return {'curve_type': value.curve_type, 'function_data': sienna_function_data_to_json(value.function_data), 'initial_input_association_id': value.initial_input_association_id, 'input_at_zero_association_id': value.input_at_zero_association_id}
