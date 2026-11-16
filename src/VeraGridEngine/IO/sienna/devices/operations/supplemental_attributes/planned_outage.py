# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PlannedOutage schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPlannedOutage(SiennaSchemaModel):
    """Expose every declared PlannedOutage property through fixed slots."""

    __slots__ = ('id', 'outage_schedule', 'monitored_components', 'identifier',)

    def __init__(self, id: int, outage_schedule: str, monitored_components: list[int], identifier: str | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.outage_schedule: str = outage_schedule
        self.monitored_components: list[int] = monitored_components
        self.identifier: str | None = identifier


def parse_sienna_planned_outage(data: dict[str, Any]) -> SiennaPlannedOutage:
    """Parse declared PlannedOutage properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PlannedOutage object.
    """
    return SiennaPlannedOutage(id=get_required_value(data, 'id', 'PlannedOutage'), outage_schedule=get_required_value(data, 'outage_schedule', 'PlannedOutage'), monitored_components=data.get('monitored_components', None), identifier=data.get('identifier', None))


def sienna_planned_outage_to_json(value: SiennaPlannedOutage) -> dict[str, Any]:
    """Write every PlannedOutage slot to explicit schema property names.

    :param value: Typed PlannedOutage object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'outage_schedule': value.outage_schedule, 'monitored_components': value.monitored_components, 'identifier': value.identifier}
