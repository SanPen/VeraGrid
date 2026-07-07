# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Limit'.

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

def build_typ_310__limit_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Limit__310'

def build_typ_310__limit_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_310__limit_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Limit_eps: Var = vf.add_var('Limit__eps_' + template_name)
    Limit_y_max: Var = vf.add_var('Limit__y_max_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Limit_proc_flipflop_4: Var = vf.add_var('Limit__proc_flipflop_4_' + template_name)
    Limit_proc_select_6: Var = vf.add_var('Limit__proc_select_6_' + template_name)
    Limit_proc_select_const_0: Var = vf.add_var('Limit__proc_select_const_0_' + template_name)
    Limit_proc_select_const_2: Var = vf.add_var('Limit__proc_select_const_2_' + template_name)
    Limit_proc_selfix_1: Var = vf.add_var('Limit__proc_selfix_1_' + template_name)
    Limit_proc_selfix_3: Var = vf.add_var('Limit__proc_selfix_3_' + template_name)
    Limit_proc_selfix_5: Var = vf.add_var('Limit__proc_selfix_5_' + template_name)
    Limit_proc_selfix_7: Var = vf.add_var('Limit__proc_selfix_7_' + template_name)
    Limit_proc_selfix_8: Var = vf.add_var('Limit__proc_selfix_8_' + template_name)
    Limit_proc_selfix_9: Var = vf.add_var('Limit__proc_selfix_9_' + template_name)
    Limit_rstmax: Var = vf.add_var('Limit_rstmax_' + template_name)
    Limit_setmax: Var = vf.add_var('Limit_setmax_' + template_name)
    Limit_yo_max: Var = vf.add_var('Limit_yo_max_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Limit_setmax - ((Limit_proc_selfix_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Limit_proc_selfix_1) * ((Limit_proc_select_const_0 * sym.Const(1.0)) + ((sym.Const(1.0) - Limit_proc_select_const_0) * sym.Const(0.0)))))))
    algebraic_equations.append((Limit_rstmax - ((Limit_proc_selfix_3 * sym.Const(0.0)) + ((sym.Const(1.0) - Limit_proc_selfix_3) * ((Limit_proc_select_const_2 * sym.Const(1.0)) + ((sym.Const(1.0) - Limit_proc_select_const_2) * sym.Const(0.0)))))))
    algebraic_equations.append((Limit_yo_max - ((Limit_proc_selfix_5 * sym.Const(0.0)) + ((sym.Const(1.0) - Limit_proc_selfix_5) * Limit_proc_flipflop_4))))
    algebraic_equations.append((yo - ((Limit_proc_selfix_7 * ((yi * sym.heaviside((Limit_y_max - yi))) + (Limit_y_max * (sym.Const(1) - sym.heaviside((Limit_y_max - yi)))))) + ((sym.Const(1.0) - Limit_proc_selfix_7) * ((Limit_proc_select_6 * Limit_y_max) + ((sym.Const(1.0) - Limit_proc_select_6) * yi))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Limit_setmax)
    algebraic_variables.append(Limit_rstmax)
    algebraic_variables.append(Limit_yo_max)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Limit_eps] = vf.add_const(None, name='eps')
    event_parameters[Limit_y_max] = vf.add_const(None, name='y_max')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Limit_proc_select_const_0] = vf.add_const(0.0, name='')
    mode_parameters[Limit_proc_selfix_1] = vf.add_const(0.0, name='')
    mode_parameters[Limit_proc_select_const_2] = vf.add_const(0.0, name='')
    mode_parameters[Limit_proc_selfix_3] = vf.add_const(0.0, name='')
    mode_parameters[Limit_proc_flipflop_4] = vf.add_const(0.0, name='')
    mode_parameters[Limit_proc_selfix_5] = vf.add_const(0.0, name='')
    mode_parameters[Limit_proc_select_6] = vf.add_const(0.0, name='')
    mode_parameters[Limit_proc_selfix_7] = vf.add_const(0.0, name='')
    mode_parameters[Limit_proc_selfix_8] = vf.add_const(0.0, name='')
    mode_parameters[Limit_proc_selfix_9] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Limit_setmax] = ((Limit_proc_selfix_8 * sym.heaviside(((yi - Limit_y_max) - sym.Const(1e-06)))) + ((sym.Const(1.0) - Limit_proc_selfix_8) * sym.heaviside((((yi + Limit_eps) - Limit_y_max) - sym.Const(1e-06)))))
    initial_equations[Limit_rstmax] = ((Limit_proc_selfix_9 * sym.heaviside(((Limit_y_max - yi) - sym.Const(1e-06)))) + ((sym.Const(1.0) - Limit_proc_selfix_9) * sym.heaviside(((Limit_y_max - (yi - Limit_eps)) - sym.Const(1e-06)))))
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=Limit_proc_select_const_0, source=(sym.heaviside((((yi + Limit_eps) - Limit_y_max) - 1e-06)) * sym.heaviside(((Limit_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_proc_selfix_1))
    procedural_logic_entries.append(sampled_value(output=Limit_proc_select_const_2, source=(sym.heaviside(((Limit_y_max - (yi - Limit_eps)) - 1e-06)) * sym.heaviside(((Limit_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_proc_selfix_3))
    procedural_logic_entries.append(flipflop(Limit_setmax, Limit_rstmax, output=Limit_proc_flipflop_4))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_proc_selfix_5))
    procedural_logic_entries.append(sampled_value(output=Limit_proc_select_6, source=sym.Comparison(lhs=Limit_yo_max, op=sym.CmpOp.GT, rhs=0.5)))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_proc_selfix_7))
    procedural_logic_entries.append(selfix((sym.heaviside((((yi + Limit_eps) - Limit_y_max) - 1e-06)) * sym.heaviside(((Limit_y_max - (yi - Limit_eps)) - 1e-06))), output=Limit_proc_selfix_8))
    procedural_logic_entries.append(selfix((sym.heaviside((((yi + Limit_eps) - Limit_y_max) - 1e-06)) * sym.heaviside(((Limit_y_max - (yi - Limit_eps)) - 1e-06))), output=Limit_proc_selfix_9))

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

