# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ProductionVariableCostCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import SiennaCostCurve
    from VeraGridEngine.IO.sienna.devices.core.common.fuel_curve import SiennaFuelCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaProductionVariableCostCurve(SiennaSchemaModel):
    """Expose every declared ProductionVariableCostCurve property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: SiennaCostCurve | SiennaFuelCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: SiennaCostCurve | SiennaFuelCurve = value


def parse_sienna_production_variable_cost_curve(data: dict[str, Any]) -> SiennaProductionVariableCostCurve:
    """Parse declared ProductionVariableCostCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ProductionVariableCostCurve object.
    """
    return SiennaProductionVariableCostCurve(value=data.get('value', None))


def sienna_production_variable_cost_curve_to_json(value: SiennaProductionVariableCostCurve) -> dict[str, Any]:
    """Write every ProductionVariableCostCurve slot to explicit schema property names.

    :param value: Typed ProductionVariableCostCurve object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
