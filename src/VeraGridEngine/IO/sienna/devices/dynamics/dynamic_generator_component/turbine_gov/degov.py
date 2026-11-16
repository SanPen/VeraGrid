# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna DEGOV schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaDEGOV(SiennaSchemaModel):
    """Expose every declared DEGOV property through fixed slots."""

    __slots__ = ('id', 'T1', 'T2', 'T3', 'K', 'T4', 'T5', 'T6', 'Td', 'P_ref',)

    def __init__(self, id: int, T1: float, T2: float, T3: float, K: float, T4: float, T5: float, T6: float, Td: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.T1: float = T1
        self.T2: float = T2
        self.T3: float = T3
        self.K: float = K
        self.T4: float = T4
        self.T5: float = T5
        self.T6: float = T6
        self.Td: float = Td
        self.P_ref: float = P_ref


def parse_sienna_degov(data: dict[str, Any]) -> SiennaDEGOV:
    """Parse declared DEGOV properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed DEGOV object.
    """
    return SiennaDEGOV(id=get_required_value(data, 'id', 'DEGOV'), T1=get_required_value(data, 'T1', 'DEGOV'), T2=get_required_value(data, 'T2', 'DEGOV'), T3=get_required_value(data, 'T3', 'DEGOV'), K=get_required_value(data, 'K', 'DEGOV'), T4=get_required_value(data, 'T4', 'DEGOV'), T5=get_required_value(data, 'T5', 'DEGOV'), T6=get_required_value(data, 'T6', 'DEGOV'), Td=get_required_value(data, 'Td', 'DEGOV'), P_ref=data.get('P_ref', None))


def sienna_degov_to_json(value: SiennaDEGOV) -> dict[str, Any]:
    """Write every DEGOV slot to explicit schema property names.

    :param value: Typed DEGOV object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'T1': value.T1, 'T2': value.T2, 'T3': value.T3, 'K': value.K, 'T4': value.T4, 'T5': value.T5, 'T6': value.T6, 'Td': value.Td, 'P_ref': value.P_ref}
