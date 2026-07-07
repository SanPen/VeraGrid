# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Shaft J-k and Pin'.

This module is generated from the shipped VeraGrid catalog artifacts and keeps the
symbolic surface explicit so both humans and tools can inspect it directly.
"""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType

def build_typ_408__shaft_j_k_and_pin_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Shaft J-k and Pin__408'

def build_typ_408__shaft_j_k_and_pin_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_408__shaft_j_k_and_pin_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Shaft_J_k_and_Pin_D_jj: Var = vf.add_var('Shaft J-k and Pin__D_jj_' + template_name)
    Shaft_J_k_and_Pin_D_jk: Var = vf.add_var('Shaft J-k and Pin__D_jk_' + template_name)
    Shaft_J_k_and_Pin_H_j: Var = vf.add_var('Shaft J-k and Pin__H_j_' + template_name)
    Shaft_J_k_and_Pin_K_jk: Var = vf.add_var('Shaft J-k and Pin__K_jk_' + template_name)
    Shaft_J_k_and_Pin_fnom: Var = vf.add_var('Shaft J-k and Pin__fnom_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Pin: Var = vf.add_var('Pin_' + template_name)
    Shaft_J_k_and_Pin_xdtheta_jk: Var = vf.add_var('Shaft J-k and Pin__xdtheta_jk_' + template_name)
    Shaft_J_k_and_Pin_xomega_j: Var = vf.add_var('Shaft J-k and Pin__xomega_j_' + template_name)
    omega_j: Var = vf.add_var('omega_j_' + template_name)
    omega_k: Var = vf.add_var('omega_k_' + template_name)
    torque_jk: Var = vf.add_var('torque_jk_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_variables: list[Var] = list()
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(omega_k)
    input_variables.append(Pin)
    output_variables: list[Var] = list()
    output_variables.append(omega_j)
    output_variables.append(torque_jk)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Shaft_J_k_and_Pin_K_jk] = vf.add_const(None, name='K_jk')
    event_parameters[Shaft_J_k_and_Pin_D_jk] = vf.add_const(None, name='D_jk')
    event_parameters[Shaft_J_k_and_Pin_D_jj] = vf.add_const(None, name='D_jj')
    event_parameters[Shaft_J_k_and_Pin_H_j] = vf.add_const(None, name='H_j')
    event_parameters[Shaft_J_k_and_Pin_fnom] = vf.add_const(None, name='fnom')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Shaft_J_k_and_Pin_xdtheta_jk] = ((sym.Const(1.0) / Shaft_J_k_and_Pin_K_jk) * ((Pin / omega_j) - (Shaft_J_k_and_Pin_D_jj * omega_j)))
    initial_equations[Shaft_J_k_and_Pin_xomega_j] = omega_k
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()

    # Assemble the final block from the explicit typed collections above.
    template.block = Block(
        state_vars=state_variables,
        state_eqs=state_equations,
        algebraic_vars=algebraic_variables,
        algebraic_eqs=algebraic_equations,
        diff_vars=differential_variables,
        init_eqs=initial_equations,
        diff_init_eqs=differential_initial_equations,
        in_vars=input_variables,
        out_vars=output_variables,
        event_dict=event_parameters,
        mode_dict=mode_parameters,
        procedural_logic=procedural_logic_entries,
        name=template_name,
    )

    return template

