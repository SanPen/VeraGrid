# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PSSFixed schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPSSFixed(SiennaSchemaModel):
    """Expose every declared PSSFixed property through fixed slots."""

    __slots__ = ('id', 'V_pss',)

    def __init__(self, id: int, V_pss: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.V_pss: float = V_pss


def parse_sienna_pss_fixed(data: dict[str, Any]) -> SiennaPSSFixed:
    """Parse declared PSSFixed properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PSSFixed object.
    """
    return SiennaPSSFixed(id=get_required_value(data, 'id', 'PSSFixed'), V_pss=get_required_value(data, 'V_pss', 'PSSFixed'))


def sienna_pss_fixed_to_json(value: SiennaPSSFixed) -> dict[str, Any]:
    """Write every PSSFixed slot to explicit schema property names.

    :param value: Typed PSSFixed object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'V_pss': value.V_pss}
