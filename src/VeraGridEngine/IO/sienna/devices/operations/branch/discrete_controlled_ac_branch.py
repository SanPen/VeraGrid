# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna DiscreteControlledACBranch schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import SiennaOperationalFlowLimit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaDiscreteControlledACBranch(SiennaSchemaModel):
    """Expose every declared DiscreteControlledACBranch property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'active_power_flow', 'reactive_power_flow', 'arc', 'base_power', 'power_units', 'r', 'x', 'rating', 'rating_b', 'rating_c', 'operational_flow_limit', 'discrete_branch_type', 'branch_status', 'normal_branch_status',)

    def __init__(self, id: int, name: str, available: bool, active_power_flow: float, reactive_power_flow: float, arc: int, base_power: float, power_units: SiennaUnitSystem, r: float, x: float, rating: float, rating_b: float, rating_c: float, operational_flow_limit: SiennaOperationalFlowLimit, discrete_branch_type: str, branch_status: str, normal_branch_status: str) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.active_power_flow: float = active_power_flow
        self.reactive_power_flow: float = reactive_power_flow
        self.arc: int = arc
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.r: float = r
        self.x: float = x
        self.rating: float = rating
        self.rating_b: float = rating_b
        self.rating_c: float = rating_c
        self.operational_flow_limit: SiennaOperationalFlowLimit = operational_flow_limit
        self.discrete_branch_type: str = discrete_branch_type
        self.branch_status: str = branch_status
        self.normal_branch_status: str = normal_branch_status


def parse_sienna_discrete_controlled_ac_branch(data: dict[str, Any]) -> SiennaDiscreteControlledACBranch:
    """Parse declared DiscreteControlledACBranch properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed DiscreteControlledACBranch object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaDiscreteControlledACBranch(id=get_required_value(data, 'id', 'DiscreteControlledACBranch'), name=get_required_value(data, 'name', 'DiscreteControlledACBranch'), available=get_required_value(data, 'available', 'DiscreteControlledACBranch'), active_power_flow=get_required_value(data, 'active_power_flow', 'DiscreteControlledACBranch'), reactive_power_flow=get_required_value(data, 'reactive_power_flow', 'DiscreteControlledACBranch'), arc=get_required_value(data, 'arc', 'DiscreteControlledACBranch'), base_power=get_required_value(data, 'base_power', 'DiscreteControlledACBranch'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'DiscreteControlledACBranch')), r=get_required_value(data, 'r', 'DiscreteControlledACBranch'), x=get_required_value(data, 'x', 'DiscreteControlledACBranch'), rating=get_required_value(data, 'rating', 'DiscreteControlledACBranch'), rating_b=data.get('rating_b', None), rating_c=data.get('rating_c', None), operational_flow_limit=None if data.get('operational_flow_limit', None) is None else parse_sienna_operational_flow_limit(data.get('operational_flow_limit', None)), discrete_branch_type=data.get('discrete_branch_type', None), branch_status=data.get('branch_status', None), normal_branch_status=data.get('normal_branch_status', None))

def sienna_discrete_controlled_ac_branch_to_json(value: SiennaDiscreteControlledACBranch) -> dict[str, Any]:
    """Write every DiscreteControlledACBranch slot to explicit schema property names.

    :param value: Typed DiscreteControlledACBranch object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import sienna_operational_flow_limit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'active_power_flow': value.active_power_flow, 'reactive_power_flow': value.reactive_power_flow, 'arc': value.arc, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'r': value.r, 'x': value.x, 'rating': value.rating, 'rating_b': value.rating_b, 'rating_c': value.rating_c, 'operational_flow_limit': None if value.operational_flow_limit is None else sienna_operational_flow_limit_to_json(value.operational_flow_limit), 'discrete_branch_type': value.discrete_branch_type, 'branch_status': value.branch_status, 'normal_branch_status': value.normal_branch_status}
