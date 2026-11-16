# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ServiceAssociation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaServiceAssociation(SiennaSchemaModel):
    """Expose every declared ServiceAssociation property through fixed slots."""

    __slots__ = ('service_id', 'entity_id',)

    def __init__(self, service_id: int, entity_id: int) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.service_id: int = service_id
        self.entity_id: int = entity_id


def parse_sienna_service_association(data: dict[str, Any]) -> SiennaServiceAssociation:
    """Parse declared ServiceAssociation properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ServiceAssociation object.
    """
    return SiennaServiceAssociation(service_id=get_required_value(data, 'service_id', 'ServiceAssociation'), entity_id=get_required_value(data, 'entity_id', 'ServiceAssociation'))


def sienna_service_association_to_json(value: SiennaServiceAssociation) -> dict[str, Any]:
    """Write every ServiceAssociation slot to explicit schema property names.

    :param value: Typed ServiceAssociation object.
    :return: JSON object with declared schema properties.
    """
    return {'service_id': value.service_id, 'entity_id': value.entity_id}
