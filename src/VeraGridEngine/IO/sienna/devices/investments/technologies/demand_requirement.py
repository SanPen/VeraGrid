# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna DemandRequirement schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import SiennaValueCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaDemandRequirement(SiennaSchemaModel):
    """Expose every declared DemandRequirement property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'power_systems_type', 'conformity', 'growth_rate', 'new_demand_mw', 'new_construction_year', 'region', 'value_of_lost_load', 'unserved_demand_curve',)

    def __init__(self, id: int, name: str, available: bool, power_systems_type: str, conformity: str, growth_rate: float, new_demand_mw: float, new_construction_year: int, region: list[int], value_of_lost_load: float, unserved_demand_curve: SiennaValueCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.power_systems_type: str = power_systems_type
        self.conformity: str = conformity
        self.growth_rate: float = growth_rate
        self.new_demand_mw: float = new_demand_mw
        self.new_construction_year: int = new_construction_year
        self.region: list[int] = region
        self.value_of_lost_load: float = value_of_lost_load
        self.unserved_demand_curve: SiennaValueCurve = unserved_demand_curve


def parse_sienna_demand_requirement(data: dict[str, Any]) -> SiennaDemandRequirement:
    """Parse declared DemandRequirement properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed DemandRequirement object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
    return SiennaDemandRequirement(id=get_required_value(data, 'id', 'DemandRequirement'), name=get_required_value(data, 'name', 'DemandRequirement'), available=data.get('available', None), power_systems_type=get_required_value(data, 'power_systems_type', 'DemandRequirement'), conformity=data.get('conformity', None), growth_rate=data.get('growth_rate', None), new_demand_mw=data.get('new_demand_mw', None), new_construction_year=data.get('new_construction_year', None), region=data.get('region', None), value_of_lost_load=data.get('value_of_lost_load', None), unserved_demand_curve=None if data.get('unserved_demand_curve', None) is None else parse_sienna_value_curve(data.get('unserved_demand_curve', None)))

def sienna_demand_requirement_to_json(value: SiennaDemandRequirement) -> dict[str, Any]:
    """Write every DemandRequirement slot to explicit schema property names.

    :param value: Typed DemandRequirement object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import sienna_value_curve_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'power_systems_type': value.power_systems_type, 'conformity': value.conformity, 'growth_rate': value.growth_rate, 'new_demand_mw': value.new_demand_mw, 'new_construction_year': value.new_construction_year, 'region': value.region, 'value_of_lost_load': value.value_of_lost_load, 'unserved_demand_curve': None if value.unserved_demand_curve is None else sienna_value_curve_to_json(value.unserved_demand_curve)}
