# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Reduced-order UPC grid-following phasor VSC templates."""

from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.block_helpers import tf_to_block
from VeraGridEngine.Templates.Rms.converters.vsc_gfl import pll_transform_rms
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


class UpcGflPhasorModel(Enum):
    """Select the UPC phasor reduction applied to the GFL current loop."""

    I0 = 'I0'
    I1 = 'I1'
    PQ1 = 'PQ1'


def build_upc_phasor_gfl_rms_template(
        vf: VarFactory,
        model: UpcGflPhasorModel,
        name: str,
) -> RmsModelTemplate:
    """Build a reduced-order UPC grid-following phasor VSC.

    :param vf: Variable factory used to allocate symbolic variables.
    :param model: Colib reduction that determines the current-loop dynamics.
    :param name: Unique template instance name.
    :return: RMS grid-following VSC template.
    """
    template: RmsModelTemplate = RmsModelTemplate()
    template.name = name
    template.tpe = DeviceType.VscDevice

    # The phasor model receives the AC terminal and DC-link state from the network.
    voltage_magnitude = vf.add_var('Vm_')
    voltage_angle = vf.add_var('Va_')
    dc_voltage = vf.add_var('Vdc_')
    active_terminal_power = vf.add_var('Pt_vsc')
    reactive_terminal_power = vf.add_var('Qt_vsc')
    loss_power = vf.add_var('Pf_vsc')
    active_power = vf.add_var('P')
    reactive_power = vf.add_var('Q')
    direct_current = vf.add_var('i_d')
    quadrature_current = vf.add_var('i_q')
    direct_current_reference = vf.add_var('i_d_ref')
    quadrature_current_reference = vf.add_var('i_q_ref')
    active_power_reference = vf.add_var('P_ref')
    reactive_power_reference = vf.add_var('Q_ref')
    power_proportional_gain = vf.add_var('Kp_pq')
    power_integral_gain = vf.add_var('Ki_pq')
    current_time_constant = vf.add_var('tau_c')
    power_time_constant = vf.add_var('tau_pq')

    # The PLL places the voltage on the q axis before power-to-current conversion.
    pll_block, pll_outputs = pll_transform_rms(vf, voltage_magnitude, voltage_angle, name='upc_gfl')
    voltage_direct = pll_outputs[0]
    voltage_quadrature = pll_outputs[1]

    power_blocks: list[Block] = list()
    if model == UpcGflPhasorModel.I0 or model == UpcGflPhasorModel.I1:
        # I0 and I1 retain the full model's power controllers.
        reactive_controller, direct_current_reference = tf_to_block(
            var_factory=vf,
            num=[power_integral_gain, power_proportional_gain],
            den=[0, 1],
            x=reactive_power_reference - reactive_power,
            y=direct_current_reference,
            name='q_ctrl',
        )
        active_controller, quadrature_current_reference = tf_to_block(
            var_factory=vf,
            num=[power_integral_gain, power_proportional_gain],
            den=[0, 1],
            x=active_power_reference - active_power,
            y=quadrature_current_reference,
            name='p_ctrl',
        )
        power_blocks = [reactive_controller, active_controller]
    else:
        # PQ1 replaces the closed-loop outer controls by first-order current references.
        reactive_filter, direct_current_reference = tf_to_block(
            var_factory=vf,
            num=[1],
            den=[1, power_time_constant],
            x=reactive_power_reference / voltage_quadrature,
            y=direct_current_reference,
            name='q_filter',
        )
        active_filter, quadrature_current_reference = tf_to_block(
            var_factory=vf,
            num=[1],
            den=[1, power_time_constant],
            x=active_power_reference / voltage_quadrature,
            y=quadrature_current_reference,
            name='p_filter',
        )
        power_blocks = [reactive_filter, active_filter]

    current_blocks: list[Block] = list()
    if model == UpcGflPhasorModel.I1:
        # I1 retains the current-loop response as a first-order lag.
        direct_filter, direct_current = tf_to_block(
            var_factory=vf,
            num=[1],
            den=[1, current_time_constant],
            x=direct_current_reference,
            y=direct_current,
            name='id_filter',
        )
        quadrature_filter, quadrature_current = tf_to_block(
            var_factory=vf,
            num=[1],
            den=[1, current_time_constant],
            x=quadrature_current_reference,
            y=quadrature_current,
            name='iq_filter',
        )
        current_blocks = [direct_filter, quadrature_filter]
    else:
        # I0 and PQ1 remove current-loop dynamics, leaving direct current injection.
        direct_current_equation = direct_current - direct_current_reference
        quadrature_current_equation = quadrature_current - quadrature_current_reference
        current_block = Block(
            algebraic_eqs=[direct_current_equation, quadrature_current_equation],
            algebraic_vars=[direct_current, quadrature_current],
        )
        current_blocks = [current_block]

    # Terminal power equations connect the reduced controller to the RMS network.
    model_block = Block(
        algebraic_eqs=[
            active_power - (voltage_quadrature * quadrature_current + voltage_direct * direct_current),
            reactive_power - (voltage_quadrature * direct_current - voltage_direct * quadrature_current),
            active_terminal_power + active_power,
            reactive_terminal_power + reactive_power,
            loss_power - active_power,
        ],
        algebraic_vars=[active_power, reactive_power, active_terminal_power, reactive_terminal_power, loss_power],
        event_dict={
            active_power_reference: active_power,
            reactive_power_reference: reactive_power,
            power_proportional_gain: vf.add_const(0.05),
            power_integral_gain: vf.add_const(1.0),
            current_time_constant: vf.add_const(0.001),
            power_time_constant: vf.add_const(0.02),
        },
        init_eqs={
            active_power: -active_terminal_power,
            reactive_power: -reactive_terminal_power,
            direct_current: reactive_power / voltage_quadrature,
            quadrature_current: active_power / voltage_quadrature,
            direct_current_reference: direct_current,
            quadrature_current_reference: quadrature_current,
            active_terminal_power: -active_power,
            reactive_terminal_power: -reactive_power,
            loss_power: active_power,
        },
        in_vars=[voltage_magnitude, voltage_angle, dc_voltage],
        out_vars=[active_terminal_power, reactive_terminal_power, loss_power],
        external_mapping={
            VarPowerFlowReferenceType.Vmt: voltage_magnitude,
            VarPowerFlowReferenceType.Vat: voltage_angle,
            VarPowerFlowReferenceType.Vdc: dc_voltage,
            VarPowerFlowReferenceType.Pt: active_terminal_power,
            VarPowerFlowReferenceType.Qt: reactive_terminal_power,
            VarPowerFlowReferenceType.Pf: loss_power,
        },
    )
    model_block.add(pll_block)
    for power_block in power_blocks:
        model_block.add(power_block)
    for current_block in current_blocks:
        model_block.add(current_block)
    model_block.unify_blocks()

    template.block = model_block
    template.comment = 'Colib UPC {0} grid-following phasor VSC realization'.format(model.value)
    return template


def get_upc_phasor_i0_gfl_rms_template(vf: VarFactory, name: str = 'UPC Phasor-I0 GFL VSC') -> RmsModelTemplate:
    """Build the UPC I0 GFL model without current-loop dynamics.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS I0 grid-following VSC template.
    """
    return build_upc_phasor_gfl_rms_template(vf=vf, model=UpcGflPhasorModel.I0, name=name)


def get_upc_phasor_i1_gfl_rms_template(vf: VarFactory, name: str = 'UPC Phasor-I1 GFL VSC') -> RmsModelTemplate:
    """Build the UPC I1 GFL model with first-order current-loop dynamics.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS I1 grid-following VSC template.
    """
    return build_upc_phasor_gfl_rms_template(vf=vf, model=UpcGflPhasorModel.I1, name=name)


def get_upc_phasor_pq1_gfl_rms_template(vf: VarFactory, name: str = 'UPC Phasor-PQ1 GFL VSC') -> RmsModelTemplate:
    """Build the UPC PQ1 GFL model with first-order outer-loop dynamics.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS PQ1 grid-following VSC template.
    """
    return build_upc_phasor_gfl_rms_template(vf=vf, model=UpcGflPhasorModel.PQ1, name=name)
