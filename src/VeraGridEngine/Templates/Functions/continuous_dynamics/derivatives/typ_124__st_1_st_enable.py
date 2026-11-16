# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'sT/(1+sT) _enable'.

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

def build_typ_124__st_1_st_enable_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'sT/(1+sT) _enable__124'

def build_typ_124__st_1_st_enable_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_124__st_1_st_enable_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    sT_1_sT_enable_T: Var = vf.add_var('sT/(1+sT) _enable__T_' + template_name)
    # Declare the state variables used by the template.
    sT_1_sT_enable_x: Var = vf.add_var('sT/(1+sT) _enable__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    sT_1_sT_enable_proc_selfix_0: Var = vf.add_var('sT/(1+sT) _enable__proc_selfix_0_' + template_name)
    sT_1_sT_enable_dx: Var = vf.add_var('sT/(1+sT) _enable_dx_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_sT_1_sT_enable_x: Var = vf.add_diff_var('d_sT/(1+sT) _enable__x_' + template_name, base_var=sT_1_sT_enable_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(sT_1_sT_enable_dx)
    state_variables: list[Var] = list()
    state_variables.append(sT_1_sT_enable_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((sT_1_sT_enable_dx - ((sT_1_sT_enable_proc_selfix_0 * ((yi - sT_1_sT_enable_x) / sT_1_sT_enable_T)) + ((sym.Const(1.0) - sT_1_sT_enable_proc_selfix_0) * sym.Const(0.0)))))
    algebraic_equations.append((yo - (sT_1_sT_enable_T * sT_1_sT_enable_dx)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(sT_1_sT_enable_dx)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_sT_1_sT_enable_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[sT_1_sT_enable_T] = vf.add_const(None, name='T')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[sT_1_sT_enable_proc_selfix_0] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=sT_1_sT_enable_T, op=sym.CmpOp.GT, rhs=0.0), output=sT_1_sT_enable_proc_selfix_0))

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

