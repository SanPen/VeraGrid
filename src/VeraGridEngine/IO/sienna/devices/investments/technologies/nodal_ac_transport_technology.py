# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna NodalACTransportTechnology schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import SiennaCapitalCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import SiennaTechnologyFinancialData

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaNodalACTransportTechnology(SiennaSchemaModel):
    """Expose every declared NodalACTransportTechnology property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'power_systems_type', 'start_node', 'end_node', 'capacity_limits', 'capital_costs', 'resistance', 'voltage', 'unit_size', 'reactance', 'financial_data',)

    def __init__(self, id: int, name: str, available: bool, power_systems_type: str, start_node: int, end_node: int, capacity_limits: SiennaMinMax, capital_costs: SiennaCapitalCost, resistance: float, voltage: float, unit_size: float, reactance: float, financial_data: SiennaTechnologyFinancialData) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.power_systems_type: str = power_systems_type
        self.start_node: int = start_node
        self.end_node: int = end_node
        self.capacity_limits: SiennaMinMax = capacity_limits
        self.capital_costs: SiennaCapitalCost = capital_costs
        self.resistance: float = resistance
        self.voltage: float = voltage
        self.unit_size: float = unit_size
        self.reactance: float = reactance
        self.financial_data: SiennaTechnologyFinancialData = financial_data


def parse_sienna_nodal_ac_transport_technology(data: dict[str, Any]) -> SiennaNodalACTransportTechnology:
    """Parse declared NodalACTransportTechnology properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed NodalACTransportTechnology object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import parse_sienna_capital_cost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import parse_sienna_technology_financial_data
    return SiennaNodalACTransportTechnology(id=get_required_value(data, 'id', 'NodalACTransportTechnology'), name=get_required_value(data, 'name', 'NodalACTransportTechnology'), available=get_required_value(data, 'available', 'NodalACTransportTechnology'), power_systems_type=get_required_value(data, 'power_systems_type', 'NodalACTransportTechnology'), start_node=get_required_value(data, 'start_node', 'NodalACTransportTechnology'), end_node=get_required_value(data, 'end_node', 'NodalACTransportTechnology'), capacity_limits=None if data.get('capacity_limits', None) is None else parse_sienna_min_max(data.get('capacity_limits', None)), capital_costs=None if data.get('capital_costs', None) is None else parse_sienna_capital_cost(data.get('capital_costs', None)), resistance=data.get('resistance', None), voltage=data.get('voltage', None), unit_size=data.get('unit_size', None), reactance=data.get('reactance', None), financial_data=parse_sienna_technology_financial_data(get_required_value(data, 'financial_data', 'NodalACTransportTechnology')))

def sienna_nodal_ac_transport_technology_to_json(value: SiennaNodalACTransportTechnology) -> dict[str, Any]:
    """Write every NodalACTransportTechnology slot to explicit schema property names.

    :param value: Typed NodalACTransportTechnology object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.capital_cost import sienna_capital_cost_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.investments.financials.technology_financial_data import sienna_technology_financial_data_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'power_systems_type': value.power_systems_type, 'start_node': value.start_node, 'end_node': value.end_node, 'capacity_limits': None if value.capacity_limits is None else sienna_min_max_to_json(value.capacity_limits), 'capital_costs': None if value.capital_costs is None else sienna_capital_cost_to_json(value.capital_costs), 'resistance': value.resistance, 'voltage': value.voltage, 'unit_size': value.unit_size, 'reactance': value.reactance, 'financial_data': sienna_technology_financial_data_to_json(value.financial_data)}
