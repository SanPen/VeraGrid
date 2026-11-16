# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Connected AC9C bridge, power-stage, feedback and exciter section."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_field_feedback import (
    Ac9cFieldFeedbackSettings,
    build_ac9c_field_feedback_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_bridge import (
    Ac9cRectifierBridgeSettings,
    build_ac9c_rectifier_bridge_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_freewheel_voltage import (
    Ac9cFreewheelVoltageSettings,
    build_ac9c_freewheel_voltage_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_stage import (
    Ac9cPowerStageType,
    build_ac9c_power_stage_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rotating_exciter import (
    Ac9cRotatingExciterSettings,
    build_ac9c_rotating_exciter_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
from VeraGridEngine.enumerations import DeviceType


def substitute_component_input(block: Block, port: Var, signal: Expr) -> None:
    """Replace one open component port throughout its native equations.

    :param block: Component block owning the open port.
    :param port: Input variable to connect and remove from its open ports.
    :param signal: Connected signal expression.
    :return: None.
    """
    substitution: dict[Var, Expr] = dict(((port, signal),))
    block.state_eqs = [equation.subs(substitution) for equation in block.state_eqs]
    block.algebraic_eqs = [equation.subs(substitution) for equation in block.algebraic_eqs]
    block.inequalities = [equation.subs(substitution) for equation in block.inequalities]
    block.event_dict = dict(
        (parameter, expression.subs(substitution))
        for parameter, expression in block.event_dict.items()
    )
    block.mode_dict = dict(
        (variable, expression.subs(substitution))
        for variable, expression in block.mode_dict.items()
    )
    block.init_eqs = dict(
        (variable, expression.subs(substitution))
        for variable, expression in block.init_eqs.items()
        if variable != port
    )
    block.diff_init_eqs = dict(
        (variable, expression.subs(substitution))
        for variable, expression in block.diff_init_eqs.items()
    )
    block.post_init_seed_eqs = dict(
        (variable, expression.subs(substitution))
        for variable, expression in block.post_init_seed_eqs.items()
    )
    block.in_vars.remove(port)


def build_ac9c_power_exciter_template(
        vf: VarFactory,
        name: str = 'AC9C power and rotating exciter',
        stage_type: Ac9cPowerStageType = Ac9cPowerStageType.THYRISTOR_BRIDGE,
        vlim1: float = 0.0,
        vlim2: float = -0.1,
        field_feedback_settings: Ac9cFieldFeedbackSettings | None = None,
        freewheel_settings: Ac9cFreewheelVoltageSettings | None = None,
        exciter_settings: Ac9cRotatingExciterSettings | None = None,
        bridge_settings: Ac9cRectifierBridgeSettings | None = None,
) -> RmsModelTemplate:
    """Connect AC9C's freewheel path, selector and rotating exciter.

    ``VFE`` feeds ``KF/(1+s*TF)``; its output feeds KFW and the selected
    freewheel voltage feeds the power-stage selector. The controlled bridge
    output ``VA`` is added to selected power-stage output ``VR`` before the
    rotating exciter; its field feedback ``VFE`` is subtracted inside the
    exciter equation. ``VCT`` and
    ``VAVR`` remain host inputs because the potential-source network and
    current-regulator gate routing are separate source functions.

    :param vf: Shared symbol factory for the connected components.
    :param name: Unique composition label.
    :param stage_type: PSS/E thyristor or chopper selector.
    :param vlim1: Upper chopper threshold.
    :param vlim2: Lower chopper threshold.
    :param field_feedback_settings: KF/TF filter values and initial point.
    :param freewheel_settings: KFW and VFW limits/initial point.
    :param exciter_settings: Rotating-field parameters and initial point.
    :param bridge_settings: Controlled-bridge values and initial point.
    :return: Connected partial AC9C template with field-voltage output.
    """
    feedback_template: RmsModelTemplate = build_ac9c_field_feedback_template(
        vf, name + ' field feedback', field_feedback_settings,
    )
    freewheel_template: RmsModelTemplate = build_ac9c_freewheel_voltage_template(
        vf, name + ' freewheel voltage', freewheel_settings,
    )
    stage_template: RmsModelTemplate = build_ac9c_power_stage_template(
        vf, name + ' power stage', stage_type, vlim1, vlim2,
    )
    exciter_template: RmsModelTemplate = build_ac9c_rotating_exciter_template(
        vf, name + ' rotating exciter', exciter_settings,
    )
    bridge_template: RmsModelTemplate = build_ac9c_rectifier_bridge_template(
        vf, name + ' controlled bridge', bridge_settings,
    )
    feedback_block: Block = feedback_template.block
    freewheel_block: Block = freewheel_template.block
    stage_block: Block = stage_template.block
    exciter_block: Block = exciter_template.block
    bridge_block: Block = bridge_template.block

    vfe: Var = exciter_block.out_vars[1]
    filtered_feedback: Var = feedback_block.out_vars[0]
    freewheel_voltage: Var = freewheel_block.out_vars[0]
    amplifier_voltage: Var = bridge_block.out_vars[0]
    rectifier_voltage: Var = stage_block.out_vars[0]
    efe_input: Var = exciter_block.in_vars[0]
    substitute_component_input(feedback_block, feedback_block.in_vars[0], vfe)
    substitute_component_input(freewheel_block, freewheel_block.in_vars[0], filtered_feedback)
    substitute_component_input(stage_block, stage_block.in_vars[1], freewheel_voltage)
    substitute_component_input(bridge_block, bridge_block.in_vars[0], stage_block.in_vars[1])
    substitute_component_input(exciter_block, efe_input, rectifier_voltage + amplifier_voltage)

    vct_input: Var = stage_block.in_vars[0]
    vavr_input: Var = stage_block.in_vars[1]
    ifd_input: Var = exciter_block.in_vars[0]
    root: Block = Block(name=name)
    root.children = list((stage_block, bridge_block, exciter_block,
                          feedback_block, freewheel_block))
    root.in_vars = list((vct_input, vavr_input, ifd_input))
    root.out_vars = list((exciter_block.out_vars[0], vfe, filtered_feedback,
                          freewheel_voltage, amplifier_voltage, rectifier_voltage,
                          exciter_block.out_vars[2]))
    root.unify_blocks()
    root.in_vars = list((vct_input, vavr_input, ifd_input))
    root.out_vars = list((exciter_block.out_vars[0], vfe, filtered_feedback,
                          freewheel_voltage, amplifier_voltage, rectifier_voltage,
                          exciter_block.out_vars[2]))

    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.NoDevice
    template.block = root
    template.comment = 'Connected AC9C bridge and power-stage/exciter section; potential-source and gate signals remain host inputs'
    return template
