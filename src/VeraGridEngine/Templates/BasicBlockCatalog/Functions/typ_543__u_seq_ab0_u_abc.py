# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'U seq/ab0 -> U abc'.

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
from VeraGridEngine.Utils.procedural_logic import movingavg, sampled_value
from VeraGridEngine.enumerations import DeviceType

def build_typ_543__u_seq_ab0_u_abc_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'U seq/ab0 -> U abc__543'

def build_typ_543__u_seq_ab0_u_abc_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_543__u_seq_ab0_u_abc_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    U_seq_ab0_U_abc_fn: Var = vf.add_var('U seq/ab0 -> U abc__fn_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    U_seq_ab0_U_abc_proc_movingavg_0: Var = vf.add_var('U seq/ab0 -> U abc__proc_movingavg_0_' + template_name)
    U_seq_ab0_U_abc_proc_movingavg_10: Var = vf.add_var('U seq/ab0 -> U abc__proc_movingavg_10_' + template_name)
    U_seq_ab0_U_abc_proc_movingavg_2: Var = vf.add_var('U seq/ab0 -> U abc__proc_movingavg_2_' + template_name)
    U_seq_ab0_U_abc_proc_movingavg_4: Var = vf.add_var('U seq/ab0 -> U abc__proc_movingavg_4_' + template_name)
    U_seq_ab0_U_abc_proc_movingavg_6: Var = vf.add_var('U seq/ab0 -> U abc__proc_movingavg_6_' + template_name)
    U_seq_ab0_U_abc_proc_movingavg_8: Var = vf.add_var('U seq/ab0 -> U abc__proc_movingavg_8_' + template_name)
    U_seq_ab0_U_abc_proc_select_1: Var = vf.add_var('U seq/ab0 -> U abc__proc_select_1_' + template_name)
    U_seq_ab0_U_abc_proc_select_11: Var = vf.add_var('U seq/ab0 -> U abc__proc_select_11_' + template_name)
    U_seq_ab0_U_abc_proc_select_3: Var = vf.add_var('U seq/ab0 -> U abc__proc_select_3_' + template_name)
    U_seq_ab0_U_abc_proc_select_5: Var = vf.add_var('U seq/ab0 -> U abc__proc_select_5_' + template_name)
    U_seq_ab0_U_abc_proc_select_7: Var = vf.add_var('U seq/ab0 -> U abc__proc_select_7_' + template_name)
    U_seq_ab0_U_abc_proc_select_9: Var = vf.add_var('U seq/ab0 -> U abc__proc_select_9_' + template_name)
    U_seq_ab0_U_abc_t: Var = vf.add_var('U seq/ab0 -> U abc_t_' + template_name)
    U_seq_ab0_U_abc_t0: Var = vf.add_var('U seq/ab0 -> U abc_t0_' + template_name)
    U_seq_ab0_U_abc_uai: Var = vf.add_var('U seq/ab0 -> U abc_uai_' + template_name)
    U_seq_ab0_U_abc_uar: Var = vf.add_var('U seq/ab0 -> U abc_uar_' + template_name)
    U_seq_ab0_U_abc_ubi: Var = vf.add_var('U seq/ab0 -> U abc_ubi_' + template_name)
    U_seq_ab0_U_abc_ubr: Var = vf.add_var('U seq/ab0 -> U abc_ubr_' + template_name)
    U_seq_ab0_U_abc_uci: Var = vf.add_var('U seq/ab0 -> U abc_uci_' + template_name)
    U_seq_ab0_U_abc_ucr: Var = vf.add_var('U seq/ab0 -> U abc_ucr_' + template_name)
    glob_time: Var = vf.add_var('glob_time_' + template_name)
    u0: Var = vf.add_var('u0_' + template_name)
    u0i: Var = vf.add_var('u0i_' + template_name)
    u0r: Var = vf.add_var('u0r_' + template_name)
    u1: Var = vf.add_var('u1_' + template_name)
    u1i: Var = vf.add_var('u1i_' + template_name)
    u1r: Var = vf.add_var('u1r_' + template_name)
    u2i: Var = vf.add_var('u2i_' + template_name)
    u2r: Var = vf.add_var('u2r_' + template_name)
    ua: Var = vf.add_var('ua_' + template_name)
    uab: Var = vf.add_var('uab_' + template_name)
    ub: Var = vf.add_var('ub_' + template_name)
    ubc: Var = vf.add_var('ubc_' + template_name)
    uc: Var = vf.add_var('uc_' + template_name)
    uca: Var = vf.add_var('uca_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((U_seq_ab0_U_abc_uar - (u1r + u0)))
    algebraic_equations.append((U_seq_ab0_U_abc_uai - sym.Const(0.0)))
    algebraic_equations.append((U_seq_ab0_U_abc_ubr - ((((-u1r) / sym.Const(2.0)) + ((u1i * sym.sqrt(sym.Const(3.0))) / sym.Const(2.0))) + u0)))
    algebraic_equations.append((U_seq_ab0_U_abc_ubi - sym.Const(0.0)))
    algebraic_equations.append((U_seq_ab0_U_abc_ucr - ((((-u1r) / sym.Const(2.0)) - ((u1i * sym.sqrt(sym.Const(3.0))) / sym.Const(2.0))) + u0)))
    algebraic_equations.append((U_seq_ab0_U_abc_uci - sym.Const(0.0)))
    algebraic_equations.append((ua - ((U_seq_ab0_U_abc_proc_select_1 * (sym.sqrt(sym.Const(2.0)) * sym.sqrt(((sym.Const(0.0) * sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_0))) + (U_seq_ab0_U_abc_proc_movingavg_0 * (sym.Const(1) - sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_0)))))))) + ((sym.Const(1.0) - U_seq_ab0_U_abc_proc_select_1) * u1))))
    algebraic_equations.append((ub - ((U_seq_ab0_U_abc_proc_select_3 * (sym.sqrt(sym.Const(2.0)) * sym.sqrt(((sym.Const(0.0) * sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_2))) + (U_seq_ab0_U_abc_proc_movingavg_2 * (sym.Const(1) - sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_2)))))))) + ((sym.Const(1.0) - U_seq_ab0_U_abc_proc_select_3) * u1))))
    algebraic_equations.append((uc - ((U_seq_ab0_U_abc_proc_select_5 * (sym.sqrt(sym.Const(2.0)) * sym.sqrt(((sym.Const(0.0) * sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_4))) + (U_seq_ab0_U_abc_proc_movingavg_4 * (sym.Const(1) - sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_4)))))))) + ((sym.Const(1.0) - U_seq_ab0_U_abc_proc_select_5) * u1))))
    algebraic_equations.append((uab - ((U_seq_ab0_U_abc_proc_select_7 * ((sym.sqrt(sym.Const(2.0)) / sym.sqrt(sym.Const(3.0))) * sym.sqrt(((sym.Const(0.0) * sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_6))) + (U_seq_ab0_U_abc_proc_movingavg_6 * (sym.Const(1) - sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_6)))))))) + ((sym.Const(1.0) - U_seq_ab0_U_abc_proc_select_7) * u1))))
    algebraic_equations.append((ubc - ((U_seq_ab0_U_abc_proc_select_9 * ((sym.sqrt(sym.Const(2.0)) / sym.sqrt(sym.Const(3.0))) * sym.sqrt(((sym.Const(0.0) * sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_8))) + (U_seq_ab0_U_abc_proc_movingavg_8 * (sym.Const(1) - sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_8)))))))) + ((sym.Const(1.0) - U_seq_ab0_U_abc_proc_select_9) * u1))))
    algebraic_equations.append((uca - ((U_seq_ab0_U_abc_proc_select_11 * ((sym.sqrt(sym.Const(2.0)) / sym.sqrt(sym.Const(3.0))) * sym.sqrt(((sym.Const(0.0) * sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_10))) + (U_seq_ab0_U_abc_proc_movingavg_10 * (sym.Const(1) - sym.heaviside((sym.Const(0.0) - U_seq_ab0_U_abc_proc_movingavg_10)))))))) + ((sym.Const(1.0) - U_seq_ab0_U_abc_proc_select_11) * u1))))
    algebraic_equations.append((U_seq_ab0_U_abc_t - glob_time))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(U_seq_ab0_U_abc_uar)
    algebraic_variables.append(U_seq_ab0_U_abc_uai)
    algebraic_variables.append(U_seq_ab0_U_abc_ubr)
    algebraic_variables.append(U_seq_ab0_U_abc_ubi)
    algebraic_variables.append(U_seq_ab0_U_abc_ucr)
    algebraic_variables.append(U_seq_ab0_U_abc_uci)
    algebraic_variables.append(ua)
    algebraic_variables.append(ub)
    algebraic_variables.append(uc)
    algebraic_variables.append(uab)
    algebraic_variables.append(ubc)
    algebraic_variables.append(uca)
    algebraic_variables.append(U_seq_ab0_U_abc_t)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(u1)
    input_variables.append(u1r)
    input_variables.append(u1i)
    input_variables.append(u2r)
    input_variables.append(u2i)
    input_variables.append(u0r)
    input_variables.append(u0i)
    input_variables.append(u0)
    output_variables: list[Var] = list()
    output_variables.append(ua)
    output_variables.append(ub)
    output_variables.append(uc)
    output_variables.append(uab)
    output_variables.append(ubc)
    output_variables.append(uca)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[U_seq_ab0_U_abc_fn] = vf.add_const(None, name='fn')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[U_seq_ab0_U_abc_proc_movingavg_0] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_select_1] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_movingavg_2] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_select_3] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_movingavg_4] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_select_5] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_movingavg_6] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_select_7] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_movingavg_8] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_select_9] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_movingavg_10] = vf.add_const(0.0, name='')
    mode_parameters[U_seq_ab0_U_abc_proc_select_11] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[U_seq_ab0_U_abc_t0] = glob_time
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(movingavg((U_seq_ab0_U_abc_uar * U_seq_ab0_U_abc_uar), ((1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))) / 20.0), (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))), output=U_seq_ab0_U_abc_proc_movingavg_0))
    procedural_logic_entries.append(sampled_value(output=U_seq_ab0_U_abc_proc_select_1, source=sym.Comparison(lhs=U_seq_ab0_U_abc_t, op=sym.CmpOp.GT, rhs=(U_seq_ab0_U_abc_t0 + (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))))))))))
    procedural_logic_entries.append(movingavg((U_seq_ab0_U_abc_ubr * U_seq_ab0_U_abc_ubr), ((1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))) / 20.0), (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))), output=U_seq_ab0_U_abc_proc_movingavg_2))
    procedural_logic_entries.append(sampled_value(output=U_seq_ab0_U_abc_proc_select_3, source=sym.Comparison(lhs=U_seq_ab0_U_abc_t, op=sym.CmpOp.GT, rhs=(U_seq_ab0_U_abc_t0 + (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))))))))))
    procedural_logic_entries.append(movingavg((U_seq_ab0_U_abc_ucr * U_seq_ab0_U_abc_ucr), ((1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))) / 20.0), (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))), output=U_seq_ab0_U_abc_proc_movingavg_4))
    procedural_logic_entries.append(sampled_value(output=U_seq_ab0_U_abc_proc_select_5, source=sym.Comparison(lhs=U_seq_ab0_U_abc_t, op=sym.CmpOp.GT, rhs=(U_seq_ab0_U_abc_t0 + (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))))))))))
    procedural_logic_entries.append(movingavg(((U_seq_ab0_U_abc_uar - U_seq_ab0_U_abc_ubr) * (U_seq_ab0_U_abc_uar - U_seq_ab0_U_abc_ubr)), ((1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))) / 20.0), (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))), output=U_seq_ab0_U_abc_proc_movingavg_6))
    procedural_logic_entries.append(sampled_value(output=U_seq_ab0_U_abc_proc_select_7, source=sym.Comparison(lhs=U_seq_ab0_U_abc_t, op=sym.CmpOp.GT, rhs=(U_seq_ab0_U_abc_t0 + (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))))))))))
    procedural_logic_entries.append(movingavg(((U_seq_ab0_U_abc_ubr - U_seq_ab0_U_abc_ucr) * (U_seq_ab0_U_abc_ubr - U_seq_ab0_U_abc_ucr)), ((1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))) / 20.0), (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))), output=U_seq_ab0_U_abc_proc_movingavg_8))
    procedural_logic_entries.append(sampled_value(output=U_seq_ab0_U_abc_proc_select_9, source=sym.Comparison(lhs=U_seq_ab0_U_abc_t, op=sym.CmpOp.GT, rhs=(U_seq_ab0_U_abc_t0 + (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))))))))))
    procedural_logic_entries.append(movingavg(((U_seq_ab0_U_abc_ucr - U_seq_ab0_U_abc_uar) * (U_seq_ab0_U_abc_ucr - U_seq_ab0_U_abc_uar)), ((1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))) / 20.0), (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0)))))), output=U_seq_ab0_U_abc_proc_movingavg_10))
    procedural_logic_entries.append(sampled_value(output=U_seq_ab0_U_abc_proc_select_11, source=sym.Comparison(lhs=U_seq_ab0_U_abc_t, op=sym.CmpOp.GT, rhs=(U_seq_ab0_U_abc_t0 + (1.0 / ((U_seq_ab0_U_abc_fn * sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))) + (10.0 * (1 - sym.heaviside((U_seq_ab0_U_abc_fn - 10.0))))))))))

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

