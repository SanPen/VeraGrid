# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna DbdPnts schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaDbdPnts(SiennaSchemaModel):
    """Expose every declared DbdPnts property through fixed slots."""

    __slots__ = ('dbd1', 'dbd2',)

    def __init__(self, dbd1: float, dbd2: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.dbd1: float = dbd1
        self.dbd2: float = dbd2


def parse_sienna_dbd_pnts(data: dict[str, Any]) -> SiennaDbdPnts:
    """Parse declared DbdPnts properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed DbdPnts object.
    """
    return SiennaDbdPnts(dbd1=data.get('dbd1', None), dbd2=data.get('dbd2', None))


def sienna_dbd_pnts_to_json(value: SiennaDbdPnts) -> dict[str, Any]:
    """Write every DbdPnts slot to explicit schema property names.

    :param value: Typed DbdPnts object.
    :return: JSON object with declared schema properties.
    """
    return {'dbd1': value.dbd1, 'dbd2': value.dbd2}
