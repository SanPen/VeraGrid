# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Scl1c'.

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

def build_scl1c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Return the canonical template rewritten in explicit Block(...) form.

    This helper exists for human auditability and follows the same broad
    construction style used by the handwritten EMT/RMS templates: variables
    are declared through the VarFactory first, then the explicit Block(...)
    is assembled from state, algebraic, initialization, and event sections.

    :param vf: Variable factory used to allocate the symbolic variables.
    :type vf: VarFactory
    :param name: Optional runtime template name.
    :type name: str | None
    :return: Materialized result produced by this builder.
    :rtype: RmsModelTemplate
"""
    template_name: str
    if name is None:
        template_name: str = 'Scl1c'
    else:
        template_name: str = name

    templ: RmsModelTemplate = RmsModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = template_name

    # Inputs
    inputs: list[Var] = list()

    # ______________________________________________________________________________________
    #                                    variables
    # ______________________________________________________________________________________

    # State variables
    scl_firstOrder_y_Scl1c: Var = vf.add_var(name='scl.firstOrder.y_Scl1c')
    scl_firstOrder1_y_Scl1c: Var = vf.add_var(name='scl.firstOrder1.y_Scl1c')
    scl_firstOrder2_y_Scl1c: Var = vf.add_var(name='scl.firstOrder2.y_Scl1c')
    scl_limPIOel_integrator_y_Scl1c: Var = vf.add_var(name='scl.limPIOel.integrator.y_Scl1c')
    scl_limPIUel_integrator_y_Scl1c: Var = vf.add_var(name='scl.limPIUel.integrator.y_Scl1c')

    # Algebraic variables
    scl_power_y_Scl1c: Var = vf.add_var(name='scl.power.y_Scl1c')
    scl_add_y_Scl1c: Var = vf.add_var(name='scl.add.y_Scl1c')
    scl_add1_y_Scl1c: Var = vf.add_var(name='scl.add1.y_Scl1c')
    scl_power1_y_Scl1c: Var = vf.add_var(name='scl.power1.y_Scl1c')
    scl_feedback_y_Scl1c: Var = vf.add_var(name='scl.feedback.y_Scl1c')
    whenCondition1_Scl1c: Var = vf.add_var(name='$whenCondition1_Scl1c')
    scl_timer_y_Scl1c: Var = vf.add_var(name='scl.timer.y_Scl1c')
    scl_greaterThreshold_y_Scl1c: Var = vf.add_var(name='scl.greaterThreshold.y_Scl1c')
    scl_min1_y_Scl1c: Var = vf.add_var(name='scl.min1.y_Scl1c')
    scl_min2_y_Scl1c: Var = vf.add_var(name='scl.min2.y_Scl1c')
    scl_feedback1_y_Scl1c: Var = vf.add_var(name='scl.feedback1.y_Scl1c')
    scl_switchOel_u3_Scl1c: Var = vf.add_var(name='scl.switchOel.u3_Scl1c')
    scl_switchOel_y_Scl1c: Var = vf.add_var(name='scl.switchOel.y_Scl1c')
    scl_limPIOel_add_y_Scl1c: Var = vf.add_var(name='scl.limPIOel.add.y_Scl1c')
    scl_limPIOel_y_Scl1c: Var = vf.add_var(name='scl.limPIOel.y_Scl1c')
    scl_limiterOel_y_Scl1c: Var = vf.add_var(name='scl.limiterOel.y_Scl1c')
    scl_USclOelPu_Scl1c: Var = vf.add_var(name='scl.USclOelPu_Scl1c')
    scl_limPIOel_hysteresisMax_y_Scl1c: Var = vf.add_var(name='scl.limPIOel.hysteresisMax.y_Scl1c')
    scl_limPIOel_hysteresisMin_y_Scl1c: Var = vf.add_var(name='scl.limPIOel.hysteresisMin.y_Scl1c')
    scl_limPIOel_switch1_u2_Scl1c: Var = vf.add_var(name='scl.limPIOel.switch1.u2_Scl1c')
    scl_limPIOel_switch1_y_Scl1c: Var = vf.add_var(name='scl.limPIOel.switch1.y_Scl1c')
    scl_switchUel_u3_Scl1c: Var = vf.add_var(name='scl.switchUel.u3_Scl1c')
    scl_switchUel_y_Scl1c: Var = vf.add_var(name='scl.switchUel.y_Scl1c')
    scl_limPIUel_add_y_Scl1c: Var = vf.add_var(name='scl.limPIUel.add.y_Scl1c')
    scl_limPIUel_y_Scl1c: Var = vf.add_var(name='scl.limPIUel.y_Scl1c')
    scl_USclUelPu_Scl1c: Var = vf.add_var(name='scl.USclUelPu_Scl1c')
    scl_limPIUel_hysteresisMax_y_Scl1c: Var = vf.add_var(name='scl.limPIUel.hysteresisMax.y_Scl1c')
    scl_limPIUel_hysteresisMin_y_Scl1c: Var = vf.add_var(name='scl.limPIUel.hysteresisMin.y_Scl1c')
    scl_limPIUel_switch1_u2_Scl1c: Var = vf.add_var(name='scl.limPIUel.switch1.u2_Scl1c')
    scl_limPIUel_switch1_y_Scl1c: Var = vf.add_var(name='scl.limPIUel.switch1.y_Scl1c')
    scl_timer_entryTime_Scl1c: Var = vf.add_var(name='scl.timer.entryTime_Scl1c')
    scl_QGenPu_Scl1c: Var = vf.add_var(name='scl.QGenPu_Scl1c')
    scl_itPu_im_Scl1c: Var = vf.add_var(name='scl.itPu.im_Scl1c')
    scl_itPu_re_Scl1c: Var = vf.add_var(name='scl.itPu.re_Scl1c')
    scl_utPu_im_Scl1c: Var = vf.add_var(name='scl.utPu.im_Scl1c')
    scl_utPu_re_Scl1c: Var = vf.add_var(name='scl.utPu.re_Scl1c')
    scl_limPIOel_limiter1_simplifiedExpr_Scl1c: Var = vf.add_var(name='scl.limPIOel.limiter1.simplifiedExpr_Scl1c')
    scl_limPIOel_integrator_local_reset_Scl1c: Var = vf.add_var(name='scl.limPIOel.integrator.local_reset_Scl1c')
    scl_limPIOel_integrator_local_set_Scl1c: Var = vf.add_var(name='scl.limPIOel.integrator.local_set_Scl1c')
    scl_limPIUel_limiter1_simplifiedExpr_Scl1c: Var = vf.add_var(name='scl.limPIUel.limiter1.simplifiedExpr_Scl1c')
    scl_limPIUel_integrator_local_reset_Scl1c: Var = vf.add_var(name='scl.limPIUel.integrator.local_reset_Scl1c')
    scl_limPIUel_integrator_local_set_Scl1c: Var = vf.add_var(name='scl.limPIUel.integrator.local_set_Scl1c')
    scl_limiterOel_simplifiedExpr_Scl1c: Var = vf.add_var(name='scl.limiterOel.simplifiedExpr_Scl1c')
    scl_limiterUel_simplifiedExpr_Scl1c: Var = vf.add_var(name='scl.limiterUel.simplifiedExpr_Scl1c')
    scl_division_y_Scl1c: Var = vf.add_var(name='scl.division.y_Scl1c')
    scl_complexToPolar1_phi_Scl1c: Var = vf.add_var(name='scl.complexToPolar1.phi_Scl1c')
    scl_complexToPolar1_len_Scl1c: Var = vf.add_var(name='scl.complexToPolar1.len_Scl1c')
    scl_complexToPolar_phi_Scl1c: Var = vf.add_var(name='scl.complexToPolar.phi_Scl1c')
    scl_complexToPolar_len_Scl1c: Var = vf.add_var(name='scl.complexToPolar.len_Scl1c')
    START_scl_firstOrder_y_Scl1c: Var = vf.add_var(name='$START.scl.firstOrder.y_Scl1c')
    START_scl_firstOrder1_y_Scl1c: Var = vf.add_var(name='$START.scl.firstOrder1.y_Scl1c')
    START_scl_firstOrder2_y_Scl1c: Var = vf.add_var(name='$START.scl.firstOrder2.y_Scl1c')
    PRE_scl_timer_entryTime_Scl1c: Var = vf.add_var(name='$PRE.scl.timer.entryTime_Scl1c')
    PRE_scl_limPIUel_hysteresisMin_y_Scl1c: Var = vf.add_var(name='$PRE.scl.limPIUel.hysteresisMin.y_Scl1c')
    PRE_scl_limPIUel_hysteresisMax_y_Scl1c: Var = vf.add_var(name='$PRE.scl.limPIUel.hysteresisMax.y_Scl1c')
    PRE_scl_limPIOel_hysteresisMin_y_Scl1c: Var = vf.add_var(name='$PRE.scl.limPIOel.hysteresisMin.y_Scl1c')
    PRE_scl_limPIOel_hysteresisMax_y_Scl1c: Var = vf.add_var(name='$PRE.scl.limPIOel.hysteresisMax.y_Scl1c')

    # Differential variables
    d_scl_firstOrder_y_Scl1c: Var = vf.add_diff_var(name='d_scl.firstOrder.y_Scl1c', base_var=scl_firstOrder_y_Scl1c)
    d_scl_firstOrder1_y_Scl1c: Var = vf.add_diff_var(name='d_scl.firstOrder1.y_Scl1c', base_var=scl_firstOrder1_y_Scl1c)
    d_scl_firstOrder2_y_Scl1c: Var = vf.add_diff_var(name='d_scl.firstOrder2.y_Scl1c', base_var=scl_firstOrder2_y_Scl1c)
    d_scl_limPIOel_integrator_y_Scl1c: Var = vf.add_diff_var(name='d_scl.limPIOel.integrator.y_Scl1c', base_var=scl_limPIOel_integrator_y_Scl1c)
    d_scl_limPIUel_integrator_y_Scl1c: Var = vf.add_diff_var(name='d_scl.limPIUel.integrator.y_Scl1c', base_var=scl_limPIUel_integrator_y_Scl1c)

    # Internal variables
    time_Scl1c: Var = vf.add_var(name='time_Scl1c')

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________

    # Runtime parameters and event variables
    scl_firstOrder_T_Scl1c: Var = vf.add_var(name='scl.firstOrder.T_Scl1c')
    scl_firstOrder_k_Scl1c: Var = vf.add_var(name='scl.firstOrder.k_Scl1c')
    scl_firstOrder1_T_Scl1c: Var = vf.add_var(name='scl.firstOrder1.T_Scl1c')
    scl_firstOrder1_k_Scl1c: Var = vf.add_var(name='scl.firstOrder1.k_Scl1c')
    scl_firstOrder2_T_Scl1c: Var = vf.add_var(name='scl.firstOrder2.T_Scl1c')
    scl_firstOrder2_k_Scl1c: Var = vf.add_var(name='scl.firstOrder2.k_Scl1c')
    scl_limPIOel_integrator_k_Scl1c: Var = vf.add_var(name='scl.limPIOel.integrator.k_Scl1c')
    scl_limPIUel_integrator_k_Scl1c: Var = vf.add_var(name='scl.limPIUel.integrator.k_Scl1c')
    scl_power_N_Scl1c: Var = vf.add_var(name='scl.power.N_Scl1c')
    scl_add_k1_Scl1c: Var = vf.add_var(name='scl.add.k1_Scl1c')
    scl_const_k_Scl1c: Var = vf.add_var(name='scl.const.k_Scl1c')
    scl_add_k2_Scl1c: Var = vf.add_var(name='scl.add.k2_Scl1c')
    scl_add1_k1_Scl1c: Var = vf.add_var(name='scl.add1.k1_Scl1c')
    scl_add1_k2_Scl1c: Var = vf.add_var(name='scl.add1.k2_Scl1c')
    scl_power1_N_Scl1c: Var = vf.add_var(name='scl.power1.N_Scl1c')
    scl_ISclLimPu_Scl1c: Var = vf.add_var(name='scl.ISclLimPu_Scl1c')
    scl_greaterThreshold_threshold_Scl1c: Var = vf.add_var(name='scl.greaterThreshold.threshold_Scl1c')
    scl_VSclDb_Scl1c: Var = vf.add_var(name='scl.VSclDb_Scl1c')
    scl_tDScl_Scl1c: Var = vf.add_var(name='scl.tDScl_Scl1c')
    scl_Sw2_Scl1c: Var = vf.add_var(name='scl.Sw2_Scl1c')
    scl_booleanConstant_k_Scl1c: Var = vf.add_var(name='scl.booleanConstant.k_Scl1c')
    scl_limPIOel_add_k2_Scl1c: Var = vf.add_var(name='scl.limPIOel.add.k2_Scl1c')
    scl_limPIOel_add_k1_Scl1c: Var = vf.add_var(name='scl.limPIOel.add.k1_Scl1c')
    scl_limPIOel_limiter1_uMin_Scl1c: Var = vf.add_var(name='scl.limPIOel.limiter1.uMin_Scl1c')
    scl_limPIOel_limiter1_uMax_Scl1c: Var = vf.add_var(name='scl.limPIOel.limiter1.uMax_Scl1c')
    scl_limiterOel_uMin_Scl1c: Var = vf.add_var(name='scl.limiterOel.uMin_Scl1c')
    scl_limiterOel_uMax_Scl1c: Var = vf.add_var(name='scl.limiterOel.uMax_Scl1c')
    scl_gain_k_Scl1c: Var = vf.add_var(name='scl.gain.k_Scl1c')
    scl_limPIOel_hysteresisMax_uHigh_Scl1c: Var = vf.add_var(name='scl.limPIOel.hysteresisMax.uHigh_Scl1c')
    scl_limPIOel_hysteresisMax_uLow_Scl1c: Var = vf.add_var(name='scl.limPIOel.hysteresisMax.uLow_Scl1c')
    scl_limPIOel_hysteresisMin_uHigh_Scl1c: Var = vf.add_var(name='scl.limPIOel.hysteresisMin.uHigh_Scl1c')
    scl_limPIOel_hysteresisMin_uLow_Scl1c: Var = vf.add_var(name='scl.limPIOel.hysteresisMin.uLow_Scl1c')
    scl_limPIOel_const_k_Scl1c: Var = vf.add_var(name='scl.limPIOel.const.k_Scl1c')
    scl_limPIUel_add_k2_Scl1c: Var = vf.add_var(name='scl.limPIUel.add.k2_Scl1c')
    scl_limPIUel_add_k1_Scl1c: Var = vf.add_var(name='scl.limPIUel.add.k1_Scl1c')
    scl_limPIUel_limiter1_uMin_Scl1c: Var = vf.add_var(name='scl.limPIUel.limiter1.uMin_Scl1c')
    scl_limPIUel_limiter1_uMax_Scl1c: Var = vf.add_var(name='scl.limPIUel.limiter1.uMax_Scl1c')
    scl_limiterUel_uMin_Scl1c: Var = vf.add_var(name='scl.limiterUel.uMin_Scl1c')
    scl_limiterUel_uMax_Scl1c: Var = vf.add_var(name='scl.limiterUel.uMax_Scl1c')
    scl_limPIUel_hysteresisMax_uLow_Scl1c: Var = vf.add_var(name='scl.limPIUel.hysteresisMax.uLow_Scl1c')
    scl_limPIUel_hysteresisMax_uHigh_Scl1c: Var = vf.add_var(name='scl.limPIUel.hysteresisMax.uHigh_Scl1c')
    scl_limPIUel_hysteresisMin_uHigh_Scl1c: Var = vf.add_var(name='scl.limPIUel.hysteresisMin.uHigh_Scl1c')
    scl_limPIUel_hysteresisMin_uLow_Scl1c: Var = vf.add_var(name='scl.limPIUel.hysteresisMin.uLow_Scl1c')
    scl_limPIUel_const_k_Scl1c: Var = vf.add_var(name='scl.limPIUel.const.k_Scl1c')
    scl_limPIOel_integrator_y_start_Scl1c: Var = vf.add_var(name='scl.limPIOel.integrator.y_start_Scl1c')
    scl_limPIUel_integrator_y_start_Scl1c: Var = vf.add_var(name='scl.limPIUel.integrator.y_start_Scl1c')
    scl_limPIOel_Y0_Scl1c: Var = vf.add_var(name='scl.limPIOel.Y0_Scl1c')
    scl_limPIUel_Y0_Scl1c: Var = vf.add_var(name='scl.limPIUel.Y0_Scl1c')
    scl_limPIUel_hysteresisMin_pre_y_start_Scl1c: Var = vf.add_var(name='scl.limPIUel.hysteresisMin.pre_y_start_Scl1c')
    scl_limPIUel_hysteresisMax_pre_y_start_Scl1c: Var = vf.add_var(name='scl.limPIUel.hysteresisMax.pre_y_start_Scl1c')
    scl_limPIOel_hysteresisMin_pre_y_start_Scl1c: Var = vf.add_var(name='scl.limPIOel.hysteresisMin.pre_y_start_Scl1c')
    scl_limPIOel_hysteresisMax_pre_y_start_Scl1c: Var = vf.add_var(name='scl.limPIOel.hysteresisMax.pre_y_start_Scl1c')
    scl_IqMinPu_Scl1c: Var = vf.add_var(name='scl.IqMinPu_Scl1c')
    scl_K_Scl1c: Var = vf.add_var(name='scl.K_Scl1c')
    scl_KiOex_Scl1c: Var = vf.add_var(name='scl.KiOex_Scl1c')
    scl_KiUex_Scl1c: Var = vf.add_var(name='scl.KiUex_Scl1c')
    scl_KpOex_Scl1c: Var = vf.add_var(name='scl.KpOex_Scl1c')
    scl_KpUex_Scl1c: Var = vf.add_var(name='scl.KpUex_Scl1c')
    scl_QGen0Pu_Scl1c: Var = vf.add_var(name='scl.QGen0Pu_Scl1c')
    scl_VSclMaxPu_Scl1c: Var = vf.add_var(name='scl.VSclMaxPu_Scl1c')
    scl_VSclMinPu_Scl1c: Var = vf.add_var(name='scl.VSclMinPu_Scl1c')
    scl_const1_k_Scl1c: Var = vf.add_var(name='scl.const1.k_Scl1c')
    scl_tQScl_Scl1c: Var = vf.add_var(name='scl.tQScl_Scl1c')
    scl_firstOrder_y_start_Scl1c: Var = vf.add_var(name='scl.firstOrder.y_start_Scl1c')
    scl_ut0Pu_im_Scl1c: Var = vf.add_var(name='scl.ut0Pu.im_Scl1c')
    scl_ut0Pu_re_Scl1c: Var = vf.add_var(name='scl.ut0Pu.re_Scl1c')
    scl_tIt_Scl1c: Var = vf.add_var(name='scl.tIt_Scl1c')
    scl_firstOrder1_y_start_Scl1c: Var = vf.add_var(name='scl.firstOrder1.y_start_Scl1c')
    scl_it0Pu_im_Scl1c: Var = vf.add_var(name='scl.it0Pu.im_Scl1c')
    scl_it0Pu_re_Scl1c: Var = vf.add_var(name='scl.it0Pu.re_Scl1c')
    scl_tInv_Scl1c: Var = vf.add_var(name='scl.tInv_Scl1c')
    scl_firstOrder2_y_start_Scl1c: Var = vf.add_var(name='scl.firstOrder2.y_start_Scl1c')
    scl_limPIOel_Ki_Scl1c: Var = vf.add_var(name='scl.limPIOel.Ki_Scl1c')
    scl_limPIOel_Kp_Scl1c: Var = vf.add_var(name='scl.limPIOel.Kp_Scl1c')
    scl_limPIOel_Tol_Scl1c: Var = vf.add_var(name='scl.limPIOel.Tol_Scl1c')
    scl_limPIOel_YMax_Scl1c: Var = vf.add_var(name='scl.limPIOel.YMax_Scl1c')
    scl_limPIOel_YMin_Scl1c: Var = vf.add_var(name='scl.limPIOel.YMin_Scl1c')
    scl_limPIUel_Ki_Scl1c: Var = vf.add_var(name='scl.limPIUel.Ki_Scl1c')
    scl_limPIUel_Kp_Scl1c: Var = vf.add_var(name='scl.limPIUel.Kp_Scl1c')
    scl_limPIUel_Tol_Scl1c: Var = vf.add_var(name='scl.limPIUel.Tol_Scl1c')
    scl_limPIUel_YMax_Scl1c: Var = vf.add_var(name='scl.limPIUel.YMax_Scl1c')
    scl_limPIUel_YMin_Scl1c: Var = vf.add_var(name='scl.limPIUel.YMin_Scl1c')
    scl_firstOrder_initType_Scl1c: Var = vf.add_var(name='scl.firstOrder.initType_Scl1c')
    scl_firstOrder1_initType_Scl1c: Var = vf.add_var(name='scl.firstOrder1.initType_Scl1c')
    scl_firstOrder2_initType_Scl1c: Var = vf.add_var(name='scl.firstOrder2.initType_Scl1c')
    scl_limPIOel_integrator_initType_Scl1c: Var = vf.add_var(name='scl.limPIOel.integrator.initType_Scl1c')
    scl_limPIOel_limiter1_homotopyType_Scl1c: Var = vf.add_var(name='scl.limPIOel.limiter1.homotopyType_Scl1c')
    scl_limPIUel_integrator_initType_Scl1c: Var = vf.add_var(name='scl.limPIUel.integrator.initType_Scl1c')
    scl_limPIUel_limiter1_homotopyType_Scl1c: Var = vf.add_var(name='scl.limPIUel.limiter1.homotopyType_Scl1c')
    scl_limiterOel_homotopyType_Scl1c: Var = vf.add_var(name='scl.limiterOel.homotopyType_Scl1c')
    scl_limiterUel_homotopyType_Scl1c: Var = vf.add_var(name='scl.limiterUel.homotopyType_Scl1c')
    scl_Sw1_Scl1c: Var = vf.add_var(name='scl.Sw1_Scl1c')
    scl_limPIOel_integrator_use_reset_Scl1c: Var = vf.add_var(name='scl.limPIOel.integrator.use_reset_Scl1c')
    scl_limPIOel_integrator_use_set_Scl1c: Var = vf.add_var(name='scl.limPIOel.integrator.use_set_Scl1c')
    scl_limPIOel_limiter1_limitsAtInit_Scl1c: Var = vf.add_var(name='scl.limPIOel.limiter1.limitsAtInit_Scl1c')
    scl_limPIOel_limiter1_strict_Scl1c: Var = vf.add_var(name='scl.limPIOel.limiter1.strict_Scl1c')
    scl_limPIUel_integrator_use_reset_Scl1c: Var = vf.add_var(name='scl.limPIUel.integrator.use_reset_Scl1c')
    scl_limPIUel_integrator_use_set_Scl1c: Var = vf.add_var(name='scl.limPIUel.integrator.use_set_Scl1c')
    scl_limPIUel_limiter1_limitsAtInit_Scl1c: Var = vf.add_var(name='scl.limPIUel.limiter1.limitsAtInit_Scl1c')
    scl_limPIUel_limiter1_strict_Scl1c: Var = vf.add_var(name='scl.limPIUel.limiter1.strict_Scl1c')
    scl_limiterOel_limitsAtInit_Scl1c: Var = vf.add_var(name='scl.limiterOel.limitsAtInit_Scl1c')
    scl_limiterOel_strict_Scl1c: Var = vf.add_var(name='scl.limiterOel.strict_Scl1c')
    scl_limiterUel_limitsAtInit_Scl1c: Var = vf.add_var(name='scl.limiterUel.limitsAtInit_Scl1c')
    scl_limiterUel_strict_Scl1c: Var = vf.add_var(name='scl.limiterUel.strict_Scl1c')
    scl_power_NInteger_Scl1c: Var = vf.add_var(name='scl.power.NInteger_Scl1c')
    scl_power1_NInteger_Scl1c: Var = vf.add_var(name='scl.power1.NInteger_Scl1c')

    event_dict: dict[Var, Expr | Const] = dict({
        scl_ISclLimPu_Scl1c: vf.add_const(value=1.1),
        scl_IqMinPu_Scl1c: vf.add_const(value=0.0),
        scl_K_Scl1c: vf.add_const(value=1.0),
        scl_KiOex_Scl1c: vf.add_const(value=1.0),
        scl_KiUex_Scl1c: vf.add_const(value=1.0),
        scl_KpOex_Scl1c: vf.add_const(value=1.0),
        scl_KpUex_Scl1c: vf.add_const(value=1.0),
        scl_QGen0Pu_Scl1c: vf.add_const(value=0.0),
        scl_VSclDb_Scl1c: vf.add_const(value=0.0),
        scl_VSclMaxPu_Scl1c: vf.add_const(value=1.0),
        scl_VSclMinPu_Scl1c: vf.add_const(value=-1.0),
        scl_add_k1_Scl1c: vf.add_const(value=1.0),
        scl_add_k2_Scl1c: vf.add_const(value=-1.0),
        scl_add1_k1_Scl1c: vf.add_const(value=-1.0),
        scl_add1_k2_Scl1c: vf.add_const(value=-1.0),
        scl_const_k_Scl1c: scl_IqMinPu_Scl1c,
        scl_const1_k_Scl1c: scl_ISclLimPu_Scl1c,
        scl_firstOrder_T_Scl1c: scl_tQScl_Scl1c,
        scl_firstOrder_k_Scl1c: vf.add_const(value=1.0),
        scl_firstOrder_y_start_Scl1c: (scl_QGen0Pu_Scl1c / (((scl_ut0Pu_re_Scl1c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl1c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5))),
        scl_firstOrder1_T_Scl1c: scl_tIt_Scl1c,
        scl_firstOrder1_k_Scl1c: vf.add_const(value=1.0),
        scl_firstOrder1_y_start_Scl1c: (((scl_it0Pu_re_Scl1c ** vf.add_const(value=2.0)) + (scl_it0Pu_im_Scl1c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)),
        scl_firstOrder2_T_Scl1c: scl_tInv_Scl1c,
        scl_firstOrder2_k_Scl1c: vf.add_const(value=1.0),
        scl_firstOrder2_y_start_Scl1c: (((scl_it0Pu_re_Scl1c ** vf.add_const(value=2.0)) + (scl_it0Pu_im_Scl1c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)),
        scl_gain_k_Scl1c: vf.add_const(value=-1.0),
        scl_greaterThreshold_threshold_Scl1c: vf.add_const(value=0.0),
        scl_it0Pu_im_Scl1c: vf.add_const(value=0.0),
        scl_it0Pu_re_Scl1c: vf.add_const(value=0.8),
        scl_limPIOel_Ki_Scl1c: scl_KiOex_Scl1c,
        scl_limPIOel_Kp_Scl1c: scl_KpOex_Scl1c,
        scl_limPIOel_Tol_Scl1c: vf.add_const(value=1e-05),
        scl_limPIOel_Y0_Scl1c: vf.add_const(value=0.0),
        scl_limPIOel_YMax_Scl1c: scl_VSclMaxPu_Scl1c,
        scl_limPIOel_YMin_Scl1c: scl_VSclMinPu_Scl1c,
        scl_limPIOel_add_k1_Scl1c: scl_limPIOel_Kp_Scl1c,
        scl_limPIOel_add_k2_Scl1c: vf.add_const(value=1.0),
        scl_limPIOel_const_k_Scl1c: vf.add_const(value=0.0),
        scl_limPIOel_hysteresisMax_uHigh_Scl1c: scl_limPIOel_YMax_Scl1c,
        scl_limPIOel_hysteresisMax_uLow_Scl1c: (scl_limPIOel_YMax_Scl1c + (scl_limPIOel_Tol_Scl1c * (scl_limPIOel_YMin_Scl1c - scl_limPIOel_YMax_Scl1c))),
        scl_limPIOel_hysteresisMin_uHigh_Scl1c: (scl_limPIOel_YMin_Scl1c + (scl_limPIOel_Tol_Scl1c * (scl_limPIOel_YMax_Scl1c - scl_limPIOel_YMin_Scl1c))),
        scl_limPIOel_hysteresisMin_uLow_Scl1c: scl_limPIOel_YMin_Scl1c,
        scl_limPIOel_integrator_k_Scl1c: scl_limPIOel_Ki_Scl1c,
        scl_limPIOel_integrator_y_start_Scl1c: scl_limPIOel_Y0_Scl1c,
        scl_limPIOel_limiter1_uMax_Scl1c: scl_limPIOel_YMax_Scl1c,
        scl_limPIOel_limiter1_uMin_Scl1c: scl_limPIOel_YMin_Scl1c,
        scl_limPIUel_Ki_Scl1c: scl_KiUex_Scl1c,
        scl_limPIUel_Kp_Scl1c: scl_KpUex_Scl1c,
        scl_limPIUel_Tol_Scl1c: vf.add_const(value=1e-05),
        scl_limPIUel_Y0_Scl1c: vf.add_const(value=0.0),
        scl_limPIUel_YMax_Scl1c: scl_VSclMaxPu_Scl1c,
        scl_limPIUel_YMin_Scl1c: scl_VSclMinPu_Scl1c,
        scl_limPIUel_add_k1_Scl1c: scl_limPIUel_Kp_Scl1c,
        scl_limPIUel_add_k2_Scl1c: vf.add_const(value=1.0),
        scl_limPIUel_const_k_Scl1c: vf.add_const(value=0.0),
        scl_limPIUel_hysteresisMax_uHigh_Scl1c: scl_limPIUel_YMax_Scl1c,
        scl_limPIUel_hysteresisMax_uLow_Scl1c: (scl_limPIUel_YMax_Scl1c + (scl_limPIUel_Tol_Scl1c * (scl_limPIUel_YMin_Scl1c - scl_limPIUel_YMax_Scl1c))),
        scl_limPIUel_hysteresisMin_uHigh_Scl1c: (scl_limPIUel_YMin_Scl1c + (scl_limPIUel_Tol_Scl1c * (scl_limPIUel_YMax_Scl1c - scl_limPIUel_YMin_Scl1c))),
        scl_limPIUel_hysteresisMin_uLow_Scl1c: scl_limPIUel_YMin_Scl1c,
        scl_limPIUel_integrator_k_Scl1c: scl_limPIUel_Ki_Scl1c,
        scl_limPIUel_integrator_y_start_Scl1c: scl_limPIUel_Y0_Scl1c,
        scl_limPIUel_limiter1_uMax_Scl1c: scl_limPIUel_YMax_Scl1c,
        scl_limPIUel_limiter1_uMin_Scl1c: scl_limPIUel_YMin_Scl1c,
        scl_limiterOel_uMax_Scl1c: vf.add_const(value=999.0),
        scl_limiterOel_uMin_Scl1c: vf.add_const(value=0.0),
        scl_limiterUel_uMax_Scl1c: vf.add_const(value=999.0),
        scl_limiterUel_uMin_Scl1c: vf.add_const(value=0.0),
        scl_power_N_Scl1c: scl_K_Scl1c,
        scl_power1_N_Scl1c: scl_K_Scl1c,
        scl_tDScl_Scl1c: vf.add_const(value=0.02),
        scl_tInv_Scl1c: vf.add_const(value=1.0),
        scl_tIt_Scl1c: vf.add_const(value=0.02),
        scl_tQScl_Scl1c: vf.add_const(value=0.02),
        scl_ut0Pu_im_Scl1c: vf.add_const(value=0.0),
        scl_ut0Pu_re_Scl1c: vf.add_const(value=1.0),
        scl_firstOrder_initType_Scl1c: vf.add_const(value=1.0),
        scl_firstOrder1_initType_Scl1c: vf.add_const(value=1.0),
        scl_firstOrder2_initType_Scl1c: vf.add_const(value=1.0),
        scl_limPIOel_integrator_initType_Scl1c: vf.add_const(value=3.0),
        scl_limPIOel_limiter1_homotopyType_Scl1c: vf.add_const(value=1.0),
        scl_limPIUel_integrator_initType_Scl1c: vf.add_const(value=3.0),
        scl_limPIUel_limiter1_homotopyType_Scl1c: vf.add_const(value=1.0),
        scl_limiterOel_homotopyType_Scl1c: vf.add_const(value=1.0),
        scl_limiterUel_homotopyType_Scl1c: vf.add_const(value=1.0),
        scl_Sw1_Scl1c: vf.add_const(value=0.0),
        scl_Sw2_Scl1c: vf.add_const(value=0.0),
        scl_booleanConstant_k_Scl1c: scl_Sw1_Scl1c,
        scl_limPIOel_hysteresisMax_pre_y_start_Scl1c: vf.add_const(value=0.0),
        scl_limPIOel_hysteresisMin_pre_y_start_Scl1c: vf.add_const(value=1.0),
        scl_limPIOel_integrator_use_reset_Scl1c: vf.add_const(value=0.0),
        scl_limPIOel_integrator_use_set_Scl1c: vf.add_const(value=0.0),
        scl_limPIOel_limiter1_limitsAtInit_Scl1c: vf.add_const(value=1.0),
        scl_limPIOel_limiter1_strict_Scl1c: vf.add_const(value=0.0),
        scl_limPIUel_hysteresisMax_pre_y_start_Scl1c: vf.add_const(value=0.0),
        scl_limPIUel_hysteresisMin_pre_y_start_Scl1c: vf.add_const(value=1.0),
        scl_limPIUel_integrator_use_reset_Scl1c: vf.add_const(value=0.0),
        scl_limPIUel_integrator_use_set_Scl1c: vf.add_const(value=0.0),
        scl_limPIUel_limiter1_limitsAtInit_Scl1c: vf.add_const(value=1.0),
        scl_limPIUel_limiter1_strict_Scl1c: vf.add_const(value=0.0),
        scl_limiterOel_limitsAtInit_Scl1c: vf.add_const(value=1.0),
        scl_limiterOel_strict_Scl1c: vf.add_const(value=0.0),
        scl_limiterUel_limitsAtInit_Scl1c: vf.add_const(value=1.0),
        scl_limiterUel_strict_Scl1c: vf.add_const(value=0.0),
        scl_power_NInteger_Scl1c: vf.add_const(value=1.0),
        scl_power1_NInteger_Scl1c: vf.add_const(value=1.0),
    })

    external_mapping: dict[object, Var] = dict()

    api_obj_mapping: dict[object, Var] = dict()

    templ.block = Block(
        state_eqs=[
            (((scl_firstOrder_k_Scl1c * scl_division_y_Scl1c) - scl_firstOrder_y_Scl1c) / scl_firstOrder_T_Scl1c),
            (((scl_firstOrder1_k_Scl1c * scl_complexToPolar_len_Scl1c) - scl_firstOrder1_y_Scl1c) / scl_firstOrder1_T_Scl1c),
            (((scl_firstOrder2_k_Scl1c * scl_complexToPolar_len_Scl1c) - scl_firstOrder2_y_Scl1c) / scl_firstOrder2_T_Scl1c),
            (scl_limPIOel_integrator_k_Scl1c * scl_limPIOel_switch1_y_Scl1c),
            (scl_limPIUel_integrator_k_Scl1c * scl_limPIUel_switch1_y_Scl1c),
        ],
        state_vars=[
            scl_firstOrder_y_Scl1c,
            scl_firstOrder1_y_Scl1c,
            scl_firstOrder2_y_Scl1c,
            scl_limPIOel_integrator_y_Scl1c,
            scl_limPIUel_integrator_y_Scl1c,
        ],
        algebraic_eqs=[
            (scl_power_y_Scl1c - (scl_firstOrder_y_Scl1c ** scl_power_N_Scl1c)),
            (scl_add_y_Scl1c - ((scl_add_k1_Scl1c * scl_power_y_Scl1c) + (scl_add_k2_Scl1c * scl_const_k_Scl1c))),
            (scl_add1_y_Scl1c - ((scl_add1_k1_Scl1c * scl_const_k_Scl1c) + (scl_add1_k2_Scl1c * scl_power_y_Scl1c))),
            (scl_power1_y_Scl1c - (scl_firstOrder1_y_Scl1c ** scl_power1_N_Scl1c)),
            (scl_feedback_y_Scl1c - (scl_power1_y_Scl1c - scl_ISclLimPu_Scl1c)),
            (whenCondition1_Scl1c - sym.heaviside(((scl_feedback_y_Scl1c - scl_greaterThreshold_threshold_Scl1c) - vf.add_const(value=1e-06)))),
            (scl_timer_y_Scl1c - ((whenCondition1_Scl1c * (time_Scl1c - scl_timer_entryTime_Scl1c)) + ((vf.add_const(value=1.0) - whenCondition1_Scl1c) * vf.add_const(value=0.0)))),
            (scl_greaterThreshold_y_Scl1c - whenCondition1_Scl1c),
            (scl_min1_y_Scl1c - ((scl_add_y_Scl1c * sym.heaviside((scl_feedback_y_Scl1c - scl_add_y_Scl1c))) + (scl_feedback_y_Scl1c * (vf.add_const(value=1) - sym.heaviside((scl_feedback_y_Scl1c - scl_add_y_Scl1c)))))),
            (scl_min2_y_Scl1c - ((scl_feedback_y_Scl1c * sym.heaviside((scl_add1_y_Scl1c - scl_feedback_y_Scl1c))) + (scl_add1_y_Scl1c * (vf.add_const(value=1) - sym.heaviside((scl_add1_y_Scl1c - scl_feedback_y_Scl1c)))))),
            (scl_feedback1_y_Scl1c - (scl_firstOrder2_y_Scl1c - scl_ISclLimPu_Scl1c)),
            (scl_switchOel_u3_Scl1c - ((((vf.add_const(value=1.0) - scl_Sw2_Scl1c) * sym.heaviside(((scl_timer_y_Scl1c - scl_tDScl_Scl1c) - vf.add_const(value=1e-06)))) + (scl_Sw2_Scl1c * sym.heaviside(((scl_feedback1_y_Scl1c - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))))) * sym.heaviside(((scl_QGenPu_Scl1c - scl_VSclDb_Scl1c) - vf.add_const(value=1e-06))) * scl_feedback_y_Scl1c)),
            (scl_switchOel_y_Scl1c - ((scl_booleanConstant_k_Scl1c * scl_min1_y_Scl1c) + ((vf.add_const(value=1.0) - scl_booleanConstant_k_Scl1c) * scl_switchOel_u3_Scl1c))),
            (scl_limPIOel_add_y_Scl1c - ((scl_limPIOel_add_k1_Scl1c * scl_switchOel_y_Scl1c) + (scl_limPIOel_add_k2_Scl1c * scl_limPIOel_integrator_y_Scl1c))),
            (scl_limPIOel_y_Scl1c - ((sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_limiter1_uMax_Scl1c) - vf.add_const(value=1e-06))) * scl_limPIOel_limiter1_uMax_Scl1c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_limiter1_uMax_Scl1c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_limPIOel_limiter1_uMin_Scl1c - scl_limPIOel_add_y_Scl1c) - vf.add_const(value=1e-06))) * scl_limPIOel_limiter1_uMin_Scl1c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limPIOel_limiter1_uMin_Scl1c - scl_limPIOel_add_y_Scl1c) - vf.add_const(value=1e-06)))) * scl_limPIOel_add_y_Scl1c))))),
            (scl_limiterOel_y_Scl1c - ((sym.heaviside(((scl_limPIOel_y_Scl1c - scl_limiterOel_uMax_Scl1c) - vf.add_const(value=1e-06))) * scl_limiterOel_uMax_Scl1c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limPIOel_y_Scl1c - scl_limiterOel_uMax_Scl1c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_limiterOel_uMin_Scl1c - scl_limPIOel_y_Scl1c) - vf.add_const(value=1e-06))) * scl_limiterOel_uMin_Scl1c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limiterOel_uMin_Scl1c - scl_limPIOel_y_Scl1c) - vf.add_const(value=1e-06)))) * scl_limPIOel_y_Scl1c))))),
            (scl_USclOelPu_Scl1c - (scl_gain_k_Scl1c * scl_limiterOel_y_Scl1c)),
            ((scl_limPIOel_hysteresisMax_y_Scl1c - sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_hysteresisMax_uHigh_Scl1c) - vf.add_const(value=1e-06)))) - sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_hysteresisMax_uLow_Scl1c) + vf.add_const(value=1e-06)))),
            ((scl_limPIOel_hysteresisMin_y_Scl1c - sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_hysteresisMin_uHigh_Scl1c) - vf.add_const(value=1e-06)))) - sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_hysteresisMin_uLow_Scl1c) + vf.add_const(value=1e-06)))),
            (scl_limPIOel_switch1_u2_Scl1c - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - scl_limPIOel_hysteresisMax_y_Scl1c) * (vf.add_const(value=1.0) - (vf.add_const(value=1.0) - scl_limPIOel_hysteresisMin_y_Scl1c))))),
            (scl_limPIOel_switch1_y_Scl1c - ((scl_limPIOel_switch1_u2_Scl1c * scl_limPIOel_const_k_Scl1c) + ((vf.add_const(value=1.0) - scl_limPIOel_switch1_u2_Scl1c) * scl_switchOel_y_Scl1c))),
            (scl_switchUel_u3_Scl1c - ((((vf.add_const(value=1.0) - scl_Sw2_Scl1c) * sym.heaviside(((scl_timer_y_Scl1c - scl_tDScl_Scl1c) - vf.add_const(value=1e-06)))) + (scl_Sw2_Scl1c * sym.heaviside(((scl_feedback1_y_Scl1c - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))))) * sym.heaviside((((-scl_VSclDb_Scl1c) - scl_QGenPu_Scl1c) - vf.add_const(value=1e-06))) * scl_feedback_y_Scl1c)),
            (scl_switchUel_y_Scl1c - ((scl_booleanConstant_k_Scl1c * scl_min2_y_Scl1c) + ((vf.add_const(value=1.0) - scl_booleanConstant_k_Scl1c) * scl_switchUel_u3_Scl1c))),
            (scl_limPIUel_add_y_Scl1c - ((scl_limPIUel_add_k1_Scl1c * scl_switchUel_y_Scl1c) + (scl_limPIUel_add_k2_Scl1c * scl_limPIUel_integrator_y_Scl1c))),
            (scl_limPIUel_y_Scl1c - ((sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_limiter1_uMax_Scl1c) - vf.add_const(value=1e-06))) * scl_limPIUel_limiter1_uMax_Scl1c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_limiter1_uMax_Scl1c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_limPIUel_limiter1_uMin_Scl1c - scl_limPIUel_add_y_Scl1c) - vf.add_const(value=1e-06))) * scl_limPIUel_limiter1_uMin_Scl1c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limPIUel_limiter1_uMin_Scl1c - scl_limPIUel_add_y_Scl1c) - vf.add_const(value=1e-06)))) * scl_limPIUel_add_y_Scl1c))))),
            (scl_USclUelPu_Scl1c - ((sym.heaviside(((scl_limPIUel_y_Scl1c - scl_limiterUel_uMax_Scl1c) - vf.add_const(value=1e-06))) * scl_limiterUel_uMax_Scl1c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limPIUel_y_Scl1c - scl_limiterUel_uMax_Scl1c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_limiterUel_uMin_Scl1c - scl_limPIUel_y_Scl1c) - vf.add_const(value=1e-06))) * scl_limiterUel_uMin_Scl1c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limiterUel_uMin_Scl1c - scl_limPIUel_y_Scl1c) - vf.add_const(value=1e-06)))) * scl_limPIUel_y_Scl1c))))),
            ((scl_limPIUel_hysteresisMax_y_Scl1c - sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_hysteresisMax_uHigh_Scl1c) - vf.add_const(value=1e-06)))) - sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_hysteresisMax_uLow_Scl1c) + vf.add_const(value=1e-06)))),
            ((scl_limPIUel_hysteresisMin_y_Scl1c - sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_hysteresisMin_uHigh_Scl1c) - vf.add_const(value=1e-06)))) - sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_hysteresisMin_uLow_Scl1c) + vf.add_const(value=1e-06)))),
            (scl_limPIUel_switch1_u2_Scl1c - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - scl_limPIUel_hysteresisMax_y_Scl1c) * (vf.add_const(value=1.0) - (vf.add_const(value=1.0) - scl_limPIUel_hysteresisMin_y_Scl1c))))),
            (scl_limPIUel_switch1_y_Scl1c - ((scl_limPIUel_switch1_u2_Scl1c * scl_limPIUel_const_k_Scl1c) + ((vf.add_const(value=1.0) - scl_limPIUel_switch1_u2_Scl1c) * scl_switchUel_y_Scl1c))),
            (scl_complexToPolar1_len_Scl1c - (((scl_utPu_re_Scl1c ** vf.add_const(value=2.0)) + (scl_utPu_im_Scl1c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5))),
            (scl_complexToPolar_len_Scl1c - (((scl_itPu_re_Scl1c ** vf.add_const(value=2.0)) + (scl_itPu_im_Scl1c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5))),
            (scl_division_y_Scl1c - (scl_QGenPu_Scl1c / scl_complexToPolar1_len_Scl1c)),
        ],
        algebraic_vars=[
            scl_power_y_Scl1c,
            scl_add_y_Scl1c,
            scl_add1_y_Scl1c,
            scl_power1_y_Scl1c,
            scl_feedback_y_Scl1c,
            whenCondition1_Scl1c,
            scl_timer_y_Scl1c,
            scl_greaterThreshold_y_Scl1c,
            scl_min1_y_Scl1c,
            scl_min2_y_Scl1c,
            scl_feedback1_y_Scl1c,
            scl_switchOel_u3_Scl1c,
            scl_switchOel_y_Scl1c,
            scl_limPIOel_add_y_Scl1c,
            scl_limPIOel_y_Scl1c,
            scl_limiterOel_y_Scl1c,
            scl_USclOelPu_Scl1c,
            scl_limPIOel_hysteresisMax_y_Scl1c,
            scl_limPIOel_hysteresisMin_y_Scl1c,
            scl_limPIOel_switch1_u2_Scl1c,
            scl_limPIOel_switch1_y_Scl1c,
            scl_switchUel_u3_Scl1c,
            scl_switchUel_y_Scl1c,
            scl_limPIUel_add_y_Scl1c,
            scl_limPIUel_y_Scl1c,
            scl_USclUelPu_Scl1c,
            scl_limPIUel_hysteresisMax_y_Scl1c,
            scl_limPIUel_hysteresisMin_y_Scl1c,
            scl_limPIUel_switch1_u2_Scl1c,
            scl_limPIUel_switch1_y_Scl1c,
            scl_timer_entryTime_Scl1c,
            scl_QGenPu_Scl1c,
            scl_itPu_im_Scl1c,
            scl_itPu_re_Scl1c,
            scl_utPu_im_Scl1c,
            scl_utPu_re_Scl1c,
            scl_limPIOel_limiter1_simplifiedExpr_Scl1c,
            scl_limPIOel_integrator_local_reset_Scl1c,
            scl_limPIOel_integrator_local_set_Scl1c,
            scl_limPIUel_limiter1_simplifiedExpr_Scl1c,
            scl_limPIUel_integrator_local_reset_Scl1c,
            scl_limPIUel_integrator_local_set_Scl1c,
            scl_limiterOel_simplifiedExpr_Scl1c,
            scl_limiterUel_simplifiedExpr_Scl1c,
            scl_division_y_Scl1c,
            scl_complexToPolar1_phi_Scl1c,
            scl_complexToPolar1_len_Scl1c,
            scl_complexToPolar_phi_Scl1c,
            scl_complexToPolar_len_Scl1c,
            START_scl_firstOrder_y_Scl1c,
            START_scl_firstOrder1_y_Scl1c,
            START_scl_firstOrder2_y_Scl1c,
            PRE_scl_timer_entryTime_Scl1c,
            PRE_scl_limPIUel_hysteresisMin_y_Scl1c,
            PRE_scl_limPIUel_hysteresisMax_y_Scl1c,
            PRE_scl_limPIOel_hysteresisMin_y_Scl1c,
            PRE_scl_limPIOel_hysteresisMax_y_Scl1c,
        ],
        init_eqs={
            scl_firstOrder_y_Scl1c: START_scl_firstOrder_y_Scl1c,
            scl_firstOrder1_y_Scl1c: START_scl_firstOrder1_y_Scl1c,
            scl_firstOrder2_y_Scl1c: START_scl_firstOrder2_y_Scl1c,
            scl_limPIOel_integrator_y_Scl1c: scl_limPIOel_integrator_y_start_Scl1c,
            scl_limPIUel_integrator_y_Scl1c: scl_limPIUel_integrator_y_start_Scl1c,
            scl_QGenPu_Scl1c: vf.add_const(value=0.0),
            scl_USclOelPu_Scl1c: vf.add_const(value=0.0),
            scl_USclUelPu_Scl1c: vf.add_const(value=0.0),
            scl_itPu_im_Scl1c: vf.add_const(value=0.0),
            scl_itPu_re_Scl1c: vf.add_const(value=0.8),
            scl_limPIOel_y_Scl1c: scl_limPIOel_Y0_Scl1c,
            scl_limPIUel_y_Scl1c: scl_limPIUel_Y0_Scl1c,
            scl_limiterOel_y_Scl1c: vf.add_const(value=0.0),
            scl_utPu_im_Scl1c: vf.add_const(value=0.0),
            scl_utPu_re_Scl1c: vf.add_const(value=1.0),
            scl_limPIOel_hysteresisMin_y_Scl1c: (sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_hysteresisMin_uHigh_Scl1c) - vf.add_const(value=1e-06))) + sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_hysteresisMin_uLow_Scl1c) + vf.add_const(value=1e-06)))),
            scl_limPIUel_hysteresisMin_y_Scl1c: (sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_hysteresisMin_uHigh_Scl1c) - vf.add_const(value=1e-06))) + sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_hysteresisMin_uLow_Scl1c) + vf.add_const(value=1e-06)))),
            scl_limPIOel_limiter1_simplifiedExpr_Scl1c: vf.add_const(value=0.0),
            scl_limPIOel_integrator_local_reset_Scl1c: vf.add_const(value=0.0),
            scl_limPIOel_integrator_local_set_Scl1c: vf.add_const(value=0.0),
            scl_limPIUel_limiter1_simplifiedExpr_Scl1c: vf.add_const(value=0.0),
            scl_limPIUel_integrator_local_reset_Scl1c: vf.add_const(value=0.0),
            scl_limPIUel_integrator_local_set_Scl1c: vf.add_const(value=0.0),
            scl_limiterOel_simplifiedExpr_Scl1c: vf.add_const(value=0.0),
            scl_limiterUel_simplifiedExpr_Scl1c: vf.add_const(value=0.0),
            scl_division_y_Scl1c: vf.add_const(value=0.0),
            scl_complexToPolar1_phi_Scl1c: vf.add_const(value=0.0),
            scl_complexToPolar1_len_Scl1c: vf.add_const(value=1.0),
            scl_complexToPolar_phi_Scl1c: vf.add_const(value=0.0),
            scl_complexToPolar_len_Scl1c: vf.add_const(value=0.8000000000000003),
            scl_greaterThreshold_y_Scl1c: sym.heaviside(((scl_feedback_y_Scl1c - scl_greaterThreshold_threshold_Scl1c) - vf.add_const(value=1e-06))),
            whenCondition1_Scl1c: scl_greaterThreshold_y_Scl1c,
            PRE_scl_timer_entryTime_Scl1c: vf.add_const(value=0.0),
            scl_timer_entryTime_Scl1c: PRE_scl_timer_entryTime_Scl1c,
            scl_timer_y_Scl1c: ((scl_greaterThreshold_y_Scl1c * (time_Scl1c - scl_timer_entryTime_Scl1c)) + ((vf.add_const(value=1.0) - scl_greaterThreshold_y_Scl1c) * vf.add_const(value=0.0))),
            PRE_scl_limPIUel_hysteresisMin_y_Scl1c: scl_limPIUel_hysteresisMin_pre_y_start_Scl1c,
            PRE_scl_limPIUel_hysteresisMax_y_Scl1c: scl_limPIUel_hysteresisMax_pre_y_start_Scl1c,
            scl_limPIUel_hysteresisMax_y_Scl1c: (sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_hysteresisMax_uHigh_Scl1c) - vf.add_const(value=1e-06))) + sym.heaviside(((scl_limPIUel_add_y_Scl1c - scl_limPIUel_hysteresisMax_uLow_Scl1c) + vf.add_const(value=1e-06)))),
            PRE_scl_limPIOel_hysteresisMin_y_Scl1c: scl_limPIOel_hysteresisMin_pre_y_start_Scl1c,
            PRE_scl_limPIOel_hysteresisMax_y_Scl1c: scl_limPIOel_hysteresisMax_pre_y_start_Scl1c,
            scl_limPIOel_hysteresisMax_y_Scl1c: (sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_hysteresisMax_uHigh_Scl1c) - vf.add_const(value=1e-06))) + sym.heaviside(((scl_limPIOel_add_y_Scl1c - scl_limPIOel_hysteresisMax_uLow_Scl1c) + vf.add_const(value=1e-06)))),
        },
        event_dict=event_dict,
        in_vars=inputs,
        out_vars=[
        ],
        external_mapping=external_mapping,
        api_obj_mapping=api_obj_mapping,
        diff_vars=[
            d_scl_firstOrder_y_Scl1c,
            d_scl_firstOrder1_y_Scl1c,
            d_scl_firstOrder2_y_Scl1c,
            d_scl_limPIOel_integrator_y_Scl1c,
            d_scl_limPIUel_integrator_y_Scl1c,
        ],
        name=template_name,
    )
    templ.comment = 'Generator stator current limiter SCL1C'
    return templ
