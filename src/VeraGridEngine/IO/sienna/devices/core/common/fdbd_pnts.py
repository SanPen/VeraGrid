# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FdbdPnts schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFdbdPnts(SiennaSchemaModel):
    """Expose every declared FdbdPnts property through fixed slots."""

    __slots__ = ('fdbd1', 'fdbd2',)

    def __init__(self, fdbd1: float, fdbd2: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.fdbd1: float = fdbd1
        self.fdbd2: float = fdbd2


def parse_sienna_fdbd_pnts(data: dict[str, Any]) -> SiennaFdbdPnts:
    """Parse declared FdbdPnts properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FdbdPnts object.
    """
    return SiennaFdbdPnts(fdbd1=data.get('fdbd1', None), fdbd2=data.get('fdbd2', None))


def sienna_fdbd_pnts_to_json(value: SiennaFdbdPnts) -> dict[str, Any]:
    """Write every FdbdPnts slot to explicit schema property names.

    :param value: Typed FdbdPnts object.
    :return: JSON object with declared schema properties.
    """
    return {'fdbd1': value.fdbd1, 'fdbd2': value.fdbd2}
