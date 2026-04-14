# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List, Dict
import numpy as np

from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block, Var, Const, Expr, VarPowerFlowRefferenceType, tf_to_diffblock, \
    tf_to_block_with_states, tf_to_diffblock_with_states, hard_sat, DiffBlock
from VeraGridEngine.Utils.Symbolic.symbolic import cos, sin, real, imag, conj, angle, exp, log, abs, UndefinedConst, \
    sqrt, atan, f_exc


def GenqecBuild(name: str = "") -> RmsModelTemplate:
    """
     generator with quadratic saturation
    """

    templ = RmsModelTemplate()

    # Inputs
    # Vm: Bus voltage module
    # Va: Bus voltage angle
    # Tm: mechanical torque (from governor)
    # Vf: excitation voltage (from exciter)

    inputs: List[Var] = [Var("Vm_" + name),
                         Var("Va" + name),
                         Var("Tm_" + name),
                         Var("Vf_" + name)]

    # ______________________________________________________________________________________
    #                                    variables
    # ______________________________________________________________________________________

    # Saturation factors
    Sat_d = Var('Sat_d' + name)
    Sat_q = Var('Sat_q' + name)

    # State variables
    delta = Var("delta" + name)  # rotor angle
    omega = Var("omega" + name)  # rotor electrical speed
    Eq1 = Var("Eq1" + name)  # internal emf behind Xd'
    Ed1 = Var("Ed1" + name)
    Eq2 = Var("Eq2" + name)
    Ed2 = Var("Ed2" + name)
    Eq_prime = Var("Eq_prime" + name)  # transient voltage q-axis
    Ed_prime = Var("Ed_prime" + name)  # transient voltage d-axis
    Eq_2prime = Var("Eq_2prime" + name)  # subtransient voltage q-axis
    Ed_2prime = Var("Ed_2prime" + name)  # subtransient voltage d-axis

    # Algebraic variables
    Pg = Var('Pg' + name)
    Qg = Var('Qg' + name)
    Id = Var("Id" + name)
    Iq = Var("Iq" + name)
    Vd = Var("Vd" + name)
    Vq = Var("Vq" + name)
    Psid = Var("Psid" + name)
    Psiq = Var("Psiq" + name)
    Te = Var("Te" + name)
    IRPu = Var("IRPu" + name)

    # Saturated resistances
    Xd_sat = Var('Xd_sat' + name)
    Xq_sat = Var('Xq_sat' + name)
    Xd_prime_sat = Var('Xd_prime_sat' + name)
    Xq_prime_sat = Var('Xq_prime_sat' + name)
    Xd_2prime_sat = Var('Xd_2prime_sat' + name)
    Xq_2prime_sat = Var('Xq_2prime_sat' + name)
    Ed2_coef = Var('Ed2_coef' + name)
    Eq2_coef = Var('Eq2_coef' + name)
    Sa = Var('Sa' + name)
    V_qag = Var('V_qag' + name)
    V_dag = Var('V_dag' + name)
    Psi_ag = Var('Psi_ag' + name)

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________
    fn = Var('fn')  # system frequency [Hz]
    ws = Var('ws')  # synchronous speed [rad/s]
    M = Var('M')  # inertia constant
    D = Var('D')  # damping (optional)
    Rs = Var('Rs')  # stator resistance
    Ra = Var('Ra')  # armature resistance (if distinct)

    # Reactances
    Xd = Var('Xd')
    Xq = Var('Xq')
    Xd_prime = Var('Xd_prime')
    Xq_prime = Var('Xq_prime')
    Xd_2prime = Var('Xd_2prime')
    Xq_2prime = Var('Xq_2prime')
    Xl = Var('Xl')

    # Time constants
    Td0_prime = Var('Td0_prime')
    Tq0_prime = Var('Tq0_prime')
    Td0_2prime = Var('Td0_2prime')
    Tq0_2prime = Var('Tq0_2prime')

    A = Var('A')
    B = Var("B")

    event_dict = {
        fn: Const(50.0),
        ws: Const(1.0),
        M: Const(3.5),
        D: Const(10.0),
        Rs: Const(0.003),
        Ra: Const(0.003),

        # Reactances
        Xd: Const(1.8),
        Xq: Const(1.7),
        Xd_prime: Const(0.3),
        Xq_prime: Const(0.55),
        Xd_2prime: Const(0.25),
        Xq_2prime: Const(0.25),
        Xl: Const(0.15),

        # Time constants
        Td0_prime: Const(8.0),
        Tq0_prime: Const(0.4),
        Td0_2prime: Const(0.03),
        Tq0_2prime: Const(0.05),

        A: Const(5.0),
        B: Const(1.0)
    }

    templ.block = Block(
        state_eqs=[
            (omega - Const(1)) * ws,  # dδ/dt
            (inputs[2] - Te - D * (omega - Const(1))) * (1 / M),  # dω/dt
            inputs[3] / Td0_prime - Sat_q * Eq1 / Td0_prime,  # dEq'/dt
            -Sat_q * Ed1 / Tq0_prime,  # dEd'/dt
            Eq2_coef * (-Eq2),  # dEq''/dt
            Ed2_coef * (-Ed2),  # dEd''/dt
        ],
        state_vars=[delta, omega, Eq_prime, Ed_prime, Eq_2prime, Ed_2prime],
        algebraic_eqs=[
            Vd - (-inputs[2] * sin(inputs[3] - delta)),  # from input block
            Vq - (inputs[2] * cos(inputs[3] - delta)),  # from input block
            Pg - (Vd * Id + Vq * Iq),  # from input block
            Qg - (Vq * Id - Vd * Iq),  # from input block
            Vd - (omega * Ed_2prime + Iq * Xq_2prime_sat - Id * Ra),
            Vq - (omega * Eq_2prime - Id * Xd_2prime_sat - Iq * Ra),
            Psid - (Eq_prime - Id * Xd_2prime_sat),
            Psiq - (-Ed_prime - Iq * Xq_2prime_sat),
            Te - (Psid * Iq - Psiq * Id),
            (Xd_sat - Xd_prime_sat) * Eq1 - (
                    (Xd_sat - Xd_prime_sat) * Eq_2prime + (Eq_prime - Eq_2prime) * (Xd_sat - Xd_2prime_sat)),
            # Eq1 definition
            (Xq_sat - Xq_prime_sat) * Ed1 - (
                    (Xq_sat - Xq_prime_sat) * Ed_2prime + (Ed_prime - Ed_2prime) * (Xq_sat - Xq_2prime_sat)),
            # Ed1 definition
            (Xd_sat - Xd_2prime_sat) * Eq2 - (-1) * (
                    (Eq_prime - Eq_2prime) * (Xd_sat - Xd_prime_sat) + Id * (Xd_sat - Xd_2prime_sat) ** 2),
            # Ed2 definition
            (Xq_sat - Xq_2prime_sat) * Ed2 - (-1) * (
                    (Ed_prime - Ed_2prime) * (Xq_sat - Xq_prime_sat) + Iq * (Xq_sat - Xq_2prime_sat) ** 2),
            # Eq2 definition
            Eq2_coef * (Tq0_2prime * (Xq_sat - Xq_2prime_sat)) - (Xq_prime_sat - Xq_2prime_sat) * Sat_q,
            Ed2_coef * (Td0_2prime * (Xd_sat - Xd_2prime_sat)) - (Xd_prime_sat - Xd_2prime_sat) * Sat_d,
            # saturated resistance
            Sat_d * Xd_2prime_sat - (Xd_2prime - Xl + Xl * Sat_d),
            Sat_q * Xq_2prime_sat - (Xq_2prime - Xl + Xl * Sat_q),
            Sat_d * Xd_prime_sat - (Xd_prime - Xl + Xl * Sat_d),
            Sat_q * Xq_prime_sat - (Xq_prime - Xl + Xl * Sat_q),
            Sat_d * Xd_sat - (Xd - Xl + Xl * Sat_d),
            Sat_q * Xq_sat - (Xq - Xl + Xl * Sat_q),
            # flux
            V_dag - (Vd - Ra * Id + Xq_2prime_sat * Iq + Iq * Ra + Id * Xl),
            V_qag - (Vq - Ra * Iq + Xd_2prime_sat * Id + Id * Ra - Iq * Xl),
            omega * Psi_ag - ws * sqrt(V_qag * V_qag + V_dag * V_dag),
            Sat_d - (Const(1) + Sa),
            Sat_q - (Const(1) + Sa),
            # saturations (quadratic)
            Sa - A * ((Psi_ag - B) + sqrt((Psi_ag - B) ** 2 + Const(1e-4))),
            IRPu - Eq1 * (1 + Sa)
        ],
        algebraic_vars=[Pg, Qg, Vd, Vq, Psid, Psiq, Ed2_coef, Eq2_coef, Te, Ed1, Eq1, Ed2, Eq2, Id, Iq,
                        # saturated resistance
                        Xq_sat, Xd_sat, Xq_prime_sat, Xd_prime_sat, Xq_2prime_sat, Xd_2prime_sat,
                        # flux
                        Sa, V_dag, V_qag, Sat_d, Sat_q, Psi_ag,
                        IRPu],
        init_eqs={
            omega: Const(0),
            V_dag: inputs[0] * sin(inputs[1]) + imag(
                conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * Ra + real(
                conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * Xl,
            V_qag: inputs[0] * cos(inputs[1]) + real(
                conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * Ra + imag(
                conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * Xl,
            Psi_ag: sqrt(V_dag ** 2 + V_qag ** 2),
            Sa: A * (Psi_ag - B) ** 2,
            delta: atan(
                (inputs[0] * sin(inputs[1]) + imag(
                    conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * Ra + real(
                    conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) *
                 ((Xq - Xl) / (Const(1) + Sa) + Xl)) /
                (inputs[0] * cos(inputs[1]) + real(
                    conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * Ra + imag(
                    conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) *
                 ((Xq - Xl) / (Const(1) + Sa) + Xl))),
            Vd: (inputs[0] * sin(delta - inputs[1])),
            Vq: (inputs[0] * cos(delta - inputs[1])),
            Id: real(conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * sin(delta) - real(
                conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * cos(delta),
            Iq: real(conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * cos(delta) + real(
                conj(Pg + 1j * Qg) / conj(inputs[0] * exp(1j * inputs[1]))) * sin(delta),
            Ed_prime: (Xq - Xq_prime) * Iq / (Const(1) + Sa),
            Eq_prime: Ed_prime + (Xq_prime - Xl) * (Iq / (Const(1) + Sa)) + (Xq_prime - Xl) * (
                    Iq / (Const(1) + Sa)),
            Eq_2prime: Vd,
            Ed_2prime: Vq,
        },
        out_vars=[Pg, Qg, omega, IRPu],
        in_vars=inputs,
        event_dict=event_dict,
        name="genqec"
    )

    return templ


def GovernorBuild(self, name: str = "") -> RmsModelTemplate:
    
    templ = RmsModelTemplate()
    
    parameters = {
        # Time constants
        "T1": Const(1.0),  # governor time constant (s)
        "T2": Const(1.0),  # reheater time constant (s)
        "T3": Const(10.0),  # crossover time constant (s)
        "T4": Const(0.2),  # lead/lag constant (s)
        "T5": Const(0.5),  # lead/lag constant (s)
        "T6": Const(0.1),  # lead/lag constant (s)
        "T7": Const(0.05),  # lead/lag constant (s)

        # Steam fractions (distribution factors)
        "K1": Const(0.5),
        "K2": Const(0.5),
        "K3": Const(0.0),
        "K4": Const(0.0),
        "K5": Const(0.0),
        "K6": Const(0.0),
        "K7": Const(0.0),
        "K8": Const(0.0),
    }

    inputs = [Var("omega_")]

    # ______________________________________________________________________________________
    #                                    variables
    # ______________________________________________________________________________________

    Tm = Var("Tm")  # Mechanical power input (pu
    et = Var("et")

    # reference
    Pm_ref = Var('Pm_ref')
    algebraic_eqs = []
    algebraic_vars = []

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________

    # Gains and limits
    K = Var("K")  # governor gain (inverse droop)
    Pmax = Var("Pmax")  # max mechanical power (pu)
    Pmin = Var("Pmin")  # min mechanical power (pu)
    Uc = Var("Uc")  # max valve closing rate (pu/s)
    Uo = Var("Uo")  # max valve opening rate (pu/s)
    T_aux = Var("T_aux")

    # Control
    Kp = Var("Kp")
    Ki = Var("Ki")
    omega_ref = Var('omega_ref')
    p0 = Var('p0')
    P0 = Var('P0')

    events_dict = {
        # control parameters
        Kp: Const(-0.01),
        Ki: Const(-0.01),
        p0: Const(1.0),
        P0: Const(0.01),
        omega_ref: Const(1),

        # Governor parameters
        K: Const(10.0),  # governor gain (inverse droop)
        Pmax: Const(2.0),  # max mechanical power (pu)
        Pmin: Const(0.0),  # min mechanical power (pu)
        Uc: Const(-0.1),  # max valve closing rate (pu/s)
        Uo: Const(0.1),  # max valve opening rate (pu/s)
        T_aux: Const(0.0),

    }
    controller_block = Block(
        state_eqs=[
            P0 * (inputs[0] - omega_ref)
        ],
        state_vars=[et],
        algebraic_eqs=[
            T_aux - (Kp * (inputs[0] - omega_ref) + Ki * et),
        ],
        algebraic_vars=[T_aux],
    )

    u1 = inputs[0] - omega_ref
    lead_lag_block, y1 = tf_to_diffblock(
        num=np.array([1, parameters["T2"]]),
        den=np.array([1, parameters["T1"]]),
        x=u1,
        name='gov0',
    )

    # ==============================
    # First Feed back Loop
    y2_3 = Var('y2_3_gov')
    algebraic_vars.append(y2_3)
    x2 = Pm_ref - K * y1 - y2_3

    y2 = x2 * (1 / parameters["T3"])
    y2_1 = hard_sat(y2, Uc, Uo)
    tf1, y2_2 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([0, 1]),
        x=y2_1,
        name='gov1',
    )
    algebraic_eqs.append(y2_3 - hard_sat(y2_2, Pmin, Pmax))

    # ==============================
    # We compute different outputs for every tf
    tf2, y3_1 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["T4"]]),
        x=y2_3,
        name='gov2',
    )
    tf3, y3_2 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["T5"]]),
        x=y3_1,
        name='gov3',
    )
    tf4, y3_3 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["T6"]]),
        x=y3_2,
        name='gov4',
    )
    tf5, y3_4 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["T7"]]),
        x=y3_3,
        name='gov5',
    )

    u = parameters["K1"] * y3_1 + parameters["K2"] * y3_2 + parameters["K3"] * y3_3 + \
        parameters["K4"] * y3_4 + T_aux
    aux_block = Block(
        algebraic_eqs=[u - Tm] + algebraic_eqs,
        algebraic_vars=[Tm, Pm_ref] + algebraic_vars,
    )

    templ.block = Block(
        children=[lead_lag_block, tf1, tf2, tf3, tf4, tf5, aux_block, controller_block],
        parameters=parameters,
        out_vars=[Tm],
        in_vars=inputs,
        event_dict=events_dict,
        name="governor"
    )

    return templ


def StabilizerBuild(self, name: str = "") -> RmsModelTemplate:
   
    templ = RmsModelTemplate()

    parameters = {
        # Stabilizer parameters
        "A1": Const(1.0),  # notch filter coefficient 1
        "A2": Const(1.0),  # notch filter coefficient 2
        "t1": Const(0.1),  # lead time constant
        "t2": Const(0.02),  # lag time constant
        "t3": Const(0.02),  # lag time constant
        "t4": Const(0.1),  # second lag time constant
        "t5": Const(10.0),  # washout time constant
        "t6": Const(0.02),  # transducer time constant
    }

    # input variables
    # omega: omega from generator

    inputs = [Var("omega_")]

    # PSS parameters with typical values

    Ks = Var("Ks")  # stabilizer gain
    VPssMaxPu = Var("VPssMaxPu")  # max stabilizer output
    VPssMinPu = Var("VPssMinPu")  # min stabilizer output
    SNom = Var("SNom")  # nominal apparent power

    events_dict = {
        # Stabilizer parameters
        Ks: Const(20.0),  # stabilizer gain
        VPssMaxPu: Const(1.0),  # max stabilizer output
        VPssMinPu: Const(-1.0),  # min stabilizer output
        SNom: Const(1.0),  # nominal apparent power
    }

    # variables
    Vpss = Var('V_pss')

    vars_block = Block(
        algebraic_vars=[],
    )

    tf, y = tf_to_diffblock_with_states(
        num=np.array([1.0]),
        den=np.array([1, parameters["t6"]]),
        x=inputs[0],
        name='stabilizer1',
    )

    tf2, y2 = tf_to_diffblock_with_states(
        num=np.array([0, parameters["t5"]]),
        den=np.array([1, parameters["t5"]]),
        x=Ks * y,
        name='stabilizer2',
    )
    tf3, y3 = tf_to_diffblock_with_states(
        num=np.array([1]),
        den=np.array([1, parameters["A1"], parameters["A2"]]),
        x=y2,
        name='stabilizer3',
    )
    tf4, y4 = tf_to_diffblock_with_states(
        num=np.array([1, parameters["t1"]]),
        den=np.array([1, parameters["t2"]]),
        x=y3,
        name='stabilizer4',
    )
    tf5, y5 = tf_to_diffblock_with_states(
        num=np.array([1, parameters["t3"]]),
        den=np.array([1, parameters["t4"]]),
        x=y4,
        name='stabilizer5',
    )

    algebraic_eqs = list()
    algebraic_eqs.append(hard_sat(y5, VPssMinPu, VPssMaxPu) - Vpss)
    block_1 = Block()

    templ.block = Block(
        children=[tf, tf2, tf3, tf4, tf5],
        algebraic_eqs=algebraic_eqs,
        algebraic_vars=[Vpss],
        in_vars=inputs,
        out_vars=[Vpss],
        event_dict=events_dict,
        parameters=parameters,
        name="stabilizer",
    )

    templ.block.add(vars_block)
    templ.block.add(block_1)

    return templ


def ExciterBuild(self, name: str = "") -> RmsModelTemplate:
    """
    
    :param self: 
    :param name: 
    :return: 
    """
    templ = RmsModelTemplate()

    parameters = {
        # Exciter (AVR) parameters
        "Ka": Const(200.0),  # AVR gain
        "Kf": Const(0.03),  # exciter rate feedback gain

        # Time constants
        "tA": Const(0.02),  # AVR time constant (s)
        "tB": Const(10.0),  # lead-lag: lag time constant (s)
        "tC": Const(1.0),  # lead-lag: lead time constant (s)
        "tE": Const(0.5),  # exciter field time constant (s)
        "tF": Const(1.0),  # rate feedback time constant (s)
        "tR": Const(0.02),  # stator voltage filter time constant (s)

        # Exciter submodel parameters
        "Kc": Const(0.2),  # rectifier loading factor
        "Kd": Const(0.1),  # demagnetizing factor
        "Ke": Const(1.0),  # field resistance constant

    }

    # input variables
    # IRPu: rotor current (pu) ???
    # Va: measured stator voltage (from generator) (pu)
    # Vpss: output from power system stabilizer (pu)

    inputs = [Var("IRPu_"), Var("Va_"), Var("Vpss_")]

    algebraic_vars = []

    # ______________________________________________________________________________________
    #                                    variables
    # ______________________________________________________________________________________

    Vf = Var("Vf")
    Efe = Var('Efe')
    UsRefPu = Var("UsRefPu")  # reference voltage (pu)

    # Exciter internal variables
    VeMaxPu = Var('VeMaxPu')
    u_aux = Var('u_aux')

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________

    # ---- Exciter (AVR) parameters ----
    AEz = Var("AEz")  # saturation gain
    BEz = Var("BEz")  # saturation exponential coefficient
    EfeMaxPu = Var("EfeMaxPu")  # max exciter field voltage (pu)
    EfeMinPu = Var("EfeMinPu")  # min exciter field voltage (pu)

    # ---- Exciter (AVR) time constants and limits ----

    TolLi = Var("TolLi")  # limiter crossing tolerance (fraction)

    VaMaxPu = Var("VaMaxPu")  # AVR output max (pu)
    VaMinPu = Var("VaMinPu")  # AVR output min (pu)
    VeMinPu = Var("VeMinPu")  # min exciter output voltage (pu)
    VfeMaxPu = Var("VfeMaxPu")  # max exciter field current signal (pu)

    # exciter submodel parameters
    AEx = Var("AEx")  # Gain of saturation function
    BEx = Var("BEx")  # Exponential coefficient of saturation function
    ToLLi = Var("ToLLi")  # Tolerance on limit crossing
    VeMinPu_submodel = Var("VeMinPu_submodel")  # Minimum exciter output voltage (pu)
    VfeMaxPu_submodel = Var("VfeMaxPu_submodel")  # Maximum exciter field current signal (pu)
    F_rectifier = Var("F_rectifier")  # Rectifier factor

    events_dict = {
        # Exciter (AVR) parameters
        AEz: Const(0.02),  # saturation gain
        BEz: Const(1.5),  # saturation exponential coefficient
        EfeMaxPu: Const(15.0),  # max exciter field voltage (pu)
        EfeMinPu: Const(-5.0),  # min exciter field voltage (pu)

        # Time constants
        TolLi: Const(0.05),  # limiter crossing tolerance (fraction)

        # Limits
        VaMaxPu: Const(20.0),  # AVR output max (pu)
        VaMinPu: Const(-10.0),  # AVR output min (pu)
        VeMinPu: Const(-1.0),  # min exciter output voltage (pu)
        VfeMaxPu: Const(5.0),  # max exciter field current signal (pu)

        # Exciter submodel parameters
        AEx: Const(0.02),  # saturation gain
        BEx: Const(-0.01),  # exponential coeff of saturation function
        ToLLi: Const(0.05),  # tolerance on limit crossing
        VeMinPu_submodel: Const(-0.1),  # minimum exciter output voltage
        VfeMaxPu_submodel: Const(5.0),  # max exciter field current signal
        F_rectifier: Const(1.0),  # rectifier factor (1=DC, 0.5=AC)
    }

    # ---Internal Blocks---
    tf1, y1 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["tR"]]),
        x=inputs[1],
        name='exciter1',
    )  # filtered stator voltage

    # error1 = UPssPu - y + UsRefPu
    error1 = (- y1 + UsRefPu) + inputs[2]
    tf2, y2 = tf_to_diffblock(
        num=np.array([0, parameters["Kf"]]),
        den=np.array([1, parameters["tF"]]),
        x=Vf,
        name='exciter2',
    )
    error2 = error1 - y2

    tf3, y3 = tf_to_diffblock(
        num=np.array([1, parameters["tC"]]),
        den=np.array([1, parameters["tB"]]),
        x=error2,
        name='exciter3',
    )
    tf4, y4 = tf_to_diffblock(
        num=np.array([parameters["Ka"]]),
        den=np.array([1, parameters["tA"]]),
        x=y3,
        name='exciter4',
    )

    y5 = hard_sat(y4, VaMinPu, VaMaxPu)

    min_const = Const(max(events_dict[VaMinPu], events_dict[EfeMinPu]))
    max_const = Const(min(events_dict[VaMaxPu], events_dict[EfeMaxPu]))
    y6 = hard_sat(y4, min_const, max_const)

    # exciter submodel

    algebraic_eqs_submodel = []
    algebraic_vars_submodel = []

    x1 = VfeMaxPu - inputs[0] * parameters["Kd"]
    error1 = Efe - (inputs[0] * parameters["Kd"] + u_aux)

    tf1_sub, Ve_presat = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([0, parameters["tE"]]),
        x=error1,
        name='subexciter1',
    )

    Ve = hard_sat(Ve_presat, VeMinPu, Const(1000))
    aux_expr = parameters["Ke"] * Ve + AEx * Ve * exp(BEx * Ve)
    algebraic_eqs_submodel.append(u_aux - aux_expr)
    algebraic_eqs_submodel.append(VeMaxPu * u_aux - x1)

    f_input = Var('f_input')
    f_output = Var('f_output')
    f_output_res = f_exc(f_input)
    algebraic_vars_submodel.append(f_input)
    algebraic_vars_submodel.append(f_output)
    algebraic_eqs_submodel.append(f_input * Ve - inputs[0] * parameters["Kc"])

    algebraic_eqs_submodel.append(Vf - f_output * Ve)
    algebraic_eqs_submodel.append(f_output_res - f_output)

    aux_model = DiffBlock(
        algebraic_eqs=algebraic_eqs_submodel,
        algebraic_vars=[u_aux, VeMaxPu, Vf] + algebraic_vars_submodel
    )

    exciter_submodel = DiffBlock(children=[tf1_sub, aux_model])

    linking_block = Block(
        algebraic_eqs=[y6 - Efe],
        algebraic_vars=[Efe, UsRefPu] + algebraic_vars,

    )

    templ.block = Block(
        children=[tf1, tf2, tf3, tf4, exciter_submodel, linking_block],
        out_vars=[Vf],
        in_vars=inputs,
        event_dict=events_dict
    )

    return templ


def get_complete_generator_template() -> RmsModelTemplate:
    """
    
    :return: 
    """
    templ = RmsModelTemplate()
    # ______________________________________________________________________________________
    #                                    variables
    # ______________________________________________________________________________________

    Vm: Var = Var('Vm_placeholder')
    Va: Var = Var('Va_placeholder')

    Pg: Var = Var('P_g')
    Qg: Var = Var('Q_g')

    # Variables
    ## generator
    ### state variables
    delta = Var("delta")
    omega = Var("omega")
    Eq1 = Var("Eq1")  # internal emf behind Xd'
    Ed1 = Var("Ed1")
    Eq2 = Var("Eq2")
    Ed2 = Var("Ed2")
    Eq_prime = Var("Eq_prime")  # transient voltage q-axis
    Ed_prime = Var("Ed_prime")  # transient voltage d-axis
    Eq_2prime = Var("Eq_2prime")  # subtransient voltage q-axis
    Ed_2prime = Var("Ed_2prime")  # subtransient voltage d-axis

    ### algebraic variables
    Psid = Var("psid")
    Psiq = Var("psiq")
    Id = Var("i_d")
    Iq = Var("i_q")
    Vd = Var("v_d")
    Vq = Var("v_q")
    Te = Var("Te")
    IRPu = Var("IRPu")

    ### Saturated resistances
    Xd_sat = Var('Xd_sat')
    Xq_sat = Var('Xq_sat')
    Xd_prime_sat = Var('Xd_prime_sat')
    Xq_prime_sat = Var('Xq_prime_sat')
    Xd_2prime_sat = Var('Xd_2prime_sat')
    Xq_2prime_sat = Var('Xq_2prime_sat')
    Ed2_coef = Var('Ed2_coef')
    Eq2_coef = Var('Eq2_coef')
    Sa = Var('Sa')
    V_qag = Var('V_qag')
    V_dag = Var('V_dag')
    Psi_ag = Var('Psi_ag')

    ### Saturation factors
    Sat_d = Var('Sat_d')
    Sat_q = Var('Sat_q')

    # governor
    Tm = Var("Tm")  # Mechanical power input (pu
    et = Var("et")
    # reference
    Pm_ref = Var('Pm_ref')

    # stabilizer
    Vpss = Var('V_pss')

    # exciter
    Vf = Var("Vf")
    Efe = Var('Efe')
    UsRefPu = Var("UsRefPu")  # reference voltage (pu)

    # Exciter internal variables
    VeMaxPu = Var('VeMaxPu')
    u_aux = Var('u_aux')

    # ______________________________________________________________________________________
    #                                    event parameters
    # ______________________________________________________________________________________

    # generator
    fn = Var(
        'fn')  # system frequency [Hz] # not specified in the generator, must be specified in multicircuit, like Sbase...
    ws = Var('ws')  # synchronous speed [rad/s]
    M = Var('M')  # inertia constant
    D = Var('D')  # damping (optional)
    Rs = Var('Rs')  # stator resistance
    Ra = Var('Ra')  # armature resistance (if distinct)

    # Reactances
    Xd = Var('Xd')
    Xq = Var('Xq')
    Xd_prime = Var('Xd_prime')
    Xq_prime = Var('Xq_prime')
    Xd_2prime = Var('Xd_2prime')
    Xq_2prime = Var('Xq_2prime')
    Xl = Var('Xl')

    # Time constants
    Td0_prime = Var('Td0_prime')
    Tq0_prime = Var('Tq0_prime')
    Td0_2prime = Var('Td0_2prime')
    Tq0_2prime = Var('Tq0_2prime')

    A = Var('A')  # saturation speed RMS/EMT
    B = Var("B")  # saturation threshold RMS/EMT

    # governor
    # Gains and limits
    K = Var("K")  # governor gain (inverse droop)
    Pmax = Var("Pmax")  # max mechanical power (pu)
    Pmin = Var("Pmin")  # min mechanical power (pu)
    Uc = Var("Uc")  # max valve closing rate (pu/s)
    Uo = Var("Uo")  # max valve opening rate (pu/s)
    T_aux = Var("T_aux")

    # Control
    Kp = Var("Kp")
    Ki = Var("Ki")
    omega_ref = Var('omega_ref')
    p0 = Var('p0')
    P0 = Var('P0')

    # stabilizer
    Ks = Var("Ks")  # stabilizer gain
    VPssMaxPu = Var("VPssMaxPu")  # max stabilizer output
    VPssMinPu = Var("VPssMinPu")  # min stabilizer output
    SNom = Var("SNom")  # nominal apparent power

    # ---- Exciter (AVR) parameters ----
    AEz = Var("AEz")  # saturation gain
    BEz = Var("BEz")  # saturation exponential coefficient
    EfeMaxPu = Var("EfeMaxPu")  # max exciter field voltage (pu)
    EfeMinPu = Var("EfeMinPu")  # min exciter field voltage (pu)

    # ---- Exciter (AVR) time constants and limits ----
    TolLi = Var("TolLi")  # limiter crossing tolerance (fraction)

    VaMaxPu = Var("VaMaxPu")  # AVR output max (pu)
    VaMinPu = Var("VaMinPu")  # AVR output min (pu)
    VeMinPu = Var("VeMinPu")  # min exciter output voltage (pu)
    VfeMaxPu = Var("VfeMaxPu")  # max exciter field current signal (pu)

    # exciter submodel parameters
    AEx = Var("AEx")  # Gain of saturation function
    BEx = Var("BEx")  # Exponential coefficient of saturation function
    ToLLi = Var("ToLLi")  # Tolerance on limit crossing
    VeMinPu_submodel = Var("VeMinPu_submodel")  # Minimum exciter output voltage (pu)
    VfeMaxPu_submodel = Var("VfeMaxPu_submodel")  # Maximum exciter field current signal (pu)
    F_rectifier = Var("F_rectifier")  # Rectifier factor

    # ______________________________________________________________________________________
    #                                    event_dict
    # ______________________________________________________________________________________

    event_dict = {
        # generator
        fn: Const(50.0),
        ws: Const(1.0),
        M: Const(3.5),
        D: Const(10.0),
        Rs: Const(0.003),
        Ra: Const(0.003),

        # Reactances
        Xd: Const(1.8),
        Xq: Const(1.7),
        Xd_prime: Const(0.3),
        Xq_prime: Const(0.55),
        Xd_2prime: Const(0.25),
        Xq_2prime: Const(0.25),
        Xl: Const(0.15),

        # Time constants
        Td0_prime: Const(8.0),
        Tq0_prime: Const(0.4),
        Td0_2prime: Const(0.03),
        Tq0_2prime: Const(0.05),

        A: Const(5.0),
        B: Const(1.0),

        # governor
        # control parameters
        Kp: Const(-0.01),
        Ki: Const(-0.01),
        p0: Const(1.0),
        P0: Const(0.01),
        omega_ref: Const(1),

        # Governor parameters
        K: Const(10.0),  # governor gain (inverse droop)
        Pmax: Const(2.0),  # max mechanical power (pu)
        Pmin: Const(0.0),  # min mechanical power (pu)
        Uc: Const(-0.1),  # max valve closing rate (pu/s)
        Uo: Const(0.1),  # max valve opening rate (pu/s)
        T_aux: Const(0.0),

        # Stabilizer parameters
        Ks: Const(20.0),  # stabilizer gain
        VPssMaxPu: Const(1.0),  # max stabilizer output
        VPssMinPu: Const(-1.0),  # min stabilizer output
        SNom: Const(1.0),  # nominal apparent power

        # Exciter (AVR) parameters
        AEz: Const(0.02),  # saturation gain
        BEz: Const(1.5),  # saturation exponential coefficient
        EfeMaxPu: Const(15.0),  # max exciter field voltage (pu)
        EfeMinPu: Const(-5.0),  # min exciter field voltage (pu)

        # Time constants
        TolLi: Const(0.05),  # limiter crossing tolerance (fraction)

        # Limits
        VaMaxPu: Const(20.0),  # AVR output max (pu)
        VaMinPu: Const(-10.0),  # AVR output min (pu)
        VeMinPu: Const(-1.0),  # min exciter output voltage (pu)
        VfeMaxPu: Const(5.0),  # max exciter field current signal (pu)

        # Exciter submodel parameters
        AEx: Const(0.02),  # saturation gain
        BEx: Const(-0.01),  # exponential coeff of saturation function
        ToLLi: Const(0.05),  # tolerance on limit crossing
        VeMinPu_submodel: Const(-0.1),  # minimum exciter output voltage
        VfeMaxPu_submodel: Const(5.0),  # max exciter field current signal
        F_rectifier: Const(1.0),  # rectifier factor (1=DC, 0.5=AC)
    }

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________
    #
    parameters = {
        # Governor
        # Time constants
        "T1": Const(1.0),  # governor time constant (s)
        "T2": Const(1.0),  # reheater time constant (s)
        "T3": Const(10.0),  # crossover time constant (s)
        "T4": Const(0.2),  # lead/lag constant (s)
        "T5": Const(0.5),  # lead/lag constant (s)
        "T6": Const(0.1),  # lead/lag constant (s)
        "T7": Const(0.05),  # lead/lag constant (s)

        # Steam fractions (distribution factors)
        "K1": Const(0.5),
        "K2": Const(0.5),
        "K3": Const(0.0),
        "K4": Const(0.0),
        "K5": Const(0.0),
        "K6": Const(0.0),
        "K7": Const(0.0),
        "K8": Const(0.0),

        # Stabilizer parameters
        "A1": Const(1.0),  # notch filter coefficient 1
        "A2": Const(1.0),  # notch filter coefficient 2
        "t1": Const(0.1),  # lead time constant
        "t2": Const(0.02),  # lag time constant
        "t3": Const(0.02),  # lag time constant
        "t4": Const(0.1),  # second lag time constant
        "t5": Const(10.0),  # washout time constant
        "t6": Const(0.02),  # transducer time constant

        # Exciter (AVR) parameters
        "Ka": Const(200.0),  # AVR gain
        "Kf": Const(0.03),  # exciter rate feedback gain

        # Time constants
        "tA": Const(0.02),  # AVR time constant (s)
        "tB": Const(10.0),  # lead-lag: lag time constant (s)
        "tC": Const(1.0),  # lead-lag: lead time constant (s)
        "tE": Const(0.5),  # exciter field time constant (s)
        "tF": Const(1.0),  # rate feedback time constant (s)
        "tR": Const(0.02),  # stator voltage filter time constant (s)

        # Exciter submodel parameters
        "Kc": Const(0.2),  # rectifier loading factor
        "Kd": Const(0.1),  # demagnetizing factor
        "Ke": Const(1.0),  # field resistance constant
    }

    generator_model = Block(
        state_eqs=[
            # generator
            (omega - Const(1)) * ws,  # dδ/dt
            (Tm - Te - D * (omega - Const(1))) * (1 / M),  # dω/dt
            Vf / Td0_prime - Sat_q * Eq1 / Td0_prime,  # dEq'/dt
            -Sat_q * Ed1 / Tq0_prime,  # dEd'/dt
            Eq2_coef * (-Eq2),  # dEq''/dt
            Ed2_coef * (-Ed2),  # dEd''/dt
            # governor
            P0 * (omega - omega_ref)
        ],
        state_vars=[
            # generator
            delta, omega, Eq_prime, Ed_prime, Eq_2prime, Ed_2prime,
            # governor
            et],
        algebraic_eqs=[
            # generator
            Vd - (-Tm * sin(Vf - delta)),  # from input block
            Vq - (Tm * cos(Vf - delta)),  # from input block
            Pg - (Vd * Id + Vq * Iq),  # from input block
            Qg - (Vq * Id - Vd * Iq),  # from input block
            Vd - (omega * Ed_2prime + Iq * Xq_2prime_sat - Id * Ra),
            Vq - (omega * Eq_2prime - Id * Xd_2prime_sat - Iq * Ra),
            Psid - (Eq_prime - Id * Xd_2prime_sat),
            Psiq - (-Ed_prime - Iq * Xq_2prime_sat),
            Te - (Psid * Iq - Psiq * Id),
            (Xd_sat - Xd_prime_sat) * Eq1 - (
                    (Xd_sat - Xd_prime_sat) * Eq_2prime + (Eq_prime - Eq_2prime) * (
                    Xd_sat - Xd_2prime_sat)),
            # Eq1 definition
            (Xq_sat - Xq_prime_sat) * Ed1 - (
                    (Xq_sat - Xq_prime_sat) * Ed_2prime + (Ed_prime - Ed_2prime) * (Xq_sat - Xq_2prime_sat)),
            # Ed1 definition
            (Xd_sat - Xd_2prime_sat) * Eq2 - (-1) * (
                    (Eq_prime - Eq_2prime) * (Xd_sat - Xd_prime_sat) + Id * (Xd_sat - Xd_2prime_sat) ** 2),
            # Ed2 definition
            (Xq_sat - Xq_2prime_sat) * Ed2 - (-1) * (
                    (Ed_prime - Ed_2prime) * (Xq_sat - Xq_prime_sat) + Iq * (Xq_sat - Xq_2prime_sat) ** 2),
            # Eq2 definition
            Eq2_coef * (Tq0_2prime * (Xq_sat - Xq_2prime_sat)) - (Xq_prime_sat - Xq_2prime_sat) * Sat_q,
            Ed2_coef * (Td0_2prime * (Xd_sat - Xd_2prime_sat)) - (Xd_prime_sat - Xd_2prime_sat) * Sat_d,
            # saturated resistance
            Sat_d * Xd_2prime_sat - (Xd_2prime - Xl + Xl * Sat_d),
            Sat_q * Xq_2prime_sat - (Xq_2prime - Xl + Xl * Sat_q),
            Sat_d * Xd_prime_sat - (Xd_prime - Xl + Xl * Sat_d),
            Sat_q * Xq_prime_sat - (Xq_prime - Xl + Xl * Sat_q),
            Sat_d * Xd_sat - (Xd - Xl + Xl * Sat_d),
            Sat_q * Xq_sat - (Xq - Xl + Xl * Sat_q),
            # flux
            V_dag - (Vd - Ra * Id + Xq_2prime_sat * Iq + Iq * Ra + Id * Xl),
            V_qag - (Vq - Ra * Iq + Xd_2prime_sat * Id + Id * Ra - Iq * Xl),
            omega * Psi_ag - ws * sqrt(V_qag * V_qag + V_dag * V_dag),
            Sat_d - (Const(1) + Sa),
            Sat_q - (Const(1) + Sa),
            # saturations (quadratic)
            Sa - A * ((Psi_ag - B) + sqrt((Psi_ag - B) ** 2 + Const(1e-4))),
            IRPu - Eq1 * (1 + Sa),
            # governor
            T_aux - (Kp * (omega - omega_ref) + Ki * et)

        ],
        algebraic_vars=[
            # generator
            Pg, Qg, Vd, Vq, Psid, Psiq, Ed2_coef, Eq2_coef, Te,
            Ed1, Eq1, Ed2, Eq2, Id, Iq,
            # saturated resistance
            Xq_sat, Xd_sat, Xq_prime_sat, Xd_prime_sat, Xq_2prime_sat, Xd_2prime_sat,
            # flux
            Sa, V_dag, V_qag, Sat_d, Sat_q, Psi_ag, IRPu,
            # governor
            T_aux,
        ],
        init_eqs={
            omega: Const(0),
            V_dag: Vm * sin(Va) + imag(
                conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * Ra + real(
                conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * Xl,
            V_qag: Vm * cos(Va) + real(
                conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * Ra + imag(
                conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * Xl,
            Psi_ag: sqrt(V_dag ** 2 + V_qag ** 2),
            Sa: A * (Psi_ag - B) ** 2,
            delta: atan(
                (Vm * sin(Va) + imag(
                    conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * Ra + real(
                    conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) *
                 ((Xq - Xl) / (Const(1) + Sa) + Xl)) /
                (Vm * cos(Va) + real(
                    conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * Ra + imag(
                    conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) *
                 ((Xq - Xl) / (Const(1) + Sa) + Xl))),
            Vd: (Vm * sin(delta - Va)),
            Vq: (Vm * cos(delta - Va)),
            Id: real(conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * sin(
                delta) - real(
                conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * cos(delta),
            Iq: real(conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * cos(
                delta) + real(
                conj(Pg + 1j * Qg) / conj(Vm * exp(1j * Va))) * sin(delta),
            Ed_prime: (Xq - Xq_prime) * Iq / (Const(1) + Sa),
            Eq_prime: Ed_prime + (Xq_prime - Xl) * (Iq / (Const(1) + Sa)) + (
                    Xq_prime - Xl) * (
                              Iq / (Const(1) + Sa)),
            Eq_2prime: Vd,
            Ed_2prime: Vq,
        })

    # governor_blocks:
    algebraic_eqs_gov = []
    algebraic_vars_gov = []

    u1 = omega - omega_ref
    lead_lag_block, y1 = tf_to_diffblock(
        num=np.array([1, parameters["T2"]]),
        den=np.array([1, parameters["T1"]]),
        x=u1,
        name='gov0',
    )

    # ==============================
    # First Feed back Loop
    y2_3 = Var('y2_3_gov')
    algebraic_vars_gov.append(y2_3)
    x2 = Pm_ref - K * y1 - y2_3

    y2 = x2 * (1 / parameters["T3"])
    y2_1 = hard_sat(y2, Uc, Uo)
    tf1, y2_2 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([0, 1]),
        x=y2_1,
        name='gov1',
    )
    algebraic_eqs_gov.append(y2_3 - hard_sat(y2_2, Pmin, Pmax))

    # ==============================
    # We compute different outputs for every tf
    tf2, y3_1 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["T4"]]),
        x=y2_3,
        name='gov2',
    )
    tf3, y3_2 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["T5"]]),
        x=y3_1,
        name='gov3',
    )
    tf4, y3_3 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["T6"]]),
        x=y3_2,
        name='gov4',
    )
    tf5, y3_4 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["T7"]]),
        x=y3_3,
        name='gov5',
    )

    u = parameters["K1"] * y3_1 + parameters["K2"] * y3_2 + parameters["K3"] * y3_3 + \
        parameters["K4"] * y3_4 + T_aux
    aux_block = Block(
        algebraic_eqs=[u - Tm] + algebraic_eqs_gov,
        algebraic_vars=[Tm, Pm_ref] + algebraic_vars_gov,
    )

    governor_block = Block(
        children=[lead_lag_block, tf1, tf2, tf3, tf4, tf5, aux_block, ]
    )

    # stabilizer

    vars_block = Block(
        algebraic_vars=[],
    )

    tf, y = tf_to_diffblock_with_states(
        num=np.array([1.0]),
        den=np.array([1, parameters["t6"]]),
        x=omega,
        name='stabilizer1',
    )

    tf2, y2 = tf_to_diffblock_with_states(
        num=np.array([0, parameters["t5"]]),
        den=np.array([1, parameters["t5"]]),
        x=Ks * y,
        name='stabilizer2',
    )
    tf3, y3 = tf_to_diffblock_with_states(
        num=np.array([1]),
        den=np.array([1, parameters["A1"], parameters["A2"]]),
        x=y2,
        name='stabilizer3',
    )
    tf4, y4 = tf_to_diffblock_with_states(
        num=np.array([1, parameters["t1"]]),
        den=np.array([1, parameters["t2"]]),
        x=y3,
        name='stabilizer4',
    )
    tf5, y5 = tf_to_diffblock_with_states(
        num=np.array([1, parameters["t3"]]),
        den=np.array([1, parameters["t4"]]),
        x=y4,
        name='stabilizer5',
    )

    algebraic_eqs_stabil = list()
    algebraic_eqs_stabil.append(hard_sat(y5, VPssMinPu, VPssMaxPu) - Vpss)
    block_1 = Block()

    stabilizer_block = Block(
        children=[tf, tf2, tf3, tf4, tf5],
        algebraic_eqs=algebraic_eqs_stabil,
        algebraic_vars=[Vpss],
    )

    stabilizer_block.add(vars_block)
    stabilizer_block.add(block_1)

    # exciter####################################################################
    #############################################################################

    # ---Internal Blocks---
    tf1, y1 = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([1, parameters["tR"]]),
        x=Va,
        name='exciter1',
    )  # filtered stator voltage

    # error1 = UPssPu - y + UsRefPu
    error1 = (- y1 + UsRefPu) + Vpss
    tf2, y2 = tf_to_diffblock(
        num=np.array([0, parameters["Kf"]]),
        den=np.array([1, parameters["tF"]]),
        x=Vf,
        name='exciter2',
    )
    error2 = error1 - y2

    tf3, y3 = tf_to_diffblock(
        num=np.array([1, parameters["tC"]]),
        den=np.array([1, parameters["tB"]]),
        x=error2,
        name='exciter3',
    )
    tf4, y4 = tf_to_diffblock(
        num=np.array([parameters["Ka"]]),
        den=np.array([1, parameters["tA"]]),
        x=y3,
        name='exciter4',
    )

    y5 = hard_sat(y4, VaMinPu, VaMaxPu)

    min_const = Const(max(event_dict[VaMinPu], event_dict[EfeMinPu]))
    max_const = Const(min(event_dict[VaMaxPu], event_dict[EfeMaxPu]))
    y6 = hard_sat(y4, min_const, max_const)

    # exciter submodel

    algebraic_eqs_submodel = []
    algebraic_vars_submodel = []

    x1 = VfeMaxPu - IRPu * parameters["Kd"]
    error1 = Efe - (IRPu * parameters["Kd"] + u_aux)

    tf1_sub, Ve_presat = tf_to_diffblock(
        num=np.array([1]),
        den=np.array([0, parameters["tE"]]),
        x=error1,
        name='subexciter1',
    )

    Ve = hard_sat(Ve_presat, VeMinPu, Const(1000))
    aux_expr = parameters["Ke"] * Ve + AEx * Ve * exp(BEx * Ve)
    algebraic_eqs_submodel.append(u_aux - aux_expr)
    algebraic_eqs_submodel.append(sqrt((VeMaxPu * u_aux) ** 2 + Const(1e-5)) - x1)

    f_input = Var('f_input')
    f_output = Var('f_output')
    f_output_res = f_exc(f_input)
    algebraic_vars_submodel.append(f_input)
    algebraic_vars_submodel.append(f_output)
    algebraic_eqs_submodel.append(f_input * Ve - IRPu * parameters["Kc"])

    algebraic_eqs_submodel.append(Vf - f_output * Ve)
    algebraic_eqs_submodel.append(f_output_res - f_output)

    aux_model = DiffBlock(
        algebraic_eqs=algebraic_eqs_submodel,
        algebraic_vars=[u_aux, VeMaxPu, Vf] + algebraic_vars_submodel
    )

    exciter_submodel = DiffBlock(children=[tf1_sub, aux_model])

    linking_block = Block(
        algebraic_eqs=[y6 - Efe],
        algebraic_vars=[Efe, UsRefPu],

    )

    exciter_model = Block(children=[tf1, tf2, tf3, tf4, exciter_submodel, linking_block])

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Vm: Vm,
        VarPowerFlowRefferenceType.Va: Va,
        VarPowerFlowRefferenceType.P: Pg,
        VarPowerFlowRefferenceType.Q: Qg
    }

    templ.block.event_dict = event_dict
    # templ.block.init_values = init_values

    templ.block.children.append(governor_block)
    templ.block.children.append(stabilizer_block)
    templ.block.children.append(exciter_model)
    templ.block.children.append(generator_model)

    return templ
