# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SynchronousCondenser schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSynchronousCondenser(SiennaSchemaModel):
    """Expose every declared SynchronousCondenser property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'reactive_power', 'rating', 'reactive_power_limits', 'base_power', 'power_units', 'active_power_losses', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, reactive_power: float, rating: float, reactive_power_limits: SiennaMinMax, base_power: float, power_units: SiennaUnitSystem, active_power_losses: float, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.reactive_power: float = reactive_power
        self.rating: float = rating
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.active_power_losses: float = active_power_losses
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_synchronous_condenser(data: dict[str, Any]) -> SiennaSynchronousCondenser:
    """Parse declared SynchronousCondenser properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SynchronousCondenser object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaSynchronousCondenser(id=get_required_value(data, 'id', 'SynchronousCondenser'), name=get_required_value(data, 'name', 'SynchronousCondenser'), available=get_required_value(data, 'available', 'SynchronousCondenser'), bus=get_required_value(data, 'bus', 'SynchronousCondenser'), reactive_power=get_required_value(data, 'reactive_power', 'SynchronousCondenser'), rating=get_required_value(data, 'rating', 'SynchronousCondenser'), reactive_power_limits=None if data.get('reactive_power_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_limits', None)), base_power=get_required_value(data, 'base_power', 'SynchronousCondenser'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'SynchronousCondenser')), active_power_losses=data.get('active_power_losses', None), dynamic_injector=data.get('dynamic_injector', None))

def sienna_synchronous_condenser_to_json(value: SiennaSynchronousCondenser) -> dict[str, Any]:
    """Write every SynchronousCondenser slot to explicit schema property names.

    :param value: Typed SynchronousCondenser object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'reactive_power': value.reactive_power, 'rating': value.rating, 'reactive_power_limits': None if value.reactive_power_limits is None else sienna_min_max_to_json(value.reactive_power_limits), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'active_power_losses': value.active_power_losses, 'dynamic_injector': value.dynamic_injector}
