# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna STAB1 schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSTAB1(SiennaSchemaModel):
    """Expose every declared STAB1 property through fixed slots."""

    __slots__ = ('id', 'KT', 'T', 'T1T3', 'T3', 'T2T4', 'T4', 'H_lim',)

    def __init__(self, id: int, KT: float, T: float, T1T3: float, T3: float, T2T4: float, T4: float, H_lim: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.KT: float = KT
        self.T: float = T
        self.T1T3: float = T1T3
        self.T3: float = T3
        self.T2T4: float = T2T4
        self.T4: float = T4
        self.H_lim: float = H_lim


def parse_sienna_stab1(data: dict[str, Any]) -> SiennaSTAB1:
    """Parse declared STAB1 properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed STAB1 object.
    """
    return SiennaSTAB1(id=get_required_value(data, 'id', 'STAB1'), KT=get_required_value(data, 'KT', 'STAB1'), T=get_required_value(data, 'T', 'STAB1'), T1T3=get_required_value(data, 'T1T3', 'STAB1'), T3=get_required_value(data, 'T3', 'STAB1'), T2T4=get_required_value(data, 'T2T4', 'STAB1'), T4=get_required_value(data, 'T4', 'STAB1'), H_lim=get_required_value(data, 'H_lim', 'STAB1'))


def sienna_stab1_to_json(value: SiennaSTAB1) -> dict[str, Any]:
    """Write every STAB1 slot to explicit schema property names.

    :param value: Typed STAB1 object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'KT': value.KT, 'T': value.T, 'T1T3': value.T1T3, 'T3': value.T3, 'T2T4': value.T2T4, 'T4': value.T4, 'H_lim': value.H_lim}
