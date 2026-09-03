# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'St7b'.

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

def build_st7b_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'St7b'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    avr_Efd0Pu: Var = vf.add_var('avr.Efd0Pu_' + template_name)
    avr_Kh: Var = vf.add_var('avr.Kh_' + template_name)
    avr_Kia: Var = vf.add_var('avr.Kia_' + template_name)
    avr_Kl: Var = vf.add_var('avr.Kl_' + template_name)
    avr_Kpa: Var = vf.add_var('avr.Kpa_' + template_name)
    avr_PositionOel: Var = vf.add_var('avr.PositionOel_' + template_name)
    avr_PositionScl: Var = vf.add_var('avr.PositionScl_' + template_name)
    avr_PositionUel: Var = vf.add_var('avr.PositionUel_' + template_name)
    avr_UOel0Pu: Var = vf.add_var('avr.UOel0Pu_' + template_name)
    avr_USclOel0Pu: Var = vf.add_var('avr.USclOel0Pu_' + template_name)
    avr_USclUel0Pu: Var = vf.add_var('avr.USclUel0Pu_' + template_name)
    avr_UUel0Pu: Var = vf.add_var('avr.UUel0Pu_' + template_name)
    avr_Us0Pu: Var = vf.add_var('avr.Us0Pu_' + template_name)
    avr_UsRef0Pu: Var = vf.add_var('avr.UsRef0Pu_' + template_name)
    avr_VMaxPu: Var = vf.add_var('avr.VMaxPu_' + template_name)
    avr_VMinPu: Var = vf.add_var('avr.VMinPu_' + template_name)
    avr_VrMaxPu: Var = vf.add_var('avr.VrMaxPu_' + template_name)
    avr_VrMinPu: Var = vf.add_var('avr.VrMinPu_' + template_name)
    avr_add3_k1: Var = vf.add_var('avr.add3.k1_' + template_name)
    avr_add3_k2: Var = vf.add_var('avr.add3.k2_' + template_name)
    avr_add3_k3: Var = vf.add_var('avr.add3.k3_' + template_name)
    avr_firstOrder_T: Var = vf.add_var('avr.firstOrder.T_' + template_name)
    avr_firstOrder_initType: Var = vf.add_var('avr.firstOrder.initType_' + template_name)
    avr_firstOrder_k: Var = vf.add_var('avr.firstOrder.k_' + template_name)
    avr_firstOrder_y_start: Var = vf.add_var('avr.firstOrder.y_start_' + template_name)
    avr_firstOrder2_T: Var = vf.add_var('avr.firstOrder2.T_' + template_name)
    avr_firstOrder2_initType: Var = vf.add_var('avr.firstOrder2.initType_' + template_name)
    avr_firstOrder2_k: Var = vf.add_var('avr.firstOrder2.k_' + template_name)
    avr_firstOrder2_y_start: Var = vf.add_var('avr.firstOrder2.y_start_' + template_name)
    avr_gain_k: Var = vf.add_var('avr.gain.k_' + template_name)
    avr_gain1_k: Var = vf.add_var('avr.gain1.k_' + template_name)
    avr_gain2_k: Var = vf.add_var('avr.gain2.k_' + template_name)
    avr_gain3_k: Var = vf.add_var('avr.gain3.k_' + template_name)
    avr_gain4_k: Var = vf.add_var('avr.gain4.k_' + template_name)
    avr_limiter_homotopyType: Var = vf.add_var('avr.limiter.homotopyType_' + template_name)
    avr_limiter_limitsAtInit: Var = vf.add_var('avr.limiter.limitsAtInit_' + template_name)
    avr_limiter_strict: Var = vf.add_var('avr.limiter.strict_' + template_name)
    avr_limiter_uMax: Var = vf.add_var('avr.limiter.uMax_' + template_name)
    avr_limiter_uMin: Var = vf.add_var('avr.limiter.uMin_' + template_name)
    avr_max1_nu: Var = vf.add_var('avr.max1.nu_' + template_name)
    avr_max2_nu: Var = vf.add_var('avr.max2.nu_' + template_name)
    avr_min1_nu: Var = vf.add_var('avr.min1.nu_' + template_name)
    avr_min2_nu: Var = vf.add_var('avr.min2.nu_' + template_name)
    avr_sum1_k_1: Var = vf.add_var('avr.sum1.k[1]_' + template_name)
    avr_sum1_k_2: Var = vf.add_var('avr.sum1.k[2]_' + template_name)
    avr_sum1_k_3: Var = vf.add_var('avr.sum1.k[3]_' + template_name)
    avr_sum1_k_4: Var = vf.add_var('avr.sum1.k[4]_' + template_name)
    avr_sum1_nin: Var = vf.add_var('avr.sum1.nin_' + template_name)
    avr_tB: Var = vf.add_var('avr.tB_' + template_name)
    avr_tC: Var = vf.add_var('avr.tC_' + template_name)
    avr_tF: Var = vf.add_var('avr.tF_' + template_name)
    avr_tG: Var = vf.add_var('avr.tG_' + template_name)
    avr_tIa: Var = vf.add_var('avr.tIa_' + template_name)
    avr_tR: Var = vf.add_var('avr.tR_' + template_name)
    avr_transferFunction_a_1: Var = vf.add_var('avr.transferFunction.a[1]_' + template_name)
    avr_transferFunction_a_2: Var = vf.add_var('avr.transferFunction.a[2]_' + template_name)
    avr_transferFunction_a_end: Var = vf.add_var('avr.transferFunction.a_end_' + template_name)
    avr_transferFunction_b_1: Var = vf.add_var('avr.transferFunction.b[1]_' + template_name)
    avr_transferFunction_b_2: Var = vf.add_var('avr.transferFunction.b[2]_' + template_name)
    avr_transferFunction_bb_1: Var = vf.add_var('avr.transferFunction.bb[1]_' + template_name)
    avr_transferFunction_bb_2: Var = vf.add_var('avr.transferFunction.bb[2]_' + template_name)
    avr_transferFunction_d: Var = vf.add_var('avr.transferFunction.d_' + template_name)
    avr_transferFunction_na: Var = vf.add_var('avr.transferFunction.na_' + template_name)
    avr_transferFunction_nb: Var = vf.add_var('avr.transferFunction.nb_' + template_name)
    avr_transferFunction_nx: Var = vf.add_var('avr.transferFunction.nx_' + template_name)
    avr_transferFunction_x_start_1: Var = vf.add_var('avr.transferFunction.x_start[1]_' + template_name)
    avr_transferFunction_y_start: Var = vf.add_var('avr.transferFunction.y_start_' + template_name)
    avr_transferFunction1_a_1: Var = vf.add_var('avr.transferFunction1.a[1]_' + template_name)
    avr_transferFunction1_a_2: Var = vf.add_var('avr.transferFunction1.a[2]_' + template_name)
    avr_transferFunction1_a_end: Var = vf.add_var('avr.transferFunction1.a_end_' + template_name)
    avr_transferFunction1_b_1: Var = vf.add_var('avr.transferFunction1.b[1]_' + template_name)
    avr_transferFunction1_b_2: Var = vf.add_var('avr.transferFunction1.b[2]_' + template_name)
    avr_transferFunction1_bb_1: Var = vf.add_var('avr.transferFunction1.bb[1]_' + template_name)
    avr_transferFunction1_bb_2: Var = vf.add_var('avr.transferFunction1.bb[2]_' + template_name)
    avr_transferFunction1_d: Var = vf.add_var('avr.transferFunction1.d_' + template_name)
    avr_transferFunction1_na: Var = vf.add_var('avr.transferFunction1.na_' + template_name)
    avr_transferFunction1_nb: Var = vf.add_var('avr.transferFunction1.nb_' + template_name)
    avr_transferFunction1_nx: Var = vf.add_var('avr.transferFunction1.nx_' + template_name)
    avr_transferFunction1_x_start_1: Var = vf.add_var('avr.transferFunction1.x_start[1]_' + template_name)
    avr_transferFunction1_y_start: Var = vf.add_var('avr.transferFunction1.y_start_' + template_name)
    avr_variableLimiter_homotopyType: Var = vf.add_var('avr.variableLimiter.homotopyType_' + template_name)
    avr_variableLimiter_limitsAtInit: Var = vf.add_var('avr.variableLimiter.limitsAtInit_' + template_name)
    avr_variableLimiter_strict: Var = vf.add_var('avr.variableLimiter.strict_' + template_name)
    avr_variableLimiter_ySimplified: Var = vf.add_var('avr.variableLimiter.ySimplified_' + template_name)
    # Declare the state variables used by the template.
    avr_firstOrder_y: Var = vf.add_var('avr.firstOrder.y_' + template_name)
    avr_firstOrder2_y: Var = vf.add_var('avr.firstOrder2.y_' + template_name)
    avr_transferFunction_x_scaled_1: Var = vf.add_var('avr.transferFunction.x_scaled[1]_' + template_name)
    avr_transferFunction1_x_scaled_1: Var = vf.add_var('avr.transferFunction1.x_scaled[1]_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_avr_firstOrder_y: Var = vf.add_var('$START.avr.firstOrder.y_' + template_name)
    START_avr_firstOrder2_y: Var = vf.add_var('$START.avr.firstOrder2.y_' + template_name)
    START_avr_transferFunction_x_scaled_1: Var = vf.add_var('$START.avr.transferFunction.x_scaled[1]_' + template_name)
    START_avr_transferFunction1_x_scaled_1: Var = vf.add_var('$START.avr.transferFunction1.x_scaled[1]_' + template_name)
    avr_EfdPu: Var = vf.add_var('avr.EfdPu_' + template_name)
    avr_UOelPu: Var = vf.add_var('avr.UOelPu_' + template_name)
    avr_UPssPu: Var = vf.add_var('avr.UPssPu_' + template_name)
    avr_USclOelPu: Var = vf.add_var('avr.USclOelPu_' + template_name)
    avr_USclUelPu: Var = vf.add_var('avr.USclUelPu_' + template_name)
    avr_UUelPu: Var = vf.add_var('avr.UUelPu_' + template_name)
    avr_UsPu: Var = vf.add_var('avr.UsPu_' + template_name)
    avr_UsRefPu: Var = vf.add_var('avr.UsRefPu_' + template_name)
    avr_VFbPu: Var = vf.add_var('avr.VFbPu_' + template_name)
    avr_add3_y: Var = vf.add_var('avr.add3.y_' + template_name)
    avr_feedback_y: Var = vf.add_var('avr.feedback.y_' + template_name)
    avr_feedback1_y: Var = vf.add_var('avr.feedback1.y_' + template_name)
    avr_gain_y: Var = vf.add_var('avr.gain.y_' + template_name)
    avr_gain3_y: Var = vf.add_var('avr.gain3.y_' + template_name)
    avr_gain4_y: Var = vf.add_var('avr.gain4.y_' + template_name)
    avr_limiter_simplifiedExpr: Var = vf.add_var('avr.limiter.simplifiedExpr_' + template_name)
    avr_max3_y: Var = vf.add_var('avr.max3.y_' + template_name)
    avr_min2_u_3: Var = vf.add_var('avr.min2.u[3]_' + template_name)
    avr_min3_y: Var = vf.add_var('avr.min3.y_' + template_name)
    avr_sum1_u_2: Var = vf.add_var('avr.sum1.u[2]_' + template_name)
    avr_sum1_u_3: Var = vf.add_var('avr.sum1.u[3]_' + template_name)
    avr_sum1_u_4: Var = vf.add_var('avr.sum1.u[4]_' + template_name)
    avr_transferFunction_x_1: Var = vf.add_var('avr.transferFunction.x[1]_' + template_name)
    avr_transferFunction_y: Var = vf.add_var('avr.transferFunction.y_' + template_name)
    avr_transferFunction1_x_1: Var = vf.add_var('avr.transferFunction1.x[1]_' + template_name)
    avr_transferFunction1_y: Var = vf.add_var('avr.transferFunction1.y_' + template_name)
    avr_variableLimiter_simplifiedExpr: Var = vf.add_var('avr.variableLimiter.simplifiedExpr_' + template_name)
    # Declare the differential variables used by the template.
    d_avr_firstOrder_y: Var = vf.add_diff_var('d_avr.firstOrder.y_' + template_name, base_var=avr_firstOrder_y)
    d_avr_firstOrder2_y: Var = vf.add_diff_var('d_avr.firstOrder2.y_' + template_name, base_var=avr_firstOrder2_y)
    d_avr_transferFunction_x_scaled_1: Var = vf.add_diff_var('d_avr.transferFunction.x_scaled[1]_' + template_name, base_var=avr_transferFunction_x_scaled_1)
    d_avr_transferFunction1_x_scaled_1: Var = vf.add_diff_var('d_avr.transferFunction1.x_scaled[1]_' + template_name, base_var=avr_transferFunction1_x_scaled_1)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((avr_transferFunction_a_end * avr_firstOrder_y) - (avr_transferFunction_a_2 * avr_transferFunction_x_scaled_1)) / avr_transferFunction_a_1))
    state_equations.append((((avr_firstOrder2_k * avr_EfdPu) - avr_firstOrder2_y) / avr_firstOrder2_T))
    state_equations.append((((avr_transferFunction1_a_end * avr_min3_y) - (avr_transferFunction1_a_2 * avr_transferFunction1_x_scaled_1)) / avr_transferFunction1_a_1))
    state_equations.append((((avr_firstOrder_k * avr_UsPu) - avr_firstOrder_y) / avr_firstOrder_T))
    state_variables: list[Var] = list()
    state_variables.append(avr_transferFunction_x_scaled_1)
    state_variables.append(avr_firstOrder2_y)
    state_variables.append(avr_transferFunction1_x_scaled_1)
    state_variables.append(avr_firstOrder_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((avr_gain4_y - (avr_gain4_k * avr_firstOrder2_y)))
    algebraic_equations.append((avr_gain3_y - (avr_gain3_k * avr_firstOrder2_y)))
    algebraic_equations.append((avr_feedback_y - (avr_gain1_k - avr_gain3_y)))
    algebraic_equations.append((avr_transferFunction_x_1 - (avr_transferFunction_x_scaled_1 / avr_transferFunction_a_end)))
    algebraic_equations.append((avr_transferFunction_y - (((avr_transferFunction_bb_2 - (avr_transferFunction_d * avr_transferFunction_a_2)) * avr_transferFunction_x_1) + (avr_transferFunction_d * avr_firstOrder_y))))
    algebraic_equations.append((avr_add3_y - (((avr_add3_k1 * avr_UPssPu) + (avr_add3_k2 * avr_VFbPu)) + (avr_add3_k3 * avr_transferFunction_y))))
    algebraic_equations.append((avr_feedback1_y - (avr_gain2_k - avr_gain4_y)))
    algebraic_equations.append((avr_gain_y - (avr_gain_k * avr_add3_y)))
    algebraic_equations.append((avr_max3_y - ((avr_gain_y * sym.heaviside((avr_gain_y - avr_feedback1_y))) + (avr_feedback1_y * (sym.Const(1) - sym.heaviside((avr_gain_y - avr_feedback1_y)))))))
    algebraic_equations.append((avr_min3_y - ((avr_feedback_y * sym.heaviside((avr_max3_y - avr_feedback_y))) + (avr_max3_y * (sym.Const(1) - sym.heaviside((avr_max3_y - avr_feedback_y)))))))
    algebraic_equations.append((avr_transferFunction1_x_1 - (avr_transferFunction1_x_scaled_1 / avr_transferFunction1_a_end)))
    algebraic_equations.append((avr_transferFunction1_y - (((avr_transferFunction1_bb_2 - (avr_transferFunction1_d * avr_transferFunction1_a_2)) * avr_transferFunction1_x_1) + (avr_transferFunction1_d * avr_min3_y))))
    algebraic_equations.append((avr_min2_u_3 - (avr_transferFunction1_y - avr_firstOrder2_y)))
    algebraic_equations.append((avr_EfdPu - ((sym.heaviside(((avr_min2_u_3 - avr_gain1_k) - sym.Const(1e-06))) * avr_gain1_k) + ((sym.Const(1.0) - sym.heaviside(((avr_min2_u_3 - avr_gain1_k) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_gain2_k - avr_min2_u_3) - sym.Const(1e-06))) * avr_gain2_k) + ((sym.Const(1.0) - sym.heaviside(((avr_gain2_k - avr_min2_u_3) - sym.Const(1e-06)))) * avr_min2_u_3))))))
    algebraic_equations.append((avr_VFbPu - ((sym.heaviside(((avr_UsRefPu - avr_limiter_uMax) - sym.Const(1e-06))) * avr_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_UsRefPu - avr_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limiter_uMin - avr_UsRefPu) - sym.Const(1e-06))) * avr_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limiter_uMin - avr_UsRefPu) - sym.Const(1e-06)))) * avr_UsRefPu))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(avr_gain4_y)
    algebraic_variables.append(avr_gain3_y)
    algebraic_variables.append(avr_feedback_y)
    algebraic_variables.append(avr_transferFunction_x_1)
    algebraic_variables.append(avr_transferFunction_y)
    algebraic_variables.append(avr_add3_y)
    algebraic_variables.append(avr_feedback1_y)
    algebraic_variables.append(avr_gain_y)
    algebraic_variables.append(avr_max3_y)
    algebraic_variables.append(avr_min3_y)
    algebraic_variables.append(avr_transferFunction1_x_1)
    algebraic_variables.append(avr_transferFunction1_y)
    algebraic_variables.append(avr_min2_u_3)
    algebraic_variables.append(avr_EfdPu)
    algebraic_variables.append(avr_VFbPu)
    algebraic_variables.append(avr_UOelPu)
    algebraic_variables.append(avr_UPssPu)
    algebraic_variables.append(avr_USclOelPu)
    algebraic_variables.append(avr_USclUelPu)
    algebraic_variables.append(avr_UUelPu)
    algebraic_variables.append(avr_UsPu)
    algebraic_variables.append(avr_UsRefPu)
    algebraic_variables.append(avr_limiter_simplifiedExpr)
    algebraic_variables.append(avr_variableLimiter_simplifiedExpr)
    algebraic_variables.append(START_avr_firstOrder_y)
    algebraic_variables.append(START_avr_transferFunction1_x_scaled_1)
    algebraic_variables.append(START_avr_transferFunction_x_scaled_1)
    algebraic_variables.append(START_avr_firstOrder2_y)
    algebraic_variables.append(avr_sum1_u_2)
    algebraic_variables.append(avr_sum1_u_3)
    algebraic_variables.append(avr_sum1_u_4)
    differential_variables: list[Var] = list()
    differential_variables.append(d_avr_transferFunction_x_scaled_1)
    differential_variables.append(d_avr_firstOrder2_y)
    differential_variables.append(d_avr_transferFunction1_x_scaled_1)
    differential_variables.append(d_avr_firstOrder_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[avr_Efd0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Kh] = vf.add_const(1.0, name='')
    event_parameters[avr_Kia] = vf.add_const(10.0, name='')
    event_parameters[avr_Kl] = vf.add_const(1.0, name='')
    event_parameters[avr_Kpa] = vf.add_const(1.0, name='')
    event_parameters[avr_UOel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_USclOel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_USclUel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_UUel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_Us0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_UsRef0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_VMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_VrMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VrMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_add3_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_add3_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_add3_k3] = vf.add_const(-1.0, name='')
    event_parameters[avr_firstOrder_T] = avr_tR
    event_parameters[avr_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_y_start] = avr_Us0Pu
    event_parameters[avr_firstOrder2_T] = avr_tIa
    event_parameters[avr_firstOrder2_k] = avr_Kia
    event_parameters[avr_firstOrder2_y_start] = (avr_Kia * avr_Efd0Pu)
    event_parameters[avr_gain_k] = avr_Kpa
    event_parameters[avr_gain1_k] = avr_VrMaxPu
    event_parameters[avr_gain2_k] = avr_VrMinPu
    event_parameters[avr_gain3_k] = avr_Kl
    event_parameters[avr_gain4_k] = avr_Kh
    event_parameters[avr_limiter_uMax] = avr_VMaxPu
    event_parameters[avr_limiter_uMin] = avr_VMinPu
    event_parameters[avr_sum1_k_1] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_2] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_3] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_4] = vf.add_const(1.0, name='')
    event_parameters[avr_tB] = vf.add_const(1.0, name='')
    event_parameters[avr_tC] = vf.add_const(1.0, name='')
    event_parameters[avr_tF] = vf.add_const(1.0, name='')
    event_parameters[avr_tG] = vf.add_const(1.0, name='')
    event_parameters[avr_tIa] = vf.add_const(1.0, name='')
    event_parameters[avr_tR] = vf.add_const(0.02, name='')
    event_parameters[avr_transferFunction_a_1] = avr_tF
    event_parameters[avr_transferFunction_a_2] = vf.add_const(1.0, name='')
    event_parameters[avr_transferFunction_a_end] = ((sym.heaviside(((avr_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((avr_transferFunction_a_1 ** sym.Const(2.0)) + (avr_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06))) * avr_transferFunction_a_2) + ((sym.Const(1.0) - sym.heaviside(((avr_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((avr_transferFunction_a_1 ** sym.Const(2.0)) + (avr_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06)))) * sym.Const(1.0)))
    event_parameters[avr_transferFunction_b_1] = avr_tG
    event_parameters[avr_transferFunction_b_2] = vf.add_const(1.0, name='')
    event_parameters[avr_transferFunction_bb_1] = avr_transferFunction_b_1
    event_parameters[avr_transferFunction_bb_2] = avr_transferFunction_b_2
    event_parameters[avr_transferFunction_d] = (avr_transferFunction_bb_1 / avr_transferFunction_a_1)
    event_parameters[avr_transferFunction_x_start_1] = avr_Us0Pu
    event_parameters[avr_transferFunction_y_start] = avr_Us0Pu
    event_parameters[avr_transferFunction1_a_1] = avr_tB
    event_parameters[avr_transferFunction1_a_2] = vf.add_const(1.0, name='')
    event_parameters[avr_transferFunction1_a_end] = ((sym.heaviside(((avr_transferFunction1_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((avr_transferFunction1_a_1 ** sym.Const(2.0)) + (avr_transferFunction1_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06))) * avr_transferFunction1_a_2) + ((sym.Const(1.0) - sym.heaviside(((avr_transferFunction1_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((avr_transferFunction1_a_1 ** sym.Const(2.0)) + (avr_transferFunction1_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06)))) * sym.Const(1.0)))
    event_parameters[avr_transferFunction1_b_1] = avr_tC
    event_parameters[avr_transferFunction1_b_2] = vf.add_const(1.0, name='')
    event_parameters[avr_transferFunction1_bb_1] = avr_transferFunction1_b_1
    event_parameters[avr_transferFunction1_bb_2] = avr_transferFunction1_b_2
    event_parameters[avr_transferFunction1_d] = (avr_transferFunction1_bb_1 / avr_transferFunction1_a_1)
    event_parameters[avr_transferFunction1_x_start_1] = ((sym.Const(1.0) + avr_Kia) * avr_Efd0Pu)
    event_parameters[avr_transferFunction1_y_start] = ((sym.Const(1.0) + avr_Kia) * avr_Efd0Pu)
    event_parameters[avr_variableLimiter_ySimplified] = vf.add_const(0.0, name='')
    event_parameters[avr_PositionOel] = vf.add_const(0.0, name='')
    event_parameters[avr_PositionScl] = vf.add_const(0.0, name='')
    event_parameters[avr_PositionUel] = vf.add_const(0.0, name='')
    event_parameters[avr_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder2_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_max1_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_max2_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_min1_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_min2_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_sum1_nin] = vf.add_const(4.0, name='')
    event_parameters[avr_transferFunction_na] = vf.add_const(2.0, name='')
    event_parameters[avr_transferFunction_nb] = vf.add_const(2.0, name='')
    event_parameters[avr_transferFunction_nx] = vf.add_const(1.0, name='')
    event_parameters[avr_transferFunction1_na] = vf.add_const(2.0, name='')
    event_parameters[avr_transferFunction1_nb] = vf.add_const(2.0, name='')
    event_parameters[avr_transferFunction1_nx] = vf.add_const(1.0, name='')
    event_parameters[avr_variableLimiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_variableLimiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_variableLimiter_strict] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[avr_firstOrder_y] = (avr_firstOrder_k * avr_UsPu)
    initial_equations[avr_firstOrder2_y] = avr_firstOrder2_y_start
    initial_equations[avr_transferFunction_x_scaled_1] = START_avr_transferFunction_x_scaled_1
    initial_equations[avr_transferFunction1_x_scaled_1] = START_avr_transferFunction1_x_scaled_1
    initial_equations[avr_EfdPu] = vf.add_const(1.0, name='')
    initial_equations[avr_UOelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UPssPu] = vf.add_const(0.0, name='')
    initial_equations[avr_USclOelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_USclUelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UUelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UsPu] = vf.add_const(1.0, name='')
    initial_equations[avr_UsRefPu] = vf.add_const(1.0, name='')
    initial_equations[avr_VFbPu] = ((sym.heaviside(((avr_UsRefPu - avr_limiter_uMax) - sym.Const(1e-06))) * avr_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_UsRefPu - avr_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limiter_uMin - avr_UsRefPu) - sym.Const(1e-06))) * avr_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limiter_uMin - avr_UsRefPu) - sym.Const(1e-06)))) * avr_UsRefPu))))
    initial_equations[avr_transferFunction_x_1] = avr_transferFunction_x_start_1
    initial_equations[avr_transferFunction_y] = avr_transferFunction_y_start
    initial_equations[avr_transferFunction1_x_1] = avr_transferFunction1_x_start_1
    initial_equations[avr_transferFunction1_y] = avr_transferFunction1_y_start
    initial_equations[avr_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_variableLimiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_u_2] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_u_3] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_u_4] = vf.add_const(0.0, name='')
    initial_equations[avr_add3_y] = (((avr_add3_k1 * avr_UPssPu) + (avr_add3_k2 * avr_VFbPu)) + (avr_add3_k3 * avr_transferFunction_y))
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

    template.comment = 'Generator AVR/exciter IEEE ST7B'
    return template
