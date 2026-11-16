# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import numba as nb

import scipy.sparse as sp
from typing import Tuple
from scipy.sparse import csc_matrix
from VeraGridEngine.basic_structures import CxVec, Vec, IntVec, Logger
from VeraGridEngine.Utils.Sparse.sparse_solve import safe_spsolve
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_full_acdc_with_negative_poles_sc import \
    PfAcDcWithNegativePolesSc
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.newton_raphson_fx import newton_raphson_fx
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import (
    compute_asynchronous_generator_q, polar_to_rect
)
from VeraGridEngine.enumerations import FaultType, ConverterControlType, GeneratorType, WindingType
from VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit_results import ShortCircuitResults
from VeraGridEngine.Topology.admittance_matrices import AdmittanceMatrices


@nb.njit(cache=True)
def compute_zero_sequence_series_admittances(ys: CxVec,
                                             conn_f: IntVec,
                                             conn_t: IntVec,
                                             neutral_star: int,
                                             floating_star: int,
                                             grounded_star: int,
                                             delta: int,
                                             neutral_zigzag: int,
                                             floating_zigzag: int,
                                             grounded_zigzag: int) -> tuple[CxVec, CxVec, CxVec]:
    """Build the terminal and mutual zero-sequence series admittances.

    :param ys: Branch series admittances.
    :param conn_f: From-side winding connection codes.
    :param conn_t: To-side winding connection codes.
    :param neutral_star: Neutral-star code.
    :param floating_star: Floating-star code.
    :param grounded_star: Grounded-star code.
    :param delta: Delta code.
    :param neutral_zigzag: Neutral-zig-zag code.
    :param floating_zigzag: Floating-zig-zag code.
    :param grounded_zigzag: Grounded-zig-zag code.
    :return: From self, to self, and mutual zero-sequence series admittances.
    """
    ysf: CxVec = np.zeros(ys.size, dtype=np.complex128)
    yst: CxVec = np.zeros(ys.size, dtype=np.complex128)
    ysft: CxVec = np.zeros(ys.size, dtype=np.complex128)

    branch_index: int
    for branch_index in range(ys.size):
        from_connection: int = conn_f[branch_index]
        to_connection: int = conn_t[branch_index]

        # A grounded star and every zig-zag label use the grounded zig-zag I0 primitive.
        if from_connection == grounded_star:
            from_grounded: bool = True
        elif from_connection == neutral_zigzag:
            from_grounded = True
        elif from_connection == floating_zigzag:
            from_grounded = True
        elif from_connection == grounded_zigzag:
            from_grounded = True
        elif from_connection == neutral_star:
            from_grounded = False
        elif from_connection == floating_star:
            from_grounded = False
        elif from_connection == delta:
            from_grounded = False
        else:
            from_grounded = False

        # Apply exactly the same canonical model to the to terminal independently.
        if to_connection == grounded_star:
            to_grounded: bool = True
        elif to_connection == neutral_zigzag:
            to_grounded = True
        elif to_connection == floating_zigzag:
            to_grounded = True
        elif to_connection == grounded_zigzag:
            to_grounded = True
        elif to_connection == neutral_star:
            to_grounded = False
        elif to_connection == floating_star:
            to_grounded = False
        elif to_connection == delta:
            to_grounded = False
        else:
            to_grounded = False

        # A grounded terminal sees the leakage path; both terminals need it for branch coupling.
        if from_grounded:
            ysf[branch_index] = ys[branch_index]
        else:
            pass
        if to_grounded:
            yst[branch_index] = ys[branch_index]
        else:
            pass
        if from_grounded and to_grounded:
            ysft[branch_index] = ys[branch_index]
        else:
            pass

    return ysf, yst, ysft


def compute_admittances_seq(R: Vec,
                            X: Vec,
                            G: Vec,
                            B: Vec,
                            tap_module: Vec,
                            vtap_f: Vec,
                            vtap_t: Vec,
                            tap_angle: Vec,
                            Cf: sp.csc_matrix,
                            Ct: sp.csc_matrix,
                            Yshunt_bus: CxVec,
                            conn_f: IntVec,
                            conn_t: IntVec,
                            vector_group_number: IntVec,
                            seq: int,) -> AdmittanceMatrices:
    """
    Compute the complete admittance matrices for the general power flow methods (Newton-Raphson based)

    :param R: array of branch resistance (p.u.)
    :param X: array of branch reactance (p.u.)
    :param G: array of branch conductance (p.u.)
    :param B: array of branch susceptance (p.u.)
    :param tap_module: array of tap modules (for all Branches, regardless of their type)
    :param vtap_f: array of virtual taps at the "from" side
    :param vtap_t: array of virtual taps at the "to" side
    :param tap_angle: array of tap angles (for all Branches, regardless of their type)
    :param Cf: Connectivity branch-bus "from" with the branch states computed
    :param Ct: Connectivity branch-bus "to" with the branch states computed
    :param Yshunt_bus: array of shunts equivalent power per bus, from the shunt devices (p.u.)
    :param seq: Sequence [0, 1, 2]
    :param conn_f: array of from-side winding connection codes
    :param conn_t: array of to-side winding connection codes
    :param vector_group_number: transformer clock number from the from side to the to side
    :return: Admittance instance
    """
    # form the admittance matrices
    ys = 1.0 / (R + 1.0j * (X + 1e-20))  # series admittance
    ysh_2 = (G + 1j * B) / 2.0  # shunt admittance

    # Clock rotation belongs to symmetrical components; tap_angle remains the physical phase shifter.
    clock_rotation = np.exp(1.0j * np.pi * vector_group_number / 6.0)

    if seq == 0:  # zero sequence
        # The Numba kernel documents and classifies every winding state per branch.
        ysf, yst, ysft = compute_zero_sequence_series_admittances(
            ys=ys,
            conn_f=conn_f,
            conn_t=conn_t,
            neutral_star=WindingType.NeutralStar.idx(),
            floating_star=WindingType.FloatingStar.idx(),
            grounded_star=WindingType.GroundedStar.idx(),
            delta=WindingType.Delta.idx(),
            neutral_zigzag=WindingType.NeutralZigZag.idx(),
            floating_zigzag=WindingType.FloatingZigZag.idx(),
            grounded_zigzag=WindingType.GroundedZigZag.idx(),
        )

        yff = (ysf + ysh_2) / (tap_module * tap_module * vtap_f * vtap_f)
        yft = -ysft / (tap_module * np.exp(-1.0j * tap_angle) * vtap_f * vtap_t)
        ytf = -ysft / (tap_module * np.exp(+1.0j * tap_angle) * vtap_t * vtap_f)
        ytt = (yst + ysh_2) / (vtap_t * vtap_t)

    elif seq == 2:  # negative sequence
        # Negative sequence rotates opposite to positive sequence through the transformer clock.
        yff = (ys + ysh_2) / (tap_module * tap_module * vtap_f * vtap_f)
        yft = -ys / (tap_module * np.exp(+1.0j * tap_angle) * vtap_f * vtap_t) * np.conj(clock_rotation)
        ytf = -ys / (tap_module * np.exp(-1.0j * tap_angle) * vtap_t * vtap_f) * clock_rotation
        ytt = (ys + ysh_2) / (vtap_t * vtap_t)

    elif seq == 1:  # positive sequence
        # Positive sequence follows the signed clock stored in the compiled branch direction.
        yff = (ys + ysh_2) / (tap_module * tap_module * vtap_f * vtap_f)
        yft = -ys / (tap_module * np.exp(-1.0j * tap_angle) * vtap_f * vtap_t) * clock_rotation
        ytf = -ys / (tap_module * np.exp(1.0j * tap_angle) * vtap_t * vtap_f) * np.conj(clock_rotation)
        ytt = (ys + ysh_2) / (vtap_t * vtap_t)
    else:
        raise Exception('Unsupported sequence when computing the admittance matrix sequence={}'.format(seq))


    # compose the matrices
    Yf = sp.diags(yff) * Cf + sp.diags(yft) * Ct
    Yt = sp.diags(ytf) * Cf + sp.diags(ytt) * Ct
    Ybus = Cf.T * Yf + Ct.T * Yt + sp.diags(Yshunt_bus)

    return AdmittanceMatrices(Ybus.tocsc(), Yf.tocsc(), Yt.tocsc(), Cf.tocsc(), Ct.tocsc(),
                              yff, yft, ytf, ytt, Yshunt_bus)


def calc_short_circuit_seq_3p(bus_idx: int,
                              Ybus: csc_matrix,
                              Vbus: CxVec,
                              Vnom: Vec,
                              Zf: CxVec,
                              baseMVA: float,
                              logger: Logger | None = None) -> Tuple[CxVec, CxVec, CxVec]:
    """
    Executes a 3-phase balanced short circuit study
    :param bus_idx: Index of the bus at which the short circuit is being studied
    :param Ybus: Admittance matrix
    :param Vbus: Voltages of the buses in the steady state
    :param Vnom: Nominal Voltages of the buses (kV)
    :param Zf: Fault impedance array
    :param baseMVA: Circuit base power (100 MVA)
    :param logger: Logger object (optional)
    :return: Voltages after the short circuit (p.u.), Short circuit power in MVA
    Computed as V = Vpre + V increment, where Vpre is the power flow solution and
    V increment is the fault contribution
    The short-circuit power is V_i^2 / Z[i,i], it will tend to infinity if the
    generator is ideal (r1 and x1 approach 0)
    """

    n = len(Vbus)

    if abs(Zf[bus_idx]) == 0.0:
        if logger is not None:
            logger.add_error(msg="Short-circuit fault impedance is zero",
                             device="3-phase fault",
                             value=Zf[bus_idx],
                             expected_value="Non-zero fault impedance")
        else:
            pass
        return Vbus.copy(), np.zeros(n, dtype=complex), np.zeros(n, dtype=complex)
    else:
        pass

    tmp = np.zeros(n)
    tmp[bus_idx] = 1
    Zcol = safe_spsolve(system_matrix=Ybus,
                        rhs=tmp,
                        logger=logger,
                        context="3-phase Thevenin impedance",
                        fault_impedance=Zf[bus_idx])
    if Zcol is None:
        return Vbus.copy(), np.zeros(n, dtype=complex), np.zeros(n, dtype=complex)
    else:
        pass

    Zii = Zcol[bus_idx]
    fault_denominator = Zii + Zf[bus_idx]

    if not np.isfinite(fault_denominator) or abs(fault_denominator) == 0.0:
        if logger is not None:
            logger.add_error(msg="Invalid short-circuit fault impedance",
                             device="3-phase fault",
                             value=Zf[bus_idx],
                             expected_value="Non-zero finite Thevenin plus fault impedance")
        else:
            pass
        return Vbus.copy(), np.zeros(n, dtype=complex), np.zeros(n, dtype=complex)
    else:
        pass

    Ifvec = np.zeros(n, dtype=complex)
    Ifvec[bus_idx] = Vbus[bus_idx] / fault_denominator

    Av_col = safe_spsolve(system_matrix=Ybus,
                          rhs=Ifvec,
                          logger=logger,
                          context="3-phase voltage increment",
                          fault_impedance=Zf[bus_idx])
    if Av_col is None:
        return Vbus.copy(), np.zeros(n, dtype=complex), np.zeros(n, dtype=complex)
    else:
        pass

    Av = - Av_col
    V = Vbus + Av

    idx_buses = range(n)
    Ibase = baseMVA / Vnom[idx_buses]
    if not np.isfinite(Zii) or abs(Zii) == 0.0:
        ICC = np.zeros(n, dtype=complex)
        SCC = np.zeros(n, dtype=complex)
        if logger is not None:
            logger.add_error(msg="Invalid short-circuit Thevenin impedance",
                             device="3-phase fault",
                             value=Zii,
                             expected_value="Non-zero finite impedance")
        else:
            pass
    else:
        ICC = Ibase * Vbus[idx_buses] / Zii
        SCC = baseMVA * Vbus[idx_buses] * Vbus[idx_buses] / Zii

    return V, SCC, ICC


def calc_short_circuit_seq_unbalanced(bus_idx: int,
                                      Y0: csc_matrix,
                                      Y1: csc_matrix,
                                      Y2: csc_matrix,
                                      Vbus: CxVec,
                                      Vnom: Vec,
                                      Zf: CxVec,
                                      fault_type: FaultType,
                                      baseMVA: float,
                                      logger: Logger | None = None) -> Tuple[CxVec, CxVec, CxVec, CxVec, CxVec]:
    """
    Executes the unbalanced short circuits (LG, LL, LLG types)

    :param bus_idx: bus where the fault is caused
    :param Y0: Admittance matrix for the zero sequence
    :param Y1: Admittance matrix for the positive sequence
    :param Y2: Admittance matrix for the negative sequence
    :param Vbus: pre-fault voltage (positive sequence)
    :param Vnom: nominal voltage (kV)
    :param Zf: fault impedance
    :param fault_type: type of unbalanced fault
    :param baseMVA: base MVA (100 MVA)
    :param logger: Logger (optional)
    :return: V0, V1, V2 for all buses
    """

    n = len(Vbus)

    # solve the fault
    Vpr = Vbus[bus_idx]

    tmp = np.zeros(n)
    tmp[bus_idx] = 1
    Zflt = Zf[bus_idx]
    fallback_v0 = np.zeros(n, dtype=complex)
    fallback_v1 = Vbus.copy()
    fallback_v2 = np.zeros(n, dtype=complex)
    fallback_power = np.zeros_like(Vbus)

    if abs(Zflt) == 0.0:
        if logger is not None:
            logger.add_error(msg="Short-circuit fault impedance is zero",
                             device=fault_type.value,
                             value=Zflt,
                             expected_value="Non-zero fault impedance")
        else:
            pass
        return fallback_v0, fallback_v1, fallback_v2, fallback_power, fallback_power
    else:
        pass

    Zth0_col = safe_spsolve(system_matrix=Y0,
                            rhs=tmp,
                            logger=logger,
                            context="zero-sequence Thevenin impedance",
                            fault_impedance=Zflt)
    Zth1_col = safe_spsolve(system_matrix=Y1,
                            rhs=tmp,
                            logger=logger,
                            context="positive-sequence Thevenin impedance",
                            fault_impedance=Zflt)
    Zth2_col = safe_spsolve(system_matrix=Y2,
                            rhs=tmp,
                            logger=logger,
                            context="negative-sequence Thevenin impedance",
                            fault_impedance=Zflt)

    if Zth0_col is None or Zth1_col is None or Zth2_col is None:
        return fallback_v0, fallback_v1, fallback_v2, fallback_power, fallback_power
    else:
        pass

    Zth0 = Zth0_col[bus_idx]
    Zth1 = Zth1_col[bus_idx]
    Zth2 = Zth2_col[bus_idx]

    if fault_type == FaultType.LG:
        denominator = Zth0 + Zth1 + Zth2 + 3 * Zflt
        if not np.isfinite(denominator) or abs(denominator) == 0.0:
            if logger is not None:
                logger.add_error(msg="Invalid short-circuit fault impedance",
                                 device=fault_type.value,
                                 value=Zflt,
                                 expected_value="Non-zero finite sequence fault denominator")
            else:
                pass
            return fallback_v0, fallback_v1, fallback_v2, fallback_power, fallback_power
        else:
            pass
        I0 = Vpr / denominator
        I1 = I0
        I2 = I0
    elif fault_type == FaultType.LL:  # between phases b and c
        I0 = 0
        denominator = Zth1 + Zth2 + Zflt
        if not np.isfinite(denominator) or abs(denominator) == 0.0:
            if logger is not None:
                logger.add_error(msg="Invalid short-circuit fault impedance",
                                 device=fault_type.value,
                                 value=Zflt,
                                 expected_value="Non-zero finite sequence fault denominator")
            else:
                pass
            return fallback_v0, fallback_v1, fallback_v2, fallback_power, fallback_power
        else:
            pass
        I1 = Vpr / denominator
        I2 = - I1
    elif fault_type == FaultType.LLG:  # between phases b and c
        shunt_denominator = Zth2 + Zth0 + 3 * Zflt
        if not np.isfinite(shunt_denominator) or abs(shunt_denominator) == 0.0:
            if logger is not None:
                logger.add_error(msg="Invalid short-circuit fault impedance",
                                 device=fault_type.value,
                                 value=Zflt,
                                 expected_value="Non-zero finite sequence fault denominator")
            else:
                pass
            return fallback_v0, fallback_v1, fallback_v2, fallback_power, fallback_power
        else:
            pass

        denominator = Zth1 + Zth2 * (Zth0 + 3 * Zflt) / shunt_denominator
        if not np.isfinite(denominator) or abs(denominator) == 0.0:
            if logger is not None:
                logger.add_error(msg="Invalid short-circuit fault impedance",
                                 device=fault_type.value,
                                 value=Zflt,
                                 expected_value="Non-zero finite sequence fault denominator")
            else:
                pass
            return fallback_v0, fallback_v1, fallback_v2, fallback_power, fallback_power
        else:
            pass

        I1 = Vpr / denominator
        I0 = -I1 * Zth2 / shunt_denominator
        I2 = -I1 * (Zth0 + 3 * Zflt) / shunt_denominator
    else:
        raise Exception('Unknown unbalanced fault type')

    # obtain the post fault voltages
    I0_vec = np.zeros(n, dtype=complex)
    I1_vec = np.zeros(n, dtype=complex)
    I2_vec = np.zeros(n, dtype=complex)

    I0_vec[bus_idx] = I0
    I1_vec[bus_idx] = I1
    I2_vec[bus_idx] = I2

    V0_col = safe_spsolve(system_matrix=Y0,
                          rhs=I0_vec,
                          logger=logger,
                          context="zero-sequence post-fault voltage",
                          fault_impedance=Zflt)
    V1_col = safe_spsolve(system_matrix=Y1,
                          rhs=I1_vec,
                          logger=logger,
                          context="positive-sequence post-fault voltage",
                          fault_impedance=Zflt)
    V2_col = safe_spsolve(system_matrix=Y2,
                          rhs=I2_vec,
                          logger=logger,
                          context="negative-sequence post-fault voltage",
                          fault_impedance=Zflt)

    if V0_col is None or V1_col is None or V2_col is None:
        return fallback_v0, fallback_v1, fallback_v2, fallback_power, fallback_power
    else:
        pass

    V0_fin = - V0_col
    V1_fin = Vbus - V1_col
    V2_fin = - V2_col

    SCC = np.zeros_like(Vbus)
    ICC = np.zeros_like(Vbus)
    Ibase = baseMVA / Vnom[bus_idx]
    if not np.isfinite(Zth1) or abs(Zth1) == 0.0:
        if logger is not None:
            logger.add_error(msg="Invalid short-circuit Thevenin impedance",
                             device=fault_type.value,
                             value=Zth1,
                             expected_value="Non-zero finite impedance")
        else:
            pass
    else:
        ICC[bus_idx] = Ibase * V1_fin[bus_idx] / Zth1
        SCC[bus_idx] = baseMVA * V1_fin[bus_idx] * V1_fin[bus_idx] / Zth1

    return V0_fin, V1_fin, V2_fin, SCC, ICC


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


def short_circuit_ph3(nc: NumericalCircuit,
                      Vpf: CxVec,
                      Zf: CxVec,
                      bus_index: int,
                      logger: Logger | None = None) -> ShortCircuitResults:
    """
    Run a 3-phase short circuit simulation for a single island
    :param nc: NumericalCircuit
    :param Vpf: Power flow voltage vector applicable to the island
    :param Zf: Short circuit impedance vector applicable to the island
    :param bus_index: Bus index
    :param logger: Logger
    :return: short circuit results
    """
    adm = nc.get_admittance_matrices()
    Y_gen = nc.generator_data.get_Yshunt(seq=1)
    Y_batt = nc.battery_data.get_Yshunt(seq=1)
    Ybus_gen_batt = adm.Ybus + sp.diags(Y_gen) + sp.diags(Y_batt)

    # Compute the short circuit
    V, SCpower, ICurrent = calc_short_circuit_seq_3p(bus_idx=bus_index,
                                                     Ybus=Ybus_gen_batt,
                                                     Vbus=Vpf,
                                                     Vnom=nc.bus_data.Vnom,
                                                     Zf=Zf,
                                                     baseMVA=nc.Sbase,
                                                     logger=logger)

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
                             fault_type: FaultType,
                             logger: Logger | None = None) -> ShortCircuitResults:
    """
    Run an unbalanced short circuit simulation for a single island
    :param nc:
    :param Vpf: Power flow voltage vector applicable to the island
    :param Zf: Short circuit impedance vector applicable to the island
    :param bus_index: Index of the failed bus
    :param fault_type: FaultType
    :param logger: Logger object
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

    adm0 = compute_admittances_seq(R=nc.passive_branch_data.R0,
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
                                   conn_f=nc.passive_branch_data.conn_f,
                                   conn_t=nc.passive_branch_data.conn_t,
                                   vector_group_number=nc.passive_branch_data.vector_group_number,
                                   seq=0)

    Y_gen1 = nc.generator_data.get_Yshunt(seq=1)
    Y_batt1 = nc.battery_data.get_Yshunt(seq=1)
    Yshunt_bus1 = nc.get_Yshunt_bus_pu() + Y_gen1 + Y_batt1

    adm1 = compute_admittances_seq(R=nc.passive_branch_data.R,
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
                                   conn_f=nc.passive_branch_data.conn_f,
                                   conn_t=nc.passive_branch_data.conn_t,
                                   vector_group_number=nc.passive_branch_data.vector_group_number,
                                   seq=1)

    Y_gen2 = nc.generator_data.get_Yshunt(seq=2)
    Y_batt2 = nc.battery_data.get_Yshunt(seq=2)
    Yshunt_bus2 = Y_gen2 + Y_batt2

    adm2 = compute_admittances_seq(R=nc.passive_branch_data.R2,
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
                                   conn_f=nc.passive_branch_data.conn_f,
                                   conn_t=nc.passive_branch_data.conn_t,
                                   vector_group_number=nc.passive_branch_data.vector_group_number,
                                   seq=2)

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

    adm_series = compute_admittances_seq(R=nc.passive_branch_data.R,
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
                                         conn_f=nc.passive_branch_data.conn_f,
                                         conn_t=nc.passive_branch_data.conn_t,
                                         vector_group_number=nc.passive_branch_data.vector_group_number,
                                         seq=1)

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
    V0, V1, V2, SCC, ICC = calc_short_circuit_seq_unbalanced(bus_idx=bus_index,
                                                             Y0=adm0.Ybus,
                                                             Y1=adm1.Ybus,
                                                             Y2=adm2.Ybus,
                                                             Vnom=nc.bus_data.Vnom,
                                                             Vbus=Vpf,
                                                             Zf=Zf,
                                                             fault_type=fault_type,
                                                             baseMVA=nc.Sbase,
                                                             logger=logger)

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


def calc_short_circuit_seq_with_vsc(nc: NumericalCircuit,
                                    V_pf: CxVec,
                                    S_pf: CxVec,
                                    St_vsc_pf: CxVec,
                                    Pfp_vsc_pf: Vec | None,
                                    Pfn_vsc_pf: Vec | None,
                                    Z_fault: CxVec,
                                    fault_bus: int,
                                    options: PowerFlowOptions,
                                    constz: bool,
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

        Yfault = np.zeros(shape=nbus, dtype=complex)
        Yfault[fault_bus] = 1 / Z_fault[fault_bus]

        Ygen = np.zeros(shape=nbus, dtype=complex)
        non_norton_gen_pf = np.zeros(shape=nbus, dtype=complex)
        invalid_gen_linear = np.zeros(shape=nbus, dtype=complex)
        invalid_gen_buses = set()
        invalid_gen_scheduled = np.zeros(shape=nbus, dtype=complex)
        dynamic_async_gen = np.zeros(len(nc.generator_data.bus_idx), dtype=bool)
        dynamic_async_p = np.zeros(shape=nbus, dtype=complex)
        dynamic_async_pf = np.zeros(shape=nbus, dtype=complex)
        static_gen_from_generator_scheduled = np.zeros(shape=nbus, dtype=complex)
        static_gen_from_generator_pf = np.zeros(shape=nbus, dtype=complex)
        static_gen_from_generator_buses = set()
        regular_gen_buses = set()
        gen_idx = nc.generator_data.original_idx
        valid_gen_buses = set()
        q_async_pf = compute_asynchronous_generator_q(V=V_pf,
                                                      gen_bus_idx=nc.generator_data.bus_idx,
                                                      gen_active=nc.generator_data.active,
                                                      gen_types=nc.generator_data.tpe_int,
                                                      Rs=nc.generator_data.Rs,
                                                      Xs=nc.generator_data.Xs,
                                                      Xm=nc.generator_data.Xm,
                                                      Rr=nc.generator_data.Rr,
                                                      Xr=nc.generator_data.Xr,
                                                      P=nc.generator_data.p,
                                                      Snom=nc.generator_data.snom)
        for gen_i in range(len(gen_idx)):
            if not nc.generator_data.active[gen_i]:
                continue

            gen_bus = bus_gen_idx[gen_i]
            if nc.generator_data.is_static_generator[gen_i]:
                static_gen_from_generator_buses.add(gen_bus)
                static_gen_from_generator_scheduled[gen_bus] += (
                                                                        nc.generator_data.p[gen_i] + 1j *
                                                                        nc.generator_data.q[gen_i]
                                                                ) / nc.Sbase
                continue

            regular_gen_buses.add(gen_bus)
            zgen = nc.generator_data.r1[gen_i] + 1j * nc.generator_data.x1[gen_i]

            if np.isfinite(zgen) and (abs(zgen) > 1e-12 or nc.bus_data.is_dc[gen_bus]):
                Ygen[gen_bus] += 1 / zgen
                valid_gen_buses.add(gen_bus)
            else:
                invalid_gen_buses.add(gen_bus)
                if nc.generator_data.tpe_int[gen_i] == GeneratorType.Asynchronous.idx():
                    dynamic_async_gen[gen_i] = True
                    dynamic_async_p[gen_bus] += nc.generator_data.p[gen_i] / nc.Sbase
                    dynamic_async_pf[gen_bus] += (
                                                         nc.generator_data.p[gen_i] + 1j * q_async_pf[gen_i]
                                                 ) / nc.Sbase
                else:
                    invalid_gen_scheduled[gen_bus] += (
                                                              nc.generator_data.p[gen_i] + 1j * nc.generator_data.q[
                                                          gen_i]
                                                      ) / nc.Sbase
                logger.add_warning(
                    msg="Generator positive-sequence impedance is missing or too small for short-circuit Norton model",
                    device=nc.generator_data.names[gen_i],
                    value=zgen,
                    expected_value="|R1 + jX1| > 1e-12",
                    device_class="Generator"
                )

        S0_non_gen = S0 - nc.generator_data.get_injections_per_bus() / nc.Sbase
        S0_static_gen = nc.load_data.get_static_generator_injections_per_bus() / nc.Sbase
        S0_non_static_gen = S0_non_gen - S0_static_gen
        S0_gen = S_pf / nc.Sbase - S0_non_gen - I0 - Y0

        for gen_bus in static_gen_from_generator_buses:
            if gen_bus in regular_gen_buses:
                static_gen_from_generator_pf[gen_bus] = static_gen_from_generator_scheduled[gen_bus]
            else:
                static_gen_from_generator_pf[gen_bus] = S0_gen[gen_bus]

        for gen_bus in invalid_gen_buses:
            if gen_bus in valid_gen_buses:
                non_norton_gen_pf[gen_bus] = invalid_gen_scheduled[gen_bus] + dynamic_async_pf[gen_bus]
                invalid_gen_linear[gen_bus] = invalid_gen_scheduled[gen_bus] + dynamic_async_p[gen_bus]
            else:
                non_dynamic_pf = S0_gen[gen_bus] - dynamic_async_pf[gen_bus]
                non_norton_gen_pf[gen_bus] = S0_gen[gen_bus]
                invalid_gen_linear[gen_bus] = non_dynamic_pf + dynamic_async_p[gen_bus]

        S0_gen_valid = S0_gen - non_norton_gen_pf - static_gen_from_generator_pf

        if constz:
            static_gen_linear = S0_static_gen + static_gen_from_generator_pf
            S0_linear = invalid_gen_linear
            I0_linear = np.zeros(shape=nbus, dtype=complex)  # Add generator's norton
            Y0_linear = (- np.conj((S0_non_static_gen + static_gen_linear) / (np.conj(V_pf) * V_pf))
                         - I0 / V_pf - Y0 + Ygen + Yfault)

        else:
            S0_linear = S0_non_gen + static_gen_from_generator_pf + invalid_gen_linear
            I0_linear = np.zeros(shape=nbus, dtype=complex)  # Add generator's norton
            Y0_linear = - I0 / V_pf - Y0 + Ygen + Yfault

        for gen_bus in valid_gen_buses:
            Ugen = V_pf[gen_bus]
            Sgen = S0_gen_valid[gen_bus]
            Igen = np.conj(Sgen / Ugen)
            Egen = Ugen + Igen / Ygen[gen_bus]
            I0_linear[gen_bus] += Ygen[gen_bus] * Egen

        for vsc_i in range(len(nc.vsc_data.control1_int)):
            nc.vsc_data.control1_int[vsc_i] = ConverterControlType.Fault1.idx()
            nc.vsc_data.control2_int[vsc_i] = ConverterControlType.Fault2.idx()

        if len(indices.vd) > 0:

            problem = PfAcDcWithNegativePolesSc(V0=V_pf,
                                                S0=S0_linear,
                                                I0=I0_linear,
                                                Y0=Y0_linear,
                                                St_vsc_pf=St_vsc_pf,
                                                Pfp_vsc_pf=Pfp_vsc_pf,
                                                Pfn_vsc_pf=Pfn_vsc_pf,
                                                Qmin=Qmin,
                                                Qmax=Qmax,
                                                nc=nc,
                                                options=options,
                                                logger=logger,
                                                sc_async_gen_q_mask=dynamic_async_gen,
                                                sc_async_gen_q_prefault=q_async_pf)

            solution = newton_raphson_fx(problem=problem,
                                         tol=options.tolerance,
                                         max_iter=options.max_iter,
                                         trust=options.trust_radius,
                                         verbose=options.verbose,
                                         logger=logger)

            convergence_value = (
                f"error={solution.norm_f:.6g}, "
                f"iterations={solution.iterations}, "
                f"elapsed={solution.elapsed:.6g} s"
            )
            if solution.converged:
                logger.add_info(msg="Short-circuit VSC Newton-Raphson converged",
                                device=f"Island {i}",
                                value=convergence_value)
            else:
                logger.add_warning(msg="Short-circuit VSC Newton-Raphson did not converge",
                                   device=f"Island {i}",
                                   value=convergence_value,
                                   expected_value=f"error <= {options.tolerance}")

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

    sc_results.Sbus1[:, 0] = pf_results.Sbus  # MVA
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
    sc_results.vsc_losses[:, 0] = pf_results.losses_vsc  # in MVA already
    sc_results.vsc_loading[:, 0] = pf_results.loading_vsc

    # Restore original generator control flags
    nc.bus_data.is_vm_controlled[bus_gen_idx] = original_is_vm_controlled
    nc.bus_data.is_va_controlled[bus_gen_idx] = original_is_va_controlled
    nc.bus_data.is_p_controlled[bus_gen_idx] = original_is_p_controlled
    nc.bus_data.is_q_controlled[bus_gen_idx] = original_is_q_controlled

    return sc_results
