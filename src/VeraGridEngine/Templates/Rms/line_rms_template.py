# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List
import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.symbolic import Var, cos, sin
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def get_line_rms_template(vfactory: VarFactory, name="Line_rms_template") -> RmsModelTemplate:
    """
    Get the RMS template model of the Line
    :return: RmsModelTemplate
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LineDevice
    templ.name = name

    inputs: List[Var] = [vfactory.add_var("Vmf_" + name, VarPowerFlowRefferenceType.Vmf),
                         vfactory.add_var("Vaf_" + name, VarPowerFlowRefferenceType.Vaf),
                         vfactory.add_var("Vmt_" + name, VarPowerFlowRefferenceType.Vmt),
                         vfactory.add_var("Vat_" + name, VarPowerFlowRefferenceType.Vat),]

    Qf = vfactory.add_var("Qf")
    Qt = vfactory.add_var("Qt")
    Pf = vfactory.add_var("Pf")
    Pt = vfactory.add_var("Pt")

    g = vfactory.add_var("g")
    b = vfactory.add_var("b")
    bsh = vfactory.add_var("bsh")

    templ.block.parameters[g] = vfactory.add_const(5)
    templ.block.parameters[b] = vfactory.add_const(-12)
    templ.block.parameters[bsh] = vfactory.add_const(0.03)

    templ.block.algebraic_vars = [Pf, Pt, Qf, Qt]
    templ.block.out_vars = [Pf, Pt, Qf, Qt]

    pi2 = np.pi / 2
    templ.block.algebraic_eqs = [
        Pf - ((inputs[0] ** 2 * g) - g * inputs[0] * inputs[2] * cos(inputs[1] - inputs[3]) + b * inputs[0] * inputs[2] * cos(inputs[1] - inputs[3] + pi2)),
        Qf - (inputs[0] ** 2 * (-bsh / 2 - b) - g * inputs[0] * inputs[2] * sin(inputs[1] - inputs[3]) + b * inputs[0] * inputs[2] * sin(inputs[1] - inputs[3] + pi2)),
        Pt - ((inputs[2] ** 2 * g) - g * inputs[2] * inputs[0] * cos(inputs[3] - inputs[1]) + b * inputs[2] * inputs[0] * cos(inputs[3] - inputs[1] + pi2)),
        Qt - (inputs[2] ** 2 * (-bsh / 2 - b) - g * inputs[2] * inputs[0] * sin(inputs[3] - inputs[1]) + b * inputs[2] * inputs[0] * sin(inputs[3] - inputs[1] + pi2)),
    ]

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Vaf: inputs[1],
        VarPowerFlowRefferenceType.Vat: inputs[3],
        VarPowerFlowRefferenceType.Vmf: inputs[0],
        VarPowerFlowRefferenceType.Vmt: inputs[2],
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


def get_dc_line_rms_template(vfactory: VarFactory, name="DC_Line_rms_template") -> RmsModelTemplate:
    """
    Get the RMS template model of a DC line with series R-L dynamics.
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.DCLineDevice
    templ.name = name

    Vdcf = vfactory.add_var("Vdcf_" + name, VarPowerFlowRefferenceType.Vmf)
    Vdct = vfactory.add_var("Vdct_" + name, VarPowerFlowRefferenceType.Vmt)
    inputs: List[Var] = [Vdcf, Vdct]

    If_dc = vfactory.add_var("If_dc")
    Pf = vfactory.add_var("Pf")
    Pt = vfactory.add_var("Pt")
    dIf_dcdt = vfactory.add_diff_var("dIf_dcdt", base_var=If_dc)

    r = vfactory.add_var("r")
    l = vfactory.add_var("l")

    templ.block.parameters[r] = vfactory.add_const(0.01)
    templ.block.parameters[l] = vfactory.add_const(0.05)

    templ.block.algebraic_vars = [If_dc, Pf, Pt]
    templ.block.diff_vars = [dIf_dcdt]

    templ.block.algebraic_eqs = [
        l * dIf_dcdt + r * If_dc - (Vdcf - Vdct),
        Pf - Vdcf * If_dc,
        Pt + Vdct * If_dc,
    ]
    templ.block.init_eqs = {
        If_dc: (Vdcf - Vdct) / r,
        Pf: Vdcf * If_dc,
        Pt: -Vdct * If_dc,
    }
    templ.block.diff_init_eqs = {
        dIf_dcdt: sym.Const(0.0),
    }

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Vmf: Vdcf,
        VarPowerFlowRefferenceType.Vmt: Vdct,
        VarPowerFlowRefferenceType.If_dc: If_dc,
        VarPowerFlowRefferenceType.Pf: Pf,
        VarPowerFlowRefferenceType.Pt: Pt,
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.r: r,
        #ParamPowerFlowRefferenceType.l: l,
    }

    templ.block.in_vars = inputs

    return templ
