# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EnergyShareRequirements schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEnergyShareRequirements(SiennaSchemaModel):
    """Expose every declared EnergyShareRequirements property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'target_year', 'generation_fraction_requirement',)

    def __init__(self, id: int, name: str, available: bool, target_year: int, generation_fraction_requirement: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.target_year: int = target_year
        self.generation_fraction_requirement: float = generation_fraction_requirement


def parse_sienna_energy_share_requirements(data: dict[str, Any]) -> SiennaEnergyShareRequirements:
    """Parse declared EnergyShareRequirements properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed EnergyShareRequirements object.
    """
    return SiennaEnergyShareRequirements(id=get_required_value(data, 'id', 'EnergyShareRequirements'), name=get_required_value(data, 'name', 'EnergyShareRequirements'), available=get_required_value(data, 'available', 'EnergyShareRequirements'), target_year=data.get('target_year', None), generation_fraction_requirement=data.get('generation_fraction_requirement', None))


def sienna_energy_share_requirements_to_json(value: SiennaEnergyShareRequirements) -> dict[str, Any]:
    """Write every EnergyShareRequirements slot to explicit schema property names.

    :param value: Typed EnergyShareRequirements object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name, 'available': value.available, 'target_year': value.target_year, 'generation_fraction_requirement': value.generation_fraction_requirement}
