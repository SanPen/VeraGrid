# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna IncrementalCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.linear_function_data import SiennaLinearFunctionData
    from VeraGridEngine.IO.sienna.devices.core.common.piecewise_step_data import SiennaPiecewiseStepData

from VeraGridEngine.IO.sienna.devices.common import get_required_value
from VeraGridEngine.IO.sienna.devices.core.common.linear_function_data import (SiennaLinearFunctionData,
                                                                                parse_sienna_linear_function_data,
                                                                                sienna_linear_function_data_to_json)
from VeraGridEngine.IO.sienna.devices.core.common.piecewise_step_data import (SiennaPiecewiseStepData,
                                                                               parse_sienna_piecewise_step_data,
                                                                               sienna_piecewise_step_data_to_json)

class SiennaIncrementalCurve(SiennaSchemaModel):
    """Expose every declared IncrementalCurve property through fixed slots."""

    __slots__ = ('curve_type', 'function_data', 'initial_input', 'input_at_zero',)

    def __init__(self, curve_type: str, function_data: SiennaLinearFunctionData | SiennaPiecewiseStepData, initial_input: float, input_at_zero: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.curve_type: str = curve_type
        self.function_data: SiennaLinearFunctionData | SiennaPiecewiseStepData = function_data
        self.initial_input: float = initial_input
        self.input_at_zero: float = input_at_zero


def parse_sienna_incremental_curve(data: dict[str, Any]) -> SiennaIncrementalCurve:
    """Parse declared IncrementalCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed IncrementalCurve object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaIncrementalCurve(curve_type=get_required_value(data, 'curve_type', 'IncrementalCurve'), function_data=parse_sienna_schema_union((SiennaObjectKind.LinearFunctionData, SiennaObjectKind.PiecewiseStepData), get_required_value(data, 'function_data', 'IncrementalCurve')), initial_input=data.get('initial_input', None), input_at_zero=data.get('input_at_zero', None))

def sienna_incremental_curve_to_json(value: SiennaIncrementalCurve) -> dict[str, Any]:
    """Write every IncrementalCurve slot to explicit schema property names.

    :param value: Typed IncrementalCurve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'curve_type': value.curve_type, 'function_data': write_sienna_schema_union((SiennaObjectKind.LinearFunctionData, SiennaObjectKind.PiecewiseStepData), value.function_data), 'initial_input': value.initial_input, 'input_at_zero': value.input_at_zero}
