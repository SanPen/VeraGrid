# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ReactivePowerSharing schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaReactivePowerSharing(SiennaSchemaModel):
    """Expose every declared ReactivePowerSharing property through fixed slots."""

    __slots__ = ('id', 'name',)

    def __init__(self, id: int, name: str) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name


def parse_sienna_reactive_power_sharing(data: dict[str, Any]) -> SiennaReactivePowerSharing:
    """Parse declared ReactivePowerSharing properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ReactivePowerSharing object.
    """
    return SiennaReactivePowerSharing(id=get_required_value(data, 'id', 'ReactivePowerSharing'), name=get_required_value(data, 'name', 'ReactivePowerSharing'))


def sienna_reactive_power_sharing_to_json(value: SiennaReactivePowerSharing) -> dict[str, Any]:
    """Write every ReactivePowerSharing slot to explicit schema property names.

    :param value: Typed ReactivePowerSharing object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name}
