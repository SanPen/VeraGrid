# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna InterruptibleStandardLoad schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.import_export_time_series_cost import SiennaImportExportTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.load_cost import SiennaLoadCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import SiennaMarketBidCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import SiennaMarketBidTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import SiennaLoadConformity

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaInterruptibleStandardLoad(SiennaSchemaModel):
    """Expose every declared InterruptibleStandardLoad property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'base_power', 'power_units', 'operation_cost', 'conformity', 'constant_active_power', 'constant_reactive_power', 'impedance_active_power', 'impedance_reactive_power', 'current_active_power', 'current_reactive_power', 'max_constant_active_power', 'max_constant_reactive_power', 'max_impedance_active_power', 'max_impedance_reactive_power', 'max_current_active_power', 'max_current_reactive_power', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, base_power: float, power_units: SiennaUnitSystem, operation_cost: SiennaLoadCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, conformity: SiennaLoadConformity, constant_active_power: float, constant_reactive_power: float, impedance_active_power: float, impedance_reactive_power: float, current_active_power: float, current_reactive_power: float, max_constant_active_power: float, max_constant_reactive_power: float, max_impedance_active_power: float, max_impedance_reactive_power: float, max_current_active_power: float, max_current_reactive_power: float, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.operation_cost: SiennaLoadCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.conformity: SiennaLoadConformity = conformity
        self.constant_active_power: float = constant_active_power
        self.constant_reactive_power: float = constant_reactive_power
        self.impedance_active_power: float = impedance_active_power
        self.impedance_reactive_power: float = impedance_reactive_power
        self.current_active_power: float = current_active_power
        self.current_reactive_power: float = current_reactive_power
        self.max_constant_active_power: float = max_constant_active_power
        self.max_constant_reactive_power: float = max_constant_reactive_power
        self.max_impedance_active_power: float = max_impedance_active_power
        self.max_impedance_reactive_power: float = max_impedance_reactive_power
        self.max_current_active_power: float = max_current_active_power
        self.max_current_reactive_power: float = max_current_reactive_power
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_interruptible_standard_load(data: dict[str, Any]) -> SiennaInterruptibleStandardLoad:
    """Parse declared InterruptibleStandardLoad properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed InterruptibleStandardLoad object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import parse_sienna_load_conformity
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaInterruptibleStandardLoad(id=get_required_value(data, 'id', 'InterruptibleStandardLoad'), name=get_required_value(data, 'name', 'InterruptibleStandardLoad'), available=get_required_value(data, 'available', 'InterruptibleStandardLoad'), bus=get_required_value(data, 'bus', 'InterruptibleStandardLoad'), base_power=get_required_value(data, 'base_power', 'InterruptibleStandardLoad'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'InterruptibleStandardLoad')), operation_cost=parse_sienna_schema_union((SiennaObjectKind.LoadCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'InterruptibleStandardLoad')), conformity=None if data.get('conformity', None) is None else parse_sienna_load_conformity(data.get('conformity', None)), constant_active_power=data.get('constant_active_power', None), constant_reactive_power=data.get('constant_reactive_power', None), impedance_active_power=data.get('impedance_active_power', None), impedance_reactive_power=data.get('impedance_reactive_power', None), current_active_power=data.get('current_active_power', None), current_reactive_power=data.get('current_reactive_power', None), max_constant_active_power=data.get('max_constant_active_power', None), max_constant_reactive_power=data.get('max_constant_reactive_power', None), max_impedance_active_power=data.get('max_impedance_active_power', None), max_impedance_reactive_power=data.get('max_impedance_reactive_power', None), max_current_active_power=data.get('max_current_active_power', None), max_current_reactive_power=data.get('max_current_reactive_power', None), dynamic_injector=data.get('dynamic_injector', None))

def sienna_interruptible_standard_load_to_json(value: SiennaInterruptibleStandardLoad) -> dict[str, Any]:
    """Write every InterruptibleStandardLoad slot to explicit schema property names.

    :param value: Typed InterruptibleStandardLoad object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import sienna_load_conformity_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'operation_cost': write_sienna_schema_union((SiennaObjectKind.LoadCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), value.operation_cost), 'conformity': None if value.conformity is None else sienna_load_conformity_to_json(value.conformity), 'constant_active_power': value.constant_active_power, 'constant_reactive_power': value.constant_reactive_power, 'impedance_active_power': value.impedance_active_power, 'impedance_reactive_power': value.impedance_reactive_power, 'current_active_power': value.current_active_power, 'current_reactive_power': value.current_reactive_power, 'max_constant_active_power': value.max_constant_active_power, 'max_constant_reactive_power': value.max_constant_reactive_power, 'max_impedance_active_power': value.max_impedance_active_power, 'max_impedance_reactive_power': value.max_impedance_reactive_power, 'max_current_active_power': value.max_current_active_power, 'max_current_reactive_power': value.max_current_reactive_power, 'dynamic_injector': value.dynamic_injector}
