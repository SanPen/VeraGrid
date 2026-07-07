# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import math

from VeraGridEngine.Templates.templates_common_functions import tf_to_block
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Branches.hvdc_line import HvdcLine
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import sin, cos, sqrt
from VeraGridEngine.enumerations import HvdcControlType
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit

class HvdcRmsTemplate(RmsModelTemplate):
    """
    RMS Template for HVDC Line with fixed power setpoint control.
    """
    __slots__ = (
        "tpe",
        "_block",
    )

    def __init__(self, nc: NumericalCircuit, hvdc: HvdcLine, hvdc_idx: int, vf: VarFactory, name: str = "hvdc_rms_template"):
        """
        Create the RMS Template of an HVDC Line
        
        :param nc: NumericalCircuit with compiled data
        :param hvdc: HVDC Line device
        :param hvdc_idx: Index of the HVDC in nc.hvdc_data
        :param vf: VarFactory for creating symbolic variables
        :param name: Name of the RMS Model
        """
        super().__init__(name=name)
        
        self.tpe: DeviceType = DeviceType.HVDCLineDevice 

        if hvdc.rms_model.empty():
            # Create algebraic variables for power flow
            Pf = vf.add_var("Pf")
            Pt = vf.add_var("Pt")
            Qf = vf.add_var("Qf")
            Qt = vf.add_var("Qt")
            
            # Get voltage magnitude references from connected buses
            # These are symbolic variables linked to bus voltages via .E()
            Vmf = vf.add_var(f"Vmf_{hvdc.name}")
            Vaf = vf.add_var(f"Vaf_{hvdc.name}")
            Vmt = vf.add_var(f"Vmt_{hvdc.name}")
            Vat = vf.add_var(f"Vat_{hvdc.name}")    
            
            #Parameters
            Ti = vf.add_var('Ti')  # Time constant for control dynamics
            Tr = vf.add_var('Tr')  # Time constant for control dynamics
            Ki = vf.add_var('Ki')  # Time constant for control dynamics
            Kp = vf.add_var('Kp')  # Time constant for control dynamics
            vdc_ref = vf.add_var('vdc_ref')  # Time constant for control dynamics
            vac_ref = vf.add_var('vac_ref')  # Time constant for control dynamics
            gamma_ref = vf.add_var('gamma_ref')  # Time constant for control dynamics

            #We initialize parameters
            parameters={
                vac_ref: vf.add_const(hvdc.Vset_f),
                vdc_ref: vf.add_const(hvdc.dc_link_voltage),
                gamma_ref: vf.add_const(1.0),
                Ti: vf.add_const(0.01),    # Time constant for DC voltage control (s)
                Tr: vf.add_const(0.01),    # Time constant for AC voltage control (s)
                Ki: vf.add_const(0.1),     # Integral gain for PI controller
                Kp: vf.add_const(1.0),     # Proportional gain for PI controller
            }
            #Internal HVDC states
            pi = math.pi
            phi_f = vf.add_var(f"phi_h_{hvdc.name}")  #Phase for reactive power control
            alpha = vf.add_var(f"alpha_{hvdc.name}")  # Firing angle for reactive power control
            gamma = vf.add_var(f"gamma_{hvdc.name}")  # Firing angle for reactive power control
            phi_t = vf.add_var(f"phi_t_{hvdc.name}")  #Phase for reactive power control
            ir_dc = vf.add_var(f"ir_dc_{hvdc.name}")  # DC current variable
            k = vf.add_const(0.9995*3/pi)*sqrt(2)
            K_droop = vf.add_const(0.05)  # Droop gain for frequency control
            
            x_r = vf.add_var(f"m_f_{hvdc.name}")  # Tap for from side (rectifier control)
            x_i = vf.add_var(f"m_t_{hvdc.name}")  # Tap for to side (inverter control)
            ii_dc = ir_dc
            m_f = x_r  
            m_t = x_i 

            r = vf.add_const(nc.hvdc_data.r[hvdc_idx])  
            vr_dc = k*m_f*Vmf*cos(phi_f)
            vi_dc = k*m_t*Vmt*cos(phi_t)
            P_loss = r*(Pf/Vmf)**2

            block = Block(
                algebraic_vars=[Pf, Pt, Qf, Qt, gamma, phi_f, phi_t, ir_dc],
                algebraic_eqs=[
                    Pf - (-vr_dc*ir_dc),
                    Qf - (-k*m_f*Vmf*ir_dc*sin(phi_f)),
                    k*m_f*Vmt*(cos(alpha) - cos(phi_f)) - vf.add_const(3/pi)*x_r*ir_dc,
                    Pt - (-vi_dc*ii_dc),
                    Qt - (k*m_t*Vmt*ii_dc*sin(phi_t)),
                    k*m_t*Vmt*(cos(pi-gamma) + cos(phi_t)) - vf.add_const(3/pi)*x_i*ii_dc,
                    gamma - gamma_ref,
                    Pf + P_loss - Pt,

                ],
                parameters=parameters,
                init_eqs={
                    phi_f: vf.add_const(pi/2),  # Initial phase for reactive power control
                    phi_t: vf.add_const(pi/2),  # Initial phase for reactive power control
                    alpha: vf.add_const(pi/2),  # Initial firing angle
                    gamma: vf.add_const(pi/2),  # Initial firing angle
                    ir_dc: vf.add_const(hvdc.Pset/hvdc.dc_link_voltage),  # Initial DC current based on power setpoint and voltage
                    gamma_ref: vf.add_const(1)  # Initial reference for gamma (can be adjusted based on control mode)
                },
                in_vars=[Vmf, Vaf, Vmt, Vat],
            )

            if hvdc.control_mode == HvdcControlType.type_0_free:
                Pdc_ref = hvdc.Pset/nc.Sbase + K_droop*(Vaf - Vat)
            elif hvdc.control_mode == HvdcControlType.type_1_Pset:
                Pdc_ref = hvdc.Pset/nc.Sbase
            else:
                # Default to Pset mode
                Pdc_ref = hvdc.Pset/nc.Sbase
            idc_ref = Pdc_ref/vdc_ref

            control_block = Block(
                state_vars=[x_i, x_r],
                state_eqs=[
                    (vdc_ref - vi_dc)/Ti,      # dx_i/dt: DC voltage control (inverter side)
                    (Vmf - vac_ref)/Tr,        # dx_r/dt: AC voltage control (rectifier side)
                ]
            )
            PI_block, _ = tf_to_block(
                var_factory = vf,
                x = idc_ref - ir_dc,
                y = alpha,
                num=[Ki, Kp],
                den=[0, 1]
            )

            block.children.append(control_block)
            block.children.append(PI_block)

            # External mapping for power flow references
            block.external_mapping = {
                VarPowerFlowRefferenceType.Pf: Pf,
                VarPowerFlowRefferenceType.Pt: Pt,
                VarPowerFlowRefferenceType.Qf: Qf,
                VarPowerFlowRefferenceType.Qt: Qt,
            }
            block.unify_blocks()
            self._block = block


def initialize_hvdc_rms(hvdc: HvdcLine, hvdc_idx: int, vf: VarFactory, nc: NumericalCircuit):
    """
    Initialize the RMS model for an HVDC Line
    
    :param hvdc: HVDC Line device
    :param hvdc_idx: Index of the HVDC in nc.hvdc_data
    :param vf: VarFactory
    :param nc: NumericalCircuit with compiled data
    """
    hvdc.rms_model = HvdcRmsTemplate(nc, hvdc=hvdc, hvdc_idx=hvdc_idx, vf=vf).block
