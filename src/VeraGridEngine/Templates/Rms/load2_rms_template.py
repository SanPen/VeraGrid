# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate



def get_load2_rms_template(var_factory: VarFactory, name = "Load rms template") -> RmsModelTemplate:
    """
    Get the RMS template model of the Load
    :return: RmsModelTemplate
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    inputs= [var_factory.add_var("Vm_" + name),
                         var_factory.add_var("Va_" + name)
                         ]

    Pl0 = var_factory.add_var("Pl0")
    Ql0 = var_factory.add_var("Ql0")

    Ql = var_factory.add_var("Ql")
    Pl = var_factory.add_var("Pl")

    # templ.block.event_dict[Pl0] = var_factory.add_const(-0.0999999)
    # templ.block.event_dict[Ql0] = var_factory.add_const(-0.009999999862208533)

    templ.block.event_dict[Pl0] = var_factory.add_const(-17.6699999999199)
    templ.block.event_dict[Ql0] = var_factory.add_const(-0.999999999989467)

    templ.block.algebraic_vars = [Pl, Ql]

    templ.block.algebraic_eqs = [
                Pl - Pl0,
                Ql - Ql0]

    templ.block.external_mapping = {
        VarPowerFlowReferenceType.Va: inputs[0],
        VarPowerFlowReferenceType.Vm: inputs[1],
        VarPowerFlowReferenceType.P: Pl,
        VarPowerFlowReferenceType.Q: Ql
    }

    templ.block.in_vars = inputs

    return templ