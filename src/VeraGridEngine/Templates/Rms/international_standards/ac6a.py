# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Ac6a'.

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

def build_ac6a_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
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
        template_name: str = 'Ac6a'
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
    avr_acRotatingExciter_firstOrder_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.firstOrder.y_Ac6a')
    avr_transferFunction1_x_scaled_1_Ac6a: Var = vf.add_var(name='avr.transferFunction1.x_scaled[1]_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.x_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.x_Ac6a')
    avr_transferFunction_x_scaled_1_Ac6a: Var = vf.add_var(name='avr.transferFunction.x_scaled[1]_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_w_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.w_Ac6a')
    avr_limitedLeadLag_firstOrder_y_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.firstOrder.y_Ac6a')
    avr_firstOrder_y_Ac6a: Var = vf.add_var(name='avr.firstOrder.y_Ac6a')

    # Algebraic variables
    avr_transferFunction1_x_1_Ac6a: Var = vf.add_var(name='avr.transferFunction1.x[1]_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.y_Ac6a')
    avr_acRotatingExciter_division_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.division.y_Ac6a')
    avr_acRotatingExciter_rectifierRegulationCharacteristic_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.rectifierRegulationCharacteristic.y_Ac6a')
    avr_EfdPu_Ac6a: Var = vf.add_var(name='avr.EfdPu_Ac6a')
    avr_acRotatingExciter_product1_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.product1.y_Ac6a')
    avr_acRotatingExciter_division1_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.division1.y_Ac6a')
    avr_acRotatingExciter_VfePu_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.VfePu_Ac6a')
    avr_add_y_Ac6a: Var = vf.add_var(name='avr.add.y_Ac6a')
    avr_gain1_y_Ac6a: Var = vf.add_var(name='avr.gain1.y_Ac6a')
    avr_limiter_y_Ac6a: Var = vf.add_var(name='avr.limiter.y_Ac6a')
    avr_transferFunction1_y_Ac6a: Var = vf.add_var(name='avr.transferFunction1.y_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.y_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.y_Ac6a')
    avr_transferFunction_x_1_Ac6a: Var = vf.add_var(name='avr.transferFunction.x[1]_Ac6a')
    avr_sum1_u_1_Ac6a: Var = vf.add_var(name='avr.sum1.u[1]_Ac6a')
    avr_sum1_y_Ac6a: Var = vf.add_var(name='avr.sum1.y_Ac6a')
    avr_gain_y_Ac6a: Var = vf.add_var(name='avr.gain.y_Ac6a')
    avr_transferFunction_y_Ac6a: Var = vf.add_var(name='avr.transferFunction.y_Ac6a')
    avr_limitedLeadLag_feedback_y_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.feedback.y_Ac6a')
    avr_limitedLeadLag_gain_y_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.gain.y_Ac6a')
    avr_limitedLeadLag_y_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.y_Ac6a')
    avr_feedback_y_Ac6a: Var = vf.add_var(name='avr.feedback.y_Ac6a')
    avr_variableLimiter_y_Ac6a: Var = vf.add_var(name='avr.variableLimiter.y_Ac6a')
    avr_acRotatingExciter_feedback_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.feedback.y_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_startFreezingMax_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.startFreezingMax_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.keepFreezingMax_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.isFrozenMax_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_startFreezingMin_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.startFreezingMin_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.keepFreezingMin_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.isFrozenMin_Ac6a')
    avr_acRotatingExciter_add_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.add.y_Ac6a')
    avr_acRotatingExciter_add1_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.add1.y_Ac6a')
    avr_IrPu_Ac6a: Var = vf.add_var(name='avr.IrPu_Ac6a')
    avr_UPssPu_Ac6a: Var = vf.add_var(name='avr.UPssPu_Ac6a')
    avr_UUelPu_Ac6a: Var = vf.add_var(name='avr.UUelPu_Ac6a')
    avr_UsPu_Ac6a: Var = vf.add_var(name='avr.UsPu_Ac6a')
    avr_UsRefPu_Ac6a: Var = vf.add_var(name='avr.UsRefPu_Ac6a')
    avr_limitedLeadLag_limiter_simplifiedExpr_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.limiter.simplifiedExpr_Ac6a')
    avr_variableLimiter_simplifiedExpr_Ac6a: Var = vf.add_var(name='avr.variableLimiter.simplifiedExpr_Ac6a')
    avr_limiter_simplifiedExpr_Ac6a: Var = vf.add_var(name='avr.limiter.simplifiedExpr_Ac6a')
    START_avr_firstOrder_y_Ac6a: Var = vf.add_var(name='$START.avr.firstOrder.y_Ac6a')
    START_avr_transferFunction_x_scaled_1_Ac6a: Var = vf.add_var(name='$START.avr.transferFunction.x_scaled[1]_Ac6a')
    START_avr_limitedLeadLag_firstOrder_y_Ac6a: Var = vf.add_var(name='$START.avr.limitedLeadLag.firstOrder.y_Ac6a')
    START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a: Var = vf.add_var(name='$START.avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.x_Ac6a')
    START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a: Var = vf.add_var(name='$START.avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.x_Ac6a')
    PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a: Var = vf.add_var(name='$PRE.avr.acRotatingExciter.integratorVariableLimits.isFrozenMax_Ac6a')
    START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a: Var = vf.add_var(name='$START.avr.acRotatingExciter.integratorVariableLimits.isFrozenMax_Ac6a')
    PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a: Var = vf.add_var(name='$PRE.avr.acRotatingExciter.integratorVariableLimits.isFrozenMin_Ac6a')
    START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a: Var = vf.add_var(name='$START.avr.acRotatingExciter.integratorVariableLimits.isFrozenMin_Ac6a')
    START_avr_acRotatingExciter_integratorVariableLimits_w_Ac6a: Var = vf.add_var(name='$START.avr.acRotatingExciter.integratorVariableLimits.w_Ac6a')
    START_avr_acRotatingExciter_firstOrder_y_Ac6a: Var = vf.add_var(name='$START.avr.acRotatingExciter.firstOrder.y_Ac6a')
    START_avr_transferFunction1_x_scaled_1_Ac6a: Var = vf.add_var(name='$START.avr.transferFunction1.x_scaled[1]_Ac6a')
    avr_acRotatingExciter_power_y_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.power.y_Ac6a')

    # Differential variables
    d_avr_acRotatingExciter_firstOrder_y_Ac6a: Var = vf.add_diff_var(name='d_avr.acRotatingExciter.firstOrder.y_Ac6a', base_var=avr_acRotatingExciter_firstOrder_y_Ac6a)
    d_avr_transferFunction1_x_scaled_1_Ac6a: Var = vf.add_diff_var(name='d_avr.transferFunction1.x_scaled[1]_Ac6a', base_var=avr_transferFunction1_x_scaled_1_Ac6a)
    d_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a: Var = vf.add_diff_var(name='d_avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.x_Ac6a', base_var=avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a)
    d_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a: Var = vf.add_diff_var(name='d_avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.x_Ac6a', base_var=avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a)
    d_avr_transferFunction_x_scaled_1_Ac6a: Var = vf.add_diff_var(name='d_avr.transferFunction.x_scaled[1]_Ac6a', base_var=avr_transferFunction_x_scaled_1_Ac6a)
    d_avr_acRotatingExciter_integratorVariableLimits_w_Ac6a: Var = vf.add_diff_var(name='d_avr.acRotatingExciter.integratorVariableLimits.w_Ac6a', base_var=avr_acRotatingExciter_integratorVariableLimits_w_Ac6a)
    d_avr_limitedLeadLag_firstOrder_y_Ac6a: Var = vf.add_diff_var(name='d_avr.limitedLeadLag.firstOrder.y_Ac6a', base_var=avr_limitedLeadLag_firstOrder_y_Ac6a)
    d_avr_firstOrder_y_Ac6a: Var = vf.add_diff_var(name='d_avr.firstOrder.y_Ac6a', base_var=avr_firstOrder_y_Ac6a)

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________

    # Runtime parameters and event variables
    avr_acRotatingExciter_firstOrder_T_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.firstOrder.T_Ac6a')
    avr_acRotatingExciter_firstOrder_k_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.firstOrder.k_Ac6a')
    avr_transferFunction1_a_2_Ac6a: Var = vf.add_var(name='avr.transferFunction1.a[2]_Ac6a')
    avr_transferFunction1_a_1_Ac6a: Var = vf.add_var(name='avr.transferFunction1.a[1]_Ac6a')
    avr_transferFunction1_a_end_Ac6a: Var = vf.add_var(name='avr.transferFunction1.a_end_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.zeroGain_Ac6a')
    avr_acRotatingExciter_const1_k_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.const1.k_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_T_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.T_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.zeroGain_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_T_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.T_Ac6a')
    avr_transferFunction_a_end_Ac6a: Var = vf.add_var(name='avr.transferFunction.a_end_Ac6a')
    avr_transferFunction_a_1_Ac6a: Var = vf.add_var(name='avr.transferFunction.a[1]_Ac6a')
    avr_transferFunction_a_2_Ac6a: Var = vf.add_var(name='avr.transferFunction.a[2]_Ac6a')
    avr_limitedLeadLag_firstOrder_T_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.firstOrder.T_Ac6a')
    avr_limitedLeadLag_firstOrder_k_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.firstOrder.k_Ac6a')
    avr_firstOrder_T_Ac6a: Var = vf.add_var(name='avr.firstOrder.T_Ac6a')
    avr_firstOrder_k_Ac6a: Var = vf.add_var(name='avr.firstOrder.k_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_DefaultLimitMax_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.DefaultLimitMax_Ac6a')
    avr_acRotatingExciter_gain_k_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.gain.k_Ac6a')
    avr_acRotatingExciter_rectifierRegulationCharacteristic_A1_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.rectifierRegulationCharacteristic.A1_Ac6a')
    avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.rectifierRegulationCharacteristic.UHigh_Ac6a')
    avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.rectifierRegulationCharacteristic.ULow_Ac6a')
    avr_acRotatingExciter_rectifierRegulationCharacteristic_A2_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.rectifierRegulationCharacteristic.A2_Ac6a')
    avr_acRotatingExciter_add2_k1_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.add2.k1_Ac6a')
    avr_acRotatingExciter_add2_k2_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.add2.k2_Ac6a')
    avr_acRotatingExciter_gain1_k_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.gain1.k_Ac6a')
    avr_add_k2_Ac6a: Var = vf.add_var(name='avr.add.k2_Ac6a')
    avr_const_k_Ac6a: Var = vf.add_var(name='avr.const.k_Ac6a')
    avr_add_k1_Ac6a: Var = vf.add_var(name='avr.add.k1_Ac6a')
    avr_gain1_k_Ac6a: Var = vf.add_var(name='avr.gain1.k_Ac6a')
    avr_limiter_uMax_Ac6a: Var = vf.add_var(name='avr.limiter.uMax_Ac6a')
    avr_limiter_uMin_Ac6a: Var = vf.add_var(name='avr.limiter.uMin_Ac6a')
    avr_transferFunction1_bb_2_Ac6a: Var = vf.add_var(name='avr.transferFunction1.bb[2]_Ac6a')
    avr_transferFunction1_d_Ac6a: Var = vf.add_var(name='avr.transferFunction1.d_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_k_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.k_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_k_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.k_Ac6a')
    avr_sum1_k_1_Ac6a: Var = vf.add_var(name='avr.sum1.k[1]_Ac6a')
    avr_gain_k_Ac6a: Var = vf.add_var(name='avr.gain.k_Ac6a')
    avr_transferFunction_bb_2_Ac6a: Var = vf.add_var(name='avr.transferFunction.bb[2]_Ac6a')
    avr_transferFunction_d_Ac6a: Var = vf.add_var(name='avr.transferFunction.d_Ac6a')
    avr_limitedLeadLag_gain_k_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.gain.k_Ac6a')
    avr_limitedLeadLag_limiter_uMin_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.limiter.uMin_Ac6a')
    avr_limitedLeadLag_limiter_uMax_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.limiter.uMax_Ac6a')
    avr_gain3_k_Ac6a: Var = vf.add_var(name='avr.gain3.k_Ac6a')
    avr_gain2_k_Ac6a: Var = vf.add_var(name='avr.gain2.k_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_K_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.K_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.LimitMax0_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.LimitMin0_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_Tol_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.Tol_Ac6a')
    avr_acRotatingExciter_Efd0Pu_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.Efd0Pu_Ac6a')
    avr_acRotatingExciter_Efe0Pu_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.Efe0Pu_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_Y0_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.Y0_Ac6a')
    avr_limitedLeadLag_Y0_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.Y0_Ac6a')
    avr_transferFunction_x_start_1_Ac6a: Var = vf.add_var(name='avr.transferFunction.x_start[1]_Ac6a')
    avr_transferFunction_y_start_Ac6a: Var = vf.add_var(name='avr.transferFunction.y_start_Ac6a')
    avr_transferFunction1_x_start_1_Ac6a: Var = vf.add_var(name='avr.transferFunction1.x_start[1]_Ac6a')
    avr_transferFunction1_y_start_Ac6a: Var = vf.add_var(name='avr.transferFunction1.y_start_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_FrozenMax0_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.FrozenMax0_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_FrozenMin0_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.FrozenMin0_Ac6a')
    avr_acRotatingExciter_add1_k2_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.add1.k2_Ac6a')
    avr_acRotatingExciter_const_k_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.const.k_Ac6a')
    avr_acRotatingExciter_add1_k1_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.add1.k1_Ac6a')
    avr_acRotatingExciter_add_k2_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.add.k2_Ac6a')
    avr_acRotatingExciter_const2_k_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.const2.k_Ac6a')
    avr_acRotatingExciter_add_k1_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.add.k1_Ac6a')
    avr_AEx_Ac6a: Var = vf.add_var(name='avr.AEx_Ac6a')
    avr_BEx_Ac6a: Var = vf.add_var(name='avr.BEx_Ac6a')
    avr_Efd0Pu_Ac6a: Var = vf.add_var(name='avr.Efd0Pu_Ac6a')
    avr_Efe0Pu_Ac6a: Var = vf.add_var(name='avr.Efe0Pu_Ac6a')
    avr_EfeMaxPu_Ac6a: Var = vf.add_var(name='avr.EfeMaxPu_Ac6a')
    avr_EfeMinPu_Ac6a: Var = vf.add_var(name='avr.EfeMinPu_Ac6a')
    avr_Ir0Pu_Ac6a: Var = vf.add_var(name='avr.Ir0Pu_Ac6a')
    avr_Ka_Ac6a: Var = vf.add_var(name='avr.Ka_Ac6a')
    avr_Kc_Ac6a: Var = vf.add_var(name='avr.Kc_Ac6a')
    avr_Kd_Ac6a: Var = vf.add_var(name='avr.Kd_Ac6a')
    avr_Ke_Ac6a: Var = vf.add_var(name='avr.Ke_Ac6a')
    avr_Kh_Ac6a: Var = vf.add_var(name='avr.Kh_Ac6a')
    avr_TolLi_Ac6a: Var = vf.add_var(name='avr.TolLi_Ac6a')
    avr_UUel0Pu_Ac6a: Var = vf.add_var(name='avr.UUel0Pu_Ac6a')
    avr_Us0Pu_Ac6a: Var = vf.add_var(name='avr.Us0Pu_Ac6a')
    avr_UsRef0Pu_Ac6a: Var = vf.add_var(name='avr.UsRef0Pu_Ac6a')
    avr_Va0Pu_Ac6a: Var = vf.add_var(name='avr.Va0Pu_Ac6a')
    avr_Vh0Pu_Ac6a: Var = vf.add_var(name='avr.Vh0Pu_Ac6a')
    avr_VaMaxPu_Ac6a: Var = vf.add_var(name='avr.VaMaxPu_Ac6a')
    avr_VaMinPu_Ac6a: Var = vf.add_var(name='avr.VaMinPu_Ac6a')
    avr_Ve0Pu_Ac6a: Var = vf.add_var(name='avr.Ve0Pu_Ac6a')
    avr_VeMax0Pu_Ac6a: Var = vf.add_var(name='avr.VeMax0Pu_Ac6a')
    avr_VeMinPu_Ac6a: Var = vf.add_var(name='avr.VeMinPu_Ac6a')
    avr_VfeLimPu_Ac6a: Var = vf.add_var(name='avr.VfeLimPu_Ac6a')
    avr_VfeMaxPu_Ac6a: Var = vf.add_var(name='avr.VfeMaxPu_Ac6a')
    avr_VhMaxPu_Ac6a: Var = vf.add_var(name='avr.VhMaxPu_Ac6a')
    avr_acRotatingExciter_AEx_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.AEx_Ac6a')
    avr_acRotatingExciter_BEx_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.BEx_Ac6a')
    avr_acRotatingExciter_Ir0Pu_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.Ir0Pu_Ac6a')
    avr_acRotatingExciter_Kc_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.Kc_Ac6a')
    avr_acRotatingExciter_Kd_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.Kd_Ac6a')
    avr_acRotatingExciter_Ke_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.Ke_Ac6a')
    avr_acRotatingExciter_TolLi_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.TolLi_Ac6a')
    avr_acRotatingExciter_Ve0Pu_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.Ve0Pu_Ac6a')
    avr_acRotatingExciter_VeMax0Pu_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.VeMax0Pu_Ac6a')
    avr_acRotatingExciter_VeMinPu_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.VeMinPu_Ac6a')
    avr_acRotatingExciter_VfeMaxPu_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.VfeMaxPu_Ac6a')
    avr_acRotatingExciter_firstOrder_y_start_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.firstOrder.y_start_Ac6a')
    avr_acRotatingExciter_tE_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.tE_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_tDer_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.tDer_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_start_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.x_start_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_start_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.y_start_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_start_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.x_start_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_start_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.y_start_Ac6a')
    avr_acRotatingExciter_power_base_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.power.base_Ac6a')
    avr_tE_Ac6a: Var = vf.add_var(name='avr.tE_Ac6a')
    avr_add3_k1_Ac6a: Var = vf.add_var(name='avr.add3.k1_Ac6a')
    avr_add3_k2_Ac6a: Var = vf.add_var(name='avr.add3.k2_Ac6a')
    avr_add3_k3_Ac6a: Var = vf.add_var(name='avr.add3.k3_Ac6a')
    avr_tR_Ac6a: Var = vf.add_var(name='avr.tR_Ac6a')
    avr_firstOrder_y_start_Ac6a: Var = vf.add_var(name='avr.firstOrder.y_start_Ac6a')
    avr_limitedLeadLag_K_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.K_Ac6a')
    avr_limitedLeadLag_YMax_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.YMax_Ac6a')
    avr_limitedLeadLag_YMin_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.YMin_Ac6a')
    avr_limitedLeadLag_t1_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.t1_Ac6a')
    avr_limitedLeadLag_t2_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.t2_Ac6a')
    avr_limitedLeadLag_firstOrder_y_start_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.firstOrder.y_start_Ac6a')
    avr_tC_Ac6a: Var = vf.add_var(name='avr.tC_Ac6a')
    avr_tB_Ac6a: Var = vf.add_var(name='avr.tB_Ac6a')
    avr_sum1_k_2_Ac6a: Var = vf.add_var(name='avr.sum1.k[2]_Ac6a')
    avr_tA_Ac6a: Var = vf.add_var(name='avr.tA_Ac6a')
    avr_tH_Ac6a: Var = vf.add_var(name='avr.tH_Ac6a')
    avr_tJ_Ac6a: Var = vf.add_var(name='avr.tJ_Ac6a')
    avr_tK_Ac6a: Var = vf.add_var(name='avr.tK_Ac6a')
    avr_transferFunction_b_1_Ac6a: Var = vf.add_var(name='avr.transferFunction.b[1]_Ac6a')
    avr_transferFunction_b_2_Ac6a: Var = vf.add_var(name='avr.transferFunction.b[2]_Ac6a')
    avr_transferFunction_bb_1_Ac6a: Var = vf.add_var(name='avr.transferFunction.bb[1]_Ac6a')
    avr_transferFunction1_b_1_Ac6a: Var = vf.add_var(name='avr.transferFunction1.b[1]_Ac6a')
    avr_transferFunction1_b_2_Ac6a: Var = vf.add_var(name='avr.transferFunction1.b[2]_Ac6a')
    avr_transferFunction1_bb_1_Ac6a: Var = vf.add_var(name='avr.transferFunction1.bb[1]_Ac6a')
    avr_variableLimiter_ySimplified_Ac6a: Var = vf.add_var(name='avr.variableLimiter.ySimplified_Ac6a')
    avr_acRotatingExciter_firstOrder_initType_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.firstOrder.initType_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_initType_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.initType_Ac6a')
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_initType_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.initType_Ac6a')
    avr_firstOrder_initType_Ac6a: Var = vf.add_var(name='avr.firstOrder.initType_Ac6a')
    avr_limitedLeadLag_firstOrder_initType_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.firstOrder.initType_Ac6a')
    avr_limitedLeadLag_limiter_homotopyType_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.limiter.homotopyType_Ac6a')
    avr_limiter_homotopyType_Ac6a: Var = vf.add_var(name='avr.limiter.homotopyType_Ac6a')
    avr_sum1_nin_Ac6a: Var = vf.add_var(name='avr.sum1.nin_Ac6a')
    avr_transferFunction_na_Ac6a: Var = vf.add_var(name='avr.transferFunction.na_Ac6a')
    avr_transferFunction_nb_Ac6a: Var = vf.add_var(name='avr.transferFunction.nb_Ac6a')
    avr_transferFunction_nx_Ac6a: Var = vf.add_var(name='avr.transferFunction.nx_Ac6a')
    avr_transferFunction1_na_Ac6a: Var = vf.add_var(name='avr.transferFunction1.na_Ac6a')
    avr_transferFunction1_nb_Ac6a: Var = vf.add_var(name='avr.transferFunction1.nb_Ac6a')
    avr_transferFunction1_nx_Ac6a: Var = vf.add_var(name='avr.transferFunction1.nx_Ac6a')
    avr_variableLimiter_homotopyType_Ac6a: Var = vf.add_var(name='avr.variableLimiter.homotopyType_Ac6a')
    avr_acRotatingExciter_power_useExp_Ac6a: Var = vf.add_var(name='avr.acRotatingExciter.power.useExp_Ac6a')
    avr_limitedLeadLag_limiter_limitsAtInit_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.limiter.limitsAtInit_Ac6a')
    avr_limitedLeadLag_limiter_strict_Ac6a: Var = vf.add_var(name='avr.limitedLeadLag.limiter.strict_Ac6a')
    avr_limiter_limitsAtInit_Ac6a: Var = vf.add_var(name='avr.limiter.limitsAtInit_Ac6a')
    avr_limiter_strict_Ac6a: Var = vf.add_var(name='avr.limiter.strict_Ac6a')
    avr_variableLimiter_limitsAtInit_Ac6a: Var = vf.add_var(name='avr.variableLimiter.limitsAtInit_Ac6a')
    avr_variableLimiter_strict_Ac6a: Var = vf.add_var(name='avr.variableLimiter.strict_Ac6a')

    event_dict: dict[Var, Expr | Const] = dict({
        avr_AEx_Ac6a: vf.add_const(value=0.0),
        avr_BEx_Ac6a: vf.add_const(value=0.0),
        avr_Efd0Pu_Ac6a: vf.add_const(value=1.0),
        avr_Efe0Pu_Ac6a: vf.add_const(value=1.0),
        avr_EfeMaxPu_Ac6a: vf.add_const(value=5.0),
        avr_EfeMinPu_Ac6a: vf.add_const(value=-5.0),
        avr_Ir0Pu_Ac6a: vf.add_const(value=1.0),
        avr_Ka_Ac6a: vf.add_const(value=200.0),
        avr_Kc_Ac6a: vf.add_const(value=0.0),
        avr_Kd_Ac6a: vf.add_const(value=0.0),
        avr_Ke_Ac6a: vf.add_const(value=1.0),
        avr_Kh_Ac6a: vf.add_const(value=0.05),
        avr_TolLi_Ac6a: vf.add_const(value=1e-06),
        avr_UUel0Pu_Ac6a: vf.add_const(value=0.0),
        avr_Us0Pu_Ac6a: vf.add_const(value=1.0),
        avr_UsRef0Pu_Ac6a: ((avr_Va0Pu_Ac6a / avr_Ka_Ac6a) + avr_Us0Pu_Ac6a),
        avr_Va0Pu_Ac6a: (avr_Efe0Pu_Ac6a + avr_Vh0Pu_Ac6a),
        avr_VaMaxPu_Ac6a: vf.add_const(value=5.0),
        avr_VaMinPu_Ac6a: vf.add_const(value=-5.0),
        avr_Ve0Pu_Ac6a: vf.add_const(value=1.0),
        avr_VeMax0Pu_Ac6a: vf.add_const(value=5.0),
        avr_VeMinPu_Ac6a: vf.add_const(value=0.0),
        avr_VfeLimPu_Ac6a: vf.add_const(value=1.0),
        avr_VfeMaxPu_Ac6a: vf.add_const(value=999.0),
        avr_Vh0Pu_Ac6a: ((vf.add_const(value=0.0) * sym.heaviside((vf.add_const(value=0.0) - ((avr_VhMaxPu_Ac6a * sym.heaviside(((avr_Kh_Ac6a * (avr_Efe0Pu_Ac6a - avr_VfeLimPu_Ac6a)) - avr_VhMaxPu_Ac6a))) + ((avr_Kh_Ac6a * (avr_Efe0Pu_Ac6a - avr_VfeLimPu_Ac6a)) * (vf.add_const(value=1) - sym.heaviside(((avr_Kh_Ac6a * (avr_Efe0Pu_Ac6a - avr_VfeLimPu_Ac6a)) - avr_VhMaxPu_Ac6a)))))))) + (((avr_VhMaxPu_Ac6a * sym.heaviside(((avr_Kh_Ac6a * (avr_Efe0Pu_Ac6a - avr_VfeLimPu_Ac6a)) - avr_VhMaxPu_Ac6a))) + ((avr_Kh_Ac6a * (avr_Efe0Pu_Ac6a - avr_VfeLimPu_Ac6a)) * (vf.add_const(value=1) - sym.heaviside(((avr_Kh_Ac6a * (avr_Efe0Pu_Ac6a - avr_VfeLimPu_Ac6a)) - avr_VhMaxPu_Ac6a))))) * (vf.add_const(value=1) - sym.heaviside((vf.add_const(value=0.0) - ((avr_VhMaxPu_Ac6a * sym.heaviside(((avr_Kh_Ac6a * (avr_Efe0Pu_Ac6a - avr_VfeLimPu_Ac6a)) - avr_VhMaxPu_Ac6a))) + ((avr_Kh_Ac6a * (avr_Efe0Pu_Ac6a - avr_VfeLimPu_Ac6a)) * (vf.add_const(value=1) - sym.heaviside(((avr_Kh_Ac6a * (avr_Efe0Pu_Ac6a - avr_VfeLimPu_Ac6a)) - avr_VhMaxPu_Ac6a)))))))))),
        avr_VhMaxPu_Ac6a: vf.add_const(value=5.0),
        avr_acRotatingExciter_AEx_Ac6a: avr_AEx_Ac6a,
        avr_acRotatingExciter_BEx_Ac6a: vf.add_const(value=0.0),
        avr_acRotatingExciter_Efd0Pu_Ac6a: avr_Efd0Pu_Ac6a,
        avr_acRotatingExciter_Efe0Pu_Ac6a: avr_Efe0Pu_Ac6a,
        avr_acRotatingExciter_Ir0Pu_Ac6a: avr_Ir0Pu_Ac6a,
        avr_acRotatingExciter_Kc_Ac6a: avr_Kc_Ac6a,
        avr_acRotatingExciter_Kd_Ac6a: avr_Kd_Ac6a,
        avr_acRotatingExciter_Ke_Ac6a: avr_Ke_Ac6a,
        avr_acRotatingExciter_TolLi_Ac6a: avr_TolLi_Ac6a,
        avr_acRotatingExciter_Ve0Pu_Ac6a: avr_Ve0Pu_Ac6a,
        avr_acRotatingExciter_VeMax0Pu_Ac6a: avr_VeMax0Pu_Ac6a,
        avr_acRotatingExciter_VeMinPu_Ac6a: avr_VeMinPu_Ac6a,
        avr_acRotatingExciter_VfeMaxPu_Ac6a: avr_VfeMaxPu_Ac6a,
        avr_acRotatingExciter_add_k1_Ac6a: avr_acRotatingExciter_AEx_Ac6a,
        avr_acRotatingExciter_add_k2_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_add1_k1_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_add1_k2_Ac6a: vf.add_const(value=-1.0),
        avr_acRotatingExciter_add2_k1_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_add2_k2_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_const_k_Ac6a: avr_acRotatingExciter_VfeMaxPu_Ac6a,
        avr_acRotatingExciter_const1_k_Ac6a: avr_acRotatingExciter_VeMinPu_Ac6a,
        avr_acRotatingExciter_const2_k_Ac6a: avr_acRotatingExciter_Ke_Ac6a,
        avr_acRotatingExciter_firstOrder_T_Ac6a: vf.add_const(value=1e-05),
        avr_acRotatingExciter_firstOrder_k_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_firstOrder_y_start_Ac6a: avr_acRotatingExciter_VeMax0Pu_Ac6a,
        avr_acRotatingExciter_gain_k_Ac6a: avr_acRotatingExciter_Kc_Ac6a,
        avr_acRotatingExciter_gain1_k_Ac6a: avr_acRotatingExciter_Kd_Ac6a,
        avr_acRotatingExciter_integratorVariableLimits_K_Ac6a: (vf.add_const(value=1.0) / avr_acRotatingExciter_tE_Ac6a),
        avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a: avr_acRotatingExciter_VeMax0Pu_Ac6a,
        avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a: avr_acRotatingExciter_VeMinPu_Ac6a,
        avr_acRotatingExciter_integratorVariableLimits_Tol_Ac6a: avr_acRotatingExciter_TolLi_Ac6a,
        avr_acRotatingExciter_integratorVariableLimits_Y0_Ac6a: avr_acRotatingExciter_Ve0Pu_Ac6a,
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_T_Ac6a: avr_acRotatingExciter_integratorVariableLimits_tDer_Ac6a,
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_k_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_start_Ac6a: avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a,
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_start_Ac6a: vf.add_const(value=0.0),
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_T_Ac6a: avr_acRotatingExciter_integratorVariableLimits_tDer_Ac6a,
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_k_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_start_Ac6a: avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a,
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_start_Ac6a: vf.add_const(value=0.0),
        avr_acRotatingExciter_integratorVariableLimits_tDer_Ac6a: vf.add_const(value=0.01),
        avr_acRotatingExciter_power_base_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_rectifierRegulationCharacteristic_A1_Ac6a: (((sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a) + vf.add_const(value=1e-06)))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a - vf.add_const(value=0.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=0.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a) + vf.add_const(value=1e-06))))) * ((vf.add_const(value=1.0) - sym.sqrt((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a - (avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a ** vf.add_const(value=2.0))))) / avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a))),
        avr_acRotatingExciter_rectifierRegulationCharacteristic_A2_Ac6a: (((sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a - vf.add_const(value=1.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=1.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a) + vf.add_const(value=1e-06)))) * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - (sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a - vf.add_const(value=1.0)) + vf.add_const(value=1e-06))) * sym.heaviside(((vf.add_const(value=1.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a) + vf.add_const(value=1e-06))))) * sym.sqrt((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a / (vf.add_const(value=1.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a))))),
        avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a: vf.add_const(value=0.75),
        avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a: vf.add_const(value=0.4330127018922193),
        avr_acRotatingExciter_tE_Ac6a: avr_tE_Ac6a,
        avr_add_k1_Ac6a: vf.add_const(value=1.0),
        avr_add_k2_Ac6a: vf.add_const(value=-1.0),
        avr_add3_k1_Ac6a: vf.add_const(value=1.0),
        avr_add3_k2_Ac6a: vf.add_const(value=-1.0),
        avr_add3_k3_Ac6a: vf.add_const(value=1.0),
        avr_const_k_Ac6a: avr_VfeLimPu_Ac6a,
        avr_firstOrder_T_Ac6a: avr_tR_Ac6a,
        avr_firstOrder_k_Ac6a: vf.add_const(value=1.0),
        avr_firstOrder_y_start_Ac6a: avr_Us0Pu_Ac6a,
        avr_gain_k_Ac6a: avr_Ka_Ac6a,
        avr_gain1_k_Ac6a: avr_Kh_Ac6a,
        avr_gain2_k_Ac6a: avr_EfeMaxPu_Ac6a,
        avr_gain3_k_Ac6a: avr_EfeMinPu_Ac6a,
        avr_limitedLeadLag_K_Ac6a: vf.add_const(value=1.0),
        avr_limitedLeadLag_Y0_Ac6a: avr_Va0Pu_Ac6a,
        avr_limitedLeadLag_YMax_Ac6a: avr_VaMaxPu_Ac6a,
        avr_limitedLeadLag_YMin_Ac6a: avr_VaMinPu_Ac6a,
        avr_limitedLeadLag_firstOrder_T_Ac6a: avr_limitedLeadLag_t1_Ac6a,
        avr_limitedLeadLag_firstOrder_k_Ac6a: ((avr_limitedLeadLag_t1_Ac6a - avr_limitedLeadLag_t2_Ac6a) / (avr_limitedLeadLag_t1_Ac6a * avr_limitedLeadLag_K_Ac6a)),
        avr_limitedLeadLag_firstOrder_y_start_Ac6a: (avr_limitedLeadLag_Y0_Ac6a * ((avr_limitedLeadLag_t1_Ac6a - avr_limitedLeadLag_t2_Ac6a) / (avr_limitedLeadLag_t1_Ac6a * avr_limitedLeadLag_K_Ac6a))),
        avr_limitedLeadLag_gain_k_Ac6a: (avr_limitedLeadLag_K_Ac6a * (avr_limitedLeadLag_t1_Ac6a / avr_limitedLeadLag_t2_Ac6a)),
        avr_limitedLeadLag_limiter_uMax_Ac6a: avr_limitedLeadLag_YMax_Ac6a,
        avr_limitedLeadLag_limiter_uMin_Ac6a: avr_limitedLeadLag_YMin_Ac6a,
        avr_limitedLeadLag_t1_Ac6a: avr_tC_Ac6a,
        avr_limitedLeadLag_t2_Ac6a: avr_tB_Ac6a,
        avr_limiter_uMax_Ac6a: avr_VhMaxPu_Ac6a,
        avr_limiter_uMin_Ac6a: vf.add_const(value=0.0),
        avr_sum1_k_1_Ac6a: vf.add_const(value=1.0),
        avr_sum1_k_2_Ac6a: vf.add_const(value=1.0),
        avr_tA_Ac6a: vf.add_const(value=0.02),
        avr_tB_Ac6a: vf.add_const(value=1.0),
        avr_tC_Ac6a: vf.add_const(value=1.0),
        avr_tE_Ac6a: vf.add_const(value=0.5),
        avr_tH_Ac6a: vf.add_const(value=1.0),
        avr_tJ_Ac6a: vf.add_const(value=1.0),
        avr_tK_Ac6a: vf.add_const(value=1.0),
        avr_tR_Ac6a: vf.add_const(value=0.02),
        avr_transferFunction_a_1_Ac6a: avr_tA_Ac6a,
        avr_transferFunction_a_2_Ac6a: vf.add_const(value=1.0),
        avr_transferFunction_a_end_Ac6a: ((sym.heaviside(((avr_transferFunction_a_2_Ac6a - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((avr_transferFunction_a_1_Ac6a ** vf.add_const(value=2.0)) + (avr_transferFunction_a_2_Ac6a ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06))) * avr_transferFunction_a_2_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_transferFunction_a_2_Ac6a - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((avr_transferFunction_a_1_Ac6a ** vf.add_const(value=2.0)) + (avr_transferFunction_a_2_Ac6a ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06)))) * vf.add_const(value=1.0))),
        avr_transferFunction_b_1_Ac6a: avr_tK_Ac6a,
        avr_transferFunction_b_2_Ac6a: vf.add_const(value=1.0),
        avr_transferFunction_bb_1_Ac6a: avr_transferFunction_b_1_Ac6a,
        avr_transferFunction_bb_2_Ac6a: avr_transferFunction_b_2_Ac6a,
        avr_transferFunction_d_Ac6a: (avr_transferFunction_bb_1_Ac6a / avr_transferFunction_a_1_Ac6a),
        avr_transferFunction_x_start_1_Ac6a: avr_Va0Pu_Ac6a,
        avr_transferFunction_y_start_Ac6a: avr_Va0Pu_Ac6a,
        avr_transferFunction1_a_1_Ac6a: avr_tH_Ac6a,
        avr_transferFunction1_a_2_Ac6a: vf.add_const(value=1.0),
        avr_transferFunction1_a_end_Ac6a: ((sym.heaviside(((avr_transferFunction1_a_2_Ac6a - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((avr_transferFunction1_a_1_Ac6a ** vf.add_const(value=2.0)) + (avr_transferFunction1_a_2_Ac6a ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06))) * avr_transferFunction1_a_2_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_transferFunction1_a_2_Ac6a - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((avr_transferFunction1_a_1_Ac6a ** vf.add_const(value=2.0)) + (avr_transferFunction1_a_2_Ac6a ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06)))) * vf.add_const(value=1.0))),
        avr_transferFunction1_b_1_Ac6a: avr_tJ_Ac6a,
        avr_transferFunction1_b_2_Ac6a: vf.add_const(value=1.0),
        avr_transferFunction1_bb_1_Ac6a: avr_transferFunction1_b_1_Ac6a,
        avr_transferFunction1_bb_2_Ac6a: avr_transferFunction1_b_2_Ac6a,
        avr_transferFunction1_d_Ac6a: (avr_transferFunction1_bb_1_Ac6a / avr_transferFunction1_a_1_Ac6a),
        avr_transferFunction1_x_start_1_Ac6a: avr_Vh0Pu_Ac6a,
        avr_transferFunction1_y_start_Ac6a: avr_Vh0Pu_Ac6a,
        avr_variableLimiter_ySimplified_Ac6a: vf.add_const(value=0.0),
        avr_acRotatingExciter_firstOrder_initType_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_initType_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_initType_Ac6a: vf.add_const(value=1.0),
        avr_firstOrder_initType_Ac6a: vf.add_const(value=1.0),
        avr_limitedLeadLag_firstOrder_initType_Ac6a: vf.add_const(value=1.0),
        avr_limitedLeadLag_limiter_homotopyType_Ac6a: vf.add_const(value=1.0),
        avr_limiter_homotopyType_Ac6a: vf.add_const(value=1.0),
        avr_sum1_nin_Ac6a: vf.add_const(value=2.0),
        avr_transferFunction_na_Ac6a: vf.add_const(value=2.0),
        avr_transferFunction_nb_Ac6a: vf.add_const(value=2.0),
        avr_transferFunction_nx_Ac6a: vf.add_const(value=1.0),
        avr_transferFunction1_na_Ac6a: vf.add_const(value=2.0),
        avr_transferFunction1_nb_Ac6a: vf.add_const(value=2.0),
        avr_transferFunction1_nx_Ac6a: vf.add_const(value=1.0),
        avr_variableLimiter_homotopyType_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_integratorVariableLimits_DefaultLimitMax_Ac6a: vf.add_const(value=1.0),
        avr_acRotatingExciter_integratorVariableLimits_FrozenMax0_Ac6a: sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_Y0_Ac6a - (avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a - (avr_acRotatingExciter_integratorVariableLimits_Tol_Ac6a * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a - avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a))))) - vf.add_const(value=1e-06))),
        avr_acRotatingExciter_integratorVariableLimits_FrozenMin0_Ac6a: sym.heaviside((((avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a + (avr_acRotatingExciter_integratorVariableLimits_Tol_Ac6a * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a - avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a)))) - avr_acRotatingExciter_integratorVariableLimits_Y0_Ac6a) - vf.add_const(value=1e-06))),
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain_Ac6a: sym.heaviside(((vf.add_const(value=2.220446049250313e-16) - sym.abs(avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_k_Ac6a)) - vf.add_const(value=1e-06))),
        avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain_Ac6a: sym.heaviside(((vf.add_const(value=2.220446049250313e-16) - sym.abs(avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_k_Ac6a)) - vf.add_const(value=1e-06))),
        avr_acRotatingExciter_power_useExp_Ac6a: vf.add_const(value=1.0),
        avr_limitedLeadLag_limiter_limitsAtInit_Ac6a: vf.add_const(value=1.0),
        avr_limitedLeadLag_limiter_strict_Ac6a: vf.add_const(value=0.0),
        avr_limiter_limitsAtInit_Ac6a: vf.add_const(value=1.0),
        avr_limiter_strict_Ac6a: vf.add_const(value=0.0),
        avr_variableLimiter_limitsAtInit_Ac6a: vf.add_const(value=1.0),
        avr_variableLimiter_strict_Ac6a: vf.add_const(value=0.0),
    })

    external_mapping: dict[object, Var] = dict()

    api_obj_mapping: dict[object, Var] = dict()

    templ.block = Block(
        state_eqs=[
            (((avr_acRotatingExciter_firstOrder_k_Ac6a * avr_acRotatingExciter_division1_y_Ac6a) - avr_acRotatingExciter_firstOrder_y_Ac6a) / avr_acRotatingExciter_firstOrder_T_Ac6a),
            (((avr_transferFunction1_a_end_Ac6a * avr_limiter_y_Ac6a) - (avr_transferFunction1_a_2_Ac6a * avr_transferFunction1_x_scaled_1_Ac6a)) / avr_transferFunction1_a_1_Ac6a),
            ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain_Ac6a * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain_Ac6a) * ((avr_acRotatingExciter_const1_k_Ac6a - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a) / avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_T_Ac6a))),
            ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain_Ac6a * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain_Ac6a) * ((avr_acRotatingExciter_firstOrder_y_Ac6a - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a) / avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_T_Ac6a))),
            (((avr_transferFunction_a_end_Ac6a * avr_gain_y_Ac6a) - (avr_transferFunction_a_2_Ac6a * avr_transferFunction_x_scaled_1_Ac6a)) / avr_transferFunction_a_1_Ac6a),
            ((avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a * avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_Ac6a) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a) * ((avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a * avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_Ac6a) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a) * (avr_acRotatingExciter_integratorVariableLimits_K_Ac6a * avr_acRotatingExciter_feedback_y_Ac6a))))),
            (((avr_limitedLeadLag_firstOrder_k_Ac6a * avr_limitedLeadLag_y_Ac6a) - avr_limitedLeadLag_firstOrder_y_Ac6a) / avr_limitedLeadLag_firstOrder_T_Ac6a),
            (((avr_firstOrder_k_Ac6a * avr_UsPu_Ac6a) - avr_firstOrder_y_Ac6a) / avr_firstOrder_T_Ac6a),
        ],
        state_vars=[
            avr_acRotatingExciter_firstOrder_y_Ac6a,
            avr_transferFunction1_x_scaled_1_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a,
            avr_transferFunction_x_scaled_1_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_w_Ac6a,
            avr_limitedLeadLag_firstOrder_y_Ac6a,
            avr_firstOrder_y_Ac6a,
        ],
        algebraic_eqs=[
            (avr_transferFunction1_x_1_Ac6a - (avr_transferFunction1_x_scaled_1_Ac6a / avr_transferFunction1_a_end_Ac6a)),
            (avr_acRotatingExciter_integratorVariableLimits_y_Ac6a - (((sym.heaviside(((avr_acRotatingExciter_const1_k_Ac6a - avr_acRotatingExciter_firstOrder_y_Ac6a) - vf.add_const(value=1e-06))) * avr_acRotatingExciter_integratorVariableLimits_DefaultLimitMax_Ac6a) * avr_acRotatingExciter_firstOrder_y_Ac6a) + ((vf.add_const(value=1.0) - (sym.heaviside(((avr_acRotatingExciter_const1_k_Ac6a - avr_acRotatingExciter_firstOrder_y_Ac6a) - vf.add_const(value=1e-06))) * avr_acRotatingExciter_integratorVariableLimits_DefaultLimitMax_Ac6a)) * ((sym.heaviside(((avr_acRotatingExciter_const1_k_Ac6a - avr_acRotatingExciter_firstOrder_y_Ac6a) - vf.add_const(value=1e-06))) * avr_acRotatingExciter_const1_k_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_acRotatingExciter_const1_k_Ac6a - avr_acRotatingExciter_firstOrder_y_Ac6a) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((avr_acRotatingExciter_const1_k_Ac6a - avr_acRotatingExciter_integratorVariableLimits_w_Ac6a) - vf.add_const(value=1e-06))) * avr_acRotatingExciter_const1_k_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_acRotatingExciter_const1_k_Ac6a - avr_acRotatingExciter_integratorVariableLimits_w_Ac6a) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w_Ac6a - avr_acRotatingExciter_firstOrder_y_Ac6a) - vf.add_const(value=1e-06))) * avr_acRotatingExciter_firstOrder_y_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w_Ac6a - avr_acRotatingExciter_firstOrder_y_Ac6a) - vf.add_const(value=1e-06)))) * avr_acRotatingExciter_integratorVariableLimits_w_Ac6a))))))))),
            (avr_acRotatingExciter_division_y_Ac6a - (avr_acRotatingExciter_gain_k_Ac6a / avr_acRotatingExciter_integratorVariableLimits_y_Ac6a)),
            (avr_acRotatingExciter_rectifierRegulationCharacteristic_y_Ac6a - ((sym.heaviside(((vf.add_const(value=0.0) - avr_acRotatingExciter_division_y_Ac6a) + vf.add_const(value=1e-06))) * vf.add_const(value=1.0)) + ((vf.add_const(value=1.0) - sym.heaviside(((vf.add_const(value=0.0) - avr_acRotatingExciter_division_y_Ac6a) + vf.add_const(value=1e-06)))) * ((((sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - vf.add_const(value=0.0)) - vf.add_const(value=1e-06)))) * sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a - avr_acRotatingExciter_division_y_Ac6a) + vf.add_const(value=1e-06)))) * (vf.add_const(value=1.0) - (avr_acRotatingExciter_rectifierRegulationCharacteristic_A1_Ac6a * avr_acRotatingExciter_division_y_Ac6a))) + ((vf.add_const(value=1.0) - ((sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - vf.add_const(value=0.0)) - vf.add_const(value=1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - vf.add_const(value=0.0)) - vf.add_const(value=1e-06)))) * sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a - avr_acRotatingExciter_division_y_Ac6a) + vf.add_const(value=1e-06))))) * ((((sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a) - vf.add_const(value=1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a) - vf.add_const(value=1e-06)))) * sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a - avr_acRotatingExciter_division_y_Ac6a) - vf.add_const(value=1e-06)))) * sym.sqrt((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a - (avr_acRotatingExciter_division_y_Ac6a ** vf.add_const(value=2.0))))) + ((vf.add_const(value=1.0) - ((sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a) - vf.add_const(value=1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow_Ac6a) - vf.add_const(value=1e-06)))) * sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a - avr_acRotatingExciter_division_y_Ac6a) - vf.add_const(value=1e-06))))) * ((((sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a) + vf.add_const(value=1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a) + vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=1.0) - avr_acRotatingExciter_division_y_Ac6a) + vf.add_const(value=1e-06)))) * (avr_acRotatingExciter_rectifierRegulationCharacteristic_A2_Ac6a * (vf.add_const(value=1.0) - avr_acRotatingExciter_division_y_Ac6a))) + ((vf.add_const(value=1.0) - ((sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a) + vf.add_const(value=1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y_Ac6a - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh_Ac6a) + vf.add_const(value=1e-06)))) * sym.heaviside(((vf.add_const(value=1.0) - avr_acRotatingExciter_division_y_Ac6a) + vf.add_const(value=1e-06))))) * vf.add_const(value=0.0)))))))))),
            (avr_EfdPu_Ac6a - (avr_acRotatingExciter_rectifierRegulationCharacteristic_y_Ac6a * avr_acRotatingExciter_integratorVariableLimits_y_Ac6a)),
            (avr_acRotatingExciter_product1_y_Ac6a - (avr_acRotatingExciter_add_y_Ac6a * avr_acRotatingExciter_integratorVariableLimits_y_Ac6a)),
            (avr_acRotatingExciter_division1_y_Ac6a - (avr_acRotatingExciter_add1_y_Ac6a / avr_acRotatingExciter_product1_y_Ac6a)),
            (avr_acRotatingExciter_VfePu_Ac6a - ((avr_acRotatingExciter_add2_k1_Ac6a * avr_acRotatingExciter_gain1_k_Ac6a) + (avr_acRotatingExciter_add2_k2_Ac6a * avr_acRotatingExciter_product1_y_Ac6a))),
            (avr_add_y_Ac6a - ((avr_add_k1_Ac6a * avr_acRotatingExciter_VfePu_Ac6a) + (avr_add_k2_Ac6a * avr_const_k_Ac6a))),
            (avr_gain1_y_Ac6a - (avr_gain1_k_Ac6a * avr_add_y_Ac6a)),
            (avr_limiter_y_Ac6a - ((sym.heaviside(((avr_gain1_y_Ac6a - avr_limiter_uMax_Ac6a) - vf.add_const(value=1e-06))) * avr_limiter_uMax_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_gain1_y_Ac6a - avr_limiter_uMax_Ac6a) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((avr_limiter_uMin_Ac6a - avr_gain1_y_Ac6a) - vf.add_const(value=1e-06))) * avr_limiter_uMin_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_limiter_uMin_Ac6a - avr_gain1_y_Ac6a) - vf.add_const(value=1e-06)))) * avr_gain1_y_Ac6a))))),
            (avr_transferFunction1_y_Ac6a - (((avr_transferFunction1_bb_2_Ac6a - (avr_transferFunction1_d_Ac6a * avr_transferFunction1_a_2_Ac6a)) * avr_transferFunction1_x_1_Ac6a) + (avr_transferFunction1_d_Ac6a * avr_limiter_y_Ac6a))),
            (avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_Ac6a - ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain_Ac6a * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain_Ac6a) * ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_k_Ac6a / avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_T_Ac6a) * (avr_acRotatingExciter_const1_k_Ac6a - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a))))),
            (avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_Ac6a - ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain_Ac6a * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain_Ac6a) * ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_k_Ac6a / avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_T_Ac6a) * (avr_acRotatingExciter_firstOrder_y_Ac6a - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a))))),
            (avr_transferFunction_x_1_Ac6a - (avr_transferFunction_x_scaled_1_Ac6a / avr_transferFunction_a_end_Ac6a)),
            (avr_sum1_u_1_Ac6a - (((avr_UsRefPu_Ac6a - avr_firstOrder_y_Ac6a) + avr_UPssPu_Ac6a) + avr_UUelPu_Ac6a)),
            (avr_sum1_y_Ac6a - (avr_sum1_k_1_Ac6a * avr_sum1_u_1_Ac6a)),
            (avr_gain_y_Ac6a - (avr_gain_k_Ac6a * avr_sum1_y_Ac6a)),
            (avr_transferFunction_y_Ac6a - (((avr_transferFunction_bb_2_Ac6a - (avr_transferFunction_d_Ac6a * avr_transferFunction_a_2_Ac6a)) * avr_transferFunction_x_1_Ac6a) + (avr_transferFunction_d_Ac6a * avr_gain_y_Ac6a))),
            (avr_limitedLeadLag_feedback_y_Ac6a - (avr_transferFunction_y_Ac6a - avr_limitedLeadLag_firstOrder_y_Ac6a)),
            (avr_limitedLeadLag_gain_y_Ac6a - (avr_limitedLeadLag_gain_k_Ac6a * avr_limitedLeadLag_feedback_y_Ac6a)),
            (avr_limitedLeadLag_y_Ac6a - ((sym.heaviside(((avr_limitedLeadLag_gain_y_Ac6a - avr_limitedLeadLag_limiter_uMax_Ac6a) - vf.add_const(value=1e-06))) * avr_limitedLeadLag_limiter_uMax_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_limitedLeadLag_gain_y_Ac6a - avr_limitedLeadLag_limiter_uMax_Ac6a) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((avr_limitedLeadLag_limiter_uMin_Ac6a - avr_limitedLeadLag_gain_y_Ac6a) - vf.add_const(value=1e-06))) * avr_limitedLeadLag_limiter_uMin_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_limitedLeadLag_limiter_uMin_Ac6a - avr_limitedLeadLag_gain_y_Ac6a) - vf.add_const(value=1e-06)))) * avr_limitedLeadLag_gain_y_Ac6a))))),
            (avr_feedback_y_Ac6a - (avr_limitedLeadLag_y_Ac6a - avr_transferFunction1_y_Ac6a)),
            (avr_variableLimiter_y_Ac6a - ((sym.heaviside(((avr_feedback_y_Ac6a - avr_gain2_k_Ac6a) - vf.add_const(value=1e-06))) * avr_gain2_k_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_feedback_y_Ac6a - avr_gain2_k_Ac6a) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((avr_gain3_k_Ac6a - avr_feedback_y_Ac6a) - vf.add_const(value=1e-06))) * avr_gain3_k_Ac6a) + ((vf.add_const(value=1.0) - sym.heaviside(((avr_gain3_k_Ac6a - avr_feedback_y_Ac6a) - vf.add_const(value=1e-06)))) * avr_feedback_y_Ac6a))))),
            (avr_acRotatingExciter_feedback_y_Ac6a - (avr_variableLimiter_y_Ac6a - avr_acRotatingExciter_VfePu_Ac6a)),
            ((avr_acRotatingExciter_integratorVariableLimits_startFreezingMax_Ac6a - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w_Ac6a - avr_acRotatingExciter_firstOrder_y_Ac6a) - vf.add_const(value=1e-06)))) - sym.heaviside((((avr_acRotatingExciter_integratorVariableLimits_K_Ac6a * avr_acRotatingExciter_feedback_y_Ac6a) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_Ac6a) - vf.add_const(value=1e-06)))),
            ((avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax_Ac6a - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w_Ac6a - (avr_acRotatingExciter_firstOrder_y_Ac6a - (avr_acRotatingExciter_integratorVariableLimits_Tol_Ac6a * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a - avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a))))) - vf.add_const(value=1e-06)))) - sym.heaviside((((avr_acRotatingExciter_integratorVariableLimits_K_Ac6a * avr_acRotatingExciter_feedback_y_Ac6a) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_Ac6a) - vf.add_const(value=1e-06)))),
            (avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_startFreezingMax_Ac6a) * (vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax_Ac6a)))),
            ((avr_acRotatingExciter_integratorVariableLimits_startFreezingMin_Ac6a - sym.heaviside(((avr_acRotatingExciter_const1_k_Ac6a - avr_acRotatingExciter_integratorVariableLimits_w_Ac6a) - vf.add_const(value=1e-06)))) - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_Ac6a - (avr_acRotatingExciter_integratorVariableLimits_K_Ac6a * avr_acRotatingExciter_feedback_y_Ac6a)) - vf.add_const(value=1e-06)))),
            ((avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin_Ac6a - sym.heaviside((((avr_acRotatingExciter_const1_k_Ac6a + (avr_acRotatingExciter_integratorVariableLimits_Tol_Ac6a * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a - avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a)))) - avr_acRotatingExciter_integratorVariableLimits_w_Ac6a) - vf.add_const(value=1e-06)))) - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_Ac6a - (avr_acRotatingExciter_integratorVariableLimits_K_Ac6a * avr_acRotatingExciter_feedback_y_Ac6a)) - vf.add_const(value=1e-06)))),
            (avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a - (vf.add_const(value=1.0) - ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_startFreezingMin_Ac6a) * (vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin_Ac6a)))),
        ],
        algebraic_vars=[
            avr_transferFunction1_x_1_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_y_Ac6a,
            avr_acRotatingExciter_division_y_Ac6a,
            avr_acRotatingExciter_rectifierRegulationCharacteristic_y_Ac6a,
            avr_EfdPu_Ac6a,
            avr_acRotatingExciter_product1_y_Ac6a,
            avr_acRotatingExciter_division1_y_Ac6a,
            avr_acRotatingExciter_VfePu_Ac6a,
            avr_add_y_Ac6a,
            avr_gain1_y_Ac6a,
            avr_limiter_y_Ac6a,
            avr_transferFunction1_y_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_Ac6a,
            avr_transferFunction_x_1_Ac6a,
            avr_sum1_u_1_Ac6a,
            avr_sum1_y_Ac6a,
            avr_gain_y_Ac6a,
            avr_transferFunction_y_Ac6a,
            avr_limitedLeadLag_feedback_y_Ac6a,
            avr_limitedLeadLag_gain_y_Ac6a,
            avr_limitedLeadLag_y_Ac6a,
            avr_feedback_y_Ac6a,
            avr_variableLimiter_y_Ac6a,
            avr_acRotatingExciter_feedback_y_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_startFreezingMax_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_startFreezingMin_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a,
            avr_acRotatingExciter_add_y_Ac6a,
            avr_acRotatingExciter_add1_y_Ac6a,
            avr_IrPu_Ac6a,
            avr_UPssPu_Ac6a,
            avr_UUelPu_Ac6a,
            avr_UsPu_Ac6a,
            avr_UsRefPu_Ac6a,
            avr_limitedLeadLag_limiter_simplifiedExpr_Ac6a,
            avr_variableLimiter_simplifiedExpr_Ac6a,
            avr_limiter_simplifiedExpr_Ac6a,
            START_avr_firstOrder_y_Ac6a,
            START_avr_transferFunction_x_scaled_1_Ac6a,
            START_avr_limitedLeadLag_firstOrder_y_Ac6a,
            START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a,
            START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a,
            PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a,
            START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a,
            PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a,
            START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a,
            START_avr_acRotatingExciter_integratorVariableLimits_w_Ac6a,
            START_avr_acRotatingExciter_firstOrder_y_Ac6a,
            START_avr_transferFunction1_x_scaled_1_Ac6a,
            avr_acRotatingExciter_power_y_Ac6a,
        ],
        init_eqs={
            avr_acRotatingExciter_firstOrder_y_Ac6a: START_avr_acRotatingExciter_firstOrder_y_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a: START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a: START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_w_Ac6a: START_avr_acRotatingExciter_integratorVariableLimits_w_Ac6a,
            avr_firstOrder_y_Ac6a: (avr_firstOrder_k_Ac6a * avr_UsPu_Ac6a),
            avr_limitedLeadLag_firstOrder_y_Ac6a: START_avr_limitedLeadLag_firstOrder_y_Ac6a,
            avr_transferFunction_x_scaled_1_Ac6a: START_avr_transferFunction_x_scaled_1_Ac6a,
            avr_transferFunction1_x_scaled_1_Ac6a: START_avr_transferFunction1_x_scaled_1_Ac6a,
            avr_EfdPu_Ac6a: avr_acRotatingExciter_Efd0Pu_Ac6a,
            avr_IrPu_Ac6a: vf.add_const(value=1.0),
            avr_UPssPu_Ac6a: vf.add_const(value=0.0),
            avr_UUelPu_Ac6a: vf.add_const(value=0.0),
            avr_UsPu_Ac6a: vf.add_const(value=1.0),
            avr_UsRefPu_Ac6a: vf.add_const(value=1.0),
            avr_acRotatingExciter_VfePu_Ac6a: avr_acRotatingExciter_Efe0Pu_Ac6a,
            avr_acRotatingExciter_division_y_Ac6a: vf.add_const(value=0.0),
            avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_Ac6a: vf.add_const(value=0.0),
            avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_Ac6a: vf.add_const(value=0.0),
            avr_acRotatingExciter_integratorVariableLimits_y_Ac6a: avr_acRotatingExciter_integratorVariableLimits_Y0_Ac6a,
            avr_acRotatingExciter_rectifierRegulationCharacteristic_y_Ac6a: vf.add_const(value=1.0),
            avr_limitedLeadLag_y_Ac6a: avr_limitedLeadLag_Y0_Ac6a,
            avr_transferFunction_x_1_Ac6a: avr_transferFunction_x_start_1_Ac6a,
            avr_transferFunction_y_Ac6a: avr_transferFunction_y_start_Ac6a,
            avr_transferFunction1_x_1_Ac6a: avr_transferFunction1_x_start_1_Ac6a,
            avr_transferFunction1_y_Ac6a: avr_transferFunction1_y_start_Ac6a,
            avr_variableLimiter_y_Ac6a: avr_acRotatingExciter_Efe0Pu_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a: avr_acRotatingExciter_integratorVariableLimits_FrozenMax0_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a: avr_acRotatingExciter_integratorVariableLimits_FrozenMin0_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax_Ac6a: (sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w_Ac6a - (avr_acRotatingExciter_firstOrder_y_Ac6a - (avr_acRotatingExciter_integratorVariableLimits_Tol_Ac6a * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a - avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a))))) - vf.add_const(value=1e-06))) + sym.heaviside((((avr_acRotatingExciter_integratorVariableLimits_K_Ac6a * avr_acRotatingExciter_feedback_y_Ac6a) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_Ac6a) - vf.add_const(value=1e-06)))),
            avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin_Ac6a: (sym.heaviside((((avr_acRotatingExciter_const1_k_Ac6a + (avr_acRotatingExciter_integratorVariableLimits_Tol_Ac6a * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0_Ac6a - avr_acRotatingExciter_integratorVariableLimits_LimitMin0_Ac6a)))) - avr_acRotatingExciter_integratorVariableLimits_w_Ac6a) - vf.add_const(value=1e-06))) + sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_Ac6a - (avr_acRotatingExciter_integratorVariableLimits_K_Ac6a * avr_acRotatingExciter_feedback_y_Ac6a)) - vf.add_const(value=1e-06)))),
            avr_acRotatingExciter_integratorVariableLimits_startFreezingMax_Ac6a: avr_acRotatingExciter_integratorVariableLimits_FrozenMax0_Ac6a,
            avr_acRotatingExciter_integratorVariableLimits_startFreezingMin_Ac6a: avr_acRotatingExciter_integratorVariableLimits_FrozenMin0_Ac6a,
            avr_limitedLeadLag_limiter_simplifiedExpr_Ac6a: vf.add_const(value=0.0),
            avr_variableLimiter_simplifiedExpr_Ac6a: vf.add_const(value=0.0),
            avr_limiter_simplifiedExpr_Ac6a: vf.add_const(value=0.0),
            PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a: START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a,
            PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a: START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a,
            avr_acRotatingExciter_add1_y_Ac6a: ((avr_acRotatingExciter_add1_k1_Ac6a * avr_acRotatingExciter_const_k_Ac6a) + (avr_acRotatingExciter_add1_k2_Ac6a * avr_acRotatingExciter_gain1_k_Ac6a)),
            avr_acRotatingExciter_add_y_Ac6a: (avr_acRotatingExciter_add_k1_Ac6a + (avr_acRotatingExciter_add_k2_Ac6a * avr_acRotatingExciter_const2_k_Ac6a)),
            avr_acRotatingExciter_power_y_Ac6a: vf.add_const(value=1.0),
            avr_sum1_u_1_Ac6a: (((avr_UsRefPu_Ac6a - avr_firstOrder_y_Ac6a) + avr_UPssPu_Ac6a) + avr_UUelPu_Ac6a),
            avr_sum1_y_Ac6a: (avr_sum1_k_1_Ac6a * avr_sum1_u_1_Ac6a),
        },
        diff_init_eqs={
            d_avr_acRotatingExciter_integratorVariableLimits_w_Ac6a: (((avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a * (avr_acRotatingExciter_integratorVariableLimits_w_Ac6a - avr_acRotatingExciter_firstOrder_y_Ac6a)) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a) * ((avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a * (avr_acRotatingExciter_integratorVariableLimits_w_Ac6a - avr_acRotatingExciter_const1_k_Ac6a)) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a) * (-(avr_acRotatingExciter_integratorVariableLimits_K_Ac6a) * avr_acRotatingExciter_feedback_y_Ac6a))))) + ((avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMax_Ac6a) * ((avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMin_Ac6a) * vf.add_const(value=1.0)))))),
        },
        event_dict=event_dict,
        in_vars=inputs,
        out_vars=[
        ],
        external_mapping=external_mapping,
        api_obj_mapping=api_obj_mapping,
        diff_vars=[
            d_avr_acRotatingExciter_firstOrder_y_Ac6a,
            d_avr_transferFunction1_x_scaled_1_Ac6a,
            d_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_Ac6a,
            d_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_Ac6a,
            d_avr_transferFunction_x_scaled_1_Ac6a,
            d_avr_acRotatingExciter_integratorVariableLimits_w_Ac6a,
            d_avr_limitedLeadLag_firstOrder_y_Ac6a,
            d_avr_firstOrder_y_Ac6a,
        ],
        name=template_name,
    )
    templ.comment = 'Generator AVR/exciter IEEE AC6A'
    return templ
