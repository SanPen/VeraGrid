# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Switch par 1->2 by par'.

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

def build_typ_508__switch_par_1_2_by_par_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Switch par 1->2 by par__508'

def build_typ_508__switch_par_1_2_by_par_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_508__switch_par_1_2_by_par_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Switch_par_1_2_by_par_K: Var = vf.add_var('Switch par 1->2 by par__K_' + template_name)
    Switch_par_1_2_by_par_sw: Var = vf.add_var('Switch par 1->2 by par__sw_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Switch_par_1_2_by_par_proc_selfix_const_0: Var = vf.add_var('Switch par 1->2 by par__proc_selfix_const_0_' + template_name)
    Switch_par_1_2_by_par_proc_selfix_const_1: Var = vf.add_var('Switch par 1->2 by par__proc_selfix_const_1_' + template_name)
    Switch_par_1_2_by_par_proc_selfix_const_2: Var = vf.add_var('Switch par 1->2 by par__proc_selfix_const_2_' + template_name)
    Switch_par_1_2_by_par_proc_selfix_const_3: Var = vf.add_var('Switch par 1->2 by par__proc_selfix_const_3_' + template_name)
    yo1: Var = vf.add_var('yo1_' + template_name)
    yo2: Var = vf.add_var('yo2_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo1 - ((Switch_par_1_2_by_par_proc_selfix_const_2 * sym.Const(0.0)) + ((sym.Const(1.0) - Switch_par_1_2_by_par_proc_selfix_const_2) * Switch_par_1_2_by_par_K))))
    algebraic_equations.append((yo2 - ((Switch_par_1_2_by_par_proc_selfix_const_3 * Switch_par_1_2_by_par_K) + ((sym.Const(1.0) - Switch_par_1_2_by_par_proc_selfix_const_3) * sym.Const(0.0)))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo1)
    algebraic_variables.append(yo2)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    output_variables.append(yo1)
    output_variables.append(yo2)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Switch_par_1_2_by_par_sw] = vf.add_const(None, name='sw')
    event_parameters[Switch_par_1_2_by_par_K] = vf.add_const(None, name='K')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Switch_par_1_2_by_par_proc_selfix_const_0] = vf.add_const(0.0, name='')
    mode_parameters[Switch_par_1_2_by_par_proc_selfix_const_1] = vf.add_const(0.0, name='')
    mode_parameters[Switch_par_1_2_by_par_proc_selfix_const_2] = vf.add_const(0.0, name='')
    mode_parameters[Switch_par_1_2_by_par_proc_selfix_const_3] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[yo1] = ((Switch_par_1_2_by_par_proc_selfix_const_0 * sym.Const(0.0)) + ((sym.Const(1.0) - Switch_par_1_2_by_par_proc_selfix_const_0) * Switch_par_1_2_by_par_K))
    initial_equations[yo2] = ((Switch_par_1_2_by_par_proc_selfix_const_1 * Switch_par_1_2_by_par_K) + ((sym.Const(1.0) - Switch_par_1_2_by_par_proc_selfix_const_1) * sym.Const(0.0)))
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(Switch_par_1_2_by_par_sw, output=Switch_par_1_2_by_par_proc_selfix_const_0))
    procedural_logic_entries.append(selfix(Switch_par_1_2_by_par_sw, output=Switch_par_1_2_by_par_proc_selfix_const_1))
    procedural_logic_entries.append(selfix(Switch_par_1_2_by_par_sw, output=Switch_par_1_2_by_par_proc_selfix_const_2))
    procedural_logic_entries.append(selfix(Switch_par_1_2_by_par_sw, output=Switch_par_1_2_by_par_proc_selfix_const_3))

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

