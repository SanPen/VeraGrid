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
    Get the phasor-based RMS template model of the Line.
    
    This template uses phasor representation (Vr, Vi) for voltages, which makes
    the current equations linear. The power equations are derived from:
    - Current: I = Y * (Vf - Vt) + Ysh * V
    - Power: S = V * conj(I)
    
    Where V = Vr + j*Vi and Y = g + j*b
    
    :param vfactory: Variable factory for creating variables
    :param name: Name of the template
    :return: RmsModelTemplate with phasor-based line equations
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LineDevice
    templ.name = name

    # Inputs: phasor voltages at from and to buses
    inputs: List[Var] = [vfactory.add_var("Vrf_" + name),
                         vfactory.add_var("Vif_" + name),
                         vfactory.add_var("Vrt_" + name),
                         vfactory.add_var("Vit_" + name)]

    # Outputs: power flows
    Qf = vfactory.add_var("Qf")
    Qt = vfactory.add_var("Qt")
    Pf = vfactory.add_var("Pf")
    Pt = vfactory.add_var("Pt")

    # Parameters: line admittance
    g = vfactory.add_var("g")
    b = vfactory.add_var("b")
    bsh = vfactory.add_var("bsh")

    # Set default parameter values
    templ.block.parameters[g] = vfactory.add_const(5)
    templ.block.parameters[b] = vfactory.add_const(-12)
    templ.block.parameters[bsh] = vfactory.add_const(0.03)

    templ.block.algebraic_vars = [Pf, Pt, Qf, Qt]

    # Voltage variables
    Vrf = inputs[0]
    Vif = inputs[1]
    Vrt = inputs[2]
    Vit = inputs[3]
    
    # Current equations (linear in phasor representation)
    # If = (g+j*b)*(Vf-Vt) + j*(bsh/2)*Vf
    # Real part of current at from bus
    Ir_f = g * (Vrf - Vrt) - b * (Vif - Vit) - (bsh / 2) * Vif
    # Imaginary part of current at from bus  
    Ii_f = g * (Vif - Vit) + b * (Vrf - Vrt) + (bsh / 2) * Vrf
    
    # It = (g+j*b)*(Vt-Vf) + j*(bsh/2)*Vt
    # Real part of current at to bus
    Ir_t = g * (Vrt - Vrf) - b * (Vit - Vif) - (bsh / 2) * Vit
    # Imaginary part of current at to bus
    Ii_t = g * (Vit - Vif) + b * (Vrt - Vrf) + (bsh / 2) * Vrt

    # Power equations: S = V * conj(I) = (Vr+j*Vi)*(Ir-j*Ii)
    # Pf = Vrf*Ir_f + Vif*Ii_f
    # Qf = Vif*Ir_f - Vrf*Ii_f
    # Pt = Vrt*Ir_t + Vit*Ii_t
    # Qt = Vit*Ir_t - Vrt*Ii_t
    
    templ.block.algebraic_eqs = [
        Pf - (Vrf * Ir_f + Vif * Ii_f),
        Qf - (Vif * Ir_f - Vrf * Ii_f),
        Pt - (Vrt * Ir_t + Vit * Ii_t),
        Qt - (Vit * Ir_t - Vrt * Ii_t),
    ]

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Vrf: inputs[0],
        VarPowerFlowRefferenceType.Vif: inputs[1],
        VarPowerFlowRefferenceType.Vrt: inputs[2],
        VarPowerFlowRefferenceType.Vit: inputs[3],
        VarPowerFlowRefferenceType.Pf: Pf,
        VarPowerFlowRefferenceType.Pt: Pt,
        VarPowerFlowRefferenceType.Qf: Qf,
        VarPowerFlowRefferenceType.Qt: Qt,
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.g: g,
        ParamPowerFlowRefferenceType.b: b,
        ParamPowerFlowRefferenceType.bsh: bsh,
    }

    templ.block.in_vars = inputs

    return templ
