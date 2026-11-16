# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TimeSeriesFeatures schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTimeSeriesFeatures(SiennaSchemaModel):
    """Expose every declared TimeSeriesFeatures property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: dict[str, object]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: dict[str, object] = value


def parse_sienna_time_series_features(data: dict[str, Any]) -> SiennaTimeSeriesFeatures:
    """Parse declared TimeSeriesFeatures properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TimeSeriesFeatures object.
    """
    return SiennaTimeSeriesFeatures(value=data.get('value', None))


def sienna_time_series_features_to_json(value: SiennaTimeSeriesFeatures) -> dict[str, Any]:
    """Write every TimeSeriesFeatures slot to explicit schema property names.

    :param value: Typed TimeSeriesFeatures object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
