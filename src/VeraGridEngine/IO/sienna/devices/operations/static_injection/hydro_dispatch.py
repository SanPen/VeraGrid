# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HydroDispatch schema object."""

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
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import SiennaOperationalStates

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHydroDispatch(SiennaSchemaModel):
    """Expose every declared HydroDispatch property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'active_power', 'reactive_power', 'rating', 'prime_mover_type', 'active_power_limits', 'reactive_power_limits', 'ramp_limits', 'time_limits', 'base_power', 'power_units', 'status', 'time_at_status', 'operation_cost', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, active_power: float, reactive_power: float, rating: float, prime_mover_type: SiennaPrimeMovers, active_power_limits: SiennaMinMax, reactive_power_limits: SiennaMinMax, ramp_limits: SiennaUpDown, time_limits: SiennaUpDown, base_power: float, power_units: SiennaUnitSystem, status: SiennaOperationalStates, time_at_status: float, operation_cost: SiennaHydroGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, dynamic_injector: int | None) -> None:
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
        self.prime_mover_type: SiennaPrimeMovers = prime_mover_type
        self.active_power_limits: SiennaMinMax = active_power_limits
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.ramp_limits: SiennaUpDown = ramp_limits
        self.time_limits: SiennaUpDown = time_limits
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.status: SiennaOperationalStates = status
        self.time_at_status: float = time_at_status
        self.operation_cost: SiennaHydroGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_hydro_dispatch(data: dict[str, Any]) -> SiennaHydroDispatch:
    """Parse declared HydroDispatch properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HydroDispatch object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import parse_sienna_prime_movers
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import parse_sienna_up_down
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import parse_sienna_operational_states
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaHydroDispatch(id=get_required_value(data, 'id', 'HydroDispatch'), name=get_required_value(data, 'name', 'HydroDispatch'), available=get_required_value(data, 'available', 'HydroDispatch'), bus=get_required_value(data, 'bus', 'HydroDispatch'), active_power=get_required_value(data, 'active_power', 'HydroDispatch'), reactive_power=get_required_value(data, 'reactive_power', 'HydroDispatch'), rating=get_required_value(data, 'rating', 'HydroDispatch'), prime_mover_type=parse_sienna_prime_movers(get_required_value(data, 'prime_mover_type', 'HydroDispatch')), active_power_limits=parse_sienna_min_max(get_required_value(data, 'active_power_limits', 'HydroDispatch')), reactive_power_limits=None if data.get('reactive_power_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_limits', None)), ramp_limits=None if data.get('ramp_limits', None) is None else parse_sienna_up_down(data.get('ramp_limits', None)), time_limits=None if data.get('time_limits', None) is None else parse_sienna_up_down(data.get('time_limits', None)), base_power=get_required_value(data, 'base_power', 'HydroDispatch'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'HydroDispatch')), status=None if data.get('status', None) is None else parse_sienna_operational_states(data.get('status', None)), time_at_status=data.get('time_at_status', None), operation_cost=parse_sienna_schema_union((SiennaObjectKind.HydroGenerationCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'HydroDispatch')), dynamic_injector=data.get('dynamic_injector', None))

def sienna_hydro_dispatch_to_json(value: SiennaHydroDispatch) -> dict[str, Any]:
    """Write every HydroDispatch slot to explicit schema property names.

    :param value: Typed HydroDispatch object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import sienna_prime_movers_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import sienna_up_down_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.operational_states import sienna_operational_states_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'active_power': value.active_power, 'reactive_power': value.reactive_power, 'rating': value.rating, 'prime_mover_type': sienna_prime_movers_to_json(value.prime_mover_type), 'active_power_limits': sienna_min_max_to_json(value.active_power_limits), 'reactive_power_limits': None if value.reactive_power_limits is None else sienna_min_max_to_json(value.reactive_power_limits), 'ramp_limits': None if value.ramp_limits is None else sienna_up_down_to_json(value.ramp_limits), 'time_limits': None if value.time_limits is None else sienna_up_down_to_json(value.time_limits), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'status': None if value.status is None else sienna_operational_states_to_json(value.status), 'time_at_status': value.time_at_status, 'operation_cost': write_sienna_schema_union((SiennaObjectKind.HydroGenerationCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), value.operation_cost), 'dynamic_injector': value.dynamic_injector}
