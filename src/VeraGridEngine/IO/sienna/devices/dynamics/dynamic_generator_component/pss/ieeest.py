# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna IEEEST schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaIEEEST(SiennaSchemaModel):
    """Expose every declared IEEEST property through fixed slots."""

    __slots__ = ('id', 'input_code', 'remote_bus_control', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'Ks', 'Ls_lim', 'Vcu', 'Vcl',)

    def __init__(self, id: int, input_code: int, remote_bus_control: int, A1: float, A2: float, A3: float, A4: float, A5: float, A6: float, T1: float, T2: float, T3: float, T4: float, T5: float, T6: float, Ks: float, Ls_lim: list[float], Vcu: float, Vcl: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.input_code: int = input_code
        self.remote_bus_control: int = remote_bus_control
        self.A1: float = A1
        self.A2: float = A2
        self.A3: float = A3
        self.A4: float = A4
        self.A5: float = A5
        self.A6: float = A6
        self.T1: float = T1
        self.T2: float = T2
        self.T3: float = T3
        self.T4: float = T4
        self.T5: float = T5
        self.T6: float = T6
        self.Ks: float = Ks
        self.Ls_lim: list[float] = Ls_lim
        self.Vcu: float = Vcu
        self.Vcl: float = Vcl


def parse_sienna_ieeest(data: dict[str, Any]) -> SiennaIEEEST:
    """Parse declared IEEEST properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed IEEEST object.
    """
    return SiennaIEEEST(id=get_required_value(data, 'id', 'IEEEST'), input_code=get_required_value(data, 'input_code', 'IEEEST'), remote_bus_control=get_required_value(data, 'remote_bus_control', 'IEEEST'), A1=get_required_value(data, 'A1', 'IEEEST'), A2=get_required_value(data, 'A2', 'IEEEST'), A3=get_required_value(data, 'A3', 'IEEEST'), A4=get_required_value(data, 'A4', 'IEEEST'), A5=get_required_value(data, 'A5', 'IEEEST'), A6=get_required_value(data, 'A6', 'IEEEST'), T1=get_required_value(data, 'T1', 'IEEEST'), T2=get_required_value(data, 'T2', 'IEEEST'), T3=get_required_value(data, 'T3', 'IEEEST'), T4=get_required_value(data, 'T4', 'IEEEST'), T5=get_required_value(data, 'T5', 'IEEEST'), T6=get_required_value(data, 'T6', 'IEEEST'), Ks=get_required_value(data, 'Ks', 'IEEEST'), Ls_lim=get_required_value(data, 'Ls_lim', 'IEEEST'), Vcu=get_required_value(data, 'Vcu', 'IEEEST'), Vcl=get_required_value(data, 'Vcl', 'IEEEST'))


def sienna_ieeest_to_json(value: SiennaIEEEST) -> dict[str, Any]:
    """Write every IEEEST slot to explicit schema property names.

    :param value: Typed IEEEST object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'input_code': value.input_code, 'remote_bus_control': value.remote_bus_control, 'A1': value.A1, 'A2': value.A2, 'A3': value.A3, 'A4': value.A4, 'A5': value.A5, 'A6': value.A6, 'T1': value.T1, 'T2': value.T2, 'T3': value.T3, 'T4': value.T4, 'T5': value.T5, 'T6': value.T6, 'Ks': value.Ks, 'Ls_lim': value.Ls_lim, 'Vcu': value.Vcu, 'Vcl': value.Vcl}
