# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Oel5c'.

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

def build_oel5c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'Oel5c'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    oel_IBiasPu: Var = vf.add_var('oel.IBiasPu_' + template_name)
    oel_IfdLevelPu: Var = vf.add_var('oel.IfdLevelPu_' + template_name)
    oel_IfdLimPu: Var = vf.add_var('oel.IfdLimPu_' + template_name)
    oel_IfdPu: Var = vf.add_var('oel.IfdPu_' + template_name)
    oel_IfdRef1Pu: Var = vf.add_var('oel.IfdRef1Pu_' + template_name)
    oel_IfdRef2Pu: Var = vf.add_var('oel.IfdRef2Pu_' + template_name)
    oel_Input0Pu: Var = vf.add_var('oel.Input0Pu_' + template_name)
    oel_K: Var = vf.add_var('oel.K_' + template_name)
    oel_K1: Var = vf.add_var('oel.K1_' + template_name)
    oel_KIfdt: Var = vf.add_var('oel.KIfdt_' + template_name)
    oel_KScale1: Var = vf.add_var('oel.KScale1_' + template_name)
    oel_KScale2: Var = vf.add_var('oel.KScale2_' + template_name)
    oel_KiOel: Var = vf.add_var('oel.KiOel_' + template_name)
    oel_KiVfe: Var = vf.add_var('oel.KiVfe_' + template_name)
    oel_KpOel: Var = vf.add_var('oel.KpOel_' + template_name)
    oel_KpVfe: Var = vf.add_var('oel.KpVfe_' + template_name)
    oel_Sw1: Var = vf.add_var('oel.Sw1_' + template_name)
    oel_TolPI: Var = vf.add_var('oel.TolPI_' + template_name)
    oel_VOel1MaxPu: Var = vf.add_var('oel.VOel1MaxPu_' + template_name)
    oel_VOelMaxPu: Var = vf.add_var('oel.VOelMaxPu_' + template_name)
    oel_VOelMinPu: Var = vf.add_var('oel.VOelMinPu_' + template_name)
    oel_Vfe0Pu: Var = vf.add_var('oel.Vfe0Pu_' + template_name)
    oel_VfeMaxPu: Var = vf.add_var('oel.VfeMaxPu_' + template_name)
    oel_VfeMinPu: Var = vf.add_var('oel.VfeMinPu_' + template_name)
    oel_VfeRefPu: Var = vf.add_var('oel.VfeRefPu_' + template_name)
    oel_add_k1: Var = vf.add_var('oel.add.k1_' + template_name)
    oel_add_k2: Var = vf.add_var('oel.add.k2_' + template_name)
    oel_add3_k1: Var = vf.add_var('oel.add3.k1_' + template_name)
    oel_add3_k2: Var = vf.add_var('oel.add3.k2_' + template_name)
    oel_add3_k3: Var = vf.add_var('oel.add3.k3_' + template_name)
    oel_booleanConstant_k: Var = vf.add_var('oel.booleanConstant.k_' + template_name)
    oel_const_k: Var = vf.add_var('oel.const.k_' + template_name)
    oel_const1_k: Var = vf.add_var('oel.const1.k_' + template_name)
    oel_const2_k: Var = vf.add_var('oel.const2.k_' + template_name)
    oel_const3_k: Var = vf.add_var('oel.const3.k_' + template_name)
    oel_const4_k: Var = vf.add_var('oel.const4.k_' + template_name)
    oel_firstOrder_T: Var = vf.add_var('oel.firstOrder.T_' + template_name)
    oel_firstOrder_initType: Var = vf.add_var('oel.firstOrder.initType_' + template_name)
    oel_firstOrder_k: Var = vf.add_var('oel.firstOrder.k_' + template_name)
    oel_firstOrder_y_start: Var = vf.add_var('oel.firstOrder.y_start_' + template_name)
    oel_firstOrder2_T: Var = vf.add_var('oel.firstOrder2.T_' + template_name)
    oel_firstOrder2_initType: Var = vf.add_var('oel.firstOrder2.initType_' + template_name)
    oel_firstOrder2_k: Var = vf.add_var('oel.firstOrder2.k_' + template_name)
    oel_firstOrder2_y_start: Var = vf.add_var('oel.firstOrder2.y_start_' + template_name)
    oel_flipFlopS_Y0: Var = vf.add_var('oel.flipFlopS.Y0_' + template_name)
    oel_gain_k: Var = vf.add_var('oel.gain.k_' + template_name)
    oel_greaterThreshold_threshold: Var = vf.add_var('oel.greaterThreshold.threshold_' + template_name)
    oel_greaterThreshold1_threshold: Var = vf.add_var('oel.greaterThreshold1.threshold_' + template_name)
    oel_greaterThreshold2_threshold: Var = vf.add_var('oel.greaterThreshold2.threshold_' + template_name)
    oel_lessEqualThreshold_threshold: Var = vf.add_var('oel.lessEqualThreshold.threshold_' + template_name)
    oel_limIntegrator_initType: Var = vf.add_var('oel.limIntegrator.initType_' + template_name)
    oel_limIntegrator_k: Var = vf.add_var('oel.limIntegrator.k_' + template_name)
    oel_limIntegrator_limitsAtInit: Var = vf.add_var('oel.limIntegrator.limitsAtInit_' + template_name)
    oel_limIntegrator_outMax: Var = vf.add_var('oel.limIntegrator.outMax_' + template_name)
    oel_limIntegrator_outMin: Var = vf.add_var('oel.limIntegrator.outMin_' + template_name)
    oel_limIntegrator_strict: Var = vf.add_var('oel.limIntegrator.strict_' + template_name)
    oel_limIntegrator_use_reset: Var = vf.add_var('oel.limIntegrator.use_reset_' + template_name)
    oel_limIntegrator_use_set: Var = vf.add_var('oel.limIntegrator.use_set_' + template_name)
    oel_limIntegrator_y_start: Var = vf.add_var('oel.limIntegrator.y_start_' + template_name)
    oel_limitedPI_Ki: Var = vf.add_var('oel.limitedPI.Ki_' + template_name)
    oel_limitedPI_Kp: Var = vf.add_var('oel.limitedPI.Kp_' + template_name)
    oel_limitedPI_Tol: Var = vf.add_var('oel.limitedPI.Tol_' + template_name)
    oel_limitedPI_Y0: Var = vf.add_var('oel.limitedPI.Y0_' + template_name)
    oel_limitedPI_YMax: Var = vf.add_var('oel.limitedPI.YMax_' + template_name)
    oel_limitedPI_YMin: Var = vf.add_var('oel.limitedPI.YMin_' + template_name)
    oel_limitedPI_add_k1: Var = vf.add_var('oel.limitedPI.add.k1_' + template_name)
    oel_limitedPI_add_k2: Var = vf.add_var('oel.limitedPI.add.k2_' + template_name)
    oel_limitedPI_const_k: Var = vf.add_var('oel.limitedPI.const.k_' + template_name)
    oel_limitedPI_hysteresisMax_pre_y_start: Var = vf.add_var('oel.limitedPI.hysteresisMax.pre_y_start_' + template_name)
    oel_limitedPI_hysteresisMax_uHigh: Var = vf.add_var('oel.limitedPI.hysteresisMax.uHigh_' + template_name)
    oel_limitedPI_hysteresisMax_uLow: Var = vf.add_var('oel.limitedPI.hysteresisMax.uLow_' + template_name)
    oel_limitedPI_hysteresisMin_pre_y_start: Var = vf.add_var('oel.limitedPI.hysteresisMin.pre_y_start_' + template_name)
    oel_limitedPI_hysteresisMin_uHigh: Var = vf.add_var('oel.limitedPI.hysteresisMin.uHigh_' + template_name)
    oel_limitedPI_hysteresisMin_uLow: Var = vf.add_var('oel.limitedPI.hysteresisMin.uLow_' + template_name)
    oel_limitedPI_integrator_initType: Var = vf.add_var('oel.limitedPI.integrator.initType_' + template_name)
    oel_limitedPI_integrator_k: Var = vf.add_var('oel.limitedPI.integrator.k_' + template_name)
    oel_limitedPI_integrator_use_reset: Var = vf.add_var('oel.limitedPI.integrator.use_reset_' + template_name)
    oel_limitedPI_integrator_use_set: Var = vf.add_var('oel.limitedPI.integrator.use_set_' + template_name)
    oel_limitedPI_integrator_y_start: Var = vf.add_var('oel.limitedPI.integrator.y_start_' + template_name)
    oel_limitedPI_limiter1_homotopyType: Var = vf.add_var('oel.limitedPI.limiter1.homotopyType_' + template_name)
    oel_limitedPI_limiter1_limitsAtInit: Var = vf.add_var('oel.limitedPI.limiter1.limitsAtInit_' + template_name)
    oel_limitedPI_limiter1_strict: Var = vf.add_var('oel.limitedPI.limiter1.strict_' + template_name)
    oel_limitedPI_limiter1_uMax: Var = vf.add_var('oel.limitedPI.limiter1.uMax_' + template_name)
    oel_limitedPI_limiter1_uMin: Var = vf.add_var('oel.limitedPI.limiter1.uMin_' + template_name)
    oel_limitedPI1_Ki: Var = vf.add_var('oel.limitedPI1.Ki_' + template_name)
    oel_limitedPI1_Kp: Var = vf.add_var('oel.limitedPI1.Kp_' + template_name)
    oel_limitedPI1_Tol: Var = vf.add_var('oel.limitedPI1.Tol_' + template_name)
    oel_limitedPI1_Y0: Var = vf.add_var('oel.limitedPI1.Y0_' + template_name)
    oel_limitedPI1_YMax: Var = vf.add_var('oel.limitedPI1.YMax_' + template_name)
    oel_limitedPI1_YMin: Var = vf.add_var('oel.limitedPI1.YMin_' + template_name)
    oel_limitedPI1_add_k1: Var = vf.add_var('oel.limitedPI1.add.k1_' + template_name)
    oel_limitedPI1_add_k2: Var = vf.add_var('oel.limitedPI1.add.k2_' + template_name)
    oel_limitedPI1_const_k: Var = vf.add_var('oel.limitedPI1.const.k_' + template_name)
    oel_limitedPI1_hysteresisMax_pre_y_start: Var = vf.add_var('oel.limitedPI1.hysteresisMax.pre_y_start_' + template_name)
    oel_limitedPI1_hysteresisMax_uHigh: Var = vf.add_var('oel.limitedPI1.hysteresisMax.uHigh_' + template_name)
    oel_limitedPI1_hysteresisMax_uLow: Var = vf.add_var('oel.limitedPI1.hysteresisMax.uLow_' + template_name)
    oel_limitedPI1_hysteresisMin_pre_y_start: Var = vf.add_var('oel.limitedPI1.hysteresisMin.pre_y_start_' + template_name)
    oel_limitedPI1_hysteresisMin_uHigh: Var = vf.add_var('oel.limitedPI1.hysteresisMin.uHigh_' + template_name)
    oel_limitedPI1_hysteresisMin_uLow: Var = vf.add_var('oel.limitedPI1.hysteresisMin.uLow_' + template_name)
    oel_limitedPI1_integrator_initType: Var = vf.add_var('oel.limitedPI1.integrator.initType_' + template_name)
    oel_limitedPI1_integrator_k: Var = vf.add_var('oel.limitedPI1.integrator.k_' + template_name)
    oel_limitedPI1_integrator_use_reset: Var = vf.add_var('oel.limitedPI1.integrator.use_reset_' + template_name)
    oel_limitedPI1_integrator_use_set: Var = vf.add_var('oel.limitedPI1.integrator.use_set_' + template_name)
    oel_limitedPI1_integrator_y_start: Var = vf.add_var('oel.limitedPI1.integrator.y_start_' + template_name)
    oel_limitedPI1_limiter1_homotopyType: Var = vf.add_var('oel.limitedPI1.limiter1.homotopyType_' + template_name)
    oel_limitedPI1_limiter1_limitsAtInit: Var = vf.add_var('oel.limitedPI1.limiter1.limitsAtInit_' + template_name)
    oel_limitedPI1_limiter1_strict: Var = vf.add_var('oel.limitedPI1.limiter1.strict_' + template_name)
    oel_limitedPI1_limiter1_uMax: Var = vf.add_var('oel.limitedPI1.limiter1.uMax_' + template_name)
    oel_limitedPI1_limiter1_uMin: Var = vf.add_var('oel.limitedPI1.limiter1.uMin_' + template_name)
    oel_power1_N: Var = vf.add_var('oel.power1.N_' + template_name)
    oel_power1_NInteger: Var = vf.add_var('oel.power1.NInteger_' + template_name)
    oel_tBOel: Var = vf.add_var('oel.tBOel_' + template_name)
    oel_tCOel: Var = vf.add_var('oel.tCOel_' + template_name)
    oel_tF1: Var = vf.add_var('oel.tF1_' + template_name)
    oel_tF2: Var = vf.add_var('oel.tF2_' + template_name)
    oel_tIfdLevel: Var = vf.add_var('oel.tIfdLevel_' + template_name)
    oel_tOel: Var = vf.add_var('oel.tOel_' + template_name)
    oel_transferFunction_a_1: Var = vf.add_var('oel.transferFunction.a[1]_' + template_name)
    oel_transferFunction_a_2: Var = vf.add_var('oel.transferFunction.a[2]_' + template_name)
    oel_transferFunction_a_end: Var = vf.add_var('oel.transferFunction.a_end_' + template_name)
    oel_transferFunction_a_one: Var = vf.add_var('oel.transferFunction.a_one_' + template_name)
    oel_transferFunction_b_1: Var = vf.add_var('oel.transferFunction.b[1]_' + template_name)
    oel_transferFunction_b_2: Var = vf.add_var('oel.transferFunction.b[2]_' + template_name)
    oel_transferFunction_bb_1: Var = vf.add_var('oel.transferFunction.bb[1]_' + template_name)
    oel_transferFunction_bb_2: Var = vf.add_var('oel.transferFunction.bb[2]_' + template_name)
    oel_transferFunction_d: Var = vf.add_var('oel.transferFunction.d_' + template_name)
    oel_transferFunction_na: Var = vf.add_var('oel.transferFunction.na_' + template_name)
    oel_transferFunction_nb: Var = vf.add_var('oel.transferFunction.nb_' + template_name)
    oel_transferFunction_nx: Var = vf.add_var('oel.transferFunction.nx_' + template_name)
    oel_transferFunction_x_start_1: Var = vf.add_var('oel.transferFunction.x_start[1]_' + template_name)
    oel_transferFunction_y_start: Var = vf.add_var('oel.transferFunction.y_start_' + template_name)
    # Declare the state variables used by the template.
    oel_firstOrder_y: Var = vf.add_var('oel.firstOrder.y_' + template_name)
    oel_firstOrder2_y: Var = vf.add_var('oel.firstOrder2.y_' + template_name)
    oel_limIntegrator_y: Var = vf.add_var('oel.limIntegrator.y_' + template_name)
    oel_limitedPI_integrator_y: Var = vf.add_var('oel.limitedPI.integrator.y_' + template_name)
    oel_limitedPI1_integrator_y: Var = vf.add_var('oel.limitedPI1.integrator.y_' + template_name)
    oel_transferFunction_x_scaled_1: Var = vf.add_var('oel.transferFunction.x_scaled[1]_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_oel_flipFlopS_y: Var = vf.add_var('$PRE.oel.flipFlopS.y_' + template_name)
    PRE_oel_limitedPI_hysteresisMax_y: Var = vf.add_var('$PRE.oel.limitedPI.hysteresisMax.y_' + template_name)
    PRE_oel_limitedPI_hysteresisMin_y: Var = vf.add_var('$PRE.oel.limitedPI.hysteresisMin.y_' + template_name)
    PRE_oel_limitedPI1_hysteresisMax_y: Var = vf.add_var('$PRE.oel.limitedPI1.hysteresisMax.y_' + template_name)
    PRE_oel_limitedPI1_hysteresisMin_y: Var = vf.add_var('$PRE.oel.limitedPI1.hysteresisMin.y_' + template_name)
    PRE_oel_timer_entryTime: Var = vf.add_var('$PRE.oel.timer.entryTime_' + template_name)
    START_oel_firstOrder_y: Var = vf.add_var('$START.oel.firstOrder.y_' + template_name)
    START_oel_firstOrder2_y: Var = vf.add_var('$START.oel.firstOrder2.y_' + template_name)
    START_oel_flipFlopS_y: Var = vf.add_var('$START.oel.flipFlopS.y_' + template_name)
    START_oel_transferFunction_x_scaled_1: Var = vf.add_var('$START.oel.transferFunction.x_scaled[1]_' + template_name)
    whenCondition1: Var = vf.add_var('$whenCondition1_' + template_name)
    whenCondition2: Var = vf.add_var('$whenCondition2_' + template_name)
    whenCondition3: Var = vf.add_var('$whenCondition3_' + template_name)
    oel_UOelPu: Var = vf.add_var('oel.UOelPu_' + template_name)
    oel_VfePu: Var = vf.add_var('oel.VfePu_' + template_name)
    oel_add_y: Var = vf.add_var('oel.add.y_' + template_name)
    oel_add3_y: Var = vf.add_var('oel.add3.y_' + template_name)
    oel_feedback3_y: Var = vf.add_var('oel.feedback3.y_' + template_name)
    oel_flipFlopS_y: Var = vf.add_var('oel.flipFlopS.y_' + template_name)
    oel_gain_y: Var = vf.add_var('oel.gain.y_' + template_name)
    oel_greaterThreshold_y: Var = vf.add_var('oel.greaterThreshold.y_' + template_name)
    oel_greaterThreshold1_y: Var = vf.add_var('oel.greaterThreshold1.y_' + template_name)
    oel_greaterThreshold2_y: Var = vf.add_var('oel.greaterThreshold2.y_' + template_name)
    oel_inputPu: Var = vf.add_var('oel.inputPu_' + template_name)
    oel_lessEqualThreshold_y: Var = vf.add_var('oel.lessEqualThreshold.y_' + template_name)
    oel_limIntegrator_local_reset: Var = vf.add_var('oel.limIntegrator.local_reset_' + template_name)
    oel_limIntegrator_local_set: Var = vf.add_var('oel.limIntegrator.local_set_' + template_name)
    oel_limitedPI_add_y: Var = vf.add_var('oel.limitedPI.add.y_' + template_name)
    oel_limitedPI_hysteresisMax_y: Var = vf.add_var('oel.limitedPI.hysteresisMax.y_' + template_name)
    oel_limitedPI_hysteresisMin_y: Var = vf.add_var('oel.limitedPI.hysteresisMin.y_' + template_name)
    oel_limitedPI_integrator_local_reset: Var = vf.add_var('oel.limitedPI.integrator.local_reset_' + template_name)
    oel_limitedPI_integrator_local_set: Var = vf.add_var('oel.limitedPI.integrator.local_set_' + template_name)
    oel_limitedPI_limiter1_simplifiedExpr: Var = vf.add_var('oel.limitedPI.limiter1.simplifiedExpr_' + template_name)
    oel_limitedPI_switch1_u2: Var = vf.add_var('oel.limitedPI.switch1.u2_' + template_name)
    oel_limitedPI_switch1_y: Var = vf.add_var('oel.limitedPI.switch1.y_' + template_name)
    oel_limitedPI_y: Var = vf.add_var('oel.limitedPI.y_' + template_name)
    oel_limitedPI1_add_y: Var = vf.add_var('oel.limitedPI1.add.y_' + template_name)
    oel_limitedPI1_hysteresisMax_y: Var = vf.add_var('oel.limitedPI1.hysteresisMax.y_' + template_name)
    oel_limitedPI1_hysteresisMin_y: Var = vf.add_var('oel.limitedPI1.hysteresisMin.y_' + template_name)
    oel_limitedPI1_integrator_local_reset: Var = vf.add_var('oel.limitedPI1.integrator.local_reset_' + template_name)
    oel_limitedPI1_integrator_local_set: Var = vf.add_var('oel.limitedPI1.integrator.local_set_' + template_name)
    oel_limitedPI1_limiter1_simplifiedExpr: Var = vf.add_var('oel.limitedPI1.limiter1.simplifiedExpr_' + template_name)
    oel_limitedPI1_switch1_u2: Var = vf.add_var('oel.limitedPI1.switch1.u2_' + template_name)
    oel_limitedPI1_switch1_y: Var = vf.add_var('oel.limitedPI1.switch1.y_' + template_name)
    oel_limitedPI1_y: Var = vf.add_var('oel.limitedPI1.y_' + template_name)
    oel_or1_y: Var = vf.add_var('oel.or1.y_' + template_name)
    oel_power1_y: Var = vf.add_var('oel.power1.y_' + template_name)
    oel_switch_y: Var = vf.add_var('oel.switch.y_' + template_name)
    oel_switch2_y: Var = vf.add_var('oel.switch2.y_' + template_name)
    oel_timer_entryTime: Var = vf.add_var('oel.timer.entryTime_' + template_name)
    oel_timer_y: Var = vf.add_var('oel.timer.y_' + template_name)
    oel_transferFunction_x_1: Var = vf.add_var('oel.transferFunction.x[1]_' + template_name)
    oel_transferFunction_y: Var = vf.add_var('oel.transferFunction.y_' + template_name)
    time: Var = vf.add_var('time_' + template_name)
    # Declare the differential variables used by the template.
    d_oel_firstOrder_y: Var = vf.add_diff_var('d_oel.firstOrder.y_' + template_name, base_var=oel_firstOrder_y)
    d_oel_firstOrder2_y: Var = vf.add_diff_var('d_oel.firstOrder2.y_' + template_name, base_var=oel_firstOrder2_y)
    d_oel_limIntegrator_y: Var = vf.add_diff_var('d_oel.limIntegrator.y_' + template_name, base_var=oel_limIntegrator_y)
    d_oel_limitedPI_integrator_y: Var = vf.add_diff_var('d_oel.limitedPI.integrator.y_' + template_name, base_var=oel_limitedPI_integrator_y)
    d_oel_limitedPI1_integrator_y: Var = vf.add_diff_var('d_oel.limitedPI1.integrator.y_' + template_name, base_var=oel_limitedPI1_integrator_y)
    d_oel_transferFunction_x_scaled_1: Var = vf.add_diff_var('d_oel.transferFunction.x_scaled[1]_' + template_name, base_var=oel_transferFunction_x_scaled_1)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((oel_limitedPI1_integrator_k * oel_limitedPI1_switch1_y))
    state_equations.append((((oel_transferFunction_a_end * oel_firstOrder_y) - oel_transferFunction_x_scaled_1) / oel_transferFunction_a_one))
    state_equations.append((((oel_firstOrder2_k * oel_VfePu) - oel_firstOrder2_y) / oel_firstOrder2_T))
    state_equations.append((oel_limitedPI_integrator_k * oel_limitedPI_switch1_y))
    state_equations.append((((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_add3_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_add3_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_add3_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((oel_limIntegrator_k * oel_add3_y) - sym.Const(0.0)) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_add3_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_add3_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_add3_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((oel_limIntegrator_k * oel_add3_y) - sym.Const(0.0)) - sym.Const(1e-06)))))))) * (oel_limIntegrator_k * oel_add3_y))))
    state_equations.append((((oel_firstOrder_k * oel_Input0Pu) - oel_firstOrder_y) / oel_firstOrder_T))
    state_variables: list[Var] = list()
    state_variables.append(oel_limitedPI1_integrator_y)
    state_variables.append(oel_transferFunction_x_scaled_1)
    state_variables.append(oel_firstOrder2_y)
    state_variables.append(oel_limitedPI_integrator_y)
    state_variables.append(oel_limIntegrator_y)
    state_variables.append(oel_firstOrder_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((whenCondition3 - sym.heaviside(((oel_firstOrder_y - oel_greaterThreshold1_threshold) - sym.Const(1e-06)))))
    algebraic_equations.append((oel_timer_y - ((whenCondition3 * (time - oel_timer_entryTime)) + ((sym.Const(1.0) - whenCondition3) * sym.Const(0.0)))))
    algebraic_equations.append((oel_greaterThreshold2_y - sym.heaviside(((oel_timer_y - oel_greaterThreshold2_threshold) - sym.Const(1e-06)))))
    algebraic_equations.append((oel_greaterThreshold1_y - whenCondition3))
    algebraic_equations.append((oel_lessEqualThreshold_y - sym.heaviside(((oel_lessEqualThreshold_threshold - oel_limIntegrator_y) + sym.Const(1e-06)))))
    algebraic_equations.append((whenCondition1 - sym.heaviside(((oel_limIntegrator_y - oel_greaterThreshold_threshold) - sym.Const(1e-06)))))
    algebraic_equations.append((whenCondition2 - (oel_lessEqualThreshold_y * (sym.Const(1.0) - whenCondition1))))
    algebraic_equations.append((oel_switch2_y - ((oel_flipFlopS_y * oel_const3_k) + ((sym.Const(1.0) - oel_flipFlopS_y) * oel_const4_k))))
    algebraic_equations.append((oel_or1_y - (sym.Const(1.0) - ((sym.Const(1.0) - oel_greaterThreshold2_y) * (sym.Const(1.0) - oel_flipFlopS_y)))))
    algebraic_equations.append((oel_greaterThreshold_y - whenCondition1))
    algebraic_equations.append((oel_gain_y - (oel_gain_k * oel_limIntegrator_y)))
    algebraic_equations.append((oel_transferFunction_x_1 - (oel_transferFunction_x_scaled_1 / oel_transferFunction_a_end)))
    algebraic_equations.append((oel_transferFunction_y - (((oel_transferFunction_bb_2 - oel_transferFunction_d) * oel_transferFunction_x_1) + (oel_transferFunction_d * oel_firstOrder_y))))
    algebraic_equations.append((oel_add_y - ((oel_add_k1 * oel_switch2_y) + (oel_add_k2 * oel_transferFunction_y))))
    algebraic_equations.append((oel_limitedPI1_add_y - ((oel_limitedPI1_add_k1 * oel_add_y) + (oel_limitedPI1_add_k2 * oel_limitedPI1_integrator_y))))
    algebraic_equations.append((oel_limitedPI1_hysteresisMin_y - (sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI1_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_hysteresisMin_uLow - oel_limitedPI1_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((oel_limitedPI1_hysteresisMax_y - (sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI1_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_hysteresisMax_uLow - oel_limitedPI1_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((oel_limitedPI1_switch1_u2 - (sym.Const(1.0) - ((sym.Const(1.0) - oel_limitedPI1_hysteresisMax_y) * (sym.Const(1.0) - (sym.Const(1.0) - oel_limitedPI1_hysteresisMin_y))))))
    algebraic_equations.append((oel_limitedPI1_y - ((sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_limiter1_uMax) - sym.Const(1e-06))) * oel_limitedPI1_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((oel_limitedPI1_limiter1_uMin - oel_limitedPI1_add_y) - sym.Const(1e-06))) * oel_limitedPI1_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_limiter1_uMin - oel_limitedPI1_add_y) - sym.Const(1e-06)))) * oel_limitedPI1_add_y))))))
    algebraic_equations.append((oel_limitedPI1_switch1_y - ((oel_limitedPI1_switch1_u2 * oel_limitedPI1_const_k) + ((sym.Const(1.0) - oel_limitedPI1_switch1_u2) * oel_add_y))))
    algebraic_equations.append((oel_feedback3_y - (oel_const_k - oel_firstOrder2_y)))
    algebraic_equations.append((oel_limitedPI_add_y - ((oel_limitedPI_add_k1 * oel_feedback3_y) + (oel_limitedPI_add_k2 * oel_limitedPI_integrator_y))))
    algebraic_equations.append((oel_limitedPI_y - ((sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_limiter1_uMax) - sym.Const(1e-06))) * oel_limitedPI_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((oel_limitedPI_limiter1_uMin - oel_limitedPI_add_y) - sym.Const(1e-06))) * oel_limitedPI_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((oel_limitedPI_limiter1_uMin - oel_limitedPI_add_y) - sym.Const(1e-06)))) * oel_limitedPI_add_y))))))
    algebraic_equations.append((oel_switch_y - ((oel_booleanConstant_k * oel_const1_k) + ((sym.Const(1.0) - oel_booleanConstant_k) * oel_limitedPI_y))))
    algebraic_equations.append((oel_UOelPu - ((oel_or1_y * oel_limitedPI1_y) + ((sym.Const(1.0) - oel_or1_y) * oel_switch_y))))
    algebraic_equations.append((oel_limitedPI_hysteresisMax_y - (sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_hysteresisMax_uLow - oel_limitedPI_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((oel_limitedPI_hysteresisMin_y - (sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_hysteresisMin_uLow - oel_limitedPI_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((oel_limitedPI_switch1_u2 - (sym.Const(1.0) - ((sym.Const(1.0) - oel_limitedPI_hysteresisMax_y) * (sym.Const(1.0) - (sym.Const(1.0) - oel_limitedPI_hysteresisMin_y))))))
    algebraic_equations.append((oel_limitedPI_switch1_y - ((oel_limitedPI_switch1_u2 * oel_limitedPI_const_k) + ((sym.Const(1.0) - oel_limitedPI_switch1_u2) * oel_feedback3_y))))
    algebraic_equations.append((oel_power1_y - (oel_firstOrder_y ** oel_power1_N)))
    algebraic_equations.append((oel_add3_y - ((oel_add3_k1 * oel_gain_y) + ((oel_add3_k2 * oel_power1_y) + (oel_add3_k3 * oel_const2_k)))))
    algebraic_equations.append((oel_flipFlopS_y - (whenCondition1 + (PRE_oel_flipFlopS_y * (sym.Const(1.0) - whenCondition1) * (sym.Const(1.0) - whenCondition2)))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(whenCondition3)
    algebraic_variables.append(oel_timer_y)
    algebraic_variables.append(oel_greaterThreshold2_y)
    algebraic_variables.append(oel_greaterThreshold1_y)
    algebraic_variables.append(oel_lessEqualThreshold_y)
    algebraic_variables.append(whenCondition1)
    algebraic_variables.append(whenCondition2)
    algebraic_variables.append(oel_switch2_y)
    algebraic_variables.append(oel_or1_y)
    algebraic_variables.append(oel_greaterThreshold_y)
    algebraic_variables.append(oel_gain_y)
    algebraic_variables.append(oel_transferFunction_x_1)
    algebraic_variables.append(oel_transferFunction_y)
    algebraic_variables.append(oel_add_y)
    algebraic_variables.append(oel_limitedPI1_add_y)
    algebraic_variables.append(oel_limitedPI1_hysteresisMin_y)
    algebraic_variables.append(oel_limitedPI1_hysteresisMax_y)
    algebraic_variables.append(oel_limitedPI1_switch1_u2)
    algebraic_variables.append(oel_limitedPI1_y)
    algebraic_variables.append(oel_limitedPI1_switch1_y)
    algebraic_variables.append(oel_feedback3_y)
    algebraic_variables.append(oel_limitedPI_add_y)
    algebraic_variables.append(oel_limitedPI_y)
    algebraic_variables.append(oel_switch_y)
    algebraic_variables.append(oel_UOelPu)
    algebraic_variables.append(oel_limitedPI_hysteresisMax_y)
    algebraic_variables.append(oel_limitedPI_hysteresisMin_y)
    algebraic_variables.append(oel_limitedPI_switch1_u2)
    algebraic_variables.append(oel_limitedPI_switch1_y)
    algebraic_variables.append(oel_power1_y)
    algebraic_variables.append(oel_add3_y)
    algebraic_variables.append(oel_flipFlopS_y)
    algebraic_variables.append(oel_timer_entryTime)
    algebraic_variables.append(oel_VfePu)
    algebraic_variables.append(oel_inputPu)
    algebraic_variables.append(oel_limIntegrator_local_reset)
    algebraic_variables.append(oel_limIntegrator_local_set)
    algebraic_variables.append(oel_limitedPI_limiter1_simplifiedExpr)
    algebraic_variables.append(oel_limitedPI_integrator_local_reset)
    algebraic_variables.append(oel_limitedPI_integrator_local_set)
    algebraic_variables.append(oel_limitedPI1_limiter1_simplifiedExpr)
    algebraic_variables.append(oel_limitedPI1_integrator_local_reset)
    algebraic_variables.append(oel_limitedPI1_integrator_local_set)
    algebraic_variables.append(START_oel_firstOrder_y)
    algebraic_variables.append(START_oel_firstOrder2_y)
    algebraic_variables.append(START_oel_transferFunction_x_scaled_1)
    algebraic_variables.append(PRE_oel_flipFlopS_y)
    algebraic_variables.append(START_oel_flipFlopS_y)
    algebraic_variables.append(PRE_oel_limitedPI1_hysteresisMin_y)
    algebraic_variables.append(PRE_oel_limitedPI1_hysteresisMax_y)
    algebraic_variables.append(PRE_oel_timer_entryTime)
    algebraic_variables.append(PRE_oel_limitedPI_hysteresisMin_y)
    algebraic_variables.append(PRE_oel_limitedPI_hysteresisMax_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_oel_limitedPI1_integrator_y)
    differential_variables.append(d_oel_transferFunction_x_scaled_1)
    differential_variables.append(d_oel_firstOrder2_y)
    differential_variables.append(d_oel_limitedPI_integrator_y)
    differential_variables.append(d_oel_limIntegrator_y)
    differential_variables.append(d_oel_firstOrder_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[oel_IBiasPu] = vf.add_const(0.0, name='')
    event_parameters[oel_IfdLevelPu] = vf.add_const(1.1, name='')
    event_parameters[oel_IfdLimPu] = vf.add_const(1.2, name='')
    event_parameters[oel_IfdPu] = vf.add_const(1.1, name='')
    event_parameters[oel_IfdRef1Pu] = vf.add_const(1.0, name='')
    event_parameters[oel_IfdRef2Pu] = vf.add_const(1.2, name='')
    event_parameters[oel_Input0Pu] = vf.add_const(1.0, name='')
    event_parameters[oel_K] = vf.add_const(1.0, name='')
    event_parameters[oel_K1] = vf.add_const(1.0, name='')
    event_parameters[oel_KIfdt] = vf.add_const(1.0, name='')
    event_parameters[oel_KScale1] = vf.add_const(1.0, name='')
    event_parameters[oel_KScale2] = vf.add_const(1.0, name='')
    event_parameters[oel_KiOel] = vf.add_const(1.0, name='')
    event_parameters[oel_KiVfe] = vf.add_const(1.0, name='')
    event_parameters[oel_KpOel] = vf.add_const(1.0, name='')
    event_parameters[oel_KpVfe] = vf.add_const(1.0, name='')
    event_parameters[oel_TolPI] = vf.add_const(1e-06, name='')
    event_parameters[oel_VOel1MaxPu] = vf.add_const(1.0, name='')
    event_parameters[oel_VOelMaxPu] = vf.add_const(1.0, name='')
    event_parameters[oel_VOelMinPu] = vf.add_const(-1.0, name='')
    event_parameters[oel_Vfe0Pu] = vf.add_const(0.0, name='')
    event_parameters[oel_VfeMaxPu] = vf.add_const(1.0, name='')
    event_parameters[oel_VfeMinPu] = vf.add_const(-1.0, name='')
    event_parameters[oel_VfeRefPu] = vf.add_const(0.0, name='')
    event_parameters[oel_add_k1] = vf.add_const(1.0, name='')
    event_parameters[oel_add_k2] = (-oel_K)
    event_parameters[oel_add3_k1] = vf.add_const(-1.0, name='')
    event_parameters[oel_add3_k2] = vf.add_const(1.0, name='')
    event_parameters[oel_add3_k3] = vf.add_const(-1.0, name='')
    event_parameters[oel_const_k] = oel_VfeRefPu
    event_parameters[oel_const1_k] = oel_IBiasPu
    event_parameters[oel_const2_k] = oel_IfdPu
    event_parameters[oel_const3_k] = oel_IfdRef2Pu
    event_parameters[oel_const4_k] = oel_IfdRef1Pu
    event_parameters[oel_firstOrder_T] = oel_tF1
    event_parameters[oel_firstOrder_k] = oel_KScale1
    event_parameters[oel_firstOrder_y_start] = (oel_KScale1 * oel_Input0Pu)
    event_parameters[oel_firstOrder2_T] = oel_tF2
    event_parameters[oel_firstOrder2_k] = oel_KScale2
    event_parameters[oel_firstOrder2_y_start] = (oel_KScale2 * oel_Vfe0Pu)
    event_parameters[oel_gain_k] = oel_KIfdt
    event_parameters[oel_greaterThreshold_threshold] = oel_IfdLimPu
    event_parameters[oel_greaterThreshold1_threshold] = oel_IfdLevelPu
    event_parameters[oel_greaterThreshold2_threshold] = oel_tIfdLevel
    event_parameters[oel_lessEqualThreshold_threshold] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_k] = (sym.Const(1.0) / oel_tOel)
    event_parameters[oel_limIntegrator_outMax] = oel_VOel1MaxPu
    event_parameters[oel_limIntegrator_outMin] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_y_start] = ((((oel_KScale1 * oel_Input0Pu) ** oel_K1) - oel_IfdPu) / oel_KIfdt)
    event_parameters[oel_limitedPI_Ki] = oel_KiVfe
    event_parameters[oel_limitedPI_Kp] = oel_KpVfe
    event_parameters[oel_limitedPI_Tol] = vf.add_const(1e-05, name='')
    event_parameters[oel_limitedPI_Y0] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_YMax] = oel_VfeMaxPu
    event_parameters[oel_limitedPI_YMin] = oel_VfeMinPu
    event_parameters[oel_limitedPI_add_k1] = oel_limitedPI_Kp
    event_parameters[oel_limitedPI_add_k2] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI_const_k] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_hysteresisMax_uHigh] = oel_limitedPI_YMax
    event_parameters[oel_limitedPI_hysteresisMax_uLow] = (oel_limitedPI_YMax + (oel_limitedPI_Tol * (oel_limitedPI_YMin - oel_limitedPI_YMax)))
    event_parameters[oel_limitedPI_hysteresisMin_uHigh] = (oel_limitedPI_YMin + (oel_limitedPI_Tol * (oel_limitedPI_YMax - oel_limitedPI_YMin)))
    event_parameters[oel_limitedPI_hysteresisMin_uLow] = oel_limitedPI_YMin
    event_parameters[oel_limitedPI_integrator_k] = oel_limitedPI_Ki
    event_parameters[oel_limitedPI_integrator_y_start] = oel_limitedPI_Y0
    event_parameters[oel_limitedPI_limiter1_uMax] = oel_limitedPI_YMax
    event_parameters[oel_limitedPI_limiter1_uMin] = oel_limitedPI_YMin
    event_parameters[oel_limitedPI1_Ki] = oel_KiOel
    event_parameters[oel_limitedPI1_Kp] = oel_KpOel
    event_parameters[oel_limitedPI1_Tol] = oel_TolPI
    event_parameters[oel_limitedPI1_Y0] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI1_YMax] = oel_VOelMaxPu
    event_parameters[oel_limitedPI1_YMin] = oel_VOelMinPu
    event_parameters[oel_limitedPI1_add_k1] = oel_limitedPI1_Kp
    event_parameters[oel_limitedPI1_add_k2] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI1_const_k] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI1_hysteresisMax_uHigh] = oel_limitedPI1_YMax
    event_parameters[oel_limitedPI1_hysteresisMax_uLow] = (oel_limitedPI1_YMax + (oel_limitedPI1_Tol * (oel_limitedPI1_YMin - oel_limitedPI1_YMax)))
    event_parameters[oel_limitedPI1_hysteresisMin_uHigh] = (oel_limitedPI1_YMin + (oel_limitedPI1_Tol * (oel_limitedPI1_YMax - oel_limitedPI1_YMin)))
    event_parameters[oel_limitedPI1_hysteresisMin_uLow] = oel_limitedPI1_YMin
    event_parameters[oel_limitedPI1_integrator_k] = oel_limitedPI1_Ki
    event_parameters[oel_limitedPI1_integrator_y_start] = oel_limitedPI1_Y0
    event_parameters[oel_limitedPI1_limiter1_uMax] = oel_limitedPI1_YMax
    event_parameters[oel_limitedPI1_limiter1_uMin] = oel_limitedPI1_YMin
    event_parameters[oel_power1_N] = oel_K1
    event_parameters[oel_tBOel] = vf.add_const(1.0, name='')
    event_parameters[oel_tCOel] = vf.add_const(1.0, name='')
    event_parameters[oel_tF1] = vf.add_const(0.02, name='')
    event_parameters[oel_tF2] = vf.add_const(0.02, name='')
    event_parameters[oel_tIfdLevel] = vf.add_const(0.0, name='')
    event_parameters[oel_tOel] = vf.add_const(1.0, name='')
    event_parameters[oel_transferFunction_a_1] = vf.add_const(1.0, name='')
    event_parameters[oel_transferFunction_a_2] = vf.add_const(1.0, name='')
    event_parameters[oel_transferFunction_a_end] = vf.add_const(1.0, name='')
    event_parameters[oel_transferFunction_a_one] = vf.add_const(1.0, name='')
    event_parameters[oel_transferFunction_b_1] = oel_tCOel
    event_parameters[oel_transferFunction_b_2] = vf.add_const(1.0, name='')
    event_parameters[oel_transferFunction_bb_1] = oel_transferFunction_b_1
    event_parameters[oel_transferFunction_bb_2] = oel_transferFunction_b_2
    event_parameters[oel_transferFunction_d] = (oel_transferFunction_bb_1 / oel_transferFunction_a_one)
    event_parameters[oel_transferFunction_x_start_1] = (oel_KScale1 * oel_Input0Pu)
    event_parameters[oel_transferFunction_y_start] = (oel_KScale1 * oel_Input0Pu)
    event_parameters[oel_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[oel_firstOrder2_initType] = vf.add_const(1.0, name='')
    event_parameters[oel_limIntegrator_initType] = vf.add_const(3.0, name='')
    event_parameters[oel_limitedPI_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[oel_limitedPI_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI1_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[oel_limitedPI1_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[oel_transferFunction_na] = vf.add_const(2.0, name='')
    event_parameters[oel_transferFunction_nb] = vf.add_const(2.0, name='')
    event_parameters[oel_transferFunction_nx] = vf.add_const(1.0, name='')
    event_parameters[oel_Sw1] = vf.add_const(0.0, name='')
    event_parameters[oel_booleanConstant_k] = oel_Sw1
    event_parameters[oel_flipFlopS_Y0] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[oel_limIntegrator_strict] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_hysteresisMax_pre_y_start] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_hysteresisMin_pre_y_start] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI1_hysteresisMax_pre_y_start] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI1_hysteresisMin_pre_y_start] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI1_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI1_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI1_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI1_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[oel_power1_NInteger] = vf.add_const(1.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[oel_firstOrder_y] = oel_firstOrder_y_start
    initial_equations[oel_firstOrder2_y] = oel_firstOrder2_y_start
    initial_equations[oel_limIntegrator_y] = oel_limIntegrator_y_start
    initial_equations[oel_limitedPI_integrator_y] = oel_limitedPI_integrator_y_start
    initial_equations[oel_limitedPI1_integrator_y] = oel_limitedPI1_integrator_y_start
    initial_equations[oel_transferFunction_x_scaled_1] = (oel_transferFunction_a_end * oel_transferFunction_x_start_1)
    initial_equations[oel_UOelPu] = vf.add_const(0.0, name='')
    initial_equations[oel_VfePu] = vf.add_const(0.0, name='')
    initial_equations[oel_gain_y] = vf.add_const(0.0, name='')
    initial_equations[oel_inputPu] = vf.add_const(1.0, name='')
    initial_equations[oel_limitedPI_y] = oel_limitedPI_Y0
    initial_equations[oel_limitedPI1_y] = oel_limitedPI1_Y0
    initial_equations[oel_transferFunction_x_1] = oel_transferFunction_x_start_1
    initial_equations[oel_transferFunction_y] = oel_transferFunction_y_start
    initial_equations[oel_flipFlopS_y] = (whenCondition1 + (PRE_oel_flipFlopS_y * (sym.Const(1.0) - whenCondition1) * (sym.Const(1.0) - whenCondition2)))
    initial_equations[oel_limitedPI_hysteresisMin_y] = (sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_hysteresisMin_uLow - oel_limitedPI_add_y) + sym.Const(1e-06))))))
    initial_equations[oel_limitedPI1_hysteresisMin_y] = (sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI1_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_hysteresisMin_uLow - oel_limitedPI1_add_y) + sym.Const(1e-06))))))
    initial_equations[oel_limIntegrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[oel_limIntegrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[oel_limitedPI_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[oel_limitedPI_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[oel_limitedPI_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[oel_limitedPI1_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[oel_limitedPI1_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[oel_limitedPI1_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[oel_greaterThreshold1_y] = sym.heaviside(((oel_firstOrder_y - oel_greaterThreshold1_threshold) - sym.Const(1e-06)))
    initial_equations[whenCondition3] = oel_greaterThreshold1_y
    initial_equations[PRE_oel_flipFlopS_y] = START_oel_flipFlopS_y
    initial_equations[PRE_oel_limitedPI1_hysteresisMin_y] = oel_limitedPI1_hysteresisMin_pre_y_start
    initial_equations[PRE_oel_limitedPI1_hysteresisMax_y] = oel_limitedPI1_hysteresisMax_pre_y_start
    initial_equations[oel_limitedPI1_hysteresisMax_y] = (sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI1_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_add_y - oel_limitedPI1_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI1_hysteresisMax_uLow - oel_limitedPI1_add_y) + sym.Const(1e-06))))))
    initial_equations[PRE_oel_timer_entryTime] = vf.add_const(0.0, name='')
    initial_equations[oel_timer_entryTime] = PRE_oel_timer_entryTime
    initial_equations[oel_timer_y] = ((oel_greaterThreshold1_y * (time - oel_timer_entryTime)) + ((sym.Const(1.0) - oel_greaterThreshold1_y) * sym.Const(0.0)))
    initial_equations[PRE_oel_limitedPI_hysteresisMin_y] = oel_limitedPI_hysteresisMin_pre_y_start
    initial_equations[PRE_oel_limitedPI_hysteresisMax_y] = oel_limitedPI_hysteresisMax_pre_y_start
    initial_equations[oel_limitedPI_hysteresisMax_y] = (sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_hysteresisMax_uLow - oel_limitedPI_add_y) + sym.Const(1e-06))))))
    initial_equations[oel_greaterThreshold_y] = sym.heaviside(((oel_limIntegrator_y - oel_greaterThreshold_threshold) - sym.Const(1e-06)))
    initial_equations[whenCondition1] = oel_greaterThreshold_y
    initial_equations[whenCondition2] = (oel_lessEqualThreshold_y * (sym.Const(1.0) - oel_greaterThreshold_y))
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

    template.comment = 'Generator over-excitation limiter OEL5C'
    return template
