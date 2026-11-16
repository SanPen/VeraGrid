# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna AreaInterchange schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.from_to_to_from import SiennaFromTo_ToFrom
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaAreaInterchange(SiennaSchemaModel):
    """Expose every declared AreaInterchange property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'active_power_flow', 'from_area', 'to_area', 'flow_limits', 'base_power', 'power_units',)

    def __init__(self, id: int, name: str, available: bool, active_power_flow: float, from_area: int, to_area: int, flow_limits: SiennaFromTo_ToFrom, base_power: float, power_units: SiennaUnitSystem) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.active_power_flow: float = active_power_flow
        self.from_area: int = from_area
        self.to_area: int = to_area
        self.flow_limits: SiennaFromTo_ToFrom = flow_limits
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units


def parse_sienna_area_interchange(data: dict[str, Any]) -> SiennaAreaInterchange:
    """Parse declared AreaInterchange properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed AreaInterchange object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.from_to_to_from import parse_sienna_from_to_to_from
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaAreaInterchange(id=get_required_value(data, 'id', 'AreaInterchange'), name=get_required_value(data, 'name', 'AreaInterchange'), available=get_required_value(data, 'available', 'AreaInterchange'), active_power_flow=get_required_value(data, 'active_power_flow', 'AreaInterchange'), from_area=get_required_value(data, 'from_area', 'AreaInterchange'), to_area=get_required_value(data, 'to_area', 'AreaInterchange'), flow_limits=parse_sienna_from_to_to_from(get_required_value(data, 'flow_limits', 'AreaInterchange')), base_power=get_required_value(data, 'base_power', 'AreaInterchange'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'AreaInterchange')))

def sienna_area_interchange_to_json(value: SiennaAreaInterchange) -> dict[str, Any]:
    """Write every AreaInterchange slot to explicit schema property names.

    :param value: Typed AreaInterchange object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.from_to_to_from import sienna_from_to_to_from_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'active_power_flow': value.active_power_flow, 'from_area': value.from_area, 'to_area': value.to_area, 'flow_limits': sienna_from_to_to_from_to_json(value.flow_limits), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units)}
