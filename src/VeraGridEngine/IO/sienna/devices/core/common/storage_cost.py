# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna StorageCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.charge_discharge import SiennaChargeDischarge
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import SiennaCostCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaStorageCost(SiennaSchemaModel):
    """Expose every declared StorageCost property through fixed slots."""

    __slots__ = ('cost_type', 'charge_variable_cost', 'discharge_variable_cost', 'fixed', 'shut_down', 'start_up', 'energy_shortage_cost', 'energy_surplus_cost',)

    def __init__(self, cost_type: str, charge_variable_cost: SiennaCostCurve, discharge_variable_cost: SiennaCostCurve, fixed: float, shut_down: float, start_up: float | SiennaChargeDischarge, energy_shortage_cost: float, energy_surplus_cost: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.cost_type: str = cost_type
        self.charge_variable_cost: SiennaCostCurve = charge_variable_cost
        self.discharge_variable_cost: SiennaCostCurve = discharge_variable_cost
        self.fixed: float = fixed
        self.shut_down: float = shut_down
        self.start_up: float | SiennaChargeDischarge = start_up
        self.energy_shortage_cost: float = energy_shortage_cost
        self.energy_surplus_cost: float = energy_surplus_cost


def parse_sienna_storage_cost(data: dict[str, Any]) -> SiennaStorageCost:
    """Parse declared StorageCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed StorageCost object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import parse_sienna_cost_curve
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaStorageCost(cost_type=data.get('cost_type', None), charge_variable_cost=None if data.get('charge_variable_cost', None) is None else parse_sienna_cost_curve(data.get('charge_variable_cost', None)), discharge_variable_cost=None if data.get('discharge_variable_cost', None) is None else parse_sienna_cost_curve(data.get('discharge_variable_cost', None)), fixed=get_required_value(data, 'fixed', 'StorageCost'), shut_down=get_required_value(data, 'shut_down', 'StorageCost'), start_up=parse_sienna_schema_union((SiennaObjectKind.ChargeDischarge,), get_required_value(data, 'start_up', 'StorageCost')), energy_shortage_cost=data.get('energy_shortage_cost', None), energy_surplus_cost=data.get('energy_surplus_cost', None))

def sienna_storage_cost_to_json(value: SiennaStorageCost) -> dict[str, Any]:
    """Write every StorageCost slot to explicit schema property names.

    :param value: Typed StorageCost object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import sienna_cost_curve_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'cost_type': value.cost_type, 'charge_variable_cost': None if value.charge_variable_cost is None else sienna_cost_curve_to_json(value.charge_variable_cost), 'discharge_variable_cost': None if value.discharge_variable_cost is None else sienna_cost_curve_to_json(value.discharge_variable_cost), 'fixed': value.fixed, 'shut_down': value.shut_down, 'start_up': write_sienna_schema_union((SiennaObjectKind.ChargeDischarge,), value.start_up), 'energy_shortage_cost': value.energy_shortage_cost, 'energy_surplus_cost': value.energy_surplus_cost}
