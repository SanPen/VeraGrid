# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'WT4BCurrentSource2020'.

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

def build_wt4bcurrentsource2020_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'WT4BCurrentSource2020'
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
    wt_BesPu: Var = vf.add_var('wt.BesPu_' + template_name)
    wt_CdrtPu: Var = vf.add_var('wt.CdrtPu_' + template_name)
    wt_DPMaxP4BPu: Var = vf.add_var('wt.DPMaxP4BPu_' + template_name)
    wt_DPRefMax4BPu: Var = vf.add_var('wt.DPRefMax4BPu_' + template_name)
    wt_DPRefMin4BPu: Var = vf.add_var('wt.DPRefMin4BPu_' + template_name)
    wt_DUdb1Pu: Var = vf.add_var('wt.DUdb1Pu_' + template_name)
    wt_DUdb2Pu: Var = vf.add_var('wt.DUdb2Pu_' + template_name)
    wt_DfcMaxPu: Var = vf.add_var('wt.DfcMaxPu_' + template_name)
    wt_DfpMaxPu: Var = vf.add_var('wt.DfpMaxPu_' + template_name)
    wt_DipMaxPu: Var = vf.add_var('wt.DipMaxPu_' + template_name)
    wt_DiqMaxPu: Var = vf.add_var('wt.DiqMaxPu_' + template_name)
    wt_DiqMinPu: Var = vf.add_var('wt.DiqMinPu_' + template_name)
    wt_GesPu: Var = vf.add_var('wt.GesPu_' + template_name)
    wt_Hgen: Var = vf.add_var('wt.Hgen_' + template_name)
    wt_Hwtr: Var = vf.add_var('wt.Hwtr_' + template_name)
    wt_IGsIm0Pu: Var = vf.add_var('wt.IGsIm0Pu_' + template_name)
    wt_IGsRe0Pu: Var = vf.add_var('wt.IGsRe0Pu_' + template_name)
    wt_IMaxDipPu: Var = vf.add_var('wt.IMaxDipPu_' + template_name)
    wt_IMaxPu: Var = vf.add_var('wt.IMaxPu_' + template_name)
    wt_IpMax0Pu: Var = vf.add_var('wt.IpMax0Pu_' + template_name)
    wt_IqH1Pu: Var = vf.add_var('wt.IqH1Pu_' + template_name)
    wt_IqMax0Pu: Var = vf.add_var('wt.IqMax0Pu_' + template_name)
    wt_IqMaxPu: Var = vf.add_var('wt.IqMaxPu_' + template_name)
    wt_IqMin0Pu: Var = vf.add_var('wt.IqMin0Pu_' + template_name)
    wt_IqMinPu: Var = vf.add_var('wt.IqMinPu_' + template_name)
    wt_IqPostPu: Var = vf.add_var('wt.IqPostPu_' + template_name)
    wt_KdrtPu: Var = vf.add_var('wt.KdrtPu_' + template_name)
    wt_Kipaw: Var = vf.add_var('wt.Kipaw_' + template_name)
    wt_Kiq: Var = vf.add_var('wt.Kiq_' + template_name)
    wt_Kiqaw: Var = vf.add_var('wt.Kiqaw_' + template_name)
    wt_Kiu: Var = vf.add_var('wt.Kiu_' + template_name)
    wt_Kpaw: Var = vf.add_var('wt.Kpaw_' + template_name)
    wt_Kpq: Var = vf.add_var('wt.Kpq_' + template_name)
    wt_Kpqu: Var = vf.add_var('wt.Kpqu_' + template_name)
    wt_Kpu: Var = vf.add_var('wt.Kpu_' + template_name)
    wt_Kpufrt: Var = vf.add_var('wt.Kpufrt_' + template_name)
    wt_Kqv: Var = vf.add_var('wt.Kqv_' + template_name)
    wt_MdfsLim: Var = vf.add_var('wt.MdfsLim_' + template_name)
    wt_MpUScale: Var = vf.add_var('wt.MpUScale_' + template_name)
    wt_MqG: Var = vf.add_var('wt.MqG_' + template_name)
    wt_Mqfrt: Var = vf.add_var('wt.Mqfrt_' + template_name)
    wt_Mqpri: Var = vf.add_var('wt.Mqpri_' + template_name)
    wt_P0Pu: Var = vf.add_var('wt.P0Pu_' + template_name)
    wt_PAg0Pu: Var = vf.add_var('wt.PAg0Pu_' + template_name)
    wt_Q0Pu: Var = vf.add_var('wt.Q0Pu_' + template_name)
    wt_QMax0Pu: Var = vf.add_var('wt.QMax0Pu_' + template_name)
    wt_QMaxPu: Var = vf.add_var('wt.QMaxPu_' + template_name)
    wt_QMin0Pu: Var = vf.add_var('wt.QMin0Pu_' + template_name)
    wt_QMinPu: Var = vf.add_var('wt.QMinPu_' + template_name)
    wt_QlConst: Var = vf.add_var('wt.QlConst_' + template_name)
    wt_RDropPu: Var = vf.add_var('wt.RDropPu_' + template_name)
    wt_ResPu: Var = vf.add_var('wt.ResPu_' + template_name)
    wt_SNom: Var = vf.add_var('wt.SNom_' + template_name)
    wt_TableIpMaxUwt11: Var = vf.add_var('wt.TableIpMaxUwt11_' + template_name)
    wt_TableIpMaxUwt12: Var = vf.add_var('wt.TableIpMaxUwt12_' + template_name)
    wt_TableIpMaxUwt21: Var = vf.add_var('wt.TableIpMaxUwt21_' + template_name)
    wt_TableIpMaxUwt22: Var = vf.add_var('wt.TableIpMaxUwt22_' + template_name)
    wt_TableIpMaxUwt31: Var = vf.add_var('wt.TableIpMaxUwt31_' + template_name)
    wt_TableIpMaxUwt32: Var = vf.add_var('wt.TableIpMaxUwt32_' + template_name)
    wt_TableIpMaxUwt41: Var = vf.add_var('wt.TableIpMaxUwt41_' + template_name)
    wt_TableIpMaxUwt42: Var = vf.add_var('wt.TableIpMaxUwt42_' + template_name)
    wt_TableIpMaxUwt51: Var = vf.add_var('wt.TableIpMaxUwt51_' + template_name)
    wt_TableIpMaxUwt52: Var = vf.add_var('wt.TableIpMaxUwt52_' + template_name)
    wt_TableIpMaxUwt61: Var = vf.add_var('wt.TableIpMaxUwt61_' + template_name)
    wt_TableIpMaxUwt62: Var = vf.add_var('wt.TableIpMaxUwt62_' + template_name)
    wt_TableIpMaxUwt71: Var = vf.add_var('wt.TableIpMaxUwt71_' + template_name)
    wt_TableIpMaxUwt72: Var = vf.add_var('wt.TableIpMaxUwt72_' + template_name)
    wt_TableIpMaxUwt_1_1: Var = vf.add_var('wt.TableIpMaxUwt[1,1]_' + template_name)
    wt_TableIpMaxUwt_1_2: Var = vf.add_var('wt.TableIpMaxUwt[1,2]_' + template_name)
    wt_TableIpMaxUwt_2_1: Var = vf.add_var('wt.TableIpMaxUwt[2,1]_' + template_name)
    wt_TableIpMaxUwt_2_2: Var = vf.add_var('wt.TableIpMaxUwt[2,2]_' + template_name)
    wt_TableIpMaxUwt_3_1: Var = vf.add_var('wt.TableIpMaxUwt[3,1]_' + template_name)
    wt_TableIpMaxUwt_3_2: Var = vf.add_var('wt.TableIpMaxUwt[3,2]_' + template_name)
    wt_TableIpMaxUwt_4_1: Var = vf.add_var('wt.TableIpMaxUwt[4,1]_' + template_name)
    wt_TableIpMaxUwt_4_2: Var = vf.add_var('wt.TableIpMaxUwt[4,2]_' + template_name)
    wt_TableIpMaxUwt_5_1: Var = vf.add_var('wt.TableIpMaxUwt[5,1]_' + template_name)
    wt_TableIpMaxUwt_5_2: Var = vf.add_var('wt.TableIpMaxUwt[5,2]_' + template_name)
    wt_TableIpMaxUwt_6_1: Var = vf.add_var('wt.TableIpMaxUwt[6,1]_' + template_name)
    wt_TableIpMaxUwt_6_2: Var = vf.add_var('wt.TableIpMaxUwt[6,2]_' + template_name)
    wt_TableIpMaxUwt_7_1: Var = vf.add_var('wt.TableIpMaxUwt[7,1]_' + template_name)
    wt_TableIpMaxUwt_7_2: Var = vf.add_var('wt.TableIpMaxUwt[7,2]_' + template_name)
    wt_TableIqMaxUwt11: Var = vf.add_var('wt.TableIqMaxUwt11_' + template_name)
    wt_TableIqMaxUwt12: Var = vf.add_var('wt.TableIqMaxUwt12_' + template_name)
    wt_TableIqMaxUwt21: Var = vf.add_var('wt.TableIqMaxUwt21_' + template_name)
    wt_TableIqMaxUwt22: Var = vf.add_var('wt.TableIqMaxUwt22_' + template_name)
    wt_TableIqMaxUwt31: Var = vf.add_var('wt.TableIqMaxUwt31_' + template_name)
    wt_TableIqMaxUwt32: Var = vf.add_var('wt.TableIqMaxUwt32_' + template_name)
    wt_TableIqMaxUwt41: Var = vf.add_var('wt.TableIqMaxUwt41_' + template_name)
    wt_TableIqMaxUwt42: Var = vf.add_var('wt.TableIqMaxUwt42_' + template_name)
    wt_TableIqMaxUwt51: Var = vf.add_var('wt.TableIqMaxUwt51_' + template_name)
    wt_TableIqMaxUwt52: Var = vf.add_var('wt.TableIqMaxUwt52_' + template_name)
    wt_TableIqMaxUwt61: Var = vf.add_var('wt.TableIqMaxUwt61_' + template_name)
    wt_TableIqMaxUwt62: Var = vf.add_var('wt.TableIqMaxUwt62_' + template_name)
    wt_TableIqMaxUwt71: Var = vf.add_var('wt.TableIqMaxUwt71_' + template_name)
    wt_TableIqMaxUwt72: Var = vf.add_var('wt.TableIqMaxUwt72_' + template_name)
    wt_TableIqMaxUwt81: Var = vf.add_var('wt.TableIqMaxUwt81_' + template_name)
    wt_TableIqMaxUwt82: Var = vf.add_var('wt.TableIqMaxUwt82_' + template_name)
    wt_TableIqMaxUwt_1_1: Var = vf.add_var('wt.TableIqMaxUwt[1,1]_' + template_name)
    wt_TableIqMaxUwt_1_2: Var = vf.add_var('wt.TableIqMaxUwt[1,2]_' + template_name)
    wt_TableIqMaxUwt_2_1: Var = vf.add_var('wt.TableIqMaxUwt[2,1]_' + template_name)
    wt_TableIqMaxUwt_2_2: Var = vf.add_var('wt.TableIqMaxUwt[2,2]_' + template_name)
    wt_TableIqMaxUwt_3_1: Var = vf.add_var('wt.TableIqMaxUwt[3,1]_' + template_name)
    wt_TableIqMaxUwt_3_2: Var = vf.add_var('wt.TableIqMaxUwt[3,2]_' + template_name)
    wt_TableIqMaxUwt_4_1: Var = vf.add_var('wt.TableIqMaxUwt[4,1]_' + template_name)
    wt_TableIqMaxUwt_4_2: Var = vf.add_var('wt.TableIqMaxUwt[4,2]_' + template_name)
    wt_TableIqMaxUwt_5_1: Var = vf.add_var('wt.TableIqMaxUwt[5,1]_' + template_name)
    wt_TableIqMaxUwt_5_2: Var = vf.add_var('wt.TableIqMaxUwt[5,2]_' + template_name)
    wt_TableIqMaxUwt_6_1: Var = vf.add_var('wt.TableIqMaxUwt[6,1]_' + template_name)
    wt_TableIqMaxUwt_6_2: Var = vf.add_var('wt.TableIqMaxUwt[6,2]_' + template_name)
    wt_TableIqMaxUwt_7_1: Var = vf.add_var('wt.TableIqMaxUwt[7,1]_' + template_name)
    wt_TableIqMaxUwt_7_2: Var = vf.add_var('wt.TableIqMaxUwt[7,2]_' + template_name)
    wt_TableIqMaxUwt_8_1: Var = vf.add_var('wt.TableIqMaxUwt[8,1]_' + template_name)
    wt_TableIqMaxUwt_8_2: Var = vf.add_var('wt.TableIqMaxUwt[8,2]_' + template_name)
    wt_TableQMaxPwtcFilt11: Var = vf.add_var('wt.TableQMaxPwtcFilt11_' + template_name)
    wt_TableQMaxPwtcFilt12: Var = vf.add_var('wt.TableQMaxPwtcFilt12_' + template_name)
    wt_TableQMaxPwtcFilt21: Var = vf.add_var('wt.TableQMaxPwtcFilt21_' + template_name)
    wt_TableQMaxPwtcFilt22: Var = vf.add_var('wt.TableQMaxPwtcFilt22_' + template_name)
    wt_TableQMaxPwtcFilt31: Var = vf.add_var('wt.TableQMaxPwtcFilt31_' + template_name)
    wt_TableQMaxPwtcFilt32: Var = vf.add_var('wt.TableQMaxPwtcFilt32_' + template_name)
    wt_TableQMaxPwtcFilt41: Var = vf.add_var('wt.TableQMaxPwtcFilt41_' + template_name)
    wt_TableQMaxPwtcFilt42: Var = vf.add_var('wt.TableQMaxPwtcFilt42_' + template_name)
    wt_TableQMaxPwtcFilt_1_1: Var = vf.add_var('wt.TableQMaxPwtcFilt[1,1]_' + template_name)
    wt_TableQMaxPwtcFilt_1_2: Var = vf.add_var('wt.TableQMaxPwtcFilt[1,2]_' + template_name)
    wt_TableQMaxPwtcFilt_2_1: Var = vf.add_var('wt.TableQMaxPwtcFilt[2,1]_' + template_name)
    wt_TableQMaxPwtcFilt_2_2: Var = vf.add_var('wt.TableQMaxPwtcFilt[2,2]_' + template_name)
    wt_TableQMaxPwtcFilt_3_1: Var = vf.add_var('wt.TableQMaxPwtcFilt[3,1]_' + template_name)
    wt_TableQMaxPwtcFilt_3_2: Var = vf.add_var('wt.TableQMaxPwtcFilt[3,2]_' + template_name)
    wt_TableQMaxPwtcFilt_4_1: Var = vf.add_var('wt.TableQMaxPwtcFilt[4,1]_' + template_name)
    wt_TableQMaxPwtcFilt_4_2: Var = vf.add_var('wt.TableQMaxPwtcFilt[4,2]_' + template_name)
    wt_TableQMaxUwtcFilt11: Var = vf.add_var('wt.TableQMaxUwtcFilt11_' + template_name)
    wt_TableQMaxUwtcFilt12: Var = vf.add_var('wt.TableQMaxUwtcFilt12_' + template_name)
    wt_TableQMaxUwtcFilt21: Var = vf.add_var('wt.TableQMaxUwtcFilt21_' + template_name)
    wt_TableQMaxUwtcFilt22: Var = vf.add_var('wt.TableQMaxUwtcFilt22_' + template_name)
    wt_TableQMaxUwtcFilt31: Var = vf.add_var('wt.TableQMaxUwtcFilt31_' + template_name)
    wt_TableQMaxUwtcFilt32: Var = vf.add_var('wt.TableQMaxUwtcFilt32_' + template_name)
    wt_TableQMaxUwtcFilt41: Var = vf.add_var('wt.TableQMaxUwtcFilt41_' + template_name)
    wt_TableQMaxUwtcFilt42: Var = vf.add_var('wt.TableQMaxUwtcFilt42_' + template_name)
    wt_TableQMaxUwtcFilt51: Var = vf.add_var('wt.TableQMaxUwtcFilt51_' + template_name)
    wt_TableQMaxUwtcFilt52: Var = vf.add_var('wt.TableQMaxUwtcFilt52_' + template_name)
    wt_TableQMaxUwtcFilt61: Var = vf.add_var('wt.TableQMaxUwtcFilt61_' + template_name)
    wt_TableQMaxUwtcFilt62: Var = vf.add_var('wt.TableQMaxUwtcFilt62_' + template_name)
    wt_TableQMaxUwtcFilt_1_1: Var = vf.add_var('wt.TableQMaxUwtcFilt[1,1]_' + template_name)
    wt_TableQMaxUwtcFilt_1_2: Var = vf.add_var('wt.TableQMaxUwtcFilt[1,2]_' + template_name)
    wt_TableQMaxUwtcFilt_2_1: Var = vf.add_var('wt.TableQMaxUwtcFilt[2,1]_' + template_name)
    wt_TableQMaxUwtcFilt_2_2: Var = vf.add_var('wt.TableQMaxUwtcFilt[2,2]_' + template_name)
    wt_TableQMaxUwtcFilt_3_1: Var = vf.add_var('wt.TableQMaxUwtcFilt[3,1]_' + template_name)
    wt_TableQMaxUwtcFilt_3_2: Var = vf.add_var('wt.TableQMaxUwtcFilt[3,2]_' + template_name)
    wt_TableQMaxUwtcFilt_4_1: Var = vf.add_var('wt.TableQMaxUwtcFilt[4,1]_' + template_name)
    wt_TableQMaxUwtcFilt_4_2: Var = vf.add_var('wt.TableQMaxUwtcFilt[4,2]_' + template_name)
    wt_TableQMaxUwtcFilt_5_1: Var = vf.add_var('wt.TableQMaxUwtcFilt[5,1]_' + template_name)
    wt_TableQMaxUwtcFilt_5_2: Var = vf.add_var('wt.TableQMaxUwtcFilt[5,2]_' + template_name)
    wt_TableQMaxUwtcFilt_6_1: Var = vf.add_var('wt.TableQMaxUwtcFilt[6,1]_' + template_name)
    wt_TableQMaxUwtcFilt_6_2: Var = vf.add_var('wt.TableQMaxUwtcFilt[6,2]_' + template_name)
    wt_TableQMinPwtcFilt11: Var = vf.add_var('wt.TableQMinPwtcFilt11_' + template_name)
    wt_TableQMinPwtcFilt12: Var = vf.add_var('wt.TableQMinPwtcFilt12_' + template_name)
    wt_TableQMinPwtcFilt21: Var = vf.add_var('wt.TableQMinPwtcFilt21_' + template_name)
    wt_TableQMinPwtcFilt22: Var = vf.add_var('wt.TableQMinPwtcFilt22_' + template_name)
    wt_TableQMinPwtcFilt31: Var = vf.add_var('wt.TableQMinPwtcFilt31_' + template_name)
    wt_TableQMinPwtcFilt32: Var = vf.add_var('wt.TableQMinPwtcFilt32_' + template_name)
    wt_TableQMinPwtcFilt41: Var = vf.add_var('wt.TableQMinPwtcFilt41_' + template_name)
    wt_TableQMinPwtcFilt42: Var = vf.add_var('wt.TableQMinPwtcFilt42_' + template_name)
    wt_TableQMinPwtcFilt_1_1: Var = vf.add_var('wt.TableQMinPwtcFilt[1,1]_' + template_name)
    wt_TableQMinPwtcFilt_1_2: Var = vf.add_var('wt.TableQMinPwtcFilt[1,2]_' + template_name)
    wt_TableQMinPwtcFilt_2_1: Var = vf.add_var('wt.TableQMinPwtcFilt[2,1]_' + template_name)
    wt_TableQMinPwtcFilt_2_2: Var = vf.add_var('wt.TableQMinPwtcFilt[2,2]_' + template_name)
    wt_TableQMinPwtcFilt_3_1: Var = vf.add_var('wt.TableQMinPwtcFilt[3,1]_' + template_name)
    wt_TableQMinPwtcFilt_3_2: Var = vf.add_var('wt.TableQMinPwtcFilt[3,2]_' + template_name)
    wt_TableQMinPwtcFilt_4_1: Var = vf.add_var('wt.TableQMinPwtcFilt[4,1]_' + template_name)
    wt_TableQMinPwtcFilt_4_2: Var = vf.add_var('wt.TableQMinPwtcFilt[4,2]_' + template_name)
    wt_TableQMinUwtcFilt11: Var = vf.add_var('wt.TableQMinUwtcFilt11_' + template_name)
    wt_TableQMinUwtcFilt12: Var = vf.add_var('wt.TableQMinUwtcFilt12_' + template_name)
    wt_TableQMinUwtcFilt21: Var = vf.add_var('wt.TableQMinUwtcFilt21_' + template_name)
    wt_TableQMinUwtcFilt22: Var = vf.add_var('wt.TableQMinUwtcFilt22_' + template_name)
    wt_TableQMinUwtcFilt31: Var = vf.add_var('wt.TableQMinUwtcFilt31_' + template_name)
    wt_TableQMinUwtcFilt32: Var = vf.add_var('wt.TableQMinUwtcFilt32_' + template_name)
    wt_TableQMinUwtcFilt41: Var = vf.add_var('wt.TableQMinUwtcFilt41_' + template_name)
    wt_TableQMinUwtcFilt42: Var = vf.add_var('wt.TableQMinUwtcFilt42_' + template_name)
    wt_TableQMinUwtcFilt_1_1: Var = vf.add_var('wt.TableQMinUwtcFilt[1,1]_' + template_name)
    wt_TableQMinUwtcFilt_1_2: Var = vf.add_var('wt.TableQMinUwtcFilt[1,2]_' + template_name)
    wt_TableQMinUwtcFilt_2_1: Var = vf.add_var('wt.TableQMinUwtcFilt[2,1]_' + template_name)
    wt_TableQMinUwtcFilt_2_2: Var = vf.add_var('wt.TableQMinUwtcFilt[2,2]_' + template_name)
    wt_TableQMinUwtcFilt_3_1: Var = vf.add_var('wt.TableQMinUwtcFilt[3,1]_' + template_name)
    wt_TableQMinUwtcFilt_3_2: Var = vf.add_var('wt.TableQMinUwtcFilt[3,2]_' + template_name)
    wt_TableQMinUwtcFilt_4_1: Var = vf.add_var('wt.TableQMinUwtcFilt[4,1]_' + template_name)
    wt_TableQMinUwtcFilt_4_2: Var = vf.add_var('wt.TableQMinUwtcFilt[4,2]_' + template_name)
    wt_TabletUoverUwtfilt11: Var = vf.add_var('wt.TabletUoverUwtfilt11_' + template_name)
    wt_TabletUoverUwtfilt12: Var = vf.add_var('wt.TabletUoverUwtfilt12_' + template_name)
    wt_TabletUoverUwtfilt21: Var = vf.add_var('wt.TabletUoverUwtfilt21_' + template_name)
    wt_TabletUoverUwtfilt22: Var = vf.add_var('wt.TabletUoverUwtfilt22_' + template_name)
    wt_TabletUoverUwtfilt31: Var = vf.add_var('wt.TabletUoverUwtfilt31_' + template_name)
    wt_TabletUoverUwtfilt32: Var = vf.add_var('wt.TabletUoverUwtfilt32_' + template_name)
    wt_TabletUoverUwtfilt41: Var = vf.add_var('wt.TabletUoverUwtfilt41_' + template_name)
    wt_TabletUoverUwtfilt42: Var = vf.add_var('wt.TabletUoverUwtfilt42_' + template_name)
    wt_TabletUoverUwtfilt51: Var = vf.add_var('wt.TabletUoverUwtfilt51_' + template_name)
    wt_TabletUoverUwtfilt52: Var = vf.add_var('wt.TabletUoverUwtfilt52_' + template_name)
    wt_TabletUoverUwtfilt61: Var = vf.add_var('wt.TabletUoverUwtfilt61_' + template_name)
    wt_TabletUoverUwtfilt62: Var = vf.add_var('wt.TabletUoverUwtfilt62_' + template_name)
    wt_TabletUoverUwtfilt71: Var = vf.add_var('wt.TabletUoverUwtfilt71_' + template_name)
    wt_TabletUoverUwtfilt72: Var = vf.add_var('wt.TabletUoverUwtfilt72_' + template_name)
    wt_TabletUoverUwtfilt81: Var = vf.add_var('wt.TabletUoverUwtfilt81_' + template_name)
    wt_TabletUoverUwtfilt82: Var = vf.add_var('wt.TabletUoverUwtfilt82_' + template_name)
    wt_TabletUoverUwtfilt_1_1: Var = vf.add_var('wt.TabletUoverUwtfilt[1,1]_' + template_name)
    wt_TabletUoverUwtfilt_1_2: Var = vf.add_var('wt.TabletUoverUwtfilt[1,2]_' + template_name)
    wt_TabletUoverUwtfilt_2_1: Var = vf.add_var('wt.TabletUoverUwtfilt[2,1]_' + template_name)
    wt_TabletUoverUwtfilt_2_2: Var = vf.add_var('wt.TabletUoverUwtfilt[2,2]_' + template_name)
    wt_TabletUoverUwtfilt_3_1: Var = vf.add_var('wt.TabletUoverUwtfilt[3,1]_' + template_name)
    wt_TabletUoverUwtfilt_3_2: Var = vf.add_var('wt.TabletUoverUwtfilt[3,2]_' + template_name)
    wt_TabletUoverUwtfilt_4_1: Var = vf.add_var('wt.TabletUoverUwtfilt[4,1]_' + template_name)
    wt_TabletUoverUwtfilt_4_2: Var = vf.add_var('wt.TabletUoverUwtfilt[4,2]_' + template_name)
    wt_TabletUoverUwtfilt_5_1: Var = vf.add_var('wt.TabletUoverUwtfilt[5,1]_' + template_name)
    wt_TabletUoverUwtfilt_5_2: Var = vf.add_var('wt.TabletUoverUwtfilt[5,2]_' + template_name)
    wt_TabletUoverUwtfilt_6_1: Var = vf.add_var('wt.TabletUoverUwtfilt[6,1]_' + template_name)
    wt_TabletUoverUwtfilt_6_2: Var = vf.add_var('wt.TabletUoverUwtfilt[6,2]_' + template_name)
    wt_TabletUoverUwtfilt_7_1: Var = vf.add_var('wt.TabletUoverUwtfilt[7,1]_' + template_name)
    wt_TabletUoverUwtfilt_7_2: Var = vf.add_var('wt.TabletUoverUwtfilt[7,2]_' + template_name)
    wt_TabletUoverUwtfilt_8_1: Var = vf.add_var('wt.TabletUoverUwtfilt[8,1]_' + template_name)
    wt_TabletUoverUwtfilt_8_2: Var = vf.add_var('wt.TabletUoverUwtfilt[8,2]_' + template_name)
    wt_TabletUunderUwtfilt11: Var = vf.add_var('wt.TabletUunderUwtfilt11_' + template_name)
    wt_TabletUunderUwtfilt12: Var = vf.add_var('wt.TabletUunderUwtfilt12_' + template_name)
    wt_TabletUunderUwtfilt21: Var = vf.add_var('wt.TabletUunderUwtfilt21_' + template_name)
    wt_TabletUunderUwtfilt22: Var = vf.add_var('wt.TabletUunderUwtfilt22_' + template_name)
    wt_TabletUunderUwtfilt31: Var = vf.add_var('wt.TabletUunderUwtfilt31_' + template_name)
    wt_TabletUunderUwtfilt32: Var = vf.add_var('wt.TabletUunderUwtfilt32_' + template_name)
    wt_TabletUunderUwtfilt41: Var = vf.add_var('wt.TabletUunderUwtfilt41_' + template_name)
    wt_TabletUunderUwtfilt42: Var = vf.add_var('wt.TabletUunderUwtfilt42_' + template_name)
    wt_TabletUunderUwtfilt51: Var = vf.add_var('wt.TabletUunderUwtfilt51_' + template_name)
    wt_TabletUunderUwtfilt52: Var = vf.add_var('wt.TabletUunderUwtfilt52_' + template_name)
    wt_TabletUunderUwtfilt61: Var = vf.add_var('wt.TabletUunderUwtfilt61_' + template_name)
    wt_TabletUunderUwtfilt62: Var = vf.add_var('wt.TabletUunderUwtfilt62_' + template_name)
    wt_TabletUunderUwtfilt71: Var = vf.add_var('wt.TabletUunderUwtfilt71_' + template_name)
    wt_TabletUunderUwtfilt72: Var = vf.add_var('wt.TabletUunderUwtfilt72_' + template_name)
    wt_TabletUunderUwtfilt_1_1: Var = vf.add_var('wt.TabletUunderUwtfilt[1,1]_' + template_name)
    wt_TabletUunderUwtfilt_1_2: Var = vf.add_var('wt.TabletUunderUwtfilt[1,2]_' + template_name)
    wt_TabletUunderUwtfilt_2_1: Var = vf.add_var('wt.TabletUunderUwtfilt[2,1]_' + template_name)
    wt_TabletUunderUwtfilt_2_2: Var = vf.add_var('wt.TabletUunderUwtfilt[2,2]_' + template_name)
    wt_TabletUunderUwtfilt_3_1: Var = vf.add_var('wt.TabletUunderUwtfilt[3,1]_' + template_name)
    wt_TabletUunderUwtfilt_3_2: Var = vf.add_var('wt.TabletUunderUwtfilt[3,2]_' + template_name)
    wt_TabletUunderUwtfilt_4_1: Var = vf.add_var('wt.TabletUunderUwtfilt[4,1]_' + template_name)
    wt_TabletUunderUwtfilt_4_2: Var = vf.add_var('wt.TabletUunderUwtfilt[4,2]_' + template_name)
    wt_TabletUunderUwtfilt_5_1: Var = vf.add_var('wt.TabletUunderUwtfilt[5,1]_' + template_name)
    wt_TabletUunderUwtfilt_5_2: Var = vf.add_var('wt.TabletUunderUwtfilt[5,2]_' + template_name)
    wt_TabletUunderUwtfilt_6_1: Var = vf.add_var('wt.TabletUunderUwtfilt[6,1]_' + template_name)
    wt_TabletUunderUwtfilt_6_2: Var = vf.add_var('wt.TabletUunderUwtfilt[6,2]_' + template_name)
    wt_TabletUunderUwtfilt_7_1: Var = vf.add_var('wt.TabletUunderUwtfilt[7,1]_' + template_name)
    wt_TabletUunderUwtfilt_7_2: Var = vf.add_var('wt.TabletUunderUwtfilt[7,2]_' + template_name)
    wt_Tabletfoverfwtfilt11: Var = vf.add_var('wt.Tabletfoverfwtfilt11_' + template_name)
    wt_Tabletfoverfwtfilt12: Var = vf.add_var('wt.Tabletfoverfwtfilt12_' + template_name)
    wt_Tabletfoverfwtfilt21: Var = vf.add_var('wt.Tabletfoverfwtfilt21_' + template_name)
    wt_Tabletfoverfwtfilt22: Var = vf.add_var('wt.Tabletfoverfwtfilt22_' + template_name)
    wt_Tabletfoverfwtfilt31: Var = vf.add_var('wt.Tabletfoverfwtfilt31_' + template_name)
    wt_Tabletfoverfwtfilt32: Var = vf.add_var('wt.Tabletfoverfwtfilt32_' + template_name)
    wt_Tabletfoverfwtfilt41: Var = vf.add_var('wt.Tabletfoverfwtfilt41_' + template_name)
    wt_Tabletfoverfwtfilt42: Var = vf.add_var('wt.Tabletfoverfwtfilt42_' + template_name)
    wt_Tabletfoverfwtfilt_1_1: Var = vf.add_var('wt.Tabletfoverfwtfilt[1,1]_' + template_name)
    wt_Tabletfoverfwtfilt_1_2: Var = vf.add_var('wt.Tabletfoverfwtfilt[1,2]_' + template_name)
    wt_Tabletfoverfwtfilt_2_1: Var = vf.add_var('wt.Tabletfoverfwtfilt[2,1]_' + template_name)
    wt_Tabletfoverfwtfilt_2_2: Var = vf.add_var('wt.Tabletfoverfwtfilt[2,2]_' + template_name)
    wt_Tabletfoverfwtfilt_3_1: Var = vf.add_var('wt.Tabletfoverfwtfilt[3,1]_' + template_name)
    wt_Tabletfoverfwtfilt_3_2: Var = vf.add_var('wt.Tabletfoverfwtfilt[3,2]_' + template_name)
    wt_Tabletfoverfwtfilt_4_1: Var = vf.add_var('wt.Tabletfoverfwtfilt[4,1]_' + template_name)
    wt_Tabletfoverfwtfilt_4_2: Var = vf.add_var('wt.Tabletfoverfwtfilt[4,2]_' + template_name)
    wt_Tabletfunderfwtfilt11: Var = vf.add_var('wt.Tabletfunderfwtfilt11_' + template_name)
    wt_Tabletfunderfwtfilt12: Var = vf.add_var('wt.Tabletfunderfwtfilt12_' + template_name)
    wt_Tabletfunderfwtfilt21: Var = vf.add_var('wt.Tabletfunderfwtfilt21_' + template_name)
    wt_Tabletfunderfwtfilt22: Var = vf.add_var('wt.Tabletfunderfwtfilt22_' + template_name)
    wt_Tabletfunderfwtfilt31: Var = vf.add_var('wt.Tabletfunderfwtfilt31_' + template_name)
    wt_Tabletfunderfwtfilt32: Var = vf.add_var('wt.Tabletfunderfwtfilt32_' + template_name)
    wt_Tabletfunderfwtfilt41: Var = vf.add_var('wt.Tabletfunderfwtfilt41_' + template_name)
    wt_Tabletfunderfwtfilt42: Var = vf.add_var('wt.Tabletfunderfwtfilt42_' + template_name)
    wt_Tabletfunderfwtfilt51: Var = vf.add_var('wt.Tabletfunderfwtfilt51_' + template_name)
    wt_Tabletfunderfwtfilt52: Var = vf.add_var('wt.Tabletfunderfwtfilt52_' + template_name)
    wt_Tabletfunderfwtfilt61: Var = vf.add_var('wt.Tabletfunderfwtfilt61_' + template_name)
    wt_Tabletfunderfwtfilt62: Var = vf.add_var('wt.Tabletfunderfwtfilt62_' + template_name)
    wt_Tabletfunderfwtfilt_1_1: Var = vf.add_var('wt.Tabletfunderfwtfilt[1,1]_' + template_name)
    wt_Tabletfunderfwtfilt_1_2: Var = vf.add_var('wt.Tabletfunderfwtfilt[1,2]_' + template_name)
    wt_Tabletfunderfwtfilt_2_1: Var = vf.add_var('wt.Tabletfunderfwtfilt[2,1]_' + template_name)
    wt_Tabletfunderfwtfilt_2_2: Var = vf.add_var('wt.Tabletfunderfwtfilt[2,2]_' + template_name)
    wt_Tabletfunderfwtfilt_3_1: Var = vf.add_var('wt.Tabletfunderfwtfilt[3,1]_' + template_name)
    wt_Tabletfunderfwtfilt_3_2: Var = vf.add_var('wt.Tabletfunderfwtfilt[3,2]_' + template_name)
    wt_Tabletfunderfwtfilt_4_1: Var = vf.add_var('wt.Tabletfunderfwtfilt[4,1]_' + template_name)
    wt_Tabletfunderfwtfilt_4_2: Var = vf.add_var('wt.Tabletfunderfwtfilt[4,2]_' + template_name)
    wt_Tabletfunderfwtfilt_5_1: Var = vf.add_var('wt.Tabletfunderfwtfilt[5,1]_' + template_name)
    wt_Tabletfunderfwtfilt_5_2: Var = vf.add_var('wt.Tabletfunderfwtfilt[5,2]_' + template_name)
    wt_Tabletfunderfwtfilt_6_1: Var = vf.add_var('wt.Tabletfunderfwtfilt[6,1]_' + template_name)
    wt_Tabletfunderfwtfilt_6_2: Var = vf.add_var('wt.Tabletfunderfwtfilt[6,2]_' + template_name)
    wt_U0Pu: Var = vf.add_var('wt.U0Pu_' + template_name)
    wt_UGsIm0Pu: Var = vf.add_var('wt.UGsIm0Pu_' + template_name)
    wt_UGsRe0Pu: Var = vf.add_var('wt.UGsRe0Pu_' + template_name)
    wt_UMaxPu: Var = vf.add_var('wt.UMaxPu_' + template_name)
    wt_UMinPu: Var = vf.add_var('wt.UMinPu_' + template_name)
    wt_UOverPu: Var = vf.add_var('wt.UOverPu_' + template_name)
    wt_UPhase0: Var = vf.add_var('wt.UPhase0_' + template_name)
    wt_UPll1Pu: Var = vf.add_var('wt.UPll1Pu_' + template_name)
    wt_UPll2Pu: Var = vf.add_var('wt.UPll2Pu_' + template_name)
    wt_URef0Pu: Var = vf.add_var('wt.URef0Pu_' + template_name)
    wt_UUnderPu: Var = vf.add_var('wt.UUnderPu_' + template_name)
    wt_UpDipPu: Var = vf.add_var('wt.UpDipPu_' + template_name)
    wt_UpquMaxPu: Var = vf.add_var('wt.UpquMaxPu_' + template_name)
    wt_UqDipPu: Var = vf.add_var('wt.UqDipPu_' + template_name)
    wt_UqRisePu: Var = vf.add_var('wt.UqRisePu_' + template_name)
    wt_XDropPu: Var = vf.add_var('wt.XDropPu_' + template_name)
    wt_XWT0Pu: Var = vf.add_var('wt.XWT0Pu_' + template_name)
    wt_XesPu: Var = vf.add_var('wt.XesPu_' + template_name)
    wt_control4B_DPMaxP4BPu: Var = vf.add_var('wt.control4B.DPMaxP4BPu_' + template_name)
    wt_control4B_DPRefMax4BPu: Var = vf.add_var('wt.control4B.DPRefMax4BPu_' + template_name)
    wt_control4B_DPRefMin4BPu: Var = vf.add_var('wt.control4B.DPRefMin4BPu_' + template_name)
    wt_control4B_DUdb1Pu: Var = vf.add_var('wt.control4B.DUdb1Pu_' + template_name)
    wt_control4B_DUdb2Pu: Var = vf.add_var('wt.control4B.DUdb2Pu_' + template_name)
    wt_control4B_IMaxDipPu: Var = vf.add_var('wt.control4B.IMaxDipPu_' + template_name)
    wt_control4B_IMaxPu: Var = vf.add_var('wt.control4B.IMaxPu_' + template_name)
    wt_control4B_IpMax0Pu: Var = vf.add_var('wt.control4B.IpMax0Pu_' + template_name)
    wt_control4B_IqH1Pu: Var = vf.add_var('wt.control4B.IqH1Pu_' + template_name)
    wt_control4B_IqMax0Pu: Var = vf.add_var('wt.control4B.IqMax0Pu_' + template_name)
    wt_control4B_IqMaxPu: Var = vf.add_var('wt.control4B.IqMaxPu_' + template_name)
    wt_control4B_IqMin0Pu: Var = vf.add_var('wt.control4B.IqMin0Pu_' + template_name)
    wt_control4B_IqMinPu: Var = vf.add_var('wt.control4B.IqMinPu_' + template_name)
    wt_control4B_IqPostPu: Var = vf.add_var('wt.control4B.IqPostPu_' + template_name)
    wt_control4B_Kiq: Var = vf.add_var('wt.control4B.Kiq_' + template_name)
    wt_control4B_Kiu: Var = vf.add_var('wt.control4B.Kiu_' + template_name)
    wt_control4B_Kpaw: Var = vf.add_var('wt.control4B.Kpaw_' + template_name)
    wt_control4B_Kpq: Var = vf.add_var('wt.control4B.Kpq_' + template_name)
    wt_control4B_Kpqu: Var = vf.add_var('wt.control4B.Kpqu_' + template_name)
    wt_control4B_Kpu: Var = vf.add_var('wt.control4B.Kpu_' + template_name)
    wt_control4B_Kpufrt: Var = vf.add_var('wt.control4B.Kpufrt_' + template_name)
    wt_control4B_Kqv: Var = vf.add_var('wt.control4B.Kqv_' + template_name)
    wt_control4B_MdfsLim: Var = vf.add_var('wt.control4B.MdfsLim_' + template_name)
    wt_control4B_MpUScale: Var = vf.add_var('wt.control4B.MpUScale_' + template_name)
    wt_control4B_MqG: Var = vf.add_var('wt.control4B.MqG_' + template_name)
    wt_control4B_Mqfrt: Var = vf.add_var('wt.control4B.Mqfrt_' + template_name)
    wt_control4B_Mqpri: Var = vf.add_var('wt.control4B.Mqpri_' + template_name)
    wt_control4B_P0Pu: Var = vf.add_var('wt.control4B.P0Pu_' + template_name)
    wt_control4B_Q0Pu: Var = vf.add_var('wt.control4B.Q0Pu_' + template_name)
    wt_control4B_QMax0Pu: Var = vf.add_var('wt.control4B.QMax0Pu_' + template_name)
    wt_control4B_QMaxPu: Var = vf.add_var('wt.control4B.QMaxPu_' + template_name)
    wt_control4B_QMin0Pu: Var = vf.add_var('wt.control4B.QMin0Pu_' + template_name)
    wt_control4B_QMinPu: Var = vf.add_var('wt.control4B.QMinPu_' + template_name)
    wt_control4B_QlConst: Var = vf.add_var('wt.control4B.QlConst_' + template_name)
    wt_control4B_RDropPu: Var = vf.add_var('wt.control4B.RDropPu_' + template_name)
    wt_control4B_SNom: Var = vf.add_var('wt.control4B.SNom_' + template_name)
    wt_control4B_TableIpMaxUwt11: Var = vf.add_var('wt.control4B.TableIpMaxUwt11_' + template_name)
    wt_control4B_TableIpMaxUwt12: Var = vf.add_var('wt.control4B.TableIpMaxUwt12_' + template_name)
    wt_control4B_TableIpMaxUwt21: Var = vf.add_var('wt.control4B.TableIpMaxUwt21_' + template_name)
    wt_control4B_TableIpMaxUwt22: Var = vf.add_var('wt.control4B.TableIpMaxUwt22_' + template_name)
    wt_control4B_TableIpMaxUwt31: Var = vf.add_var('wt.control4B.TableIpMaxUwt31_' + template_name)
    wt_control4B_TableIpMaxUwt32: Var = vf.add_var('wt.control4B.TableIpMaxUwt32_' + template_name)
    wt_control4B_TableIpMaxUwt41: Var = vf.add_var('wt.control4B.TableIpMaxUwt41_' + template_name)
    wt_control4B_TableIpMaxUwt42: Var = vf.add_var('wt.control4B.TableIpMaxUwt42_' + template_name)
    wt_control4B_TableIpMaxUwt51: Var = vf.add_var('wt.control4B.TableIpMaxUwt51_' + template_name)
    wt_control4B_TableIpMaxUwt52: Var = vf.add_var('wt.control4B.TableIpMaxUwt52_' + template_name)
    wt_control4B_TableIpMaxUwt61: Var = vf.add_var('wt.control4B.TableIpMaxUwt61_' + template_name)
    wt_control4B_TableIpMaxUwt62: Var = vf.add_var('wt.control4B.TableIpMaxUwt62_' + template_name)
    wt_control4B_TableIpMaxUwt71: Var = vf.add_var('wt.control4B.TableIpMaxUwt71_' + template_name)
    wt_control4B_TableIpMaxUwt72: Var = vf.add_var('wt.control4B.TableIpMaxUwt72_' + template_name)
    wt_control4B_TableIpMaxUwt_1_1: Var = vf.add_var('wt.control4B.TableIpMaxUwt[1,1]_' + template_name)
    wt_control4B_TableIpMaxUwt_1_2: Var = vf.add_var('wt.control4B.TableIpMaxUwt[1,2]_' + template_name)
    wt_control4B_TableIpMaxUwt_2_1: Var = vf.add_var('wt.control4B.TableIpMaxUwt[2,1]_' + template_name)
    wt_control4B_TableIpMaxUwt_2_2: Var = vf.add_var('wt.control4B.TableIpMaxUwt[2,2]_' + template_name)
    wt_control4B_TableIpMaxUwt_3_1: Var = vf.add_var('wt.control4B.TableIpMaxUwt[3,1]_' + template_name)
    wt_control4B_TableIpMaxUwt_3_2: Var = vf.add_var('wt.control4B.TableIpMaxUwt[3,2]_' + template_name)
    wt_control4B_TableIpMaxUwt_4_1: Var = vf.add_var('wt.control4B.TableIpMaxUwt[4,1]_' + template_name)
    wt_control4B_TableIpMaxUwt_4_2: Var = vf.add_var('wt.control4B.TableIpMaxUwt[4,2]_' + template_name)
    wt_control4B_TableIpMaxUwt_5_1: Var = vf.add_var('wt.control4B.TableIpMaxUwt[5,1]_' + template_name)
    wt_control4B_TableIpMaxUwt_5_2: Var = vf.add_var('wt.control4B.TableIpMaxUwt[5,2]_' + template_name)
    wt_control4B_TableIpMaxUwt_6_1: Var = vf.add_var('wt.control4B.TableIpMaxUwt[6,1]_' + template_name)
    wt_control4B_TableIpMaxUwt_6_2: Var = vf.add_var('wt.control4B.TableIpMaxUwt[6,2]_' + template_name)
    wt_control4B_TableIpMaxUwt_7_1: Var = vf.add_var('wt.control4B.TableIpMaxUwt[7,1]_' + template_name)
    wt_control4B_TableIpMaxUwt_7_2: Var = vf.add_var('wt.control4B.TableIpMaxUwt[7,2]_' + template_name)
    wt_control4B_TableIqMaxUwt11: Var = vf.add_var('wt.control4B.TableIqMaxUwt11_' + template_name)
    wt_control4B_TableIqMaxUwt12: Var = vf.add_var('wt.control4B.TableIqMaxUwt12_' + template_name)
    wt_control4B_TableIqMaxUwt21: Var = vf.add_var('wt.control4B.TableIqMaxUwt21_' + template_name)
    wt_control4B_TableIqMaxUwt22: Var = vf.add_var('wt.control4B.TableIqMaxUwt22_' + template_name)
    wt_control4B_TableIqMaxUwt31: Var = vf.add_var('wt.control4B.TableIqMaxUwt31_' + template_name)
    wt_control4B_TableIqMaxUwt32: Var = vf.add_var('wt.control4B.TableIqMaxUwt32_' + template_name)
    wt_control4B_TableIqMaxUwt41: Var = vf.add_var('wt.control4B.TableIqMaxUwt41_' + template_name)
    wt_control4B_TableIqMaxUwt42: Var = vf.add_var('wt.control4B.TableIqMaxUwt42_' + template_name)
    wt_control4B_TableIqMaxUwt51: Var = vf.add_var('wt.control4B.TableIqMaxUwt51_' + template_name)
    wt_control4B_TableIqMaxUwt52: Var = vf.add_var('wt.control4B.TableIqMaxUwt52_' + template_name)
    wt_control4B_TableIqMaxUwt61: Var = vf.add_var('wt.control4B.TableIqMaxUwt61_' + template_name)
    wt_control4B_TableIqMaxUwt62: Var = vf.add_var('wt.control4B.TableIqMaxUwt62_' + template_name)
    wt_control4B_TableIqMaxUwt71: Var = vf.add_var('wt.control4B.TableIqMaxUwt71_' + template_name)
    wt_control4B_TableIqMaxUwt72: Var = vf.add_var('wt.control4B.TableIqMaxUwt72_' + template_name)
    wt_control4B_TableIqMaxUwt81: Var = vf.add_var('wt.control4B.TableIqMaxUwt81_' + template_name)
    wt_control4B_TableIqMaxUwt82: Var = vf.add_var('wt.control4B.TableIqMaxUwt82_' + template_name)
    wt_control4B_TableIqMaxUwt_1_1: Var = vf.add_var('wt.control4B.TableIqMaxUwt[1,1]_' + template_name)
    wt_control4B_TableIqMaxUwt_1_2: Var = vf.add_var('wt.control4B.TableIqMaxUwt[1,2]_' + template_name)
    wt_control4B_TableIqMaxUwt_2_1: Var = vf.add_var('wt.control4B.TableIqMaxUwt[2,1]_' + template_name)
    wt_control4B_TableIqMaxUwt_2_2: Var = vf.add_var('wt.control4B.TableIqMaxUwt[2,2]_' + template_name)
    wt_control4B_TableIqMaxUwt_3_1: Var = vf.add_var('wt.control4B.TableIqMaxUwt[3,1]_' + template_name)
    wt_control4B_TableIqMaxUwt_3_2: Var = vf.add_var('wt.control4B.TableIqMaxUwt[3,2]_' + template_name)
    wt_control4B_TableIqMaxUwt_4_1: Var = vf.add_var('wt.control4B.TableIqMaxUwt[4,1]_' + template_name)
    wt_control4B_TableIqMaxUwt_4_2: Var = vf.add_var('wt.control4B.TableIqMaxUwt[4,2]_' + template_name)
    wt_control4B_TableIqMaxUwt_5_1: Var = vf.add_var('wt.control4B.TableIqMaxUwt[5,1]_' + template_name)
    wt_control4B_TableIqMaxUwt_5_2: Var = vf.add_var('wt.control4B.TableIqMaxUwt[5,2]_' + template_name)
    wt_control4B_TableIqMaxUwt_6_1: Var = vf.add_var('wt.control4B.TableIqMaxUwt[6,1]_' + template_name)
    wt_control4B_TableIqMaxUwt_6_2: Var = vf.add_var('wt.control4B.TableIqMaxUwt[6,2]_' + template_name)
    wt_control4B_TableIqMaxUwt_7_1: Var = vf.add_var('wt.control4B.TableIqMaxUwt[7,1]_' + template_name)
    wt_control4B_TableIqMaxUwt_7_2: Var = vf.add_var('wt.control4B.TableIqMaxUwt[7,2]_' + template_name)
    wt_control4B_TableIqMaxUwt_8_1: Var = vf.add_var('wt.control4B.TableIqMaxUwt[8,1]_' + template_name)
    wt_control4B_TableIqMaxUwt_8_2: Var = vf.add_var('wt.control4B.TableIqMaxUwt[8,2]_' + template_name)
    wt_control4B_TableQMaxPwtcFilt11: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt11_' + template_name)
    wt_control4B_TableQMaxPwtcFilt12: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt12_' + template_name)
    wt_control4B_TableQMaxPwtcFilt21: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt21_' + template_name)
    wt_control4B_TableQMaxPwtcFilt22: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt22_' + template_name)
    wt_control4B_TableQMaxPwtcFilt31: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt31_' + template_name)
    wt_control4B_TableQMaxPwtcFilt32: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt32_' + template_name)
    wt_control4B_TableQMaxPwtcFilt41: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt41_' + template_name)
    wt_control4B_TableQMaxPwtcFilt42: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt42_' + template_name)
    wt_control4B_TableQMaxPwtcFilt_1_1: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt[1,1]_' + template_name)
    wt_control4B_TableQMaxPwtcFilt_1_2: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt[1,2]_' + template_name)
    wt_control4B_TableQMaxPwtcFilt_2_1: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt[2,1]_' + template_name)
    wt_control4B_TableQMaxPwtcFilt_2_2: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt[2,2]_' + template_name)
    wt_control4B_TableQMaxPwtcFilt_3_1: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt[3,1]_' + template_name)
    wt_control4B_TableQMaxPwtcFilt_3_2: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt[3,2]_' + template_name)
    wt_control4B_TableQMaxPwtcFilt_4_1: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt[4,1]_' + template_name)
    wt_control4B_TableQMaxPwtcFilt_4_2: Var = vf.add_var('wt.control4B.TableQMaxPwtcFilt[4,2]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt11: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt11_' + template_name)
    wt_control4B_TableQMaxUwtcFilt12: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt12_' + template_name)
    wt_control4B_TableQMaxUwtcFilt21: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt21_' + template_name)
    wt_control4B_TableQMaxUwtcFilt22: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt22_' + template_name)
    wt_control4B_TableQMaxUwtcFilt31: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt31_' + template_name)
    wt_control4B_TableQMaxUwtcFilt32: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt32_' + template_name)
    wt_control4B_TableQMaxUwtcFilt41: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt41_' + template_name)
    wt_control4B_TableQMaxUwtcFilt42: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt42_' + template_name)
    wt_control4B_TableQMaxUwtcFilt51: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt51_' + template_name)
    wt_control4B_TableQMaxUwtcFilt52: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt52_' + template_name)
    wt_control4B_TableQMaxUwtcFilt61: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt61_' + template_name)
    wt_control4B_TableQMaxUwtcFilt62: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt62_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_1_1: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[1,1]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_1_2: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[1,2]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_2_1: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[2,1]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_2_2: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[2,2]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_3_1: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[3,1]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_3_2: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[3,2]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_4_1: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[4,1]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_4_2: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[4,2]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_5_1: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[5,1]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_5_2: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[5,2]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_6_1: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[6,1]_' + template_name)
    wt_control4B_TableQMaxUwtcFilt_6_2: Var = vf.add_var('wt.control4B.TableQMaxUwtcFilt[6,2]_' + template_name)
    wt_control4B_TableQMinPwtcFilt11: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt11_' + template_name)
    wt_control4B_TableQMinPwtcFilt12: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt12_' + template_name)
    wt_control4B_TableQMinPwtcFilt21: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt21_' + template_name)
    wt_control4B_TableQMinPwtcFilt22: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt22_' + template_name)
    wt_control4B_TableQMinPwtcFilt31: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt31_' + template_name)
    wt_control4B_TableQMinPwtcFilt32: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt32_' + template_name)
    wt_control4B_TableQMinPwtcFilt41: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt41_' + template_name)
    wt_control4B_TableQMinPwtcFilt42: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt42_' + template_name)
    wt_control4B_TableQMinPwtcFilt_1_1: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt[1,1]_' + template_name)
    wt_control4B_TableQMinPwtcFilt_1_2: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt[1,2]_' + template_name)
    wt_control4B_TableQMinPwtcFilt_2_1: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt[2,1]_' + template_name)
    wt_control4B_TableQMinPwtcFilt_2_2: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt[2,2]_' + template_name)
    wt_control4B_TableQMinPwtcFilt_3_1: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt[3,1]_' + template_name)
    wt_control4B_TableQMinPwtcFilt_3_2: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt[3,2]_' + template_name)
    wt_control4B_TableQMinPwtcFilt_4_1: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt[4,1]_' + template_name)
    wt_control4B_TableQMinPwtcFilt_4_2: Var = vf.add_var('wt.control4B.TableQMinPwtcFilt[4,2]_' + template_name)
    wt_control4B_TableQMinUwtcFilt11: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt11_' + template_name)
    wt_control4B_TableQMinUwtcFilt12: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt12_' + template_name)
    wt_control4B_TableQMinUwtcFilt21: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt21_' + template_name)
    wt_control4B_TableQMinUwtcFilt22: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt22_' + template_name)
    wt_control4B_TableQMinUwtcFilt31: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt31_' + template_name)
    wt_control4B_TableQMinUwtcFilt32: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt32_' + template_name)
    wt_control4B_TableQMinUwtcFilt41: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt41_' + template_name)
    wt_control4B_TableQMinUwtcFilt42: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt42_' + template_name)
    wt_control4B_TableQMinUwtcFilt_1_1: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt[1,1]_' + template_name)
    wt_control4B_TableQMinUwtcFilt_1_2: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt[1,2]_' + template_name)
    wt_control4B_TableQMinUwtcFilt_2_1: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt[2,1]_' + template_name)
    wt_control4B_TableQMinUwtcFilt_2_2: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt[2,2]_' + template_name)
    wt_control4B_TableQMinUwtcFilt_3_1: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt[3,1]_' + template_name)
    wt_control4B_TableQMinUwtcFilt_3_2: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt[3,2]_' + template_name)
    wt_control4B_TableQMinUwtcFilt_4_1: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt[4,1]_' + template_name)
    wt_control4B_TableQMinUwtcFilt_4_2: Var = vf.add_var('wt.control4B.TableQMinUwtcFilt[4,2]_' + template_name)
    wt_control4B_U0Pu: Var = vf.add_var('wt.control4B.U0Pu_' + template_name)
    wt_control4B_UMaxPu: Var = vf.add_var('wt.control4B.UMaxPu_' + template_name)
    wt_control4B_UMinPu: Var = vf.add_var('wt.control4B.UMinPu_' + template_name)
    wt_control4B_UPhase0: Var = vf.add_var('wt.control4B.UPhase0_' + template_name)
    wt_control4B_URef0Pu: Var = vf.add_var('wt.control4B.URef0Pu_' + template_name)
    wt_control4B_UpDipPu: Var = vf.add_var('wt.control4B.UpDipPu_' + template_name)
    wt_control4B_UpquMaxPu: Var = vf.add_var('wt.control4B.UpquMaxPu_' + template_name)
    wt_control4B_UqDipPu: Var = vf.add_var('wt.control4B.UqDipPu_' + template_name)
    wt_control4B_UqRisePu: Var = vf.add_var('wt.control4B.UqRisePu_' + template_name)
    wt_control4B_XDropPu: Var = vf.add_var('wt.control4B.XDropPu_' + template_name)
    wt_control4B_XWT0Pu: Var = vf.add_var('wt.control4B.XWT0Pu_' + template_name)
    wt_control4B_const_k: Var = vf.add_var('wt.control4B.const.k_' + template_name)
    wt_control4B_currentLimiter_IMaxDipPu: Var = vf.add_var('wt.control4B.currentLimiter.IMaxDipPu_' + template_name)
    wt_control4B_currentLimiter_IMaxPu: Var = vf.add_var('wt.control4B.currentLimiter.IMaxPu_' + template_name)
    wt_control4B_currentLimiter_IpMax0Pu: Var = vf.add_var('wt.control4B.currentLimiter.IpMax0Pu_' + template_name)
    wt_control4B_currentLimiter_IqMax0Pu: Var = vf.add_var('wt.control4B.currentLimiter.IqMax0Pu_' + template_name)
    wt_control4B_currentLimiter_IqMin0Pu: Var = vf.add_var('wt.control4B.currentLimiter.IqMin0Pu_' + template_name)
    wt_control4B_currentLimiter_Kpqu: Var = vf.add_var('wt.control4B.currentLimiter.Kpqu_' + template_name)
    wt_control4B_currentLimiter_MdfsLim: Var = vf.add_var('wt.control4B.currentLimiter.MdfsLim_' + template_name)
    wt_control4B_currentLimiter_Mqpri: Var = vf.add_var('wt.control4B.currentLimiter.Mqpri_' + template_name)
    wt_control4B_currentLimiter_P0Pu: Var = vf.add_var('wt.control4B.currentLimiter.P0Pu_' + template_name)
    wt_control4B_currentLimiter_Q0Pu: Var = vf.add_var('wt.control4B.currentLimiter.Q0Pu_' + template_name)
    wt_control4B_currentLimiter_SNom: Var = vf.add_var('wt.control4B.currentLimiter.SNom_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt11: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt11_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt12: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt12_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt21: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt21_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt22: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt22_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt31: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt31_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt32: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt32_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt41: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt41_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt42: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt42_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt51: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt51_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt52: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt52_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt61: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt61_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt62: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt62_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt71: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt71_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt72: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt72_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_1_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[1,1]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_1_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[1,2]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_2_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[2,1]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_2_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[2,2]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_3_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[3,1]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_3_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[3,2]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_4_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[4,1]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_4_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[4,2]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_5_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[5,1]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_5_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[5,2]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_6_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[6,1]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_6_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[6,2]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_7_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[7,1]_' + template_name)
    wt_control4B_currentLimiter_TableIpMaxUwt_7_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIpMaxUwt[7,2]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt11: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt11_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt12: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt12_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt21: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt21_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt22: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt22_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt31: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt31_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt32: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt32_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt41: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt41_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt42: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt42_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt51: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt51_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt52: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt52_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt61: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt61_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt62: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt62_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt71: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt71_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt72: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt72_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt81: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt81_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt82: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt82_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_1_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[1,1]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_1_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[1,2]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_2_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[2,1]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_2_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[2,2]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_3_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[3,1]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_3_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[3,2]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_4_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[4,1]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_4_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[4,2]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_5_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[5,1]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_5_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[5,2]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_6_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[6,1]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_6_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[6,2]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_7_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[7,1]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_7_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[7,2]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_8_1: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[8,1]_' + template_name)
    wt_control4B_currentLimiter_TableIqMaxUwt_8_2: Var = vf.add_var('wt.control4B.currentLimiter.TableIqMaxUwt[8,2]_' + template_name)
    wt_control4B_currentLimiter_U0Pu: Var = vf.add_var('wt.control4B.currentLimiter.U0Pu_' + template_name)
    wt_control4B_currentLimiter_UPhase0: Var = vf.add_var('wt.control4B.currentLimiter.UPhase0_' + template_name)
    wt_control4B_currentLimiter_UpquMaxPu: Var = vf.add_var('wt.control4B.currentLimiter.UpquMaxPu_' + template_name)
    wt_control4B_currentLimiter_abs_generateEvent: Var = vf.add_var('wt.control4B.currentLimiter.abs.generateEvent_' + template_name)
    wt_control4B_currentLimiter_add1_k1: Var = vf.add_var('wt.control4B.currentLimiter.add1.k1_' + template_name)
    wt_control4B_currentLimiter_add1_k2: Var = vf.add_var('wt.control4B.currentLimiter.add1.k2_' + template_name)
    wt_control4B_currentLimiter_booleanConstant_k: Var = vf.add_var('wt.control4B.currentLimiter.booleanConstant.k_' + template_name)
    wt_control4B_currentLimiter_booleanConstant1_k: Var = vf.add_var('wt.control4B.currentLimiter.booleanConstant1.k_' + template_name)
    wt_control4B_currentLimiter_booleanToInteger_integerFalse: Var = vf.add_var('wt.control4B.currentLimiter.booleanToInteger.integerFalse_' + template_name)
    wt_control4B_currentLimiter_booleanToInteger_integerTrue: Var = vf.add_var('wt.control4B.currentLimiter.booleanToInteger.integerTrue_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_columns_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.columns[1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_extrapolation: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.extrapolation_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_fileName: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.fileName_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_nout: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.nout_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_smoothness: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.smoothness_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_tableID: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.tableID_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_tableName: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.tableName_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_tableOnFile: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.tableOnFile_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_1_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[1,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_1_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[1,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_2_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[2,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_2_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[2,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_3_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[3,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_3_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[3,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_4_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[4,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_4_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[4,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_5_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[5,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_5_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[5,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_6_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[6,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_6_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[6,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_7_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[7,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_7_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[7,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_8_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[8,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_table_8_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.table[8,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_u_max: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.u_max_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_u_min: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.u_min_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_verboseExtrapolation: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.verboseExtrapolation_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_verboseRead: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.verboseRead_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_columns_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.columns[1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_extrapolation: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.extrapolation_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_fileName: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.fileName_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_nout: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.nout_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_smoothness: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.smoothness_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_tableID: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.tableID_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_tableName: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.tableName_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_tableOnFile: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.tableOnFile_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_1_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[1,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_1_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[1,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_2_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[2,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_2_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[2,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_3_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[3,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_3_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[3,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_4_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[4,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_4_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[4,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_5_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[5,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_5_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[5,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_6_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[6,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_6_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[6,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_7_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[7,1]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_table_7_2: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.table[7,2]_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_u_max: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.u_max_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_u_min: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.u_min_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_verboseExtrapolation: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.verboseExtrapolation_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds1_verboseRead: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds1.verboseRead_' + template_name)
    wt_control4B_currentLimiter_const_k: Var = vf.add_var('wt.control4B.currentLimiter.const.k_' + template_name)
    wt_control4B_currentLimiter_const1_k: Var = vf.add_var('wt.control4B.currentLimiter.const1.k_' + template_name)
    wt_control4B_currentLimiter_const2_k: Var = vf.add_var('wt.control4B.currentLimiter.const2.k_' + template_name)
    wt_control4B_currentLimiter_const3_k: Var = vf.add_var('wt.control4B.currentLimiter.const3.k_' + template_name)
    wt_control4B_currentLimiter_const4_k: Var = vf.add_var('wt.control4B.currentLimiter.const4.k_' + template_name)
    wt_control4B_currentLimiter_const5_k: Var = vf.add_var('wt.control4B.currentLimiter.const5.k_' + template_name)
    wt_control4B_currentLimiter_gain_k: Var = vf.add_var('wt.control4B.currentLimiter.gain.k_' + template_name)
    wt_control4B_currentLimiter_gain1_k: Var = vf.add_var('wt.control4B.currentLimiter.gain1.k_' + template_name)
    wt_control4B_currentLimiter_product1_nu: Var = vf.add_var('wt.control4B.currentLimiter.product1.nu_' + template_name)
    wt_control4B_currentLimiter_switch1_nu: Var = vf.add_var('wt.control4B.currentLimiter.switch1.nu_' + template_name)
    wt_control4B_currentLimiter_switch2_nu: Var = vf.add_var('wt.control4B.currentLimiter.switch2.nu_' + template_name)
    wt_control4B_currentLimiter_switch4_nu: Var = vf.add_var('wt.control4B.currentLimiter.switch4.nu_' + template_name)
    wt_control4B_pControl4B_DPMaxP4BPu: Var = vf.add_var('wt.control4B.pControl4B.DPMaxP4BPu_' + template_name)
    wt_control4B_pControl4B_DPRefMax4BPu: Var = vf.add_var('wt.control4B.pControl4B.DPRefMax4BPu_' + template_name)
    wt_control4B_pControl4B_DPRefMin4BPu: Var = vf.add_var('wt.control4B.pControl4B.DPRefMin4BPu_' + template_name)
    wt_control4B_pControl4B_IpMax0Pu: Var = vf.add_var('wt.control4B.pControl4B.IpMax0Pu_' + template_name)
    wt_control4B_pControl4B_Kpaw: Var = vf.add_var('wt.control4B.pControl4B.Kpaw_' + template_name)
    wt_control4B_pControl4B_MpUScale: Var = vf.add_var('wt.control4B.pControl4B.MpUScale_' + template_name)
    wt_control4B_pControl4B_P0Pu: Var = vf.add_var('wt.control4B.pControl4B.P0Pu_' + template_name)
    wt_control4B_pControl4B_SNom: Var = vf.add_var('wt.control4B.pControl4B.SNom_' + template_name)
    wt_control4B_pControl4B_U0Pu: Var = vf.add_var('wt.control4B.pControl4B.U0Pu_' + template_name)
    wt_control4B_pControl4B_UpDipPu: Var = vf.add_var('wt.control4B.pControl4B.UpDipPu_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_DyMax: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.DyMax_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_DyMin: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.DyMin_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_Kaw: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.Kaw_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_UseLimits: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.UseLimits_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_Y0: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.Y0_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_YMax: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.YMax_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_YMin: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.YMin_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_k1: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.add.k1_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_k2: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.add.k2_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_k: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.gain.k_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_initType: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.integrator.initType_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_k: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.integrator.k_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_use_reset: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.integrator.use_reset_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_use_set: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.integrator.use_set_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y_start: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.integrator.y_start_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_homotopyType: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.limiter.homotopyType_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.limiter.limitsAtInit_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_strict: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.limiter.strict_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMax: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.limiter.uMax_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMin: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.limiter.uMin_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_tI: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.tI_' + template_name)
    wt_control4B_pControl4B_booleanConstant_k: Var = vf.add_var('wt.control4B.pControl4B.booleanConstant.k_' + template_name)
    wt_control4B_pControl4B_const_k: Var = vf.add_var('wt.control4B.pControl4B.const.k_' + template_name)
    wt_control4B_pControl4B_const1_k: Var = vf.add_var('wt.control4B.pControl4B.const1.k_' + template_name)
    wt_control4B_pControl4B_const2_k: Var = vf.add_var('wt.control4B.pControl4B.const2.k_' + template_name)
    wt_control4B_pControl4B_firstOrder_T: Var = vf.add_var('wt.control4B.pControl4B.firstOrder.T_' + template_name)
    wt_control4B_pControl4B_firstOrder_initType: Var = vf.add_var('wt.control4B.pControl4B.firstOrder.initType_' + template_name)
    wt_control4B_pControl4B_firstOrder_k: Var = vf.add_var('wt.control4B.pControl4B.firstOrder.k_' + template_name)
    wt_control4B_pControl4B_firstOrder_y_start: Var = vf.add_var('wt.control4B.pControl4B.firstOrder.y_start_' + template_name)
    wt_control4B_pControl4B_rampLimiter_DuMax: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.DuMax_' + template_name)
    wt_control4B_pControl4B_rampLimiter_DuMin: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.DuMin_' + template_name)
    wt_control4B_pControl4B_rampLimiter_Y0: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.Y0_' + template_name)
    wt_control4B_pControl4B_rampLimiter_gain_k: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.gain.k_' + template_name)
    wt_control4B_pControl4B_rampLimiter_integrator_initType: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.integrator.initType_' + template_name)
    wt_control4B_pControl4B_rampLimiter_integrator_k: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.integrator.k_' + template_name)
    wt_control4B_pControl4B_rampLimiter_integrator_use_reset: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.integrator.use_reset_' + template_name)
    wt_control4B_pControl4B_rampLimiter_integrator_use_set: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.integrator.use_set_' + template_name)
    wt_control4B_pControl4B_rampLimiter_integrator_y_start: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.integrator.y_start_' + template_name)
    wt_control4B_pControl4B_rampLimiter_limiter_homotopyType: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.limiter.homotopyType_' + template_name)
    wt_control4B_pControl4B_rampLimiter_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.limiter.limitsAtInit_' + template_name)
    wt_control4B_pControl4B_rampLimiter_limiter_strict: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.limiter.strict_' + template_name)
    wt_control4B_pControl4B_rampLimiter_limiter_uMax: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.limiter.uMax_' + template_name)
    wt_control4B_pControl4B_rampLimiter_limiter_uMin: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.limiter.uMin_' + template_name)
    wt_control4B_pControl4B_rampLimiter_tS: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.tS_' + template_name)
    wt_control4B_pControl4B_tPAero: Var = vf.add_var('wt.control4B.pControl4B.tPAero_' + template_name)
    wt_control4B_pControl4B_tPOrdP4B: Var = vf.add_var('wt.control4B.pControl4B.tPOrdP4B_' + template_name)
    wt_control4B_pControl4B_tS: Var = vf.add_var('wt.control4B.pControl4B.tS_' + template_name)
    wt_control4B_qControl_DUdb1Pu: Var = vf.add_var('wt.control4B.qControl.DUdb1Pu_' + template_name)
    wt_control4B_qControl_DUdb2Pu: Var = vf.add_var('wt.control4B.qControl.DUdb2Pu_' + template_name)
    wt_control4B_qControl_IqH1Pu: Var = vf.add_var('wt.control4B.qControl.IqH1Pu_' + template_name)
    wt_control4B_qControl_IqMaxPu: Var = vf.add_var('wt.control4B.qControl.IqMaxPu_' + template_name)
    wt_control4B_qControl_IqMinPu: Var = vf.add_var('wt.control4B.qControl.IqMinPu_' + template_name)
    wt_control4B_qControl_IqPostPu: Var = vf.add_var('wt.control4B.qControl.IqPostPu_' + template_name)
    wt_control4B_qControl_Kiq: Var = vf.add_var('wt.control4B.qControl.Kiq_' + template_name)
    wt_control4B_qControl_Kiu: Var = vf.add_var('wt.control4B.qControl.Kiu_' + template_name)
    wt_control4B_qControl_Kpq: Var = vf.add_var('wt.control4B.qControl.Kpq_' + template_name)
    wt_control4B_qControl_Kpu: Var = vf.add_var('wt.control4B.qControl.Kpu_' + template_name)
    wt_control4B_qControl_Kpufrt: Var = vf.add_var('wt.control4B.qControl.Kpufrt_' + template_name)
    wt_control4B_qControl_Kqv: Var = vf.add_var('wt.control4B.qControl.Kqv_' + template_name)
    wt_control4B_qControl_MqG: Var = vf.add_var('wt.control4B.qControl.MqG_' + template_name)
    wt_control4B_qControl_Mqfrt: Var = vf.add_var('wt.control4B.qControl.Mqfrt_' + template_name)
    wt_control4B_qControl_P0Pu: Var = vf.add_var('wt.control4B.qControl.P0Pu_' + template_name)
    wt_control4B_qControl_Q0Pu: Var = vf.add_var('wt.control4B.qControl.Q0Pu_' + template_name)
    wt_control4B_qControl_QMax0Pu: Var = vf.add_var('wt.control4B.qControl.QMax0Pu_' + template_name)
    wt_control4B_qControl_QMin0Pu: Var = vf.add_var('wt.control4B.qControl.QMin0Pu_' + template_name)
    wt_control4B_qControl_RDropPu: Var = vf.add_var('wt.control4B.qControl.RDropPu_' + template_name)
    wt_control4B_qControl_SNom: Var = vf.add_var('wt.control4B.qControl.SNom_' + template_name)
    wt_control4B_qControl_U0Pu: Var = vf.add_var('wt.control4B.qControl.U0Pu_' + template_name)
    wt_control4B_qControl_UMaxPu: Var = vf.add_var('wt.control4B.qControl.UMaxPu_' + template_name)
    wt_control4B_qControl_UMinPu: Var = vf.add_var('wt.control4B.qControl.UMinPu_' + template_name)
    wt_control4B_qControl_URef0Pu: Var = vf.add_var('wt.control4B.qControl.URef0Pu_' + template_name)
    wt_control4B_qControl_UqDipPu: Var = vf.add_var('wt.control4B.qControl.UqDipPu_' + template_name)
    wt_control4B_qControl_UqRisePu: Var = vf.add_var('wt.control4B.qControl.UqRisePu_' + template_name)
    wt_control4B_qControl_XDropPu: Var = vf.add_var('wt.control4B.qControl.XDropPu_' + template_name)
    wt_control4B_qControl_XWT0Pu: Var = vf.add_var('wt.control4B.qControl.XWT0Pu_' + template_name)
    wt_control4B_qControl_abs_generateEvent: Var = vf.add_var('wt.control4B.qControl.abs.generateEvent_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_DyMax: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.DyMax_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_DyMin: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.DyMin_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_U0: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.U0_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_Y0: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.Y0_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_YMax: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.YMax_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_YMin: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.YMin_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_fixedDelay_delayTime: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.fixedDelay.delayTime_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_homotopyType: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.limiter.homotopyType_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.limiter.limitsAtInit_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_strict: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.limiter.strict_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMax: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.limiter.uMax_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMin: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.limiter.uMin_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_DuMax: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.DuMax_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_DuMin: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.DuMin_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_Y0: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.Y0_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_k: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.gain.k_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_initType: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.initType_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_k: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.k_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_use_reset: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.use_reset_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_use_set: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.use_set_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y_start: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.y_start_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_homotopyType: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.homotopyType_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.limitsAtInit_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_strict: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.strict_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.uMax_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.uMin_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_tS: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.tS_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_tS: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.tS_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_DyMax: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.DyMax_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_DyMin: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.DyMin_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_UseLimits: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.UseLimits_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_Y0: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.Y0_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_YMax: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.YMax_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_YMin: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.YMin_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_const_k: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.const.k_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_k: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.gain.k_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_initType: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.integrator.initType_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_k: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.integrator.k_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_use_reset: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.integrator.use_reset_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_use_set: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.integrator.use_set_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y_start: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.integrator.y_start_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_homotopyType: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.limiter.homotopyType_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.limiter.limitsAtInit_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_strict: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.limiter.strict_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMax: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.limiter.uMax_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMin: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.limiter.uMin_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_tI: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.tI_' + template_name)
    wt_control4B_qControl_add_k1: Var = vf.add_var('wt.control4B.qControl.add.k1_' + template_name)
    wt_control4B_qControl_add_k2: Var = vf.add_var('wt.control4B.qControl.add.k2_' + template_name)
    wt_control4B_qControl_add1_k1: Var = vf.add_var('wt.control4B.qControl.add1.k1_' + template_name)
    wt_control4B_qControl_add1_k2: Var = vf.add_var('wt.control4B.qControl.add1.k2_' + template_name)
    wt_control4B_qControl_add2_k1: Var = vf.add_var('wt.control4B.qControl.add2.k1_' + template_name)
    wt_control4B_qControl_add2_k2: Var = vf.add_var('wt.control4B.qControl.add2.k2_' + template_name)
    wt_control4B_qControl_add3_k1: Var = vf.add_var('wt.control4B.qControl.add3.k1_' + template_name)
    wt_control4B_qControl_add3_k2: Var = vf.add_var('wt.control4B.qControl.add3.k2_' + template_name)
    wt_control4B_qControl_add4_k1: Var = vf.add_var('wt.control4B.qControl.add4.k1_' + template_name)
    wt_control4B_qControl_add4_k2: Var = vf.add_var('wt.control4B.qControl.add4.k2_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_DyMax: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.DyMax_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_DyMin: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.DyMin_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_Y0: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.Y0_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_YMax: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.YMax_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_YMin: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.YMin_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_const_k: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.const.k_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_gain_k: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.gain.k_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_integrator_initType: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.integrator.initType_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_integrator_k: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.integrator.k_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_integrator_use_reset: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.integrator.use_reset_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_integrator_use_set: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.integrator.use_set_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_integrator_y_start: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.integrator.y_start_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter_homotopyType: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter.homotopyType_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter.limitsAtInit_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter_strict: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter.strict_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter_uMax: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter.uMax_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter_uMin: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter.uMin_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter1_homotopyType: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter1.homotopyType_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter1_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter1.limitsAtInit_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter1_strict: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter1.strict_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter1_uMax: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter1.uMax_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter1_uMin: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter1.uMin_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_tI: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.tI_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_DyMax: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.DyMax_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_DyMin: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.DyMin_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_Y0: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.Y0_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_YMax: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.YMax_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_YMin: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.YMin_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_const_k: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.const.k_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_gain_k: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.gain.k_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_integrator_initType: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.integrator.initType_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_integrator_k: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.integrator.k_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_integrator_use_reset: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.integrator.use_reset_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_integrator_use_set: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.integrator.use_set_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_integrator_y_start: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.integrator.y_start_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter_homotopyType: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter.homotopyType_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter.limitsAtInit_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter_strict: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter.strict_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter_uMax: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter.uMax_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter_uMin: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter.uMin_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter1_homotopyType: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter1.homotopyType_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter1_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter1.limitsAtInit_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter1_strict: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter1.strict_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMax: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter1.uMax_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMin: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter1.uMin_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_tI: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.tI_' + template_name)
    wt_control4B_qControl_booleanToInteger_integerFalse: Var = vf.add_var('wt.control4B.qControl.booleanToInteger.integerFalse_' + template_name)
    wt_control4B_qControl_booleanToInteger_integerTrue: Var = vf.add_var('wt.control4B.qControl.booleanToInteger.integerTrue_' + template_name)
    wt_control4B_qControl_const_k: Var = vf.add_var('wt.control4B.qControl.const.k_' + template_name)
    wt_control4B_qControl_const1_k: Var = vf.add_var('wt.control4B.qControl.const1.k_' + template_name)
    wt_control4B_qControl_const5_k: Var = vf.add_var('wt.control4B.qControl.const5.k_' + template_name)
    wt_control4B_qControl_const8_k: Var = vf.add_var('wt.control4B.qControl.const8.k_' + template_name)
    wt_control4B_qControl_deadZone_deadZoneAtInit: Var = vf.add_var('wt.control4B.qControl.deadZone.deadZoneAtInit_' + template_name)
    wt_control4B_qControl_deadZone_uMax: Var = vf.add_var('wt.control4B.qControl.deadZone.uMax_' + template_name)
    wt_control4B_qControl_deadZone_uMin: Var = vf.add_var('wt.control4B.qControl.deadZone.uMin_' + template_name)
    wt_control4B_qControl_delayFlag_FI0: Var = vf.add_var('wt.control4B.qControl.delayFlag.FI0_' + template_name)
    wt_control4B_qControl_delayFlag_FO0: Var = vf.add_var('wt.control4B.qControl.delayFlag.FO0_' + template_name)
    wt_control4B_qControl_delayFlag_booleanToInteger_integerFalse: Var = vf.add_var('wt.control4B.qControl.delayFlag.booleanToInteger.integerFalse_' + template_name)
    wt_control4B_qControl_delayFlag_booleanToInteger_integerTrue: Var = vf.add_var('wt.control4B.qControl.delayFlag.booleanToInteger.integerTrue_' + template_name)
    wt_control4B_qControl_delayFlag_const7_k: Var = vf.add_var('wt.control4B.qControl.delayFlag.const7.k_' + template_name)
    wt_control4B_qControl_delayFlag_fixedDelay_delayTime: Var = vf.add_var('wt.control4B.qControl.delayFlag.fixedDelay.delayTime_' + template_name)
    wt_control4B_qControl_delayFlag_integerConstant_k: Var = vf.add_var('wt.control4B.qControl.delayFlag.integerConstant.k_' + template_name)
    wt_control4B_qControl_delayFlag_tD: Var = vf.add_var('wt.control4B.qControl.delayFlag.tD_' + template_name)
    wt_control4B_qControl_delayFlag_tS: Var = vf.add_var('wt.control4B.qControl.delayFlag.tS_' + template_name)
    wt_control4B_qControl_derivative_T: Var = vf.add_var('wt.control4B.qControl.derivative.T_' + template_name)
    wt_control4B_qControl_derivative_initType: Var = vf.add_var('wt.control4B.qControl.derivative.initType_' + template_name)
    wt_control4B_qControl_derivative_k: Var = vf.add_var('wt.control4B.qControl.derivative.k_' + template_name)
    wt_control4B_qControl_derivative_x_start: Var = vf.add_var('wt.control4B.qControl.derivative.x_start_' + template_name)
    wt_control4B_qControl_derivative_y_start: Var = vf.add_var('wt.control4B.qControl.derivative.y_start_' + template_name)
    wt_control4B_qControl_derivative_zeroGain: Var = vf.add_var('wt.control4B.qControl.derivative.zeroGain_' + template_name)
    wt_control4B_qControl_gain_k: Var = vf.add_var('wt.control4B.qControl.gain.k_' + template_name)
    wt_control4B_qControl_gain1_k: Var = vf.add_var('wt.control4B.qControl.gain1.k_' + template_name)
    wt_control4B_qControl_gain2_k: Var = vf.add_var('wt.control4B.qControl.gain2.k_' + template_name)
    wt_control4B_qControl_gain3_k: Var = vf.add_var('wt.control4B.qControl.gain3.k_' + template_name)
    wt_control4B_qControl_gain4_k: Var = vf.add_var('wt.control4B.qControl.gain4.k_' + template_name)
    wt_control4B_qControl_gain5_k: Var = vf.add_var('wt.control4B.qControl.gain5.k_' + template_name)
    wt_control4B_qControl_gain6_k: Var = vf.add_var('wt.control4B.qControl.gain6.k_' + template_name)
    wt_control4B_qControl_gain7_k: Var = vf.add_var('wt.control4B.qControl.gain7.k_' + template_name)
    wt_control4B_qControl_greaterEqualThreshold_threshold: Var = vf.add_var('wt.control4B.qControl.greaterEqualThreshold.threshold_' + template_name)
    wt_control4B_qControl_greaterThreshold_threshold: Var = vf.add_var('wt.control4B.qControl.greaterThreshold.threshold_' + template_name)
    wt_control4B_qControl_integerConstant_k: Var = vf.add_var('wt.control4B.qControl.integerConstant.k_' + template_name)
    wt_control4B_qControl_integerConstant1_k: Var = vf.add_var('wt.control4B.qControl.integerConstant1.k_' + template_name)
    wt_control4B_qControl_integerConstant2_k: Var = vf.add_var('wt.control4B.qControl.integerConstant2.k_' + template_name)
    wt_control4B_qControl_lessThreshold_threshold: Var = vf.add_var('wt.control4B.qControl.lessThreshold.threshold_' + template_name)
    wt_control4B_qControl_limiter_homotopyType: Var = vf.add_var('wt.control4B.qControl.limiter.homotopyType_' + template_name)
    wt_control4B_qControl_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.limiter.limitsAtInit_' + template_name)
    wt_control4B_qControl_limiter_strict: Var = vf.add_var('wt.control4B.qControl.limiter.strict_' + template_name)
    wt_control4B_qControl_limiter_uMax: Var = vf.add_var('wt.control4B.qControl.limiter.uMax_' + template_name)
    wt_control4B_qControl_limiter_uMin: Var = vf.add_var('wt.control4B.qControl.limiter.uMin_' + template_name)
    wt_control4B_qControl_limiter2_homotopyType: Var = vf.add_var('wt.control4B.qControl.limiter2.homotopyType_' + template_name)
    wt_control4B_qControl_limiter2_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.limiter2.limitsAtInit_' + template_name)
    wt_control4B_qControl_limiter2_strict: Var = vf.add_var('wt.control4B.qControl.limiter2.strict_' + template_name)
    wt_control4B_qControl_limiter2_uMax: Var = vf.add_var('wt.control4B.qControl.limiter2.uMax_' + template_name)
    wt_control4B_qControl_limiter2_uMin: Var = vf.add_var('wt.control4B.qControl.limiter2.uMin_' + template_name)
    wt_control4B_qControl_limiter3_homotopyType: Var = vf.add_var('wt.control4B.qControl.limiter3.homotopyType_' + template_name)
    wt_control4B_qControl_limiter3_limitsAtInit: Var = vf.add_var('wt.control4B.qControl.limiter3.limitsAtInit_' + template_name)
    wt_control4B_qControl_limiter3_strict: Var = vf.add_var('wt.control4B.qControl.limiter3.strict_' + template_name)
    wt_control4B_qControl_limiter3_uMax: Var = vf.add_var('wt.control4B.qControl.limiter3.uMax_' + template_name)
    wt_control4B_qControl_limiter3_uMin: Var = vf.add_var('wt.control4B.qControl.limiter3.uMin_' + template_name)
    wt_control4B_qControl_switch_nu: Var = vf.add_var('wt.control4B.qControl.switch.nu_' + template_name)
    wt_control4B_qControl_switch2_nu: Var = vf.add_var('wt.control4B.qControl.switch2.nu_' + template_name)
    wt_control4B_qControl_switch4_nu: Var = vf.add_var('wt.control4B.qControl.switch4.nu_' + template_name)
    wt_control4B_qControl_switch6_nu: Var = vf.add_var('wt.control4B.qControl.switch6.nu_' + template_name)
    wt_control4B_qControl_switch7_nu: Var = vf.add_var('wt.control4B.qControl.switch7.nu_' + template_name)
    wt_control4B_qControl_switch8_nu: Var = vf.add_var('wt.control4B.qControl.switch8.nu_' + template_name)
    wt_control4B_qControl_tPost: Var = vf.add_var('wt.control4B.qControl.tPost_' + template_name)
    wt_control4B_qControl_tQord: Var = vf.add_var('wt.control4B.qControl.tQord_' + template_name)
    wt_control4B_qControl_tS: Var = vf.add_var('wt.control4B.qControl.tS_' + template_name)
    wt_control4B_qControl_tUss: Var = vf.add_var('wt.control4B.qControl.tUss_' + template_name)
    wt_control4B_qControl_vDrop_P0Pu: Var = vf.add_var('wt.control4B.qControl.vDrop.P0Pu_' + template_name)
    wt_control4B_qControl_vDrop_Q0Pu: Var = vf.add_var('wt.control4B.qControl.vDrop.Q0Pu_' + template_name)
    wt_control4B_qControl_vDrop_RDropPu: Var = vf.add_var('wt.control4B.qControl.vDrop.RDropPu_' + template_name)
    wt_control4B_qControl_vDrop_U0Pu: Var = vf.add_var('wt.control4B.qControl.vDrop.U0Pu_' + template_name)
    wt_control4B_qControl_vDrop_UDrop0Pu: Var = vf.add_var('wt.control4B.qControl.vDrop.UDrop0Pu_' + template_name)
    wt_control4B_qControl_vDrop_XDropPu: Var = vf.add_var('wt.control4B.qControl.vDrop.XDropPu_' + template_name)
    wt_control4B_qLimiter_P0Pu: Var = vf.add_var('wt.control4B.qLimiter.P0Pu_' + template_name)
    wt_control4B_qLimiter_QMax0Pu: Var = vf.add_var('wt.control4B.qLimiter.QMax0Pu_' + template_name)
    wt_control4B_qLimiter_QMaxPu: Var = vf.add_var('wt.control4B.qLimiter.QMaxPu_' + template_name)
    wt_control4B_qLimiter_QMin0Pu: Var = vf.add_var('wt.control4B.qLimiter.QMin0Pu_' + template_name)
    wt_control4B_qLimiter_QMinPu: Var = vf.add_var('wt.control4B.qLimiter.QMinPu_' + template_name)
    wt_control4B_qLimiter_QlConst: Var = vf.add_var('wt.control4B.qLimiter.QlConst_' + template_name)
    wt_control4B_qLimiter_SNom: Var = vf.add_var('wt.control4B.qLimiter.SNom_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt11: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt11_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt12: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt12_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt21: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt21_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt22: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt22_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt31: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt31_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt32: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt32_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt41: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt41_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt42: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt42_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt_1_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt[1,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt_1_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt[1,2]_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt_2_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt[2,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt_2_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt[2,2]_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt_3_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt[3,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt_3_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt[3,2]_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt_4_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt[4,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxPwtcFilt_4_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxPwtcFilt[4,2]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt11: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt11_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt12: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt12_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt21: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt21_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt22: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt22_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt31: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt31_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt32: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt32_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt41: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt41_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt42: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt42_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt51: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt51_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt52: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt52_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt61: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt61_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt62: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt62_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_1_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[1,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_1_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[1,2]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_2_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[2,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_2_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[2,2]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_3_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[3,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_3_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[3,2]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_4_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[4,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_4_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[4,2]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_5_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[5,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_5_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[5,2]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_6_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[6,1]_' + template_name)
    wt_control4B_qLimiter_TableQMaxUwtcFilt_6_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMaxUwtcFilt[6,2]_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt11: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt11_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt12: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt12_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt21: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt21_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt22: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt22_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt31: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt31_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt32: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt32_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt41: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt41_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt42: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt42_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt_1_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt[1,1]_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt_1_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt[1,2]_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt_2_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt[2,1]_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt_2_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt[2,2]_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt_3_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt[3,1]_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt_3_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt[3,2]_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt_4_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt[4,1]_' + template_name)
    wt_control4B_qLimiter_TableQMinPwtcFilt_4_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMinPwtcFilt[4,2]_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt11: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt11_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt12: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt12_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt21: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt21_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt22: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt22_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt31: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt31_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt32: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt32_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt41: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt41_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt42: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt42_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt_1_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt[1,1]_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt_1_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt[1,2]_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt_2_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt[2,1]_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt_2_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt[2,2]_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt_3_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt[3,1]_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt_3_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt[3,2]_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt_4_1: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt[4,1]_' + template_name)
    wt_control4B_qLimiter_TableQMinUwtcFilt_4_2: Var = vf.add_var('wt.control4B.qLimiter.TableQMinUwtcFilt[4,2]_' + template_name)
    wt_control4B_qLimiter_U0Pu: Var = vf.add_var('wt.control4B.qLimiter.U0Pu_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_DyMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.DyMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_DyMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.DyMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_U0: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.U0_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_Y0: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.Y0_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_YMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.YMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_YMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.YMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_fixedDelay_delayTime: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.fixedDelay.delayTime_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_homotopyType: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.limiter.homotopyType_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.limiter.limitsAtInit_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_strict: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.limiter.strict_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.limiter.uMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.limiter.uMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_DuMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.DuMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_DuMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.DuMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_Y0: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.Y0_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_k: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.gain.k_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_initType: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.initType_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_k: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.k_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_use_reset: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.use_reset_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_use_set: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.use_set_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y_start: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.y_start_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_homotopyType: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.homotopyType_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.limitsAtInit_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_strict: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.strict_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.uMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.uMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_tS: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.tS_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_tS: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.tS_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_DyMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.DyMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_DyMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.DyMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_U0: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.U0_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_Y0: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.Y0_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_YMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.YMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_YMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.YMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_fixedDelay_delayTime: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.fixedDelay.delayTime_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_homotopyType: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.limiter.homotopyType_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.limiter.limitsAtInit_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_strict: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.limiter.strict_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.limiter.uMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.limiter.uMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_DuMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.DuMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_DuMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.DuMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_Y0: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.Y0_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_k: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.gain.k_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_initType: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.integrator.initType_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_k: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.integrator.k_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_use_reset: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.integrator.use_reset_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_use_set: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.integrator.use_set_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y_start: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.integrator.y_start_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_homotopyType: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.limiter.homotopyType_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_limitsAtInit: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.limiter.limitsAtInit_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_strict: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.limiter.strict_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMax: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.limiter.uMax_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMin: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.limiter.uMin_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_tS: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.tS_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_tS: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.tS_' + template_name)
    wt_control4B_qLimiter_booleanConstant_k: Var = vf.add_var('wt.control4B.qLimiter.booleanConstant.k_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_columns_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.columns[1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_extrapolation: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.extrapolation_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_fileName: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.fileName_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_nout: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.nout_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_smoothness: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.smoothness_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_tableID: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.tableID_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_tableName: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.tableName_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_tableOnFile: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.tableOnFile_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_1_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[1,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_1_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[1,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_2_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[2,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_2_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[2,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_3_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[3,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_3_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[3,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_4_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[4,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_4_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[4,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_5_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[5,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_5_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[5,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_6_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[6,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_table_6_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.table[6,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_u_max: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.u_max_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_u_min: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.u_min_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_verboseExtrapolation: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.verboseExtrapolation_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_verboseRead: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.verboseRead_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_columns_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.columns[1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_extrapolation: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.extrapolation_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_fileName: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.fileName_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_nout: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.nout_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_smoothness: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.smoothness_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_tableID: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.tableID_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_tableName: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.tableName_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_tableOnFile: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.tableOnFile_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_table_1_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.table[1,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_table_1_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.table[1,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_table_2_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.table[2,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_table_2_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.table[2,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_table_3_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.table[3,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_table_3_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.table[3,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_table_4_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.table[4,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_table_4_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.table[4,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_u_max: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.u_max_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_u_min: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.u_min_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_verboseExtrapolation: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.verboseExtrapolation_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_verboseRead: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.verboseRead_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_columns_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.columns[1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_extrapolation: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.extrapolation_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_fileName: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.fileName_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_nout: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.nout_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_smoothness: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.smoothness_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_tableID: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.tableID_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_tableName: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.tableName_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_tableOnFile: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.tableOnFile_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_table_1_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.table[1,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_table_1_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.table[1,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_table_2_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.table[2,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_table_2_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.table[2,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_table_3_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.table[3,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_table_3_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.table[3,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_table_4_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.table[4,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_table_4_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.table[4,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_u_max: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.u_max_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_u_min: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.u_min_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_verboseExtrapolation: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.verboseExtrapolation_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_verboseRead: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.verboseRead_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_columns_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.columns[1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_extrapolation: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.extrapolation_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_fileName: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.fileName_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_nout: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.nout_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_smoothness: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.smoothness_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_tableID: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.tableID_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_tableName: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.tableName_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_tableOnFile: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.tableOnFile_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_table_1_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.table[1,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_table_1_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.table[1,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_table_2_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.table[2,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_table_2_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.table[2,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_table_3_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.table[3,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_table_3_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.table[3,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_table_4_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.table[4,1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_table_4_2: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.table[4,2]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_u_max: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.u_max_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_u_min: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.u_min_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_verboseExtrapolation: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.verboseExtrapolation_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_verboseRead: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.verboseRead_' + template_name)
    wt_control4B_qLimiter_const_k: Var = vf.add_var('wt.control4B.qLimiter.const.k_' + template_name)
    wt_control4B_qLimiter_constant1_k: Var = vf.add_var('wt.control4B.qLimiter.constant1.k_' + template_name)
    wt_control4B_qLimiter_integerToBoolean_threshold: Var = vf.add_var('wt.control4B.qLimiter.integerToBoolean.threshold_' + template_name)
    wt_control4B_qLimiter_tS: Var = vf.add_var('wt.control4B.qLimiter.tS_' + template_name)
    wt_control4B_tPAero: Var = vf.add_var('wt.control4B.tPAero_' + template_name)
    wt_control4B_tPOrdP4B: Var = vf.add_var('wt.control4B.tPOrdP4B_' + template_name)
    wt_control4B_tPost: Var = vf.add_var('wt.control4B.tPost_' + template_name)
    wt_control4B_tQord: Var = vf.add_var('wt.control4B.tQord_' + template_name)
    wt_control4B_tS: Var = vf.add_var('wt.control4B.tS_' + template_name)
    wt_control4B_tUss: Var = vf.add_var('wt.control4B.tUss_' + template_name)
    wt_controlMeasurements_DfMaxPu: Var = vf.add_var('wt.controlMeasurements.DfMaxPu_' + template_name)
    wt_controlMeasurements_P0Pu: Var = vf.add_var('wt.controlMeasurements.P0Pu_' + template_name)
    wt_controlMeasurements_Q0Pu: Var = vf.add_var('wt.controlMeasurements.Q0Pu_' + template_name)
    wt_controlMeasurements_SNom: Var = vf.add_var('wt.controlMeasurements.SNom_' + template_name)
    wt_controlMeasurements_U0Pu: Var = vf.add_var('wt.controlMeasurements.U0Pu_' + template_name)
    wt_controlMeasurements_UPhase0: Var = vf.add_var('wt.controlMeasurements.UPhase0_' + template_name)
    wt_controlMeasurements_add_k1: Var = vf.add_var('wt.controlMeasurements.add.k1_' + template_name)
    wt_controlMeasurements_add_k2: Var = vf.add_var('wt.controlMeasurements.add.k2_' + template_name)
    wt_controlMeasurements_complexToReal_useConjugateInput: Var = vf.add_var('wt.controlMeasurements.complexToReal.useConjugateInput_' + template_name)
    wt_controlMeasurements_derivative_T: Var = vf.add_var('wt.controlMeasurements.derivative.T_' + template_name)
    wt_controlMeasurements_derivative_initType: Var = vf.add_var('wt.controlMeasurements.derivative.initType_' + template_name)
    wt_controlMeasurements_derivative_k: Var = vf.add_var('wt.controlMeasurements.derivative.k_' + template_name)
    wt_controlMeasurements_derivative_x_start: Var = vf.add_var('wt.controlMeasurements.derivative.x_start_' + template_name)
    wt_controlMeasurements_derivative_y_start: Var = vf.add_var('wt.controlMeasurements.derivative.y_start_' + template_name)
    wt_controlMeasurements_derivative_zeroGain: Var = vf.add_var('wt.controlMeasurements.derivative.zeroGain_' + template_name)
    wt_controlMeasurements_firstOrder_T: Var = vf.add_var('wt.controlMeasurements.firstOrder.T_' + template_name)
    wt_controlMeasurements_firstOrder_initType: Var = vf.add_var('wt.controlMeasurements.firstOrder.initType_' + template_name)
    wt_controlMeasurements_firstOrder_k: Var = vf.add_var('wt.controlMeasurements.firstOrder.k_' + template_name)
    wt_controlMeasurements_firstOrder_y_start: Var = vf.add_var('wt.controlMeasurements.firstOrder.y_start_' + template_name)
    wt_controlMeasurements_firstOrder1_T: Var = vf.add_var('wt.controlMeasurements.firstOrder1.T_' + template_name)
    wt_controlMeasurements_firstOrder1_initType: Var = vf.add_var('wt.controlMeasurements.firstOrder1.initType_' + template_name)
    wt_controlMeasurements_firstOrder1_k: Var = vf.add_var('wt.controlMeasurements.firstOrder1.k_' + template_name)
    wt_controlMeasurements_firstOrder1_y_start: Var = vf.add_var('wt.controlMeasurements.firstOrder1.y_start_' + template_name)
    wt_controlMeasurements_firstOrder2_T: Var = vf.add_var('wt.controlMeasurements.firstOrder2.T_' + template_name)
    wt_controlMeasurements_firstOrder2_initType: Var = vf.add_var('wt.controlMeasurements.firstOrder2.initType_' + template_name)
    wt_controlMeasurements_firstOrder2_k: Var = vf.add_var('wt.controlMeasurements.firstOrder2.k_' + template_name)
    wt_controlMeasurements_firstOrder2_y_start: Var = vf.add_var('wt.controlMeasurements.firstOrder2.y_start_' + template_name)
    wt_controlMeasurements_firstOrder3_T: Var = vf.add_var('wt.controlMeasurements.firstOrder3.T_' + template_name)
    wt_controlMeasurements_firstOrder3_initType: Var = vf.add_var('wt.controlMeasurements.firstOrder3.initType_' + template_name)
    wt_controlMeasurements_firstOrder3_k: Var = vf.add_var('wt.controlMeasurements.firstOrder3.k_' + template_name)
    wt_controlMeasurements_firstOrder3_y_start: Var = vf.add_var('wt.controlMeasurements.firstOrder3.y_start_' + template_name)
    wt_controlMeasurements_firstOrder4_T: Var = vf.add_var('wt.controlMeasurements.firstOrder4.T_' + template_name)
    wt_controlMeasurements_firstOrder4_initType: Var = vf.add_var('wt.controlMeasurements.firstOrder4.initType_' + template_name)
    wt_controlMeasurements_firstOrder4_k: Var = vf.add_var('wt.controlMeasurements.firstOrder4.k_' + template_name)
    wt_controlMeasurements_firstOrder4_y_start: Var = vf.add_var('wt.controlMeasurements.firstOrder4.y_start_' + template_name)
    wt_controlMeasurements_i0Pu_im: Var = vf.add_var('wt.controlMeasurements.i0Pu.im_' + template_name)
    wt_controlMeasurements_i0Pu_re: Var = vf.add_var('wt.controlMeasurements.i0Pu.re_' + template_name)
    wt_controlMeasurements_product_useConjugateInput1: Var = vf.add_var('wt.controlMeasurements.product.useConjugateInput1_' + template_name)
    wt_controlMeasurements_product_useConjugateInput2: Var = vf.add_var('wt.controlMeasurements.product.useConjugateInput2_' + template_name)
    wt_controlMeasurements_rampLimiter_DuMax: Var = vf.add_var('wt.controlMeasurements.rampLimiter.DuMax_' + template_name)
    wt_controlMeasurements_rampLimiter_DuMin: Var = vf.add_var('wt.controlMeasurements.rampLimiter.DuMin_' + template_name)
    wt_controlMeasurements_rampLimiter_Y0: Var = vf.add_var('wt.controlMeasurements.rampLimiter.Y0_' + template_name)
    wt_controlMeasurements_rampLimiter_gain_k: Var = vf.add_var('wt.controlMeasurements.rampLimiter.gain.k_' + template_name)
    wt_controlMeasurements_rampLimiter_integrator_initType: Var = vf.add_var('wt.controlMeasurements.rampLimiter.integrator.initType_' + template_name)
    wt_controlMeasurements_rampLimiter_integrator_k: Var = vf.add_var('wt.controlMeasurements.rampLimiter.integrator.k_' + template_name)
    wt_controlMeasurements_rampLimiter_integrator_use_reset: Var = vf.add_var('wt.controlMeasurements.rampLimiter.integrator.use_reset_' + template_name)
    wt_controlMeasurements_rampLimiter_integrator_use_set: Var = vf.add_var('wt.controlMeasurements.rampLimiter.integrator.use_set_' + template_name)
    wt_controlMeasurements_rampLimiter_integrator_y_start: Var = vf.add_var('wt.controlMeasurements.rampLimiter.integrator.y_start_' + template_name)
    wt_controlMeasurements_rampLimiter_limiter_homotopyType: Var = vf.add_var('wt.controlMeasurements.rampLimiter.limiter.homotopyType_' + template_name)
    wt_controlMeasurements_rampLimiter_limiter_limitsAtInit: Var = vf.add_var('wt.controlMeasurements.rampLimiter.limiter.limitsAtInit_' + template_name)
    wt_controlMeasurements_rampLimiter_limiter_strict: Var = vf.add_var('wt.controlMeasurements.rampLimiter.limiter.strict_' + template_name)
    wt_controlMeasurements_rampLimiter_limiter_uMax: Var = vf.add_var('wt.controlMeasurements.rampLimiter.limiter.uMax_' + template_name)
    wt_controlMeasurements_rampLimiter_limiter_uMin: Var = vf.add_var('wt.controlMeasurements.rampLimiter.limiter.uMin_' + template_name)
    wt_controlMeasurements_rampLimiter_tS: Var = vf.add_var('wt.controlMeasurements.rampLimiter.tS_' + template_name)
    wt_controlMeasurements_tIFilt: Var = vf.add_var('wt.controlMeasurements.tIFilt_' + template_name)
    wt_controlMeasurements_tPFilt: Var = vf.add_var('wt.controlMeasurements.tPFilt_' + template_name)
    wt_controlMeasurements_tQFilt: Var = vf.add_var('wt.controlMeasurements.tQFilt_' + template_name)
    wt_controlMeasurements_tS: Var = vf.add_var('wt.controlMeasurements.tS_' + template_name)
    wt_controlMeasurements_tUFilt: Var = vf.add_var('wt.controlMeasurements.tUFilt_' + template_name)
    wt_controlMeasurements_tfFilt: Var = vf.add_var('wt.controlMeasurements.tfFilt_' + template_name)
    wt_controlMeasurements_u0Pu_im: Var = vf.add_var('wt.controlMeasurements.u0Pu.im_' + template_name)
    wt_controlMeasurements_u0Pu_re: Var = vf.add_var('wt.controlMeasurements.u0Pu.re_' + template_name)
    wt_fOverPu: Var = vf.add_var('wt.fOverPu_' + template_name)
    wt_fUnderPu: Var = vf.add_var('wt.fUnderPu_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt11: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt11_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt12: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt12_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt21: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt21_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt22: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt22_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt31: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt31_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt32: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt32_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt41: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt41_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt42: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt42_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt51: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt51_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt52: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt52_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt61: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt61_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt62: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt62_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt71: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt71_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt72: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt72_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt81: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt81_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt82: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt82_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_1_1: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[1,1]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_1_2: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[1,2]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_2_1: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[2,1]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_2_2: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[2,2]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_3_1: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[3,1]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_3_2: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[3,2]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_4_1: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[4,1]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_4_2: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[4,2]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_5_1: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[5,1]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_5_2: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[5,2]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_6_1: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[6,1]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_6_2: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[6,2]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_7_1: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[7,1]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_7_2: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[7,2]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_8_1: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[8,1]_' + template_name)
    wt_gridProtection_TabletUoverUwtfilt_8_2: Var = vf.add_var('wt.gridProtection.TabletUoverUwtfilt[8,2]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt11: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt11_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt12: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt12_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt21: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt21_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt22: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt22_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt31: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt31_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt32: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt32_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt41: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt41_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt42: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt42_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt51: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt51_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt52: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt52_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt61: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt61_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt62: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt62_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt71: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt71_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt72: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt72_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_1_1: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[1,1]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_1_2: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[1,2]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_2_1: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[2,1]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_2_2: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[2,2]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_3_1: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[3,1]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_3_2: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[3,2]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_4_1: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[4,1]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_4_2: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[4,2]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_5_1: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[5,1]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_5_2: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[5,2]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_6_1: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[6,1]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_6_2: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[6,2]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_7_1: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[7,1]_' + template_name)
    wt_gridProtection_TabletUunderUwtfilt_7_2: Var = vf.add_var('wt.gridProtection.TabletUunderUwtfilt[7,2]_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt11: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt11_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt12: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt12_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt21: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt21_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt22: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt22_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt31: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt31_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt32: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt32_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt41: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt41_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt42: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt42_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt_1_1: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt[1,1]_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt_1_2: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt[1,2]_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt_2_1: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt[2,1]_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt_2_2: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt[2,2]_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt_3_1: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt[3,1]_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt_3_2: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt[3,2]_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt_4_1: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt[4,1]_' + template_name)
    wt_gridProtection_Tabletfoverfwtfilt_4_2: Var = vf.add_var('wt.gridProtection.Tabletfoverfwtfilt[4,2]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt11: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt11_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt12: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt12_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt21: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt21_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt22: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt22_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt31: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt31_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt32: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt32_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt41: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt41_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt42: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt42_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt51: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt51_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt52: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt52_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt61: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt61_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt62: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt62_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_1_1: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[1,1]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_1_2: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[1,2]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_2_1: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[2,1]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_2_2: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[2,2]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_3_1: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[3,1]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_3_2: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[3,2]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_4_1: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[4,1]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_4_2: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[4,2]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_5_1: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[5,1]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_5_2: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[5,2]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_6_1: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[6,1]_' + template_name)
    wt_gridProtection_Tabletfunderfwtfilt_6_2: Var = vf.add_var('wt.gridProtection.Tabletfunderfwtfilt[6,2]_' + template_name)
    wt_gridProtection_U0Pu: Var = vf.add_var('wt.gridProtection.U0Pu_' + template_name)
    wt_gridProtection_UOverPu: Var = vf.add_var('wt.gridProtection.UOverPu_' + template_name)
    wt_gridProtection_UUnderPu: Var = vf.add_var('wt.gridProtection.UUnderPu_' + template_name)
    wt_gridProtection_combiTable1D_columns_1: Var = vf.add_var('wt.gridProtection.combiTable1D.columns[1]_' + template_name)
    wt_gridProtection_combiTable1D_extrapolation: Var = vf.add_var('wt.gridProtection.combiTable1D.extrapolation_' + template_name)
    wt_gridProtection_combiTable1D_fileName: Var = vf.add_var('wt.gridProtection.combiTable1D.fileName_' + template_name)
    wt_gridProtection_combiTable1D_nout: Var = vf.add_var('wt.gridProtection.combiTable1D.nout_' + template_name)
    wt_gridProtection_combiTable1D_smoothness: Var = vf.add_var('wt.gridProtection.combiTable1D.smoothness_' + template_name)
    wt_gridProtection_combiTable1D_tableID: Var = vf.add_var('wt.gridProtection.combiTable1D.tableID_' + template_name)
    wt_gridProtection_combiTable1D_tableName: Var = vf.add_var('wt.gridProtection.combiTable1D.tableName_' + template_name)
    wt_gridProtection_combiTable1D_tableOnFile: Var = vf.add_var('wt.gridProtection.combiTable1D.tableOnFile_' + template_name)
    wt_gridProtection_combiTable1D_table_1_1: Var = vf.add_var('wt.gridProtection.combiTable1D.table[1,1]_' + template_name)
    wt_gridProtection_combiTable1D_table_1_2: Var = vf.add_var('wt.gridProtection.combiTable1D.table[1,2]_' + template_name)
    wt_gridProtection_combiTable1D_table_2_1: Var = vf.add_var('wt.gridProtection.combiTable1D.table[2,1]_' + template_name)
    wt_gridProtection_combiTable1D_table_2_2: Var = vf.add_var('wt.gridProtection.combiTable1D.table[2,2]_' + template_name)
    wt_gridProtection_combiTable1D_table_3_1: Var = vf.add_var('wt.gridProtection.combiTable1D.table[3,1]_' + template_name)
    wt_gridProtection_combiTable1D_table_3_2: Var = vf.add_var('wt.gridProtection.combiTable1D.table[3,2]_' + template_name)
    wt_gridProtection_combiTable1D_table_4_1: Var = vf.add_var('wt.gridProtection.combiTable1D.table[4,1]_' + template_name)
    wt_gridProtection_combiTable1D_table_4_2: Var = vf.add_var('wt.gridProtection.combiTable1D.table[4,2]_' + template_name)
    wt_gridProtection_combiTable1D_table_5_1: Var = vf.add_var('wt.gridProtection.combiTable1D.table[5,1]_' + template_name)
    wt_gridProtection_combiTable1D_table_5_2: Var = vf.add_var('wt.gridProtection.combiTable1D.table[5,2]_' + template_name)
    wt_gridProtection_combiTable1D_table_6_1: Var = vf.add_var('wt.gridProtection.combiTable1D.table[6,1]_' + template_name)
    wt_gridProtection_combiTable1D_table_6_2: Var = vf.add_var('wt.gridProtection.combiTable1D.table[6,2]_' + template_name)
    wt_gridProtection_combiTable1D_table_7_1: Var = vf.add_var('wt.gridProtection.combiTable1D.table[7,1]_' + template_name)
    wt_gridProtection_combiTable1D_table_7_2: Var = vf.add_var('wt.gridProtection.combiTable1D.table[7,2]_' + template_name)
    wt_gridProtection_combiTable1D_table_8_1: Var = vf.add_var('wt.gridProtection.combiTable1D.table[8,1]_' + template_name)
    wt_gridProtection_combiTable1D_table_8_2: Var = vf.add_var('wt.gridProtection.combiTable1D.table[8,2]_' + template_name)
    wt_gridProtection_combiTable1D_u_max: Var = vf.add_var('wt.gridProtection.combiTable1D.u_max_' + template_name)
    wt_gridProtection_combiTable1D_u_min: Var = vf.add_var('wt.gridProtection.combiTable1D.u_min_' + template_name)
    wt_gridProtection_combiTable1D_verboseExtrapolation: Var = vf.add_var('wt.gridProtection.combiTable1D.verboseExtrapolation_' + template_name)
    wt_gridProtection_combiTable1D_verboseRead: Var = vf.add_var('wt.gridProtection.combiTable1D.verboseRead_' + template_name)
    wt_gridProtection_combiTable1D1_columns_1: Var = vf.add_var('wt.gridProtection.combiTable1D1.columns[1]_' + template_name)
    wt_gridProtection_combiTable1D1_extrapolation: Var = vf.add_var('wt.gridProtection.combiTable1D1.extrapolation_' + template_name)
    wt_gridProtection_combiTable1D1_fileName: Var = vf.add_var('wt.gridProtection.combiTable1D1.fileName_' + template_name)
    wt_gridProtection_combiTable1D1_nout: Var = vf.add_var('wt.gridProtection.combiTable1D1.nout_' + template_name)
    wt_gridProtection_combiTable1D1_smoothness: Var = vf.add_var('wt.gridProtection.combiTable1D1.smoothness_' + template_name)
    wt_gridProtection_combiTable1D1_tableID: Var = vf.add_var('wt.gridProtection.combiTable1D1.tableID_' + template_name)
    wt_gridProtection_combiTable1D1_tableName: Var = vf.add_var('wt.gridProtection.combiTable1D1.tableName_' + template_name)
    wt_gridProtection_combiTable1D1_tableOnFile: Var = vf.add_var('wt.gridProtection.combiTable1D1.tableOnFile_' + template_name)
    wt_gridProtection_combiTable1D1_table_1_1: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[1,1]_' + template_name)
    wt_gridProtection_combiTable1D1_table_1_2: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[1,2]_' + template_name)
    wt_gridProtection_combiTable1D1_table_2_1: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[2,1]_' + template_name)
    wt_gridProtection_combiTable1D1_table_2_2: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[2,2]_' + template_name)
    wt_gridProtection_combiTable1D1_table_3_1: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[3,1]_' + template_name)
    wt_gridProtection_combiTable1D1_table_3_2: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[3,2]_' + template_name)
    wt_gridProtection_combiTable1D1_table_4_1: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[4,1]_' + template_name)
    wt_gridProtection_combiTable1D1_table_4_2: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[4,2]_' + template_name)
    wt_gridProtection_combiTable1D1_table_5_1: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[5,1]_' + template_name)
    wt_gridProtection_combiTable1D1_table_5_2: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[5,2]_' + template_name)
    wt_gridProtection_combiTable1D1_table_6_1: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[6,1]_' + template_name)
    wt_gridProtection_combiTable1D1_table_6_2: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[6,2]_' + template_name)
    wt_gridProtection_combiTable1D1_table_7_1: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[7,1]_' + template_name)
    wt_gridProtection_combiTable1D1_table_7_2: Var = vf.add_var('wt.gridProtection.combiTable1D1.table[7,2]_' + template_name)
    wt_gridProtection_combiTable1D1_u_max: Var = vf.add_var('wt.gridProtection.combiTable1D1.u_max_' + template_name)
    wt_gridProtection_combiTable1D1_u_min: Var = vf.add_var('wt.gridProtection.combiTable1D1.u_min_' + template_name)
    wt_gridProtection_combiTable1D1_verboseExtrapolation: Var = vf.add_var('wt.gridProtection.combiTable1D1.verboseExtrapolation_' + template_name)
    wt_gridProtection_combiTable1D1_verboseRead: Var = vf.add_var('wt.gridProtection.combiTable1D1.verboseRead_' + template_name)
    wt_gridProtection_combiTable1D2_columns_1: Var = vf.add_var('wt.gridProtection.combiTable1D2.columns[1]_' + template_name)
    wt_gridProtection_combiTable1D2_extrapolation: Var = vf.add_var('wt.gridProtection.combiTable1D2.extrapolation_' + template_name)
    wt_gridProtection_combiTable1D2_fileName: Var = vf.add_var('wt.gridProtection.combiTable1D2.fileName_' + template_name)
    wt_gridProtection_combiTable1D2_nout: Var = vf.add_var('wt.gridProtection.combiTable1D2.nout_' + template_name)
    wt_gridProtection_combiTable1D2_smoothness: Var = vf.add_var('wt.gridProtection.combiTable1D2.smoothness_' + template_name)
    wt_gridProtection_combiTable1D2_tableID: Var = vf.add_var('wt.gridProtection.combiTable1D2.tableID_' + template_name)
    wt_gridProtection_combiTable1D2_tableName: Var = vf.add_var('wt.gridProtection.combiTable1D2.tableName_' + template_name)
    wt_gridProtection_combiTable1D2_tableOnFile: Var = vf.add_var('wt.gridProtection.combiTable1D2.tableOnFile_' + template_name)
    wt_gridProtection_combiTable1D2_table_1_1: Var = vf.add_var('wt.gridProtection.combiTable1D2.table[1,1]_' + template_name)
    wt_gridProtection_combiTable1D2_table_1_2: Var = vf.add_var('wt.gridProtection.combiTable1D2.table[1,2]_' + template_name)
    wt_gridProtection_combiTable1D2_table_2_1: Var = vf.add_var('wt.gridProtection.combiTable1D2.table[2,1]_' + template_name)
    wt_gridProtection_combiTable1D2_table_2_2: Var = vf.add_var('wt.gridProtection.combiTable1D2.table[2,2]_' + template_name)
    wt_gridProtection_combiTable1D2_table_3_1: Var = vf.add_var('wt.gridProtection.combiTable1D2.table[3,1]_' + template_name)
    wt_gridProtection_combiTable1D2_table_3_2: Var = vf.add_var('wt.gridProtection.combiTable1D2.table[3,2]_' + template_name)
    wt_gridProtection_combiTable1D2_table_4_1: Var = vf.add_var('wt.gridProtection.combiTable1D2.table[4,1]_' + template_name)
    wt_gridProtection_combiTable1D2_table_4_2: Var = vf.add_var('wt.gridProtection.combiTable1D2.table[4,2]_' + template_name)
    wt_gridProtection_combiTable1D2_u_max: Var = vf.add_var('wt.gridProtection.combiTable1D2.u_max_' + template_name)
    wt_gridProtection_combiTable1D2_u_min: Var = vf.add_var('wt.gridProtection.combiTable1D2.u_min_' + template_name)
    wt_gridProtection_combiTable1D2_verboseExtrapolation: Var = vf.add_var('wt.gridProtection.combiTable1D2.verboseExtrapolation_' + template_name)
    wt_gridProtection_combiTable1D2_verboseRead: Var = vf.add_var('wt.gridProtection.combiTable1D2.verboseRead_' + template_name)
    wt_gridProtection_combiTable1D3_columns_1: Var = vf.add_var('wt.gridProtection.combiTable1D3.columns[1]_' + template_name)
    wt_gridProtection_combiTable1D3_extrapolation: Var = vf.add_var('wt.gridProtection.combiTable1D3.extrapolation_' + template_name)
    wt_gridProtection_combiTable1D3_fileName: Var = vf.add_var('wt.gridProtection.combiTable1D3.fileName_' + template_name)
    wt_gridProtection_combiTable1D3_nout: Var = vf.add_var('wt.gridProtection.combiTable1D3.nout_' + template_name)
    wt_gridProtection_combiTable1D3_smoothness: Var = vf.add_var('wt.gridProtection.combiTable1D3.smoothness_' + template_name)
    wt_gridProtection_combiTable1D3_tableID: Var = vf.add_var('wt.gridProtection.combiTable1D3.tableID_' + template_name)
    wt_gridProtection_combiTable1D3_tableName: Var = vf.add_var('wt.gridProtection.combiTable1D3.tableName_' + template_name)
    wt_gridProtection_combiTable1D3_tableOnFile: Var = vf.add_var('wt.gridProtection.combiTable1D3.tableOnFile_' + template_name)
    wt_gridProtection_combiTable1D3_table_1_1: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[1,1]_' + template_name)
    wt_gridProtection_combiTable1D3_table_1_2: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[1,2]_' + template_name)
    wt_gridProtection_combiTable1D3_table_2_1: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[2,1]_' + template_name)
    wt_gridProtection_combiTable1D3_table_2_2: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[2,2]_' + template_name)
    wt_gridProtection_combiTable1D3_table_3_1: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[3,1]_' + template_name)
    wt_gridProtection_combiTable1D3_table_3_2: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[3,2]_' + template_name)
    wt_gridProtection_combiTable1D3_table_4_1: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[4,1]_' + template_name)
    wt_gridProtection_combiTable1D3_table_4_2: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[4,2]_' + template_name)
    wt_gridProtection_combiTable1D3_table_5_1: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[5,1]_' + template_name)
    wt_gridProtection_combiTable1D3_table_5_2: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[5,2]_' + template_name)
    wt_gridProtection_combiTable1D3_table_6_1: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[6,1]_' + template_name)
    wt_gridProtection_combiTable1D3_table_6_2: Var = vf.add_var('wt.gridProtection.combiTable1D3.table[6,2]_' + template_name)
    wt_gridProtection_combiTable1D3_u_max: Var = vf.add_var('wt.gridProtection.combiTable1D3.u_max_' + template_name)
    wt_gridProtection_combiTable1D3_u_min: Var = vf.add_var('wt.gridProtection.combiTable1D3.u_min_' + template_name)
    wt_gridProtection_combiTable1D3_verboseExtrapolation: Var = vf.add_var('wt.gridProtection.combiTable1D3.verboseExtrapolation_' + template_name)
    wt_gridProtection_combiTable1D3_verboseRead: Var = vf.add_var('wt.gridProtection.combiTable1D3.verboseRead_' + template_name)
    wt_gridProtection_const_k: Var = vf.add_var('wt.gridProtection.const.k_' + template_name)
    wt_gridProtection_const1_k: Var = vf.add_var('wt.gridProtection.const1.k_' + template_name)
    wt_gridProtection_const2_k: Var = vf.add_var('wt.gridProtection.const2.k_' + template_name)
    wt_gridProtection_const3_k: Var = vf.add_var('wt.gridProtection.const3.k_' + template_name)
    wt_gridProtection_fOverPu: Var = vf.add_var('wt.gridProtection.fOverPu_' + template_name)
    wt_gridProtection_fUnderPu: Var = vf.add_var('wt.gridProtection.fUnderPu_' + template_name)
    wt_gridProtection_or1_nu: Var = vf.add_var('wt.gridProtection.or1.nu_' + template_name)
    wt_gridProtection_pre1_pre_u_start: Var = vf.add_var('wt.gridProtection.pre1.pre_u_start_' + template_name)
    wt_i0Pu_im: Var = vf.add_var('wt.i0Pu.im_' + template_name)
    wt_i0Pu_re: Var = vf.add_var('wt.i0Pu.re_' + template_name)
    wt_mechanical_CdrtPu: Var = vf.add_var('wt.mechanical.CdrtPu_' + template_name)
    wt_mechanical_Hgen: Var = vf.add_var('wt.mechanical.Hgen_' + template_name)
    wt_mechanical_Hwtr: Var = vf.add_var('wt.mechanical.Hwtr_' + template_name)
    wt_mechanical_KdrtPu: Var = vf.add_var('wt.mechanical.KdrtPu_' + template_name)
    wt_mechanical_P0Pu: Var = vf.add_var('wt.mechanical.P0Pu_' + template_name)
    wt_mechanical_PAg0Pu: Var = vf.add_var('wt.mechanical.PAg0Pu_' + template_name)
    wt_mechanical_SNom: Var = vf.add_var('wt.mechanical.SNom_' + template_name)
    wt_mechanical_add_k1: Var = vf.add_var('wt.mechanical.add.k1_' + template_name)
    wt_mechanical_add_k2: Var = vf.add_var('wt.mechanical.add.k2_' + template_name)
    wt_mechanical_add1_k1: Var = vf.add_var('wt.mechanical.add1.k1_' + template_name)
    wt_mechanical_add1_k2: Var = vf.add_var('wt.mechanical.add1.k2_' + template_name)
    wt_mechanical_add2_k1: Var = vf.add_var('wt.mechanical.add2.k1_' + template_name)
    wt_mechanical_add2_k2: Var = vf.add_var('wt.mechanical.add2.k2_' + template_name)
    wt_mechanical_integrator_initType: Var = vf.add_var('wt.mechanical.integrator.initType_' + template_name)
    wt_mechanical_integrator_k: Var = vf.add_var('wt.mechanical.integrator.k_' + template_name)
    wt_mechanical_integrator_use_reset: Var = vf.add_var('wt.mechanical.integrator.use_reset_' + template_name)
    wt_mechanical_integrator_use_set: Var = vf.add_var('wt.mechanical.integrator.use_set_' + template_name)
    wt_mechanical_integrator_y_start: Var = vf.add_var('wt.mechanical.integrator.y_start_' + template_name)
    wt_mechanical_integrator1_initType: Var = vf.add_var('wt.mechanical.integrator1.initType_' + template_name)
    wt_mechanical_integrator1_k: Var = vf.add_var('wt.mechanical.integrator1.k_' + template_name)
    wt_mechanical_integrator1_use_reset: Var = vf.add_var('wt.mechanical.integrator1.use_reset_' + template_name)
    wt_mechanical_integrator1_use_set: Var = vf.add_var('wt.mechanical.integrator1.use_set_' + template_name)
    wt_mechanical_integrator1_y_start: Var = vf.add_var('wt.mechanical.integrator1.y_start_' + template_name)
    wt_mechanical_pI_Ki: Var = vf.add_var('wt.mechanical.pI.Ki_' + template_name)
    wt_mechanical_pI_Kp: Var = vf.add_var('wt.mechanical.pI.Kp_' + template_name)
    wt_mechanical_pI_Y0: Var = vf.add_var('wt.mechanical.pI.Y0_' + template_name)
    wt_mechanical_pI_add_k1: Var = vf.add_var('wt.mechanical.pI.add.k1_' + template_name)
    wt_mechanical_pI_add_k2: Var = vf.add_var('wt.mechanical.pI.add.k2_' + template_name)
    wt_mechanical_pI_integrator_initType: Var = vf.add_var('wt.mechanical.pI.integrator.initType_' + template_name)
    wt_mechanical_pI_integrator_k: Var = vf.add_var('wt.mechanical.pI.integrator.k_' + template_name)
    wt_mechanical_pI_integrator_use_reset: Var = vf.add_var('wt.mechanical.pI.integrator.use_reset_' + template_name)
    wt_mechanical_pI_integrator_use_set: Var = vf.add_var('wt.mechanical.pI.integrator.use_set_' + template_name)
    wt_mechanical_pI_integrator_y_start: Var = vf.add_var('wt.mechanical.pI.integrator.y_start_' + template_name)
    wt_pll_U0Pu: Var = vf.add_var('wt.pll.U0Pu_' + template_name)
    wt_pll_UPhase0: Var = vf.add_var('wt.pll.UPhase0_' + template_name)
    wt_pll_UPll1Pu: Var = vf.add_var('wt.pll.UPll1Pu_' + template_name)
    wt_pll_UPll2Pu: Var = vf.add_var('wt.pll.UPll2Pu_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_DyMax: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.DyMax_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_DyMin: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.DyMin_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_UseLimits: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.UseLimits_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_Y0: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.Y0_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_YMax: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.YMax_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_YMin: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.YMin_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_const_k: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.const.k_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_gain_k: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.gain.k_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_integrator_initType: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.integrator.initType_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_integrator_k: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.integrator.k_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_integrator_use_reset: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.integrator.use_reset_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_integrator_use_set: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.integrator.use_set_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_integrator_y_start: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.integrator.y_start_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_limiter_homotopyType: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.limiter.homotopyType_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_limiter_limitsAtInit: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.limiter.limitsAtInit_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_limiter_strict: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.limiter.strict_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMax: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.limiter.uMax_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMin: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.limiter.uMin_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_tI: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.tI_' + template_name)
    wt_pll_fixedBooleanDelay_Y0: Var = vf.add_var('wt.pll.fixedBooleanDelay.Y0_' + template_name)
    wt_pll_fixedBooleanDelay_tDelay: Var = vf.add_var('wt.pll.fixedBooleanDelay.tDelay_' + template_name)
    wt_pll_fixedBooleanDelay1_Y0: Var = vf.add_var('wt.pll.fixedBooleanDelay1.Y0_' + template_name)
    wt_pll_fixedBooleanDelay1_tDelay: Var = vf.add_var('wt.pll.fixedBooleanDelay1.tDelay_' + template_name)
    wt_pll_lessThreshold_threshold: Var = vf.add_var('wt.pll.lessThreshold.threshold_' + template_name)
    wt_pll_lessThreshold1_threshold: Var = vf.add_var('wt.pll.lessThreshold1.threshold_' + template_name)
    wt_pll_tPll: Var = vf.add_var('wt.pll.tPll_' + template_name)
    wt_pll_tS: Var = vf.add_var('wt.pll.tS_' + template_name)
    wt_protectionMeasurements_DfMaxPu: Var = vf.add_var('wt.protectionMeasurements.DfMaxPu_' + template_name)
    wt_protectionMeasurements_P0Pu: Var = vf.add_var('wt.protectionMeasurements.P0Pu_' + template_name)
    wt_protectionMeasurements_Q0Pu: Var = vf.add_var('wt.protectionMeasurements.Q0Pu_' + template_name)
    wt_protectionMeasurements_SNom: Var = vf.add_var('wt.protectionMeasurements.SNom_' + template_name)
    wt_protectionMeasurements_U0Pu: Var = vf.add_var('wt.protectionMeasurements.U0Pu_' + template_name)
    wt_protectionMeasurements_UPhase0: Var = vf.add_var('wt.protectionMeasurements.UPhase0_' + template_name)
    wt_protectionMeasurements_add_k1: Var = vf.add_var('wt.protectionMeasurements.add.k1_' + template_name)
    wt_protectionMeasurements_add_k2: Var = vf.add_var('wt.protectionMeasurements.add.k2_' + template_name)
    wt_protectionMeasurements_complexToReal_useConjugateInput: Var = vf.add_var('wt.protectionMeasurements.complexToReal.useConjugateInput_' + template_name)
    wt_protectionMeasurements_derivative_T: Var = vf.add_var('wt.protectionMeasurements.derivative.T_' + template_name)
    wt_protectionMeasurements_derivative_initType: Var = vf.add_var('wt.protectionMeasurements.derivative.initType_' + template_name)
    wt_protectionMeasurements_derivative_k: Var = vf.add_var('wt.protectionMeasurements.derivative.k_' + template_name)
    wt_protectionMeasurements_derivative_x_start: Var = vf.add_var('wt.protectionMeasurements.derivative.x_start_' + template_name)
    wt_protectionMeasurements_derivative_y_start: Var = vf.add_var('wt.protectionMeasurements.derivative.y_start_' + template_name)
    wt_protectionMeasurements_derivative_zeroGain: Var = vf.add_var('wt.protectionMeasurements.derivative.zeroGain_' + template_name)
    wt_protectionMeasurements_firstOrder_T: Var = vf.add_var('wt.protectionMeasurements.firstOrder.T_' + template_name)
    wt_protectionMeasurements_firstOrder_initType: Var = vf.add_var('wt.protectionMeasurements.firstOrder.initType_' + template_name)
    wt_protectionMeasurements_firstOrder_k: Var = vf.add_var('wt.protectionMeasurements.firstOrder.k_' + template_name)
    wt_protectionMeasurements_firstOrder_y_start: Var = vf.add_var('wt.protectionMeasurements.firstOrder.y_start_' + template_name)
    wt_protectionMeasurements_firstOrder1_T: Var = vf.add_var('wt.protectionMeasurements.firstOrder1.T_' + template_name)
    wt_protectionMeasurements_firstOrder1_initType: Var = vf.add_var('wt.protectionMeasurements.firstOrder1.initType_' + template_name)
    wt_protectionMeasurements_firstOrder1_k: Var = vf.add_var('wt.protectionMeasurements.firstOrder1.k_' + template_name)
    wt_protectionMeasurements_firstOrder1_y_start: Var = vf.add_var('wt.protectionMeasurements.firstOrder1.y_start_' + template_name)
    wt_protectionMeasurements_firstOrder2_T: Var = vf.add_var('wt.protectionMeasurements.firstOrder2.T_' + template_name)
    wt_protectionMeasurements_firstOrder2_initType: Var = vf.add_var('wt.protectionMeasurements.firstOrder2.initType_' + template_name)
    wt_protectionMeasurements_firstOrder2_k: Var = vf.add_var('wt.protectionMeasurements.firstOrder2.k_' + template_name)
    wt_protectionMeasurements_firstOrder2_y_start: Var = vf.add_var('wt.protectionMeasurements.firstOrder2.y_start_' + template_name)
    wt_protectionMeasurements_firstOrder3_T: Var = vf.add_var('wt.protectionMeasurements.firstOrder3.T_' + template_name)
    wt_protectionMeasurements_firstOrder3_initType: Var = vf.add_var('wt.protectionMeasurements.firstOrder3.initType_' + template_name)
    wt_protectionMeasurements_firstOrder3_k: Var = vf.add_var('wt.protectionMeasurements.firstOrder3.k_' + template_name)
    wt_protectionMeasurements_firstOrder3_y_start: Var = vf.add_var('wt.protectionMeasurements.firstOrder3.y_start_' + template_name)
    wt_protectionMeasurements_firstOrder4_T: Var = vf.add_var('wt.protectionMeasurements.firstOrder4.T_' + template_name)
    wt_protectionMeasurements_firstOrder4_initType: Var = vf.add_var('wt.protectionMeasurements.firstOrder4.initType_' + template_name)
    wt_protectionMeasurements_firstOrder4_k: Var = vf.add_var('wt.protectionMeasurements.firstOrder4.k_' + template_name)
    wt_protectionMeasurements_firstOrder4_y_start: Var = vf.add_var('wt.protectionMeasurements.firstOrder4.y_start_' + template_name)
    wt_protectionMeasurements_i0Pu_im: Var = vf.add_var('wt.protectionMeasurements.i0Pu.im_' + template_name)
    wt_protectionMeasurements_i0Pu_re: Var = vf.add_var('wt.protectionMeasurements.i0Pu.re_' + template_name)
    wt_protectionMeasurements_product_useConjugateInput1: Var = vf.add_var('wt.protectionMeasurements.product.useConjugateInput1_' + template_name)
    wt_protectionMeasurements_product_useConjugateInput2: Var = vf.add_var('wt.protectionMeasurements.product.useConjugateInput2_' + template_name)
    wt_protectionMeasurements_rampLimiter_DuMax: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.DuMax_' + template_name)
    wt_protectionMeasurements_rampLimiter_DuMin: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.DuMin_' + template_name)
    wt_protectionMeasurements_rampLimiter_Y0: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.Y0_' + template_name)
    wt_protectionMeasurements_rampLimiter_gain_k: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.gain.k_' + template_name)
    wt_protectionMeasurements_rampLimiter_integrator_initType: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.integrator.initType_' + template_name)
    wt_protectionMeasurements_rampLimiter_integrator_k: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.integrator.k_' + template_name)
    wt_protectionMeasurements_rampLimiter_integrator_use_reset: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.integrator.use_reset_' + template_name)
    wt_protectionMeasurements_rampLimiter_integrator_use_set: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.integrator.use_set_' + template_name)
    wt_protectionMeasurements_rampLimiter_integrator_y_start: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.integrator.y_start_' + template_name)
    wt_protectionMeasurements_rampLimiter_limiter_homotopyType: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.limiter.homotopyType_' + template_name)
    wt_protectionMeasurements_rampLimiter_limiter_limitsAtInit: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.limiter.limitsAtInit_' + template_name)
    wt_protectionMeasurements_rampLimiter_limiter_strict: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.limiter.strict_' + template_name)
    wt_protectionMeasurements_rampLimiter_limiter_uMax: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.limiter.uMax_' + template_name)
    wt_protectionMeasurements_rampLimiter_limiter_uMin: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.limiter.uMin_' + template_name)
    wt_protectionMeasurements_rampLimiter_tS: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.tS_' + template_name)
    wt_protectionMeasurements_tIFilt: Var = vf.add_var('wt.protectionMeasurements.tIFilt_' + template_name)
    wt_protectionMeasurements_tPFilt: Var = vf.add_var('wt.protectionMeasurements.tPFilt_' + template_name)
    wt_protectionMeasurements_tQFilt: Var = vf.add_var('wt.protectionMeasurements.tQFilt_' + template_name)
    wt_protectionMeasurements_tS: Var = vf.add_var('wt.protectionMeasurements.tS_' + template_name)
    wt_protectionMeasurements_tUFilt: Var = vf.add_var('wt.protectionMeasurements.tUFilt_' + template_name)
    wt_protectionMeasurements_tfFilt: Var = vf.add_var('wt.protectionMeasurements.tfFilt_' + template_name)
    wt_protectionMeasurements_u0Pu_im: Var = vf.add_var('wt.protectionMeasurements.u0Pu.im_' + template_name)
    wt_protectionMeasurements_u0Pu_re: Var = vf.add_var('wt.protectionMeasurements.u0Pu.re_' + template_name)
    wt_tG: Var = vf.add_var('wt.tG_' + template_name)
    wt_tIcFilt: Var = vf.add_var('wt.tIcFilt_' + template_name)
    wt_tIpFilt: Var = vf.add_var('wt.tIpFilt_' + template_name)
    wt_tPAero: Var = vf.add_var('wt.tPAero_' + template_name)
    wt_tPOrdP4B: Var = vf.add_var('wt.tPOrdP4B_' + template_name)
    wt_tPcFilt: Var = vf.add_var('wt.tPcFilt_' + template_name)
    wt_tPll: Var = vf.add_var('wt.tPll_' + template_name)
    wt_tPost: Var = vf.add_var('wt.tPost_' + template_name)
    wt_tPpFilt: Var = vf.add_var('wt.tPpFilt_' + template_name)
    wt_tQcFilt: Var = vf.add_var('wt.tQcFilt_' + template_name)
    wt_tQord: Var = vf.add_var('wt.tQord_' + template_name)
    wt_tQpFilt: Var = vf.add_var('wt.tQpFilt_' + template_name)
    wt_tS: Var = vf.add_var('wt.tS_' + template_name)
    wt_tUcFilt: Var = vf.add_var('wt.tUcFilt_' + template_name)
    wt_tUpFilt: Var = vf.add_var('wt.tUpFilt_' + template_name)
    wt_tUss: Var = vf.add_var('wt.tUss_' + template_name)
    wt_tfcFilt: Var = vf.add_var('wt.tfcFilt_' + template_name)
    wt_tfpFilt: Var = vf.add_var('wt.tfpFilt_' + template_name)
    wt_u0Pu_im: Var = vf.add_var('wt.u0Pu.im_' + template_name)
    wt_u0Pu_re: Var = vf.add_var('wt.u0Pu.re_' + template_name)
    wt_wT4Injector_BesPu: Var = vf.add_var('wt.wT4Injector.BesPu_' + template_name)
    wt_wT4Injector_DipMaxPu: Var = vf.add_var('wt.wT4Injector.DipMaxPu_' + template_name)
    wt_wT4Injector_DiqMaxPu: Var = vf.add_var('wt.wT4Injector.DiqMaxPu_' + template_name)
    wt_wT4Injector_DiqMinPu: Var = vf.add_var('wt.wT4Injector.DiqMinPu_' + template_name)
    wt_wT4Injector_GesPu: Var = vf.add_var('wt.wT4Injector.GesPu_' + template_name)
    wt_wT4Injector_IGsIm0Pu: Var = vf.add_var('wt.wT4Injector.IGsIm0Pu_' + template_name)
    wt_wT4Injector_IGsRe0Pu: Var = vf.add_var('wt.wT4Injector.IGsRe0Pu_' + template_name)
    wt_wT4Injector_IpMax0Pu: Var = vf.add_var('wt.wT4Injector.IpMax0Pu_' + template_name)
    wt_wT4Injector_IqMax0Pu: Var = vf.add_var('wt.wT4Injector.IqMax0Pu_' + template_name)
    wt_wT4Injector_IqMin0Pu: Var = vf.add_var('wt.wT4Injector.IqMin0Pu_' + template_name)
    wt_wT4Injector_Kipaw: Var = vf.add_var('wt.wT4Injector.Kipaw_' + template_name)
    wt_wT4Injector_Kiqaw: Var = vf.add_var('wt.wT4Injector.Kiqaw_' + template_name)
    wt_wT4Injector_NbSwitchOffSignals: Var = vf.add_var('wt.wT4Injector.NbSwitchOffSignals_' + template_name)
    wt_wT4Injector_P0Pu: Var = vf.add_var('wt.wT4Injector.P0Pu_' + template_name)
    wt_wT4Injector_PAg0Pu: Var = vf.add_var('wt.wT4Injector.PAg0Pu_' + template_name)
    wt_wT4Injector_Q0Pu: Var = vf.add_var('wt.wT4Injector.Q0Pu_' + template_name)
    wt_wT4Injector_ResPu: Var = vf.add_var('wt.wT4Injector.ResPu_' + template_name)
    wt_wT4Injector_Running0: Var = vf.add_var('wt.wT4Injector.Running0_' + template_name)
    wt_wT4Injector_SNom: Var = vf.add_var('wt.wT4Injector.SNom_' + template_name)
    wt_wT4Injector_State0: Var = vf.add_var('wt.wT4Injector.State0_' + template_name)
    wt_wT4Injector_SwitchOffSignal10: Var = vf.add_var('wt.wT4Injector.SwitchOffSignal10_' + template_name)
    wt_wT4Injector_SwitchOffSignal20: Var = vf.add_var('wt.wT4Injector.SwitchOffSignal20_' + template_name)
    wt_wT4Injector_SwitchOffSignal30: Var = vf.add_var('wt.wT4Injector.SwitchOffSignal30_' + template_name)
    wt_wT4Injector_U0Pu: Var = vf.add_var('wt.wT4Injector.U0Pu_' + template_name)
    wt_wT4Injector_UGsIm0Pu: Var = vf.add_var('wt.wT4Injector.UGsIm0Pu_' + template_name)
    wt_wT4Injector_UGsRe0Pu: Var = vf.add_var('wt.wT4Injector.UGsRe0Pu_' + template_name)
    wt_wT4Injector_UPhase0: Var = vf.add_var('wt.wT4Injector.UPhase0_' + template_name)
    wt_wT4Injector_XesPu: Var = vf.add_var('wt.wT4Injector.XesPu_' + template_name)
    wt_wT4Injector_elecSystem_BesPu: Var = vf.add_var('wt.wT4Injector.elecSystem.BesPu_' + template_name)
    wt_wT4Injector_elecSystem_GesPu: Var = vf.add_var('wt.wT4Injector.elecSystem.GesPu_' + template_name)
    wt_wT4Injector_elecSystem_IGsIm0Pu: Var = vf.add_var('wt.wT4Injector.elecSystem.IGsIm0Pu_' + template_name)
    wt_wT4Injector_elecSystem_IGsRe0Pu: Var = vf.add_var('wt.wT4Injector.elecSystem.IGsRe0Pu_' + template_name)
    wt_wT4Injector_elecSystem_ResPu: Var = vf.add_var('wt.wT4Injector.elecSystem.ResPu_' + template_name)
    wt_wT4Injector_elecSystem_SNom: Var = vf.add_var('wt.wT4Injector.elecSystem.SNom_' + template_name)
    wt_wT4Injector_elecSystem_UGsIm0Pu: Var = vf.add_var('wt.wT4Injector.elecSystem.UGsIm0Pu_' + template_name)
    wt_wT4Injector_elecSystem_UGsRe0Pu: Var = vf.add_var('wt.wT4Injector.elecSystem.UGsRe0Pu_' + template_name)
    wt_wT4Injector_elecSystem_XesPu: Var = vf.add_var('wt.wT4Injector.elecSystem.XesPu_' + template_name)
    wt_wT4Injector_elecSystem_i0Pu_im: Var = vf.add_var('wt.wT4Injector.elecSystem.i0Pu.im_' + template_name)
    wt_wT4Injector_elecSystem_i0Pu_re: Var = vf.add_var('wt.wT4Injector.elecSystem.i0Pu.re_' + template_name)
    wt_wT4Injector_elecSystem_u0Pu_im: Var = vf.add_var('wt.wT4Injector.elecSystem.u0Pu.im_' + template_name)
    wt_wT4Injector_elecSystem_u0Pu_re: Var = vf.add_var('wt.wT4Injector.elecSystem.u0Pu.re_' + template_name)
    wt_wT4Injector_genSystem_DipMaxPu: Var = vf.add_var('wt.wT4Injector.genSystem.DipMaxPu_' + template_name)
    wt_wT4Injector_genSystem_DiqMaxPu: Var = vf.add_var('wt.wT4Injector.genSystem.DiqMaxPu_' + template_name)
    wt_wT4Injector_genSystem_DiqMinPu: Var = vf.add_var('wt.wT4Injector.genSystem.DiqMinPu_' + template_name)
    wt_wT4Injector_genSystem_IGsIm0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.IGsIm0Pu_' + template_name)
    wt_wT4Injector_genSystem_IGsRe0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.IGsRe0Pu_' + template_name)
    wt_wT4Injector_genSystem_IpMax0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.IpMax0Pu_' + template_name)
    wt_wT4Injector_genSystem_IqMax0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.IqMax0Pu_' + template_name)
    wt_wT4Injector_genSystem_IqMin0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.IqMin0Pu_' + template_name)
    wt_wT4Injector_genSystem_Kipaw: Var = vf.add_var('wt.wT4Injector.genSystem.Kipaw_' + template_name)
    wt_wT4Injector_genSystem_Kiqaw: Var = vf.add_var('wt.wT4Injector.genSystem.Kiqaw_' + template_name)
    wt_wT4Injector_genSystem_P0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.P0Pu_' + template_name)
    wt_wT4Injector_genSystem_PAg0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.PAg0Pu_' + template_name)
    wt_wT4Injector_genSystem_Q0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.Q0Pu_' + template_name)
    wt_wT4Injector_genSystem_SNom: Var = vf.add_var('wt.wT4Injector.genSystem.SNom_' + template_name)
    wt_wT4Injector_genSystem_U0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.U0Pu_' + template_name)
    wt_wT4Injector_genSystem_UGsIm0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.UGsIm0Pu_' + template_name)
    wt_wT4Injector_genSystem_UGsRe0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.UGsRe0Pu_' + template_name)
    wt_wT4Injector_genSystem_UPhase0: Var = vf.add_var('wt.wT4Injector.genSystem.UPhase0_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_DyMax: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.DyMax_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_DyMin: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.DyMin_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_Kaw: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.Kaw_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_UseLimits: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.UseLimits_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_Y0: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.Y0_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_YMax: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.YMax_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_YMin: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.YMin_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_k1: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.add.k1_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_k2: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.add.k2_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_k: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.gain.k_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_initType: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.initType_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_k: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.k_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_use_reset: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.use_reset_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_use_set: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.use_set_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y_start: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.y_start_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_homotopyType: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.homotopyType_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_limitsAtInit: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.limitsAtInit_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_strict: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.strict_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.uMax_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.uMin_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_tI: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.tI_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMax: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.DyMax_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMin: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.DyMin_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_Kaw: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.Kaw_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_UseLimits: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.UseLimits_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_Y0: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.Y0_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_YMax: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.YMax_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_YMin: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.YMin_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k1: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.add.k1_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k2: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.add.k2_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_k: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.gain.k_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_initType: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.initType_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_k: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.k_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_use_reset: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.use_reset_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_use_set: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.use_set_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y_start: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.y_start_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_homotopyType: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.homotopyType_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_limitsAtInit: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.limitsAtInit_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_strict: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.strict_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.uMax_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.uMin_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_tI: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.tI_' + template_name)
    wt_wT4Injector_genSystem_complexToReal_useConjugateInput: Var = vf.add_var('wt.wT4Injector.genSystem.complexToReal.useConjugateInput_' + template_name)
    wt_wT4Injector_genSystem_const_k: Var = vf.add_var('wt.wT4Injector.genSystem.const.k_' + template_name)
    wt_wT4Injector_genSystem_iECFrameRotation_IGsIm0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.iECFrameRotation.IGsIm0Pu_' + template_name)
    wt_wT4Injector_genSystem_iECFrameRotation_IGsRe0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.iECFrameRotation.IGsRe0Pu_' + template_name)
    wt_wT4Injector_genSystem_iECFrameRotation_P0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.iECFrameRotation.P0Pu_' + template_name)
    wt_wT4Injector_genSystem_iECFrameRotation_Q0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.iECFrameRotation.Q0Pu_' + template_name)
    wt_wT4Injector_genSystem_iECFrameRotation_SNom: Var = vf.add_var('wt.wT4Injector.genSystem.iECFrameRotation.SNom_' + template_name)
    wt_wT4Injector_genSystem_iECFrameRotation_U0Pu: Var = vf.add_var('wt.wT4Injector.genSystem.iECFrameRotation.U0Pu_' + template_name)
    wt_wT4Injector_genSystem_iECFrameRotation_UPhase0: Var = vf.add_var('wt.wT4Injector.genSystem.iECFrameRotation.UPhase0_' + template_name)
    wt_wT4Injector_genSystem_product_useConjugateInput1: Var = vf.add_var('wt.wT4Injector.genSystem.product.useConjugateInput1_' + template_name)
    wt_wT4Injector_genSystem_product_useConjugateInput2: Var = vf.add_var('wt.wT4Injector.genSystem.product.useConjugateInput2_' + template_name)
    wt_wT4Injector_genSystem_tG: Var = vf.add_var('wt.wT4Injector.genSystem.tG_' + template_name)
    wt_wT4Injector_i0Pu_im: Var = vf.add_var('wt.wT4Injector.i0Pu.im_' + template_name)
    wt_wT4Injector_i0Pu_re: Var = vf.add_var('wt.wT4Injector.i0Pu.re_' + template_name)
    wt_wT4Injector_tG: Var = vf.add_var('wt.wT4Injector.tG_' + template_name)
    wt_wT4Injector_u0Pu_im: Var = vf.add_var('wt.wT4Injector.u0Pu.im_' + template_name)
    wt_wT4Injector_u0Pu_re: Var = vf.add_var('wt.wT4Injector.u0Pu.re_' + template_name)
    # Declare the state variables used by the template.
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.integrator.y_' + template_name)
    wt_control4B_pControl4B_firstOrder_y: Var = vf.add_var('wt.control4B.pControl4B.firstOrder.y_' + template_name)
    wt_control4B_pControl4B_rampLimiter_integrator_y: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.integrator.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.integrator.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_integrator_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.integrator.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_integrator_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.integrator.y_' + template_name)
    wt_control4B_qControl_derivative_x: Var = vf.add_var('wt.control4B.qControl.derivative.x_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.integrator.y_' + template_name)
    wt_controlMeasurements_derivative_x: Var = vf.add_var('wt.controlMeasurements.derivative.x_' + template_name)
    wt_controlMeasurements_firstOrder_y: Var = vf.add_var('wt.controlMeasurements.firstOrder.y_' + template_name)
    wt_controlMeasurements_firstOrder1_y: Var = vf.add_var('wt.controlMeasurements.firstOrder1.y_' + template_name)
    wt_controlMeasurements_firstOrder2_y: Var = vf.add_var('wt.controlMeasurements.firstOrder2.y_' + template_name)
    wt_controlMeasurements_firstOrder3_y: Var = vf.add_var('wt.controlMeasurements.firstOrder3.y_' + template_name)
    wt_controlMeasurements_firstOrder4_y: Var = vf.add_var('wt.controlMeasurements.firstOrder4.y_' + template_name)
    wt_controlMeasurements_rampLimiter_integrator_y: Var = vf.add_var('wt.controlMeasurements.rampLimiter.integrator.y_' + template_name)
    wt_mechanical_integrator_y: Var = vf.add_var('wt.mechanical.integrator.y_' + template_name)
    wt_mechanical_integrator1_y: Var = vf.add_var('wt.mechanical.integrator1.y_' + template_name)
    wt_mechanical_pI_integrator_y: Var = vf.add_var('wt.mechanical.pI.integrator.y_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_integrator_y: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.integrator.y_' + template_name)
    wt_protectionMeasurements_derivative_x: Var = vf.add_var('wt.protectionMeasurements.derivative.x_' + template_name)
    wt_protectionMeasurements_firstOrder_y: Var = vf.add_var('wt.protectionMeasurements.firstOrder.y_' + template_name)
    wt_protectionMeasurements_firstOrder1_y: Var = vf.add_var('wt.protectionMeasurements.firstOrder1.y_' + template_name)
    wt_protectionMeasurements_firstOrder2_y: Var = vf.add_var('wt.protectionMeasurements.firstOrder2.y_' + template_name)
    wt_protectionMeasurements_firstOrder3_y: Var = vf.add_var('wt.protectionMeasurements.firstOrder3.y_' + template_name)
    wt_protectionMeasurements_firstOrder4_y: Var = vf.add_var('wt.protectionMeasurements.firstOrder4.y_' + template_name)
    wt_protectionMeasurements_rampLimiter_integrator_y: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.integrator.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_wt_control4B_qControl_delayFlag_timer_entryTime: Var = vf.add_var('$PRE.wt.control4B.qControl.delayFlag.timer.entryTime_' + template_name)
    PRE_wt_gridProtection_pre1_u: Var = vf.add_var('$PRE.wt.gridProtection.pre1.u_' + template_name)
    PRE_wt_gridProtection_timer_entryTime: Var = vf.add_var('$PRE.wt.gridProtection.timer.entryTime_' + template_name)
    PRE_wt_gridProtection_timer1_entryTime: Var = vf.add_var('$PRE.wt.gridProtection.timer1.entryTime_' + template_name)
    PRE_wt_gridProtection_timer2_entryTime: Var = vf.add_var('$PRE.wt.gridProtection.timer2.entryTime_' + template_name)
    PRE_wt_gridProtection_timer3_entryTime: Var = vf.add_var('$PRE.wt.gridProtection.timer3.entryTime_' + template_name)
    PRE_wt_pll_fixedBooleanDelay_y: Var = vf.add_var('$PRE.wt.pll.fixedBooleanDelay.y_' + template_name)
    PRE_wt_pll_fixedBooleanDelay1_y: Var = vf.add_var('$PRE.wt.pll.fixedBooleanDelay1.y_' + template_name)
    PRE_wt_wT4Injector_running_value: Var = vf.add_var('$PRE.wt.wT4Injector.running.value_' + template_name)
    PRE_wt_wT4Injector_state: Var = vf.add_var('$PRE.wt.wT4Injector.state_' + template_name)
    START_wt_control4B_pControl4B_firstOrder_y: Var = vf.add_var('$START.wt.control4B.pControl4B.firstOrder.y_' + template_name)
    START_wt_control4B_qControl_derivative_x: Var = vf.add_var('$START.wt.control4B.qControl.derivative.x_' + template_name)
    START_wt_controlMeasurements_derivative_x: Var = vf.add_var('$START.wt.controlMeasurements.derivative.x_' + template_name)
    START_wt_controlMeasurements_firstOrder_y: Var = vf.add_var('$START.wt.controlMeasurements.firstOrder.y_' + template_name)
    START_wt_controlMeasurements_firstOrder1_y: Var = vf.add_var('$START.wt.controlMeasurements.firstOrder1.y_' + template_name)
    START_wt_controlMeasurements_firstOrder2_y: Var = vf.add_var('$START.wt.controlMeasurements.firstOrder2.y_' + template_name)
    START_wt_controlMeasurements_firstOrder3_y: Var = vf.add_var('$START.wt.controlMeasurements.firstOrder3.y_' + template_name)
    START_wt_controlMeasurements_firstOrder4_y: Var = vf.add_var('$START.wt.controlMeasurements.firstOrder4.y_' + template_name)
    START_wt_pll_fixedBooleanDelay_y: Var = vf.add_var('$START.wt.pll.fixedBooleanDelay.y_' + template_name)
    START_wt_pll_fixedBooleanDelay1_y: Var = vf.add_var('$START.wt.pll.fixedBooleanDelay1.y_' + template_name)
    START_wt_protectionMeasurements_derivative_x: Var = vf.add_var('$START.wt.protectionMeasurements.derivative.x_' + template_name)
    START_wt_protectionMeasurements_firstOrder_y: Var = vf.add_var('$START.wt.protectionMeasurements.firstOrder.y_' + template_name)
    START_wt_protectionMeasurements_firstOrder1_y: Var = vf.add_var('$START.wt.protectionMeasurements.firstOrder1.y_' + template_name)
    START_wt_protectionMeasurements_firstOrder2_y: Var = vf.add_var('$START.wt.protectionMeasurements.firstOrder2.y_' + template_name)
    START_wt_protectionMeasurements_firstOrder3_y: Var = vf.add_var('$START.wt.protectionMeasurements.firstOrder3.y_' + template_name)
    START_wt_protectionMeasurements_firstOrder4_y: Var = vf.add_var('$START.wt.protectionMeasurements.firstOrder4.y_' + template_name)
    START_wt_wT4Injector_running_value: Var = vf.add_var('$START.wt.wT4Injector.running.value_' + template_name)
    START_wt_wT4Injector_state: Var = vf.add_var('$START.wt.wT4Injector.state_' + template_name)
    cse1: Var = vf.add_var('$cse1_' + template_name)
    cse2: Var = vf.add_var('$cse2_' + template_name)
    whenCondition1: Var = vf.add_var('$whenCondition1_' + template_name)
    whenCondition10: Var = vf.add_var('$whenCondition10_' + template_name)
    whenCondition11: Var = vf.add_var('$whenCondition11_' + template_name)
    whenCondition12: Var = vf.add_var('$whenCondition12_' + template_name)
    whenCondition13: Var = vf.add_var('$whenCondition13_' + template_name)
    whenCondition14: Var = vf.add_var('$whenCondition14_' + template_name)
    whenCondition15: Var = vf.add_var('$whenCondition15_' + template_name)
    whenCondition16: Var = vf.add_var('$whenCondition16_' + template_name)
    whenCondition2: Var = vf.add_var('$whenCondition2_' + template_name)
    whenCondition3: Var = vf.add_var('$whenCondition3_' + template_name)
    whenCondition4: Var = vf.add_var('$whenCondition4_' + template_name)
    whenCondition5: Var = vf.add_var('$whenCondition5_' + template_name)
    whenCondition6: Var = vf.add_var('$whenCondition6_' + template_name)
    whenCondition7: Var = vf.add_var('$whenCondition7_' + template_name)
    whenCondition8: Var = vf.add_var('$whenCondition8_' + template_name)
    whenCondition9: Var = vf.add_var('$whenCondition9_' + template_name)
    grid_U: Var = vf.add_var('grid.U_' + template_name)
    grid_terminal_V_im: Var = vf.add_var('grid.terminal.V.im_' + template_name)
    grid_terminal_V_re: Var = vf.add_var('grid.terminal.V.re_' + template_name)
    time: Var = vf.add_var('time_' + template_name)
    wt_PWTRefPu: Var = vf.add_var('wt.PWTRefPu_' + template_name)
    wt_control4B_currentLimiter_abs_y: Var = vf.add_var('wt.control4B.currentLimiter.abs.y_' + template_name)
    wt_control4B_currentLimiter_add1_y: Var = vf.add_var('wt.control4B.currentLimiter.add1.y_' + template_name)
    wt_control4B_currentLimiter_combiTable1Ds_y_1: Var = vf.add_var('wt.control4B.currentLimiter.combiTable1Ds.y[1]_' + template_name)
    wt_control4B_currentLimiter_division_y: Var = vf.add_var('wt.control4B.currentLimiter.division.y_' + template_name)
    wt_control4B_currentLimiter_feedback_y: Var = vf.add_var('wt.control4B.currentLimiter.feedback.y_' + template_name)
    wt_control4B_currentLimiter_feedback1_y: Var = vf.add_var('wt.control4B.currentLimiter.feedback1.y_' + template_name)
    wt_control4B_currentLimiter_feedback4_y: Var = vf.add_var('wt.control4B.currentLimiter.feedback4.y_' + template_name)
    wt_control4B_currentLimiter_gain_y: Var = vf.add_var('wt.control4B.currentLimiter.gain.y_' + template_name)
    wt_control4B_currentLimiter_gain1_y: Var = vf.add_var('wt.control4B.currentLimiter.gain1.y_' + template_name)
    wt_control4B_currentLimiter_greater_y: Var = vf.add_var('wt.control4B.currentLimiter.greater.y_' + template_name)
    wt_control4B_currentLimiter_max_y: Var = vf.add_var('wt.control4B.currentLimiter.max.y_' + template_name)
    wt_control4B_currentLimiter_max1_y: Var = vf.add_var('wt.control4B.currentLimiter.max1.y_' + template_name)
    wt_control4B_currentLimiter_max2_y: Var = vf.add_var('wt.control4B.currentLimiter.max2.y_' + template_name)
    wt_control4B_currentLimiter_min_y: Var = vf.add_var('wt.control4B.currentLimiter.min.y_' + template_name)
    wt_control4B_currentLimiter_min3_y: Var = vf.add_var('wt.control4B.currentLimiter.min3.y_' + template_name)
    wt_control4B_currentLimiter_product_y: Var = vf.add_var('wt.control4B.currentLimiter.product.y_' + template_name)
    wt_control4B_currentLimiter_product1_u_2: Var = vf.add_var('wt.control4B.currentLimiter.product1.u[2]_' + template_name)
    wt_control4B_currentLimiter_product1_y: Var = vf.add_var('wt.control4B.currentLimiter.product1.y_' + template_name)
    wt_control4B_currentLimiter_product2_y: Var = vf.add_var('wt.control4B.currentLimiter.product2.y_' + template_name)
    wt_control4B_currentLimiter_product3_y: Var = vf.add_var('wt.control4B.currentLimiter.product3.y_' + template_name)
    wt_control4B_currentLimiter_sqrtNoEvent_y: Var = vf.add_var('wt.control4B.currentLimiter.sqrtNoEvent.y_' + template_name)
    wt_control4B_currentLimiter_sqrtNoEvent1_y: Var = vf.add_var('wt.control4B.currentLimiter.sqrtNoEvent1.y_' + template_name)
    wt_control4B_currentLimiter_switch_y: Var = vf.add_var('wt.control4B.currentLimiter.switch.y_' + template_name)
    wt_control4B_currentLimiter_switch1_u: Var = vf.add_var('wt.control4B.currentLimiter.switch1.u_' + template_name)
    wt_control4B_currentLimiter_switch1_u_1: Var = vf.add_var('wt.control4B.currentLimiter.switch1.u[1]_' + template_name)
    wt_control4B_currentLimiter_switch1_u_2: Var = vf.add_var('wt.control4B.currentLimiter.switch1.u[2]_' + template_name)
    wt_control4B_currentLimiter_switch1_u_3: Var = vf.add_var('wt.control4B.currentLimiter.switch1.u[3]_' + template_name)
    wt_control4B_currentLimiter_switch2_u: Var = vf.add_var('wt.control4B.currentLimiter.switch2.u_' + template_name)
    wt_control4B_currentLimiter_switch2_u_1: Var = vf.add_var('wt.control4B.currentLimiter.switch2.u[1]_' + template_name)
    wt_control4B_currentLimiter_switch2_u_2: Var = vf.add_var('wt.control4B.currentLimiter.switch2.u[2]_' + template_name)
    wt_control4B_currentLimiter_switch2_u_3: Var = vf.add_var('wt.control4B.currentLimiter.switch2.u[3]_' + template_name)
    wt_control4B_currentLimiter_switch2_y: Var = vf.add_var('wt.control4B.currentLimiter.switch2.y_' + template_name)
    wt_control4B_currentLimiter_switch4_u: Var = vf.add_var('wt.control4B.currentLimiter.switch4.u_' + template_name)
    wt_control4B_currentLimiter_switch4_u_1: Var = vf.add_var('wt.control4B.currentLimiter.switch4.u[1]_' + template_name)
    wt_control4B_currentLimiter_switch4_u_2: Var = vf.add_var('wt.control4B.currentLimiter.switch4.u[2]_' + template_name)
    wt_control4B_currentLimiter_switch4_u_3: Var = vf.add_var('wt.control4B.currentLimiter.switch4.u[3]_' + template_name)
    wt_control4B_currentLimiter_switch4_y: Var = vf.add_var('wt.control4B.currentLimiter.switch4.y_' + template_name)
    wt_control4B_ipCmdPu: Var = vf.add_var('wt.control4B.ipCmdPu_' + template_name)
    wt_control4B_ipMaxPu: Var = vf.add_var('wt.control4B.ipMaxPu_' + template_name)
    wt_control4B_iqCmdPu: Var = vf.add_var('wt.control4B.iqCmdPu_' + template_name)
    wt_control4B_iqMaxPu: Var = vf.add_var('wt.control4B.iqMaxPu_' + template_name)
    wt_control4B_iqMinPu: Var = vf.add_var('wt.control4B.iqMinPu_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_y: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.add.y_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_feedback_y: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.feedback.y_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_feedback1_y: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.feedback1.y_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_y: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.gain.y_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_local_reset: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.integrator.local_reset_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_local_set: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.integrator.local_set_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.limiter.simplifiedExpr_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_y: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.limiter.y_' + template_name)
    wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_y: Var = vf.add_var('wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.y_' + template_name)
    wt_control4B_pControl4B_and1_y: Var = vf.add_var('wt.control4B.pControl4B.and1.y_' + template_name)
    wt_control4B_pControl4B_less_y: Var = vf.add_var('wt.control4B.pControl4B.less.y_' + template_name)
    wt_control4B_pControl4B_max_y: Var = vf.add_var('wt.control4B.pControl4B.max.y_' + template_name)
    wt_control4B_pControl4B_product_y: Var = vf.add_var('wt.control4B.pControl4B.product.y_' + template_name)
    wt_control4B_pControl4B_product1_y: Var = vf.add_var('wt.control4B.pControl4B.product1.y_' + template_name)
    wt_control4B_pControl4B_product2_y: Var = vf.add_var('wt.control4B.pControl4B.product2.y_' + template_name)
    wt_control4B_pControl4B_rampLimiter_feedback_y: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.feedback.y_' + template_name)
    wt_control4B_pControl4B_rampLimiter_gain_y: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.gain.y_' + template_name)
    wt_control4B_pControl4B_rampLimiter_integrator_local_reset: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.integrator.local_reset_' + template_name)
    wt_control4B_pControl4B_rampLimiter_integrator_local_set: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.integrator.local_set_' + template_name)
    wt_control4B_pControl4B_rampLimiter_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.limiter.simplifiedExpr_' + template_name)
    wt_control4B_pControl4B_rampLimiter_limiter_y: Var = vf.add_var('wt.control4B.pControl4B.rampLimiter.limiter.y_' + template_name)
    wt_control4B_pControl4B_switch1_y: Var = vf.add_var('wt.control4B.pControl4B.switch1.y_' + template_name)
    wt_control4B_qControl_abs_y: Var = vf.add_var('wt.control4B.qControl.abs.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_fixedDelay_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.fixedDelay.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.limiter.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_feedback_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.feedback.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.gain.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_reset: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.local_reset_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_set: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.local_set_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFeedthroughFreeze_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFeedthroughFreeze.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_feedback_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.feedback.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.gain.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_local_reset: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.integrator.local_reset_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_local_set: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.integrator.local_set_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.limiter.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_switch1_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.switch1.y_' + template_name)
    wt_control4B_qControl_absLimRateLimFirstOrderFreeze_y: Var = vf.add_var('wt.control4B.qControl.absLimRateLimFirstOrderFreeze.y_' + template_name)
    wt_control4B_qControl_add1_y: Var = vf.add_var('wt.control4B.qControl.add1.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_gain_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.gain.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_integrator_local_reset: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.integrator.local_reset_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_integrator_local_set: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.integrator.local_set_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_limiter1_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.limiter1.simplifiedExpr_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_max_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.max.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_min_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.min.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_switch1_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.switch1.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_switch2_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.switch2.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_gain_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.gain.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_integrator_local_reset: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.integrator.local_reset_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_integrator_local_set: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.integrator.local_set_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_limiter1_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.limiter1.simplifiedExpr_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_max_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.max.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_min_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.min.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_switch1_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.switch1.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_switch2_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.switch2.y_' + template_name)
    wt_control4B_qControl_antiWindupIntegrator1_y: Var = vf.add_var('wt.control4B.qControl.antiWindupIntegrator1.y_' + template_name)
    wt_control4B_qControl_booleanToInteger_y: Var = vf.add_var('wt.control4B.qControl.booleanToInteger.y_' + template_name)
    wt_control4B_qControl_deadZone_y: Var = vf.add_var('wt.control4B.qControl.deadZone.y_' + template_name)
    wt_control4B_qControl_delayFlag_booleanToInteger_y: Var = vf.add_var('wt.control4B.qControl.delayFlag.booleanToInteger.y_' + template_name)
    wt_control4B_qControl_delayFlag_fI: Var = vf.add_var('wt.control4B.qControl.delayFlag.fI_' + template_name)
    wt_control4B_qControl_delayFlag_fO: Var = vf.add_var('wt.control4B.qControl.delayFlag.fO_' + template_name)
    wt_control4B_qControl_delayFlag_fixedDelay_y: Var = vf.add_var('wt.control4B.qControl.delayFlag.fixedDelay.y_' + template_name)
    wt_control4B_qControl_delayFlag_less1_y: Var = vf.add_var('wt.control4B.qControl.delayFlag.less1.y_' + template_name)
    wt_control4B_qControl_delayFlag_switch1_y: Var = vf.add_var('wt.control4B.qControl.delayFlag.switch1.y_' + template_name)
    wt_control4B_qControl_delayFlag_switch18_y: Var = vf.add_var('wt.control4B.qControl.delayFlag.switch18.y_' + template_name)
    wt_control4B_qControl_delayFlag_timer_entryTime: Var = vf.add_var('wt.control4B.qControl.delayFlag.timer.entryTime_' + template_name)
    wt_control4B_qControl_delayFlag_timer_y: Var = vf.add_var('wt.control4B.qControl.delayFlag.timer.y_' + template_name)
    wt_control4B_qControl_derivative_y: Var = vf.add_var('wt.control4B.qControl.derivative.y_' + template_name)
    wt_control4B_qControl_division_y: Var = vf.add_var('wt.control4B.qControl.division.y_' + template_name)
    wt_control4B_qControl_division1_y: Var = vf.add_var('wt.control4B.qControl.division1.y_' + template_name)
    wt_control4B_qControl_division2_y: Var = vf.add_var('wt.control4B.qControl.division2.y_' + template_name)
    wt_control4B_qControl_fFrt: Var = vf.add_var('wt.control4B.qControl.fFrt_' + template_name)
    wt_control4B_qControl_feedback_y: Var = vf.add_var('wt.control4B.qControl.feedback.y_' + template_name)
    wt_control4B_qControl_feedback1_y: Var = vf.add_var('wt.control4B.qControl.feedback1.y_' + template_name)
    wt_control4B_qControl_gain_y: Var = vf.add_var('wt.control4B.qControl.gain.y_' + template_name)
    wt_control4B_qControl_gain1_y: Var = vf.add_var('wt.control4B.qControl.gain1.y_' + template_name)
    wt_control4B_qControl_gain2_y: Var = vf.add_var('wt.control4B.qControl.gain2.y_' + template_name)
    wt_control4B_qControl_gain5_y: Var = vf.add_var('wt.control4B.qControl.gain5.y_' + template_name)
    wt_control4B_qControl_gain6_y: Var = vf.add_var('wt.control4B.qControl.gain6.y_' + template_name)
    wt_control4B_qControl_greaterEqualThreshold_y: Var = vf.add_var('wt.control4B.qControl.greaterEqualThreshold.y_' + template_name)
    wt_control4B_qControl_greaterThreshold_y: Var = vf.add_var('wt.control4B.qControl.greaterThreshold.y_' + template_name)
    wt_control4B_qControl_integerToReal_y: Var = vf.add_var('wt.control4B.qControl.integerToReal.y_' + template_name)
    wt_control4B_qControl_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qControl_limiter_y: Var = vf.add_var('wt.control4B.qControl.limiter.y_' + template_name)
    wt_control4B_qControl_limiter2_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.limiter2.simplifiedExpr_' + template_name)
    wt_control4B_qControl_limiter3_simplifiedExpr: Var = vf.add_var('wt.control4B.qControl.limiter3.simplifiedExpr_' + template_name)
    wt_control4B_qControl_max_y: Var = vf.add_var('wt.control4B.qControl.max.y_' + template_name)
    wt_control4B_qControl_switch_u: Var = vf.add_var('wt.control4B.qControl.switch.u_' + template_name)
    wt_control4B_qControl_switch_u_1: Var = vf.add_var('wt.control4B.qControl.switch.u[1]_' + template_name)
    wt_control4B_qControl_switch_u_2: Var = vf.add_var('wt.control4B.qControl.switch.u[2]_' + template_name)
    wt_control4B_qControl_switch_u_3: Var = vf.add_var('wt.control4B.qControl.switch.u[3]_' + template_name)
    wt_control4B_qControl_switch_u_4: Var = vf.add_var('wt.control4B.qControl.switch.u[4]_' + template_name)
    wt_control4B_qControl_switch_u_5: Var = vf.add_var('wt.control4B.qControl.switch.u[5]_' + template_name)
    wt_control4B_qControl_switch_y: Var = vf.add_var('wt.control4B.qControl.switch.y_' + template_name)
    wt_control4B_qControl_switch1_y: Var = vf.add_var('wt.control4B.qControl.switch1.y_' + template_name)
    wt_control4B_qControl_switch2_u: Var = vf.add_var('wt.control4B.qControl.switch2.u_' + template_name)
    wt_control4B_qControl_switch2_u_1: Var = vf.add_var('wt.control4B.qControl.switch2.u[1]_' + template_name)
    wt_control4B_qControl_switch2_u_2: Var = vf.add_var('wt.control4B.qControl.switch2.u[2]_' + template_name)
    wt_control4B_qControl_switch2_u_3: Var = vf.add_var('wt.control4B.qControl.switch2.u[3]_' + template_name)
    wt_control4B_qControl_switch2_u_4: Var = vf.add_var('wt.control4B.qControl.switch2.u[4]_' + template_name)
    wt_control4B_qControl_switch2_u_5: Var = vf.add_var('wt.control4B.qControl.switch2.u[5]_' + template_name)
    wt_control4B_qControl_switch2_y: Var = vf.add_var('wt.control4B.qControl.switch2.y_' + template_name)
    wt_control4B_qControl_switch4_u: Var = vf.add_var('wt.control4B.qControl.switch4.u_' + template_name)
    wt_control4B_qControl_switch4_u_1: Var = vf.add_var('wt.control4B.qControl.switch4.u[1]_' + template_name)
    wt_control4B_qControl_switch4_u_2: Var = vf.add_var('wt.control4B.qControl.switch4.u[2]_' + template_name)
    wt_control4B_qControl_switch4_u_3: Var = vf.add_var('wt.control4B.qControl.switch4.u[3]_' + template_name)
    wt_control4B_qControl_switch4_u_4: Var = vf.add_var('wt.control4B.qControl.switch4.u[4]_' + template_name)
    wt_control4B_qControl_switch4_u_5: Var = vf.add_var('wt.control4B.qControl.switch4.u[5]_' + template_name)
    wt_control4B_qControl_switch6_u: Var = vf.add_var('wt.control4B.qControl.switch6.u_' + template_name)
    wt_control4B_qControl_switch6_u_1: Var = vf.add_var('wt.control4B.qControl.switch6.u[1]_' + template_name)
    wt_control4B_qControl_switch6_u_2: Var = vf.add_var('wt.control4B.qControl.switch6.u[2]_' + template_name)
    wt_control4B_qControl_switch6_u_3: Var = vf.add_var('wt.control4B.qControl.switch6.u[3]_' + template_name)
    wt_control4B_qControl_switch6_u_4: Var = vf.add_var('wt.control4B.qControl.switch6.u[4]_' + template_name)
    wt_control4B_qControl_switch7_u: Var = vf.add_var('wt.control4B.qControl.switch7.u_' + template_name)
    wt_control4B_qControl_switch7_u_1: Var = vf.add_var('wt.control4B.qControl.switch7.u[1]_' + template_name)
    wt_control4B_qControl_switch7_u_2: Var = vf.add_var('wt.control4B.qControl.switch7.u[2]_' + template_name)
    wt_control4B_qControl_switch7_u_3: Var = vf.add_var('wt.control4B.qControl.switch7.u[3]_' + template_name)
    wt_control4B_qControl_switch8_u: Var = vf.add_var('wt.control4B.qControl.switch8.u_' + template_name)
    wt_control4B_qControl_switch8_u_1: Var = vf.add_var('wt.control4B.qControl.switch8.u[1]_' + template_name)
    wt_control4B_qControl_switch8_u_2: Var = vf.add_var('wt.control4B.qControl.switch8.u[2]_' + template_name)
    wt_control4B_qControl_switch8_u_3: Var = vf.add_var('wt.control4B.qControl.switch8.u[3]_' + template_name)
    wt_control4B_qControl_switch8_u_4: Var = vf.add_var('wt.control4B.qControl.switch8.u[4]_' + template_name)
    wt_control4B_qControl_switch8_y: Var = vf.add_var('wt.control4B.qControl.switch8.y_' + template_name)
    wt_control4B_qControl_vDrop_UDropPu: Var = vf.add_var('wt.control4B.qControl.vDrop.UDropPu_' + template_name)
    wt_control4B_qControl_variableLimiter_y: Var = vf.add_var('wt.control4B.qControl.variableLimiter.y_' + template_name)
    wt_control4B_qControl_variableLimiter1_y: Var = vf.add_var('wt.control4B.qControl.variableLimiter1.y_' + template_name)
    wt_control4B_qLimiter_QWTMaxPu: Var = vf.add_var('wt.control4B.qLimiter.QWTMaxPu_' + template_name)
    wt_control4B_qLimiter_QWTMinPu: Var = vf.add_var('wt.control4B.qLimiter.QWTMinPu_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_fixedDelay_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.fixedDelay.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.limiter.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_feedback_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.feedback.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.gain.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_reset: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.local_reset_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_set: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.local_set_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.limiter.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_fixedDelay_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.fixedDelay.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.limiter.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_feedback_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.feedback.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.gain.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_local_reset: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.integrator.local_reset_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_local_set: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.integrator.local_set_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_simplifiedExpr: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.limiter.simplifiedExpr_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.limiter.y_' + template_name)
    wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y: Var = vf.add_var('wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.y_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds_y_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds.y[1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds1_y_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds1.y[1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds2_y_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds2.y[1]_' + template_name)
    wt_control4B_qLimiter_combiTable1Ds3_y_1: Var = vf.add_var('wt.control4B.qLimiter.combiTable1Ds3.y[1]_' + template_name)
    wt_control4B_qLimiter_integerToBoolean_y: Var = vf.add_var('wt.control4B.qLimiter.integerToBoolean.y_' + template_name)
    wt_control4B_qLimiter_max_y: Var = vf.add_var('wt.control4B.qLimiter.max.y_' + template_name)
    wt_control4B_qLimiter_min_y: Var = vf.add_var('wt.control4B.qLimiter.min.y_' + template_name)
    wt_controlMeasurements_IWtPu: Var = vf.add_var('wt.controlMeasurements.IWtPu_' + template_name)
    wt_controlMeasurements_PPu: Var = vf.add_var('wt.controlMeasurements.PPu_' + template_name)
    wt_controlMeasurements_PPuSnRef: Var = vf.add_var('wt.controlMeasurements.PPuSnRef_' + template_name)
    wt_controlMeasurements_QPu: Var = vf.add_var('wt.controlMeasurements.QPu_' + template_name)
    wt_controlMeasurements_QPuSnRef: Var = vf.add_var('wt.controlMeasurements.QPuSnRef_' + template_name)
    wt_controlMeasurements_UPu: Var = vf.add_var('wt.controlMeasurements.UPu_' + template_name)
    wt_controlMeasurements_UWtPu: Var = vf.add_var('wt.controlMeasurements.UWtPu_' + template_name)
    wt_controlMeasurements_complexToPolar_len: Var = vf.add_var('wt.controlMeasurements.complexToPolar.len_' + template_name)
    wt_controlMeasurements_complexToPolar_phi: Var = vf.add_var('wt.controlMeasurements.complexToPolar.phi_' + template_name)
    wt_controlMeasurements_complexToReal_im: Var = vf.add_var('wt.controlMeasurements.complexToReal.im_' + template_name)
    wt_controlMeasurements_complexToReal_re: Var = vf.add_var('wt.controlMeasurements.complexToReal.re_' + template_name)
    wt_controlMeasurements_derivative_y: Var = vf.add_var('wt.controlMeasurements.derivative.y_' + template_name)
    wt_controlMeasurements_iPu_im: Var = vf.add_var('wt.controlMeasurements.iPu.im_' + template_name)
    wt_controlMeasurements_iPu_re: Var = vf.add_var('wt.controlMeasurements.iPu.re_' + template_name)
    wt_controlMeasurements_omegaFiltPu: Var = vf.add_var('wt.controlMeasurements.omegaFiltPu_' + template_name)
    wt_controlMeasurements_product_y_im: Var = vf.add_var('wt.controlMeasurements.product.y.im_' + template_name)
    wt_controlMeasurements_rampLimiter_feedback_y: Var = vf.add_var('wt.controlMeasurements.rampLimiter.feedback.y_' + template_name)
    wt_controlMeasurements_rampLimiter_gain_y: Var = vf.add_var('wt.controlMeasurements.rampLimiter.gain.y_' + template_name)
    wt_controlMeasurements_rampLimiter_integrator_local_reset: Var = vf.add_var('wt.controlMeasurements.rampLimiter.integrator.local_reset_' + template_name)
    wt_controlMeasurements_rampLimiter_integrator_local_set: Var = vf.add_var('wt.controlMeasurements.rampLimiter.integrator.local_set_' + template_name)
    wt_controlMeasurements_rampLimiter_limiter_simplifiedExpr: Var = vf.add_var('wt.controlMeasurements.rampLimiter.limiter.simplifiedExpr_' + template_name)
    wt_controlMeasurements_rampLimiter_limiter_y: Var = vf.add_var('wt.controlMeasurements.rampLimiter.limiter.y_' + template_name)
    wt_controlMeasurements_theta: Var = vf.add_var('wt.controlMeasurements.theta_' + template_name)
    wt_gridProtection_combiTable1D_y_1: Var = vf.add_var('wt.gridProtection.combiTable1D.y[1]_' + template_name)
    wt_gridProtection_combiTable1D1_y_1: Var = vf.add_var('wt.gridProtection.combiTable1D1.y[1]_' + template_name)
    wt_gridProtection_combiTable1D2_y_1: Var = vf.add_var('wt.gridProtection.combiTable1D2.y[1]_' + template_name)
    wt_gridProtection_combiTable1D3_y_1: Var = vf.add_var('wt.gridProtection.combiTable1D3.y[1]_' + template_name)
    wt_gridProtection_lessEqual_y: Var = vf.add_var('wt.gridProtection.lessEqual.y_' + template_name)
    wt_gridProtection_lessEqual1_y: Var = vf.add_var('wt.gridProtection.lessEqual1.y_' + template_name)
    wt_gridProtection_lessEqual2_y: Var = vf.add_var('wt.gridProtection.lessEqual2.y_' + template_name)
    wt_gridProtection_lessEqual3_y: Var = vf.add_var('wt.gridProtection.lessEqual3.y_' + template_name)
    wt_gridProtection_or1_u_1: Var = vf.add_var('wt.gridProtection.or1.u[1]_' + template_name)
    wt_gridProtection_or1_u_2: Var = vf.add_var('wt.gridProtection.or1.u[2]_' + template_name)
    wt_gridProtection_or1_u_3: Var = vf.add_var('wt.gridProtection.or1.u[3]_' + template_name)
    wt_gridProtection_or1_u_4: Var = vf.add_var('wt.gridProtection.or1.u[4]_' + template_name)
    wt_gridProtection_or1_u_5: Var = vf.add_var('wt.gridProtection.or1.u[5]_' + template_name)
    wt_gridProtection_pre1_u: Var = vf.add_var('wt.gridProtection.pre1.u_' + template_name)
    wt_gridProtection_timer_entryTime: Var = vf.add_var('wt.gridProtection.timer.entryTime_' + template_name)
    wt_gridProtection_timer_y: Var = vf.add_var('wt.gridProtection.timer.y_' + template_name)
    wt_gridProtection_timer1_entryTime: Var = vf.add_var('wt.gridProtection.timer1.entryTime_' + template_name)
    wt_gridProtection_timer1_y: Var = vf.add_var('wt.gridProtection.timer1.y_' + template_name)
    wt_gridProtection_timer2_entryTime: Var = vf.add_var('wt.gridProtection.timer2.entryTime_' + template_name)
    wt_gridProtection_timer2_y: Var = vf.add_var('wt.gridProtection.timer2.y_' + template_name)
    wt_gridProtection_timer3_entryTime: Var = vf.add_var('wt.gridProtection.timer3.entryTime_' + template_name)
    wt_gridProtection_timer3_y: Var = vf.add_var('wt.gridProtection.timer3.y_' + template_name)
    wt_mechanical_add_y: Var = vf.add_var('wt.mechanical.add.y_' + template_name)
    wt_mechanical_add1_y: Var = vf.add_var('wt.mechanical.add1.y_' + template_name)
    wt_mechanical_add2_y: Var = vf.add_var('wt.mechanical.add2.y_' + template_name)
    wt_mechanical_division_y: Var = vf.add_var('wt.mechanical.division.y_' + template_name)
    wt_mechanical_division1_y: Var = vf.add_var('wt.mechanical.division1.y_' + template_name)
    wt_mechanical_integrator_local_reset: Var = vf.add_var('wt.mechanical.integrator.local_reset_' + template_name)
    wt_mechanical_integrator_local_set: Var = vf.add_var('wt.mechanical.integrator.local_set_' + template_name)
    wt_mechanical_integrator1_local_reset: Var = vf.add_var('wt.mechanical.integrator1.local_reset_' + template_name)
    wt_mechanical_integrator1_local_set: Var = vf.add_var('wt.mechanical.integrator1.local_set_' + template_name)
    wt_mechanical_pI_integrator_local_reset: Var = vf.add_var('wt.mechanical.pI.integrator.local_reset_' + template_name)
    wt_mechanical_pI_integrator_local_set: Var = vf.add_var('wt.mechanical.pI.integrator.local_set_' + template_name)
    wt_mechanical_pI_y: Var = vf.add_var('wt.mechanical.pI.y_' + template_name)
    wt_omegaRefPu: Var = vf.add_var('wt.omegaRefPu_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_feedback_y: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.feedback.y_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_gain_y: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.gain.y_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_integrator_local_reset: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.integrator.local_reset_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_integrator_local_set: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.integrator.local_set_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_limiter_simplifiedExpr: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.limiter.simplifiedExpr_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_limiter_y: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.limiter.y_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_switch1_y: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.switch1.y_' + template_name)
    wt_pll_absLimRateLimFirstOrderFreeze_y: Var = vf.add_var('wt.pll.absLimRateLimFirstOrderFreeze.y_' + template_name)
    wt_pll_fixedBooleanDelay_uReal: Var = vf.add_var('wt.pll.fixedBooleanDelay.uReal_' + template_name)
    wt_pll_fixedBooleanDelay_y: Var = vf.add_var('wt.pll.fixedBooleanDelay.y_' + template_name)
    wt_pll_fixedBooleanDelay_yReal: Var = vf.add_var('wt.pll.fixedBooleanDelay.yReal_' + template_name)
    wt_pll_fixedBooleanDelay1_uReal: Var = vf.add_var('wt.pll.fixedBooleanDelay1.uReal_' + template_name)
    wt_pll_fixedBooleanDelay1_y: Var = vf.add_var('wt.pll.fixedBooleanDelay1.y_' + template_name)
    wt_pll_fixedBooleanDelay1_yReal: Var = vf.add_var('wt.pll.fixedBooleanDelay1.yReal_' + template_name)
    wt_pll_lessThreshold_y: Var = vf.add_var('wt.pll.lessThreshold.y_' + template_name)
    wt_pll_lessThreshold1_y: Var = vf.add_var('wt.pll.lessThreshold1.y_' + template_name)
    wt_pll_thetaPll: Var = vf.add_var('wt.pll.thetaPll_' + template_name)
    wt_protectionMeasurements_IWtPu: Var = vf.add_var('wt.protectionMeasurements.IWtPu_' + template_name)
    wt_protectionMeasurements_PPu: Var = vf.add_var('wt.protectionMeasurements.PPu_' + template_name)
    wt_protectionMeasurements_PPuSnRef: Var = vf.add_var('wt.protectionMeasurements.PPuSnRef_' + template_name)
    wt_protectionMeasurements_QPu: Var = vf.add_var('wt.protectionMeasurements.QPu_' + template_name)
    wt_protectionMeasurements_QPuSnRef: Var = vf.add_var('wt.protectionMeasurements.QPuSnRef_' + template_name)
    wt_protectionMeasurements_UPu: Var = vf.add_var('wt.protectionMeasurements.UPu_' + template_name)
    wt_protectionMeasurements_UWtPu: Var = vf.add_var('wt.protectionMeasurements.UWtPu_' + template_name)
    wt_protectionMeasurements_complexToPolar_len: Var = vf.add_var('wt.protectionMeasurements.complexToPolar.len_' + template_name)
    wt_protectionMeasurements_complexToPolar_phi: Var = vf.add_var('wt.protectionMeasurements.complexToPolar.phi_' + template_name)
    wt_protectionMeasurements_complexToReal_im: Var = vf.add_var('wt.protectionMeasurements.complexToReal.im_' + template_name)
    wt_protectionMeasurements_complexToReal_re: Var = vf.add_var('wt.protectionMeasurements.complexToReal.re_' + template_name)
    wt_protectionMeasurements_derivative_y: Var = vf.add_var('wt.protectionMeasurements.derivative.y_' + template_name)
    wt_protectionMeasurements_omegaFiltPu: Var = vf.add_var('wt.protectionMeasurements.omegaFiltPu_' + template_name)
    wt_protectionMeasurements_product_y_im: Var = vf.add_var('wt.protectionMeasurements.product.y.im_' + template_name)
    wt_protectionMeasurements_rampLimiter_feedback_y: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.feedback.y_' + template_name)
    wt_protectionMeasurements_rampLimiter_gain_y: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.gain.y_' + template_name)
    wt_protectionMeasurements_rampLimiter_integrator_local_reset: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.integrator.local_reset_' + template_name)
    wt_protectionMeasurements_rampLimiter_integrator_local_set: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.integrator.local_set_' + template_name)
    wt_protectionMeasurements_rampLimiter_limiter_simplifiedExpr: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.limiter.simplifiedExpr_' + template_name)
    wt_protectionMeasurements_rampLimiter_limiter_y: Var = vf.add_var('wt.protectionMeasurements.rampLimiter.limiter.y_' + template_name)
    wt_protectionMeasurements_theta: Var = vf.add_var('wt.protectionMeasurements.theta_' + template_name)
    wt_tanPhi: Var = vf.add_var('wt.tanPhi_' + template_name)
    wt_terminal_i_im: Var = vf.add_var('wt.terminal.i.im_' + template_name)
    wt_terminal_i_re: Var = vf.add_var('wt.terminal.i.re_' + template_name)
    wt_wT4Injector_PAgPu: Var = vf.add_var('wt.wT4Injector.PAgPu_' + template_name)
    wt_wT4Injector_PGenPu: Var = vf.add_var('wt.wT4Injector.PGenPu_' + template_name)
    wt_wT4Injector_QGenPu: Var = vf.add_var('wt.wT4Injector.QGenPu_' + template_name)
    wt_wT4Injector_elecSystem_IGsPu: Var = vf.add_var('wt.wT4Injector.elecSystem.IGsPu_' + template_name)
    wt_wT4Injector_elecSystem_UGsPu: Var = vf.add_var('wt.wT4Injector.elecSystem.UGsPu_' + template_name)
    wt_wT4Injector_elecSystem_iGsImPu: Var = vf.add_var('wt.wT4Injector.elecSystem.iGsImPu_' + template_name)
    wt_wT4Injector_elecSystem_iGsRePu: Var = vf.add_var('wt.wT4Injector.elecSystem.iGsRePu_' + template_name)
    wt_wT4Injector_elecSystem_uGsImPu: Var = vf.add_var('wt.wT4Injector.elecSystem.uGsImPu_' + template_name)
    wt_wT4Injector_elecSystem_uGsRePu: Var = vf.add_var('wt.wT4Injector.elecSystem.uGsRePu_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.add.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_feedback_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.feedback.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_feedback1_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.feedback1.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.gain.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_reset: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.local_reset_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_set: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.local_set_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_simplifiedExpr: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.simplifiedExpr_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.limiter.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.add.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.feedback.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback1_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.feedback1.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.gain.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_reset: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.local_reset_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_set: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.local_set_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_simplifiedExpr: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.simplifiedExpr_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.limiter.y_' + template_name)
    wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y: Var = vf.add_var('wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.y_' + template_name)
    wt_wT4Injector_genSystem_complexToReal_im: Var = vf.add_var('wt.wT4Injector.genSystem.complexToReal.im_' + template_name)
    wt_wT4Injector_genSystem_product_u2_im: Var = vf.add_var('wt.wT4Injector.genSystem.product.u2.im_' + template_name)
    wt_wT4Injector_genSystem_product_u2_re: Var = vf.add_var('wt.wT4Injector.genSystem.product.u2.re_' + template_name)
    wt_wT4Injector_genSystem_product_y_im: Var = vf.add_var('wt.wT4Injector.genSystem.product.y.im_' + template_name)
    wt_wT4Injector_genSystem_realToComplex_im: Var = vf.add_var('wt.wT4Injector.genSystem.realToComplex.im_' + template_name)
    wt_wT4Injector_genSystem_realToComplex_re: Var = vf.add_var('wt.wT4Injector.genSystem.realToComplex.re_' + template_name)
    wt_wT4Injector_genSystem_terminal_i_im: Var = vf.add_var('wt.wT4Injector.genSystem.terminal.i.im_' + template_name)
    wt_wT4Injector_genSystem_terminal_i_re: Var = vf.add_var('wt.wT4Injector.genSystem.terminal.i.re_' + template_name)
    wt_wT4Injector_running_value: Var = vf.add_var('wt.wT4Injector.running.value_' + template_name)
    wt_wT4Injector_state: Var = vf.add_var('wt.wT4Injector.state_' + template_name)
    wt_wT4Injector_switchOffSignal1_value: Var = vf.add_var('wt.wT4Injector.switchOffSignal1.value_' + template_name)
    wt_wT4Injector_switchOffSignal2_value: Var = vf.add_var('wt.wT4Injector.switchOffSignal2.value_' + template_name)
    wt_wT4Injector_switchOffSignal3_value: Var = vf.add_var('wt.wT4Injector.switchOffSignal3.value_' + template_name)
    wt_xWTRefPu: Var = vf.add_var('wt.xWTRefPu_' + template_name)
    # Declare the differential variables used by the template.
    d_wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y: Var = vf.add_diff_var('d_wt.control4B.pControl4B.absLimRateLimFirstOrderAntiWindup.integrator.y_' + template_name, base_var=wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y)
    d_wt_control4B_pControl4B_firstOrder_y: Var = vf.add_diff_var('d_wt.control4B.pControl4B.firstOrder.y_' + template_name, base_var=wt_control4B_pControl4B_firstOrder_y)
    d_wt_control4B_pControl4B_rampLimiter_integrator_y: Var = vf.add_diff_var('d_wt.control4B.pControl4B.rampLimiter.integrator.y_' + template_name, base_var=wt_control4B_pControl4B_rampLimiter_integrator_y)
    d_wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y: Var = vf.add_diff_var('d_wt.control4B.qControl.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.y_' + template_name, base_var=wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y)
    d_wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y: Var = vf.add_diff_var('d_wt.control4B.qControl.absLimRateLimFirstOrderFreeze.integrator.y_' + template_name, base_var=wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y)
    d_wt_control4B_qControl_antiWindupIntegrator_integrator_y: Var = vf.add_diff_var('d_wt.control4B.qControl.antiWindupIntegrator.integrator.y_' + template_name, base_var=wt_control4B_qControl_antiWindupIntegrator_integrator_y)
    d_wt_control4B_qControl_antiWindupIntegrator1_integrator_y: Var = vf.add_diff_var('d_wt.control4B.qControl.antiWindupIntegrator1.integrator.y_' + template_name, base_var=wt_control4B_qControl_antiWindupIntegrator1_integrator_y)
    d_wt_control4B_qControl_derivative_x: Var = vf.add_diff_var('d_wt.control4B.qControl.derivative.x_' + template_name, base_var=wt_control4B_qControl_derivative_x)
    d_wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y: Var = vf.add_diff_var('d_wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze.rampLimiter.integrator.y_' + template_name, base_var=wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y)
    d_wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y: Var = vf.add_diff_var('d_wt.control4B.qLimiter.absLimRateLimFeedthroughFreeze1.rampLimiter.integrator.y_' + template_name, base_var=wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y)
    d_wt_controlMeasurements_derivative_x: Var = vf.add_diff_var('d_wt.controlMeasurements.derivative.x_' + template_name, base_var=wt_controlMeasurements_derivative_x)
    d_wt_controlMeasurements_firstOrder_y: Var = vf.add_diff_var('d_wt.controlMeasurements.firstOrder.y_' + template_name, base_var=wt_controlMeasurements_firstOrder_y)
    d_wt_controlMeasurements_firstOrder1_y: Var = vf.add_diff_var('d_wt.controlMeasurements.firstOrder1.y_' + template_name, base_var=wt_controlMeasurements_firstOrder1_y)
    d_wt_controlMeasurements_firstOrder2_y: Var = vf.add_diff_var('d_wt.controlMeasurements.firstOrder2.y_' + template_name, base_var=wt_controlMeasurements_firstOrder2_y)
    d_wt_controlMeasurements_firstOrder3_y: Var = vf.add_diff_var('d_wt.controlMeasurements.firstOrder3.y_' + template_name, base_var=wt_controlMeasurements_firstOrder3_y)
    d_wt_controlMeasurements_firstOrder4_y: Var = vf.add_diff_var('d_wt.controlMeasurements.firstOrder4.y_' + template_name, base_var=wt_controlMeasurements_firstOrder4_y)
    d_wt_controlMeasurements_rampLimiter_integrator_y: Var = vf.add_diff_var('d_wt.controlMeasurements.rampLimiter.integrator.y_' + template_name, base_var=wt_controlMeasurements_rampLimiter_integrator_y)
    d_wt_mechanical_integrator_y: Var = vf.add_diff_var('d_wt.mechanical.integrator.y_' + template_name, base_var=wt_mechanical_integrator_y)
    d_wt_mechanical_integrator1_y: Var = vf.add_diff_var('d_wt.mechanical.integrator1.y_' + template_name, base_var=wt_mechanical_integrator1_y)
    d_wt_mechanical_pI_integrator_y: Var = vf.add_diff_var('d_wt.mechanical.pI.integrator.y_' + template_name, base_var=wt_mechanical_pI_integrator_y)
    d_wt_pll_absLimRateLimFirstOrderFreeze_integrator_y: Var = vf.add_diff_var('d_wt.pll.absLimRateLimFirstOrderFreeze.integrator.y_' + template_name, base_var=wt_pll_absLimRateLimFirstOrderFreeze_integrator_y)
    d_wt_protectionMeasurements_derivative_x: Var = vf.add_diff_var('d_wt.protectionMeasurements.derivative.x_' + template_name, base_var=wt_protectionMeasurements_derivative_x)
    d_wt_protectionMeasurements_firstOrder_y: Var = vf.add_diff_var('d_wt.protectionMeasurements.firstOrder.y_' + template_name, base_var=wt_protectionMeasurements_firstOrder_y)
    d_wt_protectionMeasurements_firstOrder1_y: Var = vf.add_diff_var('d_wt.protectionMeasurements.firstOrder1.y_' + template_name, base_var=wt_protectionMeasurements_firstOrder1_y)
    d_wt_protectionMeasurements_firstOrder2_y: Var = vf.add_diff_var('d_wt.protectionMeasurements.firstOrder2.y_' + template_name, base_var=wt_protectionMeasurements_firstOrder2_y)
    d_wt_protectionMeasurements_firstOrder3_y: Var = vf.add_diff_var('d_wt.protectionMeasurements.firstOrder3.y_' + template_name, base_var=wt_protectionMeasurements_firstOrder3_y)
    d_wt_protectionMeasurements_firstOrder4_y: Var = vf.add_diff_var('d_wt.protectionMeasurements.firstOrder4.y_' + template_name, base_var=wt_protectionMeasurements_firstOrder4_y)
    d_wt_protectionMeasurements_rampLimiter_integrator_y: Var = vf.add_diff_var('d_wt.protectionMeasurements.rampLimiter.integrator.y_' + template_name, base_var=wt_protectionMeasurements_rampLimiter_integrator_y)
    d_wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y: Var = vf.add_diff_var('d_wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup.integrator.y_' + template_name, base_var=wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y)
    d_wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y: Var = vf.add_diff_var('d_wt.wT4Injector.genSystem.absLimRateLimFirstOrderAntiWindup1.integrator.y_' + template_name, base_var=wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((wt_controlMeasurements_firstOrder4_k * wt_controlMeasurements_rampLimiter_integrator_y) - wt_controlMeasurements_firstOrder4_y) / wt_controlMeasurements_firstOrder4_T))
    state_equations.append(((wt_controlMeasurements_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - wt_controlMeasurements_derivative_zeroGain) * ((wt_controlMeasurements_theta - wt_controlMeasurements_derivative_x) / wt_controlMeasurements_derivative_T))))
    state_equations.append((wt_controlMeasurements_rampLimiter_integrator_k * wt_controlMeasurements_rampLimiter_limiter_y))
    state_equations.append((((wt_controlMeasurements_firstOrder3_k * wt_controlMeasurements_UPu) - wt_controlMeasurements_firstOrder3_y) / wt_controlMeasurements_firstOrder3_T))
    state_equations.append((wt_protectionMeasurements_rampLimiter_integrator_k * wt_protectionMeasurements_rampLimiter_limiter_y))
    state_equations.append(((wt_protectionMeasurements_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - wt_protectionMeasurements_derivative_zeroGain) * ((wt_protectionMeasurements_theta - wt_protectionMeasurements_derivative_x) / wt_protectionMeasurements_derivative_T))))
    state_equations.append((((wt_protectionMeasurements_firstOrder4_k * wt_protectionMeasurements_rampLimiter_integrator_y) - wt_protectionMeasurements_firstOrder4_y) / wt_protectionMeasurements_firstOrder4_T))
    state_equations.append((((wt_protectionMeasurements_firstOrder3_k * wt_protectionMeasurements_UPu) - wt_protectionMeasurements_firstOrder3_y) / wt_protectionMeasurements_firstOrder3_T))
    state_equations.append((wt_mechanical_pI_integrator_k * wt_mechanical_add2_y))
    state_equations.append((wt_mechanical_integrator_k * wt_mechanical_add_y))
    state_equations.append(((wt_control4B_qControl_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - wt_control4B_qControl_derivative_zeroGain) * ((wt_controlMeasurements_firstOrder3_y - wt_control4B_qControl_derivative_x) / wt_control4B_qControl_derivative_T))))
    state_equations.append((wt_control4B_pControl4B_rampLimiter_integrator_k * wt_control4B_pControl4B_rampLimiter_limiter_y))
    state_equations.append((((wt_control4B_pControl4B_firstOrder_k * wt_control4B_pControl4B_switch1_y) - wt_control4B_pControl4B_firstOrder_y) / wt_control4B_pControl4B_firstOrder_T))
    state_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_k * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_y))
    state_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_k * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_y))
    state_equations.append((wt_pll_absLimRateLimFirstOrderFreeze_integrator_k * wt_pll_absLimRateLimFirstOrderFreeze_switch1_y))
    state_equations.append((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_k * wt_control4B_qControl_absLimRateLimFirstOrderFreeze_switch1_y))
    state_equations.append((wt_control4B_qControl_antiWindupIntegrator_integrator_k * wt_control4B_qControl_antiWindupIntegrator_switch2_y))
    state_equations.append((wt_control4B_qControl_antiWindupIntegrator1_integrator_k * wt_control4B_qControl_antiWindupIntegrator1_switch2_y))
    state_equations.append((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_k * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_y))
    state_equations.append((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_k * wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_y))
    state_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_k * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_y))
    state_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_k * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_y))
    state_equations.append((((wt_controlMeasurements_firstOrder2_k * wt_protectionMeasurements_complexToPolar_len) - wt_controlMeasurements_firstOrder2_y) / wt_controlMeasurements_firstOrder2_T))
    state_equations.append((((wt_protectionMeasurements_firstOrder2_k * wt_protectionMeasurements_complexToPolar_len) - wt_protectionMeasurements_firstOrder2_y) / wt_protectionMeasurements_firstOrder2_T))
    state_equations.append((((wt_controlMeasurements_firstOrder_k * wt_controlMeasurements_PPu) - wt_controlMeasurements_firstOrder_y) / wt_controlMeasurements_firstOrder_T))
    state_equations.append((((wt_protectionMeasurements_firstOrder_k * wt_controlMeasurements_PPu) - wt_protectionMeasurements_firstOrder_y) / wt_protectionMeasurements_firstOrder_T))
    state_equations.append((((wt_controlMeasurements_firstOrder1_k * wt_controlMeasurements_complexToReal_im) - wt_controlMeasurements_firstOrder1_y) / wt_controlMeasurements_firstOrder1_T))
    state_equations.append((((wt_protectionMeasurements_firstOrder1_k * wt_protectionMeasurements_complexToReal_im) - wt_protectionMeasurements_firstOrder1_y) / wt_protectionMeasurements_firstOrder1_T))
    state_equations.append((wt_mechanical_integrator1_k * wt_mechanical_add1_y))
    state_variables: list[Var] = list()
    state_variables.append(wt_controlMeasurements_firstOrder4_y)
    state_variables.append(wt_controlMeasurements_derivative_x)
    state_variables.append(wt_controlMeasurements_rampLimiter_integrator_y)
    state_variables.append(wt_controlMeasurements_firstOrder3_y)
    state_variables.append(wt_protectionMeasurements_rampLimiter_integrator_y)
    state_variables.append(wt_protectionMeasurements_derivative_x)
    state_variables.append(wt_protectionMeasurements_firstOrder4_y)
    state_variables.append(wt_protectionMeasurements_firstOrder3_y)
    state_variables.append(wt_mechanical_pI_integrator_y)
    state_variables.append(wt_mechanical_integrator_y)
    state_variables.append(wt_control4B_qControl_derivative_x)
    state_variables.append(wt_control4B_pControl4B_rampLimiter_integrator_y)
    state_variables.append(wt_control4B_pControl4B_firstOrder_y)
    state_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y)
    state_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y)
    state_variables.append(wt_pll_absLimRateLimFirstOrderFreeze_integrator_y)
    state_variables.append(wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y)
    state_variables.append(wt_control4B_qControl_antiWindupIntegrator_integrator_y)
    state_variables.append(wt_control4B_qControl_antiWindupIntegrator1_integrator_y)
    state_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y)
    state_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y)
    state_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y)
    state_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y)
    state_variables.append(wt_controlMeasurements_firstOrder2_y)
    state_variables.append(wt_protectionMeasurements_firstOrder2_y)
    state_variables.append(wt_controlMeasurements_firstOrder_y)
    state_variables.append(wt_protectionMeasurements_firstOrder_y)
    state_variables.append(wt_controlMeasurements_firstOrder1_y)
    state_variables.append(wt_protectionMeasurements_firstOrder1_y)
    state_variables.append(wt_mechanical_integrator1_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((wt_controlMeasurements_UWtPu - (((grid_terminal_V_re ** sym.Const(2.0)) + (grid_terminal_V_im ** sym.Const(2.0))) ** sym.Const(0.5))))
    algebraic_equations.append((wt_controlMeasurements_UPu - wt_controlMeasurements_UWtPu))
    algebraic_equations.append((wt_protectionMeasurements_UWtPu - (((grid_terminal_V_re ** sym.Const(2.0)) + (grid_terminal_V_im ** sym.Const(2.0))) ** sym.Const(0.5))))
    algebraic_equations.append((wt_protectionMeasurements_UPu - wt_protectionMeasurements_UWtPu))
    algebraic_equations.append((wt_pll_lessThreshold_y - sym.heaviside(((wt_pll_lessThreshold_threshold - wt_controlMeasurements_UPu) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_pll_lessThreshold1_y - sym.heaviside(((wt_pll_lessThreshold1_threshold - wt_controlMeasurements_UPu) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_pll_fixedBooleanDelay1_uReal - ((wt_pll_lessThreshold1_y * sym.Const(1.0)) + ((sym.Const(1.0) - wt_pll_lessThreshold1_y) * sym.Const(0.0)))))
    algebraic_equations.append((wt_pll_fixedBooleanDelay_uReal - ((wt_pll_lessThreshold_y * sym.Const(1.0)) + ((sym.Const(1.0) - wt_pll_lessThreshold_y) * sym.Const(0.0)))))
    algebraic_equations.append((wt_control4B_pControl4B_less_y - sym.heaviside(((wt_control4B_pControl4B_const1_k - wt_controlMeasurements_UPu) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_control4B_pControl4B_and1_y - (wt_control4B_pControl4B_less_y * wt_control4B_pControl4B_booleanConstant_k)))
    algebraic_equations.append((wt_controlMeasurements_omegaFiltPu - ((wt_controlMeasurements_add_k1 * wt_controlMeasurements_firstOrder4_y) + wt_controlMeasurements_add_k2)))
    algebraic_equations.append((wt_controlMeasurements_derivative_y - ((wt_controlMeasurements_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - wt_controlMeasurements_derivative_zeroGain) * ((wt_controlMeasurements_derivative_k / wt_controlMeasurements_derivative_T) * (wt_controlMeasurements_theta - wt_controlMeasurements_derivative_x))))))
    algebraic_equations.append((wt_controlMeasurements_rampLimiter_feedback_y - (wt_controlMeasurements_derivative_y - wt_controlMeasurements_rampLimiter_integrator_y)))
    algebraic_equations.append((wt_controlMeasurements_rampLimiter_gain_y - (wt_controlMeasurements_rampLimiter_gain_k * wt_controlMeasurements_rampLimiter_feedback_y)))
    algebraic_equations.append((wt_controlMeasurements_rampLimiter_limiter_y - ((sym.heaviside(((wt_controlMeasurements_rampLimiter_gain_y - wt_controlMeasurements_rampLimiter_limiter_uMax) - sym.Const(1e-06))) * wt_controlMeasurements_rampLimiter_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_controlMeasurements_rampLimiter_gain_y - wt_controlMeasurements_rampLimiter_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_controlMeasurements_rampLimiter_limiter_uMin - wt_controlMeasurements_rampLimiter_gain_y) - sym.Const(1e-06))) * wt_controlMeasurements_rampLimiter_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_controlMeasurements_rampLimiter_limiter_uMin - wt_controlMeasurements_rampLimiter_gain_y) - sym.Const(1e-06)))) * wt_controlMeasurements_rampLimiter_gain_y))))))
    algebraic_equations.append((wt_gridProtection_or1_u_5 - wt_gridProtection_pre1_u))
    algebraic_equations.append((whenCondition10 - sym.heaviside(((wt_gridProtection_const1_k - wt_protectionMeasurements_firstOrder3_y) + sym.Const(1e-06)))))
    algebraic_equations.append((wt_gridProtection_timer1_y - ((whenCondition10 * (time - wt_gridProtection_timer1_entryTime)) + ((sym.Const(1.0) - whenCondition10) * sym.Const(0.0)))))
    algebraic_equations.append((wt_gridProtection_lessEqual1_y - whenCondition10))
    algebraic_equations.append((whenCondition9 - sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - wt_gridProtection_const_k) + sym.Const(1e-06)))))
    algebraic_equations.append((wt_gridProtection_timer_y - ((whenCondition9 * (time - wt_gridProtection_timer_entryTime)) + ((sym.Const(1.0) - whenCondition9) * sym.Const(0.0)))))
    algebraic_equations.append((wt_gridProtection_lessEqual_y - whenCondition9))
    algebraic_equations.append((wt_protectionMeasurements_derivative_y - ((wt_protectionMeasurements_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - wt_protectionMeasurements_derivative_zeroGain) * ((wt_protectionMeasurements_derivative_k / wt_protectionMeasurements_derivative_T) * (wt_protectionMeasurements_theta - wt_protectionMeasurements_derivative_x))))))
    algebraic_equations.append((wt_protectionMeasurements_rampLimiter_feedback_y - (wt_protectionMeasurements_derivative_y - wt_protectionMeasurements_rampLimiter_integrator_y)))
    algebraic_equations.append((wt_protectionMeasurements_rampLimiter_gain_y - (wt_protectionMeasurements_rampLimiter_gain_k * wt_protectionMeasurements_rampLimiter_feedback_y)))
    algebraic_equations.append((wt_protectionMeasurements_rampLimiter_limiter_y - ((sym.heaviside(((wt_protectionMeasurements_rampLimiter_gain_y - wt_protectionMeasurements_rampLimiter_limiter_uMax) - sym.Const(1e-06))) * wt_protectionMeasurements_rampLimiter_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_protectionMeasurements_rampLimiter_gain_y - wt_protectionMeasurements_rampLimiter_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_protectionMeasurements_rampLimiter_limiter_uMin - wt_protectionMeasurements_rampLimiter_gain_y) - sym.Const(1e-06))) * wt_protectionMeasurements_rampLimiter_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_protectionMeasurements_rampLimiter_limiter_uMin - wt_protectionMeasurements_rampLimiter_gain_y) - sym.Const(1e-06)))) * wt_protectionMeasurements_rampLimiter_gain_y))))))
    algebraic_equations.append((wt_protectionMeasurements_omegaFiltPu - ((wt_protectionMeasurements_add_k1 * wt_protectionMeasurements_firstOrder4_y) + wt_protectionMeasurements_add_k2)))
    algebraic_equations.append((wt_gridProtection_combiTable1D2_y_1 - (((((sym.Const(0.33) * sym.heaviside(((sym.Const(1.0) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06)))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.5) - sym.Const(1.0))) * wt_protectionMeasurements_omegaFiltPu) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.5) - sym.Const(1.0))) * sym.Const(1.0)))) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(1.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.5) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.0) - sym.Const(1.5))) * wt_protectionMeasurements_omegaFiltPu) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.0) - sym.Const(1.5))) * sym.Const(1.5)))) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(1.5)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(2.0) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.01) - sym.Const(2.0))) * wt_protectionMeasurements_omegaFiltPu) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.01) - sym.Const(2.0))) * sym.Const(2.0)))) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(2.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(2.01) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06))))) + (sym.Const(0.33) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(2.01)) + sym.Const(1e-06)))))))
    algebraic_equations.append((wt_gridProtection_combiTable1D3_y_1 - (((((((sym.Const(0.33) * sym.heaviside(((sym.Const(0.0) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06)))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(0.5) - sym.Const(0.0))) * wt_protectionMeasurements_omegaFiltPu) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(0.5) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.5) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.0) - sym.Const(0.5))) * wt_protectionMeasurements_omegaFiltPu) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.0) - sym.Const(0.5))) * sym.Const(0.5)))) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(0.5)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.01) - sym.Const(1.0))) * wt_protectionMeasurements_omegaFiltPu) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.01) - sym.Const(1.0))) * sym.Const(1.0)))) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(1.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.01) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.02) - sym.Const(1.01))) * wt_protectionMeasurements_omegaFiltPu) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.02) - sym.Const(1.01))) * sym.Const(1.01)))) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(1.01)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.02) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.03) - sym.Const(1.02))) * wt_protectionMeasurements_omegaFiltPu) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.03) - sym.Const(1.02))) * sym.Const(1.02)))) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(1.02)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.03) - wt_protectionMeasurements_omegaFiltPu) - sym.Const(1e-06))))) + (sym.Const(0.33) * sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - sym.Const(1.03)) + sym.Const(1e-06)))))))
    algebraic_equations.append((whenCondition11 - sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - wt_gridProtection_const2_k) + sym.Const(1e-06)))))
    algebraic_equations.append((wt_gridProtection_timer2_y - ((whenCondition11 * (time - wt_gridProtection_timer2_entryTime)) + ((sym.Const(1.0) - whenCondition11) * sym.Const(0.0)))))
    algebraic_equations.append((whenCondition16 - sym.heaviside(((wt_gridProtection_timer2_y - wt_gridProtection_combiTable1D2_y_1) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_gridProtection_or1_u_3 - whenCondition16))
    algebraic_equations.append((wt_gridProtection_lessEqual2_y - whenCondition11))
    algebraic_equations.append((whenCondition12 - sym.heaviside(((wt_gridProtection_const3_k - wt_protectionMeasurements_omegaFiltPu) + sym.Const(1e-06)))))
    algebraic_equations.append((wt_gridProtection_timer3_y - ((whenCondition12 * (time - wt_gridProtection_timer3_entryTime)) + ((sym.Const(1.0) - whenCondition12) * sym.Const(0.0)))))
    algebraic_equations.append((whenCondition15 - sym.heaviside(((wt_gridProtection_timer3_y - wt_gridProtection_combiTable1D3_y_1) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_gridProtection_or1_u_4 - whenCondition15))
    algebraic_equations.append((wt_gridProtection_lessEqual3_y - whenCondition12))
    algebraic_equations.append((wt_mechanical_add2_y - ((wt_mechanical_add2_k1 * wt_mechanical_integrator_y) + (wt_mechanical_add2_k2 * wt_mechanical_integrator1_y))))
    algebraic_equations.append((wt_mechanical_pI_y - ((wt_mechanical_pI_add_k1 * wt_mechanical_add2_y) + (wt_mechanical_pI_add_k2 * wt_mechanical_pI_integrator_y))))
    algebraic_equations.append((wt_mechanical_division_y - (wt_control4B_pControl4B_firstOrder_y / wt_mechanical_integrator_y)))
    algebraic_equations.append((wt_mechanical_add_y - ((wt_mechanical_add_k1 * wt_mechanical_division_y) + (wt_mechanical_add_k2 * wt_mechanical_pI_y))))
    algebraic_equations.append((wt_control4B_currentLimiter_add1_y - ((wt_control4B_currentLimiter_add1_k1 * wt_control4B_currentLimiter_const4_k) + (wt_control4B_currentLimiter_add1_k2 * wt_controlMeasurements_firstOrder3_y))))
    algebraic_equations.append((wt_control4B_currentLimiter_gain1_y - (wt_control4B_currentLimiter_gain1_k * wt_control4B_currentLimiter_add1_y)))
    algebraic_equations.append((wt_control4B_currentLimiter_switch_y - ((wt_control4B_currentLimiter_booleanConstant_k * wt_mechanical_integrator1_y) + ((sym.Const(1.0) - wt_control4B_currentLimiter_booleanConstant_k) * wt_control4B_currentLimiter_const_k))))
    algebraic_equations.append((wt_control4B_qControl_greaterThreshold_y - sym.heaviside(((wt_controlMeasurements_firstOrder3_y - wt_control4B_qControl_greaterThreshold_threshold) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_control4B_qControl_booleanToInteger_y - ((wt_control4B_qControl_greaterThreshold_y * wt_control4B_qControl_booleanToInteger_integerTrue) + ((sym.Const(1.0) - wt_control4B_qControl_greaterThreshold_y) * wt_control4B_qControl_booleanToInteger_integerFalse))))
    algebraic_equations.append((wt_control4B_qControl_derivative_y - ((wt_control4B_qControl_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - wt_control4B_qControl_derivative_zeroGain) * ((wt_control4B_qControl_derivative_k / wt_control4B_qControl_derivative_T) * (wt_controlMeasurements_firstOrder3_y - wt_control4B_qControl_derivative_x))))))
    algebraic_equations.append((wt_control4B_qControl_deadZone_y - ((sym.heaviside(((wt_control4B_qControl_derivative_y - wt_control4B_qControl_deadZone_uMax) - sym.Const(1e-06))) * (wt_control4B_qControl_derivative_y - wt_control4B_qControl_deadZone_uMax)) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_derivative_y - wt_control4B_qControl_deadZone_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_deadZone_uMin - wt_control4B_qControl_derivative_y) - sym.Const(1e-06))) * (wt_control4B_qControl_derivative_y - wt_control4B_qControl_deadZone_uMin)) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_deadZone_uMin - wt_control4B_qControl_derivative_y) - sym.Const(1e-06)))) * sym.Const(0.0)))))))
    algebraic_equations.append((wt_control4B_qControl_switch6_u_1 - (wt_control4B_qControl_gain7_k * wt_control4B_qControl_deadZone_y)))
    algebraic_equations.append((whenCondition8 - sym.heaviside(((wt_control4B_qControl_lessThreshold_threshold - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_control4B_qControl_delayFlag_booleanToInteger_y - (((sym.Const(1.0) - whenCondition8) * wt_control4B_qControl_delayFlag_booleanToInteger_integerTrue) + ((sym.Const(1.0) - (sym.Const(1.0) - whenCondition8)) * wt_control4B_qControl_delayFlag_booleanToInteger_integerFalse))))
    algebraic_equations.append((wt_control4B_qControl_delayFlag_timer_y - ((whenCondition8 * (time - wt_control4B_qControl_delayFlag_timer_entryTime)) + ((sym.Const(1.0) - whenCondition8) * sym.Const(0.0)))))
    algebraic_equations.append((wt_control4B_qControl_delayFlag_fI - (sym.Const(1.0) - whenCondition8)))
    algebraic_equations.append((wt_control4B_qControl_abs_y - ((sym.heaviside(((wt_controlMeasurements_firstOrder_y - sym.Const(0.0)) + sym.Const(1e-06))) * wt_controlMeasurements_firstOrder_y) + ((sym.Const(1.0) - sym.heaviside(((wt_controlMeasurements_firstOrder_y - sym.Const(0.0)) + sym.Const(1e-06)))) * (-wt_controlMeasurements_firstOrder_y)))))
    algebraic_equations.append((wt_control4B_qControl_gain6_y - (wt_control4B_qControl_gain6_k * wt_controlMeasurements_firstOrder1_y)))
    algebraic_equations.append((wt_control4B_qControl_gain5_y - (wt_control4B_qControl_gain5_k * wt_controlMeasurements_firstOrder_y)))
    algebraic_equations.append((wt_control4B_qControl_vDrop_UDropPu - sym.Const(0.0)))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_fixedDelay_y - sym.Const(0.0)))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator1_y - ((sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator1_integrator_y - wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator1_integrator_y - wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMin - wt_control4B_qControl_antiWindupIntegrator1_integrator_y) - sym.Const(1e-06))) * wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMin - wt_control4B_qControl_antiWindupIntegrator1_integrator_y) - sym.Const(1e-06)))) * wt_control4B_qControl_antiWindupIntegrator1_integrator_y))))))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator_y - ((sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator_integrator_y - wt_control4B_qControl_antiWindupIntegrator_limiter1_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_antiWindupIntegrator_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator_integrator_y - wt_control4B_qControl_antiWindupIntegrator_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator_limiter1_uMin - wt_control4B_qControl_antiWindupIntegrator_integrator_y) - sym.Const(1e-06))) * wt_control4B_qControl_antiWindupIntegrator_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator_limiter1_uMin - wt_control4B_qControl_antiWindupIntegrator_integrator_y) - sym.Const(1e-06)))) * wt_control4B_qControl_antiWindupIntegrator_integrator_y))))))
    algebraic_equations.append((wt_control4B_qControl_delayFlag_fixedDelay_y - sym.Const(0.0)))
    algebraic_equations.append((wt_control4B_qControl_delayFlag_switch18_y - (((sym.Const(1.0) - whenCondition8) * wt_control4B_qControl_delayFlag_const7_k) + ((sym.Const(1.0) - (sym.Const(1.0) - whenCondition8)) * wt_control4B_qControl_delayFlag_fixedDelay_y))))
    algebraic_equations.append((wt_control4B_qControl_delayFlag_less1_y - sym.heaviside(((wt_control4B_qControl_delayFlag_switch18_y - wt_control4B_qControl_delayFlag_timer_y) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_control4B_qControl_delayFlag_switch1_y - ((wt_control4B_qControl_delayFlag_less1_y * wt_control4B_qControl_delayFlag_integerConstant_k) + ((sym.Const(1.0) - wt_control4B_qControl_delayFlag_less1_y) * wt_control4B_qControl_delayFlag_booleanToInteger_y))))
    algebraic_equations.append((wt_control4B_qControl_delayFlag_fO - (((sym.Const(1.0) - whenCondition8) * wt_control4B_qControl_delayFlag_booleanToInteger_y) + ((sym.Const(1.0) - (sym.Const(1.0) - whenCondition8)) * wt_control4B_qControl_delayFlag_switch1_y))))
    algebraic_equations.append((wt_control4B_qControl_fFrt - ((wt_control4B_qControl_greaterThreshold_y * wt_control4B_qControl_booleanToInteger_y) + ((sym.Const(1.0) - wt_control4B_qControl_greaterThreshold_y) * wt_control4B_qControl_delayFlag_fO))))
    algebraic_equations.append((wt_control4B_currentLimiter_product1_y - (wt_control4B_qControl_fFrt * wt_control4B_currentLimiter_product1_u_2)))
    algebraic_equations.append((wt_control4B_qControl_integerToReal_y - wt_control4B_qControl_fFrt))
    algebraic_equations.append((wt_control4B_qControl_greaterEqualThreshold_y - sym.heaviside(((wt_control4B_qControl_integerToReal_y - wt_control4B_qControl_greaterEqualThreshold_threshold) + sym.Const(1e-06)))))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_y - ((wt_control4B_qControl_greaterEqualThreshold_y * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_fixedDelay_y) + ((sym.Const(1.0) - wt_control4B_qControl_greaterEqualThreshold_y) * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y))))
    algebraic_equations.append((wt_control4B_qControl_switch4_u_5 - (wt_control4B_qControl_gain4_k * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_y)))
    algebraic_equations.append((wt_control4B_qControl_switch4_u_3 - wt_control4B_qControl_switch4_u_5))
    algebraic_equations.append((wt_control4B_qLimiter_integerToBoolean_y - sym.heaviside(((wt_control4B_qControl_fFrt - wt_control4B_qLimiter_integerToBoolean_threshold) + sym.Const(1e-06)))))
    algebraic_equations.append((wt_control4B_pControl4B_rampLimiter_feedback_y - (wt_PWTRefPu - wt_control4B_pControl4B_rampLimiter_integrator_y)))
    algebraic_equations.append((wt_control4B_pControl4B_rampLimiter_gain_y - (wt_control4B_pControl4B_rampLimiter_gain_k * wt_control4B_pControl4B_rampLimiter_feedback_y)))
    algebraic_equations.append((wt_control4B_pControl4B_rampLimiter_limiter_y - ((sym.heaviside(((wt_control4B_pControl4B_rampLimiter_gain_y - wt_control4B_pControl4B_rampLimiter_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_pControl4B_rampLimiter_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_pControl4B_rampLimiter_gain_y - wt_control4B_pControl4B_rampLimiter_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_pControl4B_rampLimiter_limiter_uMin - wt_control4B_pControl4B_rampLimiter_gain_y) - sym.Const(1e-06))) * wt_control4B_pControl4B_rampLimiter_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_pControl4B_rampLimiter_limiter_uMin - wt_control4B_pControl4B_rampLimiter_gain_y) - sym.Const(1e-06)))) * wt_control4B_pControl4B_rampLimiter_gain_y))))))
    algebraic_equations.append((wt_control4B_pControl4B_product_y - (wt_control4B_pControl4B_rampLimiter_integrator_y * wt_controlMeasurements_UPu)))
    algebraic_equations.append((wt_control4B_pControl4B_switch1_y - ((wt_control4B_pControl4B_and1_y * wt_control4B_pControl4B_product_y) + ((sym.Const(1.0) - wt_control4B_pControl4B_and1_y) * wt_control4B_pControl4B_rampLimiter_integrator_y))))
    algebraic_equations.append((wt_control4B_pControl4B_product2_y - (wt_control4B_pControl4B_switch1_y * wt_mechanical_integrator1_y)))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_fixedDelay_y - sym.Const(0.0)))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y - ((wt_control4B_qLimiter_integerToBoolean_y * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_fixedDelay_y) + ((sym.Const(1.0) - wt_control4B_qLimiter_integerToBoolean_y) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y))))
    algebraic_equations.append((wt_control4B_qLimiter_combiTable1Ds2_y_1 - (((((sym.Const(0.0) * sym.heaviside(((sym.Const(0.0) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) - sym.Const(1e-06)))) + ((((((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.001) - sym.Const(0.0))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) + (sym.Const(0.0) - (((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.001) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.001) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.0)) / (sym.Const(0.3) - sym.Const(0.001))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) + (sym.Const(0.0) - (((sym.Const(0.33) - sym.Const(0.0)) / (sym.Const(0.3) - sym.Const(0.001))) * sym.Const(0.001)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y - sym.Const(0.001)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.3) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.0) - sym.Const(0.3))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.0) - sym.Const(0.3))) * sym.Const(0.3)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y - sym.Const(0.3)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) - sym.Const(1e-06))))) + (sym.Const(0.33) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y - sym.Const(1.0)) + sym.Const(1e-06)))))))
    algebraic_equations.append((wt_control4B_qLimiter_combiTable1Ds3_y_1 - (((((sym.Const(0.0) * sym.heaviside(((sym.Const(0.0) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) - sym.Const(1e-06)))) + ((((((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.001) - sym.Const(0.0))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) + (sym.Const(0.0) - (((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.001) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.001) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) - sym.Const(1e-06))))) + ((((((sym.Const(-0.33) - sym.Const(0.0)) / (sym.Const(0.3) - sym.Const(0.001))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) + (sym.Const(0.0) - (((sym.Const(-0.33) - sym.Const(0.0)) / (sym.Const(0.3) - sym.Const(0.001))) * sym.Const(0.001)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y - sym.Const(0.001)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.3) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) - sym.Const(1e-06))))) + ((((((sym.Const(-0.33) - sym.Const(-0.33)) / (sym.Const(1.0) - sym.Const(0.3))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) + (sym.Const(-0.33) - (((sym.Const(-0.33) - sym.Const(-0.33)) / (sym.Const(1.0) - sym.Const(0.3))) * sym.Const(0.3)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y - sym.Const(0.3)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y) - sym.Const(1e-06))))) + (sym.Const(-0.33) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y - sym.Const(1.0)) + sym.Const(1e-06)))))))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_y - ((sym.heaviside(((wt_controlMeasurements_firstOrder_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_controlMeasurements_firstOrder_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMin - wt_controlMeasurements_firstOrder_y) - sym.Const(1e-06))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMin - wt_controlMeasurements_firstOrder_y) - sym.Const(1e-06)))) * wt_controlMeasurements_firstOrder_y))))))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_feedback_y - (wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y)))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_y - (wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_k * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_feedback_y)))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_y - ((sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMin - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_y) - sym.Const(1e-06))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMin - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_y) - sym.Const(1e-06)))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_y))))))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_fixedDelay_y - sym.Const(0.0)))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - ((wt_control4B_qLimiter_integerToBoolean_y * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_fixedDelay_y) + ((sym.Const(1.0) - wt_control4B_qLimiter_integerToBoolean_y) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y))))
    algebraic_equations.append((wt_control4B_qLimiter_combiTable1Ds_y_1 - (((((((sym.Const(0.0) * sym.heaviside(((sym.Const(0.0) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06)))) + ((((((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.001) - sym.Const(0.0))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) + (sym.Const(0.0) - (((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.001) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.001) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.0)) / (sym.Const(0.8) - sym.Const(0.001))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) + (sym.Const(0.0) - (((sym.Const(0.33) - sym.Const(0.0)) / (sym.Const(0.8) - sym.Const(0.001))) * sym.Const(0.001)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(0.001)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.8) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.2) - sym.Const(0.8))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.2) - sym.Const(0.8))) * sym.Const(0.8)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(0.8)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.2) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.21) - sym.Const(1.2))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.21) - sym.Const(1.2))) * sym.Const(1.2)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(1.2)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.21) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.22) - sym.Const(1.21))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.22) - sym.Const(1.21))) * sym.Const(1.21)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(1.21)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.22) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06))))) + (sym.Const(0.33) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(1.22)) + sym.Const(1e-06)))))))
    algebraic_equations.append((wt_control4B_qLimiter_min_y - sym.min(wt_control4B_qLimiter_combiTable1Ds_y_1, wt_control4B_qLimiter_combiTable1Ds2_y_1)))
    algebraic_equations.append((wt_control4B_qLimiter_QWTMaxPu - ((wt_control4B_qLimiter_booleanConstant_k * wt_control4B_qLimiter_const_k) + ((sym.Const(1.0) - wt_control4B_qLimiter_booleanConstant_k) * wt_control4B_qLimiter_min_y))))
    algebraic_equations.append((wt_control4B_qLimiter_combiTable1Ds1_y_1 - (((((sym.Const(0.0) * sym.heaviside(((sym.Const(0.0) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06)))) + ((((((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.001) - sym.Const(0.0))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) + (sym.Const(0.0) - (((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.001) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.001) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06))))) + ((((((sym.Const(-0.33) - sym.Const(0.0)) / (sym.Const(0.8) - sym.Const(0.001))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) + (sym.Const(0.0) - (((sym.Const(-0.33) - sym.Const(0.0)) / (sym.Const(0.8) - sym.Const(0.001))) * sym.Const(0.001)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(0.001)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.8) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06))))) + ((((((sym.Const(-0.33) - sym.Const(-0.33)) / (sym.Const(1.2) - sym.Const(0.8))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) + (sym.Const(-0.33) - (((sym.Const(-0.33) - sym.Const(-0.33)) / (sym.Const(1.2) - sym.Const(0.8))) * sym.Const(0.8)))) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(0.8)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.2) - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y) - sym.Const(1e-06))))) + (sym.Const(-0.33) * sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y - sym.Const(1.2)) + sym.Const(1e-06)))))))
    algebraic_equations.append((wt_control4B_qLimiter_max_y - sym.max(wt_control4B_qLimiter_combiTable1Ds1_y_1, wt_control4B_qLimiter_combiTable1Ds3_y_1)))
    algebraic_equations.append((wt_control4B_qLimiter_QWTMinPu - ((wt_control4B_qLimiter_booleanConstant_k * wt_control4B_qLimiter_constant1_k) + ((sym.Const(1.0) - wt_control4B_qLimiter_booleanConstant_k) * wt_control4B_qLimiter_max_y))))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_y - ((sym.heaviside(((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y - wt_control4B_qLimiter_QWTMaxPu) - sym.Const(1e-06))) * wt_control4B_qLimiter_QWTMaxPu) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y - wt_control4B_qLimiter_QWTMaxPu) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qLimiter_QWTMinPu - wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y) - sym.Const(1e-06))) * wt_control4B_qLimiter_QWTMinPu) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qLimiter_QWTMinPu - wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y) - sym.Const(1e-06)))) * wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y))))))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_y - ((sym.heaviside(((wt_controlMeasurements_firstOrder3_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_controlMeasurements_firstOrder3_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMin - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMin - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06)))) * wt_controlMeasurements_firstOrder3_y))))))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_feedback_y - (wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y)))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y - (wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_k * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_feedback_y)))
    algebraic_equations.append((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_y - ((sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y) - sym.Const(1e-06))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin - wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y) - sym.Const(1e-06)))) * wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y))))))
    algebraic_equations.append((wt_pll_fixedBooleanDelay_yReal - sym.Const(0.0)))
    algebraic_equations.append((whenCondition7 - sym.heaviside(((wt_pll_fixedBooleanDelay_yReal - sym.Const(0.5)) - sym.Const(1e-06)))))
    algebraic_equations.append((whenCondition6 - sym.heaviside(((sym.Const(0.5) - wt_pll_fixedBooleanDelay_yReal) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_pll_fixedBooleanDelay1_yReal - sym.Const(0.0)))
    algebraic_equations.append((whenCondition5 - sym.heaviside(((wt_pll_fixedBooleanDelay1_yReal - sym.Const(0.5)) - sym.Const(1e-06)))))
    algebraic_equations.append((whenCondition4 - sym.heaviside(((sym.Const(0.5) - wt_pll_fixedBooleanDelay1_yReal) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_pll_absLimRateLimFirstOrderFreeze_y - ((sym.heaviside(((wt_pll_absLimRateLimFirstOrderFreeze_integrator_y - wt_pll_absLimRateLimFirstOrderFreeze_YMax) - sym.Const(1e-06))) * wt_pll_absLimRateLimFirstOrderFreeze_YMax) + ((sym.Const(1.0) - sym.heaviside(((wt_pll_absLimRateLimFirstOrderFreeze_integrator_y - wt_pll_absLimRateLimFirstOrderFreeze_YMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_pll_absLimRateLimFirstOrderFreeze_YMin - wt_pll_absLimRateLimFirstOrderFreeze_integrator_y) - sym.Const(1e-06))) * wt_pll_absLimRateLimFirstOrderFreeze_YMin) + ((sym.Const(1.0) - sym.heaviside(((wt_pll_absLimRateLimFirstOrderFreeze_YMin - wt_pll_absLimRateLimFirstOrderFreeze_integrator_y) - sym.Const(1e-06)))) * wt_pll_absLimRateLimFirstOrderFreeze_integrator_y))))))
    algebraic_equations.append((wt_pll_absLimRateLimFirstOrderFreeze_feedback_y - (wt_controlMeasurements_theta - wt_pll_absLimRateLimFirstOrderFreeze_y)))
    algebraic_equations.append((wt_pll_absLimRateLimFirstOrderFreeze_gain_y - (wt_pll_absLimRateLimFirstOrderFreeze_gain_k * wt_pll_absLimRateLimFirstOrderFreeze_feedback_y)))
    algebraic_equations.append((wt_pll_absLimRateLimFirstOrderFreeze_limiter_y - ((sym.heaviside(((wt_pll_absLimRateLimFirstOrderFreeze_gain_y - wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMax) - sym.Const(1e-06))) * wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_pll_absLimRateLimFirstOrderFreeze_gain_y - wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMin - wt_pll_absLimRateLimFirstOrderFreeze_gain_y) - sym.Const(1e-06))) * wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMin - wt_pll_absLimRateLimFirstOrderFreeze_gain_y) - sym.Const(1e-06)))) * wt_pll_absLimRateLimFirstOrderFreeze_gain_y))))))
    algebraic_equations.append((wt_pll_absLimRateLimFirstOrderFreeze_switch1_y - ((wt_pll_fixedBooleanDelay1_y * wt_pll_absLimRateLimFirstOrderFreeze_const_k) + ((sym.Const(1.0) - wt_pll_fixedBooleanDelay1_y) * wt_pll_absLimRateLimFirstOrderFreeze_limiter_y))))
    algebraic_equations.append((wt_pll_thetaPll - ((wt_pll_fixedBooleanDelay_y * wt_pll_absLimRateLimFirstOrderFreeze_y) + ((sym.Const(1.0) - wt_pll_fixedBooleanDelay_y) * wt_controlMeasurements_theta))))
    algebraic_equations.append((cse2 - sym.cos(wt_pll_thetaPll)))
    algebraic_equations.append((cse1 - sym.sin(wt_pll_thetaPll)))
    algebraic_equations.append((wt_control4B_qControl_switch2_u_4 - wt_control4B_qControl_switch2_u_5))
    algebraic_equations.append((wt_control4B_qControl_switch_u_1 - ((wt_control4B_qControl_add2_k1 * wt_control4B_qControl_switch2_u_4) + (wt_control4B_qControl_add2_k2 * wt_URef0Pu))))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_feedback_y - (wt_control4B_qControl_switch2_u_4 - wt_control4B_qControl_absLimRateLimFirstOrderFreeze_y)))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_y - (wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_k * wt_control4B_qControl_absLimRateLimFirstOrderFreeze_feedback_y)))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_y - ((sym.heaviside(((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_y - wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_y - wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMin - wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_y) - sym.Const(1e-06))) * wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMin - wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_y) - sym.Const(1e-06)))) * wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_y))))))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFirstOrderFreeze_switch1_y - ((wt_control4B_qControl_greaterEqualThreshold_y * wt_control4B_qControl_absLimRateLimFirstOrderFreeze_const_k) + ((sym.Const(1.0) - wt_control4B_qControl_greaterEqualThreshold_y) * wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_y))))
    algebraic_equations.append((wt_control4B_qControl_variableLimiter_y - ((sym.heaviside(((wt_control4B_qControl_switch2_u_4 - wt_control4B_qLimiter_QWTMaxPu) - sym.Const(1e-06))) * wt_control4B_qLimiter_QWTMaxPu) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_switch2_u_4 - wt_control4B_qLimiter_QWTMaxPu) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qLimiter_QWTMinPu - wt_control4B_qControl_switch2_u_4) - sym.Const(1e-06))) * wt_control4B_qLimiter_QWTMinPu) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qLimiter_QWTMinPu - wt_control4B_qControl_switch2_u_4) - sym.Const(1e-06)))) * wt_control4B_qControl_switch2_u_4))))))
    algebraic_equations.append((wt_control4B_qControl_feedback_y - (wt_control4B_qControl_variableLimiter_y - wt_controlMeasurements_firstOrder1_y)))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator_gain_y - (wt_control4B_qControl_antiWindupIntegrator_gain_k * wt_control4B_qControl_feedback_y)))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator_limiter_y - ((sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator_gain_y - wt_control4B_qControl_antiWindupIntegrator_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_antiWindupIntegrator_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator_gain_y - wt_control4B_qControl_antiWindupIntegrator_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator_limiter_uMin - wt_control4B_qControl_antiWindupIntegrator_gain_y) - sym.Const(1e-06))) * wt_control4B_qControl_antiWindupIntegrator_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator_limiter_uMin - wt_control4B_qControl_antiWindupIntegrator_gain_y) - sym.Const(1e-06)))) * wt_control4B_qControl_antiWindupIntegrator_gain_y))))))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator_max_y - sym.max(wt_control4B_qControl_antiWindupIntegrator_limiter_y, wt_control4B_qControl_antiWindupIntegrator_const_k)))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator_switch1_y - ((wt_control4B_qControl_greaterEqualThreshold_y * wt_control4B_qControl_antiWindupIntegrator_max_y) + ((sym.Const(1.0) - wt_control4B_qControl_greaterEqualThreshold_y) * wt_control4B_qControl_antiWindupIntegrator_limiter_y))))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator_min_y - sym.min(wt_control4B_qControl_antiWindupIntegrator_const_k, wt_control4B_qControl_antiWindupIntegrator_switch1_y)))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator_switch2_y - ((wt_control4B_qControl_greaterEqualThreshold_y * wt_control4B_qControl_antiWindupIntegrator_min_y) + ((sym.Const(1.0) - wt_control4B_qControl_greaterEqualThreshold_y) * wt_control4B_qControl_antiWindupIntegrator_switch1_y))))
    algebraic_equations.append((wt_control4B_qControl_gain_y - (wt_control4B_qControl_gain_k * wt_control4B_qControl_feedback_y)))
    algebraic_equations.append((wt_control4B_qControl_switch_u_4 - ((wt_control4B_qControl_add_k1 * wt_control4B_qControl_antiWindupIntegrator_y) + (wt_control4B_qControl_add_k2 * wt_control4B_qControl_gain_y))))
    algebraic_equations.append((wt_control4B_qControl_switch_u_2 - wt_control4B_qControl_switch_u_4))
    algebraic_equations.append((wt_control4B_qControl_switch2_y - wt_control4B_qControl_switch2_u_4))
    algebraic_equations.append((wt_control4B_currentLimiter_switch2_u_1 - wt_control4B_currentLimiter_const2_k))
    algebraic_equations.append((wt_control4B_currentLimiter_switch2_u_3 - wt_control4B_currentLimiter_const2_k))
    algebraic_equations.append((wt_control4B_currentLimiter_switch2_u_2 - wt_control4B_currentLimiter_const3_k))
    algebraic_equations.append(((wt_control4B_currentLimiter_switch2_y - wt_control4B_currentLimiter_switch2_u) - (wt_control4B_qControl_fFrt + sym.Const(1.0))))
    algebraic_equations.append((wt_control4B_currentLimiter_feedback1_y - (wt_control4B_currentLimiter_switch2_y - wt_control4B_const_k)))
    algebraic_equations.append((wt_control4B_currentLimiter_product2_y - (wt_control4B_currentLimiter_feedback1_y ** sym.Const(2.0))))
    algebraic_equations.append((wt_control4B_qControl_switch_u_3 - wt_control4B_qControl_const_k))
    algebraic_equations.append((wt_control4B_qControl_switch_u_5 - wt_control4B_qControl_const_k))
    algebraic_equations.append(((wt_control4B_qControl_switch_y - wt_control4B_qControl_switch_u) - (wt_control4B_qControl_integerConstant_k + sym.Const(1.0))))
    algebraic_equations.append((wt_control4B_qControl_limiter_y - ((sym.heaviside(((wt_control4B_qControl_switch_y - wt_control4B_qControl_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_switch_y - wt_control4B_qControl_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_limiter_uMin - wt_control4B_qControl_switch_y) - sym.Const(1e-06))) * wt_control4B_qControl_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_limiter_uMin - wt_control4B_qControl_switch_y) - sym.Const(1e-06)))) * wt_control4B_qControl_switch_y))))))
    algebraic_equations.append((wt_control4B_qControl_feedback1_y - (wt_control4B_qControl_limiter_y - wt_control4B_qControl_vDrop_UDropPu)))
    algebraic_equations.append((wt_control4B_qControl_gain2_y - (wt_control4B_qControl_gain2_k * wt_control4B_qControl_feedback1_y)))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator1_gain_y - (wt_control4B_qControl_antiWindupIntegrator1_gain_k * wt_control4B_qControl_feedback1_y)))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator1_limiter_y - ((sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator1_gain_y - wt_control4B_qControl_antiWindupIntegrator1_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_antiWindupIntegrator1_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator1_gain_y - wt_control4B_qControl_antiWindupIntegrator1_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator1_limiter_uMin - wt_control4B_qControl_antiWindupIntegrator1_gain_y) - sym.Const(1e-06))) * wt_control4B_qControl_antiWindupIntegrator1_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_antiWindupIntegrator1_limiter_uMin - wt_control4B_qControl_antiWindupIntegrator1_gain_y) - sym.Const(1e-06)))) * wt_control4B_qControl_antiWindupIntegrator1_gain_y))))))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator1_max_y - sym.max(wt_control4B_qControl_antiWindupIntegrator1_limiter_y, wt_control4B_qControl_antiWindupIntegrator1_const_k)))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator1_switch1_y - ((wt_control4B_qControl_greaterEqualThreshold_y * wt_control4B_qControl_antiWindupIntegrator1_max_y) + ((sym.Const(1.0) - wt_control4B_qControl_greaterEqualThreshold_y) * wt_control4B_qControl_antiWindupIntegrator1_limiter_y))))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator1_min_y - sym.min(wt_control4B_qControl_antiWindupIntegrator1_const_k, wt_control4B_qControl_antiWindupIntegrator1_switch1_y)))
    algebraic_equations.append((wt_control4B_qControl_antiWindupIntegrator1_switch2_y - ((wt_control4B_qControl_greaterEqualThreshold_y * wt_control4B_qControl_antiWindupIntegrator1_min_y) + ((sym.Const(1.0) - wt_control4B_qControl_greaterEqualThreshold_y) * wt_control4B_qControl_antiWindupIntegrator1_switch1_y))))
    algebraic_equations.append((wt_control4B_qControl_gain1_y - (wt_control4B_qControl_gain1_k * wt_control4B_qControl_feedback1_y)))
    algebraic_equations.append((wt_control4B_qControl_switch6_u_4 - wt_control4B_const_k))
    algebraic_equations.append((wt_control4B_qControl_switch8_u_4 - wt_control4B_const_k))
    algebraic_equations.append((whenCondition3 - (sym.Const(1.0) - wt_wT4Injector_running_value)))
    algebraic_equations.append((whenCondition2 - (sym.Const(1.0) - wt_wT4Injector_running_value)))
    algebraic_equations.append((whenCondition1 - (wt_wT4Injector_running_value * (sym.Const(1.0) - wt_wT4Injector_running_value))))
    algebraic_equations.append((wt_control4B_pControl4B_max_y - sym.max(wt_control4B_pControl4B_const_k, wt_controlMeasurements_firstOrder3_y)))
    algebraic_equations.append((wt_control4B_qControl_max_y - sym.max(wt_controlMeasurements_firstOrder3_y, wt_control4B_qControl_const5_k)))
    algebraic_equations.append((wt_control4B_qControl_division_y - (wt_control4B_qLimiter_QWTMaxPu / wt_control4B_qControl_max_y)))
    algebraic_equations.append((wt_control4B_qControl_division1_y - (wt_control4B_qLimiter_QWTMinPu / wt_control4B_qControl_max_y)))
    algebraic_equations.append((wt_control4B_qControl_variableLimiter1_y - ((sym.heaviside(((wt_control4B_qControl_gain1_y - wt_control4B_qControl_division_y) - sym.Const(1e-06))) * wt_control4B_qControl_division_y) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_gain1_y - wt_control4B_qControl_division_y) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_division1_y - wt_control4B_qControl_gain1_y) - sym.Const(1e-06))) * wt_control4B_qControl_division1_y) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_division1_y - wt_control4B_qControl_gain1_y) - sym.Const(1e-06)))) * wt_control4B_qControl_gain1_y))))))
    algebraic_equations.append((wt_control4B_qControl_switch1_y - ((wt_control4B_qControl_greaterEqualThreshold_y * wt_control4B_qControl_gain2_y) + ((sym.Const(1.0) - wt_control4B_qControl_greaterEqualThreshold_y) * wt_control4B_qControl_variableLimiter1_y))))
    algebraic_equations.append((wt_control4B_qControl_add1_y - ((wt_control4B_qControl_add1_k1 * wt_control4B_qControl_antiWindupIntegrator1_y) + (wt_control4B_qControl_add1_k2 * wt_control4B_qControl_switch1_y))))
    algebraic_equations.append((wt_control4B_qControl_switch4_u_2 - (wt_control4B_qControl_gain3_k * wt_control4B_qControl_add1_y)))
    algebraic_equations.append((wt_control4B_qControl_switch4_u_1 - wt_control4B_qControl_switch4_u_2))
    algebraic_equations.append((wt_control4B_qControl_switch4_u_4 - wt_control4B_qControl_switch4_u_1))
    algebraic_equations.append(((wt_control4B_qControl_switch7_u_1 - wt_control4B_qControl_switch4_u) - (wt_control4B_qControl_integerConstant_k + sym.Const(1.0))))
    algebraic_equations.append((wt_control4B_qControl_switch6_u_3 - ((wt_control4B_qControl_add3_k1 * wt_control4B_qControl_switch6_u_1) + (wt_control4B_qControl_add3_k2 * wt_control4B_qControl_switch7_u_1))))
    algebraic_equations.append((wt_control4B_qControl_switch6_u_2 - wt_control4B_qControl_switch6_u_3))
    algebraic_equations.append(((wt_control4B_qControl_switch8_u_2 - wt_control4B_qControl_switch6_u) - (wt_control4B_qControl_integerConstant2_k + sym.Const(1.0))))
    algebraic_equations.append((wt_control4B_qControl_switch7_u_2 - ((sym.heaviside(((wt_control4B_qControl_switch8_u_2 - wt_control4B_qControl_limiter2_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_limiter2_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_switch8_u_2 - wt_control4B_qControl_limiter2_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_limiter2_uMin - wt_control4B_qControl_switch8_u_2) - sym.Const(1e-06))) * wt_control4B_qControl_limiter2_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_limiter2_uMin - wt_control4B_qControl_switch8_u_2) - sym.Const(1e-06)))) * wt_control4B_qControl_switch8_u_2))))))
    algebraic_equations.append((wt_control4B_qControl_switch8_u_1 - wt_control4B_qControl_switch8_u_2))
    algebraic_equations.append((wt_control4B_qControl_switch8_u_3 - ((wt_control4B_qControl_add4_k1 * wt_control4B_qControl_switch7_u_1) + (wt_control4B_qControl_add4_k2 * wt_control4B_qControl_const8_k))))
    algebraic_equations.append(((wt_control4B_qControl_switch8_y - wt_control4B_qControl_switch8_u) - (wt_control4B_qControl_integerConstant2_k + sym.Const(1.0))))
    algebraic_equations.append((wt_control4B_qControl_switch7_u_3 - ((sym.heaviside(((wt_control4B_qControl_switch8_y - wt_control4B_qControl_limiter3_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_limiter3_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_switch8_y - wt_control4B_qControl_limiter3_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_limiter3_uMin - wt_control4B_qControl_switch8_y) - sym.Const(1e-06))) * wt_control4B_qControl_limiter3_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_limiter3_uMin - wt_control4B_qControl_switch8_y) - sym.Const(1e-06)))) * wt_control4B_qControl_switch8_y))))))
    algebraic_equations.append(((wt_control4B_iqCmdPu - wt_control4B_qControl_switch7_u) - (wt_control4B_qControl_fFrt + sym.Const(1.0))))
    algebraic_equations.append((wt_control4B_currentLimiter_abs_y - ((sym.heaviside(((wt_control4B_iqCmdPu - sym.Const(0.0)) + sym.Const(1e-06))) * wt_control4B_iqCmdPu) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_iqCmdPu - sym.Const(0.0)) + sym.Const(1e-06)))) * (-wt_control4B_iqCmdPu)))))
    algebraic_equations.append((wt_control4B_qControl_division2_y - (wt_control4B_qControl_absLimRateLimFirstOrderFreeze_y / wt_control4B_qControl_max_y)))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_y - ((sym.heaviside(((wt_control4B_qControl_division2_y - wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_division2_y - wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMin - wt_control4B_qControl_division2_y) - sym.Const(1e-06))) * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMin - wt_control4B_qControl_division2_y) - sym.Const(1e-06)))) * wt_control4B_qControl_division2_y))))))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_feedback_y - (wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_y - wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y)))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y - (wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_k * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_feedback_y)))
    algebraic_equations.append((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_y - ((sym.heaviside(((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y - wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y - wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin - wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y) - sym.Const(1e-06))) * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin - wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y) - sym.Const(1e-06)))) * wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y))))))
    algebraic_equations.append((wt_control4B_currentLimiter_switch4_u_1 - ((((((((sym.Const(0.0) * sym.heaviside(((sym.Const(0.0) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06)))) + ((((((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.1) - sym.Const(0.0))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(0.0) - (((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.1) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.1) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0) - sym.Const(0.0)) / (sym.Const(0.15) - sym.Const(0.1))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(0.0) - (((sym.Const(1.0) - sym.Const(0.0)) / (sym.Const(0.15) - sym.Const(0.1))) * sym.Const(0.1)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.1)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.15) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(0.9) - sym.Const(0.15))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(1.0) - (((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(0.9) - sym.Const(0.15))) * sym.Const(0.15)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.15)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.9) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(0.925) - sym.Const(0.9))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(1.0) - (((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(0.925) - sym.Const(0.9))) * sym.Const(0.9)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.9)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.925) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0001) - sym.Const(1.0)) / (sym.Const(1.075) - sym.Const(0.925))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(1.0) - (((sym.Const(1.0001) - sym.Const(1.0)) / (sym.Const(1.075) - sym.Const(0.925))) * sym.Const(0.925)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.925)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.075) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0001) - sym.Const(1.0001)) / (sym.Const(1.1) - sym.Const(1.075))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(1.0001) - (((sym.Const(1.0001) - sym.Const(1.0001)) / (sym.Const(1.1) - sym.Const(1.075))) * sym.Const(1.075)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(1.075)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.1) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + (sym.Const(1.0001) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(1.1)) + sym.Const(1e-06)))))))
    algebraic_equations.append((wt_control4B_currentLimiter_combiTable1Ds_y_1 - (((((((((sym.Const(0.0) * sym.heaviside(((sym.Const(0.0) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06)))) + ((((((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.1) - sym.Const(0.0))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(0.0) - (((sym.Const(0.0) - sym.Const(0.0)) / (sym.Const(0.1) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.1) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0) - sym.Const(0.0)) / (sym.Const(0.15) - sym.Const(0.1))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(0.0) - (((sym.Const(1.0) - sym.Const(0.0)) / (sym.Const(0.15) - sym.Const(0.1))) * sym.Const(0.1)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.1)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.15) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(0.9) - sym.Const(0.15))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(1.0) - (((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(0.9) - sym.Const(0.15))) * sym.Const(0.15)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.15)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.9) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(1.0)) / (sym.Const(0.925) - sym.Const(0.9))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(1.0) - (((sym.Const(0.33) - sym.Const(1.0)) / (sym.Const(0.925) - sym.Const(0.9))) * sym.Const(0.9)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.9)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.925) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.075) - sym.Const(0.925))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.075) - sym.Const(0.925))) * sym.Const(0.925)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(0.925)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.075) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0) - sym.Const(0.33)) / (sym.Const(1.1) - sym.Const(1.075))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(1.0) - sym.Const(0.33)) / (sym.Const(1.1) - sym.Const(1.075))) * sym.Const(1.075)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(1.075)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.1) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(1.1001) - sym.Const(1.1))) * wt_controlMeasurements_firstOrder3_y) + (sym.Const(1.0) - (((sym.Const(1.0) - sym.Const(1.0)) / (sym.Const(1.1001) - sym.Const(1.1))) * sym.Const(1.1)))) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(1.1)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.1001) - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + (sym.Const(1.0) * sym.heaviside(((wt_controlMeasurements_firstOrder3_y - sym.Const(1.1001)) + sym.Const(1e-06)))))))
    algebraic_equations.append((wt_control4B_currentLimiter_switch1_u_3 - (wt_control4B_currentLimiter_combiTable1Ds_y_1 - wt_control4B_const_k)))
    algebraic_equations.append((wt_control4B_currentLimiter_switch1_u_2 - wt_control4B_currentLimiter_switch1_u_3))
    algebraic_equations.append((wt_control4B_currentLimiter_min3_y - sym.min(wt_control4B_currentLimiter_switch1_u_3, wt_control4B_currentLimiter_abs_y)))
    algebraic_equations.append((wt_control4B_currentLimiter_product3_y - (wt_control4B_currentLimiter_min3_y ** sym.Const(2.0))))
    algebraic_equations.append((wt_control4B_currentLimiter_feedback4_y - (wt_control4B_currentLimiter_product2_y - wt_control4B_currentLimiter_product3_y)))
    algebraic_equations.append((wt_control4B_currentLimiter_max1_y - sym.max(wt_control4B_currentLimiter_feedback4_y, wt_control4B_currentLimiter_const5_k)))
    algebraic_equations.append((wt_control4B_currentLimiter_sqrtNoEvent1_y - ((sym.heaviside(((wt_control4B_currentLimiter_max1_y - sym.Const(0.0)) - sym.Const(1e-06))) * sym.sqrt(wt_control4B_currentLimiter_max1_y)) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_currentLimiter_max1_y - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.Const(0.0)))))
    algebraic_equations.append((wt_control4B_currentLimiter_switch4_u_3 - sym.min(wt_control4B_currentLimiter_switch4_u_1, wt_control4B_currentLimiter_sqrtNoEvent1_y)))
    algebraic_equations.append((wt_control4B_currentLimiter_switch4_u_2 - wt_control4B_currentLimiter_switch4_u_3))
    algebraic_equations.append(((wt_control4B_currentLimiter_switch4_y - wt_control4B_currentLimiter_switch4_u) - (wt_control4B_currentLimiter_product1_y + sym.Const(1.0))))
    algebraic_equations.append((wt_control4B_ipMaxPu - (wt_control4B_currentLimiter_switch_y * wt_control4B_currentLimiter_switch4_y)))
    algebraic_equations.append((wt_control4B_pControl4B_product1_y - (wt_control4B_ipMaxPu * wt_controlMeasurements_UPu)))
    algebraic_equations.append((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_y - ((sym.heaviside(((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y - wt_control4B_pControl4B_product1_y) - sym.Const(1e-06))) * wt_control4B_pControl4B_product1_y) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y - wt_control4B_pControl4B_product1_y) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_pControl4B_const2_k - wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y) - sym.Const(1e-06))) * wt_control4B_pControl4B_const2_k) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_pControl4B_const2_k - wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y) - sym.Const(1e-06)))) * wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y))))))
    algebraic_equations.append((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_feedback1_y - (wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_y - wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y)))
    algebraic_equations.append((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_feedback_y - (wt_control4B_pControl4B_product2_y - wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_y)))
    algebraic_equations.append((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_y - (wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_k * wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_feedback_y)))
    algebraic_equations.append((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_y - ((sym.heaviside(((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_y - wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMax) - sym.Const(1e-06))) * wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_y - wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMin - wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_y) - sym.Const(1e-06))) * wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMin - wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_y) - sym.Const(1e-06)))) * wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_y))))))
    algebraic_equations.append((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_y - ((wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_k1 * wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_y) + (wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_k2 * wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_feedback1_y))))
    algebraic_equations.append((wt_control4B_ipCmdPu - (wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_y / wt_control4B_pControl4B_max_y)))
    algebraic_equations.append((wt_control4B_currentLimiter_division_y - (wt_control4B_ipCmdPu / wt_control4B_currentLimiter_switch_y)))
    algebraic_equations.append((wt_control4B_currentLimiter_min_y - sym.min(wt_control4B_currentLimiter_division_y, wt_control4B_currentLimiter_switch4_u_1)))
    algebraic_equations.append((wt_control4B_currentLimiter_product_y - (wt_control4B_currentLimiter_min_y ** sym.Const(2.0))))
    algebraic_equations.append((wt_control4B_currentLimiter_feedback_y - (wt_control4B_currentLimiter_product2_y - wt_control4B_currentLimiter_product_y)))
    algebraic_equations.append((wt_control4B_currentLimiter_max_y - sym.max(wt_control4B_currentLimiter_const1_k, wt_control4B_currentLimiter_feedback_y)))
    algebraic_equations.append((wt_control4B_currentLimiter_sqrtNoEvent_y - ((sym.heaviside(((wt_control4B_currentLimiter_max_y - sym.Const(0.0)) - sym.Const(1e-06))) * sym.sqrt(wt_control4B_currentLimiter_max_y)) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_currentLimiter_max_y - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.Const(0.0)))))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y - ((sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y - wt_control4B_ipMaxPu) - sym.Const(1e-06))) * wt_control4B_ipMaxPu) + ((sym.Const(1.0) - sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y - wt_control4B_ipMaxPu) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_wT4Injector_genSystem_const_k - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y) - sym.Const(1e-06))) * wt_wT4Injector_genSystem_const_k) + ((sym.Const(1.0) - sym.heaviside(((wt_wT4Injector_genSystem_const_k - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y) - sym.Const(1e-06)))) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y))))))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_feedback1_y - (wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y)))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_feedback_y - (wt_control4B_ipCmdPu - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y)))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y - (wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_k * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_feedback_y)))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_y - ((sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax) - sym.Const(1e-06))) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y) - sym.Const(1e-06))) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y) - sym.Const(1e-06)))) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y))))))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_y - ((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_k1 * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_y) + (wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_k2 * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_feedback1_y))))
    algebraic_equations.append((wt_control4B_currentLimiter_switch1_u_1 - sym.min(wt_control4B_currentLimiter_sqrtNoEvent_y, wt_control4B_currentLimiter_switch1_u_3)))
    algebraic_equations.append(((wt_control4B_iqMaxPu - wt_control4B_currentLimiter_switch1_u) - (wt_control4B_currentLimiter_product1_y + sym.Const(1.0))))
    algebraic_equations.append((wt_control4B_currentLimiter_gain_y - (wt_control4B_currentLimiter_gain_k * wt_control4B_iqMaxPu)))
    algebraic_equations.append((wt_control4B_currentLimiter_max2_y - sym.max(wt_control4B_currentLimiter_gain_y, wt_control4B_currentLimiter_gain1_y)))
    algebraic_equations.append((wt_control4B_currentLimiter_greater_y - sym.heaviside(((wt_control4B_iqMaxPu - wt_control4B_currentLimiter_max2_y) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_control4B_iqMinPu - ((wt_control4B_currentLimiter_greater_y * wt_control4B_currentLimiter_max2_y) + ((sym.Const(1.0) - wt_control4B_currentLimiter_greater_y) * wt_control4B_iqMaxPu))))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y - ((sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y - wt_control4B_iqMaxPu) - sym.Const(1e-06))) * wt_control4B_iqMaxPu) + ((sym.Const(1.0) - sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y - wt_control4B_iqMaxPu) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_iqMinPu - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y) - sym.Const(1e-06))) * wt_control4B_iqMinPu) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_iqMinPu - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y) - sym.Const(1e-06)))) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y))))))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback1_y - (wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y)))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback_y - (wt_control4B_iqCmdPu - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y)))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y - (wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_k * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback_y)))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_y - ((sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax) - sym.Const(1e-06))) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y) - sym.Const(1e-06))) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin - wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y) - sym.Const(1e-06)))) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y))))))
    algebraic_equations.append((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_y - ((wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k1 * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_y) + (wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k2 * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback1_y))))
    algebraic_equations.append((wt_wT4Injector_genSystem_realToComplex_im - ((cse1 * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y) + (cse2 * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y))))
    algebraic_equations.append((wt_wT4Injector_genSystem_realToComplex_re - ((cse2 * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y) - (cse1 * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y))))
    algebraic_equations.append((wt_gridProtection_combiTable1D_y_1 - (((((((((sym.Const(0.33) * sym.heaviside(((sym.Const(1.0) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06)))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.5) - sym.Const(1.0))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.5) - sym.Const(1.0))) * sym.Const(1.0)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(1.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.5) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.0) - sym.Const(1.5))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.0) - sym.Const(1.5))) * sym.Const(1.5)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(1.5)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(2.0) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.01) - sym.Const(2.0))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.01) - sym.Const(2.0))) * sym.Const(2.0)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(2.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(2.01) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.02) - sym.Const(2.01))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.02) - sym.Const(2.01))) * sym.Const(2.01)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(2.01)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(2.02) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.03) - sym.Const(2.02))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.03) - sym.Const(2.02))) * sym.Const(2.02)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(2.02)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(2.03) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.04) - sym.Const(2.03))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.04) - sym.Const(2.03))) * sym.Const(2.03)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(2.03)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(2.04) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.05) - sym.Const(2.04))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(2.05) - sym.Const(2.04))) * sym.Const(2.04)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(2.04)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(2.05) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + (sym.Const(0.33) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(2.05)) + sym.Const(1e-06)))))))
    algebraic_equations.append((whenCondition14 - sym.heaviside(((wt_gridProtection_timer_y - wt_gridProtection_combiTable1D_y_1) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_gridProtection_or1_u_1 - whenCondition14))
    algebraic_equations.append((wt_gridProtection_combiTable1D1_y_1 - ((((((((sym.Const(0.33) * sym.heaviside(((sym.Const(0.0) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06)))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(0.5) - sym.Const(0.0))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(0.5) - sym.Const(0.0))) * sym.Const(0.0)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.5) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.0) - sym.Const(0.5))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.0) - sym.Const(0.5))) * sym.Const(0.5)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(0.5)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.01) - sym.Const(1.0))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.01) - sym.Const(1.0))) * sym.Const(1.0)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(1.0)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.01) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.02) - sym.Const(1.01))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.02) - sym.Const(1.01))) * sym.Const(1.01)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(1.01)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.02) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.03) - sym.Const(1.02))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.03) - sym.Const(1.02))) * sym.Const(1.02)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(1.02)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.03) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + ((((((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.04) - sym.Const(1.03))) * wt_protectionMeasurements_firstOrder3_y) + (sym.Const(0.33) - (((sym.Const(0.33) - sym.Const(0.33)) / (sym.Const(1.04) - sym.Const(1.03))) * sym.Const(1.03)))) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(1.03)) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.04) - wt_protectionMeasurements_firstOrder3_y) - sym.Const(1e-06))))) + (sym.Const(0.33) * sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - sym.Const(1.04)) + sym.Const(1e-06)))))))
    algebraic_equations.append((whenCondition13 - sym.heaviside(((wt_gridProtection_timer1_y - wt_gridProtection_combiTable1D1_y_1) - sym.Const(1e-06)))))
    algebraic_equations.append((wt_gridProtection_pre1_u - sym.Const(0.0)))
    algebraic_equations.append((wt_wT4Injector_elecSystem_iGsRePu - (sym.Const(-100.0) * (wt_wT4Injector_genSystem_terminal_i_re / wt_wT4Injector_elecSystem_SNom))))
    algebraic_equations.append((wt_wT4Injector_elecSystem_IGsPu - (sym.Const(100.0) * ((((wt_wT4Injector_genSystem_terminal_i_re ** sym.Const(2.0)) + (wt_wT4Injector_genSystem_terminal_i_im ** sym.Const(2.0))) ** sym.Const(0.5)) / wt_wT4Injector_elecSystem_SNom))))
    algebraic_equations.append((wt_wT4Injector_elecSystem_iGsImPu - (sym.Const(-100.0) * (wt_wT4Injector_genSystem_terminal_i_im / wt_wT4Injector_elecSystem_SNom))))
    algebraic_equations.append((wt_terminal_i_re - (sym.Const(0.01) * ((-wt_controlMeasurements_iPu_re) * wt_wT4Injector_elecSystem_SNom))))
    algebraic_equations.append((wt_wT4Injector_elecSystem_UGsPu - (((wt_wT4Injector_elecSystem_uGsRePu ** sym.Const(2.0)) + (wt_wT4Injector_elecSystem_uGsImPu ** sym.Const(2.0))) ** sym.Const(0.5))))
    algebraic_equations.append((wt_protectionMeasurements_IWtPu - (((wt_controlMeasurements_iPu_re ** sym.Const(2.0)) + (wt_controlMeasurements_iPu_im ** sym.Const(2.0))) ** sym.Const(0.5))))
    algebraic_equations.append((wt_controlMeasurements_IWtPu - wt_protectionMeasurements_IWtPu))
    algebraic_equations.append((wt_protectionMeasurements_complexToPolar_len - sym.Const(0.0)))
    algebraic_equations.append((wt_controlMeasurements_complexToPolar_len - wt_protectionMeasurements_complexToPolar_len))
    algebraic_equations.append((wt_controlMeasurements_PPu - ((grid_terminal_V_re * wt_controlMeasurements_iPu_re) + (grid_terminal_V_im * wt_controlMeasurements_iPu_im))))
    algebraic_equations.append((wt_controlMeasurements_PPuSnRef - (sym.Const(0.01) * (wt_controlMeasurements_PPu * wt_controlMeasurements_SNom))))
    algebraic_equations.append((wt_protectionMeasurements_PPuSnRef - (sym.Const(0.01) * (wt_controlMeasurements_PPu * wt_protectionMeasurements_SNom))))
    algebraic_equations.append((wt_protectionMeasurements_complexToReal_re - wt_controlMeasurements_PPu))
    algebraic_equations.append((wt_controlMeasurements_complexToReal_re - wt_controlMeasurements_PPu))
    algebraic_equations.append((wt_protectionMeasurements_PPu - wt_controlMeasurements_PPu))
    algebraic_equations.append((wt_controlMeasurements_QPu - ((grid_terminal_V_im * wt_controlMeasurements_iPu_re) - (grid_terminal_V_re * wt_controlMeasurements_iPu_im))))
    algebraic_equations.append((wt_controlMeasurements_QPuSnRef - (sym.Const(0.01) * (wt_controlMeasurements_QPu * wt_controlMeasurements_SNom))))
    algebraic_equations.append((wt_controlMeasurements_complexToReal_im - ((wt_controlMeasurements_complexToReal_useConjugateInput * (-wt_controlMeasurements_QPu)) + ((sym.Const(1.0) - wt_controlMeasurements_complexToReal_useConjugateInput) * wt_controlMeasurements_QPu))))
    algebraic_equations.append((wt_protectionMeasurements_QPuSnRef - (sym.Const(0.01) * (wt_controlMeasurements_QPu * wt_protectionMeasurements_SNom))))
    algebraic_equations.append((wt_protectionMeasurements_complexToReal_im - ((wt_protectionMeasurements_complexToReal_useConjugateInput * (-wt_controlMeasurements_QPu)) + ((sym.Const(1.0) - wt_protectionMeasurements_complexToReal_useConjugateInput) * wt_controlMeasurements_QPu))))
    algebraic_equations.append((wt_protectionMeasurements_product_y_im - wt_controlMeasurements_QPu))
    algebraic_equations.append((wt_controlMeasurements_product_y_im - wt_controlMeasurements_QPu))
    algebraic_equations.append((wt_protectionMeasurements_QPu - wt_controlMeasurements_QPu))
    algebraic_equations.append((wt_terminal_i_im - (sym.Const(0.01) * ((-wt_controlMeasurements_iPu_im) * wt_wT4Injector_elecSystem_SNom))))
    algebraic_equations.append((wt_wT4Injector_QGenPu - ((grid_terminal_V_re * wt_terminal_i_im) - (grid_terminal_V_im * wt_terminal_i_re))))
    algebraic_equations.append((wt_wT4Injector_PGenPu - (((-grid_terminal_V_re) * wt_terminal_i_re) - (grid_terminal_V_im * wt_terminal_i_im))))
    algebraic_equations.append((wt_protectionMeasurements_complexToPolar_phi - sym.atan2(wt_controlMeasurements_iPu_im, (wt_controlMeasurements_iPu_re + sym.Const(2.220446049250313e-16)))))
    algebraic_equations.append((wt_controlMeasurements_complexToPolar_phi - wt_protectionMeasurements_complexToPolar_phi))
    algebraic_equations.append((wt_wT4Injector_PAgPu - ((wt_wT4Injector_elecSystem_uGsRePu * wt_wT4Injector_genSystem_product_u2_re) + (wt_wT4Injector_elecSystem_uGsImPu * wt_wT4Injector_genSystem_product_u2_im))))
    algebraic_equations.append((wt_mechanical_division1_y - (wt_wT4Injector_PAgPu / wt_mechanical_integrator1_y)))
    algebraic_equations.append((wt_mechanical_add1_y - ((wt_mechanical_add1_k1 * wt_mechanical_pI_y) + (wt_mechanical_add1_k2 * wt_mechanical_division1_y))))
    algebraic_equations.append((wt_wT4Injector_genSystem_product_y_im - ((wt_wT4Injector_elecSystem_uGsImPu * wt_wT4Injector_genSystem_product_u2_re) - (wt_wT4Injector_elecSystem_uGsRePu * wt_wT4Injector_genSystem_product_u2_im))))
    algebraic_equations.append((wt_wT4Injector_genSystem_complexToReal_im - ((wt_wT4Injector_genSystem_complexToReal_useConjugateInput * (-wt_wT4Injector_genSystem_product_y_im)) + ((sym.Const(1.0) - wt_wT4Injector_genSystem_complexToReal_useConjugateInput) * wt_wT4Injector_genSystem_product_y_im))))
    algebraic_equations.append((wt_gridProtection_or1_u_2 - whenCondition13))
    algebraic_equations.append((wt_pll_fixedBooleanDelay_y - sym.Const(0.0)))
    algebraic_equations.append((wt_pll_fixedBooleanDelay1_y - sym.Const(0.0)))
    algebraic_equations.append((wt_wT4Injector_running_value - sym.Const(1.0)))
    algebraic_equations.append(wt_wT4Injector_state)
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(wt_pll_lessThreshold_y)
    algebraic_variables.append(wt_pll_lessThreshold1_y)
    algebraic_variables.append(wt_pll_fixedBooleanDelay1_uReal)
    algebraic_variables.append(wt_pll_fixedBooleanDelay_uReal)
    algebraic_variables.append(wt_control4B_pControl4B_less_y)
    algebraic_variables.append(wt_control4B_pControl4B_and1_y)
    algebraic_variables.append(wt_controlMeasurements_omegaFiltPu)
    algebraic_variables.append(wt_controlMeasurements_derivative_y)
    algebraic_variables.append(wt_controlMeasurements_rampLimiter_feedback_y)
    algebraic_variables.append(wt_controlMeasurements_rampLimiter_gain_y)
    algebraic_variables.append(wt_controlMeasurements_rampLimiter_limiter_y)
    algebraic_variables.append(wt_gridProtection_or1_u_5)
    algebraic_variables.append(whenCondition10)
    algebraic_variables.append(wt_gridProtection_timer1_y)
    algebraic_variables.append(wt_gridProtection_lessEqual1_y)
    algebraic_variables.append(whenCondition9)
    algebraic_variables.append(wt_gridProtection_timer_y)
    algebraic_variables.append(wt_gridProtection_lessEqual_y)
    algebraic_variables.append(wt_protectionMeasurements_derivative_y)
    algebraic_variables.append(wt_protectionMeasurements_rampLimiter_feedback_y)
    algebraic_variables.append(wt_protectionMeasurements_rampLimiter_gain_y)
    algebraic_variables.append(wt_protectionMeasurements_rampLimiter_limiter_y)
    algebraic_variables.append(wt_protectionMeasurements_omegaFiltPu)
    algebraic_variables.append(wt_gridProtection_combiTable1D2_y_1)
    algebraic_variables.append(wt_gridProtection_combiTable1D3_y_1)
    algebraic_variables.append(whenCondition11)
    algebraic_variables.append(wt_gridProtection_timer2_y)
    algebraic_variables.append(whenCondition16)
    algebraic_variables.append(wt_gridProtection_or1_u_3)
    algebraic_variables.append(wt_gridProtection_lessEqual2_y)
    algebraic_variables.append(whenCondition12)
    algebraic_variables.append(wt_gridProtection_timer3_y)
    algebraic_variables.append(whenCondition15)
    algebraic_variables.append(wt_gridProtection_or1_u_4)
    algebraic_variables.append(wt_gridProtection_lessEqual3_y)
    algebraic_variables.append(wt_mechanical_add2_y)
    algebraic_variables.append(wt_mechanical_pI_y)
    algebraic_variables.append(wt_mechanical_division_y)
    algebraic_variables.append(wt_mechanical_add_y)
    algebraic_variables.append(wt_control4B_currentLimiter_add1_y)
    algebraic_variables.append(wt_control4B_currentLimiter_gain1_y)
    algebraic_variables.append(wt_control4B_currentLimiter_switch_y)
    algebraic_variables.append(wt_control4B_qControl_greaterThreshold_y)
    algebraic_variables.append(wt_control4B_qControl_booleanToInteger_y)
    algebraic_variables.append(wt_control4B_qControl_derivative_y)
    algebraic_variables.append(wt_control4B_qControl_deadZone_y)
    algebraic_variables.append(wt_control4B_qControl_switch6_u_1)
    algebraic_variables.append(whenCondition8)
    algebraic_variables.append(wt_control4B_qControl_delayFlag_booleanToInteger_y)
    algebraic_variables.append(wt_control4B_qControl_delayFlag_timer_y)
    algebraic_variables.append(wt_control4B_qControl_delayFlag_fI)
    algebraic_variables.append(wt_control4B_qControl_abs_y)
    algebraic_variables.append(wt_control4B_qControl_gain6_y)
    algebraic_variables.append(wt_control4B_qControl_gain5_y)
    algebraic_variables.append(wt_control4B_qControl_vDrop_UDropPu)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_fixedDelay_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_y)
    algebraic_variables.append(wt_control4B_qControl_delayFlag_fixedDelay_y)
    algebraic_variables.append(wt_control4B_qControl_delayFlag_switch18_y)
    algebraic_variables.append(wt_control4B_qControl_delayFlag_less1_y)
    algebraic_variables.append(wt_control4B_qControl_delayFlag_switch1_y)
    algebraic_variables.append(wt_control4B_qControl_delayFlag_fO)
    algebraic_variables.append(wt_control4B_qControl_fFrt)
    algebraic_variables.append(wt_control4B_currentLimiter_product1_y)
    algebraic_variables.append(wt_control4B_qControl_integerToReal_y)
    algebraic_variables.append(wt_control4B_qControl_greaterEqualThreshold_y)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_y)
    algebraic_variables.append(wt_control4B_qControl_switch4_u_5)
    algebraic_variables.append(wt_control4B_qControl_switch4_u_3)
    algebraic_variables.append(wt_control4B_qLimiter_integerToBoolean_y)
    algebraic_variables.append(wt_control4B_pControl4B_rampLimiter_feedback_y)
    algebraic_variables.append(wt_control4B_pControl4B_rampLimiter_gain_y)
    algebraic_variables.append(wt_control4B_pControl4B_rampLimiter_limiter_y)
    algebraic_variables.append(wt_control4B_pControl4B_product_y)
    algebraic_variables.append(wt_control4B_pControl4B_switch1_y)
    algebraic_variables.append(wt_control4B_pControl4B_product2_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_fixedDelay_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y)
    algebraic_variables.append(wt_control4B_qLimiter_combiTable1Ds2_y_1)
    algebraic_variables.append(wt_control4B_qLimiter_combiTable1Ds3_y_1)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_feedback_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_fixedDelay_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y)
    algebraic_variables.append(wt_control4B_qLimiter_combiTable1Ds_y_1)
    algebraic_variables.append(wt_control4B_qLimiter_min_y)
    algebraic_variables.append(wt_control4B_qLimiter_QWTMaxPu)
    algebraic_variables.append(wt_control4B_qLimiter_combiTable1Ds1_y_1)
    algebraic_variables.append(wt_control4B_qLimiter_max_y)
    algebraic_variables.append(wt_control4B_qLimiter_QWTMinPu)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFirstOrderFreeze_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_feedback_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_y)
    algebraic_variables.append(wt_pll_fixedBooleanDelay_yReal)
    algebraic_variables.append(whenCondition7)
    algebraic_variables.append(whenCondition6)
    algebraic_variables.append(wt_pll_fixedBooleanDelay1_yReal)
    algebraic_variables.append(whenCondition5)
    algebraic_variables.append(whenCondition4)
    algebraic_variables.append(wt_pll_absLimRateLimFirstOrderFreeze_y)
    algebraic_variables.append(wt_pll_absLimRateLimFirstOrderFreeze_feedback_y)
    algebraic_variables.append(wt_pll_absLimRateLimFirstOrderFreeze_gain_y)
    algebraic_variables.append(wt_pll_absLimRateLimFirstOrderFreeze_limiter_y)
    algebraic_variables.append(wt_pll_absLimRateLimFirstOrderFreeze_switch1_y)
    algebraic_variables.append(wt_pll_thetaPll)
    algebraic_variables.append(cse2)
    algebraic_variables.append(cse1)
    algebraic_variables.append(wt_control4B_qControl_switch2_u_4)
    algebraic_variables.append(wt_control4B_qControl_switch_u_1)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFirstOrderFreeze_feedback_y)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_y)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_y)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFirstOrderFreeze_switch1_y)
    algebraic_variables.append(wt_control4B_qControl_variableLimiter_y)
    algebraic_variables.append(wt_control4B_qControl_feedback_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_gain_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_limiter_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_max_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_switch1_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_min_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_switch2_y)
    algebraic_variables.append(wt_control4B_qControl_gain_y)
    algebraic_variables.append(wt_control4B_qControl_switch_u_4)
    algebraic_variables.append(wt_control4B_qControl_switch_u_2)
    algebraic_variables.append(wt_control4B_qControl_switch2_y)
    algebraic_variables.append(wt_control4B_currentLimiter_switch2_u_1)
    algebraic_variables.append(wt_control4B_currentLimiter_switch2_u_3)
    algebraic_variables.append(wt_control4B_currentLimiter_switch2_u_2)
    algebraic_variables.append(wt_control4B_currentLimiter_switch2_y)
    algebraic_variables.append(wt_control4B_currentLimiter_feedback1_y)
    algebraic_variables.append(wt_control4B_currentLimiter_product2_y)
    algebraic_variables.append(wt_control4B_qControl_switch_u_3)
    algebraic_variables.append(wt_control4B_qControl_switch_u_5)
    algebraic_variables.append(wt_control4B_qControl_switch_y)
    algebraic_variables.append(wt_control4B_qControl_limiter_y)
    algebraic_variables.append(wt_control4B_qControl_feedback1_y)
    algebraic_variables.append(wt_control4B_qControl_gain2_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_gain_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_limiter_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_max_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_switch1_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_min_y)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_switch2_y)
    algebraic_variables.append(wt_control4B_qControl_gain1_y)
    algebraic_variables.append(wt_control4B_qControl_switch6_u_4)
    algebraic_variables.append(wt_control4B_qControl_switch8_u_4)
    algebraic_variables.append(whenCondition3)
    algebraic_variables.append(whenCondition2)
    algebraic_variables.append(whenCondition1)
    algebraic_variables.append(wt_control4B_pControl4B_max_y)
    algebraic_variables.append(wt_control4B_qControl_max_y)
    algebraic_variables.append(wt_control4B_qControl_division_y)
    algebraic_variables.append(wt_control4B_qControl_division1_y)
    algebraic_variables.append(wt_control4B_qControl_variableLimiter1_y)
    algebraic_variables.append(wt_control4B_qControl_switch1_y)
    algebraic_variables.append(wt_control4B_qControl_add1_y)
    algebraic_variables.append(wt_control4B_qControl_switch4_u_2)
    algebraic_variables.append(wt_control4B_qControl_switch4_u_1)
    algebraic_variables.append(wt_control4B_qControl_switch4_u_4)
    algebraic_variables.append(wt_control4B_qControl_switch7_u_1)
    algebraic_variables.append(wt_control4B_qControl_switch6_u_3)
    algebraic_variables.append(wt_control4B_qControl_switch6_u_2)
    algebraic_variables.append(wt_control4B_qControl_switch8_u_2)
    algebraic_variables.append(wt_control4B_qControl_switch7_u_2)
    algebraic_variables.append(wt_control4B_qControl_switch8_u_1)
    algebraic_variables.append(wt_control4B_qControl_switch8_u_3)
    algebraic_variables.append(wt_control4B_qControl_switch8_y)
    algebraic_variables.append(wt_control4B_qControl_switch7_u_3)
    algebraic_variables.append(wt_control4B_iqCmdPu)
    algebraic_variables.append(wt_control4B_currentLimiter_abs_y)
    algebraic_variables.append(wt_control4B_qControl_division2_y)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_y)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_feedback_y)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_y)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_y)
    algebraic_variables.append(wt_control4B_currentLimiter_switch4_u_1)
    algebraic_variables.append(wt_control4B_currentLimiter_combiTable1Ds_y_1)
    algebraic_variables.append(wt_control4B_currentLimiter_switch1_u_3)
    algebraic_variables.append(wt_control4B_currentLimiter_switch1_u_2)
    algebraic_variables.append(wt_control4B_currentLimiter_min3_y)
    algebraic_variables.append(wt_control4B_currentLimiter_product3_y)
    algebraic_variables.append(wt_control4B_currentLimiter_feedback4_y)
    algebraic_variables.append(wt_control4B_currentLimiter_max1_y)
    algebraic_variables.append(wt_control4B_currentLimiter_sqrtNoEvent1_y)
    algebraic_variables.append(wt_control4B_currentLimiter_switch4_u_3)
    algebraic_variables.append(wt_control4B_currentLimiter_switch4_u_2)
    algebraic_variables.append(wt_control4B_currentLimiter_switch4_y)
    algebraic_variables.append(wt_control4B_ipMaxPu)
    algebraic_variables.append(wt_control4B_pControl4B_product1_y)
    algebraic_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_y)
    algebraic_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_feedback1_y)
    algebraic_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_feedback_y)
    algebraic_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_y)
    algebraic_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_y)
    algebraic_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_y)
    algebraic_variables.append(wt_control4B_ipCmdPu)
    algebraic_variables.append(wt_control4B_currentLimiter_division_y)
    algebraic_variables.append(wt_control4B_currentLimiter_min_y)
    algebraic_variables.append(wt_control4B_currentLimiter_product_y)
    algebraic_variables.append(wt_control4B_currentLimiter_feedback_y)
    algebraic_variables.append(wt_control4B_currentLimiter_max_y)
    algebraic_variables.append(wt_control4B_currentLimiter_sqrtNoEvent_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_feedback1_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_feedback_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_y)
    algebraic_variables.append(wt_control4B_currentLimiter_switch1_u_1)
    algebraic_variables.append(wt_control4B_iqMaxPu)
    algebraic_variables.append(wt_control4B_currentLimiter_gain_y)
    algebraic_variables.append(wt_control4B_currentLimiter_max2_y)
    algebraic_variables.append(wt_control4B_currentLimiter_greater_y)
    algebraic_variables.append(wt_control4B_iqMinPu)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback1_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_feedback_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_realToComplex_im)
    algebraic_variables.append(wt_wT4Injector_genSystem_realToComplex_re)
    algebraic_variables.append(wt_gridProtection_combiTable1D_y_1)
    algebraic_variables.append(whenCondition14)
    algebraic_variables.append(wt_gridProtection_or1_u_1)
    algebraic_variables.append(wt_gridProtection_combiTable1D1_y_1)
    algebraic_variables.append(whenCondition13)
    algebraic_variables.append(wt_gridProtection_pre1_u)
    algebraic_variables.append(wt_wT4Injector_elecSystem_iGsRePu)
    algebraic_variables.append(wt_wT4Injector_elecSystem_IGsPu)
    algebraic_variables.append(wt_wT4Injector_elecSystem_iGsImPu)
    algebraic_variables.append(wt_terminal_i_re)
    algebraic_variables.append(wt_wT4Injector_elecSystem_UGsPu)
    algebraic_variables.append(wt_protectionMeasurements_IWtPu)
    algebraic_variables.append(wt_controlMeasurements_IWtPu)
    algebraic_variables.append(wt_protectionMeasurements_complexToPolar_len)
    algebraic_variables.append(wt_controlMeasurements_complexToPolar_len)
    algebraic_variables.append(wt_controlMeasurements_PPu)
    algebraic_variables.append(wt_controlMeasurements_PPuSnRef)
    algebraic_variables.append(wt_protectionMeasurements_PPuSnRef)
    algebraic_variables.append(wt_protectionMeasurements_complexToReal_re)
    algebraic_variables.append(wt_controlMeasurements_complexToReal_re)
    algebraic_variables.append(wt_protectionMeasurements_PPu)
    algebraic_variables.append(wt_controlMeasurements_QPu)
    algebraic_variables.append(wt_controlMeasurements_QPuSnRef)
    algebraic_variables.append(wt_controlMeasurements_complexToReal_im)
    algebraic_variables.append(wt_protectionMeasurements_QPuSnRef)
    algebraic_variables.append(wt_protectionMeasurements_complexToReal_im)
    algebraic_variables.append(wt_protectionMeasurements_product_y_im)
    algebraic_variables.append(wt_controlMeasurements_product_y_im)
    algebraic_variables.append(wt_protectionMeasurements_QPu)
    algebraic_variables.append(wt_terminal_i_im)
    algebraic_variables.append(wt_wT4Injector_QGenPu)
    algebraic_variables.append(wt_wT4Injector_PGenPu)
    algebraic_variables.append(wt_protectionMeasurements_complexToPolar_phi)
    algebraic_variables.append(wt_controlMeasurements_complexToPolar_phi)
    algebraic_variables.append(wt_wT4Injector_PAgPu)
    algebraic_variables.append(wt_mechanical_division1_y)
    algebraic_variables.append(wt_mechanical_add1_y)
    algebraic_variables.append(wt_wT4Injector_genSystem_product_y_im)
    algebraic_variables.append(wt_wT4Injector_genSystem_complexToReal_im)
    algebraic_variables.append(wt_gridProtection_or1_u_2)
    algebraic_variables.append(wt_pll_fixedBooleanDelay_y)
    algebraic_variables.append(wt_pll_fixedBooleanDelay1_y)
    algebraic_variables.append(wt_wT4Injector_running_value)
    algebraic_variables.append(wt_wT4Injector_state)
    algebraic_variables.append(wt_controlMeasurements_UPu)
    algebraic_variables.append(wt_controlMeasurements_theta)
    algebraic_variables.append(wt_gridProtection_timer1_entryTime)
    algebraic_variables.append(wt_gridProtection_timer_entryTime)
    algebraic_variables.append(wt_protectionMeasurements_theta)
    algebraic_variables.append(wt_gridProtection_timer2_entryTime)
    algebraic_variables.append(wt_gridProtection_timer3_entryTime)
    algebraic_variables.append(wt_protectionMeasurements_UPu)
    algebraic_variables.append(wt_control4B_qControl_delayFlag_timer_entryTime)
    algebraic_variables.append(wt_control4B_currentLimiter_product1_u_2)
    algebraic_variables.append(wt_control4B_qControl_switch2_u_5)
    algebraic_variables.append(wt_control4B_currentLimiter_switch2_u)
    algebraic_variables.append(wt_control4B_qControl_switch_u)
    algebraic_variables.append(wt_control4B_qControl_switch4_u)
    algebraic_variables.append(wt_control4B_qControl_switch6_u)
    algebraic_variables.append(wt_control4B_qControl_switch8_u)
    algebraic_variables.append(wt_control4B_qControl_switch7_u)
    algebraic_variables.append(wt_control4B_currentLimiter_switch4_u)
    algebraic_variables.append(wt_control4B_currentLimiter_switch1_u)
    algebraic_variables.append(wt_wT4Injector_genSystem_terminal_i_re)
    algebraic_variables.append(wt_wT4Injector_genSystem_terminal_i_im)
    algebraic_variables.append(wt_controlMeasurements_iPu_re)
    algebraic_variables.append(wt_wT4Injector_elecSystem_uGsRePu)
    algebraic_variables.append(wt_wT4Injector_elecSystem_uGsImPu)
    algebraic_variables.append(wt_controlMeasurements_iPu_im)
    algebraic_variables.append(grid_terminal_V_re)
    algebraic_variables.append(grid_terminal_V_im)
    algebraic_variables.append(wt_wT4Injector_genSystem_product_u2_re)
    algebraic_variables.append(wt_wT4Injector_genSystem_product_u2_im)
    algebraic_variables.append(wt_PWTRefPu)
    algebraic_variables.append(wt_controlMeasurements_UWtPu)
    algebraic_variables.append(wt_omegaRefPu)
    algebraic_variables.append(wt_protectionMeasurements_UWtPu)
    algebraic_variables.append(wt_tanPhi)
    algebraic_variables.append(wt_xWTRefPu)
    algebraic_variables.append(wt_wT4Injector_switchOffSignal1_value)
    algebraic_variables.append(wt_wT4Injector_switchOffSignal2_value)
    algebraic_variables.append(wt_wT4Injector_switchOffSignal3_value)
    algebraic_variables.append(grid_U)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_simplifiedExpr)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_reset)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_set)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_simplifiedExpr)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_reset)
    algebraic_variables.append(wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_set)
    algebraic_variables.append(wt_pll_absLimRateLimFirstOrderFreeze_limiter_simplifiedExpr)
    algebraic_variables.append(wt_pll_absLimRateLimFirstOrderFreeze_integrator_local_reset)
    algebraic_variables.append(wt_pll_absLimRateLimFirstOrderFreeze_integrator_local_set)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_reset)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_set)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_local_reset)
    algebraic_variables.append(wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_local_set)
    algebraic_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_local_reset)
    algebraic_variables.append(wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_local_set)
    algebraic_variables.append(wt_control4B_pControl4B_rampLimiter_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_pControl4B_rampLimiter_integrator_local_reset)
    algebraic_variables.append(wt_control4B_pControl4B_rampLimiter_integrator_local_set)
    algebraic_variables.append(wt_control4B_qControl_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_limiter2_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_limiter3_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_integrator_local_reset)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_integrator_local_set)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator_limiter1_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_integrator_local_reset)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_integrator_local_set)
    algebraic_variables.append(wt_control4B_qControl_antiWindupIntegrator1_limiter1_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_local_reset)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_local_set)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_simplifiedExpr)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_reset)
    algebraic_variables.append(wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_set)
    algebraic_variables.append(wt_mechanical_integrator_local_reset)
    algebraic_variables.append(wt_mechanical_integrator_local_set)
    algebraic_variables.append(wt_mechanical_integrator1_local_reset)
    algebraic_variables.append(wt_mechanical_integrator1_local_set)
    algebraic_variables.append(wt_mechanical_pI_integrator_local_reset)
    algebraic_variables.append(wt_mechanical_pI_integrator_local_set)
    algebraic_variables.append(wt_protectionMeasurements_rampLimiter_limiter_simplifiedExpr)
    algebraic_variables.append(wt_protectionMeasurements_rampLimiter_integrator_local_reset)
    algebraic_variables.append(wt_protectionMeasurements_rampLimiter_integrator_local_set)
    algebraic_variables.append(wt_controlMeasurements_rampLimiter_limiter_simplifiedExpr)
    algebraic_variables.append(wt_controlMeasurements_rampLimiter_integrator_local_reset)
    algebraic_variables.append(wt_controlMeasurements_rampLimiter_integrator_local_set)
    algebraic_variables.append(PRE_wt_wT4Injector_running_value)
    algebraic_variables.append(START_wt_wT4Injector_running_value)
    algebraic_variables.append(PRE_wt_pll_fixedBooleanDelay1_y)
    algebraic_variables.append(START_wt_pll_fixedBooleanDelay1_y)
    algebraic_variables.append(PRE_wt_pll_fixedBooleanDelay_y)
    algebraic_variables.append(START_wt_pll_fixedBooleanDelay_y)
    algebraic_variables.append(START_wt_control4B_pControl4B_firstOrder_y)
    algebraic_variables.append(START_wt_control4B_qControl_derivative_x)
    algebraic_variables.append(START_wt_protectionMeasurements_firstOrder_y)
    algebraic_variables.append(START_wt_protectionMeasurements_firstOrder1_y)
    algebraic_variables.append(START_wt_protectionMeasurements_firstOrder2_y)
    algebraic_variables.append(START_wt_protectionMeasurements_firstOrder3_y)
    algebraic_variables.append(START_wt_protectionMeasurements_firstOrder4_y)
    algebraic_variables.append(START_wt_protectionMeasurements_derivative_x)
    algebraic_variables.append(START_wt_controlMeasurements_firstOrder_y)
    algebraic_variables.append(START_wt_controlMeasurements_firstOrder1_y)
    algebraic_variables.append(START_wt_controlMeasurements_firstOrder2_y)
    algebraic_variables.append(START_wt_controlMeasurements_firstOrder3_y)
    algebraic_variables.append(START_wt_controlMeasurements_firstOrder4_y)
    algebraic_variables.append(START_wt_controlMeasurements_derivative_x)
    algebraic_variables.append(wt_control4B_qControl_switch2_u_3)
    algebraic_variables.append(wt_control4B_qControl_switch2_u_2)
    algebraic_variables.append(wt_control4B_qControl_switch2_u_1)
    algebraic_variables.append(wt_control4B_qControl_switch2_u)
    algebraic_variables.append(PRE_wt_gridProtection_pre1_u)
    algebraic_variables.append(PRE_wt_gridProtection_timer3_entryTime)
    algebraic_variables.append(PRE_wt_gridProtection_timer2_entryTime)
    algebraic_variables.append(PRE_wt_gridProtection_timer1_entryTime)
    algebraic_variables.append(PRE_wt_gridProtection_timer_entryTime)
    algebraic_variables.append(PRE_wt_control4B_qControl_delayFlag_timer_entryTime)
    algebraic_variables.append(PRE_wt_wT4Injector_state)
    algebraic_variables.append(START_wt_wT4Injector_state)
    differential_variables: list[Var] = list()
    differential_variables.append(d_wt_controlMeasurements_firstOrder4_y)
    differential_variables.append(d_wt_controlMeasurements_derivative_x)
    differential_variables.append(d_wt_controlMeasurements_rampLimiter_integrator_y)
    differential_variables.append(d_wt_controlMeasurements_firstOrder3_y)
    differential_variables.append(d_wt_protectionMeasurements_rampLimiter_integrator_y)
    differential_variables.append(d_wt_protectionMeasurements_derivative_x)
    differential_variables.append(d_wt_protectionMeasurements_firstOrder4_y)
    differential_variables.append(d_wt_protectionMeasurements_firstOrder3_y)
    differential_variables.append(d_wt_mechanical_pI_integrator_y)
    differential_variables.append(d_wt_mechanical_integrator_y)
    differential_variables.append(d_wt_control4B_qControl_derivative_x)
    differential_variables.append(d_wt_control4B_pControl4B_rampLimiter_integrator_y)
    differential_variables.append(d_wt_control4B_pControl4B_firstOrder_y)
    differential_variables.append(d_wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y)
    differential_variables.append(d_wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y)
    differential_variables.append(d_wt_pll_absLimRateLimFirstOrderFreeze_integrator_y)
    differential_variables.append(d_wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y)
    differential_variables.append(d_wt_control4B_qControl_antiWindupIntegrator_integrator_y)
    differential_variables.append(d_wt_control4B_qControl_antiWindupIntegrator1_integrator_y)
    differential_variables.append(d_wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y)
    differential_variables.append(d_wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y)
    differential_variables.append(d_wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y)
    differential_variables.append(d_wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y)
    differential_variables.append(d_wt_controlMeasurements_firstOrder2_y)
    differential_variables.append(d_wt_protectionMeasurements_firstOrder2_y)
    differential_variables.append(d_wt_controlMeasurements_firstOrder_y)
    differential_variables.append(d_wt_protectionMeasurements_firstOrder_y)
    differential_variables.append(d_wt_controlMeasurements_firstOrder1_y)
    differential_variables.append(d_wt_protectionMeasurements_firstOrder1_y)
    differential_variables.append(d_wt_mechanical_integrator1_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[grid_UNom] = vf.add_const(1.0, name='')
    event_parameters[grid_UPhase] = vf.add_const(0.0, name='')
    event_parameters[grid_UPu] = vf.add_const(1.0, name='')
    event_parameters[wt_BesPu] = vf.add_const(0.0, name='')
    event_parameters[wt_CdrtPu] = vf.add_const(1.5, name='')
    event_parameters[wt_DPMaxP4BPu] = vf.add_const(999.0, name='')
    event_parameters[wt_DPRefMax4BPu] = vf.add_const(999.0, name='')
    event_parameters[wt_DPRefMin4BPu] = vf.add_const(-999.0, name='')
    event_parameters[wt_DUdb1Pu] = vf.add_const(-0.1, name='')
    event_parameters[wt_DUdb2Pu] = vf.add_const(0.1, name='')
    event_parameters[wt_DfcMaxPu] = vf.add_const(999.0, name='')
    event_parameters[wt_DfpMaxPu] = vf.add_const(999.0, name='')
    event_parameters[wt_DipMaxPu] = vf.add_const(999.0, name='')
    event_parameters[wt_DiqMaxPu] = vf.add_const(999.0, name='')
    event_parameters[wt_DiqMinPu] = vf.add_const(-999.0, name='')
    event_parameters[wt_GesPu] = vf.add_const(0.0, name='')
    event_parameters[wt_Hgen] = vf.add_const(1.0, name='')
    event_parameters[wt_Hwtr] = vf.add_const(5.0, name='')
    event_parameters[wt_IGsIm0Pu] = vf.add_const(0.0, name='')
    event_parameters[wt_IGsRe0Pu] = vf.add_const(0.8, name='')
    event_parameters[wt_IMaxDipPu] = vf.add_const(1.2, name='')
    event_parameters[wt_IMaxPu] = vf.add_const(1.2, name='')
    event_parameters[wt_IpMax0Pu] = vf.add_const(1.0, name='')
    event_parameters[wt_IqH1Pu] = vf.add_const(1.1, name='')
    event_parameters[wt_IqMax0Pu] = vf.add_const(1.0, name='')
    event_parameters[wt_IqMaxPu] = vf.add_const(1.1, name='')
    event_parameters[wt_IqMin0Pu] = vf.add_const(-1.0, name='')
    event_parameters[wt_IqMinPu] = vf.add_const(-1.1, name='')
    event_parameters[wt_IqPostPu] = vf.add_const(0.0, name='')
    event_parameters[wt_KdrtPu] = vf.add_const(200.0, name='')
    event_parameters[wt_Kipaw] = vf.add_const(1.0, name='')
    event_parameters[wt_Kiq] = vf.add_const(0.1, name='')
    event_parameters[wt_Kiqaw] = vf.add_const(1.0, name='')
    event_parameters[wt_Kiu] = vf.add_const(0.1, name='')
    event_parameters[wt_Kpaw] = vf.add_const(1.0, name='')
    event_parameters[wt_Kpq] = vf.add_const(1.0, name='')
    event_parameters[wt_Kpqu] = vf.add_const(0.0, name='')
    event_parameters[wt_Kpu] = vf.add_const(1.0, name='')
    event_parameters[wt_Kpufrt] = vf.add_const(2.0, name='')
    event_parameters[wt_Kqv] = vf.add_const(2.0, name='')
    event_parameters[wt_P0Pu] = vf.add_const(-0.8, name='')
    event_parameters[wt_PAg0Pu] = vf.add_const(0.8, name='')
    event_parameters[wt_Q0Pu] = vf.add_const(0.0, name='')
    event_parameters[wt_QMax0Pu] = vf.add_const(0.33, name='')
    event_parameters[wt_QMaxPu] = vf.add_const(0.33, name='')
    event_parameters[wt_QMin0Pu] = vf.add_const(-0.33, name='')
    event_parameters[wt_QMinPu] = vf.add_const(-0.33, name='')
    event_parameters[wt_RDropPu] = vf.add_const(0.0, name='')
    event_parameters[wt_ResPu] = vf.add_const(0.0, name='')
    event_parameters[wt_SNom] = vf.add_const(100.0, name='')
    event_parameters[wt_TableIpMaxUwt_1_1] = wt_TableIpMaxUwt11
    event_parameters[wt_TableIpMaxUwt_1_2] = wt_TableIpMaxUwt12
    event_parameters[wt_TableIpMaxUwt_2_1] = wt_TableIpMaxUwt21
    event_parameters[wt_TableIpMaxUwt_2_2] = wt_TableIpMaxUwt22
    event_parameters[wt_TableIpMaxUwt_3_1] = wt_TableIpMaxUwt31
    event_parameters[wt_TableIpMaxUwt_3_2] = wt_TableIpMaxUwt32
    event_parameters[wt_TableIpMaxUwt_4_1] = wt_TableIpMaxUwt41
    event_parameters[wt_TableIpMaxUwt_4_2] = wt_TableIpMaxUwt42
    event_parameters[wt_TableIpMaxUwt_5_1] = wt_TableIpMaxUwt51
    event_parameters[wt_TableIpMaxUwt_5_2] = wt_TableIpMaxUwt52
    event_parameters[wt_TableIpMaxUwt_6_1] = wt_TableIpMaxUwt61
    event_parameters[wt_TableIpMaxUwt_6_2] = wt_TableIpMaxUwt62
    event_parameters[wt_TableIpMaxUwt_7_1] = wt_TableIpMaxUwt71
    event_parameters[wt_TableIpMaxUwt_7_2] = wt_TableIpMaxUwt72
    event_parameters[wt_TableIpMaxUwt11] = vf.add_const(0.0, name='')
    event_parameters[wt_TableIpMaxUwt12] = vf.add_const(0.0, name='')
    event_parameters[wt_TableIpMaxUwt21] = vf.add_const(0.1, name='')
    event_parameters[wt_TableIpMaxUwt22] = vf.add_const(0.0, name='')
    event_parameters[wt_TableIpMaxUwt31] = vf.add_const(0.15, name='')
    event_parameters[wt_TableIpMaxUwt32] = vf.add_const(1.0, name='')
    event_parameters[wt_TableIpMaxUwt41] = vf.add_const(0.9, name='')
    event_parameters[wt_TableIpMaxUwt42] = vf.add_const(1.0, name='')
    event_parameters[wt_TableIpMaxUwt51] = vf.add_const(0.925, name='')
    event_parameters[wt_TableIpMaxUwt52] = vf.add_const(1.0, name='')
    event_parameters[wt_TableIpMaxUwt61] = vf.add_const(1.075, name='')
    event_parameters[wt_TableIpMaxUwt62] = vf.add_const(1.0001, name='')
    event_parameters[wt_TableIpMaxUwt71] = vf.add_const(1.1, name='')
    event_parameters[wt_TableIpMaxUwt72] = vf.add_const(1.0001, name='')
    event_parameters[wt_TableIqMaxUwt_1_1] = wt_TableIqMaxUwt11
    event_parameters[wt_TableIqMaxUwt_1_2] = wt_TableIqMaxUwt12
    event_parameters[wt_TableIqMaxUwt_2_1] = wt_TableIqMaxUwt21
    event_parameters[wt_TableIqMaxUwt_2_2] = wt_TableIqMaxUwt22
    event_parameters[wt_TableIqMaxUwt_3_1] = wt_TableIqMaxUwt31
    event_parameters[wt_TableIqMaxUwt_3_2] = wt_TableIqMaxUwt32
    event_parameters[wt_TableIqMaxUwt_4_1] = wt_TableIqMaxUwt41
    event_parameters[wt_TableIqMaxUwt_4_2] = wt_TableIqMaxUwt42
    event_parameters[wt_TableIqMaxUwt_5_1] = wt_TableIqMaxUwt51
    event_parameters[wt_TableIqMaxUwt_5_2] = wt_TableIqMaxUwt52
    event_parameters[wt_TableIqMaxUwt_6_1] = wt_TableIqMaxUwt61
    event_parameters[wt_TableIqMaxUwt_6_2] = wt_TableIqMaxUwt62
    event_parameters[wt_TableIqMaxUwt_7_1] = wt_TableIqMaxUwt71
    event_parameters[wt_TableIqMaxUwt_7_2] = wt_TableIqMaxUwt72
    event_parameters[wt_TableIqMaxUwt_8_1] = wt_TableIqMaxUwt81
    event_parameters[wt_TableIqMaxUwt_8_2] = wt_TableIqMaxUwt82
    event_parameters[wt_TableIqMaxUwt11] = vf.add_const(0.0, name='')
    event_parameters[wt_TableIqMaxUwt12] = vf.add_const(0.0, name='')
    event_parameters[wt_TableIqMaxUwt21] = vf.add_const(0.1, name='')
    event_parameters[wt_TableIqMaxUwt22] = vf.add_const(0.0, name='')
    event_parameters[wt_TableIqMaxUwt31] = vf.add_const(0.15, name='')
    event_parameters[wt_TableIqMaxUwt32] = vf.add_const(1.0, name='')
    event_parameters[wt_TableIqMaxUwt41] = vf.add_const(0.9, name='')
    event_parameters[wt_TableIqMaxUwt42] = vf.add_const(1.0, name='')
    event_parameters[wt_TableIqMaxUwt51] = vf.add_const(0.925, name='')
    event_parameters[wt_TableIqMaxUwt52] = vf.add_const(0.33, name='')
    event_parameters[wt_TableIqMaxUwt61] = vf.add_const(1.075, name='')
    event_parameters[wt_TableIqMaxUwt62] = vf.add_const(0.33, name='')
    event_parameters[wt_TableIqMaxUwt71] = vf.add_const(1.1, name='')
    event_parameters[wt_TableIqMaxUwt72] = vf.add_const(1.0, name='')
    event_parameters[wt_TableIqMaxUwt81] = vf.add_const(1.1001, name='')
    event_parameters[wt_TableIqMaxUwt82] = vf.add_const(1.0, name='')
    event_parameters[wt_TableQMaxPwtcFilt_1_1] = wt_TableQMaxPwtcFilt11
    event_parameters[wt_TableQMaxPwtcFilt_1_2] = wt_TableQMaxPwtcFilt12
    event_parameters[wt_TableQMaxPwtcFilt_2_1] = wt_TableQMaxPwtcFilt21
    event_parameters[wt_TableQMaxPwtcFilt_2_2] = wt_TableQMaxPwtcFilt22
    event_parameters[wt_TableQMaxPwtcFilt_3_1] = wt_TableQMaxPwtcFilt31
    event_parameters[wt_TableQMaxPwtcFilt_3_2] = wt_TableQMaxPwtcFilt32
    event_parameters[wt_TableQMaxPwtcFilt_4_1] = wt_TableQMaxPwtcFilt41
    event_parameters[wt_TableQMaxPwtcFilt_4_2] = wt_TableQMaxPwtcFilt42
    event_parameters[wt_TableQMaxPwtcFilt11] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMaxPwtcFilt12] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMaxPwtcFilt21] = vf.add_const(0.001, name='')
    event_parameters[wt_TableQMaxPwtcFilt22] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMaxPwtcFilt31] = vf.add_const(0.3, name='')
    event_parameters[wt_TableQMaxPwtcFilt32] = vf.add_const(0.33, name='')
    event_parameters[wt_TableQMaxPwtcFilt41] = vf.add_const(1.0, name='')
    event_parameters[wt_TableQMaxPwtcFilt42] = vf.add_const(0.33, name='')
    event_parameters[wt_TableQMaxUwtcFilt_1_1] = wt_TableQMaxUwtcFilt11
    event_parameters[wt_TableQMaxUwtcFilt_1_2] = wt_TableQMaxUwtcFilt12
    event_parameters[wt_TableQMaxUwtcFilt_2_1] = wt_TableQMaxUwtcFilt21
    event_parameters[wt_TableQMaxUwtcFilt_2_2] = wt_TableQMaxUwtcFilt22
    event_parameters[wt_TableQMaxUwtcFilt_3_1] = wt_TableQMaxUwtcFilt31
    event_parameters[wt_TableQMaxUwtcFilt_3_2] = wt_TableQMaxUwtcFilt32
    event_parameters[wt_TableQMaxUwtcFilt_4_1] = wt_TableQMaxUwtcFilt41
    event_parameters[wt_TableQMaxUwtcFilt_4_2] = wt_TableQMaxUwtcFilt42
    event_parameters[wt_TableQMaxUwtcFilt_5_1] = wt_TableQMaxUwtcFilt51
    event_parameters[wt_TableQMaxUwtcFilt_5_2] = wt_TableQMaxUwtcFilt52
    event_parameters[wt_TableQMaxUwtcFilt_6_1] = wt_TableQMaxUwtcFilt61
    event_parameters[wt_TableQMaxUwtcFilt_6_2] = wt_TableQMaxUwtcFilt62
    event_parameters[wt_TableQMaxUwtcFilt11] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMaxUwtcFilt12] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMaxUwtcFilt21] = vf.add_const(0.001, name='')
    event_parameters[wt_TableQMaxUwtcFilt22] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMaxUwtcFilt31] = vf.add_const(0.8, name='')
    event_parameters[wt_TableQMaxUwtcFilt32] = vf.add_const(0.33, name='')
    event_parameters[wt_TableQMaxUwtcFilt41] = vf.add_const(1.2, name='')
    event_parameters[wt_TableQMaxUwtcFilt42] = vf.add_const(0.33, name='')
    event_parameters[wt_TableQMaxUwtcFilt51] = vf.add_const(1.21, name='')
    event_parameters[wt_TableQMaxUwtcFilt52] = vf.add_const(0.33, name='')
    event_parameters[wt_TableQMaxUwtcFilt61] = vf.add_const(1.22, name='')
    event_parameters[wt_TableQMaxUwtcFilt62] = vf.add_const(0.33, name='')
    event_parameters[wt_TableQMinPwtcFilt_1_1] = wt_TableQMinPwtcFilt11
    event_parameters[wt_TableQMinPwtcFilt_1_2] = wt_TableQMinPwtcFilt12
    event_parameters[wt_TableQMinPwtcFilt_2_1] = wt_TableQMinPwtcFilt21
    event_parameters[wt_TableQMinPwtcFilt_2_2] = wt_TableQMinPwtcFilt22
    event_parameters[wt_TableQMinPwtcFilt_3_1] = wt_TableQMinPwtcFilt31
    event_parameters[wt_TableQMinPwtcFilt_3_2] = wt_TableQMinPwtcFilt32
    event_parameters[wt_TableQMinPwtcFilt_4_1] = wt_TableQMinPwtcFilt41
    event_parameters[wt_TableQMinPwtcFilt_4_2] = wt_TableQMinPwtcFilt42
    event_parameters[wt_TableQMinPwtcFilt11] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMinPwtcFilt12] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMinPwtcFilt21] = vf.add_const(0.001, name='')
    event_parameters[wt_TableQMinPwtcFilt22] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMinPwtcFilt31] = vf.add_const(0.3, name='')
    event_parameters[wt_TableQMinPwtcFilt32] = vf.add_const(-0.33, name='')
    event_parameters[wt_TableQMinPwtcFilt41] = vf.add_const(1.0, name='')
    event_parameters[wt_TableQMinPwtcFilt42] = vf.add_const(-0.33, name='')
    event_parameters[wt_TableQMinUwtcFilt_1_1] = wt_TableQMinUwtcFilt11
    event_parameters[wt_TableQMinUwtcFilt_1_2] = wt_TableQMinUwtcFilt12
    event_parameters[wt_TableQMinUwtcFilt_2_1] = wt_TableQMinUwtcFilt21
    event_parameters[wt_TableQMinUwtcFilt_2_2] = wt_TableQMinUwtcFilt22
    event_parameters[wt_TableQMinUwtcFilt_3_1] = wt_TableQMinUwtcFilt31
    event_parameters[wt_TableQMinUwtcFilt_3_2] = wt_TableQMinUwtcFilt32
    event_parameters[wt_TableQMinUwtcFilt_4_1] = wt_TableQMinUwtcFilt41
    event_parameters[wt_TableQMinUwtcFilt_4_2] = wt_TableQMinUwtcFilt42
    event_parameters[wt_TableQMinUwtcFilt11] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMinUwtcFilt12] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMinUwtcFilt21] = vf.add_const(0.001, name='')
    event_parameters[wt_TableQMinUwtcFilt22] = vf.add_const(0.0, name='')
    event_parameters[wt_TableQMinUwtcFilt31] = vf.add_const(0.8, name='')
    event_parameters[wt_TableQMinUwtcFilt32] = vf.add_const(-0.33, name='')
    event_parameters[wt_TableQMinUwtcFilt41] = vf.add_const(1.2, name='')
    event_parameters[wt_TableQMinUwtcFilt42] = vf.add_const(-0.33, name='')
    event_parameters[wt_TabletUoverUwtfilt_1_1] = wt_TabletUoverUwtfilt11
    event_parameters[wt_TabletUoverUwtfilt_1_2] = wt_TabletUoverUwtfilt12
    event_parameters[wt_TabletUoverUwtfilt_2_1] = wt_TabletUoverUwtfilt21
    event_parameters[wt_TabletUoverUwtfilt_2_2] = wt_TabletUoverUwtfilt22
    event_parameters[wt_TabletUoverUwtfilt_3_1] = wt_TabletUoverUwtfilt31
    event_parameters[wt_TabletUoverUwtfilt_3_2] = wt_TabletUoverUwtfilt32
    event_parameters[wt_TabletUoverUwtfilt_4_1] = wt_TabletUoverUwtfilt41
    event_parameters[wt_TabletUoverUwtfilt_4_2] = wt_TabletUoverUwtfilt42
    event_parameters[wt_TabletUoverUwtfilt_5_1] = wt_TabletUoverUwtfilt51
    event_parameters[wt_TabletUoverUwtfilt_5_2] = wt_TabletUoverUwtfilt52
    event_parameters[wt_TabletUoverUwtfilt_6_1] = wt_TabletUoverUwtfilt61
    event_parameters[wt_TabletUoverUwtfilt_6_2] = wt_TabletUoverUwtfilt62
    event_parameters[wt_TabletUoverUwtfilt_7_1] = wt_TabletUoverUwtfilt71
    event_parameters[wt_TabletUoverUwtfilt_7_2] = wt_TabletUoverUwtfilt72
    event_parameters[wt_TabletUoverUwtfilt_8_1] = wt_TabletUoverUwtfilt81
    event_parameters[wt_TabletUoverUwtfilt_8_2] = wt_TabletUoverUwtfilt82
    event_parameters[wt_TabletUoverUwtfilt11] = vf.add_const(1.0, name='')
    event_parameters[wt_TabletUoverUwtfilt12] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUoverUwtfilt21] = vf.add_const(1.5, name='')
    event_parameters[wt_TabletUoverUwtfilt22] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUoverUwtfilt31] = vf.add_const(2.0, name='')
    event_parameters[wt_TabletUoverUwtfilt32] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUoverUwtfilt41] = vf.add_const(2.01, name='')
    event_parameters[wt_TabletUoverUwtfilt42] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUoverUwtfilt51] = vf.add_const(2.02, name='')
    event_parameters[wt_TabletUoverUwtfilt52] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUoverUwtfilt61] = vf.add_const(2.03, name='')
    event_parameters[wt_TabletUoverUwtfilt62] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUoverUwtfilt71] = vf.add_const(2.04, name='')
    event_parameters[wt_TabletUoverUwtfilt72] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUoverUwtfilt81] = vf.add_const(2.05, name='')
    event_parameters[wt_TabletUoverUwtfilt82] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUunderUwtfilt_1_1] = wt_TabletUunderUwtfilt11
    event_parameters[wt_TabletUunderUwtfilt_1_2] = wt_TabletUunderUwtfilt12
    event_parameters[wt_TabletUunderUwtfilt_2_1] = wt_TabletUunderUwtfilt21
    event_parameters[wt_TabletUunderUwtfilt_2_2] = wt_TabletUunderUwtfilt22
    event_parameters[wt_TabletUunderUwtfilt_3_1] = wt_TabletUunderUwtfilt31
    event_parameters[wt_TabletUunderUwtfilt_3_2] = wt_TabletUunderUwtfilt32
    event_parameters[wt_TabletUunderUwtfilt_4_1] = wt_TabletUunderUwtfilt41
    event_parameters[wt_TabletUunderUwtfilt_4_2] = wt_TabletUunderUwtfilt42
    event_parameters[wt_TabletUunderUwtfilt_5_1] = wt_TabletUunderUwtfilt51
    event_parameters[wt_TabletUunderUwtfilt_5_2] = wt_TabletUunderUwtfilt52
    event_parameters[wt_TabletUunderUwtfilt_6_1] = wt_TabletUunderUwtfilt61
    event_parameters[wt_TabletUunderUwtfilt_6_2] = wt_TabletUunderUwtfilt62
    event_parameters[wt_TabletUunderUwtfilt_7_1] = wt_TabletUunderUwtfilt71
    event_parameters[wt_TabletUunderUwtfilt_7_2] = wt_TabletUunderUwtfilt72
    event_parameters[wt_TabletUunderUwtfilt11] = vf.add_const(0.0, name='')
    event_parameters[wt_TabletUunderUwtfilt12] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUunderUwtfilt21] = vf.add_const(0.5, name='')
    event_parameters[wt_TabletUunderUwtfilt22] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUunderUwtfilt31] = vf.add_const(1.0, name='')
    event_parameters[wt_TabletUunderUwtfilt32] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUunderUwtfilt41] = vf.add_const(1.01, name='')
    event_parameters[wt_TabletUunderUwtfilt42] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUunderUwtfilt51] = vf.add_const(1.02, name='')
    event_parameters[wt_TabletUunderUwtfilt52] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUunderUwtfilt61] = vf.add_const(1.03, name='')
    event_parameters[wt_TabletUunderUwtfilt62] = vf.add_const(0.33, name='')
    event_parameters[wt_TabletUunderUwtfilt71] = vf.add_const(1.04, name='')
    event_parameters[wt_TabletUunderUwtfilt72] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfoverfwtfilt_1_1] = wt_Tabletfoverfwtfilt11
    event_parameters[wt_Tabletfoverfwtfilt_1_2] = wt_Tabletfoverfwtfilt12
    event_parameters[wt_Tabletfoverfwtfilt_2_1] = wt_Tabletfoverfwtfilt21
    event_parameters[wt_Tabletfoverfwtfilt_2_2] = wt_Tabletfoverfwtfilt22
    event_parameters[wt_Tabletfoverfwtfilt_3_1] = wt_Tabletfoverfwtfilt31
    event_parameters[wt_Tabletfoverfwtfilt_3_2] = wt_Tabletfoverfwtfilt32
    event_parameters[wt_Tabletfoverfwtfilt_4_1] = wt_Tabletfoverfwtfilt41
    event_parameters[wt_Tabletfoverfwtfilt_4_2] = wt_Tabletfoverfwtfilt42
    event_parameters[wt_Tabletfoverfwtfilt11] = vf.add_const(1.0, name='')
    event_parameters[wt_Tabletfoverfwtfilt12] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfoverfwtfilt21] = vf.add_const(1.5, name='')
    event_parameters[wt_Tabletfoverfwtfilt22] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfoverfwtfilt31] = vf.add_const(2.0, name='')
    event_parameters[wt_Tabletfoverfwtfilt32] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfoverfwtfilt41] = vf.add_const(2.01, name='')
    event_parameters[wt_Tabletfoverfwtfilt42] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfunderfwtfilt_1_1] = wt_Tabletfunderfwtfilt11
    event_parameters[wt_Tabletfunderfwtfilt_1_2] = wt_Tabletfunderfwtfilt12
    event_parameters[wt_Tabletfunderfwtfilt_2_1] = wt_Tabletfunderfwtfilt21
    event_parameters[wt_Tabletfunderfwtfilt_2_2] = wt_Tabletfunderfwtfilt22
    event_parameters[wt_Tabletfunderfwtfilt_3_1] = wt_Tabletfunderfwtfilt31
    event_parameters[wt_Tabletfunderfwtfilt_3_2] = wt_Tabletfunderfwtfilt32
    event_parameters[wt_Tabletfunderfwtfilt_4_1] = wt_Tabletfunderfwtfilt41
    event_parameters[wt_Tabletfunderfwtfilt_4_2] = wt_Tabletfunderfwtfilt42
    event_parameters[wt_Tabletfunderfwtfilt_5_1] = wt_Tabletfunderfwtfilt51
    event_parameters[wt_Tabletfunderfwtfilt_5_2] = wt_Tabletfunderfwtfilt52
    event_parameters[wt_Tabletfunderfwtfilt_6_1] = wt_Tabletfunderfwtfilt61
    event_parameters[wt_Tabletfunderfwtfilt_6_2] = wt_Tabletfunderfwtfilt62
    event_parameters[wt_Tabletfunderfwtfilt11] = vf.add_const(0.0, name='')
    event_parameters[wt_Tabletfunderfwtfilt12] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfunderfwtfilt21] = vf.add_const(0.5, name='')
    event_parameters[wt_Tabletfunderfwtfilt22] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfunderfwtfilt31] = vf.add_const(1.0, name='')
    event_parameters[wt_Tabletfunderfwtfilt32] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfunderfwtfilt41] = vf.add_const(1.01, name='')
    event_parameters[wt_Tabletfunderfwtfilt42] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfunderfwtfilt51] = vf.add_const(1.02, name='')
    event_parameters[wt_Tabletfunderfwtfilt52] = vf.add_const(0.33, name='')
    event_parameters[wt_Tabletfunderfwtfilt61] = vf.add_const(1.03, name='')
    event_parameters[wt_Tabletfunderfwtfilt62] = vf.add_const(0.33, name='')
    event_parameters[wt_U0Pu] = vf.add_const(1.0, name='')
    event_parameters[wt_UGsIm0Pu] = vf.add_const(0.0, name='')
    event_parameters[wt_UGsRe0Pu] = vf.add_const(1.0, name='')
    event_parameters[wt_UMaxPu] = vf.add_const(1.1, name='')
    event_parameters[wt_UMinPu] = vf.add_const(0.9, name='')
    event_parameters[wt_UOverPu] = vf.add_const(1.3, name='')
    event_parameters[wt_UPhase0] = vf.add_const(0.0, name='')
    event_parameters[wt_UPll1Pu] = vf.add_const(0.7, name='')
    event_parameters[wt_UPll2Pu] = vf.add_const(0.4, name='')
    event_parameters[wt_URef0Pu] = vf.add_const(1.0, name='')
    event_parameters[wt_UUnderPu] = vf.add_const(0.2, name='')
    event_parameters[wt_UpDipPu] = vf.add_const(0.9, name='')
    event_parameters[wt_UpquMaxPu] = vf.add_const(1.0, name='')
    event_parameters[wt_UqDipPu] = vf.add_const(0.9, name='')
    event_parameters[wt_UqRisePu] = vf.add_const(1.1, name='')
    event_parameters[wt_XDropPu] = vf.add_const(0.0, name='')
    event_parameters[wt_XWT0Pu] = vf.add_const(0.0, name='')
    event_parameters[wt_XesPu] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_DPMaxP4BPu] = wt_DPMaxP4BPu
    event_parameters[wt_control4B_DPRefMax4BPu] = wt_DPRefMax4BPu
    event_parameters[wt_control4B_DPRefMin4BPu] = wt_DPRefMin4BPu
    event_parameters[wt_control4B_DUdb1Pu] = wt_DUdb1Pu
    event_parameters[wt_control4B_DUdb2Pu] = wt_DUdb2Pu
    event_parameters[wt_control4B_IMaxDipPu] = wt_IMaxDipPu
    event_parameters[wt_control4B_IMaxPu] = wt_IMaxPu
    event_parameters[wt_control4B_IpMax0Pu] = wt_IpMax0Pu
    event_parameters[wt_control4B_IqH1Pu] = wt_IqH1Pu
    event_parameters[wt_control4B_IqMax0Pu] = wt_IqMax0Pu
    event_parameters[wt_control4B_IqMaxPu] = wt_IqMaxPu
    event_parameters[wt_control4B_IqMin0Pu] = wt_IqMin0Pu
    event_parameters[wt_control4B_IqMinPu] = wt_IqMinPu
    event_parameters[wt_control4B_IqPostPu] = wt_IqPostPu
    event_parameters[wt_control4B_Kiq] = wt_Kiq
    event_parameters[wt_control4B_Kiu] = wt_Kiu
    event_parameters[wt_control4B_Kpaw] = wt_Kpaw
    event_parameters[wt_control4B_Kpq] = wt_Kpq
    event_parameters[wt_control4B_Kpqu] = wt_Kpqu
    event_parameters[wt_control4B_Kpu] = wt_Kpu
    event_parameters[wt_control4B_Kpufrt] = wt_Kpufrt
    event_parameters[wt_control4B_Kqv] = wt_Kqv
    event_parameters[wt_control4B_P0Pu] = wt_P0Pu
    event_parameters[wt_control4B_Q0Pu] = wt_Q0Pu
    event_parameters[wt_control4B_QMax0Pu] = wt_QMax0Pu
    event_parameters[wt_control4B_QMaxPu] = wt_QMaxPu
    event_parameters[wt_control4B_QMin0Pu] = wt_QMin0Pu
    event_parameters[wt_control4B_QMinPu] = wt_QMinPu
    event_parameters[wt_control4B_RDropPu] = wt_RDropPu
    event_parameters[wt_control4B_SNom] = wt_SNom
    event_parameters[wt_control4B_TableIpMaxUwt_1_1] = wt_TableIpMaxUwt_1_1
    event_parameters[wt_control4B_TableIpMaxUwt_1_2] = wt_TableIpMaxUwt_1_2
    event_parameters[wt_control4B_TableIpMaxUwt_2_1] = wt_TableIpMaxUwt_2_1
    event_parameters[wt_control4B_TableIpMaxUwt_2_2] = wt_TableIpMaxUwt_2_2
    event_parameters[wt_control4B_TableIpMaxUwt_3_1] = wt_TableIpMaxUwt_3_1
    event_parameters[wt_control4B_TableIpMaxUwt_3_2] = wt_TableIpMaxUwt_3_2
    event_parameters[wt_control4B_TableIpMaxUwt_4_1] = wt_TableIpMaxUwt_4_1
    event_parameters[wt_control4B_TableIpMaxUwt_4_2] = wt_TableIpMaxUwt_4_2
    event_parameters[wt_control4B_TableIpMaxUwt_5_1] = wt_TableIpMaxUwt_5_1
    event_parameters[wt_control4B_TableIpMaxUwt_5_2] = wt_TableIpMaxUwt_5_2
    event_parameters[wt_control4B_TableIpMaxUwt_6_1] = wt_TableIpMaxUwt_6_1
    event_parameters[wt_control4B_TableIpMaxUwt_6_2] = wt_TableIpMaxUwt_6_2
    event_parameters[wt_control4B_TableIpMaxUwt_7_1] = wt_TableIpMaxUwt_7_1
    event_parameters[wt_control4B_TableIpMaxUwt_7_2] = wt_TableIpMaxUwt_7_2
    event_parameters[wt_control4B_TableIpMaxUwt11] = wt_TableIpMaxUwt11
    event_parameters[wt_control4B_TableIpMaxUwt12] = wt_TableIpMaxUwt12
    event_parameters[wt_control4B_TableIpMaxUwt21] = wt_TableIpMaxUwt21
    event_parameters[wt_control4B_TableIpMaxUwt22] = wt_TableIpMaxUwt22
    event_parameters[wt_control4B_TableIpMaxUwt31] = wt_TableIpMaxUwt31
    event_parameters[wt_control4B_TableIpMaxUwt32] = wt_TableIpMaxUwt32
    event_parameters[wt_control4B_TableIpMaxUwt41] = wt_TableIpMaxUwt41
    event_parameters[wt_control4B_TableIpMaxUwt42] = wt_TableIpMaxUwt42
    event_parameters[wt_control4B_TableIpMaxUwt51] = wt_TableIpMaxUwt51
    event_parameters[wt_control4B_TableIpMaxUwt52] = wt_TableIpMaxUwt52
    event_parameters[wt_control4B_TableIpMaxUwt61] = wt_TableIpMaxUwt61
    event_parameters[wt_control4B_TableIpMaxUwt62] = wt_TableIpMaxUwt62
    event_parameters[wt_control4B_TableIpMaxUwt71] = wt_TableIpMaxUwt71
    event_parameters[wt_control4B_TableIpMaxUwt72] = wt_TableIpMaxUwt72
    event_parameters[wt_control4B_TableIqMaxUwt_1_1] = wt_control4B_TableIqMaxUwt11
    event_parameters[wt_control4B_TableIqMaxUwt_1_2] = wt_control4B_TableIqMaxUwt12
    event_parameters[wt_control4B_TableIqMaxUwt_2_1] = wt_control4B_TableIqMaxUwt21
    event_parameters[wt_control4B_TableIqMaxUwt_2_2] = wt_control4B_TableIqMaxUwt22
    event_parameters[wt_control4B_TableIqMaxUwt_3_1] = wt_control4B_TableIqMaxUwt31
    event_parameters[wt_control4B_TableIqMaxUwt_3_2] = wt_control4B_TableIqMaxUwt32
    event_parameters[wt_control4B_TableIqMaxUwt_4_1] = wt_control4B_TableIqMaxUwt41
    event_parameters[wt_control4B_TableIqMaxUwt_4_2] = wt_control4B_TableIqMaxUwt42
    event_parameters[wt_control4B_TableIqMaxUwt_5_1] = wt_control4B_TableIqMaxUwt51
    event_parameters[wt_control4B_TableIqMaxUwt_5_2] = wt_control4B_TableIqMaxUwt52
    event_parameters[wt_control4B_TableIqMaxUwt_6_1] = wt_control4B_TableIqMaxUwt61
    event_parameters[wt_control4B_TableIqMaxUwt_6_2] = wt_control4B_TableIqMaxUwt62
    event_parameters[wt_control4B_TableIqMaxUwt_7_1] = wt_control4B_TableIqMaxUwt71
    event_parameters[wt_control4B_TableIqMaxUwt_7_2] = wt_control4B_TableIqMaxUwt72
    event_parameters[wt_control4B_TableIqMaxUwt_8_1] = wt_control4B_TableIqMaxUwt81
    event_parameters[wt_control4B_TableIqMaxUwt_8_2] = wt_control4B_TableIqMaxUwt82
    event_parameters[wt_control4B_TableIqMaxUwt11] = wt_TableIqMaxUwt11
    event_parameters[wt_control4B_TableIqMaxUwt12] = wt_TableIqMaxUwt12
    event_parameters[wt_control4B_TableIqMaxUwt21] = wt_TableIqMaxUwt21
    event_parameters[wt_control4B_TableIqMaxUwt22] = wt_TableIqMaxUwt22
    event_parameters[wt_control4B_TableIqMaxUwt31] = wt_TableIqMaxUwt31
    event_parameters[wt_control4B_TableIqMaxUwt32] = wt_TableIqMaxUwt32
    event_parameters[wt_control4B_TableIqMaxUwt41] = wt_TableIqMaxUwt41
    event_parameters[wt_control4B_TableIqMaxUwt42] = wt_TableIqMaxUwt42
    event_parameters[wt_control4B_TableIqMaxUwt51] = wt_TableIqMaxUwt51
    event_parameters[wt_control4B_TableIqMaxUwt52] = wt_TableIqMaxUwt52
    event_parameters[wt_control4B_TableIqMaxUwt61] = wt_TableIqMaxUwt61
    event_parameters[wt_control4B_TableIqMaxUwt62] = wt_TableIqMaxUwt62
    event_parameters[wt_control4B_TableIqMaxUwt71] = vf.add_const(1.1, name='')
    event_parameters[wt_control4B_TableIqMaxUwt72] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_TableIqMaxUwt81] = vf.add_const(1.1001, name='')
    event_parameters[wt_control4B_TableIqMaxUwt82] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_TableQMaxPwtcFilt_1_1] = wt_control4B_TableQMaxPwtcFilt11
    event_parameters[wt_control4B_TableQMaxPwtcFilt_1_2] = wt_control4B_TableQMaxPwtcFilt12
    event_parameters[wt_control4B_TableQMaxPwtcFilt_2_1] = wt_control4B_TableQMaxPwtcFilt21
    event_parameters[wt_control4B_TableQMaxPwtcFilt_2_2] = wt_control4B_TableQMaxPwtcFilt22
    event_parameters[wt_control4B_TableQMaxPwtcFilt_3_1] = wt_control4B_TableQMaxPwtcFilt31
    event_parameters[wt_control4B_TableQMaxPwtcFilt_3_2] = wt_control4B_TableQMaxPwtcFilt32
    event_parameters[wt_control4B_TableQMaxPwtcFilt_4_1] = wt_control4B_TableQMaxPwtcFilt41
    event_parameters[wt_control4B_TableQMaxPwtcFilt_4_2] = wt_control4B_TableQMaxPwtcFilt42
    event_parameters[wt_control4B_TableQMaxPwtcFilt11] = wt_TableQMaxPwtcFilt11
    event_parameters[wt_control4B_TableQMaxPwtcFilt12] = wt_TableQMaxPwtcFilt12
    event_parameters[wt_control4B_TableQMaxPwtcFilt21] = wt_TableQMaxPwtcFilt21
    event_parameters[wt_control4B_TableQMaxPwtcFilt22] = wt_TableQMaxPwtcFilt22
    event_parameters[wt_control4B_TableQMaxPwtcFilt31] = wt_TableQMaxPwtcFilt31
    event_parameters[wt_control4B_TableQMaxPwtcFilt32] = vf.add_const(0.33, name='')
    event_parameters[wt_control4B_TableQMaxPwtcFilt41] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_TableQMaxPwtcFilt42] = vf.add_const(0.33, name='')
    event_parameters[wt_control4B_TableQMaxUwtcFilt_1_1] = wt_TableQMaxUwtcFilt_1_1
    event_parameters[wt_control4B_TableQMaxUwtcFilt_1_2] = wt_TableQMaxUwtcFilt_1_2
    event_parameters[wt_control4B_TableQMaxUwtcFilt_2_1] = wt_TableQMaxUwtcFilt_2_1
    event_parameters[wt_control4B_TableQMaxUwtcFilt_2_2] = wt_TableQMaxUwtcFilt_2_2
    event_parameters[wt_control4B_TableQMaxUwtcFilt_3_1] = wt_TableQMaxUwtcFilt_3_1
    event_parameters[wt_control4B_TableQMaxUwtcFilt_3_2] = wt_TableQMaxUwtcFilt_3_2
    event_parameters[wt_control4B_TableQMaxUwtcFilt_4_1] = wt_TableQMaxUwtcFilt_4_1
    event_parameters[wt_control4B_TableQMaxUwtcFilt_4_2] = wt_TableQMaxUwtcFilt_4_2
    event_parameters[wt_control4B_TableQMaxUwtcFilt_5_1] = wt_TableQMaxUwtcFilt_5_1
    event_parameters[wt_control4B_TableQMaxUwtcFilt_5_2] = wt_TableQMaxUwtcFilt_5_2
    event_parameters[wt_control4B_TableQMaxUwtcFilt_6_1] = wt_TableQMaxUwtcFilt_6_1
    event_parameters[wt_control4B_TableQMaxUwtcFilt_6_2] = wt_TableQMaxUwtcFilt_6_2
    event_parameters[wt_control4B_TableQMaxUwtcFilt11] = wt_TableQMaxUwtcFilt11
    event_parameters[wt_control4B_TableQMaxUwtcFilt12] = wt_TableQMaxUwtcFilt12
    event_parameters[wt_control4B_TableQMaxUwtcFilt21] = wt_TableQMaxUwtcFilt21
    event_parameters[wt_control4B_TableQMaxUwtcFilt22] = wt_TableQMaxUwtcFilt22
    event_parameters[wt_control4B_TableQMaxUwtcFilt31] = wt_TableQMaxUwtcFilt31
    event_parameters[wt_control4B_TableQMaxUwtcFilt32] = wt_TableQMaxUwtcFilt32
    event_parameters[wt_control4B_TableQMaxUwtcFilt41] = wt_TableQMaxUwtcFilt41
    event_parameters[wt_control4B_TableQMaxUwtcFilt42] = wt_TableQMaxUwtcFilt42
    event_parameters[wt_control4B_TableQMaxUwtcFilt51] = wt_TableQMaxUwtcFilt51
    event_parameters[wt_control4B_TableQMaxUwtcFilt52] = wt_TableQMaxUwtcFilt52
    event_parameters[wt_control4B_TableQMaxUwtcFilt61] = wt_TableQMaxUwtcFilt61
    event_parameters[wt_control4B_TableQMaxUwtcFilt62] = wt_TableQMaxUwtcFilt62
    event_parameters[wt_control4B_TableQMinPwtcFilt_1_1] = wt_control4B_TableQMinPwtcFilt11
    event_parameters[wt_control4B_TableQMinPwtcFilt_1_2] = wt_control4B_TableQMinPwtcFilt12
    event_parameters[wt_control4B_TableQMinPwtcFilt_2_1] = wt_control4B_TableQMinPwtcFilt21
    event_parameters[wt_control4B_TableQMinPwtcFilt_2_2] = wt_control4B_TableQMinPwtcFilt22
    event_parameters[wt_control4B_TableQMinPwtcFilt_3_1] = wt_control4B_TableQMinPwtcFilt31
    event_parameters[wt_control4B_TableQMinPwtcFilt_3_2] = wt_control4B_TableQMinPwtcFilt32
    event_parameters[wt_control4B_TableQMinPwtcFilt_4_1] = wt_control4B_TableQMinPwtcFilt41
    event_parameters[wt_control4B_TableQMinPwtcFilt_4_2] = wt_control4B_TableQMinPwtcFilt42
    event_parameters[wt_control4B_TableQMinPwtcFilt11] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_TableQMinPwtcFilt12] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_TableQMinPwtcFilt21] = vf.add_const(0.001, name='')
    event_parameters[wt_control4B_TableQMinPwtcFilt22] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_TableQMinPwtcFilt31] = vf.add_const(0.3, name='')
    event_parameters[wt_control4B_TableQMinPwtcFilt32] = vf.add_const(-0.33, name='')
    event_parameters[wt_control4B_TableQMinPwtcFilt41] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_TableQMinPwtcFilt42] = vf.add_const(-0.33, name='')
    event_parameters[wt_control4B_TableQMinUwtcFilt_1_1] = wt_TableQMinUwtcFilt_1_1
    event_parameters[wt_control4B_TableQMinUwtcFilt_1_2] = wt_TableQMinUwtcFilt_1_2
    event_parameters[wt_control4B_TableQMinUwtcFilt_2_1] = wt_TableQMinUwtcFilt_2_1
    event_parameters[wt_control4B_TableQMinUwtcFilt_2_2] = wt_TableQMinUwtcFilt_2_2
    event_parameters[wt_control4B_TableQMinUwtcFilt_3_1] = wt_TableQMinUwtcFilt_3_1
    event_parameters[wt_control4B_TableQMinUwtcFilt_3_2] = wt_TableQMinUwtcFilt_3_2
    event_parameters[wt_control4B_TableQMinUwtcFilt_4_1] = wt_TableQMinUwtcFilt_4_1
    event_parameters[wt_control4B_TableQMinUwtcFilt_4_2] = wt_TableQMinUwtcFilt_4_2
    event_parameters[wt_control4B_TableQMinUwtcFilt11] = wt_TableQMinUwtcFilt11
    event_parameters[wt_control4B_TableQMinUwtcFilt12] = wt_TableQMinUwtcFilt12
    event_parameters[wt_control4B_TableQMinUwtcFilt21] = wt_TableQMinUwtcFilt21
    event_parameters[wt_control4B_TableQMinUwtcFilt22] = wt_TableQMinUwtcFilt22
    event_parameters[wt_control4B_TableQMinUwtcFilt31] = wt_TableQMinUwtcFilt31
    event_parameters[wt_control4B_TableQMinUwtcFilt32] = wt_TableQMinUwtcFilt32
    event_parameters[wt_control4B_TableQMinUwtcFilt41] = wt_TableQMinUwtcFilt41
    event_parameters[wt_control4B_TableQMinUwtcFilt42] = wt_TableQMinUwtcFilt42
    event_parameters[wt_control4B_U0Pu] = wt_U0Pu
    event_parameters[wt_control4B_UMaxPu] = wt_UMaxPu
    event_parameters[wt_control4B_UMinPu] = wt_UMinPu
    event_parameters[wt_control4B_UPhase0] = wt_UPhase0
    event_parameters[wt_control4B_URef0Pu] = wt_URef0Pu
    event_parameters[wt_control4B_UpDipPu] = wt_UpDipPu
    event_parameters[wt_control4B_UpquMaxPu] = wt_UpquMaxPu
    event_parameters[wt_control4B_UqDipPu] = wt_UqDipPu
    event_parameters[wt_control4B_UqRisePu] = wt_UqRisePu
    event_parameters[wt_control4B_XDropPu] = wt_XDropPu
    event_parameters[wt_control4B_XWT0Pu] = wt_XWT0Pu
    event_parameters[wt_control4B_const_k] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_IMaxDipPu] = wt_control4B_IMaxDipPu
    event_parameters[wt_control4B_currentLimiter_IMaxPu] = wt_control4B_IMaxPu
    event_parameters[wt_control4B_currentLimiter_IpMax0Pu] = wt_control4B_IpMax0Pu
    event_parameters[wt_control4B_currentLimiter_IqMax0Pu] = wt_control4B_IqMax0Pu
    event_parameters[wt_control4B_currentLimiter_IqMin0Pu] = wt_control4B_IqMin0Pu
    event_parameters[wt_control4B_currentLimiter_Kpqu] = wt_control4B_Kpqu
    event_parameters[wt_control4B_currentLimiter_P0Pu] = wt_control4B_P0Pu
    event_parameters[wt_control4B_currentLimiter_Q0Pu] = wt_control4B_Q0Pu
    event_parameters[wt_control4B_currentLimiter_SNom] = wt_control4B_SNom
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_1_1] = wt_control4B_TableIpMaxUwt_1_1
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_1_2] = wt_control4B_TableIpMaxUwt_1_2
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_2_1] = wt_control4B_TableIpMaxUwt_2_1
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_2_2] = wt_control4B_TableIpMaxUwt_2_2
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_3_1] = wt_control4B_TableIpMaxUwt_3_1
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_3_2] = wt_control4B_TableIpMaxUwt_3_2
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_4_1] = wt_control4B_TableIpMaxUwt_4_1
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_4_2] = wt_control4B_TableIpMaxUwt_4_2
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_5_1] = wt_control4B_TableIpMaxUwt_5_1
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_5_2] = wt_control4B_TableIpMaxUwt_5_2
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_6_1] = wt_control4B_TableIpMaxUwt_6_1
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_6_2] = wt_control4B_TableIpMaxUwt_6_2
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_7_1] = wt_control4B_TableIpMaxUwt_7_1
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt_7_2] = wt_control4B_TableIpMaxUwt_7_2
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt11] = wt_control4B_TableIpMaxUwt11
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt12] = wt_control4B_TableIpMaxUwt12
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt21] = wt_control4B_TableIpMaxUwt21
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt22] = wt_control4B_TableIpMaxUwt22
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt31] = wt_control4B_TableIpMaxUwt31
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt32] = wt_control4B_TableIpMaxUwt32
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt41] = wt_control4B_TableIpMaxUwt41
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt42] = wt_control4B_TableIpMaxUwt42
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt51] = wt_control4B_TableIpMaxUwt51
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt52] = wt_control4B_TableIpMaxUwt52
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt61] = wt_control4B_TableIpMaxUwt61
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt62] = wt_control4B_TableIpMaxUwt62
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt71] = wt_control4B_TableIpMaxUwt71
    event_parameters[wt_control4B_currentLimiter_TableIpMaxUwt72] = wt_control4B_TableIpMaxUwt72
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_1_1] = wt_control4B_TableIqMaxUwt_1_1
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_1_2] = wt_control4B_TableIqMaxUwt_1_2
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_2_1] = wt_control4B_TableIqMaxUwt_2_1
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_2_2] = wt_control4B_TableIqMaxUwt_2_2
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_3_1] = wt_control4B_TableIqMaxUwt_3_1
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_3_2] = wt_control4B_TableIqMaxUwt_3_2
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_4_1] = wt_control4B_TableIqMaxUwt_4_1
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_4_2] = wt_control4B_TableIqMaxUwt_4_2
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_5_1] = wt_control4B_TableIqMaxUwt_5_1
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_5_2] = wt_control4B_TableIqMaxUwt_5_2
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_6_1] = wt_control4B_TableIqMaxUwt_6_1
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_6_2] = wt_control4B_TableIqMaxUwt_6_2
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_7_1] = wt_control4B_TableIqMaxUwt_7_1
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_7_2] = wt_control4B_TableIqMaxUwt_7_2
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_8_1] = wt_control4B_TableIqMaxUwt_8_1
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt_8_2] = wt_control4B_TableIqMaxUwt_8_2
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt11] = wt_control4B_TableIqMaxUwt11
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt12] = wt_control4B_TableIqMaxUwt12
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt21] = wt_control4B_TableIqMaxUwt21
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt22] = wt_control4B_TableIqMaxUwt22
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt31] = wt_control4B_TableIqMaxUwt31
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt32] = wt_control4B_TableIqMaxUwt32
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt41] = wt_control4B_TableIqMaxUwt41
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt42] = wt_control4B_TableIqMaxUwt42
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt51] = wt_control4B_TableIqMaxUwt51
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt52] = wt_control4B_TableIqMaxUwt52
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt61] = wt_control4B_TableIqMaxUwt61
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt62] = wt_control4B_TableIqMaxUwt62
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt71] = wt_control4B_TableIqMaxUwt71
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt72] = wt_control4B_TableIqMaxUwt72
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt81] = wt_control4B_TableIqMaxUwt81
    event_parameters[wt_control4B_currentLimiter_TableIqMaxUwt82] = wt_control4B_TableIqMaxUwt82
    event_parameters[wt_control4B_currentLimiter_U0Pu] = wt_control4B_U0Pu
    event_parameters[wt_control4B_currentLimiter_UPhase0] = wt_control4B_UPhase0
    event_parameters[wt_control4B_currentLimiter_UpquMaxPu] = wt_control4B_UpquMaxPu
    event_parameters[wt_control4B_currentLimiter_add1_k1] = vf.add_const(-1.0, name='')
    event_parameters[wt_control4B_currentLimiter_add1_k2] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_1_1] = wt_control4B_currentLimiter_TableIqMaxUwt_1_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_1_2] = wt_control4B_currentLimiter_TableIqMaxUwt_1_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_2_1] = wt_control4B_currentLimiter_TableIqMaxUwt_2_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_2_2] = wt_control4B_currentLimiter_TableIqMaxUwt_2_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_3_1] = wt_control4B_currentLimiter_TableIqMaxUwt_3_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_3_2] = wt_control4B_currentLimiter_TableIqMaxUwt_3_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_4_1] = wt_control4B_currentLimiter_TableIqMaxUwt_4_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_4_2] = wt_control4B_currentLimiter_TableIqMaxUwt_4_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_5_1] = wt_control4B_currentLimiter_TableIqMaxUwt_5_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_5_2] = wt_control4B_currentLimiter_TableIqMaxUwt_5_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_6_1] = wt_control4B_currentLimiter_TableIqMaxUwt_6_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_6_2] = wt_control4B_currentLimiter_TableIqMaxUwt_6_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_7_1] = wt_control4B_currentLimiter_TableIqMaxUwt_7_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_7_2] = wt_control4B_currentLimiter_TableIqMaxUwt_7_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_8_1] = wt_control4B_currentLimiter_TableIqMaxUwt_8_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_table_8_2] = wt_control4B_currentLimiter_TableIqMaxUwt_8_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_u_max] = vf.add_const(1.1001, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_u_min] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_1_1] = wt_control4B_currentLimiter_TableIpMaxUwt_1_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_1_2] = wt_control4B_currentLimiter_TableIpMaxUwt_1_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_2_1] = wt_control4B_currentLimiter_TableIpMaxUwt_2_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_2_2] = wt_control4B_currentLimiter_TableIpMaxUwt_2_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_3_1] = wt_control4B_currentLimiter_TableIpMaxUwt_3_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_3_2] = wt_control4B_currentLimiter_TableIpMaxUwt_3_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_4_1] = wt_control4B_currentLimiter_TableIpMaxUwt_4_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_4_2] = wt_control4B_currentLimiter_TableIpMaxUwt_4_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_5_1] = wt_control4B_currentLimiter_TableIpMaxUwt_5_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_5_2] = wt_control4B_currentLimiter_TableIpMaxUwt_5_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_6_1] = wt_control4B_currentLimiter_TableIpMaxUwt_6_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_6_2] = wt_control4B_currentLimiter_TableIpMaxUwt_6_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_7_1] = wt_control4B_currentLimiter_TableIpMaxUwt_7_1
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_table_7_2] = wt_control4B_currentLimiter_TableIpMaxUwt_7_2
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_u_max] = vf.add_const(1.1, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_u_min] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_const_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_currentLimiter_const1_k] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_const2_k] = wt_control4B_currentLimiter_IMaxPu
    event_parameters[wt_control4B_currentLimiter_const3_k] = wt_control4B_currentLimiter_IMaxDipPu
    event_parameters[wt_control4B_currentLimiter_const4_k] = wt_control4B_currentLimiter_UpquMaxPu
    event_parameters[wt_control4B_currentLimiter_const5_k] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_gain_k] = vf.add_const(-1.0, name='')
    event_parameters[wt_control4B_currentLimiter_gain1_k] = wt_control4B_currentLimiter_Kpqu
    event_parameters[wt_control4B_pControl4B_DPMaxP4BPu] = wt_control4B_DPMaxP4BPu
    event_parameters[wt_control4B_pControl4B_DPRefMax4BPu] = wt_control4B_DPRefMax4BPu
    event_parameters[wt_control4B_pControl4B_DPRefMin4BPu] = wt_control4B_DPRefMin4BPu
    event_parameters[wt_control4B_pControl4B_IpMax0Pu] = wt_control4B_IpMax0Pu
    event_parameters[wt_control4B_pControl4B_Kpaw] = wt_control4B_Kpaw
    event_parameters[wt_control4B_pControl4B_P0Pu] = wt_control4B_P0Pu
    event_parameters[wt_control4B_pControl4B_SNom] = wt_control4B_SNom
    event_parameters[wt_control4B_pControl4B_U0Pu] = wt_control4B_U0Pu
    event_parameters[wt_control4B_pControl4B_UpDipPu] = wt_control4B_UpDipPu
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_DyMax] = wt_control4B_pControl4B_DPMaxP4BPu
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_DyMin] = vf.add_const(-999.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_Kaw] = wt_control4B_pControl4B_Kpaw
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_Y0] = ((sym.Const(-100.0) * wt_control4B_pControl4B_P0Pu) / wt_control4B_pControl4B_SNom)
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_YMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_YMin] = (-wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_YMax)
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_add_k2] = wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_Kaw
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_gain_k] = (sym.Const(1.0) / wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_tI)
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y_start] = wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_Y0
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMax] = wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_DyMax
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_uMin] = wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_DyMin
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_tI] = wt_control4B_pControl4B_tPOrdP4B
    event_parameters[wt_control4B_pControl4B_const_k] = vf.add_const(0.01, name='')
    event_parameters[wt_control4B_pControl4B_const1_k] = wt_control4B_pControl4B_UpDipPu
    event_parameters[wt_control4B_pControl4B_const2_k] = vf.add_const(-999.0, name='')
    event_parameters[wt_control4B_pControl4B_firstOrder_T] = wt_control4B_pControl4B_tPAero
    event_parameters[wt_control4B_pControl4B_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_firstOrder_y_start] = ((sym.Const(-100.0) * wt_control4B_pControl4B_P0Pu) / wt_control4B_pControl4B_SNom)
    event_parameters[wt_control4B_pControl4B_rampLimiter_DuMax] = wt_control4B_pControl4B_DPRefMax4BPu
    event_parameters[wt_control4B_pControl4B_rampLimiter_DuMin] = wt_control4B_pControl4B_DPRefMin4BPu
    event_parameters[wt_control4B_pControl4B_rampLimiter_Y0] = ((sym.Const(-100.0) * wt_control4B_pControl4B_P0Pu) / wt_control4B_pControl4B_SNom)
    event_parameters[wt_control4B_pControl4B_rampLimiter_gain_k] = (sym.Const(1.0) / wt_control4B_pControl4B_rampLimiter_tS)
    event_parameters[wt_control4B_pControl4B_rampLimiter_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_rampLimiter_integrator_y_start] = wt_control4B_pControl4B_rampLimiter_Y0
    event_parameters[wt_control4B_pControl4B_rampLimiter_limiter_uMax] = wt_control4B_pControl4B_rampLimiter_DuMax
    event_parameters[wt_control4B_pControl4B_rampLimiter_limiter_uMin] = wt_control4B_pControl4B_rampLimiter_DuMin
    event_parameters[wt_control4B_pControl4B_rampLimiter_tS] = wt_control4B_pControl4B_tS
    event_parameters[wt_control4B_pControl4B_tPAero] = wt_control4B_tPAero
    event_parameters[wt_control4B_pControl4B_tPOrdP4B] = wt_control4B_tPOrdP4B
    event_parameters[wt_control4B_pControl4B_tS] = wt_control4B_tS
    event_parameters[wt_control4B_qControl_DUdb1Pu] = wt_control4B_DUdb1Pu
    event_parameters[wt_control4B_qControl_DUdb2Pu] = wt_control4B_DUdb2Pu
    event_parameters[wt_control4B_qControl_IqH1Pu] = wt_control4B_IqH1Pu
    event_parameters[wt_control4B_qControl_IqMaxPu] = wt_control4B_IqMaxPu
    event_parameters[wt_control4B_qControl_IqMinPu] = wt_control4B_IqMinPu
    event_parameters[wt_control4B_qControl_IqPostPu] = wt_control4B_IqPostPu
    event_parameters[wt_control4B_qControl_Kiq] = wt_control4B_Kiq
    event_parameters[wt_control4B_qControl_Kiu] = wt_control4B_Kiu
    event_parameters[wt_control4B_qControl_Kpq] = wt_control4B_Kpq
    event_parameters[wt_control4B_qControl_Kpu] = wt_control4B_Kpu
    event_parameters[wt_control4B_qControl_Kpufrt] = wt_control4B_Kpufrt
    event_parameters[wt_control4B_qControl_Kqv] = wt_control4B_Kqv
    event_parameters[wt_control4B_qControl_P0Pu] = wt_control4B_P0Pu
    event_parameters[wt_control4B_qControl_Q0Pu] = wt_control4B_Q0Pu
    event_parameters[wt_control4B_qControl_QMax0Pu] = wt_control4B_QMax0Pu
    event_parameters[wt_control4B_qControl_QMin0Pu] = wt_control4B_QMin0Pu
    event_parameters[wt_control4B_qControl_RDropPu] = wt_control4B_RDropPu
    event_parameters[wt_control4B_qControl_SNom] = wt_control4B_SNom
    event_parameters[wt_control4B_qControl_U0Pu] = wt_control4B_U0Pu
    event_parameters[wt_control4B_qControl_UMaxPu] = wt_control4B_UMaxPu
    event_parameters[wt_control4B_qControl_UMinPu] = wt_control4B_UMinPu
    event_parameters[wt_control4B_qControl_URef0Pu] = wt_control4B_URef0Pu
    event_parameters[wt_control4B_qControl_UqDipPu] = wt_control4B_UqDipPu
    event_parameters[wt_control4B_qControl_UqRisePu] = wt_control4B_UqRisePu
    event_parameters[wt_control4B_qControl_XDropPu] = wt_control4B_XDropPu
    event_parameters[wt_control4B_qControl_XWT0Pu] = wt_control4B_XWT0Pu
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_DyMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_DyMin] = (-wt_control4B_qControl_absLimRateLimFeedthroughFreeze_DyMax)
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_U0] = ((sym.Const(-100.0) * wt_control4B_qControl_Q0Pu) / (wt_control4B_qControl_U0Pu * wt_control4B_qControl_SNom))
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_Y0] = ((sym.Const(-100.0) * wt_control4B_qControl_Q0Pu) / (wt_control4B_qControl_U0Pu * wt_control4B_qControl_SNom))
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_YMax] = wt_control4B_qControl_IqMaxPu
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_YMin] = wt_control4B_qControl_IqMinPu
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_fixedDelay_delayTime] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_tS
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMax] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_YMax
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_uMin] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_YMin
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_DuMax] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_DyMax
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_DuMin] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_DyMin
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_Y0] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_Y0
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_gain_k] = (sym.Const(1.0) / wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_tS)
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y_start] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_Y0
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_DuMax
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_DuMin
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_tS] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_tS
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_tS] = wt_control4B_qControl_tS
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_DyMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_DyMin] = (-wt_control4B_qControl_absLimRateLimFirstOrderFreeze_DyMax)
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_Y0] = wt_control4B_qControl_XWT0Pu
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_YMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_YMin] = (-wt_control4B_qControl_absLimRateLimFirstOrderFreeze_YMax)
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_const_k] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_gain_k] = (sym.Const(1.0) / wt_control4B_qControl_absLimRateLimFirstOrderFreeze_tI)
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y_start] = wt_control4B_qControl_absLimRateLimFirstOrderFreeze_Y0
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMax] = wt_control4B_qControl_absLimRateLimFirstOrderFreeze_DyMax
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_uMin] = wt_control4B_qControl_absLimRateLimFirstOrderFreeze_DyMin
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_tI] = wt_control4B_qControl_tQord
    event_parameters[wt_control4B_qControl_add_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_add_k2] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_add1_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_add1_k2] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_add2_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_add2_k2] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_add3_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_add3_k2] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_add4_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_add4_k2] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_DyMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_DyMin] = (-wt_control4B_qControl_antiWindupIntegrator_DyMax)
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_Y0] = wt_control4B_qControl_U0Pu
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_YMax] = wt_control4B_qControl_UMaxPu
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_YMin] = wt_control4B_qControl_UMinPu
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_const_k] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_gain_k] = (sym.Const(1.0) / wt_control4B_qControl_antiWindupIntegrator_tI)
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_integrator_y_start] = wt_control4B_qControl_antiWindupIntegrator_Y0
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter_uMax] = wt_control4B_qControl_antiWindupIntegrator_DyMax
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter_uMin] = wt_control4B_qControl_antiWindupIntegrator_DyMin
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter1_uMax] = wt_control4B_qControl_antiWindupIntegrator_YMax
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter1_uMin] = wt_control4B_qControl_antiWindupIntegrator_YMin
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_tI] = ((sym.heaviside(((wt_control4B_qControl_Kiq - sym.Const(1e-05)) - sym.Const(1e-06))) * (sym.Const(1.0) / wt_control4B_qControl_Kiq)) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_Kiq - sym.Const(1e-05)) - sym.Const(1e-06)))) * sym.Const(4503599627370496.0)))
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_DyMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_DyMin] = (-wt_control4B_qControl_antiWindupIntegrator1_DyMax)
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_Y0] = ((sym.Const(-100.0) * wt_control4B_qControl_Q0Pu) / (wt_control4B_qControl_U0Pu * wt_control4B_qControl_SNom))
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_YMax] = wt_control4B_qControl_IqMaxPu
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_YMin] = wt_control4B_qControl_IqMinPu
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_const_k] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_gain_k] = (sym.Const(1.0) / wt_control4B_qControl_antiWindupIntegrator1_tI)
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_integrator_y_start] = wt_control4B_qControl_antiWindupIntegrator1_Y0
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter_uMax] = wt_control4B_qControl_antiWindupIntegrator1_DyMax
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter_uMin] = wt_control4B_qControl_antiWindupIntegrator1_DyMin
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMax] = wt_control4B_qControl_antiWindupIntegrator1_YMax
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter1_uMin] = wt_control4B_qControl_antiWindupIntegrator1_YMin
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_tI] = ((sym.heaviside(((wt_control4B_qControl_Kiu - sym.Const(1e-05)) - sym.Const(1e-06))) * (sym.Const(1.0) / wt_control4B_qControl_Kiu)) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_Kiu - sym.Const(1e-05)) - sym.Const(1e-06)))) * sym.Const(4503599627370496.0)))
    event_parameters[wt_control4B_qControl_const_k] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_const1_k] = wt_control4B_qControl_URef0Pu
    event_parameters[wt_control4B_qControl_const5_k] = vf.add_const(0.01, name='')
    event_parameters[wt_control4B_qControl_const8_k] = wt_control4B_qControl_IqPostPu
    event_parameters[wt_control4B_qControl_deadZone_uMax] = wt_control4B_qControl_DUdb2Pu
    event_parameters[wt_control4B_qControl_deadZone_uMin] = wt_control4B_qControl_DUdb1Pu
    event_parameters[wt_control4B_qControl_delayFlag_const7_k] = wt_control4B_qControl_delayFlag_tD
    event_parameters[wt_control4B_qControl_delayFlag_fixedDelay_delayTime] = wt_control4B_qControl_delayFlag_tS
    event_parameters[wt_control4B_qControl_delayFlag_tD] = wt_control4B_qControl_tPost
    event_parameters[wt_control4B_qControl_delayFlag_tS] = wt_control4B_qControl_tS
    event_parameters[wt_control4B_qControl_derivative_T] = wt_control4B_qControl_tUss
    event_parameters[wt_control4B_qControl_derivative_k] = wt_control4B_qControl_tUss
    event_parameters[wt_control4B_qControl_derivative_x_start] = wt_control4B_qControl_U0Pu
    event_parameters[wt_control4B_qControl_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_gain_k] = wt_control4B_qControl_Kpq
    event_parameters[wt_control4B_qControl_gain1_k] = wt_control4B_qControl_Kpu
    event_parameters[wt_control4B_qControl_gain2_k] = wt_control4B_qControl_Kpufrt
    event_parameters[wt_control4B_qControl_gain3_k] = vf.add_const(-1.0, name='')
    event_parameters[wt_control4B_qControl_gain4_k] = vf.add_const(-1.0, name='')
    event_parameters[wt_control4B_qControl_gain5_k] = vf.add_const(-1.0, name='')
    event_parameters[wt_control4B_qControl_gain6_k] = vf.add_const(-1.0, name='')
    event_parameters[wt_control4B_qControl_gain7_k] = wt_control4B_qControl_Kqv
    event_parameters[wt_control4B_qControl_greaterEqualThreshold_threshold] = vf.add_const(0.99, name='')
    event_parameters[wt_control4B_qControl_greaterThreshold_threshold] = wt_control4B_qControl_UqRisePu
    event_parameters[wt_control4B_qControl_lessThreshold_threshold] = wt_control4B_qControl_UqDipPu
    event_parameters[wt_control4B_qControl_limiter_uMax] = wt_control4B_qControl_UMaxPu
    event_parameters[wt_control4B_qControl_limiter_uMin] = wt_control4B_qControl_UMinPu
    event_parameters[wt_control4B_qControl_limiter2_uMax] = wt_control4B_qControl_IqH1Pu
    event_parameters[wt_control4B_qControl_limiter2_uMin] = wt_control4B_qControl_IqMinPu
    event_parameters[wt_control4B_qControl_limiter3_uMax] = wt_control4B_qControl_IqH1Pu
    event_parameters[wt_control4B_qControl_limiter3_uMin] = wt_control4B_qControl_IqMinPu
    event_parameters[wt_control4B_qControl_tPost] = wt_control4B_tPost
    event_parameters[wt_control4B_qControl_tQord] = wt_control4B_tQord
    event_parameters[wt_control4B_qControl_tS] = wt_control4B_tS
    event_parameters[wt_control4B_qControl_tUss] = wt_control4B_tUss
    event_parameters[wt_control4B_qControl_vDrop_P0Pu] = (sym.Const(100.0) * (wt_control4B_qControl_P0Pu / wt_control4B_qControl_SNom))
    event_parameters[wt_control4B_qControl_vDrop_Q0Pu] = (sym.Const(100.0) * (wt_control4B_qControl_Q0Pu / wt_control4B_qControl_SNom))
    event_parameters[wt_control4B_qControl_vDrop_RDropPu] = wt_control4B_qControl_RDropPu
    event_parameters[wt_control4B_qControl_vDrop_U0Pu] = wt_control4B_qControl_U0Pu
    event_parameters[wt_control4B_qControl_vDrop_UDrop0Pu] = sym.sqrt(((((wt_control4B_qControl_vDrop_U0Pu - ((wt_control4B_qControl_vDrop_RDropPu * wt_control4B_qControl_vDrop_P0Pu) / wt_control4B_qControl_vDrop_U0Pu)) - ((wt_control4B_qControl_vDrop_XDropPu * wt_control4B_qControl_vDrop_Q0Pu) / wt_control4B_qControl_vDrop_U0Pu)) ** sym.Const(2.0)) + ((((wt_control4B_qControl_vDrop_XDropPu * wt_control4B_qControl_vDrop_P0Pu) - (wt_control4B_qControl_vDrop_RDropPu * wt_control4B_qControl_vDrop_Q0Pu)) / wt_control4B_qControl_vDrop_U0Pu) ** sym.Const(2.0))))
    event_parameters[wt_control4B_qControl_vDrop_XDropPu] = wt_control4B_qControl_XDropPu
    event_parameters[wt_control4B_qLimiter_P0Pu] = wt_control4B_P0Pu
    event_parameters[wt_control4B_qLimiter_QMax0Pu] = wt_control4B_QMax0Pu
    event_parameters[wt_control4B_qLimiter_QMaxPu] = wt_control4B_QMaxPu
    event_parameters[wt_control4B_qLimiter_QMin0Pu] = wt_control4B_QMin0Pu
    event_parameters[wt_control4B_qLimiter_QMinPu] = wt_control4B_QMinPu
    event_parameters[wt_control4B_qLimiter_SNom] = wt_control4B_SNom
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt_1_1] = wt_control4B_TableQMaxPwtcFilt_1_1
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt_1_2] = wt_control4B_TableQMaxPwtcFilt_1_2
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt_2_1] = wt_control4B_TableQMaxPwtcFilt_2_1
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt_2_2] = wt_control4B_TableQMaxPwtcFilt_2_2
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt_3_1] = wt_control4B_TableQMaxPwtcFilt_3_1
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt_3_2] = wt_control4B_TableQMaxPwtcFilt_3_2
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt_4_1] = wt_control4B_TableQMaxPwtcFilt_4_1
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt_4_2] = wt_control4B_TableQMaxPwtcFilt_4_2
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt11] = wt_control4B_TableQMaxPwtcFilt11
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt12] = wt_control4B_TableQMaxPwtcFilt12
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt21] = wt_control4B_TableQMaxPwtcFilt21
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt22] = wt_control4B_TableQMaxPwtcFilt22
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt31] = wt_control4B_TableQMaxPwtcFilt31
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt32] = wt_control4B_TableQMaxPwtcFilt32
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt41] = wt_control4B_TableQMaxPwtcFilt41
    event_parameters[wt_control4B_qLimiter_TableQMaxPwtcFilt42] = wt_control4B_TableQMaxPwtcFilt42
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_1_1] = wt_control4B_TableQMaxUwtcFilt_1_1
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_1_2] = wt_control4B_TableQMaxUwtcFilt_1_2
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_2_1] = wt_control4B_TableQMaxUwtcFilt_2_1
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_2_2] = wt_control4B_TableQMaxUwtcFilt_2_2
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_3_1] = wt_control4B_TableQMaxUwtcFilt_3_1
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_3_2] = wt_control4B_TableQMaxUwtcFilt_3_2
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_4_1] = wt_control4B_TableQMaxUwtcFilt_4_1
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_4_2] = wt_control4B_TableQMaxUwtcFilt_4_2
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_5_1] = wt_control4B_TableQMaxUwtcFilt_5_1
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_5_2] = wt_control4B_TableQMaxUwtcFilt_5_2
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_6_1] = wt_control4B_TableQMaxUwtcFilt_6_1
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt_6_2] = wt_control4B_TableQMaxUwtcFilt_6_2
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt11] = wt_control4B_TableQMaxUwtcFilt11
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt12] = wt_control4B_TableQMaxUwtcFilt12
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt21] = wt_control4B_TableQMaxUwtcFilt21
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt22] = wt_control4B_TableQMaxUwtcFilt22
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt31] = wt_control4B_TableQMaxUwtcFilt31
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt32] = wt_control4B_TableQMaxUwtcFilt32
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt41] = wt_control4B_TableQMaxUwtcFilt41
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt42] = wt_control4B_TableQMaxUwtcFilt42
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt51] = wt_control4B_TableQMaxUwtcFilt51
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt52] = wt_control4B_TableQMaxUwtcFilt52
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt61] = wt_control4B_TableQMaxUwtcFilt61
    event_parameters[wt_control4B_qLimiter_TableQMaxUwtcFilt62] = wt_control4B_TableQMaxUwtcFilt62
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt_1_1] = wt_control4B_TableQMinPwtcFilt_1_1
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt_1_2] = wt_control4B_TableQMinPwtcFilt_1_2
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt_2_1] = wt_control4B_TableQMinPwtcFilt_2_1
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt_2_2] = wt_control4B_TableQMinPwtcFilt_2_2
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt_3_1] = wt_control4B_TableQMinPwtcFilt_3_1
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt_3_2] = wt_control4B_TableQMinPwtcFilt_3_2
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt_4_1] = wt_control4B_TableQMinPwtcFilt_4_1
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt_4_2] = wt_control4B_TableQMinPwtcFilt_4_2
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt11] = wt_control4B_TableQMinPwtcFilt11
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt12] = wt_control4B_TableQMinPwtcFilt12
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt21] = wt_control4B_TableQMinPwtcFilt21
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt22] = wt_control4B_TableQMinPwtcFilt22
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt31] = wt_control4B_TableQMinPwtcFilt31
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt32] = wt_control4B_TableQMinPwtcFilt32
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt41] = wt_control4B_TableQMinPwtcFilt41
    event_parameters[wt_control4B_qLimiter_TableQMinPwtcFilt42] = wt_control4B_TableQMinPwtcFilt42
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt_1_1] = wt_control4B_TableQMinUwtcFilt_1_1
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt_1_2] = wt_control4B_TableQMinUwtcFilt_1_2
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt_2_1] = wt_control4B_TableQMinUwtcFilt_2_1
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt_2_2] = wt_control4B_TableQMinUwtcFilt_2_2
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt_3_1] = wt_control4B_TableQMinUwtcFilt_3_1
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt_3_2] = wt_control4B_TableQMinUwtcFilt_3_2
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt_4_1] = wt_control4B_TableQMinUwtcFilt_4_1
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt_4_2] = wt_control4B_TableQMinUwtcFilt_4_2
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt11] = wt_control4B_TableQMinUwtcFilt11
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt12] = wt_control4B_TableQMinUwtcFilt12
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt21] = wt_control4B_TableQMinUwtcFilt21
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt22] = wt_control4B_TableQMinUwtcFilt22
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt31] = wt_control4B_TableQMinUwtcFilt31
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt32] = wt_control4B_TableQMinUwtcFilt32
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt41] = wt_control4B_TableQMinUwtcFilt41
    event_parameters[wt_control4B_qLimiter_TableQMinUwtcFilt42] = wt_control4B_TableQMinUwtcFilt42
    event_parameters[wt_control4B_qLimiter_U0Pu] = wt_control4B_U0Pu
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_DyMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_DyMin] = (-wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_DyMax)
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_U0] = wt_control4B_qLimiter_U0Pu
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_Y0] = wt_control4B_qLimiter_U0Pu
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_YMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_YMin] = (-wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_YMax)
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_fixedDelay_delayTime] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_tS
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMax] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_YMax
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_uMin] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_YMin
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_DuMax] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_DyMax
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_DuMin] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_DyMin
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_Y0] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_Y0
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_gain_k] = (sym.Const(1.0) / wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_tS)
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y_start] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_Y0
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMax] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_DuMax
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_uMin] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_DuMin
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_tS] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_tS
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_tS] = wt_control4B_qLimiter_tS
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_DyMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_DyMin] = (-wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_DyMax)
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_U0] = ((sym.Const(-100.0) * wt_control4B_qLimiter_P0Pu) / wt_control4B_qLimiter_SNom)
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_Y0] = ((sym.Const(-100.0) * wt_control4B_qLimiter_P0Pu) / wt_control4B_qLimiter_SNom)
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_YMax] = vf.add_const(999.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_YMin] = (-wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_YMax)
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_fixedDelay_delayTime] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_tS
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMax] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_YMax
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_uMin] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_YMin
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_DuMax] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_DyMax
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_DuMin] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_DyMin
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_Y0] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_Y0
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_gain_k] = (sym.Const(1.0) / wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_tS)
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y_start] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_Y0
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMax] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_DuMax
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_uMin] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_DuMin
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_tS] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_tS
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_tS] = wt_control4B_qLimiter_tS
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_1_1] = wt_control4B_qLimiter_TableQMaxUwtcFilt_1_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_1_2] = wt_control4B_qLimiter_TableQMaxUwtcFilt_1_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_2_1] = wt_control4B_qLimiter_TableQMaxUwtcFilt_2_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_2_2] = wt_control4B_qLimiter_TableQMaxUwtcFilt_2_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_3_1] = wt_control4B_qLimiter_TableQMaxUwtcFilt_3_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_3_2] = wt_control4B_qLimiter_TableQMaxUwtcFilt_3_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_4_1] = wt_control4B_qLimiter_TableQMaxUwtcFilt_4_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_4_2] = wt_control4B_qLimiter_TableQMaxUwtcFilt_4_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_5_1] = wt_control4B_qLimiter_TableQMaxUwtcFilt_5_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_5_2] = wt_control4B_qLimiter_TableQMaxUwtcFilt_5_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_6_1] = wt_control4B_qLimiter_TableQMaxUwtcFilt_6_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_table_6_2] = wt_control4B_qLimiter_TableQMaxUwtcFilt_6_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_u_max] = vf.add_const(1.22, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_u_min] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_table_1_1] = wt_control4B_qLimiter_TableQMinUwtcFilt_1_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_table_1_2] = wt_control4B_qLimiter_TableQMinUwtcFilt_1_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_table_2_1] = wt_control4B_qLimiter_TableQMinUwtcFilt_2_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_table_2_2] = wt_control4B_qLimiter_TableQMinUwtcFilt_2_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_table_3_1] = wt_control4B_qLimiter_TableQMinUwtcFilt_3_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_table_3_2] = wt_control4B_qLimiter_TableQMinUwtcFilt_3_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_table_4_1] = wt_control4B_qLimiter_TableQMinUwtcFilt_4_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_table_4_2] = wt_control4B_qLimiter_TableQMinUwtcFilt_4_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_u_max] = vf.add_const(1.2, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_u_min] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_table_1_1] = wt_control4B_qLimiter_TableQMaxPwtcFilt_1_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_table_1_2] = wt_control4B_qLimiter_TableQMaxPwtcFilt_1_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_table_2_1] = wt_control4B_qLimiter_TableQMaxPwtcFilt_2_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_table_2_2] = wt_control4B_qLimiter_TableQMaxPwtcFilt_2_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_table_3_1] = wt_control4B_qLimiter_TableQMaxPwtcFilt_3_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_table_3_2] = wt_control4B_qLimiter_TableQMaxPwtcFilt_3_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_table_4_1] = wt_control4B_qLimiter_TableQMaxPwtcFilt_4_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_table_4_2] = wt_control4B_qLimiter_TableQMaxPwtcFilt_4_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_u_max] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_u_min] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_table_1_1] = wt_control4B_qLimiter_TableQMinPwtcFilt_1_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_table_1_2] = wt_control4B_qLimiter_TableQMinPwtcFilt_1_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_table_2_1] = wt_control4B_qLimiter_TableQMinPwtcFilt_2_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_table_2_2] = wt_control4B_qLimiter_TableQMinPwtcFilt_2_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_table_3_1] = wt_control4B_qLimiter_TableQMinPwtcFilt_3_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_table_3_2] = wt_control4B_qLimiter_TableQMinPwtcFilt_3_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_table_4_1] = wt_control4B_qLimiter_TableQMinPwtcFilt_4_1
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_table_4_2] = wt_control4B_qLimiter_TableQMinPwtcFilt_4_2
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_u_max] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_u_min] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_const_k] = wt_control4B_qLimiter_QMaxPu
    event_parameters[wt_control4B_qLimiter_constant1_k] = wt_control4B_qLimiter_QMinPu
    event_parameters[wt_control4B_qLimiter_tS] = wt_control4B_tS
    event_parameters[wt_control4B_tPAero] = wt_tPAero
    event_parameters[wt_control4B_tPOrdP4B] = wt_tPOrdP4B
    event_parameters[wt_control4B_tPost] = wt_tPost
    event_parameters[wt_control4B_tQord] = wt_tQord
    event_parameters[wt_control4B_tS] = wt_tS
    event_parameters[wt_control4B_tUss] = wt_tUss
    event_parameters[wt_controlMeasurements_DfMaxPu] = wt_DfcMaxPu
    event_parameters[wt_controlMeasurements_P0Pu] = wt_P0Pu
    event_parameters[wt_controlMeasurements_Q0Pu] = wt_Q0Pu
    event_parameters[wt_controlMeasurements_SNom] = wt_SNom
    event_parameters[wt_controlMeasurements_U0Pu] = wt_U0Pu
    event_parameters[wt_controlMeasurements_UPhase0] = wt_UPhase0
    event_parameters[wt_controlMeasurements_add_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_add_k2] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_derivative_T] = (sym.Const(0.05) * wt_controlMeasurements_tfFilt)
    event_parameters[wt_controlMeasurements_derivative_k] = vf.add_const(0.0031830988618379067, name='')
    event_parameters[wt_controlMeasurements_derivative_x_start] = wt_controlMeasurements_UPhase0
    event_parameters[wt_controlMeasurements_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder_T] = wt_controlMeasurements_tPFilt
    event_parameters[wt_controlMeasurements_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder_y_start] = ((sym.Const(-100.0) * wt_controlMeasurements_P0Pu) / wt_controlMeasurements_SNom)
    event_parameters[wt_controlMeasurements_firstOrder1_T] = wt_controlMeasurements_tQFilt
    event_parameters[wt_controlMeasurements_firstOrder1_k] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder1_y_start] = ((sym.Const(-100.0) * wt_controlMeasurements_Q0Pu) / wt_controlMeasurements_SNom)
    event_parameters[wt_controlMeasurements_firstOrder2_T] = wt_controlMeasurements_tIFilt
    event_parameters[wt_controlMeasurements_firstOrder2_k] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder2_y_start] = (sym.Const(100.0) * ((((wt_controlMeasurements_i0Pu_re ** sym.Const(2.0)) + (wt_controlMeasurements_i0Pu_im ** sym.Const(2.0))) ** sym.Const(0.5)) / wt_controlMeasurements_SNom))
    event_parameters[wt_controlMeasurements_firstOrder3_T] = wt_controlMeasurements_tUFilt
    event_parameters[wt_controlMeasurements_firstOrder3_k] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder3_y_start] = wt_controlMeasurements_U0Pu
    event_parameters[wt_controlMeasurements_firstOrder4_T] = wt_controlMeasurements_tfFilt
    event_parameters[wt_controlMeasurements_firstOrder4_k] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder4_y_start] = vf.add_const(0.0, name='')
    event_parameters[wt_controlMeasurements_i0Pu_im] = wt_i0Pu_im
    event_parameters[wt_controlMeasurements_i0Pu_re] = wt_i0Pu_re
    event_parameters[wt_controlMeasurements_rampLimiter_DuMax] = wt_controlMeasurements_DfMaxPu
    event_parameters[wt_controlMeasurements_rampLimiter_DuMin] = (-wt_controlMeasurements_rampLimiter_DuMax)
    event_parameters[wt_controlMeasurements_rampLimiter_Y0] = vf.add_const(0.0, name='')
    event_parameters[wt_controlMeasurements_rampLimiter_gain_k] = (sym.Const(1.0) / wt_controlMeasurements_rampLimiter_tS)
    event_parameters[wt_controlMeasurements_rampLimiter_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_rampLimiter_integrator_y_start] = wt_controlMeasurements_rampLimiter_Y0
    event_parameters[wt_controlMeasurements_rampLimiter_limiter_uMax] = wt_controlMeasurements_rampLimiter_DuMax
    event_parameters[wt_controlMeasurements_rampLimiter_limiter_uMin] = wt_controlMeasurements_rampLimiter_DuMin
    event_parameters[wt_controlMeasurements_rampLimiter_tS] = wt_controlMeasurements_tS
    event_parameters[wt_controlMeasurements_tIFilt] = wt_tIcFilt
    event_parameters[wt_controlMeasurements_tPFilt] = wt_tPcFilt
    event_parameters[wt_controlMeasurements_tQFilt] = wt_tQcFilt
    event_parameters[wt_controlMeasurements_tS] = wt_tS
    event_parameters[wt_controlMeasurements_tUFilt] = wt_tUcFilt
    event_parameters[wt_controlMeasurements_tfFilt] = wt_tfcFilt
    event_parameters[wt_controlMeasurements_u0Pu_im] = wt_u0Pu_im
    event_parameters[wt_controlMeasurements_u0Pu_re] = wt_u0Pu_re
    event_parameters[wt_fOverPu] = vf.add_const(1.1, name='')
    event_parameters[wt_fUnderPu] = vf.add_const(0.9, name='')
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_1_1] = wt_TabletUoverUwtfilt_1_1
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_1_2] = wt_TabletUoverUwtfilt_1_2
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_2_1] = wt_TabletUoverUwtfilt_2_1
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_2_2] = wt_TabletUoverUwtfilt_2_2
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_3_1] = wt_TabletUoverUwtfilt_3_1
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_3_2] = wt_TabletUoverUwtfilt_3_2
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_4_1] = wt_TabletUoverUwtfilt_4_1
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_4_2] = wt_TabletUoverUwtfilt_4_2
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_5_1] = wt_TabletUoverUwtfilt_5_1
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_5_2] = wt_TabletUoverUwtfilt_5_2
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_6_1] = wt_TabletUoverUwtfilt_6_1
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_6_2] = wt_TabletUoverUwtfilt_6_2
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_7_1] = wt_TabletUoverUwtfilt_7_1
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_7_2] = wt_TabletUoverUwtfilt_7_2
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_8_1] = wt_TabletUoverUwtfilt_8_1
    event_parameters[wt_gridProtection_TabletUoverUwtfilt_8_2] = wt_TabletUoverUwtfilt_8_2
    event_parameters[wt_gridProtection_TabletUoverUwtfilt11] = wt_TabletUoverUwtfilt11
    event_parameters[wt_gridProtection_TabletUoverUwtfilt12] = wt_TabletUoverUwtfilt12
    event_parameters[wt_gridProtection_TabletUoverUwtfilt21] = wt_TabletUoverUwtfilt21
    event_parameters[wt_gridProtection_TabletUoverUwtfilt22] = wt_TabletUoverUwtfilt22
    event_parameters[wt_gridProtection_TabletUoverUwtfilt31] = wt_TabletUoverUwtfilt31
    event_parameters[wt_gridProtection_TabletUoverUwtfilt32] = wt_TabletUoverUwtfilt32
    event_parameters[wt_gridProtection_TabletUoverUwtfilt41] = wt_TabletUoverUwtfilt41
    event_parameters[wt_gridProtection_TabletUoverUwtfilt42] = wt_TabletUoverUwtfilt42
    event_parameters[wt_gridProtection_TabletUoverUwtfilt51] = wt_TabletUoverUwtfilt51
    event_parameters[wt_gridProtection_TabletUoverUwtfilt52] = wt_TabletUoverUwtfilt52
    event_parameters[wt_gridProtection_TabletUoverUwtfilt61] = wt_TabletUoverUwtfilt61
    event_parameters[wt_gridProtection_TabletUoverUwtfilt62] = wt_TabletUoverUwtfilt62
    event_parameters[wt_gridProtection_TabletUoverUwtfilt71] = wt_TabletUoverUwtfilt71
    event_parameters[wt_gridProtection_TabletUoverUwtfilt72] = wt_TabletUoverUwtfilt72
    event_parameters[wt_gridProtection_TabletUoverUwtfilt81] = wt_TabletUoverUwtfilt81
    event_parameters[wt_gridProtection_TabletUoverUwtfilt82] = wt_TabletUoverUwtfilt82
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_1_1] = wt_TabletUunderUwtfilt_1_1
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_1_2] = wt_TabletUunderUwtfilt_1_2
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_2_1] = wt_TabletUunderUwtfilt_2_1
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_2_2] = wt_TabletUunderUwtfilt_2_2
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_3_1] = wt_TabletUunderUwtfilt_3_1
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_3_2] = wt_TabletUunderUwtfilt_3_2
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_4_1] = wt_TabletUunderUwtfilt_4_1
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_4_2] = wt_TabletUunderUwtfilt_4_2
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_5_1] = wt_TabletUunderUwtfilt_5_1
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_5_2] = wt_TabletUunderUwtfilt_5_2
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_6_1] = wt_TabletUunderUwtfilt_6_1
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_6_2] = wt_TabletUunderUwtfilt_6_2
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_7_1] = wt_TabletUunderUwtfilt_7_1
    event_parameters[wt_gridProtection_TabletUunderUwtfilt_7_2] = wt_TabletUunderUwtfilt_7_2
    event_parameters[wt_gridProtection_TabletUunderUwtfilt11] = wt_TabletUunderUwtfilt11
    event_parameters[wt_gridProtection_TabletUunderUwtfilt12] = wt_TabletUunderUwtfilt12
    event_parameters[wt_gridProtection_TabletUunderUwtfilt21] = wt_TabletUunderUwtfilt21
    event_parameters[wt_gridProtection_TabletUunderUwtfilt22] = wt_TabletUunderUwtfilt22
    event_parameters[wt_gridProtection_TabletUunderUwtfilt31] = wt_TabletUunderUwtfilt31
    event_parameters[wt_gridProtection_TabletUunderUwtfilt32] = wt_TabletUunderUwtfilt32
    event_parameters[wt_gridProtection_TabletUunderUwtfilt41] = wt_TabletUunderUwtfilt41
    event_parameters[wt_gridProtection_TabletUunderUwtfilt42] = wt_TabletUunderUwtfilt42
    event_parameters[wt_gridProtection_TabletUunderUwtfilt51] = wt_TabletUunderUwtfilt51
    event_parameters[wt_gridProtection_TabletUunderUwtfilt52] = wt_TabletUunderUwtfilt52
    event_parameters[wt_gridProtection_TabletUunderUwtfilt61] = wt_TabletUunderUwtfilt61
    event_parameters[wt_gridProtection_TabletUunderUwtfilt62] = wt_TabletUunderUwtfilt62
    event_parameters[wt_gridProtection_TabletUunderUwtfilt71] = wt_TabletUunderUwtfilt71
    event_parameters[wt_gridProtection_TabletUunderUwtfilt72] = wt_TabletUunderUwtfilt72
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt_1_1] = wt_Tabletfoverfwtfilt_1_1
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt_1_2] = wt_Tabletfoverfwtfilt_1_2
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt_2_1] = wt_Tabletfoverfwtfilt_2_1
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt_2_2] = wt_Tabletfoverfwtfilt_2_2
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt_3_1] = wt_Tabletfoverfwtfilt_3_1
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt_3_2] = wt_Tabletfoverfwtfilt_3_2
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt_4_1] = wt_Tabletfoverfwtfilt_4_1
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt_4_2] = wt_Tabletfoverfwtfilt_4_2
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt11] = wt_Tabletfoverfwtfilt11
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt12] = wt_Tabletfoverfwtfilt12
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt21] = wt_Tabletfoverfwtfilt21
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt22] = wt_Tabletfoverfwtfilt22
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt31] = wt_Tabletfoverfwtfilt31
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt32] = wt_Tabletfoverfwtfilt32
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt41] = wt_Tabletfoverfwtfilt41
    event_parameters[wt_gridProtection_Tabletfoverfwtfilt42] = wt_Tabletfoverfwtfilt42
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_1_1] = wt_Tabletfunderfwtfilt_1_1
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_1_2] = wt_Tabletfunderfwtfilt_1_2
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_2_1] = wt_Tabletfunderfwtfilt_2_1
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_2_2] = wt_Tabletfunderfwtfilt_2_2
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_3_1] = wt_Tabletfunderfwtfilt_3_1
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_3_2] = wt_Tabletfunderfwtfilt_3_2
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_4_1] = wt_Tabletfunderfwtfilt_4_1
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_4_2] = wt_Tabletfunderfwtfilt_4_2
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_5_1] = wt_Tabletfunderfwtfilt_5_1
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_5_2] = wt_Tabletfunderfwtfilt_5_2
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_6_1] = wt_Tabletfunderfwtfilt_6_1
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt_6_2] = wt_Tabletfunderfwtfilt_6_2
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt11] = wt_Tabletfunderfwtfilt11
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt12] = wt_Tabletfunderfwtfilt12
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt21] = wt_Tabletfunderfwtfilt21
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt22] = wt_Tabletfunderfwtfilt22
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt31] = wt_Tabletfunderfwtfilt31
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt32] = wt_Tabletfunderfwtfilt32
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt41] = wt_Tabletfunderfwtfilt41
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt42] = wt_Tabletfunderfwtfilt42
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt51] = wt_Tabletfunderfwtfilt51
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt52] = wt_Tabletfunderfwtfilt52
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt61] = wt_Tabletfunderfwtfilt61
    event_parameters[wt_gridProtection_Tabletfunderfwtfilt62] = wt_Tabletfunderfwtfilt62
    event_parameters[wt_gridProtection_U0Pu] = wt_U0Pu
    event_parameters[wt_gridProtection_UOverPu] = wt_UOverPu
    event_parameters[wt_gridProtection_UUnderPu] = wt_UUnderPu
    event_parameters[wt_gridProtection_combiTable1D_table_1_1] = wt_gridProtection_TabletUoverUwtfilt_1_1
    event_parameters[wt_gridProtection_combiTable1D_table_1_2] = wt_gridProtection_TabletUoverUwtfilt_1_2
    event_parameters[wt_gridProtection_combiTable1D_table_2_1] = wt_gridProtection_TabletUoverUwtfilt_2_1
    event_parameters[wt_gridProtection_combiTable1D_table_2_2] = wt_gridProtection_TabletUoverUwtfilt_2_2
    event_parameters[wt_gridProtection_combiTable1D_table_3_1] = wt_gridProtection_TabletUoverUwtfilt_3_1
    event_parameters[wt_gridProtection_combiTable1D_table_3_2] = wt_gridProtection_TabletUoverUwtfilt_3_2
    event_parameters[wt_gridProtection_combiTable1D_table_4_1] = wt_gridProtection_TabletUoverUwtfilt_4_1
    event_parameters[wt_gridProtection_combiTable1D_table_4_2] = wt_gridProtection_TabletUoverUwtfilt_4_2
    event_parameters[wt_gridProtection_combiTable1D_table_5_1] = wt_gridProtection_TabletUoverUwtfilt_5_1
    event_parameters[wt_gridProtection_combiTable1D_table_5_2] = wt_gridProtection_TabletUoverUwtfilt_5_2
    event_parameters[wt_gridProtection_combiTable1D_table_6_1] = wt_gridProtection_TabletUoverUwtfilt_6_1
    event_parameters[wt_gridProtection_combiTable1D_table_6_2] = wt_gridProtection_TabletUoverUwtfilt_6_2
    event_parameters[wt_gridProtection_combiTable1D_table_7_1] = wt_gridProtection_TabletUoverUwtfilt_7_1
    event_parameters[wt_gridProtection_combiTable1D_table_7_2] = wt_gridProtection_TabletUoverUwtfilt_7_2
    event_parameters[wt_gridProtection_combiTable1D_table_8_1] = wt_gridProtection_TabletUoverUwtfilt_8_1
    event_parameters[wt_gridProtection_combiTable1D_table_8_2] = wt_gridProtection_TabletUoverUwtfilt_8_2
    event_parameters[wt_gridProtection_combiTable1D_u_max] = vf.add_const(2.05, name='')
    event_parameters[wt_gridProtection_combiTable1D_u_min] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_table_1_1] = wt_gridProtection_TabletUunderUwtfilt_1_1
    event_parameters[wt_gridProtection_combiTable1D1_table_1_2] = wt_gridProtection_TabletUunderUwtfilt_1_2
    event_parameters[wt_gridProtection_combiTable1D1_table_2_1] = wt_gridProtection_TabletUunderUwtfilt_2_1
    event_parameters[wt_gridProtection_combiTable1D1_table_2_2] = wt_gridProtection_TabletUunderUwtfilt_2_2
    event_parameters[wt_gridProtection_combiTable1D1_table_3_1] = wt_gridProtection_TabletUunderUwtfilt_3_1
    event_parameters[wt_gridProtection_combiTable1D1_table_3_2] = wt_gridProtection_TabletUunderUwtfilt_3_2
    event_parameters[wt_gridProtection_combiTable1D1_table_4_1] = wt_gridProtection_TabletUunderUwtfilt_4_1
    event_parameters[wt_gridProtection_combiTable1D1_table_4_2] = wt_gridProtection_TabletUunderUwtfilt_4_2
    event_parameters[wt_gridProtection_combiTable1D1_table_5_1] = wt_gridProtection_TabletUunderUwtfilt_5_1
    event_parameters[wt_gridProtection_combiTable1D1_table_5_2] = wt_gridProtection_TabletUunderUwtfilt_5_2
    event_parameters[wt_gridProtection_combiTable1D1_table_6_1] = wt_gridProtection_TabletUunderUwtfilt_6_1
    event_parameters[wt_gridProtection_combiTable1D1_table_6_2] = wt_gridProtection_TabletUunderUwtfilt_6_2
    event_parameters[wt_gridProtection_combiTable1D1_table_7_1] = wt_gridProtection_TabletUunderUwtfilt_7_1
    event_parameters[wt_gridProtection_combiTable1D1_table_7_2] = wt_gridProtection_TabletUunderUwtfilt_7_2
    event_parameters[wt_gridProtection_combiTable1D1_u_max] = vf.add_const(1.04, name='')
    event_parameters[wt_gridProtection_combiTable1D1_u_min] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_table_1_1] = wt_gridProtection_Tabletfoverfwtfilt_1_1
    event_parameters[wt_gridProtection_combiTable1D2_table_1_2] = wt_gridProtection_Tabletfoverfwtfilt_1_2
    event_parameters[wt_gridProtection_combiTable1D2_table_2_1] = wt_gridProtection_Tabletfoverfwtfilt_2_1
    event_parameters[wt_gridProtection_combiTable1D2_table_2_2] = wt_gridProtection_Tabletfoverfwtfilt_2_2
    event_parameters[wt_gridProtection_combiTable1D2_table_3_1] = wt_gridProtection_Tabletfoverfwtfilt_3_1
    event_parameters[wt_gridProtection_combiTable1D2_table_3_2] = wt_gridProtection_Tabletfoverfwtfilt_3_2
    event_parameters[wt_gridProtection_combiTable1D2_table_4_1] = wt_gridProtection_Tabletfoverfwtfilt_4_1
    event_parameters[wt_gridProtection_combiTable1D2_table_4_2] = wt_gridProtection_Tabletfoverfwtfilt_4_2
    event_parameters[wt_gridProtection_combiTable1D2_u_max] = vf.add_const(2.01, name='')
    event_parameters[wt_gridProtection_combiTable1D2_u_min] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_table_1_1] = wt_gridProtection_Tabletfunderfwtfilt_1_1
    event_parameters[wt_gridProtection_combiTable1D3_table_1_2] = wt_gridProtection_Tabletfunderfwtfilt_1_2
    event_parameters[wt_gridProtection_combiTable1D3_table_2_1] = wt_gridProtection_Tabletfunderfwtfilt_2_1
    event_parameters[wt_gridProtection_combiTable1D3_table_2_2] = wt_gridProtection_Tabletfunderfwtfilt_2_2
    event_parameters[wt_gridProtection_combiTable1D3_table_3_1] = wt_gridProtection_Tabletfunderfwtfilt_3_1
    event_parameters[wt_gridProtection_combiTable1D3_table_3_2] = wt_gridProtection_Tabletfunderfwtfilt_3_2
    event_parameters[wt_gridProtection_combiTable1D3_table_4_1] = wt_gridProtection_Tabletfunderfwtfilt_4_1
    event_parameters[wt_gridProtection_combiTable1D3_table_4_2] = wt_gridProtection_Tabletfunderfwtfilt_4_2
    event_parameters[wt_gridProtection_combiTable1D3_table_5_1] = wt_gridProtection_Tabletfunderfwtfilt_5_1
    event_parameters[wt_gridProtection_combiTable1D3_table_5_2] = wt_gridProtection_Tabletfunderfwtfilt_5_2
    event_parameters[wt_gridProtection_combiTable1D3_table_6_1] = wt_gridProtection_Tabletfunderfwtfilt_6_1
    event_parameters[wt_gridProtection_combiTable1D3_table_6_2] = wt_gridProtection_Tabletfunderfwtfilt_6_2
    event_parameters[wt_gridProtection_combiTable1D3_u_max] = vf.add_const(1.03, name='')
    event_parameters[wt_gridProtection_combiTable1D3_u_min] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_const_k] = wt_gridProtection_UOverPu
    event_parameters[wt_gridProtection_const1_k] = wt_gridProtection_UUnderPu
    event_parameters[wt_gridProtection_const2_k] = wt_gridProtection_fOverPu
    event_parameters[wt_gridProtection_const3_k] = wt_gridProtection_fUnderPu
    event_parameters[wt_gridProtection_fOverPu] = wt_fOverPu
    event_parameters[wt_gridProtection_fUnderPu] = wt_fUnderPu
    event_parameters[wt_i0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[wt_i0Pu_re] = vf.add_const(-0.8, name='')
    event_parameters[wt_mechanical_CdrtPu] = wt_CdrtPu
    event_parameters[wt_mechanical_Hgen] = wt_Hgen
    event_parameters[wt_mechanical_Hwtr] = wt_Hwtr
    event_parameters[wt_mechanical_KdrtPu] = wt_KdrtPu
    event_parameters[wt_mechanical_P0Pu] = wt_P0Pu
    event_parameters[wt_mechanical_PAg0Pu] = wt_PAg0Pu
    event_parameters[wt_mechanical_SNom] = wt_SNom
    event_parameters[wt_mechanical_add_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_mechanical_add_k2] = vf.add_const(-1.0, name='')
    event_parameters[wt_mechanical_add1_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_mechanical_add1_k2] = vf.add_const(-1.0, name='')
    event_parameters[wt_mechanical_add2_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_mechanical_add2_k2] = vf.add_const(-1.0, name='')
    event_parameters[wt_mechanical_integrator_k] = (sym.Const(0.5) / wt_mechanical_Hwtr)
    event_parameters[wt_mechanical_integrator_y_start] = vf.add_const(1.0, name='')
    event_parameters[wt_mechanical_integrator1_k] = (sym.Const(0.5) / wt_mechanical_Hgen)
    event_parameters[wt_mechanical_integrator1_y_start] = vf.add_const(1.0, name='')
    event_parameters[wt_mechanical_pI_Ki] = wt_mechanical_KdrtPu
    event_parameters[wt_mechanical_pI_Kp] = wt_mechanical_CdrtPu
    event_parameters[wt_mechanical_pI_Y0] = wt_mechanical_PAg0Pu
    event_parameters[wt_mechanical_pI_add_k1] = wt_mechanical_pI_Kp
    event_parameters[wt_mechanical_pI_add_k2] = wt_mechanical_pI_Ki
    event_parameters[wt_mechanical_pI_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_mechanical_pI_integrator_y_start] = (wt_mechanical_pI_Y0 / wt_mechanical_pI_Ki)
    event_parameters[wt_pll_U0Pu] = wt_U0Pu
    event_parameters[wt_pll_UPhase0] = wt_UPhase0
    event_parameters[wt_pll_UPll1Pu] = wt_UPll1Pu
    event_parameters[wt_pll_UPll2Pu] = wt_UPll2Pu
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_DyMax] = vf.add_const(999.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_DyMin] = (-wt_pll_absLimRateLimFirstOrderFreeze_DyMax)
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_Y0] = wt_pll_UPhase0
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_YMax] = vf.add_const(999.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_YMin] = (-wt_pll_absLimRateLimFirstOrderFreeze_YMax)
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_const_k] = vf.add_const(0.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_gain_k] = (sym.Const(1.0) / wt_pll_absLimRateLimFirstOrderFreeze_tI)
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_integrator_y_start] = wt_pll_absLimRateLimFirstOrderFreeze_Y0
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMax] = wt_pll_absLimRateLimFirstOrderFreeze_DyMax
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_limiter_uMin] = wt_pll_absLimRateLimFirstOrderFreeze_DyMin
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_tI] = wt_pll_tPll
    event_parameters[wt_pll_fixedBooleanDelay_tDelay] = wt_pll_tS
    event_parameters[wt_pll_fixedBooleanDelay1_tDelay] = wt_pll_tS
    event_parameters[wt_pll_lessThreshold_threshold] = wt_pll_UPll1Pu
    event_parameters[wt_pll_lessThreshold1_threshold] = wt_pll_UPll2Pu
    event_parameters[wt_pll_tPll] = wt_tPll
    event_parameters[wt_pll_tS] = wt_tS
    event_parameters[wt_protectionMeasurements_DfMaxPu] = wt_DfpMaxPu
    event_parameters[wt_protectionMeasurements_P0Pu] = wt_P0Pu
    event_parameters[wt_protectionMeasurements_Q0Pu] = wt_Q0Pu
    event_parameters[wt_protectionMeasurements_SNom] = wt_SNom
    event_parameters[wt_protectionMeasurements_U0Pu] = wt_U0Pu
    event_parameters[wt_protectionMeasurements_UPhase0] = wt_UPhase0
    event_parameters[wt_protectionMeasurements_add_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_add_k2] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_derivative_T] = (sym.Const(0.05) * wt_protectionMeasurements_tfFilt)
    event_parameters[wt_protectionMeasurements_derivative_k] = vf.add_const(0.0031830988618379067, name='')
    event_parameters[wt_protectionMeasurements_derivative_x_start] = wt_protectionMeasurements_UPhase0
    event_parameters[wt_protectionMeasurements_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder_T] = wt_protectionMeasurements_tPFilt
    event_parameters[wt_protectionMeasurements_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder_y_start] = ((sym.Const(-100.0) * wt_protectionMeasurements_P0Pu) / wt_protectionMeasurements_SNom)
    event_parameters[wt_protectionMeasurements_firstOrder1_T] = wt_protectionMeasurements_tQFilt
    event_parameters[wt_protectionMeasurements_firstOrder1_k] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder1_y_start] = ((sym.Const(-100.0) * wt_protectionMeasurements_Q0Pu) / wt_protectionMeasurements_SNom)
    event_parameters[wt_protectionMeasurements_firstOrder2_T] = wt_protectionMeasurements_tIFilt
    event_parameters[wt_protectionMeasurements_firstOrder2_k] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder2_y_start] = (sym.Const(100.0) * ((((wt_protectionMeasurements_i0Pu_re ** sym.Const(2.0)) + (wt_protectionMeasurements_i0Pu_im ** sym.Const(2.0))) ** sym.Const(0.5)) / wt_protectionMeasurements_SNom))
    event_parameters[wt_protectionMeasurements_firstOrder3_T] = wt_protectionMeasurements_tUFilt
    event_parameters[wt_protectionMeasurements_firstOrder3_k] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder3_y_start] = wt_protectionMeasurements_U0Pu
    event_parameters[wt_protectionMeasurements_firstOrder4_T] = wt_protectionMeasurements_tfFilt
    event_parameters[wt_protectionMeasurements_firstOrder4_k] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder4_y_start] = vf.add_const(0.0, name='')
    event_parameters[wt_protectionMeasurements_i0Pu_im] = wt_i0Pu_im
    event_parameters[wt_protectionMeasurements_i0Pu_re] = wt_i0Pu_re
    event_parameters[wt_protectionMeasurements_rampLimiter_DuMax] = wt_protectionMeasurements_DfMaxPu
    event_parameters[wt_protectionMeasurements_rampLimiter_DuMin] = (-wt_protectionMeasurements_rampLimiter_DuMax)
    event_parameters[wt_protectionMeasurements_rampLimiter_Y0] = vf.add_const(0.0, name='')
    event_parameters[wt_protectionMeasurements_rampLimiter_gain_k] = (sym.Const(1.0) / wt_protectionMeasurements_rampLimiter_tS)
    event_parameters[wt_protectionMeasurements_rampLimiter_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_rampLimiter_integrator_y_start] = wt_protectionMeasurements_rampLimiter_Y0
    event_parameters[wt_protectionMeasurements_rampLimiter_limiter_uMax] = wt_protectionMeasurements_rampLimiter_DuMax
    event_parameters[wt_protectionMeasurements_rampLimiter_limiter_uMin] = wt_protectionMeasurements_rampLimiter_DuMin
    event_parameters[wt_protectionMeasurements_rampLimiter_tS] = wt_protectionMeasurements_tS
    event_parameters[wt_protectionMeasurements_tIFilt] = wt_tIpFilt
    event_parameters[wt_protectionMeasurements_tPFilt] = wt_tPpFilt
    event_parameters[wt_protectionMeasurements_tQFilt] = wt_tQpFilt
    event_parameters[wt_protectionMeasurements_tS] = wt_tS
    event_parameters[wt_protectionMeasurements_tUFilt] = wt_tUpFilt
    event_parameters[wt_protectionMeasurements_tfFilt] = wt_tfpFilt
    event_parameters[wt_protectionMeasurements_u0Pu_im] = wt_u0Pu_im
    event_parameters[wt_protectionMeasurements_u0Pu_re] = wt_u0Pu_re
    event_parameters[wt_tG] = vf.add_const(0.02, name='')
    event_parameters[wt_tIcFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_tIpFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_tPAero] = vf.add_const(0.02, name='')
    event_parameters[wt_tPOrdP4B] = vf.add_const(0.02, name='')
    event_parameters[wt_tPcFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_tPll] = vf.add_const(0.02, name='')
    event_parameters[wt_tPost] = vf.add_const(0.1, name='')
    event_parameters[wt_tPpFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_tQcFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_tQord] = vf.add_const(0.02, name='')
    event_parameters[wt_tQpFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_tS] = vf.add_const(0.01, name='')
    event_parameters[wt_tUcFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_tUpFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_tUss] = vf.add_const(0.02, name='')
    event_parameters[wt_tfcFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_tfpFilt] = vf.add_const(0.02, name='')
    event_parameters[wt_u0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[wt_u0Pu_re] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_BesPu] = wt_BesPu
    event_parameters[wt_wT4Injector_DipMaxPu] = wt_DipMaxPu
    event_parameters[wt_wT4Injector_DiqMaxPu] = wt_DiqMaxPu
    event_parameters[wt_wT4Injector_DiqMinPu] = wt_DiqMinPu
    event_parameters[wt_wT4Injector_GesPu] = wt_GesPu
    event_parameters[wt_wT4Injector_IGsIm0Pu] = wt_IGsIm0Pu
    event_parameters[wt_wT4Injector_IGsRe0Pu] = wt_IGsRe0Pu
    event_parameters[wt_wT4Injector_IpMax0Pu] = wt_IpMax0Pu
    event_parameters[wt_wT4Injector_IqMax0Pu] = wt_IqMax0Pu
    event_parameters[wt_wT4Injector_IqMin0Pu] = wt_IqMin0Pu
    event_parameters[wt_wT4Injector_Kipaw] = wt_Kipaw
    event_parameters[wt_wT4Injector_Kiqaw] = wt_Kiqaw
    event_parameters[wt_wT4Injector_P0Pu] = wt_P0Pu
    event_parameters[wt_wT4Injector_PAg0Pu] = wt_PAg0Pu
    event_parameters[wt_wT4Injector_Q0Pu] = wt_Q0Pu
    event_parameters[wt_wT4Injector_ResPu] = wt_ResPu
    event_parameters[wt_wT4Injector_SNom] = wt_SNom
    event_parameters[wt_wT4Injector_U0Pu] = wt_U0Pu
    event_parameters[wt_wT4Injector_UGsIm0Pu] = wt_UGsIm0Pu
    event_parameters[wt_wT4Injector_UGsRe0Pu] = wt_UGsRe0Pu
    event_parameters[wt_wT4Injector_UPhase0] = wt_UPhase0
    event_parameters[wt_wT4Injector_XesPu] = wt_XesPu
    event_parameters[wt_wT4Injector_elecSystem_BesPu] = wt_wT4Injector_BesPu
    event_parameters[wt_wT4Injector_elecSystem_GesPu] = wt_wT4Injector_GesPu
    event_parameters[wt_wT4Injector_elecSystem_IGsIm0Pu] = wt_wT4Injector_IGsIm0Pu
    event_parameters[wt_wT4Injector_elecSystem_IGsRe0Pu] = wt_wT4Injector_IGsRe0Pu
    event_parameters[wt_wT4Injector_elecSystem_ResPu] = wt_wT4Injector_ResPu
    event_parameters[wt_wT4Injector_elecSystem_SNom] = wt_wT4Injector_SNom
    event_parameters[wt_wT4Injector_elecSystem_UGsIm0Pu] = wt_wT4Injector_UGsIm0Pu
    event_parameters[wt_wT4Injector_elecSystem_UGsRe0Pu] = wt_wT4Injector_UGsRe0Pu
    event_parameters[wt_wT4Injector_elecSystem_XesPu] = wt_wT4Injector_XesPu
    event_parameters[wt_wT4Injector_elecSystem_i0Pu_im] = wt_wT4Injector_i0Pu_im
    event_parameters[wt_wT4Injector_elecSystem_i0Pu_re] = wt_wT4Injector_i0Pu_re
    event_parameters[wt_wT4Injector_elecSystem_u0Pu_im] = wt_wT4Injector_u0Pu_im
    event_parameters[wt_wT4Injector_elecSystem_u0Pu_re] = wt_wT4Injector_u0Pu_re
    event_parameters[wt_wT4Injector_genSystem_DipMaxPu] = wt_wT4Injector_DipMaxPu
    event_parameters[wt_wT4Injector_genSystem_DiqMaxPu] = wt_wT4Injector_DiqMaxPu
    event_parameters[wt_wT4Injector_genSystem_DiqMinPu] = wt_wT4Injector_DiqMinPu
    event_parameters[wt_wT4Injector_genSystem_IGsIm0Pu] = wt_wT4Injector_IGsIm0Pu
    event_parameters[wt_wT4Injector_genSystem_IGsRe0Pu] = wt_wT4Injector_IGsRe0Pu
    event_parameters[wt_wT4Injector_genSystem_IpMax0Pu] = wt_wT4Injector_IpMax0Pu
    event_parameters[wt_wT4Injector_genSystem_IqMax0Pu] = wt_wT4Injector_IqMax0Pu
    event_parameters[wt_wT4Injector_genSystem_IqMin0Pu] = wt_wT4Injector_IqMin0Pu
    event_parameters[wt_wT4Injector_genSystem_Kipaw] = wt_wT4Injector_Kipaw
    event_parameters[wt_wT4Injector_genSystem_Kiqaw] = wt_wT4Injector_Kiqaw
    event_parameters[wt_wT4Injector_genSystem_P0Pu] = wt_wT4Injector_P0Pu
    event_parameters[wt_wT4Injector_genSystem_PAg0Pu] = wt_wT4Injector_PAg0Pu
    event_parameters[wt_wT4Injector_genSystem_Q0Pu] = wt_wT4Injector_Q0Pu
    event_parameters[wt_wT4Injector_genSystem_SNom] = wt_wT4Injector_SNom
    event_parameters[wt_wT4Injector_genSystem_U0Pu] = wt_wT4Injector_U0Pu
    event_parameters[wt_wT4Injector_genSystem_UGsIm0Pu] = wt_wT4Injector_UGsIm0Pu
    event_parameters[wt_wT4Injector_genSystem_UGsRe0Pu] = wt_wT4Injector_UGsRe0Pu
    event_parameters[wt_wT4Injector_genSystem_UPhase0] = wt_wT4Injector_UPhase0
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_DyMax] = wt_wT4Injector_genSystem_DipMaxPu
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_DyMin] = vf.add_const(-999.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_Kaw] = wt_wT4Injector_genSystem_Kipaw
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_Y0] = ((sym.Const(-100.0) * wt_wT4Injector_genSystem_P0Pu) / (wt_wT4Injector_genSystem_U0Pu * wt_wT4Injector_genSystem_SNom))
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_YMax] = vf.add_const(999.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_YMin] = (-wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_YMax)
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_add_k2] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_Kaw
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_gain_k] = (sym.Const(1.0) / wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_tI)
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y_start] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_Y0
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMax] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_DyMax
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_uMin] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_DyMin
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_tI] = wt_wT4Injector_genSystem_tG
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMax] = wt_wT4Injector_genSystem_DiqMaxPu
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMin] = wt_wT4Injector_genSystem_DiqMinPu
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_Kaw] = wt_wT4Injector_genSystem_Kiqaw
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_Y0] = (sym.Const(100.0) * (wt_wT4Injector_genSystem_Q0Pu / (wt_wT4Injector_genSystem_U0Pu * wt_wT4Injector_genSystem_SNom)))
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_YMax] = vf.add_const(999.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_YMin] = (-wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_YMax)
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k1] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_add_k2] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_Kaw
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_gain_k] = (sym.Const(1.0) / wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_tI)
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y_start] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_Y0
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMax] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMax
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_uMin] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_DyMin
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_tI] = wt_wT4Injector_genSystem_tG
    event_parameters[wt_wT4Injector_genSystem_const_k] = vf.add_const(-999.0, name='')
    event_parameters[wt_wT4Injector_genSystem_iECFrameRotation_IGsIm0Pu] = wt_wT4Injector_genSystem_IGsIm0Pu
    event_parameters[wt_wT4Injector_genSystem_iECFrameRotation_IGsRe0Pu] = wt_wT4Injector_genSystem_IGsRe0Pu
    event_parameters[wt_wT4Injector_genSystem_iECFrameRotation_P0Pu] = wt_wT4Injector_genSystem_P0Pu
    event_parameters[wt_wT4Injector_genSystem_iECFrameRotation_Q0Pu] = wt_wT4Injector_genSystem_Q0Pu
    event_parameters[wt_wT4Injector_genSystem_iECFrameRotation_SNom] = wt_wT4Injector_genSystem_SNom
    event_parameters[wt_wT4Injector_genSystem_iECFrameRotation_U0Pu] = wt_wT4Injector_genSystem_U0Pu
    event_parameters[wt_wT4Injector_genSystem_iECFrameRotation_UPhase0] = wt_wT4Injector_genSystem_UPhase0
    event_parameters[wt_wT4Injector_genSystem_tG] = wt_wT4Injector_tG
    event_parameters[wt_wT4Injector_i0Pu_im] = wt_i0Pu_im
    event_parameters[wt_wT4Injector_i0Pu_re] = wt_i0Pu_re
    event_parameters[wt_wT4Injector_tG] = wt_tG
    event_parameters[wt_wT4Injector_u0Pu_im] = wt_u0Pu_im
    event_parameters[wt_wT4Injector_u0Pu_re] = wt_u0Pu_re
    event_parameters[wt_MqG] = vf.add_const(0.0, name='')
    event_parameters[wt_Mqfrt] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_MqG] = wt_MqG
    event_parameters[wt_control4B_Mqfrt] = wt_Mqfrt
    event_parameters[wt_control4B_currentLimiter_booleanToInteger_integerFalse] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_booleanToInteger_integerTrue] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_currentLimiter_product1_nu] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_currentLimiter_switch1_nu] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_currentLimiter_switch2_nu] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_currentLimiter_switch4_nu] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_rampLimiter_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_pControl4B_rampLimiter_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_MqG] = wt_control4B_MqG
    event_parameters[wt_control4B_qControl_Mqfrt] = wt_control4B_Mqfrt
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_booleanToInteger_integerFalse] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_booleanToInteger_integerTrue] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_delayFlag_FO0] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_delayFlag_booleanToInteger_integerFalse] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_delayFlag_booleanToInteger_integerTrue] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_delayFlag_integerConstant_k] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_qControl_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_integerConstant_k] = wt_control4B_qControl_MqG
    event_parameters[wt_control4B_qControl_integerConstant1_k] = wt_control4B_qControl_MqG
    event_parameters[wt_control4B_qControl_integerConstant2_k] = wt_control4B_qControl_Mqfrt
    event_parameters[wt_control4B_qControl_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_limiter2_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_limiter3_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_switch_nu] = vf.add_const(5.0, name='')
    event_parameters[wt_control4B_qControl_switch2_nu] = vf.add_const(5.0, name='')
    event_parameters[wt_control4B_qControl_switch4_nu] = vf.add_const(5.0, name='')
    event_parameters[wt_control4B_qControl_switch6_nu] = vf.add_const(4.0, name='')
    event_parameters[wt_control4B_qControl_switch7_nu] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_qControl_switch8_nu] = vf.add_const(4.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_integerToBoolean_threshold] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder1_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder2_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder3_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_firstOrder4_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_rampLimiter_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_controlMeasurements_rampLimiter_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_columns_1] = vf.add_const(2.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_extrapolation] = vf.add_const(2.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_nout] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_smoothness] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_or1_nu] = vf.add_const(5.0, name='')
    event_parameters[wt_mechanical_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_mechanical_integrator1_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_mechanical_pI_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder1_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder2_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder3_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_firstOrder4_initType] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_rampLimiter_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_protectionMeasurements_rampLimiter_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_NbSwitchOffSignals] = vf.add_const(3.0, name='')
    event_parameters[wt_wT4Injector_State0] = vf.add_const(2.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[wt_MdfsLim] = vf.add_const(0.0, name='')
    event_parameters[wt_MpUScale] = vf.add_const(0.0, name='')
    event_parameters[wt_Mqpri] = vf.add_const(0.0, name='')
    event_parameters[wt_QlConst] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_MdfsLim] = wt_MdfsLim
    event_parameters[wt_control4B_MpUScale] = wt_MpUScale
    event_parameters[wt_control4B_Mqpri] = wt_Mqpri
    event_parameters[wt_control4B_QlConst] = wt_QlConst
    event_parameters[wt_control4B_currentLimiter_MdfsLim] = wt_control4B_MdfsLim
    event_parameters[wt_control4B_currentLimiter_Mqpri] = wt_control4B_Mqpri
    event_parameters[wt_control4B_currentLimiter_abs_generateEvent] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_booleanConstant_k] = wt_control4B_currentLimiter_MdfsLim
    event_parameters[wt_control4B_currentLimiter_booleanConstant1_k] = wt_control4B_currentLimiter_Mqpri
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_MpUScale] = wt_control4B_MpUScale
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_UseLimits] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_pControl4B_booleanConstant_k] = wt_control4B_pControl4B_MpUScale
    event_parameters[wt_control4B_pControl4B_rampLimiter_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_pControl4B_rampLimiter_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_pControl4B_rampLimiter_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_pControl4B_rampLimiter_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_abs_generateEvent] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_UseLimits] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_antiWindupIntegrator1_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_deadZone_deadZoneAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_delayFlag_FI0] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(wt_control4B_qControl_derivative_k)) - sym.Const(1e-06)))
    event_parameters[wt_control4B_qControl_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_limiter2_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_limiter2_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qControl_limiter3_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qControl_limiter3_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_QlConst] = wt_control4B_QlConst
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_booleanConstant_k] = wt_control4B_qLimiter_QlConst
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_complexToReal_useConjugateInput] = vf.add_const(0.0, name='')
    event_parameters[wt_controlMeasurements_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(wt_controlMeasurements_derivative_k)) - sym.Const(1e-06)))
    event_parameters[wt_controlMeasurements_product_useConjugateInput1] = vf.add_const(0.0, name='')
    event_parameters[wt_controlMeasurements_product_useConjugateInput2] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_rampLimiter_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_controlMeasurements_rampLimiter_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_controlMeasurements_rampLimiter_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_controlMeasurements_rampLimiter_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_tableOnFile] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_verboseExtrapolation] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_verboseRead] = vf.add_const(1.0, name='')
    event_parameters[wt_gridProtection_pre1_pre_u_start] = vf.add_const(0.0, name='')
    event_parameters[wt_mechanical_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_mechanical_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_mechanical_integrator1_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_mechanical_integrator1_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_mechanical_pI_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_mechanical_pI_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_UseLimits] = vf.add_const(0.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_pll_absLimRateLimFirstOrderFreeze_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_pll_fixedBooleanDelay_Y0] = sym.heaviside(((wt_pll_UPll1Pu - wt_pll_U0Pu) - sym.Const(1e-06)))
    event_parameters[wt_pll_fixedBooleanDelay1_Y0] = sym.heaviside(((wt_pll_UPll2Pu - wt_pll_U0Pu) - sym.Const(1e-06)))
    event_parameters[wt_protectionMeasurements_complexToReal_useConjugateInput] = vf.add_const(0.0, name='')
    event_parameters[wt_protectionMeasurements_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(wt_protectionMeasurements_derivative_k)) - sym.Const(1e-06)))
    event_parameters[wt_protectionMeasurements_product_useConjugateInput1] = vf.add_const(0.0, name='')
    event_parameters[wt_protectionMeasurements_product_useConjugateInput2] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_rampLimiter_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_protectionMeasurements_rampLimiter_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_protectionMeasurements_rampLimiter_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_protectionMeasurements_rampLimiter_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_Running0] = (sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - wt_wT4Injector_SwitchOffSignal10) * (sym.Const(1.0) - wt_wT4Injector_SwitchOffSignal20)))) * (sym.Const(1.0) - wt_wT4Injector_SwitchOffSignal30))))
    event_parameters[wt_wT4Injector_SwitchOffSignal10] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_SwitchOffSignal20] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_SwitchOffSignal30] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_UseLimits] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_UseLimits] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_genSystem_complexToReal_useConjugateInput] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_genSystem_product_useConjugateInput1] = vf.add_const(0.0, name='')
    event_parameters[wt_wT4Injector_genSystem_product_useConjugateInput2] = vf.add_const(1.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_fileName] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_tableName] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds_tableID] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_currentLimiter_combiTable1Ds1_tableID] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds_tableID] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds1_tableID] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds2_tableID] = vf.add_const(0.0, name='')
    event_parameters[wt_control4B_qLimiter_combiTable1Ds3_tableID] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D_tableID] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D1_tableID] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D2_tableID] = vf.add_const(0.0, name='')
    event_parameters[wt_gridProtection_combiTable1D3_tableID] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y] = wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_y_start
    initial_equations[wt_control4B_pControl4B_firstOrder_y] = wt_control4B_pControl4B_firstOrder_y_start
    initial_equations[wt_control4B_pControl4B_rampLimiter_integrator_y] = wt_control4B_pControl4B_rampLimiter_integrator_y_start
    initial_equations[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y_start
    initial_equations[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y] = wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_y_start
    initial_equations[wt_control4B_qControl_antiWindupIntegrator_integrator_y] = wt_control4B_qControl_antiWindupIntegrator_integrator_y_start
    initial_equations[wt_control4B_qControl_antiWindupIntegrator1_integrator_y] = wt_control4B_qControl_antiWindupIntegrator1_integrator_y_start
    initial_equations[wt_control4B_qControl_derivative_x] = wt_control4B_qControl_derivative_x_start
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_y_start
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_y_start
    initial_equations[wt_controlMeasurements_derivative_x] = wt_controlMeasurements_derivative_x_start
    initial_equations[wt_controlMeasurements_firstOrder_y] = wt_controlMeasurements_firstOrder_y_start
    initial_equations[wt_controlMeasurements_firstOrder1_y] = wt_controlMeasurements_firstOrder1_y_start
    initial_equations[wt_controlMeasurements_firstOrder2_y] = wt_controlMeasurements_firstOrder2_y_start
    initial_equations[wt_controlMeasurements_firstOrder3_y] = wt_controlMeasurements_firstOrder3_y_start
    initial_equations[wt_controlMeasurements_firstOrder4_y] = wt_controlMeasurements_firstOrder4_y_start
    initial_equations[wt_controlMeasurements_rampLimiter_integrator_y] = wt_controlMeasurements_rampLimiter_integrator_y_start
    initial_equations[wt_mechanical_integrator_y] = wt_mechanical_integrator_y_start
    initial_equations[wt_mechanical_integrator1_y] = wt_mechanical_integrator1_y_start
    initial_equations[wt_mechanical_pI_integrator_y] = wt_mechanical_pI_integrator_y_start
    initial_equations[wt_pll_absLimRateLimFirstOrderFreeze_integrator_y] = wt_pll_absLimRateLimFirstOrderFreeze_integrator_y_start
    initial_equations[wt_protectionMeasurements_derivative_x] = wt_protectionMeasurements_derivative_x_start
    initial_equations[wt_protectionMeasurements_firstOrder_y] = wt_protectionMeasurements_firstOrder_y_start
    initial_equations[wt_protectionMeasurements_firstOrder1_y] = wt_protectionMeasurements_firstOrder1_y_start
    initial_equations[wt_protectionMeasurements_firstOrder2_y] = wt_protectionMeasurements_firstOrder2_y_start
    initial_equations[wt_protectionMeasurements_firstOrder3_y] = wt_protectionMeasurements_firstOrder3_y_start
    initial_equations[wt_protectionMeasurements_firstOrder4_y] = wt_protectionMeasurements_firstOrder4_y_start
    initial_equations[wt_protectionMeasurements_rampLimiter_integrator_y] = wt_protectionMeasurements_rampLimiter_integrator_y_start
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_y_start
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y] = wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_y_start
    initial_equations[wt_PWTRefPu] = vf.add_const(0.8, name='')
    initial_equations[wt_control4B_currentLimiter_switch_y] = vf.add_const(1.0, name='')
    initial_equations[wt_control4B_currentLimiter_switch2_u_1] = vf.add_const(1.2, name='')
    initial_equations[wt_control4B_currentLimiter_switch2_u_2] = vf.add_const(1.2, name='')
    initial_equations[wt_control4B_currentLimiter_switch2_u_3] = vf.add_const(1.2, name='')
    initial_equations[wt_control4B_ipCmdPu] = (((-wt_control4B_currentLimiter_P0Pu) * sym.Const(100.0)) / (wt_control4B_currentLimiter_SNom * wt_control4B_currentLimiter_U0Pu))
    initial_equations[wt_control4B_ipMaxPu] = wt_control4B_pControl4B_IpMax0Pu
    initial_equations[wt_control4B_iqCmdPu] = ((wt_control4B_currentLimiter_Q0Pu * sym.Const(100.0)) / (wt_control4B_currentLimiter_SNom * wt_control4B_currentLimiter_U0Pu))
    initial_equations[wt_control4B_iqMaxPu] = wt_control4B_currentLimiter_IqMax0Pu
    initial_equations[wt_control4B_iqMinPu] = wt_control4B_currentLimiter_IqMin0Pu
    initial_equations[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_y] = wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_Y0
    initial_equations[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_y] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_Y0
    initial_equations[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_y] = wt_control4B_qControl_absLimRateLimFirstOrderFreeze_Y0
    initial_equations[wt_control4B_qControl_antiWindupIntegrator_y] = wt_control4B_qControl_antiWindupIntegrator_Y0
    initial_equations[wt_control4B_qControl_antiWindupIntegrator1_y] = wt_control4B_qControl_antiWindupIntegrator1_Y0
    initial_equations[wt_control4B_qControl_deadZone_y] = ((sym.heaviside(((wt_control4B_qControl_derivative_y - wt_control4B_qControl_deadZone_uMax) - sym.Const(1e-06))) * (wt_control4B_qControl_derivative_y - wt_control4B_qControl_deadZone_uMax)) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_derivative_y - wt_control4B_qControl_deadZone_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qControl_deadZone_uMin - wt_control4B_qControl_derivative_y) - sym.Const(1e-06))) * (wt_control4B_qControl_derivative_y - wt_control4B_qControl_deadZone_uMin)) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_deadZone_uMin - wt_control4B_qControl_derivative_y) - sym.Const(1e-06)))) * sym.Const(0.0)))))
    initial_equations[wt_control4B_qControl_division2_y] = wt_control4B_qControl_absLimRateLimFeedthroughFreeze_U0
    initial_equations[wt_control4B_qControl_gain5_y] = wt_control4B_qControl_vDrop_P0Pu
    initial_equations[wt_control4B_qControl_gain6_y] = wt_control4B_qControl_vDrop_Q0Pu
    initial_equations[wt_control4B_qControl_switch_u_1] = ((wt_control4B_qControl_add2_k1 * wt_control4B_qControl_switch2_y) + (wt_control4B_qControl_add2_k2 * wt_control4B_qControl_const1_k))
    initial_equations[wt_control4B_qControl_switch_u_3] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_switch_u_5] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_switch2_u_4] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_switch2_y] = (wt_control4B_qControl_switch2_u + (wt_control4B_qControl_integerConstant1_k + sym.Const(1.0)))
    initial_equations[wt_control4B_qControl_switch6_u_1] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_switch6_u_4] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_switch7_u_1] = ((wt_control4B_qControl_Q0Pu * sym.Const(100.0)) / (wt_control4B_qControl_SNom * wt_control4B_qControl_U0Pu))
    initial_equations[wt_control4B_qControl_switch8_u_4] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_vDrop_UDropPu] = wt_control4B_qControl_vDrop_UDrop0Pu
    initial_equations[wt_control4B_qLimiter_QWTMaxPu] = wt_control4B_qControl_QMax0Pu
    initial_equations[wt_control4B_qLimiter_QWTMinPu] = wt_control4B_qControl_QMin0Pu
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_y] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_Y0
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_y] = wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_Y0
    initial_equations[wt_controlMeasurements_IWtPu] = (sym.Const(100.0) * ((((wt_controlMeasurements_i0Pu_re ** sym.Const(2.0)) + (wt_controlMeasurements_i0Pu_im ** sym.Const(2.0))) ** sym.Const(0.5)) / wt_controlMeasurements_SNom))
    initial_equations[wt_controlMeasurements_PPu] = wt_protectionMeasurements_complexToReal_re
    initial_equations[wt_controlMeasurements_PPuSnRef] = (-wt_controlMeasurements_P0Pu)
    initial_equations[wt_controlMeasurements_QPu] = wt_protectionMeasurements_product_y_im
    initial_equations[wt_controlMeasurements_QPuSnRef] = (-wt_controlMeasurements_Q0Pu)
    initial_equations[wt_controlMeasurements_UPu] = wt_controlMeasurements_UWtPu
    initial_equations[wt_controlMeasurements_UWtPu] = (((grid_terminal_V_re ** sym.Const(2.0)) + (grid_terminal_V_im ** sym.Const(2.0))) ** sym.Const(0.5))
    initial_equations[wt_controlMeasurements_iPu_im] = (((-wt_wT4Injector_elecSystem_i0Pu_im) * sym.Const(100.0)) / wt_wT4Injector_elecSystem_SNom)
    initial_equations[wt_controlMeasurements_iPu_re] = (((-wt_wT4Injector_elecSystem_i0Pu_re) * sym.Const(100.0)) / wt_wT4Injector_elecSystem_SNom)
    initial_equations[wt_controlMeasurements_omegaFiltPu] = vf.add_const(1.0, name='')
    initial_equations[wt_controlMeasurements_theta] = sym.atan2(grid_terminal_V_im, (grid_terminal_V_re + sym.Const(2.220446049250313e-16)))
    initial_equations[wt_mechanical_add2_y] = vf.add_const(0.0, name='')
    initial_equations[wt_mechanical_pI_y] = wt_mechanical_pI_Y0
    initial_equations[wt_omegaRefPu] = vf.add_const(1.0, name='')
    initial_equations[wt_pll_absLimRateLimFirstOrderFreeze_y] = wt_pll_absLimRateLimFirstOrderFreeze_Y0
    initial_equations[wt_pll_thetaPll] = wt_wT4Injector_genSystem_iECFrameRotation_UPhase0
    initial_equations[wt_protectionMeasurements_IWtPu] = (sym.Const(100.0) * ((((wt_controlMeasurements_i0Pu_re ** sym.Const(2.0)) + (wt_controlMeasurements_i0Pu_im ** sym.Const(2.0))) ** sym.Const(0.5)) / wt_controlMeasurements_SNom))
    initial_equations[wt_protectionMeasurements_PPu] = wt_protectionMeasurements_complexToReal_re
    initial_equations[wt_protectionMeasurements_PPuSnRef] = (sym.Const(0.01) * (wt_protectionMeasurements_PPu * wt_protectionMeasurements_SNom))
    initial_equations[wt_protectionMeasurements_QPu] = wt_protectionMeasurements_product_y_im
    initial_equations[wt_protectionMeasurements_QPuSnRef] = (sym.Const(0.01) * (wt_protectionMeasurements_QPu * wt_protectionMeasurements_SNom))
    initial_equations[wt_protectionMeasurements_UPu] = wt_protectionMeasurements_UWtPu
    initial_equations[wt_protectionMeasurements_UWtPu] = (((grid_terminal_V_re ** sym.Const(2.0)) + (grid_terminal_V_im ** sym.Const(2.0))) ** sym.Const(0.5))
    initial_equations[wt_protectionMeasurements_omegaFiltPu] = vf.add_const(1.0, name='')
    initial_equations[wt_protectionMeasurements_theta] = sym.atan2(grid_terminal_V_im, (grid_terminal_V_re + sym.Const(2.220446049250313e-16)))
    initial_equations[wt_tanPhi] = vf.add_const(0.0, name='')
    initial_equations[wt_terminal_i_im] = wt_wT4Injector_elecSystem_i0Pu_im
    initial_equations[wt_terminal_i_re] = wt_wT4Injector_elecSystem_i0Pu_re
    initial_equations[wt_wT4Injector_PAgPu] = wt_wT4Injector_genSystem_PAg0Pu
    initial_equations[wt_wT4Injector_PGenPu] = (-wt_wT4Injector_P0Pu)
    initial_equations[wt_wT4Injector_QGenPu] = (-wt_wT4Injector_Q0Pu)
    initial_equations[wt_wT4Injector_elecSystem_IGsPu] = sym.sqrt(((wt_wT4Injector_elecSystem_IGsRe0Pu ** sym.Const(2.0)) + (wt_wT4Injector_elecSystem_IGsIm0Pu ** sym.Const(2.0))))
    initial_equations[wt_wT4Injector_elecSystem_UGsPu] = sym.sqrt(((wt_wT4Injector_elecSystem_UGsRe0Pu ** sym.Const(2.0)) + (wt_wT4Injector_elecSystem_UGsIm0Pu ** sym.Const(2.0))))
    initial_equations[wt_wT4Injector_elecSystem_iGsImPu] = wt_wT4Injector_elecSystem_IGsIm0Pu
    initial_equations[wt_wT4Injector_elecSystem_iGsRePu] = wt_wT4Injector_elecSystem_IGsRe0Pu
    initial_equations[wt_wT4Injector_elecSystem_uGsImPu] = wt_wT4Injector_genSystem_UGsIm0Pu
    initial_equations[wt_wT4Injector_elecSystem_uGsRePu] = wt_wT4Injector_genSystem_UGsRe0Pu
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y] = (((-wt_wT4Injector_genSystem_iECFrameRotation_P0Pu) * sym.Const(100.0)) / (wt_wT4Injector_genSystem_iECFrameRotation_SNom * wt_wT4Injector_genSystem_iECFrameRotation_U0Pu))
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y] = ((wt_wT4Injector_genSystem_iECFrameRotation_Q0Pu * sym.Const(100.0)) / (wt_wT4Injector_genSystem_iECFrameRotation_SNom * wt_wT4Injector_genSystem_iECFrameRotation_U0Pu))
    initial_equations[wt_wT4Injector_genSystem_realToComplex_im] = ((sym.sin(wt_pll_thetaPll) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y) + (sym.cos(wt_pll_thetaPll) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y))
    initial_equations[wt_wT4Injector_genSystem_realToComplex_re] = ((sym.cos(wt_pll_thetaPll) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_y) - (sym.sin(wt_pll_thetaPll) * wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_y))
    initial_equations[wt_wT4Injector_genSystem_terminal_i_im] = (sym.Const(0.01) * ((-wt_wT4Injector_elecSystem_IGsIm0Pu) * wt_wT4Injector_elecSystem_SNom))
    initial_equations[wt_wT4Injector_genSystem_terminal_i_re] = (sym.Const(0.01) * ((-wt_wT4Injector_elecSystem_IGsRe0Pu) * wt_wT4Injector_elecSystem_SNom))
    initial_equations[wt_xWTRefPu] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_currentLimiter_product1_y] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_delayFlag_fO] = ((wt_control4B_qControl_delayFlag_fI * wt_control4B_qControl_delayFlag_booleanToInteger_y) + ((sym.Const(1.0) - wt_control4B_qControl_delayFlag_fI) * wt_control4B_qControl_delayFlag_switch1_y))
    initial_equations[wt_control4B_qControl_fFrt] = vf.add_const(0.0, name='')
    initial_equations[wt_wT4Injector_state] = PRE_wt_wT4Injector_state
    initial_equations[whenCondition11] = wt_gridProtection_lessEqual2_y
    initial_equations[whenCondition12] = wt_gridProtection_lessEqual3_y
    initial_equations[wt_control4B_pControl4B_and1_y] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_delayFlag_fI] = sym.heaviside(((wt_control4B_qControl_lessThreshold_threshold - wt_controlMeasurements_firstOrder3_y) - sym.Const(1e-06)))
    initial_equations[wt_control4B_qLimiter_integerToBoolean_y] = vf.add_const(0.0, name='')
    initial_equations[wt_gridProtection_lessEqual2_y] = sym.heaviside(((wt_protectionMeasurements_omegaFiltPu - wt_gridProtection_const2_k) + sym.Const(1e-06)))
    initial_equations[wt_gridProtection_lessEqual3_y] = sym.heaviside(((wt_gridProtection_const3_k - wt_protectionMeasurements_omegaFiltPu) + sym.Const(1e-06)))
    initial_equations[wt_pll_fixedBooleanDelay_y] = PRE_wt_pll_fixedBooleanDelay_y
    initial_equations[wt_pll_fixedBooleanDelay1_y] = PRE_wt_pll_fixedBooleanDelay1_y
    initial_equations[wt_wT4Injector_running_value] = PRE_wt_wT4Injector_running_value
    initial_equations[wt_wT4Injector_switchOffSignal1_value] = vf.add_const(0.0, name='')
    initial_equations[wt_wT4Injector_switchOffSignal2_value] = vf.add_const(0.0, name='')
    initial_equations[wt_wT4Injector_switchOffSignal3_value] = vf.add_const(0.0, name='')
    initial_equations[grid_U] = (grid_UPu * grid_UNom)
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_wT4Injector_genSystem_absLimRateLimFirstOrderAntiWindup1_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_pll_absLimRateLimFirstOrderFreeze_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_pll_absLimRateLimFirstOrderFreeze_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_pll_absLimRateLimFirstOrderFreeze_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qLimiter_absLimRateLimFeedthroughFreeze1_rampLimiter_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_pControl4B_absLimRateLimFirstOrderAntiWindup_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_pControl4B_rampLimiter_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_pControl4B_rampLimiter_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_pControl4B_rampLimiter_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_limiter2_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_limiter3_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_antiWindupIntegrator_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_antiWindupIntegrator_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_antiWindupIntegrator_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_antiWindupIntegrator_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_antiWindupIntegrator1_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_antiWindupIntegrator1_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_antiWindupIntegrator1_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_antiWindupIntegrator1_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_absLimRateLimFeedthroughFreeze_rampLimiter_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_mechanical_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_mechanical_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_mechanical_integrator1_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_mechanical_integrator1_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_mechanical_pI_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_mechanical_pI_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_protectionMeasurements_rampLimiter_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_protectionMeasurements_rampLimiter_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_protectionMeasurements_rampLimiter_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[wt_controlMeasurements_rampLimiter_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[wt_controlMeasurements_rampLimiter_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[wt_controlMeasurements_rampLimiter_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[PRE_wt_wT4Injector_running_value] = START_wt_wT4Injector_running_value
    initial_equations[whenCondition3] = (sym.Const(1.0) - PRE_wt_wT4Injector_running_value)
    initial_equations[whenCondition1] = (wt_wT4Injector_running_value * (sym.Const(1.0) - PRE_wt_wT4Injector_running_value))
    initial_equations[PRE_wt_pll_fixedBooleanDelay1_y] = START_wt_pll_fixedBooleanDelay1_y
    initial_equations[PRE_wt_pll_fixedBooleanDelay_y] = START_wt_pll_fixedBooleanDelay_y
    initial_equations[wt_gridProtection_lessEqual_y] = sym.heaviside(((wt_protectionMeasurements_firstOrder3_y - wt_gridProtection_const_k) + sym.Const(1e-06)))
    initial_equations[whenCondition9] = wt_gridProtection_lessEqual_y
    initial_equations[wt_gridProtection_lessEqual1_y] = sym.heaviside(((wt_gridProtection_const1_k - wt_protectionMeasurements_firstOrder3_y) + sym.Const(1e-06)))
    initial_equations[whenCondition10] = wt_gridProtection_lessEqual1_y
    initial_equations[whenCondition8] = (sym.Const(1.0) - wt_control4B_qControl_delayFlag_fI)
    initial_equations[wt_control4B_qControl_delayFlag_booleanToInteger_y] = ((wt_control4B_qControl_delayFlag_fI * wt_control4B_qControl_delayFlag_booleanToInteger_integerTrue) + ((sym.Const(1.0) - wt_control4B_qControl_delayFlag_fI) * wt_control4B_qControl_delayFlag_booleanToInteger_integerFalse))
    initial_equations[wt_control4B_qControl_switch2_u_3] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_switch2_u_2] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_switch2_u_1] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_currentLimiter_product1_u_2] = ((wt_control4B_currentLimiter_booleanConstant1_k * wt_control4B_currentLimiter_booleanToInteger_integerTrue) + ((sym.Const(1.0) - wt_control4B_currentLimiter_booleanConstant1_k) * wt_control4B_currentLimiter_booleanToInteger_integerFalse))
    initial_equations[wt_control4B_qControl_switch2_u_5] = vf.add_const(0.0, name='')
    initial_equations[grid_terminal_V_re] = (grid_UPu * sym.cos(grid_UPhase))
    initial_equations[grid_terminal_V_im] = (grid_UPu * sym.sin(grid_UPhase))
    initial_equations[wt_pll_fixedBooleanDelay_yReal] = wt_pll_fixedBooleanDelay_uReal
    initial_equations[wt_pll_fixedBooleanDelay1_yReal] = wt_pll_fixedBooleanDelay1_uReal
    initial_equations[PRE_wt_gridProtection_pre1_u] = wt_gridProtection_pre1_pre_u_start
    initial_equations[wt_gridProtection_or1_u_5] = PRE_wt_gridProtection_pre1_u
    initial_equations[PRE_wt_gridProtection_timer3_entryTime] = vf.add_const(0.0, name='')
    initial_equations[wt_gridProtection_timer3_entryTime] = PRE_wt_gridProtection_timer3_entryTime
    initial_equations[wt_gridProtection_timer3_y] = ((wt_gridProtection_lessEqual3_y * (time - wt_gridProtection_timer3_entryTime)) + ((sym.Const(1.0) - wt_gridProtection_lessEqual3_y) * sym.Const(0.0)))
    initial_equations[wt_gridProtection_or1_u_4] = sym.heaviside(((wt_gridProtection_timer3_y - wt_gridProtection_combiTable1D3_y_1) - sym.Const(1e-06)))
    initial_equations[whenCondition15] = wt_gridProtection_or1_u_4
    initial_equations[PRE_wt_gridProtection_timer2_entryTime] = vf.add_const(0.0, name='')
    initial_equations[wt_gridProtection_timer2_entryTime] = PRE_wt_gridProtection_timer2_entryTime
    initial_equations[wt_gridProtection_timer2_y] = ((wt_gridProtection_lessEqual2_y * (time - wt_gridProtection_timer2_entryTime)) + ((sym.Const(1.0) - wt_gridProtection_lessEqual2_y) * sym.Const(0.0)))
    initial_equations[wt_gridProtection_or1_u_3] = sym.heaviside(((wt_gridProtection_timer2_y - wt_gridProtection_combiTable1D2_y_1) - sym.Const(1e-06)))
    initial_equations[whenCondition16] = wt_gridProtection_or1_u_3
    initial_equations[PRE_wt_gridProtection_timer1_entryTime] = vf.add_const(0.0, name='')
    initial_equations[wt_gridProtection_timer1_entryTime] = PRE_wt_gridProtection_timer1_entryTime
    initial_equations[wt_gridProtection_timer1_y] = ((wt_gridProtection_lessEqual1_y * (time - wt_gridProtection_timer1_entryTime)) + ((sym.Const(1.0) - wt_gridProtection_lessEqual1_y) * sym.Const(0.0)))
    initial_equations[wt_gridProtection_or1_u_2] = sym.heaviside(((wt_gridProtection_timer1_y - wt_gridProtection_combiTable1D1_y_1) - sym.Const(1e-06)))
    initial_equations[whenCondition13] = wt_gridProtection_or1_u_2
    initial_equations[PRE_wt_gridProtection_timer_entryTime] = vf.add_const(0.0, name='')
    initial_equations[wt_gridProtection_timer_entryTime] = PRE_wt_gridProtection_timer_entryTime
    initial_equations[wt_gridProtection_timer_y] = ((wt_gridProtection_lessEqual_y * (time - wt_gridProtection_timer_entryTime)) + ((sym.Const(1.0) - wt_gridProtection_lessEqual_y) * sym.Const(0.0)))
    initial_equations[wt_gridProtection_or1_u_1] = sym.heaviside(((wt_gridProtection_timer_y - wt_gridProtection_combiTable1D_y_1) - sym.Const(1e-06)))
    initial_equations[whenCondition14] = wt_gridProtection_or1_u_1
    initial_equations[wt_gridProtection_pre1_u] = (sym.Const(1.0) - (((((sym.Const(1.0) - wt_gridProtection_or1_u_1) * (sym.Const(1.0) - wt_gridProtection_or1_u_2)) * (sym.Const(1.0) - wt_gridProtection_or1_u_3)) * (sym.Const(1.0) - wt_gridProtection_or1_u_4)) * (sym.Const(1.0) - wt_gridProtection_or1_u_5)))
    initial_equations[PRE_wt_control4B_qControl_delayFlag_timer_entryTime] = vf.add_const(0.0, name='')
    initial_equations[wt_control4B_qControl_delayFlag_timer_entryTime] = PRE_wt_control4B_qControl_delayFlag_timer_entryTime
    initial_equations[wt_control4B_qControl_delayFlag_timer_y] = (((sym.Const(1.0) - wt_control4B_qControl_delayFlag_fI) * (time - wt_control4B_qControl_delayFlag_timer_entryTime)) + ((sym.Const(1.0) - (sym.Const(1.0) - wt_control4B_qControl_delayFlag_fI)) * sym.Const(0.0)))
    initial_equations[wt_control4B_qControl_variableLimiter_y] = ((sym.heaviside(((wt_control4B_qControl_switch2_y - wt_control4B_qLimiter_QWTMaxPu) - sym.Const(1e-06))) * wt_control4B_qLimiter_QWTMaxPu) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qControl_switch2_y - wt_control4B_qLimiter_QWTMaxPu) - sym.Const(1e-06)))) * ((sym.heaviside(((wt_control4B_qLimiter_QWTMinPu - wt_control4B_qControl_switch2_y) - sym.Const(1e-06))) * wt_control4B_qLimiter_QWTMinPu) + ((sym.Const(1.0) - sym.heaviside(((wt_control4B_qLimiter_QWTMinPu - wt_control4B_qControl_switch2_y) - sym.Const(1e-06)))) * wt_control4B_qControl_switch2_y))))
    initial_equations[wt_control4B_qControl_absLimRateLimFirstOrderFreeze_feedback_y] = (wt_control4B_qControl_switch2_y - wt_control4B_qControl_absLimRateLimFirstOrderFreeze_y)
    initial_equations[wt_protectionMeasurements_product_y_im] = ((grid_terminal_V_im * wt_controlMeasurements_iPu_re) - (grid_terminal_V_re * wt_controlMeasurements_iPu_im))
    initial_equations[wt_protectionMeasurements_complexToReal_im] = ((wt_protectionMeasurements_complexToReal_useConjugateInput * (-wt_protectionMeasurements_product_y_im)) + ((sym.Const(1.0) - wt_protectionMeasurements_complexToReal_useConjugateInput) * wt_protectionMeasurements_product_y_im))
    initial_equations[wt_controlMeasurements_product_y_im] = wt_protectionMeasurements_product_y_im
    initial_equations[wt_controlMeasurements_complexToReal_im] = ((wt_controlMeasurements_complexToReal_useConjugateInput * (-wt_controlMeasurements_product_y_im)) + ((sym.Const(1.0) - wt_controlMeasurements_complexToReal_useConjugateInput) * wt_controlMeasurements_product_y_im))
    initial_equations[wt_protectionMeasurements_complexToReal_re] = ((grid_terminal_V_re * wt_controlMeasurements_iPu_re) + (grid_terminal_V_im * wt_controlMeasurements_iPu_im))
    initial_equations[wt_controlMeasurements_complexToReal_re] = wt_protectionMeasurements_complexToReal_re
    initial_equations[PRE_wt_wT4Injector_state] = START_wt_wT4Injector_state
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations[d_wt_protectionMeasurements_firstOrder_y] = (((wt_protectionMeasurements_firstOrder_k * wt_protectionMeasurements_complexToReal_re) - wt_protectionMeasurements_firstOrder_y) / wt_protectionMeasurements_firstOrder_T)
    differential_initial_equations[d_wt_controlMeasurements_firstOrder_y] = (((wt_controlMeasurements_firstOrder_k * wt_controlMeasurements_complexToReal_re) - wt_controlMeasurements_firstOrder_y) / wt_controlMeasurements_firstOrder_T)
    differential_initial_equations[d_wt_controlMeasurements_firstOrder2_y] = (((wt_controlMeasurements_firstOrder2_k * wt_controlMeasurements_complexToPolar_len) - wt_controlMeasurements_firstOrder2_y) / wt_controlMeasurements_firstOrder2_T)
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

    template.comment = 'Generator WECC type-4 wind current-source B 2020'
    return template
