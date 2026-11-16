# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna IEEET1 schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaIEEET1(SiennaSchemaModel):
    """Expose every declared IEEET1 property through fixed slots."""

    __slots__ = ('id', 'Tr', 'Ka', 'Ta', 'Vr_lim', 'Ke', 'Te', 'Kf', 'Tf', 'switch', 'E_sat', 'Se', 'V_ref',)

    def __init__(self, id: int, Tr: float, Ka: float, Ta: float, Vr_lim: SiennaMinMax, Ke: float, Te: float, Kf: float, Tf: float, switch: int, E_sat: list[float], Se: list[float], V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Tr: float = Tr
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Ke: float = Ke
        self.Te: float = Te
        self.Kf: float = Kf
        self.Tf: float = Tf
        self.switch: int = switch
        self.E_sat: list[float] = E_sat
        self.Se: list[float] = Se
        self.V_ref: float = V_ref


def parse_sienna_ieeet1(data: dict[str, Any]) -> SiennaIEEET1:
    """Parse declared IEEET1 properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed IEEET1 object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaIEEET1(id=get_required_value(data, 'id', 'IEEET1'), Tr=get_required_value(data, 'Tr', 'IEEET1'), Ka=get_required_value(data, 'Ka', 'IEEET1'), Ta=get_required_value(data, 'Ta', 'IEEET1'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'IEEET1')), Ke=get_required_value(data, 'Ke', 'IEEET1'), Te=get_required_value(data, 'Te', 'IEEET1'), Kf=get_required_value(data, 'Kf', 'IEEET1'), Tf=get_required_value(data, 'Tf', 'IEEET1'), switch=get_required_value(data, 'switch', 'IEEET1'), E_sat=get_required_value(data, 'E_sat', 'IEEET1'), Se=get_required_value(data, 'Se', 'IEEET1'), V_ref=data.get('V_ref', None))

def sienna_ieeet1_to_json(value: SiennaIEEET1) -> dict[str, Any]:
    """Write every IEEET1 slot to explicit schema property names.

    :param value: Typed IEEET1 object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Tr': value.Tr, 'Ka': value.Ka, 'Ta': value.Ta, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Ke': value.Ke, 'Te': value.Te, 'Kf': value.Kf, 'Tf': value.Tf, 'switch': value.switch, 'E_sat': value.E_sat, 'Se': value.Se, 'V_ref': value.V_ref}
