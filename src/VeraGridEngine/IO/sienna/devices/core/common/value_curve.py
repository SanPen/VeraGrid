# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ValueCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.average_rate_curve import SiennaAverageRateCurve
    from VeraGridEngine.IO.sienna.devices.core.common.incremental_curve import SiennaIncrementalCurve
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import SiennaInputOutputCurve
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_average_rate_curve import SiennaTimeSeriesAverageRateCurve
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_incremental_curve import SiennaTimeSeriesIncrementalCurve
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_input_output_curve import SiennaTimeSeriesInputOutputCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value
from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind, parse_sienna_schema_union)

class SiennaValueCurve(SiennaSchemaModel):
    """Expose every declared ValueCurve property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: SiennaInputOutputCurve | SiennaIncrementalCurve | SiennaAverageRateCurve | SiennaTimeSeriesInputOutputCurve | SiennaTimeSeriesIncrementalCurve | SiennaTimeSeriesAverageRateCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: SiennaInputOutputCurve | SiennaIncrementalCurve | SiennaAverageRateCurve | SiennaTimeSeriesInputOutputCurve | SiennaTimeSeriesIncrementalCurve | SiennaTimeSeriesAverageRateCurve = value


def parse_sienna_value_curve(data: dict[str, Any]) -> SiennaValueCurve:
    """Parse declared ValueCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ValueCurve object.
    """
    nested_value: dict[str, Any] = get_required_value(data, "value", "ValueCurve")
    curve_type: str = str(get_required_value(nested_value, "curve_type", "ValueCurve value"))
    kind_by_curve_type: dict[str, SiennaObjectKind] = {
        "INPUT_OUTPUT": SiennaObjectKind.InputOutputCurve,
        "INCREMENTAL": SiennaObjectKind.IncrementalCurve,
        "AVERAGE_RATE": SiennaObjectKind.AverageRateCurve,
        "TIME_SERIES_INPUT_OUTPUT": SiennaObjectKind.TimeSeriesInputOutputCurve,
        "TIME_SERIES_INCREMENTAL": SiennaObjectKind.TimeSeriesIncrementalCurve,
        "TIME_SERIES_AVERAGE_RATE": SiennaObjectKind.TimeSeriesAverageRateCurve}
    kind: SiennaObjectKind | None = kind_by_curve_type.get(curve_type, None)
    if kind is None:
        raise ValueError(f"Unsupported ValueCurve curve_type '{curve_type}'")
    else:
        value: object = parse_sienna_schema_union(kinds=(kind,), data=nested_value)
    return SiennaValueCurve(value=value)


def sienna_value_curve_to_json(value: SiennaValueCurve) -> dict[str, Any]:
    """Write every ValueCurve slot to explicit schema property names.

    :param value: Typed ValueCurve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'value': write_sienna_schema_union(
        kinds=(SiennaObjectKind.InputOutputCurve, SiennaObjectKind.IncrementalCurve,
               SiennaObjectKind.AverageRateCurve, SiennaObjectKind.TimeSeriesInputOutputCurve,
               SiennaObjectKind.TimeSeriesIncrementalCurve, SiennaObjectKind.TimeSeriesAverageRateCurve),
        value=value.value)}
