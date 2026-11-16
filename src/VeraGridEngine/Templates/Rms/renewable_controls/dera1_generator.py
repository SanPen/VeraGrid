# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Physical generator boundary for the assembled PSS/E DERA1 controller."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.current_source_host import (
    build_renewable_current_source_host,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_active_power import (
    Dera1ActivePowerSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_controller import (
    build_dera1_controller_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_inner_current_loop import (
    Dera1InnerCurrentLoopSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_protection import (
    Dera1ProtectionSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_reactive_current import (
    Dera1ReactiveCurrentSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_voltage_measurement import (
    Dera1VoltageMeasurementSettings,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import WrappedDerivativeLogic
from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowReferenceType,
    RmsProblemTypes,
    VarPowerFlowReferenceType,
)


def build_dera1_generator_template(
        vf: VarFactory,
        name: str = 'DERA1 generator',
        active_settings: Dera1ActivePowerSettings | None = None,
        reactive_settings: Dera1ReactiveCurrentSettings | None = None,
        inner_current_settings: Dera1InnerCurrentLoopSettings | None = None,
        protection_settings: Dera1ProtectionSettings | None = None,
        voltage_settings: Dera1VoltageMeasurementSettings | None = None,
        imax: float = 1.0,
        active_current_priority: bool = False,
        generator: bool = True,
        problem_type: RmsProblemTypes = RmsProblemTypes.PowerBalanceVectorized,
) -> RmsModelTemplate:
    """Build a network-connected DERA1 generator and current-control chain.

    Bus frequency is estimated from the wrapped derivative of the voltage
    angle at accepted RMS boundaries. The estimate drives both the DERA1 pu
    active-power path and its hertz relay input.

    :param vf: Shared symbolic variable factory.
    :param name: Unique generator-template name.
    :param active_settings: Frequency and active-power control parameters.
    :param reactive_settings: Q/PF and voltage-support parameters.
    :param inner_current_settings: Tg and rrpwr parameters.
    :param protection_settings: Voltage/frequency relay parameters.
    :param voltage_settings: Trv measurement parameter.
    :param imax: Maximum converter current in pu.
    :param active_current_priority: True selects P priority.
    :param generator: True clips active power to generation.
    :param problem_type: RMS network formulation.
    :return: Generator-device template with physical P/Q and Id/Iq boundaries.
    """
    selected_active: Dera1ActivePowerSettings = (
        Dera1ActivePowerSettings() if active_settings is None else active_settings
    )
    selected_protection: Dera1ProtectionSettings = (
        Dera1ProtectionSettings() if protection_settings is None
        else protection_settings
    )
    template: RmsModelTemplate = build_renewable_current_source_host(
        vf=vf, name=name, problem_type=problem_type,
    )
    block: Block = template.block
    angle: Var = vf.add_var(
        'BusVoltageAngle_' + name, reference=VarPowerFlowReferenceType.Va,
    )
    block.in_vars.append(angle)
    block.external_mapping[VarPowerFlowReferenceType.Va] = angle
    frequency_base: Var = vf.add_var('FrequencyBaseHz_' + name)
    angular_frequency_base: Var = vf.add_var('AngularFrequencyBase_' + name)
    block.parameters[frequency_base] = vf.add_const(value=None, name=frequency_base.name)
    block.parameters[angular_frequency_base] = vf.add_const(value=None, name=angular_frequency_base.name)
    block.api_obj_mapping[ParamPowerFlowReferenceType.freq] = frequency_base
    block.api_obj_mapping[ParamPowerFlowReferenceType.omega_base] = angular_frequency_base
    angle_rate: Var = vf.add_var('BusAngularFrequencyDeviation_' + name)
    block.event_dict[angle_rate] = Const(0.0)
    block.procedural_logic.append(WrappedDerivativeLogic(
        output_var_name=angle_rate.name,
        source_expr=angle,
        maximum_rate_expr=None,
        name=name + ' bus-frequency measurement',
    ))
    block.init_eqs[angle_rate] = Const(0.0)

    machine_to_system_base: Expr = (
        block.api_obj_mapping[ParamPowerFlowReferenceType.generator_snom_mva]
        / block.api_obj_mapping[ParamPowerFlowReferenceType.Sbase]
    )
    active_reference: Var = vf.add_var('ActivePowerReferencePu_' + name)
    reactive_reference: Var = vf.add_var('ReactivePowerReferencePu_' + name)
    block.event_dict[active_reference] = (
        block.external_mapping[VarPowerFlowReferenceType.P] / machine_to_system_base
    )
    block.event_dict[reactive_reference] = (
        block.external_mapping[VarPowerFlowReferenceType.Q] / machine_to_system_base
    )
    frequency_deviation_pu: Expr = angle_rate / block.api_obj_mapping[
        ParamPowerFlowReferenceType.omega_base
    ]
    frequency_hz: Expr = (
        block.api_obj_mapping[ParamPowerFlowReferenceType.freq]
        + angle_rate / Const(2.0 * 3.141592653589793)
    )
    if problem_type in (RmsProblemTypes.CurrentBalance, RmsProblemTypes.Multilinear):
        voltage: Expr = (
            block.external_mapping[VarPowerFlowReferenceType.Vr] ** Const(2.0)
            + block.external_mapping[VarPowerFlowReferenceType.Vi] ** Const(2.0)
        ) ** Const(0.5)
    else:
        voltage = block.external_mapping[VarPowerFlowReferenceType.Vm]

    active_current_order: Var = next(
        parameter for parameter in block.event_dict
        if parameter.name.startswith('IpCommand_')
    )
    reactive_current_order: Var = next(
        parameter for parameter in block.event_dict
        if parameter.name.startswith('IqCommand_')
    )
    controller_template: RmsModelTemplate = build_dera1_controller_template(
        vf=vf,
        name=name + ' control',
        active_settings=selected_active,
        reactive_settings=reactive_settings,
        inner_current_settings=inner_current_settings,
        protection_settings=selected_protection,
        voltage_settings=voltage_settings,
        imax=imax,
        active_current_priority=active_current_priority,
        generator=generator,
    )
    controller: Block = controller_template.block
    block.state_vars.extend(controller.state_vars)
    block.diff_vars.extend(controller.diff_vars)
    controller_mapping: dict[Var, Var] = dict((
        (controller.in_vars[0], voltage),
        (controller.in_vars[1], frequency_deviation_pu),
        (controller.in_vars[2], frequency_hz),
        (controller.in_vars[3], active_reference),
        (controller.in_vars[4], reactive_reference),
    ))
    controller_equation: Expr
    for controller_equation in controller.state_eqs:
        block.state_eqs.append(controller_equation.subs(controller_mapping))
    for controller_equation in controller.algebraic_eqs:
        block.algebraic_eqs.append(controller_equation.subs(controller_mapping))
    controller_signal: Var
    for controller_signal in controller.state_vars:
        block.init_eqs[controller_signal] = controller.init_eqs[controller_signal].subs(controller_mapping)
    for controller_signal in controller.algebraic_vars:
        if controller_signal in controller.init_eqs:
            controller_initial: Expr | Const = controller.init_eqs[controller_signal]
            block.init_eqs[controller_signal] = controller_initial.subs(controller_mapping)
        else:
            pass
    block.event_dict.pop(active_current_order)
    block.event_dict.pop(reactive_current_order)
    block.event_dict.update(controller.event_dict)
    block.mode_dict.update(controller.mode_dict)
    for logic in controller.procedural_logic:
        block.procedural_logic.append(logic.remap(controller_mapping))
    active_output: Var = controller.out_vars[0]
    reactive_output: Var = controller.out_vars[1]
    block.algebraic_eqs[0] = block.out_vars[2] - active_output
    block.algebraic_eqs[1] = block.out_vars[3] - reactive_output
    template.tpe = DeviceType.GeneratorDevice
    template.comment = (
        'PSS/E DERA1 generator current-source model with wrapped bus-frequency measurement'
    )
    return template
