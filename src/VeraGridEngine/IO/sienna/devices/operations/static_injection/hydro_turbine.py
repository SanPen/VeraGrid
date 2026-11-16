# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HydroTurbine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.hydro_generation_cost import SiennaHydroGenerationCost
    from VeraGridEngine.IO.sienna.devices.core.common.import_export_time_series_cost import SiennaImportExportTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import SiennaMarketBidCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import SiennaMarketBidTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import SiennaPrimeMovers
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import SiennaUpDown
    from VeraGridEngine.IO.sienna.devices.operations.common.commitment_modes import SiennaCommitmentModes
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import SiennaOperationalStates

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHydroTurbine(SiennaSchemaModel):
    """Expose every declared HydroTurbine property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'active_power', 'reactive_power', 'rating', 'active_power_limits', 'reactive_power_limits', 'base_power', 'power_units', 'status', 'time_at_status', 'commitment_mode', 'operation_cost', 'powerhouse_elevation', 'ramp_limits', 'time_limits', 'outflow_limits', 'efficiency', 'turbine_type', 'conversion_factor', 'prime_mover_type', 'travel_time', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, active_power: float, reactive_power: float, rating: float, active_power_limits: SiennaMinMax, reactive_power_limits: SiennaMinMax, base_power: float, power_units: SiennaUnitSystem, status: SiennaOperationalStates, time_at_status: float, commitment_mode: SiennaCommitmentModes, operation_cost: SiennaHydroGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, powerhouse_elevation: float, ramp_limits: SiennaUpDown, time_limits: SiennaUpDown, outflow_limits: SiennaMinMax, efficiency: float, turbine_type: str, conversion_factor: float, prime_mover_type: SiennaPrimeMovers, travel_time: float | None, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.active_power: float = active_power
        self.reactive_power: float = reactive_power
        self.rating: float = rating
        self.active_power_limits: SiennaMinMax = active_power_limits
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.status: SiennaOperationalStates = status
        self.time_at_status: float = time_at_status
        self.commitment_mode: SiennaCommitmentModes = commitment_mode
        self.operation_cost: SiennaHydroGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.powerhouse_elevation: float = powerhouse_elevation
        self.ramp_limits: SiennaUpDown = ramp_limits
        self.time_limits: SiennaUpDown = time_limits
        self.outflow_limits: SiennaMinMax = outflow_limits
        self.efficiency: float = efficiency
        self.turbine_type: str = turbine_type
        self.conversion_factor: float = conversion_factor
        self.prime_mover_type: SiennaPrimeMovers = prime_mover_type
        self.travel_time: float | None = travel_time
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_hydro_turbine(data: dict[str, Any]) -> SiennaHydroTurbine:
    """Parse declared HydroTurbine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HydroTurbine object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import parse_sienna_prime_movers
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import parse_sienna_up_down
    from VeraGridEngine.IO.sienna.devices.operations.common.commitment_modes import parse_sienna_commitment_modes
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import parse_sienna_operational_states
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaHydroTurbine(id=get_required_value(data, 'id', 'HydroTurbine'), name=get_required_value(data, 'name', 'HydroTurbine'), available=get_required_value(data, 'available', 'HydroTurbine'), bus=get_required_value(data, 'bus', 'HydroTurbine'), active_power=get_required_value(data, 'active_power', 'HydroTurbine'), reactive_power=get_required_value(data, 'reactive_power', 'HydroTurbine'), rating=get_required_value(data, 'rating', 'HydroTurbine'), active_power_limits=parse_sienna_min_max(get_required_value(data, 'active_power_limits', 'HydroTurbine')), reactive_power_limits=None if data.get('reactive_power_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_limits', None)), base_power=get_required_value(data, 'base_power', 'HydroTurbine'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'HydroTurbine')), status=None if data.get('status', None) is None else parse_sienna_operational_states(data.get('status', None)), time_at_status=data.get('time_at_status', None), commitment_mode=None if data.get('commitment_mode', None) is None else parse_sienna_commitment_modes(data.get('commitment_mode', None)), operation_cost=parse_sienna_schema_union((SiennaObjectKind.HydroGenerationCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'HydroTurbine')), powerhouse_elevation=data.get('powerhouse_elevation', None), ramp_limits=None if data.get('ramp_limits', None) is None else parse_sienna_up_down(data.get('ramp_limits', None)), time_limits=None if data.get('time_limits', None) is None else parse_sienna_up_down(data.get('time_limits', None)), outflow_limits=None if data.get('outflow_limits', None) is None else parse_sienna_min_max(data.get('outflow_limits', None)), efficiency=data.get('efficiency', None), turbine_type=data.get('turbine_type', None), conversion_factor=data.get('conversion_factor', None), prime_mover_type=None if data.get('prime_mover_type', None) is None else parse_sienna_prime_movers(data.get('prime_mover_type', None)), travel_time=data.get('travel_time', None), dynamic_injector=data.get('dynamic_injector', None))

def sienna_hydro_turbine_to_json(value: SiennaHydroTurbine) -> dict[str, Any]:
    """Write every HydroTurbine slot to explicit schema property names.

    :param value: Typed HydroTurbine object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import sienna_prime_movers_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import sienna_up_down_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.commitment_modes import sienna_commitment_modes_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import sienna_operational_states_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'active_power': value.active_power, 'reactive_power': value.reactive_power, 'rating': value.rating, 'active_power_limits': sienna_min_max_to_json(value.active_power_limits), 'reactive_power_limits': None if value.reactive_power_limits is None else sienna_min_max_to_json(value.reactive_power_limits), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'status': None if value.status is None else sienna_operational_states_to_json(value.status), 'time_at_status': value.time_at_status, 'commitment_mode': None if value.commitment_mode is None else sienna_commitment_modes_to_json(value.commitment_mode), 'operation_cost': write_sienna_schema_union((SiennaObjectKind.HydroGenerationCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), value.operation_cost), 'powerhouse_elevation': value.powerhouse_elevation, 'ramp_limits': None if value.ramp_limits is None else sienna_up_down_to_json(value.ramp_limits), 'time_limits': None if value.time_limits is None else sienna_up_down_to_json(value.time_limits), 'outflow_limits': None if value.outflow_limits is None else sienna_min_max_to_json(value.outflow_limits), 'efficiency': value.efficiency, 'turbine_type': value.turbine_type, 'conversion_factor': value.conversion_factor, 'prime_mover_type': None if value.prime_mover_type is None else sienna_prime_movers_to_json(value.prime_mover_type), 'travel_time': value.travel_time, 'dynamic_injector': value.dynamic_injector}
