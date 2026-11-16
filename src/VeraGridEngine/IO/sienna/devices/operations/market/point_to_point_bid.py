# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PointToPointBid schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_cost import SiennaMarketBidCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import SiennaMarketBidTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPointToPointBid(SiennaSchemaModel):
    """Expose every declared PointToPointBid property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'from_id', 'to_id', 'max_active_power', 'spread_bid', 'price_limits', 'linked_crr',)

    def __init__(self, id: int, name: str, available: bool, from_id: int, to_id: int, max_active_power: float, spread_bid: SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost, price_limits: SiennaMinMax, linked_crr: str | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.from_id: int = from_id
        self.to_id: int = to_id
        self.max_active_power: float = max_active_power
        self.spread_bid: SiennaMarketBidCost | SiennaMarketBidTimeSeriesCost = spread_bid
        self.price_limits: SiennaMinMax = price_limits
        self.linked_crr: str | None = linked_crr


def parse_sienna_point_to_point_bid(data: dict[str, Any]) -> SiennaPointToPointBid:
    """Parse declared PointToPointBid properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PointToPointBid object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaPointToPointBid(id=get_required_value(data, 'id', 'PointToPointBid'), name=get_required_value(data, 'name', 'PointToPointBid'), available=get_required_value(data, 'available', 'PointToPointBid'), from_id=get_required_value(data, 'from_id', 'PointToPointBid'), to_id=get_required_value(data, 'to_id', 'PointToPointBid'), max_active_power=get_required_value(data, 'max_active_power', 'PointToPointBid'), spread_bid=parse_sienna_schema_union((SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost), get_required_value(data, 'spread_bid', 'PointToPointBid')), price_limits=parse_sienna_min_max(get_required_value(data, 'price_limits', 'PointToPointBid')), linked_crr=data.get('linked_crr', None))

def sienna_point_to_point_bid_to_json(value: SiennaPointToPointBid) -> dict[str, Any]:
    """Write every PointToPointBid slot to explicit schema property names.

    :param value: Typed PointToPointBid object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'from_id': value.from_id, 'to_id': value.to_id, 'max_active_power': value.max_active_power, 'spread_bid': write_sienna_schema_union((SiennaObjectKind.MarketBidCost, SiennaObjectKind.MarketBidTimeSeriesCost), value.spread_bid), 'price_limits': sienna_min_max_to_json(value.price_limits), 'linked_crr': value.linked_crr}
