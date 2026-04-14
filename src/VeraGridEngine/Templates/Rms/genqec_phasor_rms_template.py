# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Generator template (genqec) for phasor-based RMS simulation.

This template accepts Vr, Vi (phasor voltage components) as inputs instead of Vm, Va (polar coordinates).
This allows direct connection to phasor bus models without coordinate conversion.
"""

import numpy as np
import math

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym
import VeraGridEngine.Utils.Symbolic.symbolic_ml as sym_ml
from VeraGridEngine.Templates.templates_common_functions import to_implicit

def get_genqec_phasor(vfactory: VarFactory, name: str = "") -> RmsModelTemplate:
    """
    Generator with quadratic saturation for phasor-based RMS simulation.
    
    This version accepts Vr, Vi (phasor voltage components) as inputs instead of Vm, Va.
    The dq-frame voltages are computed directly from Vr, Vi using Park transformation:
    - Vd = Vr * sin(delta) - Vi * cos(delta)
    - Vq = Vr * cos(delta) + Vi * sin(delta)
    
    Args:
        vfactory: VarFactory instance for creating variables
        name: Name suffix for the template
        
    Returns:
        RmsModelTemplate: Generator model template for phasor simulation
    """
    pi = math.pi
    templ = RmsModelTemplate(name=name)
    templ.tpe = DeviceType.GeneratorDevice

    # Inputs: Vr, Vi (phasor voltage components), Tm, Vf
    Vr = vfactory.add_var("Vr_" + name, VarPowerFlowRefferenceType.Vr)
    Vi = vfactory.add_var("Vi_" + name, VarPowerFlowRefferenceType.Vi)
    inputs = [Vr, Vi,
              vfactory.add_var("Tm_" + name),
              vfactory.add_var("Vf_" + name)]

    # ______________________________________________________________________________________
    #                                    variables
    # ______________________________________________________________________________________

    # State variables
    delta = vfactory.add_var("delta" + name)  # rotor angle
    omega = vfactory.add_var("omega" + name)  # rotor electrical speed
    Eq1 = vfactory.add_var("Eq1" + name)  # internal emf behind Xd'
    Ed1 = vfactory.add_var("Ed1" + name)
    Eq_prime = vfactory.add_var("Eq_prime" + name)  # transient voltage q-axis
    Ed_prime = vfactory.add_var("Ed_prime" + name)  # transient voltage d-axis
    Psid_prime = vfactory.add_var("Psid_prime" + name)  # transient voltage d-axis
    Psiq_prime = vfactory.add_var("Psiq_prime" + name)  # transient voltage d-axis

    # Algebraic variables
    Pg = vfactory.add_var('Pg' + name)
    Qg = vfactory.add_var('Qg' + name)
    Id = vfactory.add_var("Id" + name)
    Iq = vfactory.add_var("Iq" + name)
    Vd = vfactory.add_var("Vd" + name)
    Vq = vfactory.add_var("Vq" + name)
    Psid = vfactory.add_var("Psid" + name)
    Psiq = vfactory.add_var("Psiq" + name)
    Te = vfactory.add_var("Te" + name)
    IRPu = vfactory.add_var("IRPu" + name)

    # Saturated resistances
    Xd_2prime_sat = vfactory.add_var('Xd_2prime_sat' + name)
    Xq_2prime_sat = vfactory.add_var('Xq_2prime_sat' + name)
    Sa = vfactory.add_var('Sa' + name)
    Sat = vfactory.add_var('Sat' + name)
    V_qag = vfactory.add_var('V_qag' + name)
    V_dag = vfactory.add_var('V_dag' + name)
    Psi_ag = vfactory.add_var('Psi_ag' + name)
    
    # Phasor current outputs for current balance formulation
    Irg = vfactory.add_var('Irg' + name)  # Real current injection
    Iig = vfactory.add_var('Iig' + name)  # Imaginary current injection

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________
    fn = vfactory.add_var('fn')  # system frequency [Hz]
    ws = vfactory.add_var('ws')  # synchronous speed [rad/s]
    M = vfactory.add_var('M')  # inertia constant
    D = vfactory.add_var('D')  # damping (optional)
    Rs = vfactory.add_var('Rs')  # stator resistance
    Ra = vfactory.add_var('Ra')  # armature resistance (if distinct)

    # Reactances
    Xd = vfactory.add_var('Xd')
    Xq = vfactory.add_var('Xq')
    Xd_prime = vfactory.add_var('Xd_prime')
    Xq_prime = vfactory.add_var('Xq_prime')
    Xd_2prime = vfactory.add_var('Xd_2prime')
    Xq_2prime = vfactory.add_var('Xq_2prime')
    Xl = vfactory.add_var('Xl')

    # Time constants
    Td0_prime = vfactory.add_var('Td0_prime')
    Tq0_prime = vfactory.add_var('Tq0_prime')
    Td0_2prime = vfactory.add_var('Td0_2prime')
    Tq0_2prime = vfactory.add_var('Tq0_2prime')

    # Auxiliary expressions for phasor computation
    A = vfactory.add_var('A')
    B = vfactory.add_var("B")
    Xd_prime_minus_Xl = vfactory.add_var('Xd_prime_minus_Xl')
    Xq_prime_minus_Xl = vfactory.add_var('Xq_prime_minus_Xl')
    Xdaux = vfactory.add_var('Xdaux')
    Xdaux2 = vfactory.add_var('Xdaux2')
    Xdaux3 = vfactory.add_var('Xdaux3')

    Xqaux = vfactory.add_var('Xqaux')
    Xqaux2 = vfactory.add_var('Xqaux2')
    Xqaux3 = vfactory.add_var('Xqaux3')

    event_dict = {
        fn: vfactory.add_const(50.0),
        ws: vfactory.add_const(2 * pi * 50),
        M: vfactory.add_const(3.5),
        D: vfactory.add_const(10.0),
        Rs: vfactory.add_const(0.003),
        Ra: vfactory.add_const(0.003),

        # Reactances
        Xd: vfactory.add_const(1.8),
        Xq: vfactory.add_const(1.7),
        Xd_prime: vfactory.add_const(0.3),
        Xq_prime: vfactory.add_const(0.55),
        Xd_2prime: vfactory.add_const(0.25),
        Xq_2prime: vfactory.add_const(0.35),
        Xl: vfactory.add_const(0.15),

        # Time constants
        Td0_prime: vfactory.add_const(8.0),
        Tq0_prime: vfactory.add_const(0.4),
        Td0_2prime: vfactory.add_const(0.03),
        Tq0_2prime: vfactory.add_const(0.05),

        Xd_prime_minus_Xl: Xd_prime - Xl,
        Xq_prime_minus_Xl: Xq_prime - Xl,
        Xdaux: ((Xd_prime - Xd_2prime) / (Xd_prime_minus_Xl) ** 2),
        Xdaux2: ((Xd_prime - Xd_2prime) / (Xd_prime_minus_Xl)),
        Xdaux3: ((Xd_2prime - Xl) / (Xd_prime_minus_Xl)),
        Xqaux: ((Xq_prime - Xq_2prime) / (Xq_prime_minus_Xl) ** 2),
        Xqaux2: (Xq_prime - Xq_2prime) / (Xq_prime_minus_Xl),
        Xqaux3: ((Xq_2prime - Xl) / (Xq_prime_minus_Xl)),
        A: vfactory.add_const(5.0),
        B: vfactory.add_const(1.0)
    }

    Eq_2prime_expr = Psid_prime * Xdaux2 + Eq_prime * Xdaux3
    Ed_2prime_expr = Psiq_prime * Xqaux2 + Ed_prime * Xqaux3
    Iq_sat = vfactory.add_var('Iq_sat')
    Id_sat = vfactory.add_var('Id_sat')

    # Vm and Va for initialization (computed from Vr, Vi)
    Vm_init = sym.sqrt(Vr * Vr + Vi * Vi)
    # Note: atan2 doesn't exist in this symbolic library, use atan(Vi/Vr)
    # This assumes normal operation where Vr > 0
    Va_init = sym.atan(Vi / Vr)

    # Air-gap voltage expressions for initialization (using computed Vm, Va)
    Viag_expr = Vm_init * sym.sin(Va_init) + sym.imag(
        sym.conj(Pg + 1j * Qg) / sym.conj(Vm_init * sym.exp(1j * Va_init))) * Ra + sym.real(
        sym.conj(Pg + 1j * Qg) / sym.conj(Vm_init * sym.exp(1j * Va_init))) * Xl
    Vrag_expr = Vm_init * sym.cos(Va_init) + sym.real(
        sym.conj(Pg + 1j * Qg) / sym.conj(Vm_init * sym.exp(1j * Va_init))) * Ra - sym.imag(
        sym.conj(Pg + 1j * Qg) / sym.conj(Vm_init * sym.exp(1j * Va_init))) * (Xl)

    # Multilinear blocks (from generation_tensygrid_ml.py)
    # We call trig_transform only on delta to get cos(delta) and sin(delta)
    ml_trig_block, cos_delta, sin_delta = sym_ml.trig_transform(vfactory, delta)
    
    # We call ml_positive_part to get (Psi_ag-B)^+ := max(Psi_ag-B, 0)
    ml_positive_part, Psi_plus, Psi_minus = sym_ml.ml_positive_part(vfactory, Psi_ag - B)
    
    # Get multilinear block internal variables for initialization
    u_plus1_ml = ml_positive_part.algebraic_vars[0]  # u_plus1
    u_plus2_ml = ml_positive_part.algebraic_vars[1]  # u_plus2
    u_minus1_ml = ml_positive_part.algebraic_vars[2]  # u_minus1
    u_minus2_ml = ml_positive_part.algebraic_vars[3]  # u_minus2

    templ.block = Block(
        state_eqs=[
            (omega - vfactory.add_const(1)) * ws,  # dδ/dt
            (inputs[2] - Te - D * (omega - vfactory.add_const(1))) * (1 / M),  # dω/dt
            (inputs[3] - Sat * Eq1) / Td0_prime,  # dEq'/dt
            -Sat * Ed1 / Tq0_prime,  # dEd'/dt
            (-Psiq_prime + Iq_sat * Xq_prime_minus_Xl + Ed_prime),  # dPsiq'/dt
            (-Psid_prime - Id_sat * Xd_prime_minus_Xl + Eq_prime),  # dPsid'/dt
        ],
        state_vars=[delta, omega, Eq_prime, Ed_prime, Psiq_prime, Psid_prime],
        algebraic_eqs=[
            # Park transformation from Vr, Vi to Vd, Vq using multilinear trig_transform on delta only
            Vd - ( Vr * sin_delta - Vi * cos_delta),
            Vq - ( Vr * cos_delta + Vi * sin_delta),
            
            Pg - (Vd * Id + Vq * Iq),  # active power
            Qg - (Vq * Id - Vd * Iq),  # reactive power
            Vd - (omega * Ed_2prime_expr + Iq * Xq_2prime_sat - Id * Ra),
            Vq - (omega * Eq_2prime_expr - Id * Xd_2prime_sat - Iq * Ra),
            Psid - (Eq_2prime_expr - Id * Xd_2prime_sat),
            Psiq - (-Ed_2prime_expr - Iq * Xq_2prime_sat),
            Te - (Psid * Iq - Psiq * Id),

            Ed1 - (Ed_prime - (Xq - Xq_prime) * (
                    Iq_sat - (Ed_prime - Psiq_prime + Iq_sat * (Xq_prime_minus_Xl)) * Xqaux)),
            Eq1 - (Eq_prime + (Xd - Xd_prime) * (
                    Id_sat + (Eq_prime - Psid_prime - Id_sat * (Xd_prime_minus_Xl)) * Xdaux)),

            # saturated resistance
            Sat - (vfactory.add_const(1) + Sa),
            Id - Id_sat * Sat,
            Iq - Iq_sat * Sat,
            Sat * Xd_2prime_sat - (Xd_2prime + Xl * Sa),
            Sat * Xq_2prime_sat - (Xq_2prime + Xl * Sa),

            # flux
            V_dag - (Vd + Id * Ra - Iq * Xl),
            V_qag - (Vq + Iq * Ra + Id * Xl),
            omega * Psi_ag - sym.sqrt(V_qag * V_qag + V_dag * V_dag),
            # saturations using multilinear ml_positive_part
            Sa - A * Psi_plus,

            # Eq1, Eq2, Ed1, Ed2 exciter
            IRPu - Eq1 * Sat,
            
            # Phasor current outputs (inverse Park transformation)
            # Ir = Id*sin(delta) + Iq*cos(delta)
            # Ii = -Id*cos(delta) + Iq*sin(delta)
            Irg - (Id * sin_delta + Iq * cos_delta),
            Iig - (-Id * cos_delta + Iq * sin_delta),
        ],
        algebraic_vars=[Pg, Qg, Vd, Vq, Psid, Psiq, Te, Ed1, Eq1, Id, Iq,
                        # saturated resistance
                        Xq_2prime_sat, Xd_2prime_sat, Id_sat, Iq_sat,
                        # flux
                        Sa, Sat, V_dag, V_qag, Psi_ag,
                        IRPu,
                        # Phasor current outputs for current balance
                        Irg, Iig],
        init_eqs={
            # Air Gap Voltages and delta (must come first as others depend on these)
            omega: vfactory.add_const(1),
            Psi_ag: sym.sqrt(Viag_expr ** 2 + Vrag_expr ** 2),
            # Saturation initialization: Sa = A * max(Psi_ag - B, 0)
            # Since Psi_ag > B at init, use direct formula: Sa = A * (Psi_ag - B)
            Sa: A * sym.max(Psi_ag - B, vfactory.add_const(0)),
            Sat: vfactory.add_const(1) + Sa,
            # Multilinear block internal variables
            u_plus1_ml: sym.sqrt(sym.max(Psi_ag - B, vfactory.add_const(0))),
            u_plus2_ml: u_plus1_ml,
            u_minus1_ml: vfactory.add_const(0),  # sqrt(max(-(Psi_ag-B), 0)) = 0 when Psi_ag > B
            u_minus2_ml: u_minus1_ml,
            delta: sym.atan(
                (Vm_init * sym.sin(Va_init) + sym.imag(
                    sym.conj(Pg + 1j * Qg) / sym.conj(Vm_init * sym.exp(1j * Va_init))) * Ra + sym.real(
                    sym.conj(Pg + 1j * Qg) / sym.conj(Vm_init * sym.exp(1j * Va_init))) *
                 ((Xq - Xl) / (vfactory.add_const(1) + Sa) + Xl)) /
                (Vm_init * sym.cos(Va_init) + sym.real(
                    sym.conj(Pg + 1j * Qg) / sym.conj(Vm_init * sym.exp(1j * Va_init))) * Ra - sym.imag(
                    sym.conj(Pg + 1j * Qg) / sym.conj(Vm_init * sym.exp(1j * Va_init))) *
                 ((Xq - Xl) / (vfactory.add_const(1) + Sa) + Xl))),
            
            # Multilinear block variables (depend on delta and Psi_ag)

            # Saturated Resistances
            Xd_2prime_sat: (Xd_2prime - Xl + Xl * Sat) / Sat,
            Xq_2prime_sat: (Xq_2prime - Xl + Xl * Sat) / Sat,

            # Terminal Voltages and Intensities in dq frame
            Vd: -(Vm_init * sym.sin(Va_init - delta)),
            Vq: (Vm_init * sym.cos(Va_init - delta)),
            Id: (Pg * Vd + Qg * Vq) / (Vd ** 2 + Vq ** 2),
            Iq: (Pg * Vq - Qg * Vd) / (Vd ** 2 + Vq ** 2),
            V_dag: (Vd + Id * Ra - Iq * Xl),
            V_qag: (Vq + Iq * Ra + Id * Xl),

            # We initialize the states Eq', Ed', Psid', Psiq'
            Psid_prime: (Vq + Xd_2prime_sat * Id + Ra * Iq) / omega - (Xd_2prime - Xl) * Id / Sat,
            Ed_prime: (Xq - Xq_prime) * Iq / Sat,
            Psiq_prime: (Xq - Xl) * Iq / Sat,
            Eq_prime: Psid_prime + (Xd_prime - Xl) * Id / Sat,
            Ed1: (Ed_prime - (Xq - Xq_prime) * (
                    Iq / Sat - (Ed_prime - Psiq_prime + Iq * (Xq_prime - Xl) / Sat) * Xqaux)),
            Eq1: (Eq_prime + (Xd - Xd_prime) * (
                    Id / Sat + (Eq_prime - Psid_prime - Id * (Xd_prime - Xl) / Sat) * Xdaux)),

            Psid: (Eq_2prime_expr - Id * Xd_2prime_sat),
            Psiq: (-Ed_2prime_expr - Iq * Xq_2prime_sat),
            Te: (Psid * Iq - Psiq * Id),

            IRPu: Eq1 * (1 + Sa),
            Sat: vfactory.add_const(1) + Sa,
            Iq_sat: Iq / Sat,
            Id_sat: Id / Sat,
        },
        external_mapping={
            VarPowerFlowRefferenceType.Ir: Irg,
            VarPowerFlowRefferenceType.Ii: Iig,
            VarPowerFlowRefferenceType.Vr: inputs[0],
            VarPowerFlowRefferenceType.Vi: inputs[1],
        },

        api_obj_mapping={
            ParamPowerFlowRefferenceType.fn: fn,
            ParamPowerFlowRefferenceType.ws: ws,
            ParamPowerFlowRefferenceType.M: M,
            ParamPowerFlowRefferenceType.D: D,
            ParamPowerFlowRefferenceType.Rs: Rs,
            ParamPowerFlowRefferenceType.Ra: Ra,

            # Reactances
            ParamPowerFlowRefferenceType.Xd: Xd,
            ParamPowerFlowRefferenceType.Xq: Xq,
            ParamPowerFlowRefferenceType.Xd_prime: Xd_prime,
            ParamPowerFlowRefferenceType.Xq_prime: Xq_prime,
            ParamPowerFlowRefferenceType.Xd_2prime: Xd_2prime,
            ParamPowerFlowRefferenceType.Xq_2prime: Xq_2prime,
            ParamPowerFlowRefferenceType.Xl: Xl,

            # Time constants
            ParamPowerFlowRefferenceType.Td0_prime: Td0_prime,
            ParamPowerFlowRefferenceType.Tq0_prime: Tq0_prime,
            ParamPowerFlowRefferenceType.Td0_2prime: Td0_2prime,
            ParamPowerFlowRefferenceType.Tq0_2prime: Tq0_2prime,

            ParamPowerFlowRefferenceType.Xd_prime_minus_Xl: Xd_prime_minus_Xl,
            ParamPowerFlowRefferenceType.Xq_prime_minus_Xl: Xq_prime_minus_Xl,
            ParamPowerFlowRefferenceType.Xdaux: Xdaux,
            ParamPowerFlowRefferenceType.Xdaux2: Xdaux2,
            ParamPowerFlowRefferenceType.Xdaux3: Xdaux3,
            ParamPowerFlowRefferenceType.Xqaux: Xqaux,
            ParamPowerFlowRefferenceType.Xqaux2: Xqaux2,
            ParamPowerFlowRefferenceType.Xqaux3: Xqaux3,

            ParamPowerFlowRefferenceType.A: A,
            ParamPowerFlowRefferenceType.B: B,
        },

        out_vars=[Irg, Iig, omega, IRPu, Te],
        in_vars=inputs,
        event_dict=event_dict,
        name="genqec_phasor",
        children=[ml_trig_block, ml_positive_part]
    )

    return templ


def get_complete_generator_template_phasor(vfactory: VarFactory, name="complete generator phasor rms template") -> RmsModelTemplate:
    """
    Complete generator template with governor, exciter, and stabilizer for phasor-based RMS simulation.
    
    This is the phasor version that accepts Vr, Vi (phasor voltage components) as inputs instead of Vm, Va.
    The governor, exciter, and stabilizer models are internally connected to the generator.
    The exciter's Vm input is computed internally as Vm = sqrt(Vr^2 + Vi^2).
    
    Uses models from generation_tensygrid_ml.py (GenqecBuild, GovernorBuild, StabilizerBuild, ExciterBuild).
    
    Args:
        vfactory: VarFactory instance for creating variables
        name: Name of the template
        
    Returns:
        RmsModelTemplate: Complete generator model template for phasor simulation
    """
    from VeraGridEngine.Templates.Rms.generation_tensygrid_ml import GenqecBuild, GovernorBuild, StabilizerBuild, ExciterBuild
    
    templ = RmsModelTemplate(name=name)
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name

    # Generate models from generation_tensygrid_ml.py
    genqec_mdl = GenqecBuild(vfactory=vfactory, name=name).block
    governor_mdl = GovernorBuild(vfactory=vfactory, name=name).block
    stabilizer_mdl = StabilizerBuild(vfactory=vfactory, name=name).block
    exciter_mdl = ExciterBuild(vfactory=vfactory, name=name).block

    # Create Vm calculation block: Vm = sqrt(Vr^2 + Vi^2)
    # This computes the voltage magnitude from phasor components for the exciter
    Vr_input = genqec_mdl.in_vars[0]  # Vr
    Vi_input = genqec_mdl.in_vars[1]  # Vi
    
    # Create a block to compute Vm = sqrt(Vr^2 + Vi^2)
    Vm_calc = vfactory.add_var(f"Vm_calc_{name}")
    Vm_calc_aux = vfactory.add_var(f"Vm_calc_{name}")
    vm_calc_block = Block(
        algebraic_eqs=[
            Vm_calc*Vm_calc_aux - (Vr_input * Vr_input + Vi_input * Vi_input),
            Vm_calc -Vm_calc_aux],
        algebraic_vars=[Vm_calc, Vm_calc_aux],
        out_vars=[Vm_calc],
        init_eqs={
                Vm_calc: sym.sqrt(Vr_input * Vr_input + Vi_input * Vi_input),  
                Vm_calc_aux: Vm_calc,
        },
        name=f"vm_calc_{name}"
    )

    # Connect models
    # genqec inputs: [Vr, Vi, Tm, Vf]
    # genqec outputs: [Pg, Qg, omega, IRPu, Te]
    genqec_mdl.connect([genqec_mdl.in_vars[3]], [exciter_mdl.out_vars[0]])  # Vf from exciter
    exciter_mdl.connect([exciter_mdl.in_vars[0]], [genqec_mdl.out_vars[3]])  # IRPu to exciter
    exciter_mdl.connect([exciter_mdl.in_vars[1]], [vm_calc_block.out_vars[0]])  # Vm from calculation block
    exciter_mdl.connect([exciter_mdl.in_vars[2]], [stabilizer_mdl.out_vars[0]])  # Vpss to exciter

    stabilizer_mdl.connect([stabilizer_mdl.in_vars[0]], [genqec_mdl.out_vars[2]])  # omega to stabilizer

    genqec_mdl.connect([genqec_mdl.in_vars[2]], [governor_mdl.out_vars[0]])  # Tm from governor

    governor_mdl.connect([governor_mdl.in_vars[0]], [genqec_mdl.out_vars[2]])  # omega to governor
    governor_mdl.connect([governor_mdl.in_vars[1]], [genqec_mdl.out_vars[4]])  # Te to governor

    templ.block.children.append(genqec_mdl)
    templ.block.children.append(governor_mdl)
    templ.block.children.append(stabilizer_mdl)
    templ.block.children.append(exciter_mdl)
    templ.block.children.append(vm_calc_block)

    # Flatten all blocks before converting to implicit form
    templ.block.unify_blocks()
    # 
    templ.block = to_implicit(templ.block, vfactory)
    # External mapping for phasor coordinates (current balance)
    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Vr: genqec_mdl.in_vars[0],
        VarPowerFlowRefferenceType.Vi: genqec_mdl.in_vars[1],
        VarPowerFlowRefferenceType.Ir: genqec_mdl.out_vars[0],
        VarPowerFlowRefferenceType.Ii: genqec_mdl.out_vars[1],
    }

    templ.block.in_vars = [genqec_mdl.in_vars[0], genqec_mdl.in_vars[1]]
    templ.block.out_vars = [genqec_mdl.out_vars[0], genqec_mdl.out_vars[1]]

    return templ
