# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple

from typing import TYPE_CHECKING
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType

if TYPE_CHECKING:
    from VeraGridEngine.Devices.Substation.bus import Bus


class BusPhasorRmsTemplate(RmsModelTemplate):
    """
    Phasor-based RMS template for buses using real and imaginary voltage components.
    
    This template represents bus voltage as V = Vr + j*Vi instead of polar coordinates (Vm, Va).
    This representation makes line equations linear in the voltage variables.
    """
    __slots__ = (
        "tpe",
        "_block",
        "Vr",
        "Vi",
    )

    def __init__(self, vf: VarFactory, is_dc:bool=False, name: str = "rms_bus_phasor_template"):
        """
        Creates the Phasor-based RMS Template of a Bus
        :param vf: VarFactory
        :param is_dc: Whether this is a DC bus
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
            # Use phasor representation: V = Vr + j*Vi
            self.Vr = vf.add_var("Vr", VarPowerFlowRefferenceType.Vr)
            self.Vi = vf.add_var("Vi", VarPowerFlowRefferenceType.Vi)

            self._block = Block(
                algebraic_vars=[self.Vr, self.Vi],
                out_vars=[self.Vr, self.Vi]
            )
    
            self._block.external_mapping = {
                VarPowerFlowRefferenceType.Vr: self.Vr,
                VarPowerFlowRefferenceType.Vi: self.Vi
            }


def initialize_bus_phasor_rms(bus: Bus, vf: VarFactory):
    """
    Initialize the phasor-based RMS model for a bus.
    
    :param bus: Bus device
    :param vf: VarFactory for creating variables
    :return: None
    """
    bus.rms_model = BusPhasorRmsTemplate(vf=vf, is_dc=bus.is_dc).block

def get_bus_phasor_rms_algebraic_vars(bus_rms_model: Block) -> Tuple[Var, Var]:
    """
    Get the algebraic variables (Vr, Vi) from the phasor bus model.
    
    :param bus_rms_model: The block containing the bus model
    :return: Tuple of (Vr, Vi) RMS variables
    """
    return bus_rms_model.algebraic_vars[0], bus_rms_model.algebraic_vars[1]

def check_empty_bus(bus_rms_model: Block):
    """Check if the bus model has no algebraic variables."""
    return len(bus_rms_model.algebraic_vars) == 0

def polar_to_phasor(Vm: float, Va: float) -> Tuple[float, float]:
    """
    Convert polar coordinates (magnitude, angle) to phasor (real, imaginary).
    
    :param Vm: Voltage magnitude in p.u.
    :param Va: Voltage angle in radians
    :return: Tuple of (Vr, Vi)
    """
    import numpy as np
    Vr = Vm * np.cos(Va)
    Vi = Vm * np.sin(Va)
    return Vr, Vi

def phasor_to_polar(Vr: float, Vi: float) -> Tuple[float, float]:
    """
    Convert phasor (real, imaginary) to polar coordinates (magnitude, angle).
    
    :param Vr: Real part of voltage in p.u.
    :param Vi: Imaginary part of voltage in p.u.
    :return: Tuple of (Vm, Va)
    """
    import numpy as np
    Vm = np.sqrt(Vr**2 + Vi**2)
    Va = np.arctan2(Vi, Vr)
    return Vm, Va
