# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Scl2c'.

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

def build_scl2c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
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
        template_name: str = 'Scl2c'
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
    scl_firstOrder_y_Scl2c: Var = vf.add_var(name='scl.firstOrder.y_Scl2c')
    scl_firstOrder1_y_Scl2c: Var = vf.add_var(name='scl.firstOrder1.y_Scl2c')
    scl_firstOrder2_y_Scl2c: Var = vf.add_var(name='scl.firstOrder2.y_Scl2c')
    scl_firstOrder3_y_Scl2c: Var = vf.add_var(name='scl.firstOrder3.y_Scl2c')
    scl_firstOrder4_y_Scl2c: Var = vf.add_var(name='scl.firstOrder4.y_Scl2c')
    scl_firstOrder5_y_Scl2c: Var = vf.add_var(name='scl.firstOrder5.y_Scl2c')
    scl_pidOel_D_x_Scl2c: Var = vf.add_var(name='scl.pidOel.D.x_Scl2c')
    scl_limitedLeadLag2_firstOrder_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.firstOrder.y_Scl2c')
    scl_limitedLeadLag3_firstOrder_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.firstOrder.y_Scl2c')
    scl_pidOel_I_y_Scl2c: Var = vf.add_var(name='scl.pidOel.I.y_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.y_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.y_Scl2c')
    scl_firstOrder7_y_Scl2c: Var = vf.add_var(name='scl.firstOrder7.y_Scl2c')
    scl_firstOrder6_y_Scl2c: Var = vf.add_var(name='scl.firstOrder6.y_Scl2c')
    scl_pidUel_D_x_Scl2c: Var = vf.add_var(name='scl.pidUel.D.x_Scl2c')
    scl_limitedLeadLag_firstOrder_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.firstOrder.y_Scl2c')
    scl_limitedLeadLag1_firstOrder_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.firstOrder.y_Scl2c')
    scl_pidUel_I_y_Scl2c: Var = vf.add_var(name='scl.pidUel.I.y_Scl2c')

    # Algebraic variables
    scl_pythagoras_y2_Scl2c: Var = vf.add_var(name='scl.pythagoras.y2_Scl2c')
    scl_pythagoras_y_Scl2c: Var = vf.add_var(name='scl.pythagoras.y_Scl2c')
    scl_pythagoras1_y2_Scl2c: Var = vf.add_var(name='scl.pythagoras1.y2_Scl2c')
    scl_pythagoras1_y_Scl2c: Var = vf.add_var(name='scl.pythagoras1.y_Scl2c')
    whenCondition2_Scl2c: Var = vf.add_var(name='$whenCondition2_Scl2c')
    scl_sclOelActivation_timer_y_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.timer.y_Scl2c')
    scl_sclOelActivation_timer_u_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.timer.u_Scl2c')
    whenCondition1_Scl2c: Var = vf.add_var(name='$whenCondition1_Scl2c')
    scl_sclOelActivation_timer1_y_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.timer1.y_Scl2c')
    scl_sclOelActivation_timer1_u_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.timer1.u_Scl2c')
    scl_add_y_Scl2c: Var = vf.add_var(name='scl.add.y_Scl2c')
    scl_max1_u_1_Scl2c: Var = vf.add_var(name='scl.max1.u[1]_Scl2c')
    scl_max1_u_3_Scl2c: Var = vf.add_var(name='scl.max1.u[3]_Scl2c')
    scl_sclReferenceCurrent_tErr_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.tErr_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_u_1_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.u[1]_Scl2c')
    scl_sclReferenceCurrent_lessEqualThreshold1_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.lessEqualThreshold1.y_Scl2c')
    scl_sclOelActivation_IOelBiasPu_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.IOelBiasPu_Scl2c')
    scl_max1_u_2_Scl2c: Var = vf.add_var(name='scl.max1.u[2]_Scl2c')
    scl_max1_yMin_Scl2c: Var = vf.add_var(name='scl.max1.yMin_Scl2c')
    scl_pidOel_controlError_Scl2c: Var = vf.add_var(name='scl.pidOel.controlError_Scl2c')
    scl_pidOel_addP_y_Scl2c: Var = vf.add_var(name='scl.pidOel.addP.y_Scl2c')
    scl_pidOel_P_y_Scl2c: Var = vf.add_var(name='scl.pidOel.P.y_Scl2c')
    scl_pidOel_addD_y_Scl2c: Var = vf.add_var(name='scl.pidOel.addD.y_Scl2c')
    scl_pidOel_D_y_Scl2c: Var = vf.add_var(name='scl.pidOel.D.y_Scl2c')
    scl_pidOel_addPID_y_Scl2c: Var = vf.add_var(name='scl.pidOel.addPID.y_Scl2c')
    scl_pidOel_gainPID_y_Scl2c: Var = vf.add_var(name='scl.pidOel.gainPID.y_Scl2c')
    scl_pidOel_limiter_u_Scl2c: Var = vf.add_var(name='scl.pidOel.limiter.u_Scl2c')
    scl_pidOel_y_Scl2c: Var = vf.add_var(name='scl.pidOel.y_Scl2c')
    scl_limitedLeadLag2_feedback_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.feedback.y_Scl2c')
    scl_limitedLeadLag2_gain_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.gain.y_Scl2c')
    scl_limitedLeadLag2_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.y_Scl2c')
    scl_limitedLeadLag3_feedback_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.feedback.y_Scl2c')
    scl_limitedLeadLag3_gain_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.gain.y_Scl2c')
    scl_USclOelPu_Scl2c: Var = vf.add_var(name='scl.USclOelPu_Scl2c')
    scl_pidOel_addSat_y_Scl2c: Var = vf.add_var(name='scl.pidOel.addSat.y_Scl2c')
    scl_pidOel_gainTrack_y_Scl2c: Var = vf.add_var(name='scl.pidOel.gainTrack.y_Scl2c')
    scl_pidOel_addI_y_Scl2c: Var = vf.add_var(name='scl.pidOel.addI.y_Scl2c')
    scl_sclReferenceCurrent_gain_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.gain.y_Scl2c')
    scl_sclReferenceCurrent_power1_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.power1.y_Scl2c')
    scl_sclReferenceCurrent_feedback1_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.feedback1.y_Scl2c')
    scl_sclReferenceCurrent_gain1_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.gain1.y_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_expr_2_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.expr[2]_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_expr_1_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.expr[1]_Scl2c')
    scl_sclReferenceCurrent_power_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.power.y_Scl2c')
    scl_sclReferenceCurrent_feedback2_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.feedback2.y_Scl2c')
    scl_sclReferenceCurrent_gain2_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.gain2.y_Scl2c')
    scl_sclReferenceCurrent_limiter_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limiter.y_Scl2c')
    scl_sclReferenceCurrent_lessEqualThreshold_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.lessEqualThreshold.y_Scl2c')
    scl_sclReferenceCurrent_switch_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.switch.y_Scl2c')
    scl_sclReferenceCurrent_add_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.add.y_Scl2c')
    scl_sclReferenceCurrent_gain3_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.gain3.y_Scl2c')
    scl_sclReferenceCurrent_feedback_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.feedback.y_Scl2c')
    scl_sclReferenceCurrent_lessThreshold_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.lessThreshold.y_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_u_2_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.u[2]_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_firstActiveIndex_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.firstActiveIndex_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_y_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.y_Scl2c')
    scl_sclReferenceCurrent_IRefPu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.IRefPu_Scl2c')
    scl_limiter_y_Scl2c: Var = vf.add_var(name='scl.limiter.y_Scl2c')
    whenCondition4_Scl2c: Var = vf.add_var(name='$whenCondition4_Scl2c')
    scl_sclUelActivation_timer_y_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.timer.y_Scl2c')
    scl_sclUelActivation_timer_u_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.timer.u_Scl2c')
    whenCondition3_Scl2c: Var = vf.add_var(name='$whenCondition3_Scl2c')
    scl_sclUelActivation_timer1_y_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.timer1.y_Scl2c')
    scl_sclUelActivation_timer1_u_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.timer1.u_Scl2c')
    scl_sclUelActivation_IUelBiasPu_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.IUelBiasPu_Scl2c')
    scl_add3_y_Scl2c: Var = vf.add_var(name='scl.add3.y_Scl2c')
    scl_pidUel_controlError_Scl2c: Var = vf.add_var(name='scl.pidUel.controlError_Scl2c')
    scl_pidUel_addP_y_Scl2c: Var = vf.add_var(name='scl.pidUel.addP.y_Scl2c')
    scl_pidUel_P_y_Scl2c: Var = vf.add_var(name='scl.pidUel.P.y_Scl2c')
    scl_pidUel_addD_y_Scl2c: Var = vf.add_var(name='scl.pidUel.addD.y_Scl2c')
    scl_pidUel_D_y_Scl2c: Var = vf.add_var(name='scl.pidUel.D.y_Scl2c')
    scl_pidUel_addPID_y_Scl2c: Var = vf.add_var(name='scl.pidUel.addPID.y_Scl2c')
    scl_pidUel_gainPID_y_Scl2c: Var = vf.add_var(name='scl.pidUel.gainPID.y_Scl2c')
    scl_pidUel_limiter_u_Scl2c: Var = vf.add_var(name='scl.pidUel.limiter.u_Scl2c')
    scl_pidUel_y_Scl2c: Var = vf.add_var(name='scl.pidUel.y_Scl2c')
    scl_limitedLeadLag_feedback_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.feedback.y_Scl2c')
    scl_limitedLeadLag_gain_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.gain.y_Scl2c')
    scl_limitedLeadLag_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.y_Scl2c')
    scl_limitedLeadLag1_feedback_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.feedback.y_Scl2c')
    scl_limitedLeadLag1_gain_y_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.gain.y_Scl2c')
    scl_USclUelPu_Scl2c: Var = vf.add_var(name='scl.USclUelPu_Scl2c')
    scl_pidUel_addSat_y_Scl2c: Var = vf.add_var(name='scl.pidUel.addSat.y_Scl2c')
    scl_pidUel_gainTrack_y_Scl2c: Var = vf.add_var(name='scl.pidUel.gainTrack.y_Scl2c')
    scl_pidUel_addI_y_Scl2c: Var = vf.add_var(name='scl.pidUel.addI.y_Scl2c')
    scl_sclOelActivation_timer_entryTime_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.timer.entryTime_Scl2c')
    scl_sclOelActivation_timer1_entryTime_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.timer1.entryTime_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_expr_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.expr_Scl2c')
    scl_sclUelActivation_timer_entryTime_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.timer.entryTime_Scl2c')
    scl_sclUelActivation_timer1_entryTime_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.timer1.entryTime_Scl2c')
    scl_PGenPu_Scl2c: Var = vf.add_var(name='scl.PGenPu_Scl2c')
    scl_QGenPu_Scl2c: Var = vf.add_var(name='scl.QGenPu_Scl2c')
    scl_itPu_im_Scl2c: Var = vf.add_var(name='scl.itPu.im_Scl2c')
    scl_itPu_re_Scl2c: Var = vf.add_var(name='scl.itPu.re_Scl2c')
    scl_utPu_im_Scl2c: Var = vf.add_var(name='scl.utPu.im_Scl2c')
    scl_utPu_re_Scl2c: Var = vf.add_var(name='scl.utPu.re_Scl2c')
    scl_limitedLeadLag_limiter_simplifiedExpr_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.limiter.simplifiedExpr_Scl2c')
    scl_limitedLeadLag1_limiter_simplifiedExpr_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.limiter.simplifiedExpr_Scl2c')
    scl_pythagoras_valid_Scl2c: Var = vf.add_var(name='scl.pythagoras.valid_Scl2c')
    scl_pythagoras1_valid_Scl2c: Var = vf.add_var(name='scl.pythagoras1.valid_Scl2c')
    scl_pidUel_I_local_reset_Scl2c: Var = vf.add_var(name='scl.pidUel.I.local_reset_Scl2c')
    scl_pidUel_I_local_set_Scl2c: Var = vf.add_var(name='scl.pidUel.I.local_set_Scl2c')
    scl_pidOel_I_local_reset_Scl2c: Var = vf.add_var(name='scl.pidOel.I.local_reset_Scl2c')
    scl_pidOel_I_local_set_Scl2c: Var = vf.add_var(name='scl.pidOel.I.local_set_Scl2c')
    scl_limitedLeadLag2_limiter_simplifiedExpr_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.limiter.simplifiedExpr_Scl2c')
    scl_limitedLeadLag3_limiter_simplifiedExpr_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.limiter.simplifiedExpr_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_local_reset_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.local_reset_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_local_set_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.local_set_Scl2c')
    scl_sclReferenceCurrent_limiter_simplifiedExpr_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limiter.simplifiedExpr_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_local_reset_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.local_reset_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_local_set_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.local_set_Scl2c')
    scl_limiter_simplifiedExpr_Scl2c: Var = vf.add_var(name='scl.limiter.simplifiedExpr_Scl2c')
    scl_division_y_Scl2c: Var = vf.add_var(name='scl.division.y_Scl2c')
    scl_complexToPolar1_phi_Scl2c: Var = vf.add_var(name='scl.complexToPolar1.phi_Scl2c')
    scl_complexToPolar1_len_Scl2c: Var = vf.add_var(name='scl.complexToPolar1.len_Scl2c')
    scl_division1_y_Scl2c: Var = vf.add_var(name='scl.division1.y_Scl2c')
    scl_complexToPolar_phi_Scl2c: Var = vf.add_var(name='scl.complexToPolar.phi_Scl2c')
    scl_complexToPolar_len_Scl2c: Var = vf.add_var(name='scl.complexToPolar.len_Scl2c')
    scl_pidOel_u_m_Scl2c: Var = vf.add_var(name='scl.pidOel.u_m_Scl2c')
    scl_pidUel_u_m_Scl2c: Var = vf.add_var(name='scl.pidUel.u_m_Scl2c')
    START_scl_limitedLeadLag_firstOrder_y_Scl2c: Var = vf.add_var(name='$START.scl.limitedLeadLag.firstOrder.y_Scl2c')
    START_scl_limitedLeadLag1_firstOrder_y_Scl2c: Var = vf.add_var(name='$START.scl.limitedLeadLag1.firstOrder.y_Scl2c')
    START_scl_firstOrder_y_Scl2c: Var = vf.add_var(name='$START.scl.firstOrder.y_Scl2c')
    START_scl_firstOrder1_y_Scl2c: Var = vf.add_var(name='$START.scl.firstOrder1.y_Scl2c')
    START_scl_firstOrder2_y_Scl2c: Var = vf.add_var(name='$START.scl.firstOrder2.y_Scl2c')
    START_scl_firstOrder3_y_Scl2c: Var = vf.add_var(name='$START.scl.firstOrder3.y_Scl2c')
    START_scl_firstOrder4_y_Scl2c: Var = vf.add_var(name='$START.scl.firstOrder4.y_Scl2c')
    START_scl_pidUel_D_x_Scl2c: Var = vf.add_var(name='$START.scl.pidUel.D.x_Scl2c')
    START_scl_pidOel_D_x_Scl2c: Var = vf.add_var(name='$START.scl.pidOel.D.x_Scl2c')
    START_scl_limitedLeadLag2_firstOrder_y_Scl2c: Var = vf.add_var(name='$START.scl.limitedLeadLag2.firstOrder.y_Scl2c')
    START_scl_limitedLeadLag3_firstOrder_y_Scl2c: Var = vf.add_var(name='$START.scl.limitedLeadLag3.firstOrder.y_Scl2c')
    START_scl_firstOrder5_y_Scl2c: Var = vf.add_var(name='$START.scl.firstOrder5.y_Scl2c')
    START_scl_firstOrder6_y_Scl2c: Var = vf.add_var(name='$START.scl.firstOrder6.y_Scl2c')
    START_scl_firstOrder7_y_Scl2c: Var = vf.add_var(name='$START.scl.firstOrder7.y_Scl2c')
    PRE_scl_sclOelActivation_timer1_entryTime_Scl2c: Var = vf.add_var(name='$PRE.scl.sclOelActivation.timer1.entryTime_Scl2c')
    PRE_scl_sclOelActivation_timer_entryTime_Scl2c: Var = vf.add_var(name='$PRE.scl.sclOelActivation.timer.entryTime_Scl2c')
    PRE_scl_sclUelActivation_timer1_entryTime_Scl2c: Var = vf.add_var(name='$PRE.scl.sclUelActivation.timer1.entryTime_Scl2c')
    PRE_scl_sclUelActivation_timer_entryTime_Scl2c: Var = vf.add_var(name='$PRE.scl.sclUelActivation.timer.entryTime_Scl2c')
    PRE_scl_sclReferenceCurrent_multiSwitch1_u_2_Scl2c: Var = vf.add_var(name='$PRE.scl.sclReferenceCurrent.multiSwitch1.u[2]_Scl2c')
    PRE_scl_sclReferenceCurrent_multiSwitch1_u_1_Scl2c: Var = vf.add_var(name='$PRE.scl.sclReferenceCurrent.multiSwitch1.u[1]_Scl2c')

    # Differential variables
    d_scl_firstOrder_y_Scl2c: Var = vf.add_diff_var(name='d_scl.firstOrder.y_Scl2c', base_var=scl_firstOrder_y_Scl2c)
    d_scl_firstOrder1_y_Scl2c: Var = vf.add_diff_var(name='d_scl.firstOrder1.y_Scl2c', base_var=scl_firstOrder1_y_Scl2c)
    d_scl_firstOrder2_y_Scl2c: Var = vf.add_diff_var(name='d_scl.firstOrder2.y_Scl2c', base_var=scl_firstOrder2_y_Scl2c)
    d_scl_firstOrder3_y_Scl2c: Var = vf.add_diff_var(name='d_scl.firstOrder3.y_Scl2c', base_var=scl_firstOrder3_y_Scl2c)
    d_scl_firstOrder4_y_Scl2c: Var = vf.add_diff_var(name='d_scl.firstOrder4.y_Scl2c', base_var=scl_firstOrder4_y_Scl2c)
    d_scl_firstOrder5_y_Scl2c: Var = vf.add_diff_var(name='d_scl.firstOrder5.y_Scl2c', base_var=scl_firstOrder5_y_Scl2c)
    d_scl_pidOel_D_x_Scl2c: Var = vf.add_diff_var(name='d_scl.pidOel.D.x_Scl2c', base_var=scl_pidOel_D_x_Scl2c)
    d_scl_limitedLeadLag2_firstOrder_y_Scl2c: Var = vf.add_diff_var(name='d_scl.limitedLeadLag2.firstOrder.y_Scl2c', base_var=scl_limitedLeadLag2_firstOrder_y_Scl2c)
    d_scl_limitedLeadLag3_firstOrder_y_Scl2c: Var = vf.add_diff_var(name='d_scl.limitedLeadLag3.firstOrder.y_Scl2c', base_var=scl_limitedLeadLag3_firstOrder_y_Scl2c)
    d_scl_pidOel_I_y_Scl2c: Var = vf.add_diff_var(name='d_scl.pidOel.I.y_Scl2c', base_var=scl_pidOel_I_y_Scl2c)
    d_scl_sclReferenceCurrent_limIntegrator_y_Scl2c: Var = vf.add_diff_var(name='d_scl.sclReferenceCurrent.limIntegrator.y_Scl2c', base_var=scl_sclReferenceCurrent_limIntegrator_y_Scl2c)
    d_scl_sclReferenceCurrent_limIntegrator1_y_Scl2c: Var = vf.add_diff_var(name='d_scl.sclReferenceCurrent.limIntegrator1.y_Scl2c', base_var=scl_sclReferenceCurrent_limIntegrator1_y_Scl2c)
    d_scl_firstOrder7_y_Scl2c: Var = vf.add_diff_var(name='d_scl.firstOrder7.y_Scl2c', base_var=scl_firstOrder7_y_Scl2c)
    d_scl_firstOrder6_y_Scl2c: Var = vf.add_diff_var(name='d_scl.firstOrder6.y_Scl2c', base_var=scl_firstOrder6_y_Scl2c)
    d_scl_pidUel_D_x_Scl2c: Var = vf.add_diff_var(name='d_scl.pidUel.D.x_Scl2c', base_var=scl_pidUel_D_x_Scl2c)
    d_scl_limitedLeadLag_firstOrder_y_Scl2c: Var = vf.add_diff_var(name='d_scl.limitedLeadLag.firstOrder.y_Scl2c', base_var=scl_limitedLeadLag_firstOrder_y_Scl2c)
    d_scl_limitedLeadLag1_firstOrder_y_Scl2c: Var = vf.add_diff_var(name='d_scl.limitedLeadLag1.firstOrder.y_Scl2c', base_var=scl_limitedLeadLag1_firstOrder_y_Scl2c)
    d_scl_pidUel_I_y_Scl2c: Var = vf.add_diff_var(name='d_scl.pidUel.I.y_Scl2c', base_var=scl_pidUel_I_y_Scl2c)

    # Internal variables
    time_Scl2c: Var = vf.add_var(name='time_Scl2c')

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________

    # Runtime parameters and event variables
    scl_firstOrder_T_Scl2c: Var = vf.add_var(name='scl.firstOrder.T_Scl2c')
    scl_firstOrder_k_Scl2c: Var = vf.add_var(name='scl.firstOrder.k_Scl2c')
    scl_firstOrder1_T_Scl2c: Var = vf.add_var(name='scl.firstOrder1.T_Scl2c')
    scl_firstOrder1_k_Scl2c: Var = vf.add_var(name='scl.firstOrder1.k_Scl2c')
    scl_firstOrder2_k_Scl2c: Var = vf.add_var(name='scl.firstOrder2.k_Scl2c')
    scl_firstOrder2_T_Scl2c: Var = vf.add_var(name='scl.firstOrder2.T_Scl2c')
    scl_firstOrder3_T_Scl2c: Var = vf.add_var(name='scl.firstOrder3.T_Scl2c')
    scl_firstOrder3_k_Scl2c: Var = vf.add_var(name='scl.firstOrder3.k_Scl2c')
    scl_firstOrder4_k_Scl2c: Var = vf.add_var(name='scl.firstOrder4.k_Scl2c')
    scl_firstOrder4_T_Scl2c: Var = vf.add_var(name='scl.firstOrder4.T_Scl2c')
    scl_firstOrder5_k_Scl2c: Var = vf.add_var(name='scl.firstOrder5.k_Scl2c')
    scl_firstOrder5_T_Scl2c: Var = vf.add_var(name='scl.firstOrder5.T_Scl2c')
    scl_pidOel_D_T_Scl2c: Var = vf.add_var(name='scl.pidOel.D.T_Scl2c')
    scl_pidOel_D_zeroGain_Scl2c: Var = vf.add_var(name='scl.pidOel.D.zeroGain_Scl2c')
    scl_limitedLeadLag2_firstOrder_T_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.firstOrder.T_Scl2c')
    scl_limitedLeadLag2_firstOrder_k_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.firstOrder.k_Scl2c')
    scl_limitedLeadLag3_firstOrder_T_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.firstOrder.T_Scl2c')
    scl_limitedLeadLag3_firstOrder_k_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.firstOrder.k_Scl2c')
    scl_pidOel_I_k_Scl2c: Var = vf.add_var(name='scl.pidOel.I.k_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.outMin_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_outMax_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.outMax_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.k_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_outMax_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.outMax_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.k_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.outMin_Scl2c')
    scl_firstOrder7_T_Scl2c: Var = vf.add_var(name='scl.firstOrder7.T_Scl2c')
    scl_firstOrder7_k_Scl2c: Var = vf.add_var(name='scl.firstOrder7.k_Scl2c')
    scl_firstOrder6_T_Scl2c: Var = vf.add_var(name='scl.firstOrder6.T_Scl2c')
    scl_firstOrder6_k_Scl2c: Var = vf.add_var(name='scl.firstOrder6.k_Scl2c')
    scl_pidUel_D_T_Scl2c: Var = vf.add_var(name='scl.pidUel.D.T_Scl2c')
    scl_pidUel_D_zeroGain_Scl2c: Var = vf.add_var(name='scl.pidUel.D.zeroGain_Scl2c')
    scl_limitedLeadLag_firstOrder_T_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.firstOrder.T_Scl2c')
    scl_limitedLeadLag_firstOrder_k_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.firstOrder.k_Scl2c')
    scl_limitedLeadLag1_firstOrder_T_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.firstOrder.T_Scl2c')
    scl_limitedLeadLag1_firstOrder_k_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.firstOrder.k_Scl2c')
    scl_pidUel_I_k_Scl2c: Var = vf.add_var(name='scl.pidUel.I.k_Scl2c')
    scl_sclOelActivation_IThOffPu_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.IThOffPu_Scl2c')
    scl_add_k1_Scl2c: Var = vf.add_var(name='scl.add.k1_Scl2c')
    scl_const_k_Scl2c: Var = vf.add_var(name='scl.const.k_Scl2c')
    scl_add_k2_Scl2c: Var = vf.add_var(name='scl.add.k2_Scl2c')
    scl_add1_k1_Scl2c: Var = vf.add_var(name='scl.add1.k1_Scl2c')
    scl_add1_k2_Scl2c: Var = vf.add_var(name='scl.add1.k2_Scl2c')
    scl_const1_k_Scl2c: Var = vf.add_var(name='scl.const1.k_Scl2c')
    scl_add2_k1_Scl2c: Var = vf.add_var(name='scl.add2.k1_Scl2c')
    scl_const2_k_Scl2c: Var = vf.add_var(name='scl.const2.k_Scl2c')
    scl_add2_k2_Scl2c: Var = vf.add_var(name='scl.add2.k2_Scl2c')
    scl_sclReferenceCurrent_const3_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.const3.k_Scl2c')
    scl_sclReferenceCurrent_greaterEqualThreshold_threshold_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.greaterEqualThreshold.threshold_Scl2c')
    scl_sclReferenceCurrent_lessEqualThreshold1_threshold_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.lessEqualThreshold1.threshold_Scl2c')
    scl_sclOelActivation_VtResetPu_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.VtResetPu_Scl2c')
    scl_sclOelActivation_tOff_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.tOff_Scl2c')
    scl_sclOelActivation_IInstPu_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.IInstPu_Scl2c')
    scl_sclOelActivation_IResetPu_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.IResetPu_Scl2c')
    scl_sclOelActivation_VtMinPu_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.VtMinPu_Scl2c')
    scl_sclOelActivation_tEnOel_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.tEnOel_Scl2c')
    scl_add31_k2_Scl2c: Var = vf.add_var(name='scl.add31.k2_Scl2c')
    scl_add31_k3_Scl2c: Var = vf.add_var(name='scl.add31.k3_Scl2c')
    scl_add31_k1_Scl2c: Var = vf.add_var(name='scl.add31.k1_Scl2c')
    scl_pidOel_addP_k1_Scl2c: Var = vf.add_var(name='scl.pidOel.addP.k1_Scl2c')
    scl_pidOel_P_k_Scl2c: Var = vf.add_var(name='scl.pidOel.P.k_Scl2c')
    scl_pidOel_addD_k1_Scl2c: Var = vf.add_var(name='scl.pidOel.addD.k1_Scl2c')
    scl_pidOel_D_k_Scl2c: Var = vf.add_var(name='scl.pidOel.D.k_Scl2c')
    scl_pidOel_addPID_k2_Scl2c: Var = vf.add_var(name='scl.pidOel.addPID.k2_Scl2c')
    scl_pidOel_addPID_k1_Scl2c: Var = vf.add_var(name='scl.pidOel.addPID.k1_Scl2c')
    scl_pidOel_addPID_k3_Scl2c: Var = vf.add_var(name='scl.pidOel.addPID.k3_Scl2c')
    scl_pidOel_gainPID_k_Scl2c: Var = vf.add_var(name='scl.pidOel.gainPID.k_Scl2c')
    scl_pidOel_FFzero_k_Scl2c: Var = vf.add_var(name='scl.pidOel.FFzero.k_Scl2c')
    scl_pidOel_addFF_k2_Scl2c: Var = vf.add_var(name='scl.pidOel.addFF.k2_Scl2c')
    scl_pidOel_addFF_k1_Scl2c: Var = vf.add_var(name='scl.pidOel.addFF.k1_Scl2c')
    scl_pidOel_limiter_uMax_Scl2c: Var = vf.add_var(name='scl.pidOel.limiter.uMax_Scl2c')
    scl_pidOel_limiter_uMin_Scl2c: Var = vf.add_var(name='scl.pidOel.limiter.uMin_Scl2c')
    scl_limitedLeadLag2_gain_k_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.gain.k_Scl2c')
    scl_limitedLeadLag2_limiter_uMin_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.limiter.uMin_Scl2c')
    scl_limitedLeadLag2_limiter_uMax_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.limiter.uMax_Scl2c')
    scl_limitedLeadLag3_gain_k_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.gain.k_Scl2c')
    scl_limitedLeadLag3_limiter_uMin_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.limiter.uMin_Scl2c')
    scl_limitedLeadLag3_limiter_uMax_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.limiter.uMax_Scl2c')
    scl_pidOel_addSat_k2_Scl2c: Var = vf.add_var(name='scl.pidOel.addSat.k2_Scl2c')
    scl_pidOel_addSat_k1_Scl2c: Var = vf.add_var(name='scl.pidOel.addSat.k1_Scl2c')
    scl_pidOel_gainTrack_k_Scl2c: Var = vf.add_var(name='scl.pidOel.gainTrack.k_Scl2c')
    scl_pidOel_addI_k1_Scl2c: Var = vf.add_var(name='scl.pidOel.addI.k1_Scl2c')
    scl_pidOel_addI_k3_Scl2c: Var = vf.add_var(name='scl.pidOel.addI.k3_Scl2c')
    scl_sclReferenceCurrent_gain_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.gain.k_Scl2c')
    scl_sclReferenceCurrent_power1_N_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.power1.N_Scl2c')
    scl_sclReferenceCurrent_const_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.const.k_Scl2c')
    scl_sclReferenceCurrent_gain1_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.gain1.k_Scl2c')
    scl_sclReferenceCurrent_const4_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.const4.k_Scl2c')
    scl_sclReferenceCurrent_booleanConstant_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.booleanConstant.k_Scl2c')
    scl_sclReferenceCurrent_const5_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.const5.k_Scl2c')
    scl_sclReferenceCurrent_power_N_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.power.N_Scl2c')
    scl_sclReferenceCurrent_gain2_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.gain2.k_Scl2c')
    scl_sclReferenceCurrent_limiter_uMin_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limiter.uMin_Scl2c')
    scl_sclReferenceCurrent_limiter_uMax_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limiter.uMax_Scl2c')
    scl_sclReferenceCurrent_lessEqualThreshold_threshold_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.lessEqualThreshold.threshold_Scl2c')
    scl_sclReferenceCurrent_const2_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.const2.k_Scl2c')
    scl_sclReferenceCurrent_const1_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.const1.k_Scl2c')
    scl_sclReferenceCurrent_add_k1_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.add.k1_Scl2c')
    scl_sclReferenceCurrent_add_k2_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.add.k2_Scl2c')
    scl_sclReferenceCurrent_gain3_k_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.gain3.k_Scl2c')
    scl_sclReferenceCurrent_lessThreshold_threshold_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.lessThreshold.threshold_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_y_default_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.y_default_Scl2c')
    scl_sclReferenceCurrent_KPRef_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.KPRef_Scl2c')
    scl_limiter_uMax_Scl2c: Var = vf.add_var(name='scl.limiter.uMax_Scl2c')
    scl_limiter_uMin_Scl2c: Var = vf.add_var(name='scl.limiter.uMin_Scl2c')
    scl_sclUelActivation_IThOffPu_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.IThOffPu_Scl2c')
    scl_sclUelActivation_IResetPu_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.IResetPu_Scl2c')
    scl_sclUelActivation_tEnUel_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.tEnUel_Scl2c')
    scl_sclUelActivation_tOff_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.tOff_Scl2c')
    scl_sclUelActivation_IInstUelPu_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.IInstUelPu_Scl2c')
    scl_add3_k1_Scl2c: Var = vf.add_var(name='scl.add3.k1_Scl2c')
    scl_add3_k3_Scl2c: Var = vf.add_var(name='scl.add3.k3_Scl2c')
    scl_add3_k2_Scl2c: Var = vf.add_var(name='scl.add3.k2_Scl2c')
    scl_pidUel_addP_k1_Scl2c: Var = vf.add_var(name='scl.pidUel.addP.k1_Scl2c')
    scl_pidUel_P_k_Scl2c: Var = vf.add_var(name='scl.pidUel.P.k_Scl2c')
    scl_pidUel_addD_k1_Scl2c: Var = vf.add_var(name='scl.pidUel.addD.k1_Scl2c')
    scl_pidUel_D_k_Scl2c: Var = vf.add_var(name='scl.pidUel.D.k_Scl2c')
    scl_pidUel_addPID_k3_Scl2c: Var = vf.add_var(name='scl.pidUel.addPID.k3_Scl2c')
    scl_pidUel_addPID_k2_Scl2c: Var = vf.add_var(name='scl.pidUel.addPID.k2_Scl2c')
    scl_pidUel_addPID_k1_Scl2c: Var = vf.add_var(name='scl.pidUel.addPID.k1_Scl2c')
    scl_pidUel_gainPID_k_Scl2c: Var = vf.add_var(name='scl.pidUel.gainPID.k_Scl2c')
    scl_pidUel_addFF_k1_Scl2c: Var = vf.add_var(name='scl.pidUel.addFF.k1_Scl2c')
    scl_pidUel_FFzero_k_Scl2c: Var = vf.add_var(name='scl.pidUel.FFzero.k_Scl2c')
    scl_pidUel_addFF_k2_Scl2c: Var = vf.add_var(name='scl.pidUel.addFF.k2_Scl2c')
    scl_pidUel_limiter_uMin_Scl2c: Var = vf.add_var(name='scl.pidUel.limiter.uMin_Scl2c')
    scl_pidUel_limiter_uMax_Scl2c: Var = vf.add_var(name='scl.pidUel.limiter.uMax_Scl2c')
    scl_limitedLeadLag_gain_k_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.gain.k_Scl2c')
    scl_limitedLeadLag_limiter_uMin_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.limiter.uMin_Scl2c')
    scl_limitedLeadLag_limiter_uMax_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.limiter.uMax_Scl2c')
    scl_limitedLeadLag1_gain_k_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.gain.k_Scl2c')
    scl_limitedLeadLag1_limiter_uMax_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.limiter.uMax_Scl2c')
    scl_limitedLeadLag1_limiter_uMin_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.limiter.uMin_Scl2c')
    scl_pidUel_addSat_k2_Scl2c: Var = vf.add_var(name='scl.pidUel.addSat.k2_Scl2c')
    scl_pidUel_addSat_k1_Scl2c: Var = vf.add_var(name='scl.pidUel.addSat.k1_Scl2c')
    scl_pidUel_gainTrack_k_Scl2c: Var = vf.add_var(name='scl.pidUel.gainTrack.k_Scl2c')
    scl_pidUel_addI_k1_Scl2c: Var = vf.add_var(name='scl.pidUel.addI.k1_Scl2c')
    scl_pidUel_addI_k3_Scl2c: Var = vf.add_var(name='scl.pidUel.addI.k3_Scl2c')
    scl_pidOel_I_y_start_Scl2c: Var = vf.add_var(name='scl.pidOel.I.y_start_Scl2c')
    scl_pidUel_I_y_start_Scl2c: Var = vf.add_var(name='scl.pidUel.I.y_start_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_y_start_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.y_start_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_y_start_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.y_start_Scl2c')
    scl_limitedLeadLag3_Y0_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.Y0_Scl2c')
    scl_limitedLeadLag1_Y0_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.Y0_Scl2c')
    scl_limitedLeadLag_Y0_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.Y0_Scl2c')
    scl_limitedLeadLag2_Y0_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.Y0_Scl2c')
    scl_sclUelActivation_IUelRef0Pu_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.IUelRef0Pu_Scl2c')
    scl_sclOelActivation_IOelRef0Pu_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.IOelRef0Pu_Scl2c')
    scl_sclReferenceCurrent_IRef0Pu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.IRef0Pu_Scl2c')
    scl_sclReferenceCurrent_tErr0_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.tErr0_Scl2c')
    scl_C1_Scl2c: Var = vf.add_var(name='scl.C1_Scl2c')
    scl_C2_Scl2c: Var = vf.add_var(name='scl.C2_Scl2c')
    scl_FixedRd_Scl2c: Var = vf.add_var(name='scl.FixedRd_Scl2c')
    scl_FixedRu_Scl2c: Var = vf.add_var(name='scl.FixedRu_Scl2c')
    scl_IInstPu_Scl2c: Var = vf.add_var(name='scl.IInstPu_Scl2c')
    scl_IInstUelPu_Scl2c: Var = vf.add_var(name='scl.IInstUelPu_Scl2c')
    scl_ILimPu_Scl2c: Var = vf.add_var(name='scl.ILimPu_Scl2c')
    scl_IRef0Pu_Scl2c: Var = vf.add_var(name='scl.IRef0Pu_Scl2c')
    scl_PGen0Pu_Scl2c: Var = vf.add_var(name='scl.PGen0Pu_Scl2c')
    scl_ut0Pu_re_Scl2c: Var = vf.add_var(name='scl.ut0Pu.re_Scl2c')
    scl_ut0Pu_im_Scl2c: Var = vf.add_var(name='scl.ut0Pu.im_Scl2c')
    scl_QGen0Pu_Scl2c: Var = vf.add_var(name='scl.QGen0Pu_Scl2c')
    scl_IResetPu_Scl2c: Var = vf.add_var(name='scl.IResetPu_Scl2c')
    scl_IScaled0Pu_Scl2c: Var = vf.add_var(name='scl.IScaled0Pu_Scl2c')
    scl_it0Pu_re_Scl2c: Var = vf.add_var(name='scl.it0Pu.re_Scl2c')
    scl_it0Pu_im_Scl2c: Var = vf.add_var(name='scl.it0Pu.im_Scl2c')
    scl_ITfPu_Scl2c: Var = vf.add_var(name='scl.ITfPu_Scl2c')
    scl_IThOffPu_Scl2c: Var = vf.add_var(name='scl.IThOffPu_Scl2c')
    scl_IqOelMinPu_Scl2c: Var = vf.add_var(name='scl.IqOelMinPu_Scl2c')
    scl_IqUelMaxPu_Scl2c: Var = vf.add_var(name='scl.IqUelMaxPu_Scl2c')
    scl_K1_Scl2c: Var = vf.add_var(name='scl.K1_Scl2c')
    scl_K2_Scl2c: Var = vf.add_var(name='scl.K2_Scl2c')
    scl_KFb_Scl2c: Var = vf.add_var(name='scl.KFb_Scl2c')
    scl_KIpOel_Scl2c: Var = vf.add_var(name='scl.KIpOel_Scl2c')
    scl_KIpUel_Scl2c: Var = vf.add_var(name='scl.KIpUel_Scl2c')
    scl_KIqOel_Scl2c: Var = vf.add_var(name='scl.KIqOel_Scl2c')
    scl_KIqUel_Scl2c: Var = vf.add_var(name='scl.KIqUel_Scl2c')
    scl_KPRef_Scl2c: Var = vf.add_var(name='scl.KPRef_Scl2c')
    scl_KdOel_Scl2c: Var = vf.add_var(name='scl.KdOel_Scl2c')
    scl_KdUel_Scl2c: Var = vf.add_var(name='scl.KdUel_Scl2c')
    scl_KiOel_Scl2c: Var = vf.add_var(name='scl.KiOel_Scl2c')
    scl_KiUel_Scl2c: Var = vf.add_var(name='scl.KiUel_Scl2c')
    scl_KpOel_Scl2c: Var = vf.add_var(name='scl.KpOel_Scl2c')
    scl_KpUel_Scl2c: Var = vf.add_var(name='scl.KpUel_Scl2c')
    scl_Krd_Scl2c: Var = vf.add_var(name='scl.Krd_Scl2c')
    scl_Kru_Scl2c: Var = vf.add_var(name='scl.Kru_Scl2c')
    scl_Kzru_Scl2c: Var = vf.add_var(name='scl.Kzru_Scl2c')
    scl_VInvMaxPu_Scl2c: Var = vf.add_var(name='scl.VInvMaxPu_Scl2c')
    scl_VInvMinPu_Scl2c: Var = vf.add_var(name='scl.VInvMinPu_Scl2c')
    scl_VOel1MaxPu_Scl2c: Var = vf.add_var(name='scl.VOel1MaxPu_Scl2c')
    scl_VOel1MinPu_Scl2c: Var = vf.add_var(name='scl.VOel1MinPu_Scl2c')
    scl_VOel2MaxPu_Scl2c: Var = vf.add_var(name='scl.VOel2MaxPu_Scl2c')
    scl_VOel2MinPu_Scl2c: Var = vf.add_var(name='scl.VOel2MinPu_Scl2c')
    scl_VOel3MaxPu_Scl2c: Var = vf.add_var(name='scl.VOel3MaxPu_Scl2c')
    scl_VOel3MinPu_Scl2c: Var = vf.add_var(name='scl.VOel3MinPu_Scl2c')
    scl_VUel1MaxPu_Scl2c: Var = vf.add_var(name='scl.VUel1MaxPu_Scl2c')
    scl_VUel1MinPu_Scl2c: Var = vf.add_var(name='scl.VUel1MinPu_Scl2c')
    scl_VUel2MaxPu_Scl2c: Var = vf.add_var(name='scl.VUel2MaxPu_Scl2c')
    scl_VUel2MinPu_Scl2c: Var = vf.add_var(name='scl.VUel2MinPu_Scl2c')
    scl_VUel3MaxPu_Scl2c: Var = vf.add_var(name='scl.VUel3MaxPu_Scl2c')
    scl_VUel3MinPu_Scl2c: Var = vf.add_var(name='scl.VUel3MinPu_Scl2c')
    scl_VtMinPu_Scl2c: Var = vf.add_var(name='scl.VtMinPu_Scl2c')
    scl_VtResetPu_Scl2c: Var = vf.add_var(name='scl.VtResetPu_Scl2c')
    scl_tIpUel_Scl2c: Var = vf.add_var(name='scl.tIpUel_Scl2c')
    scl_firstOrder_y_start_Scl2c: Var = vf.add_var(name='scl.firstOrder.y_start_Scl2c')
    scl_tIpOel_Scl2c: Var = vf.add_var(name='scl.tIpOel_Scl2c')
    scl_firstOrder1_y_start_Scl2c: Var = vf.add_var(name='scl.firstOrder1.y_start_Scl2c')
    scl_tIqOel_Scl2c: Var = vf.add_var(name='scl.tIqOel_Scl2c')
    scl_firstOrder2_y_start_Scl2c: Var = vf.add_var(name='scl.firstOrder2.y_start_Scl2c')
    scl_tIqUel_Scl2c: Var = vf.add_var(name='scl.tIqUel_Scl2c')
    scl_firstOrder3_y_start_Scl2c: Var = vf.add_var(name='scl.firstOrder3.y_start_Scl2c')
    scl_tVtScl_Scl2c: Var = vf.add_var(name='scl.tVtScl_Scl2c')
    scl_firstOrder4_y_start_Scl2c: Var = vf.add_var(name='scl.firstOrder4.y_start_Scl2c')
    scl_tItScl_Scl2c: Var = vf.add_var(name='scl.tItScl_Scl2c')
    scl_firstOrder5_y_start_Scl2c: Var = vf.add_var(name='scl.firstOrder5.y_start_Scl2c')
    scl_firstOrder6_y_start_Scl2c: Var = vf.add_var(name='scl.firstOrder6.y_start_Scl2c')
    scl_tAScl_Scl2c: Var = vf.add_var(name='scl.tAScl_Scl2c')
    scl_firstOrder7_y_start_Scl2c: Var = vf.add_var(name='scl.firstOrder7.y_start_Scl2c')
    scl_limitedLeadLag_K_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.K_Scl2c')
    scl_limitedLeadLag_YMax_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.YMax_Scl2c')
    scl_limitedLeadLag_YMin_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.YMin_Scl2c')
    scl_limitedLeadLag_t1_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.t1_Scl2c')
    scl_limitedLeadLag_t2_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.t2_Scl2c')
    scl_limitedLeadLag_firstOrder_y_start_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.firstOrder.y_start_Scl2c')
    scl_tC2Uel_Scl2c: Var = vf.add_var(name='scl.tC2Uel_Scl2c')
    scl_tB2Uel_Scl2c: Var = vf.add_var(name='scl.tB2Uel_Scl2c')
    scl_limitedLeadLag1_K_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.K_Scl2c')
    scl_limitedLeadLag1_YMax_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.YMax_Scl2c')
    scl_limitedLeadLag1_YMin_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.YMin_Scl2c')
    scl_limitedLeadLag1_t1_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.t1_Scl2c')
    scl_limitedLeadLag1_t2_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.t2_Scl2c')
    scl_limitedLeadLag1_firstOrder_y_start_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.firstOrder.y_start_Scl2c')
    scl_tC1Uel_Scl2c: Var = vf.add_var(name='scl.tC1Uel_Scl2c')
    scl_tB1Uel_Scl2c: Var = vf.add_var(name='scl.tB1Uel_Scl2c')
    scl_limitedLeadLag2_K_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.K_Scl2c')
    scl_limitedLeadLag2_YMax_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.YMax_Scl2c')
    scl_limitedLeadLag2_YMin_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.YMin_Scl2c')
    scl_limitedLeadLag2_t1_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.t1_Scl2c')
    scl_limitedLeadLag2_t2_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.t2_Scl2c')
    scl_limitedLeadLag2_firstOrder_y_start_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.firstOrder.y_start_Scl2c')
    scl_tC2Oel_Scl2c: Var = vf.add_var(name='scl.tC2Oel_Scl2c')
    scl_tB2Oel_Scl2c: Var = vf.add_var(name='scl.tB2Oel_Scl2c')
    scl_limitedLeadLag3_K_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.K_Scl2c')
    scl_limitedLeadLag3_YMax_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.YMax_Scl2c')
    scl_limitedLeadLag3_YMin_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.YMin_Scl2c')
    scl_limitedLeadLag3_t1_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.t1_Scl2c')
    scl_limitedLeadLag3_t2_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.t2_Scl2c')
    scl_limitedLeadLag3_firstOrder_y_start_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.firstOrder.y_start_Scl2c')
    scl_tC1Oel_Scl2c: Var = vf.add_var(name='scl.tC1Oel_Scl2c')
    scl_tB1Oel_Scl2c: Var = vf.add_var(name='scl.tB1Oel_Scl2c')
    scl_pidOel_Td_Scl2c: Var = vf.add_var(name='scl.pidOel.Td_Scl2c')
    scl_pidOel_Nd_Scl2c: Var = vf.add_var(name='scl.pidOel.Nd_Scl2c')
    scl_pidOel_D_x_start_Scl2c: Var = vf.add_var(name='scl.pidOel.D.x_start_Scl2c')
    scl_pidOel_xd_start_Scl2c: Var = vf.add_var(name='scl.pidOel.xd_start_Scl2c')
    scl_pidOel_D_y_start_Scl2c: Var = vf.add_var(name='scl.pidOel.D.y_start_Scl2c')
    scl_pidOel_Ti_Scl2c: Var = vf.add_var(name='scl.pidOel.Ti_Scl2c')
    scl_pidOel_xi_start_Scl2c: Var = vf.add_var(name='scl.pidOel.xi_start_Scl2c')
    scl_pidOel_Ni_Scl2c: Var = vf.add_var(name='scl.pidOel.Ni_Scl2c')
    scl_tDOel_Scl2c: Var = vf.add_var(name='scl.tDOel_Scl2c')
    scl_pidOel_wd_Scl2c: Var = vf.add_var(name='scl.pidOel.wd_Scl2c')
    scl_pidOel_addD_k2_Scl2c: Var = vf.add_var(name='scl.pidOel.addD.k2_Scl2c')
    scl_pidOel_kFF_Scl2c: Var = vf.add_var(name='scl.pidOel.kFF_Scl2c')
    scl_pidOel_addI_k2_Scl2c: Var = vf.add_var(name='scl.pidOel.addI.k2_Scl2c')
    scl_pidOel_wp_Scl2c: Var = vf.add_var(name='scl.pidOel.wp_Scl2c')
    scl_pidOel_addP_k2_Scl2c: Var = vf.add_var(name='scl.pidOel.addP.k2_Scl2c')
    scl_pidOel_k_Scl2c: Var = vf.add_var(name='scl.pidOel.k_Scl2c')
    scl_pidOel_yMax_Scl2c: Var = vf.add_var(name='scl.pidOel.yMax_Scl2c')
    scl_pidOel_yMin_Scl2c: Var = vf.add_var(name='scl.pidOel.yMin_Scl2c')
    scl_pidOel_y_start_Scl2c: Var = vf.add_var(name='scl.pidOel.y_start_Scl2c')
    scl_pidUel_Nd_Scl2c: Var = vf.add_var(name='scl.pidUel.Nd_Scl2c')
    scl_pidUel_Td_Scl2c: Var = vf.add_var(name='scl.pidUel.Td_Scl2c')
    scl_pidUel_D_x_start_Scl2c: Var = vf.add_var(name='scl.pidUel.D.x_start_Scl2c')
    scl_pidUel_xd_start_Scl2c: Var = vf.add_var(name='scl.pidUel.xd_start_Scl2c')
    scl_pidUel_D_y_start_Scl2c: Var = vf.add_var(name='scl.pidUel.D.y_start_Scl2c')
    scl_pidUel_Ti_Scl2c: Var = vf.add_var(name='scl.pidUel.Ti_Scl2c')
    scl_pidUel_xi_start_Scl2c: Var = vf.add_var(name='scl.pidUel.xi_start_Scl2c')
    scl_pidUel_Ni_Scl2c: Var = vf.add_var(name='scl.pidUel.Ni_Scl2c')
    scl_tDUel_Scl2c: Var = vf.add_var(name='scl.tDUel_Scl2c')
    scl_pidUel_wd_Scl2c: Var = vf.add_var(name='scl.pidUel.wd_Scl2c')
    scl_pidUel_addD_k2_Scl2c: Var = vf.add_var(name='scl.pidUel.addD.k2_Scl2c')
    scl_pidUel_kFF_Scl2c: Var = vf.add_var(name='scl.pidUel.kFF_Scl2c')
    scl_pidUel_addI_k2_Scl2c: Var = vf.add_var(name='scl.pidUel.addI.k2_Scl2c')
    scl_pidUel_wp_Scl2c: Var = vf.add_var(name='scl.pidUel.wp_Scl2c')
    scl_pidUel_addP_k2_Scl2c: Var = vf.add_var(name='scl.pidUel.addP.k2_Scl2c')
    scl_pidUel_k_Scl2c: Var = vf.add_var(name='scl.pidUel.k_Scl2c')
    scl_pidUel_yMax_Scl2c: Var = vf.add_var(name='scl.pidUel.yMax_Scl2c')
    scl_pidUel_yMin_Scl2c: Var = vf.add_var(name='scl.pidUel.yMin_Scl2c')
    scl_pidUel_y_start_Scl2c: Var = vf.add_var(name='scl.pidUel.y_start_Scl2c')
    scl_sclOelActivation_Vt0Pu_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.Vt0Pu_Scl2c')
    scl_tEnOel_Scl2c: Var = vf.add_var(name='scl.tEnOel_Scl2c')
    scl_sclOelActivation_tErr0_Scl2c: Var = vf.add_var(name='scl.sclOelActivation.tErr0_Scl2c')
    scl_tErr0_Scl2c: Var = vf.add_var(name='scl.tErr0_Scl2c')
    scl_tOff_Scl2c: Var = vf.add_var(name='scl.tOff_Scl2c')
    scl_sclReferenceCurrent_C1_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.C1_Scl2c')
    scl_sclReferenceCurrent_C2_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.C2_Scl2c')
    scl_sclReferenceCurrent_FixedRd_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.FixedRd_Scl2c')
    scl_sclReferenceCurrent_FixedRu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.FixedRu_Scl2c')
    scl_sclReferenceCurrent_I0Pu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.I0Pu_Scl2c')
    scl_sclReferenceCurrent_IInstPu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.IInstPu_Scl2c')
    scl_sclReferenceCurrent_ILimPu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.ILimPu_Scl2c')
    scl_sclReferenceCurrent_ITfPu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.ITfPu_Scl2c')
    scl_sclReferenceCurrent_K1_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.K1_Scl2c')
    scl_sclReferenceCurrent_K2_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.K2_Scl2c')
    scl_sclReferenceCurrent_KFb_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.KFb_Scl2c')
    scl_sclReferenceCurrent_Krd_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.Krd_Scl2c')
    scl_sclReferenceCurrent_Kru_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.Kru_Scl2c')
    scl_sclReferenceCurrent_Kzru_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.Kzru_Scl2c')
    scl_sclReferenceCurrent_VInvMaxPu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.VInvMaxPu_Scl2c')
    scl_sclReferenceCurrent_VInvMinPu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.VInvMinPu_Scl2c')
    scl_sclReferenceCurrent_Vt0Pu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.Vt0Pu_Scl2c')
    scl_sclReferenceCurrent_VtResetPu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.VtResetPu_Scl2c')
    scl_sclReferenceCurrent_tScl_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.tScl_Scl2c')
    scl_sclReferenceCurrent_tMax_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.tMax_Scl2c')
    scl_sclReferenceCurrent_tMin_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.tMin_Scl2c')
    scl_sclReferenceCurrent_tInt0_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.tInt0_Scl2c')
    scl_tInt0_Scl2c: Var = vf.add_var(name='scl.tInt0_Scl2c')
    scl_tMax_Scl2c: Var = vf.add_var(name='scl.tMax_Scl2c')
    scl_tMin_Scl2c: Var = vf.add_var(name='scl.tMin_Scl2c')
    scl_tScl_Scl2c: Var = vf.add_var(name='scl.tScl_Scl2c')
    scl_tEnUel_Scl2c: Var = vf.add_var(name='scl.tEnUel_Scl2c')
    scl_sclUelActivation_tErr0_Scl2c: Var = vf.add_var(name='scl.sclUelActivation.tErr0_Scl2c')
    scl_firstOrder_initType_Scl2c: Var = vf.add_var(name='scl.firstOrder.initType_Scl2c')
    scl_firstOrder1_initType_Scl2c: Var = vf.add_var(name='scl.firstOrder1.initType_Scl2c')
    scl_firstOrder2_initType_Scl2c: Var = vf.add_var(name='scl.firstOrder2.initType_Scl2c')
    scl_firstOrder3_initType_Scl2c: Var = vf.add_var(name='scl.firstOrder3.initType_Scl2c')
    scl_firstOrder4_initType_Scl2c: Var = vf.add_var(name='scl.firstOrder4.initType_Scl2c')
    scl_firstOrder5_initType_Scl2c: Var = vf.add_var(name='scl.firstOrder5.initType_Scl2c')
    scl_firstOrder6_initType_Scl2c: Var = vf.add_var(name='scl.firstOrder6.initType_Scl2c')
    scl_firstOrder7_initType_Scl2c: Var = vf.add_var(name='scl.firstOrder7.initType_Scl2c')
    scl_limitedLeadLag_firstOrder_initType_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.firstOrder.initType_Scl2c')
    scl_limitedLeadLag_limiter_homotopyType_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.limiter.homotopyType_Scl2c')
    scl_limitedLeadLag1_firstOrder_initType_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.firstOrder.initType_Scl2c')
    scl_limitedLeadLag1_limiter_homotopyType_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.limiter.homotopyType_Scl2c')
    scl_limitedLeadLag2_firstOrder_initType_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.firstOrder.initType_Scl2c')
    scl_limitedLeadLag2_limiter_homotopyType_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.limiter.homotopyType_Scl2c')
    scl_limitedLeadLag3_firstOrder_initType_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.firstOrder.initType_Scl2c')
    scl_limitedLeadLag3_limiter_homotopyType_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.limiter.homotopyType_Scl2c')
    scl_limiter_homotopyType_Scl2c: Var = vf.add_var(name='scl.limiter.homotopyType_Scl2c')
    scl_max1_nu_Scl2c: Var = vf.add_var(name='scl.max1.nu_Scl2c')
    scl_pidOel_D_initType_Scl2c: Var = vf.add_var(name='scl.pidOel.D.initType_Scl2c')
    scl_pidOel_I_initType_Scl2c: Var = vf.add_var(name='scl.pidOel.I.initType_Scl2c')
    scl_pidOel_controllerType_Scl2c: Var = vf.add_var(name='scl.pidOel.controllerType_Scl2c')
    scl_pidOel_homotopyType_Scl2c: Var = vf.add_var(name='scl.pidOel.homotopyType_Scl2c')
    scl_pidOel_initType_Scl2c: Var = vf.add_var(name='scl.pidOel.initType_Scl2c')
    scl_pidOel_limiter_homotopyType_Scl2c: Var = vf.add_var(name='scl.pidOel.limiter.homotopyType_Scl2c')
    scl_pidUel_D_initType_Scl2c: Var = vf.add_var(name='scl.pidUel.D.initType_Scl2c')
    scl_pidUel_I_initType_Scl2c: Var = vf.add_var(name='scl.pidUel.I.initType_Scl2c')
    scl_pidUel_controllerType_Scl2c: Var = vf.add_var(name='scl.pidUel.controllerType_Scl2c')
    scl_pidUel_homotopyType_Scl2c: Var = vf.add_var(name='scl.pidUel.homotopyType_Scl2c')
    scl_pidUel_initType_Scl2c: Var = vf.add_var(name='scl.pidUel.initType_Scl2c')
    scl_pidUel_limiter_homotopyType_Scl2c: Var = vf.add_var(name='scl.pidUel.limiter.homotopyType_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_initType_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.initType_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_initType_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.initType_Scl2c')
    scl_sclReferenceCurrent_limiter_homotopyType_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limiter.homotopyType_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_nu_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.nu_Scl2c')
    scl_sclReferenceCurrent_multiSwitch1_precision_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.multiSwitch1.precision_Scl2c')
    scl_Sw1_Scl2c: Var = vf.add_var(name='scl.Sw1_Scl2c')
    scl_limitedLeadLag_limiter_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.limiter.limitsAtInit_Scl2c')
    scl_limitedLeadLag_limiter_strict_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag.limiter.strict_Scl2c')
    scl_limitedLeadLag1_limiter_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.limiter.limitsAtInit_Scl2c')
    scl_limitedLeadLag1_limiter_strict_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag1.limiter.strict_Scl2c')
    scl_limitedLeadLag2_limiter_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.limiter.limitsAtInit_Scl2c')
    scl_limitedLeadLag2_limiter_strict_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag2.limiter.strict_Scl2c')
    scl_limitedLeadLag3_limiter_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.limiter.limitsAtInit_Scl2c')
    scl_limitedLeadLag3_limiter_strict_Scl2c: Var = vf.add_var(name='scl.limitedLeadLag3.limiter.strict_Scl2c')
    scl_limiter_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.limiter.limitsAtInit_Scl2c')
    scl_limiter_strict_Scl2c: Var = vf.add_var(name='scl.limiter.strict_Scl2c')
    scl_pidOel_I_use_reset_Scl2c: Var = vf.add_var(name='scl.pidOel.I.use_reset_Scl2c')
    scl_pidOel_I_use_set_Scl2c: Var = vf.add_var(name='scl.pidOel.I.use_set_Scl2c')
    scl_pidOel_limiter_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.pidOel.limiter.limitsAtInit_Scl2c')
    scl_pidOel_limiter_strict_Scl2c: Var = vf.add_var(name='scl.pidOel.limiter.strict_Scl2c')
    scl_pidOel_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.pidOel.limitsAtInit_Scl2c')
    scl_pidOel_strict_Scl2c: Var = vf.add_var(name='scl.pidOel.strict_Scl2c')
    scl_pidOel_withFeedForward_Scl2c: Var = vf.add_var(name='scl.pidOel.withFeedForward_Scl2c')
    scl_pidOel_with_D_Scl2c: Var = vf.add_var(name='scl.pidOel.with_D_Scl2c')
    scl_pidOel_with_I_Scl2c: Var = vf.add_var(name='scl.pidOel.with_I_Scl2c')
    scl_pidUel_I_use_reset_Scl2c: Var = vf.add_var(name='scl.pidUel.I.use_reset_Scl2c')
    scl_pidUel_I_use_set_Scl2c: Var = vf.add_var(name='scl.pidUel.I.use_set_Scl2c')
    scl_pidUel_limiter_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.pidUel.limiter.limitsAtInit_Scl2c')
    scl_pidUel_limiter_strict_Scl2c: Var = vf.add_var(name='scl.pidUel.limiter.strict_Scl2c')
    scl_pidUel_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.pidUel.limitsAtInit_Scl2c')
    scl_pidUel_strict_Scl2c: Var = vf.add_var(name='scl.pidUel.strict_Scl2c')
    scl_pidUel_withFeedForward_Scl2c: Var = vf.add_var(name='scl.pidUel.withFeedForward_Scl2c')
    scl_pidUel_with_D_Scl2c: Var = vf.add_var(name='scl.pidUel.with_D_Scl2c')
    scl_pidUel_with_I_Scl2c: Var = vf.add_var(name='scl.pidUel.with_I_Scl2c')
    scl_pythagoras_u1IsHypotenuse_Scl2c: Var = vf.add_var(name='scl.pythagoras.u1IsHypotenuse_Scl2c')
    scl_pythagoras1_u1IsHypotenuse_Scl2c: Var = vf.add_var(name='scl.pythagoras1.u1IsHypotenuse_Scl2c')
    scl_sclReferenceCurrent_Sw1_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.Sw1_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.limitsAtInit_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_strict_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.strict_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_use_reset_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.use_reset_Scl2c')
    scl_sclReferenceCurrent_limIntegrator_use_set_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator.use_set_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.limitsAtInit_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_strict_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.strict_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_use_reset_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.use_reset_Scl2c')
    scl_sclReferenceCurrent_limIntegrator1_use_set_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limIntegrator1.use_set_Scl2c')
    scl_sclReferenceCurrent_limiter_limitsAtInit_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limiter.limitsAtInit_Scl2c')
    scl_sclReferenceCurrent_limiter_strict_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.limiter.strict_Scl2c')
    scl_sclReferenceCurrent_power_NInteger_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.power.NInteger_Scl2c')
    scl_sclReferenceCurrent_power1_NInteger_Scl2c: Var = vf.add_var(name='scl.sclReferenceCurrent.power1.NInteger_Scl2c')
    scl_pidOel_unitTime_Scl2c: Var = vf.add_var(name='scl.pidOel.unitTime_Scl2c')
    scl_pidUel_unitTime_Scl2c: Var = vf.add_var(name='scl.pidUel.unitTime_Scl2c')

    event_dict: dict[Var, Expr | Const] = dict({
        scl_C1_Scl2c: vf.add_const(value=1.0),
        scl_C2_Scl2c: vf.add_const(value=1.0),
        scl_FixedRd_Scl2c: vf.add_const(value=0.0),
        scl_FixedRu_Scl2c: vf.add_const(value=0.0),
        scl_IInstPu_Scl2c: vf.add_const(value=1.5),
        scl_IInstUelPu_Scl2c: vf.add_const(value=1.5),
        scl_ILimPu_Scl2c: vf.add_const(value=1.2),
        scl_IRef0Pu_Scl2c: sym.sqrt((((scl_PGen0Pu_Scl2c ** vf.add_const(value=2.0)) + (scl_QGen0Pu_Scl2c ** vf.add_const(value=2.0))) / ((scl_ut0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl2c ** vf.add_const(value=2.0))))),
        scl_IResetPu_Scl2c: vf.add_const(value=1.0),
        scl_IScaled0Pu_Scl2c: ((((scl_it0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_it0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)) / scl_ITfPu_Scl2c),
        scl_ITfPu_Scl2c: vf.add_const(value=1.1),
        scl_IThOffPu_Scl2c: vf.add_const(value=1.0),
        scl_IqOelMinPu_Scl2c: vf.add_const(value=0.0),
        scl_IqUelMaxPu_Scl2c: vf.add_const(value=0.0),
        scl_K1_Scl2c: vf.add_const(value=1.0),
        scl_K2_Scl2c: vf.add_const(value=1.0),
        scl_KFb_Scl2c: vf.add_const(value=1.0),
        scl_KIpOel_Scl2c: vf.add_const(value=1.0),
        scl_KIpUel_Scl2c: vf.add_const(value=1.0),
        scl_KIqOel_Scl2c: vf.add_const(value=1.0),
        scl_KIqUel_Scl2c: vf.add_const(value=1.0),
        scl_KPRef_Scl2c: vf.add_const(value=1.0),
        scl_KdOel_Scl2c: vf.add_const(value=0.0),
        scl_KdUel_Scl2c: vf.add_const(value=0.0),
        scl_KiOel_Scl2c: vf.add_const(value=1.0),
        scl_KiUel_Scl2c: vf.add_const(value=1.0),
        scl_KpOel_Scl2c: vf.add_const(value=1.0),
        scl_KpUel_Scl2c: vf.add_const(value=1.0),
        scl_Krd_Scl2c: vf.add_const(value=0.1),
        scl_Kru_Scl2c: vf.add_const(value=0.1),
        scl_Kzru_Scl2c: vf.add_const(value=0.0),
        scl_PGen0Pu_Scl2c: vf.add_const(value=0.8),
        scl_QGen0Pu_Scl2c: vf.add_const(value=0.0),
        scl_VInvMaxPu_Scl2c: vf.add_const(value=1.0),
        scl_VInvMinPu_Scl2c: vf.add_const(value=0.0),
        scl_VOel1MaxPu_Scl2c: vf.add_const(value=1.0),
        scl_VOel1MinPu_Scl2c: vf.add_const(value=-1.0),
        scl_VOel2MaxPu_Scl2c: vf.add_const(value=1.0),
        scl_VOel2MinPu_Scl2c: vf.add_const(value=-1.0),
        scl_VOel3MaxPu_Scl2c: vf.add_const(value=1.0),
        scl_VOel3MinPu_Scl2c: vf.add_const(value=-1.0),
        scl_VUel1MaxPu_Scl2c: vf.add_const(value=1.0),
        scl_VUel1MinPu_Scl2c: vf.add_const(value=-1.0),
        scl_VUel2MaxPu_Scl2c: vf.add_const(value=1.0),
        scl_VUel2MinPu_Scl2c: vf.add_const(value=-1.0),
        scl_VUel3MaxPu_Scl2c: vf.add_const(value=1.0),
        scl_VUel3MinPu_Scl2c: vf.add_const(value=-1.0),
        scl_VtMinPu_Scl2c: vf.add_const(value=0.9),
        scl_VtResetPu_Scl2c: vf.add_const(value=1.0),
        scl_add_k1_Scl2c: vf.add_const(value=-1.0),
        scl_add_k2_Scl2c: vf.add_const(value=1.0),
        scl_add1_k1_Scl2c: vf.add_const(value=1.0),
        scl_add1_k2_Scl2c: vf.add_const(value=-1.0),
        scl_add2_k1_Scl2c: vf.add_const(value=1.0),
        scl_add2_k2_Scl2c: vf.add_const(value=-1.0),
        scl_add3_k1_Scl2c: vf.add_const(value=-1.0),
        scl_add3_k2_Scl2c: vf.add_const(value=1.0),
        scl_add3_k3_Scl2c: vf.add_const(value=-1.0),
        scl_add31_k1_Scl2c: vf.add_const(value=1.0),
        scl_add31_k2_Scl2c: vf.add_const(value=-1.0),
        scl_add31_k3_Scl2c: vf.add_const(value=1.0),
        scl_const_k_Scl2c: scl_IqUelMaxPu_Scl2c,
        scl_const1_k_Scl2c: scl_IqOelMinPu_Scl2c,
        scl_const2_k_Scl2c: scl_VtMinPu_Scl2c,
        scl_firstOrder_T_Scl2c: scl_tIpUel_Scl2c,
        scl_firstOrder_k_Scl2c: scl_KIpUel_Scl2c,
        scl_firstOrder_y_start_Scl2c: (scl_KIpUel_Scl2c * (scl_PGen0Pu_Scl2c / (((scl_ut0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)))),
        scl_firstOrder1_T_Scl2c: scl_tIpOel_Scl2c,
        scl_firstOrder1_k_Scl2c: scl_KIpOel_Scl2c,
        scl_firstOrder1_y_start_Scl2c: (scl_KIpOel_Scl2c * (scl_PGen0Pu_Scl2c / (((scl_ut0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)))),
        scl_firstOrder2_T_Scl2c: scl_tIqOel_Scl2c,
        scl_firstOrder2_k_Scl2c: scl_KIqOel_Scl2c,
        scl_firstOrder2_y_start_Scl2c: (scl_KIqOel_Scl2c * (scl_QGen0Pu_Scl2c / (((scl_ut0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)))),
        scl_firstOrder3_T_Scl2c: scl_tIqUel_Scl2c,
        scl_firstOrder3_k_Scl2c: scl_KIqUel_Scl2c,
        scl_firstOrder3_y_start_Scl2c: (scl_KIqUel_Scl2c * (scl_QGen0Pu_Scl2c / (((scl_ut0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)))),
        scl_firstOrder4_T_Scl2c: scl_tVtScl_Scl2c,
        scl_firstOrder4_k_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder4_y_start_Scl2c: (((scl_ut0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)),
        scl_firstOrder5_T_Scl2c: scl_tItScl_Scl2c,
        scl_firstOrder5_k_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder5_y_start_Scl2c: (((scl_it0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_it0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)),
        scl_firstOrder6_T_Scl2c: scl_tIpOel_Scl2c,
        scl_firstOrder6_k_Scl2c: scl_KPRef_Scl2c,
        scl_firstOrder6_y_start_Scl2c: (scl_KPRef_Scl2c * (scl_PGen0Pu_Scl2c / (((scl_ut0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)))),
        scl_firstOrder7_T_Scl2c: scl_tAScl_Scl2c,
        scl_firstOrder7_k_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder7_y_start_Scl2c: scl_IRef0Pu_Scl2c,
        scl_it0Pu_im_Scl2c: vf.add_const(value=0.0),
        scl_it0Pu_re_Scl2c: vf.add_const(value=0.8),
        scl_limitedLeadLag_K_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag_Y0_Scl2c: vf.add_const(value=0.0),
        scl_limitedLeadLag_YMax_Scl2c: scl_VUel2MaxPu_Scl2c,
        scl_limitedLeadLag_YMin_Scl2c: scl_VUel2MinPu_Scl2c,
        scl_limitedLeadLag_firstOrder_T_Scl2c: scl_limitedLeadLag_t1_Scl2c,
        scl_limitedLeadLag_firstOrder_k_Scl2c: ((scl_limitedLeadLag_t1_Scl2c - scl_limitedLeadLag_t2_Scl2c) / (scl_limitedLeadLag_t1_Scl2c * scl_limitedLeadLag_K_Scl2c)),
        scl_limitedLeadLag_firstOrder_y_start_Scl2c: (scl_limitedLeadLag_Y0_Scl2c * ((scl_limitedLeadLag_t1_Scl2c - scl_limitedLeadLag_t2_Scl2c) / (scl_limitedLeadLag_t1_Scl2c * scl_limitedLeadLag_K_Scl2c))),
        scl_limitedLeadLag_gain_k_Scl2c: (scl_limitedLeadLag_K_Scl2c * (scl_limitedLeadLag_t1_Scl2c / scl_limitedLeadLag_t2_Scl2c)),
        scl_limitedLeadLag_limiter_uMax_Scl2c: scl_limitedLeadLag_YMax_Scl2c,
        scl_limitedLeadLag_limiter_uMin_Scl2c: scl_limitedLeadLag_YMin_Scl2c,
        scl_limitedLeadLag_t1_Scl2c: scl_tC2Uel_Scl2c,
        scl_limitedLeadLag_t2_Scl2c: scl_tB2Uel_Scl2c,
        scl_limitedLeadLag1_K_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag1_Y0_Scl2c: vf.add_const(value=0.0),
        scl_limitedLeadLag1_YMax_Scl2c: scl_VUel1MaxPu_Scl2c,
        scl_limitedLeadLag1_YMin_Scl2c: scl_VUel1MinPu_Scl2c,
        scl_limitedLeadLag1_firstOrder_T_Scl2c: scl_limitedLeadLag1_t1_Scl2c,
        scl_limitedLeadLag1_firstOrder_k_Scl2c: ((scl_limitedLeadLag1_t1_Scl2c - scl_limitedLeadLag1_t2_Scl2c) / (scl_limitedLeadLag1_t1_Scl2c * scl_limitedLeadLag1_K_Scl2c)),
        scl_limitedLeadLag1_firstOrder_y_start_Scl2c: (scl_limitedLeadLag1_Y0_Scl2c * ((scl_limitedLeadLag1_t1_Scl2c - scl_limitedLeadLag1_t2_Scl2c) / (scl_limitedLeadLag1_t1_Scl2c * scl_limitedLeadLag1_K_Scl2c))),
        scl_limitedLeadLag1_gain_k_Scl2c: (scl_limitedLeadLag1_K_Scl2c * (scl_limitedLeadLag1_t1_Scl2c / scl_limitedLeadLag1_t2_Scl2c)),
        scl_limitedLeadLag1_limiter_uMax_Scl2c: scl_limitedLeadLag1_YMax_Scl2c,
        scl_limitedLeadLag1_limiter_uMin_Scl2c: scl_limitedLeadLag1_YMin_Scl2c,
        scl_limitedLeadLag1_t1_Scl2c: scl_tC1Uel_Scl2c,
        scl_limitedLeadLag1_t2_Scl2c: scl_tB1Uel_Scl2c,
        scl_limitedLeadLag2_K_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag2_Y0_Scl2c: vf.add_const(value=0.0),
        scl_limitedLeadLag2_YMax_Scl2c: scl_VOel2MaxPu_Scl2c,
        scl_limitedLeadLag2_YMin_Scl2c: scl_VOel2MinPu_Scl2c,
        scl_limitedLeadLag2_firstOrder_T_Scl2c: scl_limitedLeadLag2_t1_Scl2c,
        scl_limitedLeadLag2_firstOrder_k_Scl2c: ((scl_limitedLeadLag2_t1_Scl2c - scl_limitedLeadLag2_t2_Scl2c) / (scl_limitedLeadLag2_t1_Scl2c * scl_limitedLeadLag2_K_Scl2c)),
        scl_limitedLeadLag2_firstOrder_y_start_Scl2c: (scl_limitedLeadLag2_Y0_Scl2c * ((scl_limitedLeadLag2_t1_Scl2c - scl_limitedLeadLag2_t2_Scl2c) / (scl_limitedLeadLag2_t1_Scl2c * scl_limitedLeadLag2_K_Scl2c))),
        scl_limitedLeadLag2_gain_k_Scl2c: (scl_limitedLeadLag2_K_Scl2c * (scl_limitedLeadLag2_t1_Scl2c / scl_limitedLeadLag2_t2_Scl2c)),
        scl_limitedLeadLag2_limiter_uMax_Scl2c: scl_limitedLeadLag2_YMax_Scl2c,
        scl_limitedLeadLag2_limiter_uMin_Scl2c: scl_limitedLeadLag2_YMin_Scl2c,
        scl_limitedLeadLag2_t1_Scl2c: scl_tC2Oel_Scl2c,
        scl_limitedLeadLag2_t2_Scl2c: scl_tB2Oel_Scl2c,
        scl_limitedLeadLag3_K_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag3_Y0_Scl2c: vf.add_const(value=0.0),
        scl_limitedLeadLag3_YMax_Scl2c: scl_VOel1MaxPu_Scl2c,
        scl_limitedLeadLag3_YMin_Scl2c: scl_VOel1MinPu_Scl2c,
        scl_limitedLeadLag3_firstOrder_T_Scl2c: scl_limitedLeadLag3_t1_Scl2c,
        scl_limitedLeadLag3_firstOrder_k_Scl2c: ((scl_limitedLeadLag3_t1_Scl2c - scl_limitedLeadLag3_t2_Scl2c) / (scl_limitedLeadLag3_t1_Scl2c * scl_limitedLeadLag3_K_Scl2c)),
        scl_limitedLeadLag3_firstOrder_y_start_Scl2c: (scl_limitedLeadLag3_Y0_Scl2c * ((scl_limitedLeadLag3_t1_Scl2c - scl_limitedLeadLag3_t2_Scl2c) / (scl_limitedLeadLag3_t1_Scl2c * scl_limitedLeadLag3_K_Scl2c))),
        scl_limitedLeadLag3_gain_k_Scl2c: (scl_limitedLeadLag3_K_Scl2c * (scl_limitedLeadLag3_t1_Scl2c / scl_limitedLeadLag3_t2_Scl2c)),
        scl_limitedLeadLag3_limiter_uMax_Scl2c: scl_limitedLeadLag3_YMax_Scl2c,
        scl_limitedLeadLag3_limiter_uMin_Scl2c: scl_limitedLeadLag3_YMin_Scl2c,
        scl_limitedLeadLag3_t1_Scl2c: scl_tC1Oel_Scl2c,
        scl_limitedLeadLag3_t2_Scl2c: scl_tB1Oel_Scl2c,
        scl_limiter_uMax_Scl2c: scl_IInstUelPu_Scl2c,
        scl_limiter_uMin_Scl2c: vf.add_const(value=-999.0),
        scl_pidOel_D_T_Scl2c: (((scl_pidOel_Td_Scl2c / scl_pidOel_Nd_Scl2c) * sym.heaviside(((scl_pidOel_Td_Scl2c / scl_pidOel_Nd_Scl2c) - vf.add_const(value=1e-14)))) + (vf.add_const(value=1e-14) * (vf.add_const(value=1) - sym.heaviside(((scl_pidOel_Td_Scl2c / scl_pidOel_Nd_Scl2c) - vf.add_const(value=1e-14)))))),
        scl_pidOel_D_k_Scl2c: scl_pidOel_Td_Scl2c,
        scl_pidOel_D_x_start_Scl2c: scl_pidOel_xd_start_Scl2c,
        scl_pidOel_D_y_start_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_FFzero_k_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_I_k_Scl2c: (vf.add_const(value=1.0) / scl_pidOel_Ti_Scl2c),
        scl_pidOel_I_y_start_Scl2c: scl_pidOel_xi_start_Scl2c,
        scl_pidOel_Nd_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_Ni_Scl2c: vf.add_const(value=0.9),
        scl_pidOel_P_k_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_Td_Scl2c: scl_tDOel_Scl2c,
        scl_pidOel_Ti_Scl2c: (vf.add_const(value=1.0) / scl_KiOel_Scl2c),
        scl_pidOel_addD_k1_Scl2c: scl_pidOel_wd_Scl2c,
        scl_pidOel_addD_k2_Scl2c: vf.add_const(value=-1.0),
        scl_pidOel_addFF_k1_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_addFF_k2_Scl2c: scl_pidOel_kFF_Scl2c,
        scl_pidOel_addI_k1_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_addI_k2_Scl2c: vf.add_const(value=-1.0),
        scl_pidOel_addI_k3_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_addP_k1_Scl2c: scl_pidOel_wp_Scl2c,
        scl_pidOel_addP_k2_Scl2c: vf.add_const(value=-1.0),
        scl_pidOel_addPID_k1_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_addPID_k2_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_addPID_k3_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_addSat_k1_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_addSat_k2_Scl2c: vf.add_const(value=-1.0),
        scl_pidOel_gainPID_k_Scl2c: scl_pidOel_k_Scl2c,
        scl_pidOel_gainTrack_k_Scl2c: (vf.add_const(value=1.0) / (scl_pidOel_Ni_Scl2c * scl_pidOel_k_Scl2c)),
        scl_pidOel_k_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_kFF_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_limiter_uMax_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_limiter_uMin_Scl2c: vf.add_const(value=-1.0),
        scl_pidOel_wd_Scl2c: (scl_KdOel_Scl2c / scl_tDOel_Scl2c),
        scl_pidOel_wp_Scl2c: scl_KpOel_Scl2c,
        scl_pidOel_xd_start_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_xi_start_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_yMax_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_yMin_Scl2c: vf.add_const(value=-1.0),
        scl_pidOel_y_start_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_D_T_Scl2c: (((scl_pidUel_Td_Scl2c / scl_pidUel_Nd_Scl2c) * sym.heaviside(((scl_pidUel_Td_Scl2c / scl_pidUel_Nd_Scl2c) - vf.add_const(value=1e-14)))) + (vf.add_const(value=1e-14) * (vf.add_const(value=1) - sym.heaviside(((scl_pidUel_Td_Scl2c / scl_pidUel_Nd_Scl2c) - vf.add_const(value=1e-14)))))),
        scl_pidUel_D_k_Scl2c: scl_pidUel_Td_Scl2c,
        scl_pidUel_D_x_start_Scl2c: scl_pidUel_xd_start_Scl2c,
        scl_pidUel_D_y_start_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_FFzero_k_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_I_k_Scl2c: (vf.add_const(value=1.0) / scl_pidUel_Ti_Scl2c),
        scl_pidUel_I_y_start_Scl2c: scl_pidUel_xi_start_Scl2c,
        scl_pidUel_Nd_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_Ni_Scl2c: vf.add_const(value=0.9),
        scl_pidUel_P_k_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_Td_Scl2c: scl_tDUel_Scl2c,
        scl_pidUel_Ti_Scl2c: (vf.add_const(value=1.0) / scl_KiUel_Scl2c),
        scl_pidUel_addD_k1_Scl2c: scl_pidUel_wd_Scl2c,
        scl_pidUel_addD_k2_Scl2c: vf.add_const(value=-1.0),
        scl_pidUel_addFF_k1_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_addFF_k2_Scl2c: scl_pidUel_kFF_Scl2c,
        scl_pidUel_addI_k1_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_addI_k2_Scl2c: vf.add_const(value=-1.0),
        scl_pidUel_addI_k3_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_addP_k1_Scl2c: scl_pidUel_wp_Scl2c,
        scl_pidUel_addP_k2_Scl2c: vf.add_const(value=-1.0),
        scl_pidUel_addPID_k1_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_addPID_k2_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_addPID_k3_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_addSat_k1_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_addSat_k2_Scl2c: vf.add_const(value=-1.0),
        scl_pidUel_gainPID_k_Scl2c: scl_pidUel_k_Scl2c,
        scl_pidUel_gainTrack_k_Scl2c: (vf.add_const(value=1.0) / (scl_pidUel_Ni_Scl2c * scl_pidUel_k_Scl2c)),
        scl_pidUel_k_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_kFF_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_limiter_uMax_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_limiter_uMin_Scl2c: vf.add_const(value=-1.0),
        scl_pidUel_wd_Scl2c: (scl_KdUel_Scl2c / scl_tDUel_Scl2c),
        scl_pidUel_wp_Scl2c: scl_KpUel_Scl2c,
        scl_pidUel_xd_start_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_xi_start_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_yMax_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_yMin_Scl2c: vf.add_const(value=-1.0),
        scl_pidUel_y_start_Scl2c: vf.add_const(value=0.0),
        scl_sclOelActivation_IInstPu_Scl2c: scl_IInstPu_Scl2c,
        scl_sclOelActivation_IOelRef0Pu_Scl2c: scl_IRef0Pu_Scl2c,
        scl_sclOelActivation_IResetPu_Scl2c: scl_IResetPu_Scl2c,
        scl_sclOelActivation_IThOffPu_Scl2c: scl_IThOffPu_Scl2c,
        scl_sclOelActivation_Vt0Pu_Scl2c: (((scl_ut0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)),
        scl_sclOelActivation_VtMinPu_Scl2c: scl_VtMinPu_Scl2c,
        scl_sclOelActivation_VtResetPu_Scl2c: scl_VtResetPu_Scl2c,
        scl_sclOelActivation_tEnOel_Scl2c: scl_tEnOel_Scl2c,
        scl_sclOelActivation_tErr0_Scl2c: scl_tErr0_Scl2c,
        scl_sclOelActivation_tOff_Scl2c: scl_tOff_Scl2c,
        scl_sclReferenceCurrent_C1_Scl2c: scl_C1_Scl2c,
        scl_sclReferenceCurrent_C2_Scl2c: scl_C2_Scl2c,
        scl_sclReferenceCurrent_FixedRd_Scl2c: scl_FixedRd_Scl2c,
        scl_sclReferenceCurrent_FixedRu_Scl2c: scl_FixedRu_Scl2c,
        scl_sclReferenceCurrent_I0Pu_Scl2c: (((scl_it0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_it0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)),
        scl_sclReferenceCurrent_IInstPu_Scl2c: scl_IInstPu_Scl2c,
        scl_sclReferenceCurrent_ILimPu_Scl2c: scl_ILimPu_Scl2c,
        scl_sclReferenceCurrent_IRef0Pu_Scl2c: scl_IRef0Pu_Scl2c,
        scl_sclReferenceCurrent_ITfPu_Scl2c: scl_ITfPu_Scl2c,
        scl_sclReferenceCurrent_K1_Scl2c: scl_K1_Scl2c,
        scl_sclReferenceCurrent_K2_Scl2c: scl_K2_Scl2c,
        scl_sclReferenceCurrent_KFb_Scl2c: scl_KFb_Scl2c,
        scl_sclReferenceCurrent_KPRef_Scl2c: scl_KPRef_Scl2c,
        scl_sclReferenceCurrent_Krd_Scl2c: scl_Krd_Scl2c,
        scl_sclReferenceCurrent_Kru_Scl2c: scl_Kru_Scl2c,
        scl_sclReferenceCurrent_Kzru_Scl2c: scl_Kzru_Scl2c,
        scl_sclReferenceCurrent_VInvMaxPu_Scl2c: scl_VInvMaxPu_Scl2c,
        scl_sclReferenceCurrent_VInvMinPu_Scl2c: scl_VInvMinPu_Scl2c,
        scl_sclReferenceCurrent_Vt0Pu_Scl2c: (((scl_ut0Pu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_ut0Pu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5)),
        scl_sclReferenceCurrent_VtResetPu_Scl2c: scl_VtResetPu_Scl2c,
        scl_sclReferenceCurrent_add_k1_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_add_k2_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_const_k_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_const1_k_Scl2c: scl_sclReferenceCurrent_FixedRu_Scl2c,
        scl_sclReferenceCurrent_const2_k_Scl2c: scl_sclReferenceCurrent_FixedRd_Scl2c,
        scl_sclReferenceCurrent_const3_k_Scl2c: scl_sclReferenceCurrent_tScl_Scl2c,
        scl_sclReferenceCurrent_const4_k_Scl2c: scl_sclReferenceCurrent_Krd_Scl2c,
        scl_sclReferenceCurrent_const5_k_Scl2c: scl_sclReferenceCurrent_Kru_Scl2c,
        scl_sclReferenceCurrent_gain_k_Scl2c: (vf.add_const(value=1.0) / scl_sclReferenceCurrent_ITfPu_Scl2c),
        scl_sclReferenceCurrent_gain1_k_Scl2c: scl_sclReferenceCurrent_K1_Scl2c,
        scl_sclReferenceCurrent_gain2_k_Scl2c: scl_sclReferenceCurrent_K2_Scl2c,
        scl_sclReferenceCurrent_gain3_k_Scl2c: scl_sclReferenceCurrent_KFb_Scl2c,
        scl_sclReferenceCurrent_greaterEqualThreshold_threshold_Scl2c: (scl_sclReferenceCurrent_Kzru_Scl2c * scl_sclReferenceCurrent_tScl_Scl2c),
        scl_sclReferenceCurrent_lessEqualThreshold_threshold_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_lessEqualThreshold1_threshold_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_lessThreshold_threshold_Scl2c: scl_sclReferenceCurrent_VtResetPu_Scl2c,
        scl_sclReferenceCurrent_limIntegrator_k_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_limIntegrator_outMax_Scl2c: scl_sclReferenceCurrent_tMax_Scl2c,
        scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c: scl_sclReferenceCurrent_tMin_Scl2c,
        scl_sclReferenceCurrent_limIntegrator_y_start_Scl2c: scl_sclReferenceCurrent_tInt0_Scl2c,
        scl_sclReferenceCurrent_limIntegrator1_k_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_limIntegrator1_outMax_Scl2c: scl_sclReferenceCurrent_IInstPu_Scl2c,
        scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c: scl_sclReferenceCurrent_ILimPu_Scl2c,
        scl_sclReferenceCurrent_limIntegrator1_y_start_Scl2c: scl_sclReferenceCurrent_IRef0Pu_Scl2c,
        scl_sclReferenceCurrent_limiter_uMax_Scl2c: scl_sclReferenceCurrent_VInvMaxPu_Scl2c,
        scl_sclReferenceCurrent_limiter_uMin_Scl2c: scl_sclReferenceCurrent_VInvMinPu_Scl2c,
        scl_sclReferenceCurrent_multiSwitch1_y_default_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_power_N_Scl2c: scl_sclReferenceCurrent_C2_Scl2c,
        scl_sclReferenceCurrent_power1_N_Scl2c: scl_sclReferenceCurrent_C1_Scl2c,
        scl_sclReferenceCurrent_tErr0_Scl2c: scl_tErr0_Scl2c,
        scl_sclReferenceCurrent_tInt0_Scl2c: scl_tInt0_Scl2c,
        scl_sclReferenceCurrent_tMax_Scl2c: scl_tMax_Scl2c,
        scl_sclReferenceCurrent_tMin_Scl2c: scl_tMin_Scl2c,
        scl_sclReferenceCurrent_tScl_Scl2c: scl_tScl_Scl2c,
        scl_sclUelActivation_IInstUelPu_Scl2c: scl_IInstUelPu_Scl2c,
        scl_sclUelActivation_IResetPu_Scl2c: scl_IResetPu_Scl2c,
        scl_sclUelActivation_IThOffPu_Scl2c: scl_IThOffPu_Scl2c,
        scl_sclUelActivation_IUelRef0Pu_Scl2c: scl_IRef0Pu_Scl2c,
        scl_sclUelActivation_tEnUel_Scl2c: scl_tEnUel_Scl2c,
        scl_sclUelActivation_tErr0_Scl2c: scl_tErr0_Scl2c,
        scl_sclUelActivation_tOff_Scl2c: scl_tOff_Scl2c,
        scl_tAScl_Scl2c: vf.add_const(value=0.02),
        scl_tB1Oel_Scl2c: vf.add_const(value=1.0),
        scl_tB1Uel_Scl2c: vf.add_const(value=1.0),
        scl_tB2Oel_Scl2c: vf.add_const(value=1.0),
        scl_tB2Uel_Scl2c: vf.add_const(value=1.0),
        scl_tC1Oel_Scl2c: vf.add_const(value=1.0),
        scl_tC1Uel_Scl2c: vf.add_const(value=1.0),
        scl_tC2Oel_Scl2c: vf.add_const(value=1.0),
        scl_tC2Uel_Scl2c: vf.add_const(value=1.0),
        scl_tDOel_Scl2c: vf.add_const(value=0.02),
        scl_tDUel_Scl2c: vf.add_const(value=0.02),
        scl_tEnOel_Scl2c: vf.add_const(value=0.0),
        scl_tEnUel_Scl2c: vf.add_const(value=0.0),
        scl_tErr0_Scl2c: (scl_tScl_Scl2c - scl_tInt0_Scl2c),
        scl_tInt0_Scl2c: (((scl_K2_Scl2c * (vf.add_const(value=-1.0) + (scl_IScaled0Pu_Scl2c ** scl_C2_Scl2c))) + ((sym.heaviside(((vf.add_const(value=1.0) - scl_IScaled0Pu_Scl2c) + vf.add_const(value=1e-06))) * scl_FixedRu_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=1.0) - scl_IScaled0Pu_Scl2c) + vf.add_const(value=1e-06)))) * scl_FixedRd_Scl2c))) / scl_KFb_Scl2c),
        scl_tIpOel_Scl2c: vf.add_const(value=0.02),
        scl_tIpUel_Scl2c: vf.add_const(value=0.02),
        scl_tIqOel_Scl2c: vf.add_const(value=0.02),
        scl_tIqUel_Scl2c: vf.add_const(value=0.02),
        scl_tItScl_Scl2c: vf.add_const(value=0.02),
        scl_tMax_Scl2c: vf.add_const(value=999.0),
        scl_tMin_Scl2c: vf.add_const(value=0.0),
        scl_tOff_Scl2c: vf.add_const(value=0.0),
        scl_tScl_Scl2c: vf.add_const(value=1.0),
        scl_tVtScl_Scl2c: vf.add_const(value=0.02),
        scl_ut0Pu_im_Scl2c: vf.add_const(value=0.0),
        scl_ut0Pu_re_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder_initType_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder1_initType_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder2_initType_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder3_initType_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder4_initType_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder5_initType_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder6_initType_Scl2c: vf.add_const(value=1.0),
        scl_firstOrder7_initType_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag_firstOrder_initType_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag_limiter_homotopyType_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag1_firstOrder_initType_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag1_limiter_homotopyType_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag2_firstOrder_initType_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag2_limiter_homotopyType_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag3_firstOrder_initType_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag3_limiter_homotopyType_Scl2c: vf.add_const(value=1.0),
        scl_limiter_homotopyType_Scl2c: vf.add_const(value=1.0),
        scl_max1_nu_Scl2c: vf.add_const(value=3.0),
        scl_pidOel_D_initType_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_I_initType_Scl2c: vf.add_const(value=3.0),
        scl_pidOel_controllerType_Scl2c: vf.add_const(value=4.0),
        scl_pidOel_homotopyType_Scl2c: vf.add_const(value=2.0),
        scl_pidOel_initType_Scl2c: vf.add_const(value=5.0),
        scl_pidOel_limiter_homotopyType_Scl2c: vf.add_const(value=2.0),
        scl_pidUel_D_initType_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_I_initType_Scl2c: vf.add_const(value=3.0),
        scl_pidUel_controllerType_Scl2c: vf.add_const(value=4.0),
        scl_pidUel_homotopyType_Scl2c: vf.add_const(value=2.0),
        scl_pidUel_initType_Scl2c: vf.add_const(value=5.0),
        scl_pidUel_limiter_homotopyType_Scl2c: vf.add_const(value=2.0),
        scl_sclReferenceCurrent_limIntegrator_initType_Scl2c: vf.add_const(value=3.0),
        scl_sclReferenceCurrent_limIntegrator1_initType_Scl2c: vf.add_const(value=3.0),
        scl_sclReferenceCurrent_limiter_homotopyType_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_multiSwitch1_nu_Scl2c: vf.add_const(value=2.0),
        scl_sclReferenceCurrent_multiSwitch1_precision_Scl2c: vf.add_const(value=3.0),
        scl_Sw1_Scl2c: vf.add_const(value=0.0),
        scl_limitedLeadLag_limiter_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag_limiter_strict_Scl2c: vf.add_const(value=0.0),
        scl_limitedLeadLag1_limiter_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag1_limiter_strict_Scl2c: vf.add_const(value=0.0),
        scl_limitedLeadLag2_limiter_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag2_limiter_strict_Scl2c: vf.add_const(value=0.0),
        scl_limitedLeadLag3_limiter_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_limitedLeadLag3_limiter_strict_Scl2c: vf.add_const(value=0.0),
        scl_limiter_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_limiter_strict_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_D_zeroGain_Scl2c: sym.heaviside(((vf.add_const(value=2.220446049250313e-16) - sym.abs(scl_pidOel_D_k_Scl2c)) - vf.add_const(value=1e-06))),
        scl_pidOel_I_use_reset_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_I_use_set_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_limiter_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_limiter_strict_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_strict_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_withFeedForward_Scl2c: vf.add_const(value=0.0),
        scl_pidOel_with_D_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_with_I_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_D_zeroGain_Scl2c: sym.heaviside(((vf.add_const(value=2.220446049250313e-16) - sym.abs(scl_pidUel_D_k_Scl2c)) - vf.add_const(value=1e-06))),
        scl_pidUel_I_use_reset_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_I_use_set_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_limiter_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_limiter_strict_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_strict_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_withFeedForward_Scl2c: vf.add_const(value=0.0),
        scl_pidUel_with_D_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_with_I_Scl2c: vf.add_const(value=1.0),
        scl_pythagoras_u1IsHypotenuse_Scl2c: vf.add_const(value=0.0),
        scl_pythagoras1_u1IsHypotenuse_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_Sw1_Scl2c: scl_Sw1_Scl2c,
        scl_sclReferenceCurrent_booleanConstant_k_Scl2c: scl_sclReferenceCurrent_Sw1_Scl2c,
        scl_sclReferenceCurrent_limIntegrator_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_limIntegrator_strict_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_limIntegrator_use_reset_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_limIntegrator_use_set_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_limIntegrator1_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_limIntegrator1_strict_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_limIntegrator1_use_reset_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_limIntegrator1_use_set_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_limiter_limitsAtInit_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_limiter_strict_Scl2c: vf.add_const(value=0.0),
        scl_sclReferenceCurrent_power_NInteger_Scl2c: vf.add_const(value=1.0),
        scl_sclReferenceCurrent_power1_NInteger_Scl2c: vf.add_const(value=1.0),
        scl_pidOel_unitTime_Scl2c: vf.add_const(value=1.0),
        scl_pidUel_unitTime_Scl2c: vf.add_const(value=1.0),
    })

    external_mapping: dict[object, Var] = dict()

    api_obj_mapping: dict[object, Var] = dict()

    templ.block = Block(
        state_eqs=[
            (((vf.add_const(value=0.8) * scl_firstOrder_k_Scl2c) - scl_firstOrder_y_Scl2c) / scl_firstOrder_T_Scl2c),
            (((vf.add_const(value=0.8) * scl_firstOrder1_k_Scl2c) - scl_firstOrder1_y_Scl2c) / scl_firstOrder1_T_Scl2c),
            (((scl_firstOrder2_k_Scl2c * scl_division1_y_Scl2c) - scl_firstOrder2_y_Scl2c) / scl_firstOrder2_T_Scl2c),
            (((scl_firstOrder3_k_Scl2c * scl_division1_y_Scl2c) - scl_firstOrder3_y_Scl2c) / scl_firstOrder3_T_Scl2c),
            ((scl_firstOrder4_k_Scl2c - scl_firstOrder4_y_Scl2c) / scl_firstOrder4_T_Scl2c),
            (((vf.add_const(value=0.8000000000000003) * scl_firstOrder5_k_Scl2c) - scl_firstOrder5_y_Scl2c) / scl_firstOrder5_T_Scl2c),
            ((scl_pidOel_D_zeroGain_Scl2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - scl_pidOel_D_zeroGain_Scl2c) * ((scl_pidOel_addD_y_Scl2c - scl_pidOel_D_x_Scl2c) / scl_pidOel_D_T_Scl2c))),
            (((scl_limitedLeadLag2_firstOrder_k_Scl2c * scl_limitedLeadLag2_y_Scl2c) - scl_limitedLeadLag2_firstOrder_y_Scl2c) / scl_limitedLeadLag2_firstOrder_T_Scl2c),
            (((scl_limitedLeadLag3_firstOrder_k_Scl2c * scl_USclOelPu_Scl2c) - scl_limitedLeadLag3_firstOrder_y_Scl2c) / scl_limitedLeadLag3_firstOrder_T_Scl2c),
            (scl_pidOel_I_k_Scl2c * scl_pidOel_addI_y_Scl2c),
            (((vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator_y_Scl2c) - vf.add_const(value=1e-06))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator_y_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator_k_Scl2c * scl_sclReferenceCurrent_feedback_y_Scl2c)) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator_y_Scl2c) - vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator_k_Scl2c * scl_sclReferenceCurrent_feedback_y_Scl2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_y_Scl2c - scl_sclReferenceCurrent_limIntegrator_outMax_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator_y_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator_k_Scl2c * scl_sclReferenceCurrent_feedback_y_Scl2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_y_Scl2c - scl_sclReferenceCurrent_limIntegrator_outMax_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside((((scl_sclReferenceCurrent_limIntegrator_k_Scl2c * scl_sclReferenceCurrent_feedback_y_Scl2c) - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))))))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator_y_Scl2c) - vf.add_const(value=1e-06))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator_y_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator_k_Scl2c * scl_sclReferenceCurrent_feedback_y_Scl2c)) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator_y_Scl2c) - vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator_k_Scl2c * scl_sclReferenceCurrent_feedback_y_Scl2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_y_Scl2c - scl_sclReferenceCurrent_limIntegrator_outMax_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator_y_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator_k_Scl2c * scl_sclReferenceCurrent_feedback_y_Scl2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator_y_Scl2c - scl_sclReferenceCurrent_limIntegrator_outMax_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside((((scl_sclReferenceCurrent_limIntegrator_k_Scl2c * scl_sclReferenceCurrent_feedback_y_Scl2c) - vf.add_const(value=0.0)) - vf.add_const(value=1e-06)))))))) * (scl_sclReferenceCurrent_limIntegrator_k_Scl2c * scl_sclReferenceCurrent_feedback_y_Scl2c))),
            (((vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator1_y_Scl2c) - vf.add_const(value=1e-06))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator1_y_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator1_k_Scl2c * scl_sclReferenceCurrent_multiSwitch1_y_Scl2c)) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator1_y_Scl2c) - vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator1_k_Scl2c * scl_sclReferenceCurrent_multiSwitch1_y_Scl2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_y_Scl2c - scl_sclReferenceCurrent_limIntegrator1_outMax_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator1_y_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator1_k_Scl2c * scl_sclReferenceCurrent_multiSwitch1_y_Scl2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_y_Scl2c - scl_sclReferenceCurrent_limIntegrator1_outMax_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside((((scl_sclReferenceCurrent_limIntegrator1_k_Scl2c * scl_sclReferenceCurrent_multiSwitch1_y_Scl2c) - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))))))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator1_y_Scl2c) - vf.add_const(value=1e-06))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator1_y_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator1_k_Scl2c * scl_sclReferenceCurrent_multiSwitch1_y_Scl2c)) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator1_y_Scl2c) - vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator1_k_Scl2c * scl_sclReferenceCurrent_multiSwitch1_y_Scl2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_y_Scl2c - scl_sclReferenceCurrent_limIntegrator1_outMax_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_outMin_Scl2c - scl_sclReferenceCurrent_limIntegrator1_y_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (scl_sclReferenceCurrent_limIntegrator1_k_Scl2c * scl_sclReferenceCurrent_multiSwitch1_y_Scl2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclReferenceCurrent_limIntegrator1_y_Scl2c - scl_sclReferenceCurrent_limIntegrator1_outMax_Scl2c) - vf.add_const(value=1e-06)))) * sym.heaviside((((scl_sclReferenceCurrent_limIntegrator1_k_Scl2c * scl_sclReferenceCurrent_multiSwitch1_y_Scl2c) - vf.add_const(value=0.0)) - vf.add_const(value=1e-06)))))))) * (scl_sclReferenceCurrent_limIntegrator1_k_Scl2c * scl_sclReferenceCurrent_multiSwitch1_y_Scl2c))),
            (((scl_firstOrder7_k_Scl2c * scl_sclReferenceCurrent_IRefPu_Scl2c) - scl_firstOrder7_y_Scl2c) / scl_firstOrder7_T_Scl2c),
            (((vf.add_const(value=0.8) * scl_firstOrder6_k_Scl2c) - scl_firstOrder6_y_Scl2c) / scl_firstOrder6_T_Scl2c),
            ((scl_pidUel_D_zeroGain_Scl2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - scl_pidUel_D_zeroGain_Scl2c) * ((scl_pidUel_addD_y_Scl2c - scl_pidUel_D_x_Scl2c) / scl_pidUel_D_T_Scl2c))),
            (((scl_limitedLeadLag_firstOrder_k_Scl2c * scl_limitedLeadLag_y_Scl2c) - scl_limitedLeadLag_firstOrder_y_Scl2c) / scl_limitedLeadLag_firstOrder_T_Scl2c),
            (((scl_limitedLeadLag1_firstOrder_k_Scl2c * scl_USclUelPu_Scl2c) - scl_limitedLeadLag1_firstOrder_y_Scl2c) / scl_limitedLeadLag1_firstOrder_T_Scl2c),
            (scl_pidUel_I_k_Scl2c * scl_pidUel_addI_y_Scl2c),
        ],
        state_vars=[
            scl_firstOrder_y_Scl2c,
            scl_firstOrder1_y_Scl2c,
            scl_firstOrder2_y_Scl2c,
            scl_firstOrder3_y_Scl2c,
            scl_firstOrder4_y_Scl2c,
            scl_firstOrder5_y_Scl2c,
            scl_pidOel_D_x_Scl2c,
            scl_limitedLeadLag2_firstOrder_y_Scl2c,
            scl_limitedLeadLag3_firstOrder_y_Scl2c,
            scl_pidOel_I_y_Scl2c,
            scl_sclReferenceCurrent_limIntegrator_y_Scl2c,
            scl_sclReferenceCurrent_limIntegrator1_y_Scl2c,
            scl_firstOrder7_y_Scl2c,
            scl_firstOrder6_y_Scl2c,
            scl_pidUel_D_x_Scl2c,
            scl_limitedLeadLag_firstOrder_y_Scl2c,
            scl_limitedLeadLag1_firstOrder_y_Scl2c,
            scl_pidUel_I_y_Scl2c,
        ],
        algebraic_eqs=[
            (scl_pythagoras_y2_Scl2c - ((scl_firstOrder_y_Scl2c ** vf.add_const(value=2.0)) + (scl_firstOrder3_y_Scl2c ** vf.add_const(value=2.0)))),
            (scl_pythagoras_y_Scl2c - (scl_pythagoras_y2_Scl2c ** vf.add_const(value=0.5))),
            (scl_pythagoras1_y2_Scl2c - ((scl_firstOrder2_y_Scl2c ** vf.add_const(value=2.0)) + (scl_firstOrder1_y_Scl2c ** vf.add_const(value=2.0)))),
            (scl_pythagoras1_y_Scl2c - (scl_pythagoras1_y2_Scl2c ** vf.add_const(value=0.5))),
            (whenCondition2_Scl2c - sym.heaviside(((scl_pythagoras1_y_Scl2c - scl_firstOrder7_y_Scl2c) - vf.add_const(value=1e-06)))),
            (scl_sclOelActivation_timer_y_Scl2c - ((whenCondition2_Scl2c * (time_Scl2c - scl_sclOelActivation_timer_entryTime_Scl2c)) + ((vf.add_const(value=1.0) - whenCondition2_Scl2c) * vf.add_const(value=0.0)))),
            (scl_sclOelActivation_timer_u_Scl2c - whenCondition2_Scl2c),
            (whenCondition1_Scl2c - sym.heaviside(((scl_firstOrder7_y_Scl2c - (scl_pythagoras1_y_Scl2c + scl_sclOelActivation_IThOffPu_Scl2c)) - vf.add_const(value=1e-06)))),
            (scl_sclOelActivation_timer1_y_Scl2c - ((whenCondition1_Scl2c * (time_Scl2c - scl_sclOelActivation_timer1_entryTime_Scl2c)) + ((vf.add_const(value=1.0) - whenCondition1_Scl2c) * vf.add_const(value=0.0)))),
            (scl_sclOelActivation_timer1_u_Scl2c - whenCondition1_Scl2c),
            (scl_add_y_Scl2c - ((scl_add_k1_Scl2c * scl_firstOrder3_y_Scl2c) + (scl_add_k2_Scl2c * scl_const_k_Scl2c))),
            (scl_max1_u_1_Scl2c - ((scl_add1_k1_Scl2c * scl_const1_k_Scl2c) + (scl_add1_k2_Scl2c * scl_firstOrder2_y_Scl2c))),
            (scl_max1_u_3_Scl2c - ((scl_add2_k1_Scl2c * scl_const2_k_Scl2c) + (scl_add2_k2_Scl2c * scl_firstOrder4_y_Scl2c))),
            (scl_sclReferenceCurrent_tErr_Scl2c - (scl_sclReferenceCurrent_const3_k_Scl2c - scl_sclReferenceCurrent_limIntegrator_y_Scl2c)),
            (scl_sclReferenceCurrent_multiSwitch1_u_1_Scl2c - sym.heaviside(((scl_sclReferenceCurrent_tErr_Scl2c - scl_sclReferenceCurrent_greaterEqualThreshold_threshold_Scl2c) + vf.add_const(value=1e-06)))),
            (scl_sclReferenceCurrent_lessEqualThreshold1_y_Scl2c - sym.heaviside(((scl_sclReferenceCurrent_lessEqualThreshold1_threshold_Scl2c - scl_sclReferenceCurrent_tErr_Scl2c) + vf.add_const(value=1e-06)))),
            (scl_sclOelActivation_IOelBiasPu_Scl2c - (((vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - (sym.heaviside(((scl_firstOrder4_y_Scl2c - scl_sclOelActivation_VtMinPu_Scl2c) - vf.add_const(value=1e-06))) * (vf.add_const(value=1.0) - (((((vf.add_const(value=1.0) - sym.heaviside(((scl_firstOrder4_y_Scl2c - scl_sclOelActivation_VtMinPu_Scl2c) - vf.add_const(value=1e-06)))) * (vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_tErr_Scl2c) + vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_firstOrder4_y_Scl2c - scl_sclOelActivation_VtMinPu_Scl2c) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_tErr_Scl2c) + vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_sclOelActivation_timer_y_Scl2c - scl_sclOelActivation_tEnOel_Scl2c) + vf.add_const(value=1e-06)))))))) * (vf.add_const(value=1.0) - (sym.heaviside(((scl_sclOelActivation_tEnOel_Scl2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - scl_sclOelActivation_tEnOel_Scl2c) + vf.add_const(value=1e-06))))))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - (sym.heaviside(((scl_firstOrder4_y_Scl2c - scl_sclOelActivation_VtMinPu_Scl2c) - vf.add_const(value=1e-06))) * (vf.add_const(value=1.0) - (((((vf.add_const(value=1.0) - sym.heaviside(((scl_firstOrder4_y_Scl2c - scl_sclOelActivation_VtMinPu_Scl2c) - vf.add_const(value=1e-06)))) * (vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_tErr_Scl2c) + vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_firstOrder4_y_Scl2c - scl_sclOelActivation_VtMinPu_Scl2c) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_tErr_Scl2c) + vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_sclOelActivation_timer_y_Scl2c - scl_sclOelActivation_tEnOel_Scl2c) + vf.add_const(value=1e-06)))))))) * (vf.add_const(value=1.0) - (sym.heaviside(((scl_sclOelActivation_tEnOel_Scl2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - scl_sclOelActivation_tEnOel_Scl2c) + vf.add_const(value=1e-06)))))))) * (((vf.add_const(value=1.0) - (((vf.add_const(value=1.0) - ((sym.heaviside(((scl_firstOrder7_y_Scl2c - scl_sclOelActivation_IInstPu_Scl2c) + vf.add_const(value=1e-06))) * sym.heaviside(((scl_sclOelActivation_IInstPu_Scl2c - scl_firstOrder7_y_Scl2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclOelActivation_timer1_y_Scl2c - scl_sclOelActivation_tOff_Scl2c) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_sclOelActivation_timer1_y_Scl2c - scl_sclOelActivation_tOff_Scl2c) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_sclOelActivation_VtResetPu_Scl2c - scl_firstOrder4_y_Scl2c) - vf.add_const(value=1e-06)))))) * scl_sclOelActivation_IResetPu_Scl2c) + ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - (((vf.add_const(value=1.0) - ((sym.heaviside(((scl_firstOrder7_y_Scl2c - scl_sclOelActivation_IInstPu_Scl2c) + vf.add_const(value=1e-06))) * sym.heaviside(((scl_sclOelActivation_IInstPu_Scl2c - scl_firstOrder7_y_Scl2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclOelActivation_timer1_y_Scl2c - scl_sclOelActivation_tOff_Scl2c) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_sclOelActivation_timer1_y_Scl2c - scl_sclOelActivation_tOff_Scl2c) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_sclOelActivation_VtResetPu_Scl2c - scl_firstOrder4_y_Scl2c) - vf.add_const(value=1e-06))))))) * vf.add_const(value=0.0)))))),
            (scl_max1_u_2_Scl2c - ((scl_add31_k1_Scl2c * scl_sclOelActivation_IOelBiasPu_Scl2c) + ((scl_add31_k2_Scl2c * scl_pythagoras1_y_Scl2c) + (scl_add31_k3_Scl2c * scl_firstOrder7_y_Scl2c)))),
            (scl_max1_yMin_Scl2c - ((((scl_max1_u_1_Scl2c * sym.heaviside((scl_max1_u_2_Scl2c - scl_max1_u_1_Scl2c))) + (scl_max1_u_2_Scl2c * (vf.add_const(value=1) - sym.heaviside((scl_max1_u_2_Scl2c - scl_max1_u_1_Scl2c))))) * sym.heaviside((scl_max1_u_3_Scl2c - ((scl_max1_u_1_Scl2c * sym.heaviside((scl_max1_u_2_Scl2c - scl_max1_u_1_Scl2c))) + (scl_max1_u_2_Scl2c * (vf.add_const(value=1) - sym.heaviside((scl_max1_u_2_Scl2c - scl_max1_u_1_Scl2c)))))))) + (scl_max1_u_3_Scl2c * (vf.add_const(value=1) - sym.heaviside((scl_max1_u_3_Scl2c - ((scl_max1_u_1_Scl2c * sym.heaviside((scl_max1_u_2_Scl2c - scl_max1_u_1_Scl2c))) + (scl_max1_u_2_Scl2c * (vf.add_const(value=1) - sym.heaviside((scl_max1_u_2_Scl2c - scl_max1_u_1_Scl2c))))))))))),
            (scl_pidOel_controlError_Scl2c - ((((scl_max1_u_1_Scl2c * sym.heaviside((scl_max1_u_1_Scl2c - scl_max1_u_2_Scl2c))) + (scl_max1_u_2_Scl2c * (vf.add_const(value=1) - sym.heaviside((scl_max1_u_1_Scl2c - scl_max1_u_2_Scl2c))))) * sym.heaviside((((scl_max1_u_1_Scl2c * sym.heaviside((scl_max1_u_1_Scl2c - scl_max1_u_2_Scl2c))) + (scl_max1_u_2_Scl2c * (vf.add_const(value=1) - sym.heaviside((scl_max1_u_1_Scl2c - scl_max1_u_2_Scl2c))))) - scl_max1_u_3_Scl2c))) + (scl_max1_u_3_Scl2c * (vf.add_const(value=1) - sym.heaviside((((scl_max1_u_1_Scl2c * sym.heaviside((scl_max1_u_1_Scl2c - scl_max1_u_2_Scl2c))) + (scl_max1_u_2_Scl2c * (vf.add_const(value=1) - sym.heaviside((scl_max1_u_1_Scl2c - scl_max1_u_2_Scl2c))))) - scl_max1_u_3_Scl2c)))))),
            (scl_pidOel_addP_y_Scl2c - (scl_pidOel_addP_k1_Scl2c * scl_pidOel_controlError_Scl2c)),
            (scl_pidOel_P_y_Scl2c - (scl_pidOel_P_k_Scl2c * scl_pidOel_addP_y_Scl2c)),
            (scl_pidOel_addD_y_Scl2c - (scl_pidOel_addD_k1_Scl2c * scl_pidOel_controlError_Scl2c)),
            (scl_pidOel_D_y_Scl2c - ((scl_pidOel_D_zeroGain_Scl2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - scl_pidOel_D_zeroGain_Scl2c) * ((scl_pidOel_D_k_Scl2c / scl_pidOel_D_T_Scl2c) * (scl_pidOel_addD_y_Scl2c - scl_pidOel_D_x_Scl2c))))),
            (scl_pidOel_addPID_y_Scl2c - ((scl_pidOel_addPID_k1_Scl2c * scl_pidOel_P_y_Scl2c) + ((scl_pidOel_addPID_k2_Scl2c * scl_pidOel_D_y_Scl2c) + (scl_pidOel_addPID_k3_Scl2c * scl_pidOel_I_y_Scl2c)))),
            (scl_pidOel_gainPID_y_Scl2c - (scl_pidOel_gainPID_k_Scl2c * scl_pidOel_addPID_y_Scl2c)),
            (scl_pidOel_limiter_u_Scl2c - ((scl_pidOel_addFF_k1_Scl2c * scl_pidOel_gainPID_y_Scl2c) + (scl_pidOel_addFF_k2_Scl2c * scl_pidOel_FFzero_k_Scl2c))),
            (scl_pidOel_y_Scl2c - ((sym.heaviside(((scl_pidOel_limiter_u_Scl2c - scl_pidOel_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_pidOel_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_pidOel_limiter_u_Scl2c - scl_pidOel_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_pidOel_limiter_uMin_Scl2c - scl_pidOel_limiter_u_Scl2c) - vf.add_const(value=1e-06))) * scl_pidOel_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_pidOel_limiter_uMin_Scl2c - scl_pidOel_limiter_u_Scl2c) - vf.add_const(value=1e-06)))) * scl_pidOel_limiter_u_Scl2c))))),
            (scl_limitedLeadLag2_feedback_y_Scl2c - (scl_pidOel_y_Scl2c - scl_limitedLeadLag2_firstOrder_y_Scl2c)),
            (scl_limitedLeadLag2_gain_y_Scl2c - (scl_limitedLeadLag2_gain_k_Scl2c * scl_limitedLeadLag2_feedback_y_Scl2c)),
            (scl_limitedLeadLag2_y_Scl2c - ((sym.heaviside(((scl_limitedLeadLag2_gain_y_Scl2c - scl_limitedLeadLag2_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_limitedLeadLag2_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limitedLeadLag2_gain_y_Scl2c - scl_limitedLeadLag2_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_limitedLeadLag2_limiter_uMin_Scl2c - scl_limitedLeadLag2_gain_y_Scl2c) - vf.add_const(value=1e-06))) * scl_limitedLeadLag2_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limitedLeadLag2_limiter_uMin_Scl2c - scl_limitedLeadLag2_gain_y_Scl2c) - vf.add_const(value=1e-06)))) * scl_limitedLeadLag2_gain_y_Scl2c))))),
            (scl_limitedLeadLag3_feedback_y_Scl2c - (scl_limitedLeadLag2_y_Scl2c - scl_limitedLeadLag3_firstOrder_y_Scl2c)),
            (scl_limitedLeadLag3_gain_y_Scl2c - (scl_limitedLeadLag3_gain_k_Scl2c * scl_limitedLeadLag3_feedback_y_Scl2c)),
            (scl_USclOelPu_Scl2c - ((sym.heaviside(((scl_limitedLeadLag3_gain_y_Scl2c - scl_limitedLeadLag3_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_limitedLeadLag3_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limitedLeadLag3_gain_y_Scl2c - scl_limitedLeadLag3_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_limitedLeadLag3_limiter_uMin_Scl2c - scl_limitedLeadLag3_gain_y_Scl2c) - vf.add_const(value=1e-06))) * scl_limitedLeadLag3_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limitedLeadLag3_limiter_uMin_Scl2c - scl_limitedLeadLag3_gain_y_Scl2c) - vf.add_const(value=1e-06)))) * scl_limitedLeadLag3_gain_y_Scl2c))))),
            (scl_pidOel_addSat_y_Scl2c - ((scl_pidOel_addSat_k1_Scl2c * scl_pidOel_y_Scl2c) + (scl_pidOel_addSat_k2_Scl2c * scl_pidOel_limiter_u_Scl2c))),
            (scl_pidOel_gainTrack_y_Scl2c - (scl_pidOel_gainTrack_k_Scl2c * scl_pidOel_addSat_y_Scl2c)),
            (scl_pidOel_addI_y_Scl2c - ((scl_pidOel_addI_k1_Scl2c * scl_pidOel_controlError_Scl2c) + (scl_pidOel_addI_k3_Scl2c * scl_pidOel_gainTrack_y_Scl2c))),
            (scl_sclReferenceCurrent_gain_y_Scl2c - (scl_sclReferenceCurrent_gain_k_Scl2c * scl_firstOrder5_y_Scl2c)),
            (scl_sclReferenceCurrent_power1_y_Scl2c - (scl_sclReferenceCurrent_gain_y_Scl2c ** scl_sclReferenceCurrent_power1_N_Scl2c)),
            (scl_sclReferenceCurrent_feedback1_y_Scl2c - (scl_sclReferenceCurrent_power1_y_Scl2c - scl_sclReferenceCurrent_const_k_Scl2c)),
            (scl_sclReferenceCurrent_gain1_y_Scl2c - (scl_sclReferenceCurrent_gain1_k_Scl2c * scl_sclReferenceCurrent_feedback1_y_Scl2c)),
            (scl_sclReferenceCurrent_multiSwitch1_expr_2_Scl2c - ((scl_sclReferenceCurrent_booleanConstant_k_Scl2c * scl_sclReferenceCurrent_gain1_y_Scl2c) + ((vf.add_const(value=1.0) - scl_sclReferenceCurrent_booleanConstant_k_Scl2c) * scl_sclReferenceCurrent_const4_k_Scl2c))),
            (scl_sclReferenceCurrent_multiSwitch1_expr_1_Scl2c - ((scl_sclReferenceCurrent_booleanConstant_k_Scl2c * scl_sclReferenceCurrent_gain1_y_Scl2c) + ((vf.add_const(value=1.0) - scl_sclReferenceCurrent_booleanConstant_k_Scl2c) * scl_sclReferenceCurrent_const5_k_Scl2c))),
            (scl_sclReferenceCurrent_power_y_Scl2c - (scl_sclReferenceCurrent_gain_y_Scl2c ** scl_sclReferenceCurrent_power_N_Scl2c)),
            (scl_sclReferenceCurrent_feedback2_y_Scl2c - (scl_sclReferenceCurrent_power_y_Scl2c - scl_sclReferenceCurrent_const_k_Scl2c)),
            (scl_sclReferenceCurrent_gain2_y_Scl2c - (scl_sclReferenceCurrent_gain2_k_Scl2c * scl_sclReferenceCurrent_feedback2_y_Scl2c)),
            (scl_sclReferenceCurrent_limiter_y_Scl2c - ((sym.heaviside(((scl_sclReferenceCurrent_gain2_y_Scl2c - scl_sclReferenceCurrent_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_sclReferenceCurrent_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_sclReferenceCurrent_gain2_y_Scl2c - scl_sclReferenceCurrent_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_sclReferenceCurrent_limiter_uMin_Scl2c - scl_sclReferenceCurrent_gain2_y_Scl2c) - vf.add_const(value=1e-06))) * scl_sclReferenceCurrent_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_sclReferenceCurrent_limiter_uMin_Scl2c - scl_sclReferenceCurrent_gain2_y_Scl2c) - vf.add_const(value=1e-06)))) * scl_sclReferenceCurrent_gain2_y_Scl2c))))),
            (scl_sclReferenceCurrent_lessEqualThreshold_y_Scl2c - sym.heaviside(((scl_sclReferenceCurrent_lessEqualThreshold_threshold_Scl2c - scl_sclReferenceCurrent_gain_y_Scl2c) + vf.add_const(value=1e-06)))),
            (scl_sclReferenceCurrent_switch_y_Scl2c - ((scl_sclReferenceCurrent_lessEqualThreshold_y_Scl2c * scl_sclReferenceCurrent_const1_k_Scl2c) + ((vf.add_const(value=1.0) - scl_sclReferenceCurrent_lessEqualThreshold_y_Scl2c) * scl_sclReferenceCurrent_const2_k_Scl2c))),
            (scl_sclReferenceCurrent_add_y_Scl2c - ((scl_sclReferenceCurrent_add_k1_Scl2c * scl_sclReferenceCurrent_limiter_y_Scl2c) + (scl_sclReferenceCurrent_add_k2_Scl2c * scl_sclReferenceCurrent_switch_y_Scl2c))),
            (scl_sclReferenceCurrent_gain3_y_Scl2c - (scl_sclReferenceCurrent_gain3_k_Scl2c * scl_sclReferenceCurrent_limIntegrator_y_Scl2c)),
            (scl_sclReferenceCurrent_feedback_y_Scl2c - (scl_sclReferenceCurrent_add_y_Scl2c - scl_sclReferenceCurrent_gain3_y_Scl2c)),
            (scl_sclReferenceCurrent_lessThreshold_y_Scl2c - sym.heaviside(((scl_sclReferenceCurrent_lessThreshold_threshold_Scl2c - scl_firstOrder4_y_Scl2c) - vf.add_const(value=1e-06)))),
            (scl_sclReferenceCurrent_multiSwitch1_u_2_Scl2c - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - scl_sclReferenceCurrent_lessEqualThreshold1_y_Scl2c) * (vf.add_const(value=1.0) - scl_sclReferenceCurrent_lessThreshold_y_Scl2c)))),
            (scl_sclReferenceCurrent_multiSwitch1_firstActiveIndex_Scl2c - ((vf.add_const(value=0.0) + ((vf.add_const(value=1.0) * scl_sclReferenceCurrent_multiSwitch1_u_1_Scl2c) * vf.add_const(value=1.0))) + ((vf.add_const(value=2.0) * scl_sclReferenceCurrent_multiSwitch1_u_2_Scl2c) * (vf.add_const(value=1.0) - scl_sclReferenceCurrent_multiSwitch1_u_1_Scl2c)))),
            (scl_sclReferenceCurrent_multiSwitch1_y_Scl2c - (((sym.heaviside(((scl_sclReferenceCurrent_multiSwitch1_firstActiveIndex_Scl2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_multiSwitch1_firstActiveIndex_Scl2c) + vf.add_const(value=1e-06)))) * scl_sclReferenceCurrent_multiSwitch1_y_default_Scl2c) + ((vf.add_const(value=1.0) - (sym.heaviside(((scl_sclReferenceCurrent_multiSwitch1_firstActiveIndex_Scl2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_multiSwitch1_firstActiveIndex_Scl2c) + vf.add_const(value=1e-06))))) * scl_sclReferenceCurrent_multiSwitch1_expr_Scl2c))),
            (scl_complexToPolar1_len_Scl2c - (((scl_utPu_re_Scl2c ** vf.add_const(value=2.0)) + (scl_utPu_im_Scl2c ** vf.add_const(value=2.0))) ** vf.add_const(value=0.5))),
            (scl_division1_y_Scl2c - (scl_QGenPu_Scl2c / scl_complexToPolar1_len_Scl2c)),
            (scl_sclReferenceCurrent_IRefPu_Scl2c - ((((sym.heaviside(((scl_sclReferenceCurrent_KPRef_Scl2c - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))) * sym.heaviside(((scl_sclReferenceCurrent_KPRef_Scl2c - vf.add_const(value=0.0)) - vf.add_const(value=1e-06)))) * sym.heaviside((((scl_sclReferenceCurrent_limIntegrator1_y_Scl2c ** vf.add_const(value=2.0)) - (scl_firstOrder6_y_Scl2c ** vf.add_const(value=2.0))) - vf.add_const(value=1e-06)))) * sym.sqrt(((scl_sclReferenceCurrent_limIntegrator1_y_Scl2c ** vf.add_const(value=2.0)) - (scl_firstOrder6_y_Scl2c ** vf.add_const(value=2.0))))) + ((vf.add_const(value=1.0) - ((sym.heaviside(((scl_sclReferenceCurrent_KPRef_Scl2c - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))) * sym.heaviside(((scl_sclReferenceCurrent_KPRef_Scl2c - vf.add_const(value=0.0)) - vf.add_const(value=1e-06)))) * sym.heaviside((((scl_sclReferenceCurrent_limIntegrator1_y_Scl2c ** vf.add_const(value=2.0)) - (scl_firstOrder6_y_Scl2c ** vf.add_const(value=2.0))) - vf.add_const(value=1e-06))))) * scl_sclReferenceCurrent_limIntegrator1_y_Scl2c))),
            (scl_limiter_y_Scl2c - ((sym.heaviside(((scl_firstOrder7_y_Scl2c - scl_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_firstOrder7_y_Scl2c - scl_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_limiter_uMin_Scl2c - scl_firstOrder7_y_Scl2c) - vf.add_const(value=1e-06))) * scl_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limiter_uMin_Scl2c - scl_firstOrder7_y_Scl2c) - vf.add_const(value=1e-06)))) * scl_firstOrder7_y_Scl2c))))),
            (whenCondition4_Scl2c - sym.heaviside(((scl_pythagoras_y_Scl2c - scl_limiter_y_Scl2c) - vf.add_const(value=1e-06)))),
            (scl_sclUelActivation_timer_y_Scl2c - ((whenCondition4_Scl2c * (time_Scl2c - scl_sclUelActivation_timer_entryTime_Scl2c)) + ((vf.add_const(value=1.0) - whenCondition4_Scl2c) * vf.add_const(value=0.0)))),
            (scl_sclUelActivation_timer_u_Scl2c - whenCondition4_Scl2c),
            (whenCondition3_Scl2c - sym.heaviside(((scl_limiter_y_Scl2c - (scl_pythagoras_y_Scl2c + scl_sclUelActivation_IThOffPu_Scl2c)) - vf.add_const(value=1e-06)))),
            (scl_sclUelActivation_timer1_y_Scl2c - ((whenCondition3_Scl2c * (time_Scl2c - scl_sclUelActivation_timer1_entryTime_Scl2c)) + ((vf.add_const(value=1.0) - whenCondition3_Scl2c) * vf.add_const(value=0.0)))),
            (scl_sclUelActivation_timer1_u_Scl2c - whenCondition3_Scl2c),
            (scl_sclUelActivation_IUelBiasPu_Scl2c - (((vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - (((vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_tErr_Scl2c) + vf.add_const(value=1e-06)))) * (vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_tErr_Scl2c) + vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_sclUelActivation_timer_y_Scl2c - scl_sclUelActivation_tEnUel_Scl2c) + vf.add_const(value=1e-06))))))) * (vf.add_const(value=1.0) - (sym.heaviside(((scl_sclUelActivation_tEnUel_Scl2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - scl_sclUelActivation_tEnUel_Scl2c) + vf.add_const(value=1e-06))))))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - (((vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_tErr_Scl2c) + vf.add_const(value=1e-06)))) * (vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - scl_sclReferenceCurrent_tErr_Scl2c) + vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((scl_sclUelActivation_timer_y_Scl2c - scl_sclUelActivation_tEnUel_Scl2c) + vf.add_const(value=1e-06))))))) * (vf.add_const(value=1.0) - (sym.heaviside(((scl_sclUelActivation_tEnUel_Scl2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - scl_sclUelActivation_tEnUel_Scl2c) + vf.add_const(value=1e-06)))))))) * ((((sym.heaviside(((scl_limiter_y_Scl2c - scl_sclUelActivation_IInstUelPu_Scl2c) + vf.add_const(value=1e-06))) * sym.heaviside(((scl_limiter_y_Scl2c - scl_sclUelActivation_IInstUelPu_Scl2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclUelActivation_timer1_y_Scl2c - scl_sclUelActivation_tOff_Scl2c) - vf.add_const(value=1e-06)))) * scl_sclUelActivation_IResetPu_Scl2c) + ((vf.add_const(value=1.0) - ((sym.heaviside(((scl_limiter_y_Scl2c - scl_sclUelActivation_IInstUelPu_Scl2c) + vf.add_const(value=1e-06))) * sym.heaviside(((scl_limiter_y_Scl2c - scl_sclUelActivation_IInstUelPu_Scl2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((scl_sclUelActivation_timer1_y_Scl2c - scl_sclUelActivation_tOff_Scl2c) - vf.add_const(value=1e-06))))) * vf.add_const(value=0.0)))))),
            (scl_add3_y_Scl2c - ((scl_add3_k1_Scl2c * scl_sclUelActivation_IUelBiasPu_Scl2c) + ((scl_add3_k2_Scl2c * scl_pythagoras_y_Scl2c) + (scl_add3_k3_Scl2c * scl_limiter_y_Scl2c)))),
            (scl_pidUel_controlError_Scl2c - ((scl_add3_y_Scl2c * sym.heaviside((scl_add_y_Scl2c - scl_add3_y_Scl2c))) + (scl_add_y_Scl2c * (vf.add_const(value=1) - sym.heaviside((scl_add_y_Scl2c - scl_add3_y_Scl2c)))))),
            (scl_pidUel_addP_y_Scl2c - (scl_pidUel_addP_k1_Scl2c * scl_pidUel_controlError_Scl2c)),
            (scl_pidUel_P_y_Scl2c - (scl_pidUel_P_k_Scl2c * scl_pidUel_addP_y_Scl2c)),
            (scl_pidUel_addD_y_Scl2c - (scl_pidUel_addD_k1_Scl2c * scl_pidUel_controlError_Scl2c)),
            (scl_pidUel_D_y_Scl2c - ((scl_pidUel_D_zeroGain_Scl2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - scl_pidUel_D_zeroGain_Scl2c) * ((scl_pidUel_D_k_Scl2c / scl_pidUel_D_T_Scl2c) * (scl_pidUel_addD_y_Scl2c - scl_pidUel_D_x_Scl2c))))),
            (scl_pidUel_addPID_y_Scl2c - ((scl_pidUel_addPID_k1_Scl2c * scl_pidUel_P_y_Scl2c) + ((scl_pidUel_addPID_k2_Scl2c * scl_pidUel_D_y_Scl2c) + (scl_pidUel_addPID_k3_Scl2c * scl_pidUel_I_y_Scl2c)))),
            (scl_pidUel_gainPID_y_Scl2c - (scl_pidUel_gainPID_k_Scl2c * scl_pidUel_addPID_y_Scl2c)),
            (scl_pidUel_limiter_u_Scl2c - ((scl_pidUel_addFF_k1_Scl2c * scl_pidUel_gainPID_y_Scl2c) + (scl_pidUel_addFF_k2_Scl2c * scl_pidUel_FFzero_k_Scl2c))),
            (scl_pidUel_y_Scl2c - ((sym.heaviside(((scl_pidUel_limiter_u_Scl2c - scl_pidUel_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_pidUel_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_pidUel_limiter_u_Scl2c - scl_pidUel_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_pidUel_limiter_uMin_Scl2c - scl_pidUel_limiter_u_Scl2c) - vf.add_const(value=1e-06))) * scl_pidUel_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_pidUel_limiter_uMin_Scl2c - scl_pidUel_limiter_u_Scl2c) - vf.add_const(value=1e-06)))) * scl_pidUel_limiter_u_Scl2c))))),
            (scl_limitedLeadLag_feedback_y_Scl2c - (scl_pidUel_y_Scl2c - scl_limitedLeadLag_firstOrder_y_Scl2c)),
            (scl_limitedLeadLag_gain_y_Scl2c - (scl_limitedLeadLag_gain_k_Scl2c * scl_limitedLeadLag_feedback_y_Scl2c)),
            (scl_limitedLeadLag_y_Scl2c - ((sym.heaviside(((scl_limitedLeadLag_gain_y_Scl2c - scl_limitedLeadLag_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_limitedLeadLag_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limitedLeadLag_gain_y_Scl2c - scl_limitedLeadLag_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_limitedLeadLag_limiter_uMin_Scl2c - scl_limitedLeadLag_gain_y_Scl2c) - vf.add_const(value=1e-06))) * scl_limitedLeadLag_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limitedLeadLag_limiter_uMin_Scl2c - scl_limitedLeadLag_gain_y_Scl2c) - vf.add_const(value=1e-06)))) * scl_limitedLeadLag_gain_y_Scl2c))))),
            (scl_limitedLeadLag1_feedback_y_Scl2c - (scl_limitedLeadLag_y_Scl2c - scl_limitedLeadLag1_firstOrder_y_Scl2c)),
            (scl_limitedLeadLag1_gain_y_Scl2c - (scl_limitedLeadLag1_gain_k_Scl2c * scl_limitedLeadLag1_feedback_y_Scl2c)),
            (scl_USclUelPu_Scl2c - ((sym.heaviside(((scl_limitedLeadLag1_gain_y_Scl2c - scl_limitedLeadLag1_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_limitedLeadLag1_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limitedLeadLag1_gain_y_Scl2c - scl_limitedLeadLag1_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_limitedLeadLag1_limiter_uMin_Scl2c - scl_limitedLeadLag1_gain_y_Scl2c) - vf.add_const(value=1e-06))) * scl_limitedLeadLag1_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_limitedLeadLag1_limiter_uMin_Scl2c - scl_limitedLeadLag1_gain_y_Scl2c) - vf.add_const(value=1e-06)))) * scl_limitedLeadLag1_gain_y_Scl2c))))),
            (scl_pidUel_addSat_y_Scl2c - ((scl_pidUel_addSat_k1_Scl2c * scl_pidUel_y_Scl2c) + (scl_pidUel_addSat_k2_Scl2c * scl_pidUel_limiter_u_Scl2c))),
            (scl_pidUel_gainTrack_y_Scl2c - (scl_pidUel_gainTrack_k_Scl2c * scl_pidUel_addSat_y_Scl2c)),
            (scl_pidUel_addI_y_Scl2c - ((scl_pidUel_addI_k1_Scl2c * scl_pidUel_controlError_Scl2c) + (scl_pidUel_addI_k3_Scl2c * scl_pidUel_gainTrack_y_Scl2c))),
        ],
        algebraic_vars=[
            scl_pythagoras_y2_Scl2c,
            scl_pythagoras_y_Scl2c,
            scl_pythagoras1_y2_Scl2c,
            scl_pythagoras1_y_Scl2c,
            whenCondition2_Scl2c,
            scl_sclOelActivation_timer_y_Scl2c,
            scl_sclOelActivation_timer_u_Scl2c,
            whenCondition1_Scl2c,
            scl_sclOelActivation_timer1_y_Scl2c,
            scl_sclOelActivation_timer1_u_Scl2c,
            scl_add_y_Scl2c,
            scl_max1_u_1_Scl2c,
            scl_max1_u_3_Scl2c,
            scl_sclReferenceCurrent_tErr_Scl2c,
            scl_sclReferenceCurrent_multiSwitch1_u_1_Scl2c,
            scl_sclReferenceCurrent_lessEqualThreshold1_y_Scl2c,
            scl_sclOelActivation_IOelBiasPu_Scl2c,
            scl_max1_u_2_Scl2c,
            scl_max1_yMin_Scl2c,
            scl_pidOel_controlError_Scl2c,
            scl_pidOel_addP_y_Scl2c,
            scl_pidOel_P_y_Scl2c,
            scl_pidOel_addD_y_Scl2c,
            scl_pidOel_D_y_Scl2c,
            scl_pidOel_addPID_y_Scl2c,
            scl_pidOel_gainPID_y_Scl2c,
            scl_pidOel_limiter_u_Scl2c,
            scl_pidOel_y_Scl2c,
            scl_limitedLeadLag2_feedback_y_Scl2c,
            scl_limitedLeadLag2_gain_y_Scl2c,
            scl_limitedLeadLag2_y_Scl2c,
            scl_limitedLeadLag3_feedback_y_Scl2c,
            scl_limitedLeadLag3_gain_y_Scl2c,
            scl_USclOelPu_Scl2c,
            scl_pidOel_addSat_y_Scl2c,
            scl_pidOel_gainTrack_y_Scl2c,
            scl_pidOel_addI_y_Scl2c,
            scl_sclReferenceCurrent_gain_y_Scl2c,
            scl_sclReferenceCurrent_power1_y_Scl2c,
            scl_sclReferenceCurrent_feedback1_y_Scl2c,
            scl_sclReferenceCurrent_gain1_y_Scl2c,
            scl_sclReferenceCurrent_multiSwitch1_expr_2_Scl2c,
            scl_sclReferenceCurrent_multiSwitch1_expr_1_Scl2c,
            scl_sclReferenceCurrent_power_y_Scl2c,
            scl_sclReferenceCurrent_feedback2_y_Scl2c,
            scl_sclReferenceCurrent_gain2_y_Scl2c,
            scl_sclReferenceCurrent_limiter_y_Scl2c,
            scl_sclReferenceCurrent_lessEqualThreshold_y_Scl2c,
            scl_sclReferenceCurrent_switch_y_Scl2c,
            scl_sclReferenceCurrent_add_y_Scl2c,
            scl_sclReferenceCurrent_gain3_y_Scl2c,
            scl_sclReferenceCurrent_feedback_y_Scl2c,
            scl_sclReferenceCurrent_lessThreshold_y_Scl2c,
            scl_sclReferenceCurrent_multiSwitch1_u_2_Scl2c,
            scl_sclReferenceCurrent_multiSwitch1_firstActiveIndex_Scl2c,
            scl_sclReferenceCurrent_multiSwitch1_y_Scl2c,
            scl_sclReferenceCurrent_IRefPu_Scl2c,
            scl_limiter_y_Scl2c,
            whenCondition4_Scl2c,
            scl_sclUelActivation_timer_y_Scl2c,
            scl_sclUelActivation_timer_u_Scl2c,
            whenCondition3_Scl2c,
            scl_sclUelActivation_timer1_y_Scl2c,
            scl_sclUelActivation_timer1_u_Scl2c,
            scl_sclUelActivation_IUelBiasPu_Scl2c,
            scl_add3_y_Scl2c,
            scl_pidUel_controlError_Scl2c,
            scl_pidUel_addP_y_Scl2c,
            scl_pidUel_P_y_Scl2c,
            scl_pidUel_addD_y_Scl2c,
            scl_pidUel_D_y_Scl2c,
            scl_pidUel_addPID_y_Scl2c,
            scl_pidUel_gainPID_y_Scl2c,
            scl_pidUel_limiter_u_Scl2c,
            scl_pidUel_y_Scl2c,
            scl_limitedLeadLag_feedback_y_Scl2c,
            scl_limitedLeadLag_gain_y_Scl2c,
            scl_limitedLeadLag_y_Scl2c,
            scl_limitedLeadLag1_feedback_y_Scl2c,
            scl_limitedLeadLag1_gain_y_Scl2c,
            scl_USclUelPu_Scl2c,
            scl_pidUel_addSat_y_Scl2c,
            scl_pidUel_gainTrack_y_Scl2c,
            scl_pidUel_addI_y_Scl2c,
            scl_sclOelActivation_timer_entryTime_Scl2c,
            scl_sclOelActivation_timer1_entryTime_Scl2c,
            scl_sclReferenceCurrent_multiSwitch1_expr_Scl2c,
            scl_sclUelActivation_timer_entryTime_Scl2c,
            scl_sclUelActivation_timer1_entryTime_Scl2c,
            scl_PGenPu_Scl2c,
            scl_QGenPu_Scl2c,
            scl_itPu_im_Scl2c,
            scl_itPu_re_Scl2c,
            scl_utPu_im_Scl2c,
            scl_utPu_re_Scl2c,
            scl_limitedLeadLag_limiter_simplifiedExpr_Scl2c,
            scl_limitedLeadLag1_limiter_simplifiedExpr_Scl2c,
            scl_pythagoras_valid_Scl2c,
            scl_pythagoras1_valid_Scl2c,
            scl_pidUel_I_local_reset_Scl2c,
            scl_pidUel_I_local_set_Scl2c,
            scl_pidOel_I_local_reset_Scl2c,
            scl_pidOel_I_local_set_Scl2c,
            scl_limitedLeadLag2_limiter_simplifiedExpr_Scl2c,
            scl_limitedLeadLag3_limiter_simplifiedExpr_Scl2c,
            scl_sclReferenceCurrent_limIntegrator1_local_reset_Scl2c,
            scl_sclReferenceCurrent_limIntegrator1_local_set_Scl2c,
            scl_sclReferenceCurrent_limiter_simplifiedExpr_Scl2c,
            scl_sclReferenceCurrent_limIntegrator_local_reset_Scl2c,
            scl_sclReferenceCurrent_limIntegrator_local_set_Scl2c,
            scl_limiter_simplifiedExpr_Scl2c,
            scl_division_y_Scl2c,
            scl_complexToPolar1_phi_Scl2c,
            scl_complexToPolar1_len_Scl2c,
            scl_division1_y_Scl2c,
            scl_complexToPolar_phi_Scl2c,
            scl_complexToPolar_len_Scl2c,
            scl_pidOel_u_m_Scl2c,
            scl_pidUel_u_m_Scl2c,
            START_scl_limitedLeadLag_firstOrder_y_Scl2c,
            START_scl_limitedLeadLag1_firstOrder_y_Scl2c,
            START_scl_firstOrder_y_Scl2c,
            START_scl_firstOrder1_y_Scl2c,
            START_scl_firstOrder2_y_Scl2c,
            START_scl_firstOrder3_y_Scl2c,
            START_scl_firstOrder4_y_Scl2c,
            START_scl_pidUel_D_x_Scl2c,
            START_scl_pidOel_D_x_Scl2c,
            START_scl_limitedLeadLag2_firstOrder_y_Scl2c,
            START_scl_limitedLeadLag3_firstOrder_y_Scl2c,
            START_scl_firstOrder5_y_Scl2c,
            START_scl_firstOrder6_y_Scl2c,
            START_scl_firstOrder7_y_Scl2c,
            PRE_scl_sclOelActivation_timer1_entryTime_Scl2c,
            PRE_scl_sclOelActivation_timer_entryTime_Scl2c,
            PRE_scl_sclUelActivation_timer1_entryTime_Scl2c,
            PRE_scl_sclUelActivation_timer_entryTime_Scl2c,
            PRE_scl_sclReferenceCurrent_multiSwitch1_u_2_Scl2c,
            PRE_scl_sclReferenceCurrent_multiSwitch1_u_1_Scl2c,
        ],
        init_eqs={
            scl_firstOrder_y_Scl2c: START_scl_firstOrder_y_Scl2c,
            scl_firstOrder1_y_Scl2c: START_scl_firstOrder1_y_Scl2c,
            scl_firstOrder2_y_Scl2c: START_scl_firstOrder2_y_Scl2c,
            scl_firstOrder3_y_Scl2c: START_scl_firstOrder3_y_Scl2c,
            scl_firstOrder4_y_Scl2c: START_scl_firstOrder4_y_Scl2c,
            scl_firstOrder5_y_Scl2c: START_scl_firstOrder5_y_Scl2c,
            scl_firstOrder6_y_Scl2c: START_scl_firstOrder6_y_Scl2c,
            scl_firstOrder7_y_Scl2c: START_scl_firstOrder7_y_Scl2c,
            scl_limitedLeadLag_firstOrder_y_Scl2c: START_scl_limitedLeadLag_firstOrder_y_Scl2c,
            scl_limitedLeadLag1_firstOrder_y_Scl2c: START_scl_limitedLeadLag1_firstOrder_y_Scl2c,
            scl_limitedLeadLag2_firstOrder_y_Scl2c: START_scl_limitedLeadLag2_firstOrder_y_Scl2c,
            scl_limitedLeadLag3_firstOrder_y_Scl2c: START_scl_limitedLeadLag3_firstOrder_y_Scl2c,
            scl_pidOel_D_x_Scl2c: START_scl_pidOel_D_x_Scl2c,
            scl_pidOel_I_y_Scl2c: scl_pidOel_I_y_start_Scl2c,
            scl_pidUel_D_x_Scl2c: START_scl_pidUel_D_x_Scl2c,
            scl_pidUel_I_y_Scl2c: scl_pidUel_I_y_start_Scl2c,
            scl_sclReferenceCurrent_limIntegrator_y_Scl2c: scl_sclReferenceCurrent_limIntegrator_y_start_Scl2c,
            scl_sclReferenceCurrent_limIntegrator1_y_Scl2c: scl_sclReferenceCurrent_limIntegrator1_y_start_Scl2c,
            scl_PGenPu_Scl2c: vf.add_const(value=0.8),
            scl_QGenPu_Scl2c: vf.add_const(value=0.0),
            scl_USclOelPu_Scl2c: scl_limitedLeadLag3_Y0_Scl2c,
            scl_USclUelPu_Scl2c: scl_limitedLeadLag1_Y0_Scl2c,
            scl_itPu_im_Scl2c: vf.add_const(value=0.0),
            scl_itPu_re_Scl2c: vf.add_const(value=0.8),
            scl_limitedLeadLag_y_Scl2c: scl_limitedLeadLag_Y0_Scl2c,
            scl_limitedLeadLag2_y_Scl2c: scl_limitedLeadLag2_Y0_Scl2c,
            scl_limiter_y_Scl2c: scl_sclUelActivation_IUelRef0Pu_Scl2c,
            scl_pythagoras_y_Scl2c: scl_sclUelActivation_IUelRef0Pu_Scl2c,
            scl_pythagoras1_y_Scl2c: scl_sclOelActivation_IOelRef0Pu_Scl2c,
            scl_sclOelActivation_IOelBiasPu_Scl2c: vf.add_const(value=0.0),
            scl_sclReferenceCurrent_IRefPu_Scl2c: scl_sclReferenceCurrent_IRef0Pu_Scl2c,
            scl_sclReferenceCurrent_multiSwitch1_expr_1_Scl2c: vf.add_const(value=0.1),
            scl_sclReferenceCurrent_multiSwitch1_expr_2_Scl2c: vf.add_const(value=0.1),
            scl_sclReferenceCurrent_tErr_Scl2c: scl_sclReferenceCurrent_tErr0_Scl2c,
            scl_sclUelActivation_IUelBiasPu_Scl2c: vf.add_const(value=0.0),
            scl_utPu_im_Scl2c: vf.add_const(value=0.0),
            scl_utPu_re_Scl2c: vf.add_const(value=1.0),
            scl_limitedLeadLag_limiter_simplifiedExpr_Scl2c: vf.add_const(value=0.0),
            scl_limitedLeadLag1_limiter_simplifiedExpr_Scl2c: vf.add_const(value=0.0),
            scl_pythagoras_valid_Scl2c: vf.add_const(value=1.0),
            scl_pythagoras1_valid_Scl2c: vf.add_const(value=1.0),
            scl_pidUel_I_local_reset_Scl2c: vf.add_const(value=0.0),
            scl_pidUel_I_local_set_Scl2c: vf.add_const(value=0.0),
            scl_pidOel_I_local_reset_Scl2c: vf.add_const(value=0.0),
            scl_pidOel_I_local_set_Scl2c: vf.add_const(value=0.0),
            scl_limitedLeadLag2_limiter_simplifiedExpr_Scl2c: vf.add_const(value=0.0),
            scl_limitedLeadLag3_limiter_simplifiedExpr_Scl2c: vf.add_const(value=0.0),
            scl_sclReferenceCurrent_limIntegrator1_local_reset_Scl2c: vf.add_const(value=0.0),
            scl_sclReferenceCurrent_limIntegrator1_local_set_Scl2c: vf.add_const(value=0.0),
            scl_sclReferenceCurrent_limiter_simplifiedExpr_Scl2c: vf.add_const(value=0.0),
            scl_sclReferenceCurrent_limIntegrator_local_reset_Scl2c: vf.add_const(value=0.0),
            scl_sclReferenceCurrent_limIntegrator_local_set_Scl2c: vf.add_const(value=0.0),
            scl_limiter_simplifiedExpr_Scl2c: vf.add_const(value=0.0),
            scl_division_y_Scl2c: vf.add_const(value=0.8),
            scl_complexToPolar1_phi_Scl2c: vf.add_const(value=0.0),
            scl_complexToPolar1_len_Scl2c: vf.add_const(value=0.8000000000000003),
            scl_division1_y_Scl2c: vf.add_const(value=0.0),
            scl_complexToPolar_phi_Scl2c: vf.add_const(value=0.0),
            scl_complexToPolar_len_Scl2c: vf.add_const(value=1.0),
            scl_pidOel_u_m_Scl2c: vf.add_const(value=0.0),
            scl_pidUel_u_m_Scl2c: vf.add_const(value=0.0),
            scl_sclOelActivation_timer1_u_Scl2c: sym.heaviside(((scl_firstOrder7_y_Scl2c - (scl_pythagoras1_y_Scl2c + scl_sclOelActivation_IThOffPu_Scl2c)) - vf.add_const(value=1e-06))),
            whenCondition1_Scl2c: scl_sclOelActivation_timer1_u_Scl2c,
            scl_sclOelActivation_timer_u_Scl2c: sym.heaviside(((scl_pythagoras1_y_Scl2c - scl_firstOrder7_y_Scl2c) - vf.add_const(value=1e-06))),
            whenCondition2_Scl2c: scl_sclOelActivation_timer_u_Scl2c,
            scl_sclUelActivation_timer1_u_Scl2c: sym.heaviside(((scl_limiter_y_Scl2c - (scl_pythagoras_y_Scl2c + scl_sclUelActivation_IThOffPu_Scl2c)) - vf.add_const(value=1e-06))),
            whenCondition3_Scl2c: scl_sclUelActivation_timer1_u_Scl2c,
            scl_sclUelActivation_timer_u_Scl2c: sym.heaviside(((scl_pythagoras_y_Scl2c - scl_limiter_y_Scl2c) - vf.add_const(value=1e-06))),
            whenCondition4_Scl2c: scl_sclUelActivation_timer_u_Scl2c,
            PRE_scl_sclOelActivation_timer1_entryTime_Scl2c: vf.add_const(value=0.0),
            scl_sclOelActivation_timer1_entryTime_Scl2c: PRE_scl_sclOelActivation_timer1_entryTime_Scl2c,
            scl_sclOelActivation_timer1_y_Scl2c: ((scl_sclOelActivation_timer1_u_Scl2c * (time_Scl2c - scl_sclOelActivation_timer1_entryTime_Scl2c)) + ((vf.add_const(value=1.0) - scl_sclOelActivation_timer1_u_Scl2c) * vf.add_const(value=0.0))),
            PRE_scl_sclOelActivation_timer_entryTime_Scl2c: vf.add_const(value=0.0),
            scl_sclOelActivation_timer_entryTime_Scl2c: PRE_scl_sclOelActivation_timer_entryTime_Scl2c,
            scl_sclOelActivation_timer_y_Scl2c: ((scl_sclOelActivation_timer_u_Scl2c * (time_Scl2c - scl_sclOelActivation_timer_entryTime_Scl2c)) + ((vf.add_const(value=1.0) - scl_sclOelActivation_timer_u_Scl2c) * vf.add_const(value=0.0))),
            PRE_scl_sclUelActivation_timer1_entryTime_Scl2c: vf.add_const(value=0.0),
            scl_sclUelActivation_timer1_entryTime_Scl2c: PRE_scl_sclUelActivation_timer1_entryTime_Scl2c,
            scl_sclUelActivation_timer1_y_Scl2c: ((scl_sclUelActivation_timer1_u_Scl2c * (time_Scl2c - scl_sclUelActivation_timer1_entryTime_Scl2c)) + ((vf.add_const(value=1.0) - scl_sclUelActivation_timer1_u_Scl2c) * vf.add_const(value=0.0))),
            PRE_scl_sclUelActivation_timer_entryTime_Scl2c: vf.add_const(value=0.0),
            scl_sclUelActivation_timer_entryTime_Scl2c: PRE_scl_sclUelActivation_timer_entryTime_Scl2c,
            scl_sclUelActivation_timer_y_Scl2c: ((scl_sclUelActivation_timer_u_Scl2c * (time_Scl2c - scl_sclUelActivation_timer_entryTime_Scl2c)) + ((vf.add_const(value=1.0) - scl_sclUelActivation_timer_u_Scl2c) * vf.add_const(value=0.0))),
            scl_pidOel_y_Scl2c: ((sym.heaviside(((scl_pidOel_limiter_u_Scl2c - scl_pidOel_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_pidOel_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_pidOel_limiter_u_Scl2c - scl_pidOel_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_pidOel_limiter_uMin_Scl2c - scl_pidOel_limiter_u_Scl2c) - vf.add_const(value=1e-06))) * scl_pidOel_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_pidOel_limiter_uMin_Scl2c - scl_pidOel_limiter_u_Scl2c) - vf.add_const(value=1e-06)))) * scl_pidOel_limiter_u_Scl2c)))),
            scl_pidUel_y_Scl2c: ((sym.heaviside(((scl_pidUel_limiter_u_Scl2c - scl_pidUel_limiter_uMax_Scl2c) - vf.add_const(value=1e-06))) * scl_pidUel_limiter_uMax_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_pidUel_limiter_u_Scl2c - scl_pidUel_limiter_uMax_Scl2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((scl_pidUel_limiter_uMin_Scl2c - scl_pidUel_limiter_u_Scl2c) - vf.add_const(value=1e-06))) * scl_pidUel_limiter_uMin_Scl2c) + ((vf.add_const(value=1.0) - sym.heaviside(((scl_pidUel_limiter_uMin_Scl2c - scl_pidUel_limiter_u_Scl2c) - vf.add_const(value=1e-06)))) * scl_pidUel_limiter_u_Scl2c)))),
            PRE_scl_sclReferenceCurrent_multiSwitch1_u_2_Scl2c: vf.add_const(value=0.0),
            PRE_scl_sclReferenceCurrent_multiSwitch1_u_1_Scl2c: vf.add_const(value=0.0),
        },
        event_dict=event_dict,
        in_vars=inputs,
        out_vars=[
        ],
        external_mapping=external_mapping,
        api_obj_mapping=api_obj_mapping,
        diff_vars=[
            d_scl_firstOrder_y_Scl2c,
            d_scl_firstOrder1_y_Scl2c,
            d_scl_firstOrder2_y_Scl2c,
            d_scl_firstOrder3_y_Scl2c,
            d_scl_firstOrder4_y_Scl2c,
            d_scl_firstOrder5_y_Scl2c,
            d_scl_pidOel_D_x_Scl2c,
            d_scl_limitedLeadLag2_firstOrder_y_Scl2c,
            d_scl_limitedLeadLag3_firstOrder_y_Scl2c,
            d_scl_pidOel_I_y_Scl2c,
            d_scl_sclReferenceCurrent_limIntegrator_y_Scl2c,
            d_scl_sclReferenceCurrent_limIntegrator1_y_Scl2c,
            d_scl_firstOrder7_y_Scl2c,
            d_scl_firstOrder6_y_Scl2c,
            d_scl_pidUel_D_x_Scl2c,
            d_scl_limitedLeadLag_firstOrder_y_Scl2c,
            d_scl_limitedLeadLag1_firstOrder_y_Scl2c,
            d_scl_pidUel_I_y_Scl2c,
        ],
        name=template_name,
    )
    templ.comment = 'Generator stator current limiter SCL2C'
    return templ
