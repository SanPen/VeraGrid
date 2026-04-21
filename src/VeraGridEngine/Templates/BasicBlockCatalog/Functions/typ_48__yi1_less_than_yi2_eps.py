# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'yi1 less than yi2 _eps'.

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
from VeraGridEngine.Utils.procedural_logic import flipflop, sampled_value, selfix
from VeraGridEngine.enumerations import DeviceType

def build_typ_48__yi1_less_than_yi2_eps_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'yi1 less than yi2 _eps__48'

def build_typ_48__yi1_less_than_yi2_eps_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_48__yi1_less_than_yi2_eps_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    yi1_less_than_yi2_eps_eps: Var = vf.add_var('yi1 less than yi2 _eps__eps_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    yi1: Var = vf.add_var('yi1_' + template_name)
    yi1_less_than_yi2_eps_proc_flipflop_5: Var = vf.add_var('yi1 less than yi2 _eps__proc_flipflop_5_' + template_name)
    yi1_less_than_yi2_eps_proc_select_const_0: Var = vf.add_var('yi1 less than yi2 _eps__proc_select_const_0_' + template_name)
    yi1_less_than_yi2_eps_proc_select_const_2: Var = vf.add_var('yi1 less than yi2 _eps__proc_select_const_2_' + template_name)
    yi1_less_than_yi2_eps_proc_select_const_4: Var = vf.add_var('yi1 less than yi2 _eps__proc_select_const_4_' + template_name)
    yi1_less_than_yi2_eps_proc_selfix_1: Var = vf.add_var('yi1 less than yi2 _eps__proc_selfix_1_' + template_name)
    yi1_less_than_yi2_eps_proc_selfix_3: Var = vf.add_var('yi1 less than yi2 _eps__proc_selfix_3_' + template_name)
    yi1_less_than_yi2_eps_proc_selfix_6: Var = vf.add_var('yi1 less than yi2 _eps__proc_selfix_6_' + template_name)
    yi1_less_than_yi2_eps_proc_selfix_const_7: Var = vf.add_var('yi1 less than yi2 _eps__proc_selfix_const_7_' + template_name)
    yi1_less_than_yi2_eps_rst: Var = vf.add_var('yi1 less than yi2 _eps_rst_' + template_name)
    yi1_less_than_yi2_eps_set: Var = vf.add_var('yi1 less than yi2 _eps_set_' + template_name)
    yi2: Var = vf.add_var('yi2_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yi1_less_than_yi2_eps_set - ((yi1_less_than_yi2_eps_proc_selfix_1 * sym.Const(0.0)) + ((sym.Const(1.0) - yi1_less_than_yi2_eps_proc_selfix_1) * ((yi1_less_than_yi2_eps_proc_select_const_0 * sym.Const(1.0)) + ((sym.Const(1.0) - yi1_less_than_yi2_eps_proc_select_const_0) * sym.Const(0.0)))))))
    algebraic_equations.append((yi1_less_than_yi2_eps_rst - ((yi1_less_than_yi2_eps_proc_selfix_3 * sym.Const(0.0)) + ((sym.Const(1.0) - yi1_less_than_yi2_eps_proc_selfix_3) * ((yi1_less_than_yi2_eps_proc_select_const_2 * sym.Const(1.0)) + ((sym.Const(1.0) - yi1_less_than_yi2_eps_proc_select_const_2) * sym.Const(0.0)))))))
    algebraic_equations.append((yo - ((yi1_less_than_yi2_eps_proc_selfix_6 * ((yi1_less_than_yi2_eps_proc_select_const_4 * sym.Const(1.0)) + ((sym.Const(1.0) - yi1_less_than_yi2_eps_proc_select_const_4) * sym.Const(0.0)))) + ((sym.Const(1.0) - yi1_less_than_yi2_eps_proc_selfix_6) * yi1_less_than_yi2_eps_proc_flipflop_5))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yi1_less_than_yi2_eps_set)
    algebraic_variables.append(yi1_less_than_yi2_eps_rst)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(yi1)
    input_variables.append(yi2)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[yi1_less_than_yi2_eps_eps] = vf.add_const(None, name='eps')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[yi1_less_than_yi2_eps_proc_select_const_0] = vf.add_const(0.0, name='')
    mode_parameters[yi1_less_than_yi2_eps_proc_selfix_1] = vf.add_const(0.0, name='')
    mode_parameters[yi1_less_than_yi2_eps_proc_select_const_2] = vf.add_const(0.0, name='')
    mode_parameters[yi1_less_than_yi2_eps_proc_selfix_3] = vf.add_const(0.0, name='')
    mode_parameters[yi1_less_than_yi2_eps_proc_select_const_4] = vf.add_const(0.0, name='')
    mode_parameters[yi1_less_than_yi2_eps_proc_flipflop_5] = vf.add_const(0.0, name='')
    mode_parameters[yi1_less_than_yi2_eps_proc_selfix_6] = vf.add_const(0.0, name='')
    mode_parameters[yi1_less_than_yi2_eps_proc_selfix_const_7] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[yi1_less_than_yi2_eps_set] = ((yi1_less_than_yi2_eps_proc_selfix_const_7 * sym.Const(1.0)) + ((sym.Const(1.0) - yi1_less_than_yi2_eps_proc_selfix_const_7) * sym.Const(0.0)))
    initial_equations[yi1_less_than_yi2_eps_rst] = (sym.Const(1.0) - yi1_less_than_yi2_eps_set)
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=yi1_less_than_yi2_eps_proc_select_const_0, source=(sym.heaviside(((yi2 - (yi1 + yi1_less_than_yi2_eps_eps)) - 1e-06)) * sym.heaviside(((yi1_less_than_yi2_eps_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=yi1_less_than_yi2_eps_eps, op=sym.CmpOp.LE, rhs=0.0), output=yi1_less_than_yi2_eps_proc_selfix_1))
    procedural_logic_entries.append(sampled_value(output=yi1_less_than_yi2_eps_proc_select_const_2, source=(sym.heaviside((((yi1 - yi1_less_than_yi2_eps_eps) - yi2) - 1e-06)) * sym.heaviside(((yi1_less_than_yi2_eps_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=yi1_less_than_yi2_eps_eps, op=sym.CmpOp.LE, rhs=0.0), output=yi1_less_than_yi2_eps_proc_selfix_3))
    procedural_logic_entries.append(sampled_value(output=yi1_less_than_yi2_eps_proc_select_const_4, source=(sym.heaviside(((yi2 - yi1) - 1e-06)) * sym.heaviside(((0.0 - yi1_less_than_yi2_eps_eps) + 1e-06)))))
    procedural_logic_entries.append(flipflop(yi1_less_than_yi2_eps_set, yi1_less_than_yi2_eps_rst, output=yi1_less_than_yi2_eps_proc_flipflop_5))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=yi1_less_than_yi2_eps_eps, op=sym.CmpOp.LE, rhs=0.0), output=yi1_less_than_yi2_eps_proc_selfix_6))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=(yi1 + yi1_less_than_yi2_eps_eps), op=sym.CmpOp.LT, rhs=yi2), output=yi1_less_than_yi2_eps_proc_selfix_const_7))

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

