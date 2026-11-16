# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TGSimple schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTGSimple(SiennaSchemaModel):
    """Expose every declared TGSimple property through fixed slots."""

    __slots__ = ('id', 'd_t', 'Tm', 'P_ref',)

    def __init__(self, id: int, d_t: float, Tm: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.d_t: float = d_t
        self.Tm: float = Tm
        self.P_ref: float = P_ref


def parse_sienna_tg_simple(data: dict[str, Any]) -> SiennaTGSimple:
    """Parse declared TGSimple properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TGSimple object.
    """
    return SiennaTGSimple(id=get_required_value(data, 'id', 'TGSimple'), d_t=get_required_value(data, 'd_t', 'TGSimple'), Tm=get_required_value(data, 'Tm', 'TGSimple'), P_ref=data.get('P_ref', None))


def sienna_tg_simple_to_json(value: SiennaTGSimple) -> dict[str, Any]:
    """Write every TGSimple slot to explicit schema property names.

    :param value: Typed TGSimple object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'd_t': value.d_t, 'Tm': value.Tm, 'P_ref': value.P_ref}
