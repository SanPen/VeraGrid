# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple, Optional

from typing import TYPE_CHECKING
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var

if TYPE_CHECKING:
    from VeraGridEngine.Devices.Substation.bus import Bus


class BusRmsTemplate(RmsModelTemplate):
    __slots__ = (
        "tpe",
        "_block",
        "Vm",
        "Va",
    )

    def __init__(self, vf: VarFactory, is_dc:bool=False, name: str = "rms_bus_template"):
        """
        Created the RMS Template of a Bus
        :param vf: VarFactory
        :param name: Name of the RMS Model
        """
        super().__init__(name=name)

        self.tpe: DeviceType = DeviceType.BusDevice
        if is_dc:
            Vdc = vf.add_var("Vdc")
            P = vf.add_var("P")
            Q = vf.add_var("Q")

            self._block = Block(
                algebraic_vars=[Vdc],
                out_vars = [Vdc])

            self._block.external_mapping = {
                VarPowerFlowRefferenceType.Vdc: Vdc,
                VarPowerFlowRefferenceType.P: P,
                VarPowerFlowRefferenceType.Q: Q
            }

        else:
            self.Vm = vf.add_var("Vm", VarPowerFlowRefferenceType.Vm)
            self.Va = vf.add_var("Va", VarPowerFlowRefferenceType.Va)


            self._block = Block(
                algebraic_vars=[self.Vm, self.Va],
                out_vars=[self.Vm, self.Va]
            )
    
            self._block.external_mapping = {
                VarPowerFlowRefferenceType.Vm: self.Vm,
                VarPowerFlowRefferenceType.Va: self.Va,
            }


def initialize_bus_rms(bus: Bus, vf: VarFactory):
    """

    :param bus:
    :param vf:
    :return:
    """
    bus.rms_model = BusRmsTemplate(vf=vf, is_dc=bus.is_dc).block



def get_bus_rms_algebraic_vars(bus_rms_model: Block) -> Tuple[Var, Var] | Var:
    """
    Return the RMS bus algebraic voltage variables.

    For AC buses:
        returns (Vm, Va)

    For DC buses:
        returns (Vdc, None)

    :param bus_rms_model: RMS bus block
    :return: Tuple with two positions to preserve the project API
    """
    mapping = bus_rms_model.external_mapping
    if VarPowerFlowRefferenceType.Vdc in mapping:
        vdc = mapping[VarPowerFlowRefferenceType.Vdc]
        if vdc is not None:
            return vdc
        else:
            raise ValueError("Invalid RMS bus model: expected either (Vdc) or (Vm, Va)")

    else:
        Vm = mapping[VarPowerFlowRefferenceType.Vm]
        Va = mapping[VarPowerFlowRefferenceType.Va]

        if Vm is not None and Va is not None:
            return Vm, Va

        else:
            raise ValueError("Invalid RMS bus model: expected either (Vdc) or (Vm, Va)")

