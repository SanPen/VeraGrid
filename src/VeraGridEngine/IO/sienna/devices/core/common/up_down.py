# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna UpDown schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaUpDown(SiennaSchemaModel):
    """Expose every declared UpDown property through fixed slots."""

    __slots__ = ('down', 'up',)

    def __init__(self, down: float, up: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.down: float = down
        self.up: float = up


def parse_sienna_up_down(data: dict[str, Any]) -> SiennaUpDown:
    """Parse declared UpDown properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed UpDown object.
    """
    return SiennaUpDown(down=get_required_value(data, 'down', 'UpDown'), up=get_required_value(data, 'up', 'UpDown'))


def sienna_up_down_to_json(value: SiennaUpDown) -> dict[str, Any]:
    """Write every UpDown slot to explicit schema property names.

    :param value: Typed UpDown object.
    :return: JSON object with declared schema properties.
    """
    return {'down': value.down, 'up': value.up}
