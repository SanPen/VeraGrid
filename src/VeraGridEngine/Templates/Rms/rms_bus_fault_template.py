from __future__ import annotations

from typing import Dict

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.block import VarPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType


def get_rms_bus_fault_template(
        var_factory: VarFactory,
        name: str = "RMS bus fault",
        bolted_voltage_floor_pu: float = 1.0e-6,
) -> RmsModelTemplate:
    """Build a fixed-size balanced bus-fault shunt model.

    The conductance and susceptance are runtime parameters. Their zero defaults
    make the device electrically absent at initialization, while paired RMS
    events apply and clear the physical fault without changing the DAE layout.

    :param var_factory: Circuit-owned symbolic variable factory.
    :param name: Human-readable model name.
    :param bolted_voltage_floor_pu: Positive voltage floor used while an ideal
        bolted-fault constraint is active.
    :return: RMS template containing the fault shunt block.
    """
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.ShuntDevice

    # AC bus voltage is supplied by the standard injection connection layer.
    voltage_magnitude: Var = var_factory.add_var(
        name="Vm",
        reference=VarPowerFlowReferenceType.Vm,
    )
    voltage_angle: Var = var_factory.add_var(
        name="Va",
        reference=VarPowerFlowReferenceType.Va,
    )

    # Keep a complete P/Q injection surface so the ordinary RMS nodal assembler
    # treats the fault exactly like any other shunt-connected physical device.
    active_power: Var = var_factory.add_var("P")
    reactive_power: Var = var_factory.add_var("Q")
    fault_conductance: Var = var_factory.add_var("fault_g_pu")
    fault_susceptance: Var = var_factory.add_var("fault_b_pu")
    bolted_fault_active: Var = var_factory.add_var("bolted_fault_active")

    mode_parameters: Dict[Var, Expr | Const] = dict()
    mode_parameters[fault_conductance] = Const(0.0)
    mode_parameters[fault_susceptance] = Const(0.0)
    mode_parameters[bolted_fault_active] = Const(0.0)

    # An impedance fault uses the ordinary admittance equations. An ideal
    # bolted fault instead clamps the polar voltage because an infinite shunt
    # admittance makes the zero-voltage angle singular in a P/Q formulation.
    # The fault P/Q variables then remain available for the nodal balance to
    # determine the current supplied into the ideal short circuit.
    inactive_constraint: Expr = Const(1.0) - bolted_fault_active
    voltage_floor: Const = Const(max(float(bolted_voltage_floor_pu), 1.0e-12))

    # A positive conductance consumes active power. An inductive fault has a
    # negative susceptance and therefore consumes reactive power as well.
    block: Block = Block(
        algebraic_eqs=list([
            inactive_constraint * (
                active_power + fault_conductance * voltage_magnitude ** 2
            ) + bolted_fault_active * (voltage_magnitude - voltage_floor),
            inactive_constraint * (
                reactive_power - fault_susceptance * voltage_magnitude ** 2
            ) + bolted_fault_active * voltage_angle,
        ]),
        algebraic_vars=list([active_power, reactive_power]),
        in_vars=list([voltage_magnitude, voltage_angle]),
        init_eqs=dict({
            active_power: Const(0.0),
            reactive_power: Const(0.0),
        }),
        external_mapping=dict({
            VarPowerFlowReferenceType.Vm: voltage_magnitude,
            VarPowerFlowReferenceType.Va: voltage_angle,
            VarPowerFlowReferenceType.P: active_power,
            VarPowerFlowReferenceType.Q: reactive_power,
        }),
    )
    block.name = name
    # A fault application changes the network admittance discontinuously. Keep
    # both components in the discrete-mode registry so the RMS integrator aligns
    # the edge, invalidates the pre-fault Jacobian and restarts its state history
    # on the post-fault algebraic manifold.
    block.mode_dict = mode_parameters
    template.block = block
    template.comment = 'Bus fault RMS shunt model'
    return template
