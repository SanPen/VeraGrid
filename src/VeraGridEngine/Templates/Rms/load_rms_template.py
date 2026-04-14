# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block, Var, Const, VarPowerFlowRefferenceType


def LoadRmsTemplate(name: str = "rms_load_template") -> RmsModelTemplate:
    """

    :param name:
    :return:
    """
    templ = RmsModelTemplate()

    Pl0 = Var("Pl0")
    Ql0 = Var("Ql0")

    Ql = Var("Ql")
    Pl = Var("Pl")

    templ.block = Block(
        algebraic_vars=[Pl, Ql],
        algebraic_eqs=[
            Pl - Pl0,
            Ql - Ql0
        ],
        event_dict={Pl0: Const(-0.075000000001172),
                    Ql0: Const(-0.009999999862208533)},
        external_mapping={
            VarPowerFlowRefferenceType.P: Pl,
            VarPowerFlowRefferenceType.Q: Ql
        },
        name=name
    )

    return templ
