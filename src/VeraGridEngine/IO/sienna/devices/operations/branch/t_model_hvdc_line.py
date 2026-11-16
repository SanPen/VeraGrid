# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TModelHVDCLine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import SiennaOperationalFlowLimit

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTModelHVDCLine(SiennaSchemaModel):
    """Expose every declared TModelHVDCLine property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'active_power_flow', 'arc', 'base_current', 'r', 'l', 'c', 'operational_flow_limit',)

    def __init__(self, id: int, name: str, available: bool, active_power_flow: float, arc: int, base_current: float, r: float, l: float, c: float, operational_flow_limit: SiennaOperationalFlowLimit) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.active_power_flow: float = active_power_flow
        self.arc: int = arc
        self.base_current: float = base_current
        self.r: float = r
        self.l: float = l
        self.c: float = c
        self.operational_flow_limit: SiennaOperationalFlowLimit = operational_flow_limit


def parse_sienna_t_model_hvdc_line(data: dict[str, Any]) -> SiennaTModelHVDCLine:
    """Parse declared TModelHVDCLine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TModelHVDCLine object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
    return SiennaTModelHVDCLine(id=get_required_value(data, 'id', 'TModelHVDCLine'), name=get_required_value(data, 'name', 'TModelHVDCLine'), available=get_required_value(data, 'available', 'TModelHVDCLine'), active_power_flow=get_required_value(data, 'active_power_flow', 'TModelHVDCLine'), arc=get_required_value(data, 'arc', 'TModelHVDCLine'), base_current=get_required_value(data, 'base_current', 'TModelHVDCLine'), r=get_required_value(data, 'r', 'TModelHVDCLine'), l=get_required_value(data, 'l', 'TModelHVDCLine'), c=get_required_value(data, 'c', 'TModelHVDCLine'), operational_flow_limit=None if data.get('operational_flow_limit', None) is None else parse_sienna_operational_flow_limit(data.get('operational_flow_limit', None)))

def sienna_t_model_hvdc_line_to_json(value: SiennaTModelHVDCLine) -> dict[str, Any]:
    """Write every TModelHVDCLine slot to explicit schema property names.

    :param value: Typed TModelHVDCLine object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import sienna_operational_flow_limit_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'active_power_flow': value.active_power_flow, 'arc': value.arc, 'base_current': value.base_current, 'r': value.r, 'l': value.l, 'c': value.c, 'operational_flow_limit': None if value.operational_flow_limit is None else sienna_operational_flow_limit_to_json(value.operational_flow_limit)}
