# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ESST1A schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaESST1A(SiennaSchemaModel):
    """Expose every declared ESST1A property through fixed slots."""

    __slots__ = ('id', 'UEL_flags', 'PSS_flags', 'Tr', 'Vi_lim', 'Tc', 'Tb', 'Tc1', 'Tb1', 'Ka', 'Ta', 'Va_lim', 'Vr_lim', 'Kc', 'Kf', 'Tf', 'K_lr', 'I_lr', 'V_ref',)

    def __init__(self, id: int, UEL_flags: int, PSS_flags: int, Tr: float, Vi_lim: list[float], Tc: float, Tb: float, Tc1: float, Tb1: float, Ka: float, Ta: float, Va_lim: SiennaMinMax, Vr_lim: SiennaMinMax, Kc: float, Kf: float, Tf: float, K_lr: float, I_lr: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.UEL_flags: int = UEL_flags
        self.PSS_flags: int = PSS_flags
        self.Tr: float = Tr
        self.Vi_lim: list[float] = Vi_lim
        self.Tc: float = Tc
        self.Tb: float = Tb
        self.Tc1: float = Tc1
        self.Tb1: float = Tb1
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Va_lim: SiennaMinMax = Va_lim
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Kc: float = Kc
        self.Kf: float = Kf
        self.Tf: float = Tf
        self.K_lr: float = K_lr
        self.I_lr: float = I_lr
        self.V_ref: float = V_ref


def parse_sienna_esst1_a(data: dict[str, Any]) -> SiennaESST1A:
    """Parse declared ESST1A properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ESST1A object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaESST1A(id=get_required_value(data, 'id', 'ESST1A'), UEL_flags=get_required_value(data, 'UEL_flags', 'ESST1A'), PSS_flags=get_required_value(data, 'PSS_flags', 'ESST1A'), Tr=get_required_value(data, 'Tr', 'ESST1A'), Vi_lim=get_required_value(data, 'Vi_lim', 'ESST1A'), Tc=get_required_value(data, 'Tc', 'ESST1A'), Tb=get_required_value(data, 'Tb', 'ESST1A'), Tc1=get_required_value(data, 'Tc1', 'ESST1A'), Tb1=get_required_value(data, 'Tb1', 'ESST1A'), Ka=get_required_value(data, 'Ka', 'ESST1A'), Ta=get_required_value(data, 'Ta', 'ESST1A'), Va_lim=parse_sienna_min_max(get_required_value(data, 'Va_lim', 'ESST1A')), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'ESST1A')), Kc=get_required_value(data, 'Kc', 'ESST1A'), Kf=get_required_value(data, 'Kf', 'ESST1A'), Tf=get_required_value(data, 'Tf', 'ESST1A'), K_lr=get_required_value(data, 'K_lr', 'ESST1A'), I_lr=get_required_value(data, 'I_lr', 'ESST1A'), V_ref=data.get('V_ref', None))

def sienna_esst1_a_to_json(value: SiennaESST1A) -> dict[str, Any]:
    """Write every ESST1A slot to explicit schema property names.

    :param value: Typed ESST1A object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'UEL_flags': value.UEL_flags, 'PSS_flags': value.PSS_flags, 'Tr': value.Tr, 'Vi_lim': value.Vi_lim, 'Tc': value.Tc, 'Tb': value.Tb, 'Tc1': value.Tc1, 'Tb1': value.Tb1, 'Ka': value.Ka, 'Ta': value.Ta, 'Va_lim': sienna_min_max_to_json(value.Va_lim), 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Kc': value.Kc, 'Kf': value.Kf, 'Tf': value.Tf, 'K_lr': value.K_lr, 'I_lr': value.I_lr, 'V_ref': value.V_ref}
