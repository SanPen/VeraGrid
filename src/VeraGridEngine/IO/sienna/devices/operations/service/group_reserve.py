# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna GroupReserve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import SiennaCostCurve
    from VeraGridEngine.IO.sienna.devices.operations.common.reserve_direction import SiennaReserveDirection

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaGroupReserve(SiennaSchemaModel):
    """Expose every declared GroupReserve property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'requirement', 'variable', 'reserve_direction',)

    def __init__(self, id: int, name: str, available: bool, requirement: float, variable: SiennaCostCurve, reserve_direction: SiennaReserveDirection) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.requirement: float = requirement
        self.variable: SiennaCostCurve = variable
        self.reserve_direction: SiennaReserveDirection = reserve_direction


def parse_sienna_group_reserve(data: dict[str, Any]) -> SiennaGroupReserve:
    """Parse declared GroupReserve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed GroupReserve object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import parse_sienna_cost_curve
    from VeraGridEngine.IO.sienna.devices.operations.common.reserve_direction import parse_sienna_reserve_direction
    return SiennaGroupReserve(id=get_required_value(data, 'id', 'GroupReserve'), name=get_required_value(data, 'name', 'GroupReserve'), available=get_required_value(data, 'available', 'GroupReserve'), requirement=get_required_value(data, 'requirement', 'GroupReserve'), variable=None if data.get('variable', None) is None else parse_sienna_cost_curve(data.get('variable', None)), reserve_direction=parse_sienna_reserve_direction(get_required_value(data, 'reserve_direction', 'GroupReserve')))

def sienna_group_reserve_to_json(value: SiennaGroupReserve) -> dict[str, Any]:
    """Write every GroupReserve slot to explicit schema property names.

    :param value: Typed GroupReserve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import sienna_cost_curve_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.reserve_direction import sienna_reserve_direction_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'requirement': value.requirement, 'variable': None if value.variable is None else sienna_cost_curve_to_json(value.variable), 'reserve_direction': sienna_reserve_direction_to_json(value.reserve_direction)}
