# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna TwoTerminalLCCLine schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import SiennaLossCurve
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import SiennaOperationalFlowLimit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem
    from VeraGridEngine.IO.sienna.devices.operations.common.lcc_control_mode import SiennaLCCControlMode

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaTwoTerminalLCCLine(SiennaSchemaModel):
    """Expose every declared TwoTerminalLCCLine property through fixed slots."""

    __slots__ = ('id', 'name', 'available', 'arc', 'active_power_flow', 'r', 'power_transfer_setpoint', 'current_transfer_setpoint', 'scheduled_dc_voltage', 'rectifier_bridges', 'rectifier_delay_angle_limits', 'rectifier_rc', 'rectifier_xc', 'rectifier_base_voltage', 'inverter_bridges', 'inverter_extinction_angle_limits', 'inverter_rc', 'inverter_xc', 'inverter_base_voltage', 'control_mode', 'switch_mode_voltage', 'compounding_resistance', 'min_compounding_voltage', 'rectifier_transformer_ratio', 'rectifier_tap_setting', 'rectifier_tap_limits', 'rectifier_tap_step', 'rectifier_delay_angle', 'rectifier_capacitor_reactance', 'inverter_transformer_ratio', 'inverter_tap_setting', 'inverter_tap_limits', 'inverter_tap_step', 'inverter_extinction_angle', 'inverter_capacitor_reactance', 'rating', 'rating_from', 'rating_to', 'operational_flow_limit', 'reactive_power_limits_from', 'reactive_power_limits_to', 'loss', 'base_power', 'power_units',)

    def __init__(self, id: int, name: str, available: bool, arc: int, active_power_flow: float, r: float, power_transfer_setpoint: float | None, current_transfer_setpoint: float | None, scheduled_dc_voltage: float, rectifier_bridges: int, rectifier_delay_angle_limits: SiennaMinMax, rectifier_rc: float, rectifier_xc: float, rectifier_base_voltage: float, inverter_bridges: int, inverter_extinction_angle_limits: SiennaMinMax, inverter_rc: float, inverter_xc: float, inverter_base_voltage: float, control_mode: SiennaLCCControlMode, switch_mode_voltage: float, compounding_resistance: float, min_compounding_voltage: float, rectifier_transformer_ratio: float, rectifier_tap_setting: float, rectifier_tap_limits: SiennaMinMax, rectifier_tap_step: float, rectifier_delay_angle: float, rectifier_capacitor_reactance: float, inverter_transformer_ratio: float, inverter_tap_setting: float, inverter_tap_limits: SiennaMinMax, inverter_tap_step: float, inverter_extinction_angle: float, inverter_capacitor_reactance: float, rating: float, rating_from: float, rating_to: float, operational_flow_limit: SiennaOperationalFlowLimit, reactive_power_limits_from: SiennaMinMax, reactive_power_limits_to: SiennaMinMax, loss: SiennaLossCurve, base_power: float, power_units: SiennaUnitSystem) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.available: bool = available
        self.arc: int = arc
        self.active_power_flow: float = active_power_flow
        self.r: float = r
        self.power_transfer_setpoint: float | None = power_transfer_setpoint
        self.current_transfer_setpoint: float | None = current_transfer_setpoint
        self.scheduled_dc_voltage: float = scheduled_dc_voltage
        self.rectifier_bridges: int = rectifier_bridges
        self.rectifier_delay_angle_limits: SiennaMinMax = rectifier_delay_angle_limits
        self.rectifier_rc: float = rectifier_rc
        self.rectifier_xc: float = rectifier_xc
        self.rectifier_base_voltage: float = rectifier_base_voltage
        self.inverter_bridges: int = inverter_bridges
        self.inverter_extinction_angle_limits: SiennaMinMax = inverter_extinction_angle_limits
        self.inverter_rc: float = inverter_rc
        self.inverter_xc: float = inverter_xc
        self.inverter_base_voltage: float = inverter_base_voltage
        self.control_mode: SiennaLCCControlMode = control_mode
        self.switch_mode_voltage: float = switch_mode_voltage
        self.compounding_resistance: float = compounding_resistance
        self.min_compounding_voltage: float = min_compounding_voltage
        self.rectifier_transformer_ratio: float = rectifier_transformer_ratio
        self.rectifier_tap_setting: float = rectifier_tap_setting
        self.rectifier_tap_limits: SiennaMinMax = rectifier_tap_limits
        self.rectifier_tap_step: float = rectifier_tap_step
        self.rectifier_delay_angle: float = rectifier_delay_angle
        self.rectifier_capacitor_reactance: float = rectifier_capacitor_reactance
        self.inverter_transformer_ratio: float = inverter_transformer_ratio
        self.inverter_tap_setting: float = inverter_tap_setting
        self.inverter_tap_limits: SiennaMinMax = inverter_tap_limits
        self.inverter_tap_step: float = inverter_tap_step
        self.inverter_extinction_angle: float = inverter_extinction_angle
        self.inverter_capacitor_reactance: float = inverter_capacitor_reactance
        self.rating: float = rating
        self.rating_from: float = rating_from
        self.rating_to: float = rating_to
        self.operational_flow_limit: SiennaOperationalFlowLimit = operational_flow_limit
        self.reactive_power_limits_from: SiennaMinMax = reactive_power_limits_from
        self.reactive_power_limits_to: SiennaMinMax = reactive_power_limits_to
        self.loss: SiennaLossCurve = loss
        self.base_power: float = base_power
        self.power_units: SiennaUnitSystem = power_units


def parse_sienna_two_terminal_lcc_line(data: dict[str, Any]) -> SiennaTwoTerminalLCCLine:
    """Parse declared TwoTerminalLCCLine properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed TwoTerminalLCCLine object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import parse_sienna_loss_curve
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import parse_sienna_operational_flow_limit
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    from VeraGridEngine.IO.sienna.devices.operations.common.lcc_control_mode import parse_sienna_lcc_control_mode
    return SiennaTwoTerminalLCCLine(id=get_required_value(data, 'id', 'TwoTerminalLCCLine'), name=get_required_value(data, 'name', 'TwoTerminalLCCLine'), available=get_required_value(data, 'available', 'TwoTerminalLCCLine'), arc=get_required_value(data, 'arc', 'TwoTerminalLCCLine'), active_power_flow=get_required_value(data, 'active_power_flow', 'TwoTerminalLCCLine'), r=get_required_value(data, 'r', 'TwoTerminalLCCLine'), power_transfer_setpoint=data.get('power_transfer_setpoint', None), current_transfer_setpoint=data.get('current_transfer_setpoint', None), scheduled_dc_voltage=get_required_value(data, 'scheduled_dc_voltage', 'TwoTerminalLCCLine'), rectifier_bridges=get_required_value(data, 'rectifier_bridges', 'TwoTerminalLCCLine'), rectifier_delay_angle_limits=parse_sienna_min_max(get_required_value(data, 'rectifier_delay_angle_limits', 'TwoTerminalLCCLine')), rectifier_rc=get_required_value(data, 'rectifier_rc', 'TwoTerminalLCCLine'), rectifier_xc=get_required_value(data, 'rectifier_xc', 'TwoTerminalLCCLine'), rectifier_base_voltage=get_required_value(data, 'rectifier_base_voltage', 'TwoTerminalLCCLine'), inverter_bridges=get_required_value(data, 'inverter_bridges', 'TwoTerminalLCCLine'), inverter_extinction_angle_limits=parse_sienna_min_max(get_required_value(data, 'inverter_extinction_angle_limits', 'TwoTerminalLCCLine')), inverter_rc=get_required_value(data, 'inverter_rc', 'TwoTerminalLCCLine'), inverter_xc=get_required_value(data, 'inverter_xc', 'TwoTerminalLCCLine'), inverter_base_voltage=get_required_value(data, 'inverter_base_voltage', 'TwoTerminalLCCLine'), control_mode=None if data.get('control_mode', None) is None else parse_sienna_lcc_control_mode(data.get('control_mode', None)), switch_mode_voltage=data.get('switch_mode_voltage', None), compounding_resistance=data.get('compounding_resistance', None), min_compounding_voltage=data.get('min_compounding_voltage', None), rectifier_transformer_ratio=data.get('rectifier_transformer_ratio', None), rectifier_tap_setting=data.get('rectifier_tap_setting', None), rectifier_tap_limits=None if data.get('rectifier_tap_limits', None) is None else parse_sienna_min_max(data.get('rectifier_tap_limits', None)), rectifier_tap_step=data.get('rectifier_tap_step', None), rectifier_delay_angle=data.get('rectifier_delay_angle', None), rectifier_capacitor_reactance=data.get('rectifier_capacitor_reactance', None), inverter_transformer_ratio=data.get('inverter_transformer_ratio', None), inverter_tap_setting=data.get('inverter_tap_setting', None), inverter_tap_limits=None if data.get('inverter_tap_limits', None) is None else parse_sienna_min_max(data.get('inverter_tap_limits', None)), inverter_tap_step=data.get('inverter_tap_step', None), inverter_extinction_angle=data.get('inverter_extinction_angle', None), inverter_capacitor_reactance=data.get('inverter_capacitor_reactance', None), rating=get_required_value(data, 'rating', 'TwoTerminalLCCLine'), rating_from=data.get('rating_from', None), rating_to=data.get('rating_to', None), operational_flow_limit=None if data.get('operational_flow_limit', None) is None else parse_sienna_operational_flow_limit(data.get('operational_flow_limit', None)), reactive_power_limits_from=None if data.get('reactive_power_limits_from', None) is None else parse_sienna_min_max(data.get('reactive_power_limits_from', None)), reactive_power_limits_to=None if data.get('reactive_power_limits_to', None) is None else parse_sienna_min_max(data.get('reactive_power_limits_to', None)), loss=None if data.get('loss', None) is None else parse_sienna_loss_curve(data.get('loss', None)), base_power=get_required_value(data, 'base_power', 'TwoTerminalLCCLine'), power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'TwoTerminalLCCLine')))

def sienna_two_terminal_lcc_line_to_json(value: SiennaTwoTerminalLCCLine) -> dict[str, Any]:
    """Write every TwoTerminalLCCLine slot to explicit schema property names.

    :param value: Typed TwoTerminalLCCLine object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.loss_curve import sienna_loss_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.operational_flow_limit import sienna_operational_flow_limit_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    from VeraGridEngine.IO.sienna.devices.operations.common.lcc_control_mode import sienna_lcc_control_mode_to_json
    return {'id': value.id, 'name': value.name, 'available': value.available, 'arc': value.arc, 'active_power_flow': value.active_power_flow, 'r': value.r, 'power_transfer_setpoint': value.power_transfer_setpoint, 'current_transfer_setpoint': value.current_transfer_setpoint, 'scheduled_dc_voltage': value.scheduled_dc_voltage, 'rectifier_bridges': value.rectifier_bridges, 'rectifier_delay_angle_limits': sienna_min_max_to_json(value.rectifier_delay_angle_limits), 'rectifier_rc': value.rectifier_rc, 'rectifier_xc': value.rectifier_xc, 'rectifier_base_voltage': value.rectifier_base_voltage, 'inverter_bridges': value.inverter_bridges, 'inverter_extinction_angle_limits': sienna_min_max_to_json(value.inverter_extinction_angle_limits), 'inverter_rc': value.inverter_rc, 'inverter_xc': value.inverter_xc, 'inverter_base_voltage': value.inverter_base_voltage, 'control_mode': None if value.control_mode is None else sienna_lcc_control_mode_to_json(value.control_mode), 'switch_mode_voltage': value.switch_mode_voltage, 'compounding_resistance': value.compounding_resistance, 'min_compounding_voltage': value.min_compounding_voltage, 'rectifier_transformer_ratio': value.rectifier_transformer_ratio, 'rectifier_tap_setting': value.rectifier_tap_setting, 'rectifier_tap_limits': None if value.rectifier_tap_limits is None else sienna_min_max_to_json(value.rectifier_tap_limits), 'rectifier_tap_step': value.rectifier_tap_step, 'rectifier_delay_angle': value.rectifier_delay_angle, 'rectifier_capacitor_reactance': value.rectifier_capacitor_reactance, 'inverter_transformer_ratio': value.inverter_transformer_ratio, 'inverter_tap_setting': value.inverter_tap_setting, 'inverter_tap_limits': None if value.inverter_tap_limits is None else sienna_min_max_to_json(value.inverter_tap_limits), 'inverter_tap_step': value.inverter_tap_step, 'inverter_extinction_angle': value.inverter_extinction_angle, 'inverter_capacitor_reactance': value.inverter_capacitor_reactance, 'rating': value.rating, 'rating_from': value.rating_from, 'rating_to': value.rating_to, 'operational_flow_limit': None if value.operational_flow_limit is None else sienna_operational_flow_limit_to_json(value.operational_flow_limit), 'reactive_power_limits_from': None if value.reactive_power_limits_from is None else sienna_min_max_to_json(value.reactive_power_limits_from), 'reactive_power_limits_to': None if value.reactive_power_limits_to is None else sienna_min_max_to_json(value.reactive_power_limits_to), 'loss': None if value.loss is None else sienna_loss_curve_to_json(value.loss), 'base_power': value.base_power, 'power_units': sienna_unit_system_to_json(value.power_units)}
