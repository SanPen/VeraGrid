# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TwoTerminalGenericHVDCLine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import SiennaLossCurve
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import SiennaOperationalFlowLimit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTwoTerminalGenericHVDCLine(SiennaSchemaModel):
    """Expose every declared TwoTerminalGenericHVDCLine property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'active_power_flow', 'arc', 'rating', 'rating_from', 'rating_to', 'operational_flow_limit', 'reactive_power_limits_from', 'reactive_power_limits_to', 'loss', 'base_power', 'power_units',)

    def __init__(self, id: int, name: str, available: bool, active_power_flow: float, arc: int, rating: float, rating_from: float, rating_to: float, operational_flow_limit: SiennaOperationalFlowLimit, reactive_power_limits_from: SiennaMinMax, reactive_power_limits_to: SiennaMinMax, loss: SiennaLossCurve, base_power: float, power_units: SiennaUnitSystem) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.active_power_flow: float = active_power_flow
        self.arc: int = arc
        self.rating: float = rating
        self.rating_from: float = rating_from
        self.rating_to: float = rating_to
        self.operational_flow_limit: SiennaOperationalFlowLimit = operational_flow_limit
        self.reactive_power_limits_from: SiennaMinMax = reactive_power_limits_from
        self.reactive_power_limits_to: SiennaMinMax = reactive_power_limits_to
        self.loss: SiennaLossCurve = loss
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units


def parse_sienna_two_terminal_generic_hvdc_line(data: dict[str, Any]) -> SiennaTwoTerminalGenericHVDCLine:
    """Parse declared TwoTerminalGenericHVDCLine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TwoTerminalGenericHVDCLine object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import parse_sienna_loss_curve
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaTwoTerminalGenericHVDCLine(id=get_required_value(data, 'id', 'TwoTerminalGenericHVDCLine'), name=get_required_value(data, 'name', 'TwoTerminalGenericHVDCLine'), available=get_required_value(data, 'available', 'TwoTerminalGenericHVDCLine'), active_power_flow=get_required_value(data, 'active_power_flow', 'TwoTerminalGenericHVDCLine'), arc=get_required_value(data, 'arc', 'TwoTerminalGenericHVDCLine'), rating=get_required_value(data, 'rating', 'TwoTerminalGenericHVDCLine'), rating_from=data.get('rating_from', None), rating_to=data.get('rating_to', None), operational_flow_limit=None if data.get('operational_flow_limit', None) is None else parse_sienna_operational_flow_limit(data.get('operational_flow_limit', None)), reactive_power_limits_from=parse_sienna_min_max(get_required_value(data, 'reactive_power_limits_from', 'TwoTerminalGenericHVDCLine')), reactive_power_limits_to=parse_sienna_min_max(get_required_value(data, 'reactive_power_limits_to', 'TwoTerminalGenericHVDCLine')), loss=None if data.get('loss', None) is None else parse_sienna_loss_curve(data.get('loss', None)), base_power=get_required_value(data, 'base_power', 'TwoTerminalGenericHVDCLine'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'TwoTerminalGenericHVDCLine')))

def sienna_two_terminal_generic_hvdc_line_to_json(value: SiennaTwoTerminalGenericHVDCLine) -> dict[str, Any]:
    """Write every TwoTerminalGenericHVDCLine slot to explicit schema property names.

    :param value: Typed TwoTerminalGenericHVDCLine object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import sienna_loss_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import sienna_operational_flow_limit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'active_power_flow': value.active_power_flow, 'arc': value.arc, 'rating': value.rating, 'rating_from': value.rating_from, 'rating_to': value.rating_to, 'operational_flow_limit': None if value.operational_flow_limit is None else sienna_operational_flow_limit_to_json(value.operational_flow_limit), 'reactive_power_limits_from': sienna_min_max_to_json(value.reactive_power_limits_from), 'reactive_power_limits_to': sienna_min_max_to_json(value.reactive_power_limits_to), 'loss': None if value.loss is None else sienna_loss_curve_to_json(value.loss), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units)}
