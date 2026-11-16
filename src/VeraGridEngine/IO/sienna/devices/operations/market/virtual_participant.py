# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna VirtualParticipant schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import SiennaMarketBidCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import SiennaMarketBidTimeSeriesCost

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaVirtualParticipant(SiennaSchemaModel):
    """Expose every declared VirtualParticipant property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'settlement_point_id', 'max_supply', 'max_demand', 'operation_cost',)

    def __init__(self, id: int, name: str, available: bool, settlement_point_id: int | None, max_supply: float, max_demand: float, operation_cost: SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.settlement_point_id: int | None = settlement_point_id
        self.max_supply: float = max_supply
        self.max_demand: float = max_demand
        self.operation_cost: SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost = operation_cost


def parse_sienna_virtual_participant(data: dict[str, Any]) -> SiennaVirtualParticipant:
    """Parse declared VirtualParticipant properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed VirtualParticipant object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaVirtualParticipant(id=get_required_value(data, 'id', 'VirtualParticipant'), name=get_required_value(data, 'name', 'VirtualParticipant'), available=get_required_value(data, 'available', 'VirtualParticipant'), settlement_point_id=data.get('settlement_point_id', None), max_supply=get_required_value(data, 'max_supply', 'VirtualParticipant'), max_demand=get_required_value(data, 'max_demand', 'VirtualParticipant'), operation_cost=parse_sienna_schema_union((SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost), get_required_value(data, 'operation_cost', 'VirtualParticipant')))

def sienna_virtual_participant_to_json(value: SiennaVirtualParticipant) -> dict[str, Any]:
    """Write every VirtualParticipant slot to explicit schema property names.

    :param value: Typed VirtualParticipant object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'settlement_point_id': value.settlement_point_id, 'max_supply': value.max_supply, 'max_demand': value.max_demand, 'operation_cost': write_sienna_schema_union((SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost), value.operation_cost)}
