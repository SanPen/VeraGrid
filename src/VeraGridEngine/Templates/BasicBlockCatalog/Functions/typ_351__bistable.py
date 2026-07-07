# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Bistable'.

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
from VeraGridEngine.Utils.procedural_logic import flipflop, sampled_value
from VeraGridEngine.enumerations import DeviceType

def build_typ_351__bistable_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Bistable__351'

def build_typ_351__bistable_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_351__bistable_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Bistable_PRIO_SET: Var = vf.add_var('Bistable__PRIO_SET_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Bistable_proc_flipflop_0: Var = vf.add_var('Bistable__proc_flipflop_0_' + template_name)
    Bistable_proc_select_1: Var = vf.add_var('Bistable__proc_select_1_' + template_name)
    Bistable_proc_select_2: Var = vf.add_var('Bistable__proc_select_2_' + template_name)
    Bistable_xSR: Var = vf.add_var('Bistable_xSR_' + template_name)
    Q: Var = vf.add_var('Q_' + template_name)
    R: Var = vf.add_var('R_' + template_name)
    S: Var = vf.add_var('S_' + template_name)
    not_Q: Var = vf.add_var('not_Q_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Bistable_xSR - Bistable_proc_flipflop_0))
    algebraic_equations.append((Q - ((Bistable_proc_select_2 * ((Bistable_proc_select_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Bistable_proc_select_1) * sym.Const(1.0)))) + ((sym.Const(1.0) - Bistable_proc_select_2) * Bistable_xSR))))
    algebraic_equations.append((not_Q - (sym.Const(1.0) - Q)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Bistable_xSR)
    algebraic_variables.append(Q)
    algebraic_variables.append(not_Q)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(S)
    input_variables.append(R)
    output_variables: list[Var] = list()
    output_variables.append(Q)
    output_variables.append(not_Q)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Bistable_PRIO_SET] = vf.add_const(None, name='PRIO_SET')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Bistable_proc_flipflop_0] = vf.add_const(0.0, name='')
    mode_parameters[Bistable_proc_select_1] = vf.add_const(0.0, name='')
    mode_parameters[Bistable_proc_select_2] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(flipflop(S, R, output=Bistable_proc_flipflop_0))
    procedural_logic_entries.append(sampled_value(output=Bistable_proc_select_1, source=sym.Comparison(lhs=Bistable_PRIO_SET, op=sym.CmpOp.LT, rhs=0.5)))
    procedural_logic_entries.append(sampled_value(output=Bistable_proc_select_2, source=(S * R)))

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

