# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AndersonFouadMachine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAndersonFouadMachine(SiennaSchemaModel):
    """Expose every declared AndersonFouadMachine property through fixed slots."""

    __slots__ = ('id', 'R', 'Xd', 'Xq', 'Xd_p', 'Xq_p', 'Xd_pp', 'Xq_pp', 'Td0_p', 'Tq0_p', 'Td0_pp', 'Tq0_pp',)

    def __init__(self, id: int, R: float, Xd: float, Xq: float, Xd_p: float, Xq_p: float, Xd_pp: float, Xq_pp: float, Td0_p: float, Tq0_p: float, Td0_pp: float, Tq0_pp: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.Xd: float = Xd
        self.Xq: float = Xq
        self.Xd_p: float = Xd_p
        self.Xq_p: float = Xq_p
        self.Xd_pp: float = Xd_pp
        self.Xq_pp: float = Xq_pp
        self.Td0_p: float = Td0_p
        self.Tq0_p: float = Tq0_p
        self.Td0_pp: float = Td0_pp
        self.Tq0_pp: float = Tq0_pp


def parse_sienna_anderson_fouad_machine(data: dict[str, Any]) -> SiennaAndersonFouadMachine:
    """Parse declared AndersonFouadMachine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed AndersonFouadMachine object.
    """
    return SiennaAndersonFouadMachine(id=get_required_value(data, 'id', 'AndersonFouadMachine'), R=get_required_value(data, 'R', 'AndersonFouadMachine'), Xd=get_required_value(data, 'Xd', 'AndersonFouadMachine'), Xq=get_required_value(data, 'Xq', 'AndersonFouadMachine'), Xd_p=get_required_value(data, 'Xd_p', 'AndersonFouadMachine'), Xq_p=get_required_value(data, 'Xq_p', 'AndersonFouadMachine'), Xd_pp=get_required_value(data, 'Xd_pp', 'AndersonFouadMachine'), Xq_pp=get_required_value(data, 'Xq_pp', 'AndersonFouadMachine'), Td0_p=get_required_value(data, 'Td0_p', 'AndersonFouadMachine'), Tq0_p=get_required_value(data, 'Tq0_p', 'AndersonFouadMachine'), Td0_pp=get_required_value(data, 'Td0_pp', 'AndersonFouadMachine'), Tq0_pp=get_required_value(data, 'Tq0_pp', 'AndersonFouadMachine'))


def sienna_anderson_fouad_machine_to_json(value: SiennaAndersonFouadMachine) -> dict[str, Any]:
    """Write every AndersonFouadMachine slot to explicit schema property names.

    :param value: Typed AndersonFouadMachine object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'R': value.R, 'Xd': value.Xd, 'Xq': value.Xq, 'Xd_p': value.Xd_p, 'Xq_p': value.Xq_p, 'Xd_pp': value.Xd_pp, 'Xq_pp': value.Xq_pp, 'Td0_p': value.Td0_p, 'Tq0_p': value.Tq0_p, 'Td0_pp': value.Td0_pp, 'Tq0_pp': value.Tq0_pp}
