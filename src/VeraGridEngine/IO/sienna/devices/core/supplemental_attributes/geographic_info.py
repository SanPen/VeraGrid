# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna GeographicInfo schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaGeographicInfo(SiennaSchemaModel):
    """Expose every declared GeographicInfo property through fixed slots."""

    __slots__ = ('id', 'geo_json',)

    def __init__(self, id: int, geo_json: dict[str, object]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.geo_json: dict[str, object] = geo_json


def parse_sienna_geographic_info(data: dict[str, Any]) -> SiennaGeographicInfo:
    """Parse declared GeographicInfo properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed GeographicInfo object.
    """
    return SiennaGeographicInfo(id=get_required_value(data, 'id', 'GeographicInfo'), geo_json=get_required_value(data, 'geo_json', 'GeographicInfo'))


def sienna_geographic_info_to_json(value: SiennaGeographicInfo) -> dict[str, Any]:
    """Write every GeographicInfo slot to explicit schema property names.

    :param value: Typed GeographicInfo object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'geo_json': value.geo_json}
