# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HybridSystem schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import SiennaComplexNumber
    from VeraGridEngine.IO.sienna.devices.core.common.in_out import SiennaInOut
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import SiennaMarketBidCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import SiennaOperationalStates

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHybridSystem(SiennaSchemaModel):
    """Expose every declared HybridSystem property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'status', 'bus', 'active_power', 'reactive_power', 'base_power', 'power_units', 'operation_cost', 'thermal_unit', 'electric_load', 'storage', 'renewable_unit', 'interconnection_impedance', 'interconnection_rating', 'input_active_power_limits', 'output_active_power_limits', 'reactive_power_limits', 'interconnection_efficiency', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, status: SiennaOperationalStates, bus: int, active_power: float, reactive_power: float, base_power: float, power_units: SiennaUnitSystem, operation_cost: SiennaMarketBidCost, thermal_unit: int | None, electric_load: int | None, storage: int | None, renewable_unit: int | None, interconnection_impedance: SiennaComplexNumber, interconnection_rating: float | None, input_active_power_limits: SiennaMinMax, output_active_power_limits: SiennaMinMax, reactive_power_limits: SiennaMinMax, interconnection_efficiency: SiennaInOut, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.status: SiennaOperationalStates = status
        self.bus: int = bus
        self.active_power: float = active_power
        self.reactive_power: float = reactive_power
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.operation_cost: SiennaMarketBidCost = operation_cost
        self.thermal_unit: int | None = thermal_unit
        self.electric_load: int | None = electric_load
        self.storage: int | None = storage
        self.renewable_unit: int | None = renewable_unit
        self.interconnection_impedance: SiennaComplexNumber = interconnection_impedance
        self.interconnection_rating: float | None = interconnection_rating
        self.input_active_power_limits: SiennaMinMax = input_active_power_limits
        self.output_active_power_limits: SiennaMinMax = output_active_power_limits
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.interconnection_efficiency: SiennaInOut = interconnection_efficiency
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_hybrid_system(data: dict[str, Any]) -> SiennaHybridSystem:
    """Parse declared HybridSystem properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HybridSystem object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import parse_sienna_complex_number
    from VeraGridEngine.IO.sienna.devices.core.common.in_out import parse_sienna_in_out
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import parse_sienna_market_bid_cost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import parse_sienna_operational_states
    return SiennaHybridSystem(id=get_required_value(data, 'id', 'HybridSystem'), name=get_required_value(data, 'name', 'HybridSystem'), available=get_required_value(data, 'available', 'HybridSystem'), status=parse_sienna_operational_states(get_required_value(data, 'status', 'HybridSystem')), bus=get_required_value(data, 'bus', 'HybridSystem'), active_power=get_required_value(data, 'active_power', 'HybridSystem'), reactive_power=get_required_value(data, 'reactive_power', 'HybridSystem'), base_power=get_required_value(data, 'base_power', 'HybridSystem'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'HybridSystem')), operation_cost=parse_sienna_market_bid_cost(get_required_value(data, 'operation_cost', 'HybridSystem')), thermal_unit=data.get('thermal_unit', None), electric_load=data.get('electric_load', None), storage=data.get('storage', None), renewable_unit=data.get('renewable_unit', None), interconnection_impedance=None if data.get('interconnection_impedance', None) is None else parse_sienna_complex_number(data.get('interconnection_impedance', None)), interconnection_rating=data.get('interconnection_rating', None), input_active_power_limits=None if data.get('input_active_power_limits', None) is None else parse_sienna_min_max(data.get('input_active_power_limits', None)), output_active_power_limits=None if data.get('output_active_power_limits', None) is None else parse_sienna_min_max(data.get('output_active_power_limits', None)), reactive_power_limits=None if data.get('reactive_power_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_limits', None)), interconnection_efficiency=None if data.get('interconnection_efficiency', None) is None else parse_sienna_in_out(data.get('interconnection_efficiency', None)), dynamic_injector=data.get('dynamic_injector', None))

def sienna_hybrid_system_to_json(value: SiennaHybridSystem) -> dict[str, Any]:
    """Write every HybridSystem slot to explicit schema property names.

    :param value: Typed HybridSystem object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.complex_number import sienna_complex_number_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.in_out import sienna_in_out_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import sienna_market_bid_cost_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import sienna_operational_states_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'status': sienna_operational_states_to_json(value.status), 'bus': value.bus, 'active_power': value.active_power, 'reactive_power': value.reactive_power, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'operation_cost': sienna_market_bid_cost_to_json(value.operation_cost), 'thermal_unit': value.thermal_unit, 'electric_load': value.electric_load, 'storage': value.storage, 'renewable_unit': value.renewable_unit, 'interconnection_impedance': None if value.interconnection_impedance is None else sienna_complex_number_to_json(value.interconnection_impedance), 'interconnection_rating': value.interconnection_rating, 'input_active_power_limits': None if value.input_active_power_limits is None else sienna_min_max_to_json(value.input_active_power_limits), 'output_active_power_limits': None if value.output_active_power_limits is None else sienna_min_max_to_json(value.output_active_power_limits), 'reactive_power_limits': None if value.reactive_power_limits is None else sienna_min_max_to_json(value.reactive_power_limits), 'interconnection_efficiency': None if value.interconnection_efficiency is None else sienna_in_out_to_json(value.interconnection_efficiency), 'dynamic_injector': value.dynamic_injector}
