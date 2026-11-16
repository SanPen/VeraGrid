# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HydroReservoirCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHydroReservoirCost(SiennaSchemaModel):
    """Expose every declared HydroReservoirCost property through fixed slots."""

    __slots__ = ('cost_type', 'level_shortage_cost', 'level_surplus_cost', 'spillage_cost',)

    def __init__(self, cost_type: str, level_shortage_cost: float, level_surplus_cost: float, spillage_cost: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.cost_type: str = cost_type
        self.level_shortage_cost: float = level_shortage_cost
        self.level_surplus_cost: float = level_surplus_cost
        self.spillage_cost: float = spillage_cost


def parse_sienna_hydro_reservoir_cost(data: dict[str, Any]) -> SiennaHydroReservoirCost:
    """Parse declared HydroReservoirCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HydroReservoirCost object.
    """
    return SiennaHydroReservoirCost(cost_type=data.get('cost_type', None), level_shortage_cost=data.get('level_shortage_cost', None), level_surplus_cost=data.get('level_surplus_cost', None), spillage_cost=data.get('spillage_cost', None))


def sienna_hydro_reservoir_cost_to_json(value: SiennaHydroReservoirCost) -> dict[str, Any]:
    """Write every HydroReservoirCost slot to explicit schema property names.

    :param value: Typed HydroReservoirCost object.
    :return: JSON object with declared schema properties.
    """
    return {'cost_type': value.cost_type, 'level_shortage_cost': value.level_shortage_cost, 'level_surplus_cost': value.level_surplus_cost, 'spillage_cost': value.spillage_cost}
