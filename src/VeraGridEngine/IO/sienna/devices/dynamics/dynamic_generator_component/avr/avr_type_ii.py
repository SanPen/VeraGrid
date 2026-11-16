# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AVRTypeII schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAVRTypeII(SiennaSchemaModel):
    """Expose every declared AVRTypeII property through fixed slots."""

    __slots__ = ('id', 'K0', 'T1', 'T2', 'T3', 'T4', 'Te', 'Tr', 'Va_lim', 'Ae', 'Be', 'V_ref',)

    def __init__(self, id: int, K0: float, T1: float, T2: float, T3: float, T4: float, Te: float, Tr: float, Va_lim: SiennaMinMax, Ae: float, Be: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.K0: float = K0
        self.T1: float = T1
        self.T2: float = T2
        self.T3: float = T3
        self.T4: float = T4
        self.Te: float = Te
        self.Tr: float = Tr
        self.Va_lim: SiennaMinMax = Va_lim
        self.Ae: float = Ae
        self.Be: float = Be
        self.V_ref: float = V_ref


def parse_sienna_avr_type_ii(data: dict[str, Any]) -> SiennaAVRTypeII:
    """Parse declared AVRTypeII properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed AVRTypeII object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaAVRTypeII(id=get_required_value(data, 'id', 'AVRTypeII'), K0=get_required_value(data, 'K0', 'AVRTypeII'), T1=get_required_value(data, 'T1', 'AVRTypeII'), T2=get_required_value(data, 'T2', 'AVRTypeII'), T3=get_required_value(data, 'T3', 'AVRTypeII'), T4=get_required_value(data, 'T4', 'AVRTypeII'), Te=get_required_value(data, 'Te', 'AVRTypeII'), Tr=get_required_value(data, 'Tr', 'AVRTypeII'), Va_lim=parse_sienna_min_max(get_required_value(data, 'Va_lim', 'AVRTypeII')), Ae=get_required_value(data, 'Ae', 'AVRTypeII'), Be=get_required_value(data, 'Be', 'AVRTypeII'), V_ref=data.get('V_ref', None))

def sienna_avr_type_ii_to_json(value: SiennaAVRTypeII) -> dict[str, Any]:
    """Write every AVRTypeII slot to explicit schema property names.

    :param value: Typed AVRTypeII object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'K0': value.K0, 'T1': value.T1, 'T2': value.T2, 'T3': value.T3, 'T4': value.T4, 'Te': value.Te, 'Tr': value.Tr, 'Va_lim': sienna_min_max_to_json(value.Va_lim), 'Ae': value.Ae, 'Be': value.Be, 'V_ref': value.V_ref}
