# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple, TYPE_CHECKING
import numpy as np

from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var

if TYPE_CHECKING:
    from VeraGridEngine.Devices.Substation.bus import Bus


class BusComplexRmsTemplate(RmsModelTemplate):
    """
    Complex phasor-based RMS template for buses using a single complex voltage variable.
    
    This template represents bus voltage as a single complex variable V = Vr + j*Vi
    instead of separate real and imaginary components. The complex representation
    enables truly multilinear current equations in the network.
    
    For compilation purposes, the complex variable is split into real and imaginary
    parts, but symbolically it remains a single complex entity.
    """
    __slots__ = (
        "tpe",
        "_block",
        "V_complex",
        "Vr",
        "Vi",
        "P",
        "Q",
        "I_complex",
        "Ir",
        "Ii",
    )

    def __init__(self, vf: VarFactory, is_dc: bool = False, name: str = "rms_bus_complex_template"):
        """
        Creates the Complex Phasor-based RMS Template of a Bus
        
        :param vf: VarFactory for creating symbolic variables
        :param is_dc: Whether this is a DC bus
        :param name: Name of the RMS Model
        """
        super().__init__(name=name)

        self.tpe: DeviceType = DeviceType.BusDevice
        
        if is_dc:
            # DC buses use real voltage only
            Vdc = vf.add_var("Vdc")
            P = vf.add_var("P")
            Q = vf.add_var("Q")

            self._block = Block(
                algebraic_vars=[Vdc],
                out_vars=[Vdc]
            )

            self._block.external_mapping = {
                VarPowerFlowRefferenceType.Vdc: Vdc,
                VarPowerFlowRefferenceType.P: P,
                VarPowerFlowRefferenceType.Q: Q
            }
        else:
            # AC buses use complex voltage representation
            # We create a single complex variable
            self.V_complex = vf.add_var("V_complex")  # Complex voltage V = Vr + j*Vi
            
            # For practical purposes, we also create real/imaginary components
            # These are derived from the complex variable but used for compilation
            self.Vr = vf.add_var("Vr")
            self.Vi = vf.add_var("Vi")
            
            # Power injections
            self.P = vf.add_var("P")
            self.Q = vf.add_var("Q")
            
            # Complex current injection (for current balance equations)
            self.I_complex = vf.add_var("I_complex")
            self.Ir = vf.add_var("Ir")
            self.Ii = vf.add_var("Ii")

            # Algebraic variables are the real/imaginary components of voltage
            # (the complex variable is symbolic, compiled to real parts)
            self._block = Block(
                algebraic_vars=[self.Vr, self.Vi],
                out_vars=[self.Vr, self.Vi]
            )
    
            self._block.external_mapping = {
                # Complex phasor mapping
                VarPowerFlowRefferenceType.V_complex: self.V_complex,
                VarPowerFlowRefferenceType.I_complex: self.I_complex,
                # Real/imaginary component mapping (for compatibility)
                VarPowerFlowRefferenceType.Vr: self.Vr,
                VarPowerFlowRefferenceType.Vi: self.Vi,
                VarPowerFlowRefferenceType.P: self.P,
                VarPowerFlowRefferenceType.Q: self.Q
            }


def initialize_bus_complex_rms(bus: Bus, vf: VarFactory):
    """
    Initialize the complex phasor-based RMS model for a bus.
    
    :param bus: Bus device
    :param vf: VarFactory for creating variables
    :return: None
    """
    bus.rms_model = BusComplexRmsTemplate(vf=vf, is_dc=bus.is_dc).block


def get_bus_complex_rms_algebraic_vars(bus_rms_model: Block) -> Tuple[Var, Var]:
    """
    Get the algebraic variables (Vr, Vi) from the complex bus model.
    
    :param bus_rms_model: The block containing the bus model
    :return: Tuple of (Vr, Vi) RMS variables
    """
    return bus_rms_model.algebraic_vars[0], bus_rms_model.algebraic_vars[1]


def get_bus_complex_voltage(bus_rms_model: Block) -> Var:
    """
    Get the complex voltage variable from the bus model.
    
    :param bus_rms_model: The block containing the bus model
    :return: Complex voltage variable
    """
    return bus_rms_model.external_mapping[VarPowerFlowRefferenceType.V_complex]


def polar_to_complex(Vm: float, Va: float) -> complex:
    """
    Convert polar coordinates (magnitude, angle) to complex phasor.
    
    :param Vm: Voltage magnitude in p.u.
    :param Va: Voltage angle in radians
    :return: Complex voltage V = Vm * exp(j*Va)
    """
    return complex(Vm * np.cos(Va), Vm * np.sin(Va))


def complex_to_polar(V: complex) -> Tuple[float, float]:
    """
    Convert complex phasor to polar coordinates (magnitude, angle).
    
    :param V: Complex voltage in p.u.
    :return: Tuple of (Vm, Va) where Va is in radians
    """
    Vm = np.abs(V)
    Va = np.angle(V)
    return Vm, Va


def complex_to_real_imag(V: complex) -> Tuple[float, float]:
    """
    Convert complex phasor to real and imaginary components.
    
    :param V: Complex voltage V = Vr + j*Vi
    :return: Tuple of (Vr, Vi)
    """
    return V.real, V.imag


def real_imag_to_complex(Vr: float, Vi: float) -> complex:
    """
    Convert real and imaginary components to complex phasor.
    
    :param Vr: Real part of voltage
    :param Vi: Imaginary part of voltage
    :return: Complex voltage V = Vr + j*Vi
    """
    return complex(Vr, Vi)
