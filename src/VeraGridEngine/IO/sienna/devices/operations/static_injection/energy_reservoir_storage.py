# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EnergyReservoirStorage schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.energy_unit_basis import SiennaEnergyUnitBasis
    from VeraGridEngine.IO.sienna.devices.core.common.import_export_time_series_cost import SiennaImportExportTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.in_out import SiennaInOut
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import SiennaMarketBidCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import SiennaMarketBidTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import SiennaPrimeMovers
    from VeraGridEngine.IO.sienna.devices.core.common.storage_cost import SiennaStorageCost
    from VeraGridEngine.IO.sienna.devices.core.common.storage_tech import SiennaStorageTech
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import SiennaUpDown

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEnergyReservoirStorage(SiennaSchemaModel):
    """Expose every declared EnergyReservoirStorage property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'prime_mover_type', 'storage_technology_type', 'storage_capacity', 'energy_units', 'storage_level_limits', 'initial_storage_capacity_level', 'rating', 'active_power', 'input_active_power_limits', 'output_active_power_limits', 'efficiency', 'reactive_power', 'reactive_power_limits', 'base_power', 'power_units', 'operation_cost', 'conversion_factor', 'storage_target', 'cycle_limits', 'ramp_limits', 'self_discharge', 'standing_loss', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, prime_mover_type: SiennaPrimeMovers, storage_technology_type: SiennaStorageTech, storage_capacity: float, energy_units: SiennaEnergyUnitBasis, storage_level_limits: SiennaMinMax, initial_storage_capacity_level: float, rating: float, active_power: float, input_active_power_limits: SiennaMinMax, output_active_power_limits: SiennaMinMax, efficiency: SiennaInOut, reactive_power: float, reactive_power_limits: SiennaMinMax, base_power: float, power_units: SiennaUnitSystem, operation_cost: SiennaStorageCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, conversion_factor: float, storage_target: float, cycle_limits: int, ramp_limits: SiennaUpDown, self_discharge: float, standing_loss: float, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.prime_mover_type: SiennaPrimeMovers = prime_mover_type
        self.storage_technology_type: SiennaStorageTech = storage_technology_type
        self.storage_capacity: float = storage_capacity
        self.energy_units: SiennaEnergyUnitBasis = energy_units
        self.storage_level_limits: SiennaMinMax = storage_level_limits
        self.initial_storage_capacity_level: float = initial_storage_capacity_level
        self.rating: float = rating
        self.active_power: float = active_power
        self.input_active_power_limits: SiennaMinMax = input_active_power_limits
        self.output_active_power_limits: SiennaMinMax = output_active_power_limits
        self.efficiency: SiennaInOut = efficiency
        self.reactive_power: float = reactive_power
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.operation_cost: SiennaStorageCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.conversion_factor: float = conversion_factor
        self.storage_target: float = storage_target
        self.cycle_limits: int = cycle_limits
        self.ramp_limits: SiennaUpDown = ramp_limits
        self.self_discharge: float = self_discharge
        self.standing_loss: float = standing_loss
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_energy_reservoir_storage(data: dict[str, Any]) -> SiennaEnergyReservoirStorage:
    """Parse declared EnergyReservoirStorage properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed EnergyReservoirStorage object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.energy_unit_basis import parse_sienna_energy_unit_basis
    from VeraGridEngine.IO.sienna.devices.core.common.in_out import parse_sienna_in_out
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import parse_sienna_prime_movers
    from VeraGridEngine.IO.sienna.devices.core.common.storage_tech import parse_sienna_storage_tech
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import parse_sienna_up_down
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaEnergyReservoirStorage(id=get_required_value(data, 'id', 'EnergyReservoirStorage'), name=get_required_value(data, 'name', 'EnergyReservoirStorage'), available=get_required_value(data, 'available', 'EnergyReservoirStorage'), bus=get_required_value(data, 'bus', 'EnergyReservoirStorage'), prime_mover_type=parse_sienna_prime_movers(get_required_value(data, 'prime_mover_type', 'EnergyReservoirStorage')), storage_technology_type=parse_sienna_storage_tech(get_required_value(data, 'storage_technology_type', 'EnergyReservoirStorage')), storage_capacity=get_required_value(data, 'storage_capacity', 'EnergyReservoirStorage'), energy_units=None if data.get('energy_units', None) is None else parse_sienna_energy_unit_basis(data.get('energy_units', None)), storage_level_limits=parse_sienna_min_max(get_required_value(data, 'storage_level_limits', 'EnergyReservoirStorage')), initial_storage_capacity_level=get_required_value(data, 'initial_storage_capacity_level', 'EnergyReservoirStorage'), rating=get_required_value(data, 'rating', 'EnergyReservoirStorage'), active_power=get_required_value(data, 'active_power', 'EnergyReservoirStorage'), input_active_power_limits=parse_sienna_min_max(get_required_value(data, 'input_active_power_limits', 'EnergyReservoirStorage')), output_active_power_limits=parse_sienna_min_max(get_required_value(data, 'output_active_power_limits', 'EnergyReservoirStorage')), efficiency=parse_sienna_in_out(get_required_value(data, 'efficiency', 'EnergyReservoirStorage')), reactive_power=get_required_value(data, 'reactive_power', 'EnergyReservoirStorage'), reactive_power_limits=None if data.get('reactive_power_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_limits', None)), base_power=get_required_value(data, 'base_power', 'EnergyReservoirStorage'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'EnergyReservoirStorage')), operation_cost=parse_sienna_schema_union((SiennaObjectKind.StorageCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'EnergyReservoirStorage')), conversion_factor=data.get('conversion_factor', None), storage_target=data.get('storage_target', None), cycle_limits=data.get('cycle_limits', None), ramp_limits=None if data.get('ramp_limits', None) is None else parse_sienna_up_down(data.get('ramp_limits', None)), self_discharge=data.get('self_discharge', None), standing_loss=data.get('standing_loss', None), dynamic_injector=data.get('dynamic_injector', None))

def sienna_energy_reservoir_storage_to_json(value: SiennaEnergyReservoirStorage) -> dict[str, Any]:
    """Write every EnergyReservoirStorage slot to explicit schema property names.

    :param value: Typed EnergyReservoirStorage object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.energy_unit_basis import sienna_energy_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.in_out import sienna_in_out_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import sienna_prime_movers_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.storage_tech import sienna_storage_tech_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import sienna_up_down_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'prime_mover_type': sienna_prime_movers_to_json(value.prime_mover_type), 'storage_technology_type': sienna_storage_tech_to_json(value.storage_technology_type), 'storage_capacity': value.storage_capacity, 'energy_units': None if value.energy_units is None else sienna_energy_unit_basis_to_json(value.energy_units), 'storage_level_limits': sienna_min_max_to_json(value.storage_level_limits), 'initial_storage_capacity_level': value.initial_storage_capacity_level, 'rating': value.rating, 'active_power': value.active_power, 'input_active_power_limits': sienna_min_max_to_json(value.input_active_power_limits), 'output_active_power_limits': sienna_min_max_to_json(value.output_active_power_limits), 'efficiency': sienna_in_out_to_json(value.efficiency), 'reactive_power': value.reactive_power, 'reactive_power_limits': None if value.reactive_power_limits is None else sienna_min_max_to_json(value.reactive_power_limits), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'operation_cost': write_sienna_schema_union((SiennaObjectKind.StorageCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), value.operation_cost), 'conversion_factor': value.conversion_factor, 'storage_target': value.storage_target, 'cycle_limits': value.cycle_limits, 'ramp_limits': None if value.ramp_limits is None else sienna_up_down_to_json(value.ramp_limits), 'self_discharge': value.self_discharge, 'standing_loss': value.standing_loss, 'dynamic_injector': value.dynamic_injector}
