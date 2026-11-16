# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna DeterministicSingleTimeSeries schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.time_series.common.element_type import SiennaElementType
    from VeraGridEngine.IO.sienna.devices.time_series.common.interval_alignment import SiennaIntervalAlignment
    from VeraGridEngine.IO.sienna.devices.time_series.common.owner_category import SiennaOwnerCategory
    from VeraGridEngine.IO.sienna.devices.time_series.common.period import SiennaPeriod
    from VeraGridEngine.IO.sienna.devices.time_series.common.time_reference import SiennaTimeReference
    from VeraGridEngine.IO.sienna.devices.time_series.common.time_series_features import SiennaTimeSeriesFeatures

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaDeterministicSingleTimeSeries(SiennaSchemaModel):
    """Expose every declared DeterministicSingleTimeSeries property through fixed slots."""

    __slots__ = ('association_id', 'owner_id', 'owner_type', 'owner_category', 'time_series_type', 'name', 'features', 'uri', 'data_hash', 'element_type', 'element_shape', 'array_shape', 'units', 'quantity_kind', 'unit_system', 'time_reference', 'interval_alignment', 'component_field', 'application_data', 'initial_timestamp', 'resolution', 'horizon', 'interval', 'count',)

    def __init__(self, association_id: int, owner_id: int, owner_type: str, owner_category: SiennaOwnerCategory, time_series_type: str, name: str, features: SiennaTimeSeriesFeatures, uri: str, data_hash: str, element_type: SiennaElementType, element_shape: list[int], array_shape: list[int], units: str, quantity_kind: str, unit_system: SiennaUnitSystem, time_reference: SiennaTimeReference, interval_alignment: SiennaIntervalAlignment, component_field: str, application_data: str, initial_timestamp: str | int | float | bool | None, resolution: SiennaPeriod, horizon: SiennaPeriod, interval: SiennaPeriod, count: int) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.association_id: int = association_id
        self.owner_id: int = owner_id
        self.owner_type: str = owner_type
        self.owner_category: SiennaOwnerCategory = owner_category
        self.time_series_type: str = time_series_type
        self.name: str = name
        self.features: SiennaTimeSeriesFeatures = features
        self.uri: str = uri
        self.data_hash: str = data_hash
        self.element_type: SiennaElementType = element_type
        self.element_shape: list[int] = element_shape
        self.array_shape: list[int] = array_shape
        self.units: str = units
        self.quantity_kind: str = quantity_kind
        self.unit_system: SiennaUnitSystem = unit_system
        self.time_reference: SiennaTimeReference = time_reference
        self.interval_alignment: SiennaIntervalAlignment = interval_alignment
        self.component_field: str = component_field
        self.application_data: str = application_data
        self.initial_timestamp: str | int | float | bool | None = initial_timestamp
        self.resolution: SiennaPeriod = resolution
        self.horizon: SiennaPeriod = horizon
        self.interval: SiennaPeriod = interval
        self.count: int = count


def parse_sienna_deterministic_single_time_series(data: dict[str, Any]) -> SiennaDeterministicSingleTimeSeries:
    """Parse declared DeterministicSingleTimeSeries properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed DeterministicSingleTimeSeries object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.time_series.common.element_type import parse_sienna_element_type
    from VeraGridEngine.IO.sienna.devices.time_series.common.interval_alignment import parse_sienna_interval_alignment
    from VeraGridEngine.IO.sienna.devices.time_series.common.owner_category import parse_sienna_owner_category
    from VeraGridEngine.IO.sienna.devices.time_series.common.period import parse_sienna_period
    from VeraGridEngine.IO.sienna.devices.time_series.common.time_reference import parse_sienna_time_reference
    from VeraGridEngine.IO.sienna.devices.time_series.common.time_series_features import parse_sienna_time_series_features
    return SiennaDeterministicSingleTimeSeries(association_id=get_required_value(data, 'association_id', 'DeterministicSingleTimeSeries'), owner_id=get_required_value(data, 'owner_id', 'DeterministicSingleTimeSeries'), owner_type=get_required_value(data, 'owner_type', 'DeterministicSingleTimeSeries'), owner_category=parse_sienna_owner_category(get_required_value(data, 'owner_category', 'DeterministicSingleTimeSeries')), time_series_type=get_required_value(data, 'time_series_type', 'DeterministicSingleTimeSeries'), name=get_required_value(data, 'name', 'DeterministicSingleTimeSeries'), features=parse_sienna_time_series_features(get_required_value(data, 'features', 'DeterministicSingleTimeSeries')), uri=get_required_value(data, 'uri', 'DeterministicSingleTimeSeries'), data_hash=data.get('data_hash', None), element_type=parse_sienna_element_type(get_required_value(data, 'element_type', 'DeterministicSingleTimeSeries')), element_shape=get_required_value(data, 'element_shape', 'DeterministicSingleTimeSeries'), array_shape=data.get('array_shape', None), units=data.get('units', None), quantity_kind=data.get('quantity_kind', None), unit_system=None if data.get('unit_system', None) is None else parse_sienna_unit_system(data.get('unit_system', None)), time_reference=None if data.get('time_reference', None) is None else parse_sienna_time_reference(data.get('time_reference', None)), interval_alignment=None if data.get('interval_alignment', None) is None else parse_sienna_interval_alignment(data.get('interval_alignment', None)), component_field=data.get('component_field', None), application_data=data.get('application_data', None), initial_timestamp=get_required_value(data, 'initial_timestamp', 'DeterministicSingleTimeSeries'), resolution=parse_sienna_period(get_required_value(data, 'resolution', 'DeterministicSingleTimeSeries')), horizon=parse_sienna_period(get_required_value(data, 'horizon', 'DeterministicSingleTimeSeries')), interval=parse_sienna_period(get_required_value(data, 'interval', 'DeterministicSingleTimeSeries')), count=get_required_value(data, 'count', 'DeterministicSingleTimeSeries'))

def sienna_deterministic_single_time_series_to_json(value: SiennaDeterministicSingleTimeSeries) -> dict[str, Any]:
    """Write every DeterministicSingleTimeSeries slot to explicit schema property names.

    :param value: Typed DeterministicSingleTimeSeries object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.time_series.common.element_type import sienna_element_type_to_json
    from VeraGridEngine.IO.sienna.devices.time_series.common.interval_alignment import sienna_interval_alignment_to_json
    from VeraGridEngine.IO.sienna.devices.time_series.common.owner_category import sienna_owner_category_to_json
    from VeraGridEngine.IO.sienna.devices.time_series.common.period import sienna_period_to_json
    from VeraGridEngine.IO.sienna.devices.time_series.common.time_reference import sienna_time_reference_to_json
    from VeraGridEngine.IO.sienna.devices.time_series.common.time_series_features import sienna_time_series_features_to_json
    return {'association_id': value.association_id, 'owner_id': value.owner_id, 'owner_type': value.owner_type, 'owner_category': sienna_owner_category_to_json(value.owner_category), 'time_series_type': value.time_series_type, 'name': value.name, 'features': sienna_time_series_features_to_json(value.features), 'uri': value.uri, 'data_hash': value.data_hash, 'element_type': sienna_element_type_to_json(value.element_type), 'element_shape': value.element_shape, 'array_shape': value.array_shape, 'units': value.units, 'quantity_kind': value.quantity_kind, 'unit_system': None if value.unit_system is None else sienna_unit_system_to_json(value.unit_system), 'time_reference': None if value.time_reference is None else sienna_time_reference_to_json(value.time_reference), 'interval_alignment': None if value.interval_alignment is None else sienna_interval_alignment_to_json(value.interval_alignment), 'component_field': value.component_field, 'application_data': value.application_data, 'initial_timestamp': value.initial_timestamp, 'resolution': sienna_period_to_json(value.resolution), 'horizon': sienna_period_to_json(value.horizon), 'interval': sienna_period_to_json(value.interval), 'count': value.count}
