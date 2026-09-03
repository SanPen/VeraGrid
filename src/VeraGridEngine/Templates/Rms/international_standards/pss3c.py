# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Pss3c'.

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

def build_pss3c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'Pss3c'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    pss_A1: Var = vf.add_var('pss.A1_' + template_name)
    pss_A2: Var = vf.add_var('pss.A2_' + template_name)
    pss_A3: Var = vf.add_var('pss.A3_' + template_name)
    pss_A4: Var = vf.add_var('pss.A4_' + template_name)
    pss_A5: Var = vf.add_var('pss.A5_' + template_name)
    pss_A6: Var = vf.add_var('pss.A6_' + template_name)
    pss_A7: Var = vf.add_var('pss.A7_' + template_name)
    pss_A8: Var = vf.add_var('pss.A8_' + template_name)
    pss_KOmega: Var = vf.add_var('pss.KOmega_' + template_name)
    pss_KOmegaRef: Var = vf.add_var('pss.KOmegaRef_' + template_name)
    pss_Ks1: Var = vf.add_var('pss.Ks1_' + template_name)
    pss_Ks2: Var = vf.add_var('pss.Ks2_' + template_name)
    pss_PGen0Pu: Var = vf.add_var('pss.PGen0Pu_' + template_name)
    pss_PPssOffPu: Var = vf.add_var('pss.PPssOffPu_' + template_name)
    pss_PPssOnPu: Var = vf.add_var('pss.PPssOnPu_' + template_name)
    pss_SNom: Var = vf.add_var('pss.SNom_' + template_name)
    pss_VPssMaxPu: Var = vf.add_var('pss.VPssMaxPu_' + template_name)
    pss_VPssMinPu: Var = vf.add_var('pss.VPssMinPu_' + template_name)
    pss_add_k1: Var = vf.add_var('pss.add.k1_' + template_name)
    pss_add_k2: Var = vf.add_var('pss.add.k2_' + template_name)
    pss_add1_k1: Var = vf.add_var('pss.add1.k1_' + template_name)
    pss_add1_k2: Var = vf.add_var('pss.add1.k2_' + template_name)
    pss_const_k: Var = vf.add_var('pss.const.k_' + template_name)
    pss_firstOrder_T: Var = vf.add_var('pss.firstOrder.T_' + template_name)
    pss_firstOrder_initType: Var = vf.add_var('pss.firstOrder.initType_' + template_name)
    pss_firstOrder_k: Var = vf.add_var('pss.firstOrder.k_' + template_name)
    pss_firstOrder_y_start: Var = vf.add_var('pss.firstOrder.y_start_' + template_name)
    pss_firstOrder1_T: Var = vf.add_var('pss.firstOrder1.T_' + template_name)
    pss_firstOrder1_initType: Var = vf.add_var('pss.firstOrder1.initType_' + template_name)
    pss_firstOrder1_k: Var = vf.add_var('pss.firstOrder1.k_' + template_name)
    pss_firstOrder1_y_start: Var = vf.add_var('pss.firstOrder1.y_start_' + template_name)
    pss_gain_k: Var = vf.add_var('pss.gain.k_' + template_name)
    pss_hysteresis_pre_y_start: Var = vf.add_var('pss.hysteresis.pre_y_start_' + template_name)
    pss_hysteresis_uHigh: Var = vf.add_var('pss.hysteresis.uHigh_' + template_name)
    pss_hysteresis_uLow: Var = vf.add_var('pss.hysteresis.uLow_' + template_name)
    pss_limiter2_homotopyType: Var = vf.add_var('pss.limiter2.homotopyType_' + template_name)
    pss_limiter2_limitsAtInit: Var = vf.add_var('pss.limiter2.limitsAtInit_' + template_name)
    pss_limiter2_strict: Var = vf.add_var('pss.limiter2.strict_' + template_name)
    pss_limiter2_uMax: Var = vf.add_var('pss.limiter2.uMax_' + template_name)
    pss_limiter2_uMin: Var = vf.add_var('pss.limiter2.uMin_' + template_name)
    pss_t1: Var = vf.add_var('pss.t1_' + template_name)
    pss_t2: Var = vf.add_var('pss.t2_' + template_name)
    pss_tW1: Var = vf.add_var('pss.tW1_' + template_name)
    pss_tW2: Var = vf.add_var('pss.tW2_' + template_name)
    pss_tW3: Var = vf.add_var('pss.tW3_' + template_name)
    pss_transferFunction_a_1: Var = vf.add_var('pss.transferFunction.a[1]_' + template_name)
    pss_transferFunction_a_2: Var = vf.add_var('pss.transferFunction.a[2]_' + template_name)
    pss_transferFunction_a_3: Var = vf.add_var('pss.transferFunction.a[3]_' + template_name)
    pss_transferFunction_a_end: Var = vf.add_var('pss.transferFunction.a_end_' + template_name)
    pss_transferFunction_a_one: Var = vf.add_var('pss.transferFunction.a_one_' + template_name)
    pss_transferFunction_b_1: Var = vf.add_var('pss.transferFunction.b[1]_' + template_name)
    pss_transferFunction_b_2: Var = vf.add_var('pss.transferFunction.b[2]_' + template_name)
    pss_transferFunction_b_3: Var = vf.add_var('pss.transferFunction.b[3]_' + template_name)
    pss_transferFunction_bb_1: Var = vf.add_var('pss.transferFunction.bb[1]_' + template_name)
    pss_transferFunction_bb_2: Var = vf.add_var('pss.transferFunction.bb[2]_' + template_name)
    pss_transferFunction_bb_3: Var = vf.add_var('pss.transferFunction.bb[3]_' + template_name)
    pss_transferFunction_d: Var = vf.add_var('pss.transferFunction.d_' + template_name)
    pss_transferFunction_na: Var = vf.add_var('pss.transferFunction.na_' + template_name)
    pss_transferFunction_nb: Var = vf.add_var('pss.transferFunction.nb_' + template_name)
    pss_transferFunction_nx: Var = vf.add_var('pss.transferFunction.nx_' + template_name)
    pss_transferFunction_x_start_1: Var = vf.add_var('pss.transferFunction.x_start[1]_' + template_name)
    pss_transferFunction_x_start_2: Var = vf.add_var('pss.transferFunction.x_start[2]_' + template_name)
    pss_transferFunction_y_start: Var = vf.add_var('pss.transferFunction.y_start_' + template_name)
    pss_transferFunction1_a_1: Var = vf.add_var('pss.transferFunction1.a[1]_' + template_name)
    pss_transferFunction1_a_2: Var = vf.add_var('pss.transferFunction1.a[2]_' + template_name)
    pss_transferFunction1_a_3: Var = vf.add_var('pss.transferFunction1.a[3]_' + template_name)
    pss_transferFunction1_a_end: Var = vf.add_var('pss.transferFunction1.a_end_' + template_name)
    pss_transferFunction1_a_one: Var = vf.add_var('pss.transferFunction1.a_one_' + template_name)
    pss_transferFunction1_b_1: Var = vf.add_var('pss.transferFunction1.b[1]_' + template_name)
    pss_transferFunction1_b_2: Var = vf.add_var('pss.transferFunction1.b[2]_' + template_name)
    pss_transferFunction1_b_3: Var = vf.add_var('pss.transferFunction1.b[3]_' + template_name)
    pss_transferFunction1_bb_1: Var = vf.add_var('pss.transferFunction1.bb[1]_' + template_name)
    pss_transferFunction1_bb_2: Var = vf.add_var('pss.transferFunction1.bb[2]_' + template_name)
    pss_transferFunction1_bb_3: Var = vf.add_var('pss.transferFunction1.bb[3]_' + template_name)
    pss_transferFunction1_d: Var = vf.add_var('pss.transferFunction1.d_' + template_name)
    pss_transferFunction1_na: Var = vf.add_var('pss.transferFunction1.na_' + template_name)
    pss_transferFunction1_nb: Var = vf.add_var('pss.transferFunction1.nb_' + template_name)
    pss_transferFunction1_nx: Var = vf.add_var('pss.transferFunction1.nx_' + template_name)
    pss_transferFunction1_x_start_1: Var = vf.add_var('pss.transferFunction1.x_start[1]_' + template_name)
    pss_transferFunction1_x_start_2: Var = vf.add_var('pss.transferFunction1.x_start[2]_' + template_name)
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
    # Declare the state variables used by the template.
    pss_firstOrder_y: Var = vf.add_var('pss.firstOrder.y_' + template_name)
    pss_firstOrder1_y: Var = vf.add_var('pss.firstOrder1.y_' + template_name)
    pss_transferFunction_x_scaled_1: Var = vf.add_var('pss.transferFunction.x_scaled[1]_' + template_name)
    pss_transferFunction_x_scaled_2: Var = vf.add_var('pss.transferFunction.x_scaled[2]_' + template_name)
    pss_transferFunction1_x_scaled_1: Var = vf.add_var('pss.transferFunction1.x_scaled[1]_' + template_name)
    pss_transferFunction1_x_scaled_2: Var = vf.add_var('pss.transferFunction1.x_scaled[2]_' + template_name)
    pss_washout_derivative_x: Var = vf.add_var('pss.washout.derivative.x_' + template_name)
    pss_washout1_derivative_x: Var = vf.add_var('pss.washout1.derivative.x_' + template_name)
    pss_washout2_derivative_x: Var = vf.add_var('pss.washout2.derivative.x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_pss_hysteresis_y: Var = vf.add_var('$PRE.pss.hysteresis.y_' + template_name)
    START_pss_firstOrder_y: Var = vf.add_var('$START.pss.firstOrder.y_' + template_name)
    START_pss_firstOrder1_y: Var = vf.add_var('$START.pss.firstOrder1.y_' + template_name)
    START_pss_transferFunction_x_scaled_1: Var = vf.add_var('$START.pss.transferFunction.x_scaled[1]_' + template_name)
    START_pss_transferFunction_x_scaled_2: Var = vf.add_var('$START.pss.transferFunction.x_scaled[2]_' + template_name)
    START_pss_transferFunction1_x_scaled_1: Var = vf.add_var('$START.pss.transferFunction1.x_scaled[1]_' + template_name)
    START_pss_transferFunction1_x_scaled_2: Var = vf.add_var('$START.pss.transferFunction1.x_scaled[2]_' + template_name)
    START_pss_washout_derivative_x: Var = vf.add_var('$START.pss.washout.derivative.x_' + template_name)
    START_pss_washout1_derivative_x: Var = vf.add_var('$START.pss.washout1.derivative.x_' + template_name)
    START_pss_washout2_derivative_x: Var = vf.add_var('$START.pss.washout2.derivative.x_' + template_name)
    pss_PGenPu: Var = vf.add_var('pss.PGenPu_' + template_name)
    pss_VPssPu: Var = vf.add_var('pss.VPssPu_' + template_name)
    pss_add_y: Var = vf.add_var('pss.add.y_' + template_name)
    pss_add1_y: Var = vf.add_var('pss.add1.y_' + template_name)
    pss_gain_y: Var = vf.add_var('pss.gain.y_' + template_name)
    pss_hysteresis_y: Var = vf.add_var('pss.hysteresis.y_' + template_name)
    pss_limiter2_simplifiedExpr: Var = vf.add_var('pss.limiter2.simplifiedExpr_' + template_name)
    pss_limiter2_y: Var = vf.add_var('pss.limiter2.y_' + template_name)
    pss_omegaPu: Var = vf.add_var('pss.omegaPu_' + template_name)
    pss_omegaRefPu: Var = vf.add_var('pss.omegaRefPu_' + template_name)
    pss_washout_y: Var = vf.add_var('pss.washout.y_' + template_name)
    pss_washout1_y: Var = vf.add_var('pss.washout1.y_' + template_name)
    pss_washout2_y: Var = vf.add_var('pss.washout2.y_' + template_name)
    # Declare the differential variables used by the template.
    d_pss_firstOrder_y: Var = vf.add_diff_var('d_pss.firstOrder.y_' + template_name, base_var=pss_firstOrder_y)
    d_pss_firstOrder1_y: Var = vf.add_diff_var('d_pss.firstOrder1.y_' + template_name, base_var=pss_firstOrder1_y)
    d_pss_transferFunction_x_scaled_1: Var = vf.add_diff_var('d_pss.transferFunction.x_scaled[1]_' + template_name, base_var=pss_transferFunction_x_scaled_1)
    d_pss_transferFunction_x_scaled_2: Var = vf.add_diff_var('d_pss.transferFunction.x_scaled[2]_' + template_name, base_var=pss_transferFunction_x_scaled_2)
    d_pss_transferFunction1_x_scaled_1: Var = vf.add_diff_var('d_pss.transferFunction1.x_scaled[1]_' + template_name, base_var=pss_transferFunction1_x_scaled_1)
    d_pss_transferFunction1_x_scaled_2: Var = vf.add_diff_var('d_pss.transferFunction1.x_scaled[2]_' + template_name, base_var=pss_transferFunction1_x_scaled_2)
    d_pss_washout_derivative_x: Var = vf.add_diff_var('d_pss.washout.derivative.x_' + template_name, base_var=pss_washout_derivative_x)
    d_pss_washout1_derivative_x: Var = vf.add_diff_var('d_pss.washout1.derivative.x_' + template_name, base_var=pss_washout1_derivative_x)
    d_pss_washout2_derivative_x: Var = vf.add_diff_var('d_pss.washout2.derivative.x_' + template_name, base_var=pss_washout2_derivative_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((pss_washout1_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout1_derivative_zeroGain) * ((pss_firstOrder1_y - pss_washout1_derivative_x) / pss_washout1_derivative_T))))
    state_equations.append(((pss_washout_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout_derivative_zeroGain) * ((pss_firstOrder_y - pss_washout_derivative_x) / pss_washout_derivative_T))))
    state_equations.append((((pss_firstOrder_k * pss_add1_y) - pss_firstOrder_y) / pss_firstOrder_T))
    state_equations.append((((pss_firstOrder1_k * pss_gain_y) - pss_firstOrder1_y) / pss_firstOrder1_T))
    state_equations.append(((pss_washout2_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout2_derivative_zeroGain) * ((pss_add_y - pss_washout2_derivative_x) / pss_washout2_derivative_T))))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_equations.append(sym.Const(0.0))
    state_variables: list[Var] = list()
    state_variables.append(pss_washout1_derivative_x)
    state_variables.append(pss_washout_derivative_x)
    state_variables.append(pss_firstOrder_y)
    state_variables.append(pss_firstOrder1_y)
    state_variables.append(pss_washout2_derivative_x)
    state_variables.append(pss_transferFunction1_x_scaled_2)
    state_variables.append(pss_transferFunction1_x_scaled_1)
    state_variables.append(pss_transferFunction_x_scaled_2)
    state_variables.append(pss_transferFunction_x_scaled_1)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((pss_washout1_y - ((pss_washout1_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout1_derivative_zeroGain) * ((pss_washout1_derivative_k / pss_washout1_derivative_T) * (pss_firstOrder1_y - pss_washout1_derivative_x))))))
    algebraic_equations.append((pss_washout_y - ((pss_washout_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout_derivative_zeroGain) * ((pss_washout_derivative_k / pss_washout_derivative_T) * (pss_firstOrder_y - pss_washout_derivative_x))))))
    algebraic_equations.append((pss_add_y - ((pss_add_k1 * pss_washout1_y) + (pss_add_k2 * pss_washout_y))))
    algebraic_equations.append((pss_washout2_y - ((pss_washout2_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout2_derivative_zeroGain) * ((pss_washout2_derivative_k / pss_washout2_derivative_T) * (pss_add_y - pss_washout2_derivative_x))))))
    algebraic_equations.append((pss_limiter2_y - ((sym.heaviside(((pss_washout2_y - pss_limiter2_uMax) - sym.Const(1e-06))) * pss_limiter2_uMax) + ((sym.Const(1.0) - sym.heaviside(((pss_washout2_y - pss_limiter2_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((pss_limiter2_uMin - pss_washout2_y) - sym.Const(1e-06))) * pss_limiter2_uMin) + ((sym.Const(1.0) - sym.heaviside(((pss_limiter2_uMin - pss_washout2_y) - sym.Const(1e-06)))) * pss_washout2_y))))))
    algebraic_equations.append((pss_hysteresis_y - (sym.heaviside(((pss_PGenPu - pss_hysteresis_uHigh) - sym.Const(1e-06))) + ((sym.Const(1.0) - sym.heaviside(((pss_PGenPu - pss_hysteresis_uHigh) - sym.Const(1e-06)))) * (PRE_pss_hysteresis_y * sym.heaviside(((pss_PGenPu - pss_hysteresis_uLow) + sym.Const(1e-06))))))))
    algebraic_equations.append((pss_VPssPu - ((pss_hysteresis_y * pss_limiter2_y) + ((sym.Const(1.0) - pss_hysteresis_y) * pss_const_k))))
    algebraic_equations.append((pss_add1_y - ((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu))))
    algebraic_equations.append((pss_gain_y - (pss_gain_k * pss_PGenPu)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(pss_washout1_y)
    algebraic_variables.append(pss_washout_y)
    algebraic_variables.append(pss_add_y)
    algebraic_variables.append(pss_washout2_y)
    algebraic_variables.append(pss_limiter2_y)
    algebraic_variables.append(pss_hysteresis_y)
    algebraic_variables.append(pss_VPssPu)
    algebraic_variables.append(pss_add1_y)
    algebraic_variables.append(pss_gain_y)
    algebraic_variables.append(pss_PGenPu)
    algebraic_variables.append(pss_omegaPu)
    algebraic_variables.append(pss_omegaRefPu)
    algebraic_variables.append(START_pss_transferFunction1_x_scaled_2)
    algebraic_variables.append(START_pss_transferFunction1_x_scaled_1)
    algebraic_variables.append(START_pss_transferFunction_x_scaled_2)
    algebraic_variables.append(START_pss_transferFunction_x_scaled_1)
    algebraic_variables.append(pss_limiter2_simplifiedExpr)
    algebraic_variables.append(START_pss_washout1_derivative_x)
    algebraic_variables.append(START_pss_washout_derivative_x)
    algebraic_variables.append(START_pss_firstOrder_y)
    algebraic_variables.append(START_pss_firstOrder1_y)
    algebraic_variables.append(START_pss_washout2_derivative_x)
    algebraic_variables.append(PRE_pss_hysteresis_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_pss_washout1_derivative_x)
    differential_variables.append(d_pss_washout_derivative_x)
    differential_variables.append(d_pss_firstOrder_y)
    differential_variables.append(d_pss_firstOrder1_y)
    differential_variables.append(d_pss_washout2_derivative_x)
    differential_variables.append(d_pss_transferFunction1_x_scaled_2)
    differential_variables.append(d_pss_transferFunction1_x_scaled_1)
    differential_variables.append(d_pss_transferFunction_x_scaled_2)
    differential_variables.append(d_pss_transferFunction_x_scaled_1)
    input_variables: list[Var] = list()
    input_variables.append(pss_PGenPu)
    input_variables.append(pss_omegaPu)
    input_variables.append(pss_omegaRefPu)
    output_variables: list[Var] = list()
    output_variables.append(pss_VPssPu)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[pss_A1] = vf.add_const(0.0, name='')
    event_parameters[pss_A2] = vf.add_const(0.0, name='')
    event_parameters[pss_A3] = vf.add_const(0.0, name='')
    event_parameters[pss_A4] = vf.add_const(0.0, name='')
    event_parameters[pss_A5] = vf.add_const(0.0, name='')
    event_parameters[pss_A6] = vf.add_const(0.0, name='')
    event_parameters[pss_A7] = vf.add_const(0.0, name='')
    event_parameters[pss_A8] = vf.add_const(0.0, name='')
    event_parameters[pss_KOmega] = vf.add_const(1.0, name='')
    event_parameters[pss_KOmegaRef] = vf.add_const(0.0, name='')
    event_parameters[pss_Ks1] = vf.add_const(10.0, name='')
    event_parameters[pss_Ks2] = vf.add_const(1.0, name='')
    event_parameters[pss_PGen0Pu] = vf.add_const(0.8, name='')
    event_parameters[pss_PPssOffPu] = vf.add_const(0.05, name='')
    event_parameters[pss_PPssOnPu] = vf.add_const(0.1, name='')
    event_parameters[pss_SNom] = vf.add_const(100.0, name='')
    event_parameters[pss_VPssMaxPu] = vf.add_const(0.1, name='')
    event_parameters[pss_VPssMinPu] = vf.add_const(-0.1, name='')
    event_parameters[pss_add_k1] = vf.add_const(1.0, name='')
    event_parameters[pss_add_k2] = vf.add_const(1.0, name='')
    event_parameters[pss_add1_k1] = pss_KOmega
    event_parameters[pss_add1_k2] = pss_KOmegaRef
    event_parameters[pss_const_k] = vf.add_const(0.0, name='')
    event_parameters[pss_firstOrder_T] = pss_t2
    event_parameters[pss_firstOrder_k] = pss_Ks2
    event_parameters[pss_firstOrder_y_start] = (pss_Ks2 * (pss_KOmega + pss_KOmegaRef))
    event_parameters[pss_firstOrder1_T] = pss_t1
    event_parameters[pss_firstOrder1_k] = pss_Ks1
    event_parameters[pss_firstOrder1_y_start] = (sym.Const(100.0) * (pss_Ks1 * (pss_PGen0Pu / pss_SNom)))
    event_parameters[pss_gain_k] = (sym.Const(100.0) / pss_SNom)
    event_parameters[pss_hysteresis_uHigh] = pss_PPssOnPu
    event_parameters[pss_hysteresis_uLow] = pss_PPssOffPu
    event_parameters[pss_limiter2_uMax] = pss_VPssMaxPu
    event_parameters[pss_limiter2_uMin] = pss_VPssMinPu
    event_parameters[pss_t1] = vf.add_const(0.02, name='')
    event_parameters[pss_t2] = vf.add_const(0.02, name='')
    event_parameters[pss_tW1] = vf.add_const(10.0, name='')
    event_parameters[pss_tW2] = vf.add_const(10.0, name='')
    event_parameters[pss_tW3] = vf.add_const(10.0, name='')
    event_parameters[pss_transferFunction_a_1] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction_a_2] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction_a_3] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction_a_end] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction_a_one] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction_b_1] = pss_A2
    event_parameters[pss_transferFunction_b_2] = pss_A1
    event_parameters[pss_transferFunction_b_3] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction_bb_1] = pss_transferFunction_b_1
    event_parameters[pss_transferFunction_bb_2] = pss_transferFunction_b_2
    event_parameters[pss_transferFunction_bb_3] = pss_transferFunction_b_3
    event_parameters[pss_transferFunction_d] = (pss_transferFunction_bb_1 / pss_transferFunction_a_one)
    event_parameters[pss_transferFunction_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction_x_start_2] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction1_a_1] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction1_a_2] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction1_a_3] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction1_a_end] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction1_a_one] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction1_b_1] = pss_A6
    event_parameters[pss_transferFunction1_b_2] = pss_A5
    event_parameters[pss_transferFunction1_b_3] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction1_bb_1] = pss_transferFunction1_b_1
    event_parameters[pss_transferFunction1_bb_2] = pss_transferFunction1_b_2
    event_parameters[pss_transferFunction1_bb_3] = pss_transferFunction1_b_3
    event_parameters[pss_transferFunction1_d] = (pss_transferFunction1_bb_1 / pss_transferFunction1_a_one)
    event_parameters[pss_transferFunction1_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction1_x_start_2] = vf.add_const(0.0, name='')
    event_parameters[pss_transferFunction1_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_U0] = (pss_Ks2 * (pss_KOmega + pss_KOmegaRef))
    event_parameters[pss_washout_derivative_T] = vf.add_const(10.0, name='')
    event_parameters[pss_washout_derivative_k] = vf.add_const(10.0, name='')
    event_parameters[pss_washout_derivative_x_start] = pss_washout_U0
    event_parameters[pss_washout_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_washout1_U0] = (sym.Const(100.0) * (pss_Ks1 * (pss_PGen0Pu / pss_SNom)))
    event_parameters[pss_washout1_derivative_T] = vf.add_const(10.0, name='')
    event_parameters[pss_washout1_derivative_k] = vf.add_const(10.0, name='')
    event_parameters[pss_washout1_derivative_x_start] = pss_washout1_U0
    event_parameters[pss_washout1_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout1_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_washout2_U0] = vf.add_const(0.0, name='')
    event_parameters[pss_washout2_derivative_T] = vf.add_const(10.0, name='')
    event_parameters[pss_washout2_derivative_k] = vf.add_const(10.0, name='')
    event_parameters[pss_washout2_derivative_x_start] = pss_washout2_U0
    event_parameters[pss_washout2_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout2_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_firstOrder1_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter2_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[pss_transferFunction_na] = vf.add_const(3.0, name='')
    event_parameters[pss_transferFunction_nb] = vf.add_const(3.0, name='')
    event_parameters[pss_transferFunction_nx] = vf.add_const(2.0, name='')
    event_parameters[pss_transferFunction1_na] = vf.add_const(3.0, name='')
    event_parameters[pss_transferFunction1_nb] = vf.add_const(3.0, name='')
    event_parameters[pss_transferFunction1_nx] = vf.add_const(2.0, name='')
    event_parameters[pss_washout_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_washout1_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_washout2_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_hysteresis_pre_y_start] = sym.heaviside((((pss_gain_k * pss_PGen0Pu) - pss_PPssOffPu) - sym.Const(1e-06)))
    event_parameters[pss_limiter2_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[pss_limiter2_strict] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_washout_derivative_k)) - sym.Const(1e-06)))
    event_parameters[pss_washout1_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_washout1_derivative_k)) - sym.Const(1e-06)))
    event_parameters[pss_washout2_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_washout2_derivative_k)) - sym.Const(1e-06)))
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[pss_omegaPu] = vf.add_const(1.0, name='')
    initial_equations[pss_omegaRefPu] = vf.add_const(1.0, name='')
    initial_equations[pss_firstOrder_y] = (pss_Ks2 * ((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)))
    initial_equations[pss_firstOrder1_y] = (pss_Ks1 * (pss_gain_k * pss_PGenPu))
    initial_equations[pss_transferFunction_x_scaled_1] = vf.add_const(0.0, name='')
    initial_equations[pss_transferFunction_x_scaled_2] = vf.add_const(0.0, name='')
    initial_equations[pss_transferFunction1_x_scaled_1] = vf.add_const(0.0, name='')
    initial_equations[pss_transferFunction1_x_scaled_2] = vf.add_const(0.0, name='')
    initial_equations[pss_washout_derivative_x] = (pss_Ks2 * ((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu)))
    initial_equations[pss_washout1_derivative_x] = (pss_Ks1 * (pss_gain_k * pss_PGenPu))
    initial_equations[pss_washout2_derivative_x] = pss_washout2_derivative_x_start
    initial_equations[pss_PGenPu] = pss_PGen0Pu
    initial_equations[pss_VPssPu] = vf.add_const(0.0, name='')
    initial_equations[pss_add_y] = pss_washout2_U0
    initial_equations[pss_limiter2_y] = vf.add_const(0.0, name='')
    initial_equations[pss_washout_y] = vf.add_const(0.0, name='')
    initial_equations[pss_washout1_y] = vf.add_const(0.0, name='')
    initial_equations[pss_washout2_y] = pss_transferFunction1_y_start
    initial_equations[pss_hysteresis_y] = pss_hysteresis_pre_y_start
    initial_equations[pss_limiter2_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[pss_add1_y] = ((pss_add1_k1 * pss_omegaPu) + (pss_add1_k2 * pss_omegaRefPu))
    initial_equations[pss_gain_y] = (pss_gain_k * pss_PGenPu)
    initial_equations[PRE_pss_hysteresis_y] = pss_hysteresis_pre_y_start
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

    template.comment = 'Generator power system stabilizer PSS3C'
    return template
