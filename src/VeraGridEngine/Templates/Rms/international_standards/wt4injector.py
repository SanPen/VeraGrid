# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'WT4Injector'.

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

def build_wt4injector_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'WT4Injector'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    grid_UNom: Var = vf.add_var('grid.UNom_' + template_name)
    grid_UPhase: Var = vf.add_var('grid.UPhase_' + template_name)
    grid_UPu: Var = vf.add_var('grid.UPu_' + template_name)
    inj_BesPu: Var = vf.add_var('inj.BesPu_' + template_name)
    inj_DipMaxPu: Var = vf.add_var('inj.DipMaxPu_' + template_name)
    inj_DiqMaxPu: Var = vf.add_var('inj.DiqMaxPu_' + template_name)
    inj_DiqMinPu: Var = vf.add_var('inj.DiqMinPu_' + template_name)
    inj_GesPu: Var = vf.add_var('inj.GesPu_' + template_name)
    inj_IGsIm0Pu: Var = vf.add_var('inj.IGsIm0Pu_' + template_name)
    inj_IGsRe0Pu: Var = vf.add_var('inj.IGsRe0Pu_' + template_name)
    inj_IpMax0Pu: Var = vf.add_var('inj.IpMax0Pu_' + template_name)
    inj_IqMax0Pu: Var = vf.add_var('inj.IqMax0Pu_' + template_name)
    inj_IqMin0Pu: Var = vf.add_var('inj.IqMin0Pu_' + template_name)
    inj_Kipaw: Var = vf.add_var('inj.Kipaw_' + template_name)
    inj_Kiqaw: Var = vf.add_var('inj.Kiqaw_' + template_name)
    inj_NbSwitchOffSignals: Var = vf.add_var('inj.NbSwitchOffSignals_' + template_name)
    inj_P0Pu: Var = vf.add_var('inj.P0Pu_' + template_name)
    inj_PAg0Pu: Var = vf.add_var('inj.PAg0Pu_' + template_name)
    inj_Q0Pu: Var = vf.add_var('inj.Q0Pu_' + template_name)
    inj_ResPu: Var = vf.add_var('inj.ResPu_' + template_name)
    inj_Running0: Var = vf.add_var('inj.Running0_' + template_name)
    inj_SNom: Var = vf.add_var('inj.SNom_' + template_name)
    inj_State0: Var = vf.add_var('inj.State0_' + template_name)
    inj_SwitchOffSignal10: Var = vf.add_var('inj.SwitchOffSignal10_' + template_name)
    inj_SwitchOffSignal20: Var = vf.add_var('inj.SwitchOffSignal20_' + template_name)
    inj_SwitchOffSignal30: Var = vf.add_var('inj.SwitchOffSignal30_' + template_name)
    inj_U0Pu: Var = vf.add_var('inj.U0Pu_' + template_name)
    inj_UGsIm0Pu: Var = vf.add_var('inj.UGsIm0Pu_' + template_name)
    inj_UGsRe0Pu: Var = vf.add_var('inj.UGsRe0Pu_' + template_name)
    inj_UPhase0: Var = vf.add_var('inj.UPhase0_' + template_name)
    inj_XesPu: Var = vf.add_var('inj.XesPu_' + template_name)
    inj_elecSystem_BesPu: Var = vf.add_var('inj.elecSystem.BesPu_' + template_name)
    inj_elecSystem_GesPu: Var = vf.add_var('inj.elecSystem.GesPu_' + template_name)
    inj_elecSystem_IGsIm0Pu: Var = vf.add_var('inj.elecSystem.IGsIm0Pu_' + template_name)
    inj_elecSystem_IGsRe0Pu: Var = vf.add_var('inj.elecSystem.IGsRe0Pu_' + template_name)
    inj_elecSystem_ResPu: Var = vf.add_var('inj.elecSystem.ResPu_' + template_name)
    inj_elecSystem_SNom: Var = vf.add_var('inj.elecSystem.SNom_' + template_name)
    inj_elecSystem_UGsIm0Pu: Var = vf.add_var('inj.elecSystem.UGsIm0Pu_' + template_name)
    inj_elecSystem_UGsRe0Pu: Var = vf.add_var('inj.elecSystem.UGsRe0Pu_' + template_name)
    inj_elecSystem_XesPu: Var = vf.add_var('inj.elecSystem.XesPu_' + template_name)
    inj_elecSystem_i0Pu_im: Var = vf.add_var('inj.elecSystem.i0Pu.im_' + template_name)
    inj_elecSystem_i0Pu_re: Var = vf.add_var('inj.elecSystem.i0Pu.re_' + template_name)
    inj_elecSystem_u0Pu_im: Var = vf.add_var('inj.elecSystem.u0Pu.im_' + template_name)
    inj_elecSystem_u0Pu_re: Var = vf.add_var('inj.elecSystem.u0Pu.re_' + template_name)
    inj_genSystem_DipMaxPu: Var = vf.add_var('inj.genSystem.DipMaxPu_' + template_name)
    inj_genSystem_DiqMaxPu: Var = vf.add_var('inj.genSystem.DiqMaxPu_' + template_name)
    inj_genSystem_DiqMinPu: Var = vf.add_var('inj.genSystem.DiqMinPu_' + template_name)
    inj_genSystem_IGsIm0Pu: Var = vf.add_var('inj.genSystem.IGsIm0Pu_' + template_name)
    inj_genSystem_IGsRe0Pu: Var = vf.add_var('inj.genSystem.IGsRe0Pu_' + template_name)
    inj_genSystem_IpMax0Pu: Var = vf.add_var('inj.genSystem.IpMax0Pu_' + template_name)
    inj_genSystem_IqMax0Pu: Var = vf.add_var('inj.genSystem.IqMax0Pu_' + template_name)
    inj_genSystem_IqMin0Pu: Var = vf.add_var('inj.genSystem.IqMin0Pu_' + template_name)
    inj_genSystem_Kipaw: Var = vf.add_var('inj.genSystem.Kipaw_' + template_name)
    inj_genSystem_Kiqaw: Var = vf.add_var('inj.genSystem.Kiqaw_' + template_name)
    inj_genSystem_P0Pu: Var = vf.add_var('inj.genSystem.P0Pu_' + template_name)
    inj_genSystem_PAg0Pu: Var = vf.add_var('inj.genSystem.PAg0Pu_' + template_name)
    inj_genSystem_Q0Pu: Var = vf.add_var('inj.genSystem.Q0Pu_' + template_name)
    inj_genSystem_SNom: Var = vf.add_var('inj.genSystem.SNom_' + template_name)
    inj_genSystem_U0Pu: Var = vf.add_var('inj.genSystem.U0Pu_' + template_name)
    inj_genSystem_UGsIm0Pu: Var = vf.add_var('inj.genSystem.UGsIm0Pu_' + template_name)
    inj_genSystem_UGsRe0Pu: Var = vf.add_var('inj.genSystem.UGsRe0Pu_' + template_name)
    inj_genSystem_UPhase0: Var = vf.add_var('inj.genSystem.UPhase0_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_DyMax: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.DyMax_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_DyMin: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.DyMin_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_Kaw: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.Kaw_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_UseLimits: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.UseLimits_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_Y0: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.Y0_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_YMax: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.YMax_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_YMin: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.YMin_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_k1: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.add.k1_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_k2: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.add.k2_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_k: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.gain.k_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_initType: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.initType_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_k: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.k_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_use_reset: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.use_reset_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_use_set: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.use_set_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y_start: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.y_start_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_homotopyType: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.homotopyType_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_limitsAtInit: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.limitsAtInit_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_strict: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.strict_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.uMax_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.uMin_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_tI: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.tI_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMax: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.DyMax_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMin: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.DyMin_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_Kaw: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.Kaw_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_UseLimits: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.UseLimits_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_Y0: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.Y0_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_YMax: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.YMax_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_YMin: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.YMin_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k1: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.add.k1_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k2: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.add.k2_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_k: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.gain.k_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_initType: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.initType_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_k: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.k_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_use_reset: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.use_reset_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_use_set: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.use_set_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y_start: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.y_start_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_homotopyType: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.homotopyType_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_limitsAtInit: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.limitsAtInit_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_strict: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.strict_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.uMax_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.uMin_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_tI: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.tI_' + template_name)
    inj_genSystem_complexToReal_useConjugateInput: Var = vf.add_var('inj.genSystem.complexToReal.useConjugateInput_' + template_name)
    inj_genSystem_const_k: Var = vf.add_var('inj.genSystem.const.k_' + template_name)
    inj_genSystem_iECFrameRotation_IGsIm0Pu: Var = vf.add_var('inj.genSystem.iECFrameRotation.IGsIm0Pu_' + template_name)
    inj_genSystem_iECFrameRotation_IGsRe0Pu: Var = vf.add_var('inj.genSystem.iECFrameRotation.IGsRe0Pu_' + template_name)
    inj_genSystem_iECFrameRotation_P0Pu: Var = vf.add_var('inj.genSystem.iECFrameRotation.P0Pu_' + template_name)
    inj_genSystem_iECFrameRotation_Q0Pu: Var = vf.add_var('inj.genSystem.iECFrameRotation.Q0Pu_' + template_name)
    inj_genSystem_iECFrameRotation_SNom: Var = vf.add_var('inj.genSystem.iECFrameRotation.SNom_' + template_name)
    inj_genSystem_iECFrameRotation_U0Pu: Var = vf.add_var('inj.genSystem.iECFrameRotation.U0Pu_' + template_name)
    inj_genSystem_iECFrameRotation_UPhase0: Var = vf.add_var('inj.genSystem.iECFrameRotation.UPhase0_' + template_name)
    inj_genSystem_product_useConjugateInput1: Var = vf.add_var('inj.genSystem.product.useConjugateInput1_' + template_name)
    inj_genSystem_product_useConjugateInput2: Var = vf.add_var('inj.genSystem.product.useConjugateInput2_' + template_name)
    inj_genSystem_tG: Var = vf.add_var('inj.genSystem.tG_' + template_name)
    inj_i0Pu_im: Var = vf.add_var('inj.i0Pu.im_' + template_name)
    inj_i0Pu_re: Var = vf.add_var('inj.i0Pu.re_' + template_name)
    inj_tG: Var = vf.add_var('inj.tG_' + template_name)
    inj_u0Pu_im: Var = vf.add_var('inj.u0Pu.im_' + template_name)
    inj_u0Pu_re: Var = vf.add_var('inj.u0Pu.re_' + template_name)
    # Declare the state variables used by the template.
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.y_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_inj_running_value: Var = vf.add_var('$PRE.inj.running.value_' + template_name)
    PRE_inj_state: Var = vf.add_var('$PRE.inj.state_' + template_name)
    START_inj_running_value: Var = vf.add_var('$START.inj.running.value_' + template_name)
    START_inj_state: Var = vf.add_var('$START.inj.state_' + template_name)
    whenCondition1: Var = vf.add_var('$whenCondition1_' + template_name)
    whenCondition2: Var = vf.add_var('$whenCondition2_' + template_name)
    whenCondition3: Var = vf.add_var('$whenCondition3_' + template_name)
    grid_U: Var = vf.add_var('grid.U_' + template_name)
    grid_terminal_V_im: Var = vf.add_var('grid.terminal.V.im_' + template_name)
    grid_terminal_V_re: Var = vf.add_var('grid.terminal.V.re_' + template_name)
    inj_PAgPu: Var = vf.add_var('inj.PAgPu_' + template_name)
    inj_PGenPu: Var = vf.add_var('inj.PGenPu_' + template_name)
    inj_QGenPu: Var = vf.add_var('inj.QGenPu_' + template_name)
    inj_elecSystem_IGsPu: Var = vf.add_var('inj.elecSystem.IGsPu_' + template_name)
    inj_elecSystem_UGsPu: Var = vf.add_var('inj.elecSystem.UGsPu_' + template_name)
    inj_elecSystem_iGsImPu: Var = vf.add_var('inj.elecSystem.iGsImPu_' + template_name)
    inj_elecSystem_iGsRePu: Var = vf.add_var('inj.elecSystem.iGsRePu_' + template_name)
    inj_elecSystem_uGsImPu: Var = vf.add_var('inj.elecSystem.uGsImPu_' + template_name)
    inj_elecSystem_uGsRePu: Var = vf.add_var('inj.elecSystem.uGsRePu_' + template_name)
    inj_fOCB: Var = vf.add_var('inj.fOCB_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.add.y_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_feedback_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.feedback.y_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_feedback1_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.feedback1.y_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.gain.y_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_reset: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.local_reset_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_set: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.local_set_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_simplifiedExpr: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.simplifiedExpr_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.y_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.add.y_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback1_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.feedback1.y_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.gain.y_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_reset: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.local_reset_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_set: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.local_set_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_simplifiedExpr: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.simplifiedExpr_' + template_name)
    inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_y: Var = vf.add_var('inj.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.y_' + template_name)
    inj_genSystem_complexToReal_im: Var = vf.add_var('inj.genSystem.complexToReal.im_' + template_name)
    inj_genSystem_product_u2_im: Var = vf.add_var('inj.genSystem.product.u2.im_' + template_name)
    inj_genSystem_product_u2_re: Var = vf.add_var('inj.genSystem.product.u2.re_' + template_name)
    inj_genSystem_product_y_im: Var = vf.add_var('inj.genSystem.product.y.im_' + template_name)
    inj_genSystem_realToComplex_im: Var = vf.add_var('inj.genSystem.realToComplex.im_' + template_name)
    inj_genSystem_realToComplex_re: Var = vf.add_var('inj.genSystem.realToComplex.re_' + template_name)
    inj_genSystem_terminal_i_im: Var = vf.add_var('inj.genSystem.terminal.i.im_' + template_name)
    inj_genSystem_terminal_i_re: Var = vf.add_var('inj.genSystem.terminal.i.re_' + template_name)
    inj_iWtPu_im: Var = vf.add_var('inj.iWtPu.im_' + template_name)
    inj_iWtPu_re: Var = vf.add_var('inj.iWtPu.re_' + template_name)
    inj_ipCmdPu: Var = vf.add_var('inj.ipCmdPu_' + template_name)
    inj_ipMaxPu: Var = vf.add_var('inj.ipMaxPu_' + template_name)
    inj_iqCmdPu: Var = vf.add_var('inj.iqCmdPu_' + template_name)
    inj_iqMaxPu: Var = vf.add_var('inj.iqMaxPu_' + template_name)
    inj_iqMinPu: Var = vf.add_var('inj.iqMinPu_' + template_name)
    inj_running_value: Var = vf.add_var('inj.running.value_' + template_name)
    inj_state: Var = vf.add_var('inj.state_' + template_name)
    inj_switchOffSignal1_value: Var = vf.add_var('inj.switchOffSignal1.value_' + template_name)
    inj_switchOffSignal2_value: Var = vf.add_var('inj.switchOffSignal2.value_' + template_name)
    inj_switchOffSignal3_value: Var = vf.add_var('inj.switchOffSignal3.value_' + template_name)
    inj_terminal_i_im: Var = vf.add_var('inj.terminal.i.im_' + template_name)
    inj_terminal_i_re: Var = vf.add_var('inj.terminal.i.re_' + template_name)
    inj_theta: Var = vf.add_var('inj.theta_' + template_name)
    # Declare the differential variables used by the template.
    d_inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y: Var = vf.add_diff_var('d_inj.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.y_' + template_name, base_var=inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y)
    d_inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y: Var = vf.add_diff_var('d_inj.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.y_' + template_name, base_var=inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_k * inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_y))
    state_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_k * inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_y))
    state_variables: list[Var] = list()
    state_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y)
    state_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((inj_genSystem_realToComplex_re - ((sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y - inj_ipMaxPu) - sym.Const(1e-06))) * inj_ipMaxPu) + ((sym.Const(1.0) - sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y - inj_ipMaxPu) - sym.Const(1e-06)))) * ((sym.heaviside(((inj_genSystem_const_k - inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y) - sym.Const(1e-06))) * inj_genSystem_const_k) + ((sym.Const(1.0) - sym.heaviside(((inj_genSystem_const_k - inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y) - sym.Const(1e-06)))) * inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y))))))
    algebraic_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup_feedback1_y - (inj_genSystem_realToComplex_re - inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y)))
    algebraic_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup_feedback_y - (inj_ipCmdPu - inj_genSystem_realToComplex_re)))
    algebraic_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y - (inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_k * inj_genSystem_absLimRateLimFirstOrderAntiWindup_feedback_y)))
    algebraic_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_y - ((sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y - inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax) - sym.Const(1e-06))) * inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y - inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin - inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y) - sym.Const(1e-06))) * inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin - inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y) - sym.Const(1e-06)))) * inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y))))))
    algebraic_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_y - ((inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_k1 * inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_y) + (inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_k2 * inj_genSystem_absLimRateLimFirstOrderAntiWindup_feedback1_y))))
    algebraic_equations.append((inj_genSystem_realToComplex_im - ((sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y - inj_iqMaxPu) - sym.Const(1e-06))) * inj_iqMaxPu) + ((sym.Const(1.0) - sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y - inj_iqMaxPu) - sym.Const(1e-06)))) * ((sym.heaviside(((inj_iqMinPu - inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y) - sym.Const(1e-06))) * inj_iqMinPu) + ((sym.Const(1.0) - sym.heaviside(((inj_iqMinPu - inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y) - sym.Const(1e-06)))) * inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y))))))
    algebraic_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback1_y - (inj_genSystem_realToComplex_im - inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y)))
    algebraic_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y - (inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_k * (inj_iqCmdPu - inj_genSystem_realToComplex_im))))
    algebraic_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_y - ((sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y - inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax) - sym.Const(1e-06))) * inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y - inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin - inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y) - sym.Const(1e-06))) * inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin - inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y) - sym.Const(1e-06)))) * inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y))))))
    algebraic_equations.append((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_y - ((inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k1 * inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_y) + (inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k2 * inj_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback1_y))))
    algebraic_equations.append((whenCondition1 - (sym.Const(1.0) - inj_running_value)))
    algebraic_equations.append((whenCondition3 - (sym.Const(1.0) - inj_running_value)))
    algebraic_equations.append((whenCondition2 - (inj_running_value * (sym.Const(1.0) - inj_running_value))))
    algebraic_equations.append((inj_elecSystem_iGsImPu - (sym.Const(-100.0) * (inj_genSystem_terminal_i_im / inj_elecSystem_SNom))))
    algebraic_equations.append((inj_elecSystem_IGsPu - (sym.Const(100.0) * ((((inj_genSystem_terminal_i_re ** sym.Const(2.0)) + (inj_genSystem_terminal_i_im ** sym.Const(2.0))) ** sym.Const(0.5)) / inj_elecSystem_SNom))))
    algebraic_equations.append((inj_elecSystem_iGsRePu - (sym.Const(-100.0) * (inj_genSystem_terminal_i_re / inj_elecSystem_SNom))))
    algebraic_equations.append((inj_terminal_i_im - (sym.Const(0.01) * ((-inj_iWtPu_im) * inj_elecSystem_SNom))))
    algebraic_equations.append((inj_elecSystem_UGsPu - (((inj_elecSystem_uGsRePu ** sym.Const(2.0)) + (inj_elecSystem_uGsImPu ** sym.Const(2.0))) ** sym.Const(0.5))))
    algebraic_equations.append((inj_genSystem_product_y_im - ((inj_elecSystem_uGsImPu * inj_genSystem_product_u2_re) - (inj_elecSystem_uGsRePu * inj_genSystem_product_u2_im))))
    algebraic_equations.append((inj_genSystem_complexToReal_im - ((inj_genSystem_complexToReal_useConjugateInput * (-inj_genSystem_product_y_im)) + ((sym.Const(1.0) - inj_genSystem_complexToReal_useConjugateInput) * inj_genSystem_product_y_im))))
    algebraic_equations.append((inj_PAgPu - ((inj_elecSystem_uGsRePu * inj_genSystem_product_u2_re) + (inj_elecSystem_uGsImPu * inj_genSystem_product_u2_im))))
    algebraic_equations.append((inj_terminal_i_re - (sym.Const(0.01) * ((-inj_iWtPu_re) * inj_elecSystem_SNom))))
    algebraic_equations.append((inj_PGenPu - (((-grid_terminal_V_re) * inj_terminal_i_re) - (grid_terminal_V_im * inj_terminal_i_im))))
    algebraic_equations.append((inj_QGenPu - ((grid_terminal_V_re * inj_terminal_i_im) - (grid_terminal_V_im * inj_terminal_i_re))))
    algebraic_equations.append((inj_running_value - sym.Const(1.0)))
    algebraic_equations.append(inj_state)
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(inj_genSystem_realToComplex_re)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup_feedback1_y)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup_feedback_y)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_y)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_y)
    algebraic_variables.append(inj_genSystem_realToComplex_im)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback1_y)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_y)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_y)
    algebraic_variables.append(whenCondition1)
    algebraic_variables.append(whenCondition3)
    algebraic_variables.append(whenCondition2)
    algebraic_variables.append(inj_elecSystem_iGsImPu)
    algebraic_variables.append(inj_elecSystem_IGsPu)
    algebraic_variables.append(inj_elecSystem_iGsRePu)
    algebraic_variables.append(inj_terminal_i_im)
    algebraic_variables.append(inj_elecSystem_UGsPu)
    algebraic_variables.append(inj_genSystem_product_y_im)
    algebraic_variables.append(inj_genSystem_complexToReal_im)
    algebraic_variables.append(inj_PAgPu)
    algebraic_variables.append(inj_terminal_i_re)
    algebraic_variables.append(inj_PGenPu)
    algebraic_variables.append(inj_QGenPu)
    algebraic_variables.append(inj_running_value)
    algebraic_variables.append(inj_state)
    algebraic_variables.append(inj_genSystem_terminal_i_im)
    algebraic_variables.append(inj_genSystem_terminal_i_re)
    algebraic_variables.append(inj_iWtPu_im)
    algebraic_variables.append(inj_elecSystem_uGsRePu)
    algebraic_variables.append(inj_elecSystem_uGsImPu)
    algebraic_variables.append(inj_genSystem_product_u2_re)
    algebraic_variables.append(inj_genSystem_product_u2_im)
    algebraic_variables.append(inj_iWtPu_re)
    algebraic_variables.append(grid_terminal_V_re)
    algebraic_variables.append(grid_terminal_V_im)
    algebraic_variables.append(inj_ipCmdPu)
    algebraic_variables.append(inj_ipMaxPu)
    algebraic_variables.append(inj_iqCmdPu)
    algebraic_variables.append(inj_iqMaxPu)
    algebraic_variables.append(inj_iqMinPu)
    algebraic_variables.append(inj_theta)
    algebraic_variables.append(inj_fOCB)
    algebraic_variables.append(inj_switchOffSignal1_value)
    algebraic_variables.append(inj_switchOffSignal2_value)
    algebraic_variables.append(inj_switchOffSignal3_value)
    algebraic_variables.append(grid_U)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_simplifiedExpr)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_reset)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_set)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_simplifiedExpr)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_reset)
    algebraic_variables.append(inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_set)
    algebraic_variables.append(PRE_inj_running_value)
    algebraic_variables.append(START_inj_running_value)
    algebraic_variables.append(PRE_inj_state)
    algebraic_variables.append(START_inj_state)
    differential_variables: list[Var] = list()
    differential_variables.append(d_inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y)
    differential_variables.append(d_inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[grid_UNom] = vf.add_const(1.0, name='')
    event_parameters[grid_UPhase] = vf.add_const(0.0, name='')
    event_parameters[grid_UPu] = vf.add_const(1.0, name='')
    event_parameters[inj_BesPu] = vf.add_const(0.0, name='')
    event_parameters[inj_DipMaxPu] = vf.add_const(99.0, name='')
    event_parameters[inj_DiqMaxPu] = vf.add_const(999.0, name='')
    event_parameters[inj_DiqMinPu] = vf.add_const(-999.0, name='')
    event_parameters[inj_GesPu] = vf.add_const(0.0, name='')
    event_parameters[inj_IGsIm0Pu] = vf.add_const(0.0, name='')
    event_parameters[inj_IGsRe0Pu] = vf.add_const(0.8, name='')
    event_parameters[inj_IpMax0Pu] = vf.add_const(1.2, name='')
    event_parameters[inj_IqMax0Pu] = vf.add_const(1.1, name='')
    event_parameters[inj_IqMin0Pu] = vf.add_const(-1.1, name='')
    event_parameters[inj_Kipaw] = vf.add_const(0.0, name='')
    event_parameters[inj_Kiqaw] = vf.add_const(0.0, name='')
    event_parameters[inj_P0Pu] = vf.add_const(-0.8, name='')
    event_parameters[inj_PAg0Pu] = vf.add_const(0.8, name='')
    event_parameters[inj_Q0Pu] = vf.add_const(0.0, name='')
    event_parameters[inj_ResPu] = vf.add_const(0.0, name='')
    event_parameters[inj_SNom] = vf.add_const(100.0, name='')
    event_parameters[inj_U0Pu] = vf.add_const(1.0, name='')
    event_parameters[inj_UGsIm0Pu] = vf.add_const(0.0, name='')
    event_parameters[inj_UGsRe0Pu] = vf.add_const(1.0, name='')
    event_parameters[inj_UPhase0] = vf.add_const(0.0, name='')
    event_parameters[inj_XesPu] = vf.add_const(0.0, name='')
    event_parameters[inj_elecSystem_BesPu] = inj_BesPu
    event_parameters[inj_elecSystem_GesPu] = inj_GesPu
    event_parameters[inj_elecSystem_IGsIm0Pu] = inj_IGsIm0Pu
    event_parameters[inj_elecSystem_IGsRe0Pu] = inj_IGsRe0Pu
    event_parameters[inj_elecSystem_ResPu] = inj_ResPu
    event_parameters[inj_elecSystem_SNom] = inj_SNom
    event_parameters[inj_elecSystem_UGsIm0Pu] = inj_UGsIm0Pu
    event_parameters[inj_elecSystem_UGsRe0Pu] = inj_UGsRe0Pu
    event_parameters[inj_elecSystem_XesPu] = inj_XesPu
    event_parameters[inj_elecSystem_i0Pu_im] = inj_i0Pu_im
    event_parameters[inj_elecSystem_i0Pu_re] = inj_i0Pu_re
    event_parameters[inj_elecSystem_u0Pu_im] = inj_u0Pu_im
    event_parameters[inj_elecSystem_u0Pu_re] = inj_u0Pu_re
    event_parameters[inj_genSystem_DipMaxPu] = inj_DipMaxPu
    event_parameters[inj_genSystem_DiqMaxPu] = inj_DiqMaxPu
    event_parameters[inj_genSystem_DiqMinPu] = inj_DiqMinPu
    event_parameters[inj_genSystem_IGsIm0Pu] = inj_IGsIm0Pu
    event_parameters[inj_genSystem_IGsRe0Pu] = inj_IGsRe0Pu
    event_parameters[inj_genSystem_IpMax0Pu] = inj_IpMax0Pu
    event_parameters[inj_genSystem_IqMax0Pu] = inj_IqMax0Pu
    event_parameters[inj_genSystem_IqMin0Pu] = inj_IqMin0Pu
    event_parameters[inj_genSystem_Kipaw] = inj_Kipaw
    event_parameters[inj_genSystem_Kiqaw] = inj_Kiqaw
    event_parameters[inj_genSystem_P0Pu] = inj_P0Pu
    event_parameters[inj_genSystem_PAg0Pu] = inj_PAg0Pu
    event_parameters[inj_genSystem_Q0Pu] = inj_Q0Pu
    event_parameters[inj_genSystem_SNom] = inj_SNom
    event_parameters[inj_genSystem_U0Pu] = inj_U0Pu
    event_parameters[inj_genSystem_UGsIm0Pu] = inj_UGsIm0Pu
    event_parameters[inj_genSystem_UGsRe0Pu] = inj_UGsRe0Pu
    event_parameters[inj_genSystem_UPhase0] = inj_UPhase0
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_DyMax] = inj_genSystem_DipMaxPu
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_DyMin] = vf.add_const(-999.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_Kaw] = inj_genSystem_Kipaw
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_Y0] = ((sym.Const(-100.0) * inj_genSystem_P0Pu) / (inj_genSystem_U0Pu * inj_genSystem_SNom))
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_YMax] = vf.add_const(999.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_YMin] = (-inj_genSystem_absLimRateLimFirstOrderAntiWindup_YMax)
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_k1] = vf.add_const(1.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_add_k2] = inj_genSystem_absLimRateLimFirstOrderAntiWindup_Kaw
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_gain_k] = (sym.Const(1.0) / inj_genSystem_absLimRateLimFirstOrderAntiWindup_tI)
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y_start] = inj_genSystem_absLimRateLimFirstOrderAntiWindup_Y0
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax] = inj_genSystem_absLimRateLimFirstOrderAntiWindup_DyMax
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin] = inj_genSystem_absLimRateLimFirstOrderAntiWindup_DyMin
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_tI] = inj_genSystem_tG
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMax] = inj_genSystem_DiqMaxPu
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMin] = inj_genSystem_DiqMinPu
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_Kaw] = inj_genSystem_Kiqaw
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_Y0] = (sym.Const(100.0) * (inj_genSystem_Q0Pu / (inj_genSystem_U0Pu * inj_genSystem_SNom)))
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_YMax] = vf.add_const(999.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_YMin] = (-inj_genSystem_absLimRateLimFirstOrderAntiWindup1_YMax)
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k1] = vf.add_const(1.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k2] = inj_genSystem_absLimRateLimFirstOrderAntiWindup1_Kaw
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_k] = (sym.Const(1.0) / inj_genSystem_absLimRateLimFirstOrderAntiWindup1_tI)
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y_start] = inj_genSystem_absLimRateLimFirstOrderAntiWindup1_Y0
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax] = inj_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMax
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin] = inj_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMin
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_tI] = inj_genSystem_tG
    event_parameters[inj_genSystem_const_k] = vf.add_const(-999.0, name='')
    event_parameters[inj_genSystem_iECFrameRotation_IGsIm0Pu] = inj_genSystem_IGsIm0Pu
    event_parameters[inj_genSystem_iECFrameRotation_IGsRe0Pu] = inj_genSystem_IGsRe0Pu
    event_parameters[inj_genSystem_iECFrameRotation_P0Pu] = inj_genSystem_P0Pu
    event_parameters[inj_genSystem_iECFrameRotation_Q0Pu] = inj_genSystem_Q0Pu
    event_parameters[inj_genSystem_iECFrameRotation_SNom] = inj_genSystem_SNom
    event_parameters[inj_genSystem_iECFrameRotation_U0Pu] = inj_genSystem_U0Pu
    event_parameters[inj_genSystem_iECFrameRotation_UPhase0] = inj_genSystem_UPhase0
    event_parameters[inj_genSystem_tG] = inj_tG
    event_parameters[inj_i0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[inj_i0Pu_re] = vf.add_const(-0.8, name='')
    event_parameters[inj_tG] = vf.add_const(0.02, name='')
    event_parameters[inj_u0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[inj_u0Pu_re] = vf.add_const(1.0, name='')
    event_parameters[inj_NbSwitchOffSignals] = vf.add_const(3.0, name='')
    event_parameters[inj_State0] = vf.add_const(2.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[inj_Running0] = (sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - inj_SwitchOffSignal10) * (sym.Const(1.0) - inj_SwitchOffSignal20)))) * (sym.Const(1.0) - inj_SwitchOffSignal30))))
    event_parameters[inj_SwitchOffSignal10] = vf.add_const(0.0, name='')
    event_parameters[inj_SwitchOffSignal20] = vf.add_const(0.0, name='')
    event_parameters[inj_SwitchOffSignal30] = vf.add_const(0.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_UseLimits] = vf.add_const(1.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_UseLimits] = vf.add_const(1.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[inj_genSystem_complexToReal_useConjugateInput] = vf.add_const(0.0, name='')
    event_parameters[inj_genSystem_product_useConjugateInput1] = vf.add_const(0.0, name='')
    event_parameters[inj_genSystem_product_useConjugateInput2] = vf.add_const(1.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y] = inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y_start
    initial_equations[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y] = inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y_start
    initial_equations[inj_PAgPu] = inj_genSystem_PAg0Pu
    initial_equations[inj_PGenPu] = vf.add_const(0.8, name='')
    initial_equations[inj_QGenPu] = vf.add_const(0.0, name='')
    initial_equations[inj_elecSystem_IGsPu] = sym.sqrt(((inj_elecSystem_IGsRe0Pu ** sym.Const(2.0)) + (inj_elecSystem_IGsIm0Pu ** sym.Const(2.0))))
    initial_equations[inj_elecSystem_UGsPu] = sym.sqrt(((inj_elecSystem_UGsRe0Pu ** sym.Const(2.0)) + (inj_elecSystem_UGsIm0Pu ** sym.Const(2.0))))
    initial_equations[inj_elecSystem_iGsImPu] = inj_elecSystem_IGsIm0Pu
    initial_equations[inj_elecSystem_iGsRePu] = inj_elecSystem_IGsRe0Pu
    initial_equations[inj_elecSystem_uGsImPu] = inj_genSystem_UGsIm0Pu
    initial_equations[inj_elecSystem_uGsRePu] = inj_genSystem_UGsRe0Pu
    initial_equations[inj_genSystem_realToComplex_im] = ((inj_genSystem_iECFrameRotation_Q0Pu * sym.Const(100.0)) / (inj_genSystem_iECFrameRotation_SNom * inj_genSystem_iECFrameRotation_U0Pu))
    initial_equations[inj_genSystem_realToComplex_re] = (((-inj_genSystem_iECFrameRotation_P0Pu) * sym.Const(100.0)) / (inj_genSystem_iECFrameRotation_SNom * inj_genSystem_iECFrameRotation_U0Pu))
    initial_equations[inj_genSystem_terminal_i_im] = (sym.Const(0.01) * ((-inj_elecSystem_IGsIm0Pu) * inj_elecSystem_SNom))
    initial_equations[inj_genSystem_terminal_i_re] = (sym.Const(0.01) * ((-inj_elecSystem_IGsRe0Pu) * inj_elecSystem_SNom))
    initial_equations[inj_iWtPu_im] = (((-inj_elecSystem_i0Pu_im) * sym.Const(100.0)) / inj_elecSystem_SNom)
    initial_equations[inj_iWtPu_re] = (((-inj_elecSystem_i0Pu_re) * sym.Const(100.0)) / inj_elecSystem_SNom)
    initial_equations[inj_ipCmdPu] = vf.add_const(0.8, name='')
    initial_equations[inj_ipMaxPu] = vf.add_const(1.2, name='')
    initial_equations[inj_iqCmdPu] = vf.add_const(0.0, name='')
    initial_equations[inj_iqMaxPu] = vf.add_const(1.1, name='')
    initial_equations[inj_iqMinPu] = vf.add_const(-1.1, name='')
    initial_equations[inj_terminal_i_im] = inj_elecSystem_i0Pu_im
    initial_equations[inj_terminal_i_re] = inj_elecSystem_i0Pu_re
    initial_equations[inj_theta] = vf.add_const(0.0, name='')
    initial_equations[inj_state] = PRE_inj_state
    initial_equations[inj_fOCB] = vf.add_const(0.0, name='')
    initial_equations[inj_running_value] = PRE_inj_running_value
    initial_equations[inj_switchOffSignal1_value] = vf.add_const(0.0, name='')
    initial_equations[inj_switchOffSignal2_value] = vf.add_const(0.0, name='')
    initial_equations[inj_switchOffSignal3_value] = vf.add_const(0.0, name='')
    initial_equations[grid_U] = (grid_UPu * grid_UNom)
    initial_equations[inj_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[inj_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[inj_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[PRE_inj_running_value] = START_inj_running_value
    initial_equations[whenCondition2] = (inj_running_value * (sym.Const(1.0) - PRE_inj_running_value))
    initial_equations[whenCondition1] = (sym.Const(1.0) - PRE_inj_running_value)
    initial_equations[grid_terminal_V_im] = (grid_UPu * sym.sin(grid_UPhase))
    initial_equations[grid_terminal_V_re] = (grid_UPu * sym.cos(grid_UPhase))
    initial_equations[PRE_inj_state] = START_inj_state
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

    template.comment = 'Generator WECC type-4 wind injector'
    return template
