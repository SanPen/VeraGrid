# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TimeSeriesInputOutputCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.function_data import SiennaFunctionData

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTimeSeriesInputOutputCurve(SiennaSchemaModel):
    """Expose every declared TimeSeriesInputOutputCurve property through fixed slots."""

    __slots__ = ('curve_type', 'function_data', 'input_at_zero',)

    def __init__(self, curve_type: str, function_data: SiennaFunctionData, input_at_zero: float | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.curve_type: str = curve_type
        self.function_data: SiennaFunctionData = function_data
        self.input_at_zero: float | None = input_at_zero


def parse_sienna_time_series_input_output_curve(data: dict[str, Any]) -> SiennaTimeSeriesInputOutputCurve:
    """Parse declared TimeSeriesInputOutputCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TimeSeriesInputOutputCurve object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.function_data import parse_sienna_function_data
    return SiennaTimeSeriesInputOutputCurve(curve_type=get_required_value(data, 'curve_type', 'TimeSeriesInputOutputCurve'), function_data=parse_sienna_function_data(get_required_value(data, 'function_data', 'TimeSeriesInputOutputCurve')), input_at_zero=data.get('input_at_zero', None))

def sienna_time_series_input_output_curve_to_json(value: SiennaTimeSeriesInputOutputCurve) -> dict[str, Any]:
    """Write every TimeSeriesInputOutputCurve slot to explicit schema property names.

    :param value: Typed TimeSeriesInputOutputCurve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.function_data import sienna_function_data_to_json
    return {'curve_type': value.curve_type, 'function_data': sienna_function_data_to_json(value.function_data), 'input_at_zero': value.input_at_zero}
