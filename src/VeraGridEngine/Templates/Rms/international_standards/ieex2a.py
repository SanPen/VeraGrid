# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'IEEX2A'.

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

def build_ieex2a_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'IEEX2A'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    avr_AEx: Var = vf.add_var('avr.AEx_' + template_name)
    avr_BEx: Var = vf.add_var('avr.BEx_' + template_name)
    avr_Efd0Pu: Var = vf.add_var('avr.Efd0Pu_' + template_name)
    avr_EfdMinPu: Var = vf.add_var('avr.EfdMinPu_' + template_name)
    avr_Ka: Var = vf.add_var('avr.Ka_' + template_name)
    avr_Ke: Var = vf.add_var('avr.Ke_' + template_name)
    avr_Kf: Var = vf.add_var('avr.Kf_' + template_name)
    avr_Us0Pu: Var = vf.add_var('avr.Us0Pu_' + template_name)
    avr_UsRef0Pu: Var = vf.add_var('avr.UsRef0Pu_' + template_name)
    avr_Va0Pu: Var = vf.add_var('avr.Va0Pu_' + template_name)
    avr_VrMaxPu: Var = vf.add_var('avr.VrMaxPu_' + template_name)
    avr_VrMinPu: Var = vf.add_var('avr.VrMinPu_' + template_name)
    avr_abs1_generateEvent: Var = vf.add_var('avr.abs1.generateEvent_' + template_name)
    avr_add_k1: Var = vf.add_var('avr.add.k1_' + template_name)
    avr_add_k2: Var = vf.add_var('avr.add.k2_' + template_name)
    avr_const_k: Var = vf.add_var('avr.const.k_' + template_name)
    avr_derivative_T: Var = vf.add_var('avr.derivative.T_' + template_name)
    avr_derivative_initType: Var = vf.add_var('avr.derivative.initType_' + template_name)
    avr_derivative_k: Var = vf.add_var('avr.derivative.k_' + template_name)
    avr_derivative_x_start: Var = vf.add_var('avr.derivative.x_start_' + template_name)
    avr_derivative_y_start: Var = vf.add_var('avr.derivative.y_start_' + template_name)
    avr_derivative_zeroGain: Var = vf.add_var('avr.derivative.zeroGain_' + template_name)
    avr_firstOrder_T: Var = vf.add_var('avr.firstOrder.T_' + template_name)
    avr_firstOrder_initType: Var = vf.add_var('avr.firstOrder.initType_' + template_name)
    avr_firstOrder_k: Var = vf.add_var('avr.firstOrder.k_' + template_name)
    avr_firstOrder_y_start: Var = vf.add_var('avr.firstOrder.y_start_' + template_name)
    avr_limIntegrator_initType: Var = vf.add_var('avr.limIntegrator.initType_' + template_name)
    avr_limIntegrator_k: Var = vf.add_var('avr.limIntegrator.k_' + template_name)
    avr_limIntegrator_limitsAtInit: Var = vf.add_var('avr.limIntegrator.limitsAtInit_' + template_name)
    avr_limIntegrator_outMax: Var = vf.add_var('avr.limIntegrator.outMax_' + template_name)
    avr_limIntegrator_outMin: Var = vf.add_var('avr.limIntegrator.outMin_' + template_name)
    avr_limIntegrator_strict: Var = vf.add_var('avr.limIntegrator.strict_' + template_name)
    avr_limIntegrator_use_reset: Var = vf.add_var('avr.limIntegrator.use_reset_' + template_name)
    avr_limIntegrator_use_set: Var = vf.add_var('avr.limIntegrator.use_set_' + template_name)
    avr_limIntegrator_y_start: Var = vf.add_var('avr.limIntegrator.y_start_' + template_name)
    avr_limitedFirstOrder_G_k: Var = vf.add_var('avr.limitedFirstOrder.G.k_' + template_name)
    avr_limitedFirstOrder_Gk_k: Var = vf.add_var('avr.limitedFirstOrder.Gk.k_' + template_name)
    avr_limitedFirstOrder_I_initType: Var = vf.add_var('avr.limitedFirstOrder.I.initType_' + template_name)
    avr_limitedFirstOrder_I_k: Var = vf.add_var('avr.limitedFirstOrder.I.k_' + template_name)
    avr_limitedFirstOrder_I_use_reset: Var = vf.add_var('avr.limitedFirstOrder.I.use_reset_' + template_name)
    avr_limitedFirstOrder_I_use_set: Var = vf.add_var('avr.limitedFirstOrder.I.use_set_' + template_name)
    avr_limitedFirstOrder_I_y_start: Var = vf.add_var('avr.limitedFirstOrder.I.y_start_' + template_name)
    avr_limitedFirstOrder_K: Var = vf.add_var('avr.limitedFirstOrder.K_' + template_name)
    avr_limitedFirstOrder_Y0: Var = vf.add_var('avr.limitedFirstOrder.Y0_' + template_name)
    avr_limitedFirstOrder_YMax: Var = vf.add_var('avr.limitedFirstOrder.YMax_' + template_name)
    avr_limitedFirstOrder_YMin: Var = vf.add_var('avr.limitedFirstOrder.YMin_' + template_name)
    avr_limitedFirstOrder_lim_homotopyType: Var = vf.add_var('avr.limitedFirstOrder.lim.homotopyType_' + template_name)
    avr_limitedFirstOrder_lim_limitsAtInit: Var = vf.add_var('avr.limitedFirstOrder.lim.limitsAtInit_' + template_name)
    avr_limitedFirstOrder_lim_strict: Var = vf.add_var('avr.limitedFirstOrder.lim.strict_' + template_name)
    avr_limitedFirstOrder_lim_uMax: Var = vf.add_var('avr.limitedFirstOrder.lim.uMax_' + template_name)
    avr_limitedFirstOrder_lim_uMin: Var = vf.add_var('avr.limitedFirstOrder.lim.uMin_' + template_name)
    avr_limitedFirstOrder_tFilter: Var = vf.add_var('avr.limitedFirstOrder.tFilter_' + template_name)
    avr_power_base: Var = vf.add_var('avr.power.base_' + template_name)
    avr_power_useExp: Var = vf.add_var('avr.power.useExp_' + template_name)
    avr_sum1_k_1: Var = vf.add_var('avr.sum1.k[1]_' + template_name)
    avr_sum1_k_2: Var = vf.add_var('avr.sum1.k[2]_' + template_name)
    avr_sum1_k_3: Var = vf.add_var('avr.sum1.k[3]_' + template_name)
    avr_sum1_k_4: Var = vf.add_var('avr.sum1.k[4]_' + template_name)
    avr_sum1_k_5: Var = vf.add_var('avr.sum1.k[5]_' + template_name)
    avr_sum1_nin: Var = vf.add_var('avr.sum1.nin_' + template_name)
    avr_tA: Var = vf.add_var('avr.tA_' + template_name)
    avr_tB: Var = vf.add_var('avr.tB_' + template_name)
    avr_tC: Var = vf.add_var('avr.tC_' + template_name)
    avr_tE: Var = vf.add_var('avr.tE_' + template_name)
    avr_tF1: Var = vf.add_var('avr.tF1_' + template_name)
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
    # Declare the state variables used by the template.
    avr_derivative_x: Var = vf.add_var('avr.derivative.x_' + template_name)
    avr_firstOrder_y: Var = vf.add_var('avr.firstOrder.y_' + template_name)
    avr_limIntegrator_y: Var = vf.add_var('avr.limIntegrator.y_' + template_name)
    avr_limitedFirstOrder_I_y: Var = vf.add_var('avr.limitedFirstOrder.I.y_' + template_name)
    avr_transferFunction_x_scaled_1: Var = vf.add_var('avr.transferFunction.x_scaled[1]_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_avr_derivative_x: Var = vf.add_var('$START.avr.derivative.x_' + template_name)
    START_avr_firstOrder_y: Var = vf.add_var('$START.avr.firstOrder.y_' + template_name)
    START_avr_transferFunction_x_scaled_1: Var = vf.add_var('$START.avr.transferFunction.x_scaled[1]_' + template_name)
    avr_UOelPu: Var = vf.add_var('avr.UOelPu_' + template_name)
    avr_UPssPu: Var = vf.add_var('avr.UPssPu_' + template_name)
    avr_UUelPu: Var = vf.add_var('avr.UUelPu_' + template_name)
    avr_UsPu: Var = vf.add_var('avr.UsPu_' + template_name)
    avr_UsRefPu: Var = vf.add_var('avr.UsRefPu_' + template_name)
    avr_abs1_y: Var = vf.add_var('avr.abs1.y_' + template_name)
    avr_add_y: Var = vf.add_var('avr.add.y_' + template_name)
    avr_derivative_y: Var = vf.add_var('avr.derivative.y_' + template_name)
    avr_feedback_y: Var = vf.add_var('avr.feedback.y_' + template_name)
    avr_feedback1_y: Var = vf.add_var('avr.feedback1.y_' + template_name)
    avr_limIntegrator_local_reset: Var = vf.add_var('avr.limIntegrator.local_reset_' + template_name)
    avr_limIntegrator_local_set: Var = vf.add_var('avr.limIntegrator.local_set_' + template_name)
    avr_limitedFirstOrder_G_y: Var = vf.add_var('avr.limitedFirstOrder.G.y_' + template_name)
    avr_limitedFirstOrder_Gk_y: Var = vf.add_var('avr.limitedFirstOrder.Gk.y_' + template_name)
    avr_limitedFirstOrder_I_local_reset: Var = vf.add_var('avr.limitedFirstOrder.I.local_reset_' + template_name)
    avr_limitedFirstOrder_I_local_set: Var = vf.add_var('avr.limitedFirstOrder.I.local_set_' + template_name)
    avr_limitedFirstOrder_I_u: Var = vf.add_var('avr.limitedFirstOrder.I.u_' + template_name)
    avr_limitedFirstOrder_feedback_y: Var = vf.add_var('avr.limitedFirstOrder.feedback.y_' + template_name)
    avr_limitedFirstOrder_lim_simplifiedExpr: Var = vf.add_var('avr.limitedFirstOrder.lim.simplifiedExpr_' + template_name)
    avr_limitedFirstOrder_y: Var = vf.add_var('avr.limitedFirstOrder.y_' + template_name)
    avr_power_y: Var = vf.add_var('avr.power.y_' + template_name)
    avr_product_y: Var = vf.add_var('avr.product.y_' + template_name)
    avr_sum1_y: Var = vf.add_var('avr.sum1.y_' + template_name)
    avr_transferFunction_x_1: Var = vf.add_var('avr.transferFunction.x[1]_' + template_name)
    avr_transferFunction_y: Var = vf.add_var('avr.transferFunction.y_' + template_name)
    # Declare the differential variables used by the template.
    d_avr_derivative_x: Var = vf.add_diff_var('d_avr.derivative.x_' + template_name, base_var=avr_derivative_x)
    d_avr_firstOrder_y: Var = vf.add_diff_var('d_avr.firstOrder.y_' + template_name, base_var=avr_firstOrder_y)
    d_avr_limIntegrator_y: Var = vf.add_diff_var('d_avr.limIntegrator.y_' + template_name, base_var=avr_limIntegrator_y)
    d_avr_limitedFirstOrder_I_y: Var = vf.add_diff_var('d_avr.limitedFirstOrder.I.y_' + template_name, base_var=avr_limitedFirstOrder_I_y)
    d_avr_transferFunction_x_scaled_1: Var = vf.add_diff_var('d_avr.transferFunction.x_scaled[1]_' + template_name, base_var=avr_transferFunction_x_scaled_1)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((avr_firstOrder_k * avr_UsPu) - avr_firstOrder_y) / avr_firstOrder_T))
    state_equations.append((avr_limitedFirstOrder_I_k * avr_limitedFirstOrder_I_u))
    state_equations.append((((avr_transferFunction_a_end * avr_feedback_y) - (avr_transferFunction_a_2 * avr_transferFunction_x_scaled_1)) / avr_transferFunction_a_1))
    state_equations.append(((avr_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_derivative_zeroGain) * ((avr_product_y - avr_derivative_x) / avr_derivative_T))))
    state_equations.append((((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limIntegrator_outMin - avr_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((avr_limIntegrator_outMin - avr_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (avr_limIntegrator_k * avr_feedback1_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limIntegrator_outMin - avr_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (avr_limIntegrator_k * avr_feedback1_y)) - sym.Const(1e-06)))) * sym.heaviside(((avr_limIntegrator_y - avr_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((avr_limIntegrator_outMin - avr_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (avr_limIntegrator_k * avr_feedback1_y)) - sym.Const(1e-06)))) * sym.heaviside(((avr_limIntegrator_y - avr_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((avr_limIntegrator_k * avr_feedback1_y) - sym.Const(0.0)) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limIntegrator_outMin - avr_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((avr_limIntegrator_outMin - avr_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (avr_limIntegrator_k * avr_feedback1_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limIntegrator_outMin - avr_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (avr_limIntegrator_k * avr_feedback1_y)) - sym.Const(1e-06)))) * sym.heaviside(((avr_limIntegrator_y - avr_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((avr_limIntegrator_outMin - avr_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (avr_limIntegrator_k * avr_feedback1_y)) - sym.Const(1e-06)))) * sym.heaviside(((avr_limIntegrator_y - avr_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((avr_limIntegrator_k * avr_feedback1_y) - sym.Const(0.0)) - sym.Const(1e-06)))))))) * (avr_limIntegrator_k * avr_feedback1_y))))
    state_variables: list[Var] = list()
    state_variables.append(avr_firstOrder_y)
    state_variables.append(avr_limitedFirstOrder_I_y)
    state_variables.append(avr_transferFunction_x_scaled_1)
    state_variables.append(avr_derivative_x)
    state_variables.append(avr_limIntegrator_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((avr_sum1_y - (((((avr_sum1_k_1 * avr_firstOrder_y) + (avr_sum1_k_2 * avr_UOelPu)) + (avr_sum1_k_3 * avr_UPssPu)) + (avr_sum1_k_4 * avr_UUelPu)) + (avr_sum1_k_5 * avr_UsRefPu))))
    algebraic_equations.append((avr_transferFunction_x_1 - (avr_transferFunction_x_scaled_1 / avr_transferFunction_a_end)))
    algebraic_equations.append((avr_limitedFirstOrder_y - ((sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))) * avr_limitedFirstOrder_lim_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06))) * avr_limitedFirstOrder_lim_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06)))) * avr_limitedFirstOrder_I_y))))))
    algebraic_equations.append((avr_abs1_y - ((sym.heaviside(((avr_limIntegrator_y - sym.Const(0.0)) + sym.Const(1e-06))) * avr_limIntegrator_y) + ((sym.Const(1.0) - sym.heaviside(((avr_limIntegrator_y - sym.Const(0.0)) + sym.Const(1e-06)))) * (-avr_limIntegrator_y)))))
    algebraic_equations.append((avr_product_y - (avr_add_y * avr_limIntegrator_y)))
    algebraic_equations.append((avr_derivative_y - ((avr_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_derivative_zeroGain) * ((avr_derivative_k / avr_derivative_T) * (avr_product_y - avr_derivative_x))))))
    algebraic_equations.append((avr_feedback_y - (avr_sum1_y - avr_derivative_y)))
    algebraic_equations.append((avr_transferFunction_y - (((avr_transferFunction_bb_2 - (avr_transferFunction_d * avr_transferFunction_a_2)) * avr_transferFunction_x_1) + (avr_transferFunction_d * avr_feedback_y))))
    algebraic_equations.append((avr_limitedFirstOrder_Gk_y - (avr_limitedFirstOrder_Gk_k * avr_transferFunction_y)))
    algebraic_equations.append((avr_limitedFirstOrder_feedback_y - (avr_limitedFirstOrder_Gk_y - avr_limitedFirstOrder_y)))
    algebraic_equations.append((avr_limitedFirstOrder_G_y - (avr_limitedFirstOrder_G_k * avr_limitedFirstOrder_feedback_y)))
    algebraic_equations.append((avr_limitedFirstOrder_I_u - (((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06)))))))) * avr_limitedFirstOrder_G_y))))
    algebraic_equations.append((avr_feedback1_y - (avr_limitedFirstOrder_y - avr_product_y)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(avr_sum1_y)
    algebraic_variables.append(avr_transferFunction_x_1)
    algebraic_variables.append(avr_limitedFirstOrder_y)
    algebraic_variables.append(avr_abs1_y)
    algebraic_variables.append(avr_product_y)
    algebraic_variables.append(avr_derivative_y)
    algebraic_variables.append(avr_feedback_y)
    algebraic_variables.append(avr_transferFunction_y)
    algebraic_variables.append(avr_limitedFirstOrder_Gk_y)
    algebraic_variables.append(avr_limitedFirstOrder_feedback_y)
    algebraic_variables.append(avr_limitedFirstOrder_G_y)
    algebraic_variables.append(avr_limitedFirstOrder_I_u)
    algebraic_variables.append(avr_feedback1_y)
    algebraic_variables.append(avr_add_y)
    algebraic_variables.append(avr_UOelPu)
    algebraic_variables.append(avr_UPssPu)
    algebraic_variables.append(avr_UUelPu)
    algebraic_variables.append(avr_UsPu)
    algebraic_variables.append(avr_UsRefPu)
    algebraic_variables.append(avr_limitedFirstOrder_lim_simplifiedExpr)
    algebraic_variables.append(avr_limitedFirstOrder_I_local_reset)
    algebraic_variables.append(avr_limitedFirstOrder_I_local_set)
    algebraic_variables.append(avr_limIntegrator_local_reset)
    algebraic_variables.append(avr_limIntegrator_local_set)
    algebraic_variables.append(START_avr_transferFunction_x_scaled_1)
    algebraic_variables.append(START_avr_derivative_x)
    algebraic_variables.append(START_avr_firstOrder_y)
    algebraic_variables.append(avr_power_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_avr_firstOrder_y)
    differential_variables.append(d_avr_limitedFirstOrder_I_y)
    differential_variables.append(d_avr_transferFunction_x_scaled_1)
    differential_variables.append(d_avr_derivative_x)
    differential_variables.append(d_avr_limIntegrator_y)
    input_variables: list[Var] = list()
    input_variables.append(avr_UOelPu)
    input_variables.append(avr_UPssPu)
    input_variables.append(avr_UUelPu)
    input_variables.append(avr_UsPu)
    input_variables.append(avr_UsRefPu)
    output_variables: list[Var] = list()
    output_variables.append(avr_limIntegrator_y)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[avr_AEx] = vf.add_const(0.0, name='')
    event_parameters[avr_BEx] = vf.add_const(0.0, name='')
    event_parameters[avr_Efd0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_EfdMinPu] = vf.add_const(0.0, name='')
    event_parameters[avr_Ka] = vf.add_const(200.0, name='')
    event_parameters[avr_Ke] = vf.add_const(1.0, name='')
    event_parameters[avr_Kf] = vf.add_const(0.05, name='')
    event_parameters[avr_Us0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_UsRef0Pu] = ((avr_Va0Pu / avr_Ka) + avr_Us0Pu)
    event_parameters[avr_Va0Pu] = (avr_Efd0Pu * (avr_Ke + avr_AEx))
    event_parameters[avr_VrMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VrMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_add_k1] = avr_AEx
    event_parameters[avr_add_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_const_k] = avr_Ke
    event_parameters[avr_derivative_T] = avr_tF1
    event_parameters[avr_derivative_k] = avr_Kf
    event_parameters[avr_derivative_x_start] = avr_Va0Pu
    event_parameters[avr_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[avr_firstOrder_T] = avr_tR
    event_parameters[avr_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_y_start] = avr_Us0Pu
    event_parameters[avr_limIntegrator_k] = (sym.Const(1.0) / avr_tE)
    event_parameters[avr_limIntegrator_outMax] = vf.add_const(999.0, name='')
    event_parameters[avr_limIntegrator_outMin] = avr_EfdMinPu
    event_parameters[avr_limIntegrator_y_start] = avr_Efd0Pu
    event_parameters[avr_limitedFirstOrder_G_k] = (sym.Const(1.0) / avr_limitedFirstOrder_tFilter)
    event_parameters[avr_limitedFirstOrder_Gk_k] = avr_limitedFirstOrder_K
    event_parameters[avr_limitedFirstOrder_I_k] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_I_y_start] = avr_limitedFirstOrder_Y0
    event_parameters[avr_limitedFirstOrder_K] = avr_Ka
    event_parameters[avr_limitedFirstOrder_Y0] = avr_Va0Pu
    event_parameters[avr_limitedFirstOrder_YMax] = avr_VrMaxPu
    event_parameters[avr_limitedFirstOrder_YMin] = avr_VrMinPu
    event_parameters[avr_limitedFirstOrder_lim_uMax] = avr_limitedFirstOrder_YMax
    event_parameters[avr_limitedFirstOrder_lim_uMin] = avr_limitedFirstOrder_YMin
    event_parameters[avr_limitedFirstOrder_tFilter] = avr_tA
    event_parameters[avr_power_base] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_1] = vf.add_const(-1.0, name='')
    event_parameters[avr_sum1_k_2] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_3] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_4] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_5] = vf.add_const(1.0, name='')
    event_parameters[avr_tA] = vf.add_const(0.02, name='')
    event_parameters[avr_tB] = vf.add_const(1.0, name='')
    event_parameters[avr_tC] = vf.add_const(1.0, name='')
    event_parameters[avr_tE] = vf.add_const(0.5, name='')
    event_parameters[avr_tF1] = vf.add_const(1.0, name='')
    event_parameters[avr_tR] = vf.add_const(0.02, name='')
    event_parameters[avr_transferFunction_a_1] = avr_tB
    event_parameters[avr_transferFunction_a_2] = vf.add_const(1.0, name='')
    event_parameters[avr_transferFunction_a_end] = ((sym.heaviside(((avr_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((avr_transferFunction_a_1 ** sym.Const(2.0)) + (avr_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06))) * avr_transferFunction_a_2) + ((sym.Const(1.0) - sym.heaviside(((avr_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((avr_transferFunction_a_1 ** sym.Const(2.0)) + (avr_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06)))) * sym.Const(1.0)))
    event_parameters[avr_transferFunction_b_1] = avr_tC
    event_parameters[avr_transferFunction_b_2] = vf.add_const(1.0, name='')
    event_parameters[avr_transferFunction_bb_1] = avr_transferFunction_b_1
    event_parameters[avr_transferFunction_bb_2] = avr_transferFunction_b_2
    event_parameters[avr_transferFunction_d] = (avr_transferFunction_bb_1 / avr_transferFunction_a_1)
    event_parameters[avr_transferFunction_x_start_1] = (avr_Va0Pu / avr_Ka)
    event_parameters[avr_transferFunction_y_start] = (avr_Va0Pu / avr_Ka)
    event_parameters[avr_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_limIntegrator_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_limitedFirstOrder_I_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_nin] = vf.add_const(5.0, name='')
    event_parameters[avr_transferFunction_na] = vf.add_const(2.0, name='')
    event_parameters[avr_transferFunction_nb] = vf.add_const(2.0, name='')
    event_parameters[avr_transferFunction_nx] = vf.add_const(1.0, name='')
    event_parameters[avr_abs1_generateEvent] = vf.add_const(0.0, name='')
    event_parameters[avr_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(avr_derivative_k)) - sym.Const(1e-06)))
    event_parameters[avr_limIntegrator_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limIntegrator_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_limIntegrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_limIntegrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_I_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_I_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_power_useExp] = vf.add_const(1.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[avr_derivative_x] = avr_derivative_x_start
    initial_equations[avr_firstOrder_y] = (avr_firstOrder_k * avr_UsPu)
    initial_equations[avr_limIntegrator_y] = avr_limIntegrator_y_start
    initial_equations[avr_limitedFirstOrder_I_y] = avr_limitedFirstOrder_I_y_start
    initial_equations[avr_transferFunction_x_scaled_1] = (avr_transferFunction_a_end * avr_transferFunction_x_start_1)
    initial_equations[avr_UOelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UPssPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UUelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UsPu] = avr_Us0Pu
    initial_equations[avr_UsRefPu] = avr_UsRef0Pu
    initial_equations[avr_limitedFirstOrder_y] = avr_limitedFirstOrder_Y0
    initial_equations[avr_product_y] = vf.add_const(1.0, name='')
    initial_equations[avr_transferFunction_x_1] = avr_transferFunction_x_start_1
    initial_equations[avr_transferFunction_y] = avr_transferFunction_y_start
    initial_equations[avr_limitedFirstOrder_lim_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_I_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_I_local_set] = vf.add_const(0.0, name='')
    initial_equations[avr_limIntegrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_limIntegrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[avr_add_y] = (avr_add_k1 + (avr_add_k2 * avr_const_k))
    initial_equations[avr_power_y] = vf.add_const(1.0, name='')
    initial_equations[avr_sum1_y] = (((((avr_sum1_k_1 * avr_firstOrder_y) + (avr_sum1_k_2 * avr_UOelPu)) + (avr_sum1_k_3 * avr_UPssPu)) + (avr_sum1_k_4 * avr_UUelPu)) + (avr_sum1_k_5 * avr_UsRefPu))
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

    template.comment = 'Generator AVR/exciter IEEX2A'
    return template
