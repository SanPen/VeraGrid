# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Ac8b'.

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

def build_ac8b_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'Ac8b'
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
    avr_Efe0Pu: Var = vf.add_var('avr.Efe0Pu_' + template_name)
    avr_Ir0Pu: Var = vf.add_var('avr.Ir0Pu_' + template_name)
    avr_Ka: Var = vf.add_var('avr.Ka_' + template_name)
    avr_Kc: Var = vf.add_var('avr.Kc_' + template_name)
    avr_Kd: Var = vf.add_var('avr.Kd_' + template_name)
    avr_Kdr: Var = vf.add_var('avr.Kdr_' + template_name)
    avr_Ke: Var = vf.add_var('avr.Ke_' + template_name)
    avr_Kir: Var = vf.add_var('avr.Kir_' + template_name)
    avr_Kpr: Var = vf.add_var('avr.Kpr_' + template_name)
    avr_TolLi: Var = vf.add_var('avr.TolLi_' + template_name)
    avr_Us0Pu: Var = vf.add_var('avr.Us0Pu_' + template_name)
    avr_Ve0Pu: Var = vf.add_var('avr.Ve0Pu_' + template_name)
    avr_VeMax0Pu: Var = vf.add_var('avr.VeMax0Pu_' + template_name)
    avr_VeMinPu: Var = vf.add_var('avr.VeMinPu_' + template_name)
    avr_VfeMaxPu: Var = vf.add_var('avr.VfeMaxPu_' + template_name)
    avr_VrMaxPu: Var = vf.add_var('avr.VrMaxPu_' + template_name)
    avr_VrMinPu: Var = vf.add_var('avr.VrMinPu_' + template_name)
    avr_acRotatingExciter_AEx: Var = vf.add_var('avr.acRotatingExciter.AEx_' + template_name)
    avr_acRotatingExciter_BEx: Var = vf.add_var('avr.acRotatingExciter.BEx_' + template_name)
    avr_acRotatingExciter_Efd0Pu: Var = vf.add_var('avr.acRotatingExciter.Efd0Pu_' + template_name)
    avr_acRotatingExciter_Efe0Pu: Var = vf.add_var('avr.acRotatingExciter.Efe0Pu_' + template_name)
    avr_acRotatingExciter_Ir0Pu: Var = vf.add_var('avr.acRotatingExciter.Ir0Pu_' + template_name)
    avr_acRotatingExciter_Kc: Var = vf.add_var('avr.acRotatingExciter.Kc_' + template_name)
    avr_acRotatingExciter_Kd: Var = vf.add_var('avr.acRotatingExciter.Kd_' + template_name)
    avr_acRotatingExciter_Ke: Var = vf.add_var('avr.acRotatingExciter.Ke_' + template_name)
    avr_acRotatingExciter_TolLi: Var = vf.add_var('avr.acRotatingExciter.TolLi_' + template_name)
    avr_acRotatingExciter_Ve0Pu: Var = vf.add_var('avr.acRotatingExciter.Ve0Pu_' + template_name)
    avr_acRotatingExciter_VeMax0Pu: Var = vf.add_var('avr.acRotatingExciter.VeMax0Pu_' + template_name)
    avr_acRotatingExciter_VeMinPu: Var = vf.add_var('avr.acRotatingExciter.VeMinPu_' + template_name)
    avr_acRotatingExciter_VfeMaxPu: Var = vf.add_var('avr.acRotatingExciter.VfeMaxPu_' + template_name)
    avr_acRotatingExciter_add_k1: Var = vf.add_var('avr.acRotatingExciter.add.k1_' + template_name)
    avr_acRotatingExciter_add_k2: Var = vf.add_var('avr.acRotatingExciter.add.k2_' + template_name)
    avr_acRotatingExciter_add1_k1: Var = vf.add_var('avr.acRotatingExciter.add1.k1_' + template_name)
    avr_acRotatingExciter_add1_k2: Var = vf.add_var('avr.acRotatingExciter.add1.k2_' + template_name)
    avr_acRotatingExciter_add2_k1: Var = vf.add_var('avr.acRotatingExciter.add2.k1_' + template_name)
    avr_acRotatingExciter_add2_k2: Var = vf.add_var('avr.acRotatingExciter.add2.k2_' + template_name)
    avr_acRotatingExciter_const_k: Var = vf.add_var('avr.acRotatingExciter.const.k_' + template_name)
    avr_acRotatingExciter_const1_k: Var = vf.add_var('avr.acRotatingExciter.const1.k_' + template_name)
    avr_acRotatingExciter_const2_k: Var = vf.add_var('avr.acRotatingExciter.const2.k_' + template_name)
    avr_acRotatingExciter_firstOrder_T: Var = vf.add_var('avr.acRotatingExciter.firstOrder.T_' + template_name)
    avr_acRotatingExciter_firstOrder_initType: Var = vf.add_var('avr.acRotatingExciter.firstOrder.initType_' + template_name)
    avr_acRotatingExciter_firstOrder_k: Var = vf.add_var('avr.acRotatingExciter.firstOrder.k_' + template_name)
    avr_acRotatingExciter_firstOrder_y_start: Var = vf.add_var('avr.acRotatingExciter.firstOrder.y_start_' + template_name)
    avr_acRotatingExciter_gain_k: Var = vf.add_var('avr.acRotatingExciter.gain.k_' + template_name)
    avr_acRotatingExciter_gain1_k: Var = vf.add_var('avr.acRotatingExciter.gain1.k_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_DefaultLimitMax: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.DefaultLimitMax_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_FrozenMax0: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.FrozenMax0_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_FrozenMin0: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.FrozenMin0_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_K: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.K_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_LimitMax0: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.LimitMax0_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_LimitMin0: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.LimitMin0_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_Tol: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.Tol_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_Y0: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.Y0_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_T: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.T_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_initType: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.initType_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_k: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.k_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_start: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.x_start_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_start: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.y_start_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.zeroGain_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_T: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.T_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_initType: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.initType_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_k: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.k_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_start: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.x_start_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_start: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.y_start_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.zeroGain_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_tDer: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.tDer_' + template_name)
    avr_acRotatingExciter_power_base: Var = vf.add_var('avr.acRotatingExciter.power.base_' + template_name)
    avr_acRotatingExciter_power_useExp: Var = vf.add_var('avr.acRotatingExciter.power.useExp_' + template_name)
    avr_acRotatingExciter_rectifierRegulationCharacteristic_A1: Var = vf.add_var('avr.acRotatingExciter.rectifierRegulationCharacteristic.A1_' + template_name)
    avr_acRotatingExciter_rectifierRegulationCharacteristic_A2: Var = vf.add_var('avr.acRotatingExciter.rectifierRegulationCharacteristic.A2_' + template_name)
    avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh: Var = vf.add_var('avr.acRotatingExciter.rectifierRegulationCharacteristic.UHigh_' + template_name)
    avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow: Var = vf.add_var('avr.acRotatingExciter.rectifierRegulationCharacteristic.ULow_' + template_name)
    avr_acRotatingExciter_tE: Var = vf.add_var('avr.acRotatingExciter.tE_' + template_name)
    avr_add_k1: Var = vf.add_var('avr.add.k1_' + template_name)
    avr_add_k2: Var = vf.add_var('avr.add.k2_' + template_name)
    avr_const1_k: Var = vf.add_var('avr.const1.k_' + template_name)
    avr_firstOrder_T: Var = vf.add_var('avr.firstOrder.T_' + template_name)
    avr_firstOrder_initType: Var = vf.add_var('avr.firstOrder.initType_' + template_name)
    avr_firstOrder_k: Var = vf.add_var('avr.firstOrder.k_' + template_name)
    avr_firstOrder_y_start: Var = vf.add_var('avr.firstOrder.y_start_' + template_name)
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
    avr_pid_D_T: Var = vf.add_var('avr.pid.D.T_' + template_name)
    avr_pid_D_initType: Var = vf.add_var('avr.pid.D.initType_' + template_name)
    avr_pid_D_k: Var = vf.add_var('avr.pid.D.k_' + template_name)
    avr_pid_D_x_start: Var = vf.add_var('avr.pid.D.x_start_' + template_name)
    avr_pid_D_y_start: Var = vf.add_var('avr.pid.D.y_start_' + template_name)
    avr_pid_D_zeroGain: Var = vf.add_var('avr.pid.D.zeroGain_' + template_name)
    avr_pid_FFzero_k: Var = vf.add_var('avr.pid.FFzero.k_' + template_name)
    avr_pid_I_initType: Var = vf.add_var('avr.pid.I.initType_' + template_name)
    avr_pid_I_k: Var = vf.add_var('avr.pid.I.k_' + template_name)
    avr_pid_I_use_reset: Var = vf.add_var('avr.pid.I.use_reset_' + template_name)
    avr_pid_I_use_set: Var = vf.add_var('avr.pid.I.use_set_' + template_name)
    avr_pid_I_y_start: Var = vf.add_var('avr.pid.I.y_start_' + template_name)
    avr_pid_Nd: Var = vf.add_var('avr.pid.Nd_' + template_name)
    avr_pid_Ni: Var = vf.add_var('avr.pid.Ni_' + template_name)
    avr_pid_P_k: Var = vf.add_var('avr.pid.P.k_' + template_name)
    avr_pid_Td: Var = vf.add_var('avr.pid.Td_' + template_name)
    avr_pid_Ti: Var = vf.add_var('avr.pid.Ti_' + template_name)
    avr_pid_addD_k1: Var = vf.add_var('avr.pid.addD.k1_' + template_name)
    avr_pid_addD_k2: Var = vf.add_var('avr.pid.addD.k2_' + template_name)
    avr_pid_addFF_k1: Var = vf.add_var('avr.pid.addFF.k1_' + template_name)
    avr_pid_addFF_k2: Var = vf.add_var('avr.pid.addFF.k2_' + template_name)
    avr_pid_addI_k1: Var = vf.add_var('avr.pid.addI.k1_' + template_name)
    avr_pid_addI_k2: Var = vf.add_var('avr.pid.addI.k2_' + template_name)
    avr_pid_addI_k3: Var = vf.add_var('avr.pid.addI.k3_' + template_name)
    avr_pid_addP_k1: Var = vf.add_var('avr.pid.addP.k1_' + template_name)
    avr_pid_addP_k2: Var = vf.add_var('avr.pid.addP.k2_' + template_name)
    avr_pid_addPID_k1: Var = vf.add_var('avr.pid.addPID.k1_' + template_name)
    avr_pid_addPID_k2: Var = vf.add_var('avr.pid.addPID.k2_' + template_name)
    avr_pid_addPID_k3: Var = vf.add_var('avr.pid.addPID.k3_' + template_name)
    avr_pid_addSat_k1: Var = vf.add_var('avr.pid.addSat.k1_' + template_name)
    avr_pid_addSat_k2: Var = vf.add_var('avr.pid.addSat.k2_' + template_name)
    avr_pid_controllerType: Var = vf.add_var('avr.pid.controllerType_' + template_name)
    avr_pid_gainPID_k: Var = vf.add_var('avr.pid.gainPID.k_' + template_name)
    avr_pid_gainTrack_k: Var = vf.add_var('avr.pid.gainTrack.k_' + template_name)
    avr_pid_homotopyType: Var = vf.add_var('avr.pid.homotopyType_' + template_name)
    avr_pid_initType: Var = vf.add_var('avr.pid.initType_' + template_name)
    avr_pid_k: Var = vf.add_var('avr.pid.k_' + template_name)
    avr_pid_kFF: Var = vf.add_var('avr.pid.kFF_' + template_name)
    avr_pid_limiter_homotopyType: Var = vf.add_var('avr.pid.limiter.homotopyType_' + template_name)
    avr_pid_limiter_limitsAtInit: Var = vf.add_var('avr.pid.limiter.limitsAtInit_' + template_name)
    avr_pid_limiter_strict: Var = vf.add_var('avr.pid.limiter.strict_' + template_name)
    avr_pid_limiter_uMax: Var = vf.add_var('avr.pid.limiter.uMax_' + template_name)
    avr_pid_limiter_uMin: Var = vf.add_var('avr.pid.limiter.uMin_' + template_name)
    avr_pid_limitsAtInit: Var = vf.add_var('avr.pid.limitsAtInit_' + template_name)
    avr_pid_strict: Var = vf.add_var('avr.pid.strict_' + template_name)
    avr_pid_unitTime: Var = vf.add_var('avr.pid.unitTime_' + template_name)
    avr_pid_wd: Var = vf.add_var('avr.pid.wd_' + template_name)
    avr_pid_withFeedForward: Var = vf.add_var('avr.pid.withFeedForward_' + template_name)
    avr_pid_with_D: Var = vf.add_var('avr.pid.with_D_' + template_name)
    avr_pid_with_I: Var = vf.add_var('avr.pid.with_I_' + template_name)
    avr_pid_wp: Var = vf.add_var('avr.pid.wp_' + template_name)
    avr_pid_xd_start: Var = vf.add_var('avr.pid.xd_start_' + template_name)
    avr_pid_xi_start: Var = vf.add_var('avr.pid.xi_start_' + template_name)
    avr_pid_yMax: Var = vf.add_var('avr.pid.yMax_' + template_name)
    avr_pid_yMin: Var = vf.add_var('avr.pid.yMin_' + template_name)
    avr_pid_y_start: Var = vf.add_var('avr.pid.y_start_' + template_name)
    avr_sum1_k_1: Var = vf.add_var('avr.sum1.k[1]_' + template_name)
    avr_sum1_k_2: Var = vf.add_var('avr.sum1.k[2]_' + template_name)
    avr_sum1_nin: Var = vf.add_var('avr.sum1.nin_' + template_name)
    avr_tA: Var = vf.add_var('avr.tA_' + template_name)
    avr_tDr: Var = vf.add_var('avr.tDr_' + template_name)
    avr_tE: Var = vf.add_var('avr.tE_' + template_name)
    avr_tR: Var = vf.add_var('avr.tR_' + template_name)
    # Declare the state variables used by the template.
    avr_acRotatingExciter_firstOrder_y: Var = vf.add_var('avr.acRotatingExciter.firstOrder.y_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.x_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.x_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_w: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.w_' + template_name)
    avr_firstOrder_y: Var = vf.add_var('avr.firstOrder.y_' + template_name)
    avr_limitedFirstOrder_I_y: Var = vf.add_var('avr.limitedFirstOrder.I.y_' + template_name)
    avr_pid_D_x: Var = vf.add_var('avr.pid.D.x_' + template_name)
    avr_pid_I_y: Var = vf.add_var('avr.pid.I.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax: Var = vf.add_var('$PRE.avr.acRotatingExciter.integratorVariableLimits.isFrozenMax_' + template_name)
    PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin: Var = vf.add_var('$PRE.avr.acRotatingExciter.integratorVariableLimits.isFrozenMin_' + template_name)
    START_avr_acRotatingExciter_firstOrder_y: Var = vf.add_var('$START.avr.acRotatingExciter.firstOrder.y_' + template_name)
    START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x: Var = vf.add_var('$START.avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.x_' + template_name)
    START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x: Var = vf.add_var('$START.avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.x_' + template_name)
    START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax: Var = vf.add_var('$START.avr.acRotatingExciter.integratorVariableLimits.isFrozenMax_' + template_name)
    START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin: Var = vf.add_var('$START.avr.acRotatingExciter.integratorVariableLimits.isFrozenMin_' + template_name)
    START_avr_acRotatingExciter_integratorVariableLimits_w: Var = vf.add_var('$START.avr.acRotatingExciter.integratorVariableLimits.w_' + template_name)
    START_avr_firstOrder_y: Var = vf.add_var('$START.avr.firstOrder.y_' + template_name)
    START_avr_pid_D_x: Var = vf.add_var('$START.avr.pid.D.x_' + template_name)
    avr_EfdPu: Var = vf.add_var('avr.EfdPu_' + template_name)
    avr_IrPu: Var = vf.add_var('avr.IrPu_' + template_name)
    avr_UPssPu: Var = vf.add_var('avr.UPssPu_' + template_name)
    avr_UsPu: Var = vf.add_var('avr.UsPu_' + template_name)
    avr_UsRefPu: Var = vf.add_var('avr.UsRefPu_' + template_name)
    avr_acRotatingExciter_VfePu: Var = vf.add_var('avr.acRotatingExciter.VfePu_' + template_name)
    avr_acRotatingExciter_add_y: Var = vf.add_var('avr.acRotatingExciter.add.y_' + template_name)
    avr_acRotatingExciter_add1_y: Var = vf.add_var('avr.acRotatingExciter.add1.y_' + template_name)
    avr_acRotatingExciter_division_y: Var = vf.add_var('avr.acRotatingExciter.division.y_' + template_name)
    avr_acRotatingExciter_division1_y: Var = vf.add_var('avr.acRotatingExciter.division1.y_' + template_name)
    avr_acRotatingExciter_feedback_y: Var = vf.add_var('avr.acRotatingExciter.feedback.y_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.y_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.y_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_isFrozenMax: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.isFrozenMax_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_isFrozenMin: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.isFrozenMin_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.keepFreezingMax_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.keepFreezingMin_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_startFreezingMax: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.startFreezingMax_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_startFreezingMin: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.startFreezingMin_' + template_name)
    avr_acRotatingExciter_integratorVariableLimits_y: Var = vf.add_var('avr.acRotatingExciter.integratorVariableLimits.y_' + template_name)
    avr_acRotatingExciter_power_y: Var = vf.add_var('avr.acRotatingExciter.power.y_' + template_name)
    avr_acRotatingExciter_product1_y: Var = vf.add_var('avr.acRotatingExciter.product1.y_' + template_name)
    avr_acRotatingExciter_rectifierRegulationCharacteristic_y: Var = vf.add_var('avr.acRotatingExciter.rectifierRegulationCharacteristic.y_' + template_name)
    avr_limitedFirstOrder_G_y: Var = vf.add_var('avr.limitedFirstOrder.G.y_' + template_name)
    avr_limitedFirstOrder_Gk_y: Var = vf.add_var('avr.limitedFirstOrder.Gk.y_' + template_name)
    avr_limitedFirstOrder_I_local_reset: Var = vf.add_var('avr.limitedFirstOrder.I.local_reset_' + template_name)
    avr_limitedFirstOrder_I_local_set: Var = vf.add_var('avr.limitedFirstOrder.I.local_set_' + template_name)
    avr_limitedFirstOrder_I_u: Var = vf.add_var('avr.limitedFirstOrder.I.u_' + template_name)
    avr_limitedFirstOrder_feedback_y: Var = vf.add_var('avr.limitedFirstOrder.feedback.y_' + template_name)
    avr_limitedFirstOrder_lim_simplifiedExpr: Var = vf.add_var('avr.limitedFirstOrder.lim.simplifiedExpr_' + template_name)
    avr_limitedFirstOrder_y: Var = vf.add_var('avr.limitedFirstOrder.y_' + template_name)
    avr_pid_D_y: Var = vf.add_var('avr.pid.D.y_' + template_name)
    avr_pid_I_local_reset: Var = vf.add_var('avr.pid.I.local_reset_' + template_name)
    avr_pid_I_local_set: Var = vf.add_var('avr.pid.I.local_set_' + template_name)
    avr_pid_P_y: Var = vf.add_var('avr.pid.P.y_' + template_name)
    avr_pid_addD_y: Var = vf.add_var('avr.pid.addD.y_' + template_name)
    avr_pid_addI_y: Var = vf.add_var('avr.pid.addI.y_' + template_name)
    avr_pid_addP_y: Var = vf.add_var('avr.pid.addP.y_' + template_name)
    avr_pid_addPID_y: Var = vf.add_var('avr.pid.addPID.y_' + template_name)
    avr_pid_addSat_y: Var = vf.add_var('avr.pid.addSat.y_' + template_name)
    avr_pid_controlError: Var = vf.add_var('avr.pid.controlError_' + template_name)
    avr_pid_gainPID_y: Var = vf.add_var('avr.pid.gainPID.y_' + template_name)
    avr_pid_gainTrack_y: Var = vf.add_var('avr.pid.gainTrack.y_' + template_name)
    avr_pid_limiter_u: Var = vf.add_var('avr.pid.limiter.u_' + template_name)
    avr_pid_y: Var = vf.add_var('avr.pid.y_' + template_name)
    avr_sum1_u_1: Var = vf.add_var('avr.sum1.u[1]_' + template_name)
    avr_sum1_y: Var = vf.add_var('avr.sum1.y_' + template_name)
    # Declare the differential variables used by the template.
    d_avr_acRotatingExciter_firstOrder_y: Var = vf.add_diff_var('d_avr.acRotatingExciter.firstOrder.y_' + template_name, base_var=avr_acRotatingExciter_firstOrder_y)
    d_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x: Var = vf.add_diff_var('d_avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMax.x_' + template_name, base_var=avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x)
    d_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x: Var = vf.add_diff_var('d_avr.acRotatingExciter.integratorVariableLimits.derivativeLimitMin.x_' + template_name, base_var=avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x)
    d_avr_acRotatingExciter_integratorVariableLimits_w: Var = vf.add_diff_var('d_avr.acRotatingExciter.integratorVariableLimits.w_' + template_name, base_var=avr_acRotatingExciter_integratorVariableLimits_w)
    d_avr_firstOrder_y: Var = vf.add_diff_var('d_avr.firstOrder.y_' + template_name, base_var=avr_firstOrder_y)
    d_avr_limitedFirstOrder_I_y: Var = vf.add_diff_var('d_avr.limitedFirstOrder.I.y_' + template_name, base_var=avr_limitedFirstOrder_I_y)
    d_avr_pid_D_x: Var = vf.add_diff_var('d_avr.pid.D.x_' + template_name, base_var=avr_pid_D_x)
    d_avr_pid_I_y: Var = vf.add_diff_var('d_avr.pid.I.y_' + template_name, base_var=avr_pid_I_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((avr_pid_D_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_pid_D_zeroGain) * ((avr_pid_addD_y - avr_pid_D_x) / avr_pid_D_T))))
    state_equations.append((avr_limitedFirstOrder_I_k * avr_limitedFirstOrder_I_u))
    state_equations.append((avr_pid_I_k * avr_pid_addI_y))
    state_equations.append((((avr_firstOrder_k * avr_UsPu) - avr_firstOrder_y) / avr_firstOrder_T))
    state_equations.append((((avr_acRotatingExciter_firstOrder_k * avr_acRotatingExciter_division1_y) - avr_acRotatingExciter_firstOrder_y) / avr_acRotatingExciter_firstOrder_T))
    state_equations.append(((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain) * ((avr_acRotatingExciter_const1_k - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x) / avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_T))))
    state_equations.append(((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain) * ((avr_acRotatingExciter_firstOrder_y - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x) / avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_T))))
    state_variables: list[Var] = list()
    state_variables.append(avr_pid_D_x)
    state_variables.append(avr_limitedFirstOrder_I_y)
    state_variables.append(avr_pid_I_y)
    state_variables.append(avr_firstOrder_y)
    state_variables.append(avr_acRotatingExciter_firstOrder_y)
    state_variables.append(avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x)
    state_variables.append(avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x)
    state_variables.append(avr_acRotatingExciter_integratorVariableLimits_w)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((avr_limitedFirstOrder_y - ((sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))) * avr_limitedFirstOrder_lim_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06))) * avr_limitedFirstOrder_lim_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06)))) * avr_limitedFirstOrder_I_y))))))
    algebraic_equations.append((avr_sum1_u_1 - ((avr_UsRefPu - avr_firstOrder_y) + avr_UPssPu)))
    algebraic_equations.append((avr_sum1_y - (avr_sum1_k_1 * avr_sum1_u_1)))
    algebraic_equations.append((avr_pid_addP_y - ((avr_pid_addP_k1 * avr_sum1_y) + (avr_pid_addP_k2 * avr_const1_k))))
    algebraic_equations.append((avr_pid_P_y - (avr_pid_P_k * avr_pid_addP_y)))
    algebraic_equations.append((avr_pid_addD_y - ((avr_pid_addD_k1 * avr_sum1_y) + (avr_pid_addD_k2 * avr_const1_k))))
    algebraic_equations.append((avr_pid_D_y - ((avr_pid_D_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_pid_D_zeroGain) * ((avr_pid_D_k / avr_pid_D_T) * (avr_pid_addD_y - avr_pid_D_x))))))
    algebraic_equations.append((avr_pid_addPID_y - ((avr_pid_addPID_k1 * avr_pid_P_y) + ((avr_pid_addPID_k2 * avr_pid_D_y) + (avr_pid_addPID_k3 * avr_pid_I_y)))))
    algebraic_equations.append((avr_pid_gainPID_y - (avr_pid_gainPID_k * avr_pid_addPID_y)))
    algebraic_equations.append((avr_pid_limiter_u - ((avr_pid_addFF_k1 * avr_pid_gainPID_y) + (avr_pid_addFF_k2 * avr_pid_FFzero_k))))
    algebraic_equations.append((avr_pid_y - ((sym.heaviside(((avr_pid_limiter_u - avr_pid_limiter_uMax) - sym.Const(1e-06))) * avr_pid_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_pid_limiter_u - avr_pid_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_pid_limiter_uMin - avr_pid_limiter_u) - sym.Const(1e-06))) * avr_pid_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_pid_limiter_uMin - avr_pid_limiter_u) - sym.Const(1e-06)))) * avr_pid_limiter_u))))))
    algebraic_equations.append((avr_pid_addSat_y - ((avr_pid_addSat_k1 * avr_pid_y) + (avr_pid_addSat_k2 * avr_pid_limiter_u))))
    algebraic_equations.append((avr_pid_gainTrack_y - (avr_pid_gainTrack_k * avr_pid_addSat_y)))
    algebraic_equations.append((avr_limitedFirstOrder_Gk_y - (avr_limitedFirstOrder_Gk_k * avr_pid_y)))
    algebraic_equations.append((avr_limitedFirstOrder_feedback_y - (avr_limitedFirstOrder_Gk_y - avr_limitedFirstOrder_y)))
    algebraic_equations.append((avr_limitedFirstOrder_G_y - (avr_limitedFirstOrder_G_k * avr_limitedFirstOrder_feedback_y)))
    algebraic_equations.append((avr_limitedFirstOrder_I_u - (((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06)))))))) * avr_limitedFirstOrder_G_y))))
    algebraic_equations.append((avr_pid_addI_y - ((avr_pid_addI_k1 * avr_sum1_y) + ((avr_pid_addI_k2 * avr_const1_k) + (avr_pid_addI_k3 * avr_pid_gainTrack_y)))))
    algebraic_equations.append((avr_pid_controlError - (avr_sum1_y - avr_const1_k)))
    algebraic_equations.append((avr_acRotatingExciter_integratorVariableLimits_y - (((sym.heaviside(((avr_acRotatingExciter_const1_k - avr_acRotatingExciter_firstOrder_y) - sym.Const(1e-06))) * avr_acRotatingExciter_integratorVariableLimits_DefaultLimitMax) * avr_acRotatingExciter_firstOrder_y) + ((sym.Const(1.0) - (sym.heaviside(((avr_acRotatingExciter_const1_k - avr_acRotatingExciter_firstOrder_y) - sym.Const(1e-06))) * avr_acRotatingExciter_integratorVariableLimits_DefaultLimitMax)) * ((sym.heaviside(((avr_acRotatingExciter_const1_k - avr_acRotatingExciter_firstOrder_y) - sym.Const(1e-06))) * avr_acRotatingExciter_const1_k) + ((sym.Const(1.0) - sym.heaviside(((avr_acRotatingExciter_const1_k - avr_acRotatingExciter_firstOrder_y) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_acRotatingExciter_const1_k - avr_acRotatingExciter_integratorVariableLimits_w) - sym.Const(1e-06))) * avr_acRotatingExciter_const1_k) + ((sym.Const(1.0) - sym.heaviside(((avr_acRotatingExciter_const1_k - avr_acRotatingExciter_integratorVariableLimits_w) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w - avr_acRotatingExciter_firstOrder_y) - sym.Const(1e-06))) * avr_acRotatingExciter_firstOrder_y) + ((sym.Const(1.0) - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w - avr_acRotatingExciter_firstOrder_y) - sym.Const(1e-06)))) * avr_acRotatingExciter_integratorVariableLimits_w))))))))))
    algebraic_equations.append((avr_acRotatingExciter_division_y - (avr_acRotatingExciter_gain_k / avr_acRotatingExciter_integratorVariableLimits_y)))
    algebraic_equations.append((avr_acRotatingExciter_rectifierRegulationCharacteristic_y - ((sym.heaviside(((sym.Const(0.0) - avr_acRotatingExciter_division_y) + sym.Const(1e-06))) * sym.Const(1.0)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(0.0) - avr_acRotatingExciter_division_y) + sym.Const(1e-06)))) * ((((sym.heaviside(((avr_acRotatingExciter_division_y - sym.Const(0.0)) - sym.Const(1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow - avr_acRotatingExciter_division_y) + sym.Const(1e-06)))) * (sym.Const(1.0) - (avr_acRotatingExciter_rectifierRegulationCharacteristic_A1 * avr_acRotatingExciter_division_y))) + ((sym.Const(1.0) - ((sym.heaviside(((avr_acRotatingExciter_division_y - sym.Const(0.0)) - sym.Const(1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow - avr_acRotatingExciter_division_y) + sym.Const(1e-06))))) * ((((sym.heaviside(((avr_acRotatingExciter_division_y - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06)))) * sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh - avr_acRotatingExciter_division_y) - sym.Const(1e-06)))) * sym.sqrt((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh - (avr_acRotatingExciter_division_y ** sym.Const(2.0))))) + ((sym.Const(1.0) - ((sym.heaviside(((avr_acRotatingExciter_division_y - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06)))) * sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh - avr_acRotatingExciter_division_y) - sym.Const(1e-06))))) * ((((sym.heaviside(((avr_acRotatingExciter_division_y - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - avr_acRotatingExciter_division_y) + sym.Const(1e-06)))) * (avr_acRotatingExciter_rectifierRegulationCharacteristic_A2 * (sym.Const(1.0) - avr_acRotatingExciter_division_y))) + ((sym.Const(1.0) - ((sym.heaviside(((avr_acRotatingExciter_division_y - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06))) * sym.heaviside(((avr_acRotatingExciter_division_y - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - avr_acRotatingExciter_division_y) + sym.Const(1e-06))))) * sym.Const(0.0)))))))))))
    algebraic_equations.append((avr_EfdPu - (avr_acRotatingExciter_rectifierRegulationCharacteristic_y * avr_acRotatingExciter_integratorVariableLimits_y)))
    algebraic_equations.append((avr_acRotatingExciter_product1_y - (avr_acRotatingExciter_add_y * avr_acRotatingExciter_integratorVariableLimits_y)))
    algebraic_equations.append((avr_acRotatingExciter_division1_y - (avr_acRotatingExciter_add1_y / avr_acRotatingExciter_product1_y)))
    algebraic_equations.append((avr_acRotatingExciter_VfePu - ((avr_acRotatingExciter_add2_k1 * avr_acRotatingExciter_gain1_k) + (avr_acRotatingExciter_add2_k2 * avr_acRotatingExciter_product1_y))))
    algebraic_equations.append((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y - ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain) * ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_k / avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_T) * (avr_acRotatingExciter_const1_k - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x))))))
    algebraic_equations.append((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y - ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain) * ((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_k / avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_T) * (avr_acRotatingExciter_firstOrder_y - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x))))))
    algebraic_equations.append((avr_acRotatingExciter_feedback_y - (avr_limitedFirstOrder_y - avr_acRotatingExciter_VfePu)))
    algebraic_equations.append(((avr_acRotatingExciter_integratorVariableLimits_startFreezingMax - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w - avr_acRotatingExciter_firstOrder_y) - sym.Const(1e-06)))) - sym.heaviside((((avr_acRotatingExciter_integratorVariableLimits_K * avr_acRotatingExciter_feedback_y) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y) - sym.Const(1e-06)))))
    algebraic_equations.append(((avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w - (avr_acRotatingExciter_firstOrder_y - (avr_acRotatingExciter_integratorVariableLimits_Tol * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0 - avr_acRotatingExciter_integratorVariableLimits_LimitMin0))))) - sym.Const(1e-06)))) - sym.heaviside((((avr_acRotatingExciter_integratorVariableLimits_K * avr_acRotatingExciter_feedback_y) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y) - sym.Const(1e-06)))))
    algebraic_equations.append((avr_acRotatingExciter_integratorVariableLimits_isFrozenMax - (sym.Const(1.0) - ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_startFreezingMax) * (sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax)))))
    algebraic_equations.append(((avr_acRotatingExciter_integratorVariableLimits_startFreezingMin - sym.heaviside(((avr_acRotatingExciter_const1_k - avr_acRotatingExciter_integratorVariableLimits_w) - sym.Const(1e-06)))) - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y - (avr_acRotatingExciter_integratorVariableLimits_K * avr_acRotatingExciter_feedback_y)) - sym.Const(1e-06)))))
    algebraic_equations.append(((avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin - sym.heaviside((((avr_acRotatingExciter_const1_k + (avr_acRotatingExciter_integratorVariableLimits_Tol * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0 - avr_acRotatingExciter_integratorVariableLimits_LimitMin0)))) - avr_acRotatingExciter_integratorVariableLimits_w) - sym.Const(1e-06)))) - sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y - (avr_acRotatingExciter_integratorVariableLimits_K * avr_acRotatingExciter_feedback_y)) - sym.Const(1e-06)))))
    algebraic_equations.append((avr_acRotatingExciter_integratorVariableLimits_isFrozenMin - (sym.Const(1.0) - ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_startFreezingMin) * (sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin)))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(avr_limitedFirstOrder_y)
    algebraic_variables.append(avr_sum1_u_1)
    algebraic_variables.append(avr_sum1_y)
    algebraic_variables.append(avr_pid_addP_y)
    algebraic_variables.append(avr_pid_P_y)
    algebraic_variables.append(avr_pid_addD_y)
    algebraic_variables.append(avr_pid_D_y)
    algebraic_variables.append(avr_pid_addPID_y)
    algebraic_variables.append(avr_pid_gainPID_y)
    algebraic_variables.append(avr_pid_limiter_u)
    algebraic_variables.append(avr_pid_y)
    algebraic_variables.append(avr_pid_addSat_y)
    algebraic_variables.append(avr_pid_gainTrack_y)
    algebraic_variables.append(avr_limitedFirstOrder_Gk_y)
    algebraic_variables.append(avr_limitedFirstOrder_feedback_y)
    algebraic_variables.append(avr_limitedFirstOrder_G_y)
    algebraic_variables.append(avr_limitedFirstOrder_I_u)
    algebraic_variables.append(avr_pid_addI_y)
    algebraic_variables.append(avr_pid_controlError)
    algebraic_variables.append(avr_acRotatingExciter_integratorVariableLimits_y)
    algebraic_variables.append(avr_acRotatingExciter_division_y)
    algebraic_variables.append(avr_acRotatingExciter_rectifierRegulationCharacteristic_y)
    algebraic_variables.append(avr_EfdPu)
    algebraic_variables.append(avr_acRotatingExciter_product1_y)
    algebraic_variables.append(avr_acRotatingExciter_division1_y)
    algebraic_variables.append(avr_acRotatingExciter_VfePu)
    algebraic_variables.append(avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y)
    algebraic_variables.append(avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y)
    algebraic_variables.append(avr_acRotatingExciter_feedback_y)
    algebraic_variables.append(avr_acRotatingExciter_integratorVariableLimits_startFreezingMax)
    algebraic_variables.append(avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax)
    algebraic_variables.append(avr_acRotatingExciter_integratorVariableLimits_isFrozenMax)
    algebraic_variables.append(avr_acRotatingExciter_integratorVariableLimits_startFreezingMin)
    algebraic_variables.append(avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin)
    algebraic_variables.append(avr_acRotatingExciter_integratorVariableLimits_isFrozenMin)
    algebraic_variables.append(avr_acRotatingExciter_add_y)
    algebraic_variables.append(avr_acRotatingExciter_add1_y)
    algebraic_variables.append(avr_IrPu)
    algebraic_variables.append(avr_UPssPu)
    algebraic_variables.append(avr_UsPu)
    algebraic_variables.append(avr_UsRefPu)
    algebraic_variables.append(avr_pid_I_local_reset)
    algebraic_variables.append(avr_pid_I_local_set)
    algebraic_variables.append(avr_limitedFirstOrder_lim_simplifiedExpr)
    algebraic_variables.append(avr_limitedFirstOrder_I_local_reset)
    algebraic_variables.append(avr_limitedFirstOrder_I_local_set)
    algebraic_variables.append(START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x)
    algebraic_variables.append(START_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x)
    algebraic_variables.append(PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax)
    algebraic_variables.append(START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax)
    algebraic_variables.append(PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin)
    algebraic_variables.append(START_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin)
    algebraic_variables.append(START_avr_acRotatingExciter_integratorVariableLimits_w)
    algebraic_variables.append(START_avr_acRotatingExciter_firstOrder_y)
    algebraic_variables.append(START_avr_firstOrder_y)
    algebraic_variables.append(START_avr_pid_D_x)
    algebraic_variables.append(avr_acRotatingExciter_power_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_avr_pid_D_x)
    differential_variables.append(d_avr_limitedFirstOrder_I_y)
    differential_variables.append(d_avr_pid_I_y)
    differential_variables.append(d_avr_firstOrder_y)
    differential_variables.append(d_avr_acRotatingExciter_firstOrder_y)
    differential_variables.append(d_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x)
    differential_variables.append(d_avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x)
    differential_variables.append(d_avr_acRotatingExciter_integratorVariableLimits_w)
    input_variables: list[Var] = list()
    input_variables.append(avr_IrPu)
    input_variables.append(avr_UPssPu)
    input_variables.append(avr_UsPu)
    input_variables.append(avr_UsRefPu)
    output_variables: list[Var] = list()
    output_variables.append(avr_EfdPu)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[avr_AEx] = vf.add_const(0.0, name='')
    event_parameters[avr_BEx] = vf.add_const(0.0, name='')
    event_parameters[avr_Efd0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Efe0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Ir0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Ka] = vf.add_const(200.0, name='')
    event_parameters[avr_Kc] = vf.add_const(0.0, name='')
    event_parameters[avr_Kd] = vf.add_const(0.0, name='')
    event_parameters[avr_Kdr] = vf.add_const(0.0, name='')
    event_parameters[avr_Ke] = vf.add_const(1.0, name='')
    event_parameters[avr_Kir] = vf.add_const(10.0, name='')
    event_parameters[avr_Kpr] = vf.add_const(1.0, name='')
    event_parameters[avr_TolLi] = vf.add_const(1e-06, name='')
    event_parameters[avr_Us0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Ve0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_VeMax0Pu] = vf.add_const(5.0, name='')
    event_parameters[avr_VeMinPu] = vf.add_const(0.0, name='')
    event_parameters[avr_VfeMaxPu] = vf.add_const(999.0, name='')
    event_parameters[avr_VrMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VrMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_acRotatingExciter_AEx] = avr_AEx
    event_parameters[avr_acRotatingExciter_BEx] = vf.add_const(0.0, name='')
    event_parameters[avr_acRotatingExciter_Efd0Pu] = avr_Efd0Pu
    event_parameters[avr_acRotatingExciter_Efe0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_Ir0Pu] = avr_Ir0Pu
    event_parameters[avr_acRotatingExciter_Kc] = avr_Kc
    event_parameters[avr_acRotatingExciter_Kd] = avr_Kd
    event_parameters[avr_acRotatingExciter_Ke] = avr_Ke
    event_parameters[avr_acRotatingExciter_TolLi] = avr_TolLi
    event_parameters[avr_acRotatingExciter_Ve0Pu] = avr_Ve0Pu
    event_parameters[avr_acRotatingExciter_VeMax0Pu] = avr_VeMax0Pu
    event_parameters[avr_acRotatingExciter_VeMinPu] = avr_VeMinPu
    event_parameters[avr_acRotatingExciter_VfeMaxPu] = avr_VfeMaxPu
    event_parameters[avr_acRotatingExciter_add_k1] = avr_acRotatingExciter_AEx
    event_parameters[avr_acRotatingExciter_add_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_add1_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_add1_k2] = vf.add_const(-1.0, name='')
    event_parameters[avr_acRotatingExciter_add2_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_add2_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_const_k] = avr_acRotatingExciter_VfeMaxPu
    event_parameters[avr_acRotatingExciter_const1_k] = avr_acRotatingExciter_VeMinPu
    event_parameters[avr_acRotatingExciter_const2_k] = avr_acRotatingExciter_Ke
    event_parameters[avr_acRotatingExciter_firstOrder_T] = vf.add_const(1e-05, name='')
    event_parameters[avr_acRotatingExciter_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_firstOrder_y_start] = avr_acRotatingExciter_VeMax0Pu
    event_parameters[avr_acRotatingExciter_gain_k] = avr_acRotatingExciter_Kc
    event_parameters[avr_acRotatingExciter_gain1_k] = avr_acRotatingExciter_Kd
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_K] = (sym.Const(1.0) / avr_acRotatingExciter_tE)
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_LimitMax0] = avr_acRotatingExciter_VeMax0Pu
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_LimitMin0] = avr_acRotatingExciter_VeMinPu
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_Tol] = avr_acRotatingExciter_TolLi
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_Y0] = avr_acRotatingExciter_Ve0Pu
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_T] = avr_acRotatingExciter_integratorVariableLimits_tDer
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_k] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_start] = avr_acRotatingExciter_integratorVariableLimits_LimitMax0
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y_start] = vf.add_const(0.0, name='')
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_T] = avr_acRotatingExciter_integratorVariableLimits_tDer
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_k] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_start] = avr_acRotatingExciter_integratorVariableLimits_LimitMin0
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y_start] = vf.add_const(0.0, name='')
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_tDer] = vf.add_const(0.01, name='')
    event_parameters[avr_acRotatingExciter_power_base] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_rectifierRegulationCharacteristic_A1] = (((sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow) + sym.Const(1e-06)))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow) + sym.Const(1e-06))))) * ((sym.Const(1.0) - sym.sqrt((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh - (avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow ** sym.Const(2.0))))) / avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow)))
    event_parameters[avr_acRotatingExciter_rectifierRegulationCharacteristic_A2] = (((sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06)))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.heaviside(((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06))))) * sym.sqrt((avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh / (sym.Const(1.0) - avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh)))))
    event_parameters[avr_acRotatingExciter_rectifierRegulationCharacteristic_UHigh] = vf.add_const(0.75, name='')
    event_parameters[avr_acRotatingExciter_rectifierRegulationCharacteristic_ULow] = vf.add_const(0.4330127018922193, name='')
    event_parameters[avr_acRotatingExciter_tE] = avr_tE
    event_parameters[avr_add_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_add_k2] = vf.add_const(-1.0, name='')
    event_parameters[avr_const1_k] = vf.add_const(0.0, name='')
    event_parameters[avr_firstOrder_T] = avr_tR
    event_parameters[avr_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_y_start] = avr_Us0Pu
    event_parameters[avr_limitedFirstOrder_G_k] = (sym.Const(1.0) / avr_limitedFirstOrder_tFilter)
    event_parameters[avr_limitedFirstOrder_Gk_k] = avr_limitedFirstOrder_K
    event_parameters[avr_limitedFirstOrder_I_k] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_I_y_start] = avr_limitedFirstOrder_Y0
    event_parameters[avr_limitedFirstOrder_K] = vf.add_const(200.0, name='')
    event_parameters[avr_limitedFirstOrder_Y0] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_YMax] = vf.add_const(5.0, name='')
    event_parameters[avr_limitedFirstOrder_YMin] = vf.add_const(-5.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_uMax] = avr_limitedFirstOrder_YMax
    event_parameters[avr_limitedFirstOrder_lim_uMin] = avr_limitedFirstOrder_YMin
    event_parameters[avr_limitedFirstOrder_tFilter] = avr_tA
    event_parameters[avr_pid_D_T] = (((avr_pid_Td / avr_pid_Nd) * sym.heaviside(((avr_pid_Td / avr_pid_Nd) - sym.Const(1e-14)))) + (sym.Const(1e-14) * (sym.Const(1) - sym.heaviside(((avr_pid_Td / avr_pid_Nd) - sym.Const(1e-14))))))
    event_parameters[avr_pid_D_k] = avr_pid_Td
    event_parameters[avr_pid_D_x_start] = avr_pid_xd_start
    event_parameters[avr_pid_D_y_start] = vf.add_const(0.0, name='')
    event_parameters[avr_pid_FFzero_k] = vf.add_const(0.0, name='')
    event_parameters[avr_pid_I_k] = (sym.Const(1.0) / avr_pid_Ti)
    event_parameters[avr_pid_I_y_start] = avr_pid_xi_start
    event_parameters[avr_pid_Nd] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_Ni] = vf.add_const(0.9, name='')
    event_parameters[avr_pid_P_k] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_Td] = avr_tDr
    event_parameters[avr_pid_Ti] = (sym.Const(1.0) / avr_Kir)
    event_parameters[avr_pid_addD_k1] = avr_pid_wd
    event_parameters[avr_pid_addD_k2] = vf.add_const(-1.0, name='')
    event_parameters[avr_pid_addFF_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_addFF_k2] = avr_pid_kFF
    event_parameters[avr_pid_addI_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_addI_k2] = vf.add_const(-1.0, name='')
    event_parameters[avr_pid_addI_k3] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_addP_k1] = avr_pid_wp
    event_parameters[avr_pid_addP_k2] = vf.add_const(-1.0, name='')
    event_parameters[avr_pid_addPID_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_addPID_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_addPID_k3] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_addSat_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_addSat_k2] = vf.add_const(-1.0, name='')
    event_parameters[avr_pid_gainPID_k] = avr_pid_k
    event_parameters[avr_pid_gainTrack_k] = (sym.Const(1.0) / (avr_pid_Ni * avr_pid_k))
    event_parameters[avr_pid_k] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_kFF] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_limiter_uMax] = vf.add_const(5.0, name='')
    event_parameters[avr_pid_limiter_uMin] = vf.add_const(-5.0, name='')
    event_parameters[avr_pid_wd] = (avr_Kdr / avr_tDr)
    event_parameters[avr_pid_wp] = avr_Kpr
    event_parameters[avr_pid_xd_start] = vf.add_const(0.0, name='')
    event_parameters[avr_pid_xi_start] = vf.add_const(0.005, name='')
    event_parameters[avr_pid_yMax] = vf.add_const(5.0, name='')
    event_parameters[avr_pid_yMin] = vf.add_const(-5.0, name='')
    event_parameters[avr_pid_y_start] = vf.add_const(0.005, name='')
    event_parameters[avr_sum1_k_1] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_2] = vf.add_const(1.0, name='')
    event_parameters[avr_tA] = vf.add_const(0.02, name='')
    event_parameters[avr_tDr] = vf.add_const(0.02, name='')
    event_parameters[avr_tE] = vf.add_const(0.5, name='')
    event_parameters[avr_tR] = vf.add_const(0.02, name='')
    event_parameters[avr_acRotatingExciter_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_I_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_D_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_I_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_pid_controllerType] = vf.add_const(4.0, name='')
    event_parameters[avr_pid_homotopyType] = vf.add_const(2.0, name='')
    event_parameters[avr_pid_initType] = vf.add_const(5.0, name='')
    event_parameters[avr_pid_limiter_homotopyType] = vf.add_const(2.0, name='')
    event_parameters[avr_sum1_nin] = vf.add_const(2.0, name='')
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_DefaultLimitMax] = vf.add_const(1.0, name='')
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_FrozenMax0] = sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_Y0 - (avr_acRotatingExciter_integratorVariableLimits_LimitMax0 - (avr_acRotatingExciter_integratorVariableLimits_Tol * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0 - avr_acRotatingExciter_integratorVariableLimits_LimitMin0))))) - sym.Const(1e-06)))
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_FrozenMin0] = sym.heaviside((((avr_acRotatingExciter_integratorVariableLimits_LimitMin0 + (avr_acRotatingExciter_integratorVariableLimits_Tol * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0 - avr_acRotatingExciter_integratorVariableLimits_LimitMin0)))) - avr_acRotatingExciter_integratorVariableLimits_Y0) - sym.Const(1e-06)))
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_k)) - sym.Const(1e-06)))
    event_parameters[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_k)) - sym.Const(1e-06)))
    event_parameters[avr_acRotatingExciter_power_useExp] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_I_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_I_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_pid_D_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(avr_pid_D_k)) - sym.Const(1e-06)))
    event_parameters[avr_pid_I_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_pid_I_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_pid_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_pid_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_pid_withFeedForward] = vf.add_const(0.0, name='')
    event_parameters[avr_pid_with_D] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_with_I] = vf.add_const(1.0, name='')
    event_parameters[avr_pid_unitTime] = vf.add_const(1.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[avr_acRotatingExciter_firstOrder_y] = avr_acRotatingExciter_firstOrder_y_start
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x] = avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_x_start
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x] = avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_x_start
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_w] = avr_acRotatingExciter_integratorVariableLimits_Y0
    initial_equations[avr_firstOrder_y] = (avr_firstOrder_k * avr_UsPu)
    initial_equations[avr_limitedFirstOrder_I_y] = avr_limitedFirstOrder_I_y_start
    initial_equations[avr_pid_D_x] = avr_pid_D_x_start
    initial_equations[avr_pid_I_y] = avr_pid_I_y_start
    initial_equations[avr_EfdPu] = avr_acRotatingExciter_Efd0Pu
    initial_equations[avr_IrPu] = avr_Ir0Pu
    initial_equations[avr_UPssPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UsPu] = avr_Us0Pu
    initial_equations[avr_UsRefPu] = avr_Us0Pu
    initial_equations[avr_acRotatingExciter_VfePu] = avr_acRotatingExciter_Efe0Pu
    initial_equations[avr_acRotatingExciter_division_y] = vf.add_const(0.0, name='')
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y] = vf.add_const(0.0, name='')
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y] = vf.add_const(0.0, name='')
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_y] = avr_acRotatingExciter_integratorVariableLimits_Y0
    initial_equations[avr_acRotatingExciter_rectifierRegulationCharacteristic_y] = vf.add_const(1.0, name='')
    initial_equations[avr_limitedFirstOrder_y] = avr_acRotatingExciter_Efe0Pu
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_isFrozenMax] = avr_acRotatingExciter_integratorVariableLimits_FrozenMax0
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_isFrozenMin] = avr_acRotatingExciter_integratorVariableLimits_FrozenMin0
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_keepFreezingMax] = (sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_w - (avr_acRotatingExciter_firstOrder_y - (avr_acRotatingExciter_integratorVariableLimits_Tol * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0 - avr_acRotatingExciter_integratorVariableLimits_LimitMin0))))) - sym.Const(1e-06))) + sym.heaviside((((avr_acRotatingExciter_integratorVariableLimits_K * avr_acRotatingExciter_feedback_y) - avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMax_y) - sym.Const(1e-06))))
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_keepFreezingMin] = (sym.heaviside((((avr_acRotatingExciter_const1_k + (avr_acRotatingExciter_integratorVariableLimits_Tol * sym.abs((avr_acRotatingExciter_integratorVariableLimits_LimitMax0 - avr_acRotatingExciter_integratorVariableLimits_LimitMin0)))) - avr_acRotatingExciter_integratorVariableLimits_w) - sym.Const(1e-06))) + sym.heaviside(((avr_acRotatingExciter_integratorVariableLimits_derivativeLimitMin_y - (avr_acRotatingExciter_integratorVariableLimits_K * avr_acRotatingExciter_feedback_y)) - sym.Const(1e-06))))
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_startFreezingMax] = avr_acRotatingExciter_integratorVariableLimits_FrozenMax0
    initial_equations[avr_acRotatingExciter_integratorVariableLimits_startFreezingMin] = avr_acRotatingExciter_integratorVariableLimits_FrozenMin0
    initial_equations[avr_pid_I_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_pid_I_local_set] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_lim_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_I_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_I_local_set] = vf.add_const(0.0, name='')
    initial_equations[PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMax] = avr_acRotatingExciter_integratorVariableLimits_FrozenMax0
    initial_equations[PRE_avr_acRotatingExciter_integratorVariableLimits_isFrozenMin] = avr_acRotatingExciter_integratorVariableLimits_FrozenMin0
    initial_equations[avr_acRotatingExciter_add1_y] = ((avr_acRotatingExciter_add1_k1 * avr_acRotatingExciter_const_k) + (avr_acRotatingExciter_add1_k2 * avr_acRotatingExciter_gain1_k))
    initial_equations[avr_acRotatingExciter_add_y] = (avr_acRotatingExciter_add_k1 + (avr_acRotatingExciter_add_k2 * avr_acRotatingExciter_const2_k))
    initial_equations[avr_pid_y] = ((sym.heaviside(((avr_pid_limiter_u - avr_pid_limiter_uMax) - sym.Const(1e-06))) * avr_pid_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_pid_limiter_u - avr_pid_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_pid_limiter_uMin - avr_pid_limiter_u) - sym.Const(1e-06))) * avr_pid_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_pid_limiter_uMin - avr_pid_limiter_u) - sym.Const(1e-06)))) * avr_pid_limiter_u))))
    initial_equations[avr_acRotatingExciter_power_y] = vf.add_const(1.0, name='')
    initial_equations[avr_sum1_u_1] = ((avr_UsRefPu - avr_firstOrder_y) + avr_UPssPu)
    initial_equations[avr_sum1_y] = (avr_sum1_k_1 * avr_sum1_u_1)
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations[d_avr_acRotatingExciter_integratorVariableLimits_w] = (((avr_acRotatingExciter_integratorVariableLimits_isFrozenMax * (avr_acRotatingExciter_integratorVariableLimits_w - avr_acRotatingExciter_firstOrder_y)) + ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMax) * ((avr_acRotatingExciter_integratorVariableLimits_isFrozenMin * (avr_acRotatingExciter_integratorVariableLimits_w - avr_acRotatingExciter_const1_k)) + ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMin) * ((-avr_acRotatingExciter_integratorVariableLimits_K) * avr_acRotatingExciter_feedback_y))))) + ((avr_acRotatingExciter_integratorVariableLimits_isFrozenMax * sym.Const(0.0)) + ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMax) * ((avr_acRotatingExciter_integratorVariableLimits_isFrozenMin * sym.Const(0.0)) + ((sym.Const(1.0) - avr_acRotatingExciter_integratorVariableLimits_isFrozenMin) * sym.Const(1.0))))))
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

    template.comment = 'Generator AVR/exciter IEEE AC8B'
    return template
