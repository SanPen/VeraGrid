# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna WPIDHY schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaWPIDHY(SiennaSchemaModel):
    """Expose every declared WPIDHY property through fixed slots."""

    __slots__ = ('id', 'T_reg', 'reg', 'Kp', 'Ki', 'Kd', 'Ta', 'Tb', 'V_lim', 'G_lim', 'Tw', 'P_lim', 'D', 'gate_openings', 'power_gate_openings', 'P_ref',)

    def __init__(self, id: int, T_reg: float, reg: float, Kp: float, Ki: float, Kd: float, Ta: float, Tb: float, V_lim: SiennaMinMax, G_lim: SiennaMinMax, Tw: float, P_lim: SiennaMinMax, D: float, gate_openings: list[float], power_gate_openings: list[float], P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.T_reg: float = T_reg
        self.reg: float = reg
        self.Kp: float = Kp
        self.Ki: float = Ki
        self.Kd: float = Kd
        self.Ta: float = Ta
        self.Tb: float = Tb
        self.V_lim: SiennaMinMax = V_lim
        self.G_lim: SiennaMinMax = G_lim
        self.Tw: float = Tw
        self.P_lim: SiennaMinMax = P_lim
        self.D: float = D
        self.gate_openings: list[float] = gate_openings
        self.power_gate_openings: list[float] = power_gate_openings
        self.P_ref: float = P_ref


def parse_sienna_wpidhy(data: dict[str, Any]) -> SiennaWPIDHY:
    """Parse declared WPIDHY properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed WPIDHY object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaWPIDHY(id=get_required_value(data, 'id', 'WPIDHY'), T_reg=get_required_value(data, 'T_reg', 'WPIDHY'), reg=get_required_value(data, 'reg', 'WPIDHY'), Kp=get_required_value(data, 'Kp', 'WPIDHY'), Ki=get_required_value(data, 'Ki', 'WPIDHY'), Kd=get_required_value(data, 'Kd', 'WPIDHY'), Ta=get_required_value(data, 'Ta', 'WPIDHY'), Tb=get_required_value(data, 'Tb', 'WPIDHY'), V_lim=parse_sienna_min_max(get_required_value(data, 'V_lim', 'WPIDHY')), G_lim=parse_sienna_min_max(get_required_value(data, 'G_lim', 'WPIDHY')), Tw=get_required_value(data, 'Tw', 'WPIDHY'), P_lim=parse_sienna_min_max(get_required_value(data, 'P_lim', 'WPIDHY')), D=get_required_value(data, 'D', 'WPIDHY'), gate_openings=get_required_value(data, 'gate_openings', 'WPIDHY'), power_gate_openings=get_required_value(data, 'power_gate_openings', 'WPIDHY'), P_ref=data.get('P_ref', None))

def sienna_wpidhy_to_json(value: SiennaWPIDHY) -> dict[str, Any]:
    """Write every WPIDHY slot to explicit schema property names.

    :param value: Typed WPIDHY object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'T_reg': value.T_reg, 'reg': value.reg, 'Kp': value.Kp, 'Ki': value.Ki, 'Kd': value.Kd, 'Ta': value.Ta, 'Tb': value.Tb, 'V_lim': sienna_min_max_to_json(value.V_lim), 'G_lim': sienna_min_max_to_json(value.G_lim), 'Tw': value.Tw, 'P_lim': sienna_min_max_to_json(value.P_lim), 'D': value.D, 'gate_openings': value.gate_openings, 'power_gate_openings': value.power_gate_openings, 'P_ref': value.P_ref}
