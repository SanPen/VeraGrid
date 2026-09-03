# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Pss2c'.

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

def build_pss2c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
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
        template_name: str = 'Pss2c'
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
    pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4,5]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4,4]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4,3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4,2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3,5]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3,4]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3,3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3,2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2,5]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2,4]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2,3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2,2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1,5]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1,4]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1,3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1,2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4,1]_' + template_name)
    pss_transferFunction_x_scaled_1_Pss2c: Var = vf.add_var(name='pss.transferFunction.x_scaled[1]_' + template_name)
    pss_transferFunction1_x_scaled_1_Pss2c: Var = vf.add_var(name='pss.transferFunction1.x_scaled[1]_' + template_name)
    pss_transferFunction2_x_scaled_1_Pss2c: Var = vf.add_var(name='pss.transferFunction2.x_scaled[1]_' + template_name)
    pss_transferFunction3_x_scaled_1_Pss2c: Var = vf.add_var(name='pss.transferFunction3.x_scaled[1]_' + template_name)
    pss_washout3_derivative_x_Pss2c: Var = vf.add_var(name='pss.washout3.derivative.x_' + template_name)
    pss_firstOrder1_y_Pss2c: Var = vf.add_var(name='pss.firstOrder1.y_' + template_name)
    pss_washout2_derivative_x_Pss2c: Var = vf.add_var(name='pss.washout2.derivative.x_' + template_name)
    pss_washout1_derivative_x_Pss2c: Var = vf.add_var(name='pss.washout1.derivative.x_' + template_name)
    pss_firstOrder_y_Pss2c: Var = vf.add_var(name='pss.firstOrder.y_' + template_name)
    pss_washout_derivative_x_Pss2c: Var = vf.add_var(name='pss.washout.derivative.x_' + template_name)

    # Algebraic variables
    pss_hysteresis_y_Pss2c: Var = vf.add_var(name='pss.hysteresis.y_' + template_name)
    pss_transferFunction3_x_1_Pss2c: Var = vf.add_var(name='pss.transferFunction3.x[1]_' + template_name)
    pss_transferFunction2_x_1_Pss2c: Var = vf.add_var(name='pss.transferFunction2.x[1]_' + template_name)
    pss_transferFunction1_x_1_Pss2c: Var = vf.add_var(name='pss.transferFunction1.x[1]_' + template_name)
    pss_transferFunction_x_1_Pss2c: Var = vf.add_var(name='pss.transferFunction.x[1]_' + template_name)
    pss_add_y_Pss2c: Var = vf.add_var(name='pss.add.y_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1]_' + template_name)
    pss_rampTrackingFilter_z_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.z[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4]_' + template_name)
    pss_feedback_y_Pss2c: Var = vf.add_var(name='pss.feedback.y_' + template_name)
    pss_gain1_y_Pss2c: Var = vf.add_var(name='pss.gain1.y_' + template_name)
    pss_transferFunction_y_Pss2c: Var = vf.add_var(name='pss.transferFunction.y_' + template_name)
    pss_transferFunction1_y_Pss2c: Var = vf.add_var(name='pss.transferFunction1.y_' + template_name)
    pss_transferFunction2_y_Pss2c: Var = vf.add_var(name='pss.transferFunction2.y_' + template_name)
    pss_transferFunction3_y_Pss2c: Var = vf.add_var(name='pss.transferFunction3.y_' + template_name)
    pss_limiter2_y_Pss2c: Var = vf.add_var(name='pss.limiter2.y_' + template_name)
    pss_VPssPu_Pss2c: Var = vf.add_var(name='pss.VPssPu_' + template_name)
    pss_washout2_y_Pss2c: Var = vf.add_var(name='pss.washout2.y_' + template_name)
    pss_washout3_y_Pss2c: Var = vf.add_var(name='pss.washout3.y_' + template_name)
    pss_washout_y_Pss2c: Var = vf.add_var(name='pss.washout.y_' + template_name)
    pss_washout1_y_Pss2c: Var = vf.add_var(name='pss.washout1.y_' + template_name)
    pss_gain_y_Pss2c: Var = vf.add_var(name='pss.gain.y_' + template_name)
    pss_limiter1_y_Pss2c: Var = vf.add_var(name='pss.limiter1.y_' + template_name)
    pss_limiter_y_Pss2c: Var = vf.add_var(name='pss.limiter.y_' + template_name)
    pss_PGenPu_Pss2c: Var = vf.add_var(name='pss.PGenPu_' + template_name)
    pss_omegaPu_Pss2c: Var = vf.add_var(name='pss.omegaPu_' + template_name)
    pss_omegaRefPu_Pss2c: Var = vf.add_var(name='pss.omegaRefPu_' + template_name)
    pss_limiter_simplifiedExpr_Pss2c: Var = vf.add_var(name='pss.limiter.simplifiedExpr_' + template_name)
    pss_limiter1_simplifiedExpr_Pss2c: Var = vf.add_var(name='pss.limiter1.simplifiedExpr_' + template_name)
    pss_limiter2_simplifiedExpr_Pss2c: Var = vf.add_var(name='pss.limiter2.simplifiedExpr_' + template_name)
    START_pss_washout_derivative_x_Pss2c: Var = vf.add_var(name='$START.pss.washout.derivative.x_' + template_name)
    START_pss_washout1_derivative_x_Pss2c: Var = vf.add_var(name='$START.pss.washout1.derivative.x_' + template_name)
    START_pss_washout2_derivative_x_Pss2c: Var = vf.add_var(name='$START.pss.washout2.derivative.x_' + template_name)
    START_pss_washout3_derivative_x_Pss2c: Var = vf.add_var(name='$START.pss.washout3.derivative.x_' + template_name)
    START_pss_firstOrder_y_Pss2c: Var = vf.add_var(name='$START.pss.firstOrder.y_' + template_name)
    START_pss_firstOrder1_y_Pss2c: Var = vf.add_var(name='$START.pss.firstOrder1.y_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,1]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,2]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,3]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,4]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,5]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,1]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,2]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,3]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,4]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,5]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,1]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,2]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,3]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,4]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,5]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,1]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,2]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,3]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,4]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c: Var = vf.add_var(name='$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,5]_' + template_name)
    START_pss_transferFunction_x_scaled_1_Pss2c: Var = vf.add_var(name='$START.pss.transferFunction.x_scaled[1]_' + template_name)
    START_pss_transferFunction1_x_scaled_1_Pss2c: Var = vf.add_var(name='$START.pss.transferFunction1.x_scaled[1]_' + template_name)
    START_pss_transferFunction2_x_scaled_1_Pss2c: Var = vf.add_var(name='$START.pss.transferFunction2.x_scaled[1]_' + template_name)
    START_pss_transferFunction3_x_scaled_1_Pss2c: Var = vf.add_var(name='$START.pss.transferFunction3.x_scaled[1]_' + template_name)
    pss_add1_y_Pss2c: Var = vf.add_var(name='pss.add1.y_' + template_name)
    PRE_pss_hysteresis_y_Pss2c: Var = vf.add_var(name='$PRE.pss.hysteresis.y_' + template_name)
    pss_rampTrackingFilter_z_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.z[2]_' + template_name)
    pss_rampTrackingFilter_z_3_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.z[3]_' + template_name)
    pss_rampTrackingFilter_z_4_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.z[4]_' + template_name)

    # Differential variables
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[4,5]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[4,4]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[4,3]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[4,2]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[3,5]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[3,4]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[3,3]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[3,2]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[2,5]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[2,4]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[2,3]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[2,2]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[1,5]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[1,4]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[1,3]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[1,2]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[1,1]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[2,1]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[3,1]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c: Var = vf.add_diff_var(name='d_pss.rampTrackingFilter.leadMOrderLagCascade[4,1]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c)
    d_pss_transferFunction_x_scaled_1_Pss2c: Var = vf.add_diff_var(name='d_pss.transferFunction.x_scaled[1]_' + template_name, base_var=pss_transferFunction_x_scaled_1_Pss2c)
    d_pss_transferFunction1_x_scaled_1_Pss2c: Var = vf.add_diff_var(name='d_pss.transferFunction1.x_scaled[1]_' + template_name, base_var=pss_transferFunction1_x_scaled_1_Pss2c)
    d_pss_transferFunction2_x_scaled_1_Pss2c: Var = vf.add_diff_var(name='d_pss.transferFunction2.x_scaled[1]_' + template_name, base_var=pss_transferFunction2_x_scaled_1_Pss2c)
    d_pss_transferFunction3_x_scaled_1_Pss2c: Var = vf.add_diff_var(name='d_pss.transferFunction3.x_scaled[1]_' + template_name, base_var=pss_transferFunction3_x_scaled_1_Pss2c)
    d_pss_washout3_derivative_x_Pss2c: Var = vf.add_diff_var(name='d_pss.washout3.derivative.x_' + template_name, base_var=pss_washout3_derivative_x_Pss2c)
    d_pss_firstOrder1_y_Pss2c: Var = vf.add_diff_var(name='d_pss.firstOrder1.y_' + template_name, base_var=pss_firstOrder1_y_Pss2c)
    d_pss_washout2_derivative_x_Pss2c: Var = vf.add_diff_var(name='d_pss.washout2.derivative.x_' + template_name, base_var=pss_washout2_derivative_x_Pss2c)
    d_pss_washout1_derivative_x_Pss2c: Var = vf.add_diff_var(name='d_pss.washout1.derivative.x_' + template_name, base_var=pss_washout1_derivative_x_Pss2c)
    d_pss_firstOrder_y_Pss2c: Var = vf.add_diff_var(name='d_pss.firstOrder.y_' + template_name, base_var=pss_firstOrder_y_Pss2c)
    d_pss_washout_derivative_x_Pss2c: Var = vf.add_diff_var(name='d_pss.washout.derivative.x_' + template_name, base_var=pss_washout_derivative_x_Pss2c)

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________

    # Runtime parameters and event variables
    pss_transferFunction_a_end_Pss2c: Var = vf.add_var(name='pss.transferFunction.a_end_' + template_name)
    pss_transferFunction_a_2_Pss2c: Var = vf.add_var(name='pss.transferFunction.a[2]_' + template_name)
    pss_transferFunction_a_1_Pss2c: Var = vf.add_var(name='pss.transferFunction.a[1]_' + template_name)
    pss_transferFunction1_a_1_Pss2c: Var = vf.add_var(name='pss.transferFunction1.a[1]_' + template_name)
    pss_transferFunction1_a_2_Pss2c: Var = vf.add_var(name='pss.transferFunction1.a[2]_' + template_name)
    pss_transferFunction1_a_end_Pss2c: Var = vf.add_var(name='pss.transferFunction1.a_end_' + template_name)
    pss_transferFunction2_a_end_Pss2c: Var = vf.add_var(name='pss.transferFunction2.a_end_' + template_name)
    pss_transferFunction2_a_1_Pss2c: Var = vf.add_var(name='pss.transferFunction2.a[1]_' + template_name)
    pss_transferFunction2_a_2_Pss2c: Var = vf.add_var(name='pss.transferFunction2.a[2]_' + template_name)
    pss_transferFunction3_a_end_Pss2c: Var = vf.add_var(name='pss.transferFunction3.a_end_' + template_name)
    pss_transferFunction3_a_2_Pss2c: Var = vf.add_var(name='pss.transferFunction3.a[2]_' + template_name)
    pss_transferFunction3_a_1_Pss2c: Var = vf.add_var(name='pss.transferFunction3.a[1]_' + template_name)
    pss_washout3_derivative_T_Pss2c: Var = vf.add_var(name='pss.washout3.derivative.T_' + template_name)
    pss_washout3_derivative_zeroGain_Pss2c: Var = vf.add_var(name='pss.washout3.derivative.zeroGain_' + template_name)
    pss_firstOrder1_T_Pss2c: Var = vf.add_var(name='pss.firstOrder1.T_' + template_name)
    pss_firstOrder1_k_Pss2c: Var = vf.add_var(name='pss.firstOrder1.k_' + template_name)
    pss_washout2_derivative_T_Pss2c: Var = vf.add_var(name='pss.washout2.derivative.T_' + template_name)
    pss_washout2_derivative_zeroGain_Pss2c: Var = vf.add_var(name='pss.washout2.derivative.zeroGain_' + template_name)
    pss_washout1_derivative_zeroGain_Pss2c: Var = vf.add_var(name='pss.washout1.derivative.zeroGain_' + template_name)
    pss_washout1_derivative_T_Pss2c: Var = vf.add_var(name='pss.washout1.derivative.T_' + template_name)
    pss_firstOrder_T_Pss2c: Var = vf.add_var(name='pss.firstOrder.T_' + template_name)
    pss_firstOrder_k_Pss2c: Var = vf.add_var(name='pss.firstOrder.k_' + template_name)
    pss_washout_derivative_zeroGain_Pss2c: Var = vf.add_var(name='pss.washout.derivative.zeroGain_' + template_name)
    pss_washout_derivative_T_Pss2c: Var = vf.add_var(name='pss.washout.derivative.T_' + template_name)
    pss_hysteresis_uLow_Pss2c: Var = vf.add_var(name='pss.hysteresis.uLow_' + template_name)
    pss_hysteresis_uHigh_Pss2c: Var = vf.add_var(name='pss.hysteresis.uHigh_' + template_name)
    pss_add_k2_Pss2c: Var = vf.add_var(name='pss.add.k2_' + template_name)
    pss_add_k1_Pss2c: Var = vf.add_var(name='pss.add.k1_' + template_name)
    pss_rampTrackingFilter_gain_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.gain.k_' + template_name)
    pss_gain1_k_Pss2c: Var = vf.add_var(name='pss.gain1.k_' + template_name)
    pss_transferFunction_bb_2_Pss2c: Var = vf.add_var(name='pss.transferFunction.bb[2]_' + template_name)
    pss_transferFunction_d_Pss2c: Var = vf.add_var(name='pss.transferFunction.d_' + template_name)
    pss_transferFunction1_bb_2_Pss2c: Var = vf.add_var(name='pss.transferFunction1.bb[2]_' + template_name)
    pss_transferFunction1_d_Pss2c: Var = vf.add_var(name='pss.transferFunction1.d_' + template_name)
    pss_transferFunction2_bb_2_Pss2c: Var = vf.add_var(name='pss.transferFunction2.bb[2]_' + template_name)
    pss_transferFunction2_d_Pss2c: Var = vf.add_var(name='pss.transferFunction2.d_' + template_name)
    pss_transferFunction3_bb_2_Pss2c: Var = vf.add_var(name='pss.transferFunction3.bb[2]_' + template_name)
    pss_transferFunction3_d_Pss2c: Var = vf.add_var(name='pss.transferFunction3.d_' + template_name)
    pss_limiter2_uMin_Pss2c: Var = vf.add_var(name='pss.limiter2.uMin_' + template_name)
    pss_limiter2_uMax_Pss2c: Var = vf.add_var(name='pss.limiter2.uMax_' + template_name)
    pss_const_k_Pss2c: Var = vf.add_var(name='pss.const.k_' + template_name)
    pss_washout2_derivative_k_Pss2c: Var = vf.add_var(name='pss.washout2.derivative.k_' + template_name)
    pss_washout3_derivative_k_Pss2c: Var = vf.add_var(name='pss.washout3.derivative.k_' + template_name)
    pss_washout_derivative_k_Pss2c: Var = vf.add_var(name='pss.washout.derivative.k_' + template_name)
    pss_washout1_derivative_k_Pss2c: Var = vf.add_var(name='pss.washout1.derivative.k_' + template_name)
    pss_add1_k2_Pss2c: Var = vf.add_var(name='pss.add1.k2_' + template_name)
    pss_add1_k1_Pss2c: Var = vf.add_var(name='pss.add1.k1_' + template_name)
    pss_limiter_uMin_Pss2c: Var = vf.add_var(name='pss.limiter.uMin_' + template_name)
    pss_limiter_uMax_Pss2c: Var = vf.add_var(name='pss.limiter.uMax_' + template_name)
    pss_gain_k_Pss2c: Var = vf.add_var(name='pss.gain.k_' + template_name)
    pss_limiter1_uMax_Pss2c: Var = vf.add_var(name='pss.limiter1.uMax_' + template_name)
    pss_limiter1_uMin_Pss2c: Var = vf.add_var(name='pss.limiter1.uMin_' + template_name)
    pss_rampTrackingFilter_Y0_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.Y0_' + template_name)
    pss_transferFunction_x_start_1_Pss2c: Var = vf.add_var(name='pss.transferFunction.x_start[1]_' + template_name)
    pss_transferFunction_y_start_Pss2c: Var = vf.add_var(name='pss.transferFunction.y_start_' + template_name)
    pss_transferFunction1_x_start_1_Pss2c: Var = vf.add_var(name='pss.transferFunction1.x_start[1]_' + template_name)
    pss_transferFunction1_y_start_Pss2c: Var = vf.add_var(name='pss.transferFunction1.y_start_' + template_name)
    pss_transferFunction2_x_start_1_Pss2c: Var = vf.add_var(name='pss.transferFunction2.x_start[1]_' + template_name)
    pss_transferFunction2_y_start_Pss2c: Var = vf.add_var(name='pss.transferFunction2.y_start_' + template_name)
    pss_transferFunction3_x_start_1_Pss2c: Var = vf.add_var(name='pss.transferFunction3.x_start[1]_' + template_name)
    pss_transferFunction3_y_start_Pss2c: Var = vf.add_var(name='pss.transferFunction3.y_start_' + template_name)
    pss_washout1_U0_Pss2c: Var = vf.add_var(name='pss.washout1.U0_' + template_name)
    pss_washout3_U0_Pss2c: Var = vf.add_var(name='pss.washout3.U0_' + template_name)
    pss_hysteresis_pre_y_start_Pss2c: Var = vf.add_var(name='pss.hysteresis.pre_y_start_' + template_name)
    pss_KOmega_Pss2c: Var = vf.add_var(name='pss.KOmega_' + template_name)
    pss_KOmegaRef_Pss2c: Var = vf.add_var(name='pss.KOmegaRef_' + template_name)
    pss_Ks1_Pss2c: Var = vf.add_var(name='pss.Ks1_' + template_name)
    pss_Ks2_Pss2c: Var = vf.add_var(name='pss.Ks2_' + template_name)
    pss_Ks3_Pss2c: Var = vf.add_var(name='pss.Ks3_' + template_name)
    pss_OmegaMaxPu_Pss2c: Var = vf.add_var(name='pss.OmegaMaxPu_' + template_name)
    pss_OmegaMinPu_Pss2c: Var = vf.add_var(name='pss.OmegaMinPu_' + template_name)
    pss_PGen0Pu_Pss2c: Var = vf.add_var(name='pss.PGen0Pu_' + template_name)
    pss_PGenMaxPu_Pss2c: Var = vf.add_var(name='pss.PGenMaxPu_' + template_name)
    pss_PGenMinPu_Pss2c: Var = vf.add_var(name='pss.PGenMinPu_' + template_name)
    pss_PPssOffPu_Pss2c: Var = vf.add_var(name='pss.PPssOffPu_' + template_name)
    pss_PPssOnPu_Pss2c: Var = vf.add_var(name='pss.PPssOnPu_' + template_name)
    pss_SNom_Pss2c: Var = vf.add_var(name='pss.SNom_' + template_name)
    pss_VPssMaxPu_Pss2c: Var = vf.add_var(name='pss.VPssMaxPu_' + template_name)
    pss_VPssMinPu_Pss2c: Var = vf.add_var(name='pss.VPssMinPu_' + template_name)
    pss_t6_Pss2c: Var = vf.add_var(name='pss.t6_' + template_name)
    pss_firstOrder_y_start_Pss2c: Var = vf.add_var(name='pss.firstOrder.y_start_' + template_name)
    pss_t7_Pss2c: Var = vf.add_var(name='pss.t7_' + template_name)
    pss_firstOrder1_y_start_Pss2c: Var = vf.add_var(name='pss.firstOrder1.y_start_' + template_name)
    pss_rampTrackingFilter_K_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.K_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_K_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].K_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_K_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].K_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_K_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].K_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_K_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].K_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].Y0_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].Y0_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].Y0_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].Y0_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[1].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_t2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].t2_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[2].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[3].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[4].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[5].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[1].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_t2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].t2_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[2].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[3].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[4].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[5].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[1].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_t2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].t2_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[2].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[3].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[4].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[5].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[1].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_t2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].t2_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[2].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[3].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[4].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_T_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[5].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[1].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[2].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[3].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[4].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[5].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[1].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[2].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[3].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[4].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[5].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[1].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[2].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[3].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[4].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[5].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[1].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[2].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[3].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[4].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_k_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[5].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[1].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[2].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[3].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[4].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[5].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[1].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[2].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[3].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[4].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[5].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[1].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[2].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[3].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[4].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[5].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[1].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[2].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[3].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[4].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[5].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.a[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.a[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.a[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.a[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.a[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.a[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.a[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.a[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_end_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.a_end_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_end_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.a_end_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_end_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.a_end_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_end_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.a_end_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.b[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.b[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.b[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.b[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.b[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.b[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.b[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.b[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_bb_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.bb[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_bb_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.bb[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_bb_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.bb[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_bb_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.bb[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_bb_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.bb[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_bb_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.bb[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_bb_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.bb[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_bb_2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.bb[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_d_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.d_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_d_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.d_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_d_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.d_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_d_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.d_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_x_start_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.x_start[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_x_start_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.x_start[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_x_start_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.x_start[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_x_start_1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.x_start[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_y_start_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_t1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].t1_' + template_name)
    pss_rampTrackingFilter_t1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.t1_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_t1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].t1_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_t1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].t1_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_t1_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].t1_' + template_name)
    pss_rampTrackingFilter_t2_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.t2_' + template_name)
    pss_t8_Pss2c: Var = vf.add_var(name='pss.t8_' + template_name)
    pss_t9_Pss2c: Var = vf.add_var(name='pss.t9_' + template_name)
    pss_t1_Pss2c: Var = vf.add_var(name='pss.t1_' + template_name)
    pss_t10_Pss2c: Var = vf.add_var(name='pss.t10_' + template_name)
    pss_t11_Pss2c: Var = vf.add_var(name='pss.t11_' + template_name)
    pss_t12_Pss2c: Var = vf.add_var(name='pss.t12_' + template_name)
    pss_t13_Pss2c: Var = vf.add_var(name='pss.t13_' + template_name)
    pss_t2_Pss2c: Var = vf.add_var(name='pss.t2_' + template_name)
    pss_t3_Pss2c: Var = vf.add_var(name='pss.t3_' + template_name)
    pss_t4_Pss2c: Var = vf.add_var(name='pss.t4_' + template_name)
    pss_tW1_Pss2c: Var = vf.add_var(name='pss.tW1_' + template_name)
    pss_tW2_Pss2c: Var = vf.add_var(name='pss.tW2_' + template_name)
    pss_tW3_Pss2c: Var = vf.add_var(name='pss.tW3_' + template_name)
    pss_tW4_Pss2c: Var = vf.add_var(name='pss.tW4_' + template_name)
    pss_transferFunction_b_1_Pss2c: Var = vf.add_var(name='pss.transferFunction.b[1]_' + template_name)
    pss_transferFunction_b_2_Pss2c: Var = vf.add_var(name='pss.transferFunction.b[2]_' + template_name)
    pss_transferFunction_bb_1_Pss2c: Var = vf.add_var(name='pss.transferFunction.bb[1]_' + template_name)
    pss_transferFunction1_b_1_Pss2c: Var = vf.add_var(name='pss.transferFunction1.b[1]_' + template_name)
    pss_transferFunction1_b_2_Pss2c: Var = vf.add_var(name='pss.transferFunction1.b[2]_' + template_name)
    pss_transferFunction1_bb_1_Pss2c: Var = vf.add_var(name='pss.transferFunction1.bb[1]_' + template_name)
    pss_transferFunction2_b_1_Pss2c: Var = vf.add_var(name='pss.transferFunction2.b[1]_' + template_name)
    pss_transferFunction2_b_2_Pss2c: Var = vf.add_var(name='pss.transferFunction2.b[2]_' + template_name)
    pss_transferFunction2_bb_1_Pss2c: Var = vf.add_var(name='pss.transferFunction2.bb[1]_' + template_name)
    pss_transferFunction3_b_1_Pss2c: Var = vf.add_var(name='pss.transferFunction3.b[1]_' + template_name)
    pss_transferFunction3_b_2_Pss2c: Var = vf.add_var(name='pss.transferFunction3.b[2]_' + template_name)
    pss_transferFunction3_bb_1_Pss2c: Var = vf.add_var(name='pss.transferFunction3.bb[1]_' + template_name)
    pss_washout_U0_Pss2c: Var = vf.add_var(name='pss.washout.U0_' + template_name)
    pss_washout_derivative_x_start_Pss2c: Var = vf.add_var(name='pss.washout.derivative.x_start_' + template_name)
    pss_washout_derivative_y_start_Pss2c: Var = vf.add_var(name='pss.washout.derivative.y_start_' + template_name)
    pss_washout_tW_Pss2c: Var = vf.add_var(name='pss.washout.tW_' + template_name)
    pss_washout1_derivative_x_start_Pss2c: Var = vf.add_var(name='pss.washout1.derivative.x_start_' + template_name)
    pss_washout1_derivative_y_start_Pss2c: Var = vf.add_var(name='pss.washout1.derivative.y_start_' + template_name)
    pss_washout1_tW_Pss2c: Var = vf.add_var(name='pss.washout1.tW_' + template_name)
    pss_washout2_U0_Pss2c: Var = vf.add_var(name='pss.washout2.U0_' + template_name)
    pss_washout2_derivative_x_start_Pss2c: Var = vf.add_var(name='pss.washout2.derivative.x_start_' + template_name)
    pss_washout2_derivative_y_start_Pss2c: Var = vf.add_var(name='pss.washout2.derivative.y_start_' + template_name)
    pss_washout2_tW_Pss2c: Var = vf.add_var(name='pss.washout2.tW_' + template_name)
    pss_washout3_derivative_x_start_Pss2c: Var = vf.add_var(name='pss.washout3.derivative.x_start_' + template_name)
    pss_washout3_derivative_y_start_Pss2c: Var = vf.add_var(name='pss.washout3.derivative.y_start_' + template_name)
    pss_washout3_tW_Pss2c: Var = vf.add_var(name='pss.washout3.tW_' + template_name)
    pss_M_Pss2c: Var = vf.add_var(name='pss.M_' + template_name)
    pss_N_Pss2c: Var = vf.add_var(name='pss.N_' + template_name)
    pss_firstOrder_initType_Pss2c: Var = vf.add_var(name='pss.firstOrder.initType_' + template_name)
    pss_firstOrder1_initType_Pss2c: Var = vf.add_var(name='pss.firstOrder1.initType_' + template_name)
    pss_limiter_homotopyType_Pss2c: Var = vf.add_var(name='pss.limiter.homotopyType_' + template_name)
    pss_limiter1_homotopyType_Pss2c: Var = vf.add_var(name='pss.limiter1.homotopyType_' + template_name)
    pss_limiter2_homotopyType_Pss2c: Var = vf.add_var(name='pss.limiter2.homotopyType_' + template_name)
    pss_rampTrackingFilter_M_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.M_' + template_name)
    pss_rampTrackingFilter_N_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.N_' + template_name)
    pss_rampTrackingFilter_NMax_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.NMax_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_M_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].M_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_M_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].M_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_M_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].M_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_M_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].M_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_MMax_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].MMax_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_MMax_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].MMax_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_MMax_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].MMax_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_MMax_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].MMax_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[1].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[2].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[3].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[4].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[5].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[1].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[2].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[3].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[4].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[5].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[1].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[2].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[3].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[4].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[5].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[1].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[2].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[3].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[4].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_initType_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[5].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_na_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.na_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_na_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.na_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_na_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.na_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_na_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.na_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_nb_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.nb_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_nb_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.nb_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_nb_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.nb_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_nb_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.nb_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_nx_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.nx_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_nx_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.nx_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_nx_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.nx_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_nx_Pss2c: Var = vf.add_var(name='pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.nx_' + template_name)
    pss_transferFunction_na_Pss2c: Var = vf.add_var(name='pss.transferFunction.na_' + template_name)
    pss_transferFunction_nb_Pss2c: Var = vf.add_var(name='pss.transferFunction.nb_' + template_name)
    pss_transferFunction_nx_Pss2c: Var = vf.add_var(name='pss.transferFunction.nx_' + template_name)
    pss_transferFunction1_na_Pss2c: Var = vf.add_var(name='pss.transferFunction1.na_' + template_name)
    pss_transferFunction1_nb_Pss2c: Var = vf.add_var(name='pss.transferFunction1.nb_' + template_name)
    pss_transferFunction1_nx_Pss2c: Var = vf.add_var(name='pss.transferFunction1.nx_' + template_name)
    pss_transferFunction2_na_Pss2c: Var = vf.add_var(name='pss.transferFunction2.na_' + template_name)
    pss_transferFunction2_nb_Pss2c: Var = vf.add_var(name='pss.transferFunction2.nb_' + template_name)
    pss_transferFunction2_nx_Pss2c: Var = vf.add_var(name='pss.transferFunction2.nx_' + template_name)
    pss_transferFunction3_na_Pss2c: Var = vf.add_var(name='pss.transferFunction3.na_' + template_name)
    pss_transferFunction3_nb_Pss2c: Var = vf.add_var(name='pss.transferFunction3.nb_' + template_name)
    pss_transferFunction3_nx_Pss2c: Var = vf.add_var(name='pss.transferFunction3.nx_' + template_name)
    pss_washout_derivative_initType_Pss2c: Var = vf.add_var(name='pss.washout.derivative.initType_' + template_name)
    pss_washout1_derivative_initType_Pss2c: Var = vf.add_var(name='pss.washout1.derivative.initType_' + template_name)
    pss_washout2_derivative_initType_Pss2c: Var = vf.add_var(name='pss.washout2.derivative.initType_' + template_name)
    pss_washout3_derivative_initType_Pss2c: Var = vf.add_var(name='pss.washout3.derivative.initType_' + template_name)
    pss_limiter_limitsAtInit_Pss2c: Var = vf.add_var(name='pss.limiter.limitsAtInit_' + template_name)
    pss_limiter_strict_Pss2c: Var = vf.add_var(name='pss.limiter.strict_' + template_name)
    pss_limiter1_limitsAtInit_Pss2c: Var = vf.add_var(name='pss.limiter1.limitsAtInit_' + template_name)
    pss_limiter1_strict_Pss2c: Var = vf.add_var(name='pss.limiter1.strict_' + template_name)
    pss_limiter2_limitsAtInit_Pss2c: Var = vf.add_var(name='pss.limiter2.limitsAtInit_' + template_name)
    pss_limiter2_strict_Pss2c: Var = vf.add_var(name='pss.limiter2.strict_' + template_name)

    event_dict: dict[Var, Expr | Const] = dict({
        pss_KOmega_Pss2c: vf.add_const(value=1.0),
        pss_KOmegaRef_Pss2c: vf.add_const(value=0.0),
        pss_Ks1_Pss2c: vf.add_const(value=10.0),
        pss_Ks2_Pss2c: vf.add_const(value=1.0),
        pss_Ks3_Pss2c: vf.add_const(value=1.0),
        pss_OmegaMaxPu_Pss2c: vf.add_const(value=1.1),
        pss_OmegaMinPu_Pss2c: vf.add_const(value=0.9),
        pss_PGen0Pu_Pss2c: vf.add_const(value=0.8),
        pss_PGenMaxPu_Pss2c: vf.add_const(value=1.0),
        pss_PGenMinPu_Pss2c: vf.add_const(value=0.0),
        pss_PPssOffPu_Pss2c: vf.add_const(value=0.05),
        pss_PPssOnPu_Pss2c: vf.add_const(value=0.1),
        pss_SNom_Pss2c: vf.add_const(value=100.0),
        pss_VPssMaxPu_Pss2c: vf.add_const(value=0.1),
        pss_VPssMinPu_Pss2c: vf.add_const(value=-0.1),
        pss_add_k1_Pss2c: pss_Ks3_Pss2c,
        pss_add_k2_Pss2c: vf.add_const(value=1.0),
        pss_add1_k1_Pss2c: pss_KOmega_Pss2c,
        pss_add1_k2_Pss2c: pss_KOmegaRef_Pss2c,
        pss_const_k_Pss2c: vf.add_const(value=0.0),
        pss_firstOrder_T_Pss2c: pss_t6_Pss2c,
        pss_firstOrder_k_Pss2c: vf.add_const(value=1.0),
        pss_firstOrder_y_start_Pss2c: vf.add_const(value=0.0),
        pss_firstOrder1_T_Pss2c: pss_t7_Pss2c,
        pss_firstOrder1_k_Pss2c: pss_Ks2_Pss2c,
        pss_firstOrder1_y_start_Pss2c: vf.add_const(value=0.0),
        pss_gain_k_Pss2c: (vf.add_const(value=100.0) / pss_SNom_Pss2c),
        pss_gain1_k_Pss2c: pss_Ks1_Pss2c,
        pss_hysteresis_uHigh_Pss2c: pss_PPssOnPu_Pss2c,
        pss_hysteresis_uLow_Pss2c: pss_PPssOffPu_Pss2c,
        pss_limiter_uMax_Pss2c: pss_OmegaMaxPu_Pss2c,
        pss_limiter_uMin_Pss2c: pss_OmegaMinPu_Pss2c,
        pss_limiter1_uMax_Pss2c: pss_PGenMaxPu_Pss2c,
        pss_limiter1_uMin_Pss2c: pss_PGenMinPu_Pss2c,
        pss_limiter2_uMax_Pss2c: pss_VPssMaxPu_Pss2c,
        pss_limiter2_uMin_Pss2c: pss_VPssMinPu_Pss2c,
        pss_rampTrackingFilter_K_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_Y0_Pss2c: vf.add_const(value=0.0),
        pss_rampTrackingFilter_gain_k_Pss2c: pss_rampTrackingFilter_K_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_K_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_K_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_K_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_K_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0_Pss2c: pss_rampTrackingFilter_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0_Pss2c: pss_rampTrackingFilter_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0_Pss2c: pss_rampTrackingFilter_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0_Pss2c: pss_rampTrackingFilter_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_T_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_k_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_y_start_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_1_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_2_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_1_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_2_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_1_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_2_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_1_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_2_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_end_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_end_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_end_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_end_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_1_Pss2c: vf.add_const(value=0.1),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_2_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_K_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_1_Pss2c: vf.add_const(value=0.1),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_2_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_K_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_1_Pss2c: vf.add_const(value=0.1),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_2_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_K_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_1_Pss2c: vf.add_const(value=0.1),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_2_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_K_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_bb_1_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_1_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_bb_2_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_bb_1_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_1_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_bb_2_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_bb_1_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_1_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_bb_2_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_bb_1_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_1_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_bb_2_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_d_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_d_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_d_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_d_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_x_start_1_Pss2c: vf.add_const(value=0.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_x_start_1_Pss2c: vf.add_const(value=0.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_x_start_1_Pss2c: vf.add_const(value=0.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_x_start_1_Pss2c: vf.add_const(value=0.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_y_start_Pss2c: vf.add_const(value=0.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_y_start_Pss2c: vf.add_const(value=0.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_y_start_Pss2c: vf.add_const(value=0.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_y_start_Pss2c: vf.add_const(value=0.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_t1_Pss2c: pss_rampTrackingFilter_t1_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_t1_Pss2c: pss_rampTrackingFilter_t1_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_t1_Pss2c: pss_rampTrackingFilter_t1_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_t1_Pss2c: pss_rampTrackingFilter_t1_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_1_t2_Pss2c: pss_rampTrackingFilter_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_2_t2_Pss2c: pss_rampTrackingFilter_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_3_t2_Pss2c: pss_rampTrackingFilter_t2_Pss2c,
        pss_rampTrackingFilter_leadMOrderLagCascade_4_t2_Pss2c: pss_rampTrackingFilter_t2_Pss2c,
        pss_rampTrackingFilter_t1_Pss2c: pss_t8_Pss2c,
        pss_rampTrackingFilter_t2_Pss2c: pss_t9_Pss2c,
        pss_t1_Pss2c: vf.add_const(value=0.1),
        pss_t10_Pss2c: vf.add_const(value=0.1),
        pss_t11_Pss2c: vf.add_const(value=0.05),
        pss_t12_Pss2c: vf.add_const(value=0.1),
        pss_t13_Pss2c: vf.add_const(value=0.05),
        pss_t2_Pss2c: vf.add_const(value=0.05),
        pss_t3_Pss2c: vf.add_const(value=0.1),
        pss_t4_Pss2c: vf.add_const(value=0.05),
        pss_t6_Pss2c: vf.add_const(value=0.02),
        pss_t7_Pss2c: vf.add_const(value=0.02),
        pss_t8_Pss2c: vf.add_const(value=0.1),
        pss_t9_Pss2c: vf.add_const(value=0.05),
        pss_tW1_Pss2c: vf.add_const(value=10.0),
        pss_tW2_Pss2c: vf.add_const(value=10.0),
        pss_tW3_Pss2c: vf.add_const(value=10.0),
        pss_tW4_Pss2c: vf.add_const(value=10.0),
        pss_transferFunction_a_1_Pss2c: pss_t2_Pss2c,
        pss_transferFunction_a_2_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction_a_end_Pss2c: ((sym.heaviside(((pss_transferFunction_a_2_Pss2c - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((pss_transferFunction_a_1_Pss2c ** vf.add_const(value=2.0)) + (pss_transferFunction_a_2_Pss2c ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06))) * pss_transferFunction_a_2_Pss2c) + ((vf.add_const(value=1.0) - sym.heaviside(((pss_transferFunction_a_2_Pss2c - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((pss_transferFunction_a_1_Pss2c ** vf.add_const(value=2.0)) + (pss_transferFunction_a_2_Pss2c ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06)))) * vf.add_const(value=1.0))),
        pss_transferFunction_b_1_Pss2c: pss_t1_Pss2c,
        pss_transferFunction_b_2_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction_bb_1_Pss2c: pss_transferFunction_b_1_Pss2c,
        pss_transferFunction_bb_2_Pss2c: pss_transferFunction_b_2_Pss2c,
        pss_transferFunction_d_Pss2c: (pss_transferFunction_bb_1_Pss2c / pss_transferFunction_a_1_Pss2c),
        pss_transferFunction_x_start_1_Pss2c: vf.add_const(value=0.0),
        pss_transferFunction_y_start_Pss2c: vf.add_const(value=0.0),
        pss_transferFunction1_a_1_Pss2c: pss_t4_Pss2c,
        pss_transferFunction1_a_2_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction1_a_end_Pss2c: ((sym.heaviside(((pss_transferFunction1_a_2_Pss2c - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((pss_transferFunction1_a_1_Pss2c ** vf.add_const(value=2.0)) + (pss_transferFunction1_a_2_Pss2c ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06))) * pss_transferFunction1_a_2_Pss2c) + ((vf.add_const(value=1.0) - sym.heaviside(((pss_transferFunction1_a_2_Pss2c - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((pss_transferFunction1_a_1_Pss2c ** vf.add_const(value=2.0)) + (pss_transferFunction1_a_2_Pss2c ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06)))) * vf.add_const(value=1.0))),
        pss_transferFunction1_b_1_Pss2c: pss_t3_Pss2c,
        pss_transferFunction1_b_2_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction1_bb_1_Pss2c: pss_transferFunction1_b_1_Pss2c,
        pss_transferFunction1_bb_2_Pss2c: pss_transferFunction1_b_2_Pss2c,
        pss_transferFunction1_d_Pss2c: (pss_transferFunction1_bb_1_Pss2c / pss_transferFunction1_a_1_Pss2c),
        pss_transferFunction1_x_start_1_Pss2c: vf.add_const(value=0.0),
        pss_transferFunction1_y_start_Pss2c: vf.add_const(value=0.0),
        pss_transferFunction2_a_1_Pss2c: pss_t11_Pss2c,
        pss_transferFunction2_a_2_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction2_a_end_Pss2c: ((sym.heaviside(((pss_transferFunction2_a_2_Pss2c - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((pss_transferFunction2_a_1_Pss2c ** vf.add_const(value=2.0)) + (pss_transferFunction2_a_2_Pss2c ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06))) * pss_transferFunction2_a_2_Pss2c) + ((vf.add_const(value=1.0) - sym.heaviside(((pss_transferFunction2_a_2_Pss2c - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((pss_transferFunction2_a_1_Pss2c ** vf.add_const(value=2.0)) + (pss_transferFunction2_a_2_Pss2c ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06)))) * vf.add_const(value=1.0))),
        pss_transferFunction2_b_1_Pss2c: pss_t10_Pss2c,
        pss_transferFunction2_b_2_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction2_bb_1_Pss2c: pss_transferFunction2_b_1_Pss2c,
        pss_transferFunction2_bb_2_Pss2c: pss_transferFunction2_b_2_Pss2c,
        pss_transferFunction2_d_Pss2c: (pss_transferFunction2_bb_1_Pss2c / pss_transferFunction2_a_1_Pss2c),
        pss_transferFunction2_x_start_1_Pss2c: vf.add_const(value=0.0),
        pss_transferFunction2_y_start_Pss2c: vf.add_const(value=0.0),
        pss_transferFunction3_a_1_Pss2c: pss_t13_Pss2c,
        pss_transferFunction3_a_2_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction3_a_end_Pss2c: ((sym.heaviside(((pss_transferFunction3_a_2_Pss2c - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((pss_transferFunction3_a_1_Pss2c ** vf.add_const(value=2.0)) + (pss_transferFunction3_a_2_Pss2c ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06))) * pss_transferFunction3_a_2_Pss2c) + ((vf.add_const(value=1.0) - sym.heaviside(((pss_transferFunction3_a_2_Pss2c - (vf.add_const(value=2.220446049250313e-14) * sym.sqrt(((pss_transferFunction3_a_1_Pss2c ** vf.add_const(value=2.0)) + (pss_transferFunction3_a_2_Pss2c ** vf.add_const(value=2.0)))))) - vf.add_const(value=1e-06)))) * vf.add_const(value=1.0))),
        pss_transferFunction3_b_1_Pss2c: pss_t12_Pss2c,
        pss_transferFunction3_b_2_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction3_bb_1_Pss2c: pss_transferFunction3_b_1_Pss2c,
        pss_transferFunction3_bb_2_Pss2c: pss_transferFunction3_b_2_Pss2c,
        pss_transferFunction3_d_Pss2c: (pss_transferFunction3_bb_1_Pss2c / pss_transferFunction3_a_1_Pss2c),
        pss_transferFunction3_x_start_1_Pss2c: vf.add_const(value=0.0),
        pss_transferFunction3_y_start_Pss2c: vf.add_const(value=0.0),
        pss_washout_U0_Pss2c: (pss_KOmega_Pss2c + pss_KOmegaRef_Pss2c),
        pss_washout_derivative_T_Pss2c: vf.add_const(value=10.0),
        pss_washout_derivative_k_Pss2c: vf.add_const(value=10.0),
        pss_washout_derivative_x_start_Pss2c: pss_washout_U0_Pss2c,
        pss_washout_derivative_y_start_Pss2c: vf.add_const(value=0.0),
        pss_washout_tW_Pss2c: vf.add_const(value=10.0),
        pss_washout1_U0_Pss2c: vf.add_const(value=0.0),
        pss_washout1_derivative_T_Pss2c: vf.add_const(value=10.0),
        pss_washout1_derivative_k_Pss2c: vf.add_const(value=10.0),
        pss_washout1_derivative_x_start_Pss2c: pss_washout1_U0_Pss2c,
        pss_washout1_derivative_y_start_Pss2c: vf.add_const(value=0.0),
        pss_washout1_tW_Pss2c: vf.add_const(value=10.0),
        pss_washout2_U0_Pss2c: (vf.add_const(value=100.0) * (pss_PGen0Pu_Pss2c / pss_SNom_Pss2c)),
        pss_washout2_derivative_T_Pss2c: vf.add_const(value=10.0),
        pss_washout2_derivative_k_Pss2c: vf.add_const(value=10.0),
        pss_washout2_derivative_x_start_Pss2c: pss_washout2_U0_Pss2c,
        pss_washout2_derivative_y_start_Pss2c: vf.add_const(value=0.0),
        pss_washout2_tW_Pss2c: vf.add_const(value=10.0),
        pss_washout3_U0_Pss2c: vf.add_const(value=0.0),
        pss_washout3_derivative_T_Pss2c: vf.add_const(value=10.0),
        pss_washout3_derivative_k_Pss2c: vf.add_const(value=10.0),
        pss_washout3_derivative_x_start_Pss2c: pss_washout3_U0_Pss2c,
        pss_washout3_derivative_y_start_Pss2c: vf.add_const(value=0.0),
        pss_washout3_tW_Pss2c: vf.add_const(value=10.0),
        pss_M_Pss2c: vf.add_const(value=1.0),
        pss_N_Pss2c: vf.add_const(value=1.0),
        pss_firstOrder_initType_Pss2c: vf.add_const(value=1.0),
        pss_firstOrder1_initType_Pss2c: vf.add_const(value=1.0),
        pss_limiter_homotopyType_Pss2c: vf.add_const(value=1.0),
        pss_limiter1_homotopyType_Pss2c: vf.add_const(value=1.0),
        pss_limiter2_homotopyType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_M_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_N_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_NMax_Pss2c: vf.add_const(value=4.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_M_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_M_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_M_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_M_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_MMax_Pss2c: vf.add_const(value=6.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_MMax_Pss2c: vf.add_const(value=6.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_MMax_Pss2c: vf.add_const(value=6.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_MMax_Pss2c: vf.add_const(value=6.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_initType_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_na_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_na_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_na_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_na_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_nb_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_nb_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_nb_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_nb_Pss2c: vf.add_const(value=2.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_nx_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_nx_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_nx_Pss2c: vf.add_const(value=1.0),
        pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_nx_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction_na_Pss2c: vf.add_const(value=2.0),
        pss_transferFunction_nb_Pss2c: vf.add_const(value=2.0),
        pss_transferFunction_nx_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction1_na_Pss2c: vf.add_const(value=2.0),
        pss_transferFunction1_nb_Pss2c: vf.add_const(value=2.0),
        pss_transferFunction1_nx_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction2_na_Pss2c: vf.add_const(value=2.0),
        pss_transferFunction2_nb_Pss2c: vf.add_const(value=2.0),
        pss_transferFunction2_nx_Pss2c: vf.add_const(value=1.0),
        pss_transferFunction3_na_Pss2c: vf.add_const(value=2.0),
        pss_transferFunction3_nb_Pss2c: vf.add_const(value=2.0),
        pss_transferFunction3_nx_Pss2c: vf.add_const(value=1.0),
        pss_washout_derivative_initType_Pss2c: vf.add_const(value=1.0),
        pss_washout1_derivative_initType_Pss2c: vf.add_const(value=1.0),
        pss_washout2_derivative_initType_Pss2c: vf.add_const(value=1.0),
        pss_washout3_derivative_initType_Pss2c: vf.add_const(value=1.0),
        pss_hysteresis_pre_y_start_Pss2c: vf.add_const(value=0.0),
        pss_limiter_limitsAtInit_Pss2c: vf.add_const(value=1.0),
        pss_limiter_strict_Pss2c: vf.add_const(value=0.0),
        pss_limiter1_limitsAtInit_Pss2c: vf.add_const(value=1.0),
        pss_limiter1_strict_Pss2c: vf.add_const(value=0.0),
        pss_limiter2_limitsAtInit_Pss2c: vf.add_const(value=1.0),
        pss_limiter2_strict_Pss2c: vf.add_const(value=0.0),
        pss_washout_derivative_zeroGain_Pss2c: sym.heaviside(((vf.add_const(value=2.220446049250313e-16) - sym.abs(pss_washout_derivative_k_Pss2c)) - vf.add_const(value=1e-06))),
        pss_washout1_derivative_zeroGain_Pss2c: sym.heaviside(((vf.add_const(value=2.220446049250313e-16) - sym.abs(pss_washout1_derivative_k_Pss2c)) - vf.add_const(value=1e-06))),
        pss_washout2_derivative_zeroGain_Pss2c: sym.heaviside(((vf.add_const(value=2.220446049250313e-16) - sym.abs(pss_washout2_derivative_k_Pss2c)) - vf.add_const(value=1e-06))),
        pss_washout3_derivative_zeroGain_Pss2c: sym.heaviside(((vf.add_const(value=2.220446049250313e-16) - sym.abs(pss_washout3_derivative_k_Pss2c)) - vf.add_const(value=1e-06))),
    })

    external_mapping: dict[object, Var] = dict()

    api_obj_mapping: dict[object, Var] = dict()

    templ.block = Block(
        state_eqs=[
            (((pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c) - pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c) / pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c) - (pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c)) / pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c * pss_rampTrackingFilter_z_1_Pss2c) - (pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c)) / pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c) - (pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c)) / pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c),
            (((pss_rampTrackingFilter_leadMOrderLagCascade_4_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c) - (pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c)) / pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c),
            (((pss_transferFunction_a_end_Pss2c * pss_gain1_y_Pss2c) - (pss_transferFunction_a_2_Pss2c * pss_transferFunction_x_scaled_1_Pss2c)) / pss_transferFunction_a_1_Pss2c),
            (((pss_transferFunction1_a_end_Pss2c * pss_transferFunction_y_Pss2c) - (pss_transferFunction1_a_2_Pss2c * pss_transferFunction1_x_scaled_1_Pss2c)) / pss_transferFunction1_a_1_Pss2c),
            (((pss_transferFunction2_a_end_Pss2c * pss_transferFunction1_y_Pss2c) - (pss_transferFunction2_a_2_Pss2c * pss_transferFunction2_x_scaled_1_Pss2c)) / pss_transferFunction2_a_1_Pss2c),
            (((pss_transferFunction3_a_end_Pss2c * pss_transferFunction2_y_Pss2c) - (pss_transferFunction3_a_2_Pss2c * pss_transferFunction3_x_scaled_1_Pss2c)) / pss_transferFunction3_a_1_Pss2c),
            ((pss_washout3_derivative_zeroGain_Pss2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - pss_washout3_derivative_zeroGain_Pss2c) * ((pss_washout2_y_Pss2c - pss_washout3_derivative_x_Pss2c) / pss_washout3_derivative_T_Pss2c))),
            (((pss_firstOrder1_k_Pss2c * pss_washout3_y_Pss2c) - pss_firstOrder1_y_Pss2c) / pss_firstOrder1_T_Pss2c),
            ((pss_washout2_derivative_zeroGain_Pss2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - pss_washout2_derivative_zeroGain_Pss2c) * ((pss_limiter1_y_Pss2c - pss_washout2_derivative_x_Pss2c) / pss_washout2_derivative_T_Pss2c))),
            ((pss_washout1_derivative_zeroGain_Pss2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - pss_washout1_derivative_zeroGain_Pss2c) * ((pss_washout_y_Pss2c - pss_washout1_derivative_x_Pss2c) / pss_washout1_derivative_T_Pss2c))),
            (((pss_firstOrder_k_Pss2c * pss_washout1_y_Pss2c) - pss_firstOrder_y_Pss2c) / pss_firstOrder_T_Pss2c),
            ((pss_washout_derivative_zeroGain_Pss2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - pss_washout_derivative_zeroGain_Pss2c) * ((pss_limiter_y_Pss2c - pss_washout_derivative_x_Pss2c) / pss_washout_derivative_T_Pss2c))),
        ],
        state_vars=[
            pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c,
            pss_transferFunction_x_scaled_1_Pss2c,
            pss_transferFunction1_x_scaled_1_Pss2c,
            pss_transferFunction2_x_scaled_1_Pss2c,
            pss_transferFunction3_x_scaled_1_Pss2c,
            pss_washout3_derivative_x_Pss2c,
            pss_firstOrder1_y_Pss2c,
            pss_washout2_derivative_x_Pss2c,
            pss_washout1_derivative_x_Pss2c,
            pss_firstOrder_y_Pss2c,
            pss_washout_derivative_x_Pss2c,
        ],
        algebraic_eqs=[
            ((pss_hysteresis_y_Pss2c - sym.heaviside(((pss_gain_y_Pss2c - pss_hysteresis_uHigh_Pss2c) - vf.add_const(value=1e-06)))) - sym.heaviside(((pss_gain_y_Pss2c - pss_hysteresis_uLow_Pss2c) + vf.add_const(value=1e-06)))),
            (pss_transferFunction3_x_1_Pss2c - (pss_transferFunction3_x_scaled_1_Pss2c / pss_transferFunction3_a_end_Pss2c)),
            (pss_transferFunction2_x_1_Pss2c - (pss_transferFunction2_x_scaled_1_Pss2c / pss_transferFunction2_a_end_Pss2c)),
            (pss_transferFunction1_x_1_Pss2c - (pss_transferFunction1_x_scaled_1_Pss2c / pss_transferFunction1_a_end_Pss2c)),
            (pss_transferFunction_x_1_Pss2c - (pss_transferFunction_x_scaled_1_Pss2c / pss_transferFunction_a_end_Pss2c)),
            (pss_add_y_Pss2c - ((pss_add_k1_Pss2c * pss_firstOrder1_y_Pss2c) + (pss_add_k2_Pss2c * pss_firstOrder_y_Pss2c))),
            (pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c - (pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c / pss_rampTrackingFilter_leadMOrderLagCascade_4_Pss2c)),
            (pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c - (pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c / pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c)),
            (pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c - (pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c / pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c)),
            (pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c - (pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c / pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c)),
            (pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c - (pss_rampTrackingFilter_gain_k_Pss2c * pss_add_y_Pss2c)),
            (pss_rampTrackingFilter_z_1_Pss2c - (((pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c - (pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c)) * pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c) + (pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c))),
            (pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c - (((pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c - (pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c)) * pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c) + (pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c * pss_rampTrackingFilter_z_1_Pss2c))),
            (pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c - (((pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c - (pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c)) * pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c) + (pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c))),
            (pss_rampTrackingFilter_leadMOrderLagCascade_4_Pss2c - (((pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c - (pss_rampTrackingFilter_leadMOrderLagCascade_4_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c)) * pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c) + (pss_rampTrackingFilter_leadMOrderLagCascade_4_Pss2c * pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c))),
            (pss_feedback_y_Pss2c - (pss_rampTrackingFilter_z_1_Pss2c - pss_firstOrder1_y_Pss2c)),
            (pss_gain1_y_Pss2c - (pss_gain1_k_Pss2c * pss_feedback_y_Pss2c)),
            (pss_transferFunction_y_Pss2c - (((pss_transferFunction_bb_2_Pss2c - (pss_transferFunction_d_Pss2c * pss_transferFunction_a_2_Pss2c)) * pss_transferFunction_x_1_Pss2c) + (pss_transferFunction_d_Pss2c * pss_gain1_y_Pss2c))),
            (pss_transferFunction1_y_Pss2c - (((pss_transferFunction1_bb_2_Pss2c - (pss_transferFunction1_d_Pss2c * pss_transferFunction1_a_2_Pss2c)) * pss_transferFunction1_x_1_Pss2c) + (pss_transferFunction1_d_Pss2c * pss_transferFunction_y_Pss2c))),
            (pss_transferFunction2_y_Pss2c - (((pss_transferFunction2_bb_2_Pss2c - (pss_transferFunction2_d_Pss2c * pss_transferFunction2_a_2_Pss2c)) * pss_transferFunction2_x_1_Pss2c) + (pss_transferFunction2_d_Pss2c * pss_transferFunction1_y_Pss2c))),
            (pss_transferFunction3_y_Pss2c - (((pss_transferFunction3_bb_2_Pss2c - (pss_transferFunction3_d_Pss2c * pss_transferFunction3_a_2_Pss2c)) * pss_transferFunction3_x_1_Pss2c) + (pss_transferFunction3_d_Pss2c * pss_transferFunction2_y_Pss2c))),
            (pss_limiter2_y_Pss2c - ((sym.heaviside(((pss_transferFunction3_y_Pss2c - pss_limiter2_uMax_Pss2c) - vf.add_const(value=1e-06))) * pss_limiter2_uMax_Pss2c) + ((vf.add_const(value=1.0) - sym.heaviside(((pss_transferFunction3_y_Pss2c - pss_limiter2_uMax_Pss2c) - vf.add_const(value=1e-06)))) * ((sym.heaviside(((pss_limiter2_uMin_Pss2c - pss_transferFunction3_y_Pss2c) - vf.add_const(value=1e-06))) * pss_limiter2_uMin_Pss2c) + ((vf.add_const(value=1.0) - sym.heaviside(((pss_limiter2_uMin_Pss2c - pss_transferFunction3_y_Pss2c) - vf.add_const(value=1e-06)))) * pss_transferFunction3_y_Pss2c))))),
            (pss_VPssPu_Pss2c - ((pss_hysteresis_y_Pss2c * pss_limiter2_y_Pss2c) + ((vf.add_const(value=1.0) - pss_hysteresis_y_Pss2c) * pss_const_k_Pss2c))),
            (pss_washout2_y_Pss2c - ((pss_washout2_derivative_zeroGain_Pss2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - pss_washout2_derivative_zeroGain_Pss2c) * ((pss_washout2_derivative_k_Pss2c / pss_washout2_derivative_T_Pss2c) * (pss_limiter1_y_Pss2c - pss_washout2_derivative_x_Pss2c))))),
            (pss_washout3_y_Pss2c - ((pss_washout3_derivative_zeroGain_Pss2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - pss_washout3_derivative_zeroGain_Pss2c) * ((pss_washout3_derivative_k_Pss2c / pss_washout3_derivative_T_Pss2c) * (pss_washout2_y_Pss2c - pss_washout3_derivative_x_Pss2c))))),
            (pss_washout_y_Pss2c - ((pss_washout_derivative_zeroGain_Pss2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - pss_washout_derivative_zeroGain_Pss2c) * ((pss_washout_derivative_k_Pss2c / pss_washout_derivative_T_Pss2c) * (pss_limiter_y_Pss2c - pss_washout_derivative_x_Pss2c))))),
            (pss_washout1_y_Pss2c - ((pss_washout1_derivative_zeroGain_Pss2c * vf.add_const(value=0.0)) + ((vf.add_const(value=1.0) - pss_washout1_derivative_zeroGain_Pss2c) * ((pss_washout1_derivative_k_Pss2c / pss_washout1_derivative_T_Pss2c) * (pss_washout_y_Pss2c - pss_washout1_derivative_x_Pss2c))))),
            (pss_add1_y_Pss2c - ((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c))),
            (pss_limiter_y_Pss2c - ((pss_limiter_uMin_Pss2c + ((((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c)) - pss_limiter_uMin_Pss2c) * sym.heaviside((((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c)) - pss_limiter_uMin_Pss2c)))) - ((((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c)) - pss_limiter_uMax_Pss2c) * sym.heaviside((((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c)) - pss_limiter_uMax_Pss2c))))),
            (pss_gain_y_Pss2c - (pss_gain_k_Pss2c * pss_PGenPu_Pss2c)),
            (pss_limiter1_y_Pss2c - ((pss_limiter1_uMin_Pss2c + (((pss_gain_k_Pss2c * pss_PGenPu_Pss2c) - pss_limiter1_uMin_Pss2c) * sym.heaviside(((pss_gain_k_Pss2c * pss_PGenPu_Pss2c) - pss_limiter1_uMin_Pss2c)))) - (((pss_gain_k_Pss2c * pss_PGenPu_Pss2c) - pss_limiter1_uMax_Pss2c) * sym.heaviside(((pss_gain_k_Pss2c * pss_PGenPu_Pss2c) - pss_limiter1_uMax_Pss2c))))),
        ],
        algebraic_vars=[
            pss_hysteresis_y_Pss2c,
            pss_transferFunction3_x_1_Pss2c,
            pss_transferFunction2_x_1_Pss2c,
            pss_transferFunction1_x_1_Pss2c,
            pss_transferFunction_x_1_Pss2c,
            pss_add_y_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c,
            pss_rampTrackingFilter_z_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_Pss2c,
            pss_feedback_y_Pss2c,
            pss_gain1_y_Pss2c,
            pss_transferFunction_y_Pss2c,
            pss_transferFunction1_y_Pss2c,
            pss_transferFunction2_y_Pss2c,
            pss_transferFunction3_y_Pss2c,
            pss_limiter2_y_Pss2c,
            pss_VPssPu_Pss2c,
            pss_washout2_y_Pss2c,
            pss_washout3_y_Pss2c,
            pss_washout_y_Pss2c,
            pss_washout1_y_Pss2c,
            pss_gain_y_Pss2c,
            pss_limiter1_y_Pss2c,
            pss_limiter_y_Pss2c,
            pss_PGenPu_Pss2c,
            pss_omegaPu_Pss2c,
            pss_omegaRefPu_Pss2c,
            pss_limiter_simplifiedExpr_Pss2c,
            pss_limiter1_simplifiedExpr_Pss2c,
            pss_limiter2_simplifiedExpr_Pss2c,
            START_pss_washout_derivative_x_Pss2c,
            START_pss_washout1_derivative_x_Pss2c,
            START_pss_washout2_derivative_x_Pss2c,
            START_pss_washout3_derivative_x_Pss2c,
            START_pss_firstOrder_y_Pss2c,
            START_pss_firstOrder1_y_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c,
            START_pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c,
            START_pss_transferFunction_x_scaled_1_Pss2c,
            START_pss_transferFunction1_x_scaled_1_Pss2c,
            START_pss_transferFunction2_x_scaled_1_Pss2c,
            START_pss_transferFunction3_x_scaled_1_Pss2c,
            pss_add1_y_Pss2c,
            PRE_pss_hysteresis_y_Pss2c,
            pss_rampTrackingFilter_z_2_Pss2c,
            pss_rampTrackingFilter_z_3_Pss2c,
            pss_rampTrackingFilter_z_4_Pss2c,
        ],
        init_eqs={
            pss_firstOrder_y_Pss2c: START_pss_firstOrder_y_Pss2c,
            pss_firstOrder1_y_Pss2c: START_pss_firstOrder1_y_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c: START_pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c,
            pss_transferFunction_x_scaled_1_Pss2c: START_pss_transferFunction_x_scaled_1_Pss2c,
            pss_transferFunction1_x_scaled_1_Pss2c: START_pss_transferFunction1_x_scaled_1_Pss2c,
            pss_transferFunction2_x_scaled_1_Pss2c: START_pss_transferFunction2_x_scaled_1_Pss2c,
            pss_transferFunction3_x_scaled_1_Pss2c: START_pss_transferFunction3_x_scaled_1_Pss2c,
            pss_washout_derivative_x_Pss2c: START_pss_washout_derivative_x_Pss2c,
            pss_washout1_derivative_x_Pss2c: START_pss_washout1_derivative_x_Pss2c,
            pss_washout2_derivative_x_Pss2c: START_pss_washout2_derivative_x_Pss2c,
            pss_washout3_derivative_x_Pss2c: START_pss_washout3_derivative_x_Pss2c,
            pss_PGenPu_Pss2c: vf.add_const(value=0.8),
            pss_VPssPu_Pss2c: vf.add_const(value=0.0),
            pss_limiter_y_Pss2c: ((pss_limiter_uMin_Pss2c + ((((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c)) - pss_limiter_uMin_Pss2c) * sym.heaviside((((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c)) - pss_limiter_uMin_Pss2c)))) - ((((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c)) - pss_limiter_uMax_Pss2c) * sym.heaviside((((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c)) - pss_limiter_uMax_Pss2c)))),
            pss_limiter1_y_Pss2c: ((pss_limiter1_uMin_Pss2c + (((pss_gain_k_Pss2c * pss_PGenPu_Pss2c) - pss_limiter1_uMin_Pss2c) * sym.heaviside(((pss_gain_k_Pss2c * pss_PGenPu_Pss2c) - pss_limiter1_uMin_Pss2c)))) - (((pss_gain_k_Pss2c * pss_PGenPu_Pss2c) - pss_limiter1_uMax_Pss2c) * sym.heaviside(((pss_gain_k_Pss2c * pss_PGenPu_Pss2c) - pss_limiter1_uMax_Pss2c)))),
            pss_limiter2_y_Pss2c: vf.add_const(value=0.0),
            pss_omegaPu_Pss2c: vf.add_const(value=1.0),
            pss_omegaRefPu_Pss2c: vf.add_const(value=1.0),
            pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_2_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_3_Pss2c,
            pss_rampTrackingFilter_leadMOrderLagCascade_4_Pss2c: pss_rampTrackingFilter_leadMOrderLagCascade_4_Pss2c,
            pss_rampTrackingFilter_z_1_Pss2c: pss_rampTrackingFilter_Y0_Pss2c,
            pss_transferFunction_x_1_Pss2c: pss_transferFunction_x_start_1_Pss2c,
            pss_transferFunction_y_Pss2c: pss_transferFunction_y_start_Pss2c,
            pss_transferFunction1_x_1_Pss2c: pss_transferFunction1_x_start_1_Pss2c,
            pss_transferFunction1_y_Pss2c: pss_transferFunction1_y_start_Pss2c,
            pss_transferFunction2_x_1_Pss2c: pss_transferFunction2_x_start_1_Pss2c,
            pss_transferFunction2_y_Pss2c: pss_transferFunction2_y_start_Pss2c,
            pss_transferFunction3_x_1_Pss2c: pss_transferFunction3_x_start_1_Pss2c,
            pss_transferFunction3_y_Pss2c: pss_transferFunction3_y_start_Pss2c,
            pss_washout_y_Pss2c: pss_washout1_U0_Pss2c,
            pss_washout1_y_Pss2c: vf.add_const(value=0.0),
            pss_washout2_y_Pss2c: pss_washout3_U0_Pss2c,
            pss_washout3_y_Pss2c: vf.add_const(value=0.0),
            pss_hysteresis_y_Pss2c: (sym.heaviside(((pss_gain_y_Pss2c - pss_hysteresis_uHigh_Pss2c) - vf.add_const(value=1e-06))) + sym.heaviside(((pss_gain_y_Pss2c - pss_hysteresis_uLow_Pss2c) + vf.add_const(value=1e-06)))),
            pss_limiter_simplifiedExpr_Pss2c: vf.add_const(value=0.0),
            pss_limiter1_simplifiedExpr_Pss2c: vf.add_const(value=0.0),
            pss_limiter2_simplifiedExpr_Pss2c: vf.add_const(value=0.0),
            pss_add1_y_Pss2c: ((pss_add1_k1_Pss2c * pss_omegaPu_Pss2c) + (pss_add1_k2_Pss2c * pss_omegaRefPu_Pss2c)),
            pss_gain_y_Pss2c: (pss_gain_k_Pss2c * pss_PGenPu_Pss2c),
            PRE_pss_hysteresis_y_Pss2c: pss_hysteresis_pre_y_start_Pss2c,
            pss_rampTrackingFilter_z_2_Pss2c: vf.add_const(value=0.0),
            pss_rampTrackingFilter_z_3_Pss2c: vf.add_const(value=0.0),
            pss_rampTrackingFilter_z_4_Pss2c: vf.add_const(value=0.0),
            pss_rampTrackingFilter_leadMOrderLagCascade_1_Pss2c: vf.add_const(value=1.0),
        },
        event_dict=event_dict,
        in_vars=inputs,
        out_vars=[
        ],
        external_mapping=external_mapping,
        api_obj_mapping=api_obj_mapping,
        diff_vars=[
            d_pss_rampTrackingFilter_leadMOrderLagCascade_4_5_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_4_4_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_4_3_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_4_2_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_3_5_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_3_4_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_3_3_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_3_2_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_2_5_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_2_4_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_2_3_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_2_2_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_1_5_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_1_4_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_1_3_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_1_2_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_1_1_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_2_1_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_3_1_Pss2c,
            d_pss_rampTrackingFilter_leadMOrderLagCascade_4_1_Pss2c,
            d_pss_transferFunction_x_scaled_1_Pss2c,
            d_pss_transferFunction1_x_scaled_1_Pss2c,
            d_pss_transferFunction2_x_scaled_1_Pss2c,
            d_pss_transferFunction3_x_scaled_1_Pss2c,
            d_pss_washout3_derivative_x_Pss2c,
            d_pss_firstOrder1_y_Pss2c,
            d_pss_washout2_derivative_x_Pss2c,
            d_pss_washout1_derivative_x_Pss2c,
            d_pss_firstOrder_y_Pss2c,
            d_pss_washout_derivative_x_Pss2c,
        ],
        name=template_name,
    )
    templ.comment = 'Generator power system stabilizer PSS2C'
    return templ
