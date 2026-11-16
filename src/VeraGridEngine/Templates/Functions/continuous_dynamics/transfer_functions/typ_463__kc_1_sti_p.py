# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Kc+1/sTi [(p'.

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
from VeraGridEngine.Utils.procedural_logic import lastvalue, reset, sampled_value, selfix
from VeraGridEngine.enumerations import DeviceType

def build_typ_463__kc_1_sti_p_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Kc+1/sTi [(p__463'

def build_typ_463__kc_1_sti_p_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_463__kc_1_sti_p_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Kc_1_sTi_p_ControlTuning: Var = vf.add_var('Kc+1/sTi [(p__ControlTuning_' + template_name)
    Kc_1_sTi_p_K_p: Var = vf.add_var('Kc+1/sTi [(p__K_p_' + template_name)
    Kc_1_sTi_p_T_p: Var = vf.add_var('Kc+1/sTi [(p__T_p_' + template_name)
    Kc_1_sTi_p_theta_p: Var = vf.add_var('Kc+1/sTi [(p__theta_p_' + template_name)
    Kc_1_sTi_p_y_max: Var = vf.add_var('Kc+1/sTi [(p__y_max_' + template_name)
    Kc_1_sTi_p_y_min: Var = vf.add_var('Kc+1/sTi [(p__y_min_' + template_name)
    # Declare the state variables used by the template.
    Kc_1_sTi_p_x: Var = vf.add_var('Kc+1/sTi [(p__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    Kc_1_sTi_p_Kc: Var = vf.add_var('Kc+1/sTi [(p_Kc_' + template_name)
    Kc_1_sTi_p_Ti: Var = vf.add_var('Kc+1/sTi [(p_Ti_' + template_name)
    Kc_1_sTi_p_proc_lastvalue_12: Var = vf.add_var('Kc+1/sTi [(p__proc_lastvalue_12_' + template_name)
    Kc_1_sTi_p_proc_select_11: Var = vf.add_var('Kc+1/sTi [(p__proc_select_11_' + template_name)
    Kc_1_sTi_p_proc_select_13: Var = vf.add_var('Kc+1/sTi [(p__proc_select_13_' + template_name)
    Kc_1_sTi_p_proc_selfix_0: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_0_' + template_name)
    Kc_1_sTi_p_proc_selfix_1: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_1_' + template_name)
    Kc_1_sTi_p_proc_selfix_10: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_10_' + template_name)
    Kc_1_sTi_p_proc_selfix_2: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_2_' + template_name)
    Kc_1_sTi_p_proc_selfix_3: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_3_' + template_name)
    Kc_1_sTi_p_proc_selfix_4: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_4_' + template_name)
    Kc_1_sTi_p_proc_selfix_5: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_5_' + template_name)
    Kc_1_sTi_p_proc_selfix_6: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_6_' + template_name)
    Kc_1_sTi_p_proc_selfix_7: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_7_' + template_name)
    Kc_1_sTi_p_proc_selfix_8: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_8_' + template_name)
    Kc_1_sTi_p_proc_selfix_9: Var = vf.add_var('Kc+1/sTi [(p__proc_selfix_9_' + template_name)
    Kc_1_sTi_p_tau_c: Var = vf.add_var('Kc+1/sTi [(p_tau_c_' + template_name)
    hold: Var = vf.add_var('hold_' + template_name)
    rst: Var = vf.add_var('rst_' + template_name)
    x_rst: Var = vf.add_var('x_rst_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_Kc_1_sTi_p_x: Var = vf.add_diff_var('d_Kc+1/sTi [(p__x_' + template_name, base_var=Kc_1_sTi_p_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((Kc_1_sTi_p_proc_select_11 * sym.Const(0.0)) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_select_11) * ((sym.Const(1.0) / Kc_1_sTi_p_Ti) * yi))))
    state_variables: list[Var] = list()
    state_variables.append(Kc_1_sTi_p_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo - ((Kc_1_sTi_p_proc_select_13 * Kc_1_sTi_p_proc_lastvalue_12) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_select_13) * ((Kc_1_sTi_p_y_min + ((((Kc_1_sTi_p_Kc * yi) + ((Kc_1_sTi_p_y_min + ((Kc_1_sTi_p_x - Kc_1_sTi_p_y_min) * sym.heaviside((Kc_1_sTi_p_x - Kc_1_sTi_p_y_min)))) - ((Kc_1_sTi_p_x - Kc_1_sTi_p_y_max) * sym.heaviside((Kc_1_sTi_p_x - Kc_1_sTi_p_y_max))))) - Kc_1_sTi_p_y_min) * sym.heaviside((((Kc_1_sTi_p_Kc * yi) + ((Kc_1_sTi_p_y_min + ((Kc_1_sTi_p_x - Kc_1_sTi_p_y_min) * sym.heaviside((Kc_1_sTi_p_x - Kc_1_sTi_p_y_min)))) - ((Kc_1_sTi_p_x - Kc_1_sTi_p_y_max) * sym.heaviside((Kc_1_sTi_p_x - Kc_1_sTi_p_y_max))))) - Kc_1_sTi_p_y_min)))) - ((((Kc_1_sTi_p_Kc * yi) + ((Kc_1_sTi_p_y_min + ((Kc_1_sTi_p_x - Kc_1_sTi_p_y_min) * sym.heaviside((Kc_1_sTi_p_x - Kc_1_sTi_p_y_min)))) - ((Kc_1_sTi_p_x - Kc_1_sTi_p_y_max) * sym.heaviside((Kc_1_sTi_p_x - Kc_1_sTi_p_y_max))))) - Kc_1_sTi_p_y_max) * sym.heaviside((((Kc_1_sTi_p_Kc * yi) + ((Kc_1_sTi_p_y_min + ((Kc_1_sTi_p_x - Kc_1_sTi_p_y_min) * sym.heaviside((Kc_1_sTi_p_x - Kc_1_sTi_p_y_min)))) - ((Kc_1_sTi_p_x - Kc_1_sTi_p_y_max) * sym.heaviside((Kc_1_sTi_p_x - Kc_1_sTi_p_y_max))))) - Kc_1_sTi_p_y_max))))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Kc_1_sTi_p_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    input_variables.append(hold)
    input_variables.append(x_rst)
    input_variables.append(rst)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Kc_1_sTi_p_K_p] = vf.add_const(None, name='K_p')
    event_parameters[Kc_1_sTi_p_T_p] = vf.add_const(None, name='T_p')
    event_parameters[Kc_1_sTi_p_theta_p] = vf.add_const(None, name='theta_p')
    event_parameters[Kc_1_sTi_p_ControlTuning] = vf.add_const(None, name='ControlTuning')
    event_parameters[Kc_1_sTi_p_y_max] = vf.add_const(None, name='y_max')
    event_parameters[Kc_1_sTi_p_y_min] = vf.add_const(None, name='y_min')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Kc_1_sTi_p_proc_selfix_0] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_1] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_2] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_3] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_4] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_5] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_6] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_7] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_8] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_9] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_selfix_10] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_select_11] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_lastvalue_12] = vf.add_const(0.0, name='')
    mode_parameters[Kc_1_sTi_p_proc_select_13] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Kc_1_sTi_p_tau_c] = ((Kc_1_sTi_p_proc_selfix_2 * (((sym.Const(0.1) * Kc_1_sTi_p_T_p) * sym.heaviside(((sym.Const(0.1) * Kc_1_sTi_p_T_p) - (sym.Const(0.8) * Kc_1_sTi_p_theta_p)))) + ((sym.Const(0.8) * Kc_1_sTi_p_theta_p) * (sym.Const(1) - sym.heaviside(((sym.Const(0.1) * Kc_1_sTi_p_T_p) - (sym.Const(0.8) * Kc_1_sTi_p_theta_p))))))) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_2) * ((Kc_1_sTi_p_proc_selfix_1 * (((sym.Const(1.0) * Kc_1_sTi_p_T_p) * sym.heaviside(((sym.Const(1.0) * Kc_1_sTi_p_T_p) - (sym.Const(8.0) * Kc_1_sTi_p_theta_p)))) + ((sym.Const(8.0) * Kc_1_sTi_p_theta_p) * (sym.Const(1) - sym.heaviside(((sym.Const(1.0) * Kc_1_sTi_p_T_p) - (sym.Const(8.0) * Kc_1_sTi_p_theta_p))))))) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_1) * ((Kc_1_sTi_p_proc_selfix_0 * (((sym.Const(10.0) * Kc_1_sTi_p_T_p) * sym.heaviside(((sym.Const(10.0) * Kc_1_sTi_p_T_p) - (sym.Const(80.0) * Kc_1_sTi_p_theta_p)))) + ((sym.Const(80.0) * Kc_1_sTi_p_theta_p) * (sym.Const(1) - sym.heaviside(((sym.Const(10.0) * Kc_1_sTi_p_T_p) - (sym.Const(80.0) * Kc_1_sTi_p_theta_p))))))) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_0) * sym.Const(0.0)))))))
    initial_equations[Kc_1_sTi_p_Kc] = ((Kc_1_sTi_p_proc_selfix_6 * (((sym.Const(1.0) / Kc_1_sTi_p_K_p) * Kc_1_sTi_p_T_p) / (Kc_1_sTi_p_theta_p + Kc_1_sTi_p_tau_c))) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_6) * ((Kc_1_sTi_p_proc_selfix_5 * (((sym.Const(1.0) / Kc_1_sTi_p_K_p) * Kc_1_sTi_p_T_p) / (Kc_1_sTi_p_theta_p + Kc_1_sTi_p_tau_c))) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_5) * ((Kc_1_sTi_p_proc_selfix_4 * (((sym.Const(1.0) / Kc_1_sTi_p_K_p) * Kc_1_sTi_p_T_p) / (Kc_1_sTi_p_theta_p + Kc_1_sTi_p_tau_c))) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_4) * ((Kc_1_sTi_p_proc_selfix_3 * ((sym.Const(0.586) / Kc_1_sTi_p_K_p) * ((Kc_1_sTi_p_T_p / ((Kc_1_sTi_p_theta_p * sym.heaviside((Kc_1_sTi_p_theta_p - sym.Const(1e-06)))) + (sym.Const(1e-06) * (sym.Const(1) - sym.heaviside((Kc_1_sTi_p_theta_p - sym.Const(1e-06))))))) ** sym.Const(0.916)))) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_3) * ((sym.Const(0.859) / Kc_1_sTi_p_K_p) * ((Kc_1_sTi_p_T_p / ((Kc_1_sTi_p_theta_p * sym.heaviside((Kc_1_sTi_p_theta_p - sym.Const(1e-06)))) + (sym.Const(1e-06) * (sym.Const(1) - sym.heaviside((Kc_1_sTi_p_theta_p - sym.Const(1e-06))))))) ** sym.Const(0.977)))))))))))
    initial_equations[Kc_1_sTi_p_Ti] = ((Kc_1_sTi_p_proc_selfix_10 * Kc_1_sTi_p_T_p) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_10) * ((Kc_1_sTi_p_proc_selfix_9 * Kc_1_sTi_p_T_p) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_9) * ((Kc_1_sTi_p_proc_selfix_8 * Kc_1_sTi_p_T_p) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_8) * ((Kc_1_sTi_p_proc_selfix_7 * (Kc_1_sTi_p_T_p / (sym.Const(1.03) - (sym.Const(0.165) * (((Kc_1_sTi_p_theta_p * sym.heaviside((Kc_1_sTi_p_theta_p - sym.Const(1e-06)))) + (sym.Const(1e-06) * (sym.Const(1) - sym.heaviside((Kc_1_sTi_p_theta_p - sym.Const(1e-06)))))) / Kc_1_sTi_p_T_p))))) + ((sym.Const(1.0) - Kc_1_sTi_p_proc_selfix_7) * ((Kc_1_sTi_p_T_p / sym.Const(0.674)) * ((((Kc_1_sTi_p_theta_p * sym.heaviside((Kc_1_sTi_p_theta_p - sym.Const(1e-06)))) + (sym.Const(1e-06) * (sym.Const(1) - sym.heaviside((Kc_1_sTi_p_theta_p - sym.Const(1e-06)))))) / Kc_1_sTi_p_T_p) ** sym.Const(0.68)))))))))))
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=3.0), output=Kc_1_sTi_p_proc_selfix_0))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=2.0), output=Kc_1_sTi_p_proc_selfix_1))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=1.0), output=Kc_1_sTi_p_proc_selfix_2))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=4.0), output=Kc_1_sTi_p_proc_selfix_3))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=3.0), output=Kc_1_sTi_p_proc_selfix_4))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=2.0), output=Kc_1_sTi_p_proc_selfix_5))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=1.0), output=Kc_1_sTi_p_proc_selfix_6))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=4.0), output=Kc_1_sTi_p_proc_selfix_7))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=3.0), output=Kc_1_sTi_p_proc_selfix_8))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=2.0), output=Kc_1_sTi_p_proc_selfix_9))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Kc_1_sTi_p_ControlTuning, op=sym.CmpOp.EQ, rhs=1.0), output=Kc_1_sTi_p_proc_selfix_10))
    procedural_logic_entries.append(sampled_value(output=Kc_1_sTi_p_proc_select_11, source=hold))
    procedural_logic_entries.append(lastvalue(yo, output=Kc_1_sTi_p_proc_lastvalue_12))
    procedural_logic_entries.append(sampled_value(output=Kc_1_sTi_p_proc_select_13, source=hold))
    procedural_logic_entries.append(reset(Kc_1_sTi_p_x, rst, x_rst))

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

