# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CombinedCycleAssociation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCombinedCycleAssociation(SiennaSchemaModel):
    """Expose every declared CombinedCycleAssociation property through fixed slots."""

    __slots__ = ('plant_id', 'entity_id', 'role', 'hrsg_index',)

    def __init__(self, plant_id: int, entity_id: int, role: str, hrsg_index: int) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.plant_id: int = plant_id
        self.entity_id: int = entity_id
        self.role: str = role
        self.hrsg_index: int = hrsg_index


def parse_sienna_combined_cycle_association(data: dict[str, Any]) -> SiennaCombinedCycleAssociation:
    """Parse declared CombinedCycleAssociation properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed CombinedCycleAssociation object.
    """
    return SiennaCombinedCycleAssociation(plant_id=get_required_value(data, 'plant_id', 'CombinedCycleAssociation'), entity_id=get_required_value(data, 'entity_id', 'CombinedCycleAssociation'), role=get_required_value(data, 'role', 'CombinedCycleAssociation'), hrsg_index=get_required_value(data, 'hrsg_index', 'CombinedCycleAssociation'))


def sienna_combined_cycle_association_to_json(value: SiennaCombinedCycleAssociation) -> dict[str, Any]:
    """Write every CombinedCycleAssociation slot to explicit schema property names.

    :param value: Typed CombinedCycleAssociation object.
    :return: JSON object with declared schema properties.
    """
    return {'plant_id': value.plant_id, 'entity_id': value.entity_id, 'role': value.role, 'hrsg_index': value.hrsg_index}
