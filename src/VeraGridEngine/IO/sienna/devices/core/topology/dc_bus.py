# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel
"""Sienna ``DCBus`` device object."""

from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value


class SiennaDCBus(SiennaSchemaModel):
    """Represent one Sienna ``DCBus`` component."""

    __slots__ = ("identifier", "name", "available", "number", "area", "load_zone", "base_voltage",
                 "magnitude", "voltage_limits")

    def __init__(self, identifier: int, name: str, available: bool, number: float, area: int | None,
                 load_zone: int | None, base_voltage: float | None, magnitude: float | None,
                 voltage_limits: dict[str, float] | None) -> None:
        """Store one Sienna DC-bus record.

        :param identifier: Sienna DC-bus identifier.
        :param name: DC-bus name.
        :param available: Network availability flag.
        :param number: User-visible bus number.
        :param area: Area identifier when declared.
        :param load_zone: Load-zone identifier when declared.
        :param base_voltage: Nominal voltage in kV when declared.
        :param magnitude: Initial voltage magnitude in pu when declared.
        :param voltage_limits: Voltage limits when declared.
        :return: None.
        """
        self.identifier: int = identifier
        self.name: str = name
        self.available: bool = available
        self.number: float = number
        self.area: int | None = area
        self.load_zone: int | None = load_zone
        self.base_voltage: float | None = base_voltage
        self.magnitude: float | None = magnitude
        self.voltage_limits: dict[str, float] | None = voltage_limits


def parse_sienna_dc_bus(data: dict[str, Any]) -> SiennaDCBus:
    """Parse declared DCBus properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed DCBus object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaDCBus(area=data.get('area', None), available=get_required_value(data, 'available', 'DCBus'), base_voltage=data.get('base_voltage', 0.0), identifier=get_required_value(data, 'id', 'DCBus'), load_zone=data.get('load_zone', None), magnitude=data.get('magnitude', 1.0), name=get_required_value(data, 'name', 'DCBus'), number=get_required_value(data, 'number', 'DCBus'), voltage_limits=None if data.get('voltage_limits', None) is None else parse_sienna_min_max(data.get('voltage_limits', None)))

def sienna_dc_bus_to_json(value: SiennaDCBus) -> dict[str, Any]:
    """Write every DCBus slot to explicit schema property names.

    :param value: Typed DCBus object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'area': value.area, 'available': value.available, 'base_voltage': value.base_voltage, 'id': value.identifier, 'load_zone': value.load_zone, 'magnitude': value.magnitude, 'name': value.name, 'number': value.number, 'voltage_limits': None if value.voltage_limits is None else sienna_min_max_to_json(value.voltage_limits)}
