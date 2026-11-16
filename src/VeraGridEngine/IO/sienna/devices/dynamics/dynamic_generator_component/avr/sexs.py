# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SEXS schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSEXS(SiennaSchemaModel):
    """Expose every declared SEXS property through fixed slots."""

    __slots__ = ('id', 'Ta_Tb', 'Tb', 'K', 'Te', 'V_lim', 'V_ref',)

    def __init__(self, id: int, Ta_Tb: float, Tb: float, K: float, Te: float, V_lim: SiennaMinMax, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Ta_Tb: float = Ta_Tb
        self.Tb: float = Tb
        self.K: float = K
        self.Te: float = Te
        self.V_lim: SiennaMinMax = V_lim
        self.V_ref: float = V_ref


def parse_sienna_sexs(data: dict[str, Any]) -> SiennaSEXS:
    """Parse declared SEXS properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SEXS object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaSEXS(id=get_required_value(data, 'id', 'SEXS'), Ta_Tb=get_required_value(data, 'Ta_Tb', 'SEXS'), Tb=get_required_value(data, 'Tb', 'SEXS'), K=get_required_value(data, 'K', 'SEXS'), Te=get_required_value(data, 'Te', 'SEXS'), V_lim=parse_sienna_min_max(get_required_value(data, 'V_lim', 'SEXS')), V_ref=data.get('V_ref', None))

def sienna_sexs_to_json(value: SiennaSEXS) -> dict[str, Any]:
    """Write every SEXS slot to explicit schema property names.

    :param value: Typed SEXS object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Ta_Tb': value.Ta_Tb, 'Tb': value.Tb, 'K': value.K, 'Te': value.Te, 'V_lim': sienna_min_max_to_json(value.V_lim), 'V_ref': value.V_ref}
