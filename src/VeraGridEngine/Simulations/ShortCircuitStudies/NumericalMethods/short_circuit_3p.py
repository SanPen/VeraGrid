# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Tuple
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit_results import ShortCircuitResults
from VeraGridEngine.enumerations import FaultType, PhasesShortCircuit
from VeraGridEngine.basic_structures import CxVec, Vec, IntVec
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.pf_basic_formulation_3ph import (compute_ybus,
                                                                                           compute_current_loads,
                                                                                           compute_power_loads,
                                                                                           compute_ybus_generator,
                                                                                           expand_magnitudes,
                                                                                           expand_indices_3ph,
                                                                                           expand3ph)

from VeraGridEngine.basic_structures import Logger


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
                      Sbus_C: CxVec) -> ShortCircuitResults:
    """
    Run a short circuit simulation in the phase domain
    :param nc:
    :param voltage_N: Power flow voltage vector applicable to the island
    :param voltage_A: Power flow voltage vector applicable to the island
    :param voltage_B: Power flow voltage vector applicable to the island
    :param voltage_C: Power flow voltage vector applicable to the island
    :param Zf: Short circuit impedance vector applicable to the island
    :param bus_index: Index of the failed bus
    :param fault_type: FaultType
    :param Sbus_N: Bus powers Sbus
    :param Sbus_A: Bus powers Sbus
    :param Sbus_B: Bus powers Sbus
    :param Sbus_C: Bus powers Sbus
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

    idx4: IntVec = np.array([1, 2, 3])
    gen_idx: IntVec = nc.generator_data.bus_idx
    n_buses: int = len(gen_idx)
    Inorton: CxVec = np.zeros(shape=len(Vpf_masked), dtype=complex)

    for i in range(n_buses):
        # NABC indices use four entries per bus, then the phase-presence mask.
        phase_idx: IntVec = 4 * gen_idx[i] + idx4
        U: CxVec = Vpf[phase_idx]
        Y: sp.csc_matrix = Ygen[np.ix_(phase_idx, phase_idx)]
        I: CxVec = np.conj(S[phase_idx] / U)
        E: CxVec = U + spsolve(Y, I)
        Inorton_i: CxVec = Y @ E
        Inorton[bus_lookup[phase_idx]] = Inorton_i

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
