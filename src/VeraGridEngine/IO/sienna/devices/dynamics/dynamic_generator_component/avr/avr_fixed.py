# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AVRFixed schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAVRFixed(SiennaSchemaModel):
    """Expose every declared AVRFixed property through fixed slots."""

    __slots__ = ('id', 'Vf', 'V_ref',)

    def __init__(self, id: int, Vf: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Vf: float = Vf
        self.V_ref: float = V_ref


def parse_sienna_avr_fixed(data: dict[str, Any]) -> SiennaAVRFixed:
    """Parse declared AVRFixed properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed AVRFixed object.
    """
    return SiennaAVRFixed(id=get_required_value(data, 'id', 'AVRFixed'), Vf=get_required_value(data, 'Vf', 'AVRFixed'), V_ref=data.get('V_ref', None))


def sienna_avr_fixed_to_json(value: SiennaAVRFixed) -> dict[str, Any]:
    """Write every AVRFixed slot to explicit schema property names.

    :param value: Typed AVRFixed object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'Vf': value.Vf, 'V_ref': value.V_ref}
