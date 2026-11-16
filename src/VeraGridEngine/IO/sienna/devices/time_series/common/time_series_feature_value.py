# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TimeSeriesFeatureValue schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTimeSeriesFeatureValue(SiennaSchemaModel):
    """Expose every declared TimeSeriesFeatureValue property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: str | int | float | bool | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: str | int | float | bool | None = value


def parse_sienna_time_series_feature_value(data: dict[str, Any]) -> SiennaTimeSeriesFeatureValue:
    """Parse declared TimeSeriesFeatureValue properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TimeSeriesFeatureValue object.
    """
    return SiennaTimeSeriesFeatureValue(value=data.get('value', None))


def sienna_time_series_feature_value_to_json(value: SiennaTimeSeriesFeatureValue) -> dict[str, Any]:
    """Write every TimeSeriesFeatureValue slot to explicit schema property names.

    :param value: Typed TimeSeriesFeatureValue object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
