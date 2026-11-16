# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CostCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import SiennaInputOutputCurve
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import SiennaValueCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCostCurve(SiennaSchemaModel):
    """Expose every declared CostCurve property through fixed slots."""

    __slots__ = ('power_units', 'value_curve', 'variable_cost_type', 'vom_cost',)

    def __init__(self, power_units: SiennaUnitSystem, value_curve: SiennaValueCurve, variable_cost_type: str, vom_cost: SiennaInputOutputCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.power_units: SiennaUnitSystem = power_units
        self.value_curve: SiennaValueCurve = value_curve
        self.variable_cost_type: str = variable_cost_type
        self.vom_cost: SiennaInputOutputCurve = vom_cost


def parse_sienna_cost_curve(data: dict[str, Any]) -> SiennaCostCurve:
    """Parse declared CostCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed CostCurve object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import parse_sienna_input_output_curve
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
    return SiennaCostCurve(power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'CostCurve')), value_curve=parse_sienna_value_curve(get_required_value(data, 'value_curve', 'CostCurve')), variable_cost_type=get_required_value(data, 'variable_cost_type', 'CostCurve'), vom_cost=parse_sienna_input_output_curve(get_required_value(data, 'vom_cost', 'CostCurve')))

def sienna_cost_curve_to_json(value: SiennaCostCurve) -> dict[str, Any]:
    """Write every CostCurve slot to explicit schema property names.

    :param value: Typed CostCurve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import sienna_input_output_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import sienna_value_curve_to_json
    return {'power_units': sienna_unit_system_to_json(value.power_units), 'value_curve': sienna_value_curve_to_json(value.value_curve), 'variable_cost_type': value.variable_cost_type, 'vom_cost': sienna_input_output_curve_to_json(value.vom_cost)}
