# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'MAXEX2'.

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

def build_maxex2_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'MAXEX2'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    oel_FOel_1_1: Var = vf.add_var('oel.FOel[1,1]_' + template_name)
    oel_FOel_1_2: Var = vf.add_var('oel.FOel[1,2]_' + template_name)
    oel_FOel_2_1: Var = vf.add_var('oel.FOel[2,1]_' + template_name)
    oel_FOel_2_2: Var = vf.add_var('oel.FOel[2,2]_' + template_name)
    oel_FOel_3_1: Var = vf.add_var('oel.FOel[3,1]_' + template_name)
    oel_FOel_3_2: Var = vf.add_var('oel.FOel[3,2]_' + template_name)
    oel_FOel_4_1: Var = vf.add_var('oel.FOel[4,1]_' + template_name)
    oel_FOel_4_2: Var = vf.add_var('oel.FOel[4,2]_' + template_name)
    oel_FOel_5_1: Var = vf.add_var('oel.FOel[5,1]_' + template_name)
    oel_FOel_5_2: Var = vf.add_var('oel.FOel[5,2]_' + template_name)
    oel_Ifd0Pu: Var = vf.add_var('oel.Ifd0Pu_' + template_name)
    oel_Ifd1Pu: Var = vf.add_var('oel.Ifd1Pu_' + template_name)
    oel_Ifd2Pu: Var = vf.add_var('oel.Ifd2Pu_' + template_name)
    oel_Ifd3Pu: Var = vf.add_var('oel.Ifd3Pu_' + template_name)
    oel_IfdRated: Var = vf.add_var('oel.IfdRated_' + template_name)
    oel_Kmx: Var = vf.add_var('oel.Kmx_' + template_name)
    oel_ULowPu: Var = vf.add_var('oel.ULowPu_' + template_name)
    oel_combiTable1Ds_columns_1: Var = vf.add_var('oel.combiTable1Ds.columns[1]_' + template_name)
    oel_combiTable1Ds_extrapolation: Var = vf.add_var('oel.combiTable1Ds.extrapolation_' + template_name)
    oel_combiTable1Ds_fileName: Var = vf.add_var('oel.combiTable1Ds.fileName_' + template_name)
    oel_combiTable1Ds_nout: Var = vf.add_var('oel.combiTable1Ds.nout_' + template_name)
    oel_combiTable1Ds_smoothness: Var = vf.add_var('oel.combiTable1Ds.smoothness_' + template_name)
    oel_combiTable1Ds_tableID: Var = vf.add_var('oel.combiTable1Ds.tableID_' + template_name)
    oel_combiTable1Ds_tableName: Var = vf.add_var('oel.combiTable1Ds.tableName_' + template_name)
    oel_combiTable1Ds_tableOnFile: Var = vf.add_var('oel.combiTable1Ds.tableOnFile_' + template_name)
    oel_combiTable1Ds_table_1_1: Var = vf.add_var('oel.combiTable1Ds.table[1,1]_' + template_name)
    oel_combiTable1Ds_table_1_2: Var = vf.add_var('oel.combiTable1Ds.table[1,2]_' + template_name)
    oel_combiTable1Ds_table_2_1: Var = vf.add_var('oel.combiTable1Ds.table[2,1]_' + template_name)
    oel_combiTable1Ds_table_2_2: Var = vf.add_var('oel.combiTable1Ds.table[2,2]_' + template_name)
    oel_combiTable1Ds_table_3_1: Var = vf.add_var('oel.combiTable1Ds.table[3,1]_' + template_name)
    oel_combiTable1Ds_table_3_2: Var = vf.add_var('oel.combiTable1Ds.table[3,2]_' + template_name)
    oel_combiTable1Ds_table_4_1: Var = vf.add_var('oel.combiTable1Ds.table[4,1]_' + template_name)
    oel_combiTable1Ds_table_4_2: Var = vf.add_var('oel.combiTable1Ds.table[4,2]_' + template_name)
    oel_combiTable1Ds_table_5_1: Var = vf.add_var('oel.combiTable1Ds.table[5,1]_' + template_name)
    oel_combiTable1Ds_table_5_2: Var = vf.add_var('oel.combiTable1Ds.table[5,2]_' + template_name)
    oel_combiTable1Ds_u_max: Var = vf.add_var('oel.combiTable1Ds.u_max_' + template_name)
    oel_combiTable1Ds_u_min: Var = vf.add_var('oel.combiTable1Ds.u_min_' + template_name)
    oel_combiTable1Ds_verboseExtrapolation: Var = vf.add_var('oel.combiTable1Ds.verboseExtrapolation_' + template_name)
    oel_combiTable1Ds_verboseRead: Var = vf.add_var('oel.combiTable1Ds.verboseRead_' + template_name)
    oel_flipFlopR_Y0: Var = vf.add_var('oel.flipFlopR.Y0_' + template_name)
    oel_gain_k: Var = vf.add_var('oel.gain.k_' + template_name)
    oel_greaterThreshold_threshold: Var = vf.add_var('oel.greaterThreshold.threshold_' + template_name)
    oel_lessEqualThreshold_threshold: Var = vf.add_var('oel.lessEqualThreshold.threshold_' + template_name)
    oel_limIntegrator_initType: Var = vf.add_var('oel.limIntegrator.initType_' + template_name)
    oel_limIntegrator_k: Var = vf.add_var('oel.limIntegrator.k_' + template_name)
    oel_limIntegrator_limitsAtInit: Var = vf.add_var('oel.limIntegrator.limitsAtInit_' + template_name)
    oel_limIntegrator_outMax: Var = vf.add_var('oel.limIntegrator.outMax_' + template_name)
    oel_limIntegrator_outMin: Var = vf.add_var('oel.limIntegrator.outMin_' + template_name)
    oel_limIntegrator_strict: Var = vf.add_var('oel.limIntegrator.strict_' + template_name)
    oel_limIntegrator_use_reset: Var = vf.add_var('oel.limIntegrator.use_reset_' + template_name)
    oel_limIntegrator_use_set: Var = vf.add_var('oel.limIntegrator.use_set_' + template_name)
    oel_limIntegrator_y_start: Var = vf.add_var('oel.limIntegrator.y_start_' + template_name)
    oel_t1: Var = vf.add_var('oel.t1_' + template_name)
    oel_t2: Var = vf.add_var('oel.t2_' + template_name)
    oel_t3: Var = vf.add_var('oel.t3_' + template_name)
    # Declare the state variables used by the template.
    oel_limIntegrator_y: Var = vf.add_var('oel.limIntegrator.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_oel_flipFlopR_y: Var = vf.add_var('$PRE.oel.flipFlopR.y_' + template_name)
    PRE_oel_timer_entryTime: Var = vf.add_var('$PRE.oel.timer.entryTime_' + template_name)
    START_oel_flipFlopR_y: Var = vf.add_var('$START.oel.flipFlopR.y_' + template_name)
    whenCondition1: Var = vf.add_var('$whenCondition1_' + template_name)
    whenCondition2: Var = vf.add_var('$whenCondition2_' + template_name)
    whenCondition3: Var = vf.add_var('$whenCondition3_' + template_name)
    oel_IfdPu: Var = vf.add_var('oel.IfdPu_' + template_name)
    oel_combiTable1Ds_y_1: Var = vf.add_var('oel.combiTable1Ds.y[1]_' + template_name)
    oel_feedback_y: Var = vf.add_var('oel.feedback.y_' + template_name)
    oel_flipFlopR_y: Var = vf.add_var('oel.flipFlopR.y_' + template_name)
    oel_gain_y: Var = vf.add_var('oel.gain.y_' + template_name)
    oel_greaterThreshold_y: Var = vf.add_var('oel.greaterThreshold.y_' + template_name)
    oel_lessEqualThreshold_y: Var = vf.add_var('oel.lessEqualThreshold.y_' + template_name)
    oel_limIntegrator_local_reset: Var = vf.add_var('oel.limIntegrator.local_reset_' + template_name)
    oel_limIntegrator_local_set: Var = vf.add_var('oel.limIntegrator.local_set_' + template_name)
    oel_timer_entryTime: Var = vf.add_var('oel.timer.entryTime_' + template_name)
    oel_timer_y: Var = vf.add_var('oel.timer.y_' + template_name)
    time: Var = vf.add_var('time_' + template_name)
    # Declare the differential variables used by the template.
    d_oel_limIntegrator_y: Var = vf.add_diff_var('d_oel.limIntegrator.y_' + template_name, base_var=oel_limIntegrator_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_feedback_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_feedback_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_feedback_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((oel_limIntegrator_k * oel_feedback_y) - sym.Const(0.0)) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_feedback_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_feedback_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_feedback_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((oel_limIntegrator_k * oel_feedback_y) - sym.Const(0.0)) - sym.Const(1e-06)))))))) * (oel_limIntegrator_k * oel_feedback_y))))
    state_equations[0] = ((sym.Const(1.0) - (sym.heaviside((oel_limIntegrator_y - oel_limIntegrator_outMax) + sym.Const(1e-06)) * sym.heaviside(((oel_limIntegrator_k * oel_feedback_y) - sym.Const(0.0)) - sym.Const(1e-06)))) * (sym.Const(1.0) - (sym.heaviside((oel_limIntegrator_outMin - oel_limIntegrator_y) + sym.Const(1e-06)) * sym.heaviside((sym.Const(0.0) - (oel_limIntegrator_k * oel_feedback_y)) - sym.Const(1e-06)))) * (oel_limIntegrator_k * oel_feedback_y))
    state_variables: list[Var] = list()
    state_variables.append(oel_limIntegrator_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((whenCondition2 - (oel_greaterThreshold_y * (sym.Const(1.0) - oel_lessEqualThreshold_y))))
    algebraic_equations.append((whenCondition1 - oel_lessEqualThreshold_y))
    algebraic_equations.append((whenCondition3 - oel_flipFlopR_y))
    algebraic_equations.append((oel_timer_y - ((oel_flipFlopR_y * (time - oel_timer_entryTime)) + ((sym.Const(1.0) - oel_flipFlopR_y) * sym.Const(0.0)))))
    algebraic_equations.append((oel_combiTable1Ds_y_1 - ((((((sym.Const(1.5) * sym.heaviside(((sym.Const(14.0) - oel_timer_y) - sym.Const(1e-06)))) + ((((((sym.Const(1.5) - sym.Const(1.5)) / (sym.Const(15.0) - sym.Const(14.0))) * oel_timer_y) + (sym.Const(1.5) - (((sym.Const(1.5) - sym.Const(1.5)) / (sym.Const(15.0) - sym.Const(14.0))) * sym.Const(14.0)))) * sym.heaviside(((oel_timer_y - sym.Const(14.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(15.0) - oel_timer_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.2) - sym.Const(1.5)) / (sym.Const(30.0) - sym.Const(15.0))) * oel_timer_y) + (sym.Const(1.5) - (((sym.Const(1.2) - sym.Const(1.5)) / (sym.Const(30.0) - sym.Const(15.0))) * sym.Const(15.0)))) * sym.heaviside(((oel_timer_y - sym.Const(15.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(30.0) - oel_timer_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.1) - sym.Const(1.2)) / (sym.Const(60.0) - sym.Const(30.0))) * oel_timer_y) + (sym.Const(1.2) - (((sym.Const(1.1) - sym.Const(1.2)) / (sym.Const(60.0) - sym.Const(30.0))) * sym.Const(30.0)))) * sym.heaviside(((oel_timer_y - sym.Const(30.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(60.0) - oel_timer_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.1) - sym.Const(1.1)) / (sym.Const(61.0) - sym.Const(60.0))) * oel_timer_y) + (sym.Const(1.1) - (((sym.Const(1.1) - sym.Const(1.1)) / (sym.Const(61.0) - sym.Const(60.0))) * sym.Const(60.0)))) * sym.heaviside(((oel_timer_y - sym.Const(60.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(61.0) - oel_timer_y) - sym.Const(1e-06))))) + (sym.Const(1.1) * sym.heaviside(((oel_timer_y - sym.Const(61.0)) + sym.Const(1e-06)))))))
    algebraic_equations.append((oel_gain_y - (oel_gain_k * oel_combiTable1Ds_y_1)))
    algebraic_equations.append((oel_feedback_y - (oel_gain_y - oel_IfdPu)))
    algebraic_equations.append((oel_flipFlopR_y - sym.Const(0.0)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(whenCondition2)
    algebraic_variables.append(whenCondition1)
    algebraic_variables.append(whenCondition3)
    algebraic_variables.append(oel_timer_y)
    algebraic_variables.append(oel_combiTable1Ds_y_1)
    algebraic_variables.append(oel_gain_y)
    algebraic_variables.append(oel_feedback_y)
    algebraic_variables.append(oel_flipFlopR_y)
    algebraic_variables.append(oel_greaterThreshold_y)
    algebraic_variables.append(oel_lessEqualThreshold_y)
    algebraic_variables.append(oel_timer_entryTime)
    algebraic_variables.append(oel_IfdPu)
    algebraic_variables.append(oel_limIntegrator_local_reset)
    algebraic_variables.append(oel_limIntegrator_local_set)
    algebraic_variables.append(PRE_oel_flipFlopR_y)
    algebraic_variables.append(START_oel_flipFlopR_y)
    algebraic_variables.append(PRE_oel_timer_entryTime)
    differential_variables: list[Var] = list()
    differential_variables.append(d_oel_limIntegrator_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[oel_FOel_1_1] = (sym.Const(-1.0) + oel_t3)
    event_parameters[oel_FOel_1_2] = oel_Ifd3Pu
    event_parameters[oel_FOel_2_1] = oel_t3
    event_parameters[oel_FOel_2_2] = oel_Ifd3Pu
    event_parameters[oel_FOel_3_1] = oel_t2
    event_parameters[oel_FOel_3_2] = oel_Ifd2Pu
    event_parameters[oel_FOel_4_1] = oel_t1
    event_parameters[oel_FOel_4_2] = oel_Ifd1Pu
    event_parameters[oel_FOel_5_1] = (sym.Const(1.0) + oel_t1)
    event_parameters[oel_FOel_5_2] = oel_Ifd1Pu
    event_parameters[oel_Ifd0Pu] = vf.add_const(1.0, name='')
    event_parameters[oel_Ifd1Pu] = vf.add_const(1.1, name='')
    event_parameters[oel_Ifd2Pu] = vf.add_const(1.2, name='')
    event_parameters[oel_Ifd3Pu] = vf.add_const(1.5, name='')
    event_parameters[oel_IfdRated] = vf.add_const(2.6355, name='')
    event_parameters[oel_Kmx] = vf.add_const(0.2, name='')
    event_parameters[oel_ULowPu] = vf.add_const(-0.05, name='')
    event_parameters[oel_combiTable1Ds_table_1_1] = oel_FOel_1_1
    event_parameters[oel_combiTable1Ds_table_1_2] = oel_FOel_1_2
    event_parameters[oel_combiTable1Ds_table_2_1] = oel_FOel_2_1
    event_parameters[oel_combiTable1Ds_table_2_2] = oel_FOel_2_2
    event_parameters[oel_combiTable1Ds_table_3_1] = oel_FOel_3_1
    event_parameters[oel_combiTable1Ds_table_3_2] = oel_FOel_3_2
    event_parameters[oel_combiTable1Ds_table_4_1] = oel_FOel_4_1
    event_parameters[oel_combiTable1Ds_table_4_2] = oel_FOel_4_2
    event_parameters[oel_combiTable1Ds_table_5_1] = oel_FOel_5_1
    event_parameters[oel_combiTable1Ds_table_5_2] = oel_FOel_5_2
    event_parameters[oel_combiTable1Ds_u_max] = vf.add_const(61.0, name='')
    event_parameters[oel_combiTable1Ds_u_min] = vf.add_const(14.0, name='')
    event_parameters[oel_gain_k] = oel_IfdRated
    event_parameters[oel_greaterThreshold_threshold] = (oel_Ifd1Pu * oel_IfdRated)
    event_parameters[oel_lessEqualThreshold_threshold] = (sym.Const(0.98) * (oel_Ifd1Pu * oel_IfdRated))
    event_parameters[oel_limIntegrator_k] = oel_Kmx
    event_parameters[oel_limIntegrator_outMax] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_outMin] = oel_ULowPu
    event_parameters[oel_limIntegrator_y_start] = vf.add_const(0.0, name='')
    event_parameters[oel_t1] = vf.add_const(60.0, name='')
    event_parameters[oel_t2] = vf.add_const(30.0, name='')
    event_parameters[oel_t3] = vf.add_const(15.0, name='')
    event_parameters[oel_combiTable1Ds_columns_1] = vf.add_const(2.0, name='')
    event_parameters[oel_combiTable1Ds_extrapolation] = vf.add_const(1.0, name='')
    event_parameters[oel_combiTable1Ds_nout] = vf.add_const(1.0, name='')
    event_parameters[oel_combiTable1Ds_smoothness] = vf.add_const(1.0, name='')
    event_parameters[oel_limIntegrator_initType] = vf.add_const(3.0, name='')
    event_parameters[oel_combiTable1Ds_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[oel_combiTable1Ds_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[oel_combiTable1Ds_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[oel_flipFlopR_Y0] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[oel_limIntegrator_strict] = vf.add_const(1.0, name='')
    event_parameters[oel_limIntegrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[oel_combiTable1Ds_fileName] = vf.add_const(0.0, name='')
    event_parameters[oel_combiTable1Ds_tableName] = vf.add_const(0.0, name='')
    event_parameters[oel_combiTable1Ds_tableID] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[oel_limIntegrator_y] = oel_limIntegrator_y_start
    initial_equations[oel_IfdPu] = vf.add_const(1.0, name='')
    initial_equations[whenCondition1] = vf.add_const(1.0, name='')
    initial_equations[whenCondition2] = vf.add_const(0.0, name='')
    initial_equations[oel_flipFlopR_y] = PRE_oel_flipFlopR_y
    initial_equations[oel_limIntegrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[oel_limIntegrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[oel_lessEqualThreshold_y] = sym.heaviside(((oel_lessEqualThreshold_threshold - sym.Const(1.0)) + sym.Const(1e-06)))
    initial_equations[oel_greaterThreshold_y] = sym.heaviside(((sym.Const(1.0) - oel_greaterThreshold_threshold) - sym.Const(1e-06)))
    initial_equations[PRE_oel_flipFlopR_y] = START_oel_flipFlopR_y
    initial_equations[PRE_oel_timer_entryTime] = vf.add_const(0.0, name='')
    initial_equations[oel_timer_entryTime] = PRE_oel_timer_entryTime
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

    template.block.state_eqs[0] = ((sym.Const(1.0) - (sym.heaviside((oel_limIntegrator_y - oel_limIntegrator_outMax) + sym.Const(1e-06)) * sym.heaviside(((oel_limIntegrator_k * oel_feedback_y) - sym.Const(0.0)) - sym.Const(1e-06)))) * (sym.Const(1.0) - (sym.heaviside((oel_limIntegrator_outMin - oel_limIntegrator_y) + sym.Const(1e-06)) * sym.heaviside((sym.Const(0.0) - (oel_limIntegrator_k * oel_feedback_y)) - sym.Const(1e-06)))) * (oel_limIntegrator_k * oel_feedback_y))
    template.comment = 'Generator excitation limiter MAXEX2'
    return template
