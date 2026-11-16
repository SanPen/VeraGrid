# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna Substation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSubstation(SiennaSchemaModel):
    """Expose every declared Substation property through fixed slots."""

    __slots__ = ('id', 'name', 'number', 'grounding_resistance',)

    def __init__(self, id: int, name: str, number: int, grounding_resistance: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.number: int = number
        self.grounding_resistance: float = grounding_resistance


def parse_sienna_substation(data: dict[str, Any]) -> SiennaSubstation:
    """Parse declared Substation properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed Substation object.
    """
    return SiennaSubstation(id=get_required_value(data, 'id', 'Substation'), name=get_required_value(data, 'name', 'Substation'), number=get_required_value(data, 'number', 'Substation'), grounding_resistance=get_required_value(data, 'grounding_resistance', 'Substation'))


def sienna_substation_to_json(value: SiennaSubstation) -> dict[str, Any]:
    """Write every Substation slot to explicit schema property names.

    :param value: Typed Substation object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name, 'number': value.number, 'grounding_resistance': value.grounding_resistance}
