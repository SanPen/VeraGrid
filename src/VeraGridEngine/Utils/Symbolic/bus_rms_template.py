# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple, Optional

from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var

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
                VarPowerFlowReferenceType.Vdc: Vdc,
                VarPowerFlowReferenceType.P: P,
                VarPowerFlowReferenceType.Q: Q
            }

        else:
            self.Vm = vf.add_var("Vm", reference=VarPowerFlowReferenceType.Vm)
            self.Va = vf.add_var("Va", reference=VarPowerFlowReferenceType.Va)


            self._block = Block(
                algebraic_vars=[self.Vm, self.Va],
                out_vars=[self.Vm, self.Va]
            )
    
            self._block.external_mapping = {
                VarPowerFlowReferenceType.Vm: self.Vm,
                VarPowerFlowReferenceType.Va: self.Va,
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
    if VarPowerFlowReferenceType.Vdc in mapping:
        vdc = mapping[VarPowerFlowReferenceType.Vdc]
        if vdc is not None:
            return vdc, None
        else:
            raise ValueError("Invalid RMS bus model: expected either (Vdc) or (Vm, Va)")

    else:
        Vm = mapping[VarPowerFlowReferenceType.Vm]
        Va = mapping[VarPowerFlowReferenceType.Va]

        if Vm is not None and Va is not None:
            return Vm, Va

        else:
            raise ValueError("Invalid RMS bus model: expected either (Vdc) or (Vm, Va)")
