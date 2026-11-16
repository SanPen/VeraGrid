# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna InputOutputCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.linear_function_data import SiennaLinearFunctionData
    from VeraGridEngine.IO.sienna.devices.core.common.piecewise_linear_data import SiennaPiecewiseLinearData
    from VeraGridEngine.IO.sienna.devices.core.common.quadratic_function_data import SiennaQuadraticFunctionData

from VeraGridEngine.IO.sienna.devices.common import get_required_value
from VeraGridEngine.IO.sienna.devices.core.common.linear_function_data import (SiennaLinearFunctionData,
                                                                                parse_sienna_linear_function_data,
                                                                                sienna_linear_function_data_to_json)
from VeraGridEngine.IO.sienna.devices.core.common.piecewise_linear_data import (SiennaPiecewiseLinearData,
                                                                                 parse_sienna_piecewise_linear_data,
                                                                                 sienna_piecewise_linear_data_to_json)
from VeraGridEngine.IO.sienna.devices.core.common.quadratic_function_data import (SiennaQuadraticFunctionData,
                                                                                   parse_sienna_quadratic_function_data,
                                                                                   sienna_quadratic_function_data_to_json)

class SiennaInputOutputCurve(SiennaSchemaModel):
    """Expose every declared InputOutputCurve property through fixed slots."""

    __slots__ = ('curve_type', 'function_data', 'input_at_zero',)

    def __init__(self, curve_type: str, function_data: SiennaQuadraticFunctionData | SiennaLinearFunctionData | SiennaPiecewiseLinearData, input_at_zero: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.curve_type: str = curve_type
        self.function_data: SiennaQuadraticFunctionData | SiennaLinearFunctionData | SiennaPiecewiseLinearData = function_data
        self.input_at_zero: float = input_at_zero


def parse_sienna_input_output_curve(data: dict[str, Any]) -> SiennaInputOutputCurve:
    """Parse declared InputOutputCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed InputOutputCurve object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaInputOutputCurve(curve_type=get_required_value(data, 'curve_type', 'InputOutputCurve'), function_data=parse_sienna_schema_union((SiennaObjectKind.QuadraticFunctionData, SiennaObjectKind.LinearFunctionData, SiennaObjectKind.PiecewiseLinearData), get_required_value(data, 'function_data', 'InputOutputCurve')), input_at_zero=data.get('input_at_zero', None))

def sienna_input_output_curve_to_json(value: SiennaInputOutputCurve) -> dict[str, Any]:
    """Write every InputOutputCurve slot to explicit schema property names.

    :param value: Typed InputOutputCurve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'curve_type': value.curve_type, 'function_data': write_sienna_schema_union((SiennaObjectKind.QuadraticFunctionData, SiennaObjectKind.LinearFunctionData, SiennaObjectKind.PiecewiseLinearData), value.function_data), 'input_at_zero': value.input_at_zero}
