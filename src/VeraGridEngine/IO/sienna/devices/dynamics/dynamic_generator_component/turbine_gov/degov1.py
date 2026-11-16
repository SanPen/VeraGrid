# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna DEGOV1 schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaDEGOV1(SiennaSchemaModel):
    """Expose every declared DEGOV1 property through fixed slots."""

    __slots__ = ('id', 'droop_flag', 'T1', 'T2', 'T3', 'K', 'T4', 'T5', 'T6', 'Td', 'T_lim', 'R', 'Te', 'P_ref',)

    def __init__(self, id: int, droop_flag: int, T1: float, T2: float, T3: float, K: float, T4: float, T5: float, T6: float, Td: float, T_lim: list[float], R: float, Te: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.droop_flag: int = droop_flag
        self.T1: float = T1
        self.T2: float = T2
        self.T3: float = T3
        self.K: float = K
        self.T4: float = T4
        self.T5: float = T5
        self.T6: float = T6
        self.Td: float = Td
        self.T_lim: list[float] = T_lim
        self.R: float = R
        self.Te: float = Te
        self.P_ref: float = P_ref


def parse_sienna_degov1(data: dict[str, Any]) -> SiennaDEGOV1:
    """Parse declared DEGOV1 properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed DEGOV1 object.
    """
    return SiennaDEGOV1(id=get_required_value(data, 'id', 'DEGOV1'), droop_flag=data.get('droop_flag', None), T1=get_required_value(data, 'T1', 'DEGOV1'), T2=get_required_value(data, 'T2', 'DEGOV1'), T3=get_required_value(data, 'T3', 'DEGOV1'), K=get_required_value(data, 'K', 'DEGOV1'), T4=get_required_value(data, 'T4', 'DEGOV1'), T5=get_required_value(data, 'T5', 'DEGOV1'), T6=get_required_value(data, 'T6', 'DEGOV1'), Td=get_required_value(data, 'Td', 'DEGOV1'), T_lim=get_required_value(data, 'T_lim', 'DEGOV1'), R=get_required_value(data, 'R', 'DEGOV1'), Te=get_required_value(data, 'Te', 'DEGOV1'), P_ref=data.get('P_ref', None))


def sienna_degov1_to_json(value: SiennaDEGOV1) -> dict[str, Any]:
    """Write every DEGOV1 slot to explicit schema property names.

    :param value: Typed DEGOV1 object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'droop_flag': value.droop_flag, 'T1': value.T1, 'T2': value.T2, 'T3': value.T3, 'K': value.K, 'T4': value.T4, 'T5': value.T5, 'T6': value.T6, 'Td': value.Td, 'T_lim': value.T_lim, 'R': value.R, 'Te': value.Te, 'P_ref': value.P_ref}
