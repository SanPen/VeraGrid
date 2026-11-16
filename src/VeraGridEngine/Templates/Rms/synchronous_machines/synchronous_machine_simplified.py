# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Native runtime template for the CGMES SynchronousMachineSimplified model."""

from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


def build_cgmes_synchronous_machine_simplified(
    vfactory: VarFactory,
    name: str | None = None,
) -> RmsModelTemplate:
    """Build the CGMES fixed internal-voltage machine behind ``Rs + jXp``.

    The model has rotor angle and speed states. Its internal voltage magnitude
    is initialized from the power-flow point and then held constant, matching
    the CGMES simplified model's lack of an excitation input.

    :param vfactory: Factory that allocates symbolic model variables.
    :param name: Optional template instance name.
    :return: Materialized CGMES simplified synchronous-machine template.
    """
    template_name: str = "CGMES SynchronousMachineSimplified" if name is None else name
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = DeviceType.GeneratorDevice

    # Declare network ports first so the block's outer interface follows the
    # same Vm/Va and P/Q contract as the other generator RMS templates.
    vm_var: Var = vfactory.add_var("Vm", reference=VarPowerFlowReferenceType.Vm)
    va_var: Var = vfactory.add_var("Va", reference=VarPowerFlowReferenceType.Va)
    pg_var: Var = vfactory.add_var("Pg", reference=VarPowerFlowReferenceType.P)
    qg_var: Var = vfactory.add_var("Qg", reference=VarPowerFlowReferenceType.Q)

    # Declare internal electrical and mechanical variables shared with the
    # machine, governor, and network equations.
    delta_var: Var = vfactory.add_var("delta", shared_reference="delta_reference")
    omega_var: Var = vfactory.add_var("omega", shared_reference="omega_reference")
    omega_derivative_var: Var = vfactory.add_var("OmegaDerivativePu")
    vd_var: Var = vfactory.add_var("Vd", shared_reference="vd_reference")
    vq_var: Var = vfactory.add_var("Vq", shared_reference="vq_reference")
    id_var: Var = vfactory.add_var("Id", shared_reference="id_reference")
    iq_var: Var = vfactory.add_var("Iq", shared_reference="iq_reference")
    tm_var: Var = vfactory.add_var("Tm", shared_reference="tm_reference")
    te_var: Var = vfactory.add_var("Te", shared_reference="te_reference")

    # Expose the CGMES rotating-machine attributes as model parameters; the
    # import layer will replace these defaults with the parsed DY values.
    fn_var: Var = vfactory.add_var("fn")
    damping_var: Var = vfactory.add_var("D")
    inertia_var: Var = vfactory.add_var("H")
    saturation_factor_var: Var = vfactory.add_var("S1")
    saturation_factor_120_var: Var = vfactory.add_var("S12")
    resistance_var: Var = vfactory.add_var("Rs")
    leakage_reactance_var: Var = vfactory.add_var("Xp")
    internal_voltage_var: Var = vfactory.add_var("EInternal")

    block: Block = Block(name=template_name)
    block.parameters[fn_var] = vfactory.add_const(50.0)
    block.api_obj_mapping[ParamPowerFlowReferenceType.freq] = fn_var
    block.event_dict[damping_var] = vfactory.add_const(0.0)
    block.event_dict[inertia_var] = vfactory.add_const(6.0)
    block.event_dict[saturation_factor_var] = vfactory.add_const(0.0)
    block.event_dict[saturation_factor_120_var] = vfactory.add_const(0.0)
    block.event_dict[resistance_var] = vfactory.add_const(0.0)
    block.event_dict[leakage_reactance_var] = vfactory.add_const(0.3)
    # Let the power-flow initialization expression provide EInternal; a concrete
    # event default would take precedence and leave the stator model unbalanced.
    block.event_dict[internal_voltage_var] = vfactory.add_const(None)

    # Apply the swing equation and constant internal-voltage stator equations.
    synchronous_speed: Expr = sym.Const(2.0 * math.pi) * fn_var
    block.state_vars = list((delta_var, omega_var))
    block.state_eqs = list((
        synchronous_speed * (omega_var - sym.Const(1.0)),
        omega_derivative_var,
    ))
    block.algebraic_vars = list((
        vd_var, vq_var, id_var, iq_var, pg_var, qg_var, te_var,
        omega_derivative_var,
    ))
    block.algebraic_eqs = list((
        vm_var * sym.sin(delta_var - va_var) - vd_var,
        vm_var * sym.cos(delta_var - va_var) - vq_var,
        vd_var - leakage_reactance_var * iq_var + resistance_var * id_var,
        vq_var - internal_voltage_var + leakage_reactance_var * id_var
        + resistance_var * iq_var,
        vd_var * id_var + vq_var * iq_var - pg_var,
        vq_var * id_var - vd_var * iq_var - qg_var,
        internal_voltage_var * iq_var - te_var,
        omega_derivative_var
        - (tm_var - te_var - damping_var * (omega_var - sym.Const(1.0)))
        / (sym.Const(2.0) * inertia_var),
    ))
    block.in_vars = list((vm_var, va_var, tm_var))

    # Initialize rotor orientation and current from the solved complex power;
    # deriving E from this point makes the fixed-voltage model start in balance.
    voltage_complex: Expr = vm_var * sym.exp(sym.Const(1j) * va_var)
    current_complex: Expr = sym.conj((pg_var + sym.Const(1j) * qg_var) / voltage_complex)
    internal_complex: Expr = voltage_complex + (
        resistance_var + sym.Const(1j) * leakage_reactance_var
    ) * current_complex
    block.init_eqs = dict()
    block.init_eqs[delta_var] = sym.imag(sym.log(internal_complex / sym.abs(internal_complex)))
    block.init_eqs[internal_voltage_var] = sym.abs(internal_complex)
    block.init_eqs[omega_var] = sym.Const(1.0)
    block.init_eqs[omega_derivative_var] = sym.Const(0.0)
    block.init_eqs[vd_var] = vm_var * sym.sin(delta_var - va_var)
    block.init_eqs[vq_var] = vm_var * sym.cos(delta_var - va_var)
    current_dq: Expr = current_complex * sym.exp(
        -sym.Const(1j) * (delta_var - sym.Const(math.pi / 2.0))
    )
    block.init_eqs[id_var] = sym.real(current_dq)
    block.init_eqs[iq_var] = sym.imag(current_dq)
    block.init_eqs[te_var] = internal_voltage_var * iq_var
    block.init_eqs[tm_var] = te_var

    # Publish only static power-flow ports; model links remain internal to the
    # CGMES dynamic model and are not guessed from the catalog descriptor.
    block.out_vars = list((pg_var, qg_var, omega_var, te_var, omega_derivative_var))
    block.external_mapping = dict()
    block.external_mapping[VarPowerFlowReferenceType.Vm] = vm_var
    block.external_mapping[VarPowerFlowReferenceType.Va] = va_var
    block.external_mapping[VarPowerFlowReferenceType.P] = pg_var
    block.external_mapping[VarPowerFlowReferenceType.Q] = qg_var
    template.block.children.append(block)
    template.block.external_mapping = dict(block.external_mapping)
    template.block.in_vars = list((vm_var, va_var))
    template.block.out_vars = list((pg_var, qg_var))
    template.block.name = template_name
    template.comment = "CGMES SynchronousMachineSimplified"
    return template


def build_synchronous_machine_simplified_template(
        vfactory: VarFactory,
        name: str | None = None,
) -> RmsModelTemplate:
    """Build the CGMES simplified machine with its canonical RDF parameters.

    :param vfactory: Factory used to allocate model and parameter symbols.
    :param name: Optional unique runtime model name.
    :return: Complete fixed-internal-voltage synchronous-machine model.
    """
    template_name: str = 'SynchronousMachineSimplified' if name is None else name
    template: RmsModelTemplate = build_cgmes_synchronous_machine_simplified(
        vfactory=vfactory,
        name=template_name,
    )
    parameter_block: Block = Block(name=f'{template_name}_CGMES_parameters')
    for parameter_name in (
            'enabled', 'damping', 'inertia', 'saturationFactor',
            'saturationFactor120', 'statorLeakageReactance', 'statorResistance',
    ):
        variable_name: str = f'SynchronousMachineSimplified.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        parameter_block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    template.block.children.insert(0, parameter_block)
    template.comment = 'CGMES SynchronousMachineSimplified equations and RDF parameters.'
    return template
