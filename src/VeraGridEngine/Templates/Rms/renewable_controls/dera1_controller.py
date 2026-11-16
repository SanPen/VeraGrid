# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Assemble the source DERA1 active/reactive converter control chain."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_active_power import (
    Dera1ActivePowerSettings,
    build_dera1_active_power_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_current_limit import (
    build_dera1_current_limit_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_inner_current_loop import (
    Dera1InnerCurrentLoopSettings,
    build_dera1_inner_current_loop_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_protection import (
    Dera1ProtectionSettings,
    build_dera1_protection_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_reactive_current import (
    Dera1ReactiveCurrentSettings,
    build_dera1_reactive_current_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_voltage_measurement import (
    Dera1VoltageMeasurementSettings,
    build_dera1_voltage_measurement_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicBase
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def _merge_component(
        host: Block,
        component: Block,
        input_mapping: dict[Var, Expr],
) -> None:
    """Merge one component's equations and remapped procedural logic.

    :param host: DERA1 root block receiving the component.
    :param component: Complete component block being connected.
    :param input_mapping: Open component inputs replaced by host signals.
    :return: None.
    """
    host.state_vars.extend(component.state_vars)
    host.diff_vars.extend(component.diff_vars)
    host.algebraic_vars.extend(component.algebraic_vars)
    equation: Expr
    for equation in component.state_eqs:
        host.state_eqs.append(equation.subs(input_mapping))
    for equation in component.algebraic_eqs:
        host.algebraic_eqs.append(equation.subs(input_mapping))
    variable: Var
    expression: Expr
    for variable, expression in component.init_eqs.items():
        if variable in input_mapping:
            pass
        else:
            host.init_eqs[variable] = expression.subs(input_mapping)
    host.event_dict.update(component.event_dict)
    host.mode_dict.update(component.mode_dict)
    logic: ProceduralLogicBase
    for logic in component.procedural_logic:
        host.procedural_logic.append(logic.remap(input_mapping))


def build_dera1_controller_template(
        vf: VarFactory,
        name: str = 'DERA1 controller',
        active_settings: Dera1ActivePowerSettings | None = None,
        reactive_settings: Dera1ReactiveCurrentSettings | None = None,
        inner_current_settings: Dera1InnerCurrentLoopSettings | None = None,
        protection_settings: Dera1ProtectionSettings | None = None,
        voltage_settings: Dera1VoltageMeasurementSettings | None = None,
        imax: float = 1.0,
        active_current_priority: bool = False,
        generator: bool = True,
) -> RmsModelTemplate:
    """Build the connected DERA1 current-control template through Id/Iq.

    The block exposes per-unit frequency deviation for active-power control
    and hertz for the source frequency relay. A system importer supplies both
    from the same solved/network frequency measurement.

    :param vf: Shared symbolic variable factory.
    :param name: Unique generator-template name.
    :param active_settings: Frequency and active-power control parameters.
    :param reactive_settings: Q/PF and voltage-support parameters.
    :param inner_current_settings: Tg and rrpwr parameters.
    :param protection_settings: Voltage/frequency relay parameters.
    :param voltage_settings: Trv measurement parameter.
    :param imax: PSS/E maximum converter current.
    :param active_current_priority: True selects P priority.
    :param generator: True restricts active current to generation.
    :return: Connected current-source controller with Id and Iq outputs.
    """
    active: Dera1ActivePowerSettings = (
        Dera1ActivePowerSettings() if active_settings is None else active_settings
    )
    reactive: Dera1ReactiveCurrentSettings = (
        Dera1ReactiveCurrentSettings() if reactive_settings is None else reactive_settings
    )
    inner: Dera1InnerCurrentLoopSettings = (
        Dera1InnerCurrentLoopSettings() if inner_current_settings is None
        else inner_current_settings
    )
    protection: Dera1ProtectionSettings = (
        Dera1ProtectionSettings() if protection_settings is None
        else protection_settings
    )
    voltage_measurement: Dera1VoltageMeasurementSettings = (
        Dera1VoltageMeasurementSettings() if voltage_settings is None
        else voltage_settings
    )
    control: ControlRealization = ControlRealization(vf, name)
    terminal_voltage: Var = control.input(
        'TerminalVoltageMagnitudePu', Const(voltage_measurement.initial_voltage),
    )
    frequency_deviation: Var = control.input(
        'FrequencyDeviationPu', Const(active.initial_frequency_deviation),
    )
    frequency_hz: Var = control.input(
        'SystemFrequencyHz', Const(protection.initial_frequency_hz),
    )
    active_reference: Var = control.input(
        'ActivePowerReferencePu', Const(active.initial_active_power),
    )
    reactive_reference: Var = control.input(
        'ReactivePowerReferencePu', Const(reactive.initial_reactive_power),
    )

    measurement: Block = build_dera1_voltage_measurement_template(
        vf, name + ' voltage measurement', voltage_measurement,
    ).block
    _merge_component(
        control.block, measurement,
        dict(((measurement.in_vars[0], terminal_voltage),)),
    )
    filtered_voltage: Var = measurement.out_vars[0]

    active_block: Block = build_dera1_active_power_template(
        vf, name + ' active power', active,
    ).block
    _merge_component(
        control.block, active_block,
        dict(((active_block.in_vars[0], frequency_deviation),
              (active_block.in_vars[1], active_reference))),
    )
    active_order: Var = active_block.out_vars[0]

    reactive_block: Block = build_dera1_reactive_current_template(
        vf, name + ' reactive current', reactive,
    ).block
    _merge_component(
        control.block, reactive_block,
        dict(((reactive_block.in_vars[0], filtered_voltage),
              (reactive_block.in_vars[1], active_order),
              (reactive_block.in_vars[2], reactive_reference))),
    )
    reactive_command: Var = reactive_block.out_vars[0]

    current_limit: Block = build_dera1_current_limit_template(
        vf, name + ' current limits', imax, active_current_priority, generator,
    ).block
    active_current_command: Expr = active_order / sym.max(filtered_voltage, Const(0.01))
    _merge_component(
        control.block, current_limit,
        dict(((current_limit.in_vars[0], active_current_command),
              (current_limit.in_vars[1], reactive_command))),
    )

    protection_block: Block = build_dera1_protection_template(
        vf, name + ' protection', protection,
    ).block
    _merge_component(
        control.block, protection_block,
        dict(((protection_block.in_vars[0], filtered_voltage),
              (protection_block.in_vars[1], frequency_hz))),
    )
    trip_multiplier: Var = protection_block.out_vars[2]

    current_loop: Block = build_dera1_inner_current_loop_template(
        vf, name + ' current loops', inner,
    ).block
    _merge_component(
        control.block, current_loop,
        dict(((current_loop.in_vars[0], current_limit.out_vars[0]),
              (current_loop.in_vars[1], current_limit.out_vars[1]),
              (current_loop.in_vars[2], trip_multiplier))),
    )
    template: RmsModelTemplate = control.finish(
        (current_loop.out_vars[0], current_loop.out_vars[1]),
        'PSS/E DERA1 connected current-source control chain through Id/Iq',
    )
    return template
