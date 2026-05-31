# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType, DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block


def get_load_rms_template(
        vfactory: VarFactory,
        name="Load rms template",
        pl0_init: float | None = None,
        ql0_init: float | None = None,
) -> RmsModelTemplate:
    """
    Get the RMS template model of the Load
    :return: RmsModelTemplate
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    inputs = [
        vfactory.add_var("Vm_" + name, reference=VarPowerFlowRefferenceType.Vm),
        vfactory.add_var("Va_" + name, reference=VarPowerFlowRefferenceType.Va)
    ]

    Pl0 = vfactory.add_var("Pl0")
    Ql0 = vfactory.add_var("Ql0")
    Pl = vfactory.add_var("Pl", reference=VarPowerFlowRefferenceType.P)
    Ql = vfactory.add_var("Ql", reference=VarPowerFlowRefferenceType.Q)

    block = Block()

    block.event_dict[Pl0] = Pl
    block.event_dict[Ql0] = Ql

    block.algebraic_vars = [Pl, Ql]


    block.algebraic_eqs = [Pl - Pl0, Ql - Ql0]

    block.in_vars = inputs
    block.out_vars = [Pl, Ql]

    block.name = name

    templ.block.children.append(block)

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Va: inputs[0],
        VarPowerFlowRefferenceType.Vm: inputs[1],
        VarPowerFlowRefferenceType.P: Pl,
        VarPowerFlowRefferenceType.Q: Ql
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.Pl0: Pl0,
        ParamPowerFlowRefferenceType.Ql0: Ql0,
    }

    #templ.block.init_eqs = {
    #    Pl0: Pl,
    #    Ql0: Ql,
    #}
    templ.block.in_vars = inputs
    templ.block.out_vars = [Pl, Ql]

    return templ
