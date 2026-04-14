# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List
import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def get_line_phasor_rms_template(vfactory: VarFactory, name="Line_phasor_rms_template") -> RmsModelTemplate:
    """
    Get the phasor-based RMS template model of the Line using current balance.
    
    This template uses phasor representation (Vr, Vi) for voltages and outputs
    currents directly for current balance equations:
    - Current: I = Y * (Vf - Vt) + Ysh * V
    
    Where V = Vr + j*Vi and Y = g + j*b
    
    :param vfactory: Variable factory for creating variables
    :param name: Name of the template
    :return: RmsModelTemplate with phasor-based line current equations
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LineDevice
    templ.name = name

    # Inputs: phasor voltages at from and to buses
    inputs: List[Var] = [vfactory.add_var("Vrf_" + name, VarPowerFlowRefferenceType.Vrf),
                         vfactory.add_var("Vif_" + name, VarPowerFlowRefferenceType.Vif),
                         vfactory.add_var("Vrt_" + name, VarPowerFlowRefferenceType.Vrt),
                         vfactory.add_var("Vit_" + name, VarPowerFlowRefferenceType.Vit)]

    # Outputs: currents (for current balance formulation)
    Irf = vfactory.add_var("Irf")
    Iif = vfactory.add_var("Iif")
    Irt = vfactory.add_var("Irt")
    Iit = vfactory.add_var("Iit")

    # Parameters: line admittance
    g = vfactory.add_var("g")
    b = vfactory.add_var("b")
    bsh = vfactory.add_var("bsh")

    # Set default parameter values
    templ.block.parameters[g] = vfactory.add_const(5)
    templ.block.parameters[b] = vfactory.add_const(-12)
    templ.block.parameters[bsh] = vfactory.add_const(0.03)

    templ.block.algebraic_vars = [Irf, Iif, Irt, Iit]

    # Voltage variables
    Vrf = inputs[0]
    Vif = inputs[1]
    Vrt = inputs[2]
    Vit = inputs[3]
    
    # Current equations (linear in phasor representation)
    # If = (g+j*b)*(Vf-Vt) + j*(bsh/2)*Vf
    # Ir_f = g*(Vrf-Vrt) - b*(Vif-Vit) - (bsh/2)*Vif
    # Ii_f = g*(Vif-Vit) + b*(Vrf-Vrt) + (bsh/2)*Vrf
    
    # It = (g+j*b)*(Vt-Vf) + j*(bsh/2)*Vt
    # Ir_t = g*(Vrt-Vrf) - b*(Vit-Vif) - (bsh/2)*Vit
    # Ii_t = g*(Vit-Vif) + b*(Vrt-Vrf) + (bsh/2)*Vrt
    
    # Direct current output equations
    templ.block.algebraic_eqs = [
        Irf - (g * (Vrf - Vrt) - b * (Vif - Vit) - (bsh / 2) * Vif),
        Iif - (g * (Vif - Vit) + b * (Vrf - Vrt) + (bsh / 2) * Vrf),
        Irt - (g * (Vrt - Vrf) - b * (Vit - Vif) - (bsh / 2) * Vit),
        Iit - (g * (Vit - Vif) + b * (Vrt - Vrf) + (bsh / 2) * Vrt),
    ]

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Vrf: inputs[0],
        VarPowerFlowRefferenceType.Vif: inputs[1],
        VarPowerFlowRefferenceType.Vrt: inputs[2],
        VarPowerFlowRefferenceType.Vit: inputs[3],
        VarPowerFlowRefferenceType.Irf: Irf,
        VarPowerFlowRefferenceType.Iif: Iif,
        VarPowerFlowRefferenceType.Irt: Irt,
        VarPowerFlowRefferenceType.Iit: Iit,
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.g: g,
        ParamPowerFlowRefferenceType.b: b,
        ParamPowerFlowRefferenceType.bsh: bsh,
    }

    templ.block.in_vars = inputs

    return templ
