# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'K(1+sTd)/((1+sTa)(1+sTb)s) (p'.

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

def build_typ_203__k_1_std_1_sta_1_stb_s_p_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'K(1+sTd)/((1+sTa)(1+sTb)s) (p__203'

def build_typ_203__k_1_std_1_sta_1_stb_s_p_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_203__k_1_std_1_sta_1_stb_s_p_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    K_1_sTd_1_sTa_1_sTb_s_p_K: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__K_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_Ta: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__Ta_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_Tb: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__Tb_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_Td: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__Td_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_y_max: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__y_max_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_y_min: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__y_min_' + template_name)
    # Declare the state variables used by the template.
    K_1_sTd_1_sTa_1_sTb_s_p_xa: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__xa_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_xb: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__xb_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_xc: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__xc_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_0: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__proc_selfix_0_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_1: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__proc_selfix_1_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_2: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__proc_selfix_2_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_3: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p__proc_selfix_3_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_dxa: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p_dxa_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_xaout: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p_xaout_' + template_name)
    K_1_sTd_1_sTa_1_sTb_s_p_xbout: Var = vf.add_var('K(1+sTd)/((1+sTa)(1+sTb)s) (p_xbout_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_K_1_sTd_1_sTa_1_sTb_s_p_xa: Var = vf.add_diff_var('d_K(1+sTd)/((1+sTa)(1+sTb)s) (p__xa_' + template_name, base_var=K_1_sTd_1_sTa_1_sTb_s_p_xa)
    d_K_1_sTd_1_sTa_1_sTb_s_p_xb: Var = vf.add_diff_var('d_K(1+sTd)/((1+sTa)(1+sTb)s) (p__xb_' + template_name, base_var=K_1_sTd_1_sTa_1_sTb_s_p_xb)
    d_K_1_sTd_1_sTa_1_sTb_s_p_xc: Var = vf.add_diff_var('d_K(1+sTd)/((1+sTa)(1+sTb)s) (p__xc_' + template_name, base_var=K_1_sTd_1_sTa_1_sTb_s_p_xc)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(K_1_sTd_1_sTa_1_sTb_s_p_dxa)
    state_equations.append(((K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_2 * ((K_1_sTd_1_sTa_1_sTb_s_p_xaout - K_1_sTd_1_sTa_1_sTb_s_p_xb) / K_1_sTd_1_sTa_1_sTb_s_p_Tb)) + ((sym.Const(1.0) - K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_2) * sym.Const(0.0))))
    state_equations.append(K_1_sTd_1_sTa_1_sTb_s_p_xbout)
    state_variables: list[Var] = list()
    state_variables.append(K_1_sTd_1_sTa_1_sTb_s_p_xa)
    state_variables.append(K_1_sTd_1_sTa_1_sTb_s_p_xb)
    state_variables.append(K_1_sTd_1_sTa_1_sTb_s_p_xc)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((K_1_sTd_1_sTa_1_sTb_s_p_dxa - ((K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_0 * (((K_1_sTd_1_sTa_1_sTb_s_p_K * yi) - K_1_sTd_1_sTa_1_sTb_s_p_xa) / K_1_sTd_1_sTa_1_sTb_s_p_Ta)) + ((sym.Const(1.0) - K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_0) * sym.Const(0.0)))))
    algebraic_equations.append((K_1_sTd_1_sTa_1_sTb_s_p_xaout - ((K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_1 * (K_1_sTd_1_sTa_1_sTb_s_p_xa + (K_1_sTd_1_sTa_1_sTb_s_p_Td * K_1_sTd_1_sTa_1_sTb_s_p_dxa))) + ((sym.Const(1.0) - K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_1) * (K_1_sTd_1_sTa_1_sTb_s_p_K * yi)))))
    algebraic_equations.append((K_1_sTd_1_sTa_1_sTb_s_p_xbout - ((K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_3 * K_1_sTd_1_sTa_1_sTb_s_p_xb) + ((sym.Const(1.0) - K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_3) * K_1_sTd_1_sTa_1_sTb_s_p_xaout))))
    algebraic_equations.append((yo - ((K_1_sTd_1_sTa_1_sTb_s_p_y_min + ((K_1_sTd_1_sTa_1_sTb_s_p_xc - K_1_sTd_1_sTa_1_sTb_s_p_y_min) * sym.heaviside((K_1_sTd_1_sTa_1_sTb_s_p_xc - K_1_sTd_1_sTa_1_sTb_s_p_y_min)))) - ((K_1_sTd_1_sTa_1_sTb_s_p_xc - K_1_sTd_1_sTa_1_sTb_s_p_y_max) * sym.heaviside((K_1_sTd_1_sTa_1_sTb_s_p_xc - K_1_sTd_1_sTa_1_sTb_s_p_y_max))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(K_1_sTd_1_sTa_1_sTb_s_p_dxa)
    algebraic_variables.append(K_1_sTd_1_sTa_1_sTb_s_p_xaout)
    algebraic_variables.append(K_1_sTd_1_sTa_1_sTb_s_p_xbout)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_K_1_sTd_1_sTa_1_sTb_s_p_xa)
    differential_variables.append(d_K_1_sTd_1_sTa_1_sTb_s_p_xb)
    differential_variables.append(d_K_1_sTd_1_sTa_1_sTb_s_p_xc)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[K_1_sTd_1_sTa_1_sTb_s_p_K] = vf.add_const(None, name='K')
    event_parameters[K_1_sTd_1_sTa_1_sTb_s_p_Td] = vf.add_const(None, name='Td')
    event_parameters[K_1_sTd_1_sTa_1_sTb_s_p_Ta] = vf.add_const(None, name='Ta')
    event_parameters[K_1_sTd_1_sTa_1_sTb_s_p_Tb] = vf.add_const(None, name='Tb')
    event_parameters[K_1_sTd_1_sTa_1_sTb_s_p_y_max] = vf.add_const(None, name='y_max')
    event_parameters[K_1_sTd_1_sTa_1_sTb_s_p_y_min] = vf.add_const(None, name='y_min')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_0] = vf.add_const(0.0, name='')
    mode_parameters[K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_1] = vf.add_const(0.0, name='')
    mode_parameters[K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_2] = vf.add_const(0.0, name='')
    mode_parameters[K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_3] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=K_1_sTd_1_sTa_1_sTb_s_p_Ta, op=sym.CmpOp.GT, rhs=0.0), output=K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_0))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=K_1_sTd_1_sTa_1_sTb_s_p_Ta, op=sym.CmpOp.GT, rhs=0.0), output=K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_1))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=K_1_sTd_1_sTa_1_sTb_s_p_Tb, op=sym.CmpOp.GT, rhs=0.0), output=K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_2))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=K_1_sTd_1_sTa_1_sTb_s_p_Tb, op=sym.CmpOp.GT, rhs=0.0), output=K_1_sTd_1_sTa_1_sTb_s_p_proc_selfix_3))

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

