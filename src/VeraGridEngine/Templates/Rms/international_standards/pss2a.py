# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Pss2a'.

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

def build_pss2a_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'Pss2a'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    pss_KOmega: Var = vf.add_var('pss.KOmega_' + template_name)
    pss_KOmegaRef: Var = vf.add_var('pss.KOmegaRef_' + template_name)
    pss_Ks1: Var = vf.add_var('pss.Ks1_' + template_name)
    pss_Ks2: Var = vf.add_var('pss.Ks2_' + template_name)
    pss_Ks3: Var = vf.add_var('pss.Ks3_' + template_name)
    pss_M: Var = vf.add_var('pss.M_' + template_name)
    pss_N: Var = vf.add_var('pss.N_' + template_name)
    pss_OmegaMaxPu: Var = vf.add_var('pss.OmegaMaxPu_' + template_name)
    pss_OmegaMinPu: Var = vf.add_var('pss.OmegaMinPu_' + template_name)
    pss_PGen0Pu: Var = vf.add_var('pss.PGen0Pu_' + template_name)
    pss_PGenMaxPu: Var = vf.add_var('pss.PGenMaxPu_' + template_name)
    pss_PGenMinPu: Var = vf.add_var('pss.PGenMinPu_' + template_name)
    pss_SNom: Var = vf.add_var('pss.SNom_' + template_name)
    pss_VPssMaxPu: Var = vf.add_var('pss.VPssMaxPu_' + template_name)
    pss_VPssMinPu: Var = vf.add_var('pss.VPssMinPu_' + template_name)
    pss_add_k1: Var = vf.add_var('pss.add.k1_' + template_name)
    pss_add_k2: Var = vf.add_var('pss.add.k2_' + template_name)
    pss_add1_k1: Var = vf.add_var('pss.add1.k1_' + template_name)
    pss_add1_k2: Var = vf.add_var('pss.add1.k2_' + template_name)
    pss_firstOrder_T: Var = vf.add_var('pss.firstOrder.T_' + template_name)
    pss_firstOrder_initType: Var = vf.add_var('pss.firstOrder.initType_' + template_name)
    pss_firstOrder_k: Var = vf.add_var('pss.firstOrder.k_' + template_name)
    pss_firstOrder_y_start: Var = vf.add_var('pss.firstOrder.y_start_' + template_name)
    pss_firstOrder1_T: Var = vf.add_var('pss.firstOrder1.T_' + template_name)
    pss_firstOrder1_initType: Var = vf.add_var('pss.firstOrder1.initType_' + template_name)
    pss_firstOrder1_k: Var = vf.add_var('pss.firstOrder1.k_' + template_name)
    pss_firstOrder1_y_start: Var = vf.add_var('pss.firstOrder1.y_start_' + template_name)
    pss_gain_k: Var = vf.add_var('pss.gain.k_' + template_name)
    pss_gain1_k: Var = vf.add_var('pss.gain1.k_' + template_name)
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
    pss_rampTrackingFilter_K: Var = vf.add_var('pss.rampTrackingFilter.K_' + template_name)
    pss_rampTrackingFilter_M: Var = vf.add_var('pss.rampTrackingFilter.M_' + template_name)
    pss_rampTrackingFilter_N: Var = vf.add_var('pss.rampTrackingFilter.N_' + template_name)
    pss_rampTrackingFilter_NMax: Var = vf.add_var('pss.rampTrackingFilter.NMax_' + template_name)
    pss_rampTrackingFilter_Y0: Var = vf.add_var('pss.rampTrackingFilter.Y0_' + template_name)
    pss_rampTrackingFilter_gain_k: Var = vf.add_var('pss.rampTrackingFilter.gain.k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_K: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].K_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_M: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].M_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_MMax: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].MMax_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].Y0_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[1].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[1].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[1].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[1].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[2].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[2].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[2].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[2].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[3].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[3].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[3].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[3].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[4].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[4].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[4].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[4].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[5].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[5].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[5].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].firstOrderCascade[5].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.a[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.a[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_end: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.a_end_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.b[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.b[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_bb_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.bb[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_bb_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.bb[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_d: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.d_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_na: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.na_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_nb: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.nb_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_nx: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.nx_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_x_start_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.x_start[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].leadlag.y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_t1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].t1_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_t2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1].t2_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_K: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].K_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_M: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].M_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_MMax: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].MMax_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].Y0_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[1].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[1].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[1].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[1].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[2].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[2].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[2].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[2].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[3].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[3].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[3].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[3].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[4].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[4].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[4].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[4].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[5].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[5].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[5].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].firstOrderCascade[5].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.a[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.a[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_end: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.a_end_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.b[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.b[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_bb_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.bb[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_bb_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.bb[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_d: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.d_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_na: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.na_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_nb: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.nb_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_nx: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.nx_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_x_start_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.x_start[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].leadlag.y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_t1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].t1_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_t2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2].t2_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_K: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].K_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_M: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].M_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_MMax: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].MMax_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].Y0_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[1].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[1].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[1].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[1].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[2].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[2].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[2].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[2].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[3].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[3].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[3].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[3].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[4].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[4].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[4].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[4].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[5].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[5].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[5].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].firstOrderCascade[5].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.a[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.a[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_end: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.a_end_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.b[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.b[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_bb_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.bb[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_bb_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.bb[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_d: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.d_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_na: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.na_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_nb: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.nb_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_nx: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.nx_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_x_start_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.x_start[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].leadlag.y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_t1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].t1_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_t2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3].t2_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_K: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].K_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_M: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].M_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_MMax: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].MMax_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].Y0_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[1].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[1].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[1].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[1].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[2].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[2].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[2].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[2].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[3].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[3].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[3].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[3].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[4].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[4].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[4].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[4].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_T: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[5].T_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_initType: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[5].initType_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_k: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[5].k_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].firstOrderCascade[5].y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.a[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.a[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_end: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.a_end_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.b[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.b[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_bb_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.bb[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_bb_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.bb[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_d: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.d_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_na: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.na_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_nb: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.nb_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_nx: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.nx_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_x_start_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.x_start[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_y_start: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].leadlag.y_start_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_t1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].t1_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_t2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4].t2_' + template_name)
    pss_rampTrackingFilter_t1: Var = vf.add_var('pss.rampTrackingFilter.t1_' + template_name)
    pss_rampTrackingFilter_t2: Var = vf.add_var('pss.rampTrackingFilter.t2_' + template_name)
    pss_t1: Var = vf.add_var('pss.t1_' + template_name)
    pss_t2: Var = vf.add_var('pss.t2_' + template_name)
    pss_t3: Var = vf.add_var('pss.t3_' + template_name)
    pss_t4: Var = vf.add_var('pss.t4_' + template_name)
    pss_t6: Var = vf.add_var('pss.t6_' + template_name)
    pss_t7: Var = vf.add_var('pss.t7_' + template_name)
    pss_t8: Var = vf.add_var('pss.t8_' + template_name)
    pss_t9: Var = vf.add_var('pss.t9_' + template_name)
    pss_tW1: Var = vf.add_var('pss.tW1_' + template_name)
    pss_tW2: Var = vf.add_var('pss.tW2_' + template_name)
    pss_tW3: Var = vf.add_var('pss.tW3_' + template_name)
    pss_tW4: Var = vf.add_var('pss.tW4_' + template_name)
    pss_transferFunction_a_1: Var = vf.add_var('pss.transferFunction.a[1]_' + template_name)
    pss_transferFunction_a_2: Var = vf.add_var('pss.transferFunction.a[2]_' + template_name)
    pss_transferFunction_a_end: Var = vf.add_var('pss.transferFunction.a_end_' + template_name)
    pss_transferFunction_b_1: Var = vf.add_var('pss.transferFunction.b[1]_' + template_name)
    pss_transferFunction_b_2: Var = vf.add_var('pss.transferFunction.b[2]_' + template_name)
    pss_transferFunction_bb_1: Var = vf.add_var('pss.transferFunction.bb[1]_' + template_name)
    pss_transferFunction_bb_2: Var = vf.add_var('pss.transferFunction.bb[2]_' + template_name)
    pss_transferFunction_d: Var = vf.add_var('pss.transferFunction.d_' + template_name)
    pss_transferFunction_na: Var = vf.add_var('pss.transferFunction.na_' + template_name)
    pss_transferFunction_nb: Var = vf.add_var('pss.transferFunction.nb_' + template_name)
    pss_transferFunction_nx: Var = vf.add_var('pss.transferFunction.nx_' + template_name)
    pss_transferFunction_x_start_1: Var = vf.add_var('pss.transferFunction.x_start[1]_' + template_name)
    pss_transferFunction_y_start: Var = vf.add_var('pss.transferFunction.y_start_' + template_name)
    pss_transferFunction1_a_1: Var = vf.add_var('pss.transferFunction1.a[1]_' + template_name)
    pss_transferFunction1_a_2: Var = vf.add_var('pss.transferFunction1.a[2]_' + template_name)
    pss_transferFunction1_a_end: Var = vf.add_var('pss.transferFunction1.a_end_' + template_name)
    pss_transferFunction1_b_1: Var = vf.add_var('pss.transferFunction1.b[1]_' + template_name)
    pss_transferFunction1_b_2: Var = vf.add_var('pss.transferFunction1.b[2]_' + template_name)
    pss_transferFunction1_bb_1: Var = vf.add_var('pss.transferFunction1.bb[1]_' + template_name)
    pss_transferFunction1_bb_2: Var = vf.add_var('pss.transferFunction1.bb[2]_' + template_name)
    pss_transferFunction1_d: Var = vf.add_var('pss.transferFunction1.d_' + template_name)
    pss_transferFunction1_na: Var = vf.add_var('pss.transferFunction1.na_' + template_name)
    pss_transferFunction1_nb: Var = vf.add_var('pss.transferFunction1.nb_' + template_name)
    pss_transferFunction1_nx: Var = vf.add_var('pss.transferFunction1.nx_' + template_name)
    pss_transferFunction1_x_start_1: Var = vf.add_var('pss.transferFunction1.x_start[1]_' + template_name)
    pss_transferFunction1_y_start: Var = vf.add_var('pss.transferFunction1.y_start_' + template_name)
    pss_washout_U0: Var = vf.add_var('pss.washout.U0_' + template_name)
    pss_washout_derivative_T: Var = vf.add_var('pss.washout.derivative.T_' + template_name)
    pss_washout_derivative_initType: Var = vf.add_var('pss.washout.derivative.initType_' + template_name)
    pss_washout_derivative_k: Var = vf.add_var('pss.washout.derivative.k_' + template_name)
    pss_washout_derivative_x_start: Var = vf.add_var('pss.washout.derivative.x_start_' + template_name)
    pss_washout_derivative_y_start: Var = vf.add_var('pss.washout.derivative.y_start_' + template_name)
    pss_washout_derivative_zeroGain: Var = vf.add_var('pss.washout.derivative.zeroGain_' + template_name)
    pss_washout_tW: Var = vf.add_var('pss.washout.tW_' + template_name)
    pss_washout1_U0: Var = vf.add_var('pss.washout1.U0_' + template_name)
    pss_washout1_derivative_T: Var = vf.add_var('pss.washout1.derivative.T_' + template_name)
    pss_washout1_derivative_initType: Var = vf.add_var('pss.washout1.derivative.initType_' + template_name)
    pss_washout1_derivative_k: Var = vf.add_var('pss.washout1.derivative.k_' + template_name)
    pss_washout1_derivative_x_start: Var = vf.add_var('pss.washout1.derivative.x_start_' + template_name)
    pss_washout1_derivative_y_start: Var = vf.add_var('pss.washout1.derivative.y_start_' + template_name)
    pss_washout1_derivative_zeroGain: Var = vf.add_var('pss.washout1.derivative.zeroGain_' + template_name)
    pss_washout1_tW: Var = vf.add_var('pss.washout1.tW_' + template_name)
    pss_washout2_U0: Var = vf.add_var('pss.washout2.U0_' + template_name)
    pss_washout2_derivative_T: Var = vf.add_var('pss.washout2.derivative.T_' + template_name)
    pss_washout2_derivative_initType: Var = vf.add_var('pss.washout2.derivative.initType_' + template_name)
    pss_washout2_derivative_k: Var = vf.add_var('pss.washout2.derivative.k_' + template_name)
    pss_washout2_derivative_x_start: Var = vf.add_var('pss.washout2.derivative.x_start_' + template_name)
    pss_washout2_derivative_y_start: Var = vf.add_var('pss.washout2.derivative.y_start_' + template_name)
    pss_washout2_derivative_zeroGain: Var = vf.add_var('pss.washout2.derivative.zeroGain_' + template_name)
    pss_washout2_tW: Var = vf.add_var('pss.washout2.tW_' + template_name)
    pss_washout3_U0: Var = vf.add_var('pss.washout3.U0_' + template_name)
    pss_washout3_derivative_T: Var = vf.add_var('pss.washout3.derivative.T_' + template_name)
    pss_washout3_derivative_initType: Var = vf.add_var('pss.washout3.derivative.initType_' + template_name)
    pss_washout3_derivative_k: Var = vf.add_var('pss.washout3.derivative.k_' + template_name)
    pss_washout3_derivative_x_start: Var = vf.add_var('pss.washout3.derivative.x_start_' + template_name)
    pss_washout3_derivative_y_start: Var = vf.add_var('pss.washout3.derivative.y_start_' + template_name)
    pss_washout3_derivative_zeroGain: Var = vf.add_var('pss.washout3.derivative.zeroGain_' + template_name)
    pss_washout3_tW: Var = vf.add_var('pss.washout3.tW_' + template_name)
    # Declare the state variables used by the template.
    pss_firstOrder_y: Var = vf.add_var('pss.firstOrder.y_' + template_name)
    pss_firstOrder1_y: Var = vf.add_var('pss.firstOrder1.y_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1,2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_3: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1,3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_4: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1,4]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1_5: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1,5]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2,2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_3: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2,3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_4: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2,4]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2_5: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2,5]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3,2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_3: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3,3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_4: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3,4]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3_5: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3,5]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4,1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4,2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_3: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4,3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_4: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4,4]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4_5: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4,5]_' + template_name)
    pss_transferFunction_x_scaled_1: Var = vf.add_var('pss.transferFunction.x_scaled[1]_' + template_name)
    pss_transferFunction1_x_scaled_1: Var = vf.add_var('pss.transferFunction1.x_scaled[1]_' + template_name)
    pss_washout_derivative_x: Var = vf.add_var('pss.washout.derivative.x_' + template_name)
    pss_washout1_derivative_x: Var = vf.add_var('pss.washout1.derivative.x_' + template_name)
    pss_washout2_derivative_x: Var = vf.add_var('pss.washout2.derivative.x_' + template_name)
    pss_washout3_derivative_x: Var = vf.add_var('pss.washout3.derivative.x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_pss_firstOrder_y: Var = vf.add_var('$START.pss.firstOrder.y_' + template_name)
    START_pss_firstOrder1_y: Var = vf.add_var('$START.pss.firstOrder1.y_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_1: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,1]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_2: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,2]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_3: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,3]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_4: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,4]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_1_5: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[1,5]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_1: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,1]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_2: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,2]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_3: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,3]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_4: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,4]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_2_5: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[2,5]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_1: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,1]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_2: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,2]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_3: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,3]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_4: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,4]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_3_5: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[3,5]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_1: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,1]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_2: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,2]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_3: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,3]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_4: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,4]_' + template_name)
    START_pss_rampTrackingFilter_leadMOrderLagCascade_4_5: Var = vf.add_var('$START.pss.rampTrackingFilter.leadMOrderLagCascade[4,5]_' + template_name)
    START_pss_transferFunction_x_scaled_1: Var = vf.add_var('$START.pss.transferFunction.x_scaled[1]_' + template_name)
    START_pss_transferFunction1_x_scaled_1: Var = vf.add_var('$START.pss.transferFunction1.x_scaled[1]_' + template_name)
    START_pss_washout_derivative_x: Var = vf.add_var('$START.pss.washout.derivative.x_' + template_name)
    START_pss_washout1_derivative_x: Var = vf.add_var('$START.pss.washout1.derivative.x_' + template_name)
    START_pss_washout2_derivative_x: Var = vf.add_var('$START.pss.washout2.derivative.x_' + template_name)
    START_pss_washout3_derivative_x: Var = vf.add_var('$START.pss.washout3.derivative.x_' + template_name)
    pss_PGenPu: Var = vf.add_var('pss.PGenPu_' + template_name)
    pss_VPssPu: Var = vf.add_var('pss.VPssPu_' + template_name)
    pss_add_y: Var = vf.add_var('pss.add.y_' + template_name)
    pss_add1_y: Var = vf.add_var('pss.add1.y_' + template_name)
    pss_feedback_y: Var = vf.add_var('pss.feedback.y_' + template_name)
    pss_gain_y: Var = vf.add_var('pss.gain.y_' + template_name)
    pss_gain1_y: Var = vf.add_var('pss.gain1.y_' + template_name)
    pss_limiter_simplifiedExpr: Var = vf.add_var('pss.limiter.simplifiedExpr_' + template_name)
    pss_limiter_y: Var = vf.add_var('pss.limiter.y_' + template_name)
    pss_limiter1_simplifiedExpr: Var = vf.add_var('pss.limiter1.simplifiedExpr_' + template_name)
    pss_limiter1_y: Var = vf.add_var('pss.limiter1.y_' + template_name)
    pss_limiter2_simplifiedExpr: Var = vf.add_var('pss.limiter2.simplifiedExpr_' + template_name)
    pss_omegaPu: Var = vf.add_var('pss.omegaPu_' + template_name)
    pss_omegaRefPu: Var = vf.add_var('pss.omegaRefPu_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_1: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[1]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_2: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[2]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_3: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[3]_' + template_name)
    pss_rampTrackingFilter_leadMOrderLagCascade_4: Var = vf.add_var('pss.rampTrackingFilter.leadMOrderLagCascade[4]_' + template_name)
    pss_rampTrackingFilter_z_1: Var = vf.add_var('pss.rampTrackingFilter.z[1]_' + template_name)
    pss_rampTrackingFilter_z_2: Var = vf.add_var('pss.rampTrackingFilter.z[2]_' + template_name)
    pss_rampTrackingFilter_z_3: Var = vf.add_var('pss.rampTrackingFilter.z[3]_' + template_name)
    pss_rampTrackingFilter_z_4: Var = vf.add_var('pss.rampTrackingFilter.z[4]_' + template_name)
    pss_transferFunction_x_1: Var = vf.add_var('pss.transferFunction.x[1]_' + template_name)
    pss_transferFunction_y: Var = vf.add_var('pss.transferFunction.y_' + template_name)
    pss_transferFunction1_x_1: Var = vf.add_var('pss.transferFunction1.x[1]_' + template_name)
    pss_transferFunction1_y: Var = vf.add_var('pss.transferFunction1.y_' + template_name)
    pss_washout_y: Var = vf.add_var('pss.washout.y_' + template_name)
    pss_washout1_y: Var = vf.add_var('pss.washout1.y_' + template_name)
    pss_washout2_y: Var = vf.add_var('pss.washout2.y_' + template_name)
    pss_washout3_y: Var = vf.add_var('pss.washout3.y_' + template_name)
    # Declare the differential variables used by the template.
    d_pss_firstOrder_y: Var = vf.add_diff_var('d_pss.firstOrder.y_' + template_name, base_var=pss_firstOrder_y)
    d_pss_firstOrder1_y: Var = vf.add_diff_var('d_pss.firstOrder1.y_' + template_name, base_var=pss_firstOrder1_y)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_1: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[1,1]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_1)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_2: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[1,2]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_2)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_3: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[1,3]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_3)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_4: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[1,4]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_4)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_1_5: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[1,5]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_1_5)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_1: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[2,1]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_1)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_2: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[2,2]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_2)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_3: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[2,3]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_3)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_4: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[2,4]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_4)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_2_5: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[2,5]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_2_5)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_1: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[3,1]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_1)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_2: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[3,2]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_2)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_3: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[3,3]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_3)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_4: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[3,4]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_4)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_3_5: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[3,5]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_3_5)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_1: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[4,1]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_1)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_2: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[4,2]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_2)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_3: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[4,3]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_3)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_4: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[4,4]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_4)
    d_pss_rampTrackingFilter_leadMOrderLagCascade_4_5: Var = vf.add_diff_var('d_pss.rampTrackingFilter.leadMOrderLagCascade[4,5]_' + template_name, base_var=pss_rampTrackingFilter_leadMOrderLagCascade_4_5)
    d_pss_transferFunction_x_scaled_1: Var = vf.add_diff_var('d_pss.transferFunction.x_scaled[1]_' + template_name, base_var=pss_transferFunction_x_scaled_1)
    d_pss_transferFunction1_x_scaled_1: Var = vf.add_diff_var('d_pss.transferFunction1.x_scaled[1]_' + template_name, base_var=pss_transferFunction1_x_scaled_1)
    d_pss_washout_derivative_x: Var = vf.add_diff_var('d_pss.washout.derivative.x_' + template_name, base_var=pss_washout_derivative_x)
    d_pss_washout1_derivative_x: Var = vf.add_diff_var('d_pss.washout1.derivative.x_' + template_name, base_var=pss_washout1_derivative_x)
    d_pss_washout2_derivative_x: Var = vf.add_diff_var('d_pss.washout2.derivative.x_' + template_name, base_var=pss_washout2_derivative_x)
    d_pss_washout3_derivative_x: Var = vf.add_diff_var('d_pss.washout3.derivative.x_' + template_name, base_var=pss_washout3_derivative_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append((((pss_rampTrackingFilter_gain_k * pss_add_y) - pss_rampTrackingFilter_leadMOrderLagCascade_1_1) / pss_rampTrackingFilter_leadMOrderLagCascade_1_t2))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append((((pss_transferFunction_a_end * pss_gain1_y) - (pss_transferFunction_a_2 * pss_transferFunction_x_scaled_1)) / pss_transferFunction_a_1))
    state_equations.append((((pss_transferFunction1_a_end * pss_transferFunction_y) - (pss_transferFunction1_a_2 * pss_transferFunction1_x_scaled_1)) / pss_transferFunction1_a_1))
    state_equations.append(((pss_washout3_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout3_derivative_zeroGain) * ((pss_washout2_y - pss_washout3_derivative_x) / pss_washout3_derivative_T))))
    state_equations.append((((pss_firstOrder1_k * pss_washout3_y) - pss_firstOrder1_y) / pss_firstOrder1_T))
    state_equations.append(((pss_washout2_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout2_derivative_zeroGain) * ((pss_limiter1_y - pss_washout2_derivative_x) / pss_washout2_derivative_T))))
    state_equations.append(((pss_washout1_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout1_derivative_zeroGain) * ((pss_washout_y - pss_washout1_derivative_x) / pss_washout1_derivative_T))))
    state_equations.append((((pss_firstOrder_k * pss_washout1_y) - pss_firstOrder_y) / pss_firstOrder_T))
    state_equations.append(((pss_washout_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout_derivative_zeroGain) * ((pss_limiter_y - pss_washout_derivative_x) / pss_washout_derivative_T))))
    state_variables: list[Var] = list()
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_4_5)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_4_4)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_4_3)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_4_2)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_3_5)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_3_4)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_3_3)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_3_2)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_2_5)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_2_4)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_2_3)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_2_2)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_1_5)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_1_4)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_1_3)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_1_2)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_1_1)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_2_1)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_3_1)
    state_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_4_1)
    state_variables.append(pss_transferFunction_x_scaled_1)
    state_variables.append(pss_transferFunction1_x_scaled_1)
    state_variables.append(pss_washout3_derivative_x)
    state_variables.append(pss_firstOrder1_y)
    state_variables.append(pss_washout2_derivative_x)
    state_variables.append(pss_washout1_derivative_x)
    state_variables.append(pss_firstOrder_y)
    state_variables.append(pss_washout_derivative_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((pss_transferFunction1_x_1 - (pss_transferFunction1_x_scaled_1 / pss_transferFunction1_a_end)))
    algebraic_equations.append((pss_transferFunction_x_1 - (pss_transferFunction_x_scaled_1 / pss_transferFunction_a_end)))
    algebraic_equations.append((pss_add_y - ((pss_add_k1 * pss_firstOrder1_y) + (pss_add_k2 * pss_firstOrder_y))))
    algebraic_equations.append((pss_rampTrackingFilter_leadMOrderLagCascade_4_1 - sym.Const(0.0)))
    algebraic_equations.append((pss_rampTrackingFilter_leadMOrderLagCascade_3_1 - sym.Const(0.0)))
    algebraic_equations.append((pss_rampTrackingFilter_leadMOrderLagCascade_2_1 - sym.Const(0.0)))
    algebraic_equations.append((pss_rampTrackingFilter_leadMOrderLagCascade_1_1 - pss_rampTrackingFilter_leadMOrderLagCascade_1_1))
    algebraic_equations.append((pss_rampTrackingFilter_leadMOrderLagCascade_1 - ((((pss_rampTrackingFilter_leadMOrderLagCascade_1_K - ((pss_rampTrackingFilter_leadMOrderLagCascade_1_K * pss_rampTrackingFilter_leadMOrderLagCascade_1_t1) / pss_rampTrackingFilter_leadMOrderLagCascade_1_t2)) * pss_rampTrackingFilter_leadMOrderLagCascade_1_1) + (((pss_rampTrackingFilter_leadMOrderLagCascade_1_K * pss_rampTrackingFilter_leadMOrderLagCascade_1_t1) / pss_rampTrackingFilter_leadMOrderLagCascade_1_t2) * (pss_rampTrackingFilter_gain_k * pss_add_y))))))
    algebraic_equations.append((pss_rampTrackingFilter_z_1 - pss_rampTrackingFilter_leadMOrderLagCascade_1))
    algebraic_equations.append((pss_rampTrackingFilter_leadMOrderLagCascade_2 - sym.Const(0.0)))
    algebraic_equations.append((pss_rampTrackingFilter_leadMOrderLagCascade_3 - sym.Const(0.0)))
    algebraic_equations.append((pss_rampTrackingFilter_leadMOrderLagCascade_4 - sym.Const(0.0)))
    algebraic_equations.append((pss_feedback_y - (pss_rampTrackingFilter_z_1 - pss_firstOrder1_y)))
    algebraic_equations.append((pss_gain1_y - (pss_gain1_k * pss_feedback_y)))
    algebraic_equations.append((pss_transferFunction_y - (((pss_transferFunction_bb_2 - (pss_transferFunction_d * pss_transferFunction_a_2)) * pss_transferFunction_x_1) + (pss_transferFunction_d * pss_gain1_y))))
    algebraic_equations.append((pss_transferFunction1_y - (((pss_transferFunction1_bb_2 - (pss_transferFunction1_d * pss_transferFunction1_a_2)) * pss_transferFunction1_x_1) + (pss_transferFunction1_d * pss_transferFunction_y))))
    algebraic_equations.append((pss_VPssPu - ((sym.heaviside(((pss_transferFunction1_y - pss_limiter2_uMax) - sym.Const(1e-06))) * pss_limiter2_uMax) + ((sym.Const(1.0) - sym.heaviside(((pss_transferFunction1_y - pss_limiter2_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((pss_limiter2_uMin - pss_transferFunction1_y) - sym.Const(1e-06))) * pss_limiter2_uMin) + ((sym.Const(1.0) - sym.heaviside(((pss_limiter2_uMin - pss_transferFunction1_y) - sym.Const(1e-06)))) * pss_transferFunction1_y))))))
    algebraic_equations.append((pss_washout2_y - ((pss_washout2_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout2_derivative_zeroGain) * ((pss_washout2_derivative_k / pss_washout2_derivative_T) * (pss_limiter1_y - pss_washout2_derivative_x))))))
    algebraic_equations.append((pss_washout3_y - ((pss_washout3_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout3_derivative_zeroGain) * ((pss_washout3_derivative_k / pss_washout3_derivative_T) * (pss_washout2_y - pss_washout3_derivative_x))))))
    algebraic_equations.append((pss_washout_y - ((pss_washout_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout_derivative_zeroGain) * ((pss_washout_derivative_k / pss_washout_derivative_T) * (pss_limiter_y - pss_washout_derivative_x))))))
    algebraic_equations.append((pss_washout1_y - ((pss_washout1_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout1_derivative_zeroGain) * ((pss_washout1_derivative_k / pss_washout1_derivative_T) * (pss_washout_y - pss_washout1_derivative_x))))))
    algebraic_equations.append((pss_add1_y - ((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu))))
    algebraic_equations.append((pss_limiter_y - ((pss_limiter_uMin + ((((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)) - pss_limiter_uMin) * sym.heaviside((((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)) - pss_limiter_uMin)))) - ((((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)) - pss_limiter_uMax) * sym.heaviside((((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)) - pss_limiter_uMax))))))
    algebraic_equations.append((pss_gain_y - (pss_gain_k * pss_PGenPu)))
    algebraic_equations.append((pss_limiter1_y - ((pss_limiter1_uMin + (((pss_gain_k * pss_PGenPu) - pss_limiter1_uMin) * sym.heaviside(((pss_gain_k * pss_PGenPu) - pss_limiter1_uMin)))) - (((pss_gain_k * pss_PGenPu) - pss_limiter1_uMax) * sym.heaviside(((pss_gain_k * pss_PGenPu) - pss_limiter1_uMax))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(pss_transferFunction1_x_1)
    algebraic_variables.append(pss_transferFunction_x_1)
    algebraic_variables.append(pss_add_y)
    algebraic_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_4_1)
    algebraic_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_3_1)
    algebraic_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_2_1)
    algebraic_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_1_1)
    algebraic_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_1)
    algebraic_variables.append(pss_rampTrackingFilter_z_1)
    algebraic_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_2)
    algebraic_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_3)
    algebraic_variables.append(pss_rampTrackingFilter_leadMOrderLagCascade_4)
    algebraic_variables.append(pss_feedback_y)
    algebraic_variables.append(pss_gain1_y)
    algebraic_variables.append(pss_transferFunction_y)
    algebraic_variables.append(pss_transferFunction1_y)
    algebraic_variables.append(pss_VPssPu)
    algebraic_variables.append(pss_washout2_y)
    algebraic_variables.append(pss_washout3_y)
    algebraic_variables.append(pss_washout_y)
    algebraic_variables.append(pss_washout1_y)
    algebraic_variables.append(pss_limiter1_y)
    algebraic_variables.append(pss_limiter_y)
    algebraic_variables.append(pss_PGenPu)
    algebraic_variables.append(pss_omegaPu)
    algebraic_variables.append(pss_omegaRefPu)
    algebraic_variables.append(pss_limiter_simplifiedExpr)
    algebraic_variables.append(pss_limiter1_simplifiedExpr)
    algebraic_variables.append(pss_limiter2_simplifiedExpr)
    algebraic_variables.append(START_pss_washout_derivative_x)
    algebraic_variables.append(START_pss_washout1_derivative_x)
    algebraic_variables.append(START_pss_washout2_derivative_x)
    algebraic_variables.append(START_pss_washout3_derivative_x)
    algebraic_variables.append(START_pss_firstOrder_y)
    algebraic_variables.append(START_pss_firstOrder1_y)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_1_1)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_1_2)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_1_3)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_1_4)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_1_5)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_2_1)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_2_2)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_2_3)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_2_4)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_2_5)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_3_1)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_3_2)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_3_3)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_3_4)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_3_5)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_4_1)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_4_2)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_4_3)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_4_4)
    algebraic_variables.append(START_pss_rampTrackingFilter_leadMOrderLagCascade_4_5)
    algebraic_variables.append(START_pss_transferFunction_x_scaled_1)
    algebraic_variables.append(START_pss_transferFunction1_x_scaled_1)
    algebraic_variables.append(pss_add1_y)
    algebraic_variables.append(pss_gain_y)
    algebraic_variables.append(pss_rampTrackingFilter_z_2)
    algebraic_variables.append(pss_rampTrackingFilter_z_3)
    algebraic_variables.append(pss_rampTrackingFilter_z_4)
    differential_variables: list[Var] = list()
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_4_5)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_4_4)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_4_3)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_4_2)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_3_5)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_3_4)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_3_3)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_3_2)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_2_5)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_2_4)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_2_3)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_2_2)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_1_5)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_1_4)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_1_3)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_1_2)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_1_1)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_2_1)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_3_1)
    differential_variables.append(d_pss_rampTrackingFilter_leadMOrderLagCascade_4_1)
    differential_variables.append(d_pss_transferFunction_x_scaled_1)
    differential_variables.append(d_pss_transferFunction1_x_scaled_1)
    differential_variables.append(d_pss_washout3_derivative_x)
    differential_variables.append(d_pss_firstOrder1_y)
    differential_variables.append(d_pss_washout2_derivative_x)
    differential_variables.append(d_pss_washout1_derivative_x)
    differential_variables.append(d_pss_firstOrder_y)
    differential_variables.append(d_pss_washout_derivative_x)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[pss_KOmega] = vf.add_const(1.0, name='')
    event_parameters[pss_KOmegaRef] = vf.add_const(0.0, name='')
    event_parameters[pss_Ks1] = vf.add_const(10.0, name='')
    event_parameters[pss_Ks2] = vf.add_const(1.0, name='')
    event_parameters[pss_Ks3] = vf.add_const(1.0, name='')
    event_parameters[pss_OmegaMaxPu] = vf.add_const(1.1, name='')
    event_parameters[pss_OmegaMinPu] = vf.add_const(0.9, name='')
    event_parameters[pss_PGen0Pu] = vf.add_const(0.8, name='')
    event_parameters[pss_PGenMaxPu] = vf.add_const(1.0, name='')
    event_parameters[pss_PGenMinPu] = vf.add_const(0.0, name='')
    event_parameters[pss_SNom] = vf.add_const(100.0, name='')
    event_parameters[pss_VPssMaxPu] = vf.add_const(0.1, name='')
    event_parameters[pss_VPssMinPu] = vf.add_const(-0.1, name='')
    event_parameters[pss_add_k1] = pss_Ks3
    event_parameters[pss_add_k2] = vf.add_const(1.0, name='')
    event_parameters[pss_add1_k1] = pss_KOmega
    event_parameters[pss_add1_k2] = pss_KOmegaRef
    event_parameters[pss_firstOrder_T] = pss_t6
    event_parameters[pss_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[pss_firstOrder_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_firstOrder1_T] = pss_t7
    event_parameters[pss_firstOrder1_k] = pss_Ks2
    event_parameters[pss_firstOrder1_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_gain_k] = (sym.Const(100.0) / pss_SNom)
    event_parameters[pss_gain1_k] = pss_Ks1
    event_parameters[pss_limiter_uMax] = pss_OmegaMaxPu
    event_parameters[pss_limiter_uMin] = pss_OmegaMinPu
    event_parameters[pss_limiter1_uMax] = pss_PGenMaxPu
    event_parameters[pss_limiter1_uMin] = pss_PGenMinPu
    event_parameters[pss_limiter2_uMax] = pss_VPssMaxPu
    event_parameters[pss_limiter2_uMin] = pss_VPssMinPu
    event_parameters[pss_rampTrackingFilter_K] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_Y0] = vf.add_const(0.0, name='')
    event_parameters[pss_rampTrackingFilter_gain_k] = pss_rampTrackingFilter_K
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_K] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_K] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_K] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_K] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0] = pss_rampTrackingFilter_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0] = pss_rampTrackingFilter_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0] = pss_rampTrackingFilter_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0] = pss_rampTrackingFilter_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_T] = pss_rampTrackingFilter_leadMOrderLagCascade_1_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_T] = pss_rampTrackingFilter_leadMOrderLagCascade_1_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_T] = pss_rampTrackingFilter_leadMOrderLagCascade_1_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_T] = pss_rampTrackingFilter_leadMOrderLagCascade_1_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_T] = pss_rampTrackingFilter_leadMOrderLagCascade_1_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_T] = pss_rampTrackingFilter_leadMOrderLagCascade_2_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_T] = pss_rampTrackingFilter_leadMOrderLagCascade_2_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_T] = pss_rampTrackingFilter_leadMOrderLagCascade_2_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_T] = pss_rampTrackingFilter_leadMOrderLagCascade_2_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_T] = pss_rampTrackingFilter_leadMOrderLagCascade_2_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_T] = pss_rampTrackingFilter_leadMOrderLagCascade_3_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_T] = pss_rampTrackingFilter_leadMOrderLagCascade_3_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_T] = pss_rampTrackingFilter_leadMOrderLagCascade_3_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_T] = pss_rampTrackingFilter_leadMOrderLagCascade_3_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_T] = pss_rampTrackingFilter_leadMOrderLagCascade_3_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_T] = pss_rampTrackingFilter_leadMOrderLagCascade_4_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_T] = pss_rampTrackingFilter_leadMOrderLagCascade_4_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_T] = pss_rampTrackingFilter_leadMOrderLagCascade_4_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_T] = pss_rampTrackingFilter_leadMOrderLagCascade_4_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_T] = pss_rampTrackingFilter_leadMOrderLagCascade_4_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_k] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_1_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_2_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_3_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_y_start] = pss_rampTrackingFilter_leadMOrderLagCascade_4_Y0
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_1] = pss_rampTrackingFilter_leadMOrderLagCascade_1_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_2] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_1] = pss_rampTrackingFilter_leadMOrderLagCascade_2_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_2] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_1] = pss_rampTrackingFilter_leadMOrderLagCascade_3_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_2] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_1] = pss_rampTrackingFilter_leadMOrderLagCascade_4_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_2] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_a_end] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_a_end] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_a_end] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_a_end] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_1] = vf.add_const(0.1, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_2] = pss_rampTrackingFilter_leadMOrderLagCascade_1_K
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_1] = vf.add_const(0.1, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_2] = pss_rampTrackingFilter_leadMOrderLagCascade_2_K
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_1] = vf.add_const(0.1, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_2] = pss_rampTrackingFilter_leadMOrderLagCascade_3_K
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_1] = vf.add_const(0.1, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_2] = pss_rampTrackingFilter_leadMOrderLagCascade_4_K
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_bb_1] = pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_1
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_bb_2] = pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_b_2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_bb_1] = pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_1
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_bb_2] = pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_b_2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_bb_1] = pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_1
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_bb_2] = pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_b_2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_bb_1] = pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_1
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_bb_2] = pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_b_2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_d] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_d] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_d] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_d] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_t1] = pss_rampTrackingFilter_t1
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_t1] = pss_rampTrackingFilter_t1
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_t1] = pss_rampTrackingFilter_t1
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_t1] = pss_rampTrackingFilter_t1
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_t2] = pss_rampTrackingFilter_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_t2] = pss_rampTrackingFilter_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_t2] = pss_rampTrackingFilter_t2
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_t2] = pss_rampTrackingFilter_t2
    event_parameters[pss_rampTrackingFilter_t1] = pss_t8
    event_parameters[pss_rampTrackingFilter_t2] = pss_t9
    event_parameters[pss_t1] = vf.add_const(0.1, name='')
    event_parameters[pss_t2] = vf.add_const(0.05, name='')
    event_parameters[pss_t3] = vf.add_const(0.1, name='')
    event_parameters[pss_t4] = vf.add_const(0.05, name='')
    event_parameters[pss_t6] = vf.add_const(0.02, name='')
    event_parameters[pss_t7] = vf.add_const(0.02, name='')
    event_parameters[pss_t8] = vf.add_const(0.1, name='')
    event_parameters[pss_t9] = vf.add_const(0.05, name='')
    event_parameters[pss_tW1] = vf.add_const(10.0, name='')
    event_parameters[pss_tW2] = vf.add_const(10.0, name='')
    event_parameters[pss_tW3] = vf.add_const(10.0, name='')
    event_parameters[pss_tW4] = vf.add_const(10.0, name='')
    event_parameters[pss_transferFunction_a_1] = pss_t2
    event_parameters[pss_transferFunction_a_2] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction_a_end] = ((sym.heaviside(((pss_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((pss_transferFunction_a_1 ** sym.Const(2.0)) + (pss_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06))) * pss_transferFunction_a_2) + ((sym.Const(1.0) - sym.heaviside(((pss_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((pss_transferFunction_a_1 ** sym.Const(2.0)) + (pss_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06)))) * sym.Const(1.0)))
    event_parameters[pss_transferFunction_b_1] = pss_t1
    event_parameters[pss_transferFunction_b_2] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction_bb_1] = pss_transferFunction_b_1
    event_parameters[pss_transferFunction_bb_2] = pss_transferFunction_b_2
    event_parameters[pss_transferFunction_d] = (pss_transferFunction_bb_1 / pss_transferFunction_a_1)
    event_parameters[pss_transferFunction_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction1_a_1] = pss_t4
    event_parameters[pss_transferFunction1_a_2] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction1_a_end] = ((sym.heaviside(((pss_transferFunction1_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((pss_transferFunction1_a_1 ** sym.Const(2.0)) + (pss_transferFunction1_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06))) * pss_transferFunction1_a_2) + ((sym.Const(1.0) - sym.heaviside(((pss_transferFunction1_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((pss_transferFunction1_a_1 ** sym.Const(2.0)) + (pss_transferFunction1_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06)))) * sym.Const(1.0)))
    event_parameters[pss_transferFunction1_b_1] = pss_t3
    event_parameters[pss_transferFunction1_b_2] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction1_bb_1] = pss_transferFunction1_b_1
    event_parameters[pss_transferFunction1_bb_2] = pss_transferFunction1_b_2
    event_parameters[pss_transferFunction1_d] = (pss_transferFunction1_bb_1 / pss_transferFunction1_a_1)
    event_parameters[pss_transferFunction1_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction1_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_U0] = (pss_KOmega + pss_KOmegaRef)
    event_parameters[pss_washout_derivative_T] = vf.add_const(10.0, name='')
    event_parameters[pss_washout_derivative_k] = vf.add_const(10.0, name='')
    event_parameters[pss_washout_derivative_x_start] = pss_washout_U0
    event_parameters[pss_washout_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_washout1_U0] = vf.add_const(0.0, name='')
    event_parameters[pss_washout1_derivative_T] = vf.add_const(10.0, name='')
    event_parameters[pss_washout1_derivative_k] = vf.add_const(10.0, name='')
    event_parameters[pss_washout1_derivative_x_start] = pss_washout1_U0
    event_parameters[pss_washout1_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout1_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_washout2_U0] = (sym.Const(100.0) * (pss_PGen0Pu / pss_SNom))
    event_parameters[pss_washout2_derivative_T] = vf.add_const(10.0, name='')
    event_parameters[pss_washout2_derivative_k] = vf.add_const(10.0, name='')
    event_parameters[pss_washout2_derivative_x_start] = pss_washout2_U0
    event_parameters[pss_washout2_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout2_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_washout3_U0] = vf.add_const(0.0, name='')
    event_parameters[pss_washout3_derivative_T] = vf.add_const(10.0, name='')
    event_parameters[pss_washout3_derivative_k] = vf.add_const(10.0, name='')
    event_parameters[pss_washout3_derivative_x_start] = pss_washout3_U0
    event_parameters[pss_washout3_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout3_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_M] = vf.add_const(1.0, name='')
    event_parameters[pss_N] = vf.add_const(1.0, name='')
    event_parameters[pss_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_firstOrder1_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter2_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_M] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_N] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_NMax] = vf.add_const(4.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_M] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_M] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_M] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_M] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_MMax] = vf.add_const(6.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_MMax] = vf.add_const(6.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_MMax] = vf.add_const(6.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_MMax] = vf.add_const(6.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_1_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_2_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_3_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_4_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_firstOrderCascade_5_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_1_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_2_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_3_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_4_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_firstOrderCascade_5_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_1_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_2_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_3_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_4_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_firstOrderCascade_5_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_1_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_2_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_3_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_4_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_firstOrderCascade_5_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_na] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_na] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_na] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_na] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_nb] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_nb] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_nb] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_nb] = vf.add_const(2.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_1_leadlag_nx] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_2_leadlag_nx] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_3_leadlag_nx] = vf.add_const(1.0, name='')
    event_parameters[pss_rampTrackingFilter_leadMOrderLagCascade_4_leadlag_nx] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction_na] = vf.add_const(2.0, name='')
    event_parameters[pss_transferFunction_nb] = vf.add_const(2.0, name='')
    event_parameters[pss_transferFunction_nx] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction1_na] = vf.add_const(2.0, name='')
    event_parameters[pss_transferFunction1_nb] = vf.add_const(2.0, name='')
    event_parameters[pss_transferFunction1_nx] = vf.add_const(1.0, name='')
    event_parameters[pss_washout_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_washout1_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_washout2_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_washout3_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[pss_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[pss_limiter2_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter2_strict] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_washout_derivative_k)) - sym.Const(1e-06)))
    event_parameters[pss_washout1_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_washout1_derivative_k)) - sym.Const(1e-06)))
    event_parameters[pss_washout2_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_washout2_derivative_k)) - sym.Const(1e-06)))
    event_parameters[pss_washout3_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_washout3_derivative_k)) - sym.Const(1e-06)))
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[pss_firstOrder_y] = pss_firstOrder_y_start
    initial_equations[pss_firstOrder1_y] = pss_firstOrder1_y_start
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_1_1] = START_pss_rampTrackingFilter_leadMOrderLagCascade_1_1
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_1_2] = START_pss_rampTrackingFilter_leadMOrderLagCascade_1_2
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_1_3] = START_pss_rampTrackingFilter_leadMOrderLagCascade_1_3
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_1_4] = START_pss_rampTrackingFilter_leadMOrderLagCascade_1_4
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_1_5] = START_pss_rampTrackingFilter_leadMOrderLagCascade_1_5
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_2_1] = START_pss_rampTrackingFilter_leadMOrderLagCascade_2_1
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_2_2] = START_pss_rampTrackingFilter_leadMOrderLagCascade_2_2
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_2_3] = START_pss_rampTrackingFilter_leadMOrderLagCascade_2_3
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_2_4] = START_pss_rampTrackingFilter_leadMOrderLagCascade_2_4
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_2_5] = START_pss_rampTrackingFilter_leadMOrderLagCascade_2_5
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_3_1] = START_pss_rampTrackingFilter_leadMOrderLagCascade_3_1
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_3_2] = START_pss_rampTrackingFilter_leadMOrderLagCascade_3_2
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_3_3] = START_pss_rampTrackingFilter_leadMOrderLagCascade_3_3
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_3_4] = START_pss_rampTrackingFilter_leadMOrderLagCascade_3_4
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_3_5] = START_pss_rampTrackingFilter_leadMOrderLagCascade_3_5
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_4_1] = START_pss_rampTrackingFilter_leadMOrderLagCascade_4_1
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_4_2] = START_pss_rampTrackingFilter_leadMOrderLagCascade_4_2
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_4_3] = START_pss_rampTrackingFilter_leadMOrderLagCascade_4_3
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_4_4] = START_pss_rampTrackingFilter_leadMOrderLagCascade_4_4
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_4_5] = START_pss_rampTrackingFilter_leadMOrderLagCascade_4_5
    initial_equations[pss_transferFunction_x_scaled_1] = (pss_transferFunction_a_end * pss_transferFunction_x_start_1)
    initial_equations[pss_transferFunction1_x_scaled_1] = (pss_transferFunction1_a_end * pss_transferFunction1_x_start_1)
    initial_equations[pss_washout_derivative_x] = pss_washout_derivative_x_start
    initial_equations[pss_washout1_derivative_x] = pss_washout1_derivative_x_start
    initial_equations[pss_washout2_derivative_x] = pss_washout2_derivative_x_start
    initial_equations[pss_washout3_derivative_x] = pss_washout3_derivative_x_start
    initial_equations[pss_PGenPu] = pss_PGen0Pu
    initial_equations[pss_VPssPu] = vf.add_const(0.0, name='')
    initial_equations[pss_limiter_y] = ((pss_limiter_uMin + ((((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)) - pss_limiter_uMin) * sym.heaviside((((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)) - pss_limiter_uMin)))) - ((((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)) - pss_limiter_uMax) * sym.heaviside((((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)) - pss_limiter_uMax))))
    initial_equations[pss_limiter1_y] = ((pss_limiter1_uMin + (((pss_gain_k * pss_PGenPu) - pss_limiter1_uMin) * sym.heaviside(((pss_gain_k * pss_PGenPu) - pss_limiter1_uMin)))) - (((pss_gain_k * pss_PGenPu) - pss_limiter1_uMax) * sym.heaviside(((pss_gain_k * pss_PGenPu) - pss_limiter1_uMax))))
    initial_equations[pss_omegaPu] = vf.add_const(1.0, name='')
    initial_equations[pss_omegaRefPu] = vf.add_const(1.0, name='')
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_2] = pss_rampTrackingFilter_leadMOrderLagCascade_2
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_3] = pss_rampTrackingFilter_leadMOrderLagCascade_3
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_4] = pss_rampTrackingFilter_leadMOrderLagCascade_4
    initial_equations[pss_rampTrackingFilter_z_1] = pss_rampTrackingFilter_Y0
    initial_equations[pss_transferFunction_x_1] = pss_transferFunction_x_start_1
    initial_equations[pss_transferFunction_y] = pss_transferFunction_y_start
    initial_equations[pss_transferFunction1_x_1] = pss_transferFunction1_x_start_1
    initial_equations[pss_transferFunction1_y] = pss_transferFunction1_y_start
    initial_equations[pss_washout_y] = pss_washout1_U0
    initial_equations[pss_washout1_y] = vf.add_const(0.0, name='')
    initial_equations[pss_washout2_y] = pss_washout3_U0
    initial_equations[pss_washout3_y] = vf.add_const(0.0, name='')
    initial_equations[pss_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[pss_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[pss_limiter2_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[pss_add1_y] = ((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu))
    initial_equations[pss_gain_y] = (pss_gain_k * pss_PGenPu)
    initial_equations[pss_rampTrackingFilter_z_2] = vf.add_const(0.0, name='')
    initial_equations[pss_rampTrackingFilter_z_3] = vf.add_const(0.0, name='')
    initial_equations[pss_rampTrackingFilter_z_4] = vf.add_const(0.0, name='')
    initial_equations[pss_rampTrackingFilter_leadMOrderLagCascade_1] = vf.add_const(1.0, name='')
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

    template.comment = 'Generator power system stabilizer PSS2A'
    return template
