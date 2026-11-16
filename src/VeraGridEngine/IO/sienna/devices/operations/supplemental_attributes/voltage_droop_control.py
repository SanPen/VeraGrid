# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna VoltageDroopControl schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.operations.common.voltage_unit_basis import SiennaVoltageUnitBasis

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaVoltageDroopControl(SiennaSchemaModel):
    """Expose every declared VoltageDroopControl property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'regulated_bus_id', 'reactive_power_limits', 'deadband_reactive_power', 'voltage_units', 'deadband_voltage_limits', 'voltage_limits',)

    def __init__(self, id: int, name: str, available: bool, regulated_bus_id: int, reactive_power_limits: SiennaMinMax, deadband_reactive_power: float, voltage_units: SiennaVoltageUnitBasis, deadband_voltage_limits: SiennaMinMax, voltage_limits: SiennaMinMax) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.regulated_bus_id: int = regulated_bus_id
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.deadband_reactive_power: float = deadband_reactive_power
        self.voltage_units: SiennaVoltageUnitBasis = voltage_units
        self.deadband_voltage_limits: SiennaMinMax = deadband_voltage_limits
        self.voltage_limits: SiennaMinMax = voltage_limits


def parse_sienna_voltage_droop_control(data: dict[str, Any]) -> SiennaVoltageDroopControl:
    """Parse declared VoltageDroopControl properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed VoltageDroopControl object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.operations.common.voltage_unit_basis import parse_sienna_voltage_unit_basis
    return SiennaVoltageDroopControl(id=get_required_value(data, 'id', 'VoltageDroopControl'), name=get_required_value(data, 'name', 'VoltageDroopControl'), available=data.get('available', None), regulated_bus_id=get_required_value(data, 'regulated_bus_id', 'VoltageDroopControl'), reactive_power_limits=parse_sienna_min_max(get_required_value(data, 'reactive_power_limits', 'VoltageDroopControl')), deadband_reactive_power=get_required_value(data, 'deadband_reactive_power', 'VoltageDroopControl'), voltage_units=None if data.get('voltage_units', None) is None else parse_sienna_voltage_unit_basis(data.get('voltage_units', None)), deadband_voltage_limits=parse_sienna_min_max(get_required_value(data, 'deadband_voltage_limits', 'VoltageDroopControl')), voltage_limits=parse_sienna_min_max(get_required_value(data, 'voltage_limits', 'VoltageDroopControl')))

def sienna_voltage_droop_control_to_json(value: SiennaVoltageDroopControl) -> dict[str, Any]:
    """Write every VoltageDroopControl slot to explicit schema property names.

    :param value: Typed VoltageDroopControl object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.voltage_unit_basis import sienna_voltage_unit_basis_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'regulated_bus_id': value.regulated_bus_id, 'reactive_power_limits': sienna_min_max_to_json(value.reactive_power_limits), 'deadband_reactive_power': value.deadband_reactive_power, 'voltage_units': None if value.voltage_units is None else sienna_voltage_unit_basis_to_json(value.voltage_units), 'deadband_voltage_limits': sienna_min_max_to_json(value.deadband_voltage_limits), 'voltage_limits': sienna_min_max_to_json(value.voltage_limits)}
