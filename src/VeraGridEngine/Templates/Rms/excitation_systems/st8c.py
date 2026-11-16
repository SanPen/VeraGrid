# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E ST8C static excitation with dual potential-source channels."""
from __future__ import annotations

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_current_regulator import (
    Ac9cCurrentRegulatorSettings,
    build_ac9c_current_regulator_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_field_feedback import (
    Ac9cFieldFeedbackSettings,
    build_ac9c_field_feedback_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_pid import (
    Ac9cPidSettings,
    build_ac9c_pid_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_exciter import (
    substitute_component_input,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_potential_source import (
    Ac9cPotentialSourceSettings,
    build_ac9c_potential_source_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_bridge import (
    Ac9cRectifierBridgeSettings,
    build_ac9c_rectifier_bridge_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_sources import (
    Ac9cPotentialSourceSelection,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_supply import (
    _ac9c_fex_value,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_voltage_transducer import (
    build_ac9c_voltage_transducer_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _esst3a_fex
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class St8cLimiterLocation(Enum):
    """Select the documented additive or post-regulator limiter connection."""

    SUMMATION = 1
    TAKEOVER_GATE = 2


class St8cParameters:
    """Store the 24 PSS/E ST8C constants in source order."""

    __slots__ = (
        'tr', 'kpr', 'kir', 'vpimax', 'vpimin', 'kpa', 'kia', 'vamax',
        'vamin', 'ka', 'ta', 'vrmax', 'vrmin', 'kf', 'tf', 'kc1', 'kp',
        'ki1', 'xl', 'thetap', 'vb1max', 'kc2', 'ki2', 'vb2max',
    )

    def __init__(
            self,
            tr: float = 0.02, kpr: float = 10.0, kir: float = 10.0,
            vpimax: float = 5.0, vpimin: float = -5.0,
            kpa: float = 1.0, kia: float = 1.0,
            vamax: float = 5.0, vamin: float = -5.0,
            ka: float = 1.0, ta: float = 0.02,
            vrmax: float = 5.0, vrmin: float = -5.0,
            kf: float = 0.05, tf: float = 1.0,
            kc1: float = 0.0, kp: float = 1.0, ki1: float = 0.0,
            xl: float = 0.0, thetap: float = 0.0, vb1max: float = 5.0,
            kc2: float = 0.0, ki2: float = 0.0, vb2max: float = 5.0,
    ) -> None:
        """Store source-order constants without selector or host data.

        :param tr: Terminal-voltage measurement time.
        :param kpr: Voltage regulator proportional gain.
        :param kir: Voltage regulator integral gain.
        :param vpimax: Voltage regulator upper limit.
        :param vpimin: Voltage regulator lower limit.
        :param kpa: Field-current regulator proportional gain.
        :param kia: Field-current regulator integral gain.
        :param vamax: Field-current regulator upper limit.
        :param vamin: Field-current regulator lower limit.
        :param ka: Controlled rectifier gain.
        :param ta: Controlled rectifier time constant.
        :param vrmax: Rectifier bridge upper limit.
        :param vrmin: Rectifier bridge lower limit.
        :param kf: Field-current feedback gain.
        :param tf: Field-current feedback time.
        :param kc1: First-channel commutating reactance factor.
        :param kp: Terminal potential-source voltage gain.
        :param ki1: First-channel compound current gain.
        :param xl: Potential-source reactance.
        :param thetap: Potential-source phase angle in degrees.
        :param vb1max: First-channel voltage ceiling.
        :param kc2: Second-channel commutating reactance factor.
        :param ki2: Second-channel current gain.
        :param vb2max: Second-channel voltage ceiling.
        """
        values: tuple[float, ...] = (
            tr, kpr, kir, vpimax, vpimin, kpa, kia, vamax, vamin, ka, ta,
            vrmax, vrmin, kf, tf, kc1, kp, ki1, xl, thetap, vb1max,
            kc2, ki2, vb2max,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError('ST8C constants must be finite')
        elif tr < 0.0 or tf < 0.0 or ta < 0.0:
            raise ValueError('ST8C filter and bridge times must be nonnegative')
        elif min(kpr, kir, kpa, kia, ka, kc1, kc2, kp, ki1, ki2, kf) < 0.0:
            raise ValueError('ST8C gains and loading coefficients must be nonnegative')
        elif vpimin >= vpimax or vamin >= vamax or vrmin >= vrmax:
            raise ValueError('ST8C controller and bridge bounds must be ordered')
        elif vb1max <= 0.0 or vb2max <= 0.0:
            raise ValueError('ST8C potential-source ceilings must be positive')
        else:
            pass
        self.tr: float = tr
        self.kpr: float = kpr
        self.kir: float = kir
        self.vpimax: float = vpimax
        self.vpimin: float = vpimin
        self.kpa: float = kpa
        self.kia: float = kia
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.ka: float = ka
        self.ta: float = ta
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.kf: float = kf
        self.tf: float = tf
        self.kc1: float = kc1
        self.kp: float = kp
        self.ki1: float = ki1
        self.xl: float = xl
        self.thetap: float = thetap
        self.vb1max: float = vb1max
        self.kc2: float = kc2
        self.ki2: float = ki2
        self.vb2max: float = vb2max


def build_st8c_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: St8cParameters | None = None,
        source_selection: Ac9cPotentialSourceSelection = Ac9cPotentialSourceSelection.TERMINAL_FED,
        oel_location: St8cLimiterLocation = St8cLimiterLocation.SUMMATION,
        uel_location: St8cLimiterLocation = St8cLimiterLocation.SUMMATION,
        sensed_voltage0: float = 1.0,
        field_current0: float = 1.0,
) -> RmsModelTemplate:
    """Build the five-state ST8C controller and dual rectifier supply.

    The source diagram gives ``IFDREF = sat(KPR*e + integral(KIR*e))``;
    its second summation forms ``IFDREF - IFD - KF*IFD_filtered``. The
    field-current PI and bounded bridge then multiply the first rectifier
    channel, with the second channel added to produce ``EFD``.

    :param vf: Factory owning the symbolic model.
    :param name: Optional unique template name.
    :param parameters: PSS/E source-order constants.
    :param source_selection: Terminal-fed or independent SW1 position.
    :param oel_location: Additive or low-value OEL gate location.
    :param uel_location: Additive or high-value UEL gate location.
    :param sensed_voltage0: Initial measured terminal voltage.
    :param field_current0: Initial machine field current.
    :return: ST8C template with six controller/host and four phasor inputs.
    :raises ValueError: Unsupported selectors or invalid initialization.
    """
    label: str = 'ST8C' if name is None else name
    selected: St8cParameters = St8cParameters() if parameters is None else parameters
    if not isinstance(source_selection, Ac9cPotentialSourceSelection):
        raise ValueError('ST8C SW1 source selection is invalid')
    elif not isinstance(oel_location, St8cLimiterLocation):
        raise ValueError('ST8C OEL location is invalid')
    elif not isinstance(uel_location, St8cLimiterLocation):
        raise ValueError('ST8C UEL location is invalid')
    elif not math.isfinite(sensed_voltage0) or sensed_voltage0 <= 0.0:
        raise ValueError('ST8C sensed initial voltage must be positive and finite')
    elif not math.isfinite(field_current0):
        raise ValueError('ST8C initial field current must be finite')
    else:
        pass

    feedback0: float = selected.kf * field_current0
    ifd_reference0: float = field_current0 + feedback0
    bridge0: float = 1.0
    bridge_command0: float = bridge0 / selected.ka
    transducer: RmsModelTemplate = build_ac9c_voltage_transducer_template(
        vf, label + ' voltage transducer', selected.tr, sensed_voltage0,
    )
    voltage_regulator: RmsModelTemplate = build_ac9c_pid_template(
        vf,
        label + ' voltage regulator',
        Ac9cPidSettings(
            kpr=selected.kpr, kir=selected.kir,
            kdr=0.0, tdr=0.0,
            vpidmax=selected.vpimax, vpidmin=selected.vpimin,
            error0=0.0, vpid0=ifd_reference0,
        ),
    )
    current_regulator: RmsModelTemplate = build_ac9c_current_regulator_template(
        vf,
        label + ' field-current regulator',
        Ac9cCurrentRegulatorSettings(
            kpa=selected.kpa, kia=selected.kia,
            vamax=selected.vamax, vamin=selected.vamin,
            error0=0.0, vavr0=bridge_command0,
        ),
    )
    bridge: RmsModelTemplate = build_ac9c_rectifier_bridge_template(
        vf,
        label + ' controlled rectifier bridge',
        Ac9cRectifierBridgeSettings(
            ka=selected.ka, ta=selected.ta,
            vrmax=selected.vrmax, vrmin=selected.vrmin,
            vavr0=bridge_command0, va0=bridge0,
        ),
    )
    feedback: RmsModelTemplate = build_ac9c_field_feedback_template(
        vf,
        label + ' field-current feedback',
        Ac9cFieldFeedbackSettings(
            kf=selected.kf, tf=selected.tf,
            signal0=field_current0, feedback0=feedback0,
        ),
    )
    potential: RmsModelTemplate = build_ac9c_potential_source_template(
        vf,
        label + ' potential sources',
        Ac9cPotentialSourceSettings(
            kp=selected.kp, ki1=selected.ki1, ki2=selected.ki2,
            xl=selected.xl, theta_p=selected.thetap,
        ),
    )
    transducer_block: Block = transducer.block
    regulator_block: Block = voltage_regulator.block
    current_block: Block = current_regulator.block
    bridge_block: Block = bridge.block
    feedback_block: Block = feedback.block
    potential_block: Block = potential.block

    measured_voltage: Var = transducer_block.out_vars[0]
    voltage_reference: Var = vf.add_var('VoltageReferencePu_' + label)
    supplementary: Var = vf.add_var('SupplementaryVoltagePu_' + label)
    overexcitation: Var = vf.add_var('OverexcitationSignalPu_' + label)
    underexcitation: Var = vf.add_var('UnderexcitationSignalPu_' + label)
    field_current: Var = vf.add_var('FieldCurrentPu_' + label)
    voltage_error: Var = regulator_block.in_vars[0]
    voltage_error_expression: Expr = voltage_reference + supplementary - measured_voltage
    if oel_location is St8cLimiterLocation.SUMMATION:
        voltage_error_expression += overexcitation
    else:
        pass
    if uel_location is St8cLimiterLocation.SUMMATION:
        voltage_error_expression += underexcitation
    else:
        pass
    substitute_component_input(regulator_block, voltage_error, voltage_error_expression)

    ifd_reference: Var = regulator_block.out_vars[0]
    filtered_feedback: Var = feedback_block.out_vars[0]
    current_error: Expr = ifd_reference - field_current - filtered_feedback
    if uel_location is St8cLimiterLocation.TAKEOVER_GATE:
        current_error = sym.max(current_error, underexcitation)
    else:
        pass
    if oel_location is St8cLimiterLocation.TAKEOVER_GATE:
        current_error = sym.min(current_error, overexcitation)
    else:
        pass
    substitute_component_input(current_block, current_block.in_vars[0], current_error)
    substitute_component_input(bridge_block, bridge_block.in_vars[0], current_block.out_vars[0])
    substitute_component_input(feedback_block, feedback_block.in_vars[0], field_current)

    terminal_source: Var = potential_block.algebraic_vars[0]
    current_source: Var = potential_block.algebraic_vars[1]
    if source_selection is Ac9cPotentialSourceSelection.TERMINAL_FED:
        selected_source: Expr = terminal_source
    else:
        selected_source = Const(abs(selected.kp))
    channel1_control: ControlRealization = ControlRealization(vf, label + ' channel 1')
    channel1_kc: Var = channel1_control.parameter('KC1', selected.kc1)
    channel1_vbmax: Var = channel1_control.parameter('VB1MAX', selected.vb1max)
    channel1_source_input: Var = channel1_control.input(
        'PotentialSourcePu', Const(abs(selected.kp)),
    )
    channel1_loading: Expr = sym.safe_divide(
        channel1_kc * field_current, channel1_source_input, Const(1.0),
    )
    channel1_initial: float = min(
        selected.vb1max,
        abs(selected.kp) * _ac9c_fex_value(
            selected.kc1 * field_current0 / max(0.001, abs(selected.kp)),
        ),
    )
    channel1_voltage: Var = channel1_control.algebraic(
        'AvailableVoltagePu',
        sym.min(channel1_vbmax, channel1_source_input * _esst3a_fex(channel1_loading)),
        Const(channel1_initial),
    )
    channel1_block: Block = channel1_control.finish(
        (channel1_voltage,), 'ST8C first field-current-loaded rectifier channel',
    ).block
    channel2_control: ControlRealization = ControlRealization(vf, label + ' channel 2')
    channel2_kc: Var = channel2_control.parameter('KC2', selected.kc2)
    channel2_vbmax: Var = channel2_control.parameter('VB2MAX', selected.vb2max)
    channel2_source_input: Var = channel2_control.input(
        'PotentialSourcePu', Const(max(0.001, selected.ki2)),
    )
    channel2_loading: Expr = sym.safe_divide(
        channel2_kc * field_current, channel2_source_input, Const(1.0),
    )
    channel2_initial: float = min(
        selected.vb2max,
        max(0.001, selected.ki2) * _ac9c_fex_value(
            selected.kc2 * field_current0 / max(0.001, selected.ki2),
        ),
    )
    channel2_voltage: Var = channel2_control.algebraic(
        'AvailableVoltagePu',
        sym.min(channel2_vbmax, channel2_source_input * _esst3a_fex(channel2_loading)),
        Const(channel2_initial),
    )
    channel2_block: Block = channel2_control.finish(
        (channel2_voltage,), 'ST8C second field-current-loaded rectifier channel',
    ).block
    substitute_component_input(channel1_block, channel1_source_input, selected_source)
    substitute_component_input(channel2_block, channel2_source_input, current_source)
    terminal_current_re: Var = potential_block.in_vars[2]
    terminal_current_im: Var = potential_block.in_vars[3]
    bridge_voltage: Var = bridge_block.out_vars[0]
    first_rectifier_voltage: Var = channel1_voltage
    second_rectifier_voltage: Var = channel2_voltage
    exciter_voltage_control: ControlRealization = ControlRealization(vf, label + ' output')
    bridge_signal: Var = exciter_voltage_control.input('BridgeVoltagePu', Const(bridge0))
    first_supply_signal: Var = exciter_voltage_control.input('FirstSupplyPu', Const(1.0))
    second_supply_signal: Var = exciter_voltage_control.input('SecondSupplyPu', Const(0.001))
    field_voltage: Var = exciter_voltage_control.algebraic(
        'FieldVoltagePu', bridge_signal * first_supply_signal + second_supply_signal,
        Const(bridge0 + 0.001),
    )
    output_block: Block = exciter_voltage_control.finish(
        (field_voltage,), 'ST8C bridge and dual-channel field-voltage composition',
    ).block
    substitute_component_input(output_block, bridge_signal, bridge_voltage)
    substitute_component_input(output_block, first_supply_signal, first_rectifier_voltage)
    substitute_component_input(output_block, second_supply_signal, second_rectifier_voltage)

    root: Block = Block(name=label)
    root.children = list((transducer_block, regulator_block, current_block,
                          bridge_block, feedback_block, potential_block,
                          channel1_block, channel2_block, output_block))
    root.in_vars = list((transducer_block.in_vars[0], voltage_reference,
                         supplementary, overexcitation, underexcitation,
                         field_current, potential_block.in_vars[0],
                         potential_block.in_vars[1], terminal_current_re,
                         terminal_current_im))
    root.out_vars = list((field_voltage, ifd_reference, bridge_voltage,
                          filtered_feedback, first_rectifier_voltage,
                          second_rectifier_voltage))
    root.unify_blocks()
    root.in_vars = list((transducer_block.in_vars[0], voltage_reference,
                         supplementary, overexcitation, underexcitation,
                         field_current, potential_block.in_vars[0],
                         potential_block.in_vars[1], terminal_current_re,
                         terminal_current_im))
    root.out_vars = list((field_voltage, ifd_reference, bridge_voltage,
                          filtered_feedback, first_rectifier_voltage,
                          second_rectifier_voltage))
    root.init_eqs[voltage_reference] = Const(sensed_voltage0)
    root.init_eqs[supplementary] = Const(0.0)
    root.init_eqs[overexcitation] = Const(0.0)
    root.init_eqs[underexcitation] = Const(0.0)
    root.init_eqs[field_current] = Const(field_current0)
    root.init_eqs[potential_block.in_vars[0]] = Const(sensed_voltage0)
    root.init_eqs[potential_block.in_vars[1]] = Const(0.0)
    root.init_eqs[terminal_current_re] = Const(0.0)
    root.init_eqs[terminal_current_im] = Const(0.0)
    root.init_eqs[terminal_source] = Const(abs(selected.kp))
    root.init_eqs[current_source] = Const(max(0.001, selected.ki2))
    root.init_eqs[channel1_voltage] = Const(min(selected.vb1max, abs(selected.kp)))
    root.init_eqs[channel2_voltage] = Const(min(selected.vb2max, max(0.001, selected.ki2)))

    template: RmsModelTemplate = RmsModelTemplate(name=label)
    template.tpe = DeviceType.NoDevice
    template.block = root
    template.comment = 'PSS/E ST8C static exciter with current feedback and two rectifier supply channels'
    return template
