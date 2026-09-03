# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'GovSteamEu'.

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

def _replace_assignment_equation(block: Block, target_var: Var, rhs_expr: Expr | Const | Var) -> None:
    """
    Replace the algebraic assignment associated with one symbolic variable.

    :param block: Governor block containing the algebraic equations.
    :type block: Block
    :param target_var: Assignment variable whose equation must be repaired.
    :type target_var: Var
    :param rhs_expr: Correct right-hand-side expression.
    :type rhs_expr: Expr | Const | Var
    :return: None.
    :rtype: None
    """
    equation_index: int
    equation_obj: object

    # Preserve the existing equation order so manifest shape and solver indexing remain stable.
    for equation_index, equation_obj in enumerate(block.algebraic_eqs):
        if isinstance(equation_obj, BinOp) and equation_obj.op == "-":
            if equation_obj.left is target_var or equation_obj.right is target_var:
                block.algebraic_eqs[equation_index] = target_var - rhs_expr
                return
            else:
                pass
        else:
            pass

    # A missing generated assignment is repaired during construction before solver allocation.
    block.algebraic_eqs.append(target_var - rhs_expr)

def _find_stem_in_block_or_events(stem: str, block: Block) -> Var | None:
    """
    Find one generated variable by stable symbolic-name prefix.

    :param stem: Stable generated-name prefix to locate.
    :type stem: str
    :param block: Symbolic block hierarchy to inspect.
    :type block: Block
    :return: Matching variable, or ``None`` when the prefix is absent.
    :rtype: Var | None
    """
    var_groups: tuple[list[Var], ...] = (
        block.in_vars,
        block.out_vars,
        block.algebraic_vars,
        block.state_vars,
        block.diff_vars,
    )
    var_group: list[Var]
    var_obj: Var
    child_block: Block
    result: Var | None

    # Inspect each fixed collection separately to avoid temporary concatenated lists.
    for var_group in var_groups:
        for var_obj in var_group:
            if var_obj.name.startswith(stem):
                return var_obj
            else:
                pass

    # Event parameters are a lookup dictionary, so their keys form the remaining local surface.
    for var_obj in block.event_dict.keys():
        if var_obj.name.startswith(stem):
            return var_obj
        else:
            pass

    # Recurse only after exhausting the local block to preserve deterministic first-match behavior.
    for child_block in block.children:
        result = _find_stem_in_block_or_events(stem=stem, block=child_block)
        if result is None:
            pass
        else:
            return result

    return None

def _repair_govsteameu_template(template: RmsModelTemplate) -> None:
    """
    Restore the missing public governor reference and measured-input paths in the imported GovSteamEU model.

    :param template: Materialized governor template to repair before solver compilation.
    :type template: RmsModelTemplate
    :return: None.
    :rtype: None
    """
    block: Block = template.block
    first_order_tf_t_y: Var | None = _find_stem_in_block_or_events("gov.firstOrdertfT.y", block)
    first_order_tf_t_k: Var | None = _find_stem_in_block_or_events("gov.firstOrdertfT.k", block)
    first_order_tf_t_t: Var | None = _find_stem_in_block_or_events("gov.firstOrdertfT.T", block)
    first_order_t_omega_y: Var | None = _find_stem_in_block_or_events("gov.firstOrdertOmega.y", block)
    first_order_t_omega_k: Var | None = _find_stem_in_block_or_events("gov.firstOrdertOmega.k", block)
    first_order_t_omega_t: Var | None = _find_stem_in_block_or_events("gov.firstOrdertOmega.T", block)
    f_pu: Var | None = _find_stem_in_block_or_events("gov.fPu", block)
    f_ref_pu: Var | None = _find_stem_in_block_or_events("gov.fRefPu", block)
    omega_pu: Var | None = _find_stem_in_block_or_events("gov.omegaPu", block)
    omega_ref_pu: Var | None = _find_stem_in_block_or_events("gov.omegaRefPu", block)
    p_ref_pu: Var | None = _find_stem_in_block_or_events("gov.PRefPu", block)
    p_gen_pu: Var | None = _find_stem_in_block_or_events("gov.PGenPu", block)
    addf_ref_y: Var | None = _find_stem_in_block_or_events("gov.addfRef.y", block)
    addf_ref_k1: Var | None = _find_stem_in_block_or_events("gov.addfRef.k1", block)
    addf_ref_k2: Var | None = _find_stem_in_block_or_events("gov.addfRef.k2", block)
    add_omega_omega_ref_y: Var | None = _find_stem_in_block_or_events("gov.addOmegaOmegaRef.y", block)
    add_omega_omega_ref_k1: Var | None = _find_stem_in_block_or_events("gov.addOmegaOmegaRef.k1", block)
    add_omega_omega_ref_k2: Var | None = _find_stem_in_block_or_events("gov.addOmegaOmegaRef.k2", block)
    limiter_delta_f_y: Var | None = _find_stem_in_block_or_events("gov.limiterDeltaF.y", block)
    add_p_ref_y: Var | None = _find_stem_in_block_or_events("gov.addPRef.y", block)
    add_p_ref_k1: Var | None = _find_stem_in_block_or_events("gov.addPRef.k1", block)
    add_p_ref_k2: Var | None = _find_stem_in_block_or_events("gov.addPRef.k2", block)
    gain_change_base_y: Var | None = _find_stem_in_block_or_events("gov.gainChangeBase.y", block)
    gain_change_base_k: Var | None = _find_stem_in_block_or_events("gov.gainChangeBase.k", block)
    first_order_t_p_y: Var | None = _find_stem_in_block_or_events("gov.firstOrdertP.y", block)
    first_order_t_p_y_start: Var | None = _find_stem_in_block_or_events("gov.firstOrdertP.y_start", block)

    required_vars: tuple[Var | None, ...] = (
        first_order_tf_t_y,
        first_order_tf_t_k,
        first_order_tf_t_t,
        first_order_t_omega_y,
        first_order_t_omega_k,
        first_order_t_omega_t,
        f_pu,
        f_ref_pu,
        omega_pu,
        omega_ref_pu,
        p_ref_pu,
        p_gen_pu,
        addf_ref_y,
        addf_ref_k1,
        addf_ref_k2,
        add_omega_omega_ref_y,
        add_omega_omega_ref_k1,
        add_omega_omega_ref_k2,
        limiter_delta_f_y,
        add_p_ref_y,
        add_p_ref_k1,
        add_p_ref_k2,
        gain_change_base_y,
        gain_change_base_k,
        first_order_t_p_y,
        first_order_t_p_y_start,
    )

    required_var: Var | None
    all_required_vars_found: bool = True
    for required_var in required_vars:
        if required_var is None:
            all_required_vars_found = False
        else:
            pass

    # A partial repair would silently alter the governor equations, so fail the invalid build state.
    if all_required_vars_found:
        pass
    else:
        raise KeyError("Could not repair GovSteamEu because one or more required symbolic variables were not found")

    state_index: int = block.state_vars.index(first_order_tf_t_y)
    block.state_eqs[state_index] = ((first_order_tf_t_k * f_pu) - first_order_tf_t_y) / first_order_tf_t_t
    state_index = block.state_vars.index(first_order_t_omega_y)
    block.state_eqs[state_index] = ((first_order_t_omega_k * omega_pu) - first_order_t_omega_y) / first_order_t_omega_t

    # Restore the four public signal paths documented for the governor controller.
    addf_ref_expr: Expr = (addf_ref_k1 * f_ref_pu) + (addf_ref_k2 * first_order_tf_t_y)
    add_omega_omega_ref_expr: Expr = (
        (add_omega_omega_ref_k1 * omega_ref_pu)
        + (add_omega_omega_ref_k2 * first_order_t_omega_y)
    )
    add_p_ref_expr: Expr = (add_p_ref_k1 * limiter_delta_f_y) + (add_p_ref_k2 * p_ref_pu)
    gain_change_base_expr: Expr = p_gen_pu * gain_change_base_k

    _replace_assignment_equation(block=block, target_var=addf_ref_y, rhs_expr=addf_ref_expr)
    _replace_assignment_equation(block=block, target_var=add_omega_omega_ref_y, rhs_expr=add_omega_omega_ref_expr)
    _replace_assignment_equation(block=block, target_var=add_p_ref_y, rhs_expr=add_p_ref_expr)
    _replace_assignment_equation(block=block, target_var=gain_change_base_y, rhs_expr=gain_change_base_expr)

    block.init_eqs[first_order_tf_t_y] = first_order_tf_t_k * f_pu
    block.init_eqs[first_order_t_omega_y] = first_order_t_omega_k * omega_pu
    block.init_eqs[first_order_t_p_y] = first_order_t_p_y_start
    block.init_eqs[addf_ref_y] = addf_ref_expr
    block.init_eqs[add_omega_omega_ref_y] = add_omega_omega_ref_expr
    block.init_eqs[add_p_ref_y] = add_p_ref_expr
    block.init_eqs[gain_change_base_y] = gain_change_base_expr

def build_govsteameu_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'GovSteamEu'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    gov_AddGovController_k1: Var = vf.add_var('gov.AddGovController.k1_' + template_name)
    gov_AddGovController_k2: Var = vf.add_var('gov.AddGovController.k2_' + template_name)
    gov_AddGovController_k3: Var = vf.add_var('gov.AddGovController.k3_' + template_name)
    gov_CHcPu: Var = vf.add_var('gov.CHcPu_' + template_name)
    gov_CHoPu: Var = vf.add_var('gov.CHoPu_' + template_name)
    gov_CIcPu: Var = vf.add_var('gov.CIcPu_' + template_name)
    gov_CIoPu: Var = vf.add_var('gov.CIoPu_' + template_name)
    gov_DeltaOmegaDbPu: Var = vf.add_var('gov.DeltaOmegaDbPu_' + template_name)
    gov_DeltafDbPu: Var = vf.add_var('gov.DeltafDbPu_' + template_name)
    gov_HHpMaxPu: Var = vf.add_var('gov.HHpMaxPu_' + template_name)
    gov_KE: Var = vf.add_var('gov.KE_' + template_name)
    gov_KFCor: Var = vf.add_var('gov.KFCor_' + template_name)
    gov_KHp: Var = vf.add_var('gov.KHp_' + template_name)
    gov_KLp: Var = vf.add_var('gov.KLp_' + template_name)
    gov_KOmegaCor: Var = vf.add_var('gov.KOmegaCor_' + template_name)
    gov_OmegaFMaxPu: Var = vf.add_var('gov.OmegaFMaxPu_' + template_name)
    gov_OmegaFMinPu: Var = vf.add_var('gov.OmegaFMinPu_' + template_name)
    gov_OmegaMax1Pu: Var = vf.add_var('gov.OmegaMax1Pu_' + template_name)
    gov_OmegaMax2Pu: Var = vf.add_var('gov.OmegaMax2Pu_' + template_name)
    gov_OmegaOmegaMaxPu: Var = vf.add_var('gov.OmegaOmegaMaxPu_' + template_name)
    gov_OmegaOmegaMinPu: Var = vf.add_var('gov.OmegaOmegaMinPu_' + template_name)
    gov_PBaseMw: Var = vf.add_var('gov.PBaseMw_' + template_name)
    gov_PGen0Pu: Var = vf.add_var('gov.PGen0Pu_' + template_name)
    gov_PGenBaseMw: Var = vf.add_var('gov.PGenBaseMw_' + template_name)
    gov_PMaxPu: Var = vf.add_var('gov.PMaxPu_' + template_name)
    gov_PRef0Pu: Var = vf.add_var('gov.PRef0Pu_' + template_name)
    gov_PRhMaxPu: Var = vf.add_var('gov.PRhMaxPu_' + template_name)
    gov_Pm0Pu: Var = vf.add_var('gov.Pm0Pu_' + template_name)
    gov_SimxPu: Var = vf.add_var('gov.SimxPu_' + template_name)
    gov_addCtrlOp_k1: Var = vf.add_var('gov.addCtrlOp.k1_' + template_name)
    gov_addCtrlOp_k2: Var = vf.add_var('gov.addCtrlOp.k2_' + template_name)
    gov_addCv_k1: Var = vf.add_var('gov.addCv.k1_' + template_name)
    gov_addCv_k2: Var = vf.add_var('gov.addCv.k2_' + template_name)
    gov_addLpKHpPu_k1: Var = vf.add_var('gov.addLpKHpPu.k1_' + template_name)
    gov_addLpKHpPu_k2: Var = vf.add_var('gov.addLpKHpPu.k2_' + template_name)
    gov_addOmegaOmegaRef_k1: Var = vf.add_var('gov.addOmegaOmegaRef.k1_' + template_name)
    gov_addOmegaOmegaRef_k2: Var = vf.add_var('gov.addOmegaOmegaRef.k2_' + template_name)
    gov_addPRef_k1: Var = vf.add_var('gov.addPRef.k1_' + template_name)
    gov_addPRef_k2: Var = vf.add_var('gov.addPRef.k2_' + template_name)
    gov_addPe_k1: Var = vf.add_var('gov.addPe.k1_' + template_name)
    gov_addPe_k2: Var = vf.add_var('gov.addPe.k2_' + template_name)
    gov_addPt1Boiler_k1: Var = vf.add_var('gov.addPt1Boiler.k1_' + template_name)
    gov_addPt1Boiler_k2: Var = vf.add_var('gov.addPt1Boiler.k2_' + template_name)
    gov_addPt1Iv_k1: Var = vf.add_var('gov.addPt1Iv.k1_' + template_name)
    gov_addPt1Iv_k2: Var = vf.add_var('gov.addPt1Iv.k2_' + template_name)
    gov_addPt1Rh_k1: Var = vf.add_var('gov.addPt1Rh.k1_' + template_name)
    gov_addPt1Rh_k2: Var = vf.add_var('gov.addPt1Rh.k2_' + template_name)
    gov_addfRef_k1: Var = vf.add_var('gov.addfRef.k1_' + template_name)
    gov_addfRef_k2: Var = vf.add_var('gov.addfRef.k2_' + template_name)
    gov_combiTableEmergency_columns_1: Var = vf.add_var('gov.combiTableEmergency.columns[1]_' + template_name)
    gov_combiTableEmergency_extrapolation: Var = vf.add_var('gov.combiTableEmergency.extrapolation_' + template_name)
    gov_combiTableEmergency_fileName: Var = vf.add_var('gov.combiTableEmergency.fileName_' + template_name)
    gov_combiTableEmergency_n: Var = vf.add_var('gov.combiTableEmergency.n_' + template_name)
    gov_combiTableEmergency_smoothness: Var = vf.add_var('gov.combiTableEmergency.smoothness_' + template_name)
    gov_combiTableEmergency_tableID: Var = vf.add_var('gov.combiTableEmergency.tableID_' + template_name)
    gov_combiTableEmergency_tableName: Var = vf.add_var('gov.combiTableEmergency.tableName_' + template_name)
    gov_combiTableEmergency_tableOnFile: Var = vf.add_var('gov.combiTableEmergency.tableOnFile_' + template_name)
    gov_combiTableEmergency_table_1_1: Var = vf.add_var('gov.combiTableEmergency.table[1,1]_' + template_name)
    gov_combiTableEmergency_table_1_2: Var = vf.add_var('gov.combiTableEmergency.table[1,2]_' + template_name)
    gov_combiTableEmergency_table_2_1: Var = vf.add_var('gov.combiTableEmergency.table[2,1]_' + template_name)
    gov_combiTableEmergency_table_2_2: Var = vf.add_var('gov.combiTableEmergency.table[2,2]_' + template_name)
    gov_combiTableEmergency_table_3_1: Var = vf.add_var('gov.combiTableEmergency.table[3,1]_' + template_name)
    gov_combiTableEmergency_table_3_2: Var = vf.add_var('gov.combiTableEmergency.table[3,2]_' + template_name)
    gov_combiTableEmergency_table_4_1: Var = vf.add_var('gov.combiTableEmergency.table[4,1]_' + template_name)
    gov_combiTableEmergency_table_4_2: Var = vf.add_var('gov.combiTableEmergency.table[4,2]_' + template_name)
    gov_combiTableEmergency_u_max: Var = vf.add_var('gov.combiTableEmergency.u_max_' + template_name)
    gov_combiTableEmergency_u_min: Var = vf.add_var('gov.combiTableEmergency.u_min_' + template_name)
    gov_combiTableEmergency_verboseExtrapolation: Var = vf.add_var('gov.combiTableEmergency.verboseExtrapolation_' + template_name)
    gov_combiTableEmergency_verboseRead: Var = vf.add_var('gov.combiTableEmergency.verboseRead_' + template_name)
    gov_combiTableSimx_columns_1: Var = vf.add_var('gov.combiTableSimx.columns[1]_' + template_name)
    gov_combiTableSimx_extrapolation: Var = vf.add_var('gov.combiTableSimx.extrapolation_' + template_name)
    gov_combiTableSimx_fileName: Var = vf.add_var('gov.combiTableSimx.fileName_' + template_name)
    gov_combiTableSimx_n: Var = vf.add_var('gov.combiTableSimx.n_' + template_name)
    gov_combiTableSimx_smoothness: Var = vf.add_var('gov.combiTableSimx.smoothness_' + template_name)
    gov_combiTableSimx_tableID: Var = vf.add_var('gov.combiTableSimx.tableID_' + template_name)
    gov_combiTableSimx_tableName: Var = vf.add_var('gov.combiTableSimx.tableName_' + template_name)
    gov_combiTableSimx_tableOnFile: Var = vf.add_var('gov.combiTableSimx.tableOnFile_' + template_name)
    gov_combiTableSimx_table_1_1: Var = vf.add_var('gov.combiTableSimx.table[1,1]_' + template_name)
    gov_combiTableSimx_table_1_2: Var = vf.add_var('gov.combiTableSimx.table[1,2]_' + template_name)
    gov_combiTableSimx_table_2_1: Var = vf.add_var('gov.combiTableSimx.table[2,1]_' + template_name)
    gov_combiTableSimx_table_2_2: Var = vf.add_var('gov.combiTableSimx.table[2,2]_' + template_name)
    gov_combiTableSimx_table_3_1: Var = vf.add_var('gov.combiTableSimx.table[3,1]_' + template_name)
    gov_combiTableSimx_table_3_2: Var = vf.add_var('gov.combiTableSimx.table[3,2]_' + template_name)
    gov_combiTableSimx_u_max: Var = vf.add_var('gov.combiTableSimx.u_max_' + template_name)
    gov_combiTableSimx_u_min: Var = vf.add_var('gov.combiTableSimx.u_min_' + template_name)
    gov_combiTableSimx_verboseExtrapolation: Var = vf.add_var('gov.combiTableSimx.verboseExtrapolation_' + template_name)
    gov_combiTableSimx_verboseRead: Var = vf.add_var('gov.combiTableSimx.verboseRead_' + template_name)
    gov_deadZoneFrequency_deadZoneAtInit: Var = vf.add_var('gov.deadZoneFrequency.deadZoneAtInit_' + template_name)
    gov_deadZoneFrequency_uMax: Var = vf.add_var('gov.deadZoneFrequency.uMax_' + template_name)
    gov_deadZoneFrequency_uMin: Var = vf.add_var('gov.deadZoneFrequency.uMin_' + template_name)
    gov_deadZoneOmega_deadZoneAtInit: Var = vf.add_var('gov.deadZoneOmega.deadZoneAtInit_' + template_name)
    gov_deadZoneOmega_uMax: Var = vf.add_var('gov.deadZoneOmega.uMax_' + template_name)
    gov_deadZoneOmega_uMin: Var = vf.add_var('gov.deadZoneOmega.uMin_' + template_name)
    gov_derivativetDPctPc_T: Var = vf.add_var('gov.derivativetDPctPc.T_' + template_name)
    gov_derivativetDPctPc_initType: Var = vf.add_var('gov.derivativetDPctPc.initType_' + template_name)
    gov_derivativetDPctPc_k: Var = vf.add_var('gov.derivativetDPctPc.k_' + template_name)
    gov_derivativetDPctPc_x_start: Var = vf.add_var('gov.derivativetDPctPc.x_start_' + template_name)
    gov_derivativetDPctPc_y_start: Var = vf.add_var('gov.derivativetDPctPc.y_start_' + template_name)
    gov_derivativetDPctPc_zeroGain: Var = vf.add_var('gov.derivativetDPctPc.zeroGain_' + template_name)
    gov_firstOrdertEn_T: Var = vf.add_var('gov.firstOrdertEn.T_' + template_name)
    gov_firstOrdertEn_initType: Var = vf.add_var('gov.firstOrdertEn.initType_' + template_name)
    gov_firstOrdertEn_k: Var = vf.add_var('gov.firstOrdertEn.k_' + template_name)
    gov_firstOrdertEn_y_start: Var = vf.add_var('gov.firstOrdertEn.y_start_' + template_name)
    gov_firstOrdertHp_T: Var = vf.add_var('gov.firstOrdertHp.T_' + template_name)
    gov_firstOrdertHp_initType: Var = vf.add_var('gov.firstOrdertHp.initType_' + template_name)
    gov_firstOrdertHp_k: Var = vf.add_var('gov.firstOrdertHp.k_' + template_name)
    gov_firstOrdertHp_y_start: Var = vf.add_var('gov.firstOrdertHp.y_start_' + template_name)
    gov_firstOrdertLp_T: Var = vf.add_var('gov.firstOrdertLp.T_' + template_name)
    gov_firstOrdertLp_initType: Var = vf.add_var('gov.firstOrdertLp.initType_' + template_name)
    gov_firstOrdertLp_k: Var = vf.add_var('gov.firstOrdertLp.k_' + template_name)
    gov_firstOrdertLp_y_start: Var = vf.add_var('gov.firstOrdertLp.y_start_' + template_name)
    gov_firstOrdertOmega_T: Var = vf.add_var('gov.firstOrdertOmega.T_' + template_name)
    gov_firstOrdertOmega_initType: Var = vf.add_var('gov.firstOrdertOmega.initType_' + template_name)
    gov_firstOrdertOmega_k: Var = vf.add_var('gov.firstOrdertOmega.k_' + template_name)
    gov_firstOrdertOmega_y_start: Var = vf.add_var('gov.firstOrdertOmega.y_start_' + template_name)
    gov_firstOrdertP_T: Var = vf.add_var('gov.firstOrdertP.T_' + template_name)
    gov_firstOrdertP_initType: Var = vf.add_var('gov.firstOrdertP.initType_' + template_name)
    gov_firstOrdertP_k: Var = vf.add_var('gov.firstOrdertP.k_' + template_name)
    gov_firstOrdertP_y_start: Var = vf.add_var('gov.firstOrdertP.y_start_' + template_name)
    gov_firstOrdertfT_T: Var = vf.add_var('gov.firstOrdertfT.T_' + template_name)
    gov_firstOrdertfT_initType: Var = vf.add_var('gov.firstOrdertfT.initType_' + template_name)
    gov_firstOrdertfT_k: Var = vf.add_var('gov.firstOrdertfT.k_' + template_name)
    gov_firstOrdertfT_y_start: Var = vf.add_var('gov.firstOrdertfT.y_start_' + template_name)
    gov_gainChangeBase_k: Var = vf.add_var('gov.gainChangeBase.k_' + template_name)
    gov_gainCv_k: Var = vf.add_var('gov.gainCv.k_' + template_name)
    gov_gainFCor_k: Var = vf.add_var('gov.gainFCor.k_' + template_name)
    gov_gainIv_k: Var = vf.add_var('gov.gainIv.k_' + template_name)
    gov_gainKEPu_k: Var = vf.add_var('gov.gainKEPu.k_' + template_name)
    gov_gainKHpPu_k: Var = vf.add_var('gov.gainKHpPu.k_' + template_name)
    gov_gainKOmegaCorPu_k: Var = vf.add_var('gov.gainKOmegaCorPu.k_' + template_name)
    gov_initBPu: Var = vf.add_var('gov.initBPu_' + template_name)
    gov_initPcPu: Var = vf.add_var('gov.initPcPu_' + template_name)
    gov_integratortB_initType: Var = vf.add_var('gov.integratortB.initType_' + template_name)
    gov_integratortB_k: Var = vf.add_var('gov.integratortB.k_' + template_name)
    gov_integratortB_use_reset: Var = vf.add_var('gov.integratortB.use_reset_' + template_name)
    gov_integratortB_use_set: Var = vf.add_var('gov.integratortB.use_set_' + template_name)
    gov_integratortB_y_start: Var = vf.add_var('gov.integratortB.y_start_' + template_name)
    gov_limIntegratorCv_initType: Var = vf.add_var('gov.limIntegratorCv.initType_' + template_name)
    gov_limIntegratorCv_k: Var = vf.add_var('gov.limIntegratorCv.k_' + template_name)
    gov_limIntegratorCv_limitsAtInit: Var = vf.add_var('gov.limIntegratorCv.limitsAtInit_' + template_name)
    gov_limIntegratorCv_outMax: Var = vf.add_var('gov.limIntegratorCv.outMax_' + template_name)
    gov_limIntegratorCv_outMin: Var = vf.add_var('gov.limIntegratorCv.outMin_' + template_name)
    gov_limIntegratorCv_strict: Var = vf.add_var('gov.limIntegratorCv.strict_' + template_name)
    gov_limIntegratorCv_use_reset: Var = vf.add_var('gov.limIntegratorCv.use_reset_' + template_name)
    gov_limIntegratorCv_use_set: Var = vf.add_var('gov.limIntegratorCv.use_set_' + template_name)
    gov_limIntegratorCv_y_start: Var = vf.add_var('gov.limIntegratorCv.y_start_' + template_name)
    gov_limIntegratorIv_initType: Var = vf.add_var('gov.limIntegratorIv.initType_' + template_name)
    gov_limIntegratorIv_k: Var = vf.add_var('gov.limIntegratorIv.k_' + template_name)
    gov_limIntegratorIv_limitsAtInit: Var = vf.add_var('gov.limIntegratorIv.limitsAtInit_' + template_name)
    gov_limIntegratorIv_outMax: Var = vf.add_var('gov.limIntegratorIv.outMax_' + template_name)
    gov_limIntegratorIv_outMin: Var = vf.add_var('gov.limIntegratorIv.outMin_' + template_name)
    gov_limIntegratorIv_strict: Var = vf.add_var('gov.limIntegratorIv.strict_' + template_name)
    gov_limIntegratorIv_use_reset: Var = vf.add_var('gov.limIntegratorIv.use_reset_' + template_name)
    gov_limIntegratorIv_use_set: Var = vf.add_var('gov.limIntegratorIv.use_set_' + template_name)
    gov_limIntegratorIv_y_start: Var = vf.add_var('gov.limIntegratorIv.y_start_' + template_name)
    gov_limIntegratorPID_initType: Var = vf.add_var('gov.limIntegratorPID.initType_' + template_name)
    gov_limIntegratorPID_k: Var = vf.add_var('gov.limIntegratorPID.k_' + template_name)
    gov_limIntegratorPID_limitsAtInit: Var = vf.add_var('gov.limIntegratorPID.limitsAtInit_' + template_name)
    gov_limIntegratorPID_outMax: Var = vf.add_var('gov.limIntegratorPID.outMax_' + template_name)
    gov_limIntegratorPID_outMin: Var = vf.add_var('gov.limIntegratorPID.outMin_' + template_name)
    gov_limIntegratorPID_strict: Var = vf.add_var('gov.limIntegratorPID.strict_' + template_name)
    gov_limIntegratorPID_use_reset: Var = vf.add_var('gov.limIntegratorPID.use_reset_' + template_name)
    gov_limIntegratorPID_use_set: Var = vf.add_var('gov.limIntegratorPID.use_set_' + template_name)
    gov_limIntegratorPID_y_start: Var = vf.add_var('gov.limIntegratorPID.y_start_' + template_name)
    gov_limIntegratortRh_initType: Var = vf.add_var('gov.limIntegratortRh.initType_' + template_name)
    gov_limIntegratortRh_k: Var = vf.add_var('gov.limIntegratortRh.k_' + template_name)
    gov_limIntegratortRh_limitsAtInit: Var = vf.add_var('gov.limIntegratortRh.limitsAtInit_' + template_name)
    gov_limIntegratortRh_outMax: Var = vf.add_var('gov.limIntegratortRh.outMax_' + template_name)
    gov_limIntegratortRh_outMin: Var = vf.add_var('gov.limIntegratortRh.outMin_' + template_name)
    gov_limIntegratortRh_strict: Var = vf.add_var('gov.limIntegratortRh.strict_' + template_name)
    gov_limIntegratortRh_use_reset: Var = vf.add_var('gov.limIntegratortRh.use_reset_' + template_name)
    gov_limIntegratortRh_use_set: Var = vf.add_var('gov.limIntegratortRh.use_set_' + template_name)
    gov_limIntegratortRh_y_start: Var = vf.add_var('gov.limIntegratortRh.y_start_' + template_name)
    gov_limiterCv_homotopyType: Var = vf.add_var('gov.limiterCv.homotopyType_' + template_name)
    gov_limiterCv_limitsAtInit: Var = vf.add_var('gov.limiterCv.limitsAtInit_' + template_name)
    gov_limiterCv_strict: Var = vf.add_var('gov.limiterCv.strict_' + template_name)
    gov_limiterCv_uMax: Var = vf.add_var('gov.limiterCv.uMax_' + template_name)
    gov_limiterCv_uMin: Var = vf.add_var('gov.limiterCv.uMin_' + template_name)
    gov_limiterDeltaF_homotopyType: Var = vf.add_var('gov.limiterDeltaF.homotopyType_' + template_name)
    gov_limiterDeltaF_limitsAtInit: Var = vf.add_var('gov.limiterDeltaF.limitsAtInit_' + template_name)
    gov_limiterDeltaF_strict: Var = vf.add_var('gov.limiterDeltaF.strict_' + template_name)
    gov_limiterDeltaF_uMax: Var = vf.add_var('gov.limiterDeltaF.uMax_' + template_name)
    gov_limiterDeltaF_uMin: Var = vf.add_var('gov.limiterDeltaF.uMin_' + template_name)
    gov_limiterDeltaOmega_homotopyType: Var = vf.add_var('gov.limiterDeltaOmega.homotopyType_' + template_name)
    gov_limiterDeltaOmega_limitsAtInit: Var = vf.add_var('gov.limiterDeltaOmega.limitsAtInit_' + template_name)
    gov_limiterDeltaOmega_strict: Var = vf.add_var('gov.limiterDeltaOmega.strict_' + template_name)
    gov_limiterDeltaOmega_uMax: Var = vf.add_var('gov.limiterDeltaOmega.uMax_' + template_name)
    gov_limiterDeltaOmega_uMin: Var = vf.add_var('gov.limiterDeltaOmega.uMin_' + template_name)
    gov_limiterIv_homotopyType: Var = vf.add_var('gov.limiterIv.homotopyType_' + template_name)
    gov_limiterIv_limitsAtInit: Var = vf.add_var('gov.limiterIv.limitsAtInit_' + template_name)
    gov_limiterIv_strict: Var = vf.add_var('gov.limiterIv.strict_' + template_name)
    gov_limiterIv_uMax: Var = vf.add_var('gov.limiterIv.uMax_' + template_name)
    gov_limiterIv_uMin: Var = vf.add_var('gov.limiterIv.uMin_' + template_name)
    gov_limiterP_homotopyType: Var = vf.add_var('gov.limiterP.homotopyType_' + template_name)
    gov_limiterP_limitsAtInit: Var = vf.add_var('gov.limiterP.limitsAtInit_' + template_name)
    gov_limiterP_strict: Var = vf.add_var('gov.limiterP.strict_' + template_name)
    gov_limiterP_uMax: Var = vf.add_var('gov.limiterP.uMax_' + template_name)
    gov_limiterP_uMin: Var = vf.add_var('gov.limiterP.uMin_' + template_name)
    gov_limiterP2_homotopyType: Var = vf.add_var('gov.limiterP2.homotopyType_' + template_name)
    gov_limiterP2_limitsAtInit: Var = vf.add_var('gov.limiterP2.limitsAtInit_' + template_name)
    gov_limiterP2_strict: Var = vf.add_var('gov.limiterP2.strict_' + template_name)
    gov_limiterP2_uMax: Var = vf.add_var('gov.limiterP2.uMax_' + template_name)
    gov_limiterP2_uMin: Var = vf.add_var('gov.limiterP2.uMin_' + template_name)
    gov_tB: Var = vf.add_var('gov.tB_' + template_name)
    gov_tDp: Var = vf.add_var('gov.tDp_' + template_name)
    gov_tEn: Var = vf.add_var('gov.tEn_' + template_name)
    gov_tF: Var = vf.add_var('gov.tF_' + template_name)
    gov_tFp: Var = vf.add_var('gov.tFp_' + template_name)
    gov_tHp: Var = vf.add_var('gov.tHp_' + template_name)
    gov_tIp: Var = vf.add_var('gov.tIp_' + template_name)
    gov_tLp: Var = vf.add_var('gov.tLp_' + template_name)
    gov_tOmega: Var = vf.add_var('gov.tOmega_' + template_name)
    gov_tP: Var = vf.add_var('gov.tP_' + template_name)
    gov_tRh: Var = vf.add_var('gov.tRh_' + template_name)
    gov_tVHp: Var = vf.add_var('gov.tVHp_' + template_name)
    gov_tVLp: Var = vf.add_var('gov.tVLp_' + template_name)
    # Declare the state variables used by the template.
    gov_derivativetDPctPc_x: Var = vf.add_var('gov.derivativetDPctPc.x_' + template_name)
    gov_firstOrdertEn_y: Var = vf.add_var('gov.firstOrdertEn.y_' + template_name)
    gov_firstOrdertHp_y: Var = vf.add_var('gov.firstOrdertHp.y_' + template_name)
    gov_firstOrdertLp_y: Var = vf.add_var('gov.firstOrdertLp.y_' + template_name)
    gov_firstOrdertOmega_y: Var = vf.add_var('gov.firstOrdertOmega.y_' + template_name)
    gov_firstOrdertP_y: Var = vf.add_var('gov.firstOrdertP.y_' + template_name)
    gov_firstOrdertfT_y: Var = vf.add_var('gov.firstOrdertfT.y_' + template_name)
    gov_integratortB_y: Var = vf.add_var('gov.integratortB.y_' + template_name)
    gov_limIntegratorCv_y: Var = vf.add_var('gov.limIntegratorCv.y_' + template_name)
    gov_limIntegratorIv_y: Var = vf.add_var('gov.limIntegratorIv.y_' + template_name)
    gov_limIntegratorPID_y: Var = vf.add_var('gov.limIntegratorPID.y_' + template_name)
    gov_limIntegratortRh_y: Var = vf.add_var('gov.limIntegratortRh.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    gov_AddGovController_y: Var = vf.add_var('gov.AddGovController.y_' + template_name)
    gov_PGenPu: Var = vf.add_var('gov.PGenPu_' + template_name)
    gov_PRefPu: Var = vf.add_var('gov.PRefPu_' + template_name)
    gov_PmPu: Var = vf.add_var('gov.PmPu_' + template_name)
    gov_addCtrlOp_y: Var = vf.add_var('gov.addCtrlOp.y_' + template_name)
    gov_addCv_y: Var = vf.add_var('gov.addCv.y_' + template_name)
    gov_addOmegaOmegaRef_y: Var = vf.add_var('gov.addOmegaOmegaRef.y_' + template_name)
    gov_addPRef_y: Var = vf.add_var('gov.addPRef.y_' + template_name)
    gov_addPe_y: Var = vf.add_var('gov.addPe.y_' + template_name)
    gov_addPt1Boiler_y: Var = vf.add_var('gov.addPt1Boiler.y_' + template_name)
    gov_addPt1Iv_y: Var = vf.add_var('gov.addPt1Iv.y_' + template_name)
    gov_addPt1Rh_y: Var = vf.add_var('gov.addPt1Rh.y_' + template_name)
    gov_addfRef_y: Var = vf.add_var('gov.addfRef.y_' + template_name)
    gov_combiTableEmergency_y_1: Var = vf.add_var('gov.combiTableEmergency.y[1]_' + template_name)
    gov_combiTableSimx_u_1: Var = vf.add_var('gov.combiTableSimx.u[1]_' + template_name)
    gov_combiTableSimx_y_1: Var = vf.add_var('gov.combiTableSimx.y[1]_' + template_name)
    gov_deadZoneFrequency_y: Var = vf.add_var('gov.deadZoneFrequency.y_' + template_name)
    gov_deadZoneOmega_y: Var = vf.add_var('gov.deadZoneOmega.y_' + template_name)
    gov_derivativetDPctPc_y: Var = vf.add_var('gov.derivativetDPctPc.y_' + template_name)
    gov_fPu: Var = vf.add_var('gov.fPu_' + template_name)
    gov_fRefPu: Var = vf.add_var('gov.fRefPu_' + template_name)
    gov_gainChangeBase_y: Var = vf.add_var('gov.gainChangeBase.y_' + template_name)
    gov_gainCv_y: Var = vf.add_var('gov.gainCv.y_' + template_name)
    gov_gainFCor_y: Var = vf.add_var('gov.gainFCor.y_' + template_name)
    gov_gainIv_y: Var = vf.add_var('gov.gainIv.y_' + template_name)
    gov_gainKEPu_y: Var = vf.add_var('gov.gainKEPu.y_' + template_name)
    gov_gainKHpPu_y: Var = vf.add_var('gov.gainKHpPu.y_' + template_name)
    gov_gainKOmegaCorPu_y: Var = vf.add_var('gov.gainKOmegaCorPu.y_' + template_name)
    gov_integratortB_local_reset: Var = vf.add_var('gov.integratortB.local_reset_' + template_name)
    gov_integratortB_local_set: Var = vf.add_var('gov.integratortB.local_set_' + template_name)
    gov_limIntegratorCv_local_reset: Var = vf.add_var('gov.limIntegratorCv.local_reset_' + template_name)
    gov_limIntegratorCv_local_set: Var = vf.add_var('gov.limIntegratorCv.local_set_' + template_name)
    gov_limIntegratorIv_local_reset: Var = vf.add_var('gov.limIntegratorIv.local_reset_' + template_name)
    gov_limIntegratorIv_local_set: Var = vf.add_var('gov.limIntegratorIv.local_set_' + template_name)
    gov_limIntegratorPID_local_reset: Var = vf.add_var('gov.limIntegratorPID.local_reset_' + template_name)
    gov_limIntegratorPID_local_set: Var = vf.add_var('gov.limIntegratorPID.local_set_' + template_name)
    gov_limIntegratortRh_local_reset: Var = vf.add_var('gov.limIntegratortRh.local_reset_' + template_name)
    gov_limIntegratortRh_local_set: Var = vf.add_var('gov.limIntegratortRh.local_set_' + template_name)
    gov_limiterCv_simplifiedExpr: Var = vf.add_var('gov.limiterCv.simplifiedExpr_' + template_name)
    gov_limiterCv_y: Var = vf.add_var('gov.limiterCv.y_' + template_name)
    gov_limiterDeltaF_simplifiedExpr: Var = vf.add_var('gov.limiterDeltaF.simplifiedExpr_' + template_name)
    gov_limiterDeltaF_y: Var = vf.add_var('gov.limiterDeltaF.y_' + template_name)
    gov_limiterDeltaOmega_simplifiedExpr: Var = vf.add_var('gov.limiterDeltaOmega.simplifiedExpr_' + template_name)
    gov_limiterDeltaOmega_y: Var = vf.add_var('gov.limiterDeltaOmega.y_' + template_name)
    gov_limiterIv_simplifiedExpr: Var = vf.add_var('gov.limiterIv.simplifiedExpr_' + template_name)
    gov_limiterIv_y: Var = vf.add_var('gov.limiterIv.y_' + template_name)
    gov_limiterP_simplifiedExpr: Var = vf.add_var('gov.limiterP.simplifiedExpr_' + template_name)
    gov_limiterP_y: Var = vf.add_var('gov.limiterP.y_' + template_name)
    gov_limiterP2_simplifiedExpr: Var = vf.add_var('gov.limiterP2.simplifiedExpr_' + template_name)
    gov_minEmergencyBoiler_y: Var = vf.add_var('gov.minEmergencyBoiler.y_' + template_name)
    gov_minEmergencyCv_y: Var = vf.add_var('gov.minEmergencyCv.y_' + template_name)
    gov_omegaPu: Var = vf.add_var('gov.omegaPu_' + template_name)
    gov_omegaRefPu: Var = vf.add_var('gov.omegaRefPu_' + template_name)
    gov_productVHp_y: Var = vf.add_var('gov.productVHp.y_' + template_name)
    gov_productVLp_y: Var = vf.add_var('gov.productVLp.y_' + template_name)
    # Declare the differential variables used by the template.
    d_gov_derivativetDPctPc_x: Var = vf.add_diff_var('d_gov.derivativetDPctPc.x_' + template_name, base_var=gov_derivativetDPctPc_x)
    d_gov_firstOrdertEn_y: Var = vf.add_diff_var('d_gov.firstOrdertEn.y_' + template_name, base_var=gov_firstOrdertEn_y)
    d_gov_firstOrdertHp_y: Var = vf.add_diff_var('d_gov.firstOrdertHp.y_' + template_name, base_var=gov_firstOrdertHp_y)
    d_gov_firstOrdertLp_y: Var = vf.add_diff_var('d_gov.firstOrdertLp.y_' + template_name, base_var=gov_firstOrdertLp_y)
    d_gov_firstOrdertOmega_y: Var = vf.add_diff_var('d_gov.firstOrdertOmega.y_' + template_name, base_var=gov_firstOrdertOmega_y)
    d_gov_firstOrdertP_y: Var = vf.add_diff_var('d_gov.firstOrdertP.y_' + template_name, base_var=gov_firstOrdertP_y)
    d_gov_firstOrdertfT_y: Var = vf.add_diff_var('d_gov.firstOrdertfT.y_' + template_name, base_var=gov_firstOrdertfT_y)
    d_gov_integratortB_y: Var = vf.add_diff_var('d_gov.integratortB.y_' + template_name, base_var=gov_integratortB_y)
    d_gov_limIntegratorCv_y: Var = vf.add_diff_var('d_gov.limIntegratorCv.y_' + template_name, base_var=gov_limIntegratorCv_y)
    d_gov_limIntegratorIv_y: Var = vf.add_diff_var('d_gov.limIntegratorIv.y_' + template_name, base_var=gov_limIntegratorIv_y)
    d_gov_limIntegratorPID_y: Var = vf.add_diff_var('d_gov.limIntegratorPID.y_' + template_name, base_var=gov_limIntegratorPID_y)
    d_gov_limIntegratortRh_y: Var = vf.add_diff_var('d_gov.limIntegratortRh.y_' + template_name, base_var=gov_limIntegratortRh_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((gov_firstOrdertfT_k - gov_firstOrdertfT_y) / gov_firstOrdertfT_T))
    state_equations.append(((gov_firstOrdertOmega_k - gov_firstOrdertOmega_y) / gov_firstOrdertOmega_T))
    state_equations.append((((gov_firstOrdertP_k * gov_gainChangeBase_y) - gov_firstOrdertP_y) / gov_firstOrdertP_T))
    state_equations.append((((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limIntegratorPID_outMin - gov_limIntegratorPID_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limIntegratorPID_outMin - gov_limIntegratorPID_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorPID_k * gov_addPe_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limIntegratorPID_outMin - gov_limIntegratorPID_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorPID_k * gov_addPe_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorPID_y - gov_limIntegratorPID_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorPID_outMin - gov_limIntegratorPID_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorPID_k * gov_addPe_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorPID_y - gov_limIntegratorPID_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limIntegratorPID_k * gov_addPe_y) - sym.Const(0.0)) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limIntegratorPID_outMin - gov_limIntegratorPID_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limIntegratorPID_outMin - gov_limIntegratorPID_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorPID_k * gov_addPe_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limIntegratorPID_outMin - gov_limIntegratorPID_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorPID_k * gov_addPe_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorPID_y - gov_limIntegratorPID_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorPID_outMin - gov_limIntegratorPID_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorPID_k * gov_addPe_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorPID_y - gov_limIntegratorPID_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limIntegratorPID_k * gov_addPe_y) - sym.Const(0.0)) - sym.Const(1e-06)))))))) * (gov_limIntegratorPID_k * gov_addPe_y))))
    state_equations.append((((gov_firstOrdertEn_k * gov_AddGovController_y) - gov_firstOrdertEn_y) / gov_firstOrdertEn_T))
    state_equations.append(((gov_derivativetDPctPc_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - gov_derivativetDPctPc_zeroGain) * ((gov_addPe_y - gov_derivativetDPctPc_x) / gov_derivativetDPctPc_T))))
    state_equations.append((((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limIntegratorCv_outMin - gov_limIntegratorCv_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limIntegratorCv_outMin - gov_limIntegratorCv_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorCv_k * gov_limiterCv_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limIntegratorCv_outMin - gov_limIntegratorCv_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorCv_k * gov_limiterCv_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorCv_y - gov_limIntegratorCv_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorCv_outMin - gov_limIntegratorCv_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorCv_k * gov_limiterCv_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorCv_y - gov_limIntegratorCv_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limIntegratorCv_k * gov_limiterCv_y) - sym.Const(0.0)) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limIntegratorCv_outMin - gov_limIntegratorCv_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limIntegratorCv_outMin - gov_limIntegratorCv_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorCv_k * gov_limiterCv_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limIntegratorCv_outMin - gov_limIntegratorCv_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorCv_k * gov_limiterCv_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorCv_y - gov_limIntegratorCv_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorCv_outMin - gov_limIntegratorCv_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorCv_k * gov_limiterCv_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorCv_y - gov_limIntegratorCv_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limIntegratorCv_k * gov_limiterCv_y) - sym.Const(0.0)) - sym.Const(1e-06)))))))) * (gov_limIntegratorCv_k * gov_limiterCv_y))))
    state_equations.append((((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limIntegratorIv_outMin - gov_limIntegratorIv_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limIntegratorIv_outMin - gov_limIntegratorIv_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorIv_k * gov_limiterIv_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limIntegratorIv_outMin - gov_limIntegratorIv_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorIv_k * gov_limiterIv_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorIv_y - gov_limIntegratorIv_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorIv_outMin - gov_limIntegratorIv_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorIv_k * gov_limiterIv_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorIv_y - gov_limIntegratorIv_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limIntegratorIv_k * gov_limiterIv_y) - sym.Const(0.0)) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limIntegratorIv_outMin - gov_limIntegratorIv_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limIntegratorIv_outMin - gov_limIntegratorIv_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorIv_k * gov_limiterIv_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limIntegratorIv_outMin - gov_limIntegratorIv_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorIv_k * gov_limiterIv_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorIv_y - gov_limIntegratorIv_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorIv_outMin - gov_limIntegratorIv_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratorIv_k * gov_limiterIv_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratorIv_y - gov_limIntegratorIv_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limIntegratorIv_k * gov_limiterIv_y) - sym.Const(0.0)) - sym.Const(1e-06)))))))) * (gov_limIntegratorIv_k * gov_limiterIv_y))))
    state_equations.append((((gov_firstOrdertHp_k * gov_productVHp_y) - gov_firstOrdertHp_y) / gov_firstOrdertHp_T))
    state_equations.append((gov_integratortB_k * gov_addPt1Boiler_y))
    state_equations.append((((gov_firstOrdertLp_k * gov_productVLp_y) - gov_firstOrdertLp_y) / gov_firstOrdertLp_T))
    state_equations.append((((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limIntegratortRh_outMin - gov_limIntegratortRh_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limIntegratortRh_outMin - gov_limIntegratortRh_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratortRh_k * gov_addPt1Rh_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limIntegratortRh_outMin - gov_limIntegratortRh_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratortRh_k * gov_addPt1Rh_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratortRh_y - gov_limIntegratortRh_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratortRh_outMin - gov_limIntegratortRh_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratortRh_k * gov_addPt1Rh_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratortRh_y - gov_limIntegratortRh_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limIntegratortRh_k * gov_addPt1Rh_y) - sym.Const(0.0)) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((gov_limIntegratortRh_outMin - gov_limIntegratortRh_y) - sym.Const(1e-06))) * sym.heaviside(((gov_limIntegratortRh_outMin - gov_limIntegratortRh_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratortRh_k * gov_addPt1Rh_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((gov_limIntegratortRh_outMin - gov_limIntegratortRh_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratortRh_k * gov_addPt1Rh_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratortRh_y - gov_limIntegratortRh_outMax) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratortRh_outMin - gov_limIntegratortRh_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (gov_limIntegratortRh_k * gov_addPt1Rh_y)) - sym.Const(1e-06)))) * sym.heaviside(((gov_limIntegratortRh_y - gov_limIntegratortRh_outMax) - sym.Const(1e-06)))) * sym.heaviside((((gov_limIntegratortRh_k * gov_addPt1Rh_y) - sym.Const(0.0)) - sym.Const(1e-06)))))))) * (gov_limIntegratortRh_k * gov_addPt1Rh_y))))
    state_variables: list[Var] = list()
    state_variables.append(gov_firstOrdertfT_y)
    state_variables.append(gov_firstOrdertOmega_y)
    state_variables.append(gov_firstOrdertP_y)
    state_variables.append(gov_limIntegratorPID_y)
    state_variables.append(gov_firstOrdertEn_y)
    state_variables.append(gov_derivativetDPctPc_x)
    state_variables.append(gov_limIntegratorCv_y)
    state_variables.append(gov_limIntegratorIv_y)
    state_variables.append(gov_firstOrdertHp_y)
    state_variables.append(gov_integratortB_y)
    state_variables.append(gov_firstOrdertLp_y)
    state_variables.append(gov_limIntegratortRh_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((gov_combiTableEmergency_y_1 - (((((sym.Const(1.0) * sym.heaviside(((sym.Const(0.0) - gov_firstOrdertOmega_y) - sym.Const(1e-06)))) + ((((((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(1.025) - sym.Const(0.0))) * gov_firstOrdertOmega_y) + (sym.Const(1.0) - (((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(1.025) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((gov_firstOrdertOmega_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.025) - gov_firstOrdertOmega_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.0) - sym.Const(1.0)) / (sym.Const(1.05) - sym.Const(1.025))) * gov_firstOrdertOmega_y) + (sym.Const(1.0) - (((sym.Const(0.0) - sym.Const(1.0)) / (sym.Const(1.05) - sym.Const(1.025))) * sym.Const(1.025)))) * sym.heaviside(((gov_firstOrdertOmega_y - sym.Const(1.025)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.05) - gov_firstOrdertOmega_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(1.06) - sym.Const(1.05))) * gov_firstOrdertOmega_y) + (sym.Const(0.0) - (((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(1.06) - sym.Const(1.05))) * sym.Const(1.05)))) * sym.heaviside(((gov_firstOrdertOmega_y - sym.Const(1.05)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.06) - gov_firstOrdertOmega_y) - sym.Const(1e-06))))) + (sym.Const(0.0) * sym.heaviside(((gov_firstOrdertOmega_y - sym.Const(1.06)) + sym.Const(1e-06)))))))
    algebraic_equations.append((gov_addfRef_y - (gov_addfRef_k1 + (gov_addfRef_k2 * gov_firstOrdertfT_y))))
    algebraic_equations.append((gov_addOmegaOmegaRef_y - (gov_addOmegaOmegaRef_k1 + (gov_addOmegaOmegaRef_k2 * gov_firstOrdertOmega_y))))
    algebraic_equations.append((gov_deadZoneFrequency_y - ((sym.heaviside(((gov_addfRef_y - gov_deadZoneFrequency_uMax) - sym.Const(1e-06))) * (gov_addfRef_y - gov_deadZoneFrequency_uMax)) + ((sym.Const(1.0) - sym.heaviside(((gov_addfRef_y - gov_deadZoneFrequency_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_deadZoneFrequency_uMin - gov_addfRef_y) - sym.Const(1e-06))) * (gov_addfRef_y - gov_deadZoneFrequency_uMin)) + ((sym.Const(1.0) - sym.heaviside(((gov_deadZoneFrequency_uMin - gov_addfRef_y) - sym.Const(1e-06)))) * sym.Const(0.0)))))))
    algebraic_equations.append((gov_deadZoneOmega_y - ((sym.heaviside(((gov_addOmegaOmegaRef_y - gov_deadZoneOmega_uMax) - sym.Const(1e-06))) * (gov_addOmegaOmegaRef_y - gov_deadZoneOmega_uMax)) + ((sym.Const(1.0) - sym.heaviside(((gov_addOmegaOmegaRef_y - gov_deadZoneOmega_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_deadZoneOmega_uMin - gov_addOmegaOmegaRef_y) - sym.Const(1e-06))) * (gov_addOmegaOmegaRef_y - gov_deadZoneOmega_uMin)) + ((sym.Const(1.0) - sym.heaviside(((gov_deadZoneOmega_uMin - gov_addOmegaOmegaRef_y) - sym.Const(1e-06)))) * sym.Const(0.0)))))))
    algebraic_equations.append((gov_gainFCor_y - (gov_gainFCor_k * gov_deadZoneFrequency_y)))
    algebraic_equations.append((gov_gainKHpPu_y - (gov_gainKHpPu_k * gov_firstOrdertHp_y)))
    algebraic_equations.append((gov_PmPu - ((gov_addLpKHpPu_k1 * gov_gainKHpPu_y) + (gov_addLpKHpPu_k2 * gov_firstOrdertLp_y))))
    algebraic_equations.append((gov_gainKOmegaCorPu_y - (gov_gainKOmegaCorPu_k * gov_deadZoneOmega_y)))
    algebraic_equations.append((gov_limiterDeltaF_y - ((sym.heaviside(((gov_gainFCor_y - gov_limiterDeltaF_uMax) - sym.Const(1e-06))) * gov_limiterDeltaF_uMax) + ((sym.Const(1.0) - sym.heaviside(((gov_gainFCor_y - gov_limiterDeltaF_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_limiterDeltaF_uMin - gov_gainFCor_y) - sym.Const(1e-06))) * gov_limiterDeltaF_uMin) + ((sym.Const(1.0) - sym.heaviside(((gov_limiterDeltaF_uMin - gov_gainFCor_y) - sym.Const(1e-06)))) * gov_gainFCor_y))))))
    algebraic_equations.append((gov_addPRef_y - ((gov_addPRef_k1 * gov_limiterDeltaF_y) + (sym.Const(0.8) * gov_addPRef_k2))))
    algebraic_equations.append((gov_addPe_y - ((gov_addPe_k1 * gov_firstOrdertP_y) + (gov_addPe_k2 * gov_addPRef_y))))
    algebraic_equations.append((gov_gainKEPu_y - (gov_gainKEPu_k * gov_addPe_y)))
    algebraic_equations.append((gov_derivativetDPctPc_y - ((gov_derivativetDPctPc_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - gov_derivativetDPctPc_zeroGain) * ((gov_derivativetDPctPc_k / gov_derivativetDPctPc_T) * (gov_addPe_y - gov_derivativetDPctPc_x))))))
    algebraic_equations.append((gov_AddGovController_y - ((gov_AddGovController_k1 * gov_gainKEPu_y) + ((gov_AddGovController_k2 * gov_limIntegratorPID_y) + (gov_AddGovController_k3 * gov_derivativetDPctPc_y)))))
    algebraic_equations.append((gov_minEmergencyBoiler_y - sym.min(gov_addPRef_y, gov_combiTableEmergency_y_1)))
    algebraic_equations.append((gov_limiterDeltaOmega_y - ((sym.heaviside(((gov_gainKOmegaCorPu_y - gov_limiterDeltaOmega_uMax) - sym.Const(1e-06))) * gov_limiterDeltaOmega_uMax) + ((sym.Const(1.0) - sym.heaviside(((gov_gainKOmegaCorPu_y - gov_limiterDeltaOmega_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_limiterDeltaOmega_uMin - gov_gainKOmegaCorPu_y) - sym.Const(1e-06))) * gov_limiterDeltaOmega_uMin) + ((sym.Const(1.0) - sym.heaviside(((gov_limiterDeltaOmega_uMin - gov_gainKOmegaCorPu_y) - sym.Const(1e-06)))) * gov_gainKOmegaCorPu_y))))))
    algebraic_equations.append((gov_addCtrlOp_y - ((gov_addCtrlOp_k1 * gov_firstOrdertEn_y) + (gov_addCtrlOp_k2 * gov_limiterDeltaOmega_y))))
    algebraic_equations.append((gov_limiterP_y - ((sym.heaviside(((gov_addCtrlOp_y - gov_limiterP_uMax) - sym.Const(1e-06))) * gov_limiterP_uMax) + ((sym.Const(1.0) - sym.heaviside(((gov_addCtrlOp_y - gov_limiterP_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_limiterP_uMin - gov_addCtrlOp_y) - sym.Const(1e-06))) * gov_limiterP_uMin) + ((sym.Const(1.0) - sym.heaviside(((gov_limiterP_uMin - gov_addCtrlOp_y) - sym.Const(1e-06)))) * gov_addCtrlOp_y))))))
    algebraic_equations.append((gov_minEmergencyCv_y - sym.min(gov_limiterP_y, gov_combiTableEmergency_y_1)))
    algebraic_equations.append((gov_combiTableSimx_u_1 - ((sym.heaviside(((gov_minEmergencyCv_y - gov_limiterP2_uMax) - sym.Const(1e-06))) * gov_limiterP2_uMax) + ((sym.Const(1.0) - sym.heaviside(((gov_minEmergencyCv_y - gov_limiterP2_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_limiterP2_uMin - gov_minEmergencyCv_y) - sym.Const(1e-06))) * gov_limiterP2_uMin) + ((sym.Const(1.0) - sym.heaviside(((gov_limiterP2_uMin - gov_minEmergencyCv_y) - sym.Const(1e-06)))) * gov_minEmergencyCv_y))))))
    algebraic_equations.append((gov_addCv_y - ((gov_addCv_k1 * gov_limIntegratorCv_y) + (gov_addCv_k2 * gov_combiTableSimx_u_1))))
    algebraic_equations.append((gov_gainCv_y - (gov_gainCv_k * gov_addCv_y)))
    algebraic_equations.append((gov_limiterCv_y - ((sym.heaviside(((gov_gainCv_y - gov_limiterCv_uMax) - sym.Const(1e-06))) * gov_limiterCv_uMax) + ((sym.Const(1.0) - sym.heaviside(((gov_gainCv_y - gov_limiterCv_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_limiterCv_uMin - gov_gainCv_y) - sym.Const(1e-06))) * gov_limiterCv_uMin) + ((sym.Const(1.0) - sym.heaviside(((gov_limiterCv_uMin - gov_gainCv_y) - sym.Const(1e-06)))) * gov_gainCv_y))))))
    algebraic_equations.append((gov_combiTableSimx_y_1 - ((((sym.Const(0.0) * sym.heaviside(((sym.Const(0.0) - gov_combiTableSimx_u_1) - sym.Const(1e-06)))) + ((((((sym.Const(1.0) - sym.Const(0.0)) / (sym.Const(0.425) - sym.Const(0.0))) * gov_combiTableSimx_u_1) + (sym.Const(0.0) - (((sym.Const(1.0) - sym.Const(0.0)) / (sym.Const(0.425) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((gov_combiTableSimx_u_1 - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.425) - gov_combiTableSimx_u_1) - sym.Const(1e-06))))) + ((((((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(999999.0) - sym.Const(0.425))) * gov_combiTableSimx_u_1) + (sym.Const(1.0) - (((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(999999.0) - sym.Const(0.425))) * sym.Const(0.425)))) * sym.heaviside(((gov_combiTableSimx_u_1 - sym.Const(0.425)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(999999.0) - gov_combiTableSimx_u_1) - sym.Const(1e-06))))) + (sym.Const(1.0) * sym.heaviside(((gov_combiTableSimx_u_1 - sym.Const(999999.0)) + sym.Const(1e-06)))))))
    algebraic_equations.append((gov_addPt1Iv_y - ((gov_addPt1Iv_k1 * gov_limIntegratorIv_y) + (gov_addPt1Iv_k2 * gov_combiTableSimx_y_1))))
    algebraic_equations.append((gov_gainIv_y - (gov_gainIv_k * gov_addPt1Iv_y)))
    algebraic_equations.append((gov_limiterIv_y - ((sym.heaviside(((gov_gainIv_y - gov_limiterIv_uMax) - sym.Const(1e-06))) * gov_limiterIv_uMax) + ((sym.Const(1.0) - sym.heaviside(((gov_gainIv_y - gov_limiterIv_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_limiterIv_uMin - gov_gainIv_y) - sym.Const(1e-06))) * gov_limiterIv_uMin) + ((sym.Const(1.0) - sym.heaviside(((gov_limiterIv_uMin - gov_gainIv_y) - sym.Const(1e-06)))) * gov_gainIv_y))))))
    algebraic_equations.append((gov_productVHp_y - (gov_integratortB_y * gov_limIntegratorCv_y)))
    algebraic_equations.append((gov_addPt1Boiler_y - ((gov_addPt1Boiler_k1 * gov_productVHp_y) + (gov_addPt1Boiler_k2 * gov_minEmergencyBoiler_y))))
    algebraic_equations.append((gov_productVLp_y - (gov_limIntegratortRh_y * gov_limIntegratorIv_y)))
    algebraic_equations.append((gov_addPt1Rh_y - ((gov_addPt1Rh_k1 * gov_productVLp_y) + (gov_addPt1Rh_k2 * gov_firstOrdertHp_y))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(gov_combiTableEmergency_y_1)
    algebraic_variables.append(gov_addfRef_y)
    algebraic_variables.append(gov_addOmegaOmegaRef_y)
    algebraic_variables.append(gov_deadZoneFrequency_y)
    algebraic_variables.append(gov_deadZoneOmega_y)
    algebraic_variables.append(gov_gainFCor_y)
    algebraic_variables.append(gov_gainKHpPu_y)
    algebraic_variables.append(gov_PmPu)
    algebraic_variables.append(gov_gainKOmegaCorPu_y)
    algebraic_variables.append(gov_limiterDeltaF_y)
    algebraic_variables.append(gov_addPRef_y)
    algebraic_variables.append(gov_addPe_y)
    algebraic_variables.append(gov_gainKEPu_y)
    algebraic_variables.append(gov_derivativetDPctPc_y)
    algebraic_variables.append(gov_AddGovController_y)
    algebraic_variables.append(gov_minEmergencyBoiler_y)
    algebraic_variables.append(gov_limiterDeltaOmega_y)
    algebraic_variables.append(gov_addCtrlOp_y)
    algebraic_variables.append(gov_limiterP_y)
    algebraic_variables.append(gov_minEmergencyCv_y)
    algebraic_variables.append(gov_combiTableSimx_u_1)
    algebraic_variables.append(gov_addCv_y)
    algebraic_variables.append(gov_gainCv_y)
    algebraic_variables.append(gov_limiterCv_y)
    algebraic_variables.append(gov_combiTableSimx_y_1)
    algebraic_variables.append(gov_addPt1Iv_y)
    algebraic_variables.append(gov_gainIv_y)
    algebraic_variables.append(gov_limiterIv_y)
    algebraic_variables.append(gov_productVHp_y)
    algebraic_variables.append(gov_addPt1Boiler_y)
    algebraic_variables.append(gov_productVLp_y)
    algebraic_variables.append(gov_addPt1Rh_y)
    algebraic_variables.append(gov_gainChangeBase_y)
    algebraic_variables.append(gov_PGenPu)
    algebraic_variables.append(gov_PRefPu)
    algebraic_variables.append(gov_fPu)
    algebraic_variables.append(gov_fRefPu)
    algebraic_variables.append(gov_omegaPu)
    algebraic_variables.append(gov_omegaRefPu)
    algebraic_variables.append(gov_integratortB_local_reset)
    algebraic_variables.append(gov_integratortB_local_set)
    algebraic_variables.append(gov_limIntegratorCv_local_reset)
    algebraic_variables.append(gov_limIntegratorCv_local_set)
    algebraic_variables.append(gov_limIntegratorIv_local_reset)
    algebraic_variables.append(gov_limIntegratorIv_local_set)
    algebraic_variables.append(gov_limIntegratorPID_local_reset)
    algebraic_variables.append(gov_limIntegratorPID_local_set)
    algebraic_variables.append(gov_limIntegratortRh_local_reset)
    algebraic_variables.append(gov_limIntegratortRh_local_set)
    algebraic_variables.append(gov_limiterCv_simplifiedExpr)
    algebraic_variables.append(gov_limiterDeltaF_simplifiedExpr)
    algebraic_variables.append(gov_limiterDeltaOmega_simplifiedExpr)
    algebraic_variables.append(gov_limiterIv_simplifiedExpr)
    algebraic_variables.append(gov_limiterP_simplifiedExpr)
    algebraic_variables.append(gov_limiterP2_simplifiedExpr)
    differential_variables: list[Var] = list()
    differential_variables.append(d_gov_firstOrdertfT_y)
    differential_variables.append(d_gov_firstOrdertOmega_y)
    differential_variables.append(d_gov_firstOrdertP_y)
    differential_variables.append(d_gov_limIntegratorPID_y)
    differential_variables.append(d_gov_firstOrdertEn_y)
    differential_variables.append(d_gov_derivativetDPctPc_x)
    differential_variables.append(d_gov_limIntegratorCv_y)
    differential_variables.append(d_gov_limIntegratorIv_y)
    differential_variables.append(d_gov_firstOrdertHp_y)
    differential_variables.append(d_gov_integratortB_y)
    differential_variables.append(d_gov_firstOrdertLp_y)
    differential_variables.append(d_gov_limIntegratortRh_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[gov_AddGovController_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_AddGovController_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_AddGovController_k3] = vf.add_const(1.0, name='')
    event_parameters[gov_CHcPu] = vf.add_const(-3.3, name='')
    event_parameters[gov_CHoPu] = vf.add_const(0.17, name='')
    event_parameters[gov_CIcPu] = vf.add_const(-2.2, name='')
    event_parameters[gov_CIoPu] = vf.add_const(0.123, name='')
    event_parameters[gov_DeltaOmegaDbPu] = vf.add_const(0.0004, name='')
    event_parameters[gov_DeltafDbPu] = vf.add_const(0.0, name='')
    event_parameters[gov_HHpMaxPu] = vf.add_const(1.0, name='')
    event_parameters[gov_KE] = vf.add_const(0.65, name='')
    event_parameters[gov_KFCor] = vf.add_const(20.0, name='')
    event_parameters[gov_KHp] = vf.add_const(0.277, name='')
    event_parameters[gov_KLp] = vf.add_const(0.723, name='')
    event_parameters[gov_KOmegaCor] = vf.add_const(20.0, name='')
    event_parameters[gov_OmegaFMaxPu] = vf.add_const(0.05, name='')
    event_parameters[gov_OmegaFMinPu] = vf.add_const(-0.05, name='')
    event_parameters[gov_OmegaMax1Pu] = vf.add_const(1.025, name='')
    event_parameters[gov_OmegaMax2Pu] = vf.add_const(1.05, name='')
    event_parameters[gov_OmegaOmegaMaxPu] = vf.add_const(0.1, name='')
    event_parameters[gov_OmegaOmegaMinPu] = vf.add_const(-1.0, name='')
    event_parameters[gov_PBaseMw] = vf.add_const(100.0, name='')
    event_parameters[gov_PGen0Pu] = vf.add_const(0.8, name='')
    event_parameters[gov_PGenBaseMw] = vf.add_const(100.0, name='')
    event_parameters[gov_PMaxPu] = vf.add_const(1.0, name='')
    event_parameters[gov_PRef0Pu] = (gov_PGen0Pu * (gov_PGenBaseMw / gov_PBaseMw))
    event_parameters[gov_PRhMaxPu] = vf.add_const(1.4, name='')
    event_parameters[gov_Pm0Pu] = vf.add_const(0.8, name='')
    event_parameters[gov_SimxPu] = vf.add_const(0.425, name='')
    event_parameters[gov_addCtrlOp_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_addCtrlOp_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_addCv_k1] = vf.add_const(-1.0, name='')
    event_parameters[gov_addCv_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_addLpKHpPu_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_addLpKHpPu_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_addOmegaOmegaRef_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_addOmegaOmegaRef_k2] = vf.add_const(-1.0, name='')
    event_parameters[gov_addPRef_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_addPRef_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_addPe_k1] = vf.add_const(-1.0, name='')
    event_parameters[gov_addPe_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_addPt1Boiler_k1] = vf.add_const(-1.0, name='')
    event_parameters[gov_addPt1Boiler_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_addPt1Iv_k1] = vf.add_const(-1.0, name='')
    event_parameters[gov_addPt1Iv_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_addPt1Rh_k1] = vf.add_const(-1.0, name='')
    event_parameters[gov_addPt1Rh_k2] = vf.add_const(1.0, name='')
    event_parameters[gov_addfRef_k1] = vf.add_const(1.0, name='')
    event_parameters[gov_addfRef_k2] = vf.add_const(-1.0, name='')
    event_parameters[gov_combiTableEmergency_table_1_1] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableEmergency_table_1_2] = vf.add_const(1.0, name='')
    event_parameters[gov_combiTableEmergency_table_2_1] = gov_OmegaMax1Pu
    event_parameters[gov_combiTableEmergency_table_2_2] = vf.add_const(1.0, name='')
    event_parameters[gov_combiTableEmergency_table_3_1] = gov_OmegaMax2Pu
    event_parameters[gov_combiTableEmergency_table_3_2] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableEmergency_table_4_1] = (sym.Const(0.01) + gov_OmegaMax2Pu)
    event_parameters[gov_combiTableEmergency_table_4_2] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableEmergency_u_max] = vf.add_const(1.06, name='')
    event_parameters[gov_combiTableEmergency_u_min] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableSimx_table_1_1] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableSimx_table_1_2] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableSimx_table_2_1] = gov_SimxPu
    event_parameters[gov_combiTableSimx_table_2_2] = vf.add_const(1.0, name='')
    event_parameters[gov_combiTableSimx_table_3_1] = vf.add_const(999999.0, name='')
    event_parameters[gov_combiTableSimx_table_3_2] = vf.add_const(1.0, name='')
    event_parameters[gov_combiTableSimx_u_max] = vf.add_const(999999.0, name='')
    event_parameters[gov_combiTableSimx_u_min] = vf.add_const(0.0, name='')
    event_parameters[gov_deadZoneFrequency_uMax] = gov_DeltafDbPu
    event_parameters[gov_deadZoneFrequency_uMin] = (-gov_deadZoneFrequency_uMax)
    event_parameters[gov_deadZoneOmega_uMax] = gov_DeltaOmegaDbPu
    event_parameters[gov_deadZoneOmega_uMin] = (-gov_deadZoneOmega_uMax)
    event_parameters[gov_derivativetDPctPc_T] = gov_tFp
    event_parameters[gov_derivativetDPctPc_k] = gov_tDp
    event_parameters[gov_derivativetDPctPc_x_start] = vf.add_const(0.0, name='')
    event_parameters[gov_derivativetDPctPc_y_start] = vf.add_const(0.0, name='')
    event_parameters[gov_firstOrdertEn_T] = gov_tEn
    event_parameters[gov_firstOrdertEn_k] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrdertEn_y_start] = gov_initPcPu
    event_parameters[gov_firstOrdertHp_T] = gov_tHp
    event_parameters[gov_firstOrdertHp_k] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrdertHp_y_start] = gov_Pm0Pu
    event_parameters[gov_firstOrdertLp_T] = gov_tLp
    event_parameters[gov_firstOrdertLp_k] = gov_KLp
    event_parameters[gov_firstOrdertLp_y_start] = (gov_Pm0Pu * gov_KLp)
    event_parameters[gov_firstOrdertOmega_T] = gov_tOmega
    event_parameters[gov_firstOrdertOmega_k] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrdertOmega_y_start] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrdertP_T] = gov_tP
    event_parameters[gov_firstOrdertP_k] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrdertP_y_start] = (gov_PGen0Pu * (gov_PGenBaseMw / gov_PBaseMw))
    event_parameters[gov_firstOrdertfT_T] = gov_tF
    event_parameters[gov_firstOrdertfT_k] = vf.add_const(1.0, name='')
    event_parameters[gov_firstOrdertfT_y_start] = vf.add_const(1.0, name='')
    event_parameters[gov_gainChangeBase_k] = (gov_PGenBaseMw / gov_PBaseMw)
    event_parameters[gov_gainCv_k] = (sym.Const(1.0) / gov_tVHp)
    event_parameters[gov_gainFCor_k] = gov_KFCor
    event_parameters[gov_gainIv_k] = (sym.Const(1.0) / gov_tVLp)
    event_parameters[gov_gainKEPu_k] = gov_KE
    event_parameters[gov_gainKHpPu_k] = gov_KHp
    event_parameters[gov_gainKOmegaCorPu_k] = gov_KOmegaCor
    event_parameters[gov_initBPu] = vf.add_const(1.0, name='')
    event_parameters[gov_initPcPu] = (gov_Pm0Pu - sym.min(sym.max(sym.Const(0.0), gov_OmegaOmegaMinPu), gov_OmegaOmegaMaxPu))
    event_parameters[gov_integratortB_k] = (sym.Const(1.0) / gov_tB)
    event_parameters[gov_integratortB_y_start] = vf.add_const(1.0, name='')
    event_parameters[gov_limIntegratorCv_k] = vf.add_const(1.0, name='')
    event_parameters[gov_limIntegratorCv_outMax] = gov_HHpMaxPu
    event_parameters[gov_limIntegratorCv_outMin] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorCv_y_start] = gov_Pm0Pu
    event_parameters[gov_limIntegratorIv_k] = vf.add_const(1.0, name='')
    event_parameters[gov_limIntegratorIv_outMax] = vf.add_const(1.0, name='')
    event_parameters[gov_limIntegratorIv_outMin] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorIv_y_start] = vf.add_const(1.0, name='')
    event_parameters[gov_limIntegratorPID_k] = (sym.Const(1.0) / gov_tIp)
    event_parameters[gov_limIntegratorPID_outMax] = gov_PMaxPu
    event_parameters[gov_limIntegratorPID_outMin] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorPID_y_start] = gov_initPcPu
    event_parameters[gov_limIntegratortRh_k] = (sym.Const(1.0) / gov_tRh)
    event_parameters[gov_limIntegratortRh_outMax] = gov_PRhMaxPu
    event_parameters[gov_limIntegratortRh_outMin] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratortRh_y_start] = ((sym.heaviside(((gov_tRh - sym.Const(0.0)) - sym.Const(1e-06))) * gov_Pm0Pu) + ((sym.Const(1.0) - sym.heaviside(((gov_tRh - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.Const(0.0)))
    event_parameters[gov_limiterCv_uMax] = gov_CHoPu
    event_parameters[gov_limiterCv_uMin] = gov_CHcPu
    event_parameters[gov_limiterDeltaF_uMax] = gov_OmegaFMaxPu
    event_parameters[gov_limiterDeltaF_uMin] = gov_OmegaFMinPu
    event_parameters[gov_limiterDeltaOmega_uMax] = gov_OmegaOmegaMaxPu
    event_parameters[gov_limiterDeltaOmega_uMin] = gov_OmegaOmegaMinPu
    event_parameters[gov_limiterIv_uMax] = gov_CIoPu
    event_parameters[gov_limiterIv_uMin] = gov_CIcPu
    event_parameters[gov_limiterP_uMax] = gov_PMaxPu
    event_parameters[gov_limiterP_uMin] = vf.add_const(0.0, name='')
    event_parameters[gov_limiterP2_uMax] = gov_PMaxPu
    event_parameters[gov_limiterP2_uMin] = vf.add_const(0.0, name='')
    event_parameters[gov_tB] = vf.add_const(100.0, name='')
    event_parameters[gov_tDp] = vf.add_const(1e-09, name='')
    event_parameters[gov_tEn] = vf.add_const(0.1, name='')
    event_parameters[gov_tF] = vf.add_const(1e-09, name='')
    event_parameters[gov_tFp] = vf.add_const(1e-09, name='')
    event_parameters[gov_tHp] = vf.add_const(0.31, name='')
    event_parameters[gov_tIp] = vf.add_const(2.0, name='')
    event_parameters[gov_tLp] = vf.add_const(0.45, name='')
    event_parameters[gov_tOmega] = vf.add_const(0.02, name='')
    event_parameters[gov_tP] = vf.add_const(0.07, name='')
    event_parameters[gov_tRh] = vf.add_const(8.0, name='')
    event_parameters[gov_tVHp] = vf.add_const(0.1, name='')
    event_parameters[gov_tVLp] = vf.add_const(0.15, name='')
    event_parameters[gov_combiTableEmergency_columns_1] = vf.add_const(2.0, name='')
    event_parameters[gov_combiTableEmergency_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[gov_combiTableEmergency_n] = vf.add_const(1.0, name='')
    event_parameters[gov_combiTableEmergency_smoothness] = vf.add_const(1.0, name='')
    event_parameters[gov_combiTableSimx_columns_1] = vf.add_const(2.0, name='')
    event_parameters[gov_combiTableSimx_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[gov_combiTableSimx_n] = vf.add_const(1.0, name='')
    event_parameters[gov_combiTableSimx_smoothness] = vf.add_const(1.0, name='')
    event_parameters[gov_derivativetDPctPc_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_firstOrdertEn_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_firstOrdertHp_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_firstOrdertLp_initType] = vf.add_const(4.0, name='')
    event_parameters[gov_firstOrdertOmega_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_firstOrdertP_initType] = vf.add_const(2.0, name='')
    event_parameters[gov_firstOrdertfT_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_integratortB_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_limIntegratorCv_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_limIntegratorIv_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_limIntegratorPID_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_limIntegratortRh_initType] = vf.add_const(3.0, name='')
    event_parameters[gov_limiterCv_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterDeltaF_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterDeltaOmega_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterIv_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterP_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterP2_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[gov_combiTableEmergency_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableEmergency_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableEmergency_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[gov_combiTableSimx_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableSimx_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableSimx_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[gov_deadZoneFrequency_deadZoneAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_deadZoneOmega_deadZoneAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_derivativetDPctPc_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(gov_derivativetDPctPc_k)) - sym.Const(1e-06)))
    event_parameters[gov_integratortB_use_reset] = vf.add_const(0.0, name='')
    event_parameters[gov_integratortB_use_set] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorCv_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limIntegratorCv_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorCv_use_reset] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorCv_use_set] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorIv_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limIntegratorIv_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorIv_use_reset] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorIv_use_set] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorPID_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limIntegratorPID_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorPID_use_reset] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratorPID_use_set] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratortRh_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limIntegratortRh_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratortRh_use_reset] = vf.add_const(0.0, name='')
    event_parameters[gov_limIntegratortRh_use_set] = vf.add_const(0.0, name='')
    event_parameters[gov_limiterCv_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterCv_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limiterDeltaF_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterDeltaF_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limiterDeltaOmega_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterDeltaOmega_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limiterIv_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterIv_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limiterP_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterP_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_limiterP2_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[gov_limiterP2_strict] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableEmergency_fileName] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableEmergency_tableName] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableSimx_fileName] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableSimx_tableName] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableEmergency_tableID] = vf.add_const(0.0, name='')
    event_parameters[gov_combiTableSimx_tableID] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[gov_derivativetDPctPc_x] = gov_derivativetDPctPc_x_start
    initial_equations[gov_firstOrdertEn_y] = gov_firstOrdertEn_y_start
    initial_equations[gov_firstOrdertHp_y] = gov_firstOrdertHp_y_start
    initial_equations[gov_firstOrdertLp_y] = gov_firstOrdertLp_y_start
    initial_equations[gov_firstOrdertOmega_y] = gov_firstOrdertOmega_y_start
    initial_equations[gov_firstOrdertP_y] = ((gov_gainChangeBase_y * gov_firstOrdertP_k) - (d_gov_firstOrdertP_y * gov_firstOrdertP_T))
    initial_equations[gov_firstOrdertfT_y] = gov_firstOrdertfT_y_start
    initial_equations[gov_integratortB_y] = vf.add_const(1.0, name='')
    initial_equations[gov_limIntegratorCv_y] = gov_limIntegratorCv_y_start
    initial_equations[gov_limIntegratorIv_y] = gov_limIntegratorIv_y_start
    initial_equations[gov_limIntegratorPID_y] = gov_limIntegratorPID_y_start
    initial_equations[gov_limIntegratortRh_y] = gov_limIntegratortRh_y_start
    initial_equations[gov_PGenPu] = vf.add_const(0.8, name='')
    initial_equations[gov_PRefPu] = vf.add_const(0.8, name='')
    initial_equations[gov_PmPu] = vf.add_const(0.8, name='')
    initial_equations[gov_fPu] = vf.add_const(1.0, name='')
    initial_equations[gov_fRefPu] = vf.add_const(1.0, name='')
    initial_equations[gov_omegaPu] = vf.add_const(1.0, name='')
    initial_equations[gov_omegaRefPu] = vf.add_const(1.0, name='')
    initial_equations[gov_integratortB_local_reset] = vf.add_const(0.0, name='')
    initial_equations[gov_integratortB_local_set] = vf.add_const(0.0, name='')
    initial_equations[gov_limIntegratorCv_local_reset] = vf.add_const(0.0, name='')
    initial_equations[gov_limIntegratorCv_local_set] = vf.add_const(0.0, name='')
    initial_equations[gov_limIntegratorIv_local_reset] = vf.add_const(0.0, name='')
    initial_equations[gov_limIntegratorIv_local_set] = vf.add_const(0.0, name='')
    initial_equations[gov_limIntegratorPID_local_reset] = vf.add_const(0.0, name='')
    initial_equations[gov_limIntegratorPID_local_set] = vf.add_const(0.0, name='')
    initial_equations[gov_limIntegratortRh_local_reset] = vf.add_const(0.0, name='')
    initial_equations[gov_limIntegratortRh_local_set] = vf.add_const(0.0, name='')
    initial_equations[gov_limiterCv_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[gov_limiterDeltaF_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[gov_limiterDeltaOmega_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[gov_limiterIv_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[gov_limiterP_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[gov_limiterP2_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[gov_gainChangeBase_y] = (sym.Const(0.8) * gov_gainChangeBase_k)
    initial_equations[gov_deadZoneOmega_y] = ((sym.heaviside(((gov_addOmegaOmegaRef_y - gov_deadZoneOmega_uMax) - sym.Const(1e-06))) * (gov_addOmegaOmegaRef_y - gov_deadZoneOmega_uMax)) + ((sym.Const(1.0) - sym.heaviside(((gov_addOmegaOmegaRef_y - gov_deadZoneOmega_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_deadZoneOmega_uMin - gov_addOmegaOmegaRef_y) - sym.Const(1e-06))) * (gov_addOmegaOmegaRef_y - gov_deadZoneOmega_uMin)) + ((sym.Const(1.0) - sym.heaviside(((gov_deadZoneOmega_uMin - gov_addOmegaOmegaRef_y) - sym.Const(1e-06)))) * sym.Const(0.0)))))
    initial_equations[gov_deadZoneFrequency_y] = ((sym.heaviside(((gov_addfRef_y - gov_deadZoneFrequency_uMax) - sym.Const(1e-06))) * (gov_addfRef_y - gov_deadZoneFrequency_uMax)) + ((sym.Const(1.0) - sym.heaviside(((gov_addfRef_y - gov_deadZoneFrequency_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((gov_deadZoneFrequency_uMin - gov_addfRef_y) - sym.Const(1e-06))) * (gov_addfRef_y - gov_deadZoneFrequency_uMin)) + ((sym.Const(1.0) - sym.heaviside(((gov_deadZoneFrequency_uMin - gov_addfRef_y) - sym.Const(1e-06)))) * sym.Const(0.0)))))
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations[d_gov_firstOrdertP_y] = vf.add_const(0.0, name='')
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

    _repair_govsteameu_template(template)
    template.comment = 'Generator steam governor GOVSTEAMEU'
    return template
