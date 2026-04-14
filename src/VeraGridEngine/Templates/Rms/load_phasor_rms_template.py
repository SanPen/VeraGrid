# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType, DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate


def get_load_phasor_rms_template(vfactory: VarFactory, name="Load phasor rms template") -> RmsModelTemplate:
    """
    Get the RMS template model of the Load using phasor coordinates (Vr, Vi)
    :return: RmsModelTemplate
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    # Phasor inputs: Vr, Vi
    inputs = [
        vfactory.add_var("Vr_" + name),
        vfactory.add_var("Vi_" + name)
    ]

    Pl0 = vfactory.add_var("Pl0")
    Ql0 = vfactory.add_var("Ql0")

    Ql = vfactory.add_var("Ql")
    Pl = vfactory.add_var("Pl")

    templ.block.event_dict[Pl0] = vfactory.add_const(-0.0999999)
    templ.block.event_dict[Ql0] = vfactory.add_const(-0.009999999862208533)

    templ.block.algebraic_vars = [Pl, Ql]

    # Constant power load: Pl = Pl0, Ql = Ql0
    # The load doesn't depend on voltage in this simple model
    templ.block.algebraic_eqs = [Pl - Pl0, Ql - Ql0]

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Vr: inputs[0],
        VarPowerFlowRefferenceType.Vi: inputs[1],
        VarPowerFlowRefferenceType.P: Pl,
        VarPowerFlowRefferenceType.Q: Ql
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.Pl0: Pl0,
        ParamPowerFlowRefferenceType.Ql0: Ql0,
    }

    templ.block.in_vars = inputs

    return templ
