# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Limit [ppp'.

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
from VeraGridEngine.Utils.procedural_logic import sampled_value
from VeraGridEngine.enumerations import DeviceType

def build_typ_318__limit_ppp_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Limit [ppp__318'

def build_typ_318__limit_ppp_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_318__limit_ppp_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Limit_ppp_D_MAX: Var = vf.add_var('Limit [ppp__D_MAX_' + template_name)
    Limit_ppp_D_MIN: Var = vf.add_var('Limit [ppp__D_MIN_' + template_name)
    Limit_ppp_MAG_MAX: Var = vf.add_var('Limit [ppp__MAG_MAX_' + template_name)
    Limit_ppp_Q_MAX: Var = vf.add_var('Limit [ppp__Q_MAX_' + template_name)
    Limit_ppp_Q_MIN: Var = vf.add_var('Limit [ppp__Q_MIN_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Limit_ppp_proc_select_0: Var = vf.add_var('Limit [ppp__proc_select_0_' + template_name)
    Limit_ppp_proc_select_1: Var = vf.add_var('Limit [ppp__proc_select_1_' + template_name)
    Limit_ppp_proc_select_2: Var = vf.add_var('Limit [ppp__proc_select_2_' + template_name)
    Limit_ppp_proc_select_3: Var = vf.add_var('Limit [ppp__proc_select_3_' + template_name)
    Limit_ppp_proc_select_4: Var = vf.add_var('Limit [ppp__proc_select_4_' + template_name)
    Limit_ppp_proc_select_5: Var = vf.add_var('Limit [ppp__proc_select_5_' + template_name)
    Limit_ppp_proc_select_6: Var = vf.add_var('Limit [ppp__proc_select_6_' + template_name)
    Limit_ppp_proc_select_7: Var = vf.add_var('Limit [ppp__proc_select_7_' + template_name)
    Limit_ppp_iXref_nonprio: Var = vf.add_var('Limit [ppp_iXref_nonprio_' + template_name)
    Limit_ppp_iXref_prio: Var = vf.add_var('Limit [ppp_iXref_prio_' + template_name)
    Limit_ppp_max_nonprio: Var = vf.add_var('Limit [ppp_max_nonprio_' + template_name)
    Limit_ppp_max_prio: Var = vf.add_var('Limit [ppp_max_prio_' + template_name)
    Limit_ppp_min_nonprio: Var = vf.add_var('Limit [ppp_min_nonprio_' + template_name)
    Limit_ppp_min_prio: Var = vf.add_var('Limit [ppp_min_prio_' + template_name)
    Limit_ppp_remainder: Var = vf.add_var('Limit [ppp_remainder_' + template_name)
    Limit_ppp_y_nonprio: Var = vf.add_var('Limit [ppp_y_nonprio_' + template_name)
    Limit_ppp_y_prio: Var = vf.add_var('Limit [ppp_y_prio_' + template_name)
    PRIORITISE_AXIS: Var = vf.add_var('PRIORITISE_AXIS_' + template_name)
    d: Var = vf.add_var('d_' + template_name)
    q: Var = vf.add_var('q_' + template_name)
    yo_d: Var = vf.add_var('yo_d_' + template_name)
    yo_q: Var = vf.add_var('yo_q_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Limit_ppp_iXref_prio - ((Limit_ppp_proc_select_0 * d) + ((sym.Const(1.0) - Limit_ppp_proc_select_0) * q))))
    algebraic_equations.append((Limit_ppp_iXref_nonprio - ((Limit_ppp_proc_select_1 * q) + ((sym.Const(1.0) - Limit_ppp_proc_select_1) * d))))
    algebraic_equations.append((Limit_ppp_max_prio - ((((Limit_ppp_proc_select_2 * sym.abs(Limit_ppp_D_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_2) * sym.abs(Limit_ppp_Q_MAX))) * sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_2 * sym.abs(Limit_ppp_D_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_2) * sym.abs(Limit_ppp_Q_MAX)))))) + (sym.abs(Limit_ppp_MAG_MAX) * (sym.Const(1) - sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_2 * sym.abs(Limit_ppp_D_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_2) * sym.abs(Limit_ppp_Q_MAX))))))))))
    algebraic_equations.append((Limit_ppp_min_prio - ((((Limit_ppp_proc_select_3 * sym.abs(Limit_ppp_D_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_3) * sym.abs(Limit_ppp_Q_MIN))) * sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_3 * sym.abs(Limit_ppp_D_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_3) * sym.abs(Limit_ppp_Q_MIN)))))) + (sym.abs(Limit_ppp_MAG_MAX) * (sym.Const(1) - sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_3 * sym.abs(Limit_ppp_D_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_3) * sym.abs(Limit_ppp_Q_MIN))))))))))
    algebraic_equations.append((Limit_ppp_y_prio - (((-Limit_ppp_min_prio) + ((Limit_ppp_iXref_prio - (-Limit_ppp_min_prio)) * sym.heaviside((Limit_ppp_iXref_prio - (-Limit_ppp_min_prio))))) - ((Limit_ppp_iXref_prio - Limit_ppp_max_prio) * sym.heaviside((Limit_ppp_iXref_prio - Limit_ppp_max_prio))))))
    algebraic_equations.append((Limit_ppp_remainder - sym.sqrt(sym.abs(((Limit_ppp_MAG_MAX * Limit_ppp_MAG_MAX) - (Limit_ppp_y_prio * Limit_ppp_y_prio))))))
    algebraic_equations.append((Limit_ppp_max_nonprio - ((((((Limit_ppp_proc_select_4 * sym.abs(Limit_ppp_Q_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_4) * sym.abs(Limit_ppp_D_MAX))) * sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_4 * sym.abs(Limit_ppp_Q_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_4) * sym.abs(Limit_ppp_D_MAX)))))) + (sym.abs(Limit_ppp_MAG_MAX) * (sym.Const(1) - sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_4 * sym.abs(Limit_ppp_Q_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_4) * sym.abs(Limit_ppp_D_MAX)))))))) * sym.heaviside((Limit_ppp_remainder - ((((Limit_ppp_proc_select_4 * sym.abs(Limit_ppp_Q_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_4) * sym.abs(Limit_ppp_D_MAX))) * sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_4 * sym.abs(Limit_ppp_Q_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_4) * sym.abs(Limit_ppp_D_MAX)))))) + (sym.abs(Limit_ppp_MAG_MAX) * (sym.Const(1) - sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_4 * sym.abs(Limit_ppp_Q_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_4) * sym.abs(Limit_ppp_D_MAX))))))))))) + (Limit_ppp_remainder * (sym.Const(1) - sym.heaviside((Limit_ppp_remainder - ((((Limit_ppp_proc_select_4 * sym.abs(Limit_ppp_Q_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_4) * sym.abs(Limit_ppp_D_MAX))) * sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_4 * sym.abs(Limit_ppp_Q_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_4) * sym.abs(Limit_ppp_D_MAX)))))) + (sym.abs(Limit_ppp_MAG_MAX) * (sym.Const(1) - sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_4 * sym.abs(Limit_ppp_Q_MAX)) + ((sym.Const(1.0) - Limit_ppp_proc_select_4) * sym.abs(Limit_ppp_D_MAX)))))))))))))))
    algebraic_equations.append((Limit_ppp_min_nonprio - ((((((Limit_ppp_proc_select_5 * sym.abs(Limit_ppp_Q_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_5) * sym.abs(Limit_ppp_D_MIN))) * sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_5 * sym.abs(Limit_ppp_Q_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_5) * sym.abs(Limit_ppp_D_MIN)))))) + (sym.abs(Limit_ppp_MAG_MAX) * (sym.Const(1) - sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_5 * sym.abs(Limit_ppp_Q_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_5) * sym.abs(Limit_ppp_D_MIN)))))))) * sym.heaviside((Limit_ppp_remainder - ((((Limit_ppp_proc_select_5 * sym.abs(Limit_ppp_Q_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_5) * sym.abs(Limit_ppp_D_MIN))) * sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_5 * sym.abs(Limit_ppp_Q_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_5) * sym.abs(Limit_ppp_D_MIN)))))) + (sym.abs(Limit_ppp_MAG_MAX) * (sym.Const(1) - sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_5 * sym.abs(Limit_ppp_Q_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_5) * sym.abs(Limit_ppp_D_MIN))))))))))) + (Limit_ppp_remainder * (sym.Const(1) - sym.heaviside((Limit_ppp_remainder - ((((Limit_ppp_proc_select_5 * sym.abs(Limit_ppp_Q_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_5) * sym.abs(Limit_ppp_D_MIN))) * sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_5 * sym.abs(Limit_ppp_Q_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_5) * sym.abs(Limit_ppp_D_MIN)))))) + (sym.abs(Limit_ppp_MAG_MAX) * (sym.Const(1) - sym.heaviside((sym.abs(Limit_ppp_MAG_MAX) - ((Limit_ppp_proc_select_5 * sym.abs(Limit_ppp_Q_MIN)) + ((sym.Const(1.0) - Limit_ppp_proc_select_5) * sym.abs(Limit_ppp_D_MIN)))))))))))))))
    algebraic_equations.append((Limit_ppp_y_nonprio - (((-Limit_ppp_min_nonprio) + ((Limit_ppp_iXref_nonprio - (-Limit_ppp_min_nonprio)) * sym.heaviside((Limit_ppp_iXref_nonprio - (-Limit_ppp_min_nonprio))))) - ((Limit_ppp_iXref_nonprio - Limit_ppp_max_nonprio) * sym.heaviside((Limit_ppp_iXref_nonprio - Limit_ppp_max_nonprio))))))
    algebraic_equations.append((yo_d - ((Limit_ppp_proc_select_6 * Limit_ppp_y_prio) + ((sym.Const(1.0) - Limit_ppp_proc_select_6) * Limit_ppp_y_nonprio))))
    algebraic_equations.append((yo_q - ((Limit_ppp_proc_select_7 * Limit_ppp_y_nonprio) + ((sym.Const(1.0) - Limit_ppp_proc_select_7) * Limit_ppp_y_prio))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Limit_ppp_iXref_prio)
    algebraic_variables.append(Limit_ppp_iXref_nonprio)
    algebraic_variables.append(Limit_ppp_max_prio)
    algebraic_variables.append(Limit_ppp_min_prio)
    algebraic_variables.append(Limit_ppp_y_prio)
    algebraic_variables.append(Limit_ppp_remainder)
    algebraic_variables.append(Limit_ppp_max_nonprio)
    algebraic_variables.append(Limit_ppp_min_nonprio)
    algebraic_variables.append(Limit_ppp_y_nonprio)
    algebraic_variables.append(yo_d)
    algebraic_variables.append(yo_q)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(d)
    input_variables.append(q)
    input_variables.append(PRIORITISE_AXIS)
    output_variables: list[Var] = list()
    output_variables.append(yo_d)
    output_variables.append(yo_q)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Limit_ppp_D_MAX] = vf.add_const(None, name='D_MAX')
    event_parameters[Limit_ppp_Q_MAX] = vf.add_const(None, name='Q_MAX')
    event_parameters[Limit_ppp_MAG_MAX] = vf.add_const(None, name='MAG_MAX')
    event_parameters[Limit_ppp_D_MIN] = vf.add_const(None, name='D_MIN')
    event_parameters[Limit_ppp_Q_MIN] = vf.add_const(None, name='Q_MIN')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Limit_ppp_proc_select_0] = vf.add_const(0.0, name='')
    mode_parameters[Limit_ppp_proc_select_1] = vf.add_const(0.0, name='')
    mode_parameters[Limit_ppp_proc_select_2] = vf.add_const(0.0, name='')
    mode_parameters[Limit_ppp_proc_select_3] = vf.add_const(0.0, name='')
    mode_parameters[Limit_ppp_proc_select_4] = vf.add_const(0.0, name='')
    mode_parameters[Limit_ppp_proc_select_5] = vf.add_const(0.0, name='')
    mode_parameters[Limit_ppp_proc_select_6] = vf.add_const(0.0, name='')
    mode_parameters[Limit_ppp_proc_select_7] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=Limit_ppp_proc_select_0, source=sym.Comparison(lhs=PRIORITISE_AXIS, op=sym.CmpOp.LT, rhs=0.5)))
    procedural_logic_entries.append(sampled_value(output=Limit_ppp_proc_select_1, source=sym.Comparison(lhs=PRIORITISE_AXIS, op=sym.CmpOp.LT, rhs=0.5)))
    procedural_logic_entries.append(sampled_value(output=Limit_ppp_proc_select_2, source=sym.Comparison(lhs=PRIORITISE_AXIS, op=sym.CmpOp.LT, rhs=0.5)))
    procedural_logic_entries.append(sampled_value(output=Limit_ppp_proc_select_3, source=sym.Comparison(lhs=PRIORITISE_AXIS, op=sym.CmpOp.LT, rhs=0.5)))
    procedural_logic_entries.append(sampled_value(output=Limit_ppp_proc_select_4, source=sym.Comparison(lhs=PRIORITISE_AXIS, op=sym.CmpOp.LT, rhs=0.5)))
    procedural_logic_entries.append(sampled_value(output=Limit_ppp_proc_select_5, source=sym.Comparison(lhs=PRIORITISE_AXIS, op=sym.CmpOp.LT, rhs=0.5)))
    procedural_logic_entries.append(sampled_value(output=Limit_ppp_proc_select_6, source=sym.Comparison(lhs=PRIORITISE_AXIS, op=sym.CmpOp.LT, rhs=0.5)))
    procedural_logic_entries.append(sampled_value(output=Limit_ppp_proc_select_7, source=sym.Comparison(lhs=PRIORITISE_AXIS, op=sym.CmpOp.LT, rhs=0.5)))

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

