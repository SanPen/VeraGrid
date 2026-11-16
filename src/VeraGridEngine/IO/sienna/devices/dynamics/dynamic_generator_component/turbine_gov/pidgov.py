# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PIDGOV schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPIDGOV(SiennaSchemaModel):
    """Expose every declared PIDGOV property through fixed slots."""

    __slots__ = ('id', 'feedback_flag', 'Rperm', 'T_reg', 'Kp', 'Ki', 'Kd', 'Ta', 'Tb', 'D_turb', 'gate_openings', 'power_gate_openings', 'G_lim', 'A_tw', 'Tw', 'V_lim', 'P_ref',)

    def __init__(self, id: int, feedback_flag: int, Rperm: float, T_reg: float, Kp: float, Ki: float, Kd: float, Ta: float, Tb: float, D_turb: float, gate_openings: list[float], power_gate_openings: list[float], G_lim: SiennaMinMax, A_tw: float, Tw: float, V_lim: SiennaMinMax, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.feedback_flag: int = feedback_flag
        self.Rperm: float = Rperm
        self.T_reg: float = T_reg
        self.Kp: float = Kp
        self.Ki: float = Ki
        self.Kd: float = Kd
        self.Ta: float = Ta
        self.Tb: float = Tb
        self.D_turb: float = D_turb
        self.gate_openings: list[float] = gate_openings
        self.power_gate_openings: list[float] = power_gate_openings
        self.G_lim: SiennaMinMax = G_lim
        self.A_tw: float = A_tw
        self.Tw: float = Tw
        self.V_lim: SiennaMinMax = V_lim
        self.P_ref: float = P_ref


def parse_sienna_pidgov(data: dict[str, Any]) -> SiennaPIDGOV:
    """Parse declared PIDGOV properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PIDGOV object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaPIDGOV(id=get_required_value(data, 'id', 'PIDGOV'), feedback_flag=get_required_value(data, 'feedback_flag', 'PIDGOV'), Rperm=get_required_value(data, 'Rperm', 'PIDGOV'), T_reg=get_required_value(data, 'T_reg', 'PIDGOV'), Kp=get_required_value(data, 'Kp', 'PIDGOV'), Ki=get_required_value(data, 'Ki', 'PIDGOV'), Kd=get_required_value(data, 'Kd', 'PIDGOV'), Ta=get_required_value(data, 'Ta', 'PIDGOV'), Tb=get_required_value(data, 'Tb', 'PIDGOV'), D_turb=get_required_value(data, 'D_turb', 'PIDGOV'), gate_openings=get_required_value(data, 'gate_openings', 'PIDGOV'), power_gate_openings=get_required_value(data, 'power_gate_openings', 'PIDGOV'), G_lim=parse_sienna_min_max(get_required_value(data, 'G_lim', 'PIDGOV')), A_tw=get_required_value(data, 'A_tw', 'PIDGOV'), Tw=get_required_value(data, 'Tw', 'PIDGOV'), V_lim=parse_sienna_min_max(get_required_value(data, 'V_lim', 'PIDGOV')), P_ref=data.get('P_ref', None))

def sienna_pidgov_to_json(value: SiennaPIDGOV) -> dict[str, Any]:
    """Write every PIDGOV slot to explicit schema property names.

    :param value: Typed PIDGOV object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'feedback_flag': value.feedback_flag, 'Rperm': value.Rperm, 'T_reg': value.T_reg, 'Kp': value.Kp, 'Ki': value.Ki, 'Kd': value.Kd, 'Ta': value.Ta, 'Tb': value.Tb, 'D_turb': value.D_turb, 'gate_openings': value.gate_openings, 'power_gate_openings': value.power_gate_openings, 'G_lim': sienna_min_max_to_json(value.G_lim), 'A_tw': value.A_tw, 'Tw': value.Tw, 'V_lim': sienna_min_max_to_json(value.V_lim), 'P_ref': value.P_ref}
