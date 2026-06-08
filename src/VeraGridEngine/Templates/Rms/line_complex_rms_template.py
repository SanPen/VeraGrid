# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List
import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowReferenceType, VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def get_line_complex_rms_template(vfactory: VarFactory, name="Line_complex_rms_template") -> RmsModelTemplate:
    """
    Get the complex phasor-based RMS template model of the Line with TRULY MULTILINEAR equations.
    
    This template uses complex phasor representation where:
    - V = Vr + j*Vi is the complex voltage
    - I = Y * (Vf - Vt) is the complex current (LINEAR in V!)
    - Y = g + j*b is the complex admittance
    
    The key innovation is that current equations are LINEAR in voltage variables:
    I = (g + j*b) * ((Vrf + j*Vif) - (Vrt + j*Vit))
    
    When expanded:
    Ir = g*(Vrf - Vrt) - b*(Vif - Vit)  [Linear!]
    Ii = g*(Vif - Vit) + b*(Vrf - Vrt)  [Linear!]
    
    This is truly multilinear because there are no products of voltage variables,
    unlike power equations S = V * conj(I) which are bilinear.
    
    The current balance at each node: ΣI = 0 is linear in all voltage variables.
    
    :param vfactory: Variable factory for creating variables
    :param name: Name of the template
    :return: RmsModelTemplate with complex multilinear line equations
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LineDevice
    templ.name = name

    # Inputs: complex voltages at from and to buses
    # We use separate real/imaginary inputs for compilation,
    # but conceptually they form complex voltages Vf and Vt
    inputs: List[Var] = [vfactory.add_var("Vrf_" + name),   # From bus real
                         vfactory.add_var("Vif_" + name),   # From bus imag
                         vfactory.add_var("Vrt_" + name),   # To bus real
                         vfactory.add_var("Vit_" + name)]   # To bus imag

    # Complex current outputs (from and to buses)
    # These are calculated using LINEAR equations
    If_complex = vfactory.add_var("If_complex")  # Complex current at from bus
    It_complex = vfactory.add_var("It_complex")  # Complex current at to bus
    
    # Real/imaginary components of current (for compilation)
    Ir_f = vfactory.add_var("Ir_f")  # Real current from
    Ii_f = vfactory.add_var("Ii_f")  # Imag current from
    Ir_t = vfactory.add_var("Ir_t")  # Real current to
    Ii_t = vfactory.add_var("Ii_t")  # Imag current to

    # Power outputs (derived from complex current and voltage)
    Pf = vfactory.add_var("Pf")
    Qf = vfactory.add_var("Qf")
    Pt = vfactory.add_var("Pt")
    Qt = vfactory.add_var("Qt")

    # Parameters: line admittance Y = g + j*b
    g = vfactory.add_var("g")    # Conductance (real part of Y)
    b = vfactory.add_var("b")    # Susceptance (imag part of Y)
    bsh = vfactory.add_var("bsh")  # Shunt susceptance

    # Set default parameter values
    templ.block.parameters[g] = vfactory.add_const(5)
    templ.block.parameters[b] = vfactory.add_const(-12)
    templ.block.parameters[bsh] = vfactory.add_const(0.03)

    # Algebraic variables include currents and powers
    templ.block.algebraic_vars = [Ir_f, Ii_f, Ir_t, Ii_t, Pf, Pt, Qf, Qt]

    # Voltage variables (inputs)
    Vrf = inputs[0]
    Vif = inputs[1]
    Vrt = inputs[2]
    Vit = inputs[3]
    
    # ============================================================================
    # MULTILINEAR CURRENT EQUATIONS
    # ============================================================================
    # Complex current: I = Y * (Vf - Vt) where Y = g + j*b
    # 
    # Expanding: I = (g + j*b) * ((Vrf + j*Vif) - (Vrt + j*Vit))
    #           I = (g + j*b) * ((Vrf - Vrt) + j*(Vif - Vit))
    #
    # Real part: Ir = g*(Vrf - Vrt) - b*(Vif - Vit)
    # Imag part: Ii = g*(Vif - Vit) + b*(Vrf - Vrt)
    #
    # These are TRULY LINEAR in voltage variables! No products, no squares!
    # ============================================================================
    
    # Current at from bus: If = Y * (Vf - Vt) + j*(bsh/2)*Vf
    # (includes half shunt at from bus)
    Ir_f_eq = g * (Vrf - Vrt) - b * (Vif - Vit) - (bsh / 2) * Vif
    Ii_f_eq = g * (Vif - Vit) + b * (Vrf - Vrt) + (bsh / 2) * Vrf
    
    # Current at to bus: It = Y * (Vt - Vf) + j*(bsh/2)*Vt
    # (includes half shunt at to bus)
    Ir_t_eq = g * (Vrt - Vrf) - b * (Vit - Vif) - (bsh / 2) * Vit
    Ii_t_eq = g * (Vit - Vif) + b * (Vrt - Vrf) + (bsh / 2) * Vrt

    # ============================================================================
    # POWER EQUATIONS (derived from complex quantities)
    # ============================================================================
    # S = V * conj(I) = (Vr + j*Vi)*(Ir - j*Ii)
    # P = Vr*Ir + Vi*Ii
    # Q = Vi*Ir - Vr*Ii
    #
    # Note: These are bilinear (products of V and I), but since I is linear in V,
    # these become quadratic in V. However, we keep them for power balance.
    # For truly linear equations, use current balance instead!
    # ============================================================================
    
    Pf_eq = Vrf * Ir_f + Vif * Ii_f
    Qf_eq = Vif * Ir_f - Vrf * Ii_f
    Pt_eq = Vrt * Ir_t + Vit * Ii_t
    Qt_eq = Vit * Ir_t - Vrt * Ii_t

    # Algebraic equations: currents calculated from voltages
    templ.block.algebraic_eqs = [
        # Current equations (LINEAR!)
        Ir_f - Ir_f_eq,
        Ii_f - Ii_f_eq,
        Ir_t - Ir_t_eq,
        Ii_t - Ii_t_eq,
        # Power equations (derived)
        Pf - Pf_eq,
        Qf - Qf_eq,
        Pt - Pt_eq,
        Qt - Qt_eq,
    ]

    # External mapping for reference
    templ.block.external_mapping = {
        # Complex phasor mapping
        VarPowerFlowReferenceType.Vf_complex: If_complex,  # Complex current from
        VarPowerFlowReferenceType.Vt_complex: It_complex,  # Complex current to
        VarPowerFlowReferenceType.Sf_complex: Pf,  # Will be combined with Qf
        VarPowerFlowReferenceType.St_complex: Pt,  # Will be combined with Qt
        # Real/imaginary component mapping
        VarPowerFlowReferenceType.Vrf: inputs[0],
        VarPowerFlowReferenceType.Vif: inputs[1],
        VarPowerFlowReferenceType.Vrt: inputs[2],
        VarPowerFlowReferenceType.Vit: inputs[3],
        VarPowerFlowReferenceType.Pf: Pf,
        VarPowerFlowReferenceType.Pt: Pt,
        VarPowerFlowReferenceType.Qf: Qf,
        VarPowerFlowReferenceType.Qt: Qt,
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.g: g,
        ParamPowerFlowReferenceType.b: b,
        ParamPowerFlowReferenceType.bsh: bsh,
    }

    templ.block.in_vars = inputs

    return templ


def get_line_complex_current_equations(Vrf: Var, Vif: Var, Vrt: Var, Vit: Var, 
                                       g: Var, b: Var, bsh: Var) -> tuple:
    """
    Calculate complex current using MULTILINEAR equations.
    
    This is the core innovation: current is linear in voltage!
    
    :param Vrf: From bus voltage real part
    :param Vif: From bus voltage imaginary part
    :param Vrt: To bus voltage real part
    :param Vit: To bus voltage imaginary part
    :param g: Line conductance
    :param b: Line susceptance
    :param bsh: Shunt susceptance
    :return: Tuple of (Ir_f, Ii_f, Ir_t, Ii_t) current components
    """
    # From bus current: If = Y*(Vf-Vt) + j*(bsh/2)*Vf
    Ir_f = g * (Vrf - Vrt) - b * (Vif - Vit) - (bsh / 2) * Vif
    Ii_f = g * (Vif - Vit) + b * (Vrf - Vrt) + (bsh / 2) * Vrf
    
    # To bus current: It = Y*(Vt-Vf) + j*(bsh/2)*Vt
    Ir_t = g * (Vrt - Vrf) - b * (Vit - Vif) - (bsh / 2) * Vit
    Ii_t = g * (Vit - Vif) + b * (Vrt - Vrf) + (bsh / 2) * Vrt
    
    return Ir_f, Ii_f, Ir_t, Ii_t


def calculate_complex_power(Vr: Var, Vi: Var, Ir: Var, Ii: Var) -> tuple:
    """
    Calculate complex power from voltage and current.
    
    S = V * conj(I) = (Vr + j*Vi)*(Ir - j*Ii)
    P = Vr*Ir + Vi*Ii
    Q = Vi*Ir - Vr*Ii
    
    :param Vr: Voltage real part
    :param Vi: Voltage imaginary part
    :param Ir: Current real part
    :param Ii: Current imaginary part
    :return: Tuple of (P, Q)
    """
    P = Vr * Ir + Vi * Ii
    Q = Vi * Ir - Vr * Ii
    return P, Q
