# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel
"""Sienna ``PowerLoad`` device object."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value
from VeraGridEngine.IO.sienna.devices.enums import SiennaUnitSystem


class SiennaPowerLoad(SiennaSchemaModel):
    """Represent one Sienna ``PowerLoad`` component in natural power units."""

    __slots__ = ("identifier", "name", "available", "bus", "active_power", "reactive_power", "base_power",
                 "max_active_power", "max_reactive_power", "power_units", "conformity", "dynamic_injector")

    def __init__(self, identifier: int, name: str, available: bool, bus: int, active_power: float,
                 reactive_power: float, base_power: float, max_active_power: float,
                 max_reactive_power: float, power_units: SiennaUnitSystem, conformity: str,
                 dynamic_injector: int | None) -> None:
        """Store one static demand record.

        :param identifier: Sienna component identifier.
        :param name: Load name.
        :param available: Network availability flag.
        :param bus: Referenced Sienna bus identifier.
        :param active_power: Active demand in MW.
        :param reactive_power: Reactive demand in MVAr.
        :param base_power: Component base power in MVA.
        :param max_active_power: Maximum active demand in MW.
        :param max_reactive_power: Maximum reactive demand in MVAr.
        :param power_units: Sienna power-family unit basis.
        :param conformity: Declared load conformity.
        :param dynamic_injector: Optional linked dynamic injector identifier.
        :return: None.
        """
        self.identifier: int = identifier
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.active_power: float = active_power
        self.reactive_power: float = reactive_power
        self.base_power: float = base_power
        self.max_active_power: float = max_active_power
        self.max_reactive_power: float = max_reactive_power
        self.power_units: SiennaUnitSystem = power_units
        self.conformity: str = conformity
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_power_load(data: dict[str, Any]) -> SiennaPowerLoad:
    """Parse declared PowerLoad properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PowerLoad object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import parse_sienna_load_conformity
    return SiennaPowerLoad(identifier=get_required_value(data, 'id', 'PowerLoad'), name=get_required_value(data, 'name', 'PowerLoad'), available=get_required_value(data, 'available', 'PowerLoad'), bus=get_required_value(data, 'bus', 'PowerLoad'), active_power=get_required_value(data, 'active_power', 'PowerLoad'), reactive_power=get_required_value(data, 'reactive_power', 'PowerLoad'), base_power=get_required_value(data, 'base_power', 'PowerLoad'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'PowerLoad')), max_active_power=get_required_value(data, 'max_active_power', 'PowerLoad'), max_reactive_power=get_required_value(data, 'max_reactive_power', 'PowerLoad'), conformity=None if data.get('conformity', None) is None else parse_sienna_load_conformity(data.get('conformity', None)), dynamic_injector=data.get('dynamic_injector', None))

def sienna_power_load_to_json(value: SiennaPowerLoad) -> dict[str, Any]:
    """Write every PowerLoad slot to explicit schema property names.

    :param value: Typed PowerLoad object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import sienna_load_conformity_to_json
    return {'id': value.identifier, 'name': value.name, 'available': value.available, 'bus': value.bus, 'active_power': value.active_power, 'reactive_power': value.reactive_power, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'max_active_power': value.max_active_power, 'max_reactive_power': value.max_reactive_power, 'conformity': None if value.conformity is None else sienna_load_conformity_to_json(value.conformity), 'dynamic_injector': value.dynamic_injector}
