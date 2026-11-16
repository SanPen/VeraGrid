# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EXAC2 schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEXAC2(SiennaSchemaModel):
    """Expose every declared EXAC2 property through fixed slots."""

    __slots__ = ('id', 'Tr', 'Tb', 'Tc', 'Ka', 'Ta', 'Va_lim', 'Kb', 'Vr_lim', 'Te', 'Kl', 'Kh', 'Kf', 'Tf', 'Kc', 'Kd', 'Ke', 'V_lr', 'E_sat', 'Se', 'V_ref',)

    def __init__(self, id: int, Tr: float, Tb: float, Tc: float, Ka: float, Ta: float, Va_lim: SiennaMinMax, Kb: float, Vr_lim: SiennaMinMax, Te: float, Kl: float, Kh: float, Kf: float, Tf: float, Kc: float, Kd: float, Ke: float, V_lr: float, E_sat: list[float], Se: list[float], V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Tr: float = Tr
        self.Tb: float = Tb
        self.Tc: float = Tc
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Va_lim: SiennaMinMax = Va_lim
        self.Kb: float = Kb
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Te: float = Te
        self.Kl: float = Kl
        self.Kh: float = Kh
        self.Kf: float = Kf
        self.Tf: float = Tf
        self.Kc: float = Kc
        self.Kd: float = Kd
        self.Ke: float = Ke
        self.V_lr: float = V_lr
        self.E_sat: list[float] = E_sat
        self.Se: list[float] = Se
        self.V_ref: float = V_ref


def parse_sienna_exac2(data: dict[str, Any]) -> SiennaEXAC2:
    """Parse declared EXAC2 properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed EXAC2 object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaEXAC2(id=get_required_value(data, 'id', 'EXAC2'), Tr=get_required_value(data, 'Tr', 'EXAC2'), Tb=get_required_value(data, 'Tb', 'EXAC2'), Tc=get_required_value(data, 'Tc', 'EXAC2'), Ka=get_required_value(data, 'Ka', 'EXAC2'), Ta=get_required_value(data, 'Ta', 'EXAC2'), Va_lim=parse_sienna_min_max(get_required_value(data, 'Va_lim', 'EXAC2')), Kb=get_required_value(data, 'Kb', 'EXAC2'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'EXAC2')), Te=get_required_value(data, 'Te', 'EXAC2'), Kl=get_required_value(data, 'Kl', 'EXAC2'), Kh=get_required_value(data, 'Kh', 'EXAC2'), Kf=get_required_value(data, 'Kf', 'EXAC2'), Tf=get_required_value(data, 'Tf', 'EXAC2'), Kc=get_required_value(data, 'Kc', 'EXAC2'), Kd=get_required_value(data, 'Kd', 'EXAC2'), Ke=get_required_value(data, 'Ke', 'EXAC2'), V_lr=get_required_value(data, 'V_lr', 'EXAC2'), E_sat=get_required_value(data, 'E_sat', 'EXAC2'), Se=get_required_value(data, 'Se', 'EXAC2'), V_ref=data.get('V_ref', None))

def sienna_exac2_to_json(value: SiennaEXAC2) -> dict[str, Any]:
    """Write every EXAC2 slot to explicit schema property names.

    :param value: Typed EXAC2 object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Tr': value.Tr, 'Tb': value.Tb, 'Tc': value.Tc, 'Ka': value.Ka, 'Ta': value.Ta, 'Va_lim': sienna_min_max_to_json(value.Va_lim), 'Kb': value.Kb, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Te': value.Te, 'Kl': value.Kl, 'Kh': value.Kh, 'Kf': value.Kf, 'Tf': value.Tf, 'Kc': value.Kc, 'Kd': value.Kd, 'Ke': value.Ke, 'V_lr': value.V_lr, 'E_sat': value.E_sat, 'Se': value.Se, 'V_ref': value.V_ref}
