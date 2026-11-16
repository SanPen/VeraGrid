# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RenewableGenerationCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import SiennaCostCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRenewableGenerationCost(SiennaSchemaModel):
    """Expose every declared RenewableGenerationCost property through fixed slots."""

    __slots__ = ('cost_type', 'curtailment_cost', 'variable_operation_cost', 'fixed',)

    def __init__(self, cost_type: str, curtailment_cost: SiennaCostCurve, variable_operation_cost: SiennaCostCurve, fixed: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.cost_type: str = cost_type
        self.curtailment_cost: SiennaCostCurve = curtailment_cost
        self.variable_operation_cost: SiennaCostCurve = variable_operation_cost
        self.fixed: float = fixed


def parse_sienna_renewable_generation_cost(data: dict[str, Any]) -> SiennaRenewableGenerationCost:
    """Parse declared RenewableGenerationCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RenewableGenerationCost object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import parse_sienna_cost_curve
    return SiennaRenewableGenerationCost(cost_type=data.get('cost_type', None), curtailment_cost=None if data.get('curtailment_cost', None) is None else parse_sienna_cost_curve(data.get('curtailment_cost', None)), variable_operation_cost=parse_sienna_cost_curve(get_required_value(data, 'variable_operation_cost', 'RenewableGenerationCost')), fixed=data.get('fixed', None))

def sienna_renewable_generation_cost_to_json(value: SiennaRenewableGenerationCost) -> dict[str, Any]:
    """Write every RenewableGenerationCost slot to explicit schema property names.

    :param value: Typed RenewableGenerationCost object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import sienna_cost_curve_to_json
    return {'cost_type': value.cost_type, 'curtailment_cost': None if value.curtailment_cost is None else sienna_cost_curve_to_json(value.curtailment_cost), 'variable_operation_cost': sienna_cost_curve_to_json(value.variable_operation_cost), 'fixed': value.fixed}
