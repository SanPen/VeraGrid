# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CapacityReserveMargin schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCapacityReserveMargin(SiennaSchemaModel):
    """Expose every declared CapacityReserveMargin property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'target_year', 'capacity_reserve_fraction',)

    def __init__(self, id: int, name: str, available: bool, target_year: int, capacity_reserve_fraction: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.target_year: int = target_year
        self.capacity_reserve_fraction: float = capacity_reserve_fraction


def parse_sienna_capacity_reserve_margin(data: dict[str, Any]) -> SiennaCapacityReserveMargin:
    """Parse declared CapacityReserveMargin properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed CapacityReserveMargin object.
    """
    return SiennaCapacityReserveMargin(id=get_required_value(data, 'id', 'CapacityReserveMargin'), name=get_required_value(data, 'name', 'CapacityReserveMargin'), available=get_required_value(data, 'available', 'CapacityReserveMargin'), target_year=data.get('target_year', None), capacity_reserve_fraction=data.get('capacity_reserve_fraction', None))


def sienna_capacity_reserve_margin_to_json(value: SiennaCapacityReserveMargin) -> dict[str, Any]:
    """Write every CapacityReserveMargin slot to explicit schema property names.

    :param value: Typed CapacityReserveMargin object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name, 'available': value.available, 'target_year': value.target_year, 'capacity_reserve_fraction': value.capacity_reserve_fraction}
