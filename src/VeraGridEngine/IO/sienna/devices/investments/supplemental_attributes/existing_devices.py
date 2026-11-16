# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ExistingDevices schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaExistingDevices(SiennaSchemaModel):
    """Expose every declared ExistingDevices property through fixed slots."""

    __slots__ = ('id', 'existing_devices',)

    def __init__(self, id: int, existing_devices: list[str]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.existing_devices: list[str] = existing_devices


def parse_sienna_existing_devices(data: dict[str, Any]) -> SiennaExistingDevices:
    """Parse declared ExistingDevices properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ExistingDevices object.
    """
    return SiennaExistingDevices(id=get_required_value(data, 'id', 'ExistingDevices'), existing_devices=data.get('existing_devices', None))


def sienna_existing_devices_to_json(value: SiennaExistingDevices) -> dict[str, Any]:
    """Write every ExistingDevices slot to explicit schema property names.

    :param value: Typed ExistingDevices object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'existing_devices': value.existing_devices}
