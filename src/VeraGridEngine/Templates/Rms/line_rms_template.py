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
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def get_line_rms_template(vfactory: VarFactory, name="Line_rms_template") -> RmsModelTemplate:
    """
    Get the RMS template model of the Line
    :return: RmsModelTemplate
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LineDevice
    templ.name = name

    inputs: List[Var] = [vfactory.add_var("Vmf", reference=VarPowerFlowReferenceType.Vmf),
                         vfactory.add_var("Vaf", reference=VarPowerFlowReferenceType.Vaf),
                         vfactory.add_var("Vmt", reference=VarPowerFlowReferenceType.Vmt),
                         vfactory.add_var("Vat", reference=VarPowerFlowReferenceType.Vat), ]

    Qf = vfactory.add_var("Qf", reference=VarPowerFlowReferenceType.Qf)
    Qt = vfactory.add_var("Qt", reference=VarPowerFlowReferenceType.Qt)
    Pf = vfactory.add_var("Pf", reference=VarPowerFlowReferenceType.Pf)
    Pt = vfactory.add_var("Pt", reference=VarPowerFlowReferenceType.Pt)

    g = vfactory.add_var("g")
    b = vfactory.add_var("b")
    bsh = vfactory.add_var("bsh")

    u = vfactory.add_var("u")

    block = Block()

    block.parameters[g] = vfactory.add_const(5)
    block.parameters[b] = vfactory.add_const(-12)
    block.parameters[bsh] = vfactory.add_const(0.03)

    block.event_dict[u] = vfactory.add_const(1)

    block.algebraic_vars = [Pf, Pt, Qf, Qt]


    pi2 = np.pi / 2
    block.algebraic_eqs = [
        u * (Pf - ((inputs[0] ** 2 * g) - g * inputs[0] * inputs[2] * cos(inputs[1] - inputs[3]) + b * inputs[0] * inputs[2] * cos(inputs[1] - inputs[3] + pi2))),
        u * (Qf - (inputs[0] ** 2 * (-bsh / 2 - b) - g * inputs[0] * inputs[2] * sin(inputs[1] - inputs[3]) + b * inputs[0] * inputs[2] * sin(inputs[1] - inputs[3] + pi2))),
        u * (Pt - ((inputs[2] ** 2 * g) - g * inputs[2] * inputs[0] * cos(inputs[3] - inputs[1]) + b * inputs[2] * inputs[0] * cos(inputs[3] - inputs[1] + pi2))),
        u * (Qt - (inputs[2] ** 2 * (-bsh / 2 - b) - g * inputs[2] * inputs[0] * sin(inputs[3] - inputs[1]) + b * inputs[2] * inputs[0] * sin(inputs[3] - inputs[1] + pi2))),
    ]

    block.in_vars = inputs
    block.out_vars = [Pf, Pt, Qf, Qt]

    block.name = name

    templ.block.children.append(block)

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

    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.g: g,
        ParamPowerFlowReferenceType.b: b,
        ParamPowerFlowReferenceType.bsh: bsh,
           }

    templ.block.in_vars = inputs
    templ.block.out_vars = [Pf, Pt, Qf, Qt]



    return templ


def get_dc_line_rms_template(vfactory: VarFactory, name="DC_Line_rms_template") -> RmsModelTemplate:
    """
    Get the RMS template model of a DC line with series R-L dynamics.
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.DCLineDevice
    templ.name = name

    Vdcf = vfactory.add_var("Vdcf", reference=VarPowerFlowReferenceType.Vmf)
    Vdct = vfactory.add_var("Vdct", reference=VarPowerFlowReferenceType.Vmt)
    inputs: List[Var] = [Vdcf, Vdct]

    If_dc = vfactory.add_var("If_dc")
    Pf = vfactory.add_var("Pf")
    Pt = vfactory.add_var("Pt")
    dIf_dcdt = vfactory.add_diff_var("dIf_dcdt", base_var=If_dc)

    r = vfactory.add_var("r")
    l = vfactory.add_var("l")

    block = Block()

    block.parameters[r] = vfactory.add_const(0.01)
    block.parameters[l] = vfactory.add_const(0.05)

    block.algebraic_vars = [If_dc, Pf, Pt]
    block.diff_vars = [dIf_dcdt]

    block.algebraic_eqs = [
        l * dIf_dcdt + r * If_dc - (Vdcf - Vdct),
        Pf - Vdcf * If_dc,
        Pt + Vdct * If_dc,
    ]
    block.init_eqs = {
        If_dc: (Vdcf - Vdct) / r,
        Pf: Vdcf * If_dc,
        Pt: -Vdct * If_dc,
    }
    block.diff_init_eqs = {
        dIf_dcdt: sym.Const(0.0),
    }

    block.in_vars = inputs
    block.name = name

    templ.block.external_mapping = {
        VarPowerFlowReferenceType.Vmf: Vdcf,
        VarPowerFlowReferenceType.Vmt: Vdct,
        VarPowerFlowReferenceType.If_dc: If_dc,
        VarPowerFlowReferenceType.Pf: Pf,
        VarPowerFlowReferenceType.Pt: Pt,
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.r: r,
        #ParamPowerFlowReferenceType.l: l,
    }

    templ.block.in_vars = inputs

    return templ
