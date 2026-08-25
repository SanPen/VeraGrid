# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Standalone HVDC GFL VSC with explicit controller and electrical states."""

from __future__ import annotations

import math

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_definition import TemplateDefinition, TemplateProp
from VeraGridEngine.Utils.Symbolic.block import Block, Var
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.enumerations import (
    ConverterControlType,
    DeviceType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


class _VscGflInternals:
    """Variables required by the VSC terminal and DC-link equations."""

    __slots__ = ("resistance", "inductance")

    def __init__(self, resistance: Var, inductance: Var) -> None:
        """Store the converter-interface parameters shared by the root model.

        :param resistance: Converter-interface resistance parameter.
        :param inductance: Converter-interface inductance parameter.
        :return: None.
        """
        self.resistance: Var = resistance
        self.inductance: Var = inductance


class HvdcVscGflRmsTemplate(TemplateDefinition):
    """Editable definition of the explicit-state standalone HVDC VSC."""

    __slots__ = ()

    def __init__(self, vf: VarFactory) -> None:
        """Define the structural properties exposed by the Dynamic Editor.

        :param vf: Variable factory that owns the generated RMS variables.
        :return: None.
        """
        super().__init__(
            vf,
            params=list((
                TemplateProp(
                    name="control1",
                    units="",
                    descr="Active-axis control mode (Vm_dc, Pdc, or Pac).",
                    tpe=ConverterControlType,
                    value=ConverterControlType.Vm_dc,
                    allowed_values=(
                        ConverterControlType.Vm_dc,
                        ConverterControlType.Pdc,
                        ConverterControlType.Pac,
                    ),
                ),
                TemplateProp(
                    name="control2",
                    units="",
                    descr="Reactive-axis control mode (Qac or Vm_ac).",
                    tpe=ConverterControlType,
                    value=ConverterControlType.Qac,
                    allowed_values=(
                        ConverterControlType.Qac,
                        ConverterControlType.Vm_ac,
                    ),
                ),
                TemplateProp(
                    name="cdc",
                    units="p.u.",
                    descr="DC-link capacitance used by the RMS voltage state.",
                    tpe=float,
                    value=0.40,
                ),
                TemplateProp(
                    name="name",
                    units="",
                    descr="Name of the RMS model.",
                    tpe=str,
                    value="HVDC GFL VSC explicit PI",
                ),
            )),
        )

    def eval(self) -> RmsModelTemplate:
        """Build the explicit-state VSC and persist its structural options.

        :return: Configured standalone HVDC GFL VSC RMS template.
        """
        control1: ConverterControlType = self.get_value("control1")
        control2: ConverterControlType = self.get_value("control2")
        cdc: float = self.get_value("cdc")
        name: str = self.get_value("name")
        template: RmsModelTemplate = build_hvdc_vsc_gfl_rms(
            vfactory=self.vf,
            name=name,
            control1=control1,
            control2=control2,
            cdc=cdc,
        )

        # Structural options are not ordinary equation parameters. Store them
        # with the generated block so Block Properties can rebuild the same
        # controller after a save/reopen cycle.
        configuration: dict[str, object] = dict()
        configuration["control1"] = control1.name
        configuration["control2"] = control2.name
        configuration["cdc"] = cdc
        template.block.__dict__["_modal_template_kind"] = "hvdc_vsc_gfl_rms_v2"
        template.block.__dict__["_modal_template_config"] = configuration
        return template


def _build_explicit_pi_block(
        vfactory: VarFactory,
        proportional_gain: Var,
        integral_gain: Var,
        error: Expr,
        input_vars: list[Var],
        output: Var,
        name: str,
) -> Block:
    """Build a PI controller with a dedicated integral state.

    The controller is represented as ``dxi/dt = error`` and
    ``output = Kp * error + Ki * xi``. This avoids derivative variables on an
    algebraic PI output and therefore keeps the state-space formulation
    standard for small-signal analysis.

    :param vfactory: Factory used to create the integral state.
    :param proportional_gain: PI proportional gain.
    :param integral_gain: PI integral gain.
    :param error: Controller input error.
    :param input_vars: Variables required to evaluate the controller error.
    :param output: Algebraic controller output.
    :param name: Identifier used for the state and block.
    :return: PI controller block with one explicit state.
    """
    integral_state: Var = vfactory.add_var("xi_" + name)
    init_eqs: dict[Var, Expr] = dict()
    init_eqs[integral_state] = (output - proportional_gain * error) / integral_gain
    return Block(
        name=name,
        state_vars=list((integral_state,)),
        state_eqs=list((error,)),
        algebraic_vars=list((output,)),
        algebraic_eqs=list((output - proportional_gain * error - integral_gain * integral_state,)),
        init_eqs=init_eqs,
        in_vars=input_vars,
        out_vars=list((output,)),
    )


def _build_pll_block(
        vfactory: VarFactory,
        voltage_magnitude: Var,
        voltage_angle: Var,
        signal_reference_prefix: str,
) -> tuple[Block, Var, Var, Var, Var]:
    """Build the synchronous-reference-frame PLL with an explicit PI state.

    :param vfactory: Factory used to create the PLL variables.
    :param voltage_magnitude: AC-terminal voltage magnitude.
    :param voltage_angle: AC-terminal voltage angle.
    :param signal_reference_prefix: Instance-unique prefix used to connect the
        PLL child blocks in the Dynamic Editor.
    :return: PLL block followed by d voltage, q voltage, angle and frequency.
    """
    # Each internal signal needs an instance-scoped shared reference. The
    # symbolic equations already reuse these variables, while the references
    # provide the explicit producer-consumer edges required by the editor.
    theta: Var = vfactory.add_var(
        "theta",
        shared_reference=signal_reference_prefix + "_theta",
    )
    v_d_grid: Var = vfactory.add_var(
        "vd",
        shared_reference=signal_reference_prefix + "_vd",
    )
    v_q_grid: Var = vfactory.add_var(
        "vq",
        shared_reference=signal_reference_prefix + "_vq",
    )
    omega: Var = vfactory.add_var(
        "omega",
        shared_reference=signal_reference_prefix + "_omega",
    )
    kp_pll: Var = vfactory.add_var("Kp_pll")
    ki_pll: Var = vfactory.add_var("Ki_pll")
    nominal_frequency: Var = vfactory.add_var("fn")
    pll_error: Expr = voltage_magnitude * sym.sin(voltage_angle - theta)

    coordinate_events: dict[Var, Expr] = dict()
    coordinate_events[nominal_frequency] = vfactory.add_const(50.0)
    coordinate_events[kp_pll] = vfactory.add_const(0.001)
    coordinate_events[ki_pll] = vfactory.add_const(0.1)
    coordinate_init: dict[Var, Expr] = dict()
    coordinate_init[theta] = voltage_angle
    coordinate_init[v_d_grid] = vfactory.add_const(0.0)
    coordinate_init[v_q_grid] = voltage_magnitude

    coordinate_block: Block = Block(
        name="PLL coordinates",
        state_vars=list((theta,)),
        state_eqs=list((2.0 * math.pi * nominal_frequency * (omega - 1.0),)),
        algebraic_vars=list((v_d_grid, v_q_grid)),
        algebraic_eqs=list((
            v_d_grid - voltage_magnitude * sym.sin(voltage_angle - theta),
            v_q_grid - voltage_magnitude * sym.cos(voltage_angle - theta),
        )),
        event_dict=coordinate_events,
        init_eqs=coordinate_init,
        in_vars=list((voltage_magnitude, voltage_angle, omega)),
        out_vars=list((theta, v_d_grid, v_q_grid)),
    )
    pi_block: Block = _build_explicit_pi_block(
        vfactory=vfactory,
        proportional_gain=kp_pll,
        integral_gain=ki_pll,
        error=pll_error,
        input_vars=list((voltage_magnitude, voltage_angle, theta)),
        output=omega,
        name="PLL_integrator",
    )
    pll_block: Block = Block(
        name="PLL_explicit_PI",
        children=list((coordinate_block, pi_block)),
        in_vars=list((voltage_magnitude, voltage_angle)),
        # Theta closes the loop inside the PLL and is not consumed by another
        # converter-level block. Keep only the three outward-facing signals in
        # the parent contract so the nested PLL has no dangling output port.
        out_vars=list((v_d_grid, v_q_grid, omega)),
    )
    return pll_block, v_d_grid, v_q_grid, theta, omega


def _build_gfl_converter_model_v2(
        vfactory: VarFactory,
        inputs: tuple[Var, Var, Var],
        terminal_active_power: Var,
        terminal_reactive_power: Var,
        control1: ConverterControlType,
        control2: ConverterControlType,
        signal_reference_prefix: str,
) -> tuple[Block, Var, Var, Var, Var, _VscGflInternals]:
    """Build the GFL controller and filter with explicit PI/current states.

    :param vfactory: Factory used to create all converter variables.
    :param inputs: AC voltage magnitude, AC voltage angle and DC-link voltage.
    :param terminal_active_power: Power-flow-derived AC-terminal active power
        used to initialize the internal active-power variable.
    :param terminal_reactive_power: Power-flow-derived AC-terminal reactive
        power used to initialize the internal reactive-power variable.
    :param control1: Active-axis control mode.
    :param control2: Reactive-axis control mode.
    :param signal_reference_prefix: Instance-unique prefix for internal editor
        connections.
    :return: Converter block, currents, powers and shared parameters.
    """
    voltage_magnitude: Var = inputs[0]
    voltage_angle: Var = inputs[1]
    v_dc_state: Var = inputs[2]
    pll_block: Block
    v_d_grid: Var
    v_q_grid: Var
    theta: Var
    omega: Var
    pll_block, v_d_grid, v_q_grid, theta, omega = _build_pll_block(
        vfactory=vfactory,
        voltage_magnitude=voltage_magnitude,
        voltage_angle=voltage_angle,
        signal_reference_prefix=signal_reference_prefix,
    )

    kp_icl: Var = vfactory.add_var("Kp_icl")
    ki_icl: Var = vfactory.add_var("Ki_icl")
    kp_pol: Var = vfactory.add_var("Kp_pol")
    ki_pol: Var = vfactory.add_var("Ki_pol")
    kp_vdc: Var = vfactory.add_var("Kp_vdc")
    ki_vdc: Var = vfactory.add_var("Ki_vdc")
    kp_vac: Var = vfactory.add_var("Kp_vac")
    ki_vac: Var = vfactory.add_var("Ki_vac")
    resistance: Var = vfactory.add_var("R")
    inductance: Var = vfactory.add_var("L")

    # Declare every signal crossing a child-block boundary with a unique
    # shared reference. Generic reference names would join two VSC instances
    # that happen to use the same VarFactory, hence the per-instance prefix.
    i_d: Var = vfactory.add_var(
        "i_d",
        shared_reference=signal_reference_prefix + "_i_d",
    )
    i_q: Var = vfactory.add_var(
        "i_q",
        shared_reference=signal_reference_prefix + "_i_q",
    )
    i_d_ref: Var = vfactory.add_var(
        "i_d_ref",
        shared_reference=signal_reference_prefix + "_i_d_ref",
    )
    i_q_ref: Var = vfactory.add_var(
        "i_q_ref",
        shared_reference=signal_reference_prefix + "_i_q_ref",
    )
    active_power: Var = vfactory.add_var(
        "P",
        shared_reference=signal_reference_prefix + "_active_power",
    )
    reactive_power: Var = vfactory.add_var(
        "Q",
        shared_reference=signal_reference_prefix + "_reactive_power",
    )
    active_power_ref: Var = vfactory.add_var("P_ref")
    reactive_power_ref: Var = vfactory.add_var("Q_ref")
    vdc_ref: Var = vfactory.add_var("Vdc_ref")
    vac_ref: Var = vfactory.add_var("Vm_ac_ref")
    v_d_converter: Var = vfactory.add_var("v_d_c")
    v_q_converter: Var = vfactory.add_var("v_q_c")

    event_dict: dict[Var, Expr] = dict()
    event_dict[kp_icl] = vfactory.add_const(0.20)
    event_dict[ki_icl] = vfactory.add_const(5.00)
    event_dict[kp_pol] = vfactory.add_const(0.02)
    event_dict[ki_pol] = vfactory.add_const(0.10)
    event_dict[kp_vdc] = vfactory.add_const(0.20)
    event_dict[ki_vdc] = vfactory.add_const(1.00)
    event_dict[kp_vac] = vfactory.add_const(0.1)
    event_dict[ki_vac] = vfactory.add_const(1.0)
    event_dict[resistance] = vfactory.add_const(0.0)
    event_dict[inductance] = vfactory.add_const(0.05)
    event_dict[active_power_ref] = active_power
    event_dict[reactive_power_ref] = reactive_power
    event_dict[vdc_ref] = v_dc_state
    event_dict[vac_ref] = voltage_magnitude

    active_error: Expr
    active_kp: Var
    active_ki: Var
    active_name: str
    active_inputs: list[Var]
    if control1 == ConverterControlType.Pac:
        active_error = active_power_ref - active_power
        active_kp = kp_pol
        active_ki = ki_pol
        active_name = "Pac_ctrl"
        active_inputs = list((active_power,))
    elif control1 == ConverterControlType.Pdc:
        active_error = active_power_ref - active_power
        active_kp = kp_pol
        active_ki = ki_pol
        active_name = "Pdc_ctrl"
        active_inputs = list((active_power,))
    elif control1 == ConverterControlType.Vm_dc:
        active_error = v_dc_state - vdc_ref
        active_kp = kp_vdc
        active_ki = ki_vdc
        active_name = "Vdc_ctrl"
        active_inputs = list((v_dc_state,))
    else:
        raise ValueError(f"Unsupported active-axis VSC control mode: {control1}")

    reactive_error: Expr
    reactive_kp: Var
    reactive_ki: Var
    reactive_name: str
    reactive_inputs: list[Var]
    if control2 == ConverterControlType.Qac:
        reactive_error = reactive_power_ref - reactive_power
        reactive_kp = kp_pol
        reactive_ki = ki_pol
        reactive_name = "Qac_ctrl"
        reactive_inputs = list((reactive_power,))
    elif control2 == ConverterControlType.Vm_ac:
        reactive_error = vac_ref - v_q_grid
        reactive_kp = kp_vac
        reactive_ki = ki_vac
        reactive_name = "Vac_ctrl"
        reactive_inputs = list((v_q_grid,))
    else:
        raise ValueError(f"Unsupported reactive-axis VSC control mode: {control2}")

    active_control: Block = _build_explicit_pi_block(
        vfactory=vfactory,
        proportional_gain=active_kp,
        integral_gain=active_ki,
        error=active_error,
        input_vars=active_inputs,
        output=i_q_ref,
        name=active_name,
    )
    reactive_control: Block = _build_explicit_pi_block(
        vfactory=vfactory,
        proportional_gain=reactive_kp,
        integral_gain=reactive_ki,
        error=reactive_error,
        input_vars=reactive_inputs,
        output=i_d_ref,
        name=reactive_name,
    )

    maximum_current: Expr = vfactory.add_const(1.2)
    d_axis_limit: Expr = sym.sqrt(sym.max(
        maximum_current ** 2 - sym.max(i_q, i_q_ref) ** 2,
        vfactory.add_const(1.0e-5),
    ))
    i_d_ref_limited: Var = vfactory.add_var(
        "i_d_ref_sat",
        shared_reference=signal_reference_prefix + "_i_d_ref_limited",
    )
    i_q_ref_limited: Var = vfactory.add_var(
        "i_q_ref_sat",
        shared_reference=signal_reference_prefix + "_i_q_ref_limited",
    )
    limiter_block: Block = Block(
        name="Current limiter",
        algebraic_vars=list((i_d_ref_limited, i_q_ref_limited)),
        algebraic_eqs=list((
            i_d_ref_limited - sym.hard_sat(i_d_ref, -d_axis_limit, d_axis_limit),
            i_q_ref_limited - sym.hard_sat(i_q_ref, -maximum_current, maximum_current),
        )),
        init_eqs=dict((
            (i_d_ref_limited, i_d_ref),
            (i_q_ref_limited, i_q_ref),
        )),
        in_vars=list((i_d_ref, i_q_ref, i_q)),
        out_vars=list((i_d_ref_limited, i_q_ref_limited)),
    )

    v_d_hat: Var = vfactory.add_var(
        "y_vd_hat",
        shared_reference=signal_reference_prefix + "_v_d_hat",
    )
    v_q_hat: Var = vfactory.add_var(
        "y_vq_hat",
        shared_reference=signal_reference_prefix + "_v_q_hat",
    )
    d_axis_inner_control: Block = _build_explicit_pi_block(
        vfactory=vfactory,
        proportional_gain=kp_icl,
        integral_gain=ki_icl,
        error=i_d - i_d_ref_limited,
        input_vars=list((i_d, i_d_ref_limited)),
        output=v_d_hat,
        name="vd_hat",
    )
    q_axis_inner_control: Block = _build_explicit_pi_block(
        vfactory=vfactory,
        proportional_gain=kp_icl,
        integral_gain=ki_icl,
        error=i_q - i_q_ref_limited,
        input_vars=list((i_q, i_q_ref_limited)),
        output=v_q_hat,
        name="vq_hat",
    )

    electrical_init: dict[Var, Expr] = dict()
    # P and Q are algebraic variables owned by this block. Their initialization
    # equations must therefore live here as well; placing them on the VSC root
    # makes the Dynamic Editor reject a structural control-mode rebuild.
    electrical_init[active_power] = -terminal_active_power
    electrical_init[reactive_power] = -terminal_reactive_power
    electrical_init[i_q] = active_power / v_q_grid
    electrical_init[i_d] = reactive_power / v_q_grid
    electrical_init[v_d_converter] = v_d_grid - (resistance * i_d - omega * inductance * i_q)
    electrical_init[v_q_converter] = v_q_grid - (-resistance * i_q - omega * inductance * i_d)
    electrical_block: Block = Block(
        name="Converter electrical equations",
        state_vars=list((i_d, i_q)),
        state_eqs=list((
            (v_d_grid - v_d_converter - resistance * i_d + omega * inductance * i_q) / inductance,
            (v_q_grid - v_q_converter + resistance * i_q + omega * inductance * i_d) / inductance,
        )),
        algebraic_vars=list((v_q_converter, v_d_converter, active_power, reactive_power)),
        algebraic_eqs=list((
            v_d_converter - (v_d_hat + v_d_grid - inductance * omega * i_q),
            v_q_converter - (v_q_hat + v_q_grid + inductance * omega * i_d),
            active_power - (v_q_grid * i_q + v_d_grid * i_d),
            reactive_power - (v_q_grid * i_d - v_d_grid * i_q),
        )),
        init_eqs=electrical_init,
        in_vars=list((v_d_grid, v_q_grid, omega, v_d_hat, v_q_hat)),
        out_vars=list((i_d, i_q, active_power, reactive_power)),
    )

    converter_block: Block = Block(
        name="GFL_converter_explicit_PI",
        children=list((
            active_control,
            reactive_control,
            limiter_block,
            d_axis_inner_control,
            q_axis_inner_control,
            pll_block,
            electrical_block,
        )),
        event_dict=event_dict,
        in_vars=list((voltage_magnitude, voltage_angle, v_dc_state)),
        out_vars=list((i_d, i_q, active_power, reactive_power)),
    )
    internals: _VscGflInternals = _VscGflInternals(
        resistance=resistance,
        inductance=inductance,
    )
    return converter_block, i_d, i_q, active_power, reactive_power, internals


def build_hvdc_vsc_gfl_rms(
        vfactory: VarFactory,
        name: str = "HVDC GFL VSC explicit PI",
        control1: ConverterControlType = ConverterControlType.Vm_dc,
        control2: ConverterControlType = ConverterControlType.Qac,
        cdc: float = 0.40,
) -> RmsModelTemplate:
    """Build the complete explicit-state HVDC VSC RMS model.

    The root exposes only the static-device electrical interface. Controller
    signals remain internal, while ``i_d``, ``i_q`` and the DC-link voltage are
    ordinary states. Power-flow values initialize the terminal powers; the
    root initialization equations then derive the internal ``P`` and ``Q``.

    :param vfactory: Variable factory used to construct the symbolic model.
    :param name: Root block and template display name.
    :param control1: Active-axis control mode.
    :param control2: Reactive-axis control mode.
    :param cdc: DC-link capacitance in p.u.
    :return: Reusable explicit-state RMS VSC template.
    """
    voltage_magnitude: Var = vfactory.add_var("Vm", reference=VarPowerFlowReferenceType.Vmt)
    voltage_angle: Var = vfactory.add_var("Va", reference=VarPowerFlowReferenceType.Vat)
    vdc_terminal: Var = vfactory.add_var("Vdc", reference=VarPowerFlowReferenceType.Vdc)
    # Scope all internal references to this concrete VSC. This avoids visual
    # and symbolic cross-connections when a circuit contains several stations.
    signal_reference_prefix: str = "hvdc_vsc_" + str(voltage_magnitude.non_mutable_uid)
    vdc_state: Var = vfactory.add_var(
        "Vdc_state",
        shared_reference=signal_reference_prefix + "_vdc_state",
    )
    pt_vsc: Var = vfactory.add_var("Pt_vsc", reference=VarPowerFlowReferenceType.Pt)
    qt_vsc: Var = vfactory.add_var("Qt_vsc", reference=VarPowerFlowReferenceType.Qt)
    pf_vsc: Var = vfactory.add_var("Pf_vsc", reference=VarPowerFlowReferenceType.Pf)
    qf_vsc: Var = vfactory.add_var("Qf", reference=VarPowerFlowReferenceType.Qf)

    converter_block: Block
    i_d: Var
    i_q: Var
    active_power: Var
    reactive_power: Var
    internals: _VscGflInternals
    converter_block, i_d, i_q, active_power, reactive_power, internals = _build_gfl_converter_model_v2(
        vfactory=vfactory,
        inputs=(voltage_magnitude, voltage_angle, vdc_state),
        terminal_active_power=pt_vsc,
        terminal_reactive_power=qt_vsc,
        control1=control1,
        control2=control2,
        signal_reference_prefix=signal_reference_prefix,
    )

    loss_a0: Var = vfactory.add_var("a0")
    loss_a1: Var = vfactory.add_var("a1")
    loss_a2: Var = vfactory.add_var("a2")
    cdc_parameter: Var = vfactory.add_var("Cdc")
    current_magnitude: Expr = sym.sqrt(i_d ** 2 + i_q ** 2 + vfactory.add_const(1.0e-11))
    converter_losses: Expr = loss_a0 + loss_a1 * current_magnitude + loss_a2 * current_magnitude ** 2

    terminal_block: Block = Block(
        name="VSC terminal power equations",
        # The DC-voltage coupling is an implicit constraint rather than an
        # explicit assignment to one terminal-power output. EquationDecomposer
        # can only lower explicit output definitions; allowing decomposition
        # here would discard this constraint and leave an empty nested editor.
        # Keep the complete DAE as one visible atomic block instead.
        is_decomposable=False,
        algebraic_vars=list((pt_vsc, qt_vsc, pf_vsc)),
        algebraic_eqs=list((
            vdc_terminal - vdc_state,
            pt_vsc + active_power,
            qt_vsc + reactive_power,
        )),
        in_vars=list((vdc_terminal, vdc_state, active_power, reactive_power)),
        out_vars=list((pt_vsc, qt_vsc, pf_vsc)),
    )
    dc_link_events: dict[Var, Expr] = dict()
    dc_link_events[loss_a0] = vfactory.add_const(0.0)
    dc_link_events[loss_a1] = vfactory.add_const(0.0)
    dc_link_events[loss_a2] = vfactory.add_const(0.0)
    dc_link_events[cdc_parameter] = vfactory.add_const(float(cdc))
    dc_link_block: Block = Block(
        name="DC-link capacitor",
        state_vars=list((vdc_state,)),
        state_eqs=list(((pf_vsc + pt_vsc - converter_losses) / (cdc_parameter * vdc_state),)),
        event_dict=dc_link_events,
        init_eqs=dict((
            (vdc_state, vdc_terminal),
        )),
        in_vars=list((vdc_terminal, pf_vsc, pt_vsc, i_d, i_q)),
        out_vars=list((vdc_state,)),
    )

    root_events: dict[Var, Expr] = dict()
    root_events[qf_vsc] = vfactory.add_const(0.0)
    root_block: Block = Block(
        name=name,
        children=list((converter_block, terminal_block, dc_link_block)),
        event_dict=root_events,
        in_vars=list((voltage_magnitude, voltage_angle, vdc_terminal)),
        out_vars=list((pt_vsc, qt_vsc, pf_vsc)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Vmt, voltage_magnitude),
            (VarPowerFlowReferenceType.Vat, voltage_angle),
            (VarPowerFlowReferenceType.Vdc, vdc_terminal),
            (VarPowerFlowReferenceType.P, active_power),
            (VarPowerFlowReferenceType.Q, reactive_power),
            (VarPowerFlowReferenceType.Pt, pt_vsc),
            (VarPowerFlowReferenceType.Qt, qt_vsc),
            (VarPowerFlowReferenceType.Pf, pf_vsc),
            (VarPowerFlowReferenceType.Qf, qf_vsc),
        )),
        api_obj_mapping=dict((
            (ParamPowerFlowReferenceType.R1, internals.resistance),
            (ParamPowerFlowReferenceType.X1, internals.inductance),
            (ParamPowerFlowReferenceType.alpha1, loss_a0),
            (ParamPowerFlowReferenceType.alpha2, loss_a1),
            (ParamPowerFlowReferenceType.alpha3, loss_a2),
        )),
    )

    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.VscDevice
    template.block = root_block
    return template


def get_hvdc_vdc_q_vsc_rms(
        vfactory: VarFactory,
        name: str = "HVDC GFL VSC - Vdc/Q",
) -> RmsModelTemplate:
    """Build the explicit-state DC-voltage/reactive-power terminal.

    :param vfactory: Variable factory used to construct the symbolic model.
    :param name: Root block and template display name.
    :return: Explicit-state Vdc/Q HVDC VSC template.
    """
    return build_hvdc_vsc_gfl_rms(
        vfactory=vfactory,
        name=name,
        control1=ConverterControlType.Vm_dc,
        control2=ConverterControlType.Qac,
    )


def get_hvdc_pdc_q_vsc_rms(
        vfactory: VarFactory,
        name: str = "HVDC GFL VSC - Pdc/Q",
) -> RmsModelTemplate:
    """Build the explicit-state DC-power/reactive-power terminal.

    :param vfactory: Variable factory used to construct the symbolic model.
    :param name: Root block and template display name.
    :return: Explicit-state Pdc/Q HVDC VSC template.
    """
    return build_hvdc_vsc_gfl_rms(
        vfactory=vfactory,
        name=name,
        control1=ConverterControlType.Pdc,
        control2=ConverterControlType.Qac,
    )
