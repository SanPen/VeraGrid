# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TransformerCircuit schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import SiennaImpedanceUnitBasis
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import SiennaOperationalFlowLimit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.operations.common.transformer_control_objective import SiennaTransformerControlObjective

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTransformerCircuit(SiennaSchemaModel):
    """Expose every declared TransformerCircuit property through fixed slots."""

    __slots__ = ('id', 'available', 'arc', 'tap', 'alpha', 'parameter_units', 'r', 'x', 'control_objective', 'regulated_bus_number', 'tap_ratio_limits', 'phase_angle_limits', 'controlled_voltage_limits', 'controlled_reactive_power_flow_limits', 'controlled_active_power_flow_limits', 'number_of_tap_positions', 'rating', 'rating_b', 'rating_c', 'operational_flow_limit', 'active_power_flow', 'reactive_power_flow', 'base_power', 'power_units', 'base_voltage_primary', 'base_voltage_secondary',)

    def __init__(self, id: int, available: bool, arc: int, tap: float, alpha: float, parameter_units: SiennaImpedanceUnitBasis, r: float, x: float, control_objective: SiennaTransformerControlObjective, regulated_bus_number: int, tap_ratio_limits: SiennaMinMax, phase_angle_limits: SiennaMinMax, controlled_voltage_limits: SiennaMinMax, controlled_reactive_power_flow_limits: SiennaMinMax, controlled_active_power_flow_limits: SiennaMinMax, number_of_tap_positions: int, rating: float, rating_b: float, rating_c: float, operational_flow_limit: SiennaOperationalFlowLimit, active_power_flow: float, reactive_power_flow: float, base_power: float, power_units: SiennaUnitSystem, base_voltage_primary: float, base_voltage_secondary: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.available: bool = available
        self.arc: int = arc
        self.tap: float = tap
        self.alpha: float = alpha
        self.parameter_units: SiennaImpedanceUnitBasis = parameter_units
        self.r: float = r
        self.x: float = x
        self.control_objective: SiennaTransformerControlObjective = control_objective
        self.regulated_bus_number: int = regulated_bus_number
        self.tap_ratio_limits: SiennaMinMax = tap_ratio_limits
        self.phase_angle_limits: SiennaMinMax = phase_angle_limits
        self.controlled_voltage_limits: SiennaMinMax = controlled_voltage_limits
        self.controlled_reactive_power_flow_limits: SiennaMinMax = controlled_reactive_power_flow_limits
        self.controlled_active_power_flow_limits: SiennaMinMax = controlled_active_power_flow_limits
        self.number_of_tap_positions: int = number_of_tap_positions
        self.rating: float = rating
        self.rating_b: float = rating_b
        self.rating_c: float = rating_c
        self.operational_flow_limit: SiennaOperationalFlowLimit = operational_flow_limit
        self.active_power_flow: float = active_power_flow
        self.reactive_power_flow: float = reactive_power_flow
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.base_voltage_primary: float = base_voltage_primary
        self.base_voltage_secondary: float = base_voltage_secondary


def parse_sienna_transformer_circuit(data: dict[str, Any]) -> SiennaTransformerCircuit:
    """Parse declared TransformerCircuit properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TransformerCircuit object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import parse_sienna_impedance_unit_basis
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.transformer_control_objective import parse_sienna_transformer_control_objective
    return SiennaTransformerCircuit(id=get_required_value(data, 'id', 'TransformerCircuit'), available=get_required_value(data, 'available', 'TransformerCircuit'), arc=get_required_value(data, 'arc', 'TransformerCircuit'), tap=data.get('tap', None), alpha=data.get('alpha', None), parameter_units=None if data.get('parameter_units', None) is None else parse_sienna_impedance_unit_basis(data.get('parameter_units', None)), r=data.get('r', None), x=data.get('x', None), control_objective=None if data.get('control_objective', None) is None else parse_sienna_transformer_control_objective(data.get('control_objective', None)), regulated_bus_number=data.get('regulated_bus_number', None), tap_ratio_limits=None if data.get('tap_ratio_limits', None) is None else parse_sienna_min_max(data.get('tap_ratio_limits', None)), phase_angle_limits=None if data.get('phase_angle_limits', None) is None else parse_sienna_min_max(data.get('phase_angle_limits', None)), controlled_voltage_limits=None if data.get('controlled_voltage_limits', None) is None else parse_sienna_min_max(data.get('controlled_voltage_limits', None)), controlled_reactive_power_flow_limits=None if data.get('controlled_reactive_power_flow_limits', None) is None else parse_sienna_min_max(data.get('controlled_reactive_power_flow_limits', None)), controlled_active_power_flow_limits=None if data.get('controlled_active_power_flow_limits', None) is None else parse_sienna_min_max(data.get('controlled_active_power_flow_limits', None)), number_of_tap_positions=data.get('number_of_tap_positions', None), rating=get_required_value(data, 'rating', 'TransformerCircuit'), rating_b=data.get('rating_b', None), rating_c=data.get('rating_c', None), operational_flow_limit=None if data.get('operational_flow_limit', None) is None else parse_sienna_operational_flow_limit(data.get('operational_flow_limit', None)), active_power_flow=data.get('active_power_flow', None), reactive_power_flow=data.get('reactive_power_flow', None), base_power=data.get('base_power', None), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'TransformerCircuit')), base_voltage_primary=data.get('base_voltage_primary', None), base_voltage_secondary=data.get('base_voltage_secondary', None))

def sienna_transformer_circuit_to_json(value: SiennaTransformerCircuit) -> dict[str, Any]:
    """Write every TransformerCircuit slot to explicit schema property names.

    :param value: Typed TransformerCircuit object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import sienna_impedance_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import sienna_operational_flow_limit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.transformer_control_objective import sienna_transformer_control_objective_to_json
    return {'id': value.id, 'available': value.available, 'arc': value.arc, 'tap': value.tap, 'alpha': value.alpha, 'parameter_units': None if value.parameter_units is None else sienna_impedance_unit_basis_to_json(value.parameter_units), 'r': value.r, 'x': value.x, 'control_objective': None if value.control_objective is None else sienna_transformer_control_objective_to_json(value.control_objective), 'regulated_bus_number': value.regulated_bus_number, 'tap_ratio_limits': None if value.tap_ratio_limits is None else sienna_min_max_to_json(value.tap_ratio_limits), 'phase_angle_limits': None if value.phase_angle_limits is None else sienna_min_max_to_json(value.phase_angle_limits), 'controlled_voltage_limits': None if value.controlled_voltage_limits is None else sienna_min_max_to_json(value.controlled_voltage_limits), 'controlled_reactive_power_flow_limits': None if value.controlled_reactive_power_flow_limits is None else sienna_min_max_to_json(value.controlled_reactive_power_flow_limits), 'controlled_active_power_flow_limits': None if value.controlled_active_power_flow_limits is None else sienna_min_max_to_json(value.controlled_active_power_flow_limits), 'number_of_tap_positions': value.number_of_tap_positions, 'rating': value.rating, 'rating_b': value.rating_b, 'rating_c': value.rating_c, 'operational_flow_limit': None if value.operational_flow_limit is None else sienna_operational_flow_limit_to_json(value.operational_flow_limit), 'active_power_flow': value.active_power_flow, 'reactive_power_flow': value.reactive_power_flow, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'base_voltage_primary': value.base_voltage_primary, 'base_voltage_secondary': value.base_voltage_secondary}
