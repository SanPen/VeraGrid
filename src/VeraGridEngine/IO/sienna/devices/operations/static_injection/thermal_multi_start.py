# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ThermalMultiStart schema object."""

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
    from VeraGridEngine.IO.sienna.devices.core.common.start_up_shut_down import SiennaStartUpShutDown
    from VeraGridEngine.IO.sienna.devices.core.common.start_up_stages import SiennaStartUpStages
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_fuels import SiennaThermalFuels
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_generation_cost import SiennaThermalGenerationCost
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import SiennaUpDown
    from VeraGridEngine.IO.sienna.devices.operations.common.commitment_modes import SiennaCommitmentModes
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import SiennaOperationalStates

from VeraGridEngine.IO.sienna.devices.common import get_required_value
from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind, parse_sienna_schema_object,
                                                            parse_sienna_schema_union)

class SiennaThermalMultiStart(SiennaSchemaModel):
    """Expose every declared ThermalMultiStart property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'status', 'commitment_mode', 'bus', 'active_power', 'reactive_power', 'rating', 'prime_mover_type', 'fuel', 'active_power_limits', 'reactive_power_limits', 'ramp_limits', 'power_trajectory', 'time_limits', 'start_time_limits', 'start_types', 'operation_cost', 'base_power', 'power_units', 'time_at_status', 'dynamic_injector', 'switching_times',)

    def __init__(self, id: int, name: str, available: bool, status: SiennaOperationalStates, commitment_mode: SiennaCommitmentModes, bus: int, active_power: float, reactive_power: float, rating: float, prime_mover_type: SiennaPrimeMovers, fuel: SiennaThermalFuels, active_power_limits: SiennaMinMax, reactive_power_limits: SiennaMinMax, ramp_limits: SiennaUpDown, power_trajectory: SiennaStartUpShutDown, time_limits: SiennaUpDown, start_time_limits: SiennaStartUpStages, start_types: int, operation_cost: SiennaThermalGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, base_power: float, power_units: SiennaUnitSystem, time_at_status: float, dynamic_injector: int | None, switching_times: SiennaUpDown) -> None:
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
        self.prime_mover_type: SiennaPrimeMovers = prime_mover_type
        self.fuel: SiennaThermalFuels = fuel
        self.active_power_limits: SiennaMinMax = active_power_limits
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.ramp_limits: SiennaUpDown = ramp_limits
        self.power_trajectory: SiennaStartUpShutDown = power_trajectory
        self.time_limits: SiennaUpDown = time_limits
        self.start_time_limits: SiennaStartUpStages = start_time_limits
        self.start_types: int = start_types
        self.operation_cost: SiennaThermalGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.time_at_status: float = time_at_status
        self.dynamic_injector: int | None = dynamic_injector
        self.switching_times: SiennaUpDown = switching_times


def parse_sienna_thermal_multi_start(data: dict[str, Any]) -> SiennaThermalMultiStart:
    """Parse declared ThermalMultiStart properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ThermalMultiStart object.
    """
    return SiennaThermalMultiStart(id=get_required_value(data, 'id', 'ThermalMultiStart'), name=get_required_value(data, 'name', 'ThermalMultiStart'), available=get_required_value(data, 'available', 'ThermalMultiStart'), status=parse_sienna_schema_object(SiennaObjectKind.OperationalStates, get_required_value(data, 'status', 'ThermalMultiStart')), commitment_mode=parse_sienna_schema_object(SiennaObjectKind.CommitmentModes, data.get('commitment_mode', 'UNDEFINED')), bus=get_required_value(data, 'bus', 'ThermalMultiStart'), active_power=get_required_value(data, 'active_power', 'ThermalMultiStart'), reactive_power=get_required_value(data, 'reactive_power', 'ThermalMultiStart'), rating=get_required_value(data, 'rating', 'ThermalMultiStart'), prime_mover_type=parse_sienna_schema_object(SiennaObjectKind.PrimeMovers, get_required_value(data, 'prime_mover_type', 'ThermalMultiStart')), fuel=parse_sienna_schema_object(SiennaObjectKind.ThermalFuels, get_required_value(data, 'fuel', 'ThermalMultiStart')), active_power_limits=parse_sienna_schema_object(SiennaObjectKind.MinMax, get_required_value(data, 'active_power_limits', 'ThermalMultiStart')), reactive_power_limits=parse_sienna_schema_object(SiennaObjectKind.MinMax, data.get('reactive_power_limits', dict())), ramp_limits=parse_sienna_schema_object(SiennaObjectKind.UpDown, data.get('ramp_limits', dict())), power_trajectory=parse_sienna_schema_object(SiennaObjectKind.StartUpShutDown, data.get('power_trajectory', dict())), time_limits=parse_sienna_schema_object(SiennaObjectKind.UpDown, data.get('time_limits', dict())), start_time_limits=parse_sienna_schema_object(SiennaObjectKind.StartUpStages, data.get('start_time_limits', dict())), start_types=get_required_value(data, 'start_types', 'ThermalMultiStart'), operation_cost=parse_sienna_schema_union((SiennaObjectKind.ThermalGenerationCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'ThermalMultiStart')), base_power=get_required_value(data, 'base_power', 'ThermalMultiStart'), power_units=parse_sienna_schema_object(SiennaObjectKind.UnitSystem, get_required_value(data, 'power_units', 'ThermalMultiStart')), time_at_status=data.get('time_at_status', None), dynamic_injector=data.get('dynamic_injector', None), switching_times=parse_sienna_schema_object(SiennaObjectKind.UpDown, data.get('switching_times', dict())))


def sienna_thermal_multi_start_to_json(value: SiennaThermalMultiStart) -> dict[str, Any]:
    """Write every ThermalMultiStart slot to explicit schema property names.

    :param value: Typed ThermalMultiStart object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.writer_registry import (write_sienna_schema_object,
                                                                   write_sienna_schema_union)
    return {'id': value.id, 'name': value.name, 'available': value.available,
            'status': write_sienna_schema_object(SiennaObjectKind.OperationalStates, value.status),
            'commitment_mode': write_sienna_schema_object(SiennaObjectKind.CommitmentModes,
                                                           value.commitment_mode), 'bus': value.bus,
            'active_power': value.active_power, 'reactive_power': value.reactive_power, 'rating': value.rating,
            'prime_mover_type': write_sienna_schema_object(SiennaObjectKind.PrimeMovers, value.prime_mover_type),
            'fuel': write_sienna_schema_object(SiennaObjectKind.ThermalFuels, value.fuel),
            'active_power_limits': write_sienna_schema_object(SiennaObjectKind.MinMax, value.active_power_limits),
            'reactive_power_limits': write_sienna_schema_object(SiennaObjectKind.MinMax,
                                                                 value.reactive_power_limits),
            'ramp_limits': write_sienna_schema_object(SiennaObjectKind.UpDown, value.ramp_limits),
            'power_trajectory': write_sienna_schema_object(SiennaObjectKind.StartUpShutDown,
                                                            value.power_trajectory),
            'time_limits': write_sienna_schema_object(SiennaObjectKind.UpDown, value.time_limits),
            'start_time_limits': write_sienna_schema_object(SiennaObjectKind.StartUpStages,
                                                             value.start_time_limits), 'start_types': value.start_types,
            'operation_cost': write_sienna_schema_union((SiennaObjectKind.ThermalGenerationCost,
                                                         SiennaObjectKind.MarketBidCost,
                                                         SiennaObjectKind.MarketBidTimeSeriesCost,
                                                         SiennaObjectKind.ImportExportTimeSeriesCost),
                                                        value.operation_cost), 'base_power': value.base_power,
            'power_units': write_sienna_schema_object(SiennaObjectKind.UnitSystem, value.power_units),
            'time_at_status': value.time_at_status, 'dynamic_injector': value.dynamic_injector,
            'switching_times': write_sienna_schema_object(SiennaObjectKind.UpDown, value.switching_times)}
