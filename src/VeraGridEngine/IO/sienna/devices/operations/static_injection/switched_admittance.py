# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SwitchedAdmittance schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import SiennaComplexNumber
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.shunt_admittance_unit_basis import SiennaShuntAdmittanceUnitBasis
    from VeraGridEngine.IO.sienna.devices.operations.common.switched_admittance_control_mode import SiennaSwitchedAdmittanceControlMode

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSwitchedAdmittance(SiennaSchemaModel):
    """Expose every declared SwitchedAdmittance property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'admittance_units', 'number_engaged', 'number_of_steps', 'Y_increase', 'solved_admittance', 'voltage_limits', 'reactive_power_range_limits', 'control_mode', 'regulated_bus_number', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, admittance_units: SiennaShuntAdmittanceUnitBasis, number_engaged: list[int], number_of_steps: list[int], Y_increase: list[SiennaComplexNumber], solved_admittance: float | None, voltage_limits: SiennaMinMax, reactive_power_range_limits: SiennaMinMax, control_mode: SiennaSwitchedAdmittanceControlMode, regulated_bus_number: int, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.admittance_units: SiennaShuntAdmittanceUnitBasis = admittance_units
        self.number_engaged: list[int] = number_engaged
        self.number_of_steps: list[int] = number_of_steps
        self.Y_increase: list[SiennaComplexNumber] = Y_increase
        self.solved_admittance: float | None = solved_admittance
        self.voltage_limits: SiennaMinMax = voltage_limits
        self.reactive_power_range_limits: SiennaMinMax = reactive_power_range_limits
        self.control_mode: SiennaSwitchedAdmittanceControlMode = control_mode
        self.regulated_bus_number: int = regulated_bus_number
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_switched_admittance(data: dict[str, Any]) -> SiennaSwitchedAdmittance:
    """Parse declared SwitchedAdmittance properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SwitchedAdmittance object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import parse_sienna_complex_number
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.shunt_admittance_unit_basis import parse_sienna_shunt_admittance_unit_basis
    from VeraGridEngine.IO.sienna.devices.operations.common.switched_admittance_control_mode import parse_sienna_switched_admittance_control_mode
    return SiennaSwitchedAdmittance(id=get_required_value(data, 'id', 'SwitchedAdmittance'), name=get_required_value(data, 'name', 'SwitchedAdmittance'), available=get_required_value(data, 'available', 'SwitchedAdmittance'), bus=get_required_value(data, 'bus', 'SwitchedAdmittance'), admittance_units=None if data.get('admittance_units', None) is None else parse_sienna_shunt_admittance_unit_basis(data.get('admittance_units', None)), number_engaged=data.get('number_engaged', None), number_of_steps=data.get('number_of_steps', None), Y_increase=None if data.get('Y_increase', None) is None else [parse_sienna_complex_number(item) for item in data.get('Y_increase', None)], solved_admittance=data.get('solved_admittance', None), voltage_limits=None if data.get('voltage_limits', None) is None else parse_sienna_min_max(data.get('voltage_limits', None)), reactive_power_range_limits=None if data.get('reactive_power_range_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_range_limits', None)), control_mode=None if data.get('control_mode', None) is None else parse_sienna_switched_admittance_control_mode(data.get('control_mode', None)), regulated_bus_number=data.get('regulated_bus_number', None), dynamic_injector=data.get('dynamic_injector', None))

def sienna_switched_admittance_to_json(value: SiennaSwitchedAdmittance) -> dict[str, Any]:
    """Write every SwitchedAdmittance slot to explicit schema property names.

    :param value: Typed SwitchedAdmittance object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import sienna_complex_number_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.shunt_admittance_unit_basis import sienna_shunt_admittance_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.switched_admittance_control_mode import sienna_switched_admittance_control_mode_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'admittance_units': None if value.admittance_units is None else sienna_shunt_admittance_unit_basis_to_json(value.admittance_units), 'number_engaged': value.number_engaged, 'number_of_steps': value.number_of_steps, 'Y_increase': None if value.Y_increase is None else [sienna_complex_number_to_json(item) for item in value.Y_increase], 'solved_admittance': value.solved_admittance, 'voltage_limits': None if value.voltage_limits is None else sienna_min_max_to_json(value.voltage_limits), 'reactive_power_range_limits': None if value.reactive_power_range_limits is None else sienna_min_max_to_json(value.reactive_power_range_limits), 'control_mode': None if value.control_mode is None else sienna_switched_admittance_control_mode_to_json(value.control_mode), 'regulated_bus_number': value.regulated_bus_number, 'dynamic_injector': value.dynamic_injector}
