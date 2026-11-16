# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SalientPoleMachine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSalientPoleMachine(SiennaSchemaModel):
    """Expose every declared SalientPoleMachine property through fixed slots."""

    __slots__ = ('id', 'R', 'Td0_p', 'Td0_pp', 'Tq0_pp', 'Xd', 'Xq', 'Xd_p', 'Xd_pp', 'Xl', 'Se',)

    def __init__(self, id: int, R: float, Td0_p: float, Td0_pp: float, Tq0_pp: float, Xd: float, Xq: float, Xd_p: float, Xd_pp: float, Xl: float, Se: list[float]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.Td0_p: float = Td0_p
        self.Td0_pp: float = Td0_pp
        self.Tq0_pp: float = Tq0_pp
        self.Xd: float = Xd
        self.Xq: float = Xq
        self.Xd_p: float = Xd_p
        self.Xd_pp: float = Xd_pp
        self.Xl: float = Xl
        self.Se: list[float] = Se


def parse_sienna_salient_pole_machine(data: dict[str, Any]) -> SiennaSalientPoleMachine:
    """Parse declared SalientPoleMachine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SalientPoleMachine object.
    """
    return SiennaSalientPoleMachine(id=get_required_value(data, 'id', 'SalientPoleMachine'), R=get_required_value(data, 'R', 'SalientPoleMachine'), Td0_p=get_required_value(data, 'Td0_p', 'SalientPoleMachine'), Td0_pp=get_required_value(data, 'Td0_pp', 'SalientPoleMachine'), Tq0_pp=get_required_value(data, 'Tq0_pp', 'SalientPoleMachine'), Xd=get_required_value(data, 'Xd', 'SalientPoleMachine'), Xq=get_required_value(data, 'Xq', 'SalientPoleMachine'), Xd_p=get_required_value(data, 'Xd_p', 'SalientPoleMachine'), Xd_pp=get_required_value(data, 'Xd_pp', 'SalientPoleMachine'), Xl=get_required_value(data, 'Xl', 'SalientPoleMachine'), Se=get_required_value(data, 'Se', 'SalientPoleMachine'))


def sienna_salient_pole_machine_to_json(value: SiennaSalientPoleMachine) -> dict[str, Any]:
    """Write every SalientPoleMachine slot to explicit schema property names.

    :param value: Typed SalientPoleMachine object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'R': value.R, 'Td0_p': value.Td0_p, 'Td0_pp': value.Td0_pp, 'Tq0_pp': value.Tq0_pp, 'Xd': value.Xd, 'Xq': value.Xq, 'Xd_p': value.Xd_p, 'Xd_pp': value.Xd_pp, 'Xl': value.Xl, 'Se': value.Se}
