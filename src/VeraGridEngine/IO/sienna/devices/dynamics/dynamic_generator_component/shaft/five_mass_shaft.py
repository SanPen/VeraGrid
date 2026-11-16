# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FiveMassShaft schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFiveMassShaft(SiennaSchemaModel):
    """Expose every declared FiveMassShaft property through fixed slots."""

    __slots__ = ('id', 'H', 'H_hp', 'H_ip', 'H_lp', 'H_ex', 'D', 'D_hp', 'D_ip', 'D_lp', 'D_ex', 'D_12', 'D_23', 'D_34', 'D_45', 'K_hp', 'K_ip', 'K_lp', 'K_ex',)

    def __init__(self, id: int, H: float, H_hp: float, H_ip: float, H_lp: float, H_ex: float, D: float, D_hp: float, D_ip: float, D_lp: float, D_ex: float, D_12: float, D_23: float, D_34: float, D_45: float, K_hp: float, K_ip: float, K_lp: float, K_ex: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.H: float = H
        self.H_hp: float = H_hp
        self.H_ip: float = H_ip
        self.H_lp: float = H_lp
        self.H_ex: float = H_ex
        self.D: float = D
        self.D_hp: float = D_hp
        self.D_ip: float = D_ip
        self.D_lp: float = D_lp
        self.D_ex: float = D_ex
        self.D_12: float = D_12
        self.D_23: float = D_23
        self.D_34: float = D_34
        self.D_45: float = D_45
        self.K_hp: float = K_hp
        self.K_ip: float = K_ip
        self.K_lp: float = K_lp
        self.K_ex: float = K_ex


def parse_sienna_five_mass_shaft(data: dict[str, Any]) -> SiennaFiveMassShaft:
    """Parse declared FiveMassShaft properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FiveMassShaft object.
    """
    return SiennaFiveMassShaft(id=get_required_value(data, 'id', 'FiveMassShaft'), H=get_required_value(data, 'H', 'FiveMassShaft'), H_hp=get_required_value(data, 'H_hp', 'FiveMassShaft'), H_ip=get_required_value(data, 'H_ip', 'FiveMassShaft'), H_lp=get_required_value(data, 'H_lp', 'FiveMassShaft'), H_ex=get_required_value(data, 'H_ex', 'FiveMassShaft'), D=get_required_value(data, 'D', 'FiveMassShaft'), D_hp=get_required_value(data, 'D_hp', 'FiveMassShaft'), D_ip=get_required_value(data, 'D_ip', 'FiveMassShaft'), D_lp=get_required_value(data, 'D_lp', 'FiveMassShaft'), D_ex=get_required_value(data, 'D_ex', 'FiveMassShaft'), D_12=get_required_value(data, 'D_12', 'FiveMassShaft'), D_23=get_required_value(data, 'D_23', 'FiveMassShaft'), D_34=get_required_value(data, 'D_34', 'FiveMassShaft'), D_45=get_required_value(data, 'D_45', 'FiveMassShaft'), K_hp=get_required_value(data, 'K_hp', 'FiveMassShaft'), K_ip=get_required_value(data, 'K_ip', 'FiveMassShaft'), K_lp=get_required_value(data, 'K_lp', 'FiveMassShaft'), K_ex=get_required_value(data, 'K_ex', 'FiveMassShaft'))


def sienna_five_mass_shaft_to_json(value: SiennaFiveMassShaft) -> dict[str, Any]:
    """Write every FiveMassShaft slot to explicit schema property names.

    :param value: Typed FiveMassShaft object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'H': value.H, 'H_hp': value.H_hp, 'H_ip': value.H_ip, 'H_lp': value.H_lp, 'H_ex': value.H_ex, 'D': value.D, 'D_hp': value.D_hp, 'D_ip': value.D_ip, 'D_lp': value.D_lp, 'D_ex': value.D_ex, 'D_12': value.D_12, 'D_23': value.D_23, 'D_34': value.D_34, 'D_45': value.D_45, 'K_hp': value.K_hp, 'K_ip': value.K_ip, 'K_lp': value.K_lp, 'K_ex': value.K_ex}
