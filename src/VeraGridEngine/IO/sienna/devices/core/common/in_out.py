# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna InOut schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaInOut(SiennaSchemaModel):
    """Expose every declared InOut property through fixed slots."""

    __slots__ = ('in_', 'out',)

    def __init__(self, in_: float, out: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.in_: float = in_
        self.out: float = out


def parse_sienna_in_out(data: dict[str, Any]) -> SiennaInOut:
    """Parse declared InOut properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed InOut object.
    """
    return SiennaInOut(in_=data.get('in', None), out=data.get('out', None))


def sienna_in_out_to_json(value: SiennaInOut) -> dict[str, Any]:
    """Write every InOut slot to explicit schema property names.

    :param value: Typed InOut object.
    :return: JSON object with declared schema properties.
    """
    return {'in': value.in_, 'out': value.out}
