# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Lookup array 1x3 (linear_variable)'.

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

def build_typ_11__lookup_array_1x3_linear_variable_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Lookup array 1x3 (linear_variable)__11'

def build_typ_11__lookup_array_1x3_linear_variable_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_11__lookup_array_1x3_linear_variable_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Lookup_array_1x3_linear_variable_vClip: Var = vf.add_var('Lookup array 1x3 (linear_variable)__vClip_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Lookup_array_1x3_linear_variable_proc_select_2: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_select_2_' + template_name)
    Lookup_array_1x3_linear_variable_proc_select_3: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_select_3_' + template_name)
    Lookup_array_1x3_linear_variable_proc_select_4: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_select_4_' + template_name)
    Lookup_array_1x3_linear_variable_proc_select_7: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_select_7_' + template_name)
    Lookup_array_1x3_linear_variable_proc_select_8: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_select_8_' + template_name)
    Lookup_array_1x3_linear_variable_proc_select_9: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_select_9_' + template_name)
    Lookup_array_1x3_linear_variable_proc_selfix_0: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_selfix_0_' + template_name)
    Lookup_array_1x3_linear_variable_proc_selfix_1: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_selfix_1_' + template_name)
    Lookup_array_1x3_linear_variable_proc_selfix_5: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_selfix_5_' + template_name)
    Lookup_array_1x3_linear_variable_proc_selfix_6: Var = vf.add_var('Lookup array 1x3 (linear_variable)__proc_selfix_6_' + template_name)
    Lookup_array_1x3_linear_variable_m: Var = vf.add_var('Lookup array 1x3 (linear_variable)_m_' + template_name)
    Lookup_array_1x3_linear_variable_m1: Var = vf.add_var('Lookup array 1x3 (linear_variable)_m1_' + template_name)
    Lookup_array_1x3_linear_variable_m2: Var = vf.add_var('Lookup array 1x3 (linear_variable)_m2_' + template_name)
    Lookup_array_1x3_linear_variable_n: Var = vf.add_var('Lookup array 1x3 (linear_variable)_n_' + template_name)
    arr_x1: Var = vf.add_var('arr_x1_' + template_name)
    arr_x2: Var = vf.add_var('arr_x2_' + template_name)
    arr_x3: Var = vf.add_var('arr_x3_' + template_name)
    arr_y1: Var = vf.add_var('arr_y1_' + template_name)
    arr_y2: Var = vf.add_var('arr_y2_' + template_name)
    arr_y3: Var = vf.add_var('arr_y3_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Lookup_array_1x3_linear_variable_m1 - ((arr_y2 - arr_y1) / (arr_x2 - arr_x1))))
    algebraic_equations.append((Lookup_array_1x3_linear_variable_m2 - ((arr_y3 - arr_y2) / (arr_x3 - arr_x2))))
    algebraic_equations.append((Lookup_array_1x3_linear_variable_m - ((Lookup_array_1x3_linear_variable_proc_select_4 * ((Lookup_array_1x3_linear_variable_proc_selfix_0 * sym.Const(0.0)) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_selfix_0) * Lookup_array_1x3_linear_variable_m1))) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_select_4) * ((Lookup_array_1x3_linear_variable_proc_select_3 * Lookup_array_1x3_linear_variable_m1) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_select_3) * ((Lookup_array_1x3_linear_variable_proc_select_2 * Lookup_array_1x3_linear_variable_m2) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_select_2) * ((Lookup_array_1x3_linear_variable_proc_selfix_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_selfix_1) * Lookup_array_1x3_linear_variable_m2))))))))))
    algebraic_equations.append((Lookup_array_1x3_linear_variable_n - ((Lookup_array_1x3_linear_variable_proc_select_9 * ((Lookup_array_1x3_linear_variable_proc_selfix_5 * arr_y1) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_selfix_5) * (arr_y2 - (Lookup_array_1x3_linear_variable_m * arr_x2))))) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_select_9) * ((Lookup_array_1x3_linear_variable_proc_select_8 * (arr_y2 - (Lookup_array_1x3_linear_variable_m * arr_x2))) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_select_8) * ((Lookup_array_1x3_linear_variable_proc_select_7 * (arr_y3 - (Lookup_array_1x3_linear_variable_m * arr_x3))) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_select_7) * ((Lookup_array_1x3_linear_variable_proc_selfix_6 * arr_y3) + ((sym.Const(1.0) - Lookup_array_1x3_linear_variable_proc_selfix_6) * (arr_y3 - (Lookup_array_1x3_linear_variable_m * arr_x3))))))))))))
    algebraic_equations.append((yo - ((Lookup_array_1x3_linear_variable_m * yi) + Lookup_array_1x3_linear_variable_n)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Lookup_array_1x3_linear_variable_m1)
    algebraic_variables.append(Lookup_array_1x3_linear_variable_m2)
    algebraic_variables.append(Lookup_array_1x3_linear_variable_m)
    algebraic_variables.append(Lookup_array_1x3_linear_variable_n)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(yi)
    input_variables.append(arr_x1)
    input_variables.append(arr_x2)
    input_variables.append(arr_x3)
    input_variables.append(arr_y1)
    input_variables.append(arr_y2)
    input_variables.append(arr_y3)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Lookup_array_1x3_linear_variable_vClip] = vf.add_const(None, name='vClip')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Lookup_array_1x3_linear_variable_proc_selfix_0] = vf.add_const(0.0, name='')
    mode_parameters[Lookup_array_1x3_linear_variable_proc_selfix_1] = vf.add_const(0.0, name='')
    mode_parameters[Lookup_array_1x3_linear_variable_proc_select_2] = vf.add_const(0.0, name='')
    mode_parameters[Lookup_array_1x3_linear_variable_proc_select_3] = vf.add_const(0.0, name='')
    mode_parameters[Lookup_array_1x3_linear_variable_proc_select_4] = vf.add_const(0.0, name='')
    mode_parameters[Lookup_array_1x3_linear_variable_proc_selfix_5] = vf.add_const(0.0, name='')
    mode_parameters[Lookup_array_1x3_linear_variable_proc_selfix_6] = vf.add_const(0.0, name='')
    mode_parameters[Lookup_array_1x3_linear_variable_proc_select_7] = vf.add_const(0.0, name='')
    mode_parameters[Lookup_array_1x3_linear_variable_proc_select_8] = vf.add_const(0.0, name='')
    mode_parameters[Lookup_array_1x3_linear_variable_proc_select_9] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Lookup_array_1x3_linear_variable_m1] = ((arr_y2 - arr_y1) / (arr_x2 - arr_x1))
    initial_equations[Lookup_array_1x3_linear_variable_m2] = ((arr_y3 - arr_y2) / (arr_x3 - arr_x2))
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(Lookup_array_1x3_linear_variable_vClip, output=Lookup_array_1x3_linear_variable_proc_selfix_0))
    procedural_logic_entries.append(selfix(Lookup_array_1x3_linear_variable_vClip, output=Lookup_array_1x3_linear_variable_proc_selfix_1))
    procedural_logic_entries.append(sampled_value(output=Lookup_array_1x3_linear_variable_proc_select_2, source=sym.Comparison(lhs=yi, op=sym.CmpOp.LT, rhs=arr_x3)))
    procedural_logic_entries.append(sampled_value(output=Lookup_array_1x3_linear_variable_proc_select_3, source=sym.Comparison(lhs=yi, op=sym.CmpOp.LT, rhs=arr_x2)))
    procedural_logic_entries.append(sampled_value(output=Lookup_array_1x3_linear_variable_proc_select_4, source=sym.Comparison(lhs=yi, op=sym.CmpOp.LT, rhs=arr_x1)))
    procedural_logic_entries.append(selfix(Lookup_array_1x3_linear_variable_vClip, output=Lookup_array_1x3_linear_variable_proc_selfix_5))
    procedural_logic_entries.append(selfix(Lookup_array_1x3_linear_variable_vClip, output=Lookup_array_1x3_linear_variable_proc_selfix_6))
    procedural_logic_entries.append(sampled_value(output=Lookup_array_1x3_linear_variable_proc_select_7, source=sym.Comparison(lhs=yi, op=sym.CmpOp.LT, rhs=arr_x3)))
    procedural_logic_entries.append(sampled_value(output=Lookup_array_1x3_linear_variable_proc_select_8, source=sym.Comparison(lhs=yi, op=sym.CmpOp.LT, rhs=arr_x2)))
    procedural_logic_entries.append(sampled_value(output=Lookup_array_1x3_linear_variable_proc_select_9, source=sym.Comparison(lhs=yi, op=sym.CmpOp.LT, rhs=arr_x1)))

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

