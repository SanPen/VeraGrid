# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List
import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowReferenceType, VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.symbolic import Var, cos, sin


def get_line_rms_ml_template(vfactory: VarFactory, name="Line_rms_template") -> RmsModelTemplate:
    """
    Get the RMS template model of the Line
    :return: RmsModelTemplate
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LineDevice
    templ.name = name

    inputs: List[Var] = [vfactory.add_var("Vmf", VarPowerFlowReferenceType.Vmf),
                         vfactory.add_var("Vaf", VarPowerFlowReferenceType.Vaf),
                         vfactory.add_var("Vmt", VarPowerFlowReferenceType.Vmt),
                         vfactory.add_var("Vat", VarPowerFlowReferenceType.Vat), ]

    Qf = vfactory.add_var("Qf")
    Qt = vfactory.add_var("Qt")
    Pf = vfactory.add_var("Pf")
    Pt = vfactory.add_var("Pt")
    v0 = vfactory.add_var("v0")
    v2 = vfactory.add_var("v2")

    g = vfactory.add_var("g")
    b = vfactory.add_var("b")
    bsh = vfactory.add_var("bsh")

    templ.block.parameters[g] = vfactory.add_const(5)
    templ.block.parameters[b] = vfactory.add_const(-12)
    templ.block.parameters[bsh] = vfactory.add_const(0.03)

    templ.block.algebraic_vars = [Pf, Pt, Qf, Qt, v0, v2]

    theta = inputs[1] - inputs[3]
    templ.block.algebraic_eqs = [
        Pf - ((inputs[0] *v0 * g) - g * inputs[0] * inputs[2] * cos(theta) - b * inputs[0] * inputs[2] * sin(theta)),
        Qf - (inputs[0] *v0 * (-bsh / 2 - b) - g * inputs[0] * inputs[2] * sin(theta) + b * inputs[0] * inputs[2] * cos(theta)),
        Pt - ((inputs[2] *v2 * g) - g * inputs[2] * inputs[0] * cos(theta) - b * inputs[2] * inputs[0] * sin(theta)),
        Qt - (inputs[2] *v2 * (-bsh / 2 - b) + g * inputs[2] * inputs[0] * sin(theta) - b * inputs[2] * inputs[0] * cos(theta)),
        inputs[0] - v0,
        inputs[2] - v2,
    ]

    templ.block.external_mapping = {
        VarPowerFlowReferenceType.Vaf: inputs[1],
        VarPowerFlowReferenceType.Vat: inputs[3],
        VarPowerFlowReferenceType.Vmf: inputs[0],
        VarPowerFlowReferenceType.Vmt: inputs[2],
        VarPowerFlowReferenceType.Pf: Pf,
        VarPowerFlowReferenceType.Pt: Pt,
        VarPowerFlowReferenceType.Qf: Qf,
        VarPowerFlowReferenceType.Qt: Qt,
    }

    templ.block.init_eqs = {
        v0: inputs[0],
        v2: inputs[2],
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.g: g,
        ParamPowerFlowReferenceType.b: b,
        ParamPowerFlowReferenceType.bsh: bsh,
           }

    templ.block.in_vars = inputs

    templ.comment = 'AC line RMS multilinear model'
    return templ