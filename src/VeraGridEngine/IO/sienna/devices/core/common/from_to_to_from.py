# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FromTo_ToFrom schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFromTo_ToFrom(SiennaSchemaModel):
    """Expose every declared FromTo_ToFrom property through fixed slots."""

    __slots__ = ('from_to', 'to_from',)

    def __init__(self, from_to: float, to_from: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.from_to: float = from_to
        self.to_from: float = to_from


def parse_sienna_from_to_to_from(data: dict[str, Any]) -> SiennaFromTo_ToFrom:
    """Parse declared FromTo_ToFrom properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FromTo_ToFrom object.
    """
    return SiennaFromTo_ToFrom(from_to=data.get('from_to', None), to_from=data.get('to_from', None))


def sienna_from_to_to_from_to_json(value: SiennaFromTo_ToFrom) -> dict[str, Any]:
    """Write every FromTo_ToFrom slot to explicit schema property names.

    :param value: Typed FromTo_ToFrom object.
    :return: JSON object with declared schema properties.
    """
    return {'from_to': value.from_to, 'to_from': value.to_from}
