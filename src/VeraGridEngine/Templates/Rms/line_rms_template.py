# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Var, Const, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import cos, sin


def get_line_rms_template() -> RmsModelTemplate:
    """
    Get the RMS template model of the Line
    :return: RmsModelTemplate
    """
    templ = RmsModelTemplate()

    Vmf: Var = Var('Vmf')
    Vaf: Var = Var('Vaf')
    Vmt: Var = Var('Vmt')
    Vat: Var = Var('Vat')

    Qf = Var("Qf")
    Qt = Var("Qt")
    Pf = Var("Pf")
    Pt = Var("Pt")

    g = Var("g")
    b = Var("b")
    bsh = Var("bsh")

    templ.block.event_dict[g] = Const(0.0)
    templ.block.event_dict[b] = Const(0.0)
    templ.block.event_dict[bsh] = Const(0.0)

    templ.block.algebraic_vars = [Pf, Pt, Qf, Qt]

    pi2 = np.pi / 2

    templ.block.algebraic_eqs = [
        Pf - ((Vmf ** 2 * g) - g * Vmf * Vmt * cos(Vaf - Vat) + b * Vmf * Vmt * cos(Vaf - Vat + pi2)),
        Qf - (Vmf ** 2 * (-bsh / 2 - b) - g * Vmf * Vmt * sin(Vaf - Vat) + b * Vmf * Vmt * sin(Vaf - Vat + pi2)),
        Pt - ((Vmt ** 2 * g) - g * Vmt * Vmf * cos(Vat - Vaf) + b * Vmt * Vmf * cos(Vat - Vaf + pi2)),
        Qt - (Vmt ** 2 * (-bsh / 2 - b) - g * Vmt * Vmf * sin(Vat - Vaf) + b * Vmt * Vmf * sin(Vat - Vaf + pi2)),
    ]

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Pf: Pf,
        VarPowerFlowRefferenceType.Pt: Pt,
        VarPowerFlowRefferenceType.Qf: Qf,
        VarPowerFlowRefferenceType.Qt: Qt,
    }

    return templ
