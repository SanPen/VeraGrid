# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FromTo schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFromTo(SiennaSchemaModel):
    """Expose every declared FromTo property through fixed slots."""

    __slots__ = ('from_', 'to',)

    def __init__(self, from_: float, to: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.from_: float = from_
        self.to: float = to


def parse_sienna_from_to(data: dict[str, Any]) -> SiennaFromTo:
    """Parse declared FromTo properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FromTo object.
    """
    return SiennaFromTo(from_=data.get('from', None), to=data.get('to', None))


def sienna_from_to_to_json(value: SiennaFromTo) -> dict[str, Any]:
    """Write every FromTo slot to explicit schema property names.

    :param value: Typed FromTo object.
    :return: JSON object with declared schema properties.
    """
    return {'from': value.from_, 'to': value.to}
