# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Multiply 1/K [p'.

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
from VeraGridEngine.Utils.procedural_logic import selfix
from VeraGridEngine.enumerations import DeviceType

def build_typ_173__multiply_1_k_p_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Multiply 1/K [p__173'

def build_typ_173__multiply_1_k_p_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_173__multiply_1_k_p_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Multiply_1_K_p_K: Var = vf.add_var('Multiply 1/K [p__K_' + template_name)
    Multiply_1_K_p_y_max: Var = vf.add_var('Multiply 1/K [p__y_max_' + template_name)
    Multiply_1_K_p_y_min: Var = vf.add_var('Multiply 1/K [p__y_min_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Multiply_1_K_p_proc_selfix_1: Var = vf.add_var('Multiply 1/K [p__proc_selfix_1_' + template_name)
    Multiply_1_K_p_proc_selfix_const_0: Var = vf.add_var('Multiply 1/K [p__proc_selfix_const_0_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo - ((Multiply_1_K_p_y_min + ((((Multiply_1_K_p_proc_selfix_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Multiply_1_K_p_proc_selfix_1) * (yi / ((Multiply_1_K_p_proc_selfix_const_0 * sym.Const(1.0)) + ((sym.Const(1.0) - Multiply_1_K_p_proc_selfix_const_0) * Multiply_1_K_p_K))))) - Multiply_1_K_p_y_min) * sym.heaviside((((Multiply_1_K_p_proc_selfix_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Multiply_1_K_p_proc_selfix_1) * (yi / ((Multiply_1_K_p_proc_selfix_const_0 * sym.Const(1.0)) + ((sym.Const(1.0) - Multiply_1_K_p_proc_selfix_const_0) * Multiply_1_K_p_K))))) - Multiply_1_K_p_y_min)))) - ((((Multiply_1_K_p_proc_selfix_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Multiply_1_K_p_proc_selfix_1) * (yi / ((Multiply_1_K_p_proc_selfix_const_0 * sym.Const(1.0)) + ((sym.Const(1.0) - Multiply_1_K_p_proc_selfix_const_0) * Multiply_1_K_p_K))))) - Multiply_1_K_p_y_max) * sym.heaviside((((Multiply_1_K_p_proc_selfix_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Multiply_1_K_p_proc_selfix_1) * (yi / ((Multiply_1_K_p_proc_selfix_const_0 * sym.Const(1.0)) + ((sym.Const(1.0) - Multiply_1_K_p_proc_selfix_const_0) * Multiply_1_K_p_K))))) - Multiply_1_K_p_y_max))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Multiply_1_K_p_K] = vf.add_const(None, name='K')
    event_parameters[Multiply_1_K_p_y_max] = vf.add_const(None, name='y_max')
    event_parameters[Multiply_1_K_p_y_min] = vf.add_const(None, name='y_min')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Multiply_1_K_p_proc_selfix_const_0] = vf.add_const(0.0, name='')
    mode_parameters[Multiply_1_K_p_proc_selfix_1] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Multiply_1_K_p_K, op=sym.CmpOp.EQ, rhs=0.0), output=Multiply_1_K_p_proc_selfix_const_0))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Multiply_1_K_p_K, op=sym.CmpOp.EQ, rhs=0.0), output=Multiply_1_K_p_proc_selfix_1))

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

