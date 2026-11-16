# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EXST1 schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEXST1(SiennaSchemaModel):
    """Expose every declared EXST1 property through fixed slots."""

    __slots__ = ('id', 'Tr', 'Vi_lim', 'Tc', 'Tb', 'Ka', 'Ta', 'Vr_lim', 'Kc', 'Kf', 'Tf', 'V_ref',)

    def __init__(self, id: int, Tr: float, Vi_lim: SiennaMinMax, Tc: float, Tb: float, Ka: float, Ta: float, Vr_lim: SiennaMinMax, Kc: float, Kf: float, Tf: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Tr: float = Tr
        self.Vi_lim: SiennaMinMax = Vi_lim
        self.Tc: float = Tc
        self.Tb: float = Tb
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.Vr_lim: SiennaMinMax = Vr_lim
        self.Kc: float = Kc
        self.Kf: float = Kf
        self.Tf: float = Tf
        self.V_ref: float = V_ref


def parse_sienna_exst1(data: dict[str, Any]) -> SiennaEXST1:
    """Parse declared EXST1 properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed EXST1 object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaEXST1(id=get_required_value(data, 'id', 'EXST1'), Tr=get_required_value(data, 'Tr', 'EXST1'), Vi_lim=parse_sienna_min_max(get_required_value(data, 'Vi_lim', 'EXST1')), Tc=get_required_value(data, 'Tc', 'EXST1'), Tb=get_required_value(data, 'Tb', 'EXST1'), Ka=get_required_value(data, 'Ka', 'EXST1'), Ta=get_required_value(data, 'Ta', 'EXST1'), Vr_lim=parse_sienna_min_max(get_required_value(data, 'Vr_lim', 'EXST1')), Kc=get_required_value(data, 'Kc', 'EXST1'), Kf=get_required_value(data, 'Kf', 'EXST1'), Tf=get_required_value(data, 'Tf', 'EXST1'), V_ref=data.get('V_ref', None))

def sienna_exst1_to_json(value: SiennaEXST1) -> dict[str, Any]:
    """Write every EXST1 slot to explicit schema property names.

    :param value: Typed EXST1 object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Tr': value.Tr, 'Vi_lim': sienna_min_max_to_json(value.Vi_lim), 'Tc': value.Tc, 'Tb': value.Tb, 'Ka': value.Ka, 'Ta': value.Ta, 'Vr_lim': sienna_min_max_to_json(value.Vr_lim), 'Kc': value.Kc, 'Kf': value.Kf, 'Tf': value.Tf, 'V_ref': value.V_ref}
