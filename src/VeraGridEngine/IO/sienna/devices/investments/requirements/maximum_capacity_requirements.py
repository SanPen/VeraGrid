# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna MaximumCapacityRequirements schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaMaximumCapacityRequirements(SiennaSchemaModel):
    """Expose every declared MaximumCapacityRequirements property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'target_year', 'max_capacity_mw',)

    def __init__(self, id: int, name: str, available: bool, target_year: int, max_capacity_mw: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.target_year: int = target_year
        self.max_capacity_mw: float = max_capacity_mw


def parse_sienna_maximum_capacity_requirements(data: dict[str, Any]) -> SiennaMaximumCapacityRequirements:
    """Parse declared MaximumCapacityRequirements properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed MaximumCapacityRequirements object.
    """
    return SiennaMaximumCapacityRequirements(id=get_required_value(data, 'id', 'MaximumCapacityRequirements'), name=get_required_value(data, 'name', 'MaximumCapacityRequirements'), available=get_required_value(data, 'available', 'MaximumCapacityRequirements'), target_year=data.get('target_year', None), max_capacity_mw=data.get('max_capacity_mw', None))


def sienna_maximum_capacity_requirements_to_json(value: SiennaMaximumCapacityRequirements) -> dict[str, Any]:
    """Write every MaximumCapacityRequirements slot to explicit schema property names.

    :param value: Typed MaximumCapacityRequirements object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name, 'available': value.available, 'target_year': value.target_year, 'max_capacity_mw': value.max_capacity_mw}
