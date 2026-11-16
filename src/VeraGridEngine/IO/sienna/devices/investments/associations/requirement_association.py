# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RequirementAssociation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRequirementAssociation(SiennaSchemaModel):
    """Expose every declared RequirementAssociation property through fixed slots."""

    __slots__ = ('requirement_id', 'entity_id',)

    def __init__(self, requirement_id: int, entity_id: int) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.requirement_id: int = requirement_id
        self.entity_id: int = entity_id


def parse_sienna_requirement_association(data: dict[str, Any]) -> SiennaRequirementAssociation:
    """Parse declared RequirementAssociation properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RequirementAssociation object.
    """
    return SiennaRequirementAssociation(requirement_id=get_required_value(data, 'requirement_id', 'RequirementAssociation'), entity_id=get_required_value(data, 'entity_id', 'RequirementAssociation'))


def sienna_requirement_association_to_json(value: SiennaRequirementAssociation) -> dict[str, Any]:
    """Write every RequirementAssociation slot to explicit schema property names.

    :param value: Typed RequirementAssociation object.
    :return: JSON object with declared schema properties.
    """
    return {'requirement_id': value.requirement_id, 'entity_id': value.entity_id}
