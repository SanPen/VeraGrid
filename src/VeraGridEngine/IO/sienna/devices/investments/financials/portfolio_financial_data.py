# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna PortfolioFinancialData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaPortfolioFinancialData(SiennaSchemaModel):
    """Expose every declared PortfolioFinancialData property through fixed slots."""

    __slots__ = ('id', 'discount_rate', 'inflation_rate', 'interest_rate', 'base_year',)

    def __init__(self, id: int, discount_rate: float, inflation_rate: float, interest_rate: float, base_year: int) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.discount_rate: float = discount_rate
        self.inflation_rate: float = inflation_rate
        self.interest_rate: float = interest_rate
        self.base_year: int = base_year


def parse_sienna_portfolio_financial_data(data: dict[str, Any]) -> SiennaPortfolioFinancialData:
    """Parse declared PortfolioFinancialData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed PortfolioFinancialData object.
    """
    return SiennaPortfolioFinancialData(id=get_required_value(data, 'id', 'PortfolioFinancialData'), discount_rate=get_required_value(data, 'discount_rate', 'PortfolioFinancialData'), inflation_rate=get_required_value(data, 'inflation_rate', 'PortfolioFinancialData'), interest_rate=get_required_value(data, 'interest_rate', 'PortfolioFinancialData'), base_year=get_required_value(data, 'base_year', 'PortfolioFinancialData'))


def sienna_portfolio_financial_data_to_json(value: SiennaPortfolioFinancialData) -> dict[str, Any]:
    """Write every PortfolioFinancialData slot to explicit schema property names.

    :param value: Typed PortfolioFinancialData object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'discount_rate': value.discount_rate, 'inflation_rate': value.inflation_rate, 'interest_rate': value.interest_rate, 'base_year': value.base_year}
