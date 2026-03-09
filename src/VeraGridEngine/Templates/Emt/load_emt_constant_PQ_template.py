# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType, DeviceType
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate


def get_load_3ph_emt_template(vfactory: VarFactory, name = "Load rms template") -> EmtModelTemplate:
    """
    Get the EMT template model of a balanced phase-decoupled three-phase load
    :return: EmtModelTemplate
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    Pl0_A = vfactory.add_var("Pl0_A")
    Ql0_A = vfactory.add_var("Ql0_A")
    Pl0_B = vfactory.add_var("Pl0_B")
    Ql0_B = vfactory.add_var("Ql0_B")
    Pl0_C = vfactory.add_var("Pl0_C")
    Ql0_C = vfactory.add_var("Ql0_C")

    Ql_A = vfactory.add_var("Ql_A")
    Pl_A = vfactory.add_var("Pl_A")
    Ql_B = vfactory.add_var("Ql_B")
    Pl_B = vfactory.add_var("Pl_B")
    Ql_C = vfactory.add_var("Ql_C")
    Pl_C = vfactory.add_var("Pl_C")


    templ.block.event_dict[Pl0_A] = vfactory.add_const(-0.0999999/3)
    templ.block.event_dict[Ql0_A] = vfactory.add_const(-0.009999999862208533/3)
    templ.block.event_dict[Pl0_B] = vfactory.add_const(-0.0999999/3)
    templ.block.event_dict[Ql0_B] = vfactory.add_const(-0.009999999862208533/3)
    templ.block.event_dict[Pl0_C] = vfactory.add_const(-0.0999999/3)
    templ.block.event_dict[Ql0_C] = vfactory.add_const(-0.009999999862208533/3)

    templ.block.algebraic_vars = [Pl_A, Pl_B, Pl_C, Ql_A, Ql_B, Ql_C]

    templ.block.algebraic_eqs = [
        Pl_A - Pl0_A,
        Ql_A - Ql0_A,
        Pl_B - Pl0_B,
        Ql_B - Ql0_B,
        Pl_C - Pl0_C,
        Ql_C - Ql0_C,
    ]

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.P: None,
        VarPowerFlowRefferenceType.Q: None,
        VarPowerFlowRefferenceType.P_N: None,
        VarPowerFlowRefferenceType.Q_N: None,
        VarPowerFlowRefferenceType.P_A: Pl_A,
        VarPowerFlowRefferenceType.Q_A: Ql_A,
        VarPowerFlowRefferenceType.P_B: Pl_B,
        VarPowerFlowRefferenceType.Q_B: Ql_B,
        VarPowerFlowRefferenceType.P_C: Pl_C,
        VarPowerFlowRefferenceType.Q_C: Ql_C,
        VarPowerFlowRefferenceType.i_N: None,
        VarPowerFlowRefferenceType.i_A: None,
        VarPowerFlowRefferenceType.i_B: None,
        VarPowerFlowRefferenceType.i_C: None,
        VarPowerFlowRefferenceType.theta: None
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.Pl0_A: Pl0_A,
        ParamPowerFlowRefferenceType.Ql0_A: Ql0_A,
        ParamPowerFlowRefferenceType.Pl0_B: Pl0_B,
        ParamPowerFlowRefferenceType.Ql0_B: Ql0_B,
        ParamPowerFlowRefferenceType.Pl0_C: Pl0_C,
        ParamPowerFlowRefferenceType.Ql0_C: Ql0_C,
    }

    return templ