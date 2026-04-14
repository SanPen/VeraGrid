# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from typing import List

from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block, Var, Const, Expr,VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import cos, sin, real, imag, conj, angle, exp, log, abs, UndefinedConst


class BusRmsTemplate(RmsModelTemplate):

    def __init__(self, name: str = "rms_bus_template"):
        super().__init__(name=name)

        self.tpe: DeviceType = DeviceType.BusDevice


        self.Vm = Var("Vm")
        self.Va = Var("Va")
        self.P = Var("P")
        self.Q = Var("Q")

        self.block = Block(
            algebraic_vars=[self.Vm, self.Va, self.P, self.Q])

        self._block.external_mapping={
                VarPowerFlowRefferenceType.Vm: self.Vm,
                VarPowerFlowRefferenceType.Va: self.Va,
                VarPowerFlowRefferenceType.P: self.P,
                VarPowerFlowRefferenceType.Q: self.Q
            }
