# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna DemandSideTechnology schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import SiennaValueCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaDemandSideTechnology(SiennaSchemaModel):
    """Expose every declared DemandSideTechnology property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'region', 'power_systems_type', 'technology_efficiency', 'price_per_unit', 'min_power', 'peak_demand_mw', 'max_demand_delay', 'max_demand_advance', 'demand_energy_efficiency', 'shift_variable_cost', 'curtailment_cost', 'max_demand_curtailment',)

    def __init__(self, id: int, name: str, available: bool, region: list[int], power_systems_type: str, technology_efficiency: float, price_per_unit: SiennaValueCurve, min_power: float, peak_demand_mw: float, max_demand_delay: float, max_demand_advance: float, demand_energy_efficiency: float, shift_variable_cost: SiennaValueCurve, curtailment_cost: SiennaValueCurve, max_demand_curtailment: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.region: list[int] = region
        self.power_systems_type: str = power_systems_type
        self.technology_efficiency: float = technology_efficiency
        self.price_per_unit: SiennaValueCurve = price_per_unit
        self.min_power: float = min_power
        self.peak_demand_mw: float = peak_demand_mw
        self.max_demand_delay: float = max_demand_delay
        self.max_demand_advance: float = max_demand_advance
        self.demand_energy_efficiency: float = demand_energy_efficiency
        self.shift_variable_cost: SiennaValueCurve = shift_variable_cost
        self.curtailment_cost: SiennaValueCurve = curtailment_cost
        self.max_demand_curtailment: float = max_demand_curtailment


def parse_sienna_demand_side_technology(data: dict[str, Any]) -> SiennaDemandSideTechnology:
    """Parse declared DemandSideTechnology properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed DemandSideTechnology object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
    return SiennaDemandSideTechnology(id=get_required_value(data, 'id', 'DemandSideTechnology'), name=get_required_value(data, 'name', 'DemandSideTechnology'), available=get_required_value(data, 'available', 'DemandSideTechnology'), region=data.get('region', None), power_systems_type=get_required_value(data, 'power_systems_type', 'DemandSideTechnology'), technology_efficiency=data.get('technology_efficiency', None), price_per_unit=None if data.get('price_per_unit', None) is None else parse_sienna_value_curve(data.get('price_per_unit', None)), min_power=data.get('min_power', None), peak_demand_mw=data.get('peak_demand_mw', None), max_demand_delay=data.get('max_demand_delay', None), max_demand_advance=data.get('max_demand_advance', None), demand_energy_efficiency=data.get('demand_energy_efficiency', None), shift_variable_cost=None if data.get('shift_variable_cost', None) is None else parse_sienna_value_curve(data.get('shift_variable_cost', None)), curtailment_cost=None if data.get('curtailment_cost', None) is None else parse_sienna_value_curve(data.get('curtailment_cost', None)), max_demand_curtailment=data.get('max_demand_curtailment', None))

def sienna_demand_side_technology_to_json(value: SiennaDemandSideTechnology) -> dict[str, Any]:
    """Write every DemandSideTechnology slot to explicit schema property names.

    :param value: Typed DemandSideTechnology object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import sienna_value_curve_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'region': value.region, 'power_systems_type': value.power_systems_type, 'technology_efficiency': value.technology_efficiency, 'price_per_unit': None if value.price_per_unit is None else sienna_value_curve_to_json(value.price_per_unit), 'min_power': value.min_power, 'peak_demand_mw': value.peak_demand_mw, 'max_demand_delay': value.max_demand_delay, 'max_demand_advance': value.max_demand_advance, 'demand_energy_efficiency': value.demand_energy_efficiency, 'shift_variable_cost': None if value.shift_variable_cost is None else sienna_value_curve_to_json(value.shift_variable_cost), 'curtailment_cost': None if value.curtailment_cost is None else sienna_value_curve_to_json(value.curtailment_cost), 'max_demand_curtailment': value.max_demand_curtailment}
