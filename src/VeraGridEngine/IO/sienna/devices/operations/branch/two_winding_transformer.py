# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TwoWindingTransformer schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.admittance_unit_basis import SiennaAdmittanceUnitBasis
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import SiennaComplexNumber
    from VeraGridEngine.IO.sienna.devices.operations.common.two_winding_transformer_shunt_location import SiennaTwoWindingTransformerShuntLocation

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTwoWindingTransformer(SiennaSchemaModel):
    """Expose every declared TwoWindingTransformer property through fixed slots."""

    __slots__ = ('id', 'name', 'circuit', 'admittance_units', 'magnetizing_shunt', 'shunt_location',)

    def __init__(self, id: int, name: str, circuit: int, admittance_units: SiennaAdmittanceUnitBasis, magnetizing_shunt: SiennaComplexNumber, shunt_location: SiennaTwoWindingTransformerShuntLocation) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.circuit: int = circuit
        self.admittance_units: SiennaAdmittanceUnitBasis = admittance_units
        self.magnetizing_shunt: SiennaComplexNumber = magnetizing_shunt
        self.shunt_location: SiennaTwoWindingTransformerShuntLocation = shunt_location


def parse_sienna_two_winding_transformer(data: dict[str, Any]) -> SiennaTwoWindingTransformer:
    """Parse declared TwoWindingTransformer properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TwoWindingTransformer object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.admittance_unit_basis import parse_sienna_admittance_unit_basis
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import parse_sienna_complex_number
    from VeraGridEngine.IO.sienna.devices.operations.common.two_winding_transformer_shunt_location import parse_sienna_two_winding_transformer_shunt_location
    return SiennaTwoWindingTransformer(id=get_required_value(data, 'id', 'TwoWindingTransformer'), name=get_required_value(data, 'name', 'TwoWindingTransformer'), circuit=get_required_value(data, 'circuit', 'TwoWindingTransformer'), admittance_units=None if data.get('admittance_units', None) is None else parse_sienna_admittance_unit_basis(data.get('admittance_units', None)), magnetizing_shunt=None if data.get('magnetizing_shunt', None) is None else parse_sienna_complex_number(data.get('magnetizing_shunt', None)), shunt_location=None if data.get('shunt_location', None) is None else parse_sienna_two_winding_transformer_shunt_location(data.get('shunt_location', None)))

def sienna_two_winding_transformer_to_json(value: SiennaTwoWindingTransformer) -> dict[str, Any]:
    """Write every TwoWindingTransformer slot to explicit schema property names.

    :param value: Typed TwoWindingTransformer object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.admittance_unit_basis import sienna_admittance_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import sienna_complex_number_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.two_winding_transformer_shunt_location import sienna_two_winding_transformer_shunt_location_to_json
    return {'id': value.id, 'name': value.name, 'circuit': value.circuit, 'admittance_units': None if value.admittance_units is None else sienna_admittance_unit_basis_to_json(value.admittance_units), 'magnetizing_shunt': None if value.magnetizing_shunt is None else sienna_complex_number_to_json(value.magnetizing_shunt), 'shunt_location': None if value.shunt_location is None else sienna_two_winding_transformer_shunt_location_to_json(value.shunt_location)}
