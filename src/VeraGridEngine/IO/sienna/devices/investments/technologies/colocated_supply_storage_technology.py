# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ColocatedSupplyStorageTechnology schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import SiennaCapitalCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import SiennaProductionVariableCostCurve
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import SiennaTechnologyFinancialData

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaColocatedSupplyStorageTechnology(SiennaSchemaModel):
    """Expose every declared ColocatedSupplyStorageTechnology property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'power_systems_type', 'region', 'financial_data', 'supply_technology', 'storage_technology', 'inverter_capacity_limits', 'capital_costs_inverter', 'operation_costs_inverter', 'inverter_efficiency', 'inverter_supply_ratio',)

    def __init__(self, id: int, name: str, available: bool, power_systems_type: str, region: list[int], financial_data: SiennaTechnologyFinancialData, supply_technology: int, storage_technology: int, inverter_capacity_limits: SiennaMinMax, capital_costs_inverter: SiennaCapitalCost, operation_costs_inverter: SiennaProductionVariableCostCurve, inverter_efficiency: float, inverter_supply_ratio: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.power_systems_type: str = power_systems_type
        self.region: list[int] = region
        self.financial_data: SiennaTechnologyFinancialData = financial_data
        self.supply_technology: int = supply_technology
        self.storage_technology: int = storage_technology
        self.inverter_capacity_limits: SiennaMinMax = inverter_capacity_limits
        self.capital_costs_inverter: SiennaCapitalCost = capital_costs_inverter
        self.operation_costs_inverter: SiennaProductionVariableCostCurve = operation_costs_inverter
        self.inverter_efficiency: float = inverter_efficiency
        self.inverter_supply_ratio: float = inverter_supply_ratio


def parse_sienna_colocated_supply_storage_technology(data: dict[str, Any]) -> SiennaColocatedSupplyStorageTechnology:
    """Parse declared ColocatedSupplyStorageTechnology properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ColocatedSupplyStorageTechnology object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import parse_sienna_capital_cost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import parse_sienna_production_variable_cost_curve
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import parse_sienna_technology_financial_data
    return SiennaColocatedSupplyStorageTechnology(id=get_required_value(data, 'id', 'ColocatedSupplyStorageTechnology'), name=get_required_value(data, 'name', 'ColocatedSupplyStorageTechnology'), available=data.get('available', None), power_systems_type=get_required_value(data, 'power_systems_type', 'ColocatedSupplyStorageTechnology'), region=data.get('region', None), financial_data=parse_sienna_technology_financial_data(get_required_value(data, 'financial_data', 'ColocatedSupplyStorageTechnology')), supply_technology=get_required_value(data, 'supply_technology', 'ColocatedSupplyStorageTechnology'), storage_technology=get_required_value(data, 'storage_technology', 'ColocatedSupplyStorageTechnology'), inverter_capacity_limits=None if data.get('inverter_capacity_limits', None) is None else parse_sienna_min_max(data.get('inverter_capacity_limits', None)), capital_costs_inverter=parse_sienna_capital_cost(get_required_value(data, 'capital_costs_inverter', 'ColocatedSupplyStorageTechnology')), operation_costs_inverter=parse_sienna_production_variable_cost_curve(get_required_value(data, 'operation_costs_inverter', 'ColocatedSupplyStorageTechnology')), inverter_efficiency=get_required_value(data, 'inverter_efficiency', 'ColocatedSupplyStorageTechnology'), inverter_supply_ratio=get_required_value(data, 'inverter_supply_ratio', 'ColocatedSupplyStorageTechnology'))

def sienna_colocated_supply_storage_technology_to_json(value: SiennaColocatedSupplyStorageTechnology) -> dict[str, Any]:
    """Write every ColocatedSupplyStorageTechnology slot to explicit schema property names.

    :param value: Typed ColocatedSupplyStorageTechnology object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import sienna_capital_cost_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import sienna_production_variable_cost_curve_to_json
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import sienna_technology_financial_data_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'power_systems_type': value.power_systems_type, 'region': value.region, 'financial_data': sienna_technology_financial_data_to_json(value.financial_data), 'supply_technology': value.supply_technology, 'storage_technology': value.storage_technology, 'inverter_capacity_limits': None if value.inverter_capacity_limits is None else sienna_min_max_to_json(value.inverter_capacity_limits), 'capital_costs_inverter': sienna_capital_cost_to_json(value.capital_costs_inverter), 'operation_costs_inverter': sienna_production_variable_cost_curve_to_json(value.operation_costs_inverter), 'inverter_efficiency': value.inverter_efficiency, 'inverter_supply_ratio': value.inverter_supply_ratio}
