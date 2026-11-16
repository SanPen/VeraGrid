# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Sienna ``FixedAdmittance`` device object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value


class SiennaFixedAdmittance(SiennaSchemaModel):
    """Represent one fixed shunt admittance connected to an AC bus."""

    __slots__ = ("identifier", "name", "available", "bus", "Y", "conductance", "susceptance", "base_power",
                 "admittance_units", "dynamic_injector")

    def __init__(self, identifier: int, name: str, available: bool, bus: int, conductance: float,
                 susceptance: float, base_power: float, admittance_units: str,
                 dynamic_injector: int | None) -> None:
        """Store the component-MVAr shunt values.

        :param identifier: Sienna component identifier.
        :param name: Shunt name.
        :param available: Network availability flag.
        :param bus: Connected bus identifier.
        :param conductance: Conductance in MW at one pu voltage.
        :param susceptance: Susceptance in MVAr at one pu voltage.
        :param base_power: Component base power in MVA.
        :return: None.
        """
        self.identifier: int = identifier
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.Y: complex = complex(conductance, susceptance)
        self.conductance: float = conductance
        self.susceptance: float = susceptance
        self.base_power: float = base_power
        self.admittance_units: str = admittance_units
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_fixed_admittance(data: dict[str, Any]) -> SiennaFixedAdmittance:
    """Parse declared FixedAdmittance properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FixedAdmittance object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import parse_sienna_complex_number
    from VeraGridEngine.IO.sienna.devices.core.common.shunt_admittance_unit_basis import parse_sienna_shunt_admittance_unit_basis
    admittance: SiennaComplexNumber = parse_sienna_complex_number(get_required_value(data, 'Y', 'FixedAdmittance'))
    return SiennaFixedAdmittance(identifier=get_required_value(data, 'id', 'FixedAdmittance'), name=get_required_value(data, 'name', 'FixedAdmittance'), available=get_required_value(data, 'available', 'FixedAdmittance'), bus=get_required_value(data, 'bus', 'FixedAdmittance'), conductance=admittance.real, susceptance=admittance.imag, base_power=get_required_value(data, 'base_power', 'FixedAdmittance'), admittance_units=None if data.get('admittance_units', None) is None else parse_sienna_shunt_admittance_unit_basis(data.get('admittance_units', None)), dynamic_injector=data.get('dynamic_injector', None))

def sienna_fixed_admittance_to_json(value: SiennaFixedAdmittance) -> dict[str, Any]:
    """Write every FixedAdmittance slot to explicit schema property names.

    :param value: Typed FixedAdmittance object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import sienna_complex_number_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.shunt_admittance_unit_basis import sienna_shunt_admittance_unit_basis_to_json
    return {'id': value.identifier, 'name': value.name, 'available': value.available, 'bus': value.bus, 'admittance_units': None if value.admittance_units is None else sienna_shunt_admittance_unit_basis_to_json(value.admittance_units), 'Y': {'real': value.Y.real, 'imag': value.Y.imag}, 'base_power': value.base_power, 'dynamic_injector': value.dynamic_injector}
