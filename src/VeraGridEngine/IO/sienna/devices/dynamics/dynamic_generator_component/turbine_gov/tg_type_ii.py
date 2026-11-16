# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TGTypeII schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTGTypeII(SiennaSchemaModel):
    """Expose every declared TGTypeII property through fixed slots."""

    __slots__ = ('id', 'R', 'T1', 'T2', 'tau_limits', 'P_ref',)

    def __init__(self, id: int, R: float, T1: float, T2: float, tau_limits: SiennaMinMax, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.R: float = R
        self.T1: float = T1
        self.T2: float = T2
        self.tau_limits: SiennaMinMax = tau_limits
        self.P_ref: float = P_ref


def parse_sienna_tg_type_ii(data: dict[str, Any]) -> SiennaTGTypeII:
    """Parse declared TGTypeII properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TGTypeII object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaTGTypeII(id=get_required_value(data, 'id', 'TGTypeII'), R=get_required_value(data, 'R', 'TGTypeII'), T1=get_required_value(data, 'T1', 'TGTypeII'), T2=get_required_value(data, 'T2', 'TGTypeII'), tau_limits=parse_sienna_min_max(get_required_value(data, 'tau_limits', 'TGTypeII')), P_ref=data.get('P_ref', None))

def sienna_tg_type_ii_to_json(value: SiennaTGTypeII) -> dict[str, Any]:
    """Write every TGTypeII slot to explicit schema property names.

    :param value: Typed TGTypeII object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.id, 'R': value.R, 'T1': value.T1, 'T2': value.T2, 'tau_limits': sienna_min_max_to_json(value.tau_limits), 'P_ref': value.P_ref}
