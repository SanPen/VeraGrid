# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RLFilter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRLFilter(SiennaSchemaModel):
    """Expose every declared RLFilter property through fixed slots."""

    __slots__ = ('rf', 'lf',)

    def __init__(self, rf: float, lf: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.rf: float = rf
        self.lf: float = lf


def parse_sienna_rl_filter(data: dict[str, Any]) -> SiennaRLFilter:
    """Parse declared RLFilter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RLFilter object.
    """
    return SiennaRLFilter(rf=get_required_value(data, 'rf', 'RLFilter'), lf=get_required_value(data, 'lf', 'RLFilter'))


def sienna_rl_filter_to_json(value: SiennaRLFilter) -> dict[str, Any]:
    """Write every RLFilter slot to explicit schema property names.

    :param value: Typed RLFilter object.
    :return: JSON object with declared schema properties.
    """
    return {'rf': value.rf, 'lf': value.lf}
