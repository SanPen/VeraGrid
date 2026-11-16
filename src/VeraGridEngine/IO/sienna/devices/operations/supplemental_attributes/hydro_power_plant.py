# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HydroPowerPlant schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHydroPowerPlant(SiennaSchemaModel):
    """Expose every declared HydroPowerPlant property through fixed slots."""

    __slots__ = ('id', 'name',)

    def __init__(self, id: int, name: str) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name


def parse_sienna_hydro_power_plant(data: dict[str, Any]) -> SiennaHydroPowerPlant:
    """Parse declared HydroPowerPlant properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HydroPowerPlant object.
    """
    return SiennaHydroPowerPlant(id=get_required_value(data, 'id', 'HydroPowerPlant'), name=get_required_value(data, 'name', 'HydroPowerPlant'))


def sienna_hydro_power_plant_to_json(value: SiennaHydroPowerPlant) -> dict[str, Any]:
    """Write every HydroPowerPlant slot to explicit schema property names.

    :param value: Typed HydroPowerPlant object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name}
