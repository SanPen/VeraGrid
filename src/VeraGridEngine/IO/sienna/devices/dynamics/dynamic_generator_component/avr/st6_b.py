# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ST6B schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaST6B(SiennaSchemaModel):
    """Expose every declared ST6B property through fixed slots."""

    __slots__ = ('id', 'OEL_Flag', 'Tr', 'K_pa', 'K_ia', 'K_da', 'T_da', 'Va_lim', 'K_ff', 'K_m', 'K_ci', 'K_lr', 'I_lr', 'Vr_lim', 'Kg', 'Tg', 'V_ref',)

    def __init__(self, id: int, OEL_Flag: int, Tr: float, K_pa: float, K_ia: float, K_da: float, T_da: float, Va_lim: SiennaMinMax, K_ff: float, K_m: float, K_ci: float, K_lr: float, I_lr: float, Vr_lim: SiennaMinMax, Kg: float, Tg: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.OEL_Flag: int = OEL_Flag
        self.Tr: float = Tr
        self.K_pa: float = K_pa
        self.K_ia: float = K_ia
        self.K_da: float = K_da
        self.T_da: float = T_da
        self.Va_lim: SiennaMinMax = Va_lim
        self.K_ff: float = K_ff
        self.K_m: float = K_m
        self.K_ci: float = K_ci
        self.K_lr: float = K_lr
        self.I_lr: float = I_lr
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Kg: float = Kg
        self.Tg: float = Tg
        self.V_ref: float = V_ref


def parse_sienna_st6_b(data: dict[str, Any]) -> SiennaST6B:
    """Parse declared ST6B properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ST6B object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaST6B(id=get_required_value(data, 'id', 'ST6B'), OEL_Flag=get_required_value(data, 'OEL_Flag', 'ST6B'), Tr=get_required_value(data, 'Tr', 'ST6B'), K_pa=get_required_value(data, 'K_pa', 'ST6B'), K_ia=get_required_value(data, 'K_ia', 'ST6B'), K_da=get_required_value(data, 'K_da', 'ST6B'), T_da=get_required_value(data, 'T_da', 'ST6B'), Va_lim=parse_sienna_min_max(get_required_value(data, 'Va_lim', 'ST6B')), K_ff=get_required_value(data, 'K_ff', 'ST6B'), K_m=get_required_value(data, 'K_m', 'ST6B'), K_ci=get_required_value(data, 'K_ci', 'ST6B'), K_lr=get_required_value(data, 'K_lr', 'ST6B'), I_lr=get_required_value(data, 'I_lr', 'ST6B'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'ST6B')), Kg=get_required_value(data, 'Kg', 'ST6B'), Tg=get_required_value(data, 'Tg', 'ST6B'), V_ref=data.get('V_ref', None))

def sienna_st6_b_to_json(value: SiennaST6B) -> dict[str, Any]:
    """Write every ST6B slot to explicit schema property names.

    :param value: Typed ST6B object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'OEL_Flag': value.OEL_Flag, 'Tr': value.Tr, 'K_pa': value.K_pa, 'K_ia': value.K_ia, 'K_da': value.K_da, 'T_da': value.T_da, 'Va_lim': sienna_min_max_to_json(value.Va_lim), 'K_ff': value.K_ff, 'K_m': value.K_m, 'K_ci': value.K_ci, 'K_lr': value.K_lr, 'I_lr': value.I_lr, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Kg': value.Kg, 'Tg': value.Tg, 'V_ref': value.V_ref}
