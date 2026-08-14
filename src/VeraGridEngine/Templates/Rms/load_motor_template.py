# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import math

from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import (Block, VarPowerFlowReferenceType)
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
import VeraGridEngine.Utils.Symbolic.symbolic as sym

"""
    Builds an RMS model template for an induction motor load.
    
    Implements a detailed induction motor model with transient and subtransient dynamics.
    The model includes:
    - Electrical dynamics: Transient and subtransient voltage equations (Ed', Eq', Ed'', Eq'')
    - Mechanical dynamics: Rotor speed (omega/slip) with inertia and load torque
    - Algebraic equations: Currents, voltages, and power calculations in dq-reference frame
    
    The motor is represented by its equivalent circuit parameters including stator resistance,
    leakage inductances, and magnetizing inductance. The model captures motor behavior during
    voltage disturbances, including stall and recovery characteristics.
    
    Args:
        name (str): Name of the motor load model
    
    Returns:
        RmsModelTemplate: Configured RMS model template for induction motor simulation
"""


def MotorLoadBuild(vfactory: VarFactory, name: str = "") -> RmsModelTemplate:
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    pi = math.pi
    # Inputs:
    inputs = [vfactory.add_var('Vm', reference=VarPowerFlowReferenceType.Vm),
              vfactory.add_var('Va', reference=VarPowerFlowReferenceType.Va)]
    Vm = inputs[0]
    Va = inputs[1]
    # Variables:
    omega = vfactory.add_var('omega')
    Id = vfactory.add_var('Id')
    Iq = vfactory.add_var('Iq')
    P = vfactory.add_var('Pl')
    Q = vfactory.add_var('Ql')
    Vq = vfactory.add_var('Vq')
    Vd = vfactory.add_var('Vd')
    Ed_prime = vfactory.add_var('Ed_prime')
    Eq_prime = vfactory.add_var('Eq_prime')
    Ed_2prime = vfactory.add_var('Ed_2prime')
    Eq_2prime = vfactory.add_var('Eq_2prime')

    # Parameters:
    u = vfactory.add_var('u')
    Ls = vfactory.add_var('Ls')
    Lp = vfactory.add_var('Lp')
    Rs = vfactory.add_var('Ra')
    Tp0 = vfactory.add_var('Tp0')
    H = vfactory.add_var('H')
    D = vfactory.add_var('D')
    n = vfactory.add_var('n')
    VT = vfactory.add_var('VT')
    TV = vfactory.add_var('TV')
    Lpp = vfactory.add_var('Lpp')
    Cl0 = vfactory.add_var('Cl0')
    Tpp0 = vfactory.add_var('Tpp0')
    omega_s = vfactory.add_var('omega_s')
    omega0 = vfactory.add_var('omega_0')
    SLIP0 = vfactory.add_var('SLIP0')

    # Shunt Parameters
    b = vfactory.add_var('b')
    g = vfactory.add_var('g')

    events_dict = {
        # Electrical (induction motor typical ranges)
        Rs: vfactory.add_const(0.015),  # Stator resistance (pu) ~ 0.01–0.03
        Ls: vfactory.add_const(0.15),  # Stator leakage inductance (pu) ~ 0.10–0.25
        Lp: vfactory.add_const(3.00),  # Magnetising (mutual) inductance (pu) ~ 2–5

        # Transient / rotor dynamics (approx. rotor open-circuit constants)
        Tp0: vfactory.add_const(0.60),  # "Transient" time constant (s) ~ 0.2–1.0
        Lpp: vfactory.add_const(0.12),  # Subtransient/leakage-like inductance (pu), < Ls
        Tpp0: vfactory.add_const(0.05),  # Fast electrical time constant (s) ~ 0.02–0.10

        # Mechanical
        H: vfactory.add_const(0.8),  # Inertia constant (s) ~ 0.2–1.5
        D: vfactory.add_const(0.0),  # Damping (often 0 unless explicitly modelled)
        n: vfactory.add_const(1.0),  # Exponent of the torque speed dependency (unitless)
        Cl0: vfactory.add_const(None),  # Initial load torque	(pu)
        SLIP0: vfactory.add_const(0.0),  # Initial load torque	(pu)

        # Voltage measurement / filtering
        VT: vfactory.add_const(1.0),  # Nominal terminal voltage (pu)
        TV: vfactory.add_const(0.02),  # Voltage transducer / RMS estimator time (s)
        u: vfactory.add_const(0.0),
        # frequency
        omega_s: vfactory.add_const(1.0),  # nominal frequency in pu
        omega0: vfactory.add_const(None),  # initial frequency in pu

        g: vfactory.add_const(0.0),
        b: vfactory.add_const(0.0),
    }

    SLIP = 1 - omega
    dt_Ed = Eq_prime * omega_s * SLIP - (Iq * (Ls - Lp) + Ed_prime) / Tp0
    dt_Eq = -Ed_prime * omega_s * SLIP - (-Id * (Ls - Lp) + Eq_prime) / Tp0
    block1 = Block(
        state_eqs=[
            u * dt_Ed,  # dt Ed_prime
            u * dt_Eq,  # dt Eq_prime
            u * (-(Eq_prime - Eq_2prime) * omega_s * SLIP - (Ed_prime - Eq_2prime - (Lp - Lpp) * Iq) / Tpp0 + dt_Ed),
            # dt Ed_2prime
            u * ((Ed_prime - Ed_2prime) * omega_s * SLIP - (Eq_prime - Ed_2prime + (Lp - Lpp) * Id) / Tpp0 + dt_Eq),
            # dt Eq_2prime
        ],
        state_vars=[Ed_prime, Eq_prime, Ed_2prime, Eq_2prime],
    )

    Te = vfactory.add_var('Te')
    block2 = Block(
        state_eqs=[
            u * ((Eq_2prime * Iq + Ed_2prime * Id) - Cl0 * sym.abs(omega / omega0) ** n) / 2 * H,
        ],
        state_vars=[omega],
        algebraic_eqs=[
            Te - (Eq_2prime * Iq + Ed_2prime * Id),
            u * (Vd - Ed_2prime + Rs * Id - Lpp * Iq),
            u * (Vq - Eq_2prime + Rs * Iq + Lpp * Id),
            Vd - (-Vm * sym.sin(Va)),
            Vq - (Vm * sym.cos(Va)),
            u * (P - (Vd * Id + Vq * Iq - g * Vm ** 2)),
            u * (Q - (Vq * Id - Vd * Iq + b * Vm ** 2)),
        ],
        algebraic_vars=[Id, Iq, P, Q, Vd, Vq, Te]
    )

    res_block = Block(children=[block1, block2])
    res_block.event_dict = events_dict
    res_block.external_mapping = {
        VarPowerFlowReferenceType.Vm: inputs[0],
        VarPowerFlowReferenceType.Va: inputs[1],
        VarPowerFlowReferenceType.P: P,
        VarPowerFlowReferenceType.Q: Q,
    }
    res_block.in_vars = inputs

    I = sym.conj(-(P + 1j * Q)) / (Vm * sym.exp(1j * Va))
    Ii = sym.imag(I)
    Ir = sym.real(I)
    Vi = sym.imag(Vm * sym.exp(1j * Va))
    Vr = sym.real(Vm * sym.exp(1j * Va))

    SLIP = 1 - omega
    dt_Ed = Eq_prime * omega_s * SLIP - (Iq * (Ls - Lp) + Ed_prime) / Tp0
    dt_Eq = -Ed_prime * omega_s * SLIP - (-Id * (Ls - Lp) + Eq_prime) / Tp0
    a = Tp0 * omega_s * SLIP
    L = (Ls - Lp)
    Ed_prime_calc = L * (-Iq + a * Id) / (1 + a ** 2)
    Eq_prime_calc = L * (Id + a * Iq) / (1 + a ** 2)
    A_val = (Iq * (Ls - Lp) + Ed_prime_calc) / Tp0
    omega_init = -A_val / (omega_s * Eq_prime_calc) + vfactory.add_const(1.0)
    res_block.init_eqs = {
        Vd: -Vm * sym.sin(Va),
        Vq: Vm * sym.cos(Va),
        Id: (P * Vd + Q * Vq) / (Vd ** 2 + Vq ** 2),
        Iq: (P * Vq - Q * Vd) / (Vd ** 2 + Vq ** 2),
        Ed_2prime: u * (Vd + (Rs * Id - Lpp * Iq)),
        Eq_2prime: u * (Vq + (Rs * Iq + Lpp * Id)),
        Te: u * (Eq_2prime * Iq + Ed_2prime * Id),
        Cl0: u * (Eq_2prime * Iq + Ed_2prime * Id),
        omega: u * omega_init,
        Ed_prime: u * Ed_prime_calc,
        Eq_prime: u * Eq_prime_calc,
        omega0: omega,
    }

    templ.block = res_block
    return templ
