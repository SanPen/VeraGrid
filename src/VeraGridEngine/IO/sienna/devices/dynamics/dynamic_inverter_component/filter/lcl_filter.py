# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna LCLFilter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaLCLFilter(SiennaSchemaModel):
    """Expose every declared LCLFilter property through fixed slots."""

    __slots__ = ('lf', 'rf', 'cf', 'lg', 'rg',)

    def __init__(self, lf: float, rf: float, cf: float, lg: float, rg: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.lf: float = lf
        self.rf: float = rf
        self.cf: float = cf
        self.lg: float = lg
        self.rg: float = rg


def parse_sienna_lcl_filter(data: dict[str, Any]) -> SiennaLCLFilter:
    """Parse declared LCLFilter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed LCLFilter object.
    """
    return SiennaLCLFilter(lf=get_required_value(data, 'lf', 'LCLFilter'), rf=get_required_value(data, 'rf', 'LCLFilter'), cf=get_required_value(data, 'cf', 'LCLFilter'), lg=get_required_value(data, 'lg', 'LCLFilter'), rg=get_required_value(data, 'rg', 'LCLFilter'))


def sienna_lcl_filter_to_json(value: SiennaLCLFilter) -> dict[str, Any]:
    """Write every LCLFilter slot to explicit schema property names.

    :param value: Typed LCLFilter object.
    :return: JSON object with declared schema properties.
    """
    return {'lf': value.lf, 'rf': value.rf, 'cf': value.cf, 'lg': value.lg, 'rg': value.rg}
