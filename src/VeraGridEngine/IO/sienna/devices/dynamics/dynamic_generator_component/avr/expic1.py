# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EXPIC1 schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEXPIC1(SiennaSchemaModel):
    """Expose every declared EXPIC1 property through fixed slots."""

    __slots__ = ('id', 'Tr', 'Ka', 'Ta', 'Va_lim', 'Ta_2', 'Ta_3', 'Ta_4', 'Vr_lim', 'Kf', 'Tf_1', 'Tf_2', 'Efd_lim', 'Ke', 'Te', 'E_sat', 'Se', 'Kp', 'Ki', 'Kc', 'V_ref',)

    def __init__(self, id: int, Tr: float, Ka: float, Ta: float, Va_lim: SiennaMinMax, Ta_2: float, Ta_3: float, Ta_4: float, Vr_lim: SiennaMinMax, Kf: float, Tf_1: float, Tf_2: float, Efd_lim: SiennaMinMax, Ke: float, Te: float, E_sat: list[float], Se: list[float], Kp: float, Ki: float, Kc: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Tr: float = Tr
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Va_lim: SiennaMinMax = Va_lim
        self.Ta_2: float = Ta_2
        self.Ta_3: float = Ta_3
        self.Ta_4: float = Ta_4
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Kf: float = Kf
        self.Tf_1: float = Tf_1
        self.Tf_2: float = Tf_2
        self.Efd_lim: SiennaMinMax = Efd_lim
        self.Ke: float = Ke
        self.Te: float = Te
        self.E_sat: list[float] = E_sat
        self.Se: list[float] = Se
        self.Kp: float = Kp
        self.Ki: float = Ki
        self.Kc: float = Kc
        self.V_ref: float = V_ref


def parse_sienna_expic1(data: dict[str, Any]) -> SiennaEXPIC1:
    """Parse declared EXPIC1 properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed EXPIC1 object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaEXPIC1(id=get_required_value(data, 'id', 'EXPIC1'), Tr=get_required_value(data, 'Tr', 'EXPIC1'), Ka=get_required_value(data, 'Ka', 'EXPIC1'), Ta=get_required_value(data, 'Ta', 'EXPIC1'), Va_lim=parse_sienna_min_max(get_required_value(data, 'Va_lim', 'EXPIC1')), Ta_2=get_required_value(data, 'Ta_2', 'EXPIC1'), Ta_3=get_required_value(data, 'Ta_3', 'EXPIC1'), Ta_4=get_required_value(data, 'Ta_4', 'EXPIC1'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'EXPIC1')), Kf=get_required_value(data, 'Kf', 'EXPIC1'), Tf_1=get_required_value(data, 'Tf_1', 'EXPIC1'), Tf_2=get_required_value(data, 'Tf_2', 'EXPIC1'), Efd_lim=parse_sienna_min_max(get_required_value(data, 'Efd_lim', 'EXPIC1')), Ke=get_required_value(data, 'Ke', 'EXPIC1'), Te=get_required_value(data, 'Te', 'EXPIC1'), E_sat=get_required_value(data, 'E_sat', 'EXPIC1'), Se=get_required_value(data, 'Se', 'EXPIC1'), Kp=get_required_value(data, 'Kp', 'EXPIC1'), Ki=get_required_value(data, 'Ki', 'EXPIC1'), Kc=get_required_value(data, 'Kc', 'EXPIC1'), V_ref=data.get('V_ref', None))

def sienna_expic1_to_json(value: SiennaEXPIC1) -> dict[str, Any]:
    """Write every EXPIC1 slot to explicit schema property names.

    :param value: Typed EXPIC1 object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Tr': value.Tr, 'Ka': value.Ka, 'Ta': value.Ta, 'Va_lim': sienna_min_max_to_json(value.Va_lim), 'Ta_2': value.Ta_2, 'Ta_3': value.Ta_3, 'Ta_4': value.Ta_4, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Kf': value.Kf, 'Tf_1': value.Tf_1, 'Tf_2': value.Tf_2, 'Efd_lim': sienna_min_max_to_json(value.Efd_lim), 'Ke': value.Ke, 'Te': value.Te, 'E_sat': value.E_sat, 'Se': value.Se, 'Kp': value.Kp, 'Ki': value.Ki, 'Kc': value.Kc, 'V_ref': value.V_ref}
