# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FACTSControlDevice schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.operations.common.facts_control_device_control_mode import SiennaFACTSControlDeviceControlMode
    from VeraGridEngine.IO.sienna.devices.operations.common.voltage_unit_basis import SiennaVoltageUnitBasis

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFACTSControlDevice(SiennaSchemaModel):
    """Expose every declared FACTSControlDevice property through fixed slots."""

    __slots__ = ('name', 'id', 'available', 'bus', 'control_mode', 'voltage_setpoint_units', 'voltage_setpoint', 'max_shunt_current', 'reactive_power_required', 'max_reactive_power', 'shunt_control_type', 'regulated_bus_number', 'base_power', 'power_units', 'dynamic_injector',)

    def __init__(self, name: str, id: int, available: bool, bus: int, control_mode: SiennaFACTSControlDeviceControlMode, voltage_setpoint_units: SiennaVoltageUnitBasis, voltage_setpoint: float, max_shunt_current: float, reactive_power_required: float, max_reactive_power: float, shunt_control_type: str, regulated_bus_number: int, base_power: float, power_units: SiennaUnitSystem, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.name: str = name
        self.id: int = id
        self.available: bool = available
        self.bus: int = bus
        self.control_mode: SiennaFACTSControlDeviceControlMode = control_mode
        self.voltage_setpoint_units: SiennaVoltageUnitBasis = voltage_setpoint_units
        self.voltage_setpoint: float = voltage_setpoint
        self.max_shunt_current: float = max_shunt_current
        self.reactive_power_required: float = reactive_power_required
        self.max_reactive_power: float = max_reactive_power
        self.shunt_control_type: str = shunt_control_type
        self.regulated_bus_number: int = regulated_bus_number
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_facts_control_device(data: dict[str, Any]) -> SiennaFACTSControlDevice:
    """Parse declared FACTSControlDevice properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FACTSControlDevice object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.facts_control_device_control_mode import parse_sienna_facts_control_device_control_mode
    from VeraGridEngine.IO.sienna.devices.operations.common.voltage_unit_basis import parse_sienna_voltage_unit_basis
    return SiennaFACTSControlDevice(name=get_required_value(data, 'name', 'FACTSControlDevice'), id=get_required_value(data, 'id', 'FACTSControlDevice'), available=get_required_value(data, 'available', 'FACTSControlDevice'), bus=get_required_value(data, 'bus', 'FACTSControlDevice'), control_mode=None if data.get('control_mode', None) is None else parse_sienna_facts_control_device_control_mode(data.get('control_mode', None)), voltage_setpoint_units=None if data.get('voltage_setpoint_units', None) is None else parse_sienna_voltage_unit_basis(data.get('voltage_setpoint_units', None)), voltage_setpoint=get_required_value(data, 'voltage_setpoint', 'FACTSControlDevice'), max_shunt_current=get_required_value(data, 'max_shunt_current', 'FACTSControlDevice'), reactive_power_required=get_required_value(data, 'reactive_power_required', 'FACTSControlDevice'), max_reactive_power=data.get('max_reactive_power', None), shunt_control_type=data.get('shunt_control_type', None), regulated_bus_number=data.get('regulated_bus_number', None), base_power=get_required_value(data, 'base_power', 'FACTSControlDevice'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'FACTSControlDevice')), dynamic_injector=data.get('dynamic_injector', None))

def sienna_facts_control_device_to_json(value: SiennaFACTSControlDevice) -> dict[str, Any]:
    """Write every FACTSControlDevice slot to explicit schema property names.

    :param value: Typed FACTSControlDevice object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.facts_control_device_control_mode import sienna_facts_control_device_control_mode_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.voltage_unit_basis import sienna_voltage_unit_basis_to_json
    return {'name': value.name, 'id': value.id, 'available': value.available, 'bus': value.bus, 'control_mode': None if value.control_mode is None else sienna_facts_control_device_control_mode_to_json(value.control_mode), 'voltage_setpoint_units': None if value.voltage_setpoint_units is None else sienna_voltage_unit_basis_to_json(value.voltage_setpoint_units), 'voltage_setpoint': value.voltage_setpoint, 'max_shunt_current': value.max_shunt_current, 'reactive_power_required': value.reactive_power_required, 'max_reactive_power': value.max_reactive_power, 'shunt_control_type': value.shunt_control_type, 'regulated_bus_number': value.regulated_bus_number, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'dynamic_injector': value.dynamic_injector}
