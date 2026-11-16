# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'SEXS'.

This is the runtime implementation shipped by VeraGrid.
It exposes the imported public interface, explicit symbolic equations, and
"""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp

def build_sexs_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'SEXS'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    EMax: Var = vf.add_var('EMax_' + template_name)
    EMin: Var = vf.add_var('EMin_' + template_name)
    Efd0Pu: Var = vf.add_var('Efd0Pu_' + template_name)
    K: Var = vf.add_var('K_' + template_name)
    Ta: Var = vf.add_var('Ta_' + template_name)
    Tb: Var = vf.add_var('Tb_' + template_name)
    Te: Var = vf.add_var('Te_' + template_name)
    Us0Pu: Var = vf.add_var('Us0Pu_' + template_name)
    UsRef0Pu: Var = vf.add_var('UsRef0Pu_' + template_name)
    add3_k1: Var = vf.add_var('add3.k1_' + template_name)
    add3_k2: Var = vf.add_var('add3.k2_' + template_name)
    add3_k3: Var = vf.add_var('add3.k3_' + template_name)
    leadLag_a_1: Var = vf.add_var('leadLag.a[1]_' + template_name)
    leadLag_a_2: Var = vf.add_var('leadLag.a[2]_' + template_name)
    leadLag_a_end: Var = vf.add_var('leadLag.a_end_' + template_name)
    leadLag_b_1: Var = vf.add_var('leadLag.b[1]_' + template_name)
    leadLag_b_2: Var = vf.add_var('leadLag.b[2]_' + template_name)
    leadLag_bb_1: Var = vf.add_var('leadLag.bb[1]_' + template_name)
    leadLag_bb_2: Var = vf.add_var('leadLag.bb[2]_' + template_name)
    leadLag_d: Var = vf.add_var('leadLag.d_' + template_name)
    leadLag_na: Var = vf.add_var('leadLag.na_' + template_name)
    leadLag_nb: Var = vf.add_var('leadLag.nb_' + template_name)
    leadLag_nx: Var = vf.add_var('leadLag.nx_' + template_name)
    leadLag_x_start_1: Var = vf.add_var('leadLag.x_start[1]_' + template_name)
    leadLag_y_start: Var = vf.add_var('leadLag.y_start_' + template_name)
    limitedFirstOrder_G_k: Var = vf.add_var('limitedFirstOrder.G.k_' + template_name)
    limitedFirstOrder_Gk_k: Var = vf.add_var('limitedFirstOrder.Gk.k_' + template_name)
    limitedFirstOrder_I_initType: Var = vf.add_var('limitedFirstOrder.I.initType_' + template_name)
    limitedFirstOrder_I_k: Var = vf.add_var('limitedFirstOrder.I.k_' + template_name)
    limitedFirstOrder_I_use_reset: Var = vf.add_var('limitedFirstOrder.I.use_reset_' + template_name)
    limitedFirstOrder_I_use_set: Var = vf.add_var('limitedFirstOrder.I.use_set_' + template_name)
    limitedFirstOrder_I_y_start: Var = vf.add_var('limitedFirstOrder.I.y_start_' + template_name)
    limitedFirstOrder_K: Var = vf.add_var('limitedFirstOrder.K_' + template_name)
    limitedFirstOrder_Y0: Var = vf.add_var('limitedFirstOrder.Y0_' + template_name)
    limitedFirstOrder_YMax: Var = vf.add_var('limitedFirstOrder.YMax_' + template_name)
    limitedFirstOrder_YMin: Var = vf.add_var('limitedFirstOrder.YMin_' + template_name)
    limitedFirstOrder_lim_homotopyType: Var = vf.add_var('limitedFirstOrder.lim.homotopyType_' + template_name)
    limitedFirstOrder_lim_limitsAtInit: Var = vf.add_var('limitedFirstOrder.lim.limitsAtInit_' + template_name)
    limitedFirstOrder_lim_strict: Var = vf.add_var('limitedFirstOrder.lim.strict_' + template_name)
    limitedFirstOrder_lim_uMax: Var = vf.add_var('limitedFirstOrder.lim.uMax_' + template_name)
    limitedFirstOrder_lim_uMin: Var = vf.add_var('limitedFirstOrder.lim.uMin_' + template_name)
    limitedFirstOrder_tFilter: Var = vf.add_var('limitedFirstOrder.tFilter_' + template_name)
    # Declare the state variables used by the template.
    leadLag_x_scaled_1: Var = vf.add_var('leadLag.x_scaled[1]_' + template_name)
    limitedFirstOrder_I_y: Var = vf.add_var('limitedFirstOrder.I.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_leadLag_x_scaled_1: Var = vf.add_var('$START.leadLag.x_scaled[1]_' + template_name)
    EfdPu: Var = vf.add_var('EfdPu_' + template_name)
    UpssPu: Var = vf.add_var('UpssPu_' + template_name)
    UsPu: Var = vf.add_var('UsPu_' + template_name)
    UsRefPu: Var = vf.add_var('UsRefPu_' + template_name)
    add3_y: Var = vf.add_var('add3.y_' + template_name)
    leadLag_x_1: Var = vf.add_var('leadLag.x[1]_' + template_name)
    leadLag_y: Var = vf.add_var('leadLag.y_' + template_name)
    limitedFirstOrder_G_y: Var = vf.add_var('limitedFirstOrder.G.y_' + template_name)
    limitedFirstOrder_Gk_y: Var = vf.add_var('limitedFirstOrder.Gk.y_' + template_name)
    limitedFirstOrder_I_local_reset: Var = vf.add_var('limitedFirstOrder.I.local_reset_' + template_name)
    limitedFirstOrder_I_local_set: Var = vf.add_var('limitedFirstOrder.I.local_set_' + template_name)
    limitedFirstOrder_I_u: Var = vf.add_var('limitedFirstOrder.I.u_' + template_name)
    limitedFirstOrder_feedback_y: Var = vf.add_var('limitedFirstOrder.feedback.y_' + template_name)
    limitedFirstOrder_lim_simplifiedExpr: Var = vf.add_var('limitedFirstOrder.lim.simplifiedExpr_' + template_name)
    # Declare the differential variables used by the template.
    d_leadLag_x_scaled_1: Var = vf.add_diff_var('d_leadLag.x_scaled[1]_' + template_name, base_var=leadLag_x_scaled_1)
    d_limitedFirstOrder_I_y: Var = vf.add_diff_var('d_limitedFirstOrder.I.y_' + template_name, base_var=limitedFirstOrder_I_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((limitedFirstOrder_I_k * limitedFirstOrder_I_u))
    state_equations.append((((leadLag_a_end * add3_y) - (leadLag_a_2 * leadLag_x_scaled_1)) / leadLag_a_1))
    state_variables: list[Var] = list()
    state_variables.append(limitedFirstOrder_I_y)
    state_variables.append(leadLag_x_scaled_1)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((EfdPu - ((sym.heaviside(((limitedFirstOrder_I_y - limitedFirstOrder_lim_uMax) - sym.Const(1e-06))) * limitedFirstOrder_lim_uMax) + ((sym.Const(1.0) - sym.heaviside(((limitedFirstOrder_I_y - limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((limitedFirstOrder_lim_uMin - limitedFirstOrder_I_y) - sym.Const(1e-06))) * limitedFirstOrder_lim_uMin) + ((sym.Const(1.0) - sym.heaviside(((limitedFirstOrder_lim_uMin - limitedFirstOrder_I_y) - sym.Const(1e-06)))) * limitedFirstOrder_I_y))))))
    algebraic_equations.append((leadLag_x_1 - (leadLag_x_scaled_1 / leadLag_a_end)))
    algebraic_equations.append((add3_y - ((add3_k1 * UsRefPu) + ((add3_k2 * UsPu) + (add3_k3 * UpssPu)))))
    algebraic_equations.append((leadLag_y - (((leadLag_bb_2 - (leadLag_d * leadLag_a_2)) * leadLag_x_1) + (leadLag_d * add3_y))))
    algebraic_equations.append((limitedFirstOrder_Gk_y - (limitedFirstOrder_Gk_k * leadLag_y)))
    algebraic_equations.append((limitedFirstOrder_feedback_y - (limitedFirstOrder_Gk_y - EfdPu)))
    algebraic_equations.append((limitedFirstOrder_G_y - (limitedFirstOrder_G_k * limitedFirstOrder_feedback_y)))
    algebraic_equations.append((limitedFirstOrder_I_u - (((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((limitedFirstOrder_I_y - limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((limitedFirstOrder_I_y - limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((limitedFirstOrder_I_y - limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((limitedFirstOrder_lim_uMin - limitedFirstOrder_I_y) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((limitedFirstOrder_I_y - limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((limitedFirstOrder_I_y - limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((limitedFirstOrder_I_y - limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((limitedFirstOrder_lim_uMin - limitedFirstOrder_I_y) - sym.Const(1e-06)))))))) * limitedFirstOrder_G_y))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(EfdPu)
    algebraic_variables.append(leadLag_x_1)
    algebraic_variables.append(add3_y)
    algebraic_variables.append(leadLag_y)
    algebraic_variables.append(limitedFirstOrder_Gk_y)
    algebraic_variables.append(limitedFirstOrder_feedback_y)
    algebraic_variables.append(limitedFirstOrder_G_y)
    algebraic_variables.append(limitedFirstOrder_I_u)
    algebraic_variables.append(UsRefPu)
    algebraic_variables.append(UsPu)
    algebraic_variables.append(UpssPu)
    algebraic_variables.append(limitedFirstOrder_lim_simplifiedExpr)
    algebraic_variables.append(limitedFirstOrder_I_local_reset)
    algebraic_variables.append(limitedFirstOrder_I_local_set)
    algebraic_variables.append(START_leadLag_x_scaled_1)
    differential_variables: list[Var] = list()
    differential_variables.append(d_limitedFirstOrder_I_y)
    differential_variables.append(d_leadLag_x_scaled_1)
    input_variables: list[Var] = list()
    input_variables.append(UpssPu)
    input_variables.append(UsPu)
    input_variables.append(UsRefPu)
    output_variables: list[Var] = list()
    output_variables.append(EfdPu)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[EMax] = vf.add_const(5.0, name='')
    event_parameters[EMin] = vf.add_const(0.0, name='')
    event_parameters[Efd0Pu] = vf.add_const(1.0, name='')
    event_parameters[K] = vf.add_const(100.0, name='')
    event_parameters[Ta] = vf.add_const(0.01, name='')
    event_parameters[Tb] = vf.add_const(0.1, name='')
    event_parameters[Te] = vf.add_const(0.5, name='')
    event_parameters[Us0Pu] = vf.add_const(1.0, name='')
    event_parameters[UsRef0Pu] = (Us0Pu + (Efd0Pu / K))
    event_parameters[add3_k1] = vf.add_const(1.0, name='')
    event_parameters[add3_k2] = vf.add_const(-1.0, name='')
    event_parameters[add3_k3] = vf.add_const(1.0, name='')
    event_parameters[leadLag_a_1] = Tb
    event_parameters[leadLag_a_2] = vf.add_const(1.0, name='')
    event_parameters[leadLag_a_end] = ((sym.heaviside(((leadLag_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((leadLag_a_1 ** sym.Const(2.0)) + (leadLag_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06))) * leadLag_a_2) + ((sym.Const(1.0) - sym.heaviside(((leadLag_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((leadLag_a_1 ** sym.Const(2.0)) + (leadLag_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06)))) * sym.Const(1.0)))
    event_parameters[leadLag_b_1] = Ta
    event_parameters[leadLag_b_2] = vf.add_const(1.0, name='')
    event_parameters[leadLag_bb_1] = leadLag_b_1
    event_parameters[leadLag_bb_2] = leadLag_b_2
    event_parameters[leadLag_d] = (leadLag_bb_1 / leadLag_a_1)
    event_parameters[leadLag_x_start_1] = (Efd0Pu / K)
    event_parameters[leadLag_y_start] = (Efd0Pu / K)
    event_parameters[limitedFirstOrder_G_k] = (sym.Const(1.0) / limitedFirstOrder_tFilter)
    event_parameters[limitedFirstOrder_Gk_k] = limitedFirstOrder_K
    event_parameters[limitedFirstOrder_I_k] = vf.add_const(1.0, name='')
    event_parameters[limitedFirstOrder_I_y_start] = limitedFirstOrder_Y0
    event_parameters[limitedFirstOrder_K] = K
    event_parameters[limitedFirstOrder_Y0] = Efd0Pu
    event_parameters[limitedFirstOrder_YMax] = EMax
    event_parameters[limitedFirstOrder_YMin] = EMin
    event_parameters[limitedFirstOrder_lim_uMax] = limitedFirstOrder_YMax
    event_parameters[limitedFirstOrder_lim_uMin] = limitedFirstOrder_YMin
    event_parameters[limitedFirstOrder_tFilter] = Te
    event_parameters[leadLag_na] = vf.add_const(2.0, name='')
    event_parameters[leadLag_nb] = vf.add_const(2.0, name='')
    event_parameters[leadLag_nx] = vf.add_const(1.0, name='')
    event_parameters[limitedFirstOrder_I_initType] = vf.add_const(3.0, name='')
    event_parameters[limitedFirstOrder_lim_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[limitedFirstOrder_I_use_reset] = vf.add_const(0.0, name='')
    event_parameters[limitedFirstOrder_I_use_set] = vf.add_const(0.0, name='')
    event_parameters[limitedFirstOrder_lim_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[limitedFirstOrder_lim_strict] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[leadLag_x_scaled_1] = (leadLag_a_end * leadLag_x_start_1)
    initial_equations[limitedFirstOrder_I_y] = limitedFirstOrder_I_y_start
    initial_equations[EfdPu] = limitedFirstOrder_Y0
    initial_equations[UpssPu] = vf.add_const(0.0, name='')
    initial_equations[UsPu] = vf.add_const(1.0, name='')
    initial_equations[UsRefPu] = (Us0Pu + (Efd0Pu / K))
    initial_equations[leadLag_x_1] = leadLag_x_start_1
    initial_equations[leadLag_y] = leadLag_y_start
    initial_equations[limitedFirstOrder_lim_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[limitedFirstOrder_I_local_reset] = vf.add_const(0.0, name='')
    initial_equations[limitedFirstOrder_I_local_set] = vf.add_const(0.0, name='')
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()

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

    template.comment = 'Generator AVR/exciter SEXS'
    return template
