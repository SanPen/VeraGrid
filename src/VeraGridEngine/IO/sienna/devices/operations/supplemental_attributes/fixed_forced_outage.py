# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FixedForcedOutage schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFixedForcedOutage(SiennaSchemaModel):
    """Expose every declared FixedForcedOutage property through fixed slots."""

    __slots__ = ('id', 'outage_status', 'monitored_components', 'identifier',)

    def __init__(self, id: int, outage_status: float, monitored_components: list[int], identifier: str | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.outage_status: float = outage_status
        self.monitored_components: list[int] = monitored_components
        self.identifier: str | None = identifier


def parse_sienna_fixed_forced_outage(data: dict[str, Any]) -> SiennaFixedForcedOutage:
    """Parse declared FixedForcedOutage properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FixedForcedOutage object.
    """
    return SiennaFixedForcedOutage(id=get_required_value(data, 'id', 'FixedForcedOutage'), outage_status=get_required_value(data, 'outage_status', 'FixedForcedOutage'), monitored_components=data.get('monitored_components', None), identifier=data.get('identifier', None))


def sienna_fixed_forced_outage_to_json(value: SiennaFixedForcedOutage) -> dict[str, Any]:
    """Write every FixedForcedOutage slot to explicit schema property names.

    :param value: Typed FixedForcedOutage object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'outage_status': value.outage_status, 'monitored_components': value.monitored_components, 'identifier': value.identifier}
