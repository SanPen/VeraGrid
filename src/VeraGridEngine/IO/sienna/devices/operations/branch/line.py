# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel
"""Sienna ``Line`` device object."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.from_to import SiennaFromTo
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import SiennaImpedanceUnitBasis
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import SiennaOperationalFlowLimit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value
from VeraGridEngine.IO.sienna.devices.core.common.from_to import (SiennaFromTo, parse_sienna_from_to,
                                                                   sienna_from_to_to_json)
from VeraGridEngine.IO.sienna.devices.core.common.min_max import (SiennaMinMax, parse_sienna_min_max,
                                                                   sienna_min_max_to_json)
from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import (SiennaOperationalFlowLimit,
                                                                                  parse_sienna_operational_flow_limit,
                                                                                  sienna_operational_flow_limit_to_json)
from VeraGridEngine.IO.sienna.devices.enums import SiennaImpedanceUnitBasis, SiennaUnitSystem


class SiennaLine(SiennaSchemaModel):
    """Represent one Sienna ``Line`` component in the supported pu subset."""

    __slots__ = ("identifier", "name", "available", "arc", "resistance", "reactance", "susceptance",
                 "conductance", "base_power", "rating", "power_units", "parameter_units",
                 "active_power_flow", "reactive_power_flow", "r", "x", "b", "g", "rating_b", "rating_c",
                 "operational_flow_limit", "angle_limits")

    def __init__(self, identifier: int, name: str, available: bool, arc: int, resistance: float,
                 reactance: float, susceptance: float, conductance: float, base_power: float, rating: float,
                 power_units: SiennaUnitSystem, parameter_units: SiennaImpedanceUnitBasis,
                 active_power_flow: float, reactive_power_flow: float, b: SiennaFromTo | None,
                 g: SiennaFromTo | None, rating_b: float | None, rating_c: float | None,
                 operational_flow_limit: SiennaOperationalFlowLimit | None, angle_limits: SiennaMinMax) -> None:
        """Store a line whose electrical data is expressed in component-base pu.

        :param identifier: Sienna component identifier.
        :param name: Line name.
        :param available: Network availability flag.
        :param arc: Referenced Sienna arc identifier.
        :param resistance: Series resistance in pu.
        :param reactance: Series reactance in pu.
        :param susceptance: Total shunt susceptance in pu.
        :param conductance: Total shunt conductance in pu.
        :param base_power: Component base power in MVA.
        :param rating: Thermal rating in MVA.
        :param power_units: Sienna power-family unit basis.
        :param parameter_units: Sienna impedance unit basis.
        :return: None.
        """
        self.identifier: int = identifier
        self.name: str = name
        self.available: bool = available
        self.arc: int = arc
        self.resistance: float = resistance
        self.reactance: float = reactance
        self.susceptance: float = susceptance
        self.conductance: float = conductance
        self.base_power: float = base_power
        self.rating: float = rating
        self.power_units: SiennaUnitSystem = power_units
        self.parameter_units: SiennaImpedanceUnitBasis = parameter_units
        self.active_power_flow: float = active_power_flow
        self.reactive_power_flow: float = reactive_power_flow
        self.r: float = resistance
        self.x: float = reactance
        self.b: SiennaFromTo | None = b
        self.g: SiennaFromTo | None = g
        self.rating_b: float | None = rating_b
        self.rating_c: float | None = rating_c
        self.operational_flow_limit: SiennaOperationalFlowLimit | None = operational_flow_limit
        self.angle_limits: SiennaMinMax = angle_limits


def parse_sienna_line(data: dict[str, Any]) -> SiennaLine:
    """Parse declared Line properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed Line object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.from_to import parse_sienna_from_to
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import parse_sienna_impedance_unit_basis
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    resistance: float = get_required_value(data, 'r', 'Line')
    reactance: float = get_required_value(data, 'x', 'Line')
    return SiennaLine(identifier=get_required_value(data, 'id', 'Line'), name=get_required_value(data, 'name', 'Line'), available=get_required_value(data, 'available', 'Line'), arc=get_required_value(data, 'arc', 'Line'), resistance=resistance, reactance=reactance, susceptance=float(data.get('susceptance', 0.0)), conductance=float(data.get('conductance', 0.0)), base_power=get_required_value(data, 'base_power', 'Line'), rating=get_required_value(data, 'rating', 'Line'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'Line')), parameter_units=parse_sienna_impedance_unit_basis(data.get('parameter_units', 'COMPONENT_BASE')), active_power_flow=get_required_value(data, 'active_power_flow', 'Line'), reactive_power_flow=get_required_value(data, 'reactive_power_flow', 'Line'), b=None if data.get('b', None) is None else parse_sienna_from_to(data.get('b', None)), g=None if data.get('g', None) is None else parse_sienna_from_to(data.get('g', None)), rating_b=data.get('rating_b', None), rating_c=data.get('rating_c', None), operational_flow_limit=None if data.get('operational_flow_limit', None) is None else parse_sienna_operational_flow_limit(data.get('operational_flow_limit', None)), angle_limits=parse_sienna_min_max(get_required_value(data, 'angle_limits', 'Line')))

def sienna_line_to_json(value: SiennaLine) -> dict[str, Any]:
    """Write every Line slot to explicit schema property names.

    :param value: Typed Line object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.from_to import sienna_from_to_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import sienna_impedance_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import sienna_operational_flow_limit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.identifier, 'name': value.name, 'available': value.available, 'active_power_flow': value.active_power_flow, 'reactive_power_flow': value.reactive_power_flow, 'arc': value.arc, 'r': value.r, 'x': value.x, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'parameter_units': None if value.parameter_units is None else sienna_impedance_unit_basis_to_json(value.parameter_units), 'b': None if value.b is None else sienna_from_to_to_json(value.b), 'rating': value.rating, 'rating_b': value.rating_b, 'rating_c': value.rating_c, 'operational_flow_limit': None if value.operational_flow_limit is None else sienna_operational_flow_limit_to_json(value.operational_flow_limit), 'angle_limits': sienna_min_max_to_json(value.angle_limits), 'g': None if value.g is None else sienna_from_to_to_json(value.g)}
