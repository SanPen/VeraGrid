# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AggregateTransportTechnology schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import SiennaCapitalCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import SiennaTechnologyFinancialData

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAggregateTransportTechnology(SiennaSchemaModel):
    """Expose every declared AggregateTransportTechnology property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'power_systems_type', 'start_region', 'end_region', 'capacity_limits', 'capital_costs', 'line_loss', 'unit_size', 'financial_data',)

    def __init__(self, id: int, name: str, available: bool, power_systems_type: str, start_region: int, end_region: int, capacity_limits: SiennaMinMax, capital_costs: SiennaCapitalCost, line_loss: float, unit_size: float, financial_data: SiennaTechnologyFinancialData) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.power_systems_type: str = power_systems_type
        self.start_region: int = start_region
        self.end_region: int = end_region
        self.capacity_limits: SiennaMinMax = capacity_limits
        self.capital_costs: SiennaCapitalCost = capital_costs
        self.line_loss: float = line_loss
        self.unit_size: float = unit_size
        self.financial_data: SiennaTechnologyFinancialData = financial_data


def parse_sienna_aggregate_transport_technology(data: dict[str, Any]) -> SiennaAggregateTransportTechnology:
    """Parse declared AggregateTransportTechnology properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed AggregateTransportTechnology object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import parse_sienna_capital_cost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import parse_sienna_technology_financial_data
    return SiennaAggregateTransportTechnology(id=get_required_value(data, 'id', 'AggregateTransportTechnology'), name=get_required_value(data, 'name', 'AggregateTransportTechnology'), available=get_required_value(data, 'available', 'AggregateTransportTechnology'), power_systems_type=get_required_value(data, 'power_systems_type', 'AggregateTransportTechnology'), start_region=get_required_value(data, 'start_region', 'AggregateTransportTechnology'), end_region=get_required_value(data, 'end_region', 'AggregateTransportTechnology'), capacity_limits=None if data.get('capacity_limits', None) is None else parse_sienna_min_max(data.get('capacity_limits', None)), capital_costs=None if data.get('capital_costs', None) is None else parse_sienna_capital_cost(data.get('capital_costs', None)), line_loss=data.get('line_loss', None), unit_size=data.get('unit_size', None), financial_data=parse_sienna_technology_financial_data(get_required_value(data, 'financial_data', 'AggregateTransportTechnology')))

def sienna_aggregate_transport_technology_to_json(value: SiennaAggregateTransportTechnology) -> dict[str, Any]:
    """Write every AggregateTransportTechnology slot to explicit schema property names.

    :param value: Typed AggregateTransportTechnology object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import sienna_capital_cost_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import sienna_technology_financial_data_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'power_systems_type': value.power_systems_type, 'start_region': value.start_region, 'end_region': value.end_region, 'capacity_limits': None if value.capacity_limits is None else sienna_min_max_to_json(value.capacity_limits), 'capital_costs': None if value.capital_costs is None else sienna_capital_cost_to_json(value.capital_costs), 'line_loss': value.line_loss, 'unit_size': value.unit_size, 'financial_data': sienna_technology_financial_data_to_json(value.financial_data)}
