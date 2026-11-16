# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna EmissionsData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.emission_basis import SiennaEmissionBasis
    from VeraGridEngine.IO.sienna.devices.core.common.energy_unit import SiennaEnergyUnit
    from VeraGridEngine.IO.sienna.devices.core.common.mass_unit import SiennaMassUnit
    from VeraGridEngine.IO.sienna.devices.core.common.pollutant_type import SiennaPollutantType
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import SiennaValueCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaEmissionsData(SiennaSchemaModel):
    """Expose every declared EmissionsData property through fixed slots."""

    __slots__ = ('id', 'name', 'pollutant', 'emission_rate', 'basis', 'start_up_adder', 'mass_unit', 'energy_unit', 'gwp', 'available',)

    def __init__(self, id: int, name: str, pollutant: SiennaPollutantType, emission_rate: SiennaValueCurve, basis: SiennaEmissionBasis, start_up_adder: float, mass_unit: SiennaMassUnit, energy_unit: SiennaEnergyUnit, gwp: float, available: bool) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.pollutant: SiennaPollutantType = pollutant
        self.emission_rate: SiennaValueCurve = emission_rate
        self.basis: SiennaEmissionBasis = basis
        self.start_up_adder: float = start_up_adder
        self.mass_unit: SiennaMassUnit = mass_unit
        self.energy_unit: SiennaEnergyUnit = energy_unit
        self.gwp: float = gwp
        self.available: bool = available


def parse_sienna_emissions_data(data: dict[str, Any]) -> SiennaEmissionsData:
    """Parse declared EmissionsData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed EmissionsData object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.emission_basis import parse_sienna_emission_basis
    from VeraGridEngine.IO.sienna.devices.core.common.energy_unit import parse_sienna_energy_unit
    from VeraGridEngine.IO.sienna.devices.core.common.mass_unit import parse_sienna_mass_unit
    from VeraGridEngine.IO.sienna.devices.core.common.pollutant_type import parse_sienna_pollutant_type
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
    return SiennaEmissionsData(id=get_required_value(data, 'id', 'EmissionsData'), name=get_required_value(data, 'name', 'EmissionsData'), pollutant=parse_sienna_pollutant_type(get_required_value(data, 'pollutant', 'EmissionsData')), emission_rate=parse_sienna_value_curve(get_required_value(data, 'emission_rate', 'EmissionsData')), basis=parse_sienna_emission_basis(get_required_value(data, 'basis', 'EmissionsData')), start_up_adder=data.get('start_up_adder', None), mass_unit=None if data.get('mass_unit', None) is None else parse_sienna_mass_unit(data.get('mass_unit', None)), energy_unit=parse_sienna_energy_unit(get_required_value(data, 'energy_unit', 'EmissionsData')), gwp=data.get('gwp', None), available=data.get('available', None))

def sienna_emissions_data_to_json(value: SiennaEmissionsData) -> dict[str, Any]:
    """Write every EmissionsData slot to explicit schema property names.

    :param value: Typed EmissionsData object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.emission_basis import sienna_emission_basis_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.energy_unit import sienna_energy_unit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.mass_unit import sienna_mass_unit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.pollutant_type import sienna_pollutant_type_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import sienna_value_curve_to_json
    return {'id': value.id, 'name': value.name, 'pollutant': sienna_pollutant_type_to_json(value.pollutant), 'emission_rate': sienna_value_curve_to_json(value.emission_rate), 'basis': sienna_emission_basis_to_json(value.basis), 'start_up_adder': value.start_up_adder, 'mass_unit': None if value.mass_unit is None else sienna_mass_unit_to_json(value.mass_unit), 'energy_unit': sienna_energy_unit_to_json(value.energy_unit), 'gwp': value.gwp, 'available': value.available}
