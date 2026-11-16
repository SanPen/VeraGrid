# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ShiftablePowerLoad schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.import_export_time_series_cost import SiennaImportExportTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.load_cost import SiennaLoadCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import SiennaMarketBidCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import SiennaMarketBidTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaShiftablePowerLoad(SiennaSchemaModel):
    """Expose every declared ShiftablePowerLoad property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'active_power', 'active_power_limits', 'reactive_power', 'max_active_power', 'max_reactive_power', 'base_power', 'power_units', 'load_balance_time_horizon', 'operation_cost', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, active_power: float, active_power_limits: SiennaMinMax, reactive_power: float, max_active_power: float, max_reactive_power: float, base_power: float, power_units: SiennaUnitSystem, load_balance_time_horizon: int, operation_cost: SiennaLoadCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.active_power: float = active_power
        self.active_power_limits: SiennaMinMax = active_power_limits
        self.reactive_power: float = reactive_power
        self.max_active_power: float = max_active_power
        self.max_reactive_power: float = max_reactive_power
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.load_balance_time_horizon: int = load_balance_time_horizon
        self.operation_cost: SiennaLoadCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_shiftable_power_load(data: dict[str, Any]) -> SiennaShiftablePowerLoad:
    """Parse declared ShiftablePowerLoad properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ShiftablePowerLoad object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaShiftablePowerLoad(id=get_required_value(data, 'id', 'ShiftablePowerLoad'), name=get_required_value(data, 'name', 'ShiftablePowerLoad'), available=get_required_value(data, 'available', 'ShiftablePowerLoad'), bus=get_required_value(data, 'bus', 'ShiftablePowerLoad'), active_power=get_required_value(data, 'active_power', 'ShiftablePowerLoad'), active_power_limits=parse_sienna_min_max(get_required_value(data, 'active_power_limits', 'ShiftablePowerLoad')), reactive_power=get_required_value(data, 'reactive_power', 'ShiftablePowerLoad'), max_active_power=get_required_value(data, 'max_active_power', 'ShiftablePowerLoad'), max_reactive_power=get_required_value(data, 'max_reactive_power', 'ShiftablePowerLoad'), base_power=get_required_value(data, 'base_power', 'ShiftablePowerLoad'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'ShiftablePowerLoad')), load_balance_time_horizon=get_required_value(data, 'load_balance_time_horizon', 'ShiftablePowerLoad'), operation_cost=parse_sienna_schema_union((SiennaObjectKind.LoadCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'ShiftablePowerLoad')), dynamic_injector=data.get('dynamic_injector', None))

def sienna_shiftable_power_load_to_json(value: SiennaShiftablePowerLoad) -> dict[str, Any]:
    """Write every ShiftablePowerLoad slot to explicit schema property names.

    :param value: Typed ShiftablePowerLoad object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'active_power': value.active_power, 'active_power_limits': sienna_min_max_to_json(value.active_power_limits), 'reactive_power': value.reactive_power, 'max_active_power': value.max_active_power, 'max_reactive_power': value.max_reactive_power, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'load_balance_time_horizon': value.load_balance_time_horizon, 'operation_cost': write_sienna_schema_union((SiennaObjectKind.LoadCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), value.operation_cost), 'dynamic_injector': value.dynamic_injector}
