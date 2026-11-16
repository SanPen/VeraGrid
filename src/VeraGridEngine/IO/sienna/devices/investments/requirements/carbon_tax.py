# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CarbonTax schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCarbonTax(SiennaSchemaModel):
    """Expose every declared CarbonTax property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'target_year', 'tax_dollars_per_ton',)

    def __init__(self, id: int, name: str, available: bool, target_year: int, tax_dollars_per_ton: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.target_year: int = target_year
        self.tax_dollars_per_ton: float = tax_dollars_per_ton


def parse_sienna_carbon_tax(data: dict[str, Any]) -> SiennaCarbonTax:
    """Parse declared CarbonTax properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed CarbonTax object.
    """
    return SiennaCarbonTax(id=get_required_value(data, 'id', 'CarbonTax'), name=get_required_value(data, 'name', 'CarbonTax'), available=get_required_value(data, 'available', 'CarbonTax'), target_year=data.get('target_year', None), tax_dollars_per_ton=data.get('tax_dollars_per_ton', None))


def sienna_carbon_tax_to_json(value: SiennaCarbonTax) -> dict[str, Any]:
    """Write every CarbonTax slot to explicit schema property names.

    :param value: Typed CarbonTax object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'name': value.name, 'available': value.available, 'target_year': value.target_year, 'tax_dollars_per_ton': value.tax_dollars_per_ton}
