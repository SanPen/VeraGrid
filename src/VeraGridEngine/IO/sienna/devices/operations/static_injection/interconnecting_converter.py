# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna InterconnectingConverter schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.current_loss_curve import SiennaCurrentLossCurve
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.operations.common.vscac_control_modes import SiennaVSCACControlModes
    from VeraGridEngine.IO.sienna.devices.operations.common.vscdc_control_modes import SiennaVSCDCControlModes

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaInterconnectingConverter(SiennaSchemaModel):
    """Expose every declared InterconnectingConverter property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'dc_bus', 'active_power', 'rating', 'active_power_limits', 'base_power', 'power_units', 'reactive_power_limits', 'dc_current', 'max_dc_current', 'loss_function', 'dc_control', 'ac_control', 'dc_power_setpoint', 'dc_voltage_setpoint', 'rated_dc_voltage', 'power_factor_setpoint', 'ac_voltage_setpoint', 'rated_ac_voltage', 'dc_voltage_droop', 'remote_bus_control', 'power_factor_weighting_fraction', 'voltage_limits', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, dc_bus: int, active_power: float, rating: float, active_power_limits: SiennaMinMax, base_power: float, power_units: SiennaUnitSystem, reactive_power_limits: SiennaMinMax, dc_current: float, max_dc_current: float, loss_function: SiennaCurrentLossCurve, dc_control: SiennaVSCDCControlModes, ac_control: SiennaVSCACControlModes, dc_power_setpoint: float | None, dc_voltage_setpoint: float | None, rated_dc_voltage: float, power_factor_setpoint: float | None, ac_voltage_setpoint: float | None, rated_ac_voltage: float, dc_voltage_droop: float, remote_bus_control: int | None, power_factor_weighting_fraction: float, voltage_limits: SiennaMinMax, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.dc_bus: int = dc_bus
        self.active_power: float = active_power
        self.rating: float = rating
        self.active_power_limits: SiennaMinMax = active_power_limits
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.dc_current: float = dc_current
        self.max_dc_current: float = max_dc_current
        self.loss_function: SiennaCurrentLossCurve = loss_function
        self.dc_control: SiennaVSCDCControlModes = dc_control
        self.ac_control: SiennaVSCACControlModes = ac_control
        self.dc_power_setpoint: float | None = dc_power_setpoint
        self.dc_voltage_setpoint: float | None = dc_voltage_setpoint
        self.rated_dc_voltage: float = rated_dc_voltage
        self.power_factor_setpoint: float | None = power_factor_setpoint
        self.ac_voltage_setpoint: float | None = ac_voltage_setpoint
        self.rated_ac_voltage: float = rated_ac_voltage
        self.dc_voltage_droop: float = dc_voltage_droop
        self.remote_bus_control: int | None = remote_bus_control
        self.power_factor_weighting_fraction: float = power_factor_weighting_fraction
        self.voltage_limits: SiennaMinMax = voltage_limits
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_interconnecting_converter(data: dict[str, Any]) -> SiennaInterconnectingConverter:
    """Parse declared InterconnectingConverter properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed InterconnectingConverter object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.current_loss_curve import parse_sienna_current_loss_curve
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.vscac_control_modes import parse_sienna_vscac_control_modes
    from VeraGridEngine.IO.sienna.devices.operations.common.vscdc_control_modes import parse_sienna_vscdc_control_modes
    return SiennaInterconnectingConverter(id=get_required_value(data, 'id', 'InterconnectingConverter'), name=get_required_value(data, 'name', 'InterconnectingConverter'), available=get_required_value(data, 'available', 'InterconnectingConverter'), bus=get_required_value(data, 'bus', 'InterconnectingConverter'), dc_bus=get_required_value(data, 'dc_bus', 'InterconnectingConverter'), active_power=get_required_value(data, 'active_power', 'InterconnectingConverter'), rating=get_required_value(data, 'rating', 'InterconnectingConverter'), active_power_limits=parse_sienna_min_max(get_required_value(data, 'active_power_limits', 'InterconnectingConverter')), base_power=get_required_value(data, 'base_power', 'InterconnectingConverter'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'InterconnectingConverter')), reactive_power_limits=None if data.get('reactive_power_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_limits', None)), dc_current=data.get('dc_current', None), max_dc_current=data.get('max_dc_current', None), loss_function=None if data.get('loss_function', None) is None else parse_sienna_current_loss_curve(data.get('loss_function', None)), dc_control=None if data.get('dc_control', None) is None else parse_sienna_vscdc_control_modes(data.get('dc_control', None)), ac_control=None if data.get('ac_control', None) is None else parse_sienna_vscac_control_modes(data.get('ac_control', None)), dc_power_setpoint=data.get('dc_power_setpoint', None), dc_voltage_setpoint=data.get('dc_voltage_setpoint', None), rated_dc_voltage=data.get('rated_dc_voltage', None), power_factor_setpoint=data.get('power_factor_setpoint', None), ac_voltage_setpoint=data.get('ac_voltage_setpoint', None), rated_ac_voltage=data.get('rated_ac_voltage', None), dc_voltage_droop=data.get('dc_voltage_droop', None), remote_bus_control=data.get('remote_bus_control', None), power_factor_weighting_fraction=data.get('power_factor_weighting_fraction', None), voltage_limits=None if data.get('voltage_limits', None) is None else parse_sienna_min_max(data.get('voltage_limits', None)), dynamic_injector=data.get('dynamic_injector', None))

def sienna_interconnecting_converter_to_json(value: SiennaInterconnectingConverter) -> dict[str, Any]:
    """Write every InterconnectingConverter slot to explicit schema property names.

    :param value: Typed InterconnectingConverter object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.current_loss_curve import sienna_current_loss_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.vscac_control_modes import sienna_vscac_control_modes_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.vscdc_control_modes import sienna_vscdc_control_modes_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'dc_bus': value.dc_bus, 'active_power': value.active_power, 'rating': value.rating, 'active_power_limits': sienna_min_max_to_json(value.active_power_limits), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'reactive_power_limits': None if value.reactive_power_limits is None else sienna_min_max_to_json(value.reactive_power_limits), 'dc_current': value.dc_current, 'max_dc_current': value.max_dc_current, 'loss_function': None if value.loss_function is None else sienna_current_loss_curve_to_json(value.loss_function), 'dc_control': None if value.dc_control is None else sienna_vscdc_control_modes_to_json(value.dc_control), 'ac_control': None if value.ac_control is None else sienna_vscac_control_modes_to_json(value.ac_control), 'dc_power_setpoint': value.dc_power_setpoint, 'dc_voltage_setpoint': value.dc_voltage_setpoint, 'rated_dc_voltage': value.rated_dc_voltage, 'power_factor_setpoint': value.power_factor_setpoint, 'ac_voltage_setpoint': value.ac_voltage_setpoint, 'rated_ac_voltage': value.rated_ac_voltage, 'dc_voltage_droop': value.dc_voltage_droop, 'remote_bus_control': value.remote_bus_control, 'power_factor_weighting_fraction': value.power_factor_weighting_fraction, 'voltage_limits': None if value.voltage_limits is None else sienna_min_max_to_json(value.voltage_limits), 'dynamic_injector': value.dynamic_injector}
