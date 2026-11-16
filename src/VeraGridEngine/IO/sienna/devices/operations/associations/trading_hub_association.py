# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TradingHubAssociation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTradingHubAssociation(SiennaSchemaModel):
    """Expose every declared TradingHubAssociation property through fixed slots."""

    __slots__ = ('trading_hub_id', 'entity_id',)

    def __init__(self, trading_hub_id: int, entity_id: int) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.trading_hub_id: int = trading_hub_id
        self.entity_id: int = entity_id


def parse_sienna_trading_hub_association(data: dict[str, Any]) -> SiennaTradingHubAssociation:
    """Parse declared TradingHubAssociation properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TradingHubAssociation object.
    """
    return SiennaTradingHubAssociation(trading_hub_id=get_required_value(data, 'trading_hub_id', 'TradingHubAssociation'), entity_id=get_required_value(data, 'entity_id', 'TradingHubAssociation'))


def sienna_trading_hub_association_to_json(value: SiennaTradingHubAssociation) -> dict[str, Any]:
    """Write every TradingHubAssociation slot to explicit schema property names.

    :param value: Typed TradingHubAssociation object.
    :return: JSON object with declared schema properties.
    """
    return {'trading_hub_id': value.trading_hub_id, 'entity_id': value.entity_id}
