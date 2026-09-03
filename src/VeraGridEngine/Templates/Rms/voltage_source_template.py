# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def VoltageSourceBuild(
    vfactory: VarFactory,
    name: str = "Voltage source RMS template",
) -> RmsModelTemplate:
    """Build an RMS voltage-source template with P/Q capability limits.

    Control logic:

    - Q within limits: enforce ``Vm = Vg0``.
    - Q at a limit: enforce ``Q = clamp(Q, Qmin_G, Qmax_G)``.
    - P within limits: enforce ``Va = Ag0``.
    - P at a limit: enforce ``P = clamp(P, Pmin_G, Pmax_G)``.

    :param vfactory: Shared symbolic variable factory.
    :param name: User-facing model name.
    :return: Voltage-source RMS model with an editor-visible equation block.
    """
    templ: RmsModelTemplate = RmsModelTemplate(name=name)
    templ.tpe = DeviceType.GeneratorDevice

    voltage_magnitude: Var = vfactory.add_var("Vm", reference=VarPowerFlowReferenceType.Vm)
    voltage_angle: Var = vfactory.add_var("Va", reference=VarPowerFlowReferenceType.Va)
    inputs: list[Var] = list((voltage_magnitude, voltage_angle))

    active_power: Var = vfactory.add_var("P", reference=VarPowerFlowReferenceType.P)
    reactive_power: Var = vfactory.add_var("Q", reference=VarPowerFlowReferenceType.Q)
    outputs: list[Var] = list((active_power, reactive_power))

    initial_voltage_magnitude: Var = vfactory.add_var("Vg0")
    initial_voltage_angle: Var = vfactory.add_var("Ag0")

    active_power_maximum: Var = vfactory.add_var("Pmax_G")
    active_power_minimum: Var = vfactory.add_var("Pmin_G")
    reactive_power_maximum: Var = vfactory.add_var("Qmax_G")
    reactive_power_minimum: Var = vfactory.add_var("Qmin_G")

    event_dict: dict[Var, Expr] = dict((
        (initial_voltage_magnitude, voltage_magnitude),
        (initial_voltage_angle, voltage_angle),
        (active_power_maximum, vfactory.add_const(9.999)),
        (active_power_minimum, vfactory.add_const(-9.999)),
        (reactive_power_maximum, vfactory.add_const(9.999)),
        (reactive_power_minimum, vfactory.add_const(-9.999)),
    ))

    active_power_within_limits: Expr = (
        ((active_power_maximum - active_power) >= 0).to_expression()
        * (0 <= (active_power - active_power_minimum)).to_expression()
    )
    reactive_power_within_limits: Expr = (
        ((reactive_power_maximum - reactive_power) >= 0).to_expression()
        * (0 <= (reactive_power - reactive_power_minimum)).to_expression()
    )

    saturated_active_power: Expr = sym.max(
        active_power_minimum,
        sym.min(active_power, active_power_maximum),
    )
    saturated_reactive_power: Expr = sym.max(
        reactive_power_minimum,
        sym.min(reactive_power, reactive_power_maximum),
    )

    # Store the equations in a child. The root is the device interface shown
    # by the Dynamic Editor and the child remains available for inspection.
    equation_block: Block = Block(
        name="Voltage Source equations",
        algebraic_eqs=list((
            (voltage_angle - initial_voltage_angle) * active_power_within_limits
            + (active_power - saturated_active_power) * (1 - active_power_within_limits),
            (voltage_magnitude - initial_voltage_magnitude) * reactive_power_within_limits
            + (reactive_power - saturated_reactive_power) * (1 - reactive_power_within_limits),
        )),
        algebraic_vars=list(outputs),
        event_dict=event_dict,
        in_vars=list(inputs),
        out_vars=list(outputs),
    )

    root_block: Block = Block(
        name="Voltage Source",
        children=list((equation_block,)),
        in_vars=list(inputs),
        out_vars=list(outputs),
        external_mapping=dict((
            (VarPowerFlowReferenceType.P, active_power),
            (VarPowerFlowReferenceType.Q, reactive_power),
            (VarPowerFlowReferenceType.Vm, voltage_magnitude),
            (VarPowerFlowReferenceType.Va, voltage_angle),
        )),
    )
    templ.block = root_block

    return templ


def build_thevenin_voltage_source(
        vfactory: VarFactory,
        resistance_pu: float,
        reactance_pu: float,
        name: str = "",
) -> RmsModelTemplate:
    """Build an RMS external-network source behind its DGS impedance.

    PowerFactory ``ElmXnet`` objects are ideal internal voltage sources behind
    the positive-sequence impedance derived from ``snss`` and ``rntxn``.  The
    terminal voltage therefore changes when the connected system exchanges
    power, even though the source's internal voltage remains constant.  This
    template retains that physical distinction and works with both the polar
    P/Q DAE and the rectangular-current phasor formulation.

    :param vfactory: Symbolic variable factory shared by the circuit.
    :param resistance_pu: Positive-sequence source resistance on system base.
    :param reactance_pu: Positive-sequence source reactance on system base.
    :param name: Optional human-readable template name.
    :return: External-network RMS template with a finite Thevenin impedance.
    """
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.GeneratorDevice

    # Terminal voltage is supplied by the connected AC bus.  Power and current
    # are both retained so either supported RMS network formulation can stamp
    # the same physical source without rebuilding the template.
    voltage_magnitude: Var = vfactory.add_var(
        "Vm",
        VarPowerFlowReferenceType.Vm,
    )
    voltage_angle: Var = vfactory.add_var(
        "Va",
        VarPowerFlowReferenceType.Va,
    )
    active_power: Var = vfactory.add_var(
        "P",
        VarPowerFlowReferenceType.P,
    )
    reactive_power: Var = vfactory.add_var(
        "Q",
        VarPowerFlowReferenceType.Q,
    )
    current_real: Var = vfactory.add_var(
        "Ir",
        VarPowerFlowReferenceType.Ir,
    )
    current_imaginary: Var = vfactory.add_var(
        "Ii",
        VarPowerFlowReferenceType.Ii,
    )

    source_voltage: Var = vfactory.add_var("E_internal")
    source_angle: Var = vfactory.add_var("A_internal")
    resistance: Var = vfactory.add_var("R1")
    reactance: Var = vfactory.add_var("X1")

    terminal_voltage_real: Expr = voltage_magnitude * sym.cos(voltage_angle)
    terminal_voltage_imaginary: Expr = voltage_magnitude * sym.sin(voltage_angle)
    internal_voltage_real: Expr = (
        terminal_voltage_real
        + resistance * current_real
        - reactance * current_imaginary
    )
    internal_voltage_imaginary: Expr = (
        terminal_voltage_imaginary
        + reactance * current_real
        + resistance * current_imaginary
    )

    # The power/current identities use the injection sign convention
    # S = V * conj(I).  The last two equations impose E = V + Z*I, which is the
    # Thevenin source contract exported by ElmXnet.
    block: Block = Block(
        algebraic_vars=list([
            active_power,
            reactive_power,
            current_real,
            current_imaginary,
        ]),
        algebraic_eqs=list([
            active_power - voltage_magnitude * (
                sym.cos(voltage_angle) * current_real
                + sym.sin(voltage_angle) * current_imaginary
            ),
            reactive_power - voltage_magnitude * (
                sym.sin(voltage_angle) * current_real
                - sym.cos(voltage_angle) * current_imaginary
            ),
            source_voltage * sym.cos(source_angle) - internal_voltage_real,
            source_voltage * sym.sin(source_angle) - internal_voltage_imaginary,
        ]),
        parameters=dict({
            resistance: Const(float(resistance_pu)),
            reactance: Const(float(reactance_pu)),
        }),
        event_dict=dict({
            source_voltage: Const(None),
            source_angle: Const(None),
        }),
        init_eqs=dict({
            source_voltage: sym.sqrt(
                internal_voltage_real * internal_voltage_real
                + internal_voltage_imaginary * internal_voltage_imaginary
            ),
            source_angle: sym.atan2(
                internal_voltage_imaginary,
                internal_voltage_real,
            ),
        }),
        in_vars=list([voltage_magnitude, voltage_angle]),
        out_vars=list([
            active_power,
            reactive_power,
            current_real,
            current_imaginary,
        ]),
    )
    block.name = name if len(name) > 0 else "Thevenin Voltage Source"
    block.external_mapping = {
        VarPowerFlowReferenceType.P: active_power,
        VarPowerFlowReferenceType.Q: reactive_power,
        VarPowerFlowReferenceType.Ir: current_real,
        VarPowerFlowReferenceType.Ii: current_imaginary,
        VarPowerFlowReferenceType.Vm: voltage_magnitude,
        VarPowerFlowReferenceType.Va: voltage_angle,
    }
    block.api_obj_mapping = {
        ParamPowerFlowReferenceType.R1: resistance,
        ParamPowerFlowReferenceType.X1: reactance,
    }
    template.block = block
    return template
