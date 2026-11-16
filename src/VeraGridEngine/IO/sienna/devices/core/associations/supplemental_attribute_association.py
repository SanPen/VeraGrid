# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SupplementalAttributeAssociation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSupplementalAttributeAssociation(SiennaSchemaModel):
    """Expose every declared SupplementalAttributeAssociation property through fixed slots."""

    __slots__ = ('component_id', 'component_type', 'attribute_id', 'attribute_type',)

    def __init__(self, component_id: int, component_type: str, attribute_id: int, attribute_type: str) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.component_id: int = component_id
        self.component_type: str = component_type
        self.attribute_id: int = attribute_id
        self.attribute_type: str = attribute_type


def parse_sienna_supplemental_attribute_association(data: dict[str, Any]) -> SiennaSupplementalAttributeAssociation:
    """Parse declared SupplementalAttributeAssociation properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SupplementalAttributeAssociation object.
    """
    return SiennaSupplementalAttributeAssociation(component_id=get_required_value(data, 'component_id', 'SupplementalAttributeAssociation'), component_type=get_required_value(data, 'component_type', 'SupplementalAttributeAssociation'), attribute_id=get_required_value(data, 'attribute_id', 'SupplementalAttributeAssociation'), attribute_type=get_required_value(data, 'attribute_type', 'SupplementalAttributeAssociation'))


def sienna_supplemental_attribute_association_to_json(value: SiennaSupplementalAttributeAssociation) -> dict[str, Any]:
    """Write every SupplementalAttributeAssociation slot to explicit schema property names.

    :param value: Typed SupplementalAttributeAssociation object.
    :return: JSON object with declared schema properties.
    """
    return {'component_id': value.component_id, 'component_type': value.component_type, 'attribute_id': value.attribute_id, 'attribute_type': value.attribute_type}
