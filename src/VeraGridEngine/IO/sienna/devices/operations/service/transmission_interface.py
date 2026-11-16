# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TransmissionInterface schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTransmissionInterface(SiennaSchemaModel):
    """Expose every declared TransmissionInterface property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'active_power_flow_limits', 'violation_penalty', 'direction_mapping', 'base_power', 'power_units',)

    def __init__(self, id: int, name: str, available: bool, active_power_flow_limits: SiennaMinMax, violation_penalty: float, direction_mapping: dict[str, object], base_power: float, power_units: SiennaUnitSystem) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.active_power_flow_limits: SiennaMinMax = active_power_flow_limits
        self.violation_penalty: float = violation_penalty
        self.direction_mapping: dict[str, object] = direction_mapping
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units


def parse_sienna_transmission_interface(data: dict[str, Any]) -> SiennaTransmissionInterface:
    """Parse declared TransmissionInterface properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TransmissionInterface object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaTransmissionInterface(id=get_required_value(data, 'id', 'TransmissionInterface'), name=get_required_value(data, 'name', 'TransmissionInterface'), available=get_required_value(data, 'available', 'TransmissionInterface'), active_power_flow_limits=parse_sienna_min_max(get_required_value(data, 'active_power_flow_limits', 'TransmissionInterface')), violation_penalty=data.get('violation_penalty', None), direction_mapping=data.get('direction_mapping', None), base_power=get_required_value(data, 'base_power', 'TransmissionInterface'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'TransmissionInterface')))

def sienna_transmission_interface_to_json(value: SiennaTransmissionInterface) -> dict[str, Any]:
    """Write every TransmissionInterface slot to explicit schema property names.

    :param value: Typed TransmissionInterface object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'active_power_flow_limits': sienna_min_max_to_json(value.active_power_flow_limits), 'violation_penalty': value.violation_penalty, 'direction_mapping': value.direction_mapping, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units)}
