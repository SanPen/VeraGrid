# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Connected AC9C regulator, source channels and power-stage path."""
from __future__ import annotations

from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_current_regulator import (
    Ac9cCurrentRegulatorSettings,
    build_ac9c_current_regulator_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_field_feedback import (
    Ac9cFieldFeedbackSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_freewheel_voltage import (
    Ac9cFreewheelVoltageSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_pid import (
    Ac9cPidSettings,
    build_ac9c_pid_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_exciter import (
    substitute_component_input,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_exciter import (
    build_ac9c_power_exciter_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_stage import (
    Ac9cPowerStageType,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_potential_source import (
    Ac9cPotentialSourceSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_bridge import (
    Ac9cRectifierBridgeSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_sources import (
    Ac9cPotentialSourceSelection,
    build_ac9c_rectifier_sources_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_supply import (
    Ac9cRectifierSupplySettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rotating_exciter import (
    Ac9cRotatingExciterSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_voltage_transducer import (
    build_ac9c_voltage_transducer_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import DeviceType


class Ac9cLimiterLocation(Enum):
    """Select the documented summation-point or downstream limiter gate."""

    SUMMATION_POINT = 1
    DOWNSTREAM_GATE = 2


def build_ac9c_controller_template(
        vf: VarFactory,
        name: str | None = None,
        tr: float = 0.01,
        sensed_voltage0: float = 1.0,
        pid_settings: Ac9cPidSettings | None = None,
        current_settings: Ac9cCurrentRegulatorSettings | None = None,
        bridge_settings: Ac9cRectifierBridgeSettings | None = None,
        field_feedback_settings: Ac9cFieldFeedbackSettings | None = None,
        freewheel_settings: Ac9cFreewheelVoltageSettings | None = None,
        exciter_settings: Ac9cRotatingExciterSettings | None = None,
        potential_source_settings: Ac9cPotentialSourceSettings | None = None,
        channel1_settings: Ac9cRectifierSupplySettings | None = None,
        channel2_settings: Ac9cRectifierSupplySettings | None = None,
        source_selection: Ac9cPotentialSourceSelection = Ac9cPotentialSourceSelection.TERMINAL_FED,
        stage_type: Ac9cPowerStageType = Ac9cPowerStageType.THYRISTOR_BRIDGE,
        oel_location: Ac9cLimiterLocation = Ac9cLimiterLocation.SUMMATION_POINT,
        uel_location: Ac9cLimiterLocation = Ac9cLimiterLocation.SUMMATION_POINT,
        vlim1: float = 0.0,
        vlim2: float = -0.1,
) -> RmsModelTemplate:
    """Build the sourced AC9C regulator with internal OEL/UEL location gates.

    Position (a) sums each limiter signal with the voltage error. Position (b)
    routes UEL through a high-value gate and OEL through a low-value gate after
    the PID and filtered field-current feedback. The resulting signal drives
    the field-current PI. The bridge ``VA`` and selector ``VR`` remain distinct
    outputs, as required by the source states.

    :param vf: Symbol factory shared by every child component.
    :param name: Unique composition label.
    :param tr: Terminal-voltage transducer time constant.
    :param sensed_voltage0: Solved initial sensed terminal voltage.
    :param pid_settings: PID gains, limits and initial values.
    :param current_settings: Field-current PI settings.
    :param bridge_settings: Controlled-bridge settings.
    :param field_feedback_settings: Exciter field-feedback settings.
    :param freewheel_settings: Freewheel limiter settings.
    :param exciter_settings: Rotating-exciter settings.
    :param potential_source_settings: Terminal/current-source coefficients.
    :param channel1_settings: First rectifier-channel settings.
    :param channel2_settings: Second rectifier-channel settings.
    :param source_selection: PSS/E SW1 source A/B choice.
    :param stage_type: Thyristor or chopper power-stage selection.
    :param oel_location: PSS/E OEL ICON position (a) or (b).
    :param uel_location: PSS/E UEL ICON position (a) or (b).
    :param vlim1: Upper chopper threshold.
    :param vlim2: Lower chopper threshold.
    :return: Connected seven-state AC9C regulator and excitation path.
    :raises ValueError: A limiter location is not a supported selector.
    """
    label: str = 'AC9C controller' if name is None else name
    if (not isinstance(oel_location, Ac9cLimiterLocation)
            or not isinstance(uel_location, Ac9cLimiterLocation)):
        raise ValueError('AC9C limiter locations must be supported selectors')
    else:
        pass

    transducer_template: RmsModelTemplate = build_ac9c_voltage_transducer_template(
        vf, label + ' voltage transducer', tr, sensed_voltage0,
    )
    pid_template: RmsModelTemplate = build_ac9c_pid_template(
        vf, label + ' PID', pid_settings,
    )
    current_template: RmsModelTemplate = build_ac9c_current_regulator_template(
        vf, label + ' field-current PI', current_settings,
    )
    source_template: RmsModelTemplate = build_ac9c_rectifier_sources_template(
        vf, label + ' rectifier sources', source_selection, potential_source_settings,
        channel1_settings, channel2_settings,
    )
    power_template: RmsModelTemplate = build_ac9c_power_exciter_template(
        vf=vf,
        name=label + ' power and exciter',
        stage_type=stage_type,
        vlim1=vlim1,
        vlim2=vlim2,
        field_feedback_settings=field_feedback_settings,
        freewheel_settings=freewheel_settings,
        exciter_settings=exciter_settings,
        bridge_settings=bridge_settings,
    )
    transducer_block: Block = transducer_template.block
    pid_block: Block = pid_template.block
    current_block: Block = current_template.block
    source_block: Block = source_template.block
    power_block: Block = power_template.block

    sensed_voltage: Var = transducer_block.out_vars[0]
    voltage_reference: Var = vf.add_var('VoltageReferencePu_' + label)
    voltage_bias: Var = vf.add_var('VoltageErrorBiasPu_' + label)
    overexcitation: Var = vf.add_var('OelInputPu_' + label)
    underexcitation: Var = vf.add_var('UelInputPu_' + label)
    voltage_error: Var = pid_block.in_vars[0]
    pid_error: Var = voltage_reference - sensed_voltage + voltage_bias
    if oel_location is Ac9cLimiterLocation.SUMMATION_POINT:
        pid_error += overexcitation
    else:
        pass
    if uel_location is Ac9cLimiterLocation.SUMMATION_POINT:
        pid_error += underexcitation
    else:
        pass
    substitute_component_input(
        pid_block, voltage_error, pid_error,
    )

    gated_error: Var = current_block.in_vars[0]
    vavr: Var = current_block.out_vars[0]
    potential_voltage: Var = power_block.in_vars[0]
    power_vavr_input: Var = power_block.in_vars[1]
    field_current: Var = power_block.in_vars[2]
    field_feedback: Var = power_block.out_vars[2]
    source_exciter_voltage: Var = source_block.in_vars[4]
    substitute_component_input(power_block, potential_voltage, source_block.out_vars[0])
    substitute_component_input(source_block, source_exciter_voltage, power_block.out_vars[6])
    substitute_component_input(power_block, power_vavr_input, vavr)

    takeover_error: Expr = pid_block.out_vars[0] - field_feedback
    if uel_location is Ac9cLimiterLocation.DOWNSTREAM_GATE:
        takeover_error = sym.max(takeover_error, underexcitation)
    else:
        pass
    if oel_location is Ac9cLimiterLocation.DOWNSTREAM_GATE:
        takeover_error = sym.min(takeover_error, overexcitation)
    else:
        pass
    substitute_component_input(current_block, gated_error, takeover_error)

    root: Block = Block(name=label)
    root.children = list((transducer_block, pid_block, current_block, source_block, power_block))
    root.in_vars = (list((transducer_block.in_vars[0], voltage_reference, voltage_bias,
                          overexcitation, underexcitation))
                    + list(source_block.in_vars) + [field_current])
    root.out_vars = list((pid_block.out_vars[0], vavr, power_block.out_vars[0],
                          power_block.out_vars[1], power_block.out_vars[2],
                          power_block.out_vars[3], power_block.out_vars[4],
                          power_block.out_vars[5]))
    root.unify_blocks()
    root.in_vars = (list((transducer_block.in_vars[0], voltage_reference, voltage_bias,
                          overexcitation, underexcitation))
                    + list(source_block.in_vars) + [field_current])
    root.out_vars = list((pid_block.out_vars[0], vavr, power_block.out_vars[0],
                          power_block.out_vars[1], power_block.out_vars[2],
                          power_block.out_vars[3], power_block.out_vars[4],
                          power_block.out_vars[5]))

    template: RmsModelTemplate = RmsModelTemplate(name=label)
    template.tpe = DeviceType.NoDevice
    template.block = root
    template.comment = 'AC9C seven-state voltage/current control with limiter gates and dual potential-source network'
    return template
