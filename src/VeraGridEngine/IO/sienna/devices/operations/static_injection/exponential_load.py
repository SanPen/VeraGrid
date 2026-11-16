# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ExponentialLoad schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import SiennaLoadConformity

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaExponentialLoad(SiennaSchemaModel):
    """Expose every declared ExponentialLoad property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'active_power', 'reactive_power', 'alpha', 'beta', 'base_power', 'power_units', 'max_active_power', 'max_reactive_power', 'conformity', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, active_power: float, reactive_power: float, alpha: float, beta: float, base_power: float, power_units: SiennaUnitSystem, max_active_power: float, max_reactive_power: float, conformity: SiennaLoadConformity, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.active_power: float = active_power
        self.reactive_power: float = reactive_power
        self.alpha: float = alpha
        self.beta: float = beta
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.max_active_power: float = max_active_power
        self.max_reactive_power: float = max_reactive_power
        self.conformity: SiennaLoadConformity = conformity
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_exponential_load(data: dict[str, Any]) -> SiennaExponentialLoad:
    """Parse declared ExponentialLoad properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ExponentialLoad object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import parse_sienna_load_conformity
    return SiennaExponentialLoad(id=get_required_value(data, 'id', 'ExponentialLoad'), name=get_required_value(data, 'name', 'ExponentialLoad'), available=get_required_value(data, 'available', 'ExponentialLoad'), bus=get_required_value(data, 'bus', 'ExponentialLoad'), active_power=get_required_value(data, 'active_power', 'ExponentialLoad'), reactive_power=get_required_value(data, 'reactive_power', 'ExponentialLoad'), alpha=get_required_value(data, 'alpha', 'ExponentialLoad'), beta=get_required_value(data, 'beta', 'ExponentialLoad'), base_power=get_required_value(data, 'base_power', 'ExponentialLoad'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'ExponentialLoad')), max_active_power=get_required_value(data, 'max_active_power', 'ExponentialLoad'), max_reactive_power=get_required_value(data, 'max_reactive_power', 'ExponentialLoad'), conformity=None if data.get('conformity', None) is None else parse_sienna_load_conformity(data.get('conformity', None)), dynamic_injector=data.get('dynamic_injector', None))

def sienna_exponential_load_to_json(value: SiennaExponentialLoad) -> dict[str, Any]:
    """Write every ExponentialLoad slot to explicit schema property names.

    :param value: Typed ExponentialLoad object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import sienna_load_conformity_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'active_power': value.active_power, 'reactive_power': value.reactive_power, 'alpha': value.alpha, 'beta': value.beta, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'max_active_power': value.max_active_power, 'max_reactive_power': value.max_reactive_power, 'conformity': None if value.conformity is None else sienna_load_conformity_to_json(value.conformity), 'dynamic_injector': value.dynamic_injector}
