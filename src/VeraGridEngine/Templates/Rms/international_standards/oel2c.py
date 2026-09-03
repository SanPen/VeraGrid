# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Oel2c'.

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

def build_oel2c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
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
        template_name: str = 'Oel2c'
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
    oel_firstOrder_y_Oel2c: Var = vf.add_var(name='oel.firstOrder.y_Oel2c')
    oel_firstOrder1_y_Oel2c: Var = vf.add_var(name='oel.firstOrder1.y_Oel2c')
    oel_pid_D_x_Oel2c: Var = vf.add_var(name='oel.pid.D.x_Oel2c')
    oel_limitedLeadLag_firstOrder_y_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.firstOrder.y_Oel2c')
    oel_limitedLeadLag1_firstOrder_y_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.firstOrder.y_Oel2c')
    oel_pid_I_y_Oel2c: Var = vf.add_var(name='oel.pid.I.y_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.y_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.y_Oel2c')

    # Algebraic variables
    oel_gain4_y_Oel2c: Var = vf.add_var(name='oel.gain4.y_Oel2c')
    whenCondition2_Oel2c: Var = vf.add_var(name='$whenCondition2_Oel2c')
    oel_oelActivation_timer_y_Oel2c: Var = vf.add_var(name='oel.oelActivation.timer.y_Oel2c')
    oel_oelActivation_timer_u_Oel2c: Var = vf.add_var(name='oel.oelActivation.timer.u_Oel2c')
    whenCondition1_Oel2c: Var = vf.add_var(name='$whenCondition1_Oel2c')
    oel_oelActivation_timer1_y_Oel2c: Var = vf.add_var(name='oel.oelActivation.timer1.y_Oel2c')
    oel_oelActivation_timer1_u_Oel2c: Var = vf.add_var(name='oel.oelActivation.timer1.u_Oel2c')
    oel_oelReferenceCurrent_tErr_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.tErr_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_u_1_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.u[1]_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_u_2_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.u[2]_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_firstActiveIndex_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.firstActiveIndex_Oel2c')
    oel_oelActivation_IBiasPu_Oel2c: Var = vf.add_var(name='oel.oelActivation.IBiasPu_Oel2c')
    oel_pid_controlError_Oel2c: Var = vf.add_var(name='oel.pid.controlError_Oel2c')
    oel_pid_addP_y_Oel2c: Var = vf.add_var(name='oel.pid.addP.y_Oel2c')
    oel_pid_P_y_Oel2c: Var = vf.add_var(name='oel.pid.P.y_Oel2c')
    oel_pid_addD_y_Oel2c: Var = vf.add_var(name='oel.pid.addD.y_Oel2c')
    oel_pid_D_y_Oel2c: Var = vf.add_var(name='oel.pid.D.y_Oel2c')
    oel_pid_addPID_y_Oel2c: Var = vf.add_var(name='oel.pid.addPID.y_Oel2c')
    oel_pid_gainPID_y_Oel2c: Var = vf.add_var(name='oel.pid.gainPID.y_Oel2c')
    oel_pid_limiter_u_Oel2c: Var = vf.add_var(name='oel.pid.limiter.u_Oel2c')
    oel_pid_y_Oel2c: Var = vf.add_var(name='oel.pid.y_Oel2c')
    oel_limitedLeadLag_feedback_y_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.feedback.y_Oel2c')
    oel_limitedLeadLag_gain_y_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.gain.y_Oel2c')
    oel_limitedLeadLag_y_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.y_Oel2c')
    oel_limitedLeadLag1_feedback_y_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.feedback.y_Oel2c')
    oel_limitedLeadLag1_gain_y_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.gain.y_Oel2c')
    oel_UOelPu_Oel2c: Var = vf.add_var(name='oel.UOelPu_Oel2c')
    oel_pid_addSat_y_Oel2c: Var = vf.add_var(name='oel.pid.addSat.y_Oel2c')
    oel_pid_gainTrack_y_Oel2c: Var = vf.add_var(name='oel.pid.gainTrack.y_Oel2c')
    oel_pid_addI_y_Oel2c: Var = vf.add_var(name='oel.pid.addI.y_Oel2c')
    oel_oelReferenceCurrent_gain_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.gain.y_Oel2c')
    oel_oelReferenceCurrent_power1_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.power1.y_Oel2c')
    oel_oelReferenceCurrent_feedback1_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.feedback1.y_Oel2c')
    oel_oelReferenceCurrent_gain1_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.gain1.y_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_expr_2_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.expr[2]_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_expr_1_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.expr[1]_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.y_Oel2c')
    oel_oelReferenceCurrent_power_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.power.y_Oel2c')
    oel_oelReferenceCurrent_feedback2_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.feedback2.y_Oel2c')
    oel_oelReferenceCurrent_gain2_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.gain2.y_Oel2c')
    oel_oelReferenceCurrent_limiter_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limiter.y_Oel2c')
    oel_oelReferenceCurrent_lessEqualThreshold_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.lessEqualThreshold.y_Oel2c')
    oel_oelReferenceCurrent_switch_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.switch.y_Oel2c')
    oel_oelReferenceCurrent_add_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.add.y_Oel2c')
    oel_oelReferenceCurrent_gain3_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.gain3.y_Oel2c')
    oel_oelReferenceCurrent_feedback_y_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.feedback.y_Oel2c')
    oel_oelActivation_timer_entryTime_Oel2c: Var = vf.add_var(name='oel.oelActivation.timer.entryTime_Oel2c')
    oel_oelActivation_timer1_entryTime_Oel2c: Var = vf.add_var(name='oel.oelActivation.timer1.entryTime_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_expr_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.expr_Oel2c')
    oel_inputPu_Oel2c: Var = vf.add_var(name='oel.inputPu_Oel2c')
    oel_limitedLeadLag_limiter_simplifiedExpr_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.limiter.simplifiedExpr_Oel2c')
    oel_limitedLeadLag1_limiter_simplifiedExpr_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.limiter.simplifiedExpr_Oel2c')
    oel_pid_I_local_reset_Oel2c: Var = vf.add_var(name='oel.pid.I.local_reset_Oel2c')
    oel_pid_I_local_set_Oel2c: Var = vf.add_var(name='oel.pid.I.local_set_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_local_reset_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.local_reset_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_local_set_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.local_set_Oel2c')
    oel_oelReferenceCurrent_limiter_simplifiedExpr_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limiter.simplifiedExpr_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_local_reset_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.local_reset_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_local_set_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.local_set_Oel2c')
    oel_pid_u_m_Oel2c: Var = vf.add_var(name='oel.pid.u_m_Oel2c')
    START_oel_firstOrder_y_Oel2c: Var = vf.add_var(name='$START.oel.firstOrder.y_Oel2c')
    START_oel_firstOrder1_y_Oel2c: Var = vf.add_var(name='$START.oel.firstOrder1.y_Oel2c')
    START_oel_limitedLeadLag_firstOrder_y_Oel2c: Var = vf.add_var(name='$START.oel.limitedLeadLag.firstOrder.y_Oel2c')
    START_oel_limitedLeadLag1_firstOrder_y_Oel2c: Var = vf.add_var(name='$START.oel.limitedLeadLag1.firstOrder.y_Oel2c')
    START_oel_pid_D_x_Oel2c: Var = vf.add_var(name='$START.oel.pid.D.x_Oel2c')
    PRE_oel_oelActivation_timer1_entryTime_Oel2c: Var = vf.add_var(name='$PRE.oel.oelActivation.timer1.entryTime_Oel2c')
    PRE_oel_oelActivation_timer_entryTime_Oel2c: Var = vf.add_var(name='$PRE.oel.oelActivation.timer.entryTime_Oel2c')
    PRE_oel_oelReferenceCurrent_multiSwitch1_u_2_Oel2c: Var = vf.add_var(name='$PRE.oel.oelReferenceCurrent.multiSwitch1.u[2]_Oel2c')
    PRE_oel_oelReferenceCurrent_multiSwitch1_u_1_Oel2c: Var = vf.add_var(name='$PRE.oel.oelReferenceCurrent.multiSwitch1.u[1]_Oel2c')

    # Differential variables
    d_oel_firstOrder_y_Oel2c: Var = vf.add_diff_var(name='d_oel.firstOrder.y_Oel2c', base_var=oel_firstOrder_y_Oel2c)
    d_oel_firstOrder1_y_Oel2c: Var = vf.add_diff_var(name='d_oel.firstOrder1.y_Oel2c', base_var=oel_firstOrder1_y_Oel2c)
    d_oel_pid_D_x_Oel2c: Var = vf.add_diff_var(name='d_oel.pid.D.x_Oel2c', base_var=oel_pid_D_x_Oel2c)
    d_oel_limitedLeadLag_firstOrder_y_Oel2c: Var = vf.add_diff_var(name='d_oel.limitedLeadLag.firstOrder.y_Oel2c', base_var=oel_limitedLeadLag_firstOrder_y_Oel2c)
    d_oel_limitedLeadLag1_firstOrder_y_Oel2c: Var = vf.add_diff_var(name='d_oel.limitedLeadLag1.firstOrder.y_Oel2c', base_var=oel_limitedLeadLag1_firstOrder_y_Oel2c)
    d_oel_pid_I_y_Oel2c: Var = vf.add_diff_var(name='d_oel.pid.I.y_Oel2c', base_var=oel_pid_I_y_Oel2c)
    d_oel_oelReferenceCurrent_limIntegrator1_y_Oel2c: Var = vf.add_diff_var(name='d_oel.oelReferenceCurrent.limIntegrator1.y_Oel2c', base_var=oel_oelReferenceCurrent_limIntegrator1_y_Oel2c)
    d_oel_oelReferenceCurrent_limIntegrator_y_Oel2c: Var = vf.add_diff_var(name='d_oel.oelReferenceCurrent.limIntegrator.y_Oel2c', base_var=oel_oelReferenceCurrent_limIntegrator_y_Oel2c)

    # Internal variables
    time_Oel2c: Var = vf.add_var(name='time_Oel2c')

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________

    # Runtime parameters and event variables
    oel_Input0Pu_Oel2c: Var = vf.add_var(name='oel.Input0Pu_Oel2c')
    oel_firstOrder_k_Oel2c: Var = vf.add_var(name='oel.firstOrder.k_Oel2c')
    oel_firstOrder_T_Oel2c: Var = vf.add_var(name='oel.firstOrder.T_Oel2c')
    oel_firstOrder1_k_Oel2c: Var = vf.add_var(name='oel.firstOrder1.k_Oel2c')
    oel_firstOrder1_T_Oel2c: Var = vf.add_var(name='oel.firstOrder1.T_Oel2c')
    oel_pid_D_T_Oel2c: Var = vf.add_var(name='oel.pid.D.T_Oel2c')
    oel_pid_D_zeroGain_Oel2c: Var = vf.add_var(name='oel.pid.D.zeroGain_Oel2c')
    oel_limitedLeadLag_firstOrder_T_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.firstOrder.T_Oel2c')
    oel_limitedLeadLag_firstOrder_k_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.firstOrder.k_Oel2c')
    oel_limitedLeadLag1_firstOrder_k_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.firstOrder.k_Oel2c')
    oel_limitedLeadLag1_firstOrder_T_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.firstOrder.T_Oel2c')
    oel_pid_I_k_Oel2c: Var = vf.add_var(name='oel.pid.I.k_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.k_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_outMax_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.outMax_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.outMin_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.k_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_outMax_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.outMax_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.outMin_Oel2c')
    oel_gain4_k_Oel2c: Var = vf.add_var(name='oel.gain4.k_Oel2c')
    oel_oelActivation_IThOffPu_Oel2c: Var = vf.add_var(name='oel.oelActivation.IThOffPu_Oel2c')
    oel_oelReferenceCurrent_const3_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.const3.k_Oel2c')
    oel_oelReferenceCurrent_greaterEqualThreshold_threshold_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.greaterEqualThreshold.threshold_Oel2c')
    oel_oelReferenceCurrent_lessEqualThreshold1_threshold_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.lessEqualThreshold1.threshold_Oel2c')
    oel_oelActivation_IResetPu_Oel2c: Var = vf.add_var(name='oel.oelActivation.IResetPu_Oel2c')
    oel_oelActivation_IInstPu_Oel2c: Var = vf.add_var(name='oel.oelActivation.IInstPu_Oel2c')
    oel_oelActivation_tOff_Oel2c: Var = vf.add_var(name='oel.oelActivation.tOff_Oel2c')
    oel_oelActivation_tEn_Oel2c: Var = vf.add_var(name='oel.oelActivation.tEn_Oel2c')
    oel_add3_k1_Oel2c: Var = vf.add_var(name='oel.add3.k1_Oel2c')
    oel_add3_k3_Oel2c: Var = vf.add_var(name='oel.add3.k3_Oel2c')
    oel_add3_k2_Oel2c: Var = vf.add_var(name='oel.add3.k2_Oel2c')
    oel_pid_addP_k1_Oel2c: Var = vf.add_var(name='oel.pid.addP.k1_Oel2c')
    oel_pid_P_k_Oel2c: Var = vf.add_var(name='oel.pid.P.k_Oel2c')
    oel_pid_addD_k1_Oel2c: Var = vf.add_var(name='oel.pid.addD.k1_Oel2c')
    oel_pid_D_k_Oel2c: Var = vf.add_var(name='oel.pid.D.k_Oel2c')
    oel_pid_addPID_k3_Oel2c: Var = vf.add_var(name='oel.pid.addPID.k3_Oel2c')
    oel_pid_addPID_k2_Oel2c: Var = vf.add_var(name='oel.pid.addPID.k2_Oel2c')
    oel_pid_addPID_k1_Oel2c: Var = vf.add_var(name='oel.pid.addPID.k1_Oel2c')
    oel_pid_gainPID_k_Oel2c: Var = vf.add_var(name='oel.pid.gainPID.k_Oel2c')
    oel_pid_addFF_k2_Oel2c: Var = vf.add_var(name='oel.pid.addFF.k2_Oel2c')
    oel_pid_addFF_k1_Oel2c: Var = vf.add_var(name='oel.pid.addFF.k1_Oel2c')
    oel_pid_FFzero_k_Oel2c: Var = vf.add_var(name='oel.pid.FFzero.k_Oel2c')
    oel_pid_limiter_uMin_Oel2c: Var = vf.add_var(name='oel.pid.limiter.uMin_Oel2c')
    oel_pid_limiter_uMax_Oel2c: Var = vf.add_var(name='oel.pid.limiter.uMax_Oel2c')
    oel_limitedLeadLag_gain_k_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.gain.k_Oel2c')
    oel_limitedLeadLag_limiter_uMin_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.limiter.uMin_Oel2c')
    oel_limitedLeadLag_limiter_uMax_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.limiter.uMax_Oel2c')
    oel_limitedLeadLag1_gain_k_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.gain.k_Oel2c')
    oel_limitedLeadLag1_limiter_uMax_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.limiter.uMax_Oel2c')
    oel_limitedLeadLag1_limiter_uMin_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.limiter.uMin_Oel2c')
    oel_pid_addSat_k2_Oel2c: Var = vf.add_var(name='oel.pid.addSat.k2_Oel2c')
    oel_pid_addSat_k1_Oel2c: Var = vf.add_var(name='oel.pid.addSat.k1_Oel2c')
    oel_pid_gainTrack_k_Oel2c: Var = vf.add_var(name='oel.pid.gainTrack.k_Oel2c')
    oel_pid_addI_k1_Oel2c: Var = vf.add_var(name='oel.pid.addI.k1_Oel2c')
    oel_pid_addI_k3_Oel2c: Var = vf.add_var(name='oel.pid.addI.k3_Oel2c')
    oel_oelReferenceCurrent_gain_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.gain.k_Oel2c')
    oel_oelReferenceCurrent_power1_N_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.power1.N_Oel2c')
    oel_oelReferenceCurrent_const_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.const.k_Oel2c')
    oel_oelReferenceCurrent_gain1_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.gain1.k_Oel2c')
    oel_oelReferenceCurrent_booleanConstant_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.booleanConstant.k_Oel2c')
    oel_oelReferenceCurrent_const4_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.const4.k_Oel2c')
    oel_oelReferenceCurrent_const5_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.const5.k_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_y_default_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.y_default_Oel2c')
    oel_oelReferenceCurrent_power_N_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.power.N_Oel2c')
    oel_oelReferenceCurrent_gain2_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.gain2.k_Oel2c')
    oel_oelReferenceCurrent_limiter_uMin_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limiter.uMin_Oel2c')
    oel_oelReferenceCurrent_limiter_uMax_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limiter.uMax_Oel2c')
    oel_oelReferenceCurrent_lessEqualThreshold_threshold_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.lessEqualThreshold.threshold_Oel2c')
    oel_oelReferenceCurrent_const2_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.const2.k_Oel2c')
    oel_oelReferenceCurrent_const1_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.const1.k_Oel2c')
    oel_oelReferenceCurrent_add_k2_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.add.k2_Oel2c')
    oel_oelReferenceCurrent_add_k1_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.add.k1_Oel2c')
    oel_oelReferenceCurrent_gain3_k_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.gain3.k_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_y_start_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.y_start_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_y_start_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.y_start_Oel2c')
    oel_pid_I_y_start_Oel2c: Var = vf.add_var(name='oel.pid.I.y_start_Oel2c')
    oel_limitedLeadLag1_Y0_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.Y0_Oel2c')
    oel_oelActivation_IRef0Pu_Oel2c: Var = vf.add_var(name='oel.oelActivation.IRef0Pu_Oel2c')
    oel_limitedLeadLag_Y0_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.Y0_Oel2c')
    oel_oelActivation_tErr0_Oel2c: Var = vf.add_var(name='oel.oelActivation.tErr0_Oel2c')
    oel_C1_Oel2c: Var = vf.add_var(name='oel.C1_Oel2c')
    oel_C2_Oel2c: Var = vf.add_var(name='oel.C2_Oel2c')
    oel_FixedRd_Oel2c: Var = vf.add_var(name='oel.FixedRd_Oel2c')
    oel_FixedRu_Oel2c: Var = vf.add_var(name='oel.FixedRu_Oel2c')
    oel_I0Pu_Oel2c: Var = vf.add_var(name='oel.I0Pu_Oel2c')
    oel_KScale_Oel2c: Var = vf.add_var(name='oel.KScale_Oel2c')
    oel_IInstPu_Oel2c: Var = vf.add_var(name='oel.IInstPu_Oel2c')
    oel_ILimPu_Oel2c: Var = vf.add_var(name='oel.ILimPu_Oel2c')
    oel_IRef0Pu_Oel2c: Var = vf.add_var(name='oel.IRef0Pu_Oel2c')
    oel_KAct_Oel2c: Var = vf.add_var(name='oel.KAct_Oel2c')
    oel_IResetPu_Oel2c: Var = vf.add_var(name='oel.IResetPu_Oel2c')
    oel_IScaled0Pu_Oel2c: Var = vf.add_var(name='oel.IScaled0Pu_Oel2c')
    oel_ITfPu_Oel2c: Var = vf.add_var(name='oel.ITfPu_Oel2c')
    oel_IThOffPu_Oel2c: Var = vf.add_var(name='oel.IThOffPu_Oel2c')
    oel_K1_Oel2c: Var = vf.add_var(name='oel.K1_Oel2c')
    oel_K2_Oel2c: Var = vf.add_var(name='oel.K2_Oel2c')
    oel_KFb_Oel2c: Var = vf.add_var(name='oel.KFb_Oel2c')
    oel_KdOel_Oel2c: Var = vf.add_var(name='oel.KdOel_Oel2c')
    oel_KiOel_Oel2c: Var = vf.add_var(name='oel.KiOel_Oel2c')
    oel_KpOel_Oel2c: Var = vf.add_var(name='oel.KpOel_Oel2c')
    oel_Krd_Oel2c: Var = vf.add_var(name='oel.Krd_Oel2c')
    oel_Kru_Oel2c: Var = vf.add_var(name='oel.Kru_Oel2c')
    oel_Kzru_Oel2c: Var = vf.add_var(name='oel.Kzru_Oel2c')
    oel_VInvMaxPu_Oel2c: Var = vf.add_var(name='oel.VInvMaxPu_Oel2c')
    oel_VInvMinPu_Oel2c: Var = vf.add_var(name='oel.VInvMinPu_Oel2c')
    oel_VOel1MaxPu_Oel2c: Var = vf.add_var(name='oel.VOel1MaxPu_Oel2c')
    oel_VOel1MinPu_Oel2c: Var = vf.add_var(name='oel.VOel1MinPu_Oel2c')
    oel_VOel2MaxPu_Oel2c: Var = vf.add_var(name='oel.VOel2MaxPu_Oel2c')
    oel_VOel2MinPu_Oel2c: Var = vf.add_var(name='oel.VOel2MinPu_Oel2c')
    oel_VOel3MaxPu_Oel2c: Var = vf.add_var(name='oel.VOel3MaxPu_Oel2c')
    oel_VOel3MinPu_Oel2c: Var = vf.add_var(name='oel.VOel3MinPu_Oel2c')
    oel_tROel_Oel2c: Var = vf.add_var(name='oel.tROel_Oel2c')
    oel_firstOrder_y_start_Oel2c: Var = vf.add_var(name='oel.firstOrder.y_start_Oel2c')
    oel_tAOel_Oel2c: Var = vf.add_var(name='oel.tAOel_Oel2c')
    oel_firstOrder1_y_start_Oel2c: Var = vf.add_var(name='oel.firstOrder1.y_start_Oel2c')
    oel_limitedLeadLag_K_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.K_Oel2c')
    oel_limitedLeadLag_YMax_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.YMax_Oel2c')
    oel_limitedLeadLag_YMin_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.YMin_Oel2c')
    oel_limitedLeadLag_t1_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.t1_Oel2c')
    oel_limitedLeadLag_t2_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.t2_Oel2c')
    oel_limitedLeadLag_firstOrder_y_start_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.firstOrder.y_start_Oel2c')
    oel_tC2Oel_Oel2c: Var = vf.add_var(name='oel.tC2Oel_Oel2c')
    oel_tB2Oel_Oel2c: Var = vf.add_var(name='oel.tB2Oel_Oel2c')
    oel_limitedLeadLag1_K_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.K_Oel2c')
    oel_limitedLeadLag1_YMax_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.YMax_Oel2c')
    oel_limitedLeadLag1_YMin_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.YMin_Oel2c')
    oel_limitedLeadLag1_t1_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.t1_Oel2c')
    oel_limitedLeadLag1_t2_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.t2_Oel2c')
    oel_limitedLeadLag1_firstOrder_y_start_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.firstOrder.y_start_Oel2c')
    oel_tC1Oel_Oel2c: Var = vf.add_var(name='oel.tC1Oel_Oel2c')
    oel_tB1Oel_Oel2c: Var = vf.add_var(name='oel.tB1Oel_Oel2c')
    oel_tEn_Oel2c: Var = vf.add_var(name='oel.tEn_Oel2c')
    oel_tErr0_Oel2c: Var = vf.add_var(name='oel.tErr0_Oel2c')
    oel_tOff_Oel2c: Var = vf.add_var(name='oel.tOff_Oel2c')
    oel_oelReferenceCurrent_C1_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.C1_Oel2c')
    oel_oelReferenceCurrent_C2_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.C2_Oel2c')
    oel_oelReferenceCurrent_FixedRd_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.FixedRd_Oel2c')
    oel_oelReferenceCurrent_FixedRu_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.FixedRu_Oel2c')
    oel_oelReferenceCurrent_I0Pu_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.I0Pu_Oel2c')
    oel_oelReferenceCurrent_IInstPu_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.IInstPu_Oel2c')
    oel_oelReferenceCurrent_ILimPu_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.ILimPu_Oel2c')
    oel_oelReferenceCurrent_IRef0Pu_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.IRef0Pu_Oel2c')
    oel_oelReferenceCurrent_ITfPu_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.ITfPu_Oel2c')
    oel_oelReferenceCurrent_K1_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.K1_Oel2c')
    oel_oelReferenceCurrent_K2_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.K2_Oel2c')
    oel_oelReferenceCurrent_KFb_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.KFb_Oel2c')
    oel_oelReferenceCurrent_Krd_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.Krd_Oel2c')
    oel_oelReferenceCurrent_Kru_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.Kru_Oel2c')
    oel_oelReferenceCurrent_Kzru_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.Kzru_Oel2c')
    oel_oelReferenceCurrent_VInvMaxPu_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.VInvMaxPu_Oel2c')
    oel_oelReferenceCurrent_VInvMinPu_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.VInvMinPu_Oel2c')
    oel_oelReferenceCurrent_tFcl_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.tFcl_Oel2c')
    oel_oelReferenceCurrent_tMax_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.tMax_Oel2c')
    oel_oelReferenceCurrent_tMin_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.tMin_Oel2c')
    oel_oelReferenceCurrent_tInt0_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.tInt0_Oel2c')
    oel_oelReferenceCurrent_tErr0_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.tErr0_Oel2c')
    oel_tFcl_Oel2c: Var = vf.add_var(name='oel.tFcl_Oel2c')
    oel_tInt0_Oel2c: Var = vf.add_var(name='oel.tInt0_Oel2c')
    oel_tMax_Oel2c: Var = vf.add_var(name='oel.tMax_Oel2c')
    oel_tMin_Oel2c: Var = vf.add_var(name='oel.tMin_Oel2c')
    oel_pid_Td_Oel2c: Var = vf.add_var(name='oel.pid.Td_Oel2c')
    oel_pid_Nd_Oel2c: Var = vf.add_var(name='oel.pid.Nd_Oel2c')
    oel_pid_D_x_start_Oel2c: Var = vf.add_var(name='oel.pid.D.x_start_Oel2c')
    oel_pid_xd_start_Oel2c: Var = vf.add_var(name='oel.pid.xd_start_Oel2c')
    oel_pid_D_y_start_Oel2c: Var = vf.add_var(name='oel.pid.D.y_start_Oel2c')
    oel_pid_Ti_Oel2c: Var = vf.add_var(name='oel.pid.Ti_Oel2c')
    oel_pid_xi_start_Oel2c: Var = vf.add_var(name='oel.pid.xi_start_Oel2c')
    oel_pid_Ni_Oel2c: Var = vf.add_var(name='oel.pid.Ni_Oel2c')
    oel_tDOel_Oel2c: Var = vf.add_var(name='oel.tDOel_Oel2c')
    oel_pid_wd_Oel2c: Var = vf.add_var(name='oel.pid.wd_Oel2c')
    oel_pid_addD_k2_Oel2c: Var = vf.add_var(name='oel.pid.addD.k2_Oel2c')
    oel_pid_kFF_Oel2c: Var = vf.add_var(name='oel.pid.kFF_Oel2c')
    oel_pid_addI_k2_Oel2c: Var = vf.add_var(name='oel.pid.addI.k2_Oel2c')
    oel_pid_wp_Oel2c: Var = vf.add_var(name='oel.pid.wp_Oel2c')
    oel_pid_addP_k2_Oel2c: Var = vf.add_var(name='oel.pid.addP.k2_Oel2c')
    oel_pid_k_Oel2c: Var = vf.add_var(name='oel.pid.k_Oel2c')
    oel_pid_yMax_Oel2c: Var = vf.add_var(name='oel.pid.yMax_Oel2c')
    oel_pid_yMin_Oel2c: Var = vf.add_var(name='oel.pid.yMin_Oel2c')
    oel_pid_y_start_Oel2c: Var = vf.add_var(name='oel.pid.y_start_Oel2c')
    oel_firstOrder_initType_Oel2c: Var = vf.add_var(name='oel.firstOrder.initType_Oel2c')
    oel_firstOrder1_initType_Oel2c: Var = vf.add_var(name='oel.firstOrder1.initType_Oel2c')
    oel_limitedLeadLag_firstOrder_initType_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.firstOrder.initType_Oel2c')
    oel_limitedLeadLag_limiter_homotopyType_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.limiter.homotopyType_Oel2c')
    oel_limitedLeadLag1_firstOrder_initType_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.firstOrder.initType_Oel2c')
    oel_limitedLeadLag1_limiter_homotopyType_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.limiter.homotopyType_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_initType_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.initType_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_initType_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.initType_Oel2c')
    oel_oelReferenceCurrent_limiter_homotopyType_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limiter.homotopyType_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_nu_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.nu_Oel2c')
    oel_oelReferenceCurrent_multiSwitch1_precision_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.multiSwitch1.precision_Oel2c')
    oel_pid_D_initType_Oel2c: Var = vf.add_var(name='oel.pid.D.initType_Oel2c')
    oel_pid_I_initType_Oel2c: Var = vf.add_var(name='oel.pid.I.initType_Oel2c')
    oel_pid_controllerType_Oel2c: Var = vf.add_var(name='oel.pid.controllerType_Oel2c')
    oel_pid_homotopyType_Oel2c: Var = vf.add_var(name='oel.pid.homotopyType_Oel2c')
    oel_pid_initType_Oel2c: Var = vf.add_var(name='oel.pid.initType_Oel2c')
    oel_pid_limiter_homotopyType_Oel2c: Var = vf.add_var(name='oel.pid.limiter.homotopyType_Oel2c')
    oel_Sw1_Oel2c: Var = vf.add_var(name='oel.Sw1_Oel2c')
    oel_limitedLeadLag_limiter_limitsAtInit_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.limiter.limitsAtInit_Oel2c')
    oel_limitedLeadLag_limiter_strict_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag.limiter.strict_Oel2c')
    oel_limitedLeadLag1_limiter_limitsAtInit_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.limiter.limitsAtInit_Oel2c')
    oel_limitedLeadLag1_limiter_strict_Oel2c: Var = vf.add_var(name='oel.limitedLeadLag1.limiter.strict_Oel2c')
    oel_oelReferenceCurrent_Sw1_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.Sw1_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_limitsAtInit_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.limitsAtInit_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_strict_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.strict_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_use_reset_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.use_reset_Oel2c')
    oel_oelReferenceCurrent_limIntegrator_use_set_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator.use_set_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_limitsAtInit_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.limitsAtInit_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_strict_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.strict_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_use_reset_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.use_reset_Oel2c')
    oel_oelReferenceCurrent_limIntegrator1_use_set_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limIntegrator1.use_set_Oel2c')
    oel_oelReferenceCurrent_limiter_limitsAtInit_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limiter.limitsAtInit_Oel2c')
    oel_oelReferenceCurrent_limiter_strict_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.limiter.strict_Oel2c')
    oel_oelReferenceCurrent_power_NInteger_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.power.NInteger_Oel2c')
    oel_oelReferenceCurrent_power1_NInteger_Oel2c: Var = vf.add_var(name='oel.oelReferenceCurrent.power1.NInteger_Oel2c')
    oel_pid_I_use_reset_Oel2c: Var = vf.add_var(name='oel.pid.I.use_reset_Oel2c')
    oel_pid_I_use_set_Oel2c: Var = vf.add_var(name='oel.pid.I.use_set_Oel2c')
    oel_pid_limiter_limitsAtInit_Oel2c: Var = vf.add_var(name='oel.pid.limiter.limitsAtInit_Oel2c')
    oel_pid_limiter_strict_Oel2c: Var = vf.add_var(name='oel.pid.limiter.strict_Oel2c')
    oel_pid_limitsAtInit_Oel2c: Var = vf.add_var(name='oel.pid.limitsAtInit_Oel2c')
    oel_pid_strict_Oel2c: Var = vf.add_var(name='oel.pid.strict_Oel2c')
    oel_pid_withFeedForward_Oel2c: Var = vf.add_var(name='oel.pid.withFeedForward_Oel2c')
    oel_pid_with_D_Oel2c: Var = vf.add_var(name='oel.pid.with_D_Oel2c')
    oel_pid_with_I_Oel2c: Var = vf.add_var(name='oel.pid.with_I_Oel2c')
    oel_pid_unitTime_Oel2c: Var = vf.add_var(name='oel.pid.unitTime_Oel2c')

    event_dict: dict[Var, Expr | Const] = dict({
        oel_C1_Oel2c: vf.add_const(value=1.0),
        oel_C2_Oel2c: vf.add_const(value=1.0),
        oel_FixedRd_Oel2c: vf.add_const(value=0.0),
        oel_FixedRu_Oel2c: vf.add_const(value=0.0),
        oel_I0Pu_Oel2c: (oel_KScale_Oel2c * oel_Input0Pu_Oel2c),
        oel_IInstPu_Oel2c: vf.add_const(value=1.5),
        oel_ILimPu_Oel2c: vf.add_const(value=1.2),
        oel_IRef0Pu_Oel2c: (oel_KAct_Oel2c * oel_I0Pu_Oel2c),
        oel_IResetPu_Oel2c: vf.add_const(value=1.0),
        oel_IScaled0Pu_Oel2c: (oel_I0Pu_Oel2c / oel_ITfPu_Oel2c),
        oel_ITfPu_Oel2c: vf.add_const(value=1.1),
        oel_IThOffPu_Oel2c: vf.add_const(value=1.0),
        oel_Input0Pu_Oel2c: vf.add_const(value=1.0),
        oel_K1_Oel2c: vf.add_const(value=1.0),
        oel_K2_Oel2c: vf.add_const(value=1.0),
        oel_KAct_Oel2c: vf.add_const(value=1.0),
        oel_KFb_Oel2c: vf.add_const(value=1.0),
        oel_KScale_Oel2c: vf.add_const(value=1.0),
        oel_KdOel_Oel2c: vf.add_const(value=0.0),
        oel_KiOel_Oel2c: vf.add_const(value=1.0),
        oel_KpOel_Oel2c: vf.add_const(value=1.0),
        oel_Krd_Oel2c: vf.add_const(value=0.1),
        oel_Kru_Oel2c: vf.add_const(value=0.1),
        oel_Kzru_Oel2c: vf.add_const(value=0.0),
        oel_VInvMaxPu_Oel2c: vf.add_const(value=1.0),
        oel_VInvMinPu_Oel2c: vf.add_const(value=0.0),
        oel_VOel1MaxPu_Oel2c: vf.add_const(value=1.0),
        oel_VOel1MinPu_Oel2c: vf.add_const(value=-1.0),
        oel_VOel2MaxPu_Oel2c: vf.add_const(value=1.0),
        oel_VOel2MinPu_Oel2c: vf.add_const(value=-1.0),
        oel_VOel3MaxPu_Oel2c: vf.add_const(value=1.0),
        oel_VOel3MinPu_Oel2c: vf.add_const(value=-1.0),
        oel_add3_k1_Oel2c: vf.add_const(value=-1.0),
        oel_add3_k2_Oel2c: vf.add_const(value=1.0),
        oel_add3_k3_Oel2c: vf.add_const(value=1.0),
        oel_firstOrder_T_Oel2c: oel_tROel_Oel2c,
        oel_firstOrder_k_Oel2c: oel_KScale_Oel2c,
        oel_firstOrder_y_start_Oel2c: oel_I0Pu_Oel2c,
        oel_firstOrder1_T_Oel2c: oel_tAOel_Oel2c,
        oel_firstOrder1_k_Oel2c: vf.add_const(value=1.0),
        oel_firstOrder1_y_start_Oel2c: oel_IRef0Pu_Oel2c,
        oel_gain4_k_Oel2c: oel_KAct_Oel2c,
        oel_limitedLeadLag_K_Oel2c: vf.add_const(value=1.0),
        oel_limitedLeadLag_Y0_Oel2c: vf.add_const(value=0.0),
        oel_limitedLeadLag_YMax_Oel2c: oel_VOel2MaxPu_Oel2c,
        oel_limitedLeadLag_YMin_Oel2c: oel_VOel2MinPu_Oel2c,
        oel_limitedLeadLag_firstOrder_T_Oel2c: oel_limitedLeadLag_t1_Oel2c,
        oel_limitedLeadLag_firstOrder_k_Oel2c: ((oel_limitedLeadLag_t1_Oel2c - oel_limitedLeadLag_t2_Oel2c) / (oel_limitedLeadLag_t1_Oel2c * oel_limitedLeadLag_K_Oel2c)),
        oel_limitedLeadLag_firstOrder_y_start_Oel2c: (oel_limitedLeadLag_Y0_Oel2c * ((oel_limitedLeadLag_t1_Oel2c - oel_limitedLeadLag_t2_Oel2c) / (oel_limitedLeadLag_t1_Oel2c * oel_limitedLeadLag_K_Oel2c))),
        oel_limitedLeadLag_gain_k_Oel2c: (oel_limitedLeadLag_K_Oel2c * (oel_limitedLeadLag_t1_Oel2c / oel_limitedLeadLag_t2_Oel2c)),
        oel_limitedLeadLag_limiter_uMax_Oel2c: oel_limitedLeadLag_YMax_Oel2c,
        oel_limitedLeadLag_limiter_uMin_Oel2c: oel_limitedLeadLag_YMin_Oel2c,
        oel_limitedLeadLag_t1_Oel2c: oel_tC2Oel_Oel2c,
        oel_limitedLeadLag_t2_Oel2c: oel_tB2Oel_Oel2c,
        oel_limitedLeadLag1_K_Oel2c: vf.add_const(value=1.0),
        oel_limitedLeadLag1_Y0_Oel2c: vf.add_const(value=0.0),
        oel_limitedLeadLag1_YMax_Oel2c: oel_VOel1MaxPu_Oel2c,
        oel_limitedLeadLag1_YMin_Oel2c: oel_VOel1MinPu_Oel2c,
        oel_limitedLeadLag1_firstOrder_T_Oel2c: oel_limitedLeadLag1_t1_Oel2c,
        oel_limitedLeadLag1_firstOrder_k_Oel2c: ((oel_limitedLeadLag1_t1_Oel2c - oel_limitedLeadLag1_t2_Oel2c) / (oel_limitedLeadLag1_t1_Oel2c * oel_limitedLeadLag1_K_Oel2c)),
        oel_limitedLeadLag1_firstOrder_y_start_Oel2c: (oel_limitedLeadLag1_Y0_Oel2c * ((oel_limitedLeadLag1_t1_Oel2c - oel_limitedLeadLag1_t2_Oel2c) / (oel_limitedLeadLag1_t1_Oel2c * oel_limitedLeadLag1_K_Oel2c))),
        oel_limitedLeadLag1_gain_k_Oel2c: (oel_limitedLeadLag1_K_Oel2c * (oel_limitedLeadLag1_t1_Oel2c / oel_limitedLeadLag1_t2_Oel2c)),
        oel_limitedLeadLag1_limiter_uMax_Oel2c: oel_limitedLeadLag1_YMax_Oel2c,
        oel_limitedLeadLag1_limiter_uMin_Oel2c: oel_limitedLeadLag1_YMin_Oel2c,
        oel_limitedLeadLag1_t1_Oel2c: oel_tC1Oel_Oel2c,
        oel_limitedLeadLag1_t2_Oel2c: oel_tB1Oel_Oel2c,
        oel_oelActivation_IInstPu_Oel2c: oel_IInstPu_Oel2c,
        oel_oelActivation_IRef0Pu_Oel2c: oel_IRef0Pu_Oel2c,
        oel_oelActivation_IResetPu_Oel2c: oel_IResetPu_Oel2c,
        oel_oelActivation_IThOffPu_Oel2c: oel_IThOffPu_Oel2c,
        oel_oelActivation_tEn_Oel2c: oel_tEn_Oel2c,
        oel_oelActivation_tErr0_Oel2c: oel_tErr0_Oel2c,
        oel_oelActivation_tOff_Oel2c: oel_tOff_Oel2c,
        oel_oelReferenceCurrent_C1_Oel2c: oel_C1_Oel2c,
        oel_oelReferenceCurrent_C2_Oel2c: oel_C2_Oel2c,
        oel_oelReferenceCurrent_FixedRd_Oel2c: oel_FixedRd_Oel2c,
        oel_oelReferenceCurrent_FixedRu_Oel2c: oel_FixedRu_Oel2c,
        oel_oelReferenceCurrent_I0Pu_Oel2c: oel_I0Pu_Oel2c,
        oel_oelReferenceCurrent_IInstPu_Oel2c: oel_IInstPu_Oel2c,
        oel_oelReferenceCurrent_ILimPu_Oel2c: oel_ILimPu_Oel2c,
        oel_oelReferenceCurrent_IRef0Pu_Oel2c: oel_IRef0Pu_Oel2c,
        oel_oelReferenceCurrent_ITfPu_Oel2c: oel_ITfPu_Oel2c,
        oel_oelReferenceCurrent_K1_Oel2c: oel_K1_Oel2c,
        oel_oelReferenceCurrent_K2_Oel2c: oel_K2_Oel2c,
        oel_oelReferenceCurrent_KFb_Oel2c: oel_KFb_Oel2c,
        oel_oelReferenceCurrent_Krd_Oel2c: oel_Krd_Oel2c,
        oel_oelReferenceCurrent_Kru_Oel2c: oel_Kru_Oel2c,
        oel_oelReferenceCurrent_Kzru_Oel2c: oel_Kzru_Oel2c,
        oel_oelReferenceCurrent_VInvMaxPu_Oel2c: oel_VInvMaxPu_Oel2c,
        oel_oelReferenceCurrent_VInvMinPu_Oel2c: oel_VInvMinPu_Oel2c,
        oel_oelReferenceCurrent_add_k1_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_add_k2_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_const_k_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_const1_k_Oel2c: oel_oelReferenceCurrent_FixedRu_Oel2c,
        oel_oelReferenceCurrent_const2_k_Oel2c: oel_oelReferenceCurrent_FixedRd_Oel2c,
        oel_oelReferenceCurrent_const3_k_Oel2c: oel_oelReferenceCurrent_tFcl_Oel2c,
        oel_oelReferenceCurrent_const4_k_Oel2c: oel_oelReferenceCurrent_Krd_Oel2c,
        oel_oelReferenceCurrent_const5_k_Oel2c: oel_oelReferenceCurrent_Kru_Oel2c,
        oel_oelReferenceCurrent_gain_k_Oel2c: (vf.add_const(value=1.0) / oel_oelReferenceCurrent_ITfPu_Oel2c),
        oel_oelReferenceCurrent_gain1_k_Oel2c: oel_oelReferenceCurrent_K1_Oel2c,
        oel_oelReferenceCurrent_gain2_k_Oel2c: oel_oelReferenceCurrent_K2_Oel2c,
        oel_oelReferenceCurrent_gain3_k_Oel2c: oel_oelReferenceCurrent_KFb_Oel2c,
        oel_oelReferenceCurrent_greaterEqualThreshold_threshold_Oel2c: (oel_oelReferenceCurrent_Kzru_Oel2c * oel_oelReferenceCurrent_tFcl_Oel2c),
        oel_oelReferenceCurrent_lessEqualThreshold_threshold_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_lessEqualThreshold1_threshold_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_limIntegrator_k_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_limIntegrator_outMax_Oel2c: oel_oelReferenceCurrent_tMax_Oel2c,
        oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c: oel_oelReferenceCurrent_tMin_Oel2c,
        oel_oelReferenceCurrent_limIntegrator_y_start_Oel2c: oel_oelReferenceCurrent_tInt0_Oel2c,
        oel_oelReferenceCurrent_limIntegrator1_k_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_limIntegrator1_outMax_Oel2c: oel_oelReferenceCurrent_IInstPu_Oel2c,
        oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c: oel_oelReferenceCurrent_ILimPu_Oel2c,
        oel_oelReferenceCurrent_limIntegrator1_y_start_Oel2c: oel_oelReferenceCurrent_IRef0Pu_Oel2c,
        oel_oelReferenceCurrent_limiter_uMax_Oel2c: oel_oelReferenceCurrent_VInvMaxPu_Oel2c,
        oel_oelReferenceCurrent_limiter_uMin_Oel2c: oel_oelReferenceCurrent_VInvMinPu_Oel2c,
        oel_oelReferenceCurrent_multiSwitch1_y_default_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_power_N_Oel2c: oel_oelReferenceCurrent_C2_Oel2c,
        oel_oelReferenceCurrent_power1_N_Oel2c: oel_oelReferenceCurrent_C1_Oel2c,
        oel_oelReferenceCurrent_tErr0_Oel2c: oel_tErr0_Oel2c,
        oel_oelReferenceCurrent_tFcl_Oel2c: oel_tFcl_Oel2c,
        oel_oelReferenceCurrent_tInt0_Oel2c: oel_tInt0_Oel2c,
        oel_oelReferenceCurrent_tMax_Oel2c: oel_tMax_Oel2c,
        oel_oelReferenceCurrent_tMin_Oel2c: oel_tMin_Oel2c,
        oel_pid_D_T_Oel2c: (((oel_pid_Td_Oel2c / oel_pid_Nd_Oel2c) * sym.heaviside(((oel_pid_Td_Oel2c / oel_pid_Nd_Oel2c) - vf.add_const(value=1e-14)))) + (vf.add_const(value=1e-14) * (vf.add_const(value=1) - sym.heaviside(((oel_pid_Td_Oel2c / oel_pid_Nd_Oel2c) - vf.add_const(value=1e-14)))))),
        oel_pid_D_k_Oel2c: oel_pid_Td_Oel2c,
        oel_pid_D_x_start_Oel2c: oel_pid_xd_start_Oel2c,
        oel_pid_D_y_start_Oel2c: vf.add_const(value=0.0),
        oel_pid_FFzero_k_Oel2c: vf.add_const(value=0.0),
        oel_pid_I_k_Oel2c: (vf.add_const(value=1.0) / oel_pid_Ti_Oel2c),
        oel_pid_I_y_start_Oel2c: oel_pid_xi_start_Oel2c,
        oel_pid_Nd_Oel2c: vf.add_const(value=1.0),
        oel_pid_Ni_Oel2c: vf.add_const(value=0.9),
        oel_pid_P_k_Oel2c: vf.add_const(value=1.0),
        oel_pid_Td_Oel2c: oel_tDOel_Oel2c,
        oel_pid_Ti_Oel2c: (vf.add_const(value=1.0) / oel_KiOel_Oel2c),
        oel_pid_addD_k1_Oel2c: oel_pid_wd_Oel2c,
        oel_pid_addD_k2_Oel2c: vf.add_const(value=-1.0),
        oel_pid_addFF_k1_Oel2c: vf.add_const(value=1.0),
        oel_pid_addFF_k2_Oel2c: oel_pid_kFF_Oel2c,
        oel_pid_addI_k1_Oel2c: vf.add_const(value=1.0),
        oel_pid_addI_k2_Oel2c: vf.add_const(value=-1.0),
        oel_pid_addI_k3_Oel2c: vf.add_const(value=1.0),
        oel_pid_addP_k1_Oel2c: oel_pid_wp_Oel2c,
        oel_pid_addP_k2_Oel2c: vf.add_const(value=-1.0),
        oel_pid_addPID_k1_Oel2c: vf.add_const(value=1.0),
        oel_pid_addPID_k2_Oel2c: vf.add_const(value=1.0),
        oel_pid_addPID_k3_Oel2c: vf.add_const(value=1.0),
        oel_pid_addSat_k1_Oel2c: vf.add_const(value=1.0),
        oel_pid_addSat_k2_Oel2c: vf.add_const(value=-1.0),
        oel_pid_gainPID_k_Oel2c: oel_pid_k_Oel2c,
        oel_pid_gainTrack_k_Oel2c: (vf.add_const(value=1.0) / (oel_pid_Ni_Oel2c * oel_pid_k_Oel2c)),
        oel_pid_k_Oel2c: vf.add_const(value=1.0),
        oel_pid_kFF_Oel2c: vf.add_const(value=1.0),
        oel_pid_limiter_uMax_Oel2c: vf.add_const(value=1.0),
        oel_pid_limiter_uMin_Oel2c: vf.add_const(value=-1.0),
        oel_pid_wd_Oel2c: (oel_KdOel_Oel2c / oel_tDOel_Oel2c),
        oel_pid_wp_Oel2c: oel_KpOel_Oel2c,
        oel_pid_xd_start_Oel2c: vf.add_const(value=0.0),
        oel_pid_xi_start_Oel2c: vf.add_const(value=0.0),
        oel_pid_yMax_Oel2c: vf.add_const(value=1.0),
        oel_pid_yMin_Oel2c: vf.add_const(value=-1.0),
        oel_pid_y_start_Oel2c: vf.add_const(value=0.0),
        oel_tAOel_Oel2c: vf.add_const(value=0.02),
        oel_tB1Oel_Oel2c: vf.add_const(value=1.0),
        oel_tB2Oel_Oel2c: vf.add_const(value=1.0),
        oel_tC1Oel_Oel2c: vf.add_const(value=1.0),
        oel_tC2Oel_Oel2c: vf.add_const(value=1.0),
        oel_tDOel_Oel2c: vf.add_const(value=0.02),
        oel_tEn_Oel2c: vf.add_const(value=0.0),
        oel_tErr0_Oel2c: (oel_tFcl_Oel2c - oel_tInt0_Oel2c),
        oel_tFcl_Oel2c: vf.add_const(value=1.0),
        oel_tInt0_Oel2c: (((oel_K2_Oel2c * (vf.add_const(value=-1.0) + (oel_IScaled0Pu_Oel2c ** oel_C2_Oel2c))) + ((sym.heaviside(((vf.add_const(value=1.0) - oel_IScaled0Pu_Oel2c) + vf.add_const(value=1e-06))) * oel_FixedRu_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=1.0) - oel_IScaled0Pu_Oel2c) + vf.add_const(value=1e-06)))) * oel_FixedRd_Oel2c))) / oel_KFb_Oel2c),
        oel_tMax_Oel2c: vf.add_const(value=999.0),
        oel_tMin_Oel2c: vf.add_const(value=0.0),
        oel_tOff_Oel2c: vf.add_const(value=0.0),
        oel_tROel_Oel2c: vf.add_const(value=0.02),
        oel_firstOrder_initType_Oel2c: vf.add_const(value=1.0),
        oel_firstOrder1_initType_Oel2c: vf.add_const(value=1.0),
        oel_limitedLeadLag_firstOrder_initType_Oel2c: vf.add_const(value=1.0),
        oel_limitedLeadLag_limiter_homotopyType_Oel2c: vf.add_const(value=1.0),
        oel_limitedLeadLag1_firstOrder_initType_Oel2c: vf.add_const(value=1.0),
        oel_limitedLeadLag1_limiter_homotopyType_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_limIntegrator_initType_Oel2c: vf.add_const(value=3.0),
        oel_oelReferenceCurrent_limIntegrator1_initType_Oel2c: vf.add_const(value=3.0),
        oel_oelReferenceCurrent_limiter_homotopyType_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_multiSwitch1_nu_Oel2c: vf.add_const(value=2.0),
        oel_oelReferenceCurrent_multiSwitch1_precision_Oel2c: vf.add_const(value=3.0),
        oel_pid_D_initType_Oel2c: vf.add_const(value=1.0),
        oel_pid_I_initType_Oel2c: vf.add_const(value=3.0),
        oel_pid_controllerType_Oel2c: vf.add_const(value=4.0),
        oel_pid_homotopyType_Oel2c: vf.add_const(value=2.0),
        oel_pid_initType_Oel2c: vf.add_const(value=5.0),
        oel_pid_limiter_homotopyType_Oel2c: vf.add_const(value=2.0),
        oel_Sw1_Oel2c: vf.add_const(value=0.0),
        oel_limitedLeadLag_limiter_limitsAtInit_Oel2c: vf.add_const(value=1.0),
        oel_limitedLeadLag_limiter_strict_Oel2c: vf.add_const(value=0.0),
        oel_limitedLeadLag1_limiter_limitsAtInit_Oel2c: vf.add_const(value=1.0),
        oel_limitedLeadLag1_limiter_strict_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_Sw1_Oel2c: oel_Sw1_Oel2c,
        oel_oelReferenceCurrent_booleanConstant_k_Oel2c: oel_oelReferenceCurrent_Sw1_Oel2c,
        oel_oelReferenceCurrent_limIntegrator_limitsAtInit_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_limIntegrator_strict_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_limIntegrator_use_reset_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_limIntegrator_use_set_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_limIntegrator1_limitsAtInit_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_limIntegrator1_strict_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_limIntegrator1_use_reset_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_limIntegrator1_use_set_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_limiter_limitsAtInit_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_limiter_strict_Oel2c: vf.add_const(value=0.0),
        oel_oelReferenceCurrent_power_NInteger_Oel2c: vf.add_const(value=1.0),
        oel_oelReferenceCurrent_power1_NInteger_Oel2c: vf.add_const(value=1.0),
        oel_pid_D_zeroGain_Oel2c: sym.heaviside(((vf.add_const(value=2.220446049250313e-16) - sym.abs(oel_pid_D_k_Oel2c)) - vf.add_const(value=1e-06))),
        oel_pid_I_use_reset_Oel2c: vf.add_const(value=0.0),
        oel_pid_I_use_set_Oel2c: vf.add_const(value=0.0),
        oel_pid_limiter_limitsAtInit_Oel2c: vf.add_const(value=1.0),
        oel_pid_limiter_strict_Oel2c: vf.add_const(value=0.0),
        oel_pid_limitsAtInit_Oel2c: vf.add_const(value=1.0),
        oel_pid_strict_Oel2c: vf.add_const(value=0.0),
        oel_pid_withFeedForward_Oel2c: vf.add_const(value=0.0),
        oel_pid_with_D_Oel2c: vf.add_const(value=1.0),
        oel_pid_with_I_Oel2c: vf.add_const(value=1.0),
        oel_pid_unitTime_Oel2c: vf.add_const(value=1.0),
    })

    external_mapping: dict[object, Var] = dict()

    api_obj_mapping: dict[object, Var] = dict()

    templ.block = Block(
        state_eqs=[
            (((oel_firstOrder_k_Oel2c * oel_Input0Pu_Oel2c) - oel_firstOrder_y_Oel2c) / oel_firstOrder_T_Oel2c),
            (((oel_firstOrder1_k_Oel2c * oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - oel_firstOrder1_y_Oel2c) / oel_firstOrder1_T_Oel2c),
            ((oel_pid_D_zeroGain_Oel2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - oel_pid_D_zeroGain_Oel2c) * ((oel_pid_addD_y_Oel2c - oel_pid_D_x_Oel2c) / oel_pid_D_T_Oel2c))),
            (((oel_limitedLeadLag_firstOrder_k_Oel2c * oel_limitedLeadLag_y_Oel2c) - oel_limitedLeadLag_firstOrder_y_Oel2c) / oel_limitedLeadLag_firstOrder_T_Oel2c),
            (((oel_limitedLeadLag1_firstOrder_k_Oel2c * oel_UOelPu_Oel2c) - oel_limitedLeadLag1_firstOrder_y_Oel2c) / oel_limitedLeadLag1_firstOrder_T_Oel2c),
            (oel_pid_I_k_Oel2c * oel_pid_addI_y_Oel2c),
            (((vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator1_k_Oel2c * oel_oelReferenceCurrent_multiSwitch1_y_Oel2c)) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator1_k_Oel2c * oel_oelReferenceCurrent_multiSwitch1_y_Oel2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_y_Oel2c - oel_oelReferenceCurrent_limIntegrator1_outMax_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator1_k_Oel2c * oel_oelReferenceCurrent_multiSwitch1_y_Oel2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_y_Oel2c - oel_oelReferenceCurrent_limIntegrator1_outMax_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside((((oel_oelReferenceCurrent_limIntegrator1_k_Oel2c * oel_oelReferenceCurrent_multiSwitch1_y_Oel2c) - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))))))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator1_k_Oel2c * oel_oelReferenceCurrent_multiSwitch1_y_Oel2c)) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator1_k_Oel2c * oel_oelReferenceCurrent_multiSwitch1_y_Oel2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_y_Oel2c - oel_oelReferenceCurrent_limIntegrator1_outMax_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator1_k_Oel2c * oel_oelReferenceCurrent_multiSwitch1_y_Oel2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_y_Oel2c - oel_oelReferenceCurrent_limIntegrator1_outMax_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside((((oel_oelReferenceCurrent_limIntegrator1_k_Oel2c * oel_oelReferenceCurrent_multiSwitch1_y_Oel2c) - vf.add_const(value=0.0)) - vf.add_const(value=1e-06)))))))) * (oel_oelReferenceCurrent_limIntegrator1_k_Oel2c * oel_oelReferenceCurrent_multiSwitch1_y_Oel2c))),
            (((vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator_y_Oel2c) - vf.add_const(value=1e-06))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator_y_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator_k_Oel2c * oel_oelReferenceCurrent_feedback_y_Oel2c)) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator_y_Oel2c) - vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator_k_Oel2c * oel_oelReferenceCurrent_feedback_y_Oel2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_y_Oel2c - oel_oelReferenceCurrent_limIntegrator_outMax_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator_y_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator_k_Oel2c * oel_oelReferenceCurrent_feedback_y_Oel2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_y_Oel2c - oel_oelReferenceCurrent_limIntegrator_outMax_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside((((oel_oelReferenceCurrent_limIntegrator_k_Oel2c * oel_oelReferenceCurrent_feedback_y_Oel2c) - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))))))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - ((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator_y_Oel2c) - vf.add_const(value=1e-06))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator_y_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator_k_Oel2c * oel_oelReferenceCurrent_feedback_y_Oel2c)) - vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - ((((((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator_y_Oel2c) - vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator_k_Oel2c * oel_oelReferenceCurrent_feedback_y_Oel2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_y_Oel2c - oel_oelReferenceCurrent_limIntegrator_outMax_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_outMin_Oel2c - oel_oelReferenceCurrent_limIntegrator_y_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=0.0) - (oel_oelReferenceCurrent_limIntegrator_k_Oel2c * oel_oelReferenceCurrent_feedback_y_Oel2c)) - vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelReferenceCurrent_limIntegrator_y_Oel2c - oel_oelReferenceCurrent_limIntegrator_outMax_Oel2c) - vf.add_const(value=1e-06)))) * sym.heaviside((((oel_oelReferenceCurrent_limIntegrator_k_Oel2c * oel_oelReferenceCurrent_feedback_y_Oel2c) - vf.add_const(value=0.0)) - vf.add_const(value=1e-06)))))))) * (oel_oelReferenceCurrent_limIntegrator_k_Oel2c * oel_oelReferenceCurrent_feedback_y_Oel2c))),
        ],
        state_vars=[
            oel_firstOrder_y_Oel2c,
            oel_firstOrder1_y_Oel2c,
            oel_pid_D_x_Oel2c,
            oel_limitedLeadLag_firstOrder_y_Oel2c,
            oel_limitedLeadLag1_firstOrder_y_Oel2c,
            oel_pid_I_y_Oel2c,
            oel_oelReferenceCurrent_limIntegrator1_y_Oel2c,
            oel_oelReferenceCurrent_limIntegrator_y_Oel2c,
        ],
        algebraic_eqs=[
            (oel_gain4_y_Oel2c - (oel_gain4_k_Oel2c * oel_firstOrder_y_Oel2c)),
            (whenCondition2_Oel2c - sym.heaviside(((oel_gain4_y_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06)))),
            (oel_oelActivation_timer_y_Oel2c - ((whenCondition2_Oel2c * (time_Oel2c - oel_oelActivation_timer_entryTime_Oel2c)) + ((vf.add_const(value=1.0) - whenCondition2_Oel2c) * vf.add_const(value=0.0)))),
            (oel_oelActivation_timer_u_Oel2c - whenCondition2_Oel2c),
            (whenCondition1_Oel2c - sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_y_Oel2c - (oel_gain4_y_Oel2c + oel_oelActivation_IThOffPu_Oel2c)) - vf.add_const(value=1e-06)))),
            (oel_oelActivation_timer1_y_Oel2c - ((whenCondition1_Oel2c * (time_Oel2c - oel_oelActivation_timer1_entryTime_Oel2c)) + ((vf.add_const(value=1.0) - whenCondition1_Oel2c) * vf.add_const(value=0.0)))),
            (oel_oelActivation_timer1_u_Oel2c - whenCondition1_Oel2c),
            (oel_oelReferenceCurrent_tErr_Oel2c - (oel_oelReferenceCurrent_const3_k_Oel2c - oel_oelReferenceCurrent_limIntegrator_y_Oel2c)),
            (oel_oelReferenceCurrent_multiSwitch1_u_1_Oel2c - sym.heaviside(((oel_oelReferenceCurrent_tErr_Oel2c - oel_oelReferenceCurrent_greaterEqualThreshold_threshold_Oel2c) + vf.add_const(value=1e-06)))),
            (oel_oelReferenceCurrent_multiSwitch1_u_2_Oel2c - sym.heaviside(((oel_oelReferenceCurrent_lessEqualThreshold1_threshold_Oel2c - oel_oelReferenceCurrent_tErr_Oel2c) + vf.add_const(value=1e-06)))),
            (oel_oelReferenceCurrent_multiSwitch1_firstActiveIndex_Oel2c - ((vf.add_const(value=0.0) + ((vf.add_const(value=1.0) * oel_oelReferenceCurrent_multiSwitch1_u_1_Oel2c) * vf.add_const(value=1.0))) + ((vf.add_const(value=2.0) * oel_oelReferenceCurrent_multiSwitch1_u_2_Oel2c) * (vf.add_const(value=1.0) - oel_oelReferenceCurrent_multiSwitch1_u_1_Oel2c)))),
            (oel_oelActivation_IBiasPu_Oel2c - (((vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - (((vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - oel_oelReferenceCurrent_tErr_Oel2c) + vf.add_const(value=1e-06)))) * (vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - oel_oelReferenceCurrent_tErr_Oel2c) + vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((oel_oelActivation_timer_y_Oel2c - oel_oelActivation_tEn_Oel2c) + vf.add_const(value=1e-06))))))) * (vf.add_const(value=1.0) - (sym.heaviside(((oel_oelActivation_tEn_Oel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - oel_oelActivation_tEn_Oel2c) + vf.add_const(value=1e-06))))))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - (vf.add_const(value=1.0) - (((vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - oel_oelReferenceCurrent_tErr_Oel2c) + vf.add_const(value=1e-06)))) * (vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - oel_oelReferenceCurrent_tErr_Oel2c) + vf.add_const(value=1e-06))))) * (vf.add_const(value=1.0) - sym.heaviside(((oel_oelActivation_timer_y_Oel2c - oel_oelActivation_tEn_Oel2c) + vf.add_const(value=1e-06))))))) * (vf.add_const(value=1.0) - (sym.heaviside(((oel_oelActivation_tEn_Oel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - oel_oelActivation_tEn_Oel2c) + vf.add_const(value=1e-06)))))))) * ((((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_y_Oel2c - oel_oelActivation_IInstPu_Oel2c) + vf.add_const(value=1e-06))) * sym.heaviside(((oel_oelActivation_IInstPu_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelActivation_timer1_y_Oel2c - oel_oelActivation_tOff_Oel2c) - vf.add_const(value=1e-06)))) * oel_oelActivation_IResetPu_Oel2c) + ((vf.add_const(value=1.0) - ((sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_y_Oel2c - oel_oelActivation_IInstPu_Oel2c) + vf.add_const(value=1e-06))) * sym.heaviside(((oel_oelActivation_IInstPu_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) + vf.add_const(value=1e-06)))) * sym.heaviside(((oel_oelActivation_timer1_y_Oel2c - oel_oelActivation_tOff_Oel2c) - vf.add_const(value=1e-06))))) * vf.add_const(value=0.0)))))),
            (oel_pid_controlError_Oel2c - ((oel_add3_k1_Oel2c * oel_gain4_y_Oel2c) + ((oel_add3_k2_Oel2c * oel_oelActivation_IBiasPu_Oel2c) + (oel_add3_k3_Oel2c * oel_firstOrder1_y_Oel2c)))),
            (oel_pid_addP_y_Oel2c - (oel_pid_addP_k1_Oel2c * oel_pid_controlError_Oel2c)),
            (oel_pid_P_y_Oel2c - (oel_pid_P_k_Oel2c * oel_pid_addP_y_Oel2c)),
            (oel_pid_addD_y_Oel2c - (oel_pid_addD_k1_Oel2c * oel_pid_controlError_Oel2c)),
            (oel_pid_D_y_Oel2c - ((oel_pid_D_zeroGain_Oel2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - oel_pid_D_zeroGain_Oel2c) * ((oel_pid_D_k_Oel2c / oel_pid_D_T_Oel2c) * (oel_pid_addD_y_Oel2c - oel_pid_D_x_Oel2c))))),
            (oel_pid_addPID_y_Oel2c - ((oel_pid_addPID_k1_Oel2c * oel_pid_P_y_Oel2c) + ((oel_pid_addPID_k2_Oel2c * oel_pid_D_y_Oel2c) + (oel_pid_addPID_k3_Oel2c * oel_pid_I_y_Oel2c)))),
            (oel_pid_gainPID_y_Oel2c - (oel_pid_gainPID_k_Oel2c * oel_pid_addPID_y_Oel2c)),
            (oel_pid_limiter_u_Oel2c - ((oel_pid_addFF_k1_Oel2c * oel_pid_gainPID_y_Oel2c) + (oel_pid_addFF_k2_Oel2c * oel_pid_FFzero_k_Oel2c))),
            (oel_pid_y_Oel2c - ((sym.heaviside(((oel_pid_limiter_u_Oel2c - oel_pid_limiter_uMax_Oel2c) - vf.add_const(value=1e-06))) * oel_pid_limiter_uMax_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_pid_limiter_u_Oel2c - oel_pid_limiter_uMax_Oel2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((oel_pid_limiter_uMin_Oel2c - oel_pid_limiter_u_Oel2c) - vf.add_const(value=1e-06))) * oel_pid_limiter_uMin_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_pid_limiter_uMin_Oel2c - oel_pid_limiter_u_Oel2c) - vf.add_const(value=1e-06)))) * oel_pid_limiter_u_Oel2c))))),
            (oel_limitedLeadLag_feedback_y_Oel2c - (oel_pid_y_Oel2c - oel_limitedLeadLag_firstOrder_y_Oel2c)),
            (oel_limitedLeadLag_gain_y_Oel2c - (oel_limitedLeadLag_gain_k_Oel2c * oel_limitedLeadLag_feedback_y_Oel2c)),
            (oel_limitedLeadLag_y_Oel2c - ((sym.heaviside(((oel_limitedLeadLag_gain_y_Oel2c - oel_limitedLeadLag_limiter_uMax_Oel2c) - vf.add_const(value=1e-06))) * oel_limitedLeadLag_limiter_uMax_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_limitedLeadLag_gain_y_Oel2c - oel_limitedLeadLag_limiter_uMax_Oel2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((oel_limitedLeadLag_limiter_uMin_Oel2c - oel_limitedLeadLag_gain_y_Oel2c) - vf.add_const(value=1e-06))) * oel_limitedLeadLag_limiter_uMin_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_limitedLeadLag_limiter_uMin_Oel2c - oel_limitedLeadLag_gain_y_Oel2c) - vf.add_const(value=1e-06)))) * oel_limitedLeadLag_gain_y_Oel2c))))),
            (oel_limitedLeadLag1_feedback_y_Oel2c - (oel_limitedLeadLag_y_Oel2c - oel_limitedLeadLag1_firstOrder_y_Oel2c)),
            (oel_limitedLeadLag1_gain_y_Oel2c - (oel_limitedLeadLag1_gain_k_Oel2c * oel_limitedLeadLag1_feedback_y_Oel2c)),
            (oel_UOelPu_Oel2c - ((sym.heaviside(((oel_limitedLeadLag1_gain_y_Oel2c - oel_limitedLeadLag1_limiter_uMax_Oel2c) - vf.add_const(value=1e-06))) * oel_limitedLeadLag1_limiter_uMax_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_limitedLeadLag1_gain_y_Oel2c - oel_limitedLeadLag1_limiter_uMax_Oel2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((oel_limitedLeadLag1_limiter_uMin_Oel2c - oel_limitedLeadLag1_gain_y_Oel2c) - vf.add_const(value=1e-06))) * oel_limitedLeadLag1_limiter_uMin_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_limitedLeadLag1_limiter_uMin_Oel2c - oel_limitedLeadLag1_gain_y_Oel2c) - vf.add_const(value=1e-06)))) * oel_limitedLeadLag1_gain_y_Oel2c))))),
            (oel_pid_addSat_y_Oel2c - ((oel_pid_addSat_k1_Oel2c * oel_pid_y_Oel2c) + (oel_pid_addSat_k2_Oel2c * oel_pid_limiter_u_Oel2c))),
            (oel_pid_gainTrack_y_Oel2c - (oel_pid_gainTrack_k_Oel2c * oel_pid_addSat_y_Oel2c)),
            (oel_pid_addI_y_Oel2c - ((oel_pid_addI_k1_Oel2c * oel_pid_controlError_Oel2c) + (oel_pid_addI_k3_Oel2c * oel_pid_gainTrack_y_Oel2c))),
            (oel_oelReferenceCurrent_gain_y_Oel2c - (oel_oelReferenceCurrent_gain_k_Oel2c * oel_firstOrder_y_Oel2c)),
            (oel_oelReferenceCurrent_power1_y_Oel2c - (oel_oelReferenceCurrent_gain_y_Oel2c ** oel_oelReferenceCurrent_power1_N_Oel2c)),
            (oel_oelReferenceCurrent_feedback1_y_Oel2c - (oel_oelReferenceCurrent_power1_y_Oel2c - oel_oelReferenceCurrent_const_k_Oel2c)),
            (oel_oelReferenceCurrent_gain1_y_Oel2c - (oel_oelReferenceCurrent_gain1_k_Oel2c * oel_oelReferenceCurrent_feedback1_y_Oel2c)),
            (oel_oelReferenceCurrent_multiSwitch1_expr_2_Oel2c - ((oel_oelReferenceCurrent_booleanConstant_k_Oel2c * oel_oelReferenceCurrent_gain1_y_Oel2c) + ((vf.add_const(value=1.0) - oel_oelReferenceCurrent_booleanConstant_k_Oel2c) * oel_oelReferenceCurrent_const4_k_Oel2c))),
            (oel_oelReferenceCurrent_multiSwitch1_expr_1_Oel2c - ((oel_oelReferenceCurrent_booleanConstant_k_Oel2c * oel_oelReferenceCurrent_gain1_y_Oel2c) + ((vf.add_const(value=1.0) - oel_oelReferenceCurrent_booleanConstant_k_Oel2c) * oel_oelReferenceCurrent_const5_k_Oel2c))),
            (oel_oelReferenceCurrent_multiSwitch1_y_Oel2c - (((sym.heaviside(((oel_oelReferenceCurrent_multiSwitch1_firstActiveIndex_Oel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - oel_oelReferenceCurrent_multiSwitch1_firstActiveIndex_Oel2c) + vf.add_const(value=1e-06)))) * oel_oelReferenceCurrent_multiSwitch1_y_default_Oel2c) + ((vf.add_const(value=1.0) - (sym.heaviside(((oel_oelReferenceCurrent_multiSwitch1_firstActiveIndex_Oel2c - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - oel_oelReferenceCurrent_multiSwitch1_firstActiveIndex_Oel2c) + vf.add_const(value=1e-06))))) * oel_oelReferenceCurrent_multiSwitch1_expr_Oel2c))),
            (oel_oelReferenceCurrent_power_y_Oel2c - (oel_oelReferenceCurrent_gain_y_Oel2c ** oel_oelReferenceCurrent_power_N_Oel2c)),
            (oel_oelReferenceCurrent_feedback2_y_Oel2c - (oel_oelReferenceCurrent_power_y_Oel2c - oel_oelReferenceCurrent_const_k_Oel2c)),
            (oel_oelReferenceCurrent_gain2_y_Oel2c - (oel_oelReferenceCurrent_gain2_k_Oel2c * oel_oelReferenceCurrent_feedback2_y_Oel2c)),
            (oel_oelReferenceCurrent_limiter_y_Oel2c - ((sym.heaviside(((oel_oelReferenceCurrent_gain2_y_Oel2c - oel_oelReferenceCurrent_limiter_uMax_Oel2c) - vf.add_const(value=1e-06))) * oel_oelReferenceCurrent_limiter_uMax_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_oelReferenceCurrent_gain2_y_Oel2c - oel_oelReferenceCurrent_limiter_uMax_Oel2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((oel_oelReferenceCurrent_limiter_uMin_Oel2c - oel_oelReferenceCurrent_gain2_y_Oel2c) - vf.add_const(value=1e-06))) * oel_oelReferenceCurrent_limiter_uMin_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_oelReferenceCurrent_limiter_uMin_Oel2c - oel_oelReferenceCurrent_gain2_y_Oel2c) - vf.add_const(value=1e-06)))) * oel_oelReferenceCurrent_gain2_y_Oel2c))))),
            (oel_oelReferenceCurrent_lessEqualThreshold_y_Oel2c - sym.heaviside(((oel_oelReferenceCurrent_lessEqualThreshold_threshold_Oel2c - oel_oelReferenceCurrent_gain_y_Oel2c) + vf.add_const(value=1e-06)))),
            (oel_oelReferenceCurrent_switch_y_Oel2c - ((oel_oelReferenceCurrent_lessEqualThreshold_y_Oel2c * oel_oelReferenceCurrent_const1_k_Oel2c) + ((vf.add_const(value=1.0) - oel_oelReferenceCurrent_lessEqualThreshold_y_Oel2c) * oel_oelReferenceCurrent_const2_k_Oel2c))),
            (oel_oelReferenceCurrent_add_y_Oel2c - ((oel_oelReferenceCurrent_add_k1_Oel2c * oel_oelReferenceCurrent_limiter_y_Oel2c) + (oel_oelReferenceCurrent_add_k2_Oel2c * oel_oelReferenceCurrent_switch_y_Oel2c))),
            (oel_oelReferenceCurrent_gain3_y_Oel2c - (oel_oelReferenceCurrent_gain3_k_Oel2c * oel_oelReferenceCurrent_limIntegrator_y_Oel2c)),
            (oel_oelReferenceCurrent_feedback_y_Oel2c - (oel_oelReferenceCurrent_add_y_Oel2c - oel_oelReferenceCurrent_gain3_y_Oel2c)),
        ],
        algebraic_vars=[
            oel_gain4_y_Oel2c,
            whenCondition2_Oel2c,
            oel_oelActivation_timer_y_Oel2c,
            oel_oelActivation_timer_u_Oel2c,
            whenCondition1_Oel2c,
            oel_oelActivation_timer1_y_Oel2c,
            oel_oelActivation_timer1_u_Oel2c,
            oel_oelReferenceCurrent_tErr_Oel2c,
            oel_oelReferenceCurrent_multiSwitch1_u_1_Oel2c,
            oel_oelReferenceCurrent_multiSwitch1_u_2_Oel2c,
            oel_oelReferenceCurrent_multiSwitch1_firstActiveIndex_Oel2c,
            oel_oelActivation_IBiasPu_Oel2c,
            oel_pid_controlError_Oel2c,
            oel_pid_addP_y_Oel2c,
            oel_pid_P_y_Oel2c,
            oel_pid_addD_y_Oel2c,
            oel_pid_D_y_Oel2c,
            oel_pid_addPID_y_Oel2c,
            oel_pid_gainPID_y_Oel2c,
            oel_pid_limiter_u_Oel2c,
            oel_pid_y_Oel2c,
            oel_limitedLeadLag_feedback_y_Oel2c,
            oel_limitedLeadLag_gain_y_Oel2c,
            oel_limitedLeadLag_y_Oel2c,
            oel_limitedLeadLag1_feedback_y_Oel2c,
            oel_limitedLeadLag1_gain_y_Oel2c,
            oel_UOelPu_Oel2c,
            oel_pid_addSat_y_Oel2c,
            oel_pid_gainTrack_y_Oel2c,
            oel_pid_addI_y_Oel2c,
            oel_oelReferenceCurrent_gain_y_Oel2c,
            oel_oelReferenceCurrent_power1_y_Oel2c,
            oel_oelReferenceCurrent_feedback1_y_Oel2c,
            oel_oelReferenceCurrent_gain1_y_Oel2c,
            oel_oelReferenceCurrent_multiSwitch1_expr_2_Oel2c,
            oel_oelReferenceCurrent_multiSwitch1_expr_1_Oel2c,
            oel_oelReferenceCurrent_multiSwitch1_y_Oel2c,
            oel_oelReferenceCurrent_power_y_Oel2c,
            oel_oelReferenceCurrent_feedback2_y_Oel2c,
            oel_oelReferenceCurrent_gain2_y_Oel2c,
            oel_oelReferenceCurrent_limiter_y_Oel2c,
            oel_oelReferenceCurrent_lessEqualThreshold_y_Oel2c,
            oel_oelReferenceCurrent_switch_y_Oel2c,
            oel_oelReferenceCurrent_add_y_Oel2c,
            oel_oelReferenceCurrent_gain3_y_Oel2c,
            oel_oelReferenceCurrent_feedback_y_Oel2c,
            oel_oelActivation_timer_entryTime_Oel2c,
            oel_oelActivation_timer1_entryTime_Oel2c,
            oel_oelReferenceCurrent_multiSwitch1_expr_Oel2c,
            oel_inputPu_Oel2c,
            oel_limitedLeadLag_limiter_simplifiedExpr_Oel2c,
            oel_limitedLeadLag1_limiter_simplifiedExpr_Oel2c,
            oel_pid_I_local_reset_Oel2c,
            oel_pid_I_local_set_Oel2c,
            oel_oelReferenceCurrent_limIntegrator1_local_reset_Oel2c,
            oel_oelReferenceCurrent_limIntegrator1_local_set_Oel2c,
            oel_oelReferenceCurrent_limiter_simplifiedExpr_Oel2c,
            oel_oelReferenceCurrent_limIntegrator_local_reset_Oel2c,
            oel_oelReferenceCurrent_limIntegrator_local_set_Oel2c,
            oel_pid_u_m_Oel2c,
            START_oel_firstOrder_y_Oel2c,
            START_oel_firstOrder1_y_Oel2c,
            START_oel_limitedLeadLag_firstOrder_y_Oel2c,
            START_oel_limitedLeadLag1_firstOrder_y_Oel2c,
            START_oel_pid_D_x_Oel2c,
            PRE_oel_oelActivation_timer1_entryTime_Oel2c,
            PRE_oel_oelActivation_timer_entryTime_Oel2c,
            PRE_oel_oelReferenceCurrent_multiSwitch1_u_2_Oel2c,
            PRE_oel_oelReferenceCurrent_multiSwitch1_u_1_Oel2c,
        ],
        init_eqs={
            oel_firstOrder_y_Oel2c: START_oel_firstOrder_y_Oel2c,
            oel_firstOrder1_y_Oel2c: START_oel_firstOrder1_y_Oel2c,
            oel_limitedLeadLag_firstOrder_y_Oel2c: START_oel_limitedLeadLag_firstOrder_y_Oel2c,
            oel_limitedLeadLag1_firstOrder_y_Oel2c: START_oel_limitedLeadLag1_firstOrder_y_Oel2c,
            oel_oelReferenceCurrent_limIntegrator_y_Oel2c: oel_oelReferenceCurrent_limIntegrator_y_start_Oel2c,
            oel_oelReferenceCurrent_limIntegrator1_y_Oel2c: oel_oelReferenceCurrent_limIntegrator1_y_start_Oel2c,
            oel_pid_D_x_Oel2c: START_oel_pid_D_x_Oel2c,
            oel_pid_I_y_Oel2c: oel_pid_I_y_start_Oel2c,
            oel_UOelPu_Oel2c: oel_limitedLeadLag1_Y0_Oel2c,
            oel_gain4_y_Oel2c: oel_oelActivation_IRef0Pu_Oel2c,
            oel_inputPu_Oel2c: vf.add_const(value=1.0),
            oel_limitedLeadLag_y_Oel2c: oel_limitedLeadLag_Y0_Oel2c,
            oel_oelActivation_IBiasPu_Oel2c: vf.add_const(value=0.0),
            oel_oelReferenceCurrent_multiSwitch1_expr_1_Oel2c: vf.add_const(value=0.1),
            oel_oelReferenceCurrent_multiSwitch1_expr_2_Oel2c: vf.add_const(value=0.1),
            oel_oelReferenceCurrent_tErr_Oel2c: oel_oelActivation_tErr0_Oel2c,
            oel_limitedLeadLag_limiter_simplifiedExpr_Oel2c: vf.add_const(value=0.0),
            oel_limitedLeadLag1_limiter_simplifiedExpr_Oel2c: vf.add_const(value=0.0),
            oel_pid_I_local_reset_Oel2c: vf.add_const(value=0.0),
            oel_pid_I_local_set_Oel2c: vf.add_const(value=0.0),
            oel_oelReferenceCurrent_limIntegrator1_local_reset_Oel2c: vf.add_const(value=0.0),
            oel_oelReferenceCurrent_limIntegrator1_local_set_Oel2c: vf.add_const(value=0.0),
            oel_oelReferenceCurrent_limiter_simplifiedExpr_Oel2c: vf.add_const(value=0.0),
            oel_oelReferenceCurrent_limIntegrator_local_reset_Oel2c: vf.add_const(value=0.0),
            oel_oelReferenceCurrent_limIntegrator_local_set_Oel2c: vf.add_const(value=0.0),
            oel_pid_u_m_Oel2c: vf.add_const(value=0.0),
            oel_oelActivation_timer1_u_Oel2c: sym.heaviside(((oel_oelReferenceCurrent_limIntegrator1_y_Oel2c - (oel_gain4_y_Oel2c + oel_oelActivation_IThOffPu_Oel2c)) - vf.add_const(value=1e-06))),
            whenCondition1_Oel2c: oel_oelActivation_timer1_u_Oel2c,
            oel_oelActivation_timer_u_Oel2c: sym.heaviside(((oel_gain4_y_Oel2c - oel_oelReferenceCurrent_limIntegrator1_y_Oel2c) - vf.add_const(value=1e-06))),
            whenCondition2_Oel2c: oel_oelActivation_timer_u_Oel2c,
            PRE_oel_oelActivation_timer1_entryTime_Oel2c: vf.add_const(value=0.0),
            oel_oelActivation_timer1_entryTime_Oel2c: PRE_oel_oelActivation_timer1_entryTime_Oel2c,
            oel_oelActivation_timer1_y_Oel2c: ((oel_oelActivation_timer1_u_Oel2c * (time_Oel2c - oel_oelActivation_timer1_entryTime_Oel2c)) + ((vf.add_const(value=1.0) - oel_oelActivation_timer1_u_Oel2c) * vf.add_const(value=0.0))),
            PRE_oel_oelActivation_timer_entryTime_Oel2c: vf.add_const(value=0.0),
            oel_oelActivation_timer_entryTime_Oel2c: PRE_oel_oelActivation_timer_entryTime_Oel2c,
            oel_oelActivation_timer_y_Oel2c: ((oel_oelActivation_timer_u_Oel2c * (time_Oel2c - oel_oelActivation_timer_entryTime_Oel2c)) + ((vf.add_const(value=1.0) - oel_oelActivation_timer_u_Oel2c) * vf.add_const(value=0.0))),
            oel_pid_y_Oel2c: ((sym.heaviside(((oel_pid_limiter_u_Oel2c - oel_pid_limiter_uMax_Oel2c) - vf.add_const(value=1e-06))) * oel_pid_limiter_uMax_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_pid_limiter_u_Oel2c - oel_pid_limiter_uMax_Oel2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((oel_pid_limiter_uMin_Oel2c - oel_pid_limiter_u_Oel2c) - vf.add_const(value=1e-06))) * oel_pid_limiter_uMin_Oel2c) + ((vf.add_const(value=1.0) - sym.heaviside(((oel_pid_limiter_uMin_Oel2c - oel_pid_limiter_u_Oel2c) - vf.add_const(value=1e-06)))) * oel_pid_limiter_u_Oel2c)))),
            PRE_oel_oelReferenceCurrent_multiSwitch1_u_2_Oel2c: vf.add_const(value=0.0),
            PRE_oel_oelReferenceCurrent_multiSwitch1_u_1_Oel2c: vf.add_const(value=0.0),
        },
        event_dict=event_dict,
        in_vars=inputs,
        out_vars=[
        ],
        external_mapping=external_mapping,
        api_obj_mapping=api_obj_mapping,
        diff_vars=[
            d_oel_firstOrder_y_Oel2c,
            d_oel_firstOrder1_y_Oel2c,
            d_oel_pid_D_x_Oel2c,
            d_oel_limitedLeadLag_firstOrder_y_Oel2c,
            d_oel_limitedLeadLag1_firstOrder_y_Oel2c,
            d_oel_pid_I_y_Oel2c,
            d_oel_oelReferenceCurrent_limIntegrator1_y_Oel2c,
            d_oel_oelReferenceCurrent_limIntegrator_y_Oel2c,
        ],
        name=template_name,
    )
    templ.comment = 'Generator over-excitation limiter OEL2C'
    return templ
