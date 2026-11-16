# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TGFixed schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTGFixed(SiennaSchemaModel):
    """Expose every declared TGFixed property through fixed slots."""

    __slots__ = ('id', 'efficiency', 'P_ref',)

    def __init__(self, id: int, efficiency: float, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.efficiency: float = efficiency
        self.P_ref: float = P_ref


def parse_sienna_tg_fixed(data: dict[str, Any]) -> SiennaTGFixed:
    """Parse declared TGFixed properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TGFixed object.
    """
    return SiennaTGFixed(id=get_required_value(data, 'id', 'TGFixed'), efficiency=get_required_value(data, 'efficiency', 'TGFixed'), P_ref=data.get('P_ref', None))


def sienna_tg_fixed_to_json(value: SiennaTGFixed) -> dict[str, Any]:
    """Write every TGFixed slot to explicit schema property names.

    :param value: Typed TGFixed object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'efficiency': value.efficiency, 'P_ref': value.P_ref}
