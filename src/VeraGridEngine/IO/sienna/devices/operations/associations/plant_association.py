# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PlantAssociation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPlantAssociation(SiennaSchemaModel):
    """Expose every declared PlantAssociation property through fixed slots."""

    __slots__ = ('plant_id', 'entity_id', 'group_index',)

    def __init__(self, plant_id: int, entity_id: int, group_index: int) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.plant_id: int = plant_id
        self.entity_id: int = entity_id
        self.group_index: int = group_index


def parse_sienna_plant_association(data: dict[str, Any]) -> SiennaPlantAssociation:
    """Parse declared PlantAssociation properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PlantAssociation object.
    """
    return SiennaPlantAssociation(plant_id=get_required_value(data, 'plant_id', 'PlantAssociation'), entity_id=get_required_value(data, 'entity_id', 'PlantAssociation'), group_index=get_required_value(data, 'group_index', 'PlantAssociation'))


def sienna_plant_association_to_json(value: SiennaPlantAssociation) -> dict[str, Any]:
    """Write every PlantAssociation slot to explicit schema property names.

    :param value: Typed PlantAssociation object.
    :return: JSON object with declared schema properties.
    """
    return {'plant_id': value.plant_id, 'entity_id': value.entity_id, 'group_index': value.group_index}
