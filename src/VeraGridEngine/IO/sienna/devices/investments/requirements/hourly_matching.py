# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HourlyMatching schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHourlyMatching(SiennaSchemaModel):
    """Expose every declared HourlyMatching property through fixed slots."""

    __slots__ = ('id', 'name', 'available',)

    def __init__(self, id: int, name: str, available: bool) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available


def parse_sienna_hourly_matching(data: dict[str, Any]) -> SiennaHourlyMatching:
    """Parse declared HourlyMatching properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HourlyMatching object.
    """
    return SiennaHourlyMatching(id=get_required_value(data, 'id', 'HourlyMatching'), name=get_required_value(data, 'name', 'HourlyMatching'), available=get_required_value(data, 'available', 'HourlyMatching'))


def sienna_hourly_matching_to_json(value: SiennaHourlyMatching) -> dict[str, Any]:
    """Write every HourlyMatching slot to explicit schema property names.

    :param value: Typed HourlyMatching object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name, 'available': value.available}
