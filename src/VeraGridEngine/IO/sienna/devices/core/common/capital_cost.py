# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CapitalCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import SiennaValueCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCapitalCost(SiennaSchemaModel):
    """Expose every declared CapitalCost property through fixed slots."""

    __slots__ = ('capital_cost', 'interconnection_cost',)

    def __init__(self, capital_cost: SiennaValueCurve, interconnection_cost: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.capital_cost: SiennaValueCurve = capital_cost
        self.interconnection_cost: float = interconnection_cost


def parse_sienna_capital_cost(data: dict[str, Any]) -> SiennaCapitalCost:
    """Parse declared CapitalCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed CapitalCost object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
    return SiennaCapitalCost(capital_cost=parse_sienna_value_curve(get_required_value(data, 'capital_cost', 'CapitalCost')), interconnection_cost=data.get('interconnection_cost', None))

def sienna_capital_cost_to_json(value: SiennaCapitalCost) -> dict[str, Any]:
    """Write every CapitalCost slot to explicit schema property names.

    :param value: Typed CapitalCost object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import sienna_value_curve_to_json
    return {'capital_cost': sienna_value_curve_to_json(value.capital_cost), 'interconnection_cost': value.interconnection_cost}
