# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna VirtualInertia schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaVirtualInertia(SiennaSchemaModel):
    """Expose every declared VirtualInertia property through fixed slots."""

    __slots__ = ('Ta', 'kd', 'komega', 'P_ref',)

    def __init__(self, Ta: float, kd: float, komega: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.Ta: float = Ta
        self.kd: float = kd
        self.komega: float = komega
        self.P_ref: float = P_ref


def parse_sienna_virtual_inertia(data: dict[str, Any]) -> SiennaVirtualInertia:
    """Parse declared VirtualInertia properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed VirtualInertia object.
    """
    return SiennaVirtualInertia(Ta=get_required_value(data, 'Ta', 'VirtualInertia'), kd=get_required_value(data, 'kd', 'VirtualInertia'), komega=get_required_value(data, 'komega', 'VirtualInertia'), P_ref=data.get('P_ref', None))


def sienna_virtual_inertia_to_json(value: SiennaVirtualInertia) -> dict[str, Any]:
    """Write every VirtualInertia slot to explicit schema property names.

    :param value: Typed VirtualInertia object.
    :return: JSON object with declared schema properties.
    """
    return {'Ta': value.Ta, 'kd': value.kd, 'komega': value.komega, 'P_ref': value.P_ref}
