# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AVRSimple schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAVRSimple(SiennaSchemaModel):
    """Expose every declared AVRSimple property through fixed slots."""

    __slots__ = ('id', 'Kv', 'V_ref',)

    def __init__(self, id: int, Kv: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Kv: float = Kv
        self.V_ref: float = V_ref


def parse_sienna_avr_simple(data: dict[str, Any]) -> SiennaAVRSimple:
    """Parse declared AVRSimple properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed AVRSimple object.
    """
    return SiennaAVRSimple(id=get_required_value(data, 'id', 'AVRSimple'), Kv=get_required_value(data, 'Kv', 'AVRSimple'), V_ref=data.get('V_ref', None))


def sienna_avr_simple_to_json(value: SiennaAVRSimple) -> dict[str, Any]:
    """Write every AVRSimple slot to explicit schema property names.

    :param value: Typed AVRSimple object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'Kv': value.Kv, 'V_ref': value.V_ref}
