# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna OfflineReserve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import SiennaCostCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaOfflineReserve(SiennaSchemaModel):
    """Expose every declared OfflineReserve property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'time_frame', 'requirement', 'variable', 'sustained_time', 'max_output_fraction', 'max_participation_factor', 'deployed_fraction',)

    def __init__(self, id: int, name: str, available: bool, time_frame: float, requirement: float, variable: SiennaCostCurve, sustained_time: float, max_output_fraction: float, max_participation_factor: float, deployed_fraction: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.time_frame: float = time_frame
        self.requirement: float = requirement
        self.variable: SiennaCostCurve = variable
        self.sustained_time: float = sustained_time
        self.max_output_fraction: float = max_output_fraction
        self.max_participation_factor: float = max_participation_factor
        self.deployed_fraction: float = deployed_fraction


def parse_sienna_offline_reserve(data: dict[str, Any]) -> SiennaOfflineReserve:
    """Parse declared OfflineReserve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed OfflineReserve object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import parse_sienna_cost_curve
    return SiennaOfflineReserve(id=get_required_value(data, 'id', 'OfflineReserve'), name=get_required_value(data, 'name', 'OfflineReserve'), available=get_required_value(data, 'available', 'OfflineReserve'), time_frame=get_required_value(data, 'time_frame', 'OfflineReserve'), requirement=data.get('requirement', None), variable=None if data.get('variable', None) is None else parse_sienna_cost_curve(data.get('variable', None)), sustained_time=data.get('sustained_time', None), max_output_fraction=data.get('max_output_fraction', None), max_participation_factor=data.get('max_participation_factor', None), deployed_fraction=data.get('deployed_fraction', None))

def sienna_offline_reserve_to_json(value: SiennaOfflineReserve) -> dict[str, Any]:
    """Write every OfflineReserve slot to explicit schema property names.

    :param value: Typed OfflineReserve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import sienna_cost_curve_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'time_frame': value.time_frame, 'requirement': value.requirement, 'variable': None if value.variable is None else sienna_cost_curve_to_json(value.variable), 'sustained_time': value.sustained_time, 'max_output_fraction': value.max_output_fraction, 'max_participation_factor': value.max_participation_factor, 'deployed_fraction': value.deployed_fraction}
