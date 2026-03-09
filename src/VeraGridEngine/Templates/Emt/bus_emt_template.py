# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowRefferenceType

# depending on the number of phases of the bus a different model must be created.
class BusEmtTemplateNABC(EmtModelTemplate):

    def __init__(self,
                 vf: VarFactory,
                 mask: list[bool],
                 name: str = "emt_bus_template"):
        """
        Created the RMS Template of a Bus
        :param vf: VarFactory
        :param mask: list[bool] with true if the phase exist and false if it doesn't in the order [N,A,B,C]
        :param name: Name of the EMT Model
        """

        super().__init__(name=name)

        self.tpe: DeviceType = DeviceType.BusDevice

        self.v_N = vf.add_var("v_N"+name) if mask[0] else None
        self.v_A = vf.add_var("v_A"+name) if mask[1] else None
        self.v_B = vf.add_var("v_B"+name) if mask[2] else None
        self.v_C = vf.add_var("v_C"+name) if mask[3] else None
        self.d_v_N = vf.add_diff_var(name = f"d_v_N_{name}", base_var=self.v_N) if mask[0] else None
        self.d_v_A = vf.add_diff_var(name = f"d_v_A_{name}", base_var=self.v_A) if mask[1] else None
        self.d_v_B = vf.add_diff_var(name = f"d_v_B_{name}", base_var=self.v_B) if mask[2] else None
        self.d_v_C = vf.add_diff_var(name = f"d_v_C_{name}", base_var=self.v_C) if mask[3] else None

        v_list = [v for v in (self.v_N, self.v_A, self.v_B, self.v_C) if v is not None]
        if not v_list:
            raise ValueError("Bus has no enabled phases")

        d_v_list = [dv for dv in (self.d_v_N, self.d_v_A, self.d_v_B, self.d_v_C) if dv is not None]
        if not d_v_list:
            raise ValueError("Bus has no enabled phases")

        self._block = Block(
            state_vars=v_list,
            state_eqs = d_v_list,
            # algebraic_vars=v_list,
            diff_vars = d_v_list,
            out_vars=v_list + d_v_list
        )

        self._block.external_mapping = {
            VarPowerFlowRefferenceType.v_N: self.v_N,
            VarPowerFlowRefferenceType.v_A: self.v_A,
            VarPowerFlowRefferenceType.v_B: self.v_B,
            VarPowerFlowRefferenceType.v_C: self.v_C,
            VarPowerFlowRefferenceType.d_v_N: self.d_v_N,
            VarPowerFlowRefferenceType.d_v_A: self.d_v_A,
            VarPowerFlowRefferenceType.d_v_B: self.d_v_B,
            VarPowerFlowRefferenceType.d_v_C: self.d_v_C,
            VarPowerFlowRefferenceType.P: None,
            VarPowerFlowRefferenceType.Q: None
        }

    @property
    def block(self) -> Block:
        """
        block
        :return: Block
        """
        return self._block

def get_bus_emt_template(grid: MultiCircuit,
                         bus: Bus,
                         vf: VarFactory):
    """
    Initialize 3ph bus block
    A bus will have the phases of the branches connected to it
    :param grid: Multicircuit
    :param bus: Bus
    :param vf: VarFactory
    :return:
    """
    mask = [False,False,False,False] # [N, A, B, C]
    for branch in grid.get_branches_iter(add_vsc=True, add_switch= True, add_hvdc=True):
        if bus == branch.bus_from or bus == branch.bus_to:
            mask[0] |= bool(branch.ys.phN)
            mask[1] |= bool(branch.ys.phA)
            mask[2] |= bool(branch.ys.phB)
            mask[3] |= bool(branch.ys.phC)

    # choose template depending on the number of phases
    bus.emt_model.model = BusEmtTemplateNABC(vf=vf, mask = mask, name = f"{bus.name}_emt_template").block




