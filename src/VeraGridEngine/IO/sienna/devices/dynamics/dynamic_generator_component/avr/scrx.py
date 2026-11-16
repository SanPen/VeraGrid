# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SCRX schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSCRX(SiennaSchemaModel):
    """Expose every declared SCRX property through fixed slots."""

    __slots__ = ('id', 'Ta_Tb', 'Tb', 'K', 'Te', 'Efd_lim', 'switch', 'rc_rfd', 'V_ref',)

    def __init__(self, id: int, Ta_Tb: float, Tb: float, K: float, Te: float, Efd_lim: SiennaMinMax, switch: int, rc_rfd: float, V_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Ta_Tb: float = Ta_Tb
        self.Tb: float = Tb
        self.K: float = K
        self.Te: float = Te
        self.Efd_lim: SiennaMinMax = Efd_lim
        self.switch: int = switch
        self.rc_rfd: float = rc_rfd
        self.V_ref: float = V_ref


def parse_sienna_scrx(data: dict[str, Any]) -> SiennaSCRX:
    """Parse declared SCRX properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SCRX object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaSCRX(id=get_required_value(data, 'id', 'SCRX'), Ta_Tb=get_required_value(data, 'Ta_Tb', 'SCRX'), Tb=get_required_value(data, 'Tb', 'SCRX'), K=get_required_value(data, 'K', 'SCRX'), Te=get_required_value(data, 'Te', 'SCRX'), Efd_lim=parse_sienna_min_max(get_required_value(data, 'Efd_lim', 'SCRX')), switch=get_required_value(data, 'switch', 'SCRX'), rc_rfd=get_required_value(data, 'rc_rfd', 'SCRX'), V_ref=data.get('V_ref', None))

def sienna_scrx_to_json(value: SiennaSCRX) -> dict[str, Any]:
    """Write every SCRX slot to explicit schema property names.

    :param value: Typed SCRX object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'Ta_Tb': value.Ta_Tb, 'Tb': value.Tb, 'K': value.K, 'Te': value.Te, 'Efd_lim': sienna_min_max_to_json(value.Efd_lim), 'switch': value.switch, 'rc_rfd': value.rc_rfd, 'V_ref': value.V_ref}
