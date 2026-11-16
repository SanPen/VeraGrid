# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel
"""Statically typed Sienna StandardLoad schema object."""

from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value


class SiennaStandardLoad(SiennaSchemaModel):
    """Represent declared ZIP-load fields without a dynamic property bag."""

    __slots__ = ("identifier", "name", "available", "bus", "base_power", "power_units",
                 "constant_active_power", "constant_reactive_power", "impedance_active_power",
                 "impedance_reactive_power", "current_active_power", "current_reactive_power",
                 "max_constant_active_power", "max_constant_reactive_power", "max_impedance_active_power",
                 "max_impedance_reactive_power", "max_current_active_power", "max_current_reactive_power",
                 "conformity", "dynamic_injector")

    def __init__(self, identifier: int, name: str, available: bool, bus: int, base_power: float,
                 power_units: str, constant_active_power: float, constant_reactive_power: float,
                 impedance_active_power: float, impedance_reactive_power: float, current_active_power: float,
                 current_reactive_power: float, max_constant_active_power: float,
                 max_constant_reactive_power: float, max_impedance_active_power: float,
                 max_impedance_reactive_power: float, max_current_active_power: float,
                 max_current_reactive_power: float, conformity: str, dynamic_injector: int | None) -> None:
        """Store every StandardLoad schema property in a fixed slot.

        :param identifier: Sienna component identifier.
        :param name: Component name.
        :param available: Network availability flag.
        :param bus: Connected bus identifier.
        :param base_power: Component base power in MVA.
        :param power_units: Declared power-unit basis.
        :param constant_active_power: Constant-P active demand.
        :param constant_reactive_power: Constant-P reactive demand.
        :param impedance_active_power: Constant-Z active demand.
        :param impedance_reactive_power: Constant-Z reactive demand.
        :param current_active_power: Constant-I active demand.
        :param current_reactive_power: Constant-I reactive demand.
        :param max_constant_active_power: Maximum constant-P active demand.
        :param max_constant_reactive_power: Maximum constant-P reactive demand.
        :param max_impedance_active_power: Maximum constant-Z active demand.
        :param max_impedance_reactive_power: Maximum constant-Z reactive demand.
        :param max_current_active_power: Maximum constant-I active demand.
        :param max_current_reactive_power: Maximum constant-I reactive demand.
        :param conformity: Declared load conformity.
        :param dynamic_injector: Optional linked dynamic injector identifier.
        :return: None.
        """
        self.identifier: int = identifier
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.base_power: float = base_power
        self.power_units: str = power_units
        self.constant_active_power: float = constant_active_power
        self.constant_reactive_power: float = constant_reactive_power
        self.impedance_active_power: float = impedance_active_power
        self.impedance_reactive_power: float = impedance_reactive_power
        self.current_active_power: float = current_active_power
        self.current_reactive_power: float = current_reactive_power
        self.max_constant_active_power: float = max_constant_active_power
        self.max_constant_reactive_power: float = max_constant_reactive_power
        self.max_impedance_active_power: float = max_impedance_active_power
        self.max_impedance_reactive_power: float = max_impedance_reactive_power
        self.max_current_active_power: float = max_current_active_power
        self.max_current_reactive_power: float = max_current_reactive_power
        self.conformity: str = conformity
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_standard_load(data: dict[str, Any]) -> SiennaStandardLoad:
    """Parse declared StandardLoad properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed StandardLoad object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import parse_sienna_load_conformity
    return SiennaStandardLoad(identifier=get_required_value(data, 'id', 'StandardLoad'), name=get_required_value(data, 'name', 'StandardLoad'), available=get_required_value(data, 'available', 'StandardLoad'), bus=get_required_value(data, 'bus', 'StandardLoad'), base_power=get_required_value(data, 'base_power', 'StandardLoad'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'StandardLoad')), constant_active_power=data.get('constant_active_power', 0.0), constant_reactive_power=data.get('constant_reactive_power', 0.0), impedance_active_power=data.get('impedance_active_power', 0.0), impedance_reactive_power=data.get('impedance_reactive_power', 0.0), current_active_power=data.get('current_active_power', 0.0), current_reactive_power=data.get('current_reactive_power', 0.0), max_constant_active_power=data.get('max_constant_active_power', 0.0), max_constant_reactive_power=data.get('max_constant_reactive_power', 0.0), max_impedance_active_power=data.get('max_impedance_active_power', 0.0), max_impedance_reactive_power=data.get('max_impedance_reactive_power', 0.0), max_current_active_power=data.get('max_current_active_power', 0.0), max_current_reactive_power=data.get('max_current_reactive_power', 0.0), conformity=None if data.get('conformity', None) is None else parse_sienna_load_conformity(data.get('conformity', None)), dynamic_injector=data.get('dynamic_injector', None))

def sienna_standard_load_to_json(value: SiennaStandardLoad) -> dict[str, Any]:
    """Write every StandardLoad slot to explicit schema property names.

    :param value: Typed StandardLoad object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.load_conformity import sienna_load_conformity_to_json
    return {'id': value.identifier, 'name': value.name, 'available': value.available, 'bus': value.bus, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'constant_active_power': value.constant_active_power, 'constant_reactive_power': value.constant_reactive_power, 'impedance_active_power': value.impedance_active_power, 'impedance_reactive_power': value.impedance_reactive_power, 'current_active_power': value.current_active_power, 'current_reactive_power': value.current_reactive_power, 'max_constant_active_power': value.max_constant_active_power, 'max_constant_reactive_power': value.max_constant_reactive_power, 'max_impedance_active_power': value.max_impedance_active_power, 'max_impedance_reactive_power': value.max_impedance_reactive_power, 'max_current_active_power': value.max_current_active_power, 'max_current_reactive_power': value.max_current_reactive_power, 'conformity': None if value.conformity is None else sienna_load_conformity_to_json(value.conformity), 'dynamic_injector': value.dynamic_injector}
