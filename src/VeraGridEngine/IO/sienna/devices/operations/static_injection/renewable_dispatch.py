# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RenewableDispatch schema object."""

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
    from VeraGridEngine.IO.sienna.devices.core.common.renewable_generation_cost import SiennaRenewableGenerationCost
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRenewableDispatch(SiennaSchemaModel):
    """Expose every declared RenewableDispatch property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'active_power', 'reactive_power', 'rating', 'prime_mover_type', 'reactive_power_limits', 'power_factor', 'operation_cost', 'base_power', 'power_units', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, active_power: float, reactive_power: float, rating: float, prime_mover_type: SiennaPrimeMovers, reactive_power_limits: SiennaMinMax, power_factor: float, operation_cost: SiennaRenewableGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, base_power: float, power_units: SiennaUnitSystem, dynamic_injector: int | None) -> None:
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
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.power_factor: float = power_factor
        self.operation_cost: SiennaRenewableGenerationCost | SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_renewable_dispatch(data: dict[str, Any]) -> SiennaRenewableDispatch:
    """Parse declared RenewableDispatch properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RenewableDispatch object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import parse_sienna_prime_movers
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaRenewableDispatch(id=get_required_value(data, 'id', 'RenewableDispatch'), name=get_required_value(data, 'name', 'RenewableDispatch'), available=get_required_value(data, 'available', 'RenewableDispatch'), bus=get_required_value(data, 'bus', 'RenewableDispatch'), active_power=get_required_value(data, 'active_power', 'RenewableDispatch'), reactive_power=get_required_value(data, 'reactive_power', 'RenewableDispatch'), rating=get_required_value(data, 'rating', 'RenewableDispatch'), prime_mover_type=parse_sienna_prime_movers(get_required_value(data, 'prime_mover_type', 'RenewableDispatch')), reactive_power_limits=None if data.get('reactive_power_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_limits', None)), power_factor=get_required_value(data, 'power_factor', 'RenewableDispatch'), operation_cost=parse_sienna_schema_union((SiennaObjectKind.RenewableGenerationCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'RenewableDispatch')), base_power=get_required_value(data, 'base_power', 'RenewableDispatch'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'RenewableDispatch')), dynamic_injector=data.get('dynamic_injector', None))

def sienna_renewable_dispatch_to_json(value: SiennaRenewableDispatch) -> dict[str, Any]:
    """Write every RenewableDispatch slot to explicit schema property names.

    :param value: Typed RenewableDispatch object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.prime_movers import sienna_prime_movers_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'active_power': value.active_power, 'reactive_power': value.reactive_power, 'rating': value.rating, 'prime_mover_type': sienna_prime_movers_to_json(value.prime_mover_type), 'reactive_power_limits': None if value.reactive_power_limits is None else sienna_min_max_to_json(value.reactive_power_limits), 'power_factor': value.power_factor, 'operation_cost': write_sienna_schema_union((SiennaObjectKind.RenewableGenerationCost, SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), value.operation_cost), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'dynamic_injector': value.dynamic_injector}
