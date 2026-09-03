# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Pss6c'.

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

def build_pss6c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'Pss6c'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    pss_Ics1: Var = vf.add_var('pss.Ics1_' + template_name)
    pss_Ics2: Var = vf.add_var('pss.Ics2_' + template_name)
    pss_K0: Var = vf.add_var('pss.K0_' + template_name)
    pss_K1: Var = vf.add_var('pss.K1_' + template_name)
    pss_K2: Var = vf.add_var('pss.K2_' + template_name)
    pss_K3: Var = vf.add_var('pss.K3_' + template_name)
    pss_K4: Var = vf.add_var('pss.K4_' + template_name)
    pss_KOmega: Var = vf.add_var('pss.KOmega_' + template_name)
    pss_KOmegaRef: Var = vf.add_var('pss.KOmegaRef_' + template_name)
    pss_Ki3: Var = vf.add_var('pss.Ki3_' + template_name)
    pss_Ki4: Var = vf.add_var('pss.Ki4_' + template_name)
    pss_Ks: Var = vf.add_var('pss.Ks_' + template_name)
    pss_Ks1: Var = vf.add_var('pss.Ks1_' + template_name)
    pss_Ks2: Var = vf.add_var('pss.Ks2_' + template_name)
    pss_MAcc: Var = vf.add_var('pss.MAcc_' + template_name)
    pss_OmegaMaxPu: Var = vf.add_var('pss.OmegaMaxPu_' + template_name)
    pss_OmegaMinPu: Var = vf.add_var('pss.OmegaMinPu_' + template_name)
    pss_PGen0Pu: Var = vf.add_var('pss.PGen0Pu_' + template_name)
    pss_PGenMaxPu: Var = vf.add_var('pss.PGenMaxPu_' + template_name)
    pss_PGenMinPu: Var = vf.add_var('pss.PGenMinPu_' + template_name)
    pss_PPssOffPu: Var = vf.add_var('pss.PPssOffPu_' + template_name)
    pss_PPssOnPu: Var = vf.add_var('pss.PPssOnPu_' + template_name)
    pss_PSSActivation: Var = vf.add_var('pss.PSSActivation_' + template_name)
    pss_PSSDeactivation: Var = vf.add_var('pss.PSSDeactivation_' + template_name)
    pss_SNom: Var = vf.add_var('pss.SNom_' + template_name)
    pss_Tcomp: Var = vf.add_var('pss.Tcomp_' + template_name)
    pss_Tpgfilt: Var = vf.add_var('pss.Tpgfilt_' + template_name)
    pss_VPssMaxPu: Var = vf.add_var('pss.VPssMaxPu_' + template_name)
    pss_VPssMinPu: Var = vf.add_var('pss.VPssMinPu_' + template_name)
    pss_Xcomp: Var = vf.add_var('pss.Xcomp_' + template_name)
    pss_add_k1: Var = vf.add_var('pss.add.k1_' + template_name)
    pss_add_k2: Var = vf.add_var('pss.add.k2_' + template_name)
    pss_add3_k1: Var = vf.add_var('pss.add3.k1_' + template_name)
    pss_add3_k2: Var = vf.add_var('pss.add3.k2_' + template_name)
    pss_add3_k3: Var = vf.add_var('pss.add3.k3_' + template_name)
    pss_const_k: Var = vf.add_var('pss.const.k_' + template_name)
    pss_derivative_T: Var = vf.add_var('pss.derivative.T_' + template_name)
    pss_derivative_initType: Var = vf.add_var('pss.derivative.initType_' + template_name)
    pss_derivative_k: Var = vf.add_var('pss.derivative.k_' + template_name)
    pss_derivative_x_start: Var = vf.add_var('pss.derivative.x_start_' + template_name)
    pss_derivative_y_start: Var = vf.add_var('pss.derivative.y_start_' + template_name)
    pss_derivative_zeroGain: Var = vf.add_var('pss.derivative.zeroGain_' + template_name)
    pss_firstOrder_T: Var = vf.add_var('pss.firstOrder.T_' + template_name)
    pss_firstOrder_initType: Var = vf.add_var('pss.firstOrder.initType_' + template_name)
    pss_firstOrder_k: Var = vf.add_var('pss.firstOrder.k_' + template_name)
    pss_firstOrder_y_start: Var = vf.add_var('pss.firstOrder.y_start_' + template_name)
    pss_firstOrder1_T: Var = vf.add_var('pss.firstOrder1.T_' + template_name)
    pss_firstOrder1_initType: Var = vf.add_var('pss.firstOrder1.initType_' + template_name)
    pss_firstOrder1_k: Var = vf.add_var('pss.firstOrder1.k_' + template_name)
    pss_firstOrder1_y_start: Var = vf.add_var('pss.firstOrder1.y_start_' + template_name)
    pss_firstOrder2_T: Var = vf.add_var('pss.firstOrder2.T_' + template_name)
    pss_firstOrder2_initType: Var = vf.add_var('pss.firstOrder2.initType_' + template_name)
    pss_firstOrder2_k: Var = vf.add_var('pss.firstOrder2.k_' + template_name)
    pss_firstOrder2_y_start: Var = vf.add_var('pss.firstOrder2.y_start_' + template_name)
    pss_gain_k: Var = vf.add_var('pss.gain.k_' + template_name)
    pss_gain1_k: Var = vf.add_var('pss.gain1.k_' + template_name)
    pss_hysteresis_pre_y_start: Var = vf.add_var('pss.hysteresis.pre_y_start_' + template_name)
    pss_hysteresis_uHigh: Var = vf.add_var('pss.hysteresis.uHigh_' + template_name)
    pss_hysteresis_uLow: Var = vf.add_var('pss.hysteresis.uLow_' + template_name)
    pss_integrator1_initType: Var = vf.add_var('pss.integrator1.initType_' + template_name)
    pss_integrator1_k: Var = vf.add_var('pss.integrator1.k_' + template_name)
    pss_integrator1_use_reset: Var = vf.add_var('pss.integrator1.use_reset_' + template_name)
    pss_integrator1_use_set: Var = vf.add_var('pss.integrator1.use_set_' + template_name)
    pss_integrator1_y_start: Var = vf.add_var('pss.integrator1.y_start_' + template_name)
    pss_integrator2_initType: Var = vf.add_var('pss.integrator2.initType_' + template_name)
    pss_integrator2_k: Var = vf.add_var('pss.integrator2.k_' + template_name)
    pss_integrator2_use_reset: Var = vf.add_var('pss.integrator2.use_reset_' + template_name)
    pss_integrator2_use_set: Var = vf.add_var('pss.integrator2.use_set_' + template_name)
    pss_integrator2_y_start: Var = vf.add_var('pss.integrator2.y_start_' + template_name)
    pss_integrator3_initType: Var = vf.add_var('pss.integrator3.initType_' + template_name)
    pss_integrator3_k: Var = vf.add_var('pss.integrator3.k_' + template_name)
    pss_integrator3_use_reset: Var = vf.add_var('pss.integrator3.use_reset_' + template_name)
    pss_integrator3_use_set: Var = vf.add_var('pss.integrator3.use_set_' + template_name)
    pss_integrator3_y_start: Var = vf.add_var('pss.integrator3.y_start_' + template_name)
    pss_integrator4_initType: Var = vf.add_var('pss.integrator4.initType_' + template_name)
    pss_integrator4_k: Var = vf.add_var('pss.integrator4.k_' + template_name)
    pss_integrator4_use_reset: Var = vf.add_var('pss.integrator4.use_reset_' + template_name)
    pss_integrator4_use_set: Var = vf.add_var('pss.integrator4.use_set_' + template_name)
    pss_integrator4_y_start: Var = vf.add_var('pss.integrator4.y_start_' + template_name)
    pss_limiter_homotopyType: Var = vf.add_var('pss.limiter.homotopyType_' + template_name)
    pss_limiter_limitsAtInit: Var = vf.add_var('pss.limiter.limitsAtInit_' + template_name)
    pss_limiter_strict: Var = vf.add_var('pss.limiter.strict_' + template_name)
    pss_limiter_uMax: Var = vf.add_var('pss.limiter.uMax_' + template_name)
    pss_limiter_uMin: Var = vf.add_var('pss.limiter.uMin_' + template_name)
    pss_limiter1_homotopyType: Var = vf.add_var('pss.limiter1.homotopyType_' + template_name)
    pss_limiter1_limitsAtInit: Var = vf.add_var('pss.limiter1.limitsAtInit_' + template_name)
    pss_limiter1_strict: Var = vf.add_var('pss.limiter1.strict_' + template_name)
    pss_limiter1_uMax: Var = vf.add_var('pss.limiter1.uMax_' + template_name)
    pss_limiter1_uMin: Var = vf.add_var('pss.limiter1.uMin_' + template_name)
    pss_limiter2_homotopyType: Var = vf.add_var('pss.limiter2.homotopyType_' + template_name)
    pss_limiter2_limitsAtInit: Var = vf.add_var('pss.limiter2.limitsAtInit_' + template_name)
    pss_limiter2_strict: Var = vf.add_var('pss.limiter2.strict_' + template_name)
    pss_limiter2_uMax: Var = vf.add_var('pss.limiter2.uMax_' + template_name)
    pss_limiter2_uMin: Var = vf.add_var('pss.limiter2.uMin_' + template_name)
    pss_sum1_k_1: Var = vf.add_var('pss.sum1.k[1]_' + template_name)
    pss_sum1_k_2: Var = vf.add_var('pss.sum1.k[2]_' + template_name)
    pss_sum1_k_3: Var = vf.add_var('pss.sum1.k[3]_' + template_name)
    pss_sum1_k_4: Var = vf.add_var('pss.sum1.k[4]_' + template_name)
    pss_sum1_k_5: Var = vf.add_var('pss.sum1.k[5]_' + template_name)
    pss_sum1_nin: Var = vf.add_var('pss.sum1.nin_' + template_name)
    pss_sum2_k_1: Var = vf.add_var('pss.sum2.k[1]_' + template_name)
    pss_sum2_k_2: Var = vf.add_var('pss.sum2.k[2]_' + template_name)
    pss_sum2_k_3: Var = vf.add_var('pss.sum2.k[3]_' + template_name)
    pss_sum2_k_4: Var = vf.add_var('pss.sum2.k[4]_' + template_name)
    pss_sum2_nin: Var = vf.add_var('pss.sum2.nin_' + template_name)
    pss_t1: Var = vf.add_var('pss.t1_' + template_name)
    pss_t2: Var = vf.add_var('pss.t2_' + template_name)
    pss_t3: Var = vf.add_var('pss.t3_' + template_name)
    pss_t4: Var = vf.add_var('pss.t4_' + template_name)
    pss_tD: Var = vf.add_var('pss.tD_' + template_name)
    pss_tI1: Var = vf.add_var('pss.tI1_' + template_name)
    pss_tI2: Var = vf.add_var('pss.tI2_' + template_name)
    pss_tI3: Var = vf.add_var('pss.tI3_' + template_name)
    pss_tI4: Var = vf.add_var('pss.tI4_' + template_name)
    pss_washout_U0: Var = vf.add_var('pss.washout.U0_' + template_name)
    pss_washout_derivative_T: Var = vf.add_var('pss.washout.derivative.T_' + template_name)
    pss_washout_derivative_initType: Var = vf.add_var('pss.washout.derivative.initType_' + template_name)
    pss_washout_derivative_k: Var = vf.add_var('pss.washout.derivative.k_' + template_name)
    pss_washout_derivative_x_start: Var = vf.add_var('pss.washout.derivative.x_start_' + template_name)
    pss_washout_derivative_y_start: Var = vf.add_var('pss.washout.derivative.y_start_' + template_name)
    pss_washout_derivative_zeroGain: Var = vf.add_var('pss.washout.derivative.zeroGain_' + template_name)
    pss_washout_tW: Var = vf.add_var('pss.washout.tW_' + template_name)
    # Declare the state variables used by the template.
    pss_compFreqFilter_y: Var = vf.add_var('pss.compFreqFilter.y_' + template_name)
    pss_derivative_x: Var = vf.add_var('pss.derivative.x_' + template_name)
    pss_firstOrder_y: Var = vf.add_var('pss.firstOrder.y_' + template_name)
    pss_firstOrder1_y: Var = vf.add_var('pss.firstOrder1.y_' + template_name)
    pss_firstOrder2_y: Var = vf.add_var('pss.firstOrder2.y_' + template_name)
    pss_integrator1_y: Var = vf.add_var('pss.integrator1.y_' + template_name)
    pss_integrator2_y: Var = vf.add_var('pss.integrator2.y_' + template_name)
    pss_integrator3_y: Var = vf.add_var('pss.integrator3.y_' + template_name)
    pss_integrator4_y: Var = vf.add_var('pss.integrator4.y_' + template_name)
    pss_pGenFilter_y: Var = vf.add_var('pss.pGenFilter.y_' + template_name)
    pss_washout_derivative_x: Var = vf.add_var('pss.washout.derivative.x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_pss_hysteresis_y: Var = vf.add_var('$PRE.pss.hysteresis.y_' + template_name)
    START_pss_derivative_x: Var = vf.add_var('$START.pss.derivative.x_' + template_name)
    START_pss_firstOrder_y: Var = vf.add_var('$START.pss.firstOrder.y_' + template_name)
    START_pss_firstOrder1_y: Var = vf.add_var('$START.pss.firstOrder1.y_' + template_name)
    START_pss_firstOrder2_y: Var = vf.add_var('$START.pss.firstOrder2.y_' + template_name)
    START_pss_washout_derivative_x: Var = vf.add_var('$START.pss.washout.derivative.x_' + template_name)
    pss_PAccelPu: Var = vf.add_var('pss.PAccelPu_' + template_name)
    pss_PGenPu: Var = vf.add_var('pss.PGenPu_' + template_name)
    pss_VBusPu: Var = vf.add_var('pss.VBusPu_' + template_name)
    pss_VPssPu: Var = vf.add_var('pss.VPssPu_' + template_name)
    pss_add_y: Var = vf.add_var('pss.add.y_' + template_name)
    pss_add3_y: Var = vf.add_var('pss.add3.y_' + template_name)
    pss_busFreqPu: Var = vf.add_var('pss.busFreqPu_' + template_name)
    pss_compFreqPu: Var = vf.add_var('pss.compFreqPu_' + template_name)
    pss_dVBusPu: Var = vf.add_var('pss.dVBusPu_' + template_name)
    pss_derivative_y: Var = vf.add_var('pss.derivative.y_' + template_name)
    pss_gain_y: Var = vf.add_var('pss.gain.y_' + template_name)
    pss_gain1_y: Var = vf.add_var('pss.gain1.y_' + template_name)
    pss_hysteresis_y: Var = vf.add_var('pss.hysteresis.y_' + template_name)
    pss_integrator1_local_reset: Var = vf.add_var('pss.integrator1.local_reset_' + template_name)
    pss_integrator1_local_set: Var = vf.add_var('pss.integrator1.local_set_' + template_name)
    pss_integrator2_local_reset: Var = vf.add_var('pss.integrator2.local_reset_' + template_name)
    pss_integrator2_local_set: Var = vf.add_var('pss.integrator2.local_set_' + template_name)
    pss_integrator3_local_reset: Var = vf.add_var('pss.integrator3.local_reset_' + template_name)
    pss_integrator3_local_set: Var = vf.add_var('pss.integrator3.local_set_' + template_name)
    pss_integrator4_local_reset: Var = vf.add_var('pss.integrator4.local_reset_' + template_name)
    pss_integrator4_local_set: Var = vf.add_var('pss.integrator4.local_set_' + template_name)
    pss_limiter_simplifiedExpr: Var = vf.add_var('pss.limiter.simplifiedExpr_' + template_name)
    pss_limiter_y: Var = vf.add_var('pss.limiter.y_' + template_name)
    pss_limiter1_simplifiedExpr: Var = vf.add_var('pss.limiter1.simplifiedExpr_' + template_name)
    pss_limiter1_y: Var = vf.add_var('pss.limiter1.y_' + template_name)
    pss_limiter2_simplifiedExpr: Var = vf.add_var('pss.limiter2.simplifiedExpr_' + template_name)
    pss_limiter2_y: Var = vf.add_var('pss.limiter2.y_' + template_name)
    pss_omegaPu: Var = vf.add_var('pss.omegaPu_' + template_name)
    pss_omegaRefPu: Var = vf.add_var('pss.omegaRefPu_' + template_name)
    pss_pGenFiltPu: Var = vf.add_var('pss.pGenFiltPu_' + template_name)
    pss_sum1_u_5: Var = vf.add_var('pss.sum1.u[5]_' + template_name)
    pss_sum1_y: Var = vf.add_var('pss.sum1.y_' + template_name)
    pss_sum2_y: Var = vf.add_var('pss.sum2.y_' + template_name)
    pss_washout_y: Var = vf.add_var('pss.washout.y_' + template_name)
    # Declare the differential variables used by the template.
    d_pss_compFreqFilter_y: Var = vf.add_diff_var('d_pss.compFreqFilter.y_' + template_name, base_var=pss_compFreqFilter_y)
    d_pss_derivative_x: Var = vf.add_diff_var('d_pss.derivative.x_' + template_name, base_var=pss_derivative_x)
    d_pss_firstOrder_y: Var = vf.add_diff_var('d_pss.firstOrder.y_' + template_name, base_var=pss_firstOrder_y)
    d_pss_firstOrder1_y: Var = vf.add_diff_var('d_pss.firstOrder1.y_' + template_name, base_var=pss_firstOrder1_y)
    d_pss_firstOrder2_y: Var = vf.add_diff_var('d_pss.firstOrder2.y_' + template_name, base_var=pss_firstOrder2_y)
    d_pss_integrator1_y: Var = vf.add_diff_var('d_pss.integrator1.y_' + template_name, base_var=pss_integrator1_y)
    d_pss_integrator2_y: Var = vf.add_diff_var('d_pss.integrator2.y_' + template_name, base_var=pss_integrator2_y)
    d_pss_integrator3_y: Var = vf.add_diff_var('d_pss.integrator3.y_' + template_name, base_var=pss_integrator3_y)
    d_pss_integrator4_y: Var = vf.add_diff_var('d_pss.integrator4.y_' + template_name, base_var=pss_integrator4_y)
    d_pss_pGenFilter_y: Var = vf.add_diff_var('d_pss.pGenFilter.y_' + template_name, base_var=pss_pGenFilter_y)
    d_pss_washout_derivative_x: Var = vf.add_diff_var('d_pss.washout.derivative.x_' + template_name, base_var=pss_washout_derivative_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((pss_integrator4_k * pss_integrator3_y))
    state_equations.append((pss_integrator3_k * pss_integrator2_y))
    state_equations.append((pss_integrator2_k * pss_integrator1_y))
    state_equations.append(((pss_washout_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout_derivative_zeroGain) * ((pss_add3_y - pss_washout_derivative_x) / pss_washout_derivative_T))))
    state_equations.append((pss_integrator1_k * pss_sum1_u_5))
    state_equations.append(((pss_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_derivative_zeroGain) * ((pss_firstOrder2_y - pss_derivative_x) / pss_derivative_T))))
    state_equations.append((((pss_firstOrder2_k * pss_limiter1_y) - pss_firstOrder2_y) / pss_firstOrder2_T))
    state_equations.append((((pss_firstOrder1_k * pss_firstOrder_y) - pss_firstOrder1_y) / pss_firstOrder1_T))
    state_equations.append((((pss_firstOrder_k * pss_limiter_y) - pss_firstOrder_y) / pss_firstOrder_T))
    state_equations.append(((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * (((pss_gain_k * pss_PGenPu) - pss_pGenFilter_y) / ((pss_Tpgfilt * sym.heaviside((pss_Tpgfilt - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside((pss_Tpgfilt - sym.Const(1e-12)))))))))
    state_equations.append(((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tcomp) + sym.Const(1e-06)))) * (((pss_busFreqPu + (pss_Xcomp * pss_dVBusPu)) - pss_compFreqFilter_y) / ((pss_Tcomp * sym.heaviside((pss_Tcomp - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside((pss_Tcomp - sym.Const(1e-12)))))))))
    state_variables: list[Var] = list()
    state_variables.append(pss_integrator4_y)
    state_variables.append(pss_integrator3_y)
    state_variables.append(pss_integrator2_y)
    state_variables.append(pss_washout_derivative_x)
    state_variables.append(pss_integrator1_y)
    state_variables.append(pss_derivative_x)
    state_variables.append(pss_firstOrder2_y)
    state_variables.append(pss_firstOrder1_y)
    state_variables.append(pss_firstOrder_y)
    state_variables.append(pss_pGenFilter_y)
    state_variables.append(pss_compFreqFilter_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((pss_limiter_y - ((sym.heaviside(((pss_gain_y - pss_limiter_uMax) - sym.Const(1e-06))) * pss_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((pss_gain_y - pss_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((pss_limiter_uMin - pss_gain_y) - sym.Const(1e-06))) * pss_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((pss_limiter_uMin - pss_gain_y) - sym.Const(1e-06)))) * pss_gain_y))))))
    algebraic_equations.append((pss_limiter1_y - ((sym.heaviside(((pss_add_y - pss_limiter1_uMax) - sym.Const(1e-06))) * pss_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((pss_add_y - pss_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((pss_limiter1_uMin - pss_add_y) - sym.Const(1e-06))) * pss_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((pss_limiter1_uMin - pss_add_y) - sym.Const(1e-06)))) * pss_add_y))))))
    algebraic_equations.append((pss_hysteresis_y - ((sym.Const(0.0) + ((((((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y)) - pss_PSSDeactivation) / (((pss_PSSActivation - pss_PSSDeactivation) * sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12))))))) - sym.Const(0.0)) * sym.heaviside((((((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y)) - pss_PSSDeactivation) / (((pss_PSSActivation - pss_PSSDeactivation) * sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12))))))) - sym.Const(0.0))))) - ((((((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y)) - pss_PSSDeactivation) / (((pss_PSSActivation - pss_PSSDeactivation) * sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12))))))) - sym.Const(1.0)) * sym.heaviside((((((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y)) - pss_PSSDeactivation) / (((pss_PSSActivation - pss_PSSDeactivation) * sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12))))))) - sym.Const(1.0)))))))
    algebraic_equations.append((pss_sum2_y - ((pss_sum2_k_1 * pss_integrator1_y) + ((pss_sum2_k_2 * pss_integrator2_y) + ((pss_sum2_k_3 * pss_integrator3_y) + (pss_sum2_k_4 * pss_integrator4_y))))))
    algebraic_equations.append((pss_derivative_y - ((pss_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_derivative_zeroGain) * ((pss_derivative_k / pss_derivative_T) * (pss_firstOrder2_y - pss_derivative_x))))))
    algebraic_equations.append((pss_add3_y - ((pss_add3_k1 * pss_firstOrder1_y) + ((pss_add3_k2 * pss_firstOrder_y) + (pss_add3_k3 * pss_derivative_y)))))
    algebraic_equations.append((pss_washout_y - ((pss_washout_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout_derivative_zeroGain) * ((pss_washout_derivative_k / pss_washout_derivative_T) * (pss_add3_y - pss_washout_derivative_x))))))
    algebraic_equations.append((pss_sum1_u_5 - (pss_washout_y - pss_sum2_y)))
    algebraic_equations.append((pss_sum1_y - ((pss_sum1_k_1 * pss_integrator1_y) + ((pss_sum1_k_2 * pss_integrator2_y) + ((pss_sum1_k_3 * pss_integrator3_y) + ((pss_sum1_k_4 * pss_integrator4_y) + (pss_sum1_k_5 * pss_sum1_u_5)))))))
    algebraic_equations.append((pss_gain1_y - (pss_gain1_k * pss_sum1_y)))
    algebraic_equations.append((pss_limiter2_y - ((sym.heaviside(((pss_gain1_y - pss_limiter2_uMax) - sym.Const(1e-06))) * pss_limiter2_uMax) + ((sym.Const(1.0) - sym.heaviside(((pss_gain1_y - pss_limiter2_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((pss_limiter2_uMin - pss_gain1_y) - sym.Const(1e-06))) * pss_limiter2_uMin) + ((sym.Const(1.0) - sym.heaviside(((pss_limiter2_uMin - pss_gain1_y) - sym.Const(1e-06)))) * pss_gain1_y))))))
    algebraic_equations.append((pss_VPssPu - ((pss_hysteresis_y * pss_limiter2_y) + ((sym.Const(1.0) - pss_hysteresis_y) * pss_const_k))))
    algebraic_equations.append((pss_pGenFiltPu - ((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y))))
    algebraic_equations.append((pss_compFreqPu - ((sym.heaviside(((sym.Const(1e-12) - pss_Tcomp) + sym.Const(1e-06))) * (pss_busFreqPu + (pss_Xcomp * pss_dVBusPu))) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tcomp) + sym.Const(1e-06)))) * pss_compFreqFilter_y))))
    algebraic_equations.append((pss_add_y - (((((((sym.Const(0.0) + ((sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06)))) * ((pss_add_k1 * pss_omegaPu) + (pss_add_k2 * pss_omegaRefPu)))) + ((sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06)))) * pss_busFreqPu)) + ((sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06)))) * (pss_gain_k * pss_PGenPu))) + ((sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06)))) * pss_PAccelPu)) + ((sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06)))) * pss_VBusPu)) + ((sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06)))) * pss_dVBusPu)) + ((sym.Const(1.0) - ((sym.Const(0.0) + ((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06))))) - sym.Const(0.0)) * sym.heaviside((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06))))) - sym.Const(0.0))))) - ((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06))))) - sym.Const(1.0)) * sym.heaviside((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06))))) - sym.Const(1.0)))))) * ((pss_add_k1 * pss_omegaPu) + (pss_add_k2 * pss_omegaRefPu))))))
    algebraic_equations.append((pss_gain_y - ((((((((sym.Const(0.0) + ((sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06)))) * ((pss_add_k1 * pss_omegaPu) + (pss_add_k2 * pss_omegaRefPu)))) + ((sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_busFreqPu)) + ((sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06)))) * (pss_gain_k * pss_PGenPu))) + ((sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_PAccelPu)) + ((sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_VBusPu)) + ((sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_dVBusPu)) + ((sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_compFreqPu)) + ((sym.Const(1.0) - ((sym.Const(0.0) + (((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06))))) - sym.Const(0.0)) * sym.heaviside(((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06))))) - sym.Const(0.0))))) - (((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06))))) - sym.Const(1.0)) * sym.heaviside(((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06))))) - sym.Const(1.0)))))) * (pss_gain_k * pss_PGenPu)))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(pss_limiter_y)
    algebraic_variables.append(pss_limiter1_y)
    algebraic_variables.append(pss_hysteresis_y)
    algebraic_variables.append(pss_sum2_y)
    algebraic_variables.append(pss_derivative_y)
    algebraic_variables.append(pss_add3_y)
    algebraic_variables.append(pss_washout_y)
    algebraic_variables.append(pss_sum1_u_5)
    algebraic_variables.append(pss_sum1_y)
    algebraic_variables.append(pss_gain1_y)
    algebraic_variables.append(pss_limiter2_y)
    algebraic_variables.append(pss_VPssPu)
    algebraic_variables.append(pss_gain_y)
    algebraic_variables.append(pss_add_y)
    algebraic_variables.append(pss_PGenPu)
    algebraic_variables.append(pss_omegaPu)
    algebraic_variables.append(pss_omegaRefPu)
    algebraic_variables.append(pss_limiter_simplifiedExpr)
    algebraic_variables.append(pss_limiter1_simplifiedExpr)
    algebraic_variables.append(pss_integrator1_local_reset)
    algebraic_variables.append(pss_integrator1_local_set)
    algebraic_variables.append(pss_integrator2_local_reset)
    algebraic_variables.append(pss_integrator2_local_set)
    algebraic_variables.append(pss_integrator3_local_reset)
    algebraic_variables.append(pss_integrator3_local_set)
    algebraic_variables.append(pss_integrator4_local_reset)
    algebraic_variables.append(pss_integrator4_local_set)
    algebraic_variables.append(pss_limiter2_simplifiedExpr)
    algebraic_variables.append(START_pss_firstOrder_y)
    algebraic_variables.append(START_pss_firstOrder1_y)
    algebraic_variables.append(START_pss_firstOrder2_y)
    algebraic_variables.append(START_pss_derivative_x)
    algebraic_variables.append(START_pss_washout_derivative_x)
    algebraic_variables.append(PRE_pss_hysteresis_y)
    algebraic_variables.append(pss_busFreqPu)
    algebraic_variables.append(pss_VBusPu)
    algebraic_variables.append(pss_dVBusPu)
    algebraic_variables.append(pss_PAccelPu)
    algebraic_variables.append(pss_pGenFiltPu)
    algebraic_variables.append(pss_compFreqPu)
    differential_variables: list[Var] = list()
    differential_variables.append(d_pss_integrator4_y)
    differential_variables.append(d_pss_integrator3_y)
    differential_variables.append(d_pss_integrator2_y)
    differential_variables.append(d_pss_washout_derivative_x)
    differential_variables.append(d_pss_integrator1_y)
    differential_variables.append(d_pss_derivative_x)
    differential_variables.append(d_pss_firstOrder2_y)
    differential_variables.append(d_pss_firstOrder1_y)
    differential_variables.append(d_pss_firstOrder_y)
    differential_variables.append(d_pss_pGenFilter_y)
    differential_variables.append(d_pss_compFreqFilter_y)
    input_variables: list[Var] = list()
    input_variables.append(pss_PGenPu)
    input_variables.append(pss_omegaPu)
    input_variables.append(pss_omegaRefPu)
    input_variables.append(pss_busFreqPu)
    input_variables.append(pss_VBusPu)
    input_variables.append(pss_dVBusPu)
    input_variables.append(pss_PAccelPu)
    output_variables: list[Var] = list()
    output_variables.append(pss_VPssPu)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[pss_K0] = vf.add_const(1.0, name='')
    event_parameters[pss_K1] = vf.add_const(1.0, name='')
    event_parameters[pss_K2] = vf.add_const(1.0, name='')
    event_parameters[pss_K3] = vf.add_const(1.0, name='')
    event_parameters[pss_K4] = vf.add_const(1.0, name='')
    event_parameters[pss_KOmega] = vf.add_const(1.0, name='')
    event_parameters[pss_KOmegaRef] = vf.add_const(0.0, name='')
    event_parameters[pss_Ki3] = vf.add_const(1.0, name='')
    event_parameters[pss_Ki4] = vf.add_const(1.0, name='')
    event_parameters[pss_Ks] = vf.add_const(10.0, name='')
    event_parameters[pss_Ks1] = vf.add_const(1.0, name='')
    event_parameters[pss_Ks2] = vf.add_const(1.0, name='')
    event_parameters[pss_MAcc] = vf.add_const(1.0, name='')
    event_parameters[pss_OmegaMaxPu] = vf.add_const(1.1, name='')
    event_parameters[pss_OmegaMinPu] = vf.add_const(0.9, name='')
    event_parameters[pss_PGen0Pu] = vf.add_const(0.8, name='')
    event_parameters[pss_PGenMaxPu] = vf.add_const(1.0, name='')
    event_parameters[pss_PGenMinPu] = vf.add_const(0.0, name='')
    event_parameters[pss_PPssOffPu] = vf.add_const(0.05, name='')
    event_parameters[pss_PPssOnPu] = vf.add_const(0.1, name='')
    event_parameters[pss_SNom] = vf.add_const(100.0, name='')
    event_parameters[pss_VPssMaxPu] = vf.add_const(0.1, name='')
    event_parameters[pss_VPssMinPu] = vf.add_const(-0.1, name='')
    event_parameters[pss_add_k1] = pss_KOmega
    event_parameters[pss_add_k2] = pss_KOmegaRef
    event_parameters[pss_add3_k1] = vf.add_const(1.0, name='')
    event_parameters[pss_add3_k2] = vf.add_const(-1.0, name='')
    event_parameters[pss_add3_k3] = vf.add_const(1.0, name='')
    event_parameters[pss_const_k] = vf.add_const(0.0, name='')
    event_parameters[pss_derivative_T] = pss_t4
    event_parameters[pss_derivative_k] = pss_MAcc
    event_parameters[pss_derivative_x_start] = (pss_Ks2 * (pss_KOmega + pss_KOmegaRef))
    event_parameters[pss_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_firstOrder_T] = pss_t1
    event_parameters[pss_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[pss_firstOrder_y_start] = (sym.Const(100.0) * (pss_PGen0Pu / pss_SNom))
    event_parameters[pss_firstOrder1_T] = pss_t3
    event_parameters[pss_firstOrder1_k] = pss_Ks1
    event_parameters[pss_firstOrder1_y_start] = (sym.Const(100.0) * (pss_Ks1 * (pss_PGen0Pu / pss_SNom)))
    event_parameters[pss_firstOrder2_T] = pss_t2
    event_parameters[pss_firstOrder2_k] = pss_Ks2
    event_parameters[pss_firstOrder2_y_start] = (pss_Ks2 * (pss_KOmega + pss_KOmegaRef))
    event_parameters[pss_gain_k] = (sym.Const(100.0) / pss_SNom)
    event_parameters[pss_gain1_k] = pss_Ks
    event_parameters[pss_hysteresis_uHigh] = pss_PPssOnPu
    event_parameters[pss_hysteresis_uLow] = pss_PPssOffPu
    event_parameters[pss_integrator1_k] = (sym.Const(1.0) / pss_tI1)
    event_parameters[pss_integrator1_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator2_k] = (sym.Const(1.0) / pss_tI2)
    event_parameters[pss_integrator2_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator3_k] = (pss_Ki3 / pss_tI3)
    event_parameters[pss_integrator3_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator4_k] = (pss_Ki4 / pss_tI4)
    event_parameters[pss_integrator4_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_limiter_uMax] = pss_PGenMaxPu
    event_parameters[pss_limiter_uMin] = pss_PGenMinPu
    event_parameters[pss_limiter1_uMax] = pss_OmegaMaxPu
    event_parameters[pss_limiter1_uMin] = pss_OmegaMinPu
    event_parameters[pss_limiter2_uMax] = pss_VPssMaxPu
    event_parameters[pss_limiter2_uMin] = pss_VPssMinPu
    event_parameters[pss_sum1_k_1] = pss_K1
    event_parameters[pss_sum1_k_2] = pss_K2
    event_parameters[pss_sum1_k_3] = pss_K3
    event_parameters[pss_sum1_k_4] = pss_K4
    event_parameters[pss_sum1_k_5] = pss_K0
    event_parameters[pss_sum2_k_1] = vf.add_const(1.0, name='')
    event_parameters[pss_sum2_k_2] = vf.add_const(1.0, name='')
    event_parameters[pss_sum2_k_3] = vf.add_const(1.0, name='')
    event_parameters[pss_sum2_k_4] = vf.add_const(1.0, name='')
    event_parameters[pss_t1] = vf.add_const(0.02, name='')
    event_parameters[pss_t2] = vf.add_const(0.02, name='')
    event_parameters[pss_t3] = vf.add_const(0.1, name='')
    event_parameters[pss_t4] = vf.add_const(0.02, name='')
    event_parameters[pss_tD] = vf.add_const(10.0, name='')
    event_parameters[pss_tI1] = vf.add_const(1.0, name='')
    event_parameters[pss_tI2] = vf.add_const(1.0, name='')
    event_parameters[pss_tI3] = vf.add_const(1.0, name='')
    event_parameters[pss_tI4] = vf.add_const(1.0, name='')
    event_parameters[pss_washout_U0] = (sym.Const(100.0) * ((sym.Const(-1.0) + pss_Ks1) * (pss_PGen0Pu / pss_SNom)))
    event_parameters[pss_washout_derivative_T] = vf.add_const(10.0, name='')
    event_parameters[pss_washout_derivative_k] = vf.add_const(10.0, name='')
    event_parameters[pss_washout_derivative_x_start] = pss_washout_U0
    event_parameters[pss_washout_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_firstOrder1_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_firstOrder2_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_integrator1_initType] = vf.add_const(3.0, name='')
    event_parameters[pss_integrator2_initType] = vf.add_const(3.0, name='')
    event_parameters[pss_integrator3_initType] = vf.add_const(3.0, name='')
    event_parameters[pss_integrator4_initType] = vf.add_const(3.0, name='')
    event_parameters[pss_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter2_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[pss_sum1_nin] = vf.add_const(5.0, name='')
    event_parameters[pss_sum2_nin] = vf.add_const(4.0, name='')
    event_parameters[pss_washout_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_derivative_k)) - sym.Const(1e-06)))
    event_parameters[pss_hysteresis_pre_y_start] = sym.heaviside((((pss_gain_k * pss_PGen0Pu) - pss_PSSDeactivation) - sym.Const(1e-06)))
    event_parameters[pss_integrator1_use_reset] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator1_use_set] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator2_use_reset] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator2_use_set] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator3_use_reset] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator3_use_set] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator4_use_reset] = vf.add_const(0.0, name='')
    event_parameters[pss_integrator4_use_set] = vf.add_const(0.0, name='')
    event_parameters[pss_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[pss_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[pss_limiter2_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter2_strict] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_washout_derivative_k)) - sym.Const(1e-06)))
    event_parameters[pss_Ics1] = vf.add_const(3.0, name='')
    event_parameters[pss_Ics2] = vf.add_const(1.0, name='')
    event_parameters[pss_PSSActivation] = pss_PPssOnPu
    event_parameters[pss_PSSDeactivation] = pss_PPssOffPu
    event_parameters[pss_Tpgfilt] = vf.add_const(0.0, name='')
    event_parameters[pss_Xcomp] = vf.add_const(0.0, name='')
    event_parameters[pss_Tcomp] = pss_MAcc
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[pss_derivative_x] = pss_derivative_x_start
    initial_equations[pss_firstOrder_y] = (pss_gain_k * pss_PGenPu)
    initial_equations[pss_firstOrder1_y] = (pss_Ks1 * (pss_gain_k * pss_PGenPu))
    initial_equations[pss_firstOrder2_y] = pss_firstOrder2_y_start
    initial_equations[pss_integrator1_y] = pss_integrator1_y_start
    initial_equations[pss_integrator2_y] = pss_integrator2_y_start
    initial_equations[pss_integrator3_y] = pss_integrator3_y_start
    initial_equations[pss_integrator4_y] = pss_integrator4_y_start
    initial_equations[pss_washout_derivative_x] = pss_washout_derivative_x_start
    initial_equations[pss_PGenPu] = pss_PGen0Pu
    initial_equations[pss_VPssPu] = ((pss_hysteresis_y * pss_limiter2_y) + ((sym.Const(1.0) - pss_hysteresis_y) * pss_const_k))
    initial_equations[pss_add3_y] = pss_washout_U0
    initial_equations[pss_limiter2_y] = ((pss_limiter2_uMin + ((pss_gain1_y - pss_limiter2_uMin) * sym.heaviside((pss_gain1_y - pss_limiter2_uMin)))) - ((pss_gain1_y - pss_limiter2_uMax) * sym.heaviside((pss_gain1_y - pss_limiter2_uMax))))
    initial_equations[pss_omegaPu] = vf.add_const(1.0, name='')
    initial_equations[pss_omegaRefPu] = vf.add_const(1.0, name='')
    initial_equations[pss_washout_y] = vf.add_const(0.0, name='')
    initial_equations[pss_hysteresis_y] = ((sym.Const(0.0) + ((((((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y)) - pss_PSSDeactivation) / (((pss_PSSActivation - pss_PSSDeactivation) * sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12))))))) - sym.Const(0.0)) * sym.heaviside((((((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y)) - pss_PSSDeactivation) / (((pss_PSSActivation - pss_PSSDeactivation) * sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12))))))) - sym.Const(0.0))))) - ((((((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y)) - pss_PSSDeactivation) / (((pss_PSSActivation - pss_PSSDeactivation) * sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12))))))) - sym.Const(1.0)) * sym.heaviside((((((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y)) - pss_PSSDeactivation) / (((pss_PSSActivation - pss_PSSDeactivation) * sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside(((pss_PSSActivation - pss_PSSDeactivation) - sym.Const(1e-12))))))) - sym.Const(1.0)))))
    initial_equations[pss_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[pss_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[pss_integrator1_local_reset] = vf.add_const(0.0, name='')
    initial_equations[pss_integrator1_local_set] = vf.add_const(0.0, name='')
    initial_equations[pss_integrator2_local_reset] = vf.add_const(0.0, name='')
    initial_equations[pss_integrator2_local_set] = vf.add_const(0.0, name='')
    initial_equations[pss_integrator3_local_reset] = vf.add_const(0.0, name='')
    initial_equations[pss_integrator3_local_set] = vf.add_const(0.0, name='')
    initial_equations[pss_integrator4_local_reset] = vf.add_const(0.0, name='')
    initial_equations[pss_integrator4_local_set] = vf.add_const(0.0, name='')
    initial_equations[pss_limiter2_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[pss_add_y] = (((((((sym.Const(0.0) + ((sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06)))) * ((pss_add_k1 * pss_omegaPu) + (pss_add_k2 * pss_omegaRefPu)))) + ((sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06)))) * pss_busFreqPu)) + ((sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06)))) * (pss_gain_k * pss_PGenPu))) + ((sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06)))) * pss_PAccelPu)) + ((sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06)))) * pss_VBusPu)) + ((sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06)))) * pss_dVBusPu)) + ((sym.Const(1.0) - ((sym.Const(0.0) + ((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06))))) - sym.Const(0.0)) * sym.heaviside((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06))))) - sym.Const(0.0))))) - ((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06))))) - sym.Const(1.0)) * sym.heaviside((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics2 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics2) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics2 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics2) + sym.Const(1e-06))))) - sym.Const(1.0)))))) * ((pss_add_k1 * pss_omegaPu) + (pss_add_k2 * pss_omegaRefPu))))
    initial_equations[pss_gain_y] = ((((((((sym.Const(0.0) + ((sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06)))) * ((pss_add_k1 * pss_omegaPu) + (pss_add_k2 * pss_omegaRefPu)))) + ((sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_busFreqPu)) + ((sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06)))) * (pss_gain_k * pss_PGenPu))) + ((sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_PAccelPu)) + ((sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_VBusPu)) + ((sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_dVBusPu)) + ((sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06)))) * pss_compFreqPu)) + ((sym.Const(1.0) - ((sym.Const(0.0) + (((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06))))) - sym.Const(0.0)) * sym.heaviside(((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06))))) - sym.Const(0.0))))) - (((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06))))) - sym.Const(1.0)) * sym.heaviside(((((((((sym.Const(0.0) + (sym.heaviside(((pss_Ics1 - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(2.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(2.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(3.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(3.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(4.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(4.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(5.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(5.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(6.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(6.0) - pss_Ics1) + sym.Const(1e-06))))) + (sym.heaviside(((pss_Ics1 - sym.Const(7.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(7.0) - pss_Ics1) + sym.Const(1e-06))))) - sym.Const(1.0)))))) * (pss_gain_k * pss_PGenPu)))
    initial_equations[PRE_pss_hysteresis_y] = pss_hysteresis_pre_y_start
    initial_equations[pss_busFreqPu] = ((pss_add_k1 * pss_omegaPu) + (pss_add_k2 * pss_omegaRefPu))
    initial_equations[pss_VBusPu] = vf.add_const(1.0, name='')
    initial_equations[pss_dVBusPu] = vf.add_const(0.0, name='')
    initial_equations[pss_PAccelPu] = vf.add_const(0.0, name='')
    initial_equations[pss_pGenFiltPu] = ((sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06))) * (pss_gain_k * pss_PGenPu)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tpgfilt) + sym.Const(1e-06)))) * pss_pGenFilter_y))
    initial_equations[pss_compFreqPu] = ((sym.heaviside(((sym.Const(1e-12) - pss_Tcomp) + sym.Const(1e-06))) * (pss_busFreqPu + (pss_Xcomp * pss_dVBusPu))) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(1e-12) - pss_Tcomp) + sym.Const(1e-06)))) * pss_compFreqFilter_y))
    initial_equations[pss_limiter_y] = ((pss_limiter_uMin + ((pss_gain_y - pss_limiter_uMin) * sym.heaviside((pss_gain_y - pss_limiter_uMin)))) - ((pss_gain_y - pss_limiter_uMax) * sym.heaviside((pss_gain_y - pss_limiter_uMax))))
    initial_equations[pss_limiter1_y] = ((pss_limiter1_uMin + ((pss_add_y - pss_limiter1_uMin) * sym.heaviside((pss_add_y - pss_limiter1_uMin)))) - ((pss_add_y - pss_limiter1_uMax) * sym.heaviside((pss_add_y - pss_limiter1_uMax))))
    initial_equations[pss_pGenFilter_y] = (pss_gain_k * pss_PGenPu)
    initial_equations[pss_compFreqFilter_y] = (pss_busFreqPu + (pss_Xcomp * pss_dVBusPu))
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

    template.comment = 'Generator power system stabilizer PSS6C'
    return template
