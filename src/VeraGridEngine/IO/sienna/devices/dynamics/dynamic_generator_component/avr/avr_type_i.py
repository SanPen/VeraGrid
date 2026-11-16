# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AVRTypeI schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAVRTypeI(SiennaSchemaModel):
    """Expose every declared AVRTypeI property through fixed slots."""

    __slots__ = ('id', 'Ka', 'Ke', 'Kf', 'Ta', 'Te', 'Tf', 'Tr', 'Va_lim', 'Ae', 'Be', 'V_ref',)

    def __init__(self, id: int, Ka: float, Ke: float, Kf: float, Ta: float, Te: float, Tf: float, Tr: float, Va_lim: SiennaMinMax, Ae: float, Be: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Ka: float = Ka
        self.Ke: float = Ke
        self.Kf: float = Kf
        self.Ta: float = Ta
        self.Te: float = Te
        self.Tf: float = Tf
        self.Tr: float = Tr
        self.Va_lim: SiennaMinMax = Va_lim
        self.Ae: float = Ae
        self.Be: float = Be
        self.V_ref: float = V_ref


def parse_sienna_avr_type_i(data: dict[str, Any]) -> SiennaAVRTypeI:
    """Parse declared AVRTypeI properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed AVRTypeI object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaAVRTypeI(id=get_required_value(data, 'id', 'AVRTypeI'), Ka=get_required_value(data, 'Ka', 'AVRTypeI'), Ke=get_required_value(data, 'Ke', 'AVRTypeI'), Kf=get_required_value(data, 'Kf', 'AVRTypeI'), Ta=get_required_value(data, 'Ta', 'AVRTypeI'), Te=get_required_value(data, 'Te', 'AVRTypeI'), Tf=get_required_value(data, 'Tf', 'AVRTypeI'), Tr=get_required_value(data, 'Tr', 'AVRTypeI'), Va_lim=parse_sienna_min_max(get_required_value(data, 'Va_lim', 'AVRTypeI')), Ae=get_required_value(data, 'Ae', 'AVRTypeI'), Be=get_required_value(data, 'Be', 'AVRTypeI'), V_ref=data.get('V_ref', None))

def sienna_avr_type_i_to_json(value: SiennaAVRTypeI) -> dict[str, Any]:
    """Write every AVRTypeI slot to explicit schema property names.

    :param value: Typed AVRTypeI object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Ka': value.Ka, 'Ke': value.Ke, 'Kf': value.Kf, 'Ta': value.Ta, 'Te': value.Te, 'Tf': value.Tf, 'Tr': value.Tr, 'Va_lim': sienna_min_max_to_json(value.Va_lim), 'Ae': value.Ae, 'Be': value.Be, 'V_ref': value.V_ref}
