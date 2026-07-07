# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Pt/Pturb'.

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

def build_typ_407__pt_pturb_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Pt/Pturb__407'

def build_typ_407__pt_pturb_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_407__pt_pturb_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Pt_Pturb_PN: Var = vf.add_var('Pt/Pturb__PN_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Pt_Pturb_proc_select_1: Var = vf.add_var('Pt/Pturb__proc_select_1_' + template_name)
    Pt_Pturb_proc_selfix_0: Var = vf.add_var('Pt/Pturb__proc_selfix_0_' + template_name)
    cosn: Var = vf.add_var('cosn_' + template_name)
    pt: Var = vf.add_var('pt_' + template_name)
    pturb: Var = vf.add_var('pturb_' + template_name)
    sgnn: Var = vf.add_var('sgnn_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((pt - ((Pt_Pturb_proc_select_1 * ((pturb * Pt_Pturb_PN) / (sgnn * cosn))) + ((sym.Const(1.0) - Pt_Pturb_proc_select_1) * pturb))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(pt)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(pturb)
    input_variables.append(sgnn)
    input_variables.append(cosn)
    output_variables: list[Var] = list()
    output_variables.append(pt)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Pt_Pturb_PN] = vf.add_const(None, name='PN')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Pt_Pturb_proc_selfix_0] = vf.add_const(0.0, name='')
    mode_parameters[Pt_Pturb_proc_select_1] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[pturb] = ((Pt_Pturb_proc_selfix_0 * (((pt * sgnn) * cosn) / Pt_Pturb_PN)) + ((sym.Const(1.0) - Pt_Pturb_proc_selfix_0) * pt))
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Pt_Pturb_PN, op=sym.CmpOp.GT, rhs=0.0), output=Pt_Pturb_proc_selfix_0))
    procedural_logic_entries.append(sampled_value(output=Pt_Pturb_proc_select_1, source=sym.Comparison(lhs=Pt_Pturb_PN, op=sym.CmpOp.GT, rhs=0.0)))

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

