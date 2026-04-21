# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block '(ss)/(Ass+Bs+1) _bypass'.

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

def build_typ_198__ss_ass_bs_1_bypass_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return '(ss)/(Ass+Bs+1) _bypass__198'

def build_typ_198__ss_ass_bs_1_bypass_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_198__ss_ass_bs_1_bypass_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    ss_Ass_Bs_1_bypass_A: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass__A_' + template_name)
    ss_Ass_Bs_1_bypass_B: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass__B_' + template_name)
    # Declare the state variables used by the template.
    ss_Ass_Bs_1_bypass_x1: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass__x1_' + template_name)
    ss_Ass_Bs_1_bypass_x2: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass__x2_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    ss_Ass_Bs_1_bypass_proc_selfix_0: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass__proc_selfix_0_' + template_name)
    ss_Ass_Bs_1_bypass_proc_selfix_1: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass__proc_selfix_1_' + template_name)
    ss_Ass_Bs_1_bypass_proc_selfix_2: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass__proc_selfix_2_' + template_name)
    ss_Ass_Bs_1_bypass_dx1: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass_dx1_' + template_name)
    ss_Ass_Bs_1_bypass_dx2: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass_dx2_' + template_name)
    ss_Ass_Bs_1_bypass_triv: Var = vf.add_var('(ss)/(Ass+Bs+1) _bypass_triv_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_ss_Ass_Bs_1_bypass_x1: Var = vf.add_diff_var('d_(ss)/(Ass+Bs+1) _bypass__x1_' + template_name, base_var=ss_Ass_Bs_1_bypass_x1)
    d_ss_Ass_Bs_1_bypass_x2: Var = vf.add_diff_var('d_(ss)/(Ass+Bs+1) _bypass__x2_' + template_name, base_var=ss_Ass_Bs_1_bypass_x2)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(ss_Ass_Bs_1_bypass_dx1)
    state_equations.append(ss_Ass_Bs_1_bypass_dx2)
    state_variables: list[Var] = list()
    state_variables.append(ss_Ass_Bs_1_bypass_x1)
    state_variables.append(ss_Ass_Bs_1_bypass_x2)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((ss_Ass_Bs_1_bypass_dx1 - ((ss_Ass_Bs_1_bypass_proc_selfix_0 * sym.Const(0.0)) + ((sym.Const(1.0) - ss_Ass_Bs_1_bypass_proc_selfix_0) * ss_Ass_Bs_1_bypass_x2))))
    algebraic_equations.append((ss_Ass_Bs_1_bypass_dx2 - ((ss_Ass_Bs_1_bypass_proc_selfix_1 * sym.Const(0.0)) + ((sym.Const(1.0) - ss_Ass_Bs_1_bypass_proc_selfix_1) * (((yi - ss_Ass_Bs_1_bypass_x1) - (ss_Ass_Bs_1_bypass_B * ss_Ass_Bs_1_bypass_x2)) / ss_Ass_Bs_1_bypass_A)))))
    algebraic_equations.append((yo - ((ss_Ass_Bs_1_bypass_proc_selfix_2 * yi) + ((sym.Const(1.0) - ss_Ass_Bs_1_bypass_proc_selfix_2) * ss_Ass_Bs_1_bypass_dx2))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(ss_Ass_Bs_1_bypass_dx1)
    algebraic_variables.append(ss_Ass_Bs_1_bypass_dx2)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_ss_Ass_Bs_1_bypass_x1)
    differential_variables.append(d_ss_Ass_Bs_1_bypass_x2)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[ss_Ass_Bs_1_bypass_A] = vf.add_const(None, name='A')
    event_parameters[ss_Ass_Bs_1_bypass_B] = vf.add_const(None, name='B')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[ss_Ass_Bs_1_bypass_proc_selfix_0] = vf.add_const(0.0, name='')
    mode_parameters[ss_Ass_Bs_1_bypass_proc_selfix_1] = vf.add_const(0.0, name='')
    mode_parameters[ss_Ass_Bs_1_bypass_proc_selfix_2] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[ss_Ass_Bs_1_bypass_triv] = (sym.heaviside(((sym.Const(0.0) - sym.abs(ss_Ass_Bs_1_bypass_A)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - sym.abs(ss_Ass_Bs_1_bypass_B)) + sym.Const(1e-06))))
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(ss_Ass_Bs_1_bypass_triv, output=ss_Ass_Bs_1_bypass_proc_selfix_0))
    procedural_logic_entries.append(selfix(ss_Ass_Bs_1_bypass_triv, output=ss_Ass_Bs_1_bypass_proc_selfix_1))
    procedural_logic_entries.append(selfix(ss_Ass_Bs_1_bypass_triv, output=ss_Ass_Bs_1_bypass_proc_selfix_2))

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

