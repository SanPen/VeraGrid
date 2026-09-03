# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Complete HVDC GFL VSC and independently wireable RMS Library components.

The complete model uses the same public component builders as the Library.
The electrical device and inner PIs retain the original signal interfaces.
Assembly binds their original initialization expressions to the connected
components. The RMS initializer is unchanged, and initialization-only signals
are not additional graphical ports.
"""

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


class VscActiveControlRmsTemplate(TemplateDefinition):
    """Library definition for the selectable Vdc/P explicit PI."""

    __slots__ = ()

    def __init__(self, vf: VarFactory) -> None:
        """Expose only the active-axis structural choice, not numeric gains.

        :param vf: Factory used when the component is built.
        :return: None.
        """
        super().__init__(vf, params=list((
            TemplateProp(
                name="control1", units="", descr="Active-axis control mode.",
                tpe=ConverterControlType, value=ConverterControlType.Vm_dc,
                allowed_values=(ConverterControlType.Vm_dc, ConverterControlType.Pdc, ConverterControlType.Pac),
            ),
            TemplateProp(name="name", units="", descr="Controller name.", tpe=str, value="Vdc / P control"),
        )))

    def eval(self) -> RmsModelTemplate:
        """Build the selected controller with locally owned event parameters.

        :return: Library template containing the explicit active-axis PI.
        """
        control1: ConverterControlType = self.get_value("control1")
        name: str = self.get_value("name")
        template: RmsModelTemplate = RmsModelTemplate(name=name)
        template.tpe = DeviceType.NoDevice
        template.block = build_vsc_active_control_rms(self.vf, name=name, control1=control1)
        return template


class VscReactiveControlRmsTemplate(TemplateDefinition):
    """Library definition for the selectable Qac/Vac explicit PI."""

    __slots__ = ()

    def __init__(self, vf: VarFactory) -> None:
        """Expose only the reactive-axis structural choice, not numeric gains.

        :param vf: Factory used when the component is built.
        :return: None.
        """
        super().__init__(vf, params=list((
            TemplateProp(
                name="control2", units="", descr="Reactive-axis control mode.",
                tpe=ConverterControlType, value=ConverterControlType.Qac,
                allowed_values=(ConverterControlType.Qac, ConverterControlType.Vm_ac),
            ),
            TemplateProp(name="name", units="", descr="Controller name.", tpe=str, value="Qac / Vac control"),
        )))

    def eval(self) -> RmsModelTemplate:
        """Build the selected controller with locally owned event parameters.

        :return: Library template containing the explicit reactive-axis PI.
        """
        control2: ConverterControlType = self.get_value("control2")
        name: str = self.get_value("name")
        template: RmsModelTemplate = RmsModelTemplate(name=name)
        template.tpe = DeviceType.NoDevice
        template.block = build_vsc_reactive_control_rms(self.vf, name=name, control2=control2)
        return template


def _build_explicit_pi_block(
        vfactory: VarFactory,
        proportional_gain: Var,
        integral_gain: Var,
        error: Expr,
        input_vars: list[Var],
        output: Var,
        output_initial_expression: Expr | None,
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
    :param output_initial_expression: Steady-state value imposed on the PI
        output during explicit initialization, or None to obtain that value
        from the connected electrical equations.
    :param name: Identifier used for the state and block.
    :return: PI controller block with one explicit state.
    """
    integral_state: Var = vfactory.add_var("xi_" + name)
    init_eqs: dict[Var, Expr] = dict()

    # A PI output contains the steady-state bias stored by its integrator. The
    # zero controller error alone cannot determine that bias, so initialize the
    # output from the physical equilibrium before deriving the integral state.
    if output_initial_expression is not None:
        init_eqs[output] = output_initial_expression
    else:
        # The connected plant determines the voltage correction. Do not impose
        # a zero bias or introduce an initialization-only controller input.
        pass
    init_eqs[integral_state] = (output - proportional_gain * error) / integral_gain

    # Keep the controlled output as the direct left-hand side of the residual.
    # Besides being mathematically explicit, this structure lets the equation
    # decomposer identify the output and draw the complete PI signal path.
    output_residual: Expr = output - (
        proportional_gain * error + integral_gain * integral_state
    )
    return Block(
        name=name,
        state_vars=list((integral_state,)),
        state_eqs=list((error,)),
        algebraic_vars=list((output,)),
        algebraic_eqs=list((output_residual,)),
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
        output_initial_expression=vfactory.add_const(1.0),
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


def _new_vsc_signal(vfactory: VarFactory, name: str) -> Var:
    """Create an instance-scoped signal without linking unrelated library drops.

    :param vfactory: Factory owning the signal and its shared reference.
    :param name: Human-readable port label.
    :return: Fresh signal with a unique editor-connectivity reference.
    """
    signal: Var = vfactory.add_var(name)
    # Only explicit wiring may join separately created components. Shared
    # references identify this signal, not every port with the same label.
    vfactory.add_shared_ref_to_var(signal, "hvdc_signal_" + str(signal.non_mutable_uid))
    return signal


def build_vsc_pll_rms(
        vfactory: VarFactory,
        name: str = "PLL_explicit_PI",
        inputs: tuple[Var, Var] | None = None,
) -> Block:
    """Build the standalone PLL used by the complete HVDC converter.

    :param vfactory: Factory owning all generated symbols.
    :param name: Display name of the PLL.
    :param inputs: Optional existing AC magnitude and angle, in that order.
    :return: PLL with Vm/Va inputs and vd/vq/omega outputs.
    """
    if inputs is None:
        inputs = (
            vfactory.add_var("Vm", reference=VarPowerFlowReferenceType.Vmt),
            vfactory.add_var("Va", reference=VarPowerFlowReferenceType.Vat),
        )
    else:
        pass
    block: Block
    vd: Var
    vq: Var
    theta: Var
    omega: Var
    block, vd, vq, theta, omega = _build_pll_block(
        vfactory=vfactory,
        voltage_magnitude=inputs[0],
        voltage_angle=inputs[1],
        signal_reference_prefix="hvdc_pll_" + str(inputs[0].non_mutable_uid),
    )
    block.name = name
    # Only physical terminal voltages belong to the network/PF interface.
    block.external_mapping = dict((
        (VarPowerFlowReferenceType.Vmt, inputs[0]),
        (VarPowerFlowReferenceType.Vat, inputs[1]),
    ))
    return block


def build_vsc_electrical_rms(
        vfactory: VarFactory,
        name: str = "Converter electrical equations",
        inputs: tuple[Var, Var, Var, Var, Var] | None = None,
) -> Block:
    """Build converter current dynamics and AC powers with explicit states.

    The terminal-power equations provide the initial P/Q through the actual
    signal connections. Initialized converter voltages then determine the
    upstream current-PI biases without exposing auxiliary bias ports.

    :param vfactory: Factory owning all generated symbols.
    :param name: Display name of the electrical device.
    :param inputs: Optional vd, vq, omega, y_vd_hat and y_vq_hat signals.
    :return: Device with i_d, i_q, P and Q outputs.
    """
    if inputs is None:
        inputs = (
            vfactory.add_var("vd"), vfactory.add_var("vq"),
            vfactory.add_var("omega"), vfactory.add_var("y_vd_hat"),
            vfactory.add_var("y_vq_hat"),
        )
    else:
        pass
    vd: Var
    vq: Var
    omega: Var
    vd_hat: Var
    vq_hat: Var
    vd, vq, omega, vd_hat, vq_hat = inputs
    i_d: Var = _new_vsc_signal(vfactory, "i_d")
    i_q: Var = _new_vsc_signal(vfactory, "i_q")
    active_power: Var = _new_vsc_signal(vfactory, "P")
    reactive_power: Var = _new_vsc_signal(vfactory, "Q")
    vd_converter: Var = vfactory.add_var("v_d_c")
    vq_converter: Var = vfactory.add_var("v_q_c")
    resistance: Var = vfactory.add_var("R")
    inductance: Var = vfactory.add_var("L")

    # R/L describe the internal converter filter, not the external transformer.
    # Keep the original cross-coupling signs and a single filter-parameter
    # owner. The algebraic equations also provide the initial PI corrections.
    return Block(
        name=name,
        state_vars=list((i_d, i_q)),
        state_eqs=list((
            (vd - vd_converter - resistance * i_d + omega * inductance * i_q) / inductance,
            (vq - vq_converter + resistance * i_q + omega * inductance * i_d) / inductance,
        )),
        algebraic_vars=list((vq_converter, vd_converter, active_power, reactive_power)),
        algebraic_eqs=list((
            vd_converter - (vd_hat + vd - inductance * omega * i_q),
            vq_converter - (vq_hat + vq + inductance * omega * i_d),
            active_power - (vq * i_q + vd * i_d),
            reactive_power - (vq * i_d - vd * i_q),
        )),
        event_dict=dict((
            (resistance, vfactory.add_const(0.0)),
            (inductance, vfactory.add_const(0.05)),
        )),
        init_eqs=dict((
            (i_q, active_power / vq),
            (i_d, reactive_power / vq),
            (vd_converter, vd - (resistance * i_d - omega * inductance * i_q)),
            (vq_converter, vq - (-resistance * i_q - omega * inductance * i_d)),
        )),
        in_vars=list(inputs),
        out_vars=list((i_d, i_q, active_power, reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.P, active_power),
            (VarPowerFlowReferenceType.Q, reactive_power),
        )),
    )


def build_vsc_active_control_rms(
        vfactory: VarFactory,
        name: str = "",
        control1: ConverterControlType = ConverterControlType.Vm_dc,
        inputs: tuple[Var, Var] | None = None,
) -> Block:
    """Build the Vdc/P outer PI with an explicit integral-state bias.

    :param vfactory: Factory owning all generated symbols.
    :param name: Display name; empty selects the control-mode name.
    :param control1: Vm_dc, Pdc or Pac, matching the complete template.
    :param inputs: Optional measured Vdc/P and i_q initialization signal.
    :return: Controller with one i_q_ref output and local event parameters.
    """
    feedback_name: str
    reference_name: str
    gain_name: str
    default_kp: float
    default_ki: float
    control_name: str
    if control1 == ConverterControlType.Vm_dc:
        feedback_name, reference_name, gain_name = "Vdc_state", "Vdc_ref", "vdc"
        default_kp, default_ki, control_name = 0.20, 1.0, "Vdc_ctrl"
    elif control1 == ConverterControlType.Pdc or control1 == ConverterControlType.Pac:
        feedback_name, reference_name, gain_name = "P", "P_ref", "pol"
        default_kp, default_ki = 0.02, 0.10
        control_name = "Pdc_ctrl" if control1 == ConverterControlType.Pdc else "Pac_ctrl"
    else:
        raise ValueError(f"Unsupported active-axis VSC control mode: {control1}")
    if inputs is None:
        inputs = (vfactory.add_var(feedback_name), vfactory.add_var("i_q"))
    else:
        pass
    feedback: Var = inputs[0]
    current: Var = inputs[1]
    reference: Var = vfactory.add_var(reference_name)
    kp: Var = vfactory.add_var("Kp_" + gain_name)
    ki: Var = vfactory.add_var("Ki_" + gain_name)
    output: Var = _new_vsc_signal(vfactory, "i_q_ref")
    error: Expr = feedback - reference if control1 == ConverterControlType.Vm_dc else reference - feedback
    block: Block = _build_explicit_pi_block(
        vfactory=vfactory, proportional_gain=kp, integral_gain=ki,
        error=error, input_vars=list(inputs), output=output,
        output_initial_expression=current, name=control_name,
    )
    block.name = name if name else control_name
    # The reference captures the initial feedback; the current captures the PI
    # bias. Both are required even when the initial control error is zero.
    block.event_dict = dict((
        (kp, vfactory.add_const(default_kp)),
        (ki, vfactory.add_const(default_ki)),
        (reference, feedback),
    ))
    return block


def build_vsc_reactive_control_rms(
        vfactory: VarFactory,
        name: str = "",
        control2: ConverterControlType = ConverterControlType.Qac,
        inputs: tuple[Var, Var] | None = None,
) -> Block:
    """Build the Qac/Vac outer PI with its own initialization dependencies.

    :param vfactory: Factory owning all generated symbols.
    :param name: Display name; empty selects the control-mode name.
    :param control2: Qac or Vm_ac, matching the complete template.
    :param inputs: Optional measured Q/vq and i_d initialization signal.
    :return: Controller with one i_d_ref output and local event parameters.
    """
    feedback_name: str
    reference_name: str
    gain_name: str
    default_kp: float
    default_ki: float
    control_name: str
    if control2 == ConverterControlType.Qac:
        feedback_name, reference_name, gain_name = "Q", "Q_ref", "pol"
        default_kp, default_ki, control_name = 0.02, 0.10, "Qac_ctrl"
    elif control2 == ConverterControlType.Vm_ac:
        feedback_name, reference_name, gain_name = "vq", "Vm_ac_ref", "vac"
        default_kp, default_ki, control_name = 0.10, 1.0, "Vac_ctrl"
    else:
        raise ValueError(f"Unsupported reactive-axis VSC control mode: {control2}")
    if inputs is None:
        inputs = (vfactory.add_var(feedback_name), vfactory.add_var("i_d"))
    else:
        pass
    feedback: Var = inputs[0]
    current: Var = inputs[1]
    reference: Var = vfactory.add_var(reference_name)
    kp: Var = vfactory.add_var("Kp_" + gain_name)
    ki: Var = vfactory.add_var("Ki_" + gain_name)
    output: Var = _new_vsc_signal(vfactory, "i_d_ref")
    block: Block = _build_explicit_pi_block(
        vfactory=vfactory, proportional_gain=kp, integral_gain=ki,
        error=reference - feedback, input_vars=list(inputs), output=output,
        output_initial_expression=current, name=control_name,
    )
    block.name = name if name else control_name
    # At the PLL equilibrium vq equals Vm, including for the Vac reference.
    block.event_dict = dict((
        (kp, vfactory.add_const(default_kp)),
        (ki, vfactory.add_const(default_ki)),
        (reference, feedback),
    ))
    return block


def build_vsc_current_limiter_rms(
        vfactory: VarFactory,
        name: str = "Current limiter",
        inputs: tuple[Var, Var, Var] | None = None,
) -> Block:
    """Build the converter current-reference limiter with q-axis priority.

    :param vfactory: Factory owning all generated symbols.
    :param name: Display name of the limiter.
    :param inputs: Optional i_d_ref, i_q_ref and measured i_q signals.
    :return: Limiter exposing i_d_ref_sat and i_q_ref_sat.
    """
    if inputs is None:
        inputs = (vfactory.add_var("i_d_ref"), vfactory.add_var("i_q_ref"), vfactory.add_var("i_q"))
    else:
        pass
    i_d_ref: Var
    i_q_ref: Var
    i_q: Var
    i_d_ref, i_q_ref, i_q = inputs
    maximum_current: Var = vfactory.add_var("Imax")
    d_axis_limit: Expr = sym.sqrt(sym.max(
        maximum_current ** 2 - sym.max(i_q, i_q_ref) ** 2,
        vfactory.add_const(1.0e-5),
    ))
    i_d_sat: Var = _new_vsc_signal(vfactory, "i_d_ref_sat")
    i_q_sat: Var = _new_vsc_signal(vfactory, "i_q_ref_sat")
    # Preserve the complete converter's limiter law and equilibrium seeds.
    return Block(
        name=name,
        algebraic_vars=list((i_d_sat, i_q_sat)),
        algebraic_eqs=list((
            i_d_sat - sym.hard_sat(i_d_ref, -d_axis_limit, d_axis_limit),
            i_q_sat - sym.hard_sat(i_q_ref, -maximum_current, maximum_current),
        )),
        event_dict=dict(((maximum_current, vfactory.add_const(1.2)),)),
        init_eqs=dict(((i_d_sat, i_d_ref), (i_q_sat, i_q_ref))),
        in_vars=list(inputs),
        out_vars=list((i_d_sat, i_q_sat)),
    )


def build_vsc_vd_hat_rms(
        vfactory: VarFactory,
        name: str = "d-axis current PI controller",
        inputs: tuple[Var, Var] | None = None,
        output: Var | None = None,
) -> Block:
    """Build the d-axis inner current PI producing a voltage correction.

    The historical builder and output names are retained for compatibility.
    This block is a current regulator, not a voltage estimator; the electrical
    equations add the feedforward and cross-axis voltage terms separately.

    :param vfactory: Factory owning all generated symbols.
    :param name: Display name of the controller.
    :param inputs: Optional measured i_d and limited i_d_ref_sat signals.
    :param output: Optional predeclared voltage-correction signal y_vd_hat.
    :return: Explicit-state current PI with locally owned gains.
    """
    if inputs is None:
        inputs = (vfactory.add_var("i_d"), vfactory.add_var("i_d_ref_sat"))
    else:
        pass
    if output is None:
        output = _new_vsc_signal(vfactory, "y_vd_hat")
    else:
        pass
    kp: Var = vfactory.add_var("Kp_icl")
    ki: Var = vfactory.add_var("Ki_icl")
    # A readable display label must not rename the existing integral state or
    # introduce spaces/hyphens into its symbolic identifier.
    symbolic_name: str = "vd_hat" if name == "d-axis current PI controller" else name
    block: Block = _build_explicit_pi_block(
        vfactory=vfactory, proportional_gain=kp, integral_gain=ki,
        error=inputs[0] - inputs[1], input_vars=list(inputs), output=output,
        output_initial_expression=None, name=symbolic_name,
    )
    block.name = name
    # The connected electrical equations initialize the output first; the PI
    # initialization then computes xi from that nonzero voltage correction.
    block.event_dict = dict(((kp, vfactory.add_const(0.20)), (ki, vfactory.add_const(5.0))))
    return block


def build_vsc_vq_hat_rms(
        vfactory: VarFactory,
        name: str = "q-axis current PI controller",
        inputs: tuple[Var, Var] | None = None,
        output: Var | None = None,
) -> Block:
    """Build the q-axis inner current PI producing a voltage correction.

    The historical builder and output names are retained for compatibility.
    This block is a current regulator, not a voltage estimator; the electrical
    equations add the feedforward and cross-axis voltage terms separately.

    :param vfactory: Factory owning all generated symbols.
    :param name: Display name of the controller.
    :param inputs: Optional measured i_q and limited i_q_ref_sat signals.
    :param output: Optional predeclared voltage-correction signal y_vq_hat.
    :return: Explicit-state current PI with locally owned gains.
    """
    if inputs is None:
        inputs = (vfactory.add_var("i_q"), vfactory.add_var("i_q_ref_sat"))
    else:
        pass
    if output is None:
        output = _new_vsc_signal(vfactory, "y_vq_hat")
    else:
        pass
    kp: Var = vfactory.add_var("Kp_icl")
    ki: Var = vfactory.add_var("Ki_icl")
    # Preserve the symbolic state while giving the controller a readable label.
    symbolic_name: str = "vq_hat" if name == "q-axis current PI controller" else name
    block: Block = _build_explicit_pi_block(
        vfactory=vfactory, proportional_gain=kp, integral_gain=ki,
        error=inputs[0] - inputs[1], input_vars=list(inputs), output=output,
        output_initial_expression=None, name=symbolic_name,
    )
    block.name = name
    block.event_dict = dict(((kp, vfactory.add_const(0.20)), (ki, vfactory.add_const(5.0))))
    return block


def bind_vsc_component_initialization(
        electrical: Block,
        terminal_power: Block,
        vd_controller: Block,
        vq_controller: Block,
) -> bool:
    """Bind hidden initialization equations after the four components are wired.

    The public component ports remain identical to the original composite VSC.
    Terminal powers initialize the electrical P/Q variables, while the filter
    equilibrium initializes the two current-controller outputs. The equations
    refer to the variables already unified by the editor connections; no
    initialization-only signal is added to any block interface.

    :param electrical: Connected converter electrical-equations component.
    :param terminal_power: Connected terminal-power equations component.
    :param vd_controller: Connected d-axis current PI component.
    :param vq_controller: Connected q-axis current PI component.
    :return: True when every required runtime connection is present.
    """
    electrical_contract_is_valid: bool = (
        len(electrical.in_vars) == 5
        and len(electrical.out_vars) == 4
        and len(electrical.algebraic_vars) == 4
        and len(terminal_power.in_vars) == 4
        and len(terminal_power.out_vars) == 3
        and len(vd_controller.in_vars) == 2
        and len(vd_controller.out_vars) == 1
        and len(vq_controller.in_vars) == 2
        and len(vq_controller.out_vars) == 1
    )
    if electrical_contract_is_valid:
        active_power: Var = electrical.out_vars[2]
        reactive_power: Var = electrical.out_vars[3]
        electrical_is_connected: bool = (
            terminal_power.in_vars[2].uid == active_power.uid
            and terminal_power.in_vars[3].uid == reactive_power.uid
        )
        current_controllers_are_connected: bool = (
            electrical.in_vars[3].uid == vd_controller.out_vars[0].uid
            and electrical.in_vars[4].uid == vq_controller.out_vars[0].uid
        )
        if electrical_is_connected and current_controllers_are_connected:
            # P/Q use the PF-derived receiving-end powers exposed by the
            # terminal block. The converter sign convention is opposite.
            electrical.init_eqs[active_power] = -terminal_power.out_vars[1]
            electrical.init_eqs[reactive_power] = -terminal_power.out_vars[2]

            # Each voltage residual is remainder - PI_output. Removing that
            # term recovers the original bias without duplicating filter
            # parameters or depending on user-editable variable names.
            zero: sym.Const = sym.Const(0.0)
            vd_controller.init_eqs[vd_controller.out_vars[0]] = electrical.algebraic_eqs[0].subs(
                dict(((electrical.in_vars[3], zero),))
            ).simplify()
            vq_controller.init_eqs[vq_controller.out_vars[0]] = electrical.algebraic_eqs[1].subs(
                dict(((electrical.in_vars[4], zero),))
            ).simplify()
            return True
        else:
            return False
    else:
        return False


def build_vsc_terminal_power_rms(
        vfactory: VarFactory,
        name: str = "VSC terminal power equations",
        inputs: tuple[Var, Var, Var, Var] | None = None,
        outputs: tuple[Var, Var, Var] | None = None,
) -> Block:
    """Build the VSC terminal power and implicit DC-voltage interface.

    :param vfactory: Factory owning all generated symbols.
    :param name: Display name of the terminal block.
    :param inputs: Optional Vdc, Vdc_state, internal P and internal Q.
    :param outputs: Optional predeclared Pf, Pt and Qt terminal powers.
    :return: Atomic DAE block with PF mappings and no duplicate PF init equations.
    """
    if inputs is None:
        inputs = (
            vfactory.add_var("Vdc", reference=VarPowerFlowReferenceType.Vdc),
            vfactory.add_var("Vdc_state"), vfactory.add_var("P"), vfactory.add_var("Q"),
        )
    else:
        pass
    if outputs is None:
        outputs = (
            vfactory.add_var("Pf_vsc", reference=VarPowerFlowReferenceType.Pf),
            vfactory.add_var("Pt_vsc", reference=VarPowerFlowReferenceType.Pt),
            vfactory.add_var("Qt_vsc", reference=VarPowerFlowReferenceType.Qt),
        )
    else:
        pass
    pf: Var
    pt: Var
    qt: Var
    pf, pt, qt = outputs
    qf: Var = vfactory.add_var("Qf", reference=VarPowerFlowReferenceType.Qf)
    # The voltage constraint determines Pf together with the capacitor DAE.
    # It must never be dropped by explicit-output equation decomposition.
    return Block(
        name=name,
        is_decomposable=False,
        algebraic_vars=list((pt, qt, pf)),
        algebraic_eqs=list((inputs[0] - inputs[1], pt + inputs[2], qt + inputs[3])),
        in_vars=list(inputs),
        out_vars=list(outputs),
        event_dict=dict(((qf, vfactory.add_const(0.0)),)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Vdc, inputs[0]),
            (VarPowerFlowReferenceType.Pf, pf),
            (VarPowerFlowReferenceType.Pt, pt),
            (VarPowerFlowReferenceType.Qt, qt),
            (VarPowerFlowReferenceType.Qf, qf),
        )),
    )


def build_vsc_dc_link_rms(
        vfactory: VarFactory,
        name: str = "DC-link capacitor",
        inputs: tuple[Var, Var, Var, Var, Var] | None = None,
        output: Var | None = None,
) -> Block:
    """Build the explicit DC-link voltage state and static converter losses.

    :param vfactory: Factory owning all generated symbols.
    :param name: Display name of the DC-link device.
    :param inputs: Optional Vdc, Pf, Pt, i_d and i_q signals.
    :param output: Optional predeclared Vdc_state for composite assembly.
    :return: Capacitor with Cdc in event_dict and loss coefficients mapped to the VSC.
    """
    if inputs is None:
        inputs = (
            vfactory.add_var("Vdc", reference=VarPowerFlowReferenceType.Vdc),
            vfactory.add_var("Pf_vsc", reference=VarPowerFlowReferenceType.Pf),
            vfactory.add_var("Pt_vsc", reference=VarPowerFlowReferenceType.Pt),
            vfactory.add_var("i_d"), vfactory.add_var("i_q"),
        )
    else:
        pass
    if output is None:
        output = _new_vsc_signal(vfactory, "Vdc_state")
    else:
        pass
    a0: Var = vfactory.add_var("a0")
    a1: Var = vfactory.add_var("a1")
    a2: Var = vfactory.add_var("a2")
    cdc: Var = vfactory.add_var("Cdc")
    current: Expr = sym.sqrt(inputs[3] ** 2 + inputs[4] ** 2 + vfactory.add_const(1.0e-11))
    losses: Expr = a0 + a1 * current + a2 * current ** 2
    # Loss coefficients have static counterparts: do not supply numeric
    # fallbacks or expose them as editable dynamic parameters.
    return Block(
        name=name,
        state_vars=list((output,)),
        state_eqs=list(((inputs[1] + inputs[2] - losses) / (cdc * output),)),
        parameters=dict((
            (a0, vfactory.add_const(None)),
            (a1, vfactory.add_const(None)),
            (a2, vfactory.add_const(None)),
        )),
        api_obj_mapping=dict((
            (ParamPowerFlowReferenceType.alpha1, a0),
            (ParamPowerFlowReferenceType.alpha2, a1),
            (ParamPowerFlowReferenceType.alpha3, a2),
        )),
        event_dict=dict(((cdc, vfactory.add_const(0.40)),)),
        init_eqs=dict(((output, inputs[0]),)),
        in_vars=list(inputs),
        out_vars=list((output,)),
    )


def _build_gfl_converter_model_v2(
        vfactory: VarFactory,
        inputs: tuple[Var, Var, Var],
        control1: ConverterControlType,
        control2: ConverterControlType,
        signal_reference_prefix: str,
) -> tuple[Block, Var, Var, Var, Var]:
    """Assemble the converter from the same components offered by the Library.

    :param vfactory: Factory owning all component symbols.
    :param inputs: AC magnitude, AC angle and DC-link voltage.
    :param control1: Active-axis control mode.
    :param control2: Reactive-axis control mode.
    :param signal_reference_prefix: Retained composite-instance signal namespace.
    :return: Converter followed by its currents and internal powers.
    """
    pll: Block = build_vsc_pll_rms(vfactory, inputs=(inputs[0], inputs[1]))
    vd_hat: Var = vfactory.add_var("y_vd_hat", shared_reference=signal_reference_prefix + "_v_d_hat")
    vq_hat: Var = vfactory.add_var("y_vq_hat", shared_reference=signal_reference_prefix + "_v_q_hat")
    electrical: Block = build_vsc_electrical_rms(
        vfactory,
        inputs=(pll.out_vars[0], pll.out_vars[1], pll.out_vars[2],
                vd_hat, vq_hat),
    )
    i_d: Var
    i_q: Var
    active_power: Var
    reactive_power: Var
    i_d, i_q, active_power, reactive_power = electrical.out_vars
    active_feedback: Var = inputs[2] if control1 == ConverterControlType.Vm_dc else active_power
    reactive_feedback: Var = reactive_power if control2 == ConverterControlType.Qac else pll.out_vars[1]
    active: Block = build_vsc_active_control_rms(vfactory, control1=control1, inputs=(active_feedback, i_q))
    reactive: Block = build_vsc_reactive_control_rms(vfactory, control2=control2, inputs=(reactive_feedback, i_d))
    limiter: Block = build_vsc_current_limiter_rms(
        vfactory, inputs=(reactive.out_vars[0], active.out_vars[0], i_q),
    )
    d_axis: Block = build_vsc_vd_hat_rms(vfactory, inputs=(i_d, limiter.out_vars[0]), output=vd_hat)
    q_axis: Block = build_vsc_vq_hat_rms(vfactory, inputs=(i_q, limiter.out_vars[1]), output=vq_hat)

    # Preserve the original runtime interface at every converter boundary.
    converter: Block = Block(
        name="GFL_converter_explicit_PI",
        children=list((active, reactive, limiter, d_axis, q_axis, pll, electrical)),
        in_vars=list((inputs[2], inputs[0], inputs[1])),
        out_vars=list((i_d, i_q, active_power, reactive_power)),
    )
    return converter, i_d, i_q, active_power, reactive_power


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
    electrical block then derives the internal ``P`` and ``Q``.

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

    converter_block: Block
    i_d: Var
    i_q: Var
    active_power: Var
    reactive_power: Var
    converter_block, i_d, i_q, active_power, reactive_power = _build_gfl_converter_model_v2(
        vfactory=vfactory,
        inputs=(voltage_magnitude, voltage_angle, vdc_state),
        control1=control1,
        control2=control2,
        signal_reference_prefix=signal_reference_prefix,
    )

    terminal_block: Block = build_vsc_terminal_power_rms(
        vfactory=vfactory,
        inputs=(vdc_terminal, vdc_state, active_power, reactive_power),
        outputs=(pf_vsc, pt_vsc, qt_vsc),
    )
    # Bind the same non-graphical initial conditions as the original model.
    # Standalone Library components are bound when the editor saves them.
    bind_vsc_component_initialization(
        electrical=converter_block.children[6],
        terminal_power=terminal_block,
        vd_controller=converter_block.children[3],
        vq_controller=converter_block.children[4],
    )
    dc_link_block: Block = build_vsc_dc_link_rms(
        vfactory=vfactory,
        inputs=(vdc_terminal, pf_vsc, pt_vsc, i_d, i_q),
        output=vdc_state,
    )
    dc_link_block.set_parameter_in_model(var_name="Cdc", new_value=cdc)

    # Complete and manually assembled models use the same parameter owners.
    # Keep the root mappings needed by the runtime compiler, while each
    # reusable child also carries the mappings needed by editor save.
    root_api_mapping: dict[ParamPowerFlowReferenceType, Var] = dict(dc_link_block.api_obj_mapping)
    root_external_mapping: dict[VarPowerFlowReferenceType, Var | None] = dict(terminal_block.external_mapping)
    root_external_mapping[VarPowerFlowReferenceType.Vmt] = voltage_magnitude
    root_external_mapping[VarPowerFlowReferenceType.Vat] = voltage_angle
    root_external_mapping[VarPowerFlowReferenceType.P] = active_power
    root_external_mapping[VarPowerFlowReferenceType.Q] = reactive_power
    root_block: Block = Block(
        name=name,
        children=list((converter_block, terminal_block, dc_link_block)),
        in_vars=list((vdc_terminal, voltage_magnitude, voltage_angle)),
        out_vars=list((pf_vsc, pt_vsc, qt_vsc)),
        external_mapping=root_external_mapping,
        api_obj_mapping=root_api_mapping,
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
