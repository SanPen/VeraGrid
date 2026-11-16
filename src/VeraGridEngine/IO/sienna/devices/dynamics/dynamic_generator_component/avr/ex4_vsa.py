# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EX4VSA schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEX4VSA(SiennaSchemaModel):
    """Expose every declared EX4VSA property through fixed slots."""

    __slots__ = ('id', 'Iflim', 'd', 'f', 'Spar', 'K1', 'K2', 'Oel_lim', 'G', 'Ta', 'Tb', 'Te', 'E_lim', 'V_ref',)

    def __init__(self, id: int, Iflim: float, d: float, f: float, Spar: float, K1: float, K2: float, Oel_lim: SiennaMinMax, G: float, Ta: float, Tb: float, Te: float, E_lim: SiennaMinMax, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Iflim: float = Iflim
        self.d: float = d
        self.f: float = f
        self.Spar: float = Spar
        self.K1: float = K1
        self.K2: float = K2
        self.Oel_lim: SiennaMinMax = Oel_lim
        self.G: float = G
        self.Ta: float = Ta
        self.Tb: float = Tb
        self.Te: float = Te
        self.E_lim: SiennaMinMax = E_lim
        self.V_ref: float = V_ref


def parse_sienna_ex4_vsa(data: dict[str, Any]) -> SiennaEX4VSA:
    """Parse declared EX4VSA properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed EX4VSA object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaEX4VSA(id=get_required_value(data, 'id', 'EX4VSA'), Iflim=get_required_value(data, 'Iflim', 'EX4VSA'), d=get_required_value(data, 'd', 'EX4VSA'), f=get_required_value(data, 'f', 'EX4VSA'), Spar=get_required_value(data, 'Spar', 'EX4VSA'), K1=get_required_value(data, 'K1', 'EX4VSA'), K2=get_required_value(data, 'K2', 'EX4VSA'), Oel_lim=parse_sienna_min_max(get_required_value(data, 'Oel_lim', 'EX4VSA')), G=get_required_value(data, 'G', 'EX4VSA'), Ta=get_required_value(data, 'Ta', 'EX4VSA'), Tb=get_required_value(data, 'Tb', 'EX4VSA'), Te=get_required_value(data, 'Te', 'EX4VSA'), E_lim=parse_sienna_min_max(get_required_value(data, 'E_lim', 'EX4VSA')), V_ref=data.get('V_ref', None))

def sienna_ex4_vsa_to_json(value: SiennaEX4VSA) -> dict[str, Any]:
    """Write every EX4VSA slot to explicit schema property names.

    :param value: Typed EX4VSA object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Iflim': value.Iflim, 'd': value.d, 'f': value.f, 'Spar': value.Spar, 'K1': value.K1, 'K2': value.K2, 'Oel_lim': sienna_min_max_to_json(value.Oel_lim), 'G': value.G, 'Ta': value.Ta, 'Tb': value.Tb, 'Te': value.Te, 'E_lim': sienna_min_max_to_json(value.E_lim), 'V_ref': value.V_ref}
