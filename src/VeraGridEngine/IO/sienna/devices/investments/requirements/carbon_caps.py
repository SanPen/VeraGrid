# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CarbonCaps schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCarbonCaps(SiennaSchemaModel):
    """Expose every declared CarbonCaps property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'target_year', 'max_tons_mwh', 'max_mtons',)

    def __init__(self, id: int, name: str, available: bool, target_year: int, max_tons_mwh: float, max_mtons: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.target_year: int = target_year
        self.max_tons_mwh: float = max_tons_mwh
        self.max_mtons: float = max_mtons


def parse_sienna_carbon_caps(data: dict[str, Any]) -> SiennaCarbonCaps:
    """Parse declared CarbonCaps properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed CarbonCaps object.
    """
    return SiennaCarbonCaps(id=get_required_value(data, 'id', 'CarbonCaps'), name=get_required_value(data, 'name', 'CarbonCaps'), available=get_required_value(data, 'available', 'CarbonCaps'), target_year=data.get('target_year', None), max_tons_mwh=data.get('max_tons_mwh', None), max_mtons=data.get('max_mtons', None))


def sienna_carbon_caps_to_json(value: SiennaCarbonCaps) -> dict[str, Any]:
    """Write every CarbonCaps slot to explicit schema property names.

    :param value: Typed CarbonCaps object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name, 'available': value.available, 'target_year': value.target_year, 'max_tons_mwh': value.max_tons_mwh, 'max_mtons': value.max_mtons}
