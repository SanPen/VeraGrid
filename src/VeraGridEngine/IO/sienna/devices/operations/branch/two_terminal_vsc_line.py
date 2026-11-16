# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TwoTerminalVSCLine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import SiennaLossCurve
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import SiennaOperationalFlowLimit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.operations.common.vscac_control_modes import SiennaVSCACControlModes
    from VeraGridEngine.IO.sienna.devices.operations.common.vscdc_control_modes import SiennaVSCDCControlModes

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTwoTerminalVSCLine(SiennaSchemaModel):
    """Expose every declared TwoTerminalVSCLine property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'arc', 'active_power_flow', 'rating', 'g', 'dc_current', 'reactive_power_from', 'dc_control_from', 'ac_control_from', 'dc_power_setpoint_from', 'dc_voltage_setpoint_from', 'power_factor_setpoint_from', 'ac_voltage_setpoint_from', 'rated_ac_voltage_from', 'converter_loss_from', 'max_dc_current_from', 'rating_from', 'reactive_power_limits_from', 'power_factor_weighting_fraction_from', 'voltage_limits_from', 'dc_voltage_droop_from', 'reactive_power_to', 'dc_control_to', 'ac_control_to', 'dc_power_setpoint_to', 'dc_voltage_setpoint_to', 'power_factor_setpoint_to', 'ac_voltage_setpoint_to', 'rated_ac_voltage_to', 'converter_loss_to', 'max_dc_current_to', 'rating_to', 'operational_flow_limit', 'reactive_power_limits_to', 'power_factor_weighting_fraction_to', 'voltage_limits_to', 'dc_voltage_droop_to', 'rated_dc_voltage', 'remote_bus_control_from', 'remote_bus_control_to', 'base_power', 'power_units',)

    def __init__(self, id: int, name: str, available: bool, arc: int, active_power_flow: float, rating: float, g: float, dc_current: float, reactive_power_from: float, dc_control_from: SiennaVSCDCControlModes, ac_control_from: SiennaVSCACControlModes, dc_power_setpoint_from: float | None, dc_voltage_setpoint_from: float | None, power_factor_setpoint_from: float | None, ac_voltage_setpoint_from: float | None, rated_ac_voltage_from: float, converter_loss_from: SiennaLossCurve, max_dc_current_from: float, rating_from: float, reactive_power_limits_from: SiennaMinMax, power_factor_weighting_fraction_from: float, voltage_limits_from: SiennaMinMax, dc_voltage_droop_from: float, reactive_power_to: float, dc_control_to: SiennaVSCDCControlModes, ac_control_to: SiennaVSCACControlModes, dc_power_setpoint_to: float | None, dc_voltage_setpoint_to: float | None, power_factor_setpoint_to: float | None, ac_voltage_setpoint_to: float | None, rated_ac_voltage_to: float, converter_loss_to: SiennaLossCurve, max_dc_current_to: float, rating_to: float, operational_flow_limit: SiennaOperationalFlowLimit, reactive_power_limits_to: SiennaMinMax, power_factor_weighting_fraction_to: float, voltage_limits_to: SiennaMinMax, dc_voltage_droop_to: float, rated_dc_voltage: float, remote_bus_control_from: int | None, remote_bus_control_to: int | None, base_power: float, power_units: SiennaUnitSystem) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.arc: int = arc
        self.active_power_flow: float = active_power_flow
        self.rating: float = rating
        self.g: float = g
        self.dc_current: float = dc_current
        self.reactive_power_from: float = reactive_power_from
        self.dc_control_from: SiennaVSCDCControlModes = dc_control_from
        self.ac_control_from: SiennaVSCACControlModes = ac_control_from
        self.dc_power_setpoint_from: float | None = dc_power_setpoint_from
        self.dc_voltage_setpoint_from: float | None = dc_voltage_setpoint_from
        self.power_factor_setpoint_from: float | None = power_factor_setpoint_from
        self.ac_voltage_setpoint_from: float | None = ac_voltage_setpoint_from
        self.rated_ac_voltage_from: float = rated_ac_voltage_from
        self.converter_loss_from: SiennaLossCurve = converter_loss_from
        self.max_dc_current_from: float = max_dc_current_from
        self.rating_from: float = rating_from
        self.reactive_power_limits_from: SiennaMinMax = reactive_power_limits_from
        self.power_factor_weighting_fraction_from: float = power_factor_weighting_fraction_from
        self.voltage_limits_from: SiennaMinMax = voltage_limits_from
        self.dc_voltage_droop_from: float = dc_voltage_droop_from
        self.reactive_power_to: float = reactive_power_to
        self.dc_control_to: SiennaVSCDCControlModes = dc_control_to
        self.ac_control_to: SiennaVSCACControlModes = ac_control_to
        self.dc_power_setpoint_to: float | None = dc_power_setpoint_to
        self.dc_voltage_setpoint_to: float | None = dc_voltage_setpoint_to
        self.power_factor_setpoint_to: float | None = power_factor_setpoint_to
        self.ac_voltage_setpoint_to: float | None = ac_voltage_setpoint_to
        self.rated_ac_voltage_to: float = rated_ac_voltage_to
        self.converter_loss_to: SiennaLossCurve = converter_loss_to
        self.max_dc_current_to: float = max_dc_current_to
        self.rating_to: float = rating_to
        self.operational_flow_limit: SiennaOperationalFlowLimit = operational_flow_limit
        self.reactive_power_limits_to: SiennaMinMax = reactive_power_limits_to
        self.power_factor_weighting_fraction_to: float = power_factor_weighting_fraction_to
        self.voltage_limits_to: SiennaMinMax = voltage_limits_to
        self.dc_voltage_droop_to: float = dc_voltage_droop_to
        self.rated_dc_voltage: float = rated_dc_voltage
        self.remote_bus_control_from: int | None = remote_bus_control_from
        self.remote_bus_control_to: int | None = remote_bus_control_to
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units


def parse_sienna_two_terminal_vsc_line(data: dict[str, Any]) -> SiennaTwoTerminalVSCLine:
    """Parse declared TwoTerminalVSCLine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TwoTerminalVSCLine object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import parse_sienna_loss_curve
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.vscac_control_modes import parse_sienna_vscac_control_modes
    from VeraGridEngine.IO.sienna.devices.operations.common.vscdc_control_modes import parse_sienna_vscdc_control_modes
    return SiennaTwoTerminalVSCLine(id=get_required_value(data, 'id', 'TwoTerminalVSCLine'), name=get_required_value(data, 'name', 'TwoTerminalVSCLine'), available=get_required_value(data, 'available', 'TwoTerminalVSCLine'), arc=get_required_value(data, 'arc', 'TwoTerminalVSCLine'), active_power_flow=get_required_value(data, 'active_power_flow', 'TwoTerminalVSCLine'), rating=get_required_value(data, 'rating', 'TwoTerminalVSCLine'), g=data.get('g', None), dc_current=data.get('dc_current', None), reactive_power_from=data.get('reactive_power_from', None), dc_control_from=None if data.get('dc_control_from', None) is None else parse_sienna_vscdc_control_modes(data.get('dc_control_from', None)), ac_control_from=None if data.get('ac_control_from', None) is None else parse_sienna_vscac_control_modes(data.get('ac_control_from', None)), dc_power_setpoint_from=data.get('dc_power_setpoint_from', None), dc_voltage_setpoint_from=data.get('dc_voltage_setpoint_from', None), power_factor_setpoint_from=data.get('power_factor_setpoint_from', None), ac_voltage_setpoint_from=data.get('ac_voltage_setpoint_from', None), rated_ac_voltage_from=data.get('rated_ac_voltage_from', None), converter_loss_from=None if data.get('converter_loss_from', None) is None else parse_sienna_loss_curve(data.get('converter_loss_from', None)), max_dc_current_from=data.get('max_dc_current_from', None), rating_from=data.get('rating_from', None), reactive_power_limits_from=None if data.get('reactive_power_limits_from', None) is None else parse_sienna_min_max(data.get('reactive_power_limits_from', None)), power_factor_weighting_fraction_from=data.get('power_factor_weighting_fraction_from', None), voltage_limits_from=None if data.get('voltage_limits_from', None) is None else parse_sienna_min_max(data.get('voltage_limits_from', None)), dc_voltage_droop_from=data.get('dc_voltage_droop_from', None), reactive_power_to=data.get('reactive_power_to', None), dc_control_to=None if data.get('dc_control_to', None) is None else parse_sienna_vscdc_control_modes(data.get('dc_control_to', None)), ac_control_to=None if data.get('ac_control_to', None) is None else parse_sienna_vscac_control_modes(data.get('ac_control_to', None)), dc_power_setpoint_to=data.get('dc_power_setpoint_to', None), dc_voltage_setpoint_to=data.get('dc_voltage_setpoint_to', None), power_factor_setpoint_to=data.get('power_factor_setpoint_to', None), ac_voltage_setpoint_to=data.get('ac_voltage_setpoint_to', None), rated_ac_voltage_to=data.get('rated_ac_voltage_to', None), converter_loss_to=None if data.get('converter_loss_to', None) is None else parse_sienna_loss_curve(data.get('converter_loss_to', None)), max_dc_current_to=data.get('max_dc_current_to', None), rating_to=data.get('rating_to', None), operational_flow_limit=None if data.get('operational_flow_limit', None) is None else parse_sienna_operational_flow_limit(data.get('operational_flow_limit', None)), reactive_power_limits_to=None if data.get('reactive_power_limits_to', None) is None else parse_sienna_min_max(data.get('reactive_power_limits_to', None)), power_factor_weighting_fraction_to=data.get('power_factor_weighting_fraction_to', None), voltage_limits_to=None if data.get('voltage_limits_to', None) is None else parse_sienna_min_max(data.get('voltage_limits_to', None)), dc_voltage_droop_to=data.get('dc_voltage_droop_to', None), rated_dc_voltage=data.get('rated_dc_voltage', None), remote_bus_control_from=data.get('remote_bus_control_from', None), remote_bus_control_to=data.get('remote_bus_control_to', None), base_power=get_required_value(data, 'base_power', 'TwoTerminalVSCLine'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'TwoTerminalVSCLine')))

def sienna_two_terminal_vsc_line_to_json(value: SiennaTwoTerminalVSCLine) -> dict[str, Any]:
    """Write every TwoTerminalVSCLine slot to explicit schema property names.

    :param value: Typed TwoTerminalVSCLine object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import sienna_loss_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import sienna_operational_flow_limit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.vscac_control_modes import sienna_vscac_control_modes_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.vscdc_control_modes import sienna_vscdc_control_modes_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'arc': value.arc, 'active_power_flow': value.active_power_flow, 'rating': value.rating, 'g': value.g, 'dc_current': value.dc_current, 'reactive_power_from': value.reactive_power_from, 'dc_control_from': None if value.dc_control_from is None else sienna_vscdc_control_modes_to_json(value.dc_control_from), 'ac_control_from': None if value.ac_control_from is None else sienna_vscac_control_modes_to_json(value.ac_control_from), 'dc_power_setpoint_from': value.dc_power_setpoint_from, 'dc_voltage_setpoint_from': value.dc_voltage_setpoint_from, 'power_factor_setpoint_from': value.power_factor_setpoint_from, 'ac_voltage_setpoint_from': value.ac_voltage_setpoint_from, 'rated_ac_voltage_from': value.rated_ac_voltage_from, 'converter_loss_from': None if value.converter_loss_from is None else sienna_loss_curve_to_json(value.converter_loss_from), 'max_dc_current_from': value.max_dc_current_from, 'rating_from': value.rating_from, 'reactive_power_limits_from': None if value.reactive_power_limits_from is None else sienna_min_max_to_json(value.reactive_power_limits_from), 'power_factor_weighting_fraction_from': value.power_factor_weighting_fraction_from, 'voltage_limits_from': None if value.voltage_limits_from is None else sienna_min_max_to_json(value.voltage_limits_from), 'dc_voltage_droop_from': value.dc_voltage_droop_from, 'reactive_power_to': value.reactive_power_to, 'dc_control_to': None if value.dc_control_to is None else sienna_vscdc_control_modes_to_json(value.dc_control_to), 'ac_control_to': None if value.ac_control_to is None else sienna_vscac_control_modes_to_json(value.ac_control_to), 'dc_power_setpoint_to': value.dc_power_setpoint_to, 'dc_voltage_setpoint_to': value.dc_voltage_setpoint_to, 'power_factor_setpoint_to': value.power_factor_setpoint_to, 'ac_voltage_setpoint_to': value.ac_voltage_setpoint_to, 'rated_ac_voltage_to': value.rated_ac_voltage_to, 'converter_loss_to': None if value.converter_loss_to is None else sienna_loss_curve_to_json(value.converter_loss_to), 'max_dc_current_to': value.max_dc_current_to, 'rating_to': value.rating_to, 'operational_flow_limit': None if value.operational_flow_limit is None else sienna_operational_flow_limit_to_json(value.operational_flow_limit), 'reactive_power_limits_to': None if value.reactive_power_limits_to is None else sienna_min_max_to_json(value.reactive_power_limits_to), 'power_factor_weighting_fraction_to': value.power_factor_weighting_fraction_to, 'voltage_limits_to': None if value.voltage_limits_to is None else sienna_min_max_to_json(value.voltage_limits_to), 'dc_voltage_droop_to': value.dc_voltage_droop_to, 'rated_dc_voltage': value.rated_dc_voltage, 'remote_bus_control_from': value.remote_bus_control_from, 'remote_bus_control_to': value.remote_bus_control_to, 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units)}
