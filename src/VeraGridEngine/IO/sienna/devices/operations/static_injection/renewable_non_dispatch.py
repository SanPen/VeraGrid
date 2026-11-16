# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RenewableNonDispatch schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import SiennaPrimeMovers
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRenewableNonDispatch(SiennaSchemaModel):
    """Expose every declared RenewableNonDispatch property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'active_power', 'reactive_power', 'rating', 'prime_mover_type', 'power_factor', 'base_power', 'power_units', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, active_power: float, reactive_power: float, rating: float, prime_mover_type: SiennaPrimeMovers, power_factor: float, base_power: float, power_units: SiennaUnitSystem, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.active_power: float = active_power
        self.reactive_power: float = reactive_power
        self.rating: float = rating
        self.prime_mover_type: SiennaPrimeMovers = prime_mover_type
        self.power_factor: float = power_factor
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_renewable_non_dispatch(data: dict[str, Any]) -> SiennaRenewableNonDispatch:
    """Parse declared RenewableNonDispatch properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RenewableNonDispatch object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import parse_sienna_prime_movers
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaRenewableNonDispatch(id=get_required_value(data, 'id', 'RenewableNonDispatch'), name=get_required_value(data, 'name', 'RenewableNonDispatch'), available=get_required_value(data, 'available', 'RenewableNonDispatch'), bus=get_required_value(data, 'bus', 'RenewableNonDispatch'), active_power=get_required_value(data, 'active_power', 'RenewableNonDispatch'), reactive_power=get_required_value(data, 'reactive_power', 'RenewableNonDispatch'), rating=get_required_value(data, 'rating', 'RenewableNonDispatch'), prime_mover_type=parse_sienna_prime_movers(get_required_value(data, 'prime_mover_type', 'RenewableNonDispatch')), power_factor=get_required_value(data, 'power_factor', 'RenewableNonDispatch'), base_power=get_required_value(data, 'base_power', 'RenewableNonDispatch'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'RenewableNonDispatch')), dynamic_injector=data.get('dynamic_injector', None))

def sienna_renewable_non_dispatch_to_json(value: SiennaRenewableNonDispatch) -> dict[str, Any]:
    """Write every RenewableNonDispatch slot to explicit schema property names.

    :param value: Typed RenewableNonDispatch object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import sienna_prime_movers_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'active_power': value.active_power, 'reactive_power': value.reactive_power, 'rating': value.rating, 'prime_mover_type': sienna_prime_movers_to_json(value.prime_mover_type), 'power_factor': value.power_factor, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'dynamic_injector': value.dynamic_injector}
