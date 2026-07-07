# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Kp+Ki/s+sKd/(1+sTd) [(p'.

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
from VeraGridEngine.Utils.procedural_logic import lastvalue, reset, sampled_value
from VeraGridEngine.enumerations import DeviceType

def build_typ_474__kp_ki_s_skd_1_std_p_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Kp+Ki/s+sKd/(1+sTd) [(p__474'

def build_typ_474__kp_ki_s_skd_1_std_p_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_474__kp_ki_s_skd_1_std_p_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Kp_Ki_s_sKd_1_sTd_p_Kd: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__Kd_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_Ki: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__Ki_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_Kp: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__Kp_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_Td: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__Td_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_y_max: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__y_max_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_y_min: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__y_min_' + template_name)
    # Declare the state variables used by the template.
    Kp_Ki_s_sKd_1_sTd_p_x1: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__x1_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_x2: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__x2_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    Kp_Ki_s_sKd_1_sTd_p_proc_lastvalue_2: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__proc_lastvalue_2_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_proc_select_0: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__proc_select_0_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_proc_select_1: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__proc_select_1_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_proc_select_3: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p__proc_select_3_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_dx2: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p_dx2_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_yd: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p_yd_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_yis: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p_yis_' + template_name)
    Kp_Ki_s_sKd_1_sTd_p_yk: Var = vf.add_var('Kp+Ki/s+sKd/(1+sTd) [(p_yk_' + template_name)
    hold: Var = vf.add_var('hold_' + template_name)
    rst: Var = vf.add_var('rst_' + template_name)
    x1_rst: Var = vf.add_var('x1_rst_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_Kp_Ki_s_sKd_1_sTd_p_x1: Var = vf.add_diff_var('d_Kp+Ki/s+sKd/(1+sTd) [(p__x1_' + template_name, base_var=Kp_Ki_s_sKd_1_sTd_p_x1)
    d_Kp_Ki_s_sKd_1_sTd_p_x2: Var = vf.add_diff_var('d_Kp+Ki/s+sKd/(1+sTd) [(p__x2_' + template_name, base_var=Kp_Ki_s_sKd_1_sTd_p_x2)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((Kp_Ki_s_sKd_1_sTd_p_proc_select_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Kp_Ki_s_sKd_1_sTd_p_proc_select_1) * (yi * Kp_Ki_s_sKd_1_sTd_p_Ki))))
    state_equations.append(((Kp_Ki_s_sKd_1_sTd_p_proc_select_0 * sym.Const(0.0)) + ((sym.Const(1.0) - Kp_Ki_s_sKd_1_sTd_p_proc_select_0) * Kp_Ki_s_sKd_1_sTd_p_dx2)))
    state_variables: list[Var] = list()
    state_variables.append(Kp_Ki_s_sKd_1_sTd_p_x1)
    state_variables.append(Kp_Ki_s_sKd_1_sTd_p_x2)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Kp_Ki_s_sKd_1_sTd_p_yk - (Kp_Ki_s_sKd_1_sTd_p_Kp * yi)))
    algebraic_equations.append((Kp_Ki_s_sKd_1_sTd_p_dx2 - ((yi - Kp_Ki_s_sKd_1_sTd_p_x2) / Kp_Ki_s_sKd_1_sTd_p_Td)))
    algebraic_equations.append((Kp_Ki_s_sKd_1_sTd_p_yd - (Kp_Ki_s_sKd_1_sTd_p_dx2 * Kp_Ki_s_sKd_1_sTd_p_Kd)))
    algebraic_equations.append((Kp_Ki_s_sKd_1_sTd_p_yis - ((Kp_Ki_s_sKd_1_sTd_p_y_min + ((Kp_Ki_s_sKd_1_sTd_p_x1 - Kp_Ki_s_sKd_1_sTd_p_y_min) * sym.heaviside((Kp_Ki_s_sKd_1_sTd_p_x1 - Kp_Ki_s_sKd_1_sTd_p_y_min)))) - ((Kp_Ki_s_sKd_1_sTd_p_x1 - Kp_Ki_s_sKd_1_sTd_p_y_max) * sym.heaviside((Kp_Ki_s_sKd_1_sTd_p_x1 - Kp_Ki_s_sKd_1_sTd_p_y_max))))))
    algebraic_equations.append((yo - ((Kp_Ki_s_sKd_1_sTd_p_proc_select_3 * Kp_Ki_s_sKd_1_sTd_p_proc_lastvalue_2) + ((sym.Const(1.0) - Kp_Ki_s_sKd_1_sTd_p_proc_select_3) * ((Kp_Ki_s_sKd_1_sTd_p_y_min + ((((Kp_Ki_s_sKd_1_sTd_p_yk + Kp_Ki_s_sKd_1_sTd_p_yis) + Kp_Ki_s_sKd_1_sTd_p_yd) - Kp_Ki_s_sKd_1_sTd_p_y_min) * sym.heaviside((((Kp_Ki_s_sKd_1_sTd_p_yk + Kp_Ki_s_sKd_1_sTd_p_yis) + Kp_Ki_s_sKd_1_sTd_p_yd) - Kp_Ki_s_sKd_1_sTd_p_y_min)))) - ((((Kp_Ki_s_sKd_1_sTd_p_yk + Kp_Ki_s_sKd_1_sTd_p_yis) + Kp_Ki_s_sKd_1_sTd_p_yd) - Kp_Ki_s_sKd_1_sTd_p_y_max) * sym.heaviside((((Kp_Ki_s_sKd_1_sTd_p_yk + Kp_Ki_s_sKd_1_sTd_p_yis) + Kp_Ki_s_sKd_1_sTd_p_yd) - Kp_Ki_s_sKd_1_sTd_p_y_max))))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Kp_Ki_s_sKd_1_sTd_p_yk)
    algebraic_variables.append(Kp_Ki_s_sKd_1_sTd_p_dx2)
    algebraic_variables.append(Kp_Ki_s_sKd_1_sTd_p_yd)
    algebraic_variables.append(Kp_Ki_s_sKd_1_sTd_p_yis)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Kp_Ki_s_sKd_1_sTd_p_x1)
    differential_variables.append(d_Kp_Ki_s_sKd_1_sTd_p_x2)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    input_variables.append(hold)
    input_variables.append(x1_rst)
    input_variables.append(rst)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Kp_Ki_s_sKd_1_sTd_p_Kp] = vf.add_const(None, name='Kp')
    event_parameters[Kp_Ki_s_sKd_1_sTd_p_Ki] = vf.add_const(None, name='Ki')
    event_parameters[Kp_Ki_s_sKd_1_sTd_p_Kd] = vf.add_const(None, name='Kd')
    event_parameters[Kp_Ki_s_sKd_1_sTd_p_Td] = vf.add_const(None, name='Td')
    event_parameters[Kp_Ki_s_sKd_1_sTd_p_y_max] = vf.add_const(None, name='y_max')
    event_parameters[Kp_Ki_s_sKd_1_sTd_p_y_min] = vf.add_const(None, name='y_min')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Kp_Ki_s_sKd_1_sTd_p_proc_select_0] = vf.add_const(0.0, name='')
    mode_parameters[Kp_Ki_s_sKd_1_sTd_p_proc_select_1] = vf.add_const(0.0, name='')
    mode_parameters[Kp_Ki_s_sKd_1_sTd_p_proc_lastvalue_2] = vf.add_const(0.0, name='')
    mode_parameters[Kp_Ki_s_sKd_1_sTd_p_proc_select_3] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=Kp_Ki_s_sKd_1_sTd_p_proc_select_0, source=hold))
    procedural_logic_entries.append(sampled_value(output=Kp_Ki_s_sKd_1_sTd_p_proc_select_1, source=hold))
    procedural_logic_entries.append(lastvalue(yo, output=Kp_Ki_s_sKd_1_sTd_p_proc_lastvalue_2))
    procedural_logic_entries.append(sampled_value(output=Kp_Ki_s_sKd_1_sTd_p_proc_select_3, source=hold))
    procedural_logic_entries.append(reset(Kp_Ki_s_sKd_1_sTd_p_x1, rst, x1_rst))
    procedural_logic_entries.append(reset(Kp_Ki_s_sKd_1_sTd_p_x2, rst, 0.0))

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

