# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FunctionData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.linear_function_data import SiennaLinearFunctionData
    from VeraGridEngine.IO.sienna.devices.core.common.piecewise_linear_data import SiennaPiecewiseLinearData
    from VeraGridEngine.IO.sienna.devices.core.common.piecewise_step_data import SiennaPiecewiseStepData
    from VeraGridEngine.IO.sienna.devices.core.common.quadratic_function_data import SiennaQuadraticFunctionData
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_linear_function_data import SiennaTimeSeriesLinearFunctionData
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_piecewise_linear_data import SiennaTimeSeriesPiecewiseLinearData
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_piecewise_step_data import SiennaTimeSeriesPiecewiseStepData
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_quadratic_function_data import SiennaTimeSeriesQuadraticFunctionData

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFunctionData(SiennaSchemaModel):
    """Expose every declared FunctionData property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: SiennaLinearFunctionData | SiennaQuadraticFunctionData | SiennaPiecewiseLinearData | SiennaPiecewiseStepData | SiennaTimeSeriesLinearFunctionData | SiennaTimeSeriesQuadraticFunctionData | SiennaTimeSeriesPiecewiseLinearData | SiennaTimeSeriesPiecewiseStepData) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: SiennaLinearFunctionData | SiennaQuadraticFunctionData | SiennaPiecewiseLinearData | SiennaPiecewiseStepData | SiennaTimeSeriesLinearFunctionData | SiennaTimeSeriesQuadraticFunctionData | SiennaTimeSeriesPiecewiseLinearData | SiennaTimeSeriesPiecewiseStepData = value


def parse_sienna_function_data(data: dict[str, Any]) -> SiennaFunctionData:
    """Parse declared FunctionData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FunctionData object.
    """
    return SiennaFunctionData(value=data.get('value', None))


def sienna_function_data_to_json(value: SiennaFunctionData) -> dict[str, Any]:
    """Write every FunctionData slot to explicit schema property names.

    :param value: Typed FunctionData object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
