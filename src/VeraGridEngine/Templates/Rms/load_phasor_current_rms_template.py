# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType, DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate


def get_load_phasor_current_rms_template(vfactory: VarFactory, name:str = '') -> RmsModelTemplate:
    """
    Get the RMS template model of the Load using constant current injection in phasor coordinates.
    
    This model injects constant current at the bus:
    - Ir = constant
    - Ii = constant
    
    :param vfactory: Variable factory for creating variables
    :param name: Name of the template
    :return: RmsModelTemplate with constant current load model
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    # Phasor inputs: Vr, Vi (for reference, not used in constant current model)
    inputs = [
        vfactory.add_var("Vr_" + name),
        vfactory.add_var("Vi_" + name)
    ]

    # Constant current injection parameters
    Ir0 = vfactory.add_var("Ir0")
    Ii0 = vfactory.add_var("Ii0")

    # Current injection variables
    Ir = vfactory.add_var("Ir")
    Ii = vfactory.add_var("Ii")

    # Default values (will be overwritten by initialization)
    templ.block.event_dict[Ir0] = vfactory.add_const(None)
    templ.block.event_dict[Ii0] = vfactory.add_const(None)

    templ.block.algebraic_vars = [Ir, Ii]

    # Constant current equations
    templ.block.algebraic_eqs = [Ir - Ir0, Ii - Ii0]

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Vr: inputs[0],
        VarPowerFlowRefferenceType.Vi: inputs[1],
        VarPowerFlowRefferenceType.Ir: Ir,
        VarPowerFlowRefferenceType.Ii: Ii
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.Ir0: Ir0,
        ParamPowerFlowRefferenceType.Ii0: Ii0,
    }

    templ.block.init_eqs = {
        Ir0: Ir,
        Ii0: Ii,
    }
    templ.block.out_vars = [Ir, Ii]
    templ.block.in_vars = inputs

    return templ
