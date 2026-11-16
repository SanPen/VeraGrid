# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel
"""Sienna ``Area`` device object."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value
from VeraGridEngine.IO.sienna.devices.enums import SiennaUnitSystem


class SiennaArea(SiennaSchemaModel):
    """Represent one Sienna ``Area`` component."""

    __slots__ = ("identifier", "name", "peak_active_power", "peak_reactive_power", "load_response",
                 "scheduled_net_interchange", "out_of_area_load_ids", "base_power", "power_units")

    def __init__(self, identifier: int, name: str, peak_active_power: float, peak_reactive_power: float,
                 load_response: float, scheduled_net_interchange: float | None, out_of_area_load_ids: list[int],
                 base_power: float, power_units: SiennaUnitSystem) -> None:
        """Store one Sienna area record.

        :param identifier: Sienna area identifier.
        :param name: Area name.
        :param peak_active_power: Peak active power.
        :param peak_reactive_power: Peak reactive power.
        :param load_response: Load-frequency damping coefficient.
        :param scheduled_net_interchange: Scheduled net interchange when declared.
        :param out_of_area_load_ids: Loads owned by this area on external buses.
        :param base_power: Component base power in MVA.
        :param power_units: Sienna power-family unit basis.
        :return: None.
        """
        self.identifier: int = identifier
        self.name: str = name
        self.peak_active_power: float = peak_active_power
        self.peak_reactive_power: float = peak_reactive_power
        self.load_response: float = load_response
        self.scheduled_net_interchange: float | None = scheduled_net_interchange
        self.out_of_area_load_ids: list[int] = out_of_area_load_ids
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units


def parse_sienna_area(data: dict[str, Any]) -> SiennaArea:
    """Parse declared Area properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed Area object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaArea(identifier=get_required_value(data, 'id', 'Area'), name=get_required_value(data, 'name', 'Area'), peak_active_power=data.get('peak_active_power', 0.0), peak_reactive_power=data.get('peak_reactive_power', 0.0), load_response=data.get('load_response', 0.0), scheduled_net_interchange=data.get('scheduled_net_interchange', None), out_of_area_load_ids=data.get('out_of_area_load_ids', list()), base_power=get_required_value(data, 'base_power', 'Area'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'Area')))

def sienna_area_to_json(value: SiennaArea) -> dict[str, Any]:
    """Write every Area slot to explicit schema property names.

    :param value: Typed Area object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.identifier, 'name': value.name, 'peak_active_power': value.peak_active_power, 'peak_reactive_power': value.peak_reactive_power, 'load_response': value.load_response, 'scheduled_net_interchange': value.scheduled_net_interchange, 'out_of_area_load_ids': value.out_of_area_load_ids, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units)}
