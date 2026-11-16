# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EXAC1 schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEXAC1(SiennaSchemaModel):
    """Expose every declared EXAC1 property through fixed slots."""

    __slots__ = ('id', 'Tr', 'Tb', 'Tc', 'Ka', 'Ta', 'Vr_lim', 'Te', 'Kf', 'Tf', 'Kc', 'Kd', 'Ke', 'E_sat', 'Se', 'V_ref',)

    def __init__(self, id: int, Tr: float, Tb: float, Tc: float, Ka: float, Ta: float, Vr_lim: SiennaMinMax, Te: float, Kf: float, Tf: float, Kc: float, Kd: float, Ke: float, E_sat: list[float], Se: list[float], V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Tr: float = Tr
        self.Tb: float = Tb
        self.Tc: float = Tc
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Te: float = Te
        self.Kf: float = Kf
        self.Tf: float = Tf
        self.Kc: float = Kc
        self.Kd: float = Kd
        self.Ke: float = Ke
        self.E_sat: list[float] = E_sat
        self.Se: list[float] = Se
        self.V_ref: float = V_ref


def parse_sienna_exac1(data: dict[str, Any]) -> SiennaEXAC1:
    """Parse declared EXAC1 properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed EXAC1 object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaEXAC1(id=get_required_value(data, 'id', 'EXAC1'), Tr=get_required_value(data, 'Tr', 'EXAC1'), Tb=get_required_value(data, 'Tb', 'EXAC1'), Tc=get_required_value(data, 'Tc', 'EXAC1'), Ka=get_required_value(data, 'Ka', 'EXAC1'), Ta=get_required_value(data, 'Ta', 'EXAC1'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'EXAC1')), Te=get_required_value(data, 'Te', 'EXAC1'), Kf=get_required_value(data, 'Kf', 'EXAC1'), Tf=get_required_value(data, 'Tf', 'EXAC1'), Kc=get_required_value(data, 'Kc', 'EXAC1'), Kd=get_required_value(data, 'Kd', 'EXAC1'), Ke=get_required_value(data, 'Ke', 'EXAC1'), E_sat=get_required_value(data, 'E_sat', 'EXAC1'), Se=get_required_value(data, 'Se', 'EXAC1'), V_ref=data.get('V_ref', None))

def sienna_exac1_to_json(value: SiennaEXAC1) -> dict[str, Any]:
    """Write every EXAC1 slot to explicit schema property names.

    :param value: Typed EXAC1 object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Tr': value.Tr, 'Tb': value.Tb, 'Tc': value.Tc, 'Ka': value.Ka, 'Ta': value.Ta, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Te': value.Te, 'Kf': value.Kf, 'Tf': value.Tf, 'Kc': value.Kc, 'Kd': value.Kd, 'Ke': value.Ke, 'E_sat': value.E_sat, 'Se': value.Se, 'V_ref': value.V_ref}
