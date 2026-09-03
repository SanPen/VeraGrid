# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'St4c'.

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

def build_st4c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'St4c'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    avr_Efd0Pu: Var = vf.add_var('avr.Efd0Pu_' + template_name)
    avr_Ir0Pu: Var = vf.add_var('avr.Ir0Pu_' + template_name)
    avr_Kc: Var = vf.add_var('avr.Kc_' + template_name)
    avr_Kg: Var = vf.add_var('avr.Kg_' + template_name)
    avr_Ki: Var = vf.add_var('avr.Ki_' + template_name)
    avr_Kim: Var = vf.add_var('avr.Kim_' + template_name)
    avr_Kir: Var = vf.add_var('avr.Kir_' + template_name)
    avr_Kp: Var = vf.add_var('avr.Kp_' + template_name)
    avr_Kpm: Var = vf.add_var('avr.Kpm_' + template_name)
    avr_Kpr: Var = vf.add_var('avr.Kpr_' + template_name)
    avr_PositionOel: Var = vf.add_var('avr.PositionOel_' + template_name)
    avr_PositionPss: Var = vf.add_var('avr.PositionPss_' + template_name)
    avr_PositionScl: Var = vf.add_var('avr.PositionScl_' + template_name)
    avr_PositionUel: Var = vf.add_var('avr.PositionUel_' + template_name)
    avr_Sw1: Var = vf.add_var('avr.Sw1_' + template_name)
    avr_Thetap: Var = vf.add_var('avr.Thetap_' + template_name)
    avr_UOel0Pu: Var = vf.add_var('avr.UOel0Pu_' + template_name)
    avr_USclOel0Pu: Var = vf.add_var('avr.USclOel0Pu_' + template_name)
    avr_USclUel0Pu: Var = vf.add_var('avr.USclUel0Pu_' + template_name)
    avr_UUel0Pu: Var = vf.add_var('avr.UUel0Pu_' + template_name)
    avr_Us0Pu: Var = vf.add_var('avr.Us0Pu_' + template_name)
    avr_VaMaxPu: Var = vf.add_var('avr.VaMaxPu_' + template_name)
    avr_VaMinPu: Var = vf.add_var('avr.VaMinPu_' + template_name)
    avr_Vb0Pu: Var = vf.add_var('avr.Vb0Pu_' + template_name)
    avr_VbMaxPu: Var = vf.add_var('avr.VbMaxPu_' + template_name)
    avr_VgMaxPu: Var = vf.add_var('avr.VgMaxPu_' + template_name)
    avr_VmMaxPu: Var = vf.add_var('avr.VmMaxPu_' + template_name)
    avr_VmMinPu: Var = vf.add_var('avr.VmMinPu_' + template_name)
    avr_VrMaxPu: Var = vf.add_var('avr.VrMaxPu_' + template_name)
    avr_VrMinPu: Var = vf.add_var('avr.VrMinPu_' + template_name)
    avr_XlPu: Var = vf.add_var('avr.XlPu_' + template_name)
    avr_add_k1: Var = vf.add_var('avr.add.k1_' + template_name)
    avr_add_k2: Var = vf.add_var('avr.add.k2_' + template_name)
    avr_booleanConstant_k: Var = vf.add_var('avr.booleanConstant.k_' + template_name)
    avr_const_k: Var = vf.add_var('avr.const.k_' + template_name)
    avr_const1_k: Var = vf.add_var('avr.const1.k_' + template_name)
    avr_const2_k: Var = vf.add_var('avr.const2.k_' + template_name)
    avr_firstOrder_T: Var = vf.add_var('avr.firstOrder.T_' + template_name)
    avr_firstOrder_initType: Var = vf.add_var('avr.firstOrder.initType_' + template_name)
    avr_firstOrder_k: Var = vf.add_var('avr.firstOrder.k_' + template_name)
    avr_firstOrder_y_start: Var = vf.add_var('avr.firstOrder.y_start_' + template_name)
    avr_firstOrder1_T: Var = vf.add_var('avr.firstOrder1.T_' + template_name)
    avr_firstOrder1_initType: Var = vf.add_var('avr.firstOrder1.initType_' + template_name)
    avr_firstOrder1_k: Var = vf.add_var('avr.firstOrder1.k_' + template_name)
    avr_firstOrder1_y_start: Var = vf.add_var('avr.firstOrder1.y_start_' + template_name)
    avr_gain1_k: Var = vf.add_var('avr.gain1.k_' + template_name)
    avr_it0Pu_im: Var = vf.add_var('avr.it0Pu.im_' + template_name)
    avr_it0Pu_re: Var = vf.add_var('avr.it0Pu.re_' + template_name)
    avr_limPI1_Ki: Var = vf.add_var('avr.limPI1.Ki_' + template_name)
    avr_limPI1_Kp: Var = vf.add_var('avr.limPI1.Kp_' + template_name)
    avr_limPI1_Tol: Var = vf.add_var('avr.limPI1.Tol_' + template_name)
    avr_limPI1_Y0: Var = vf.add_var('avr.limPI1.Y0_' + template_name)
    avr_limPI1_YMax: Var = vf.add_var('avr.limPI1.YMax_' + template_name)
    avr_limPI1_YMin: Var = vf.add_var('avr.limPI1.YMin_' + template_name)
    avr_limPI1_add_k1: Var = vf.add_var('avr.limPI1.add.k1_' + template_name)
    avr_limPI1_add_k2: Var = vf.add_var('avr.limPI1.add.k2_' + template_name)
    avr_limPI1_const_k: Var = vf.add_var('avr.limPI1.const.k_' + template_name)
    avr_limPI1_hysteresisMax_pre_y_start: Var = vf.add_var('avr.limPI1.hysteresisMax.pre_y_start_' + template_name)
    avr_limPI1_hysteresisMax_uHigh: Var = vf.add_var('avr.limPI1.hysteresisMax.uHigh_' + template_name)
    avr_limPI1_hysteresisMax_uLow: Var = vf.add_var('avr.limPI1.hysteresisMax.uLow_' + template_name)
    avr_limPI1_hysteresisMin_pre_y_start: Var = vf.add_var('avr.limPI1.hysteresisMin.pre_y_start_' + template_name)
    avr_limPI1_hysteresisMin_uHigh: Var = vf.add_var('avr.limPI1.hysteresisMin.uHigh_' + template_name)
    avr_limPI1_hysteresisMin_uLow: Var = vf.add_var('avr.limPI1.hysteresisMin.uLow_' + template_name)
    avr_limPI1_integrator_initType: Var = vf.add_var('avr.limPI1.integrator.initType_' + template_name)
    avr_limPI1_integrator_k: Var = vf.add_var('avr.limPI1.integrator.k_' + template_name)
    avr_limPI1_integrator_use_reset: Var = vf.add_var('avr.limPI1.integrator.use_reset_' + template_name)
    avr_limPI1_integrator_use_set: Var = vf.add_var('avr.limPI1.integrator.use_set_' + template_name)
    avr_limPI1_integrator_y_start: Var = vf.add_var('avr.limPI1.integrator.y_start_' + template_name)
    avr_limPI1_limiter1_homotopyType: Var = vf.add_var('avr.limPI1.limiter1.homotopyType_' + template_name)
    avr_limPI1_limiter1_limitsAtInit: Var = vf.add_var('avr.limPI1.limiter1.limitsAtInit_' + template_name)
    avr_limPI1_limiter1_strict: Var = vf.add_var('avr.limPI1.limiter1.strict_' + template_name)
    avr_limPI1_limiter1_uMax: Var = vf.add_var('avr.limPI1.limiter1.uMax_' + template_name)
    avr_limPI1_limiter1_uMin: Var = vf.add_var('avr.limPI1.limiter1.uMin_' + template_name)
    avr_limPI2_Ki: Var = vf.add_var('avr.limPI2.Ki_' + template_name)
    avr_limPI2_Kp: Var = vf.add_var('avr.limPI2.Kp_' + template_name)
    avr_limPI2_Tol: Var = vf.add_var('avr.limPI2.Tol_' + template_name)
    avr_limPI2_Y0: Var = vf.add_var('avr.limPI2.Y0_' + template_name)
    avr_limPI2_YMax: Var = vf.add_var('avr.limPI2.YMax_' + template_name)
    avr_limPI2_YMin: Var = vf.add_var('avr.limPI2.YMin_' + template_name)
    avr_limPI2_add_k1: Var = vf.add_var('avr.limPI2.add.k1_' + template_name)
    avr_limPI2_add_k2: Var = vf.add_var('avr.limPI2.add.k2_' + template_name)
    avr_limPI2_const_k: Var = vf.add_var('avr.limPI2.const.k_' + template_name)
    avr_limPI2_hysteresisMax_pre_y_start: Var = vf.add_var('avr.limPI2.hysteresisMax.pre_y_start_' + template_name)
    avr_limPI2_hysteresisMax_uHigh: Var = vf.add_var('avr.limPI2.hysteresisMax.uHigh_' + template_name)
    avr_limPI2_hysteresisMax_uLow: Var = vf.add_var('avr.limPI2.hysteresisMax.uLow_' + template_name)
    avr_limPI2_hysteresisMin_pre_y_start: Var = vf.add_var('avr.limPI2.hysteresisMin.pre_y_start_' + template_name)
    avr_limPI2_hysteresisMin_uHigh: Var = vf.add_var('avr.limPI2.hysteresisMin.uHigh_' + template_name)
    avr_limPI2_hysteresisMin_uLow: Var = vf.add_var('avr.limPI2.hysteresisMin.uLow_' + template_name)
    avr_limPI2_integrator_initType: Var = vf.add_var('avr.limPI2.integrator.initType_' + template_name)
    avr_limPI2_integrator_k: Var = vf.add_var('avr.limPI2.integrator.k_' + template_name)
    avr_limPI2_integrator_use_reset: Var = vf.add_var('avr.limPI2.integrator.use_reset_' + template_name)
    avr_limPI2_integrator_use_set: Var = vf.add_var('avr.limPI2.integrator.use_set_' + template_name)
    avr_limPI2_integrator_y_start: Var = vf.add_var('avr.limPI2.integrator.y_start_' + template_name)
    avr_limPI2_limiter1_homotopyType: Var = vf.add_var('avr.limPI2.limiter1.homotopyType_' + template_name)
    avr_limPI2_limiter1_limitsAtInit: Var = vf.add_var('avr.limPI2.limiter1.limitsAtInit_' + template_name)
    avr_limPI2_limiter1_strict: Var = vf.add_var('avr.limPI2.limiter1.strict_' + template_name)
    avr_limPI2_limiter1_uMax: Var = vf.add_var('avr.limPI2.limiter1.uMax_' + template_name)
    avr_limPI2_limiter1_uMin: Var = vf.add_var('avr.limPI2.limiter1.uMin_' + template_name)
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
    avr_max1_nu: Var = vf.add_var('avr.max1.nu_' + template_name)
    avr_max2_nu: Var = vf.add_var('avr.max2.nu_' + template_name)
    avr_min1_nu: Var = vf.add_var('avr.min1.nu_' + template_name)
    avr_min2_nu: Var = vf.add_var('avr.min2.nu_' + template_name)
    avr_potentialCircuit_Ki: Var = vf.add_var('avr.potentialCircuit.Ki_' + template_name)
    avr_potentialCircuit_Kp: Var = vf.add_var('avr.potentialCircuit.Kp_' + template_name)
    avr_potentialCircuit_Theta: Var = vf.add_var('avr.potentialCircuit.Theta_' + template_name)
    avr_potentialCircuit_X: Var = vf.add_var('avr.potentialCircuit.X_' + template_name)
    avr_potentialCircuit_j_im: Var = vf.add_var('avr.potentialCircuit.j.im_' + template_name)
    avr_potentialCircuit_j_re: Var = vf.add_var('avr.potentialCircuit.j.re_' + template_name)
    avr_rectifierRegulationCharacteristic_A1: Var = vf.add_var('avr.rectifierRegulationCharacteristic.A1_' + template_name)
    avr_rectifierRegulationCharacteristic_A2: Var = vf.add_var('avr.rectifierRegulationCharacteristic.A2_' + template_name)
    avr_rectifierRegulationCharacteristic_UHigh: Var = vf.add_var('avr.rectifierRegulationCharacteristic.UHigh_' + template_name)
    avr_rectifierRegulationCharacteristic_ULow: Var = vf.add_var('avr.rectifierRegulationCharacteristic.ULow_' + template_name)
    avr_sum1_k_1: Var = vf.add_var('avr.sum1.k[1]_' + template_name)
    avr_sum1_k_2: Var = vf.add_var('avr.sum1.k[2]_' + template_name)
    avr_sum1_k_3: Var = vf.add_var('avr.sum1.k[3]_' + template_name)
    avr_sum1_k_4: Var = vf.add_var('avr.sum1.k[4]_' + template_name)
    avr_sum1_k_5: Var = vf.add_var('avr.sum1.k[5]_' + template_name)
    avr_sum1_k_6: Var = vf.add_var('avr.sum1.k[6]_' + template_name)
    avr_sum1_nin: Var = vf.add_var('avr.sum1.nin_' + template_name)
    avr_tA: Var = vf.add_var('avr.tA_' + template_name)
    avr_tG: Var = vf.add_var('avr.tG_' + template_name)
    avr_tR: Var = vf.add_var('avr.tR_' + template_name)
    avr_ut0Pu_im: Var = vf.add_var('avr.ut0Pu.im_' + template_name)
    avr_ut0Pu_re: Var = vf.add_var('avr.ut0Pu.re_' + template_name)
    # Declare the state variables used by the template.
    avr_firstOrder_y: Var = vf.add_var('avr.firstOrder.y_' + template_name)
    avr_firstOrder1_y: Var = vf.add_var('avr.firstOrder1.y_' + template_name)
    avr_limPI1_integrator_y: Var = vf.add_var('avr.limPI1.integrator.y_' + template_name)
    avr_limPI2_integrator_y: Var = vf.add_var('avr.limPI2.integrator.y_' + template_name)
    avr_limitedFirstOrder_I_y: Var = vf.add_var('avr.limitedFirstOrder.I.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_avr_limPI1_hysteresisMax_y: Var = vf.add_var('$PRE.avr.limPI1.hysteresisMax.y_' + template_name)
    PRE_avr_limPI1_hysteresisMin_y: Var = vf.add_var('$PRE.avr.limPI1.hysteresisMin.y_' + template_name)
    PRE_avr_limPI2_hysteresisMax_y: Var = vf.add_var('$PRE.avr.limPI2.hysteresisMax.y_' + template_name)
    PRE_avr_limPI2_hysteresisMin_y: Var = vf.add_var('$PRE.avr.limPI2.hysteresisMin.y_' + template_name)
    START_avr_firstOrder_y: Var = vf.add_var('$START.avr.firstOrder.y_' + template_name)
    START_avr_firstOrder1_y: Var = vf.add_var('$START.avr.firstOrder1.y_' + template_name)
    avr_EfdPu: Var = vf.add_var('avr.EfdPu_' + template_name)
    avr_IrPu: Var = vf.add_var('avr.IrPu_' + template_name)
    avr_UOelPu: Var = vf.add_var('avr.UOelPu_' + template_name)
    avr_UPssPu: Var = vf.add_var('avr.UPssPu_' + template_name)
    avr_USclOelPu: Var = vf.add_var('avr.USclOelPu_' + template_name)
    avr_USclUelPu: Var = vf.add_var('avr.USclUelPu_' + template_name)
    avr_UUelPu: Var = vf.add_var('avr.UUelPu_' + template_name)
    avr_UsPu: Var = vf.add_var('avr.UsPu_' + template_name)
    avr_UsRefPu: Var = vf.add_var('avr.UsRefPu_' + template_name)
    avr_add_u2: Var = vf.add_var('avr.add.u2_' + template_name)
    avr_division_y: Var = vf.add_var('avr.division.y_' + template_name)
    avr_feedback_y: Var = vf.add_var('avr.feedback.y_' + template_name)
    avr_itPu_im: Var = vf.add_var('avr.itPu.im_' + template_name)
    avr_itPu_re: Var = vf.add_var('avr.itPu.re_' + template_name)
    avr_limPI1_add_y: Var = vf.add_var('avr.limPI1.add.y_' + template_name)
    avr_limPI1_hysteresisMax_y: Var = vf.add_var('avr.limPI1.hysteresisMax.y_' + template_name)
    avr_limPI1_hysteresisMin_y: Var = vf.add_var('avr.limPI1.hysteresisMin.y_' + template_name)
    avr_limPI1_integrator_local_reset: Var = vf.add_var('avr.limPI1.integrator.local_reset_' + template_name)
    avr_limPI1_integrator_local_set: Var = vf.add_var('avr.limPI1.integrator.local_set_' + template_name)
    avr_limPI1_limiter1_simplifiedExpr: Var = vf.add_var('avr.limPI1.limiter1.simplifiedExpr_' + template_name)
    avr_limPI1_switch1_u2: Var = vf.add_var('avr.limPI1.switch1.u2_' + template_name)
    avr_limPI1_switch1_y: Var = vf.add_var('avr.limPI1.switch1.y_' + template_name)
    avr_limPI1_y: Var = vf.add_var('avr.limPI1.y_' + template_name)
    avr_limPI2_add_y: Var = vf.add_var('avr.limPI2.add.y_' + template_name)
    avr_limPI2_hysteresisMax_y: Var = vf.add_var('avr.limPI2.hysteresisMax.y_' + template_name)
    avr_limPI2_hysteresisMin_y: Var = vf.add_var('avr.limPI2.hysteresisMin.y_' + template_name)
    avr_limPI2_integrator_local_reset: Var = vf.add_var('avr.limPI2.integrator.local_reset_' + template_name)
    avr_limPI2_integrator_local_set: Var = vf.add_var('avr.limPI2.integrator.local_set_' + template_name)
    avr_limPI2_limiter1_simplifiedExpr: Var = vf.add_var('avr.limPI2.limiter1.simplifiedExpr_' + template_name)
    avr_limPI2_switch1_u2: Var = vf.add_var('avr.limPI2.switch1.u2_' + template_name)
    avr_limPI2_switch1_y: Var = vf.add_var('avr.limPI2.switch1.y_' + template_name)
    avr_limitedFirstOrder_G_y: Var = vf.add_var('avr.limitedFirstOrder.G.y_' + template_name)
    avr_limitedFirstOrder_Gk_y: Var = vf.add_var('avr.limitedFirstOrder.Gk.y_' + template_name)
    avr_limitedFirstOrder_I_local_reset: Var = vf.add_var('avr.limitedFirstOrder.I.local_reset_' + template_name)
    avr_limitedFirstOrder_I_local_set: Var = vf.add_var('avr.limitedFirstOrder.I.local_set_' + template_name)
    avr_limitedFirstOrder_I_u: Var = vf.add_var('avr.limitedFirstOrder.I.u_' + template_name)
    avr_limitedFirstOrder_feedback_y: Var = vf.add_var('avr.limitedFirstOrder.feedback.y_' + template_name)
    avr_limitedFirstOrder_lim_simplifiedExpr: Var = vf.add_var('avr.limitedFirstOrder.lim.simplifiedExpr_' + template_name)
    avr_limitedFirstOrder_y: Var = vf.add_var('avr.limitedFirstOrder.y_' + template_name)
    avr_max1_u_3: Var = vf.add_var('avr.max1.u[3]_' + template_name)
    avr_min1_u_3: Var = vf.add_var('avr.min1.u[3]_' + template_name)
    avr_min2_u_3: Var = vf.add_var('avr.min2.u[3]_' + template_name)
    avr_min3_y: Var = vf.add_var('avr.min3.y_' + template_name)
    avr_min4_y: Var = vf.add_var('avr.min4.y_' + template_name)
    avr_potentialCircuit_v1_im: Var = vf.add_var('avr.potentialCircuit.v1.im_' + template_name)
    avr_potentialCircuit_v1_re: Var = vf.add_var('avr.potentialCircuit.v1.re_' + template_name)
    avr_potentialCircuit_v2_im: Var = vf.add_var('avr.potentialCircuit.v2.im_' + template_name)
    avr_potentialCircuit_v2_re: Var = vf.add_var('avr.potentialCircuit.v2.re_' + template_name)
    avr_potentialCircuit_vE: Var = vf.add_var('avr.potentialCircuit.vE_' + template_name)
    avr_product1_y: Var = vf.add_var('avr.product1.y_' + template_name)
    avr_rectifierRegulationCharacteristic_y: Var = vf.add_var('avr.rectifierRegulationCharacteristic.y_' + template_name)
    avr_sum1_u_3: Var = vf.add_var('avr.sum1.u[3]_' + template_name)
    avr_sum1_u_4: Var = vf.add_var('avr.sum1.u[4]_' + template_name)
    avr_sum1_u_5: Var = vf.add_var('avr.sum1.u[5]_' + template_name)
    avr_sum1_u_6: Var = vf.add_var('avr.sum1.u[6]_' + template_name)
    avr_switch_y: Var = vf.add_var('avr.switch.y_' + template_name)
    avr_utPu_im: Var = vf.add_var('avr.utPu.im_' + template_name)
    avr_utPu_re: Var = vf.add_var('avr.utPu.re_' + template_name)
    # Declare the differential variables used by the template.
    d_avr_firstOrder_y: Var = vf.add_diff_var('d_avr.firstOrder.y_' + template_name, base_var=avr_firstOrder_y)
    d_avr_firstOrder1_y: Var = vf.add_diff_var('d_avr.firstOrder1.y_' + template_name, base_var=avr_firstOrder1_y)
    d_avr_limPI1_integrator_y: Var = vf.add_diff_var('d_avr.limPI1.integrator.y_' + template_name, base_var=avr_limPI1_integrator_y)
    d_avr_limPI2_integrator_y: Var = vf.add_diff_var('d_avr.limPI2.integrator.y_' + template_name, base_var=avr_limPI2_integrator_y)
    d_avr_limitedFirstOrder_I_y: Var = vf.add_diff_var('d_avr.limitedFirstOrder.I.y_' + template_name, base_var=avr_limitedFirstOrder_I_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((avr_firstOrder_k * avr_UsPu) - avr_firstOrder_y) / avr_firstOrder_T))
    state_equations.append((avr_limPI1_integrator_k * avr_limPI1_switch1_y))
    state_equations.append((((avr_firstOrder1_k * avr_EfdPu) - avr_firstOrder1_y) / avr_firstOrder1_T))
    state_equations.append((avr_limitedFirstOrder_I_k * avr_limitedFirstOrder_I_u))
    state_equations.append((avr_limPI2_integrator_k * avr_limPI2_switch1_y))
    state_variables: list[Var] = list()
    state_variables.append(avr_firstOrder_y)
    state_variables.append(avr_limPI1_integrator_y)
    state_variables.append(avr_firstOrder1_y)
    state_variables.append(avr_limitedFirstOrder_I_y)
    state_variables.append(avr_limPI2_integrator_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((avr_switch_y - ((avr_booleanConstant_k * avr_potentialCircuit_vE) + ((sym.Const(1.0) - avr_booleanConstant_k) * avr_const1_k))))
    algebraic_equations.append((avr_division_y - (avr_gain1_k / avr_switch_y)))
    algebraic_equations.append((avr_rectifierRegulationCharacteristic_y - ((sym.heaviside(((sym.Const(0.0) - avr_division_y) + sym.Const(1e-06))) * sym.Const(1.0)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(0.0) - avr_division_y) + sym.Const(1e-06)))) * ((((sym.heaviside(((avr_division_y - sym.Const(0.0)) - sym.Const(1e-06))) * sym.heaviside(((avr_division_y - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.heaviside(((avr_rectifierRegulationCharacteristic_ULow - avr_division_y) + sym.Const(1e-06)))) * (sym.Const(1.0) - (avr_rectifierRegulationCharacteristic_A1 * avr_division_y))) + ((sym.Const(1.0) - ((sym.heaviside(((avr_division_y - sym.Const(0.0)) - sym.Const(1e-06))) * sym.heaviside(((avr_division_y - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.heaviside(((avr_rectifierRegulationCharacteristic_ULow - avr_division_y) + sym.Const(1e-06))))) * ((((sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06))) * sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06)))) * sym.heaviside(((avr_rectifierRegulationCharacteristic_UHigh - avr_division_y) - sym.Const(1e-06)))) * sym.sqrt((avr_rectifierRegulationCharacteristic_UHigh - (avr_division_y ** sym.Const(2.0))))) + ((sym.Const(1.0) - ((sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06))) * sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06)))) * sym.heaviside(((avr_rectifierRegulationCharacteristic_UHigh - avr_division_y) - sym.Const(1e-06))))) * ((((sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06))) * sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - avr_division_y) + sym.Const(1e-06)))) * (avr_rectifierRegulationCharacteristic_A2 * (sym.Const(1.0) - avr_division_y))) + ((sym.Const(1.0) - ((sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06))) * sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - avr_division_y) + sym.Const(1e-06))))) * sym.Const(0.0)))))))))))
    algebraic_equations.append((avr_product1_y - (avr_rectifierRegulationCharacteristic_y * avr_switch_y)))
    algebraic_equations.append((avr_min3_y - ((avr_const_k * sym.heaviside((avr_product1_y - avr_const_k))) + (avr_product1_y * (sym.Const(1) - sym.heaviside((avr_product1_y - avr_const_k)))))))
    algebraic_equations.append((avr_max1_u_3 - ((avr_sum1_k_1 * avr_firstOrder_y) + avr_sum1_k_2)))
    algebraic_equations.append((avr_min1_u_3 - ((((((avr_UsRefPu - avr_firstOrder_y) + avr_UOelPu) + avr_UPssPu) + avr_USclOelPu) + avr_USclUelPu) + avr_UUelPu)))
    algebraic_equations.append((avr_limPI1_add_y - ((avr_limPI1_add_k1 * avr_min1_u_3) + (avr_limPI1_add_k2 * avr_limPI1_integrator_y))))
    algebraic_equations.append((avr_limPI1_hysteresisMax_y - (sym.heaviside(((avr_limPI1_add_y - avr_limPI1_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_avr_limPI1_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((avr_limPI1_add_y - avr_limPI1_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((avr_limPI1_hysteresisMax_uLow - avr_limPI1_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((avr_limPI1_hysteresisMin_y - (sym.heaviside(((avr_limPI1_add_y - avr_limPI1_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_avr_limPI1_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((avr_limPI1_add_y - avr_limPI1_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((avr_limPI1_hysteresisMin_uLow - avr_limPI1_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((avr_limPI1_switch1_u2 - (sym.Const(1.0) - ((sym.Const(1.0) - avr_limPI1_hysteresisMax_y) * (sym.Const(1.0) - (sym.Const(1.0) - avr_limPI1_hysteresisMin_y))))))
    algebraic_equations.append((avr_limPI1_y - ((sym.heaviside(((avr_limPI1_add_y - avr_limPI1_limiter1_uMax) - sym.Const(1e-06))) * avr_limPI1_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_limPI1_add_y - avr_limPI1_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limPI1_limiter1_uMin - avr_limPI1_add_y) - sym.Const(1e-06))) * avr_limPI1_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limPI1_limiter1_uMin - avr_limPI1_add_y) - sym.Const(1e-06)))) * avr_limPI1_add_y))))))
    algebraic_equations.append((avr_limPI1_switch1_y - ((avr_limPI1_switch1_u2 * avr_limPI1_const_k) + ((sym.Const(1.0) - avr_limPI1_switch1_u2) * avr_min1_u_3))))
    algebraic_equations.append((avr_limitedFirstOrder_y - ((sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))) * avr_limitedFirstOrder_lim_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06))) * avr_limitedFirstOrder_lim_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06)))) * avr_limitedFirstOrder_I_y))))))
    algebraic_equations.append((avr_EfdPu - (avr_limitedFirstOrder_y * avr_min3_y)))
    algebraic_equations.append((avr_min4_y - ((avr_const2_k * sym.heaviside((avr_firstOrder1_y - avr_const2_k))) + (avr_firstOrder1_y * (sym.Const(1) - sym.heaviside((avr_firstOrder1_y - avr_const2_k)))))))
    algebraic_equations.append((avr_feedback_y - (avr_limPI1_y - avr_min4_y)))
    algebraic_equations.append((avr_limPI2_add_y - ((avr_limPI2_add_k1 * avr_feedback_y) + (avr_limPI2_add_k2 * avr_limPI2_integrator_y))))
    algebraic_equations.append((avr_min2_u_3 - ((sym.heaviside(((avr_limPI2_add_y - avr_limPI2_limiter1_uMax) - sym.Const(1e-06))) * avr_limPI2_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_limPI2_add_y - avr_limPI2_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limPI2_limiter1_uMin - avr_limPI2_add_y) - sym.Const(1e-06))) * avr_limPI2_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limPI2_limiter1_uMin - avr_limPI2_add_y) - sym.Const(1e-06)))) * avr_limPI2_add_y))))))
    algebraic_equations.append((avr_limitedFirstOrder_Gk_y - (avr_limitedFirstOrder_Gk_k * avr_min2_u_3)))
    algebraic_equations.append((avr_limitedFirstOrder_feedback_y - (avr_limitedFirstOrder_Gk_y - avr_limitedFirstOrder_y)))
    algebraic_equations.append((avr_limitedFirstOrder_G_y - (avr_limitedFirstOrder_G_k * avr_limitedFirstOrder_feedback_y)))
    algebraic_equations.append((avr_limitedFirstOrder_I_u - (((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06)))))))) * avr_limitedFirstOrder_G_y))))
    algebraic_equations.append((avr_limPI2_hysteresisMax_y - (sym.heaviside(((avr_limPI2_add_y - avr_limPI2_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_avr_limPI2_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((avr_limPI2_add_y - avr_limPI2_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((avr_limPI2_hysteresisMax_uLow - avr_limPI2_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((avr_limPI2_hysteresisMin_y - (sym.heaviside(((avr_limPI2_add_y - avr_limPI2_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_avr_limPI2_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((avr_limPI2_add_y - avr_limPI2_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((avr_limPI2_hysteresisMin_uLow - avr_limPI2_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((avr_limPI2_switch1_u2 - (sym.Const(1.0) - ((sym.Const(1.0) - avr_limPI2_hysteresisMax_y) * (sym.Const(1.0) - (sym.Const(1.0) - avr_limPI2_hysteresisMin_y))))))
    algebraic_equations.append((avr_limPI2_switch1_y - ((avr_limPI2_switch1_u2 * avr_limPI2_const_k) + ((sym.Const(1.0) - avr_limPI2_switch1_u2) * avr_feedback_y))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(avr_switch_y)
    algebraic_variables.append(avr_division_y)
    algebraic_variables.append(avr_rectifierRegulationCharacteristic_y)
    algebraic_variables.append(avr_product1_y)
    algebraic_variables.append(avr_min3_y)
    algebraic_variables.append(avr_max1_u_3)
    algebraic_variables.append(avr_min1_u_3)
    algebraic_variables.append(avr_limPI1_add_y)
    algebraic_variables.append(avr_limPI1_hysteresisMax_y)
    algebraic_variables.append(avr_limPI1_hysteresisMin_y)
    algebraic_variables.append(avr_limPI1_switch1_u2)
    algebraic_variables.append(avr_limPI1_y)
    algebraic_variables.append(avr_limPI1_switch1_y)
    algebraic_variables.append(avr_limitedFirstOrder_y)
    algebraic_variables.append(avr_EfdPu)
    algebraic_variables.append(avr_min4_y)
    algebraic_variables.append(avr_feedback_y)
    algebraic_variables.append(avr_limPI2_add_y)
    algebraic_variables.append(avr_min2_u_3)
    algebraic_variables.append(avr_limitedFirstOrder_Gk_y)
    algebraic_variables.append(avr_limitedFirstOrder_feedback_y)
    algebraic_variables.append(avr_limitedFirstOrder_G_y)
    algebraic_variables.append(avr_limitedFirstOrder_I_u)
    algebraic_variables.append(avr_limPI2_hysteresisMax_y)
    algebraic_variables.append(avr_limPI2_hysteresisMin_y)
    algebraic_variables.append(avr_limPI2_switch1_u2)
    algebraic_variables.append(avr_limPI2_switch1_y)
    algebraic_variables.append(avr_potentialCircuit_vE)
    algebraic_variables.append(avr_IrPu)
    algebraic_variables.append(avr_UOelPu)
    algebraic_variables.append(avr_UPssPu)
    algebraic_variables.append(avr_USclOelPu)
    algebraic_variables.append(avr_USclUelPu)
    algebraic_variables.append(avr_UUelPu)
    algebraic_variables.append(avr_UsPu)
    algebraic_variables.append(avr_UsRefPu)
    algebraic_variables.append(avr_itPu_im)
    algebraic_variables.append(avr_itPu_re)
    algebraic_variables.append(avr_utPu_im)
    algebraic_variables.append(avr_utPu_re)
    algebraic_variables.append(avr_limPI1_limiter1_simplifiedExpr)
    algebraic_variables.append(avr_limPI1_integrator_local_reset)
    algebraic_variables.append(avr_limPI1_integrator_local_set)
    algebraic_variables.append(avr_limPI2_limiter1_simplifiedExpr)
    algebraic_variables.append(avr_limPI2_integrator_local_reset)
    algebraic_variables.append(avr_limPI2_integrator_local_set)
    algebraic_variables.append(avr_limitedFirstOrder_lim_simplifiedExpr)
    algebraic_variables.append(avr_limitedFirstOrder_I_local_reset)
    algebraic_variables.append(avr_limitedFirstOrder_I_local_set)
    algebraic_variables.append(START_avr_firstOrder_y)
    algebraic_variables.append(START_avr_firstOrder1_y)
    algebraic_variables.append(avr_potentialCircuit_v2_re)
    algebraic_variables.append(avr_potentialCircuit_v2_im)
    algebraic_variables.append(avr_potentialCircuit_v1_re)
    algebraic_variables.append(avr_potentialCircuit_v1_im)
    algebraic_variables.append(PRE_avr_limPI2_hysteresisMin_y)
    algebraic_variables.append(PRE_avr_limPI2_hysteresisMax_y)
    algebraic_variables.append(PRE_avr_limPI1_hysteresisMin_y)
    algebraic_variables.append(PRE_avr_limPI1_hysteresisMax_y)
    algebraic_variables.append(avr_sum1_u_3)
    algebraic_variables.append(avr_add_u2)
    algebraic_variables.append(avr_sum1_u_4)
    algebraic_variables.append(avr_sum1_u_5)
    algebraic_variables.append(avr_sum1_u_6)
    differential_variables: list[Var] = list()
    differential_variables.append(d_avr_firstOrder_y)
    differential_variables.append(d_avr_limPI1_integrator_y)
    differential_variables.append(d_avr_firstOrder1_y)
    differential_variables.append(d_avr_limitedFirstOrder_I_y)
    differential_variables.append(d_avr_limPI2_integrator_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[avr_Efd0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Ir0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Kc] = vf.add_const(0.0, name='')
    event_parameters[avr_Kg] = vf.add_const(1.0, name='')
    event_parameters[avr_Ki] = vf.add_const(0.0, name='')
    event_parameters[avr_Kim] = vf.add_const(10.0, name='')
    event_parameters[avr_Kir] = vf.add_const(10.0, name='')
    event_parameters[avr_Kp] = vf.add_const(1.0, name='')
    event_parameters[avr_Kpm] = vf.add_const(1.0, name='')
    event_parameters[avr_Kpr] = vf.add_const(1.0, name='')
    event_parameters[avr_Thetap] = vf.add_const(0.0, name='')
    event_parameters[avr_UOel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_USclOel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_USclUel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_UUel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_Us0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_VaMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VaMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_Vb0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_VbMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VgMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VmMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VmMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_VrMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VrMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_XlPu] = vf.add_const(0.0, name='')
    event_parameters[avr_add_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_add_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_const_k] = avr_VbMaxPu
    event_parameters[avr_const1_k] = avr_Kp
    event_parameters[avr_const2_k] = avr_VgMaxPu
    event_parameters[avr_firstOrder_T] = avr_tR
    event_parameters[avr_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_y_start] = avr_Us0Pu
    event_parameters[avr_firstOrder1_T] = avr_tG
    event_parameters[avr_firstOrder1_k] = avr_Kg
    event_parameters[avr_firstOrder1_y_start] = (avr_Kg * avr_Efd0Pu)
    event_parameters[avr_gain1_k] = avr_Kc
    event_parameters[avr_it0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[avr_it0Pu_re] = vf.add_const(0.8, name='')
    event_parameters[avr_limPI1_Ki] = avr_Kir
    event_parameters[avr_limPI1_Kp] = avr_Kpr
    event_parameters[avr_limPI1_Tol] = vf.add_const(1e-05, name='')
    event_parameters[avr_limPI1_Y0] = (avr_Kg * avr_Efd0Pu)
    event_parameters[avr_limPI1_YMax] = avr_VrMaxPu
    event_parameters[avr_limPI1_YMin] = avr_VrMinPu
    event_parameters[avr_limPI1_add_k1] = avr_limPI1_Kp
    event_parameters[avr_limPI1_add_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_limPI1_const_k] = vf.add_const(0.0, name='')
    event_parameters[avr_limPI1_hysteresisMax_uHigh] = avr_limPI1_YMax
    event_parameters[avr_limPI1_hysteresisMax_uLow] = (avr_limPI1_YMax + (avr_limPI1_Tol * (avr_limPI1_YMin - avr_limPI1_YMax)))
    event_parameters[avr_limPI1_hysteresisMin_uHigh] = (avr_limPI1_YMin + (avr_limPI1_Tol * (avr_limPI1_YMax - avr_limPI1_YMin)))
    event_parameters[avr_limPI1_hysteresisMin_uLow] = avr_limPI1_YMin
    event_parameters[avr_limPI1_integrator_k] = avr_limPI1_Ki
    event_parameters[avr_limPI1_integrator_y_start] = avr_limPI1_Y0
    event_parameters[avr_limPI1_limiter1_uMax] = avr_limPI1_YMax
    event_parameters[avr_limPI1_limiter1_uMin] = avr_limPI1_YMin
    event_parameters[avr_limPI2_Ki] = avr_Kim
    event_parameters[avr_limPI2_Kp] = avr_Kpm
    event_parameters[avr_limPI2_Tol] = vf.add_const(1e-05, name='')
    event_parameters[avr_limPI2_Y0] = (avr_Efd0Pu / avr_Vb0Pu)
    event_parameters[avr_limPI2_YMax] = avr_VmMaxPu
    event_parameters[avr_limPI2_YMin] = avr_VmMinPu
    event_parameters[avr_limPI2_add_k1] = avr_limPI2_Kp
    event_parameters[avr_limPI2_add_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_limPI2_const_k] = vf.add_const(0.0, name='')
    event_parameters[avr_limPI2_hysteresisMax_uHigh] = avr_limPI2_YMax
    event_parameters[avr_limPI2_hysteresisMax_uLow] = (avr_limPI2_YMax + (avr_limPI2_Tol * (avr_limPI2_YMin - avr_limPI2_YMax)))
    event_parameters[avr_limPI2_hysteresisMin_uHigh] = (avr_limPI2_YMin + (avr_limPI2_Tol * (avr_limPI2_YMax - avr_limPI2_YMin)))
    event_parameters[avr_limPI2_hysteresisMin_uLow] = avr_limPI2_YMin
    event_parameters[avr_limPI2_integrator_k] = avr_limPI2_Ki
    event_parameters[avr_limPI2_integrator_y_start] = avr_limPI2_Y0
    event_parameters[avr_limPI2_limiter1_uMax] = avr_limPI2_YMax
    event_parameters[avr_limPI2_limiter1_uMin] = avr_limPI2_YMin
    event_parameters[avr_limitedFirstOrder_G_k] = (sym.Const(1.0) / avr_limitedFirstOrder_tFilter)
    event_parameters[avr_limitedFirstOrder_Gk_k] = avr_limitedFirstOrder_K
    event_parameters[avr_limitedFirstOrder_I_k] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_I_y_start] = avr_limitedFirstOrder_Y0
    event_parameters[avr_limitedFirstOrder_K] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_Y0] = (avr_Efd0Pu / avr_Vb0Pu)
    event_parameters[avr_limitedFirstOrder_YMax] = avr_VaMaxPu
    event_parameters[avr_limitedFirstOrder_YMin] = avr_VaMinPu
    event_parameters[avr_limitedFirstOrder_lim_uMax] = avr_limitedFirstOrder_YMax
    event_parameters[avr_limitedFirstOrder_lim_uMin] = avr_limitedFirstOrder_YMin
    event_parameters[avr_limitedFirstOrder_tFilter] = avr_tA
    event_parameters[avr_potentialCircuit_Ki] = avr_Ki
    event_parameters[avr_potentialCircuit_Kp] = avr_Kp
    event_parameters[avr_potentialCircuit_Theta] = avr_Thetap
    event_parameters[avr_potentialCircuit_X] = avr_XlPu
    event_parameters[avr_rectifierRegulationCharacteristic_A1] = (((sym.heaviside(((avr_rectifierRegulationCharacteristic_ULow - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - avr_rectifierRegulationCharacteristic_ULow) + sym.Const(1e-06)))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.heaviside(((avr_rectifierRegulationCharacteristic_ULow - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - avr_rectifierRegulationCharacteristic_ULow) + sym.Const(1e-06))))) * ((sym.Const(1.0) - sym.sqrt((avr_rectifierRegulationCharacteristic_UHigh - (avr_rectifierRegulationCharacteristic_ULow ** sym.Const(2.0))))) / avr_rectifierRegulationCharacteristic_ULow)))
    event_parameters[avr_rectifierRegulationCharacteristic_A2] = (((sym.heaviside(((avr_rectifierRegulationCharacteristic_UHigh - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06)))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.heaviside(((avr_rectifierRegulationCharacteristic_UHigh - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06))))) * sym.sqrt((avr_rectifierRegulationCharacteristic_UHigh / (sym.Const(1.0) - avr_rectifierRegulationCharacteristic_UHigh)))))
    event_parameters[avr_rectifierRegulationCharacteristic_UHigh] = vf.add_const(0.75, name='')
    event_parameters[avr_rectifierRegulationCharacteristic_ULow] = vf.add_const(0.4330127018922193, name='')
    event_parameters[avr_sum1_k_1] = vf.add_const(-1.0, name='')
    event_parameters[avr_sum1_k_2] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_3] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_4] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_5] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_6] = vf.add_const(1.0, name='')
    event_parameters[avr_tA] = vf.add_const(0.02, name='')
    event_parameters[avr_tG] = vf.add_const(0.02, name='')
    event_parameters[avr_tR] = vf.add_const(0.02, name='')
    event_parameters[avr_ut0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[avr_ut0Pu_re] = vf.add_const(1.0, name='')
    event_parameters[avr_PositionOel] = vf.add_const(0.0, name='')
    event_parameters[avr_PositionPss] = vf.add_const(0.0, name='')
    event_parameters[avr_PositionScl] = vf.add_const(0.0, name='')
    event_parameters[avr_PositionUel] = vf.add_const(0.0, name='')
    event_parameters[avr_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder1_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_limPI1_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_limPI1_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_limPI2_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_limPI2_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_I_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_max1_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_max2_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_min1_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_min2_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_sum1_nin] = vf.add_const(6.0, name='')
    event_parameters[avr_Sw1] = vf.add_const(0.0, name='')
    event_parameters[avr_booleanConstant_k] = avr_Sw1
    event_parameters[avr_limPI1_hysteresisMax_pre_y_start] = vf.add_const(0.0, name='')
    event_parameters[avr_limPI1_hysteresisMin_pre_y_start] = vf.add_const(1.0, name='')
    event_parameters[avr_limPI1_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_limPI1_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_limPI1_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limPI1_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_limPI2_hysteresisMax_pre_y_start] = vf.add_const(0.0, name='')
    event_parameters[avr_limPI2_hysteresisMin_pre_y_start] = vf.add_const(1.0, name='')
    event_parameters[avr_limPI2_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_limPI2_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_limPI2_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limPI2_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_I_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_I_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_potentialCircuit_j_im] = vf.add_const(1.0, name='')
    event_parameters[avr_potentialCircuit_j_re] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[avr_firstOrder_y] = (avr_firstOrder_k * avr_UsPu)
    initial_equations[avr_firstOrder1_y] = avr_firstOrder1_y_start
    initial_equations[avr_limPI1_integrator_y] = avr_limPI1_integrator_y_start
    initial_equations[avr_limPI2_integrator_y] = avr_limPI2_integrator_y_start
    initial_equations[avr_limitedFirstOrder_I_y] = avr_limitedFirstOrder_I_y_start
    initial_equations[avr_EfdPu] = vf.add_const(1.0, name='')
    initial_equations[avr_IrPu] = vf.add_const(1.0, name='')
    initial_equations[avr_UOelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UPssPu] = vf.add_const(0.0, name='')
    initial_equations[avr_USclOelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_USclUelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UUelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UsPu] = vf.add_const(1.0, name='')
    initial_equations[avr_UsRefPu] = vf.add_const(1.0, name='')
    initial_equations[avr_division_y] = vf.add_const(0.0, name='')
    initial_equations[avr_itPu_im] = vf.add_const(0.0, name='')
    initial_equations[avr_itPu_re] = vf.add_const(0.8, name='')
    initial_equations[avr_limPI1_y] = avr_limPI1_Y0
    initial_equations[avr_limitedFirstOrder_y] = avr_limitedFirstOrder_Y0
    initial_equations[avr_min2_u_3] = avr_limPI2_Y0
    initial_equations[avr_switch_y] = vf.add_const(1.0, name='')
    initial_equations[avr_utPu_im] = vf.add_const(0.0, name='')
    initial_equations[avr_utPu_re] = vf.add_const(1.0, name='')
    initial_equations[avr_limPI1_hysteresisMin_y] = (sym.heaviside(((avr_limPI1_add_y - avr_limPI1_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_avr_limPI1_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((avr_limPI1_add_y - avr_limPI1_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((avr_limPI1_hysteresisMin_uLow - avr_limPI1_add_y) + sym.Const(1e-06))))))
    initial_equations[avr_limPI2_hysteresisMin_y] = (sym.heaviside(((avr_limPI2_add_y - avr_limPI2_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_avr_limPI2_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((avr_limPI2_add_y - avr_limPI2_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((avr_limPI2_hysteresisMin_uLow - avr_limPI2_add_y) + sym.Const(1e-06))))))
    initial_equations[avr_limPI1_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_limPI1_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_limPI1_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[avr_limPI2_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_limPI2_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_limPI2_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_lim_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_I_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_I_local_set] = vf.add_const(0.0, name='')
    initial_equations[avr_potentialCircuit_v2_re] = (sym.Const(0.8) * (avr_potentialCircuit_Ki + (avr_potentialCircuit_X * (avr_potentialCircuit_Kp * sym.cos(avr_potentialCircuit_Theta)))))
    initial_equations[avr_potentialCircuit_v2_im] = (sym.Const(0.8) * (avr_potentialCircuit_X * (avr_potentialCircuit_Kp * sym.sin(avr_potentialCircuit_Theta))))
    initial_equations[avr_potentialCircuit_v1_re] = (avr_potentialCircuit_Kp * sym.cos(avr_potentialCircuit_Theta))
    initial_equations[avr_potentialCircuit_v1_im] = (avr_potentialCircuit_Kp * sym.sin(avr_potentialCircuit_Theta))
    initial_equations[avr_potentialCircuit_vE] = ((((avr_potentialCircuit_v1_re - avr_potentialCircuit_v2_im) ** sym.Const(2.0)) + ((avr_potentialCircuit_v1_im + avr_potentialCircuit_v2_re) ** sym.Const(2.0))) ** sym.Const(0.5))
    initial_equations[PRE_avr_limPI2_hysteresisMin_y] = avr_limPI2_hysteresisMin_pre_y_start
    initial_equations[PRE_avr_limPI2_hysteresisMax_y] = avr_limPI2_hysteresisMax_pre_y_start
    initial_equations[PRE_avr_limPI1_hysteresisMin_y] = avr_limPI1_hysteresisMin_pre_y_start
    initial_equations[PRE_avr_limPI1_hysteresisMax_y] = avr_limPI1_hysteresisMax_pre_y_start
    initial_equations[avr_limPI1_hysteresisMax_y] = (sym.heaviside(((avr_limPI1_add_y - avr_limPI1_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_avr_limPI1_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((avr_limPI1_add_y - avr_limPI1_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((avr_limPI1_hysteresisMax_uLow - avr_limPI1_add_y) + sym.Const(1e-06))))))
    initial_equations[avr_limPI2_hysteresisMax_y] = (sym.heaviside(((avr_limPI2_add_y - avr_limPI2_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_avr_limPI2_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((avr_limPI2_add_y - avr_limPI2_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((avr_limPI2_hysteresisMax_uLow - avr_limPI2_add_y) + sym.Const(1e-06))))))
    initial_equations[avr_sum1_u_3] = vf.add_const(0.0, name='')
    initial_equations[avr_add_u2] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_u_4] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_u_5] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_u_6] = vf.add_const(0.0, name='')
    initial_equations[avr_min1_u_3] = ((((((avr_UsRefPu - avr_firstOrder_y) + avr_UOelPu) + avr_UPssPu) + avr_USclOelPu) + avr_USclUelPu) + avr_UUelPu)
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

    template.comment = 'Generator AVR/exciter IEEE ST4C'
    return template
