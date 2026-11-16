# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna OneDOneQMachine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaOneDOneQMachine(SiennaSchemaModel):
    """Expose every declared OneDOneQMachine property through fixed slots."""

    __slots__ = ('id', 'R', 'Xd', 'Xq', 'Xd_p', 'Xq_p', 'Td0_p', 'Tq0_p',)

    def __init__(self, id: int, R: float, Xd: float, Xq: float, Xd_p: float, Xq_p: float, Td0_p: float, Tq0_p: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.Xd: float = Xd
        self.Xq: float = Xq
        self.Xd_p: float = Xd_p
        self.Xq_p: float = Xq_p
        self.Td0_p: float = Td0_p
        self.Tq0_p: float = Tq0_p


def parse_sienna_one_d_one_q_machine(data: dict[str, Any]) -> SiennaOneDOneQMachine:
    """Parse declared OneDOneQMachine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed OneDOneQMachine object.
    """
    return SiennaOneDOneQMachine(id=get_required_value(data, 'id', 'OneDOneQMachine'), R=get_required_value(data, 'R', 'OneDOneQMachine'), Xd=get_required_value(data, 'Xd', 'OneDOneQMachine'), Xq=get_required_value(data, 'Xq', 'OneDOneQMachine'), Xd_p=get_required_value(data, 'Xd_p', 'OneDOneQMachine'), Xq_p=get_required_value(data, 'Xq_p', 'OneDOneQMachine'), Td0_p=get_required_value(data, 'Td0_p', 'OneDOneQMachine'), Tq0_p=get_required_value(data, 'Tq0_p', 'OneDOneQMachine'))


def sienna_one_d_one_q_machine_to_json(value: SiennaOneDOneQMachine) -> dict[str, Any]:
    """Write every OneDOneQMachine slot to explicit schema property names.

    :param value: Typed OneDOneQMachine object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'R': value.R, 'Xd': value.Xd, 'Xq': value.Xq, 'Xd_p': value.Xd_p, 'Xq_p': value.Xq_p, 'Td0_p': value.Td0_p, 'Tq0_p': value.Tq0_p}
