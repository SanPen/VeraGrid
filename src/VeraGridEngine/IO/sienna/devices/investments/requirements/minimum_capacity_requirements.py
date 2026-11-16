# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna MinimumCapacityRequirements schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaMinimumCapacityRequirements(SiennaSchemaModel):
    """Expose every declared MinimumCapacityRequirements property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'target_year', 'min_capacity_mw',)

    def __init__(self, id: int, name: str, available: bool, target_year: int, min_capacity_mw: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.target_year: int = target_year
        self.min_capacity_mw: float = min_capacity_mw


def parse_sienna_minimum_capacity_requirements(data: dict[str, Any]) -> SiennaMinimumCapacityRequirements:
    """Parse declared MinimumCapacityRequirements properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed MinimumCapacityRequirements object.
    """
    return SiennaMinimumCapacityRequirements(id=get_required_value(data, 'id', 'MinimumCapacityRequirements'), name=get_required_value(data, 'name', 'MinimumCapacityRequirements'), available=get_required_value(data, 'available', 'MinimumCapacityRequirements'), target_year=data.get('target_year', None), min_capacity_mw=data.get('min_capacity_mw', None))


def sienna_minimum_capacity_requirements_to_json(value: SiennaMinimumCapacityRequirements) -> dict[str, Any]:
    """Write every MinimumCapacityRequirements slot to explicit schema property names.

    :param value: Typed MinimumCapacityRequirements object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name, 'available': value.available, 'target_year': value.target_year, 'min_capacity_mw': value.min_capacity_mw}
