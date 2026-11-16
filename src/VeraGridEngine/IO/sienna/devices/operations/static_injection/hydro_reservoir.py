# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HydroReservoir schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.function_data import SiennaFunctionData
    from VeraGridEngine.IO.sienna.devices.core.common.hydro_reservoir_cost import SiennaHydroReservoirCost
    from VeraGridEngine.IO.sienna.devices.core.common.import_export_time_series_cost import SiennaImportExportTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.market_bid_time_series_cost import SiennaMarketBidTimeSeriesCost
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHydroReservoir(SiennaSchemaModel):
    """Expose every declared HydroReservoir property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'storage_level_limits', 'initial_level', 'spillage_limits', 'inflow', 'outflow', 'level_targets', 'intake_elevation', 'head_to_volume_factor', 'upstream_turbines', 'downstream_turbines', 'upstream_reservoirs', 'operation_cost', 'evaporative_loss', 'level_data_type',)

    def __init__(self, id: int, name: str, available: bool, storage_level_limits: SiennaMinMax, initial_level: float, spillage_limits: SiennaMinMax, inflow: float, outflow: float, level_targets: float, intake_elevation: float, head_to_volume_factor: SiennaFunctionData, upstream_turbines: list[int], downstream_turbines: list[int], upstream_reservoirs: list[int], operation_cost: SiennaHydroReservoirCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost, evaporative_loss: float, level_data_type: str) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.storage_level_limits: SiennaMinMax = storage_level_limits
        self.initial_level: float = initial_level
        self.spillage_limits: SiennaMinMax = spillage_limits
        self.inflow: float = inflow
        self.outflow: float = outflow
        self.level_targets: float = level_targets
        self.intake_elevation: float = intake_elevation
        self.head_to_volume_factor: SiennaFunctionData = head_to_volume_factor
        self.upstream_turbines: list[int] = upstream_turbines
        self.downstream_turbines: list[int] = downstream_turbines
        self.upstream_reservoirs: list[int] = upstream_reservoirs
        self.operation_cost: SiennaHydroReservoirCost | SiennaMarketBidTimeSeriesCost | SiennaImportExportTimeSeriesCost = operation_cost
        self.evaporative_loss: float = evaporative_loss
        self.level_data_type: str = level_data_type


def parse_sienna_hydro_reservoir(data: dict[str, Any]) -> SiennaHydroReservoir:
    """Parse declared HydroReservoir properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HydroReservoir object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.function_data import parse_sienna_function_data
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.schema_object import (SiennaObjectKind,
                                                                parse_sienna_schema_union)
    return SiennaHydroReservoir(id=get_required_value(data, 'id', 'HydroReservoir'), name=get_required_value(data, 'name', 'HydroReservoir'), available=get_required_value(data, 'available', 'HydroReservoir'), storage_level_limits=parse_sienna_min_max(get_required_value(data, 'storage_level_limits', 'HydroReservoir')), initial_level=get_required_value(data, 'initial_level', 'HydroReservoir'), spillage_limits=None if data.get('spillage_limits', None) is None else parse_sienna_min_max(data.get('spillage_limits', None)), inflow=get_required_value(data, 'inflow', 'HydroReservoir'), outflow=get_required_value(data, 'outflow', 'HydroReservoir'), level_targets=data.get('level_targets', None), intake_elevation=get_required_value(data, 'intake_elevation', 'HydroReservoir'), head_to_volume_factor=parse_sienna_function_data(get_required_value(data, 'head_to_volume_factor', 'HydroReservoir')), upstream_turbines=data.get('upstream_turbines', None), downstream_turbines=data.get('downstream_turbines', None), upstream_reservoirs=data.get('upstream_reservoirs', None), operation_cost=parse_sienna_schema_union((SiennaObjectKind.HydroReservoirCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), get_required_value(data, 'operation_cost', 'HydroReservoir')), evaporative_loss=data.get('evaporative_loss', None), level_data_type=data.get('level_data_type', None))

def sienna_hydro_reservoir_to_json(value: SiennaHydroReservoir) -> dict[str, Any]:
    """Write every HydroReservoir slot to explicit schema property names.

    :param value: Typed HydroReservoir object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.function_data import sienna_function_data_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.writer_registry import write_sienna_schema_union
    return {'id': value.id, 'name': value.name, 'available': value.available, 'storage_level_limits': sienna_min_max_to_json(value.storage_level_limits), 'initial_level': value.initial_level, 'spillage_limits': None if value.spillage_limits is None else sienna_min_max_to_json(value.spillage_limits), 'inflow': value.inflow, 'outflow': value.outflow, 'level_targets': value.level_targets, 'intake_elevation': value.intake_elevation, 'head_to_volume_factor': sienna_function_data_to_json(value.head_to_volume_factor), 'upstream_turbines': value.upstream_turbines, 'downstream_turbines': value.downstream_turbines, 'upstream_reservoirs': value.upstream_reservoirs, 'operation_cost': write_sienna_schema_union((SiennaObjectKind.HydroReservoirCost, SiennaObjectKind.MarketBidTimeSeriesCost, SiennaObjectKind.ImportExportTimeSeriesCost), value.operation_cost), 'evaporative_loss': value.evaporative_loss, 'level_data_type': value.level_data_type}
