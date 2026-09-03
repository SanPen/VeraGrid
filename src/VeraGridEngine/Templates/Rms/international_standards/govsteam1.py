# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'GovSteam1'.

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

def build_govsteam1_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'GovSteam1'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    gov_Db1: Var = vf.add_var('gov.Db1_' + template_name)
    gov_Db2: Var = vf.add_var('gov.Db2_' + template_name)
    gov_Eps: Var = vf.add_var('gov.Eps_' + template_name)
    gov_H0: Var = vf.add_var('gov.H0_' + template_name)
    gov_K: Var = vf.add_var('gov.K_' + template_name)
    gov_K1: Var = vf.add_var('gov.K1_' + template_name)
    gov_K2: Var = vf.add_var('gov.K2_' + template_name)
    gov_K3: Var = vf.add_var('gov.K3_' + template_name)
    gov_K4: Var = vf.add_var('gov.K4_' + template_name)
    gov_K5: Var = vf.add_var('gov.K5_' + template_name)
    gov_K6: Var = vf.add_var('gov.K6_' + template_name)
    gov_K7: Var = vf.add_var('gov.K7_' + template_name)
    gov_K8: Var = vf.add_var('gov.K8_' + template_name)
    gov_PMaxPu: Var = vf.add_var('gov.PMaxPu_' + template_name)
    gov_PMinPu: Var = vf.add_var('gov.PMinPu_' + template_name)
    gov_PgvTableName: Var = vf.add_var('gov.PgvTableName_' + template_name)
    gov_Pm0Pu: Var = vf.add_var('gov.Pm0Pu_' + template_name)
    gov_PmRef0Pu: Var = vf.add_var('gov.PmRef0Pu_' + template_name)
    gov_Sdb1: Var = vf.add_var('gov.Sdb1_' + template_name)
    gov_Sdb2: Var = vf.add_var('gov.Sdb2_' + template_name)
    gov_TablesFile: Var = vf.add_var('gov.TablesFile_' + template_name)
    gov_Uc: Var = vf.add_var('gov.Uc_' + template_name)
    gov_Uo: Var = vf.add_var('gov.Uo_' + template_name)
    gov_ValveOn: Var = vf.add_var('gov.ValveOn_' + template_name)
    gov_add_k1: Var = vf.add_var('gov.add.k1_' + template_name)
    gov_add_k2: Var = vf.add_var('gov.add.k2_' + template_name)
    gov_add1_k1: Var = vf.add_var('gov.add1.k1_' + template_name)
    gov_add1_k2: Var = vf.add_var('gov.add1.k2_' + template_name)
    gov_add2_k1: Var = vf.add_var('gov.add2.k1_' + template_name)
    gov_add2_k2: Var = vf.add_var('gov.add2.k2_' + template_name)
    gov_add3_k1: Var = vf.add_var('gov.add3.k1_' + template_name)
    gov_add3_k2: Var = vf.add_var('gov.add3.k2_' + template_name)
    gov_add3_k3: Var = vf.add_var('gov.add3.k3_' + template_name)
    gov_add4_k1: Var = vf.add_var('gov.add4.k1_' + template_name)
    gov_add4_k2: Var = vf.add_var('gov.add4.k2_' + template_name)
    gov_add5_k1: Var = vf.add_var('gov.add5.k1_' + template_name)
    gov_add5_k2: Var = vf.add_var('gov.add5.k2_' + template_name)
    gov_add6_k1: Var = vf.add_var('gov.add6.k1_' + template_name)
    gov_add6_k2: Var = vf.add_var('gov.add6.k2_' + template_name)
    gov_backlashHysteresis_Aux0: Var = vf.add_var('gov.backlashHysteresis.Aux0_' + template_name)
    gov_backlashHysteresis_H0: Var = vf.add_var('gov.backlashHysteresis.H0_' + template_name)
    gov_backlashHysteresis_Tolerance: Var = vf.add_var('gov.backlashHysteresis.Tolerance_' + template_name)
    gov_backlashHysteresis_U0: Var = vf.add_var('gov.backlashHysteresis.U0_' + template_name)
    gov_backlashHysteresis_UHigh: Var = vf.add_var('gov.backlashHysteresis.UHigh_' + template_name)
    gov_backlashHysteresis_ULow: Var = vf.add_var('gov.backlashHysteresis.ULow_' + template_name)
    gov_booleanConstant_k: Var = vf.add_var('gov.booleanConstant.k_' + template_name)
    gov_booleanConstant1_k: Var = vf.add_var('gov.booleanConstant1.k_' + template_name)
    gov_booleanConstant2_k: Var = vf.add_var('gov.booleanConstant2.k_' + template_name)
    gov_const_k: Var = vf.add_var('gov.const.k_' + template_name)
    gov_deadBand_EpsMax: Var = vf.add_var('gov.deadBand.EpsMax_' + template_name)
    gov_deadBand_EpsMin: Var = vf.add_var('gov.deadBand.EpsMin_' + template_name)
    gov_deadBand_UMax: Var = vf.add_var('gov.deadBand.UMax_' + template_name)
    gov_deadBand_UMin: Var = vf.add_var('gov.deadBand.UMin_' + template_name)
    gov_firstOrder_T: Var = vf.add_var('gov.firstOrder.T_' + template_name)
    gov_firstOrder_initType: Var = vf.add_var('gov.firstOrder.initType_' + template_name)
    gov_firstOrder_k: Var = vf.add_var('gov.firstOrder.k_' + template_name)
    gov_firstOrder_y_start: Var = vf.add_var('gov.firstOrder.y_start_' + template_name)
    gov_firstOrder1_T: Var = vf.add_var('gov.firstOrder1.T_' + template_name)
    gov_firstOrder1_initType: Var = vf.add_var('gov.firstOrder1.initType_' + template_name)
    gov_firstOrder1_k: Var = vf.add_var('gov.firstOrder1.k_' + template_name)
    gov_firstOrder1_y_start: Var = vf.add_var('gov.firstOrder1.y_start_' + template_name)
    gov_firstOrder2_T: Var = vf.add_var('gov.firstOrder2.T_' + template_name)
    gov_firstOrder2_initType: Var = vf.add_var('gov.firstOrder2.initType_' + template_name)
    gov_firstOrder2_k: Var = vf.add_var('gov.firstOrder2.k_' + template_name)
    gov_firstOrder2_y_start: Var = vf.add_var('gov.firstOrder2.y_start_' + template_name)
    gov_firstOrder3_T: Var = vf.add_var('gov.firstOrder3.T_' + template_name)
    gov_firstOrder3_initType: Var = vf.add_var('gov.firstOrder3.initType_' + template_name)
    gov_firstOrder3_k: Var = vf.add_var('gov.firstOrder3.k_' + template_name)
    gov_firstOrder3_y_start: Var = vf.add_var('gov.firstOrder3.y_start_' + template_name)
    gov_gain_k: Var = vf.add_var('gov.gain.k_' + template_name)
    gov_gain1_k: Var = vf.add_var('gov.gain1.k_' + template_name)
    gov_gain2_k: Var = vf.add_var('gov.gain2.k_' + template_name)
    gov_gain3_k: Var = vf.add_var('gov.gain3.k_' + template_name)
    gov_gain4_k: Var = vf.add_var('gov.gain4.k_' + template_name)
    gov_gain5_k: Var = vf.add_var('gov.gain5.k_' + template_name)
    gov_gain6_k: Var = vf.add_var('gov.gain6.k_' + template_name)
    gov_gain7_k: Var = vf.add_var('gov.gain7.k_' + template_name)
    gov_gain8_k: Var = vf.add_var('gov.gain8.k_' + template_name)
    gov_limitedIntegrator_initType: Var = vf.add_var('gov.limitedIntegrator.initType_' + template_name)
    gov_limitedIntegrator_k: Var = vf.add_var('gov.limitedIntegrator.k_' + template_name)
    gov_limitedIntegrator_limitsAtInit: Var = vf.add_var('gov.limitedIntegrator.limitsAtInit_' + template_name)
    gov_limitedIntegrator_outMax: Var = vf.add_var('gov.limitedIntegrator.outMax_' + template_name)
    gov_limitedIntegrator_outMin: Var = vf.add_var('gov.limitedIntegrator.outMin_' + template_name)
    gov_limitedIntegrator_strict: Var = vf.add_var('gov.limitedIntegrator.strict_' + template_name)
    gov_limitedIntegrator_use_reset: Var = vf.add_var('gov.limitedIntegrator.use_reset_' + template_name)
    gov_limitedIntegrator_use_set: Var = vf.add_var('gov.limitedIntegrator.use_set_' + template_name)
    gov_limitedIntegrator_y_start: Var = vf.add_var('gov.limitedIntegrator.y_start_' + template_name)
    gov_limiter_homotopyType: Var = vf.add_var('gov.limiter.homotopyType_' + template_name)
    gov_limiter_limitsAtInit: Var = vf.add_var('gov.limiter.limitsAtInit_' + template_name)
    gov_limiter_strict: Var = vf.add_var('gov.limiter.strict_' + template_name)
    gov_limiter_uMax: Var = vf.add_var('gov.limiter.uMax_' + template_name)
    gov_limiter_uMin: Var = vf.add_var('gov.limiter.uMin_' + template_name)
    gov_pgv_columns_1: Var = vf.add_var('gov.pgv.columns[1]_' + template_name)
    gov_pgv_extrapolation: Var = vf.add_var('gov.pgv.extrapolation_' + template_name)
    gov_pgv_fileName: Var = vf.add_var('gov.pgv.fileName_' + template_name)
    gov_pgv_nout: Var = vf.add_var('gov.pgv.nout_' + template_name)
    gov_pgv_smoothness: Var = vf.add_var('gov.pgv.smoothness_' + template_name)
    gov_pgv_tableID: Var = vf.add_var('gov.pgv.tableID_' + template_name)
    gov_pgv_tableName: Var = vf.add_var('gov.pgv.tableName_' + template_name)
    gov_pgv_tableOnFile: Var = vf.add_var('gov.pgv.tableOnFile_' + template_name)
    gov_pgv_u_max: Var = vf.add_var('gov.pgv.u_max_' + template_name)
    gov_pgv_u_min: Var = vf.add_var('gov.pgv.u_min_' + template_name)
    gov_pgv_verboseExtrapolation: Var = vf.add_var('gov.pgv.verboseExtrapolation_' + template_name)
    gov_pgv_verboseRead: Var = vf.add_var('gov.pgv.verboseRead_' + template_name)
    gov_t1: Var = vf.add_var('gov.t1_' + template_name)
    gov_t2: Var = vf.add_var('gov.t2_' + template_name)
    gov_t3: Var = vf.add_var('gov.t3_' + template_name)
    gov_t4: Var = vf.add_var('gov.t4_' + template_name)
    gov_t5: Var = vf.add_var('gov.t5_' + template_name)
    gov_t6: Var = vf.add_var('gov.t6_' + template_name)
    gov_t7: Var = vf.add_var('gov.t7_' + template_name)
    gov_transferFunction_a_1: Var = vf.add_var('gov.transferFunction.a[1]_' + template_name)
    gov_transferFunction_a_2: Var = vf.add_var('gov.transferFunction.a[2]_' + template_name)
    gov_transferFunction_a_end: Var = vf.add_var('gov.transferFunction.a_end_' + template_name)
    gov_transferFunction_b_1: Var = vf.add_var('gov.transferFunction.b[1]_' + template_name)
    gov_transferFunction_b_2: Var = vf.add_var('gov.transferFunction.b[2]_' + template_name)
    gov_transferFunction_bb_1: Var = vf.add_var('gov.transferFunction.bb[1]_' + template_name)
    gov_transferFunction_bb_2: Var = vf.add_var('gov.transferFunction.bb[2]_' + template_name)
    gov_transferFunction_d: Var = vf.add_var('gov.transferFunction.d_' + template_name)
    gov_transferFunction_na: Var = vf.add_var('gov.transferFunction.na_' + template_name)
    gov_transferFunction_nb: Var = vf.add_var('gov.transferFunction.nb_' + template_name)
    gov_transferFunction_nx: Var = vf.add_var('gov.transferFunction.nx_' + template_name)
    gov_transferFunction_x_start_1: Var = vf.add_var('gov.transferFunction.x_start[1]_' + template_name)
    gov_transferFunction_y_start: Var = vf.add_var('gov.transferFunction.y_start_' + template_name)
    # Declare the state variables used by the template.
    gov_firstOrder_y: Var = vf.add_var('gov.firstOrder.y_' + template_name)
    gov_firstOrder1_y: Var = vf.add_var('gov.firstOrder1.y_' + template_name)
    gov_firstOrder2_y: Var = vf.add_var('gov.firstOrder2.y_' + template_name)
    gov_firstOrder3_y: Var = vf.add_var('gov.firstOrder3.y_' + template_name)
    gov_limitedIntegrator_y: Var = vf.add_var('gov.limitedIntegrator.y_' + template_name)
    gov_transferFunction_x_scaled_1: Var = vf.add_var('gov.transferFunction.x_scaled[1]_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_gov_backlashHysteresis_aux: Var = vf.add_var('$PRE.gov.backlashHysteresis.aux_' + template_name)
    PRE_gov_backlashHysteresis_h: Var = vf.add_var('$PRE.gov.backlashHysteresis.h_' + template_name)
    START_gov_backlashHysteresis_aux: Var = vf.add_var('$START.gov.backlashHysteresis.aux_' + template_name)
    START_gov_backlashHysteresis_h: Var = vf.add_var('$START.gov.backlashHysteresis.h_' + template_name)
    START_gov_firstOrder_y: Var = vf.add_var('$START.gov.firstOrder.y_' + template_name)
    START_gov_firstOrder1_y: Var = vf.add_var('$START.gov.firstOrder1.y_' + template_name)
    START_gov_firstOrder2_y: Var = vf.add_var('$START.gov.firstOrder2.y_' + template_name)
    START_gov_firstOrder3_y: Var = vf.add_var('$START.gov.firstOrder3.y_' + template_name)
    START_gov_transferFunction_x_scaled_1: Var = vf.add_var('$START.gov.transferFunction.x_scaled[1]_' + template_name)
    whenCondition1: Var = vf.add_var('$whenCondition1_' + template_name)
    whenCondition2: Var = vf.add_var('$whenCondition2_' + template_name)
    gov_Pm1Pu: Var = vf.add_var('gov.Pm1Pu_' + template_name)
    gov_Pm2Pu: Var = vf.add_var('gov.Pm2Pu_' + template_name)
    gov_PmRefPu: Var = vf.add_var('gov.PmRefPu_' + template_name)
    gov_add_y: Var = vf.add_var('gov.add.y_' + template_name)
    gov_add1_y: Var = vf.add_var('gov.add1.y_' + template_name)
    gov_add3_y: Var = vf.add_var('gov.add3.y_' + template_name)
    gov_add4_y: Var = vf.add_var('gov.add4.y_' + template_name)
    gov_add5_y: Var = vf.add_var('gov.add5.y_' + template_name)
    gov_backlashHysteresis_aux: Var = vf.add_var('gov.backlashHysteresis.aux_' + template_name)
    gov_backlashHysteresis_h: Var = vf.add_var('gov.backlashHysteresis.h_' + template_name)
    gov_backlashHysteresis_y: Var = vf.add_var('gov.backlashHysteresis.y_' + template_name)
    gov_deadBand_y: Var = vf.add_var('gov.deadBand.y_' + template_name)
    gov_feedback_y: Var = vf.add_var('gov.feedback.y_' + template_name)
    gov_gain_y: Var = vf.add_var('gov.gain.y_' + template_name)
    gov_gain1_y: Var = vf.add_var('gov.gain1.y_' + template_name)
    gov_gain2_y: Var = vf.add_var('gov.gain2.y_' + template_name)
    gov_gain3_y: Var = vf.add_var('gov.gain3.y_' + template_name)
    gov_gain4_y: Var = vf.add_var('gov.gain4.y_' + template_name)
    gov_gain5_y: Var = vf.add_var('gov.gain5.y_' + template_name)
    gov_gain6_y: Var = vf.add_var('gov.gain6.y_' + template_name)
    gov_gain7_y: Var = vf.add_var('gov.gain7.y_' + template_name)
    gov_gain8_y: Var = vf.add_var('gov.gain8.y_' + template_name)
    gov_limitedIntegrator_local_reset: Var = vf.add_var('gov.limitedIntegrator.local_reset_' + template_name)
    gov_limitedIntegrator_local_set: Var = vf.add_var('gov.limitedIntegrator.local_set_' + template_name)
    gov_limiter_simplifiedExpr: Var = vf.add_var('gov.limiter.simplifiedExpr_' + template_name)
    gov_limiter_y: Var = vf.add_var('gov.limiter.y_' + template_name)
    gov_omegaPu: Var = vf.add_var('gov.omegaPu_' + template_name)
    gov_pgv_y_1: Var = vf.add_var('gov.pgv.y[1]_' + template_name)
    gov_switch_y: Var = vf.add_var('gov.switch.y_' + template_name)
    gov_switch1_y: Var = vf.add_var('gov.switch1.y_' + template_name)
    gov_switch2_y: Var = vf.add_var('gov.switch2.y_' + template_name)
    gov_transferFunction_x_1: Var = vf.add_var('gov.transferFunction.x[1]_' + template_name)
    gov_transferFunction_y: Var = vf.add_var('gov.transferFunction.y_' + template_name)
    # Declare the differential variables used by the template.
    d_gov_firstOrder_y: Var = vf.add_diff_var('d_gov.firstOrder.y_' + template_name, base_var=gov_firstOrder_y)
    d_gov_firstOrder1_y: Var = vf.add_diff_var('d_gov.firstOrder1.y_' + template_name, base_var=gov_firstOrder1_y)
    d_gov_firstOrder2_y: Var = vf.add_diff_var('d_gov.firstOrder2.y_' + template_name, base_var=gov_firstOrder2_y)
    d_gov_firstOrder3_y: Var = vf.add_diff_var('d_gov.firstOrder3.y_' + template_name, base_var=gov_firstOrder3_y)
    d_gov_limitedIntegrator_y: Var = vf.add_diff_var('d_gov.limitedIntegrator.y_' + template_name, base_var=gov_limitedIntegrator_y)
    d_gov_transferFunction_x_scaled_1: Var = vf.add_diff_var('d_gov.transferFunction.x_scaled[1]_' + template_name, base_var=gov_transferFunction_x_scaled_1)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((gov_transferFunction_a_end * gov_switch_y) - (gov_transferFunction_a_2 * gov_transferFunction_x_scaled_1)) / gov_transferFunction_a_1))
    state_equations.append((((gov_firstOrder3_k * gov_firstOrder2_y) - gov_firstOrder3_y) / gov_firstOrder3_T))
    state_equations.append((((gov_firstOrder2_k * gov_firstOrder1_y) - gov_firstOrder2_y) / gov_firstOrder2_T))
    state_equations.append((((gov_firstOrder1_k * gov_firstOrder_y) - gov_firstOrder1_y) / gov_firstOrder1_T))
    state_equations.append((((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limitedIntegrator_outMin - gov_limitedIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limitedIntegrator_outMin - gov_limitedIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limitedIntegrator_k * gov_limiter_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limitedIntegrator_outMin - gov_limitedIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limitedIntegrator_k * gov_limiter_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limitedIntegrator_y - gov_limitedIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limitedIntegrator_outMin - gov_limitedIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limitedIntegrator_k * gov_limiter_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limitedIntegrator_y - gov_limitedIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limitedIntegrator_k * gov_limiter_y) - sym.Const(0.0)) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limitedIntegrator_outMin - gov_limitedIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limitedIntegrator_outMin - gov_limitedIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limitedIntegrator_k * gov_limiter_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limitedIntegrator_outMin - gov_limitedIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limitedIntegrator_k * gov_limiter_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limitedIntegrator_y - gov_limitedIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limitedIntegrator_outMin - gov_limitedIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limitedIntegrator_k * gov_limiter_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limitedIntegrator_y - gov_limitedIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limitedIntegrator_k * gov_limiter_y) - sym.Const(0.0)) - sym.Const(1e-06)))))))) * (gov_limitedIntegrator_k * gov_limiter_y))))
    state_equations.append((((gov_firstOrder_k * gov_switch2_y) - gov_firstOrder_y) / gov_firstOrder_T))
    state_variables: list[Var] = list()
    state_variables.append(gov_transferFunction_x_scaled_1)
    state_variables.append(gov_firstOrder3_y)
    state_variables.append(gov_firstOrder2_y)
    state_variables.append(gov_firstOrder1_y)
    state_variables.append(gov_limitedIntegrator_y)
    state_variables.append(gov_firstOrder_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((gov_deadBand_y - ((sym.heaviside(((gov_feedback_y - gov_deadBand_UMax) - sym.Const(1e-06))) * ((gov_feedback_y - gov_deadBand_UMax) + gov_deadBand_EpsMax)) + ((sym.Const(1.0) - sym.heaviside(((gov_feedback_y - gov_deadBand_UMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_deadBand_UMin - gov_feedback_y) - sym.Const(1e-06))) * ((gov_feedback_y - gov_deadBand_UMin) + gov_deadBand_EpsMin)) + ((sym.Const(1.0) - sym.heaviside(((gov_deadBand_UMin - gov_feedback_y) - sym.Const(1e-06)))) * sym.Const(0.0)))))))
    algebraic_equations.append((gov_switch_y - ((gov_booleanConstant1_k * gov_deadBand_y) + ((sym.Const(1.0) - gov_booleanConstant1_k) * gov_feedback_y))))
    algebraic_equations.append((gov_transferFunction_x_1 - (gov_transferFunction_x_scaled_1 / gov_transferFunction_a_end)))
    algebraic_equations.append((gov_transferFunction_y - (((gov_transferFunction_bb_2 - (gov_transferFunction_d * gov_transferFunction_a_2)) * gov_transferFunction_x_1) + (gov_transferFunction_d * gov_switch_y))))
    algebraic_equations.append((gov_gain8_y - (gov_gain8_k * gov_firstOrder3_y)))
    algebraic_equations.append((gov_gain7_y - (gov_gain7_k * gov_firstOrder2_y)))
    algebraic_equations.append((gov_gain6_y - (gov_gain6_k * gov_firstOrder1_y)))
    algebraic_equations.append((gov_gain5_y - (gov_gain5_k * gov_firstOrder3_y)))
    algebraic_equations.append((gov_gain4_y - (gov_gain4_k * gov_firstOrder2_y)))
    algebraic_equations.append((gov_gain3_y - (gov_gain3_k * gov_firstOrder1_y)))
    algebraic_equations.append((gov_gain2_y - (gov_gain2_k * gov_firstOrder_y)))
    algebraic_equations.append((gov_add_y - ((gov_add_k1 * gov_gain6_y) + (gov_add_k2 * gov_gain2_y))))
    algebraic_equations.append((gov_add1_y - ((gov_add1_k1 * gov_gain7_y) + (gov_add1_k2 * gov_add_y))))
    algebraic_equations.append((gov_Pm2Pu - ((gov_add2_k1 * gov_gain8_y) + (gov_add2_k2 * gov_add1_y))))
    algebraic_equations.append((gov_gain1_y - (gov_gain1_k * gov_firstOrder_y)))
    algebraic_equations.append((gov_add4_y - ((gov_add4_k1 * gov_gain1_y) + (gov_add4_k2 * gov_gain3_y))))
    algebraic_equations.append((gov_add5_y - ((gov_add5_k1 * gov_add4_y) + (gov_add5_k2 * gov_gain4_y))))
    algebraic_equations.append((gov_Pm1Pu - ((gov_add6_k1 * gov_add5_y) + (gov_add6_k2 * gov_gain5_y))))
    algebraic_equations.append((gov_backlashHysteresis_y - (((gov_backlashHysteresis_h * sym.heaviside((((gov_backlashHysteresis_aux - gov_backlashHysteresis_UHigh) - gov_limitedIntegrator_y) + sym.Const(1e-06)))) * (gov_limitedIntegrator_y - gov_backlashHysteresis_ULow)) + ((sym.Const(1.0) - (gov_backlashHysteresis_h * sym.heaviside((((gov_backlashHysteresis_aux - gov_backlashHysteresis_UHigh) - gov_limitedIntegrator_y) + sym.Const(1e-06))))) * ((((sym.Const(1.0) - gov_backlashHysteresis_h) * sym.heaviside(((gov_limitedIntegrator_y - (gov_backlashHysteresis_aux - gov_backlashHysteresis_ULow)) + sym.Const(1e-06)))) * (gov_limitedIntegrator_y - gov_backlashHysteresis_UHigh)) + ((sym.Const(1.0) - ((sym.Const(1.0) - gov_backlashHysteresis_h) * sym.heaviside(((gov_limitedIntegrator_y - (gov_backlashHysteresis_aux - gov_backlashHysteresis_ULow)) + sym.Const(1e-06))))) * gov_backlashHysteresis_aux))))))
    algebraic_equations.append((gov_pgv_y_1 - (((((((sym.Const(0.0) * sym.heaviside(((sym.Const(0.0) - gov_backlashHysteresis_y) - sym.Const(1e-06)))) + ((((((sym.Const(0.25) - sym.Const(0.0)) / (sym.Const(0.25) - sym.Const(0.0))) * gov_backlashHysteresis_y) + (sym.Const(0.0) - (((sym.Const(0.25) - sym.Const(0.0)) / (sym.Const(0.25) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((gov_backlashHysteresis_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.25) - gov_backlashHysteresis_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.5) - sym.Const(0.25)) / (sym.Const(0.5) - sym.Const(0.25))) * gov_backlashHysteresis_y) + (sym.Const(0.25) - (((sym.Const(0.5) - sym.Const(0.25)) / (sym.Const(0.5) - sym.Const(0.25))) * sym.Const(0.25)))) * sym.heaviside(((gov_backlashHysteresis_y - sym.Const(0.25)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.5) - gov_backlashHysteresis_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.75) - sym.Const(0.5)) / (sym.Const(0.75) - sym.Const(0.5))) * gov_backlashHysteresis_y) + (sym.Const(0.5) - (((sym.Const(0.75) - sym.Const(0.5)) / (sym.Const(0.75) - sym.Const(0.5))) * sym.Const(0.5)))) * sym.heaviside(((gov_backlashHysteresis_y - sym.Const(0.5)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.75) - gov_backlashHysteresis_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0) - sym.Const(0.75)) / (sym.Const(1.0) - sym.Const(0.75))) * gov_backlashHysteresis_y) + (sym.Const(0.75) - (((sym.Const(1.0) - sym.Const(0.75)) / (sym.Const(1.0) - sym.Const(0.75))) * sym.Const(0.75)))) * sym.heaviside(((gov_backlashHysteresis_y - sym.Const(0.75)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - gov_backlashHysteresis_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.25) - sym.Const(1.0)) / (sym.Const(1.25) - sym.Const(1.0))) * gov_backlashHysteresis_y) + (sym.Const(1.0) - (((sym.Const(1.25) - sym.Const(1.0)) / (sym.Const(1.25) - sym.Const(1.0))) * sym.Const(1.0)))) * sym.heaviside(((gov_backlashHysteresis_y - sym.Const(1.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.25) - gov_backlashHysteresis_y) - sym.Const(1e-06))))) + (sym.Const(1.25) * sym.heaviside(((gov_backlashHysteresis_y - sym.Const(1.25)) + sym.Const(1e-06)))))))
    algebraic_equations.append((gov_switch1_y - ((gov_booleanConstant_k * gov_backlashHysteresis_y) + ((sym.Const(1.0) - gov_booleanConstant_k) * gov_limitedIntegrator_y))))
    algebraic_equations.append((gov_add3_y - (((gov_add3_k1 * gov_PmRefPu) + (gov_add3_k2 * gov_transferFunction_y)) + (gov_add3_k3 * gov_switch1_y))))
    algebraic_equations.append((gov_gain_y - (gov_gain_k * gov_add3_y)))
    algebraic_equations.append((gov_limiter_y - ((sym.heaviside(((gov_gain_y - gov_limiter_uMax) - sym.Const(1e-06))) * gov_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((gov_gain_y - gov_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_limiter_uMin - gov_gain_y) - sym.Const(1e-06))) * gov_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((gov_limiter_uMin - gov_gain_y) - sym.Const(1e-06)))) * gov_gain_y))))))
    algebraic_equations.append(((whenCondition2 - sym.heaviside((((-gov_backlashHysteresis_Tolerance) - d_gov_limitedIntegrator_y) - sym.Const(1e-06)))) - sym.heaviside(((gov_limitedIntegrator_y - gov_backlashHysteresis_UHigh) + sym.Const(1e-06)))))
    algebraic_equations.append(((whenCondition1 - sym.heaviside(((d_gov_limitedIntegrator_y - gov_backlashHysteresis_Tolerance) - sym.Const(1e-06)))) - sym.heaviside(((gov_backlashHysteresis_ULow - gov_limitedIntegrator_y) + sym.Const(1e-06)))))
    algebraic_equations.append((gov_switch2_y - ((gov_booleanConstant2_k * gov_pgv_y_1) + ((sym.Const(1.0) - gov_booleanConstant2_k) * gov_backlashHysteresis_y))))
    algebraic_equations.append((gov_backlashHysteresis_aux - (gov_limitedIntegrator_y - gov_backlashHysteresis_ULow)))
    algebraic_equations.append((gov_backlashHysteresis_h - sym.Const(0.0)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(gov_deadBand_y)
    algebraic_variables.append(gov_switch_y)
    algebraic_variables.append(gov_transferFunction_x_1)
    algebraic_variables.append(gov_transferFunction_y)
    algebraic_variables.append(gov_gain8_y)
    algebraic_variables.append(gov_gain7_y)
    algebraic_variables.append(gov_gain6_y)
    algebraic_variables.append(gov_gain5_y)
    algebraic_variables.append(gov_gain4_y)
    algebraic_variables.append(gov_gain3_y)
    algebraic_variables.append(gov_gain2_y)
    algebraic_variables.append(gov_add_y)
    algebraic_variables.append(gov_add1_y)
    algebraic_variables.append(gov_Pm2Pu)
    algebraic_variables.append(gov_gain1_y)
    algebraic_variables.append(gov_add4_y)
    algebraic_variables.append(gov_add5_y)
    algebraic_variables.append(gov_Pm1Pu)
    algebraic_variables.append(gov_backlashHysteresis_y)
    algebraic_variables.append(gov_pgv_y_1)
    algebraic_variables.append(gov_switch1_y)
    algebraic_variables.append(gov_add3_y)
    algebraic_variables.append(gov_gain_y)
    algebraic_variables.append(gov_limiter_y)
    algebraic_variables.append(whenCondition2)
    algebraic_variables.append(whenCondition1)
    algebraic_variables.append(gov_switch2_y)
    algebraic_variables.append(gov_backlashHysteresis_aux)
    algebraic_variables.append(gov_backlashHysteresis_h)
    algebraic_variables.append(gov_feedback_y)
    algebraic_variables.append(gov_PmRefPu)
    algebraic_variables.append(gov_omegaPu)
    algebraic_variables.append(gov_limitedIntegrator_local_reset)
    algebraic_variables.append(gov_limitedIntegrator_local_set)
    algebraic_variables.append(gov_limiter_simplifiedExpr)
    algebraic_variables.append(PRE_gov_backlashHysteresis_aux)
    algebraic_variables.append(START_gov_backlashHysteresis_aux)
    algebraic_variables.append(PRE_gov_backlashHysteresis_h)
    algebraic_variables.append(START_gov_backlashHysteresis_h)
    algebraic_variables.append(START_gov_firstOrder_y)
    algebraic_variables.append(START_gov_firstOrder1_y)
    algebraic_variables.append(START_gov_firstOrder2_y)
    algebraic_variables.append(START_gov_firstOrder3_y)
    algebraic_variables.append(START_gov_transferFunction_x_scaled_1)
    differential_variables: list[Var] = list()
    differential_variables.append(d_gov_transferFunction_x_scaled_1)
    differential_variables.append(d_gov_firstOrder3_y)
    differential_variables.append(d_gov_firstOrder2_y)
    differential_variables.append(d_gov_firstOrder1_y)
    differential_variables.append(d_gov_limitedIntegrator_y)
    differential_variables.append(d_gov_firstOrder_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[gov_Db1] = vf.add_const(0.0, name='')
    event_parameters[gov_Db2] = vf.add_const(0.0, name='')
    event_parameters[gov_Eps] = vf.add_const(0.0, name='')
    event_parameters[gov_K] = vf.add_const(25.0, name='')
    event_parameters[gov_K1] = vf.add_const(0.2, name='')
    event_parameters[gov_K2] = vf.add_const(0.0, name='')
    event_parameters[gov_K3] = vf.add_const(0.3, name='')
    event_parameters[gov_K4] = vf.add_const(0.0, name='')
    event_parameters[gov_K5] = vf.add_const(0.5, name='')
    event_parameters[gov_K6] = vf.add_const(0.0, name='')
    event_parameters[gov_K7] = vf.add_const(0.0, name='')
    event_parameters[gov_K8] = vf.add_const(0.0, name='')
    event_parameters[gov_PMaxPu] = vf.add_const(1.0, name='')
    event_parameters[gov_PMinPu] = vf.add_const(0.0, name='')
    event_parameters[gov_Pm0Pu] = vf.add_const(0.8, name='')
    event_parameters[gov_PmRef0Pu] = vf.add_const(0.8, name='')
    event_parameters[gov_Uc] = vf.add_const(-10.0, name='')
    event_parameters[gov_Uo] = vf.add_const(1.0, name='')
    event_parameters[gov_add_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_add_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_add1_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_add1_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_add2_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_add2_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_add3_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_add3_k2] = vf.add_const(-1.0, name='')
    event_parameters[gov_add3_k3] = vf.add_const(-1.0, name='')
    event_parameters[gov_add4_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_add4_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_add5_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_add5_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_add6_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_add6_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_backlashHysteresis_Aux0] = ((gov_backlashHysteresis_H0 * (((gov_backlashHysteresis_U0 - gov_backlashHysteresis_UHigh) * sym.heaviside(((gov_backlashHysteresis_U0 - gov_backlashHysteresis_UHigh) - sym.Const(0.0)))) + (sym.Const(0.0) * (sym.Const(1) - sym.heaviside(((gov_backlashHysteresis_U0 - gov_backlashHysteresis_UHigh) - sym.Const(0.0))))))) + ((sym.Const(1.0) - gov_backlashHysteresis_H0) * (((gov_backlashHysteresis_U0 - gov_backlashHysteresis_ULow) * sym.heaviside((sym.Const(0.0) - (gov_backlashHysteresis_U0 - gov_backlashHysteresis_ULow)))) + (sym.Const(0.0) * (sym.Const(1) - sym.heaviside((sym.Const(0.0) - (gov_backlashHysteresis_U0 - gov_backlashHysteresis_ULow))))))))
    event_parameters[gov_backlashHysteresis_Tolerance] = vf.add_const(1e-05, name='')
    event_parameters[gov_backlashHysteresis_U0] = gov_PmRef0Pu
    event_parameters[gov_backlashHysteresis_UHigh] = gov_Db2
    event_parameters[gov_backlashHysteresis_ULow] = (-gov_backlashHysteresis_UHigh)
    event_parameters[gov_const_k] = vf.add_const(1.0, name='')
    event_parameters[gov_deadBand_EpsMax] = gov_Eps
    event_parameters[gov_deadBand_EpsMin] = (-gov_deadBand_EpsMax)
    event_parameters[gov_deadBand_UMax] = gov_Db1
    event_parameters[gov_deadBand_UMin] = (-gov_deadBand_UMax)
    event_parameters[gov_firstOrder_T] = gov_t4
    event_parameters[gov_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrder_y_start] = gov_Pm0Pu
    event_parameters[gov_firstOrder1_T] = gov_t5
    event_parameters[gov_firstOrder1_k] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrder1_y_start] = gov_Pm0Pu
    event_parameters[gov_firstOrder2_T] = gov_t6
    event_parameters[gov_firstOrder2_k] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrder2_y_start] = gov_Pm0Pu
    event_parameters[gov_firstOrder3_T] = gov_t7
    event_parameters[gov_firstOrder3_k] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrder3_y_start] = gov_Pm0Pu
    event_parameters[gov_gain_k] = (sym.Const(1.0) / gov_t3)
    event_parameters[gov_gain1_k] = gov_K1
    event_parameters[gov_gain2_k] = gov_K2
    event_parameters[gov_gain3_k] = gov_K3
    event_parameters[gov_gain4_k] = gov_K5
    event_parameters[gov_gain5_k] = gov_K7
    event_parameters[gov_gain6_k] = gov_K4
    event_parameters[gov_gain7_k] = gov_K6
    event_parameters[gov_gain8_k] = gov_K8
    event_parameters[gov_limitedIntegrator_k] = vf.add_const(1.0, name='')
    event_parameters[gov_limitedIntegrator_outMax] = gov_PMaxPu
    event_parameters[gov_limitedIntegrator_outMin] = gov_PMinPu
    event_parameters[gov_limitedIntegrator_y_start] = gov_PmRef0Pu
    event_parameters[gov_limiter_uMax] = gov_Uo
    event_parameters[gov_limiter_uMin] = gov_Uc
    event_parameters[gov_pgv_u_max] = vf.add_const(1.25, name='')
    event_parameters[gov_pgv_u_min] = vf.add_const(0.0, name='')
    event_parameters[gov_t1] = vf.add_const(0.0, name='')
    event_parameters[gov_t2] = vf.add_const(0.0, name='')
    event_parameters[gov_t3] = vf.add_const(0.1, name='')
    event_parameters[gov_t4] = vf.add_const(0.3, name='')
    event_parameters[gov_t5] = vf.add_const(5.0, name='')
    event_parameters[gov_t6] = vf.add_const(0.5, name='')
    event_parameters[gov_t7] = vf.add_const(0.0, name='')
    event_parameters[gov_transferFunction_a_1] = gov_t1
    event_parameters[gov_transferFunction_a_2] = vf.add_const(1.0, name='')
    event_parameters[gov_transferFunction_a_end] = ((sym.heaviside(((gov_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((gov_transferFunction_a_1 ** sym.Const(2.0)) + (gov_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06))) * gov_transferFunction_a_2) + ((sym.Const(1.0) - sym.heaviside(((gov_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((gov_transferFunction_a_1 ** sym.Const(2.0)) + (gov_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06)))) * sym.Const(1.0)))
    event_parameters[gov_transferFunction_b_1] = (gov_K * gov_t2)
    event_parameters[gov_transferFunction_b_2] = gov_K
    event_parameters[gov_transferFunction_bb_1] = gov_transferFunction_b_1
    event_parameters[gov_transferFunction_bb_2] = gov_transferFunction_b_2
    event_parameters[gov_transferFunction_d] = (gov_transferFunction_bb_1 / gov_transferFunction_a_1)
    event_parameters[gov_transferFunction_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[gov_transferFunction_y_start] = vf.add_const(0.0, name='')
    event_parameters[gov_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrder1_initType] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrder2_initType] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrder3_initType] = vf.add_const(1.0, name='')
    event_parameters[gov_limitedIntegrator_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[gov_pgv_columns_1] = vf.add_const(2.0, name='')
    event_parameters[gov_pgv_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[gov_pgv_nout] = vf.add_const(1.0, name='')
    event_parameters[gov_pgv_smoothness] = vf.add_const(1.0, name='')
    event_parameters[gov_transferFunction_na] = vf.add_const(2.0, name='')
    event_parameters[gov_transferFunction_nb] = vf.add_const(2.0, name='')
    event_parameters[gov_transferFunction_nx] = vf.add_const(1.0, name='')
    event_parameters[gov_H0] = vf.add_const(0.0, name='')
    event_parameters[gov_Sdb1] = vf.add_const(1.0, name='')
    event_parameters[gov_Sdb2] = vf.add_const(1.0, name='')
    event_parameters[gov_ValveOn] = vf.add_const(1.0, name='')
    event_parameters[gov_backlashHysteresis_H0] = gov_H0
    event_parameters[gov_booleanConstant_k] = gov_Sdb2
    event_parameters[gov_booleanConstant1_k] = gov_Sdb1
    event_parameters[gov_booleanConstant2_k] = gov_ValveOn
    event_parameters[gov_limitedIntegrator_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limitedIntegrator_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limitedIntegrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[gov_limitedIntegrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[gov_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_pgv_tableOnFile] = vf.add_const(1.0, name='')
    event_parameters[gov_pgv_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[gov_pgv_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[gov_PgvTableName] = vf.add_const(0.0, name='')
    event_parameters[gov_TablesFile] = vf.add_const(0.0, name='')
    event_parameters[gov_pgv_fileName] = gov_TablesFile
    event_parameters[gov_pgv_tableName] = gov_PgvTableName
    event_parameters[gov_pgv_tableID] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[gov_firstOrder_y] = START_gov_firstOrder_y
    initial_equations[gov_firstOrder1_y] = START_gov_firstOrder1_y
    initial_equations[gov_firstOrder2_y] = START_gov_firstOrder2_y
    initial_equations[gov_firstOrder3_y] = START_gov_firstOrder3_y
    initial_equations[gov_limitedIntegrator_y] = gov_limitedIntegrator_y_start
    initial_equations[gov_transferFunction_x_scaled_1] = START_gov_transferFunction_x_scaled_1
    initial_equations[gov_Pm1Pu] = vf.add_const(0.8, name='')
    initial_equations[gov_Pm2Pu] = vf.add_const(0.0, name='')
    initial_equations[gov_PmRefPu] = vf.add_const(0.8, name='')
    initial_equations[gov_add_y] = vf.add_const(0.0, name='')
    initial_equations[gov_add1_y] = vf.add_const(0.0, name='')
    initial_equations[gov_add5_y] = vf.add_const(0.8, name='')
    initial_equations[gov_gain2_y] = vf.add_const(0.0, name='')
    initial_equations[gov_gain5_y] = vf.add_const(0.0, name='')
    initial_equations[gov_gain6_y] = vf.add_const(0.0, name='')
    initial_equations[gov_gain7_y] = vf.add_const(0.0, name='')
    initial_equations[gov_gain8_y] = vf.add_const(0.0, name='')
    initial_equations[gov_omegaPu] = vf.add_const(1.0, name='')
    initial_equations[gov_transferFunction_x_1] = gov_transferFunction_x_start_1
    initial_equations[gov_transferFunction_y] = gov_transferFunction_y_start
    initial_equations[gov_backlashHysteresis_aux] = PRE_gov_backlashHysteresis_aux
    initial_equations[gov_backlashHysteresis_h] = PRE_gov_backlashHysteresis_h
    initial_equations[gov_limitedIntegrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[gov_limitedIntegrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[gov_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[PRE_gov_backlashHysteresis_aux] = START_gov_backlashHysteresis_aux
    initial_equations[PRE_gov_backlashHysteresis_h] = START_gov_backlashHysteresis_h
    initial_equations[gov_feedback_y] = (sym.Const(1.0) - gov_const_k)
    initial_equations[gov_backlashHysteresis_y] = (((PRE_gov_backlashHysteresis_h * sym.heaviside((((PRE_gov_backlashHysteresis_aux - gov_backlashHysteresis_UHigh) - gov_limitedIntegrator_y) + sym.Const(1e-06)))) * (gov_limitedIntegrator_y - gov_backlashHysteresis_ULow)) + ((sym.Const(1.0) - (PRE_gov_backlashHysteresis_h * sym.heaviside((((PRE_gov_backlashHysteresis_aux - gov_backlashHysteresis_UHigh) - gov_limitedIntegrator_y) + sym.Const(1e-06))))) * ((((sym.Const(1.0) - PRE_gov_backlashHysteresis_h) * sym.heaviside(((gov_limitedIntegrator_y - (PRE_gov_backlashHysteresis_aux - gov_backlashHysteresis_ULow)) + sym.Const(1e-06)))) * (gov_limitedIntegrator_y - gov_backlashHysteresis_UHigh)) + ((sym.Const(1.0) - ((sym.Const(1.0) - PRE_gov_backlashHysteresis_h) * sym.heaviside(((gov_limitedIntegrator_y - (PRE_gov_backlashHysteresis_aux - gov_backlashHysteresis_ULow)) + sym.Const(1e-06))))) * PRE_gov_backlashHysteresis_aux))))
    initial_equations[whenCondition1] = (sym.heaviside(((d_gov_limitedIntegrator_y - gov_backlashHysteresis_Tolerance) - sym.Const(1e-06))) + sym.heaviside(((gov_backlashHysteresis_ULow - gov_limitedIntegrator_y) + sym.Const(1e-06))))
    initial_equations[whenCondition2] = (sym.heaviside((((-gov_backlashHysteresis_Tolerance) - d_gov_limitedIntegrator_y) - sym.Const(1e-06))) + sym.heaviside(((gov_limitedIntegrator_y - gov_backlashHysteresis_UHigh) + sym.Const(1e-06))))
    initial_equations[gov_add3_y] = (((gov_add3_k1 * gov_PmRefPu) + (gov_add3_k2 * gov_transferFunction_y)) + (gov_add3_k3 * gov_switch1_y))
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

    template.block.event_dict[gov_t1] = vf.add_const(1.0e-05, name='')
    template.block.event_dict[gov_t2] = vf.add_const(1.0e-05, name='')
    template.block.event_dict[gov_t7] = vf.add_const(1.0e-05, name='')
    template.block.state_eqs[4] = ((sym.Const(1.0) - (sym.heaviside((gov_limitedIntegrator_y - gov_limitedIntegrator_outMax) + sym.Const(1e-06)) * sym.heaviside(((gov_limitedIntegrator_k * gov_limiter_y) - sym.Const(0.0)) - sym.Const(1e-06)))) * (sym.Const(1.0) - (sym.heaviside((gov_limitedIntegrator_outMin - gov_limitedIntegrator_y) + sym.Const(1e-06)) * sym.heaviside((sym.Const(0.0) - (gov_limitedIntegrator_k * gov_limiter_y)) - sym.Const(1e-06)))) * (gov_limitedIntegrator_k * gov_limiter_y))
    template.block.algebraic_eqs[24] = (whenCondition2 - (sym.heaviside((((-gov_backlashHysteresis_Tolerance) - d_gov_limitedIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limitedIntegrator_y - gov_backlashHysteresis_UHigh) + sym.Const(1e-06)))))
    template.block.algebraic_eqs[25] = (whenCondition1 - (sym.heaviside(((d_gov_limitedIntegrator_y - gov_backlashHysteresis_Tolerance) - sym.Const(1e-06))) * sym.heaviside(((gov_backlashHysteresis_ULow - gov_limitedIntegrator_y) + sym.Const(1e-06)))))
    template.block.algebraic_eqs[27] = (gov_backlashHysteresis_aux - ((whenCondition2 * (gov_limitedIntegrator_y - gov_backlashHysteresis_UHigh)) + ((sym.Const(1.0) - whenCondition2) * ((whenCondition1 * (gov_limitedIntegrator_y - gov_backlashHysteresis_ULow)) + ((sym.Const(1.0) - whenCondition1) * PRE_gov_backlashHysteresis_aux)))))
    template.block.algebraic_eqs[28] = (gov_backlashHysteresis_h - (whenCondition2 + (PRE_gov_backlashHysteresis_h * (sym.Const(1.0) - whenCondition1) * (sym.Const(1.0) - whenCondition2))))
    template.block.init_eqs[gov_firstOrder_y] = gov_firstOrder_y_start
    template.block.init_eqs[gov_firstOrder1_y] = gov_firstOrder1_y_start
    template.block.init_eqs[gov_firstOrder2_y] = gov_firstOrder2_y_start
    template.block.init_eqs[gov_firstOrder3_y] = gov_firstOrder3_y_start
    template.block.init_eqs[gov_transferFunction_x_scaled_1] = (gov_transferFunction_a_end * gov_transferFunction_x_start_1)
    template.block.init_eqs[gov_Pm1Pu] = gov_Pm0Pu
    template.block.init_eqs[gov_PmRefPu] = gov_PmRef0Pu
    template.block.init_eqs[PRE_gov_backlashHysteresis_aux] = gov_backlashHysteresis_Aux0
    template.block.init_eqs[PRE_gov_backlashHysteresis_h] = gov_backlashHysteresis_H0

    template.comment = 'Generator steam governor GOVSTEAM1'
    return template
