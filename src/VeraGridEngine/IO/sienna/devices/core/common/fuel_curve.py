# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna FuelCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.fuel_unit import SiennaFuelUnit
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import SiennaInputOutputCurve
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import SiennaValueCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaFuelCurve(SiennaSchemaModel):
    """Expose every declared FuelCurve property through fixed slots."""

    __slots__ = ('fuel_cost', 'fuel_cost_time_series', 'fuel_units', 'power_units', 'startup_fuel_offtake', 'value_curve', 'variable_cost_type', 'vom_cost',)

    def __init__(self, fuel_cost: float | None, fuel_cost_time_series: int | None, fuel_units: SiennaFuelUnit, power_units: SiennaUnitSystem, startup_fuel_offtake: SiennaInputOutputCurve, value_curve: SiennaValueCurve, variable_cost_type: str, vom_cost: SiennaInputOutputCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.fuel_cost: float | None = fuel_cost
        self.fuel_cost_time_series: int | None = fuel_cost_time_series
        self.fuel_units: SiennaFuelUnit = fuel_units
        self.power_units: SiennaUnitSystem = power_units
        self.startup_fuel_offtake: SiennaInputOutputCurve = startup_fuel_offtake
        self.value_curve: SiennaValueCurve = value_curve
        self.variable_cost_type: str = variable_cost_type
        self.vom_cost: SiennaInputOutputCurve = vom_cost


def parse_sienna_fuel_curve(data: dict[str, Any]) -> SiennaFuelCurve:
    """Parse declared FuelCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed FuelCurve object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.fuel_unit import parse_sienna_fuel_unit
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import parse_sienna_input_output_curve
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import parse_sienna_value_curve
    return SiennaFuelCurve(fuel_cost=data.get('fuel_cost', None), fuel_cost_time_series=data.get('fuel_cost_time_series', None), fuel_units=parse_sienna_fuel_unit(get_required_value(data, 'fuel_units', 'FuelCurve')), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'FuelCurve')), startup_fuel_offtake=None if data.get('startup_fuel_offtake', None) is None else parse_sienna_input_output_curve(data.get('startup_fuel_offtake', None)), value_curve=parse_sienna_value_curve(get_required_value(data, 'value_curve', 'FuelCurve')), variable_cost_type=get_required_value(data, 'variable_cost_type', 'FuelCurve'), vom_cost=parse_sienna_input_output_curve(get_required_value(data, 'vom_cost', 'FuelCurve')))

def sienna_fuel_curve_to_json(value: SiennaFuelCurve) -> dict[str, Any]:
    """Write every FuelCurve slot to explicit schema property names.

    :param value: Typed FuelCurve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.fuel_unit import sienna_fuel_unit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import sienna_input_output_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.value_curve import sienna_value_curve_to_json
    return {'fuel_cost': value.fuel_cost, 'fuel_cost_time_series': value.fuel_cost_time_series, 'fuel_units': sienna_fuel_unit_to_json(value.fuel_units), 'power_units': sienna_unit_system_to_json(value.power_units), 'startup_fuel_offtake': None if value.startup_fuel_offtake is None else sienna_input_output_curve_to_json(value.startup_fuel_offtake), 'value_curve': sienna_value_curve_to_json(value.value_curve), 'variable_cost_type': value.variable_cost_type, 'vom_cost': sienna_input_output_curve_to_json(value.vom_cost)}
