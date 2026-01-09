# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Tuple
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit import short_circuit_3p, short_circuit_unbalance
from VeraGridEngine.Topology.admittance_matrices import compute_admittances
from VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit_results import ShortCircuitResults
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import polar_to_rect
from VeraGridEngine.enumerations import FaultType, MethodShortCircuit, PhasesShortCircuit
from VeraGridEngine.basic_structures import CxVec, Vec, IntVec
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_basic_formulation_3ph import (compute_ybus,
                                                                                        compute_current_loads,
                                                                                        compute_power_loads,
                                                                                        compute_ybus_generator,
                                                                                        expand_magnitudes,
                                                                                        expand_indices_3ph,
                                                                                        expand3ph)
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_full_acdc_with_negative_poles import PfAcDcWithNegativePoles
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.newton_raphson_fx import newton_raphson_fx
from VeraGridEngine.basic_structures import Logger


def short_circuit_post_process(
        calculation_inputs: NumericalCircuit,
        V: CxVec,
        branch_rates: Vec,
        Yf: sp.csc_matrix,
        Yt: sp.csc_matrix
) -> Tuple[CxVec, CxVec, CxVec, CxVec, CxVec, CxVec, CxVec]:
    """
    Compute the important results for short-circuits
    :param calculation_inputs: instance of Circuit
    :param V: Voltage solution array for the circuit buses
    :param branch_rates: Array of branch ratings
    :param Yf: From admittance matrix
    :param Yt: To admittance matrix
    :return: Sf (MVA), If (p.u.), loading (p.u.), losses (MVA), Sbus(MVA)
    """

    Vf = V[calculation_inputs.passive_branch_data.F]
    Vt = V[calculation_inputs.passive_branch_data.T]

    # Branches current, loading, etc
    If = Yf * V
    It = Yt * V
    Sf = Vf * np.conj(If)
    St = Vt * np.conj(It)

    # Branch losses in MVA (not really important for short-circuits)
    losses = (Sf + St) * calculation_inputs.Sbase

    # branch voltage increment
    Vbranch = Vf - Vt

    # Branch power in MVA
    Sfb = Sf * calculation_inputs.Sbase
    Stb = St * calculation_inputs.Sbase

    # Branch loading in p.u.
    loading = Sfb / (branch_rates + 1e-9)

    return Sfb, Stb, If, It, Vbranch, loading, losses


def short_circuit_post_process_phases_abc(
        calculation_inputs: NumericalCircuit,
        V_expanded: CxVec,
        branch_rates_expanded: Vec,
        Yf: sp.csc_matrix,
        Yt: sp.csc_matrix,
        F_expanded: IntVec,
        T_expanded: IntVec,
        mask,
        branch_lookup
) -> Tuple[CxVec, CxVec, CxVec, CxVec, CxVec, CxVec, CxVec]:
    """
    Compute the important results for short-circuits
    :param calculation_inputs: instance of Circuit
    :param V_expanded: Voltage solution array for the circuit buses
    :param branch_rates_expanded: Array of branch ratings
    :param Yf: From admittance matrix
    :param Yt: To admittance matrix
    :param F_expanded:
    :param T_expanded:
    :param mask:
    :param branch_lookup:
    :return: Sf (MVA), If (p.u.), loading (p.u.), losses (MVA), Sbus(MVA)
    """

    Vf_expanded = V_expanded[F_expanded]
    Vt_expanded = V_expanded[T_expanded]

    V = V_expanded[mask]

    # Branches current, loading, etc
    If = Yf @ V
    It = Yt @ V

    If_expanded = expand_magnitudes(If, branch_lookup)
    It_expanded = expand_magnitudes(It, branch_lookup)

    Sf_expanded = Vf_expanded * np.conj(If_expanded)
    St_expanded = Vt_expanded * np.conj(It_expanded)

    # Branch losses in MVA (not really important for short-circuits)
    losses_expanded = (Sf_expanded + St_expanded) * calculation_inputs.Sbase

    # branch voltage increment
    Vbranch_expanded = Vf_expanded - Vt_expanded

    # Branch power in MVA
    Sfb_expanded = Sf_expanded * calculation_inputs.Sbase
    Stb_expanded = St_expanded * calculation_inputs.Sbase

    # Branch loading in p.u.
    loading_expanded = Sfb_expanded / (branch_rates_expanded + 1e-9)

    return Sfb_expanded, Stb_expanded, If_expanded, It_expanded, Vbranch_expanded, loading_expanded, losses_expanded


# def short_circuit_post_process_phases(
#         calculation_inputs: NumericalCircuit,
#         V: CxVec,
#         branch_rates: Vec,
#         Yf: sp.csc_matrix,
#         Yt: sp.csc_matrix
# ) -> Tuple[CxVec, CxVec, CxVec, CxVec, CxVec, CxVec, CxVec]:
#     """
#     Compute the important results for short-circuits
#     :param calculation_inputs: instance of Circuit
#     :param V: Voltage solution array for the circuit buses
#     :param branch_rates: Array of branch ratings
#     :param Yf: From admittance matrix
#     :param Yt: To admittance matrix
#     :return: Sf (MVA), If (p.u.), loading (p.u.), losses (MVA), Sbus(MVA)
#     """
#
#     Vf = V[calculation_inputs.passive_branch_data.F]
#     Vt = V[calculation_inputs.passive_branch_data.T]
#
#     # Branches current, loading, etc
#     If = Yf * V
#     It = Yt * V
#     Sf = Vf * np.conj(If)
#     St = Vt * np.conj(It)
#
#     # Branch losses in MVA (not really important for short-circuits)
#     losses = (Sf + St) * calculation_inputs.Sbase
#
#     # branch voltage increment
#     Vbranch = Vf - Vt
#
#     # Branch power in MVA
#     Sfb = Sf * calculation_inputs.Sbase
#     Stb = St * calculation_inputs.Sbase
#
#     # Branch loading in p.u.
#     loading = Sfb / (branch_rates + 1e-9)
#
#     return Sfb, Stb, If, It, Vbranch, loading, losses


def short_circuit_ph3(nc: NumericalCircuit, Vpf: CxVec, Zf: CxVec, bus_index: int):
    """
    Run a 3-phase short circuit simulation for a single island
    :param nc: NumericalCircuit
    :param Vpf: Power flow voltage vector applicable to the island
    :param Zf: Short circuit impedance vector applicable to the island
    :param bus_index: Bus index
    :return: short circuit results
    """
    adm = nc.get_admittance_matrices()
    Y_gen = nc.generator_data.get_Yshunt(seq=1)
    Y_batt = nc.battery_data.get_Yshunt(seq=1)
    Ybus_gen_batt = adm.Ybus + sp.diags(Y_gen) + sp.diags(Y_batt)

    # Compute the short circuit
    V, SCpower, ICurrent = short_circuit_3p(bus_idx=bus_index,
                                            Ybus=Ybus_gen_batt,
                                            Vbus=Vpf,
                                            Vnom=nc.bus_data.Vnom,
                                            Zf=Zf,
                                            baseMVA=nc.Sbase)

    (Sfb, Stb, If, It, Vbranch,
     loading, losses) = short_circuit_post_process(calculation_inputs=nc,
                                                   V=V,
                                                   branch_rates=nc.passive_branch_data.rates,
                                                   Yf=adm.Yf,
                                                   Yt=adm.Yt)

    # voltage, Sf, loading, losses, error, converged, Qpv
    results = ShortCircuitResults(
        nsc=1,
        n=nc.nbus,
        m=nc.nbr,
        n_hvdc=nc.nhvdc,
        n_vsc=nc.nvsc,
        bus_names=nc.bus_data.names,
        branch_names=nc.passive_branch_data.names,
        hvdc_names=nc.hvdc_data.names,
        vsc_names=nc.vsc_data.names,
        sc_names=np.array(["SC"]),
        bus_types=nc.bus_data.bus_types,
        area_names=None
    )

    results.SCpower[:, 0] = SCpower
    results.ICurrent[:, 0] = ICurrent
    results.Sbus1[:, 0] = nc.get_power_injections_pu() * nc.Sbase  # MVA
    results.voltage1[:, 0] = V
    results.Sf1[:, 0] = Sfb  # in MVA already
    results.St1[:, 0] = Stb  # in MVA already
    results.If1[:, 0] = If  # in p.u.
    results.It1[:, 0] = It  # in p.u.
    results.Vbranch1[:, 0] = Vbranch
    results.loading1[:, 0] = loading
    results.losses1[:, 0] = losses

    return results


def short_circuit_unbalanced(nc: NumericalCircuit,
                             Vpf: CxVec,
                             Zf: CxVec,
                             bus_index: int,
                             fault_type: FaultType) -> ShortCircuitResults:
    """
    Run an unbalanced short circuit simulation for a single island
    :param nc:
    :param Vpf: Power flow voltage vector applicable to the island
    :param Zf: Short circuit impedance vector applicable to the island
    :param bus_index: Index of the failed bus
    :param fault_type: FaultType
    :return: short circuit results
    """

    # build Y0, Y1, Y2
    nbr = nc.nbr
    nbus = nc.nbus

    Y_gen0 = nc.generator_data.get_Yshunt(seq=0)
    Y_batt0 = nc.battery_data.get_Yshunt(seq=0)
    Yshunt_bus0 = Y_gen0 + Y_batt0

    Cf = nc.passive_branch_data.Cf.tocsc()
    Ct = nc.passive_branch_data.Ct.tocsc()

    adm0 = compute_admittances(R=nc.passive_branch_data.R0,
                               X=nc.passive_branch_data.X0,
                               G=nc.passive_branch_data.G0,  # renamed, it was overwritten
                               B=nc.passive_branch_data.B0,
                               tap_module=nc.active_branch_data.tap_module,
                               vtap_f=nc.passive_branch_data.virtual_tap_f,
                               vtap_t=nc.passive_branch_data.virtual_tap_t,
                               tap_angle=nc.active_branch_data.tap_angle,
                               Cf=Cf,
                               Ct=Ct,
                               Yshunt_bus=Yshunt_bus0,
                               conn=nc.passive_branch_data.conn,
                               seq=0,
                               add_windings_phase=True)

    Y_gen1 = nc.generator_data.get_Yshunt(seq=1)
    Y_batt1 = nc.battery_data.get_Yshunt(seq=1)
    Yshunt_bus1 = nc.get_Yshunt_bus_pu() + Y_gen1 + Y_batt1

    adm1 = compute_admittances(R=nc.passive_branch_data.R,
                               X=nc.passive_branch_data.X,
                               G=nc.passive_branch_data.G,
                               B=nc.passive_branch_data.B,
                               tap_module=nc.active_branch_data.tap_module,
                               vtap_f=nc.passive_branch_data.virtual_tap_f,
                               vtap_t=nc.passive_branch_data.virtual_tap_t,
                               tap_angle=nc.active_branch_data.tap_angle,
                               Cf=Cf,
                               Ct=Ct,
                               Yshunt_bus=Yshunt_bus1,
                               conn=nc.passive_branch_data.conn,
                               seq=1,
                               add_windings_phase=True)

    Y_gen2 = nc.generator_data.get_Yshunt(seq=2)
    Y_batt2 = nc.battery_data.get_Yshunt(seq=2)
    Yshunt_bus2 = Y_gen2 + Y_batt2

    adm2 = compute_admittances(R=nc.passive_branch_data.R2,
                               X=nc.passive_branch_data.X2,
                               G=nc.passive_branch_data.G2,
                               B=nc.passive_branch_data.B2,
                               tap_module=nc.active_branch_data.tap_module,
                               vtap_f=nc.passive_branch_data.virtual_tap_f,
                               vtap_t=nc.passive_branch_data.virtual_tap_t,
                               tap_angle=nc.active_branch_data.tap_angle,
                               Cf=Cf,
                               Ct=Ct,
                               Yshunt_bus=Yshunt_bus2,
                               conn=nc.passive_branch_data.conn,
                               seq=2,
                               add_windings_phase=True)

    """
    Initialize Vpf introducing phase shifts
    No search algo is needed. Instead, we need to solve YV=0,
    get the angle of the voltages from here and add them to the
    original Vpf. Y should be Yseries (avoid shunts).
    In more detail:
    -----------------   -----   -----
    |   |           |   |Vvd|   |   |
    -----------------   -----   -----
    |   |           |   |   |   |   |
    |   |           | x |   | = |   |
    | Yu|     Yx    |   | V |   | 0 |
    |   |           |   |   |   |   |
    |   |           |   |   |   |   |
    -----------------   -----   -----

    where Yu = Y1.Ybus[pqpv, vd], Yx = Y1.Ybus[pqpv, pqpv], so:
    V = - inv(Yx) Yu Vvd
    ph_add = np.angle(V)
    Vpf[pqpv] *= np.exp(1j * ph_add)
    """

    adm_series = compute_admittances(R=nc.passive_branch_data.R,
                                     X=nc.passive_branch_data.X,
                                     G=np.zeros(nbr),
                                     B=np.zeros(nbr),
                                     tap_module=nc.active_branch_data.tap_module,
                                     vtap_f=nc.passive_branch_data.virtual_tap_f,
                                     vtap_t=nc.passive_branch_data.virtual_tap_t,
                                     tap_angle=nc.active_branch_data.tap_angle,
                                     Cf=Cf,
                                     Ct=Ct,
                                     Yshunt_bus=np.zeros(nbus, dtype=complex),
                                     conn=nc.passive_branch_data.conn,
                                     seq=1,
                                     add_windings_phase=True)

    indices = nc.get_simulation_indices()

    vd = indices.vd
    pqpv = indices.no_slack

    # Y1_arr = np.array(adm_series.Ybus.todense())
    # Yu = Y1_arr[np.ix_(pqpv, vd)]
    # Yx = Y1_arr[np.ix_(pqpv, pqpv)]
    #
    # I_vd = Yu * np.array(Vpf[vd])
    # Vpqpv_ph = - np.linalg.inv(Yx) @ I_vd

    # add the voltage phase due to the slack, to the rest of the nodes
    I_vd = adm_series.Ybus[np.ix_(pqpv, vd)] * Vpf[vd]
    Vpqpv_ph = - sp.linalg.spsolve(adm_series.Ybus[np.ix_(pqpv, pqpv)], I_vd)
    ph_add = np.angle(Vpqpv_ph)
    Vpf[pqpv] = polar_to_rect(np.abs(Vpf[pqpv]), np.angle(Vpf[pqpv]) + ph_add.T)

    # solve the fault
    V0, V1, V2, SCC, ICC = short_circuit_unbalance(bus_idx=bus_index,
                                                   Y0=adm0.Ybus,
                                                   Y1=adm1.Ybus,
                                                   Y2=adm2.Ybus,
                                                   Vnom=nc.bus_data.Vnom,
                                                   Vbus=Vpf,
                                                   Zf=Zf,
                                                   fault_type=fault_type,
                                                   baseMVA=nc.Sbase)

    # process results in the sequences
    (Sfb0, Stb0, If0, It0, Vbranch0,
     loading0, losses0) = short_circuit_post_process(calculation_inputs=nc,
                                                     V=V0,
                                                     branch_rates=nc.passive_branch_data.rates,
                                                     Yf=adm0.Yf,
                                                     Yt=adm0.Yt)

    (Sfb1, Stb1, If1, It1, Vbranch1,
     loading1, losses1) = short_circuit_post_process(calculation_inputs=nc,
                                                     V=V1,
                                                     branch_rates=nc.passive_branch_data.rates,
                                                     Yf=adm1.Yf,
                                                     Yt=adm1.Yt)

    (Sfb2, Stb2, If2, It2, Vbranch2,
     loading2, losses2) = short_circuit_post_process(calculation_inputs=nc,
                                                     V=V2,
                                                     branch_rates=nc.passive_branch_data.rates,
                                                     Yf=adm2.Yf,
                                                     Yt=adm2.Yt)

    # voltage, Sf, loading, losses, error, converged, Qpv
    results = ShortCircuitResults(
        nsc=1,
        n=nc.nbus,
        m=nc.nbr,
        n_hvdc=nc.nhvdc,
        n_vsc=nc.nvsc,
        bus_names=nc.bus_data.names,
        branch_names=nc.passive_branch_data.names,
        hvdc_names=nc.hvdc_data.names,
        vsc_names=nc.vsc_data.names,
        sc_names=np.array(["SC"]),
        bus_types=nc.bus_data.bus_types,
        area_names=None
    )

    results.SCpower[:, 0] = SCC
    results.ICurrent[:, 0] = ICC

    results.voltage0[:, 0] = V0
    results.Sf0[:, 0] = Sfb0  # in MVA already
    results.St0[:, 0] = Stb0  # in MVA already
    results.If0[:, 0] = If0  # in p.u.
    results.It0[:, 0] = It0  # in p.u.
    results.Vbranch0[:, 0] = Vbranch0
    results.loading0[:, 0] = loading0
    results.losses0[:, 0] = losses0

    results.voltage1[:, 0] = V1
    results.Sf1[:, 0] = Sfb1  # in MVA already
    results.St1[:, 0] = Stb1  # in MVA already
    results.If1[:, 0] = If1  # in p.u.
    results.It1[:, 0] = It1  # in p.u.
    results.Vbranch1[:, 0] = Vbranch1
    results.loading1[:, 0] = loading1
    results.losses1[:, 0] = losses1

    results.voltage2[:, 0] = V2
    results.Sf2[:, 0] = Sfb2  # in MVA already
    results.St2[:, 0] = Stb2  # in MVA already
    results.If2[:, 0] = If2  # in p.u.
    results.It2[:, 0] = It2  # in p.u.
    results.Vbranch2[:, 0] = Vbranch2
    results.loading2[:, 0] = loading2
    results.losses2[:, 0] = losses2

    return results


def maximum_initial_shortcircuit_current(nc: NumericalCircuit,
                                         Zf: complex,
                                         faulted_bus: int):
    """

    :param nc:
    :param Zf:
    :param faulted_bus:
    :return:
    """
    c_max = 1.1  # Voltage factor
    Un = nc.bus_data.Vnom[faulted_bus] * 1e3  # Nominal voltage [V]
    Zk = abs(Zf) * Un ** 2 / (nc.Sbase * 1e6)  # Fault impedance [Ohm]

    # Current contribution only from SGs
    Ik_max_PFO = 1 / Zk * c_max * Un / np.sqrt(3)
    Isk_PF = 0

    # Current contribution only from CIGs
    # sumatory
    # Isk_PF = 1/Zk * sumatory

    # Total current contribution
    Ik_max = Ik_max_PFO + Isk_PF

    return Ik_max


def short_circuit_abc(nc: NumericalCircuit,
                      voltage_N: CxVec,
                      voltage_A: CxVec,
                      voltage_B: CxVec,
                      voltage_C: CxVec,
                      Zf: CxVec,
                      bus_index: int,
                      fault_type: FaultType,
                      phases: PhasesShortCircuit,
                      Sbus_N: CxVec,
                      Sbus_A: CxVec,
                      Sbus_B: CxVec,
                      Sbus_C: CxVec,
                      ) -> ShortCircuitResults:
    """
    Run a short circuit simulation in the phase domain
    :param nc:
    :param Vpf: Power flow voltage vector applicable to the island
    :param Zf: Short circuit impedance vector applicable to the island
    :param bus_index: Index of the failed bus
    :param fault_type: FaultType
    :param Spf: Bus powers Sbus
    :param method: Method to solve the short-circuit, sequence or phase domain
    :param phases: Phases where the short-circuit occurs
    :return: short circuit results
    """
    # -----------------------------------------------------------------------------------------------------------------
    # Compute Ybus
    # -----------------------------------------------------------------------------------------------------------------
    Ybus_masked, Yf, Yt, Yshunt_bus, mask, bus_lookup, branch_lookup = compute_ybus(nc)

    # -----------------------------------------------------------------------------------------------------------------
    # Voltage and power results from the power flow simulation
    # -----------------------------------------------------------------------------------------------------------------
    Vpf = np.zeros(nc.nbus * 4, dtype=complex)
    Vpf[0::4] = voltage_N
    Vpf[1::4] = voltage_A
    Vpf[2::4] = voltage_B
    Vpf[3::4] = voltage_C
    Vpf_masked = Vpf[mask]

    Spf = np.zeros(nc.nbus * 4, dtype=complex)
    Spf[0::4] = Sbus_N
    Spf[1::4] = Sbus_A
    Spf[2::4] = Sbus_B
    Spf[3::4] = Sbus_C

    # -----------------------------------------------------------------------------------------------------------------
    # Linearised admittances of constant power and current loads
    # -----------------------------------------------------------------------------------------------------------------
    _, Y_power_linear, _ = compute_power_loads(bus_idx=nc.load_data.bus_idx,
                                               bus_lookup=bus_lookup,
                                               V=Vpf_masked,
                                               Sstar=nc.load_data.S3_star,
                                               Sfloating=nc.load_data.S3_floatingstar,
                                               Sdelta=nc.load_data.S3_delta)

    _, Y_current_linear, _ = compute_current_loads(bus_idx=nc.load_data.bus_idx,
                                                   bus_lookup=bus_lookup,
                                                   V=Vpf_masked,
                                                   Istar=nc.load_data.I3_star,
                                                   Ifloating=nc.load_data.I3_floatingstar,
                                                   Idelta=nc.load_data.I3_delta)

    Y_power_linear /= (nc.Sbase / 3)
    Y_current_linear /= (nc.Sbase / 3)

    Yloads_diags = sp.diags(Y_power_linear + Y_current_linear)

    Yloads = Y_power_linear + Y_current_linear
    Yloads_expanded = expand_magnitudes(Yloads, bus_lookup)

    # -----------------------------------------------------------------------------------------------------------------
    # Building the fault admittance matrix, depending on the short-circuit type and the phases involved
    # -----------------------------------------------------------------------------------------------------------------
    Yfault = np.zeros((len(Vpf), len(Vpf)), dtype=complex)
    a = 4 * bus_index + 1
    b = 4 * bus_index + 2
    c = 4 * bus_index + 3

    # Single Line-to-Ground (SLG)
    if fault_type == FaultType.LG:

        if phases == PhasesShortCircuit.a:
            Yfault[a, a] = 1 / (Zf[bus_index] + 1e-20)

        elif phases == PhasesShortCircuit.b:
            Yfault[b, b] = 1 / (Zf[bus_index] + 1e-20)

        elif phases == PhasesShortCircuit.c:
            Yfault[c, c] = 1 / (Zf[bus_index] + 1e-20)

    # Line-to-Line (LL)
    elif fault_type == FaultType.LL:

        if phases == PhasesShortCircuit.ab:

            Yfault[a, a] = 1 / (Zf[bus_index] + 1e-20)
            Yfault[a, b] = -1 / (Zf[bus_index] + 1e-20)
            Yfault[b, a] = -1 / (Zf[bus_index] + 1e-20)
            Yfault[b, b] = 1 / (Zf[bus_index] + 1e-20)

        elif phases == PhasesShortCircuit.bc:

            Yfault[b, b] = 1 / (Zf[bus_index] + 1e-20)
            Yfault[b, c] = -1 / (Zf[bus_index] + 1e-20)
            Yfault[c, b] = -1 / (Zf[bus_index] + 1e-20)
            Yfault[c, c] = 1 / (Zf[bus_index] + 1e-20)

        elif phases == PhasesShortCircuit.ca:

            Yfault[c, c] = 1 / (Zf[bus_index] + 1e-20)
            Yfault[c, a] = -1 / (Zf[bus_index] + 1e-20)
            Yfault[a, c] = -1 / (Zf[bus_index] + 1e-20)
            Yfault[a, a] = 1 / (Zf[bus_index] + 1e-20)

    # Double Line-to-Ground (DLG)
    elif fault_type == FaultType.LLG:

        if phases == PhasesShortCircuit.ab:
            Yfault[a, a] = 1 / (Zf[bus_index] + 1e-20)
            Yfault[b, b] = 1 / (Zf[bus_index] + 1e-20)

        elif phases == PhasesShortCircuit.bc:
            Yfault[b, b] = 1 / (Zf[bus_index] + 1e-20)
            Yfault[c, c] = 1 / (Zf[bus_index] + 1e-20)

        elif phases == PhasesShortCircuit.ca:
            Yfault[c, c] = 1 / (Zf[bus_index] + 1e-20)
            Yfault[a, a] = 1 / (Zf[bus_index] + 1e-20)

    # Three-Phase Fault (LLL)
    elif fault_type == FaultType.LLL:

        Yfault[a, a] = 2 / (Zf[bus_index] + 1e-20)
        Yfault[a, b] = -1 / (Zf[bus_index] + 1e-20)
        Yfault[a, c] = -1 / (Zf[bus_index] + 1e-20)

        Yfault[b, b] = 2 / (Zf[bus_index] + 1e-20)
        Yfault[b, a] = -1 / (Zf[bus_index] + 1e-20)
        Yfault[b, c] = -1 / (Zf[bus_index] + 1e-20)

        Yfault[c, c] = 2 / (Zf[bus_index] + 1e-20)
        Yfault[c, a] = -1 / (Zf[bus_index] + 1e-20)
        Yfault[c, b] = -1 / (Zf[bus_index] + 1e-20)

    # Three-Phase-to-Ground (LLLG)
    elif fault_type == FaultType.LLLG:

        Yfault[a, a] = 1 / (Zf[bus_index] + 1e-20)
        Yfault[b, b] = 1 / (Zf[bus_index] + 1e-20)
        Yfault[c, c] = 1 / (Zf[bus_index] + 1e-20)

    else:
        raise Exception('Incorrect fault type definition.')

    Yfault_masked = Yfault[mask, :][:, mask]
    Yfault_masked = sp.csc_matrix(Yfault_masked)

    # -----------------------------------------------------------------------------------------------------------------
    # Generators admittance matrix
    # -----------------------------------------------------------------------------------------------------------------
    Ygen = compute_ybus_generator(nc=nc)
    Ygen_masked = Ygen[mask, :][:, mask]

    # -----------------------------------------------------------------------------------------------------------------
    # Full linear admittance matrix
    # -----------------------------------------------------------------------------------------------------------------
    Ylinear_masked = Ybus_masked - Yloads_diags + Yfault_masked + Ygen_masked

    # -----------------------------------------------------------------------------------------------------------------
    # Generators Norton's current
    # -----------------------------------------------------------------------------------------------------------------
    S = (Spf / (nc.Sbase / 3)) - Vpf * np.conj(Yloads_expanded * Vpf)

    idx4 = np.array([1, 2, 3])
    idx3 = np.array([0, 1, 2])

    gen_idx = nc.generator_data.bus_idx
    n_buses = len(nc.generator_data.bus_idx)

    Inorton = np.zeros(shape=len(Vpf_masked), dtype=complex)

    for i in range(n_buses):
        U = Vpf[gen_idx[i] + idx4]
        Y = Ygen[np.ix_(gen_idx[i] + idx4, gen_idx[i] + idx4)]
        I = np.conj(S[np.ix_(gen_idx[i] + idx4)] / U)
        E = U + np.linalg.solve(Y.toarray(), I)
        Inorton_i = Y @ E
        Inorton[np.ix_(gen_idx[i] + idx3)] = Inorton_i

    # -----------------------------------------------------------------------------------------------------------------
    # Short-circuit voltage
    # -----------------------------------------------------------------------------------------------------------------
    Usc = spsolve(Ylinear_masked, Inorton)
    Usc_expanded = expand_magnitudes(Usc, bus_lookup)

    # -----------------------------------------------------------------------------------------------------------------
    # Load-Flow-Based Calculation of Initial Short-Circuit Currents for Converter-Based Power System
    # -----------------------------------------------------------------------------------------------------------------
    Ik_max = maximum_initial_shortcircuit_current(
        nc=nc,
        Zf=Zf[bus_index],
        faulted_bus=bus_index
    )

    # -----------------------------------------------------------------------------------------------------------------
    # Saving Results
    # -----------------------------------------------------------------------------------------------------------------

    # voltage, Sf, loading, losses, error, converged, Qpv
    results = ShortCircuitResults(
        nsc=1,
        n=nc.nbus,
        m=nc.nbr,
        n_hvdc=nc.nhvdc,
        n_vsc=nc.nvsc,
        bus_names=nc.bus_data.names,
        branch_names=nc.passive_branch_data.names,
        hvdc_names=nc.hvdc_data.names,
        vsc_names=nc.vsc_data.names,
        sc_names=np.array(["SC"]),
        bus_types=nc.bus_data.bus_types,
        area_names=None
    )

    Sfb, Stb, If, It, Vbranch, loading, losses = short_circuit_post_process_phases_abc(
        calculation_inputs=nc,
        V_expanded=Usc_expanded,
        branch_rates_expanded=expand3ph(nc.passive_branch_data.rates),
        Yf=Yf,
        Yt=Yt,
        F_expanded=expand_indices_3ph(nc.passive_branch_data.F),
        T_expanded=expand_indices_3ph(nc.passive_branch_data.T),
        mask=mask,
        branch_lookup=branch_lookup
    )

    results.voltageN[:, 0] = Usc_expanded[0::4]
    results.SfA[:, 0] = Sfb[0::4]  # in MVA already
    results.StA[:, 0] = Stb[0::4]  # in MVA already
    results.IfA[:, 0] = If[0::4]  # in p.u.
    results.ItA[:, 0] = It[0::4]  # in p.u.
    results.VbranchA[:, 0] = Vbranch[0::4]
    results.loadingA[:, 0] = loading[0::4]
    results.lossesA[:, 0] = losses[0::4]

    results.voltageA[:, 0] = Usc_expanded[1::4]
    results.SfA[:, 0] = Sfb[1::4]  # in MVA already
    results.StA[:, 0] = Stb[1::4]  # in MVA already
    results.IfA[:, 0] = If[1::4]  # in p.u.
    results.ItA[:, 0] = It[1::4]  # in p.u.
    results.VbranchA[:, 0] = Vbranch[1::4]
    results.loadingA[:, 0] = loading[1::4]
    results.lossesA[:, 0] = losses[1::4]

    results.voltageB[:, 0] = Usc_expanded[2::4]
    results.SfB[:, 0] = Sfb[2::4]  # in MVA already
    results.StB[:, 0] = Stb[2::4]  # in MVA already
    results.IfB[:, 0] = If[2::4]  # in p.u.
    results.ItB[:, 0] = It[2::4]  # in p.u.
    results.VbranchB[:, 0] = Vbranch[2::4]
    results.loadingB[:, 0] = loading[2::4]
    results.lossesB[:, 0] = losses[2::4]

    results.voltageC[:, 0] = Usc_expanded[3::4]
    results.SfC[:, 0] = Sfb[3::4]  # in MVA already
    results.StC[:, 0] = Stb[3::4]  # in MVA already
    results.IfC[:, 0] = If[3::4]  # in p.u.
    results.ItC[:, 0] = It[3::4]  # in p.u.
    results.VbranchC[:, 0] = Vbranch[3::4]
    results.loadingC[:, 0] = loading[3::4]
    results.lossesC[:, 0] = losses[3::4]

    return results


def short_circuit_vsc(nc: NumericalCircuit,
                      V_pf: CxVec,
                      S_pf: CxVec,
                      Z_fault: CxVec,
                      fault_bus: int,
                      options: PowerFlowOptions,
                      logger: Logger):

    if logger is None:
        logger = Logger()

    # declare results
    pf_results = PowerFlowResults(
        n=nc.nbus,
        m=nc.nbr,
        n_hvdc=nc.nhvdc,
        n_vsc=nc.nvsc,
        n_gen=nc.ngen,
        n_batt=nc.nbatt,
        n_sh=nc.nshunt,
        bus_names=nc.bus_data.names,
        branch_names=nc.passive_branch_data.names,
        hvdc_names=nc.hvdc_data.names,
        vsc_names=nc.vsc_data.names,
        gen_names=nc.generator_data.names,
        batt_names=nc.battery_data.names,
        sh_names=nc.shunt_data.names,
        bus_types=nc.bus_data.bus_types,
    )

    # Disable voltage magnitude and angle control for all generators during short-circuit
    bus_gen_idx = nc.generator_data.bus_idx
    
    original_is_vm_controlled = nc.bus_data.is_vm_controlled[bus_gen_idx].copy()
    original_is_va_controlled = nc.bus_data.is_va_controlled[bus_gen_idx].copy()
    original_is_p_controlled = nc.bus_data.is_p_controlled[bus_gen_idx].copy()
    original_is_q_controlled = nc.bus_data.is_q_controlled[bus_gen_idx].copy()

    for gen in bus_gen_idx:

        if nc.bus_data.is_dc[gen] == False:
            nc.bus_data.is_vm_controlled[gen] = False
            nc.bus_data.is_va_controlled[gen] = False
            nc.bus_data.is_p_controlled[gen] = True
            nc.bus_data.is_q_controlled[gen] = True

    # compute islands
    islands = nc.split_into_islands(ignore_single_node_islands=options.ignore_single_node_islands,
                                    consider_hvdc_as_island_links=True,
                                    logger=logger)

    for i, island in enumerate(islands):

        indices = island.get_simulation_indices()

        Qmax, Qmin = island.get_reactive_power_limits()

        S0 = island.get_power_injections_pu()
        I0 = island.get_current_injections_pu()
        Y0 = island.get_admittance_injections_pu()

        nbus = nc.nbus

        S0_linear = np.zeros(shape=nbus, dtype=complex)
        S0_non_gen = S0 - nc.generator_data.get_injections_per_bus() / nc.Sbase
        S0_gen = S_pf / nc.Sbase - S0_non_gen - I0 + Y0

        Yfault = np.zeros(shape=nbus, dtype=complex)
        Yfault[fault_bus] = 1 / Z_fault[fault_bus]

        Ygen = np.zeros(shape=nbus, dtype=complex)
        gen_idx = nc.generator_data.original_idx
        for gen_i in range(len(gen_idx)):
            Ygen[bus_gen_idx[gen_i]] += 1 / (nc.generator_data.r1[gen_i] + 1j * nc.generator_data.x1[gen_i])

        Y0_linear = - np.conj(S0_non_gen / (np.conj(V_pf) * V_pf)) - I0 / V_pf + Y0 + Ygen + Yfault

        I0_linear = np.zeros(shape=nbus, dtype=complex) # Add generator's norton
        for gen_i in range(len(bus_gen_idx)):
            Ugen = V_pf[bus_gen_idx[gen_i]]
            Sgen = S0_gen[bus_gen_idx[gen_i]]
            Igen = np.conj(Sgen / Ugen)
            Egen = Ugen + Igen / Ygen[bus_gen_idx[gen_i]]
            I0_linear[bus_gen_idx[gen_i]] += Ygen[bus_gen_idx[gen_i]] * Egen

        if len(indices.vd) > 0:

            problem = PfAcDcWithNegativePoles(V0=V_pf,
                                              S0=S0_linear,
                                              I0=I0_linear,
                                              Y0=Y0_linear,
                                              Qmin=Qmin,
                                              Qmax=Qmax,
                                              nc=nc,
                                              options=options,
                                              logger=logger)

            solution = newton_raphson_fx(problem=problem,
                                         tol=options.tolerance,
                                         max_iter=options.max_iter,
                                         trust=options.trust_radius,
                                         verbose=options.verbose,
                                         logger=logger)

            # merge the results from this island
            pf_results.apply_from_island(
                results=solution,
                b_idx=island.bus_data.original_idx,
                br_idx=island.passive_branch_data.original_idx,
                hvdc_idx=island.hvdc_data.original_idx,
                vsc_idx=island.vsc_data.original_idx
            )

        else:
            logger.add_info('No slack nodes in the island', str(i))

    # voltage, Sf, loading, losses, error, converged, Qpv
    sc_results = ShortCircuitResults(
        nsc=1,
        n=nc.nbus,
        m=nc.nbr,
        n_hvdc=nc.nhvdc,
        n_vsc=nc.nvsc,
        bus_names=nc.bus_data.names,
        branch_names=nc.passive_branch_data.names,
        hvdc_names=nc.hvdc_data.names,
        vsc_names=nc.vsc_data.names,
        sc_names=np.array(["SC"]),
        bus_types=nc.bus_data.bus_types,
        area_names=None
    )

    sc_results.SCpower[:, 0] = pf_results.voltage[fault_bus] * pf_results.voltage[fault_bus] * Yfault[fault_bus]
    sc_results.ICurrent[:, 0] = pf_results.voltage[fault_bus] * Yfault[fault_bus]

    sc_results.Sbus1[:, 0] = nc.get_power_injections_pu() * nc.Sbase  # MVA
    sc_results.voltage1[:, 0] = pf_results.voltage
    sc_results.Sf1[:, 0] = pf_results.Sf  # in MVA already
    sc_results.St1[:, 0] = pf_results.St  # in MVA already
    sc_results.If1[:, 0] = pf_results.If  # in p.u.
    sc_results.It1[:, 0] = pf_results.It  # in p.u.
    sc_results.Vbranch1[:, 0] = pf_results.Vbranch
    sc_results.loading1[:, 0] = pf_results.loading
    sc_results.losses1[:, 0] = pf_results.losses

    sc_results.hvdc_losses[:, 0] = pf_results.losses_hvdc
    sc_results.hvdc_Pf[:, 0] = pf_results.Pf_hvdc
    sc_results.hvdc_Pt[:, 0] = pf_results.Pt_hvdc
    sc_results.hvdc_loading[:, 0] = pf_results.loading_hvdc

    sc_results.vsc_Pfp[:, 0] = pf_results.Pfp_vsc  # in MVA already
    sc_results.vsc_Pfn[:, 0] = pf_results.Pfn_vsc  # in MVA already
    sc_results.vsc_St[:, 0] = pf_results.St_vsc  # in MVA already
    sc_results.vsc_If[:, 0] = pf_results.If_vsc  # in p.u.
    sc_results.vsc_It[:, 0] = pf_results.It_vsc  # in p.u.
    sc_results.vsc_losses[:, 0] = pf_results.losses_vsc # in MVA already
    sc_results.vsc_loading[:, 0] = pf_results.loading_vsc

    # Restore original generator control flags
    nc.bus_data.is_vm_controlled[bus_gen_idx] = original_is_vm_controlled
    nc.bus_data.is_va_controlled[bus_gen_idx] = original_is_va_controlled
    nc.bus_data.is_p_controlled[bus_gen_idx] = original_is_p_controlled
    nc.bus_data.is_q_controlled[bus_gen_idx] = original_is_q_controlled

    return sc_results