# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ThermalGenerationCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import SiennaProductionVariableCostCurve
    from VeraGridEngine.IO.sienna.devices.core.common.start_up_stages import SiennaStartUpStages

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaThermalGenerationCost(SiennaSchemaModel):
    """Expose every declared ThermalGenerationCost property through fixed slots."""

    __slots__ = ('cost_type', 'fixed', 'shut_down', 'start_up', 'variable_operation_cost',)

    def __init__(self, cost_type: str, fixed: float, shut_down: float, start_up: float | SiennaStartUpStages, variable_operation_cost: SiennaProductionVariableCostCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.cost_type: str = cost_type
        self.fixed: float = fixed
        self.shut_down: float = shut_down
        self.start_up: float | SiennaStartUpStages = start_up
        self.variable_operation_cost: SiennaProductionVariableCostCurve = variable_operation_cost


def parse_sienna_thermal_generation_cost(data: dict[str, Any]) -> SiennaThermalGenerationCost:
    """Parse declared ThermalGenerationCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ThermalGenerationCost object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import parse_sienna_production_variable_cost_curve
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaThermalGenerationCost(cost_type=data.get('cost_type', None), fixed=get_required_value(data, 'fixed', 'ThermalGenerationCost'), shut_down=get_required_value(data, 'shut_down', 'ThermalGenerationCost'), start_up=parse_sienna_schema_union((SiennaObjectKind.StartUpStages,), get_required_value(data, 'start_up', 'ThermalGenerationCost')), variable_operation_cost=parse_sienna_production_variable_cost_curve(get_required_value(data, 'variable_operation_cost', 'ThermalGenerationCost')))

def sienna_thermal_generation_cost_to_json(value: SiennaThermalGenerationCost) -> dict[str, Any]:
    """Write every ThermalGenerationCost slot to explicit schema property names.

    :param value: Typed ThermalGenerationCost object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.production_variable_cost_curve import sienna_production_variable_cost_curve_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'cost_type': value.cost_type, 'fixed': value.fixed, 'shut_down': value.shut_down, 'start_up': write_sienna_schema_union((SiennaObjectKind.StartUpStages,), value.start_up), 'variable_operation_cost': sienna_production_variable_cost_curve_to_json(value.variable_operation_cost)}
