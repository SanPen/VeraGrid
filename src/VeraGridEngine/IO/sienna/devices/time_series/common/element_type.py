# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ElementType schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaElementType(SiennaSchemaModel):
    """Expose every declared ElementType property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: str) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: str = value


def parse_sienna_element_type(data: dict[str, Any]) -> SiennaElementType:
    """Parse declared ElementType properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ElementType object.
    """
    return SiennaElementType(value=data.get('value', None))


def sienna_element_type_to_json(value: SiennaElementType) -> dict[str, Any]:
    """Write every ElementType slot to explicit schema property names.

    :param value: Typed ElementType object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
