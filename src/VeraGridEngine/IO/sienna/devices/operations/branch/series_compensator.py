# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna SeriesCompensator schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import SiennaImpedanceUnitBasis
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import SiennaOperationalFlowLimit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.operations.common.series_compensator_control_mode import SiennaSeriesCompensatorControlMode

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSeriesCompensator(SiennaSchemaModel):
    """Expose every declared SeriesCompensator property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'active_power_flow', 'reactive_power_flow', 'arc', 'r', 'x', 'rating', 'control_mode', 'reactance_limits', 'active_power_flow_setpoint', 'rating_b', 'rating_c', 'operational_flow_limit', 'base_power', 'power_units', 'parameter_units',)

    def __init__(self, id: int, name: str, available: bool, active_power_flow: float, reactive_power_flow: float, arc: int, r: float, x: float, rating: float, control_mode: SiennaSeriesCompensatorControlMode, reactance_limits: SiennaMinMax, active_power_flow_setpoint: float, rating_b: float, rating_c: float, operational_flow_limit: SiennaOperationalFlowLimit, base_power: float, power_units: SiennaUnitSystem, parameter_units: SiennaImpedanceUnitBasis) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.active_power_flow: float = active_power_flow
        self.reactive_power_flow: float = reactive_power_flow
        self.arc: int = arc
        self.r: float = r
        self.x: float = x
        self.rating: float = rating
        self.control_mode: SiennaSeriesCompensatorControlMode = control_mode
        self.reactance_limits: SiennaMinMax = reactance_limits
        self.active_power_flow_setpoint: float = active_power_flow_setpoint
        self.rating_b: float = rating_b
        self.rating_c: float = rating_c
        self.operational_flow_limit: SiennaOperationalFlowLimit = operational_flow_limit
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.parameter_units: SiennaImpedanceUnitBasis = parameter_units


def parse_sienna_series_compensator(data: dict[str, Any]) -> SiennaSeriesCompensator:
    """Parse declared SeriesCompensator properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed SeriesCompensator object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import parse_sienna_impedance_unit_basis
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.series_compensator_control_mode import parse_sienna_series_compensator_control_mode
    return SiennaSeriesCompensator(id=get_required_value(data, 'id', 'SeriesCompensator'), name=get_required_value(data, 'name', 'SeriesCompensator'), available=get_required_value(data, 'available', 'SeriesCompensator'), active_power_flow=get_required_value(data, 'active_power_flow', 'SeriesCompensator'), reactive_power_flow=get_required_value(data, 'reactive_power_flow', 'SeriesCompensator'), arc=get_required_value(data, 'arc', 'SeriesCompensator'), r=get_required_value(data, 'r', 'SeriesCompensator'), x=get_required_value(data, 'x', 'SeriesCompensator'), rating=get_required_value(data, 'rating', 'SeriesCompensator'), control_mode=None if data.get('control_mode', None) is None else parse_sienna_series_compensator_control_mode(data.get('control_mode', None)), reactance_limits=None if data.get('reactance_limits', None) is None else parse_sienna_min_max(data.get('reactance_limits', None)), active_power_flow_setpoint=data.get('active_power_flow_setpoint', None), rating_b=data.get('rating_b', None), rating_c=data.get('rating_c', None), operational_flow_limit=None if data.get('operational_flow_limit', None) is None else parse_sienna_operational_flow_limit(data.get('operational_flow_limit', None)), base_power=get_required_value(data, 'base_power', 'SeriesCompensator'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'SeriesCompensator')), parameter_units=None if data.get('parameter_units', None) is None else parse_sienna_impedance_unit_basis(data.get('parameter_units', None)))

def sienna_series_compensator_to_json(value: SiennaSeriesCompensator) -> dict[str, Any]:
    """Write every SeriesCompensator slot to explicit schema property names.

    :param value: Typed SeriesCompensator object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import sienna_impedance_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import sienna_operational_flow_limit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.series_compensator_control_mode import sienna_series_compensator_control_mode_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'active_power_flow': value.active_power_flow, 'reactive_power_flow': value.reactive_power_flow, 'arc': value.arc, 'r': value.r, 'x': value.x, 'rating': value.rating, 'control_mode': None if value.control_mode is None else sienna_series_compensator_control_mode_to_json(value.control_mode), 'reactance_limits': None if value.reactance_limits is None else sienna_min_max_to_json(value.reactance_limits), 'active_power_flow_setpoint': value.active_power_flow_setpoint, 'rating_b': value.rating_b, 'rating_c': value.rating_c, 'operational_flow_limit': None if value.operational_flow_limit is None else sienna_operational_flow_limit_to_json(value.operational_flow_limit), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'parameter_units': None if value.parameter_units is None else sienna_impedance_unit_basis_to_json(value.parameter_units)}
