# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HydroGenerationCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import SiennaProductionVariableCostCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHydroGenerationCost(SiennaSchemaModel):
    """Expose every declared HydroGenerationCost property through fixed slots."""

    __slots__ = ('cost_type', 'fixed', 'variable_operation_cost',)

    def __init__(self, cost_type: str, fixed: float, variable_operation_cost: SiennaProductionVariableCostCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.cost_type: str = cost_type
        self.fixed: float = fixed
        self.variable_operation_cost: SiennaProductionVariableCostCurve = variable_operation_cost


def parse_sienna_hydro_generation_cost(data: dict[str, Any]) -> SiennaHydroGenerationCost:
    """Parse declared HydroGenerationCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HydroGenerationCost object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import parse_sienna_production_variable_cost_curve
    return SiennaHydroGenerationCost(cost_type=data.get('cost_type', None), fixed=data.get('fixed', None), variable_operation_cost=parse_sienna_production_variable_cost_curve(get_required_value(data, 'variable_operation_cost', 'HydroGenerationCost')))

def sienna_hydro_generation_cost_to_json(value: SiennaHydroGenerationCost) -> dict[str, Any]:
    """Write every HydroGenerationCost slot to explicit schema property names.

    :param value: Typed HydroGenerationCost object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import sienna_production_variable_cost_curve_to_json
    return {'cost_type': value.cost_type, 'fixed': value.fixed, 'variable_operation_cost': sienna_production_variable_cost_curve_to_json(value.variable_operation_cost)}
