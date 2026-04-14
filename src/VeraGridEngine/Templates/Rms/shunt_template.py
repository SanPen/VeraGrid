# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import math
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block


def ShuntLoadBuild(vfactory: VarFactory, name: str = "") -> RmsModelTemplate:
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.ShuntDevice
    res_block = Block()
    pi = math.pi
    # Inputs:
    inputs = [vfactory.add_var('Vm'), vfactory.add_var('Va')]
    Vm = inputs[0]
    Va = inputs[1]
    # Variables:
    P = vfactory.add_var('P')
    Q = vfactory.add_var('Q')
    g = vfactory.add_var('g')
    b = vfactory.add_var('b')

    events_dict = {
        g: vfactory.add_const(0.0),
        b: vfactory.add_const(0.4),
    }

    res_block = Block(
        algebraic_eqs=[
            P + g * Vm ** 2,
            Q - b * Vm ** 2,
        ],
        algebraic_vars=[P, Q],
        init_eqs={
            P: vfactory.add_const(0.0),
            Q: vfactory.add_const(0.1),
        }
    )

    res_block.event_dict = events_dict
    res_block.external_mapping = {
        VarPowerFlowRefferenceType.Vm: inputs[0],
        VarPowerFlowRefferenceType.Va: inputs[1],
        VarPowerFlowRefferenceType.P: P,
        VarPowerFlowRefferenceType.Q: Q,
    }
    res_block.in_vars = inputs

    templ.block = res_block
    return templ
