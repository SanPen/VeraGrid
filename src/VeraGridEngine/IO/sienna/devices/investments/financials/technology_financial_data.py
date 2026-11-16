# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TechnologyFinancialData schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTechnologyFinancialData(SiennaSchemaModel):
    """Expose every declared TechnologyFinancialData property through fixed slots."""

    __slots__ = ('capital_recovery_period', 'technology_base_year', 'debt_fraction', 'debt_rate', 'return_on_equity', 'tax_rate',)

    def __init__(self, capital_recovery_period: int, technology_base_year: int, debt_fraction: float, debt_rate: float, return_on_equity: float, tax_rate: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.capital_recovery_period: int = capital_recovery_period
        self.technology_base_year: int = technology_base_year
        self.debt_fraction: float = debt_fraction
        self.debt_rate: float = debt_rate
        self.return_on_equity: float = return_on_equity
        self.tax_rate: float = tax_rate


def parse_sienna_technology_financial_data(data: dict[str, Any]) -> SiennaTechnologyFinancialData:
    """Parse declared TechnologyFinancialData properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TechnologyFinancialData object.
    """
    return SiennaTechnologyFinancialData(capital_recovery_period=get_required_value(data, 'capital_recovery_period', 'TechnologyFinancialData'), technology_base_year=get_required_value(data, 'technology_base_year', 'TechnologyFinancialData'), debt_fraction=get_required_value(data, 'debt_fraction', 'TechnologyFinancialData'), debt_rate=get_required_value(data, 'debt_rate', 'TechnologyFinancialData'), return_on_equity=get_required_value(data, 'return_on_equity', 'TechnologyFinancialData'), tax_rate=get_required_value(data, 'tax_rate', 'TechnologyFinancialData'))


def sienna_technology_financial_data_to_json(value: SiennaTechnologyFinancialData) -> dict[str, Any]:
    """Write every TechnologyFinancialData slot to explicit schema property names.

    :param value: Typed TechnologyFinancialData object.
    :return: JSON object with declared schema properties.
    """
    return {'capital_recovery_period': value.capital_recovery_period, 'technology_base_year': value.technology_base_year, 'debt_fraction': value.debt_fraction, 'debt_rate': value.debt_rate, 'return_on_equity': value.return_on_equity, 'tax_rate': value.tax_rate}
