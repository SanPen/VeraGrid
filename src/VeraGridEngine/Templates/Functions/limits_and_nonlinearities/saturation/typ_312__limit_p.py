# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Limit [p'.

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

def build_typ_312__limit_p_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Limit [p__312'

def build_typ_312__limit_p_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_312__limit_p_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Limit_p_eps: Var = vf.add_var('Limit [p__eps_' + template_name)
    Limit_p_y_max: Var = vf.add_var('Limit [p__y_max_' + template_name)
    Limit_p_y_min: Var = vf.add_var('Limit [p__y_min_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Limit_p_proc_flipflop_10: Var = vf.add_var('Limit [p__proc_flipflop_10_' + template_name)
    Limit_p_proc_flipflop_8: Var = vf.add_var('Limit [p__proc_flipflop_8_' + template_name)
    Limit_p_proc_select_12: Var = vf.add_var('Limit [p__proc_select_12_' + template_name)
    Limit_p_proc_select_13: Var = vf.add_var('Limit [p__proc_select_13_' + template_name)
    Limit_p_proc_select_const_0: Var = vf.add_var('Limit [p__proc_select_const_0_' + template_name)
    Limit_p_proc_select_const_2: Var = vf.add_var('Limit [p__proc_select_const_2_' + template_name)
    Limit_p_proc_select_const_4: Var = vf.add_var('Limit [p__proc_select_const_4_' + template_name)
    Limit_p_proc_select_const_6: Var = vf.add_var('Limit [p__proc_select_const_6_' + template_name)
    Limit_p_proc_selfix_1: Var = vf.add_var('Limit [p__proc_selfix_1_' + template_name)
    Limit_p_proc_selfix_11: Var = vf.add_var('Limit [p__proc_selfix_11_' + template_name)
    Limit_p_proc_selfix_14: Var = vf.add_var('Limit [p__proc_selfix_14_' + template_name)
    Limit_p_proc_selfix_15: Var = vf.add_var('Limit [p__proc_selfix_15_' + template_name)
    Limit_p_proc_selfix_16: Var = vf.add_var('Limit [p__proc_selfix_16_' + template_name)
    Limit_p_proc_selfix_17: Var = vf.add_var('Limit [p__proc_selfix_17_' + template_name)
    Limit_p_proc_selfix_18: Var = vf.add_var('Limit [p__proc_selfix_18_' + template_name)
    Limit_p_proc_selfix_3: Var = vf.add_var('Limit [p__proc_selfix_3_' + template_name)
    Limit_p_proc_selfix_5: Var = vf.add_var('Limit [p__proc_selfix_5_' + template_name)
    Limit_p_proc_selfix_7: Var = vf.add_var('Limit [p__proc_selfix_7_' + template_name)
    Limit_p_proc_selfix_9: Var = vf.add_var('Limit [p__proc_selfix_9_' + template_name)
    Limit_p_rstmax: Var = vf.add_var('Limit [p_rstmax_' + template_name)
    Limit_p_rstmin: Var = vf.add_var('Limit [p_rstmin_' + template_name)
    Limit_p_setmax: Var = vf.add_var('Limit [p_setmax_' + template_name)
    Limit_p_setmin: Var = vf.add_var('Limit [p_setmin_' + template_name)
    Limit_p_yo_max: Var = vf.add_var('Limit [p_yo_max_' + template_name)
    Limit_p_yo_min: Var = vf.add_var('Limit [p_yo_min_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Limit_p_setmin - ((Limit_p_proc_selfix_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Limit_p_proc_selfix_1) * ((Limit_p_proc_select_const_0 * sym.Const(1.0)) + ((sym.Const(1.0) - Limit_p_proc_select_const_0) * sym.Const(0.0)))))))
    algebraic_equations.append((Limit_p_rstmin - ((Limit_p_proc_selfix_3 * sym.Const(0.0)) + ((sym.Const(1.0) - Limit_p_proc_selfix_3) * ((Limit_p_proc_select_const_2 * sym.Const(1.0)) + ((sym.Const(1.0) - Limit_p_proc_select_const_2) * sym.Const(0.0)))))))
    algebraic_equations.append((Limit_p_setmax - ((Limit_p_proc_selfix_5 * sym.Const(0.0)) + ((sym.Const(1.0) - Limit_p_proc_selfix_5) * ((Limit_p_proc_select_const_4 * sym.Const(1.0)) + ((sym.Const(1.0) - Limit_p_proc_select_const_4) * sym.Const(0.0)))))))
    algebraic_equations.append((Limit_p_rstmax - ((Limit_p_proc_selfix_7 * sym.Const(0.0)) + ((sym.Const(1.0) - Limit_p_proc_selfix_7) * ((Limit_p_proc_select_const_6 * sym.Const(1.0)) + ((sym.Const(1.0) - Limit_p_proc_select_const_6) * sym.Const(0.0)))))))
    algebraic_equations.append((Limit_p_yo_min - ((Limit_p_proc_selfix_9 * sym.Const(0.0)) + ((sym.Const(1.0) - Limit_p_proc_selfix_9) * Limit_p_proc_flipflop_8))))
    algebraic_equations.append((Limit_p_yo_max - ((Limit_p_proc_selfix_11 * sym.Const(0.0)) + ((sym.Const(1.0) - Limit_p_proc_selfix_11) * Limit_p_proc_flipflop_10))))
    algebraic_equations.append((yo - ((Limit_p_proc_selfix_14 * ((Limit_p_y_min + ((yi - Limit_p_y_min) * sym.heaviside((yi - Limit_p_y_min)))) - ((yi - Limit_p_y_max) * sym.heaviside((yi - Limit_p_y_max))))) + ((sym.Const(1.0) - Limit_p_proc_selfix_14) * ((Limit_p_proc_select_13 * Limit_p_y_min) + ((sym.Const(1.0) - Limit_p_proc_select_13) * ((Limit_p_proc_select_12 * Limit_p_y_max) + ((sym.Const(1.0) - Limit_p_proc_select_12) * yi))))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Limit_p_setmin)
    algebraic_variables.append(Limit_p_rstmin)
    algebraic_variables.append(Limit_p_setmax)
    algebraic_variables.append(Limit_p_rstmax)
    algebraic_variables.append(Limit_p_yo_min)
    algebraic_variables.append(Limit_p_yo_max)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Limit_p_eps] = vf.add_const(None, name='eps')
    event_parameters[Limit_p_y_max] = vf.add_const(None, name='y_max')
    event_parameters[Limit_p_y_min] = vf.add_const(None, name='y_min')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Limit_p_proc_select_const_0] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_1] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_select_const_2] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_3] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_select_const_4] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_5] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_select_const_6] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_7] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_flipflop_8] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_9] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_flipflop_10] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_11] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_select_12] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_select_13] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_14] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_15] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_16] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_17] = vf.add_const(0.0, name='')
    mode_parameters[Limit_p_proc_selfix_18] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Limit_p_setmin] = ((Limit_p_proc_selfix_15 * sym.heaviside(((Limit_p_y_min - yi) - sym.Const(1e-06)))) + ((sym.Const(1.0) - Limit_p_proc_selfix_15) * sym.heaviside(((Limit_p_y_min - (yi - Limit_p_eps)) - sym.Const(1e-06)))))
    initial_equations[Limit_p_rstmin] = ((Limit_p_proc_selfix_16 * sym.heaviside(((yi - Limit_p_y_min) - sym.Const(1e-06)))) + ((sym.Const(1.0) - Limit_p_proc_selfix_16) * sym.heaviside((((yi + Limit_p_eps) - Limit_p_y_min) - sym.Const(1e-06)))))
    initial_equations[Limit_p_setmax] = ((Limit_p_proc_selfix_17 * sym.heaviside(((yi - Limit_p_y_max) - sym.Const(1e-06)))) + ((sym.Const(1.0) - Limit_p_proc_selfix_17) * sym.heaviside((((yi + Limit_p_eps) - Limit_p_y_max) - sym.Const(1e-06)))))
    initial_equations[Limit_p_rstmax] = ((Limit_p_proc_selfix_18 * sym.heaviside(((Limit_p_y_max - yi) - sym.Const(1e-06)))) + ((sym.Const(1.0) - Limit_p_proc_selfix_18) * sym.heaviside(((Limit_p_y_max - (yi - Limit_p_eps)) - sym.Const(1e-06)))))
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=Limit_p_proc_select_const_0, source=(sym.heaviside(((Limit_p_y_min - (yi - Limit_p_eps)) - 1e-06)) * sym.heaviside(((Limit_p_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_p_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_p_proc_selfix_1))
    procedural_logic_entries.append(sampled_value(output=Limit_p_proc_select_const_2, source=(sym.heaviside((((yi + Limit_p_eps) - Limit_p_y_min) - 1e-06)) * sym.heaviside(((Limit_p_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_p_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_p_proc_selfix_3))
    procedural_logic_entries.append(sampled_value(output=Limit_p_proc_select_const_4, source=(sym.heaviside((((yi + Limit_p_eps) - Limit_p_y_max) - 1e-06)) * sym.heaviside(((Limit_p_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_p_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_p_proc_selfix_5))
    procedural_logic_entries.append(sampled_value(output=Limit_p_proc_select_const_6, source=(sym.heaviside(((Limit_p_y_max - (yi - Limit_p_eps)) - 1e-06)) * sym.heaviside(((Limit_p_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_p_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_p_proc_selfix_7))
    procedural_logic_entries.append(flipflop(Limit_p_setmin, Limit_p_rstmin, output=Limit_p_proc_flipflop_8))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_p_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_p_proc_selfix_9))
    procedural_logic_entries.append(flipflop(Limit_p_setmax, Limit_p_rstmax, output=Limit_p_proc_flipflop_10))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_p_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_p_proc_selfix_11))
    procedural_logic_entries.append(sampled_value(output=Limit_p_proc_select_12, source=(sym.heaviside(((Limit_p_yo_max - 0.5) - 1e-06)) * sym.heaviside(((Limit_p_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(sampled_value(output=Limit_p_proc_select_13, source=(sym.heaviside(((Limit_p_yo_min - 0.5) - 1e-06)) * sym.heaviside(((Limit_p_eps - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Limit_p_eps, op=sym.CmpOp.LE, rhs=0.0), output=Limit_p_proc_selfix_14))
    procedural_logic_entries.append(selfix((sym.heaviside(((Limit_p_y_min - (yi - Limit_p_eps)) - 1e-06)) * sym.heaviside((((yi + Limit_p_eps) - Limit_p_y_min) - 1e-06))), output=Limit_p_proc_selfix_15))
    procedural_logic_entries.append(selfix((sym.heaviside(((Limit_p_y_min - (yi - Limit_p_eps)) - 1e-06)) * sym.heaviside((((yi + Limit_p_eps) - Limit_p_y_min) - 1e-06))), output=Limit_p_proc_selfix_16))
    procedural_logic_entries.append(selfix((sym.heaviside((((yi + Limit_p_eps) - Limit_p_y_max) - 1e-06)) * sym.heaviside(((Limit_p_y_max - (yi - Limit_p_eps)) - 1e-06))), output=Limit_p_proc_selfix_17))
    procedural_logic_entries.append(selfix((sym.heaviside((((yi + Limit_p_eps) - Limit_p_y_max) - 1e-06)) * sym.heaviside(((Limit_p_y_max - (yi - Limit_p_eps)) - 1e-06))), output=Limit_p_proc_selfix_18))

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

