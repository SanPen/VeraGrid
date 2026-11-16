# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ThermalStandard schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.import_export_time_series_cost import SiennaImportExportTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import SiennaMarketBidCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import SiennaMarketBidTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import SiennaPrimeMovers
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_fuels import SiennaThermalFuels
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_generation_cost import SiennaThermalGenerationCost
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import SiennaUpDown
    from VeraGridEngine.IO.sienna.devices.operations.common.commitment_modes import SiennaCommitmentModes
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import SiennaOperationalStates

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaThermalStandard(SiennaSchemaModel):
    """Expose every declared ThermalStandard property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'status', 'commitment_mode', 'bus', 'active_power', 'reactive_power', 'rating', 'active_power_limits', 'reactive_power_limits', 'ramp_limits', 'operation_cost', 'base_power', 'power_units', 'time_limits', 'prime_mover_type', 'fuel', 'time_at_status', 'dynamic_injector', 'switching_times',)

    def __init__(self, id: int, name: str, available: bool, status: SiennaOperationalStates, commitment_mode: SiennaCommitmentModes, bus: int, active_power: float, reactive_power: float, rating: float, active_power_limits: SiennaMinMax, reactive_power_limits: SiennaMinMax, ramp_limits: SiennaUpDown, operation_cost: SiennaThermalGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, base_power: float, power_units: SiennaUnitSystem, time_limits: SiennaUpDown, prime_mover_type: SiennaPrimeMovers, fuel: SiennaThermalFuels, time_at_status: float, dynamic_injector: int | None, switching_times: SiennaUpDown) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.status: SiennaOperationalStates = status
        self.commitment_mode: SiennaCommitmentModes = commitment_mode
        self.bus: int = bus
        self.active_power: float = active_power
        self.reactive_power: float = reactive_power
        self.rating: float = rating
        self.active_power_limits: SiennaMinMax = active_power_limits
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.ramp_limits: SiennaUpDown = ramp_limits
        self.operation_cost: SiennaThermalGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.time_limits: SiennaUpDown = time_limits
        self.prime_mover_type: SiennaPrimeMovers = prime_mover_type
        self.fuel: SiennaThermalFuels = fuel
        self.time_at_status: float = time_at_status
        self.dynamic_injector: int | None = dynamic_injector
        self.switching_times: SiennaUpDown = switching_times


def parse_sienna_thermal_standard(data: dict[str, Any]) -> SiennaThermalStandard:
    """Parse declared ThermalStandard properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ThermalStandard object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import parse_sienna_prime_movers
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_fuels import parse_sienna_thermal_fuels
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import parse_sienna_up_down
    from VeraGridEngine.IO.sienna.devices.operations.common.commitment_modes import parse_sienna_commitment_modes
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import parse_sienna_operational_states
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaThermalStandard(id=get_required_value(data, 'id', 'ThermalStandard'), name=get_required_value(data, 'name', 'ThermalStandard'), available=get_required_value(data, 'available', 'ThermalStandard'), status=parse_sienna_operational_states(get_required_value(data, 'status', 'ThermalStandard')), commitment_mode=None if data.get('commitment_mode', None) is None else parse_sienna_commitment_modes(data.get('commitment_mode', None)), bus=get_required_value(data, 'bus', 'ThermalStandard'), active_power=get_required_value(data, 'active_power', 'ThermalStandard'), reactive_power=get_required_value(data, 'reactive_power', 'ThermalStandard'), rating=get_required_value(data, 'rating', 'ThermalStandard'), active_power_limits=parse_sienna_min_max(get_required_value(data, 'active_power_limits', 'ThermalStandard')), reactive_power_limits=None if data.get('reactive_power_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_limits', None)), ramp_limits=None if data.get('ramp_limits', None) is None else parse_sienna_up_down(data.get('ramp_limits', None)), operation_cost=parse_sienna_schema_union((SiennaObjectKind.ThermalGenerationCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'ThermalStandard')), base_power=get_required_value(data, 'base_power', 'ThermalStandard'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'ThermalStandard')), time_limits=None if data.get('time_limits', None) is None else parse_sienna_up_down(data.get('time_limits', None)), prime_mover_type=None if data.get('prime_mover_type', None) is None else parse_sienna_prime_movers(data.get('prime_mover_type', None)), fuel=None if data.get('fuel', None) is None else parse_sienna_thermal_fuels(data.get('fuel', None)), time_at_status=data.get('time_at_status', None), dynamic_injector=data.get('dynamic_injector', None), switching_times=None if data.get('switching_times', None) is None else parse_sienna_up_down(data.get('switching_times', None)))

def sienna_thermal_standard_to_json(value: SiennaThermalStandard) -> dict[str, Any]:
    """Write every ThermalStandard slot to explicit schema property names.

    :param value: Typed ThermalStandard object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import sienna_prime_movers_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_fuels import sienna_thermal_fuels_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import sienna_up_down_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.commitment_modes import sienna_commitment_modes_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import sienna_operational_states_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'status': sienna_operational_states_to_json(value.status), 'commitment_mode': None if value.commitment_mode is None else sienna_commitment_modes_to_json(value.commitment_mode), 'bus': value.bus, 'active_power': value.active_power, 'reactive_power': value.reactive_power, 'rating': value.rating, 'active_power_limits': sienna_min_max_to_json(value.active_power_limits), 'reactive_power_limits': None if value.reactive_power_limits is None else sienna_min_max_to_json(value.reactive_power_limits), 'ramp_limits': None if value.ramp_limits is None else sienna_up_down_to_json(value.ramp_limits), 'operation_cost': write_sienna_schema_union((SiennaObjectKind.ThermalGenerationCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), value.operation_cost), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'time_limits': None if value.time_limits is None else sienna_up_down_to_json(value.time_limits), 'prime_mover_type': None if value.prime_mover_type is None else sienna_prime_movers_to_json(value.prime_mover_type), 'fuel': None if value.fuel is None else sienna_thermal_fuels_to_json(value.fuel), 'time_at_status': value.time_at_status, 'dynamic_injector': value.dynamic_injector, 'switching_times': None if value.switching_times is None else sienna_up_down_to_json(value.switching_times)}
