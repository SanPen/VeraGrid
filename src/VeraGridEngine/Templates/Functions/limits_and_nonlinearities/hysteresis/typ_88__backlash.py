# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Backlash'.

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

def build_typ_88__backlash_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Backlash__88'

def build_typ_88__backlash_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_88__backlash_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Backlash_db: Var = vf.add_var('Backlash__db_' + template_name)
    # Declare the state variables used by the template.
    Backlash_x: Var = vf.add_var('Backlash__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    Backlash_proc_select_0: Var = vf.add_var('Backlash__proc_select_0_' + template_name)
    Backlash_proc_select_1: Var = vf.add_var('Backlash__proc_select_1_' + template_name)
    Backlash_proc_selfix_2: Var = vf.add_var('Backlash__proc_selfix_2_' + template_name)
    Backlash_d: Var = vf.add_var('Backlash_d_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_Backlash_x: Var = vf.add_diff_var('d_Backlash__x_' + template_name, base_var=Backlash_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((Backlash_d / sym.Const(0.01)))
    state_variables: list[Var] = list()
    state_variables.append(Backlash_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Backlash_d - ((Backlash_proc_selfix_2 * sym.Const(0.0)) + ((sym.Const(1.0) - Backlash_proc_selfix_2) * ((Backlash_proc_select_1 * ((yi - Backlash_x) - Backlash_db)) + ((sym.Const(1.0) - Backlash_proc_select_1) * ((Backlash_proc_select_0 * ((yi - Backlash_x) + Backlash_db)) + ((sym.Const(1.0) - Backlash_proc_select_0) * sym.Const(0.0)))))))))
    algebraic_equations.append((yo - Backlash_x))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Backlash_d)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Backlash_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Backlash_db] = vf.add_const(None, name='db')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Backlash_proc_select_0] = vf.add_const(0.0, name='')
    mode_parameters[Backlash_proc_select_1] = vf.add_const(0.0, name='')
    mode_parameters[Backlash_proc_selfix_2] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Backlash_x] = yo
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=Backlash_proc_select_0, source=(sym.heaviside((((-Backlash_db) - (yi - Backlash_x)) + 1e-06)) * sym.heaviside(((Backlash_db - 0.0) - 1e-06)))))
    procedural_logic_entries.append(sampled_value(output=Backlash_proc_select_1, source=(sym.heaviside((((yi - Backlash_x) - Backlash_db) + 1e-06)) * sym.heaviside(((Backlash_db - 0.0) - 1e-06)))))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Backlash_db, op=sym.CmpOp.LE, rhs=0.0), output=Backlash_proc_selfix_2))

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

