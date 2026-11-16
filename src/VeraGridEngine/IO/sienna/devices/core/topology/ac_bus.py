# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Sienna ``ACBus`` device object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value


class SiennaACBus(SiennaSchemaModel):
    """Represent one Sienna ``ACBus`` component."""

    __slots__ = ("identifier", "name", "available", "number", "base_voltage", "magnitude", "angle",
                 "voltage_limits", "bus_type", "area", "load_zone")

    def __init__(self, identifier: int, name: str, available: bool, number: int,
                 base_voltage: float | None, magnitude: float | None, angle: float | None,
                 voltage_limits: dict[str, float] | None, bus_type: str | None, area: int | None,
                 load_zone: int | None) -> None:
        """Store the wire-level bus values without changing their declared units.

        :param identifier: Sienna component identifier.
        :param name: Bus name.
        :param available: Network availability flag.
        :param number: User-visible bus number.
        :param base_voltage: Nominal voltage in kV when declared.
        :param magnitude: Initial voltage magnitude in pu when declared.
        :param angle: Initial voltage angle in radians when declared.
        :param voltage_limits: Voltage lower and upper bounds when declared.
        :param bus_type: Sienna AC bus classification when declared.
        :param area: Area identifier when declared.
        :param load_zone: Load-zone identifier when declared.
        :return: None.
        """
        self.identifier: int = identifier
        self.name: str = name
        self.available: bool = available
        self.number: int = number
        self.base_voltage: float | None = base_voltage
        self.magnitude: float | None = magnitude
        self.angle: float | None = angle
        self.voltage_limits: dict[str, float] | None = voltage_limits
        self.bus_type: str | None = bus_type
        self.area: int | None = area
        self.load_zone: int | None = load_zone


def parse_sienna_ac_bus(data: dict[str, Any]) -> SiennaACBus:
    """Parse declared ACBus properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ACBus object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.ac_bus_type import parse_sienna_ac_bus_type
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaACBus(identifier=get_required_value(data, 'id', 'ACBus'), number=get_required_value(data, 'number', 'ACBus'), name=get_required_value(data, 'name', 'ACBus'), available=get_required_value(data, 'available', 'ACBus'), bus_type=None if data.get('bustype', None) is None else parse_sienna_ac_bus_type(data.get('bustype', None)), angle=data.get('angle', 0.0), magnitude=data.get('magnitude', 1.0), voltage_limits=None if data.get('voltage_limits', None) is None else parse_sienna_min_max(data.get('voltage_limits', None)), base_voltage=data.get('base_voltage', 0.0), area=data.get('area', None), load_zone=data.get('load_zone', None))

def sienna_ac_bus_to_json(value: SiennaACBus) -> dict[str, Any]:
    """Write every ACBus slot to explicit schema property names.

    :param value: Typed ACBus object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.ac_bus_type import sienna_ac_bus_type_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'id': value.identifier, 'number': value.number, 'name': value.name, 'available': value.available, 'bustype': None if value.bus_type is None else sienna_ac_bus_type_to_json(value.bus_type), 'angle': value.angle, 'magnitude': value.magnitude, 'voltage_limits': None if value.voltage_limits is None else sienna_min_max_to_json(value.voltage_limits), 'base_voltage': value.base_voltage, 'area': value.area, 'load_zone': value.load_zone}
