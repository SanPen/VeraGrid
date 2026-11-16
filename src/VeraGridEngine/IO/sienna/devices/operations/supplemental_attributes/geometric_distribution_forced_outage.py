# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna GeometricDistributionForcedOutage schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaGeometricDistributionForcedOutage(SiennaSchemaModel):
    """Expose every declared GeometricDistributionForcedOutage property through fixed slots."""

    __slots__ = ('id', 'mean_time_to_recovery', 'outage_transition_probability', 'monitored_components', 'identifier',)

    def __init__(self, id: int, mean_time_to_recovery: float, outage_transition_probability: float, monitored_components: list[int], identifier: str | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.mean_time_to_recovery: float = mean_time_to_recovery
        self.outage_transition_probability: float = outage_transition_probability
        self.monitored_components: list[int] = monitored_components
        self.identifier: str | None = identifier


def parse_sienna_geometric_distribution_forced_outage(data: dict[str, Any]) -> SiennaGeometricDistributionForcedOutage:
    """Parse declared GeometricDistributionForcedOutage properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed GeometricDistributionForcedOutage object.
    """
    return SiennaGeometricDistributionForcedOutage(id=get_required_value(data, 'id', 'GeometricDistributionForcedOutage'), mean_time_to_recovery=data.get('mean_time_to_recovery', None), outage_transition_probability=data.get('outage_transition_probability', None), monitored_components=data.get('monitored_components', None), identifier=data.get('identifier', None))


def sienna_geometric_distribution_forced_outage_to_json(value: SiennaGeometricDistributionForcedOutage) -> dict[str, Any]:
    """Write every GeometricDistributionForcedOutage slot to explicit schema property names.

    :param value: Typed GeometricDistributionForcedOutage object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'mean_time_to_recovery': value.mean_time_to_recovery, 'outage_transition_probability': value.outage_transition_probability, 'monitored_components': value.monitored_components, 'identifier': value.identifier}
