# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna StorageCapitalCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import SiennaValueCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaStorageCapitalCost(SiennaSchemaModel):
    """Expose every declared StorageCapitalCost property through fixed slots."""

    __slots__ = ('charge_capital_cost', 'discharge_capital_cost', 'energy_capital_cost', 'interconnection_cost',)

    def __init__(self, charge_capital_cost: SiennaValueCurve, discharge_capital_cost: SiennaValueCurve, energy_capital_cost: SiennaValueCurve, interconnection_cost: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.charge_capital_cost: SiennaValueCurve = charge_capital_cost
        self.discharge_capital_cost: SiennaValueCurve = discharge_capital_cost
        self.energy_capital_cost: SiennaValueCurve = energy_capital_cost
        self.interconnection_cost: float = interconnection_cost


def parse_sienna_storage_capital_cost(data: dict[str, Any]) -> SiennaStorageCapitalCost:
    """Parse declared StorageCapitalCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed StorageCapitalCost object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
    return SiennaStorageCapitalCost(charge_capital_cost=parse_sienna_value_curve(get_required_value(data, 'charge_capital_cost', 'StorageCapitalCost')), discharge_capital_cost=parse_sienna_value_curve(get_required_value(data, 'discharge_capital_cost', 'StorageCapitalCost')), energy_capital_cost=parse_sienna_value_curve(get_required_value(data, 'energy_capital_cost', 'StorageCapitalCost')), interconnection_cost=get_required_value(data, 'interconnection_cost', 'StorageCapitalCost'))

def sienna_storage_capital_cost_to_json(value: SiennaStorageCapitalCost) -> dict[str, Any]:
    """Write every StorageCapitalCost slot to explicit schema property names.

    :param value: Typed StorageCapitalCost object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import sienna_value_curve_to_json
    return {'charge_capital_cost': sienna_value_curve_to_json(value.charge_capital_cost), 'discharge_capital_cost': sienna_value_curve_to_json(value.discharge_capital_cost), 'energy_capital_cost': sienna_value_curve_to_json(value.energy_capital_cost), 'interconnection_cost': value.interconnection_cost}
