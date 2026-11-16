# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TGTypeI schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTGTypeI(SiennaSchemaModel):
    """Expose every declared TGTypeI property through fixed slots."""

    __slots__ = ('id', 'R', 'Ts', 'Tc', 'T3', 'T4', 'T5', 'valve_position_limits', 'P_ref',)

    def __init__(self, id: int, R: float, Ts: float, Tc: float, T3: float, T4: float, T5: float, valve_position_limits: SiennaMinMax, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.Ts: float = Ts
        self.Tc: float = Tc
        self.T3: float = T3
        self.T4: float = T4
        self.T5: float = T5
        self.valve_position_limits: SiennaMinMax = valve_position_limits
        self.P_ref: float = P_ref


def parse_sienna_tg_type_i(data: dict[str, Any]) -> SiennaTGTypeI:
    """Parse declared TGTypeI properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TGTypeI object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaTGTypeI(id=get_required_value(data, 'id', 'TGTypeI'), R=get_required_value(data, 'R', 'TGTypeI'), Ts=get_required_value(data, 'Ts', 'TGTypeI'), Tc=get_required_value(data, 'Tc', 'TGTypeI'), T3=get_required_value(data, 'T3', 'TGTypeI'), T4=get_required_value(data, 'T4', 'TGTypeI'), T5=get_required_value(data, 'T5', 'TGTypeI'), valve_position_limits=parse_sienna_min_max(get_required_value(data, 'valve_position_limits', 'TGTypeI')), P_ref=data.get('P_ref', None))

def sienna_tg_type_i_to_json(value: SiennaTGTypeI) -> dict[str, Any]:
    """Write every TGTypeI slot to explicit schema property names.

    :param value: Typed TGTypeI object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'R': value.R, 'Ts': value.Ts, 'Tc': value.Tc, 'T3': value.T3, 'T4': value.T4, 'T5': value.T5, 'valve_position_limits': sienna_min_max_to_json(value.valve_position_limits), 'P_ref': value.P_ref}
