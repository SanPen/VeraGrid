# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PSSSimple schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPSSSimple(SiennaSchemaModel):
    """Expose every declared PSSSimple property through fixed slots."""

    __slots__ = ('id', 'K_omega', 'K_p',)

    def __init__(self, id: int, K_omega: float, K_p: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.K_omega: float = K_omega
        self.K_p: float = K_p


def parse_sienna_pss_simple(data: dict[str, Any]) -> SiennaPSSSimple:
    """Parse declared PSSSimple properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PSSSimple object.
    """
    return SiennaPSSSimple(id=get_required_value(data, 'id', 'PSSSimple'), K_omega=get_required_value(data, 'K_omega', 'PSSSimple'), K_p=get_required_value(data, 'K_p', 'PSSSimple'))


def sienna_pss_simple_to_json(value: SiennaPSSSimple) -> dict[str, Any]:
    """Write every PSSSimple slot to explicit schema property names.

    :param value: Typed PSSSimple object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'K_omega': value.K_omega, 'K_p': value.K_p}
