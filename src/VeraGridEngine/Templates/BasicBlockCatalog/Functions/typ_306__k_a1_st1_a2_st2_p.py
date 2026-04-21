# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'K(A1+sT1)/(A2+sT2) [(p'.

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
from VeraGridEngine.Utils.procedural_logic import sampled_value, selfix
from VeraGridEngine.enumerations import DeviceType

def build_typ_306__k_a1_st1_a2_st2_p_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'K(A1+sT1)/(A2+sT2) [(p__306'

def build_typ_306__k_a1_st1_a2_st2_p_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_306__k_a1_st1_a2_st2_p_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    K_A1_sT1_A2_sT2_p_A1: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__A1_' + template_name)
    K_A1_sT1_A2_sT2_p_A2: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__A2_' + template_name)
    K_A1_sT1_A2_sT2_p_K: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__K_' + template_name)
    K_A1_sT1_A2_sT2_p_T1: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__T1_' + template_name)
    K_A1_sT1_A2_sT2_p_T2: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__T2_' + template_name)
    K_A1_sT1_A2_sT2_p_y_max: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__y_max_' + template_name)
    K_A1_sT1_A2_sT2_p_y_min: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__y_min_' + template_name)
    # Declare the state variables used by the template.
    K_A1_sT1_A2_sT2_p_x: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    K_A1_sT1_A2_sT2_p_proc_select_1: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__proc_select_1_' + template_name)
    K_A1_sT1_A2_sT2_p_proc_selfix_0: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p__proc_selfix_0_' + template_name)
    K_A1_sT1_A2_sT2_p_dx: Var = vf.add_var('K(A1+sT1)/(A2+sT2) [(p_dx_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_K_A1_sT1_A2_sT2_p_x: Var = vf.add_diff_var('d_K(A1+sT1)/(A2+sT2) [(p__x_' + template_name, base_var=K_A1_sT1_A2_sT2_p_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((K_A1_sT1_A2_sT2_p_proc_select_1 * sym.Const(0.0)) + ((sym.Const(1.0) - K_A1_sT1_A2_sT2_p_proc_select_1) * K_A1_sT1_A2_sT2_p_dx)))
    state_variables: list[Var] = list()
    state_variables.append(K_A1_sT1_A2_sT2_p_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((K_A1_sT1_A2_sT2_p_dx - ((K_A1_sT1_A2_sT2_p_proc_selfix_0 * (((K_A1_sT1_A2_sT2_p_K * yi) - (K_A1_sT1_A2_sT2_p_A2 * K_A1_sT1_A2_sT2_p_x)) / K_A1_sT1_A2_sT2_p_T2)) + ((sym.Const(1.0) - K_A1_sT1_A2_sT2_p_proc_selfix_0) * (((K_A1_sT1_A2_sT2_p_K * yi) - (K_A1_sT1_A2_sT2_p_A2 * K_A1_sT1_A2_sT2_p_x)) / sym.Const(0.01))))))
    algebraic_equations.append((yo - ((K_A1_sT1_A2_sT2_p_y_min + ((((K_A1_sT1_A2_sT2_p_A1 * K_A1_sT1_A2_sT2_p_x) + (K_A1_sT1_A2_sT2_p_T1 * K_A1_sT1_A2_sT2_p_dx)) - K_A1_sT1_A2_sT2_p_y_min) * sym.heaviside((((K_A1_sT1_A2_sT2_p_A1 * K_A1_sT1_A2_sT2_p_x) + (K_A1_sT1_A2_sT2_p_T1 * K_A1_sT1_A2_sT2_p_dx)) - K_A1_sT1_A2_sT2_p_y_min)))) - ((((K_A1_sT1_A2_sT2_p_A1 * K_A1_sT1_A2_sT2_p_x) + (K_A1_sT1_A2_sT2_p_T1 * K_A1_sT1_A2_sT2_p_dx)) - K_A1_sT1_A2_sT2_p_y_max) * sym.heaviside((((K_A1_sT1_A2_sT2_p_A1 * K_A1_sT1_A2_sT2_p_x) + (K_A1_sT1_A2_sT2_p_T1 * K_A1_sT1_A2_sT2_p_dx)) - K_A1_sT1_A2_sT2_p_y_max))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(K_A1_sT1_A2_sT2_p_dx)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_K_A1_sT1_A2_sT2_p_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[K_A1_sT1_A2_sT2_p_K] = vf.add_const(None, name='K')
    event_parameters[K_A1_sT1_A2_sT2_p_A1] = vf.add_const(None, name='A1')
    event_parameters[K_A1_sT1_A2_sT2_p_T1] = vf.add_const(None, name='T1')
    event_parameters[K_A1_sT1_A2_sT2_p_A2] = vf.add_const(None, name='A2')
    event_parameters[K_A1_sT1_A2_sT2_p_T2] = vf.add_const(None, name='T2')
    event_parameters[K_A1_sT1_A2_sT2_p_y_max] = vf.add_const(None, name='y_max')
    event_parameters[K_A1_sT1_A2_sT2_p_y_min] = vf.add_const(None, name='y_min')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[K_A1_sT1_A2_sT2_p_proc_selfix_0] = vf.add_const(0.0, name='')
    mode_parameters[K_A1_sT1_A2_sT2_p_proc_select_1] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=K_A1_sT1_A2_sT2_p_T2, op=sym.CmpOp.GT, rhs=0.0), output=K_A1_sT1_A2_sT2_p_proc_selfix_0))
    procedural_logic_entries.append(sampled_value(output=K_A1_sT1_A2_sT2_p_proc_select_1, source=(1.0 - ((1.0 - (sym.heaviside(((K_A1_sT1_A2_sT2_p_dx - 0.0) - 1e-06)) * sym.heaviside(((yo - K_A1_sT1_A2_sT2_p_y_max) + 1e-06)))) * (1.0 - (sym.heaviside(((0.0 - K_A1_sT1_A2_sT2_p_dx) - 1e-06)) * sym.heaviside(((K_A1_sT1_A2_sT2_p_y_min - yo) + 1e-06))))))))

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

