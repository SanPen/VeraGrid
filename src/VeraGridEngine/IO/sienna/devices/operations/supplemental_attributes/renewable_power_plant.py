# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RenewablePowerPlant schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRenewablePowerPlant(SiennaSchemaModel):
    """Expose every declared RenewablePowerPlant property through fixed slots."""

    __slots__ = ('id', 'name',)

    def __init__(self, id: int, name: str) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name


def parse_sienna_renewable_power_plant(data: dict[str, Any]) -> SiennaRenewablePowerPlant:
    """Parse declared RenewablePowerPlant properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RenewablePowerPlant object.
    """
    return SiennaRenewablePowerPlant(id=get_required_value(data, 'id', 'RenewablePowerPlant'), name=get_required_value(data, 'name', 'RenewablePowerPlant'))


def sienna_renewable_power_plant_to_json(value: SiennaRenewablePowerPlant) -> dict[str, Any]:
    """Write every RenewablePowerPlant slot to explicit schema property names.

    :param value: Typed RenewablePowerPlant object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name}
