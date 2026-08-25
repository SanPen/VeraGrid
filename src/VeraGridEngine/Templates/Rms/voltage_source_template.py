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
    name: str = "",
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
