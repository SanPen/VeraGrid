# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna Source schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import SiennaImpedanceUnitBasis
    from VeraGridEngine.IO.sienna.devices.core.common.import_export_cost import SiennaImportExportCost
    from VeraGridEngine.IO.sienna.devices.core.common.import_export_time_series_cost import SiennaImportExportTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import SiennaMarketBidTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaSource(SiennaSchemaModel):
    """Expose every declared Source property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'bus', 'active_power', 'reactive_power', 'active_power_limits', 'reactive_power_limits', 'parameter_units', 'R_th', 'X_th', 'internal_voltage', 'internal_angle', 'base_voltage', 'base_power', 'power_units', 'operation_cost', 'dynamic_injector',)

    def __init__(self, id: int, name: str, available: bool, bus: int, active_power: float, reactive_power: float, active_power_limits: SiennaMinMax, reactive_power_limits: SiennaMinMax, parameter_units: SiennaImpedanceUnitBasis, R_th: float, X_th: float, internal_voltage: float, internal_angle: float, base_voltage: float, base_power: float, power_units: SiennaUnitSystem, operation_cost: SiennaImportExportCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, dynamic_injector: int | None) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.bus: int = bus
        self.active_power: float = active_power
        self.reactive_power: float = reactive_power
        self.active_power_limits: SiennaMinMax = active_power_limits
        self.reactive_power_limits: SiennaMinMax = reactive_power_limits
        self.parameter_units: SiennaImpedanceUnitBasis = parameter_units
        self.R_th: float = R_th
        self.X_th: float = X_th
        self.internal_voltage: float = internal_voltage
        self.internal_angle: float = internal_angle
        self.base_voltage: float = base_voltage
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units
        self.operation_cost: SiennaImportExportCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.dynamic_injector: int | None = dynamic_injector


def parse_sienna_source(data: dict[str, Any]) -> SiennaSource:
    """Parse declared Source properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed Source object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import parse_sienna_impedance_unit_basis
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaSource(id=get_required_value(data, 'id', 'Source'), name=get_required_value(data, 'name', 'Source'), available=get_required_value(data, 'available', 'Source'), bus=get_required_value(data, 'bus', 'Source'), active_power=data.get('active_power', None), reactive_power=data.get('reactive_power', None), active_power_limits=None if data.get('active_power_limits', None) is None else parse_sienna_min_max(data.get('active_power_limits', None)), reactive_power_limits=None if data.get('reactive_power_limits', None) is None else parse_sienna_min_max(data.get('reactive_power_limits', None)), parameter_units=None if data.get('parameter_units', None) is None else parse_sienna_impedance_unit_basis(data.get('parameter_units', None)), R_th=data.get('R_th', None), X_th=data.get('X_th', None), internal_voltage=data.get('internal_voltage', None), internal_angle=data.get('internal_angle', None), base_voltage=data.get('base_voltage', None), base_power=data.get('base_power', None), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'Source')), operation_cost=parse_sienna_schema_union((SiennaObjectKind.ImportExportCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'Source')), dynamic_injector=data.get('dynamic_injector', None))

def sienna_source_to_json(value: SiennaSource) -> dict[str, Any]:
    """Write every Source slot to explicit schema property names.

    :param value: Typed Source object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.impedance_unit_basis import sienna_impedance_unit_basis_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'bus': value.bus, 'active_power': value.active_power, 'reactive_power': value.reactive_power, 'active_power_limits': None if value.active_power_limits is None else sienna_min_max_to_json(value.active_power_limits), 'reactive_power_limits': None if value.reactive_power_limits is None else sienna_min_max_to_json(value.reactive_power_limits), 'parameter_units': None if value.parameter_units is None else sienna_impedance_unit_basis_to_json(value.parameter_units), 'R_th': value.R_th, 'X_th': value.X_th, 'internal_voltage': value.internal_voltage, 'internal_angle': value.internal_angle, 'base_voltage': value.base_voltage, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units), 'operation_cost': write_sienna_schema_union((SiennaObjectKind.ImportExportCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), value.operation_cost), 'dynamic_injector': value.dynamic_injector}
