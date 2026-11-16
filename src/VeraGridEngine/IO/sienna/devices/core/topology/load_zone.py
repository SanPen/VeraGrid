# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel
"""Sienna ``LoadZone`` device object."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value
from VeraGridEngine.IO.sienna.devices.enums import SiennaUnitSystem


class SiennaLoadZone(SiennaSchemaModel):
    """Represent one Sienna ``LoadZone`` component."""

    __slots__ = ("identifier", "name", "peak_active_power", "peak_reactive_power", "base_power", "power_units")

    def __init__(self, identifier: int, name: str, peak_active_power: float, peak_reactive_power: float,
                 base_power: float, power_units: SiennaUnitSystem) -> None:
        """Store one Sienna load-zone record.

        :param identifier: Sienna load-zone identifier.
        :param name: Load-zone name.
        :param peak_active_power: Peak active power.
        :param peak_reactive_power: Peak reactive power.
        :param base_power: Component base power in MVA.
        :param power_units: Sienna power-family unit basis.
        :return: None.
        """
        self.identifier: int = identifier
        self.name: str = name
        self.peak_active_power: float = peak_active_power
        self.peak_reactive_power: float = peak_reactive_power
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units


def parse_sienna_load_zone(data: dict[str, Any]) -> SiennaLoadZone:
    """Parse declared LoadZone properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed LoadZone object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaLoadZone(identifier=get_required_value(data, 'id', 'LoadZone'), name=get_required_value(data, 'name', 'LoadZone'), peak_active_power=get_required_value(data, 'peak_active_power', 'LoadZone'), peak_reactive_power=get_required_value(data, 'peak_reactive_power', 'LoadZone'), base_power=get_required_value(data, 'base_power', 'LoadZone'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'LoadZone')))

def sienna_load_zone_to_json(value: SiennaLoadZone) -> dict[str, Any]:
    """Write every LoadZone slot to explicit schema property names.

    :param value: Typed LoadZone object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.identifier, 'name': value.name, 'peak_active_power': value.peak_active_power, 'peak_reactive_power': value.peak_reactive_power, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units)}
