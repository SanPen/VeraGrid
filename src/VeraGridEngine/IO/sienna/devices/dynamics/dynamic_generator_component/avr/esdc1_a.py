# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ESDC1A schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaESDC1A(SiennaSchemaModel):
    """Expose every declared ESDC1A property through fixed slots."""

    __slots__ = ('id', 'Tr', 'Ka', 'Ta', 'Tb', 'Tc', 'Vr_lim', 'Ke', 'Te', 'Kf', 'Tf', 'switch', 'E_sat', 'Se', 'V_ref',)

    def __init__(self, id: int, Tr: float, Ka: float, Ta: float, Tb: float, Tc: float, Vr_lim: SiennaMinMax, Ke: float, Te: float, Kf: float, Tf: float, switch: int, E_sat: list[float], Se: list[float], V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Tr: float = Tr
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Tb: float = Tb
        self.Tc: float = Tc
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Ke: float = Ke
        self.Te: float = Te
        self.Kf: float = Kf
        self.Tf: float = Tf
        self.switch: int = switch
        self.E_sat: list[float] = E_sat
        self.Se: list[float] = Se
        self.V_ref: float = V_ref


def parse_sienna_esdc1_a(data: dict[str, Any]) -> SiennaESDC1A:
    """Parse declared ESDC1A properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ESDC1A object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaESDC1A(id=get_required_value(data, 'id', 'ESDC1A'), Tr=get_required_value(data, 'Tr', 'ESDC1A'), Ka=get_required_value(data, 'Ka', 'ESDC1A'), Ta=get_required_value(data, 'Ta', 'ESDC1A'), Tb=get_required_value(data, 'Tb', 'ESDC1A'), Tc=get_required_value(data, 'Tc', 'ESDC1A'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'ESDC1A')), Ke=get_required_value(data, 'Ke', 'ESDC1A'), Te=get_required_value(data, 'Te', 'ESDC1A'), Kf=get_required_value(data, 'Kf', 'ESDC1A'), Tf=get_required_value(data, 'Tf', 'ESDC1A'), switch=get_required_value(data, 'switch', 'ESDC1A'), E_sat=get_required_value(data, 'E_sat', 'ESDC1A'), Se=get_required_value(data, 'Se', 'ESDC1A'), V_ref=data.get('V_ref', None))

def sienna_esdc1_a_to_json(value: SiennaESDC1A) -> dict[str, Any]:
    """Write every ESDC1A slot to explicit schema property names.

    :param value: Typed ESDC1A object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Tr': value.Tr, 'Ka': value.Ka, 'Ta': value.Ta, 'Tb': value.Tb, 'Tc': value.Tc, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Ke': value.Ke, 'Te': value.Te, 'Kf': value.Kf, 'Tf': value.Tf, 'switch': value.switch, 'E_sat': value.E_sat, 'Se': value.Se, 'V_ref': value.V_ref}
