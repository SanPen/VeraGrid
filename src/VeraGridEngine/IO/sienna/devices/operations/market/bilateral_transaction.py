# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna BilateralTransaction schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.operations.common.bilateral_confirmation import SiennaBilateralConfirmation
    from VeraGridEngine.IO.sienna.devices.operations.common.bilateral_product import SiennaBilateralProduct
    from VeraGridEngine.IO.sienna.devices.operations.common.market_stage import SiennaMarketStage

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaBilateralTransaction(SiennaSchemaModel):
    """Expose every declared BilateralTransaction property through fixed slots."""

    __slots__ = ('id', 'name', 'seller_id', 'buyer_id', 'from_id', 'to_id', 'product', 'market', 'confirmation', 'max_active_power', 'active_power_association_id',)

    def __init__(self, id: int, name: str, seller_id: str, buyer_id: str, from_id: int, to_id: int | None, product: SiennaBilateralProduct, market: SiennaMarketStage, confirmation: SiennaBilateralConfirmation, max_active_power: float, active_power_association_id: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.seller_id: str = seller_id
        self.buyer_id: str = buyer_id
        self.from_id: int = from_id
        self.to_id: int | None = to_id
        self.product: SiennaBilateralProduct = product
        self.market: SiennaMarketStage = market
        self.confirmation: SiennaBilateralConfirmation = confirmation
        self.max_active_power: float = max_active_power
        self.active_power_association_id: int | None = active_power_association_id


def parse_sienna_bilateral_transaction(data: dict[str, Any]) -> SiennaBilateralTransaction:
    """Parse declared BilateralTransaction properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed BilateralTransaction object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.operations.common.bilateral_confirmation import parse_sienna_bilateral_confirmation
    from VeraGridEngine.IO.sienna.devices.operations.common.bilateral_product import parse_sienna_bilateral_product
    from VeraGridEngine.IO.sienna.devices.operations.common.market_stage import parse_sienna_market_stage
    return SiennaBilateralTransaction(id=get_required_value(data, 'id', 'BilateralTransaction'), name=get_required_value(data, 'name', 'BilateralTransaction'), seller_id=get_required_value(data, 'seller_id', 'BilateralTransaction'), buyer_id=get_required_value(data, 'buyer_id', 'BilateralTransaction'), from_id=get_required_value(data, 'from_id', 'BilateralTransaction'), to_id=data.get('to_id', None), product=parse_sienna_bilateral_product(get_required_value(data, 'product', 'BilateralTransaction')), market=parse_sienna_market_stage(get_required_value(data, 'market', 'BilateralTransaction')), confirmation=parse_sienna_bilateral_confirmation(get_required_value(data, 'confirmation', 'BilateralTransaction')), max_active_power=get_required_value(data, 'max_active_power', 'BilateralTransaction'), active_power_association_id=data.get('active_power_association_id', None))

def sienna_bilateral_transaction_to_json(value: SiennaBilateralTransaction) -> dict[str, Any]:
    """Write every BilateralTransaction slot to explicit schema property names.

    :param value: Typed BilateralTransaction object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.operations.common.bilateral_confirmation import sienna_bilateral_confirmation_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.bilateral_product import sienna_bilateral_product_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.market_stage import sienna_market_stage_to_json
    return {'id': value.id, 'name': value.name, 'seller_id': value.seller_id, 'buyer_id': value.buyer_id, 'from_id': value.from_id, 'to_id': value.to_id, 'product': sienna_bilateral_product_to_json(value.product), 'market': sienna_market_stage_to_json(value.market), 'confirmation': sienna_bilateral_confirmation_to_json(value.confirmation), 'max_active_power': value.max_active_power, 'active_power_association_id': value.active_power_association_id}
