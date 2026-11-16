# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna GenericArcImpedance schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import SiennaImpedanceUnitBasis
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import SiennaOperationalFlowLimit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaGenericArcImpedance(SiennaSchemaModel):
    """Expose every declared GenericArcImpedance property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'active_power_flow', 'reactive_power_flow', 'operational_flow_limit', 'arc', 'base_power', 'power_units', 'parameter_units', 'r', 'x',)

    def __init__(self, id: int, name: str, available: bool, active_power_flow: float, reactive_power_flow: float, operational_flow_limit: SiennaOperationalFlowLimit, arc: int, base_power: float, power_units: SiennaUnitSystem, parameter_units: SiennaImpedanceUnitBasis, r: float, x: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.active_power_flow: float = active_power_flow
        self.reactive_power_flow: float = reactive_power_flow
        self.operational_flow_limit: SiennaOperationalFlowLimit = operational_flow_limit
        self.arc: int = arc
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.parameter_units: SiennaImpedanceUnitBasis = parameter_units
        self.r: float = r
        self.x: float = x


def parse_sienna_generic_arc_impedance(data: dict[str, Any]) -> SiennaGenericArcImpedance:
    """Parse declared GenericArcImpedance properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed GenericArcImpedance object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import parse_sienna_impedance_unit_basis
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaGenericArcImpedance(id=get_required_value(data, 'id', 'GenericArcImpedance'), name=get_required_value(data, 'name', 'GenericArcImpedance'), available=get_required_value(data, 'available', 'GenericArcImpedance'), active_power_flow=get_required_value(data, 'active_power_flow', 'GenericArcImpedance'), reactive_power_flow=get_required_value(data, 'reactive_power_flow', 'GenericArcImpedance'), operational_flow_limit=None if data.get('operational_flow_limit', None) is None else parse_sienna_operational_flow_limit(data.get('operational_flow_limit', None)), arc=get_required_value(data, 'arc', 'GenericArcImpedance'), base_power=get_required_value(data, 'base_power', 'GenericArcImpedance'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'GenericArcImpedance')), parameter_units=None if data.get('parameter_units', None) is None else parse_sienna_impedance_unit_basis(data.get('parameter_units', None)), r=get_required_value(data, 'r', 'GenericArcImpedance'), x=get_required_value(data, 'x', 'GenericArcImpedance'))

def sienna_generic_arc_impedance_to_json(value: SiennaGenericArcImpedance) -> dict[str, Any]:
    """Write every GenericArcImpedance slot to explicit schema property names.

    :param value: Typed GenericArcImpedance object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import sienna_impedance_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import sienna_operational_flow_limit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'active_power_flow': value.active_power_flow, 'reactive_power_flow': value.reactive_power_flow, 'operational_flow_limit': None if value.operational_flow_limit is None else sienna_operational_flow_limit_to_json(value.operational_flow_limit), 'arc': value.arc, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'parameter_units': None if value.parameter_units is None else sienna_impedance_unit_basis_to_json(value.parameter_units), 'r': value.r, 'x': value.x}
