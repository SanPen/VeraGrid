# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple, List, Callable
import numba as nb
from math import fsum
import numpy as np
from scipy.sparse import lil_matrix, csc_matrix, vstack, diags
from scipy.sparse.linalg import splu, SuperLU
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import NumericPowerFlowResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Derivatives.ac_jacobian import make_lookup
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import (
    compute_fx_error, power_flow_post_process_nonlinear_3ph, floating_star_currents, floating_star_powers,
    asynchronous_gen_currents, asynchronous_impedance, active_power_mismatch, solve_slip
)
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls import (control_q_inside_method,
                                                                                     compute_slack_distribution)
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_formulation_template import PfFormulationTemplate
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import (compute_current,
                                                                                    compute_power,
                                                                                    compute_fx,
                                                                                    polar_to_rect,
                                                                                    fortescue_012_to_abc)
from VeraGridEngine.Topology.simulation_indices import compile_types
from VeraGridEngine.basic_structures import Vec, IntVec, CxVec, CxMat, BoolVec, Logger
from VeraGridEngine.Utils.Sparse.csc2 import CSC, scipy_to_mat
from VeraGridEngine.enumerations import BusMode, WindingType, GeneratorType, ShuntConnectionType
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.positive_sequence_control import PositiveSequenceControl
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.common_mode_control import CommonModeControl


@nb.njit(cache=True)
def dIbus_dV_numba_sparse_csc(
        Yx: CxVec,
        Yp: IntVec,
        Yi: IntVec,
        V: CxVec,
        Vm: Vec,
        Iinj: CxVec,
        Ifixed: CxVec,
        bus_lookup: IntVec,
        load_bus_idx: IntVec,
        Sstar: CxVec,
        Sfloating: CxVec,
        Sdelta: CxVec,
        Istar: CxVec,
        Idelta: CxVec,
        Ifloating: CxVec,
        source_dVa: np.ndarray,
        source_dVm: np.ndarray,
        scale: float) -> Tuple[CxVec, CxVec]:
    """Differentiate the evaluated current residual in Ybus CSC order.

    For ``E = V / |V|`` and ``R = (Ybus @ V - Iinj) / E``, each stored
    ``(row, column)`` receives the network derivative minus the injection
    derivative, divided by the row's ``E``. The angle diagonal also contains
    ``-1j * R[row]`` from differentiating that row's voltage rotation.

    ``source_dVa`` and ``source_dVm`` have shape ``(original_buses, 4, 4)``;
    their last axes are the injected-current terminal and changed-voltage
    terminal, in NABC order. ``Ifixed`` covers only ordinary fixed-power
    generator injections; local sequence sources and loads use the tensors.

    :param Yx: Ybus data in CSC order.
    :param Yp: Ybus CSC column pointers.
    :param Yi: Ybus CSC row indices.
    :param V: Conductor voltages.
    :param Vm: Voltage magnitudes.
    :param Iinj: Evaluated current injections in system pu.
    :param Ifixed: Injections with a fixed-power diagonal derivative.
    :param bus_lookup: Full NABC to retained conductor lookup.
    :param load_bus_idx: Original bus index for each load.
    :param Sstar: Star load powers.
    :param Sfloating: Floating-star load powers.
    :param Sdelta: Delta load powers.
    :param Istar: Star load current parameters.
    :param Idelta: Delta load current parameters.
    :param Ifloating: Floating-star load current parameters.
    :param source_dVa: Other local source angle derivatives in system pu.
    :param source_dVm: Other local source magnitude derivatives in system pu.
    :param scale: Three-phase to system-base current conversion.
    :return: Magnitude and angle derivative data aligned with ``Yx``.
    """
    n: int = len(Yp) - 1
    E: CxVec = V / Vm
    Icalc: CxVec = np.zeros(n, dtype=np.complex128)
    dI_dVm_x: CxVec = Yx.copy()
    dI_dVa_x: CxVec = Yx.copy()

    # A load touches only its own NABC bus. Reindex its four terminals to a
    # one-load problem so the derivative clones follow the evaluator's exact
    # connection and missing-phase branches.
    local_dVa: np.ndarray = source_dVa.copy()
    local_dVm: np.ndarray = source_dVm.copy()
    local_bus_idx: IntVec = np.zeros(1, dtype=np.int32)
    local_lookup: IntVec = np.empty(4, dtype=np.int32)
    local_voltage: CxVec = np.empty(4, dtype=np.complex128)
    local_change: CxVec = np.zeros(4, dtype=np.complex128)
    retained_slot: IntVec = np.empty(n, dtype=np.int32)
    for slot in range(len(bus_lookup)):
        retained: int = bus_lookup[slot]
        if retained >= 0:
            retained_slot[retained] = slot
        else:
            pass

    for load in range(len(load_bus_idx)):
        bus: int = load_bus_idx[load]
        start: int = 4 * load
        end: int = start + 4
        star_power: CxVec = Sstar[start:end]
        floating_power: CxVec = Sfloating[start:end]
        delta_power: CxVec = Sdelta[start:end]
        star_current: CxVec = Istar[start:end]
        delta_current: CxVec = Idelta[start:end]
        floating_current: CxVec = Ifloating[start:end]

        for phase in range(4):
            conductor: int = bus_lookup[4 * bus + phase]
            if conductor >= 0:
                local_lookup[phase] = phase
                local_voltage[phase] = V[conductor]
            else:
                local_lookup[phase] = -1
                local_voltage[phase] = 0j

        for column_phase in range(4):
            conductor = bus_lookup[4 * bus + column_phase]
            if conductor >= 0:
                local_change[column_phase] = 1j * V[conductor]
                power_angle: CxVec = compute_power_load_derivatives(
                    bus_idx=local_bus_idx,
                    bus_lookup=local_lookup,
                    V=local_voltage,
                    dV=local_change,
                    Sstar=star_power,
                    Sfloating=floating_power,
                    Sdelta=delta_power)
                current_angle: CxVec = compute_current_load_derivatives(
                    bus_idx=local_bus_idx,
                    bus_lookup=local_lookup,
                    V=local_voltage,
                    dV=local_change,
                    Istar=star_current,
                    Idelta=delta_current,
                    Ifloating=floating_current)

                local_change[column_phase] = V[conductor] / Vm[conductor]
                power_magnitude: CxVec = compute_power_load_derivatives(
                    bus_idx=local_bus_idx,
                    bus_lookup=local_lookup,
                    V=local_voltage,
                    dV=local_change,
                    Sstar=star_power,
                    Sfloating=floating_power,
                    Sdelta=delta_power)
                current_magnitude: CxVec = compute_current_load_derivatives(
                    bus_idx=local_bus_idx,
                    bus_lookup=local_lookup,
                    V=local_voltage,
                    dV=local_change,
                    Istar=star_current,
                    Idelta=delta_current,
                    Ifloating=floating_current)

                for row_phase in range(4):
                    if local_lookup[row_phase] >= 0:
                        local_dVa[bus, row_phase, column_phase] += scale * (
                            power_angle[row_phase] + current_angle[row_phase])
                        local_dVm[bus, row_phase, column_phase] += scale * (
                            power_magnitude[row_phase] + current_magnitude[row_phase])
                    else:
                        pass
                local_change[column_phase] = 0j
            else:
                pass

    # Stream the network current and its polar voltage derivatives in the
    # original CSC column order, without constructing intermediate matrices.
    for j in range(n):
        for k in range(Yp[j], Yp[j + 1]):
            i: int = Yi[k]
            network_current: complex = Yx[k] * V[j]
            Icalc[i] += network_current
            dI_dVm_x[k] = Yx[k] * E[j]
            dI_dVa_x[k] = 1j * network_current

    # The Ybus pattern also stores zero entries for local terminal pairs, so
    # every cross-phase load/source derivative has a matching CSC position.
    # Subtract injection derivatives, then differentiate the row rotation.
    for j in range(n):
        column_slot: int = retained_slot[j]
        for k in range(Yp[j], Yp[j + 1]):
            i = Yi[k]
            row_slot: int = retained_slot[i]
            if row_slot // 4 == column_slot // 4:
                bus = column_slot // 4
                dI_dVm_x[k] -= local_dVm[bus, row_slot % 4, column_slot % 4]
                dI_dVa_x[k] -= local_dVa[bus, row_slot % 4, column_slot % 4]
            else:
                pass
            if i == j:
                dI_dVm_x[k] += Ifixed[j] / Vm[j]
                dI_dVa_x[k] -= 1j * Ifixed[j]
            else:
                pass
            dI_dVm_x[k] /= E[i]
            dI_dVa_x[k] /= E[i]
            if i == j:
                dI_dVa_x[k] -= 1j * (Icalc[j] - Iinj[j]) / E[j]
            else:
                pass

    return dI_dVm_x, dI_dVa_x


@nb.jit(nopython=True)
def pack_J_Ibus_csc(
        Yx: CxVec,
        Yp: IntVec,
        Yi: IntVec,
        V: CxVec,
        idx_dtheta: IntVec,
        idx_dVm: IntVec,
        idx_dP: IntVec,
        idx_dQ: IntVec,
        lookup_dP: IntVec,
        lookup_dQ: IntVec,
        Iinj: CxVec,
        Ifixed: CxVec,
        bus_lookup: IntVec,
        load_bus_idx: IntVec,
        Sstar: CxVec,
        Sfloating: CxVec,
        Sdelta: CxVec,
        Istar: CxVec,
        Idelta: CxVec,
        Ifloating: CxVec,
        source_dVa: np.ndarray,
        source_dVm: np.ndarray,
        scale: float) -> CSC:
    """Pack the complex current derivatives into the real solver Jacobian.

    Columns follow ``[angle(idx_dtheta), magnitude(idx_dVm)]``. Rows follow
    ``[real residual(idx_dP), imaginary residual(idx_dQ)]``. The derivative
    kernel shares Ybus's CSC pattern; this function only selects and packs
    those values in the original sparse assembly order.

    :param Yx: Ybus data in CSC order.
    :param Yp: Ybus CSC column pointers.
    :param Yi: Ybus CSC row indices.
    :param V: Retained conductor voltages.
    :param Iinj: Evaluated current injections in system pu.
    :param Ifixed: Fixed-power current injections in system pu.
    :param bus_lookup: Full NABC to retained conductor lookup.
    :param load_bus_idx: Original bus index for each load.
    :param Sstar: Star load powers.
    :param Sfloating: Floating-star load powers.
    :param Sdelta: Delta load powers.
    :param Istar: Star load current parameters.
    :param Idelta: Delta load current parameters.
    :param Ifloating: Floating-star load current parameters.
    :param source_dVa: Local source angle derivatives indexed by bus, row and column terminal.
    :param source_dVm: Local source magnitude derivatives with the same indexing.
    :param scale: Three-phase to system-base current conversion.
    :param idx_dtheta: Conductors whose voltage angles are solver variables.
    :param idx_dVm: Conductors whose voltage magnitudes are solver variables.
    :param idx_dP: Conductors whose real current residuals are equations.
    :param idx_dQ: Conductors whose imaginary current residuals are equations.
    :param lookup_dP: Retained conductor to real row lookup.
    :param lookup_dQ: Retained conductor to imaginary row lookup.
    :return: Real current-equation Jacobian in CSC format.
    """

    # Compute complex current derivatives before selecting real solver rows.
    dI_dVm_x, dI_dVa_x = dIbus_dV_numba_sparse_csc(
        Yx=Yx,
        Yp=Yp,
        Yi=Yi,
        V=V,
        Vm=np.abs(V),
        Iinj=Iinj,
        Ifixed=Ifixed,
        bus_lookup=bus_lookup,
        load_bus_idx=load_bus_idx,
        Sstar=Sstar,
        Sfloating=Sfloating,
        Sdelta=Sdelta,
        Istar=Istar,
        Idelta=Idelta,
        Ifloating=Ifloating,
        source_dVa=source_dVa,
        source_dVm=source_dVm,
        scale=scale)

    nj = len(idx_dtheta) + len(idx_dVm)
    nnz_estimate = 5 * len(dI_dVm_x)
    # Numba jitclass constructors do not accept keyword arguments.
    J = CSC(
        nj,
        nj,
        nnz_estimate,
        False)

    # get length of vectors
    n_no_slack = len(idx_dtheta)

    # nonzeros in J
    nnz = 0
    p = 0
    J.indptr[p] = nnz

    # J1 and J3 -----------------------------------------------------------------------------------------
    for j in idx_dtheta:  # columns

        # J1
        for k in range(Yp[j], Yp[j + 1]):  # rows
            i = Yi[k]
            ii = lookup_dP[i]

            if idx_dtheta[ii] == i:
                J.data[nnz] = dI_dVa_x[k].real
                J.indices[nnz] = ii
                nnz += 1

        # J3
        for k in range(Yp[j], Yp[j + 1]):  # rows
            i = Yi[k]
            ii = lookup_dQ[i]

            if idx_dQ[ii] == i:
                J.data[nnz] = dI_dVa_x[k].imag
                J.indices[nnz] = ii + n_no_slack
                nnz += 1

        p += 1
        J.indptr[p] = nnz

    # J2 and J4 -----------------------------------------------------------------------------------------
    for j in idx_dVm:  # columns

        # J2
        for k in range(Yp[j], Yp[j + 1]):
            i = Yi[k]  # row at Y
            ii = lookup_dP[i]

            if idx_dtheta[ii] == i:
                J.data[nnz] = dI_dVm_x[k].real
                J.indices[nnz] = ii
                nnz += 1

        # J4
        for k in range(Yp[j], Yp[j + 1]):  # rows
            i = Yi[k]
            ii = lookup_dQ[i]

            if idx_dQ[ii] == i:
                J.data[nnz] = dI_dVm_x[k].imag
                J.indices[nnz] = ii + n_no_slack
                nnz += 1

        p += 1
        J.indptr[p] = nnz

    J.indptr[p] = nnz
    J.resize(nnz)
    return J


def calc_autodiff_jacobian(func: Callable[[Vec], Vec], x: Vec, h: float = 1e-6) -> CSC:
    """
    Compute the Jacobian matrix of `func` at `x` using finite differences.
    df/dx = (f(x+h) - f(x)) / h

    :param func: function accepting a vector x and args, and returning either a vector or a
                 tuple where the first argument is a vector and the second.
    :param x: Point at which to evaluate the Jacobian (numpy array).
    :param h: Small step for finite difference.
    :return: Jacobian matrix as a CSC matrix.
    """
    nx = len(x)
    f0 = func(x)

    n_rows = len(f0)

    jac = lil_matrix((n_rows, nx))

    for j in range(nx):
        x_plus_h = np.copy(x)
        x_plus_h[j] += h
        f_plus_h = func(x_plus_h)
        row = (f_plus_h - f0) / h

        any_nan = np.isnan(row)
        if any_nan.any():
            print(any_nan.any())

        for i in range(n_rows):
            if row[i] != 0.0:
                jac[i, j] = row[i]

    return scipy_to_mat(jac.tocsc())



@nb.jit(cache=True)
def lookup_from_mask(mask: BoolVec) -> IntVec:
    """
    This function builds the lookup vector based on the information provided by the mask vector.
    The mask is a boolean vector with True for existing buses and False for non-existing buses.
    The lookup vector will save a -1 for non-existing buses and will order the existing buses from 0 to n.
    :param mask: Boolean vector with True for existing buses and False for non-existing buses.
    :return: lookup
    """
    lookup = np.full(len(mask), -1, dtype=nb.int64)
    counter = 0
    for i, m in enumerate(mask):
        if m:
            lookup[i] = counter
            counter += 1

    return lookup


def compute_ybus_generator(nc: NumericalCircuit) -> Tuple[csc_matrix]:
    """
    Compute the Ybus matrix for a generator in a 3-phase system with neutral.
    It is used only during the short-circuit analysis, not in power flow simulations.
    :param nc: NumericalCircuit
    :return: Ybus
    """

    n = nc.bus_data.nbus
    m = nc.generator_data.nelm

    Ybus_gen = lil_matrix((4 * n, 4 * n), dtype=complex)
    idx4 = np.array([0, 1, 2, 3])

    for k in range(m):
        f = nc.generator_data.bus_idx[k]
        f4 = 4 * f + idx4

        r0 = nc.generator_data.r0[k]
        x0 = nc.generator_data.x0[k]
        r1 = nc.generator_data.r1[k]
        x1 = nc.generator_data.x1[k]
        r2 = nc.generator_data.r2[k]
        x2 = nc.generator_data.x2[k]

        # Fortescue
        Zabc = fortescue_012_to_abc(complex(r0, x0), complex(r1, x1), complex(r2, x2))
        Ybus_gen[np.ix_(f4[1:4], f4[1:4])] = np.linalg.inv(Zabc)

    return Ybus_gen.tocsc()


def compute_ybus(nc: NumericalCircuit) -> Tuple[csc_matrix, csc_matrix, csc_matrix, CxVec, BoolVec, IntVec, IntVec]:
    """
    Compute admittances and masks

    The mask is a boolean vector that indicates which bus phases are active

    The bus_idx_lookup will relate the original bus indices with the sliced bus indices
    This is useful for managing the sliced bus indices in the power flow problem. For instance:

    original_pq_buses = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    mask = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]

    And the lookup becomes:
    bus_idx_lookup = [0, 1, -1, 2, -1, 3, -1, 4, -1, 5, -1, 6, -1, 7, -1, 8, -1, 9, -1, 10, -1]

    And then it will be simple to get the sliced bus indices that we finally need:
    sliced_pq_buses = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


    :param nc: NumericalCircuit
    :return: Ybus, Yf, Yt, Yshunt_bus, mask, bus_idx_lookup
    """

    n = nc.bus_data.nbus
    m = nc.passive_branch_data.nelm
    Cf = lil_matrix((4 * m, 4 * n), dtype=int)
    Ct = lil_matrix((4 * m, 4 * n), dtype=int)
    Yf = lil_matrix((4 * m, 4 * n), dtype=complex)
    Yt = lil_matrix((4 * m, 4 * n), dtype=complex)

    idx4 = np.array([0, 1, 2, 3])  # array that we use to generate the 3-phase indices

    R = np.zeros(4 * m, dtype=bool)

    for k in range(m):
        f = nc.passive_branch_data.F[k]
        t = nc.passive_branch_data.T[k]

        f4 = 4 * f + idx4
        t4 = 4 * t + idx4
        k4 = 4 * k + idx4

        Yf[np.ix_(k4, f4)] = nc.passive_branch_data.Yff3[k4, :]
        Yf[np.ix_(k4, t4)] = nc.passive_branch_data.Yft3[k4, :]
        Yt[np.ix_(k4, f4)] = nc.passive_branch_data.Ytf3[k4, :]
        Yt[np.ix_(k4, t4)] = nc.passive_branch_data.Ytt3[k4, :]

        R[4 * k + 0] = nc.passive_branch_data.phN[k]
        R[4 * k + 1] = nc.passive_branch_data.phA[k]
        R[4 * k + 2] = nc.passive_branch_data.phB[k]
        R[4 * k + 3] = nc.passive_branch_data.phC[k]

        Cf[k4, f4] = 1
        Ct[k4, t4] = 1

    if nc.passive_branch_data.Ycoupling3.nnz > 0:
        mutual: csc_matrix = nc.passive_branch_data.Ycoupling3 @ vstack((Cf, Ct), format='csc')
        Yf += mutual[:4 * m, :]
        Yt += mutual[4 * m:, :]
    else:
        pass

    zero_mask = (R == 0)
    Cfcopy = Cf.copy()
    Ctcopy = Ct.copy()

    Cfcopy[zero_mask, :] = 0
    Ctcopy[zero_mask, :] = 0

    Ctot = Cfcopy + Ctcopy
    col_sums = np.array(Ctot.sum(axis=0))[0, :]
    binary_bus_mask = (col_sums > 0).astype(bool)

    F = np.array(nc.passive_branch_data.F, dtype=int)
    T = np.array(nc.passive_branch_data.T, dtype=int)

    # --- build CSR-like incidence list: branches per bus (Numba-friendly) ---
    deg = np.zeros(n, dtype=np.int64)  # number of incident branches per bus (the bus “degree”)
    for k in range(m):
        deg[F[k]] += 1
        deg[T[k]] += 1

    # Index pointer into bus_branches that gives where each bus’s incident branches start and end
    ptr = np.zeros(n + 1, dtype=np.int64)
    for i in range(n):
        ptr[i + 1] = ptr[i] + deg[i]

    bus_branches = np.zeros(ptr[-1], dtype=np.int64)
    fill = np.zeros(n, dtype=np.int64)
    for k in range(m):
        f = F[k]
        t = T[k]

        pos_f = ptr[f] + fill[f]
        bus_branches[pos_f] = k
        fill[f] += 1

        pos_t = ptr[t] + fill[t]
        bus_branches[pos_t] = k
        fill[t] += 1

    bus_has_neutral = np.ones(4 * n, dtype=bool)  # por defecto el neutro del bus está activo

    for bus_idx in range(n):
        start = ptr[bus_idx]
        end = ptr[bus_idx + 1]

        grounded_here = False

        # Only buses with at least one incident branch need the explicit grounding scan.
        # Isolated buses keep the default neutral-active state and fall through untouched.
        if start == end:
            grounded_here = False
        else:
            # Iterate only over branches actually connected to this bus and stop as
            # soon as one grounded-star terminal is found.
            for p in range(start, end):
                k = bus_branches[p]

                # A grounded star or any zig-zag primitive anchors the local neutral reference.
                if F[k] == bus_idx and nc.passive_branch_data.is_transformer[k] and nc.passive_branch_data.conn_f[k] in (
                        WindingType.GroundedStar.idx(), WindingType.NeutralZigZag.idx(),
                        WindingType.FloatingZigZag.idx(), WindingType.GroundedZigZag.idx()):
                    grounded_here = True
                    break
                else:
                    if T[k] == bus_idx and nc.passive_branch_data.is_transformer[k] and nc.passive_branch_data.conn_t[k] in (
                            WindingType.GroundedStar.idx(), WindingType.NeutralZigZag.idx(),
                            WindingType.FloatingZigZag.idx(), WindingType.GroundedZigZag.idx()):
                        grounded_here = True
                        break
                    else:
                        pass

        if grounded_here:
            bus_has_neutral[4 * bus_idx + 0] = False  # desactiva el nodo de neutro del bus
        else:
            pass

    bus_has_neutral[0::4] &= nc.bus_data.bus_types != BusMode.Slack_tpe.value

    grounded_shunt_buses = nc.shunt_data.bus_idx[nc.shunt_data.active & nc.shunt_data.grounds_neutral]
    bus_has_neutral[4 * grounded_shunt_buses] = False
    grounded_load_buses: IntVec = nc.load_data.bus_idx[nc.load_data.active & nc.load_data.grounds_neutral]
    bus_has_neutral[4 * grounded_load_buses] = False

    # Grounded transformers, shunts, loads and slack buses fix their neutral to zero.
    binary_bus_mask[0::4] = binary_bus_mask[0::4] & bus_has_neutral[0::4]

    Ysh_bus = np.zeros((n * 4, n * 4), dtype=complex)
    for k in range(nc.shunt_data.nelm):
        f = nc.shunt_data.bus_idx[k]
        k4 = 4 * k + idx4
        f4 = 4 * f + idx4
        Ysh_bus[np.ix_(f4, f4)] += nc.shunt_data.Y3_star[np.ix_(k4, idx4)] / (nc.Sbase / 3)

    for k in range(nc.load_data.nelm):
        f = nc.load_data.bus_idx[k]
        k4 = 4 * k + idx4
        f4 = 4 * f + idx4
        Ysh_bus[np.ix_(f4, f4)] += nc.load_data.Y3_star[np.ix_(k4, idx4)] / (nc.Sbase / 3)

    Ybus = Cfcopy.T @ Yf + Ctcopy.T @ Yt + Ysh_bus

    Ybus = Ybus[np.ix_(binary_bus_mask, binary_bus_mask)]
    Ysh_bus = Ysh_bus[np.ix_(binary_bus_mask, binary_bus_mask)]
    Yf = Yf[np.ix_(R, binary_bus_mask)]
    Yt = Yt[np.ix_(R, binary_bus_mask)]

    bus_idx_lookup = lookup_from_mask(binary_bus_mask)
    branch_lookup = lookup_from_mask(R)

    Ybus = csc_matrix(Ybus)

    return Ybus.tocsc(), Yf.tocsc(), Yt.tocsc(), Ysh_bus, binary_bus_mask, bus_idx_lookup, branch_lookup


def compute_generators(bus_idx: IntVec,
                       bus_lookup: IntVec,
                       V: CxVec,
                       P: Vec,
                       Q: Vec,
                       control_mode_int: IntVec) -> CxVec:
    """

    :param bus_idx:
    :param bus_lookup:
    :param V:
    :param P:
    :param Q:
    :param control_mode_int:
    :return:
    """
    n = len(V)
    nelm = len(bus_idx)
    Igen = np.zeros(n, dtype=complex)

    for k in range(nelm):

        if control_mode_int[k] == 1:  # GeneratorControlMode.V: 1
            Q[k] = 0.0

        f = bus_idx[k]

        a = 4 * f + 1
        b = 4 * f + 2
        c = 4 * f + 3

        a2 = bus_lookup[a]
        b2 = bus_lookup[b]
        c2 = bus_lookup[c]

        # Fixed-power units can share a terminal with each other and a U1 regulator.
        Igen[a2] += np.conj((P[k] + Q[k] * 1j) / 3 / V[a2])
        Igen[b2] += np.conj((P[k] + Q[k] * 1j) / 3 / V[b2])
        Igen[c2] += np.conj((P[k] + Q[k] * 1j) / 3 / V[c2])

    return Igen


@nb.jit(cache=True)
def compute_current_loads(bus_idx: IntVec,
                          bus_lookup: IntVec,
                          V: CxVec,
                          Istar: CxVec,
                          Idelta: CxVec,
                          Ifloating: CxVec) -> Tuple[CxVec, CxVec, CxVec]:
    """Accumulate constant-current load injections in retained NABC order.

    :param bus_idx: Bus index for each load.
    :param bus_lookup: Full NABC slot to retained conductor lookup.
    :param V: Retained conductor voltages.
    :param Istar: Star branch-current parameters.
    :param Idelta: Delta branch-current parameters.
    :param Ifloating: Floating-star branch-current parameters.
    :return: Injection currents, linearized admittances, and floating neutral voltages.
    """
    n = len(V)
    nelm = len(bus_idx)

    # I = np.zeros(n, dtype=nb.complex128)
    I = np.zeros(n, dtype=np.complex128)

    # zero_load = nb.complex128(0.0)
    zero_load = complex(0.0, 0.0)

    # Un_floating = np.zeros(len(V), dtype=nb.complex128)
    Un_floating = np.zeros(len(V), dtype=np.complex128)

    for k in range(nelm):

        f = bus_idx[k]

        n = 4 * f + 0
        a = 4 * f + 1
        b = 4 * f + 2
        c = 4 * f + 3

        n2 = bus_lookup[n]
        a2 = bus_lookup[a]
        b2 = bus_lookup[b]
        c2 = bus_lookup[c]

        nn = 4 * k + 0
        ab = 4 * k + 1
        bc = 4 * k + 2
        ca = 4 * k + 3

        star = (Istar[ab] != zero_load or Istar[bc] != zero_load or Istar[ca] != zero_load)
        floating = (Ifloating[ab] != zero_load or Ifloating[bc] != zero_load or Ifloating[ca] != zero_load)
        delta = (Idelta[ab] != zero_load or Idelta[bc] != zero_load or Idelta[ca] != zero_load)

        n_connected = (Istar[nn] != zero_load and n2 >= 0)
        a_connected = (Istar[ab] != zero_load and a2 >= 0)
        b_connected = (Istar[bc] != zero_load and b2 >= 0)
        c_connected = (Istar[ca] != zero_load and c2 >= 0)

        ab_connected = (Idelta[ab] != zero_load)
        bc_connected = (Idelta[bc] != zero_load)
        ca_connected = (Idelta[ca] != zero_load)

        voltage_angle_a = np.angle(V[a2]) if a2 >= 0 else 0.0
        voltage_angle_b = np.angle(V[b2]) if b2 >= 0 else 0.0
        voltage_angle_c = np.angle(V[c2]) if c2 >= 0 else 0.0

        voltage_angle_ab = np.angle(V[a2] - V[b2]) if a2 >= 0 and b2 >= 0 else 0.0
        voltage_angle_bc = np.angle(V[b2] - V[c2]) if b2 >= 0 and c2 >= 0 else 0.0
        voltage_angle_ca = np.angle(V[c2] - V[a2]) if c2 >= 0 and a2 >= 0 else 0.0

        if delta and ab_connected and bc_connected and ca_connected:

            if a2 >= 0 and b2 >= 0 and c2 >= 0:
                Iab = np.conj(Idelta[ab] / np.sqrt(3)) * np.exp(1j * voltage_angle_ab)
                Ibc = np.conj(Idelta[bc] / np.sqrt(3)) * np.exp(1j * voltage_angle_bc)
                Ica = np.conj(Idelta[ca] / np.sqrt(3)) * np.exp(1j * voltage_angle_ca)
                I[a2] -= Iab - Ica
                I[b2] -= Ibc - Iab
                I[c2] -= Ica - Ibc

            elif a2 < 0 <= b2 and c2 >= 0:
                Ibc = np.conj(Idelta[bc] / np.sqrt(3)) * np.exp(1j * voltage_angle_bc)
                I[b2] -= Ibc
                I[c2] += Ibc

            elif b2 < 0 <= a2 and c2 >= 0:
                Ica = np.conj(Idelta[ca] / np.sqrt(3)) * np.exp(1j * voltage_angle_ca)
                I[a2] += Ica
                I[c2] -= Ica

            elif c2 < 0 <= a2 and b2 >= 0:
                Iab = np.conj(Idelta[ab] / np.sqrt(3)) * np.exp(1j * voltage_angle_ab)
                I[a2] -= Iab
                I[b2] += Iab

            else:
                pass

        elif delta and ab_connected:

            if a2 >= 0 and b2 >= 0:
                Iab = np.conj(Idelta[ab] / np.sqrt(3)) * np.exp(1j * voltage_angle_ab)
                I[a2] -= Iab
                I[b2] += Iab
            else:
                pass

        elif delta and bc_connected:

            if b2 >= 0 and c2 >= 0:
                Ibc = np.conj(Idelta[bc] / np.sqrt(3)) * np.exp(1j * voltage_angle_bc)
                I[b2] -= Ibc
                I[c2] += Ibc
            else:
                pass

        elif delta and ca_connected:

            if c2 >= 0 and a2 >= 0:
                Ica = np.conj(Idelta[ca] / np.sqrt(3)) * np.exp(1j * voltage_angle_ca)
                I[a2] += Ica
                I[c2] -= Ica
            else:
                pass

        elif star and a_connected and b_connected and c_connected and n_connected:

            Uan = V[a2] - V[n2]
            Ubn = V[b2] - V[n2]
            Ucn = V[c2] - V[n2]

            Ian = np.conj(Istar[ab]) * (Uan / abs(Uan))
            Ibn = np.conj(Istar[bc]) * (Ubn / abs(Ubn))
            Icn = np.conj(Istar[ca]) * (Ucn / abs(Ucn))

            I[a2] -= Ian
            I[b2] -= Ibn
            I[c2] -= Icn
            I[n2] += (Ian + Ibn + Icn)

        elif star and a_connected and b_connected and n_connected:

            Uan = V[a2] - V[n2]
            Ubn = V[b2] - V[n2]

            Ian = np.conj(Istar[ab]) * (Uan / abs(Uan))
            Ibn = np.conj(Istar[bc]) * (Ubn / abs(Ubn))

            I[a2] -= Ian
            I[b2] -= Ibn
            I[n2] += (Ian + Ibn)

        elif star and b_connected and c_connected and n_connected:

            Ubn = V[b2] - V[n2]
            Ucn = V[c2] - V[n2]

            Ibn = np.conj(Istar[bc]) * (Ubn / abs(Ubn))
            Icn = np.conj(Istar[ca]) * (Ucn / abs(Ucn))

            I[b2] -= Ibn
            I[c2] -= Icn
            I[n2] += (Ibn + Icn)

        elif star and a_connected and c_connected and n_connected:

            Uan = V[a2] - V[n2]
            Ucn = V[c2] - V[n2]

            Ian = np.conj(Istar[ab]) * (Uan / abs(Uan))
            Icn = np.conj(Istar[ca]) * (Ucn / abs(Ucn))

            I[a2] -= Ian
            I[c2] -= Icn
            I[n2] += (Ian + Icn)

        elif star and a_connected and n_connected:

            Uan = V[a2] - V[n2]
            Ian = np.conj(Istar[ab]) * (Uan / abs(Uan))
            I[a2] -= Ian
            I[n2] += Ian

        elif star and b_connected and n_connected:

            Ubn = V[b2] - V[n2]
            Ibn = np.conj(Istar[bc]) * (Ubn / abs(Ubn))
            I[b2] -= Ibn
            I[n2] += Ibn

        elif star and c_connected and n_connected:

            Ucn = V[c2] - V[n2]
            Icn = np.conj(Istar[ca]) * (Ucn / abs(Ucn))
            I[c2] -= Icn
            I[n2] += Icn

        elif star and a_connected and b_connected and c_connected:

            if a2 >= 0:
                I[a2] -= np.conj(Istar[ab]) * np.exp(1j * voltage_angle_a)
            if b2 >= 0:
                I[b2] -= np.conj(Istar[bc]) * np.exp(1j * voltage_angle_b)
            if c2 >= 0:
                I[c2] -= np.conj(Istar[ca]) * np.exp(1j * voltage_angle_c)

        elif star and a_connected and b_connected:

            if a2 >= 0:
                I[a2] -= np.conj(Istar[ab]) * np.exp(1j * voltage_angle_a)
            if b2 >= 0:
                I[b2] -= np.conj(Istar[bc]) * np.exp(1j * voltage_angle_b)

        elif star and b_connected and c_connected:

            if b2 >= 0:
                I[b2] -= np.conj(Istar[bc]) * np.exp(1j * voltage_angle_b)
            if c2 >= 0:
                I[c2] -= np.conj(Istar[ca]) * np.exp(1j * voltage_angle_c)

        elif star and a_connected and c_connected:

            if a2 >= 0:
                I[a2] -= np.conj(Istar[ab]) * np.exp(1j * voltage_angle_a)
            if c2 >= 0:
                I[c2] -= np.conj(Istar[ca]) * np.exp(1j * voltage_angle_c)

        elif star and a_connected:
            if a2 >= 0:
                I[a2] -= np.conj(Istar[ab]) * np.exp(1j * voltage_angle_a)

        elif star and b_connected:
            if b2 >= 0:
                I[b2] -= np.conj(Istar[bc]) * np.exp(1j * voltage_angle_b)

        elif star and c_connected:
            if c2 >= 0:
                I[c2] -= np.conj(Istar[ca]) * np.exp(1j * voltage_angle_c)

        elif floating:

            connected_count: int = int(a2 >= 0) + int(b2 >= 0) + int(c2 >= 0)
            Vn_prev: complex = ((V[a2] if a2 >= 0 else 0j)
                                + (V[b2] if b2 >= 0 else 0j)
                                + (V[c2] if c2 >= 0 else 0j)) / max(connected_count, 1)

            if a2 >= 0 and b2 >= 0 and c2 >= 0:
                Ia, Ib, Ic, Un = floating_star_currents(V[a2], V[b2], V[c2],
                                                        Ifloating[ab], Ifloating[bc], Ifloating[ca],
                                                        Vn_prev)
            elif a2 >= 0 and b2 >= 0:
                Ia, Ib, Ic, Un = floating_star_currents(V[a2], V[b2], zero_load,
                                                        Ifloating[ab], Ifloating[bc], zero_load,
                                                        Vn_prev)
            elif b2 >= 0 and c2 >= 0:
                Ia, Ib, Ic, Un = floating_star_currents(zero_load, V[b2], V[c2],
                                                        zero_load, Ifloating[bc], Ifloating[ca],
                                                        Vn_prev)
            elif a2 >= 0 and c2 >= 0:
                Ia, Ib, Ic, Un = floating_star_currents(V[a2], zero_load, V[c2],
                                                        Ifloating[ab], zero_load, Ifloating[ca],
                                                        Vn_prev)
            else:
                Ia, Ib, Ic, Un = zero_load, zero_load, zero_load, zero_load

            if a2 >= 0:
                I[a2] -= Ia
                Un_floating[a2] = Un
            else:
                pass
            if b2 >= 0:
                I[b2] -= Ib
                Un_floating[b2] = Un
            else:
                pass
            if c2 >= 0:
                I[c2] -= Ic
                Un_floating[c2] = Un
            else:
                pass

        else:
            pass

    # Y_current_linear = np.zeros_like(I, dtype=nb.complex128)
    Y_current_linear = np.zeros_like(I, dtype=np.complex128)
    for i in range(len(V)):
        if abs(V[i]) > 1e-12:
            Y_current_linear[i] = I[i] / V[i]

    return I, Y_current_linear, Un_floating


@nb.jit(cache=True)
def compute_current_load_derivatives(bus_idx: IntVec,
                                     bus_lookup: IntVec,
                                     V: CxVec,
                                     dV: CxVec,
                                     Istar: CxVec,
                                     Idelta: CxVec,
                                     Ifloating: CxVec) -> CxVec:
    """Differentiate ``compute_current_loads`` in the direction ``dV``.

    This follows the evaluator's delta, grounded/neutral star, and floating
    star branches in the same order. For a branch voltage ``U``, its current
    is ``conj(I0) * U / |U|``; the derivative includes both the voltage change
    and the change in ``|U|``. A floating star differentiates the evaluator's
    damped secant neutral iterations, including their initial neutral guess.

    :param bus_idx: Bus index for each load.
    :param bus_lookup: Full NABC slot to retained conductor lookup.
    :param V: Retained conductor voltages.
    :param dV: Change in retained conductor voltages.
    :param Istar: Star branch-current parameters.
    :param Idelta: Delta branch-current parameters.
    :param Ifloating: Floating-star branch-current parameters.
    :return: Directional change in unscaled retained load-current injections.
    """
    n: int = len(V)
    nelm: int = len(bus_idx)
    dI: CxVec = np.zeros(n, dtype=np.complex128)
    zero_load: complex = complex(0.0, 0.0)

    for k in range(nelm):
        f: int = bus_idx[k]
        n: int = 4 * f + 0
        a: int = 4 * f + 1
        b: int = 4 * f + 2
        c: int = 4 * f + 3
        n2: int = bus_lookup[n]
        a2: int = bus_lookup[a]
        b2: int = bus_lookup[b]
        c2: int = bus_lookup[c]
        nn: int = 4 * k + 0
        ab: int = 4 * k + 1
        bc: int = 4 * k + 2
        ca: int = 4 * k + 3

        star: bool = (Istar[ab] != zero_load or Istar[bc] != zero_load or Istar[ca] != zero_load)
        floating: bool = (Ifloating[ab] != zero_load or Ifloating[bc] != zero_load or Ifloating[ca] != zero_load)
        delta: bool = (Idelta[ab] != zero_load or Idelta[bc] != zero_load or Idelta[ca] != zero_load)
        n_connected: bool = (Istar[nn] != zero_load and n2 >= 0)
        a_connected: bool = (Istar[ab] != zero_load and a2 >= 0)
        b_connected: bool = (Istar[bc] != zero_load and b2 >= 0)
        c_connected: bool = (Istar[ca] != zero_load and c2 >= 0)
        ab_connected: bool = (Idelta[ab] != zero_load)
        bc_connected: bool = (Idelta[bc] != zero_load)
        ca_connected: bool = (Idelta[ca] != zero_load)

        if delta and ab_connected and bc_connected and ca_connected:
            if a2 >= 0 and b2 >= 0 and c2 >= 0:
                Uab: complex = V[a2] - V[b2]
                Ubc: complex = V[b2] - V[c2]
                Uca: complex = V[c2] - V[a2]
                dUab: complex = dV[a2] - dV[b2]
                dUbc: complex = dV[b2] - dV[c2]
                dUca: complex = dV[c2] - dV[a2]
                Iab: complex = np.conj(Idelta[ab] / np.sqrt(3)) * Uab / abs(Uab)
                Ibc: complex = np.conj(Idelta[bc] / np.sqrt(3)) * Ubc / abs(Ubc)
                Ica: complex = np.conj(Idelta[ca] / np.sqrt(3)) * Uca / abs(Uca)
                dIab: complex = Iab * (dUab / Uab - np.real(np.conj(Uab) * dUab) / abs(Uab) ** 2)
                dIbc: complex = Ibc * (dUbc / Ubc - np.real(np.conj(Ubc) * dUbc) / abs(Ubc) ** 2)
                dIca: complex = Ica * (dUca / Uca - np.real(np.conj(Uca) * dUca) / abs(Uca) ** 2)
                dI[a2] -= dIab - dIca
                dI[b2] -= dIbc - dIab
                dI[c2] -= dIca - dIbc
            elif a2 < 0 <= b2 and c2 >= 0:
                Ubc = V[b2] - V[c2]
                dUbc = dV[b2] - dV[c2]
                Ibc = np.conj(Idelta[bc] / np.sqrt(3)) * Ubc / abs(Ubc)
                dIbc = Ibc * (dUbc / Ubc - np.real(np.conj(Ubc) * dUbc) / abs(Ubc) ** 2)
                dI[b2] -= dIbc
                dI[c2] += dIbc
            elif b2 < 0 <= a2 and c2 >= 0:
                Uca = V[c2] - V[a2]
                dUca = dV[c2] - dV[a2]
                Ica = np.conj(Idelta[ca] / np.sqrt(3)) * Uca / abs(Uca)
                dIca = Ica * (dUca / Uca - np.real(np.conj(Uca) * dUca) / abs(Uca) ** 2)
                dI[a2] += dIca
                dI[c2] -= dIca
            elif c2 < 0 <= a2 and b2 >= 0:
                Uab = V[a2] - V[b2]
                dUab = dV[a2] - dV[b2]
                Iab = np.conj(Idelta[ab] / np.sqrt(3)) * Uab / abs(Uab)
                dIab = Iab * (dUab / Uab - np.real(np.conj(Uab) * dUab) / abs(Uab) ** 2)
                dI[a2] -= dIab
                dI[b2] += dIab
            else:
                pass

        elif delta and ab_connected:
            if a2 >= 0 and b2 >= 0:
                Uab = V[a2] - V[b2]
                dUab = dV[a2] - dV[b2]
                Iab = np.conj(Idelta[ab] / np.sqrt(3)) * Uab / abs(Uab)
                dIab = Iab * (dUab / Uab - np.real(np.conj(Uab) * dUab) / abs(Uab) ** 2)
                dI[a2] -= dIab
                dI[b2] += dIab
            else:
                pass
        elif delta and bc_connected:
            if b2 >= 0 and c2 >= 0:
                Ubc = V[b2] - V[c2]
                dUbc = dV[b2] - dV[c2]
                Ibc = np.conj(Idelta[bc] / np.sqrt(3)) * Ubc / abs(Ubc)
                dIbc = Ibc * (dUbc / Ubc - np.real(np.conj(Ubc) * dUbc) / abs(Ubc) ** 2)
                dI[b2] -= dIbc
                dI[c2] += dIbc
            else:
                pass
        elif delta and ca_connected:
            if c2 >= 0 and a2 >= 0:
                Uca = V[c2] - V[a2]
                dUca = dV[c2] - dV[a2]
                Ica = np.conj(Idelta[ca] / np.sqrt(3)) * Uca / abs(Uca)
                dIca = Ica * (dUca / Uca - np.real(np.conj(Uca) * dUca) / abs(Uca) ** 2)
                dI[a2] += dIca
                dI[c2] -= dIca
            else:
                pass

        elif star and a_connected and b_connected and c_connected and n_connected:
            Uan: complex = V[a2] - V[n2]
            Ubn: complex = V[b2] - V[n2]
            Ucn: complex = V[c2] - V[n2]
            dUan: complex = dV[a2] - dV[n2]
            dUbn: complex = dV[b2] - dV[n2]
            dUcn: complex = dV[c2] - dV[n2]
            Ian: complex = np.conj(Istar[ab]) * Uan / abs(Uan)
            Ibn: complex = np.conj(Istar[bc]) * Ubn / abs(Ubn)
            Icn: complex = np.conj(Istar[ca]) * Ucn / abs(Ucn)
            dIan: complex = Ian * (dUan / Uan - np.real(np.conj(Uan) * dUan) / abs(Uan) ** 2)
            dIbn: complex = Ibn * (dUbn / Ubn - np.real(np.conj(Ubn) * dUbn) / abs(Ubn) ** 2)
            dIcn: complex = Icn * (dUcn / Ucn - np.real(np.conj(Ucn) * dUcn) / abs(Ucn) ** 2)
            dI[a2] -= dIan
            dI[b2] -= dIbn
            dI[c2] -= dIcn
            dI[n2] += dIan + dIbn + dIcn
        elif star and a_connected and b_connected and n_connected:
            Uan = V[a2] - V[n2]
            Ubn = V[b2] - V[n2]
            dUan = dV[a2] - dV[n2]
            dUbn = dV[b2] - dV[n2]
            Ian = np.conj(Istar[ab]) * Uan / abs(Uan)
            Ibn = np.conj(Istar[bc]) * Ubn / abs(Ubn)
            dIan = Ian * (dUan / Uan - np.real(np.conj(Uan) * dUan) / abs(Uan) ** 2)
            dIbn = Ibn * (dUbn / Ubn - np.real(np.conj(Ubn) * dUbn) / abs(Ubn) ** 2)
            dI[a2] -= dIan
            dI[b2] -= dIbn
            dI[n2] += dIan + dIbn
        elif star and b_connected and c_connected and n_connected:
            Ubn = V[b2] - V[n2]
            Ucn = V[c2] - V[n2]
            dUbn = dV[b2] - dV[n2]
            dUcn = dV[c2] - dV[n2]
            Ibn = np.conj(Istar[bc]) * Ubn / abs(Ubn)
            Icn = np.conj(Istar[ca]) * Ucn / abs(Ucn)
            dIbn = Ibn * (dUbn / Ubn - np.real(np.conj(Ubn) * dUbn) / abs(Ubn) ** 2)
            dIcn = Icn * (dUcn / Ucn - np.real(np.conj(Ucn) * dUcn) / abs(Ucn) ** 2)
            dI[b2] -= dIbn
            dI[c2] -= dIcn
            dI[n2] += dIbn + dIcn
        elif star and a_connected and c_connected and n_connected:
            Uan = V[a2] - V[n2]
            Ucn = V[c2] - V[n2]
            dUan = dV[a2] - dV[n2]
            dUcn = dV[c2] - dV[n2]
            Ian = np.conj(Istar[ab]) * Uan / abs(Uan)
            Icn = np.conj(Istar[ca]) * Ucn / abs(Ucn)
            dIan = Ian * (dUan / Uan - np.real(np.conj(Uan) * dUan) / abs(Uan) ** 2)
            dIcn = Icn * (dUcn / Ucn - np.real(np.conj(Ucn) * dUcn) / abs(Ucn) ** 2)
            dI[a2] -= dIan
            dI[c2] -= dIcn
            dI[n2] += dIan + dIcn
        elif star and a_connected and n_connected:
            Uan = V[a2] - V[n2]
            dUan = dV[a2] - dV[n2]
            Ian = np.conj(Istar[ab]) * Uan / abs(Uan)
            dIan = Ian * (dUan / Uan - np.real(np.conj(Uan) * dUan) / abs(Uan) ** 2)
            dI[a2] -= dIan
            dI[n2] += dIan
        elif star and b_connected and n_connected:
            Ubn = V[b2] - V[n2]
            dUbn = dV[b2] - dV[n2]
            Ibn = np.conj(Istar[bc]) * Ubn / abs(Ubn)
            dIbn = Ibn * (dUbn / Ubn - np.real(np.conj(Ubn) * dUbn) / abs(Ubn) ** 2)
            dI[b2] -= dIbn
            dI[n2] += dIbn
        elif star and c_connected and n_connected:
            Ucn = V[c2] - V[n2]
            dUcn = dV[c2] - dV[n2]
            Icn = np.conj(Istar[ca]) * Ucn / abs(Ucn)
            dIcn = Icn * (dUcn / Ucn - np.real(np.conj(Ucn) * dUcn) / abs(Ucn) ** 2)
            dI[c2] -= dIcn
            dI[n2] += dIcn

        elif star and a_connected and b_connected and c_connected:
            Uan = V[a2]
            Ubn = V[b2]
            Ucn = V[c2]
            dUan = dV[a2]
            dUbn = dV[b2]
            dUcn = dV[c2]
            Ian = np.conj(Istar[ab]) * Uan / abs(Uan)
            Ibn = np.conj(Istar[bc]) * Ubn / abs(Ubn)
            Icn = np.conj(Istar[ca]) * Ucn / abs(Ucn)
            dI[a2] -= Ian * (dUan / Uan - np.real(np.conj(Uan) * dUan) / abs(Uan) ** 2)
            dI[b2] -= Ibn * (dUbn / Ubn - np.real(np.conj(Ubn) * dUbn) / abs(Ubn) ** 2)
            dI[c2] -= Icn * (dUcn / Ucn - np.real(np.conj(Ucn) * dUcn) / abs(Ucn) ** 2)
        elif star and a_connected and b_connected:
            Uan = V[a2]
            Ubn = V[b2]
            Ian = np.conj(Istar[ab]) * Uan / abs(Uan)
            Ibn = np.conj(Istar[bc]) * Ubn / abs(Ubn)
            dI[a2] -= Ian * (dV[a2] / Uan - np.real(np.conj(Uan) * dV[a2]) / abs(Uan) ** 2)
            dI[b2] -= Ibn * (dV[b2] / Ubn - np.real(np.conj(Ubn) * dV[b2]) / abs(Ubn) ** 2)
        elif star and b_connected and c_connected:
            Ubn = V[b2]
            Ucn = V[c2]
            Ibn = np.conj(Istar[bc]) * Ubn / abs(Ubn)
            Icn = np.conj(Istar[ca]) * Ucn / abs(Ucn)
            dI[b2] -= Ibn * (dV[b2] / Ubn - np.real(np.conj(Ubn) * dV[b2]) / abs(Ubn) ** 2)
            dI[c2] -= Icn * (dV[c2] / Ucn - np.real(np.conj(Ucn) * dV[c2]) / abs(Ucn) ** 2)
        elif star and a_connected and c_connected:
            Uan = V[a2]
            Ucn = V[c2]
            Ian = np.conj(Istar[ab]) * Uan / abs(Uan)
            Icn = np.conj(Istar[ca]) * Ucn / abs(Ucn)
            dI[a2] -= Ian * (dV[a2] / Uan - np.real(np.conj(Uan) * dV[a2]) / abs(Uan) ** 2)
            dI[c2] -= Icn * (dV[c2] / Ucn - np.real(np.conj(Ucn) * dV[c2]) / abs(Ucn) ** 2)
        elif star and a_connected:
            Uan = V[a2]
            Ian = np.conj(Istar[ab]) * Uan / abs(Uan)
            dI[a2] -= Ian * (dV[a2] / Uan - np.real(np.conj(Uan) * dV[a2]) / abs(Uan) ** 2)
        elif star and b_connected:
            Ubn = V[b2]
            Ibn = np.conj(Istar[bc]) * Ubn / abs(Ubn)
            dI[b2] -= Ibn * (dV[b2] / Ubn - np.real(np.conj(Ubn) * dV[b2]) / abs(Ubn) ** 2)
        elif star and c_connected:
            Ucn = V[c2]
            Icn = np.conj(Istar[ca]) * Ucn / abs(Ucn)
            dI[c2] -= Icn * (dV[c2] / Ucn - np.real(np.conj(Ucn) * dV[c2]) / abs(Ucn) ** 2)

        elif floating:
            connected_count: int = int(a2 >= 0) + int(b2 >= 0) + int(c2 >= 0)
            Vn_prev: complex = ((V[a2] if a2 >= 0 else 0j)
                                + (V[b2] if b2 >= 0 else 0j)
                                + (V[c2] if c2 >= 0 else 0j)) / max(connected_count, 1)
            dVn_prev: complex = ((dV[a2] if a2 >= 0 else 0j)
                                 + (dV[b2] if b2 >= 0 else 0j)
                                 + (dV[c2] if c2 >= 0 else 0j)) / max(connected_count, 1)
            phase_bus: IntVec = np.array([a2, b2, c2], dtype=np.int32)
            phase_parameter: CxVec = np.array([Ifloating[ab], Ifloating[bc], Ifloating[ca]])
            active: BoolVec = np.zeros(3, dtype=np.bool_)
            present_a: bool = a2 >= 0 and abs(V[a2]) > 1e-5
            present_b: bool = b2 >= 0 and abs(V[b2]) > 1e-5
            present_c: bool = c2 >= 0 and abs(V[c2]) > 1e-5
            if present_a and present_b and present_c:
                active[:] = True
            elif present_a and present_b:
                active[0] = True
                active[1] = True
            elif present_b and present_c:
                active[1] = True
                active[2] = True
            elif present_a and present_c:
                active[0] = True
                active[2] = True
            else:
                pass

            active_current: BoolVec = np.zeros(3, dtype=np.bool_)
            for phase in range(3):
                active_current[phase] = active[phase] and abs(phase_parameter[phase]) > 1e-12
            if np.sum(active_current) == 2:
                first_magnitude: float = 0.0
                second_magnitude: float = 0.0
                for phase in range(3):
                    if active_current[phase]:
                        if first_magnitude == 0.0:
                            first_magnitude = abs(phase_parameter[phase])
                        else:
                            second_magnitude = abs(phase_parameter[phase])
                    else:
                        pass
                if abs(first_magnitude - second_magnitude) > 1e-10:
                    raise ValueError('Two-phase floating-star current magnitudes must match')
                else:
                    pass
            else:
                pass

            Vn: complex = Vn_prev
            dVn: complex = dVn_prev
            error: float = 1.0
            iteration: int = 0
            failed: bool = False
            while error > 1e-6 and iteration <= 25 and np.any(active):
                F: complex = 0j
                dF: complex = 0j
                Fd: complex = 0j
                dFd: complex = 0j
                neutral_step: complex = 1e-6 * (1.0 + 1.0j)
                for phase in range(3):
                    if active[phase]:
                        conductor: int = phase_bus[phase]
                        U: complex = V[conductor] - Vn
                        dU: complex = dV[conductor] - dVn
                        Ud: complex = U - neutral_step
                        parameter: complex = np.conj(phase_parameter[phase])
                        if abs(U) >= 1e-12:
                            current: complex = parameter * U / abs(U)
                            derivative: complex = current * (dU / U
                                                             - np.real(np.conj(U) * dU) / abs(U) ** 2)
                            F += current
                            dF += derivative
                        else:
                            pass
                        if abs(Ud) >= 1e-12:
                            moved_current: complex = parameter * Ud / abs(Ud)
                            moved_derivative: complex = moved_current * (dU / Ud
                                                                          - np.real(np.conj(Ud) * dU)
                                                                          / abs(Ud) ** 2)
                            Fd += moved_current
                            dFd += moved_derivative
                        else:
                            pass
                    else:
                        pass
                if abs(F) < 1e-9:
                    break
                else:
                    Jsec: complex = (Fd - F) / neutral_step
                    if Jsec == 0:
                        failed = True
                        break
                    else:
                        dJsec: complex = (dFd - dF) / neutral_step
                        Vn -= 0.7 * F / Jsec
                        dVn -= 0.7 * (dF / Jsec - F * dJsec / Jsec ** 2)
                        error = abs(Vn - Vn_prev)
                        iteration += 1

            if not failed:
                for phase in range(3):
                    if active[phase]:
                        conductor = phase_bus[phase]
                        U = V[conductor] - Vn
                        dU = dV[conductor] - dVn
                        if abs(U) >= 1e-12:
                            current = np.conj(phase_parameter[phase]) * U / abs(U)
                            dI[conductor] -= current * (dU / U
                                                       - np.real(np.conj(U) * dU) / abs(U) ** 2)
                        else:
                            pass
                    else:
                        pass
            else:
                pass
        else:
            pass

    return dI


@nb.jit(cache=True)
def compute_power_load_derivatives(bus_idx: IntVec,
                                     bus_lookup: IntVec,
                                     V: CxVec,
                                     dV: CxVec,
                                     Sstar: CxVec,
                                     Sfloating: CxVec,
                                     Sdelta: CxVec) -> CxVec:
    """Differentiate ``compute_power_loads`` in the direction ``dV``.

    Branch selection and terminal signs mirror the power-load evaluator. A
    branch with voltage ``U`` draws ``conj(S / U)``; its derivative is
    ``-conj(S / U) * conj(dU / U)``. For a floating star, the selected
    quadratic neutral root is differentiated before its branch currents.

    :param bus_idx: Bus index for each load.
    :param bus_lookup: Full NABC slot to retained conductor lookup.
    :param V: Retained conductor voltages.
    :param dV: Change in retained conductor voltages.
    :param Sstar: Star branch powers.
    :param Sdelta: Delta branch powers.
    :param Sfloating: Floating-star branch-power parameters.
    :return: Directional change in unscaled retained load-current injections.
    """
    n: int = len(V)
    nelm: int = len(bus_idx)
    dI: CxVec = np.zeros(n, dtype=np.complex128)
    zero_load: complex = complex(0.0, 0.0)

    for k in range(nelm):
        f: int = bus_idx[k]
        n: int = 4 * f + 0
        a: int = 4 * f + 1
        b: int = 4 * f + 2
        c: int = 4 * f + 3
        n2: int = bus_lookup[n]
        a2: int = bus_lookup[a]
        b2: int = bus_lookup[b]
        c2: int = bus_lookup[c]
        nn: int = 4 * k + 0
        ab: int = 4 * k + 1
        bc: int = 4 * k + 2
        ca: int = 4 * k + 3

        star: bool = (Sstar[ab] != zero_load or Sstar[bc] != zero_load or Sstar[ca] != zero_load)
        floating: bool = (Sfloating[ab] != zero_load or Sfloating[bc] != zero_load or Sfloating[ca] != zero_load)
        delta: bool = (Sdelta[ab] != zero_load or Sdelta[bc] != zero_load or Sdelta[ca] != zero_load)
        n_connected: bool = (Sstar[nn] != zero_load and n2 >= 0)
        a_connected: bool = (Sstar[ab] != zero_load and a2 >= 0)
        b_connected: bool = (Sstar[bc] != zero_load and b2 >= 0)
        c_connected: bool = (Sstar[ca] != zero_load and c2 >= 0)
        ab_connected: bool = (Sdelta[ab] != zero_load)
        bc_connected: bool = (Sdelta[bc] != zero_load)
        ca_connected: bool = (Sdelta[ca] != zero_load)

        if delta and ab_connected and bc_connected and ca_connected:
            if a2 >= 0 and b2 >= 0 and c2 >= 0:
                Uab: complex = V[a2] - V[b2]
                Ubc: complex = V[b2] - V[c2]
                Uca: complex = V[c2] - V[a2]
                dUab: complex = dV[a2] - dV[b2]
                dUbc: complex = dV[b2] - dV[c2]
                dUca: complex = dV[c2] - dV[a2]
                Iab: complex = np.conj(Sdelta[ab] / Uab)
                Ibc: complex = np.conj(Sdelta[bc] / Ubc)
                Ica: complex = np.conj(Sdelta[ca] / Uca)
                dIab: complex = -Iab * np.conj(dUab / Uab)
                dIbc: complex = -Ibc * np.conj(dUbc / Ubc)
                dIca: complex = -Ica * np.conj(dUca / Uca)
                dI[a2] -= dIab - dIca
                dI[b2] -= dIbc - dIab
                dI[c2] -= dIca - dIbc
            elif a2 < 0 <= b2 and c2 >= 0:
                Ubc = V[b2] - V[c2]
                dUbc = dV[b2] - dV[c2]
                Ibc = np.conj(Sdelta[bc] / Ubc)
                dIbc = -Ibc * np.conj(dUbc / Ubc)
                dI[b2] -= dIbc
                dI[c2] += dIbc
            elif b2 < 0 <= a2 and c2 >= 0:
                Uca = V[c2] - V[a2]
                dUca = dV[c2] - dV[a2]
                Ica = np.conj(Sdelta[ca] / Uca)
                dIca = -Ica * np.conj(dUca / Uca)
                dI[a2] += dIca
                dI[c2] -= dIca
            elif c2 < 0 <= a2 and b2 >= 0:
                Uab = V[a2] - V[b2]
                dUab = dV[a2] - dV[b2]
                Iab = np.conj(Sdelta[ab] / Uab)
                dIab = -Iab * np.conj(dUab / Uab)
                dI[a2] -= dIab
                dI[b2] += dIab
            else:
                pass

        elif delta and ab_connected:
            if a2 >= 0 and b2 >= 0:
                Uab = V[a2] - V[b2]
                dUab = dV[a2] - dV[b2]
                Iab = np.conj(Sdelta[ab] / Uab)
                dIab = -Iab * np.conj(dUab / Uab)
                dI[a2] -= dIab
                dI[b2] += dIab
            else:
                pass
        elif delta and bc_connected:
            if b2 >= 0 and c2 >= 0:
                Ubc = V[b2] - V[c2]
                dUbc = dV[b2] - dV[c2]
                Ibc = np.conj(Sdelta[bc] / Ubc)
                dIbc = -Ibc * np.conj(dUbc / Ubc)
                dI[b2] -= dIbc
                dI[c2] += dIbc
            else:
                pass
        elif delta and ca_connected:
            if c2 >= 0 and a2 >= 0:
                Uca = V[c2] - V[a2]
                dUca = dV[c2] - dV[a2]
                Ica = np.conj(Sdelta[ca] / Uca)
                dIca = -Ica * np.conj(dUca / Uca)
                dI[a2] += dIca
                dI[c2] -= dIca
            else:
                pass

        elif star and a_connected and b_connected and c_connected and n_connected:
            Uan: complex = V[a2] - V[n2]
            Ubn: complex = V[b2] - V[n2]
            Ucn: complex = V[c2] - V[n2]
            dUan: complex = dV[a2] - dV[n2]
            dUbn: complex = dV[b2] - dV[n2]
            dUcn: complex = dV[c2] - dV[n2]
            Ian: complex = np.conj(Sstar[ab] / Uan)
            Ibn: complex = np.conj(Sstar[bc] / Ubn)
            Icn: complex = np.conj(Sstar[ca] / Ucn)
            dIan: complex = -Ian * np.conj(dUan / Uan)
            dIbn: complex = -Ibn * np.conj(dUbn / Ubn)
            dIcn: complex = -Icn * np.conj(dUcn / Ucn)
            dI[a2] -= dIan
            dI[b2] -= dIbn
            dI[c2] -= dIcn
            dI[n2] += dIan + dIbn + dIcn
        elif star and a_connected and b_connected and n_connected:
            Uan = V[a2] - V[n2]
            Ubn = V[b2] - V[n2]
            dUan = dV[a2] - dV[n2]
            dUbn = dV[b2] - dV[n2]
            Ian = np.conj(Sstar[ab] / Uan)
            Ibn = np.conj(Sstar[bc] / Ubn)
            dIan = -Ian * np.conj(dUan / Uan)
            dIbn = -Ibn * np.conj(dUbn / Ubn)
            dI[a2] -= dIan
            dI[b2] -= dIbn
            dI[n2] += dIan + dIbn
        elif star and b_connected and c_connected and n_connected:
            Ubn = V[b2] - V[n2]
            Ucn = V[c2] - V[n2]
            dUbn = dV[b2] - dV[n2]
            dUcn = dV[c2] - dV[n2]
            Ibn = np.conj(Sstar[bc] / Ubn)
            Icn = np.conj(Sstar[ca] / Ucn)
            dIbn = -Ibn * np.conj(dUbn / Ubn)
            dIcn = -Icn * np.conj(dUcn / Ucn)
            dI[b2] -= dIbn
            dI[c2] -= dIcn
            dI[n2] += dIbn + dIcn
        elif star and a_connected and c_connected and n_connected:
            Uan = V[a2] - V[n2]
            Ucn = V[c2] - V[n2]
            dUan = dV[a2] - dV[n2]
            dUcn = dV[c2] - dV[n2]
            Ian = np.conj(Sstar[ab] / Uan)
            Icn = np.conj(Sstar[ca] / Ucn)
            dIan = -Ian * np.conj(dUan / Uan)
            dIcn = -Icn * np.conj(dUcn / Ucn)
            dI[a2] -= dIan
            dI[c2] -= dIcn
            dI[n2] += dIan + dIcn
        elif star and a_connected and n_connected:
            Uan = V[a2] - V[n2]
            dUan = dV[a2] - dV[n2]
            Ian = np.conj(Sstar[ab] / Uan)
            dIan = -Ian * np.conj(dUan / Uan)
            dI[a2] -= dIan
            dI[n2] += dIan
        elif star and b_connected and n_connected:
            Ubn = V[b2] - V[n2]
            dUbn = dV[b2] - dV[n2]
            Ibn = np.conj(Sstar[bc] / Ubn)
            dIbn = -Ibn * np.conj(dUbn / Ubn)
            dI[b2] -= dIbn
            dI[n2] += dIbn
        elif star and c_connected and n_connected:
            Ucn = V[c2] - V[n2]
            dUcn = dV[c2] - dV[n2]
            Icn = np.conj(Sstar[ca] / Ucn)
            dIcn = -Icn * np.conj(dUcn / Ucn)
            dI[c2] -= dIcn
            dI[n2] += dIcn

        elif star and a_connected and b_connected and c_connected:
            Uan = V[a2]
            Ubn = V[b2]
            Ucn = V[c2]
            dUan = dV[a2]
            dUbn = dV[b2]
            dUcn = dV[c2]
            Ian = np.conj(Sstar[ab] / Uan)
            Ibn = np.conj(Sstar[bc] / Ubn)
            Icn = np.conj(Sstar[ca] / Ucn)
            dI[a2] += Ian * np.conj(dUan / Uan)
            dI[b2] += Ibn * np.conj(dUbn / Ubn)
            dI[c2] += Icn * np.conj(dUcn / Ucn)
        elif star and a_connected and b_connected:
            Uan = V[a2]
            Ubn = V[b2]
            Ian = np.conj(Sstar[ab] / Uan)
            Ibn = np.conj(Sstar[bc] / Ubn)
            dI[a2] += Ian * np.conj(dV[a2] / Uan)
            dI[b2] += Ibn * np.conj(dV[b2] / Ubn)
        elif star and b_connected and c_connected:
            Ubn = V[b2]
            Ucn = V[c2]
            Ibn = np.conj(Sstar[bc] / Ubn)
            Icn = np.conj(Sstar[ca] / Ucn)
            dI[b2] += Ibn * np.conj(dV[b2] / Ubn)
            dI[c2] += Icn * np.conj(dV[c2] / Ucn)
        elif star and a_connected and c_connected:
            Uan = V[a2]
            Ucn = V[c2]
            Ian = np.conj(Sstar[ab] / Uan)
            Icn = np.conj(Sstar[ca] / Ucn)
            dI[a2] += Ian * np.conj(dV[a2] / Uan)
            dI[c2] += Icn * np.conj(dV[c2] / Ucn)
        elif star and a_connected:
            Uan = V[a2]
            Ian = np.conj(Sstar[ab] / Uan)
            dI[a2] += Ian * np.conj(dV[a2] / Uan)
        elif star and b_connected:
            Ubn = V[b2]
            Ibn = np.conj(Sstar[bc] / Ubn)
            dI[b2] += Ibn * np.conj(dV[b2] / Ubn)
        elif star and c_connected:
            Ucn = V[c2]
            Icn = np.conj(Sstar[ca] / Ucn)
            dI[c2] += Icn * np.conj(dV[c2] / Ucn)

        elif floating:
            if a2 >= 0 and b2 >= 0 and c2 >= 0:
                Ua: complex = V[a2]
                Ub: complex = V[b2]
                Uc: complex = V[c2]
                dUa: complex = dV[a2]
                dUb: complex = dV[b2]
                dUc: complex = dV[c2]
                Sa: complex = Sfloating[ab]
                Sb: complex = Sfloating[bc]
                Sc: complex = Sfloating[ca]
                Ia, Ib, Ic, Un = floating_star_powers(
                    Ua=Ua,
                    Ub=Ub,
                    Uc=Uc,
                    Sa=Sa,
                    Sb=Sb,
                    Sc=Sc)
            elif a2 >= 0 and b2 >= 0:
                Ua = V[a2]
                Ub = V[b2]
                Uc = zero_load
                dUa = dV[a2]
                dUb = dV[b2]
                dUc = zero_load
                Sa = Sfloating[ab]
                Sb = Sfloating[bc]
                Sc = zero_load
                Ia, Ib, Ic, Un = floating_star_powers(
                    Ua=Ua,
                    Ub=Ub,
                    Uc=Uc,
                    Sa=Sa,
                    Sb=Sb,
                    Sc=Sc)
            elif b2 >= 0 and c2 >= 0:
                Ua = zero_load
                Ub = V[b2]
                Uc = V[c2]
                dUa = zero_load
                dUb = dV[b2]
                dUc = dV[c2]
                Sa = zero_load
                Sb = Sfloating[bc]
                Sc = Sfloating[ca]
                Ia, Ib, Ic, Un = floating_star_powers(
                    Ua=Ua,
                    Ub=Ub,
                    Uc=Uc,
                    Sa=Sa,
                    Sb=Sb,
                    Sc=Sc)
            elif a2 >= 0 and c2 >= 0:
                Ua = V[a2]
                Ub = zero_load
                Uc = V[c2]
                dUa = dV[a2]
                dUb = zero_load
                dUc = dV[c2]
                Sa = Sfloating[ab]
                Sb = zero_load
                Sc = Sfloating[ca]
                Ia, Ib, Ic, Un = floating_star_powers(
                    Ua=Ua,
                    Ub=Ub,
                    Uc=Uc,
                    Sa=Sa,
                    Sb=Sb,
                    Sc=Sc)
            else:
                Ua = zero_load
                Ub = zero_load
                Uc = zero_load
                dUa = zero_load
                dUb = zero_load
                dUc = zero_load
                Sa = zero_load
                Sb = zero_load
                Sc = zero_load
                Ia, Ib, Ic, Un = zero_load, zero_load, zero_load, zero_load

            # The selected neutral root satisfies A*Un**2 + B*Un + C = 0.
            A: complex = Sa + Sb + Sc
            if abs(A) <= abs(complex(1e-10, 1e-10)):
                A = complex(1e-10, 1e-10)
            else:
                pass
            B: complex = -(Sa * (Ub + Uc) + Sb * (Ua + Uc) + Sc * (Ua + Ub))
            dB: complex = -(Sa * (dUb + dUc) + Sb * (dUa + dUc) + Sc * (dUa + dUb))
            dC: complex = (Sa * (dUb * Uc + Ub * dUc)
                           + Sb * (dUa * Uc + Ua * dUc)
                           + Sc * (dUa * Ub + Ua * dUb))
            if Un != 0j and 2.0 * A * Un + B != 0j:
                dUn: complex = -(dB * Un + dC) / (2.0 * A * Un + B)
            else:
                dUn = zero_load

            if a2 >= 0 and abs(Ua) > abs(complex(1e-10, 1e-10)) and abs(Ua - Un) > abs(complex(1e-10, 1e-10)):
                dI[a2] += Ia * np.conj((dUa - dUn) / (Ua - Un))
            else:
                pass
            if b2 >= 0 and abs(Ub) > abs(complex(1e-10, 1e-10)) and abs(Ub - Un) > abs(complex(1e-10, 1e-10)):
                dI[b2] += Ib * np.conj((dUb - dUn) / (Ub - Un))
            else:
                pass
            if c2 >= 0 and abs(Uc) > abs(complex(1e-10, 1e-10)) and abs(Uc - Un) > abs(complex(1e-10, 1e-10)):
                dI[c2] += Ic * np.conj((dUc - dUn) / (Uc - Un))
            else:
                pass
        else:
            pass

    return dI

@nb.njit(cache=True)
def calc_current(Sdelta: complex, Va: complex, Vb: complex):
    """
    Performs I = conj(S / (Va - Vb))
    :param Sdelta:
    :param Va:
    :param Vb:
    :return:
    """
    dV = Va - Vb
    if dV != 0.0:
        return np.conj(Sdelta / dV)
    else:
        return 1e20


@nb.jit(cache=True)
def compute_power_loads(bus_idx: IntVec,
                        bus_lookup: IntVec,
                        V: CxVec,
                        Sstar: CxVec,
                        Sfloating: CxVec,
                        Sdelta: CxVec) -> Tuple[CxVec, CxVec, CxVec]:
    """Accumulate constant-power load injections in retained NABC order.

    :param bus_idx: Bus index for each load.
    :param bus_lookup: Full NABC slot to retained conductor lookup.
    :param V: Retained conductor voltages.
    :param Sstar: Star branch powers.
    :param Sfloating: Floating-star branch powers.
    :param Sdelta: Delta branch powers.
    :return: Injection currents, linearized admittances, and floating neutral voltages.
    """
    n = len(V)
    nelm = len(bus_idx)

    # I = np.zeros(n, dtype=nb.complex128)
    I = np.zeros(n, dtype=np.complex128)

    # zero_load = nb.complex128(0.0)
    zero_load = 0.0 + 0.0j

    # Un_floating = np.zeros(len(V), dtype=nb.complex128)
    Un_floating = np.zeros(len(V), dtype=np.complex128)

    for k in range(nelm):

        f = bus_idx[k]

        n = 4 * f + 0
        a = 4 * f + 1
        b = 4 * f + 2
        c = 4 * f + 3

        n2 = bus_lookup[n]
        a2 = bus_lookup[a]
        b2 = bus_lookup[b]
        c2 = bus_lookup[c]

        nn = 4 * k + 0
        ab = 4 * k + 1
        bc = 4 * k + 2
        ca = 4 * k + 3

        star = (Sstar[ab] != zero_load or Sstar[bc] != zero_load or Sstar[ca] != zero_load)
        floating = (Sfloating[ab] != zero_load or Sfloating[bc] != zero_load or Sfloating[ca] != zero_load)
        delta = (Sdelta[ab] != zero_load or Sdelta[bc] != zero_load or Sdelta[ca] != zero_load)

        n_connected = (Sstar[nn] != zero_load and n2 >= 0)
        a_connected = (Sstar[ab] != zero_load and a2 >= 0)
        b_connected = (Sstar[bc] != zero_load and b2 >= 0)
        c_connected = (Sstar[ca] != zero_load and c2 >= 0)

        ab_connected = (Sdelta[ab] != zero_load)
        bc_connected = (Sdelta[bc] != zero_load)
        ca_connected = (Sdelta[ca] != zero_load)

        if delta and ab_connected and bc_connected and ca_connected:

            if a2 >= 0 and b2 >= 0 and c2 >= 0:
                I[a2] -= calc_current(Sdelta[ab],V[a2], V[b2])
                I[a2] -= calc_current(Sdelta[ca],V[a2], V[c2])
                I[b2] -= calc_current(Sdelta[ab],V[b2], V[a2])
                I[b2] -= calc_current(Sdelta[bc],V[b2], V[c2])
                I[c2] -= calc_current(Sdelta[bc],V[c2], V[b2])
                I[c2] -= calc_current(Sdelta[ca],V[c2], V[a2])

            elif a2 < 0 <= b2 and c2 >= 0:
                I[b2] -= calc_current(Sdelta[bc], V[b2], V[c2])
                I[c2] -= calc_current(Sdelta[bc], V[c2], V[b2])

            elif b2 < 0 <= a2 and c2 >= 0:
                I[a2] -= calc_current(Sdelta[ca], V[a2], V[c2])
                I[c2] -= calc_current(Sdelta[ca], V[c2], V[a2])

            elif c2 < 0 <= a2 and b2 >= 0:
                I[a2] -= calc_current(Sdelta[ab], V[a2], V[b2])
                I[b2] -= calc_current(Sdelta[ab], V[b2], V[a2])

        elif delta and ab_connected:

            if a2 >= 0 and b2 >= 0:
                I[a2] -= calc_current(Sdelta[ab], V[a2], V[b2])
                I[b2] -= calc_current(Sdelta[ab], V[b2], V[a2])
            else:
                pass

        elif delta and bc_connected:

            if b2 >= 0 and c2 >= 0:
                I[b2] -= calc_current(Sdelta[bc], V[b2], V[c2])
                I[c2] -= calc_current(Sdelta[bc], V[c2], V[b2])
            else:
                pass

        elif delta and ca_connected:

            if c2 >= 0 and a2 >= 0:
                I[c2] -= calc_current(Sdelta[ca], V[c2], V[a2])
                I[a2] -= calc_current(Sdelta[ca], V[a2], V[c2])
            else:
                pass

        elif star and a_connected and b_connected and c_connected and n_connected:

            Ian = calc_current(Sstar[ab], V[a2], V[n2])
            Ibn = calc_current(Sstar[bc], V[b2], V[n2])
            Icn = calc_current(Sstar[ca], V[c2], V[n2])

            I[a2] -= Ian
            I[b2] -= Ibn
            I[c2] -= Icn
            I[n2] += (Ian + Ibn + Icn)

        elif star and a_connected and b_connected and n_connected:

            Ian = calc_current(Sstar[ab], V[a2], V[n2])
            Ibn = calc_current(Sstar[bc], V[b2], V[n2])

            I[a2] -= Ian
            I[b2] -= Ibn
            I[n2] += (Ian + Ibn)

        elif star and b_connected and c_connected and n_connected:

            Ibn = calc_current(Sstar[bc], V[b2], V[n2])
            Icn = calc_current(Sstar[ca], V[c2], V[n2])

            I[b2] -= Ibn
            I[c2] -= Icn
            I[n2] += (Ibn + Icn)

        elif star and a_connected and c_connected and n_connected:

            Ian = calc_current(Sstar[ab], V[a2], V[n2])
            Icn = calc_current(Sstar[ca], V[c2], V[n2])

            I[a2] -= Ian
            I[c2] -= Icn
            I[n2] += (Ian + Icn)

        elif star and a_connected and n_connected:

            Ian = calc_current(Sstar[ab], V[a2], V[n2])
            I[a2] -= Ian
            I[n2] += Ian

        elif star and b_connected and n_connected:

            Ibn = calc_current(Sstar[bc], V[b2], V[n2])
            I[b2] -= Ibn
            I[n2] += Ibn

        elif star and c_connected and n_connected:

            Icn = calc_current(Sstar[ca], V[c2], V[n2])
            I[c2] -= Icn
            I[n2] += Icn

        elif star and a_connected and b_connected and c_connected:

            if a2 >= 0:
                I[a2] -= np.conj(Sstar[ab] / (V[a2]))
            if b2 >= 0:
                I[b2] -= np.conj(Sstar[bc] / (V[b2]))
            if c2 >= 0:
                I[c2] -= np.conj(Sstar[ca] / (V[c2]))

        elif star and a_connected and b_connected:

            if a2 >= 0:
                I[a2] -= np.conj(Sstar[ab] / (V[a2]))
            if b2 >= 0:
                I[b2] -= np.conj(Sstar[bc] / (V[b2]))

        elif star and b_connected and c_connected:

            if b2 >= 0:
                I[b2] -= np.conj(Sstar[bc] / (V[b2]))
            if c2 >= 0:
                I[c2] -= np.conj(Sstar[ca] / (V[c2]))

        elif star and a_connected and c_connected:

            if a2 >= 0:
                I[a2] -= np.conj(Sstar[ab] / (V[a2]))
            if c2 >= 0:
                I[c2] -= np.conj(Sstar[ca] / (V[c2]))

        elif star and a_connected:
            if a2 >= 0:
                I[a2] -= np.conj(Sstar[ab] / (V[a2]))

        elif star and b_connected:
            if b2 >= 0:
                I[b2] -= np.conj(Sstar[bc] / (V[b2]))

        elif star and c_connected:
            if c2 >= 0:
                I[c2] -= np.conj(Sstar[ca] / (V[c2]))

        elif floating:

            if a2 >= 0 and b2 >= 0 and c2 >= 0:
                Ia, Ib, Ic, Un = floating_star_powers(V[a2], V[b2], V[c2],
                                                      Sfloating[ab], Sfloating[bc], Sfloating[ca])
                I[a2] -= Ia
                I[b2] -= Ib
                I[c2] -= Ic

            elif a2 >= 0 and b2 >= 0:
                Ia, Ib, Ic, Un = floating_star_powers(V[a2], V[b2], zero_load,
                                                      Sfloating[ab], Sfloating[bc], zero_load)
                I[a2] -= Ia
                I[b2] -= Ib

            elif b2 >= 0 and c2 >= 0:
                Ia, Ib, Ic, Un = floating_star_powers(zero_load, V[b2], V[c2],
                                                      zero_load, Sfloating[bc], Sfloating[ca])
                I[b2] -= Ib
                I[c2] -= Ic

            elif a2 >= 0 and c2 >= 0:
                Ia, Ib, Ic, Un = floating_star_powers(V[a2], zero_load, V[c2],
                                                      Sfloating[ab], zero_load, Sfloating[ca])
                I[a2] -= Ia
                I[c2] -= Ic

            else:
                Un = zero_load

            if a2 >= 0:
                Un_floating[a2] = Un
            else:
                pass
            if b2 >= 0:
                Un_floating[b2] = Un
            else:
                pass
            if c2 >= 0:
                Un_floating[c2] = Un
            else:
                pass

        else:
            pass

    # Y_power_linear = np.zeros_like(I, dtype=nb.complex128)
    Y_power_linear = np.zeros_like(I, dtype=np.complex128)
    for i in range(len(V)):
        if abs(V[i]) > 1e-12:
            Y_power_linear[i] = I[i] / V[i]

    return I, Y_power_linear, Un_floating


@nb.jit(cache=True)
def expand3ph(x: np.ndarray) -> np.ndarray:
    """
    Expands a numpy array to 3-pase copying the same values
    :param x:
    :return:
    """
    n = len(x)
    idx4 = np.array([0, 1, 2, 3])
    x4 = np.zeros(4 * n, dtype=x.dtype)

    for k in range(n):
        x4[4 * k + idx4] = x[k]
    return x4


@nb.jit(cache=True)
def slice_indices(pq: IntVec, bus_lookup: IntVec) -> IntVec:
    """
    Slice the indices based on the bus_lookup
    :param pq: original bus indices
    :param bus_lookup: mapping between original and sliced bus indices
    :return:
    """

    max_nnz = len(pq)
    vec = np.zeros(max_nnz, dtype=nb.int64)
    counter = 0
    for pq_idx in pq:
        val = bus_lookup[pq_idx]
        if val > -1:
            vec[counter] = val
            counter += 1

    return vec[:counter]


@nb.jit(cache=True)
def expand_indices_3ph(x: np.ndarray) -> np.ndarray:
    """
    Expands a numpy array to 3-pase copying the same values
    :param x:
    :return:
    """
    n = len(x)
    idx4 = np.array([0, 1, 2, 3])
    x4 = np.zeros(4 * n, dtype=nb.int64)

    for k in range(n):
        x4[4 * k + idx4] = 4 * x[k] + idx4

    return x4


@nb.jit(cache=True)
def expand_slice_indices_3ph(x: np.ndarray, bus_lookup: IntVec) -> np.ndarray:
    """
    Expands and slices a numpy array to 3-phase copying the same values
    :param x:
    :param bus_lookup:
    :return:
    """
    x3 = expand_indices_3ph(x)

    x3_final = slice_indices(x3, bus_lookup)
    return np.sort(x3_final)


@nb.jit(cache=True)
def expandVoltage3ph(V0: CxVec) -> CxVec:
    """
    Expands a numpy array to 3-pase copying the same values
    :param V0: array of bus voltages in positive sequence
    :return: Array of three-phase voltages in 3-phase ABC
    """
    n = len(V0)
    idx4 = np.array([0, 1, 2, 3], dtype=nb.int64)

    angles = np.array([0, 0, -2 * np.pi / 3, 2 * np.pi / 3], dtype=nb.float64)

    Vm = np.abs(V0)
    Va = np.angle(V0)
    x4 = np.zeros(4 * n, dtype=nb.complex128)

    for k in range(n):
        x4[4 * k] = 1e-4 * np.exp(1j * Va[k])
        x4[4 * k + idx4[1:]] = Vm[k] * np.exp(1j * (Va[k] + angles[1:]))

    return x4


@nb.jit(cache=True)
def expand_magnitudes(magnitude: CxVec, lookup: IntVec) -> CxVec:
    """
    Expands the masked magnitude using the lookup saving zeros where the lookup is -1,
    which means that this bus did not exist, and it was previously eliminated.
    :param magnitude: The magnitude to expand, for instance, the voltage vector at each bus
    :param lookup: The vector which contains the information about the existing and eliminated buses
    :return: magnitude_expanded
    """
    n_buses_total = len(lookup)
    magnitude_expanded = np.zeros(n_buses_total, dtype=nb.complex128)
    for i, value in enumerate(lookup):
        if value < 0:
            magnitude_expanded[i] = nb.complex128(0.0)
        else:
            magnitude_expanded[i] = magnitude[value]

    return magnitude_expanded


@nb.jit(cache=True)
def expand_matrix(magnitude: np.ndarray, lookup: IntVec) -> CxMat:
    """
    Expands a matrix by adding zero rows and columns based on the lookup indices.
    If a lookup value is negative, the corresponding row and column in the matrix
    will be replaced by zeros.

    :param magnitude: 2D numpy array (matrix to expand)
    :param lookup: List of indices for lookup
    :return: Expanded matrix with zeros in the rows and columns where lookup values are negative
    """
    n_buses_total = len(lookup)

    # Initialize the expanded matrix as a zero matrix of the same size as the lookup
    magnitude_expanded = np.zeros((n_buses_total, n_buses_total), dtype=nb.complex128)

    for i, value in enumerate(lookup):
        if value >= 0:
            # Assign the value from the original matrix to the expanded matrix
            magnitude_expanded[i, i] = magnitude[value, value]
        # Else, the row and column for that index will already be zeros by default.

    return magnitude_expanded


def passive_neutral_reduction(nc: NumericalCircuit, ybus: csc_matrix,
                              mask: BoolVec) -> Tuple[IntVec, csc_matrix | None]:
    """Eliminate linear, zero-injection conductors by exact Schur reduction.

    The voltage map reconstructs eliminated voltages without adding a ground or
    constraining a phase common mode. Singular blocks remain explicit.

    :param nc: Compiled network and nonlinear injection connections.
    :param ybus: Admittance matrix after removing absent or grounded conductors.
    :param mask: Full NABC conductor mask corresponding to ybus.
    :return: Retained indices and optional full-voltage reconstruction matrix.
    """
    candidates: BoolVec = np.flatnonzero(mask) % 4 == 0
    protected: BoolVec = np.zeros(nc.nbus, dtype=bool)
    # Explicit star P/I loads need their neutral voltage during each iteration.
    for k in range(nc.load_data.nelm):
        if nc.load_data.S3_star[4 * k] != 0 or nc.load_data.I3_star[4 * k] != 0:
            protected[nc.load_data.bus_idx[k]] = True
        else:
            pass
    candidates &= ~np.repeat(protected, 4)[mask]
    neutral_candidates: BoolVec = candidates.copy()
    # Device presence matters: cancelling scheduled powers do not make a bus passive.
    protected = ((nc.bus_data.bus_types != BusMode.PQ_tpe.value)
                 | nc.bus_data.is_vm_controlled | nc.bus_data.is_va_controlled)
    for data in (nc.load_data, nc.generator_data, nc.battery_data, nc.shunt_data):
        protected[data.bus_idx[data.active.astype(bool)]] = True
    for data in (nc.generator_data, nc.battery_data, nc.shunt_data):
        remote: IntVec = data.controllable_bus_idx[data.active.astype(bool)]
        protected[remote[remote >= 0]] = True
    for data in (nc.hvdc_data, nc.vsc_data):
        active: BoolVec = data.active.astype(bool)
        protected[data.F[active]] = True
        protected[data.T[active]] = True
    lookup: IntVec = lookup_from_mask(mask)
    for bus in np.flatnonzero(~protected):
        phases: IntVec = lookup[4 * bus + np.arange(1, 4)]
        if np.all(phases >= 0):
            # Keep a local free common mode explicit for reference handling.
            local_block: CxMat = ybus[phases, :][:, phases].toarray()
            if np.linalg.matrix_rank(local_block,
                    tol=32 * np.finfo(float).eps * np.max(abs(local_block))) == 3:
                candidates[phases] = True
            else:
                pass
        else:
            pass
    # If a phase group is singular, preserve the previous neutral-only reduction.
    for selection in (candidates, neutral_candidates):
        keep: IntVec = np.flatnonzero(~selection)
        eliminated: IntVec = np.flatnonzero(selection)
        if len(eliminated) == 0:
            return keep, None
        else:
            pass
        internal_block: csc_matrix = ybus[eliminated, :][:, eliminated].tocsc()
        scale: Vec = np.asarray(abs(internal_block).max(axis=1).toarray()).ravel()
        if np.all(scale > 0) and np.all(np.isfinite(scale)):
            scaling: csc_matrix = diags(1.0 / scale, format='csc')
            try:
                factor: SuperLU = splu(scaling @ internal_block)
                # Individually invertible buses may form a singular floating
                # group. Roundoff pivots retain the explicit physical problem.
                valid: bool = np.all(abs(factor.U.diagonal()) > 32 * np.finfo(float).eps * len(eliminated)
                    * max(1.0, np.max(abs(factor.U.data))))
                if valid:
                    coupling: csc_matrix = (scaling @ ybus[eliminated, :][:, keep]).tocsc()
                    boundary: IntVec = np.flatnonzero(np.diff(coupling.indptr))
                    # Only connected retained columns need a dense solve workspace.
                    response: CxMat = -factor.solve(coupling[:, boundary].toarray())
                    lift: lil_matrix = lil_matrix((ybus.shape[0], len(keep)), dtype=complex)
                    lift[keep, np.arange(len(keep))] = 1.0
                    lift[np.ix_(eliminated, boundary)] = response
                    return keep, lift.tocsc()
                else:
                    pass
            except RuntimeError:
                pass
            else:
                pass
        else:
            pass
    return np.arange(ybus.shape[0]), None


def include_local_couplings_in_ybus_pattern(ybus: csc_matrix,
                                             bus_lookup: IntVec) -> csc_matrix:
    """Store zero CSC entries for every retained terminal pair at each bus.

    A local load or source can couple any NABC terminal to any other one.
    Its derivative must have a CSC slot even when the network admittance at
    that position is zero. Adding stored zeros leaves ``Ybus @ V`` unchanged.

    :param ybus: Retained network admittance in CSC format.
    :param bus_lookup: Full NABC to retained conductor lookup.
    :return: Numerically identical admittance with local device positions stored.
    """
    nbus: int = ybus.shape[0]
    original_bus: IntVec = np.empty(nbus, dtype=np.int32)
    for full in range(len(bus_lookup)):
        retained: int = bus_lookup[full]
        if retained >= 0:
            original_bus[retained] = full // 4
        else:
            pass

    indptr: IntVec = np.empty(nbus + 1, dtype=ybus.indptr.dtype)
    indices: IntVec = np.empty(ybus.nnz + 4 * nbus, dtype=ybus.indices.dtype)
    data: CxVec = np.empty(ybus.nnz + 4 * nbus, dtype=ybus.data.dtype)
    nnz: int = 0
    indptr[0] = 0
    for column in range(nbus):
        start: int = ybus.indptr[column]
        end: int = ybus.indptr[column + 1]
        old_rows: IntVec = ybus.indices[start:end]
        bus: int = original_bus[column]
        terminals: IntVec = bus_lookup[4 * bus:4 * bus + 4]
        rows: IntVec = np.union1d(old_rows, terminals[terminals >= 0])
        size: int = len(rows)
        indices[nnz:nnz + size] = rows
        data[nnz:nnz + size] = 0j
        data[nnz + np.searchsorted(rows, old_rows)] = ybus.data[start:end]
        nnz += size
        indptr[column + 1] = nnz
    return csc_matrix((data[:nnz], indices[:nnz], indptr), shape=ybus.shape)


def asynchronous_current_derivative_blocks(
        voltage: CxVec,
        bus_lookup: IntVec,
        generator_buses: IntVec,
        generator_indices: IntVec,
        connections: IntVec,
        r0: Vec,
        x0: Vec,
        rs: Vec,
        xs: Vec,
        xm: Vec,
        rr: Vec,
        xr: Vec,
        power: Vec,
        nominal_power: Vec,
        system_base: float) -> tuple[np.ndarray, np.ndarray]:
    """Differentiate asynchronous ABC currents, including their solved slip.

    The machine slip solves the same active-power equation as the evaluator.
    Implicit differentiation gives ``ds = -dF_voltage / dF_slip``; the current
    derivative then includes both ``Yabc @ dV`` and ``dYabc/ds @ V * ds``.
    Each returned block is indexed by original bus, injected terminal, and
    changed terminal, in NABC order.

    :param voltage: Retained conductor voltages.
    :param bus_lookup: Full NABC to retained conductor lookup.
    :param generator_buses: Original bus index of each generator.
    :param generator_indices: Active asynchronous generator indices.
    :param connections: Generator connection codes.
    :param r0: Zero-sequence resistance on system base.
    :param x0: Zero-sequence reactance on system base.
    :param rs: Stator resistance on machine base.
    :param xs: Stator reactance on machine base.
    :param xm: Magnetising reactance on machine base.
    :param rr: Rotor resistance on machine base.
    :param xr: Rotor reactance on machine base.
    :param power: Active-power setpoints.
    :param nominal_power: Machine ratings.
    :param system_base: System MVA base.
    :return: Local angle and magnitude injection derivatives in system pu.
    """
    nbus: int = len(bus_lookup) // 4
    d_va: np.ndarray = np.zeros((nbus, 4, 4), dtype=np.complex128)
    d_vm: np.ndarray = np.zeros((nbus, 4, 4), dtype=np.complex128)
    rotation: CxVec = np.exp(-2j * np.pi / 3 * np.arange(3))

    for gen in generator_indices:
        bus: int = generator_buses[gen]
        phases: IntVec = bus_lookup[4 * bus + np.array((1, 2, 3))]
        phase_voltage: CxVec = voltage[phases]
        u1: complex = phase_voltage @ rotation.conj() / 3.0
        slip: float = solve_slip(
            f=active_power_mismatch,
            a=-0.05,
            b=-1e-6,
            tol=1e-14,
            max_iter=200,
            u=u1,
            Rs=rs[gen],
            Xs=xs[gen],
            Xm=xm[gen],
            Rr=rr[gen],
            Xr=xr[gen],
            P=power[gen],
            Sr=nominal_power[gen])
        if connections[gen] == ShuntConnectionType.GroundedStar.idx():
            y0: complex = system_base / (nominal_power[gen] * complex(r0[gen], x0[gen]))
        else:
            y0 = 0j

        z1: complex = asynchronous_impedance(
            slip=slip,
            Rs=rs[gen],
            Xs=xs[gen],
            Xm=xm[gen],
            Rr=rr[gen],
            Xr=xr[gen])
        z2: complex = asynchronous_impedance(
            slip=2.0 - slip,
            Rs=rs[gen],
            Xs=xs[gen],
            Xm=xm[gen],
            Rr=rr[gen],
            Xr=xr[gen])
        magnetising: complex = 1j * xm[gen]
        rotor1: complex = rr[gen] / slip + 1j * xr[gen]
        rotor2: complex = rr[gen] / (2.0 - slip) + 1j * xr[gen]
        dz1_ds: complex = (magnetising ** 2 / (magnetising + rotor1) ** 2
                           * (-rr[gen] / slip ** 2))
        dz2_ds: complex = (magnetising ** 2 / (magnetising + rotor2) ** 2
                           * (rr[gen] / (2.0 - slip) ** 2))
        dy1_ds: complex = -dz1_ds / z1 ** 2
        dy2_ds: complex = -dz2_ds / z2 ** 2
        y1: complex = 1.0 / z1
        admittance: np.ndarray = fortescue_012_to_abc(
            z0=y0,
            z1=y1,
            z2=1.0 / z2)
        admittance_slope: np.ndarray = fortescue_012_to_abc(
            z0=0j,
            z1=dy1_ds,
            z2=dy2_ds)
        active_slope: float = -abs(u1) ** 2 * dy1_ds.real

        for phase in range(3):
            change: CxVec = np.zeros(3, dtype=np.complex128)
            change[phase] = 1j * phase_voltage[phase]
            d_u1: complex = change @ rotation.conj() / 3.0
            d_active: float = -2.0 * np.real(np.conj(u1) * d_u1) * y1.real
            d_slip: float = -d_active / active_slope
            d_current: CxVec = -(admittance @ change
                                  + (admittance_slope @ phase_voltage) * d_slip) * nominal_power[gen] / system_base
            d_va[bus, 1:4, phase + 1] += d_current

            change[phase] = phase_voltage[phase] / abs(phase_voltage[phase])
            d_u1 = change @ rotation.conj() / 3.0
            d_active = -2.0 * np.real(np.conj(u1) * d_u1) * y1.real
            d_slip = -d_active / active_slope
            d_current = -(admittance @ change
                          + (admittance_slope @ phase_voltage) * d_slip) * nominal_power[gen] / system_base
            d_vm[bus, 1:4, phase + 1] += d_current

    return d_va, d_vm


@nb.njit
def append_positive_sequence_control_jacobian(
        Jx: Vec,
        Jp: IntVec,
        Ji: IntVec,
        voltage: CxVec,
        idx_dVa: IntVec,
        idx_dVm: IntVec,
        idx_dP: IntVec,
        lookup_p: IntVec,
        lookup_q: IntVec,
        lookup_angle: IntVec,
        lookup_magnitude: IntVec,
        phases: np.ndarray,
        rotation: CxVec,
        limited: BoolVec,
        source_dq: np.ndarray) -> CSC:
    """Append controlled-Q columns and U1 or limited-Q rows to a CSC Jacobian.

    :param Jx: Voltage-block CSC data.
    :param Jp: Voltage-block CSC column pointers.
    :param Ji: Voltage-block CSC row indices.
    :param voltage: Retained conductor voltages.
    :param idx_dVa: Angle variable conductors.
    :param idx_dVm: Magnitude variable conductors.
    :param idx_dP: Real current-residual conductors.
    :param lookup_p: Retained conductor to real residual row.
    :param lookup_q: Retained conductor to imaginary residual row.
    :param lookup_angle: Retained conductor to angle column.
    :param lookup_magnitude: Retained conductor to magnitude column.
    :param phases: Retained ABC phase indices for each controlled bus.
    :param rotation: Positive-sequence ABC rotation.
    :param limited: Whether each control uses a fixed-Q equation.
    :param source_dq: Current-injection derivatives by control and NABC terminal.
    :return: Complete real CSC Jacobian before common-mode row replacement.
    """
    n_angle: int = len(idx_dVa)
    n_voltage: int = n_angle + len(idx_dVm)
    n_controls: int = len(limited)
    q_columns: np.ndarray = np.zeros((n_voltage, n_controls))
    control_rows: np.ndarray = np.zeros((n_controls, n_voltage))
    unit: CxVec = voltage / np.abs(voltage)

    for control in range(n_controls):
        u1: complex = 0j
        for phase in range(3):
            u1 += voltage[phases[control, phase]] * np.conj(rotation[phase]) / 3.0

        for phase in range(3):
            conductor: int = phases[control, phase]
            q_change: complex = -source_dq[control, phase + 1] / unit[conductor]
            p_row: int = lookup_p[conductor]
            q_row: int = lookup_q[conductor]
            if p_row >= 0:
                q_columns[p_row, control] += q_change.real
            else:
                pass
            if q_row >= 0:
                q_columns[len(idx_dP) + q_row, control] += q_change.imag
            else:
                pass

            if not limited[control]:
                factor: complex = np.conj(rotation[phase]) / 3.0
                angle_column: int = lookup_angle[conductor]
                magnitude_column: int = lookup_magnitude[conductor]
                if angle_column >= 0:
                    d_u1: complex = 1j * voltage[conductor] * factor
                    control_rows[control, angle_column] = np.real(np.conj(u1) * d_u1) / abs(u1)
                else:
                    pass
                if magnitude_column >= 0:
                    d_u1 = unit[conductor] * factor
                    control_rows[control, n_angle + magnitude_column] = (
                        np.real(np.conj(u1) * d_u1) / abs(u1))
                else:
                    pass
            else:
                pass

    # Count before allocating so the completed matrix has only stored entries.
    nnz: int = len(Jx)
    for column in range(n_voltage):
        for control in range(n_controls):
            if control_rows[control, column] != 0.0:
                nnz += 1
            else:
                pass
    for control in range(n_controls):
        for row in range(n_voltage):
            if q_columns[row, control] != 0.0:
                nnz += 1
            else:
                pass
        if limited[control]:
            nnz += 1
        else:
            pass

    # Numba jitclass constructors do not accept keyword arguments.
    result: CSC = CSC(
        n_voltage + n_controls,
        n_voltage + n_controls,
        nnz,
        False)
    position: int = 0
    for column in range(n_voltage):
        result.indptr[column] = position
        for k in range(Jp[column], Jp[column + 1]):
            result.indices[position] = Ji[k]
            result.data[position] = Jx[k]
            position += 1
        for control in range(n_controls):
            change: float = control_rows[control, column]
            if change != 0.0:
                result.indices[position] = n_voltage + control
                result.data[position] = change
                position += 1
            else:
                pass
        result.indptr[column + 1] = position

    for control in range(n_controls):
        column = n_voltage + control
        result.indptr[column] = position
        for row in range(n_voltage):
            change = q_columns[row, control]
            if change != 0.0:
                result.indices[position] = row
                result.data[position] = change
                position += 1
            else:
                pass
        if limited[control]:
            result.indices[position] = n_voltage + control
            result.data[position] = 1.0
            position += 1
        else:
            pass
        result.indptr[column + 1] = position

    return result


@nb.njit
def apply_common_mode_jacobian(
        Jx: Vec, Jp: IntVec, Ji: IntVec, nrows: int, ncols: int,
        voltage: CxVec, idx_dVa: IntVec, idx_dVm: IntVec,
        constraints_x: CxVec, constraints_p: IntVec, constraints_i: IntVec,
        real_rows: IntVec, imag_rows: IntVec) -> CSC:
    """Replace constrained KCL rows with exact linear complex-voltage derivatives.

    The cached constraint matrix contains mean U0, complex U1 and scaled
    physical common-mode balances. Sharing it with the residual preserves
    every row replacement, including partial phases and Schur-reduced networks.

    :param Jx: Analytic current/control CSC values after current projection.
    :param Jp: Analytic Jacobian CSC column pointers.
    :param Ji: Analytic Jacobian CSC row indices.
    :param nrows: Number of residual equations.
    :param ncols: Number of solver variables.
    :param voltage: Retained conductor voltages.
    :param idx_dVa: Conductors with angle variables.
    :param idx_dVm: Conductors with magnitude variables.
    :param constraints_x: Linear complex constraint CSC values.
    :param constraints_p: Constraint CSC column pointers.
    :param constraints_i: Constraint CSC row indices.
    :param real_rows: Real KCL row replaced by each complex constraint.
    :param imag_rows: Imaginary KCL row replaced by each complex constraint.
    :return: CSC Jacobian with the residual's exact voltage constraints.
    """
    replaced: BoolVec = np.zeros(nrows, dtype=np.bool_)
    replaced[real_rows] = True
    replaced[imag_rows] = True
    # Each stored complex voltage coefficient contributes at most four real
    # entries: real/imaginary parts in its angle and magnitude columns.
    result: CSC = CSC(nrows, ncols, len(Jx) + 4 * len(constraints_x), False)
    position: int = 0
    n_angle: int = len(idx_dVa)
    n_voltage: int = n_angle + len(idx_dVm)
    for column in range(ncols):
        result.indptr[column] = position
        column_start: int = position
        for k in range(Jp[column], Jp[column + 1]):
            row: int = Ji[k]
            if not replaced[row]:
                result.indices[position] = row
                result.data[position] = Jx[k]
                position += 1
            else:
                pass
        if column < n_voltage:
            conductor: int = idx_dVa[column] if column < n_angle else idx_dVm[column - n_angle]
            direction: complex = (1j * voltage[conductor] if column < n_angle
                                  else voltage[conductor] / abs(voltage[conductor]))
            for k in range(constraints_p[conductor], constraints_p[conductor + 1]):
                constraint: int = constraints_i[k]
                change: complex = constraints_x[k] * direction
                if change.real != 0.0:
                    result.indices[position] = real_rows[constraint]
                    result.data[position] = change.real
                    position += 1
                else:
                    pass
                if change.imag != 0.0:
                    result.indices[position] = imag_rows[constraint]
                    result.data[position] = change.imag
                    position += 1
                else:
                    pass
        else:
            pass
        # Replacement rows may precede copied KCL rows. Keep canonical CSC
        # ordering so solver conversion need not sort a second matrix.
        if position - column_start > 1:
            order: IntVec = np.argsort(result.indices[column_start:position])
            column_indices: IntVec = result.indices[column_start:position].copy()
            column_values: Vec = result.data[column_start:position].copy()
            result.indices[column_start:position] = column_indices[order]
            result.data[column_start:position] = column_values[order]
        else:
            pass
        result.indptr[column + 1] = position
    result.resize(position)
    return result


def create_J_Ibus_csc(
        Yx: CxVec,
        Yp: IntVec,
        Yi: IntVec,
        V: CxVec,
        idx_dtheta: IntVec,
        idx_dVm: IntVec,
        idx_dP: IntVec,
        idx_dQ: IntVec,
        lookup_p: IntVec,
        lookup_q: IntVec,
        lookup_angle: IntVec,
        lookup_magnitude: IntVec,
        Igen: CxVec,
        Ipower: CxVec,
        Icurrent: CxVec,
        bus_lookup: IntVec,
        load_bus_idx: IntVec,
        Sstar: CxVec,
        Sfloating: CxVec,
        Sdelta: CxVec,
        Istar: CxVec,
        Idelta: CxVec,
        Ifloating: CxVec,
        source_dVa: np.ndarray,
        source_dVm: np.ndarray,
        source_dq: np.ndarray,
        control_phases: np.ndarray,
        control_rotation: CxVec,
        control_limited: BoolVec,
        regular_generator_idx: IntVec,
        asynchronous_generator_idx: IntVec,
        generator_bus_idx: IntVec,
        generator_conn: IntVec,
        generator_p: Vec,
        generator_q: Vec,
        generator_control_mode: IntVec,
        generator_r0: Vec,
        generator_x0: Vec,
        generator_rs: Vec,
        generator_xs: Vec,
        generator_xm: Vec,
        generator_rr: Vec,
        generator_xr: Vec,
        generator_snom: Vec,
        system_base: float) -> CSC:
    """Assemble the complete analytic Jacobian from evaluated currents.

    The current arrays must be the same ones used by ``fx``. This function
    prepares injection derivatives, invokes the cache-friendly CSC packer,
    appends positive-sequence control equations, and applies common-mode row
    replacements. All indices refer to retained conductors except the NABC
    bus lookup and original generator/load bus indices.

    :param Yx: Ybus CSC data.
    :param Yp: Ybus CSC column pointers.
    :param Yi: Ybus CSC row indices.
    :param V: Retained conductor voltages.
    :param idx_dtheta: Angle variable conductors.
    :param idx_dVm: Magnitude variable conductors.
    :param idx_dP: Real current-residual conductors.
    :param idx_dQ: Imaginary current-residual conductors.
    :param lookup_p: Cached retained conductor to real residual row lookup.
    :param lookup_q: Cached retained conductor to imaginary residual row lookup.
    :param lookup_angle: Cached retained conductor to angle column lookup.
    :param lookup_magnitude: Cached retained conductor to magnitude column lookup.
    :param Igen: Evaluated generator current injections before system-base scaling.
    :param Ipower: Evaluated power-load current injections before scaling.
    :param Icurrent: Evaluated current-load injections before scaling.
    :param bus_lookup: Original NABC slot to retained conductor lookup.
    :param load_bus_idx: Original bus index of each load.
    :param Sstar: Star load powers.
    :param Sfloating: Floating-star load powers.
    :param Sdelta: Delta load powers.
    :param Istar: Star load current parameters.
    :param Idelta: Delta load current parameters.
    :param Ifloating: Floating-star load current parameters.
    :param source_dVa: Positive-sequence source angle derivatives by local terminal.
    :param source_dVm: Positive-sequence source magnitude derivatives by local terminal.
    :param source_dq: Positive-sequence source reactive-control derivatives.
    :param control_phases: Retained ABC terminal indices of each controlled bus.
    :param control_rotation: Positive-sequence ABC rotation.
    :param control_limited: Fixed-Q equation flags for controlled buses.
    :param regular_generator_idx: Cached ordinary generator indices.
    :param asynchronous_generator_idx: Cached asynchronous generator indices.
    :param generator_bus_idx: Original bus index of each generator.
    :param generator_conn: Generator connection codes.
    :param generator_p: Generator active-power settings.
    :param generator_q: Generator reactive-power settings.
    :param generator_control_mode: Generator control-mode codes.
    :param generator_r0: Zero-sequence machine resistances.
    :param generator_x0: Zero-sequence machine reactances.
    :param generator_rs: Machine stator resistances.
    :param generator_xs: Machine stator reactances.
    :param generator_xm: Machine magnetising reactances.
    :param generator_rr: Machine rotor resistances.
    :param generator_xr: Machine rotor reactances.
    :param generator_snom: Machine nominal MVA ratings.
    :param system_base: System MVA base.
    :return: Complete real Jacobian in CSC format.
    """
    scale: float = 3.0 / system_base
    Iinj: CxVec = scale * (Igen + Ipower + Icurrent)

    Ifixed: CxVec = scale * compute_generators(
        bus_idx=generator_bus_idx[regular_generator_idx],
        bus_lookup=bus_lookup,
        V=V,
        P=generator_p[regular_generator_idx],
        Q=generator_q[regular_generator_idx],
        control_mode_int=generator_control_mode[regular_generator_idx]
    )

    asynchronous_dVa, asynchronous_dVm = asynchronous_current_derivative_blocks(
        voltage=V,
        bus_lookup=bus_lookup,
        generator_buses=generator_bus_idx,
        generator_indices=asynchronous_generator_idx,
        connections=generator_conn,
        r0=generator_r0,
        x0=generator_x0,
        rs=generator_rs,
        xs=generator_xs,
        xm=generator_xm,
        rr=generator_rr,
        xr=generator_xr,
        power=generator_p,
        nominal_power=generator_snom,
        system_base=system_base
    )
    source_dVa += asynchronous_dVa
    source_dVm += asynchronous_dVm

    Jvoltage: CSC = pack_J_Ibus_csc(
        Yx=Yx,
        Yp=Yp,
        Yi=Yi,
        V=V,
        idx_dtheta=idx_dtheta,
        idx_dVm=idx_dVm,
        idx_dP=idx_dP,
        idx_dQ=idx_dQ,
        lookup_dP=lookup_p,
        lookup_dQ=lookup_q,
        Iinj=Iinj,
        Ifixed=Ifixed,
        bus_lookup=bus_lookup,
        load_bus_idx=load_bus_idx,
        Sstar=Sstar,
        Sfloating=Sfloating,
        Sdelta=Sdelta,
        Istar=Istar,
        Idelta=Idelta,
        Ifloating=Ifloating,
        source_dVa=source_dVa,
        source_dVm=source_dVm,
        scale=scale
    )

    if len(control_limited) > 0:
        Jcomplete: CSC = append_positive_sequence_control_jacobian(
            Jx=Jvoltage.data,
            Jp=Jvoltage.indptr,
            Ji=Jvoltage.indices,
            voltage=V,
            idx_dVa=idx_dtheta,
            idx_dVm=idx_dVm,
            idx_dP=idx_dP,
            lookup_p=lookup_p,
            lookup_q=lookup_q,
            lookup_angle=lookup_angle,
            lookup_magnitude=lookup_magnitude,
            phases=control_phases,
            rotation=control_rotation,
            limited=control_limited,
            source_dq=source_dq
        )
    else:
        Jcomplete = Jvoltage

    return Jcomplete


class PfBasicFormulation3Ph(PfFormulationTemplate):
    __slots__ = (
        "Ybus",
        "Yf",
        "Yt",
        "Yshunt_bus",
        "mask",
        "bus_lookup",
        "branch_lookup",
        "Ybus_full",
        "Yf_full",
        "Yt_full",
        "Yshunt_bus_full",
        "bus_lookup_full",
        "retained",
        "voltage_lift",
        "passive_admittance",
        "Un_floating_current",
        "Un_floating_power",
        "logger",
        "nc",
        "S0",
        "Qmin",
        "Qmax",
        "vd",
        "pq",
        "pv",
        "pqv",
        "p",
        "no_slack",
        "idx_dVa",
        "idx_dVm",
        "idx_dP",
        "idx_dQ",
        "lookup_p",
        "lookup_q",
        "lookup_angle",
        "lookup_magnitude",
        "regular_generator_idx",
        "asynchronous_generator_idx",
        "positive_sequence",
        "common_mode",
    )

    def __init__(self,
                 V0: CxVec,
                 S0: CxVec,
                 Qmin: Vec,
                 Qmax: Vec,
                 nc: NumericalCircuit,
                 options: PowerFlowOptions,
                 logger: Logger) -> None:
        """
        PfBasicFormulation3Ph
        :param V0: Array of nodal initial solution (3N)
        :param S0: Array of power injections (3N)
        :param Qmin: Array of bus reactive power upper limit (N, not 3N)
        :param Qmax: Array of bus reactive power lower limit (N, not 3N)
        :param nc: NumericalCircuit
        :param options: PowerFlowOptions
        """
        self.Ybus, self.Yf, self.Yt, self.Yshunt_bus, self.mask, self.bus_lookup, self.branch_lookup = compute_ybus(nc)
        # Post-processing uses the original conductor layout after passive neutrals are reconstructed.
        self.Ybus_full: csc_matrix = self.Ybus
        self.Yf_full: csc_matrix = self.Yf
        self.Yt_full: csc_matrix = self.Yt
        self.Yshunt_bus_full: CxMat = self.Yshunt_bus
        self.bus_lookup_full: IntVec = self.bus_lookup

        self.retained, self.voltage_lift = passive_neutral_reduction(nc, self.Ybus, self.mask)
        eliminated: IntVec = np.setdiff1d(np.arange(self.Ybus.shape[0]), self.retained)
        self.passive_admittance: csc_matrix = self.Ybus[eliminated, :]

        if self.voltage_lift is not None:
            # Schur complement of passive N equations, using the existing solver unchanged.
            self.Ybus = (self.Ybus[self.retained, :] @ self.voltage_lift).tocsc()
            self.Yf = (self.Yf @ self.voltage_lift).tocsc()
            self.Yt = (self.Yt @ self.voltage_lift).tocsc()
            self.Yshunt_bus = self.Yshunt_bus[np.ix_(self.retained, self.retained)]
            retained_full: IntVec = np.flatnonzero(self.mask)[self.retained]
            self.mask = np.zeros_like(self.mask)
            self.mask[retained_full] = True
            self.bus_lookup = lookup_from_mask(self.mask)
            self.voltage_lift = self.voltage_lift.tocsr()
            V0new = V0[self.mask]
        else:
            V0new = V0[self.mask]

        # The same CSC traversal must contain every local device coupling.
        self.Ybus = include_local_couplings_in_ybus_pattern(self.Ybus, self.bus_lookup)

        self.Un_floating_current = np.zeros(len(V0new), dtype=complex)
        self.Un_floating_power = np.zeros(len(V0new), dtype=complex)

        PfFormulationTemplate.__init__(self, V0=V0new.astype(complex), options=options)
        self.logger = logger
        self.nc = nc
        self.S0: CxVec = S0[self.mask].copy()
        self.positive_sequence: PositiveSequenceControl = PositiveSequenceControl(nc, self.bus_lookup)
        regular: IntVec = self.positive_sequence.regular_idx
        asynchronous: BoolVec = nc.generator_data.tpe_int[regular] == GeneratorType.Asynchronous.idx()
        self.regular_generator_idx: IntVec = regular[~asynchronous]
        self.asynchronous_generator_idx: IntVec = regular[asynchronous]

        self.Qmin = expand3ph(Qmin)[self.mask] * 100e6
        self.Qmax = expand3ph(Qmax)[self.mask] * 100e6

        # U1 regulation retains all phase balance equations; its extra Q unknown
        # and voltage constraint replace the three fixed phase magnitudes.
        bus_types: IntVec = self.nc.bus_data.bus_types.copy()
        bus_types[self.positive_sequence.bus_idx] = BusMode.PQ_tpe.value
        vd, pq, pv, pqv, p, no_slack = compile_types(
            Pbus=S0.real,
            types=bus_types
        )

        self.vd = expand_slice_indices_3ph(vd, self.bus_lookup)
        self.pq = expand_slice_indices_3ph(pq, self.bus_lookup)
        # A physical synchronous slack prescribes complex U1, retaining ABC unknowns.
        self.pq = np.r_[self.pq, self.positive_sequence.slack_phases.ravel()]
        self.pv = expand_slice_indices_3ph(pv, self.bus_lookup)
        self.pqv = expand_slice_indices_3ph(pqv, self.bus_lookup)
        self.p = expand_slice_indices_3ph(p, self.bus_lookup)
        self.no_slack = expand_slice_indices_3ph(no_slack, self.bus_lookup)

        self.idx_dVa = np.r_[self.pv, self.pq, self.pqv, self.p]
        self.idx_dVm = np.r_[self.pq, self.p]
        self.idx_dP = self.idx_dVa
        self.idx_dQ = np.r_[self.pq, self.pqv]
        nbus: int = len(self.V)
        self.lookup_p: IntVec = make_lookup(size=nbus, indices=self.idx_dP)
        self.lookup_q: IntVec = make_lookup(size=nbus, indices=self.idx_dQ)
        self.lookup_angle: IntVec = make_lookup(size=nbus, indices=self.idx_dVa)
        self.lookup_magnitude: IntVec = make_lookup(size=nbus, indices=self.idx_dVm)

        # ybus: csc_matrix = admittances[0]
        # yf: csc_matrix = admittances[1]
        # yt: csc_matrix = admittances[2]
        # mask: BoolVec = admittances[4]
        # full_lookup: IntVec = admittances[5]

        # self.Ybus, self.Yf, self.Yt, self.Yshunt_bus, self.mask, self.bus_lookup, self.branch_lookup = compute_ybus(nc)

        self.common_mode: CommonModeControl = CommonModeControl(
            nc=nc,
            ybus=self.Ybus_full,
            yf=self.Yf_full,
            yt=self.Yt_full,
            mask=self.bus_lookup_full >= 0,
            full_lookup=self.bus_lookup_full,
            lookup=self.bus_lookup,
            idx_p=self.idx_dP,
            idx_q=self.idx_dQ,
            positive=self.positive_sequence,
            reduced_ybus=self.Ybus
        )
        # Passive islands can be fully reconstructed without a Newton step.
        if self.size() == 0:
            self.Scalc = compute_power(self.Ybus, self.V)
            self._error = self.passive_current_error(self.V)
            self._converged = self._error < self.options.tolerance
        else:
            pass

    def x2var(self, x: Vec) -> None:
        """
        Convert X to decision variables
        :param x: solution vector
        """
        a = len(self.idx_dVa)
        b = a + len(self.idx_dVm)

        # update the vectors
        self.Va[self.idx_dVa] = x[0:a]
        self.Vm[self.idx_dVm] = x[a:b]
        self.positive_sequence.q[:] = x[b:]

    def var2x(self) -> Vec:
        """
        Convert the internal decision variables into the vector
        :return: Vector
        """
        return np.r_[
            self.Va[self.idx_dVa],
            self.Vm[self.idx_dVm],
            self.positive_sequence.q
        ]

    def update_bus_types(self, pq: IntVec, pv: IntVec, pqv: IntVec, p: IntVec) -> None:
        """

        :param pq:
        :param pv:
        :param pqv:
        :param p:
        :return:
        """
        self.pq = pq
        self.pv = pv
        self.pqv = pqv
        self.p = p

        self.idx_dVa = np.r_[self.pv, self.pq, self.pqv, self.p]
        self.idx_dVm = np.r_[self.pq, self.p]
        self.idx_dP = self.idx_dVa
        self.idx_dQ = np.r_[self.pq, self.pqv]
        nbus: int = len(self.V)
        self.lookup_p = make_lookup(size=nbus, indices=self.idx_dP)
        self.lookup_q = make_lookup(size=nbus, indices=self.idx_dQ)
        self.lookup_angle = make_lookup(size=nbus, indices=self.idx_dVa)
        self.lookup_magnitude = make_lookup(size=nbus, indices=self.idx_dVm)

        self.common_mode: CommonModeControl = CommonModeControl(
            nc=self.nc,
            ybus=self.Ybus_full,
            yf=self.Yf_full,
            yt=self.Yt_full,
            mask=self.bus_lookup_full >= 0,
            full_lookup=self.bus_lookup_full,
            lookup=self.bus_lookup,
            idx_p=self.idx_dP,
            idx_q=self.idx_dQ,
            positive=self.positive_sequence,
            reduced_ybus=self.Ybus
        )

    def size(self) -> int:
        """
        Size of the jacobian matrix
        :return:
        """
        return len(self.idx_dVa) + len(self.idx_dVm) + len(self.positive_sequence.q)

    def generator_currents(self, voltage: CxVec, q: Vec) -> CxVec:
        """Combine legacy injections and U1 sources with their passive sequence responses.

        :param voltage: Retained phase voltages in pu.
        :param q: U1 regulator reactive powers in system pu.
        :return: Generator currents in MW / pu voltage.
        """
        currents: CxVec = compute_generators(
            bus_idx=self.nc.generator_data.bus_idx[self.regular_generator_idx],
            bus_lookup=self.bus_lookup,
            V=voltage,
            P=self.nc.generator_data.p[self.regular_generator_idx],
            Q=self.nc.generator_data.q[self.regular_generator_idx],
            control_mode_int=self.nc.generator_data.control_mode_int[self.regular_generator_idx]
        )
        # Asynchronous machines replace the fixed PQ injection, including on a
        # bus shared with a voltage regulator. Their reactive power is not a setpoint.
        gen: int
        for gen in self.asynchronous_generator_idx:
            phases: IntVec = self.bus_lookup[4 * self.nc.generator_data.bus_idx[gen] + np.array((1, 2, 3))]
            if np.any(phases < 0):
                raise ValueError('Asynchronous generator requires all three phases: '
                                 + str(self.nc.generator_data.names[gen]))
            else:
                pass
            y0: complex = 0j
            connection: int = self.nc.generator_data.conn[gen]
            if connection == ShuntConnectionType.GroundedStar.idx():
                z0: complex = complex(self.nc.generator_data.r0[gen], self.nc.generator_data.x0[gen])
                if not np.isfinite(z0) or abs(z0) < 1e-12:
                    raise ValueError('Asynchronous generator Z0 must be finite and nonzero for Yg: '
                                     + str(self.nc.generator_data.names[gen]) + '. Check R0/X0 and grounding data.')
                else:
                    # R0/X0 use the system base; the equivalent uses the machine base.
                    y0 = self.nc.Sbase / (self.nc.generator_data.snom[gen] * z0)
            elif connection in (ShuntConnectionType.Delta.idx(), ShuntConnectionType.FloatingStar.idx()):
                pass
            else:
                raise ValueError('Asynchronous generator with an explicit neutral is not supported in ABC: '
                                 + str(self.nc.generator_data.names[gen]))
            try:
                currents[phases] += asynchronous_gen_currents(
                    voltage=voltage[phases], Rs=self.nc.generator_data.Rs[gen],
                    Xs=self.nc.generator_data.Xs[gen], Xm=self.nc.generator_data.Xm[gen],
                    Rr=self.nc.generator_data.Rr[gen], Xr=self.nc.generator_data.Xr[gen],
                    P=self.nc.generator_data.p[gen], Sr=self.nc.generator_data.snom[gen], y0=y0)
            except ValueError as error:
                raise ValueError(str(self.nc.generator_data.names[gen]) + ': ' + str(error)) from error
        self.positive_sequence.add_currents(currents, voltage, q)
        return currents

    def compute_f(self, x: Vec) -> Vec:
        """
        Compute the function residual
        :param x: Solution vector
        :return: f
        """

        a = len(self.idx_dVa)
        b = a + len(self.idx_dVm)

        # copy the sliceable vectors
        Va = self.Va.copy()
        Vm = self.Vm.copy()

        # update the vectors
        Va[self.idx_dVa] = x[0:a]
        Vm[self.idx_dVm] = x[a:b]

        V = polar_to_rect(Vm, Va)

        # compute the function residual
        # Assumes the internal vars were updated already with self.x2var()

        Igen = self.generator_currents(V, x[b:])

        (Ipower,
         Y_power_linear,
         floating_power) = compute_power_loads(
            bus_idx=self.nc.load_data.bus_idx,
            bus_lookup=self.bus_lookup,
            V=V,
            Sstar=self.nc.load_data.S3_star,
            Sfloating=self.nc.load_data.S3_floatingstar,
            Sdelta=self.nc.load_data.S3_delta
        )

        (Icurrent,
         Y_current_linear,
         floating_current) = compute_current_loads(
            bus_idx=self.nc.load_data.bus_idx,
            bus_lookup=self.bus_lookup,
            V=V,
            Istar=self.nc.load_data.I3_star,
            Idelta=self.nc.load_data.I3_delta,
            Ifloating=self.nc.load_data.I3_floatingstar
        )

        Ibus = (Igen + Ipower + Icurrent) / (self.nc.Sbase / 3) / (V / np.abs(V))
        Icalc = compute_current(self.Ybus, V) / (V / np.abs(V))

        dI = (Icalc - Ibus)  # compute the mismatch
        self.common_mode.remove_ideal_current(V, dI)
        _f = np.r_[
            dI[self.idx_dP].real,
            dI[self.idx_dQ].imag,
            self.positive_sequence.residual(V, x[b:])
        ]

        self.common_mode.apply(V, _f)
        return _f

    def check_error(self, x: Vec) -> Tuple[float, Vec]:
        """
        Check error of the solution without affecting the problem
        :param x: Solution vector
        :return: error
        """
        a = len(self.idx_dVa)
        b = a + len(self.idx_dVm)

        # update the vectors
        Va = self.Va.copy()
        Vm = self.Vm.copy()
        Va[self.idx_dVa] = x[0:a]
        Vm[self.idx_dVm] = x[a:b]

        # compute the complex voltage
        V = polar_to_rect(Vm, Va)

        # compute the function residual
        # Assumes the internal vars were updated already with self.x2var()

        Igen = self.generator_currents(V, x[b:])

        (Ipower,
         Y_power_linear,
         floating_power) = compute_power_loads(bus_idx=self.nc.load_data.bus_idx,
                                                       bus_lookup=self.bus_lookup,
                                                       V=V,
                                                       Sstar=self.nc.load_data.S3_star,
                                                       Sfloating=self.nc.load_data.S3_floatingstar,
                                                       Sdelta=self.nc.load_data.S3_delta)

        (Icurrent,
         Y_current_linear,
         floating_current) = compute_current_loads(bus_idx=self.nc.load_data.bus_idx,
                                                           bus_lookup=self.bus_lookup,
                                                           V=V,
                                                           Istar=self.nc.load_data.I3_star,
                                                           Idelta=self.nc.load_data.I3_delta,
                                                           Ifloating=self.nc.load_data.I3_floatingstar)

        Ibus = (Igen + Ipower + Icurrent) / (self.nc.Sbase / 3) / (V / np.abs(V))
        Icalc = compute_current(self.Ybus, V) / (V / np.abs(V))

        # print('\nIbus =', abs(Ibus))
        # print('Icalc =', abs(Icalc))

        dI = (Icalc - Ibus)  # compute the mismatch
        self.common_mode.remove_ideal_current(V, dI)
        _f = np.r_[
            dI[self.idx_dP].real,
            dI[self.idx_dQ].imag,
            self.positive_sequence.residual(V, x[b:])
        ]

        # compute the error
        original_error: float = compute_fx_error(_f)
        self.common_mode.apply(V, _f)
        return max(original_error, compute_fx_error(_f), self.passive_current_error(V)), x

    def reconstruct_voltage(self, voltage: CxVec) -> CxVec:
        """Recover passive voltages with compensated sums of the existing lift coefficients.

        :param voltage: Retained solver voltages in pu.
        :return: Full voltages, including the original passive conductors.
        """
        if self.voltage_lift is None:
            return voltage
        full: CxVec = np.empty(self.voltage_lift.shape[0], dtype=complex)
        for row in range(len(full)):
            start, end = self.voltage_lift.indptr[row:row + 2]
            terms: CxVec = self.voltage_lift.data[start:end] * voltage[self.voltage_lift.indices[start:end]]
            full[row] = (complex(fsum(terms.real), fsum(terms.imag)) if np.all(np.isfinite(terms))
                         else np.sum(terms))
        return full

    def passive_current_error(self, voltage: CxVec) -> float:
        """Check original eliminated KCL after voltage reconstruction, including roundoff.

        :param voltage: Retained solver voltages in pu.
        :return: Largest eliminated current residual in pu.
        """
        if self.voltage_lift is None:
            return 0.0
        return float(np.max(np.abs(self.passive_admittance @ self.reconstruct_voltage(voltage))))

    def update(self, x: Vec, update_controls: bool = False) -> Tuple[float, bool, Vec, Vec]:
        """
        Update step
        :param x: Solution vector
        :param update_controls:
        :return: error, converged?, x
        """
        # set the problem state
        self.x2var(x)

        # compute the complex voltage
        self.V = polar_to_rect(self.Vm, self.Va)

        # compute the function residual
        # Assumes the internal vars were updated already with self.x2var()

        Igen = self.generator_currents(self.V, self.positive_sequence.q)

        (Ipower,
         Y_power_linear,
         self.Un_floating_power) = compute_power_loads(bus_idx=self.nc.load_data.bus_idx,
                                                       bus_lookup=self.bus_lookup,
                                                       V=self.V,
                                                       Sstar=self.nc.load_data.S3_star,
                                                       Sfloating=self.nc.load_data.S3_floatingstar,
                                                       Sdelta=self.nc.load_data.S3_delta)

        (Icurrent,
         Y_current_linear,
         self.Un_floating_current) = compute_current_loads(bus_idx=self.nc.load_data.bus_idx,
                                                           bus_lookup=self.bus_lookup,
                                                           V=self.V,
                                                           Istar=self.nc.load_data.I3_star,
                                                           Idelta=self.nc.load_data.I3_delta,
                                                           Ifloating=self.nc.load_data.I3_floatingstar)

        Ibus = (Igen + Ipower + Icurrent) / (self.nc.Sbase / 3) / (self.V / np.abs(self.V))
        Icalc = compute_current(self.Ybus, self.V) / (self.V / np.abs(self.V))
        self.Scalc = compute_power(self.Ybus, self.V)

        dI = (Icalc - Ibus)  # compute the mismatch
        self.common_mode.remove_ideal_current(self.V, dI)
        self._f = np.r_[
            dI[self.idx_dP].real,
            dI[self.idx_dQ].imag,
            self.positive_sequence.residual(self.V, self.positive_sequence.q)
        ]

        # Keep every original KCL/control equation in the convergence check. A reference
        # must never hide an incompatible injection in the replaced equation.
        original_error: float = compute_fx_error(self._f)
        self.common_mode.apply(self.V, self._f)
        self._error = max(original_error, compute_fx_error(self._f), self.passive_current_error(self.V))

        # review reactive power limits
        # it is only worth checking Q limits with a low error
        # since with higher errors, the Q values may be far from realistic
        # finally, the Q control only makes sense if there are pv nodes
        if update_controls and self._error < self._controls_tol:
            if self.options.control_Q:
                any_change = self.positive_sequence.enforce_limits()
            else:
                any_change = False

            # update Q limits control
            if self.options.control_Q and (len(self.pv) + len(self.p)) > 0:

                # check and adjust the reactive power
                # this function passes pv buses to pq when the limits are violated,
                # but not pq to pv because that is unstable
                changed, pv, pq, pqv, p = control_q_inside_method(self.Scalc,
                                                                  self.S0,  # TODO:  attribute defined outside __init__
                                                                  self.pv, self.pq,
                                                                  self.pqv, self.p,
                                                                  self.Qmin,
                                                                  self.Qmax)

                if len(changed) > 0:
                    any_change = True

                    # update the bus type lists
                    self.update_bus_types(pq=pq, pv=pv, pqv=pqv, p=p)

                    # the composition of x may have changed, so recompute
                    x = self.var2x()

            # update Slack control
            if self.options.distributed_slack:
                ok, delta = compute_slack_distribution(Scalc=self.Scalc,
                                                       vd=self.vd,
                                                       bus_installed_power=expand3ph(self.nc.bus_data.installed_power)[
                                                           self.mask])
                if ok:
                    any_change = True
                    # Update the objective power to reflect the slack distribution
                    self.S0 += delta  # TODO:  attribute defined outside __init__

            if any_change:
                # recompute the error based on the new Scalc and S0
                self._f = self.fx()

                # compute the error
                self._error, _ = self.check_error(x)

        # converged?
        self._converged = self._error < self.options.tolerance

        return self._error, self._converged, x, self.f

    def fx(self) -> Vec:
        """
        # Scalc = V · (Y x V - I)^*
        # Sbus = S0 + I0*Vm + Y0*Vm^2
        :return:
        """

        # NOTE: Assumes the internal vars were updated already with self.x2var()

        Igen = self.generator_currents(self.V, self.positive_sequence.q)

        Ipower, Y_power_linear, self.Un_floating_power = compute_power_loads(bus_idx=self.nc.load_data.bus_idx,
                                                                             bus_lookup=self.bus_lookup,
                                                                             V=self.V,
                                                                             Sstar=self.nc.load_data.S3_star,
                                                                             Sfloating=self.nc.load_data.S3_floatingstar,
                                                                             Sdelta=self.nc.load_data.S3_delta)

        Icurrent, Y_current_linear, self.Un_floating_current = compute_current_loads(bus_idx=self.nc.load_data.bus_idx,
                                                                                     bus_lookup=self.bus_lookup,
                                                                                     V=self.V,
                                                                                     Istar=self.nc.load_data.I3_star,
                                                                                     Idelta=self.nc.load_data.I3_delta,
                                                                                     Ifloating=self.nc.load_data.I3_floatingstar)

        Ibus = (Igen + Ipower + Icurrent) / (self.nc.Sbase / 3) / (self.V / np.abs(self.V))
        Icalc = compute_current(self.Ybus, self.V) / (self.V / np.abs(self.V))

        dI = Icalc - Ibus
        self.common_mode.remove_ideal_current(self.V, dI)
        self._f = np.r_[dI[self.idx_dP].real, dI[self.idx_dQ].imag,
                        self.positive_sequence.residual(self.V, self.positive_sequence.q)]

        self.common_mode.apply(self.V, self._f)
        return self._f

    def Jacobian(self, autodiff: bool = False) -> CSC:
        """Build the Jacobian of ``fx`` in the current solver coordinates.

        Evaluate injections exactly as ``fx`` does, collect analytical source
        derivatives, and let the CSC kernel add local load derivatives and
        differentiate the rotated current balance. Append reactive-control
        columns and U1 or limited-Q rows, then replace common-mode rows.

        Rows are real KCL, imaginary KCL, and control equations; columns are
        voltage angles, voltage magnitudes, and reactive-control coordinates.

        :param autodiff: Use the finite-difference comparison path.
        :return: Current-equation Jacobian in solver coordinate order.
        """
        if self.Ybus.format != 'csc':
            self.Ybus = self.Ybus.tocsc()
        else:
            pass

        if autodiff:
            return calc_autodiff_jacobian(func=self.compute_f, x=self.var2x(), h=1e-8)
        else:
            pass

        Igen: CxVec = self.generator_currents(
            voltage=self.V,
            q=self.positive_sequence.q)

        Ipower, _, _ = compute_power_loads(
            bus_idx=self.nc.load_data.bus_idx,
            bus_lookup=self.bus_lookup,
            V=self.V,
            Sstar=self.nc.load_data.S3_star,
            Sfloating=self.nc.load_data.S3_floatingstar,
            Sdelta=self.nc.load_data.S3_delta)

        Icurrent, _, _ = compute_current_loads(
            bus_idx=self.nc.load_data.bus_idx,
            bus_lookup=self.bus_lookup,
            V=self.V,
            Istar=self.nc.load_data.I3_star,
            Idelta=self.nc.load_data.I3_delta,
            Ifloating=self.nc.load_data.I3_floatingstar)

        source_dVa, source_dVm, source_dq = self.positive_sequence.current_derivative_blocks(
            voltage=self.V,
            q=self.positive_sequence.q,
            bus_lookup=self.bus_lookup)

        jacobian: CSC = create_J_Ibus_csc(
            Yx=self.Ybus.data,
            Yp=self.Ybus.indptr,
            Yi=self.Ybus.indices,
            V=self.V,
            idx_dtheta=self.idx_dVa,
            idx_dVm=self.idx_dVm,
            idx_dP=self.idx_dP,
            idx_dQ=self.idx_dQ,
            lookup_p=self.lookup_p,
            lookup_q=self.lookup_q,
            lookup_angle=self.lookup_angle,
            lookup_magnitude=self.lookup_magnitude,
            Igen=Igen,
            Ipower=Ipower,
            Icurrent=Icurrent,
            bus_lookup=self.bus_lookup,
            load_bus_idx=self.nc.load_data.bus_idx,
            Sstar=self.nc.load_data.S3_star,
            Sfloating=self.nc.load_data.S3_floatingstar,
            Sdelta=self.nc.load_data.S3_delta,
            Istar=self.nc.load_data.I3_star,
            Idelta=self.nc.load_data.I3_delta,
            Ifloating=self.nc.load_data.I3_floatingstar,
            source_dVa=source_dVa,
            source_dVm=source_dVm,
            source_dq=source_dq,
            control_phases=self.positive_sequence.phases,
            control_rotation=self.positive_sequence.rotation,
            control_limited=self.positive_sequence.limited,
            regular_generator_idx=self.regular_generator_idx,
            asynchronous_generator_idx=self.asynchronous_generator_idx,
            generator_bus_idx=self.nc.generator_data.bus_idx,
            generator_conn=self.nc.generator_data.conn,
            generator_p=self.nc.generator_data.p,
            generator_q=self.nc.generator_data.q,
            generator_control_mode=self.nc.generator_data.control_mode_int,
            generator_r0=self.nc.generator_data.r0,
            generator_x0=self.nc.generator_data.x0,
            generator_rs=self.nc.generator_data.Rs,
            generator_xs=self.nc.generator_data.Xs,
            generator_xm=self.nc.generator_data.Xm,
            generator_rr=self.nc.generator_data.Rr,
            generator_xr=self.nc.generator_data.Xr,
            generator_snom=self.nc.generator_data.snom,
            system_base=self.nc.Sbase)

        mismatch: CxVec = (self.Ybus @ self.V - (Igen + Ipower + Icurrent) * (3.0 / self.nc.Sbase)) / (
            self.V / np.abs(self.V))
        jacobian = self.common_mode.project_jacobian(
            jacobian=jacobian, voltage=self.V, mismatch=mismatch,
            lookup_p=self.lookup_p, lookup_q=self.lookup_q, lookup_angle=self.lookup_angle)
        if len(self.common_mode.constraint_real_rows) > 0:
            jacobian = apply_common_mode_jacobian(
                Jx=jacobian.data, Jp=jacobian.indptr, Ji=jacobian.indices,
                nrows=jacobian.n_rows, ncols=jacobian.n_cols,
                voltage=self.V, idx_dVa=self.idx_dVa, idx_dVm=self.idx_dVm,
                constraints_x=self.common_mode.constraints.data,
                constraints_p=self.common_mode.constraints.indptr,
                constraints_i=self.common_mode.constraints.indices,
                real_rows=self.common_mode.constraint_real_rows,
                imag_rows=self.common_mode.constraint_imag_rows)
        else:
            pass

        # Kernels differentiate the physical radius abs(V). Newton retains
        # signed Vm coordinates, especially for a neutral starting near zero.
        # dV/dVm reverses when Vm is negative; apply that exact coordinate
        # change to the complete column, including controls and references.
        n_angle: int = len(self.idx_dVa)
        magnitude: int
        for magnitude in range(len(self.idx_dVm)):
            if self.Vm[self.idx_dVm[magnitude]] < 0.0:
                column: int = n_angle + magnitude
                jacobian.data[jacobian.indptr[column]:jacobian.indptr[column + 1]] *= -1.0
            else:
                pass
        return jacobian

    def get_x_names(self) -> List[str]:
        """
        Names matching x
        :return:
        """
        cols = [f'dVa {i}' for i in self.idx_dVa]
        cols += [f'dVm {i}' for i in self.idx_dVm]
        cols += [f'Q U1 bus {i}' for i in self.positive_sequence.bus_idx]

        return cols

    def get_fx_names(self) -> List[str]:
        """
        Names matching fx
        :return:
        """
        rows = [f'dP {i}' for i in self.idx_dP]
        rows += [f'dQ {i}' for i in self.idx_dQ]
        rows += [f'U1 or Q limit bus {i}' for i in self.positive_sequence.bus_idx]

        return rows

    def get_solution(self, elapsed: float, iterations: int) -> NumericPowerFlowResults:
        """
        Get the problem solution
        :param elapsed: Elapsed seconds
        :param iterations: Iteration number
        :return: NumericPowerFlowResults
        """
        voltage: CxVec = self.V
        floating: CxVec = self.Un_floating_current + self.Un_floating_power
        if self.voltage_lift is not None:
            voltage = self.reconstruct_voltage(self.V)
            floating = np.zeros(len(voltage), dtype=complex)
            floating[self.retained] = self.Un_floating_current + self.Un_floating_power
        else:
            pass
        # Compute the Branches power and the slack buses power
        Sf, St, If, It, Vbranch, loading, losses, Sbus, V_expanded = power_flow_post_process_nonlinear_3ph(
            Sbus=self.Scalc,
            V=voltage,
            Vn_floating=floating,
            F=expand_indices_3ph(self.nc.passive_branch_data.F),
            T=expand_indices_3ph(self.nc.passive_branch_data.T),
            pv=self.retained[self.pv],
            vd=self.retained[self.vd],
            Ybus=self.Ybus_full,
            Yf=self.Yf_full,
            Yt=self.Yt_full,
            Yshunt_bus=self.Yshunt_bus_full,
            branch_rates=expand3ph(self.nc.passive_branch_data.rates),
            Sbase=self.nc.Sbase,
            bus_lookup=self.bus_lookup_full,
            branch_lookup=self.branch_lookup
        )

        return NumericPowerFlowResults(
            V=V_expanded,
            Scalc=Sbus * (self.nc.Sbase / 3),
            m=np.ones(3 * self.nc.nbr, dtype=float),
            tau=np.zeros(3 * self.nc.nbr, dtype=float),
            Sf=Sf,
            St=St,
            If=If,
            It=It,
            loading=loading,
            losses=losses,
            Pfp_vsc=np.zeros(self.nc.nvsc, dtype=float),
            Pfn_vsc=np.zeros(self.nc.nvsc, dtype=float),
            St_vsc=np.zeros(3 * self.nc.nvsc, dtype=complex),
            If_vsc=np.zeros(self.nc.nvsc, dtype=float),
            It_vsc=np.zeros(3 * self.nc.nvsc, dtype=complex),
            losses_vsc=np.zeros(self.nc.nvsc, dtype=float),
            loading_vsc=np.zeros(self.nc.nvsc, dtype=float),
            Sf_hvdc=np.zeros(3 * self.nc.nhvdc, dtype=complex),
            St_hvdc=np.zeros(3 * self.nc.nhvdc, dtype=complex),
            losses_hvdc=np.zeros(self.nc.nhvdc, dtype=complex),
            loading_hvdc=np.zeros(self.nc.nhvdc, dtype=complex),
            norm_f=self.error,
            converged=self.converged,
            iterations=iterations,
            elapsed=elapsed
        )
