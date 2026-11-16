# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SupplyTechnology schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import SiennaCapitalCost
    from VeraGridEngine.IO.sienna.devices.core.common.generic_operation_cost import SiennaGenericOperationCost
    from VeraGridEngine.IO.sienna.devices.core.common.outage_factors import SiennaOutageFactors
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import SiennaPrimeMovers
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_fuels import SiennaThermalFuels
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import SiennaUpDown
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import SiennaTechnologyFinancialData

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSupplyTechnology(SiennaSchemaModel):
    """Expose every declared SupplyTechnology property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'power_systems_type', 'region', 'prime_mover_type', 'fuel', 'cofire_start_limits', 'cofire_level_limits', 'capital_costs', 'operation_costs', 'unit_size', 'capacity_limits', 'outage_factor', 'min_generation_fraction', 'ramp_limits', 'time_limits', 'start_fuel_mmbtu_per_mw', 'lifetime', 'financial_data',)

    def __init__(self, id: int, name: str, available: bool, power_systems_type: str, region: list[int], prime_mover_type: SiennaPrimeMovers, fuel: list[SiennaThermalFuels], cofire_start_limits: dict[str, object], cofire_level_limits: dict[str, object], capital_costs: SiennaCapitalCost, operation_costs: SiennaGenericOperationCost, unit_size: float, capacity_limits: str | int | float | bool | None, outage_factor: SiennaOutageFactors, min_generation_fraction: float, ramp_limits: SiennaUpDown, time_limits: SiennaUpDown, start_fuel_mmbtu_per_mw: float, lifetime: int, financial_data: SiennaTechnologyFinancialData) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.power_systems_type: str = power_systems_type
        self.region: list[int] = region
        self.prime_mover_type: SiennaPrimeMovers = prime_mover_type
        self.fuel: list[SiennaThermalFuels] = fuel
        self.cofire_start_limits: dict[str, object] = cofire_start_limits
        self.cofire_level_limits: dict[str, object] = cofire_level_limits
        self.capital_costs: SiennaCapitalCost = capital_costs
        self.operation_costs: SiennaGenericOperationCost = operation_costs
        self.unit_size: float = unit_size
        self.capacity_limits: str | int | float | bool | None = capacity_limits
        self.outage_factor: SiennaOutageFactors = outage_factor
        self.min_generation_fraction: float = min_generation_fraction
        self.ramp_limits: SiennaUpDown = ramp_limits
        self.time_limits: SiennaUpDown = time_limits
        self.start_fuel_mmbtu_per_mw: float = start_fuel_mmbtu_per_mw
        self.lifetime: int = lifetime
        self.financial_data: SiennaTechnologyFinancialData = financial_data


def parse_sienna_supply_technology(data: dict[str, Any]) -> SiennaSupplyTechnology:
    """Parse declared SupplyTechnology properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SupplyTechnology object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import parse_sienna_capital_cost
    from VeraGridEngine.IO.sienna.devices.core.common.generic_operation_cost import parse_sienna_generic_operation_cost
    from VeraGridEngine.IO.sienna.devices.core.common.outage_factors import parse_sienna_outage_factors
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import parse_sienna_prime_movers
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_fuels import parse_sienna_thermal_fuels
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import parse_sienna_up_down
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import parse_sienna_technology_financial_data
    return SiennaSupplyTechnology(id=get_required_value(data, 'id', 'SupplyTechnology'), name=get_required_value(data, 'name', 'SupplyTechnology'), available=data.get('available', None), power_systems_type=get_required_value(data, 'power_systems_type', 'SupplyTechnology'), region=data.get('region', None), prime_mover_type=None if data.get('prime_mover_type', None) is None else parse_sienna_prime_movers(data.get('prime_mover_type', None)), fuel=None if data.get('fuel', None) is None else [parse_sienna_thermal_fuels(item) for item in data.get('fuel', None)], cofire_start_limits=data.get('cofire_start_limits', None), cofire_level_limits=data.get('cofire_level_limits', None), capital_costs=None if data.get('capital_costs', None) is None else parse_sienna_capital_cost(data.get('capital_costs', None)), operation_costs=None if data.get('operation_costs', None) is None else parse_sienna_generic_operation_cost(data.get('operation_costs', None)), unit_size=data.get('unit_size', None), capacity_limits=data.get('capacity_limits', None), outage_factor=None if data.get('outage_factor', None) is None else parse_sienna_outage_factors(data.get('outage_factor', None)), min_generation_fraction=data.get('min_generation_fraction', None), ramp_limits=None if data.get('ramp_limits', None) is None else parse_sienna_up_down(data.get('ramp_limits', None)), time_limits=None if data.get('time_limits', None) is None else parse_sienna_up_down(data.get('time_limits', None)), start_fuel_mmbtu_per_mw=data.get('start_fuel_mmbtu_per_mw', None), lifetime=data.get('lifetime', None), financial_data=parse_sienna_technology_financial_data(get_required_value(data, 'financial_data', 'SupplyTechnology')))

def sienna_supply_technology_to_json(value: SiennaSupplyTechnology) -> dict[str, Any]:
    """Write every SupplyTechnology slot to explicit schema property names.

    :param value: Typed SupplyTechnology object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import sienna_capital_cost_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.generic_operation_cost import sienna_generic_operation_cost_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.outage_factors import sienna_outage_factors_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import sienna_prime_movers_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_fuels import sienna_thermal_fuels_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import sienna_up_down_to_json
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import sienna_technology_financial_data_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'power_systems_type': value.power_systems_type, 'region': value.region, 'prime_mover_type': None if value.prime_mover_type is None else sienna_prime_movers_to_json(value.prime_mover_type), 'fuel': None if value.fuel is None else [sienna_thermal_fuels_to_json(item) for item in value.fuel], 'cofire_start_limits': value.cofire_start_limits, 'cofire_level_limits': value.cofire_level_limits, 'capital_costs': None if value.capital_costs is None else sienna_capital_cost_to_json(value.capital_costs), 'operation_costs': None if value.operation_costs is None else sienna_generic_operation_cost_to_json(value.operation_costs), 'unit_size': value.unit_size, 'capacity_limits': value.capacity_limits, 'outage_factor': None if value.outage_factor is None else sienna_outage_factors_to_json(value.outage_factor), 'min_generation_fraction': value.min_generation_fraction, 'ramp_limits': None if value.ramp_limits is None else sienna_up_down_to_json(value.ramp_limits), 'time_limits': None if value.time_limits is None else sienna_up_down_to_json(value.time_limits), 'start_fuel_mmbtu_per_mw': value.start_fuel_mmbtu_per_mw, 'lifetime': value.lifetime, 'financial_data': sienna_technology_financial_data_to_json(value.financial_data)}
