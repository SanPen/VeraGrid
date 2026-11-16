# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna StorageTechnology schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.in_out import SiennaInOut
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import SiennaPrimeMovers
    from VeraGridEngine.IO.sienna.devices.core.common.storage_capital_cost import SiennaStorageCapitalCost
    from VeraGridEngine.IO.sienna.devices.core.common.storage_cost import SiennaStorageCost
    from VeraGridEngine.IO.sienna.devices.core.common.storage_tech import SiennaStorageTech
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import SiennaTechnologyFinancialData

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaStorageTechnology(SiennaSchemaModel):
    """Expose every declared StorageTechnology property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'region', 'power_systems_type', 'min_discharge_fraction', 'prime_mover_type', 'storage_tech', 'capital_costs', 'operation_costs', 'unit_size_discharge', 'unit_size_charge', 'unit_size_energy', 'capacity_limits_charge', 'capacity_limits_discharge', 'capacity_limits_energy', 'duration_limits', 'efficiency', 'losses', 'lifetime', 'financial_data',)

    def __init__(self, id: int, name: str, available: bool, region: list[int], power_systems_type: str, min_discharge_fraction: float, prime_mover_type: SiennaPrimeMovers, storage_tech: SiennaStorageTech, capital_costs: SiennaStorageCapitalCost, operation_costs: SiennaStorageCost, unit_size_discharge: float, unit_size_charge: float, unit_size_energy: float, capacity_limits_charge: str | int | float | bool | None, capacity_limits_discharge: str | int | float | bool | None, capacity_limits_energy: str | int | float | bool | None, duration_limits: SiennaMinMax, efficiency: SiennaInOut, losses: float, lifetime: int, financial_data: SiennaTechnologyFinancialData) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.region: list[int] = region
        self.power_systems_type: str = power_systems_type
        self.min_discharge_fraction: float = min_discharge_fraction
        self.prime_mover_type: SiennaPrimeMovers = prime_mover_type
        self.storage_tech: SiennaStorageTech = storage_tech
        self.capital_costs: SiennaStorageCapitalCost = capital_costs
        self.operation_costs: SiennaStorageCost = operation_costs
        self.unit_size_discharge: float = unit_size_discharge
        self.unit_size_charge: float = unit_size_charge
        self.unit_size_energy: float = unit_size_energy
        self.capacity_limits_charge: str | int | float | bool | None = capacity_limits_charge
        self.capacity_limits_discharge: str | int | float | bool | None = capacity_limits_discharge
        self.capacity_limits_energy: str | int | float | bool | None = capacity_limits_energy
        self.duration_limits: SiennaMinMax = duration_limits
        self.efficiency: SiennaInOut = efficiency
        self.losses: float = losses
        self.lifetime: int = lifetime
        self.financial_data: SiennaTechnologyFinancialData = financial_data


def parse_sienna_storage_technology(data: dict[str, Any]) -> SiennaStorageTechnology:
    """Parse declared StorageTechnology properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed StorageTechnology object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.in_out import parse_sienna_in_out
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import parse_sienna_prime_movers
    from VeraGridEngine.IO.sienna.devices.core.common.storage_capital_cost import parse_sienna_storage_capital_cost
    from VeraGridEngine.IO.sienna.devices.core.common.storage_cost import parse_sienna_storage_cost
    from VeraGridEngine.IO.sienna.devices.core.common.storage_tech import parse_sienna_storage_tech
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import parse_sienna_technology_financial_data
    return SiennaStorageTechnology(id=get_required_value(data, 'id', 'StorageTechnology'), name=get_required_value(data, 'name', 'StorageTechnology'), available=get_required_value(data, 'available', 'StorageTechnology'), region=data.get('region', None), power_systems_type=get_required_value(data, 'power_systems_type', 'StorageTechnology'), min_discharge_fraction=data.get('min_discharge_fraction', None), prime_mover_type=None if data.get('prime_mover_type', None) is None else parse_sienna_prime_movers(data.get('prime_mover_type', None)), storage_tech=parse_sienna_storage_tech(get_required_value(data, 'storage_tech', 'StorageTechnology')), capital_costs=None if data.get('capital_costs', None) is None else parse_sienna_storage_capital_cost(data.get('capital_costs', None)), operation_costs=None if data.get('operation_costs', None) is None else parse_sienna_storage_cost(data.get('operation_costs', None)), unit_size_discharge=data.get('unit_size_discharge', None), unit_size_charge=data.get('unit_size_charge', None), unit_size_energy=data.get('unit_size_energy', None), capacity_limits_charge=data.get('capacity_limits_charge', None), capacity_limits_discharge=data.get('capacity_limits_discharge', None), capacity_limits_energy=data.get('capacity_limits_energy', None), duration_limits=None if data.get('duration_limits', None) is None else parse_sienna_min_max(data.get('duration_limits', None)), efficiency=None if data.get('efficiency', None) is None else parse_sienna_in_out(data.get('efficiency', None)), losses=data.get('losses', None), lifetime=data.get('lifetime', None), financial_data=parse_sienna_technology_financial_data(get_required_value(data, 'financial_data', 'StorageTechnology')))

def sienna_storage_technology_to_json(value: SiennaStorageTechnology) -> dict[str, Any]:
    """Write every StorageTechnology slot to explicit schema property names.

    :param value: Typed StorageTechnology object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.in_out import sienna_in_out_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import sienna_prime_movers_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.storage_capital_cost import sienna_storage_capital_cost_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.storage_cost import sienna_storage_cost_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.storage_tech import sienna_storage_tech_to_json
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import sienna_technology_financial_data_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'region': value.region, 'power_systems_type': value.power_systems_type, 'min_discharge_fraction': value.min_discharge_fraction, 'prime_mover_type': None if value.prime_mover_type is None else sienna_prime_movers_to_json(value.prime_mover_type), 'storage_tech': sienna_storage_tech_to_json(value.storage_tech), 'capital_costs': None if value.capital_costs is None else sienna_storage_capital_cost_to_json(value.capital_costs), 'operation_costs': None if value.operation_costs is None else sienna_storage_cost_to_json(value.operation_costs), 'unit_size_discharge': value.unit_size_discharge, 'unit_size_charge': value.unit_size_charge, 'unit_size_energy': value.unit_size_energy, 'capacity_limits_charge': value.capacity_limits_charge, 'capacity_limits_discharge': value.capacity_limits_discharge, 'capacity_limits_energy': value.capacity_limits_energy, 'duration_limits': None if value.duration_limits is None else sienna_min_max_to_json(value.duration_limits), 'efficiency': None if value.efficiency is None else sienna_in_out_to_json(value.efficiency), 'losses': value.losses, 'lifetime': value.lifetime, 'financial_data': sienna_technology_financial_data_to_json(value.financial_data)}
