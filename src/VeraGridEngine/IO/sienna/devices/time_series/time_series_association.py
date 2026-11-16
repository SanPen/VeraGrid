# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TimeSeriesAssociation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.time_series.deterministic import SiennaDeterministic
    from VeraGridEngine.IO.sienna.devices.time_series.deterministic_single_time_series import SiennaDeterministicSingleTimeSeries
    from VeraGridEngine.IO.sienna.devices.time_series.non_sequential_time_series import SiennaNonSequentialTimeSeries
    from VeraGridEngine.IO.sienna.devices.time_series.probabilistic import SiennaProbabilistic
    from VeraGridEngine.IO.sienna.devices.time_series.scenarios import SiennaScenarios
    from VeraGridEngine.IO.sienna.devices.time_series.single_time_series import SiennaSingleTimeSeries

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTimeSeriesAssociation(SiennaSchemaModel):
    """Expose every declared TimeSeriesAssociation property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: SiennaSingleTimeSeries | SiennaNonSequentialTimeSeries | SiennaDeterministic | SiennaDeterministicSingleTimeSeries | SiennaProbabilistic | SiennaScenarios) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: SiennaSingleTimeSeries | SiennaNonSequentialTimeSeries | SiennaDeterministic | SiennaDeterministicSingleTimeSeries | SiennaProbabilistic | SiennaScenarios = value


def parse_sienna_time_series_association(data: dict[str, Any]) -> SiennaTimeSeriesAssociation:
    """Parse declared TimeSeriesAssociation properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TimeSeriesAssociation object.
    """
    return SiennaTimeSeriesAssociation(value=data.get('value', None))


def sienna_time_series_association_to_json(value: SiennaTimeSeriesAssociation) -> dict[str, Any]:
    """Write every TimeSeriesAssociation slot to explicit schema property names.

    :param value: Typed TimeSeriesAssociation object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
