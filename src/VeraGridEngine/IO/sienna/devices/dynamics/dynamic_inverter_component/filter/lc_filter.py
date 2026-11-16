# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna LCFilter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaLCFilter(SiennaSchemaModel):
    """Expose every declared LCFilter property through fixed slots."""

    __slots__ = ('lf', 'rf', 'cf',)

    def __init__(self, lf: float, rf: float, cf: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.lf: float = lf
        self.rf: float = rf
        self.cf: float = cf


def parse_sienna_lc_filter(data: dict[str, Any]) -> SiennaLCFilter:
    """Parse declared LCFilter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed LCFilter object.
    """
    return SiennaLCFilter(lf=get_required_value(data, 'lf', 'LCFilter'), rf=get_required_value(data, 'rf', 'LCFilter'), cf=get_required_value(data, 'cf', 'LCFilter'))


def sienna_lc_filter_to_json(value: SiennaLCFilter) -> dict[str, Any]:
    """Write every LCFilter slot to explicit schema property names.

    :param value: Typed LCFilter object.
    :return: JSON object with declared schema properties.
    """
    return {'lf': value.lf, 'rf': value.rf, 'cf': value.cf}
