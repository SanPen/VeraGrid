# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ThreeWindingTransformer schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.admittance_unit_basis import SiennaAdmittanceUnitBasis
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import SiennaComplexNumber
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import SiennaImpedanceUnitBasis
    from VeraGridEngine.IO.sienna.devices.operations.common.three_winding_transformer_shunt_location import SiennaThreeWindingTransformerShuntLocation

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaThreeWindingTransformer(SiennaSchemaModel):
    """Expose every declared ThreeWindingTransformer property through fixed slots."""

    __slots__ = ('id', 'name', 'primary_circuit', 'secondary_circuit', 'tertiary_circuit', 'star_bus', 'parameter_units', 'r_12', 'x_12', 'r_23', 'x_23', 'r_31', 'x_31', 'base_power_12', 'base_power_23', 'base_power_31', 'admittance_units', 'magnetizing_shunt', 'shunt_location',)

    def __init__(self, id: int, name: str, primary_circuit: int, secondary_circuit: int, tertiary_circuit: int, star_bus: int, parameter_units: SiennaImpedanceUnitBasis, r_12: float, x_12: float, r_23: float, x_23: float, r_31: float, x_31: float, base_power_12: float, base_power_23: float, base_power_31: float, admittance_units: SiennaAdmittanceUnitBasis, magnetizing_shunt: SiennaComplexNumber, shunt_location: SiennaThreeWindingTransformerShuntLocation) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.primary_circuit: int = primary_circuit
        self.secondary_circuit: int = secondary_circuit
        self.tertiary_circuit: int = tertiary_circuit
        self.star_bus: int = star_bus
        self.parameter_units: SiennaImpedanceUnitBasis = parameter_units
        self.r_12: float = r_12
        self.x_12: float = x_12
        self.r_23: float = r_23
        self.x_23: float = x_23
        self.r_31: float = r_31
        self.x_31: float = x_31
        self.base_power_12: float = base_power_12
        self.base_power_23: float = base_power_23
        self.base_power_31: float = base_power_31
        self.admittance_units: SiennaAdmittanceUnitBasis = admittance_units
        self.magnetizing_shunt: SiennaComplexNumber = magnetizing_shunt
        self.shunt_location: SiennaThreeWindingTransformerShuntLocation = shunt_location


def parse_sienna_three_winding_transformer(data: dict[str, Any]) -> SiennaThreeWindingTransformer:
    """Parse declared ThreeWindingTransformer properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ThreeWindingTransformer object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.admittance_unit_basis import parse_sienna_admittance_unit_basis
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import parse_sienna_complex_number
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import parse_sienna_impedance_unit_basis
    from VeraGridEngine.IO.sienna.devices.operations.common.three_winding_transformer_shunt_location import parse_sienna_three_winding_transformer_shunt_location
    return SiennaThreeWindingTransformer(id=get_required_value(data, 'id', 'ThreeWindingTransformer'), name=get_required_value(data, 'name', 'ThreeWindingTransformer'), primary_circuit=get_required_value(data, 'primary_circuit', 'ThreeWindingTransformer'), secondary_circuit=get_required_value(data, 'secondary_circuit', 'ThreeWindingTransformer'), tertiary_circuit=get_required_value(data, 'tertiary_circuit', 'ThreeWindingTransformer'), star_bus=get_required_value(data, 'star_bus', 'ThreeWindingTransformer'), parameter_units=None if data.get('parameter_units', None) is None else parse_sienna_impedance_unit_basis(data.get('parameter_units', None)), r_12=data.get('r_12', None), x_12=data.get('x_12', None), r_23=data.get('r_23', None), x_23=data.get('x_23', None), r_31=data.get('r_31', None), x_31=data.get('x_31', None), base_power_12=data.get('base_power_12', None), base_power_23=data.get('base_power_23', None), base_power_31=data.get('base_power_31', None), admittance_units=None if data.get('admittance_units', None) is None else parse_sienna_admittance_unit_basis(data.get('admittance_units', None)), magnetizing_shunt=None if data.get('magnetizing_shunt', None) is None else parse_sienna_complex_number(data.get('magnetizing_shunt', None)), shunt_location=None if data.get('shunt_location', None) is None else parse_sienna_three_winding_transformer_shunt_location(data.get('shunt_location', None)))

def sienna_three_winding_transformer_to_json(value: SiennaThreeWindingTransformer) -> dict[str, Any]:
    """Write every ThreeWindingTransformer slot to explicit schema property names.

    :param value: Typed ThreeWindingTransformer object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.admittance_unit_basis import sienna_admittance_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import sienna_complex_number_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import sienna_impedance_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.three_winding_transformer_shunt_location import sienna_three_winding_transformer_shunt_location_to_json
    return {'id': value.id, 'name': value.name, 'primary_circuit': value.primary_circuit, 'secondary_circuit': value.secondary_circuit, 'tertiary_circuit': value.tertiary_circuit, 'star_bus': value.star_bus, 'parameter_units': None if value.parameter_units is None else sienna_impedance_unit_basis_to_json(value.parameter_units), 'r_12': value.r_12, 'x_12': value.x_12, 'r_23': value.r_23, 'x_23': value.x_23, 'r_31': value.r_31, 'x_31': value.x_31, 'base_power_12': value.base_power_12, 'base_power_23': value.base_power_23, 'base_power_31': value.base_power_31, 'admittance_units': None if value.admittance_units is None else sienna_admittance_unit_basis_to_json(value.admittance_units), 'magnetizing_shunt': None if value.magnetizing_shunt is None else sienna_complex_number_to_json(value.magnetizing_shunt), 'shunt_location': None if value.shunt_location is None else sienna_three_winding_transformer_shunt_location_to_json(value.shunt_location)}
