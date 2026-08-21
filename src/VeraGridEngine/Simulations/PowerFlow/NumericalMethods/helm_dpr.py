# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

# AUTHORS: Josep Fanals Batllori and Santiago Peñate Vera
# CONTACT:  u1946589@campus.udg.edu and santiago.penate.vera@gmail.com
# thanks to Llorenç Fanals Batllori for his help at coding
"""
DPRHEM power-flow solver.

This module implements VeraGrid's Dynamic Power Restart HELM variant and the remote-voltage ``PVQ/P`` extension.
The comments in the coefficient code refer to these two papers:

* Dynamic power restart HELM / DPRHEM, used here as the shifted-germ restart strategy:
  https://www.sciencedirect.com/science/article/pii/S0142061525004715
* Remote voltage control HELM, used here for the embedded ``PVQ/P`` bus equations:
  https://doi.org/10.1109/TSG.2019.2901865

The important modelling rule is that every DPR segment solves one fixed algebraic model. Discrete controls are
therefore applied only between fixed-model DPR solves, never inside a coefficient recurrence.
"""
import numpy as np
import numba as nb
import time
from scipy.sparse import csc_matrix, coo_matrix
from scipy.sparse import hstack as hs, vstack as vs
from scipy.sparse.linalg import factorized, spsolve

from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import NumericPowerFlowResults
import VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions as cf
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls import (control_q_inside_method,
                                                                                     DiscreteShuntControlState,
                                                                                     QvDroopControlState,
                                                                                     compute_slack_distribution)
from VeraGridEngine.basic_structures import Logger, CscMat, CxVec, IntVec, Vec


# @nb.njit("(c16[:])(i8, c16[:, :], f8)")
def pade4all(order, coeff_mat, s=1.0):
    """
    Computes the "order" Padè approximant of the coefficients at the approximation point s

    In DPRHEM this is only a local segment accelerator. It is not used to build one global Padé approximation across
    restart boundaries because each restart changes the expansion center.

    Arguments:
        coeff_mat: coefficient matrix (order, buses)
        order:  order of the series
        s: point of approximation (at 1 you get the voltage)

    Returns:
        Padè approximation at s for all the series
    """
    nbus = coeff_mat.shape[1]

    # complex_type = nb.complex128
    complex_type = np.complex128

    voltages = np.zeros(nbus, dtype=complex_type)

    nn = int(order / 2)
    L = nn
    M = nn

    for d in range(nbus):

        # formation of the linear system right hand side
        rhs = coeff_mat[L + 1:L + M + 1, d]

        # formation of the coefficients matrix
        C = np.zeros((L, M), dtype=complex_type)
        for i in range(L):
            k = i + 1
            C[i, :] = coeff_mat[L - M + k:L + k, d]

        # Obtaining of the b coefficients for orders greater than 0
        b = np.zeros(rhs.shape[0] + 1, dtype=complex_type)
        x = np.linalg.solve(C, -rhs)  # bn to b1
        b[0] = 1
        b[1:] = x[::-1]

        # Obtaining of the coefficients 'a'
        a = np.zeros(L + 1, dtype=complex_type)
        a[0] = coeff_mat[0, d]
        for i in range(L):
            val = complex_type(0)
            k = i + 1
            for j in range(k + 1):
                val += coeff_mat[k - j, d] * b[j]
            a[i + 1] = val

        # evaluation of the function for the value 's'
        p = complex_type(0)
        q = complex_type(0)
        for i in range(L + 1):
            p += a[i] * s ** i
            q += b[i] * s ** i

        voltages[d] = p / q

    return voltages


# @nb.njit("(c16[:])(c16[:, :], c16[:, :], i8, c16[:])")
@nb.njit(cache=True)
def conv1(A, B, c):
    """
    Performs the convolution of A* and B

    DPRHEM keeps the reciprocal-conjugate series ``X(s) = 1 / conj(U(s))`` used by HELM. This convolution forms the
    lower-order part of ``conj(U) * X``; the current-order term is handled explicitly after solving ``U[c]``.

    :param A: Coefficients matrix 1 (orders, buses)
    :param B: Coefficients matrix 2 (orders, buses)
    :param c: order of the coefficients
    :return: Array with the convolution for the buses given by "indices"
    """
    suma = np.zeros(A.shape[1], dtype=nb.complex128)
    for k in range(1, c + 1):
        for i in range(A.shape[1]):
            suma[i] += np.conj(A[k, i]) * B[c - k, i]
    return suma


# @nb.njit("(c16[:])(c16[:, :], c16[:, :], i8, i8[:])")
@nb.njit(cache=True)
def conv2(A, B, c, indices):
    """
    Performs the convolution of A and B

    This is used in the PV and remote P recurrences for the already-known part of ``X(s) * Q(s)``. The current-order
    unknown reactive coefficient is placed as a matrix unknown instead of being included in this convolution.

    :param A: Coefficients matrix 1 (orders, buses)
    :param B: Coefficients matrix 2 (orders, buses)
    :param c: order of the coefficients
    :param indices: bus indices array
    :return: Array with the convolution for the buses given by "indices"
    """
    suma = np.zeros(len(indices), dtype=nb.complex128)
    for k in range(1, c):
        for i, d in enumerate(indices):
            suma[i] += A[k, d] * B[c - 1 - k, d]
    return suma


# @nb.njit("(c16[:])(c16[:, :], c16[:, :], i8, i8[:])")
@nb.njit(cache=True)
def conv3(A, B, c, indices):
    """
    Performs the convolution of A and B*

    This supports the voltage-magnitude equations from conventional PV HELM and from the remote-voltage paper's PVQ
    buses. The matrix contains the current-order linear terms; this helper returns only lower-order products.

    :param A: Coefficients matrix 1 (orders, buses)
    :param B: Coefficients matrix 2 (orders, buses)
    :param c: order of the coefficients
    :param indices: bus indices array
    :return: Array with the convolution for the buses given by "indices"
    """
    suma = np.zeros(len(indices), dtype=nb.complex128)
    for k in range(1, c):
        for i, d in enumerate(indices):
            suma[i] += A[k, d] * np.conj(B[c - k, d])
    return suma


# Dynamic Power Restart HELM (DPRHEM)
#
# The DPRHEM paper replaces one long HELM expansion by local expansions around accepted physical states. The local
# segment recovers the target power direction from the current germ, then the outer restart loop accepts the best
# candidate voltage and repeats. This is also where VeraGrid discrete controls can safely change the fixed model.
# =====================================================================================================================
from scipy.sparse import diags as dpr_diags


class DprSegmentResult:
    """
    Result of one DPRHEM segment.

    :param U: Voltage coefficients in reduced no-slack coordinates.
    :param X: Reciprocal-conjugate voltage coefficients in reduced no-slack coordinates.
    :param Q: PV reactive power coefficients in reduced no-slack coordinates.
    :param V: Full voltage vector selected as the segment output.
    :param iterations: Number of computed/accepted coefficient orders.
    :param norm_f: Power-flow mismatch norm of ``V``.
    :param converged: True if ``norm_f`` satisfies the requested tolerance.
    :param improved: True if the segment found a better voltage than its input germ.
    """

    __slots__ = ("U", "X", "Q", "V", "iterations", "norm_f", "converged", "improved")

    def __init__(self,
                 U: np.ndarray,
                 X: np.ndarray,
                 Q: np.ndarray,
                 V: CxVec,
                 iterations: int,
                 norm_f: float,
                 converged: bool,
                 improved: bool) -> None:
        """
        Build the DPRHEM segment result.

        :param U: Voltage coefficients in reduced no-slack coordinates.
        :param X: Reciprocal-conjugate voltage coefficients in reduced no-slack coordinates.
        :param Q: PV reactive power coefficients in reduced no-slack coordinates.
        :param V: Full voltage vector selected as the segment output.
        :param iterations: Number of computed/accepted coefficient orders.
        :param norm_f: Power-flow mismatch norm of ``V``.
        :param converged: True if ``norm_f`` satisfies the requested tolerance.
        :param improved: True if the segment found a better voltage than its input germ.
        :return: None.
        """

        self.U: np.ndarray = U
        self.X: np.ndarray = X
        self.Q: np.ndarray = Q
        self.V: CxVec = V
        self.iterations: int = iterations
        self.norm_f: float = norm_f
        self.converged: bool = converged
        self.improved: bool = improved


class DprCoefficientPath:
    """
    Result of a DPRHEM coefficient solve with the accepted restart path.

    :param U: Last segment voltage coefficients in reduced no-slack coordinates.
    :param X: Last segment reciprocal-conjugate voltage coefficients in reduced no-slack coordinates.
    :param Q: Last segment reactive-power coefficients in reduced no-slack coordinates.
    :param V: Final full voltage vector.
    :param iterations: Total coefficient orders consumed by the fixed-model solve.
    :param converged: True if the final voltage satisfies the requested tolerance.
    :param segments: Accepted DPRHEM segments for this fixed algebraic model.
    """

    __slots__ = ("U", "X", "Q", "V", "iterations", "converged", "segments")

    def __init__(self,
                 U: np.ndarray,
                 X: np.ndarray,
                 Q: np.ndarray,
                 V: CxVec,
                 iterations: int,
                 converged: bool,
                 segments: list[DprSegmentResult]) -> None:
        """
        Build the DPRHEM coefficient path.

        :param U: Last segment voltage coefficients in reduced no-slack coordinates.
        :param X: Last segment reciprocal-conjugate voltage coefficients in reduced no-slack coordinates.
        :param Q: Last segment reactive-power coefficients in reduced no-slack coordinates.
        :param V: Final full voltage vector.
        :param iterations: Total coefficient orders consumed by the fixed-model solve.
        :param converged: True if the final voltage satisfies the requested tolerance.
        :param segments: Accepted DPRHEM segments for this fixed algebraic model.
        :return: None.
        """

        self.U: np.ndarray = U
        self.X: np.ndarray = X
        self.Q: np.ndarray = Q
        self.V: CxVec = V
        self.iterations: int = iterations
        self.converged: bool = converged
        self.segments: list[DprSegmentResult] = segments


class DprAdmittanceControlView:
    """
    Hold the admittance references that discrete shunt control mutates.

    The existing shunt-control wrapper only needs ``Ybus`` and ``Yshunt_bus``. DPRHEM receives those as raw
    arguments, so this small view lets the control code update the active matrices without moving the outer control
    loop back to the worker.
    """
    __slots__ = (
        "Ybus",
        "Yshunt_bus",
    )

    def __init__(self, Ybus: CscMat, Yshunt_bus: CxVec) -> None:
        """
        Build the admittance view.

        :param Ybus: Active bus admittance matrix.
        :param Yshunt_bus: Active bus shunt admittance vector.
        """
        self.Ybus: CscMat = Ybus
        self.Yshunt_bus: CxVec = Yshunt_bus


def dpr_reduced_bus_indices(no_slack: IntVec,
                            pq: IntVec,
                            pv: IntVec,
                            pqv: IntVec,
                            p: IntVec) -> tuple[IntVec, IntVec, IntVec, IntVec, IntVec]:
    """
    Convert original bus indices into the reduced no-slack indexing used by HELM.

    :param no_slack: Original non-slack bus indices.
    :param pq: Original PQ bus indices.
    :param pv: Original PV bus indices.
    :param pqv: Original PQV bus indices.
    :param p: Original P bus indices.
    :return: Reduced PQ, PV, PQV and P indices, plus original sorted non-slack indices.
    """

    pqpv_original: IntVec = no_slack.copy()

    # DPR solves all non-slack voltage coefficients in one reduced vector. The remote-voltage paper adds P and PVQ
    # bus types to the classical PQ/PV set, so all original index sets must be remapped into this same vector.
    pq_reduced: IntVec = np.searchsorted(pqpv_original, pq)
    pv_reduced: IntVec = np.searchsorted(pqpv_original, pv)
    pqv_reduced: IntVec = np.searchsorted(pqpv_original, pqv)
    p_reduced: IntVec = np.searchsorted(pqpv_original, p)

    return pq_reduced, pv_reduced, pqv_reduced, p_reduced, pqpv_original


def dpr_power_mismatch(Ybus: CscMat,
                       V: CxVec,
                       S0: CxVec,
                       no_slack: IntVec,
                       pq: IntVec,
                       pqv: IntVec,
                       Vset: CxVec) -> float:
    """
    Compute the VeraGrid power-flow mismatch norm.

    :param Ybus: Complete admittance matrix.
    :param V: Full voltage vector.
    :param S0: Specified complex bus powers.
    :param no_slack: Original non-slack bus indices.
    :param pq: Original PQ bus indices.
    :param pqv: Original remote-voltage controlled bus indices.
    :param Vset: Voltage set-point vector.
    :return: Power-flow mismatch norm.
    """

    Scalc: CxVec = cf.compute_power(Ybus, V)
    q_idx: IntVec = np.r_[pq, pqv]

    # The mismatch must match the algebraic model solved by the coefficient matrix:
    # active power at every non-slack bus, reactive power at PQ/PVQ buses, and PVQ voltage magnitude constraints.
    fx: np.ndarray = np.r_[
        (Scalc - S0)[no_slack].real,
        (Scalc - S0)[q_idx].imag,
        np.abs(V[pqv]) - np.abs(Vset[pqv])
    ]
    norm_f: float = float(cf.compute_fx_error(fx))

    return norm_f


def dpr_angle_guard(V: CxVec, sl: IntVec, no_slack: IntVec) -> bool:
    """
    Apply the DPRHEM voltage-angle physical-branch guard.

    :param V: Full voltage vector to test.
    :param sl: Slack bus indices.
    :param no_slack: Non-slack bus indices.
    :return: True if all non-slack voltage angles are within +/- 90 degrees of the slack angle.
    """

    if len(sl) > 0:
        slack_angle: float = float(np.angle(V[sl[0]], deg=True))
    else:
        slack_angle = 0.0

    angle_diff: np.ndarray = np.angle(V[no_slack], deg=True) - slack_angle
    angle_diff = (angle_diff + 180.0) % 360.0 - 180.0
    allowed: bool = bool(np.all(angle_diff < 90.0) and np.all(angle_diff > -90.0))

    return allowed


def dpr_safe_voltage_germ(V: CxVec, no_slack: IntVec) -> CxVec:
    """
    Make a voltage germ safe for reciprocal-voltage calculations.

    :param V: Full voltage vector candidate.
    :param no_slack: Original non-slack bus indices.
    :return: Full voltage vector with non-zero non-slack entries.
    """

    Vgerm: CxVec = V.copy()
    voltage_abs: np.ndarray = np.abs(Vgerm[no_slack])
    bad: np.ndarray = voltage_abs < 1e-10

    if np.any(bad):
        Vgerm[no_slack[bad]] = 1.0 + 0.0j
    else:
        Vgerm = Vgerm

    return Vgerm


def dpr_classical_no_load_germ(Yseries: CscMat, Vset: CxVec, sl: IntVec, no_slack: IntVec, pv: IntVec) -> CxVec:
    """
    Build the flat classical HELM germ used when no voltage estimate is supplied.

    The DPRHEM paper compares against a classical HELM-like flat start. For VeraGrid integration the normal path uses
    ``use_classical_germ=False`` so stored/user voltage guesses can seed the first DPR segment.

    :param Yseries: Series admittance matrix kept for interface symmetry with the shifted-germ path.
    :param Vset: Voltage set-point vector.
    :param sl: Slack bus indices.
    :param no_slack: Non-slack bus indices.
    :param pv: PV bus indices kept for interface symmetry.
    :return: Safe full voltage germ.
    """

    # The classical HELM germ is the network no-load voltage, not a flat voltage. Sigma analysis depends on this
    # analytic reference because its coefficients represent the whole loading path from no-load to target load.
    Vgerm: CxVec = np.ones_like(Vset, dtype=complex)
    Vgerm[sl] = Vset[sl]

    if len(no_slack) > 0:
        Yred: CscMat = Yseries[np.ix_(no_slack, no_slack)]
        Yslack: CscMat = -Yseries[np.ix_(no_slack, sl)]

        if len(sl) > 1:
            Vgerm[no_slack] = spsolve(Yred, Yslack.sum(axis=1))
        else:
            Vgerm[no_slack] = spsolve(Yred, Yslack)
    else:
        Vgerm = Vgerm

    return dpr_safe_voltage_germ(Vgerm, no_slack)


def dpr_known_inverse_voltage_coefficient(U: np.ndarray, X: np.ndarray, order: int) -> np.ndarray:
    """
    Compute the known part of ``X[order]`` before ``U[order]`` is solved.

    The copied base HELM formulation uses ``X(s) = 1 / conj(U(s))``.  At a given order, the part containing
    ``conj(U[order])`` is moved to the left-hand side of the DPRHEM matrix.  This function returns the remaining
    lower-order convolution.

    :param U: Voltage coefficients.
    :param X: Reciprocal-conjugate voltage coefficients.
    :param order: Coefficient order being solved.
    :return: Known lower-order contribution to ``X[order]``.
    """

    known: np.ndarray = np.zeros(U.shape[1], dtype=complex)

    # Accumulate only lower-order terms; the current-order unknown is kept in the matrix.
    for coeff_idx in range(1, order):
        known += np.conj(U[coeff_idx, :]) * X[order - coeff_idx, :]

    if order > 1:
        known = -known / np.conj(U[0, :])
    else:
        known = known

    return known


def dpr_residual_ratio(previous_norm: float, candidate_norm: float, tolerance: float) -> float:
    """
    Compute the residual-ratio indicator used by the DPRHEM restart rule.

    :param previous_norm: Previous order mismatch norm.
    :param candidate_norm: Current order mismatch norm.
    :param tolerance: Target mismatch tolerance.
    :return: Residual-ratio value.
    """

    denominator: float = previous_norm - tolerance

    if abs(denominator) > 1e-30:
        ratio: float = (previous_norm - candidate_norm) / denominator
    else:
        ratio = 0.0

    return ratio


def dpr_build_matrix(Yred: CscMat,
                     Ysh: CxVec,
                     U0: CxVec,
                     Sini_rhs: CxVec,
                     pv: IntVec,
                     pqv: IntVec,
                     p: IntVec,
                     npv: int,
                     npqv: int,
                     np_control_q: int,
                     npqpv: int) -> CscMat:
    """
    Build the real sparse DPRHEM segment matrix.

    The copied base HELM matrix is modified according to the paper's shifted-germ model: the initial physical power
    state ``Sini`` introduces a diagonal term multiplying ``conj(U[n])``.  The right-hand side then carries only
    lower-order terms and the direction power ``S_target - Sini``.

    :param Yred: Reduced series admittance matrix.
    :param Ysh: Reduced shunt admittance vector.
    :param U0: Segment voltage germ in reduced coordinates.
    :param Sini_rhs: Conjugated initial complex power in reduced coordinates.
    :param pv: Reduced PV bus indices.
    :param pqv: Reduced PVQ bus indices.
    :param p: Reduced P bus indices.
    :param npv: Number of PV buses.
    :param npqv: Number of PVQ buses.
    :param np_control_q: Number of controlled reactive power unknowns.
    :param npqpv: Number of non-slack buses.
    :return: Real sparse CSC matrix.
    """

    network_matrix: CscMat = (Yred + dpr_diags(Ysh, offsets=0, format="csc")).tocsc()

    # DPRHEM shifts the embedding around a physical voltage germ. The initial physical power is therefore non-zero
    # and contributes a diagonal coefficient multiplying conj(U[n]) on the left-hand side.
    gamma: CxVec = Sini_rhs / (np.conj(U0) * np.conj(U0))
    gamma_re: CscMat = dpr_diags(gamma.real, offsets=0, format="csc")
    gamma_im: CscMat = dpr_diags(gamma.imag, offsets=0, format="csc")

    # Real form of A*U + gamma*conj(U), with unknown vector [U.real, U.imag, Qpv, Qp].
    upper_left: CscMat = network_matrix.real + gamma_re
    upper_right: CscMat = -network_matrix.imag + gamma_im
    lower_left: CscMat = network_matrix.imag + gamma_im
    lower_right: CscMat = network_matrix.real - gamma_re

    X0: CxVec = 1.0 / np.conj(U0)
    q_rows: IntVec = np.r_[pv, p]
    voltage_rows: IntVec = np.r_[pv, pqv]

    # Unknown Q columns: local PV buses use their own Q unknowns; remote P buses use Q unknowns to enforce PVQ voltage.
    # This is the one-to-one PVQ/P specialization of the participation-factor block in Eq. (39) of the remote-control
    # HELM paper. A future multi-controller implementation would replace the identity-style P block by Kp,pvq.
    XIM: CscMat = coo_matrix((-X0[q_rows].imag, (q_rows, np.arange(np_control_q))),
                             shape=(npqpv, np_control_q)).tocsc()
    XRE: CscMat = coo_matrix((X0[q_rows].real, (q_rows, np.arange(np_control_q))),
                             shape=(npqpv, np_control_q)).tocsc()
    VRE: CscMat = coo_matrix((2.0 * U0[voltage_rows].real, (np.arange(npv + npqv), voltage_rows)),
                             shape=(npv + npqv, npqpv)).tocsc()
    VIM: CscMat = coo_matrix((2.0 * U0[voltage_rows].imag, (np.arange(npv + npqv), voltage_rows)),
                             shape=(npv + npqv, npqpv)).tocsc()
    EMPTY: CscMat = csc_matrix((npv + npqv, np_control_q))

    MAT: CscMat = vs(
        (hs((upper_left, upper_right, XIM)),
         hs((lower_left, lower_right, XRE)),
         hs((VRE, VIM, EMPTY))),
        format="csc"
    )

    return MAT


def dpr_select_candidate(Ybus: CscMat,
                         Vgerm: CxVec,
                         Vset: CxVec,
                         U: np.ndarray,
                         order: int,
                         sl: IntVec,
                         no_slack: IntVec,
                         pqpv_original: IntVec,
                         S0: CxVec,
                         pq: IntVec,
                         pqv: IntVec) -> tuple[CxVec, float, bool]:
    """
    Select the best valid truncated segment voltage.

    The paper evaluates at ``s = 1``.  The extra smaller scales are a guarded fallback for VeraGrid's very large
    PEGASE cases where the local segment radius is visibly below one; the selected state is still restarted through
    the same paper power-space update.

    :param Ybus: Complete admittance matrix.
    :param Vgerm: Full segment voltage germ.
    :param Vset: Full voltage set-point vector.
    :param U: Voltage coefficients.
    :param order: Highest available coefficient order.
    :param sl: Slack bus indices.
    :param no_slack: Non-slack bus indices.
    :param pqpv_original: Original sorted non-slack bus indices.
    :param S0: Specified power target.
    :param pq: Original PQ bus indices.
    :param pqv: Original PVQ bus indices.
    :return: Candidate voltage, mismatch norm and validity flag.
    """

    Vcandidate: CxVec = Vgerm.copy()
    candidate_norm: float = np.inf
    candidate_ok: bool = False
    candidate_scales: np.ndarray = np.array([1.0, 0.5, 0.25, 0.1, 0.05, 0.01, 0.001], dtype=float)

    # Evaluate a few points on the same analytic segment and restart from the best physical one.
    for scale in candidate_scales:
        Uscaled: CxVec = U[0, :].copy()

        for scale_order in range(1, order + 1):
            Uscaled += U[scale_order, :] * scale ** scale_order

        candidates: list[CxVec] = [Uscaled]

        # The paper evaluates the segment at s=1. This restricted Padé fallback is only used at s=1 so it remains an
        # approximant of the current local segment, not a cross-restart continuation object.
        if scale == 1.0 and order >= 4 and order % 2 == 0:
            try:
                candidates.append(pade4all(order, U[:order + 1, :], s=scale))
            except Exception:
                candidates = candidates

        for Ucandidate in candidates:
            Vscaled: CxVec = Vgerm.copy()
            Vscaled[sl] = Vset[sl]
            Vscaled[pqpv_original] = Ucandidate

            # Candidate acceptance is physical, not purely algebraic: it must reduce the actual VeraGrid mismatch and
            # stay on the expected high-voltage branch according to the slack-relative angle guard.
            scaled_norm: float = dpr_power_mismatch(Ybus=Ybus,
                                                    V=Vscaled,
                                                    S0=S0,
                                                    no_slack=no_slack,
                                                    pq=pq,
                                                    pqv=pqv,
                                                    Vset=Vset)
            scaled_ok: bool = bool(np.isfinite(scaled_norm) and dpr_angle_guard(Vscaled, sl, no_slack))

            if scaled_ok and scaled_norm < candidate_norm:
                Vcandidate = Vscaled
                candidate_norm = scaled_norm
                candidate_ok = True
            else:
                Vcandidate = Vcandidate

    return Vcandidate, candidate_norm, candidate_ok


def dpr_solve_segment(Ybus: CscMat,
                      Yseries: CscMat,
                      Vgerm: CxVec,
                      Vset: CxVec,
                      S0: CxVec,
                      Ysh0: CxVec,
                      pq: IntVec,
                      pv: IntVec,
                      pqv: IntVec,
                      p: IntVec,
                      sl: IntVec,
                      no_slack: IntVec,
                      pq_reduced: IntVec,
                      pv_reduced: IntVec,
                      pqv_reduced: IntVec,
                      p_reduced: IntVec,
                      pqpv_original: IntVec,
                      tolerance: float,
                      max_order: int,
                      current_norm: float,
                      allow_dynamic_restart: bool = True) -> DprSegmentResult:
    """
    Solve one DPRHEM shifted-germ segment.

    :param Ybus: Complete admittance matrix.
    :param Yseries: Series-only admittance matrix.
    :param Vgerm: Full voltage germ for this segment.
    :param Vset: Voltage set-point vector.
    :param S0: Specified complex target powers.
    :param Ysh0: Bus shunt admittance vector.
    :param pq: Original PQ bus indices.
    :param pv: Original PV bus indices.
    :param pqv: Original PVQ bus indices.
    :param p: Original P bus indices.
    :param sl: Slack bus indices.
    :param no_slack: Original non-slack bus indices.
    :param pq_reduced: Reduced PQ bus indices.
    :param pv_reduced: Reduced PV bus indices.
    :param pqv_reduced: Reduced PVQ bus indices.
    :param p_reduced: Reduced P bus indices.
    :param pqpv_original: Original sorted non-slack bus indices.
    :param tolerance: Target mismatch tolerance.
    :param max_order: Maximum coefficient order for this segment.
    :param current_norm: Mismatch norm at the germ.
    :param allow_dynamic_restart: Stop early when the DPR residual-ratio rule asks for a restart.
    :return: Segment result.
    """

    npqpv: int = len(pqpv_original)
    npv: int = len(pv_reduced)
    npqv: int = len(pqv_reduced)
    np_control_q: int = npv + len(p_reduced)
    Yred: CscMat = Yseries[np.ix_(pqpv_original, pqpv_original)]
    Ysh: CxVec = Ysh0[pqpv_original]
    U0: CxVec = Vgerm[pqpv_original].copy()
    bad_u0: np.ndarray = np.abs(U0) < 1e-10

    if np.any(bad_u0):
        U0[bad_u0] = 1.0 + 0.0j
    else:
        U0 = U0

    # Paper Eq. (2): initial state power is recomputed from the current voltage germ.
    Sini: CxVec = cf.compute_power(Ybus, Vgerm)
    Sini_rhs: CxVec = np.conj(Sini[pqpv_original])
    Sdir_pq_rhs: CxVec = np.conj(S0[pq] - Sini[pq])
    Sdir_pqv_rhs: CxVec = np.conj(S0[pqv] - Sini[pqv])
    Pdir_pv: np.ndarray = S0.real[pv] - Sini.real[pv]
    Pdir_p: np.ndarray = S0.real[p] - Sini.real[p]
    vec_W: np.ndarray = np.abs(Vset[pqpv_original]) * np.abs(Vset[pqpv_original])

    U: np.ndarray = np.zeros((max_order + 1, npqpv), dtype=complex)
    X: np.ndarray = np.zeros((max_order + 1, npqpv), dtype=complex)
    Q: np.ndarray = np.zeros((max_order + 1, npqpv), dtype=complex)

    # Order zero is the DPR germ. All higher orders describe the local analytic segment from this accepted state toward
    # the current fixed-model target powers.
    U[0, :] = U0
    X[0, :] = 1.0 / np.conj(U0)

    try:
        mat_factorized = factorized(dpr_build_matrix(Yred=Yred,
                                                     Ysh=Ysh,
                                                     U0=U0,
                                                     Sini_rhs=Sini_rhs,
                                                     pv=pv_reduced,
                                                     pqv=pqv_reduced,
                                                     p=p_reduced,
                                                     npv=npv,
                                                     npqv=npqv,
                                                     np_control_q=np_control_q,
                                                     npqpv=npqpv))
        factorized_ok: bool = True
    except (RuntimeError, ValueError):
        factorized_ok = False

    if factorized_ok:
        Vbest: CxVec = Vgerm.copy()
        best_norm: float = current_norm
        best_order: int = 0
        previous_norm: float = current_norm
        norm_order_1: float = current_norm
        baseline_ratio: float = np.inf
        converged: bool = current_norm <= tolerance
        improved: bool = False
        order: int = 1
        keep_solving: bool = not converged
        dval: CxVec = np.zeros(npqpv, dtype=complex)

        while order <= max_order and keep_solving:
            X_known: CxVec = dpr_known_inverse_voltage_coefficient(U, X, order)
            dval[:] = 0.0 + 0.0j

            # Paper Eq. (14): PQ bus shifted-power recurrence.
            dval[pq_reduced] = (Sini_rhs[pq_reduced] * X_known[pq_reduced]
                                + Sdir_pq_rhs * X[order - 1, pq_reduced])

            # Remote voltage paper Eq. (18): PVQ buses have fixed P, fixed Q and fixed voltage magnitude. The voltage
            # magnitude constraint is added below as a separate real row, so this row is the complex power equation.
            dval[pqv_reduced] = (Sini_rhs[pqv_reduced] * X_known[pqv_reduced]
                                 + Sdir_pqv_rhs * X[order - 1, pqv_reduced])

            # Paper Eq. (17): PV bus active-power direction and unknown reactive-power recurrence.
            dval[pv_reduced] = (Sini_rhs[pv_reduced] * X_known[pv_reduced]
                                + Pdir_pv * X[order - 1, pv_reduced]
                                - 1j * conv2(X, Q, order, pv_reduced))

            # Remote voltage paper Eq. (19): P buses keep active power fixed and use their unknown reactive power to
            # satisfy the associated PVQ voltage equation. This implementation supports the one-to-one participation
            # case, so each P bus gets one local Q unknown.
            dval[p_reduced] = (Sini_rhs[p_reduced] * X_known[p_reduced]
                               + Pdir_p * X[order - 1, p_reduced]
                               - 1j * conv2(X, Q, order, p_reduced))

            # PV and PVQ buses impose |V|^2 constraints. At order 1 the target appears explicitly; at higher orders
            # only lower-order convolution terms remain on the right-hand side.
            if order == 1:
                voltage_reduced: IntVec = np.r_[pv_reduced, pqv_reduced]
                voltage_rhs: np.ndarray = vec_W[voltage_reduced] - (np.abs(U[0, voltage_reduced]) ** 2.0)
            else:
                voltage_reduced = np.r_[pv_reduced, pqv_reduced]
                voltage_rhs = -conv3(U, U, order, voltage_reduced).real

            RHS: np.ndarray = np.r_[dval.real, dval.imag, voltage_rhs]
            LHS: np.ndarray = mat_factorized(RHS)

            # Decode the real sparse solve into complex voltage coefficients and reactive coefficients.
            U[order, :] = LHS[:npqpv] + 1j * LHS[npqpv:2 * npqpv]
            Q[order - 1, pv_reduced] = LHS[2 * npqpv:2 * npqpv + npv]
            Q[order - 1, p_reduced] = LHS[2 * npqpv + npv:]
            X[order, :] = -conv1(U, X, order) / np.conj(U[0, :])

            Vcandidate, candidate_norm, candidate_ok = dpr_select_candidate(Ybus=Ybus,
                                                                            Vgerm=Vgerm,
                                                                            Vset=Vset,
                                                                            U=U,
                                                                            order=order,
                                                                            sl=sl,
                                                                            no_slack=no_slack,
                                                                            pqpv_original=pqpv_original,
                                                                            S0=S0,
                                                                            pq=pq,
                                                                            pqv=pqv)

            if candidate_ok:
                if candidate_norm < best_norm:
                    Vbest = Vcandidate
                    best_norm = candidate_norm
                    best_order = order
                    improved = True
                else:
                    Vbest = Vbest

                if candidate_norm <= tolerance:
                    converged = True
                    keep_solving = False
                elif order == 1:
                    norm_order_1 = candidate_norm
                    keep_solving = True
                elif order == 2:
                    baseline_ratio = dpr_residual_ratio(previous_norm=norm_order_1,
                                                        candidate_norm=candidate_norm,
                                                        tolerance=tolerance)
                    keep_solving = True
                else:
                    ratio: float = dpr_residual_ratio(previous_norm=previous_norm,
                                                      candidate_norm=candidate_norm,
                                                      tolerance=tolerance)

                    # Dynamic restart rule: stop the local segment when residual improvement slows or reverses. The
                    # next segment starts from the best accepted physical voltage, as in the DPRHEM restart strategy.
                    slow_restart: bool = bool(baseline_ratio >= ratio > 0.0)
                    divergence_restart: bool = bool(ratio < 0.0)
                    restart_now: bool = bool(allow_dynamic_restart
                                             and (slow_restart or divergence_restart)
                                             and candidate_norm < current_norm)

                    if restart_now:
                        Vbest = Vcandidate
                        best_norm = candidate_norm
                        best_order = order
                        improved = True
                        keep_solving = False
                    else:
                        keep_solving = True
            else:
                keep_solving = True

            previous_norm = candidate_norm
            order += 1

        result: DprSegmentResult = DprSegmentResult(U=U,
                                                    X=X,
                                                    Q=Q,
                                                    V=Vbest,
                                                    iterations=best_order,
                                                    norm_f=best_norm,
                                                    converged=converged,
                                                    improved=improved)
    else:
        result = DprSegmentResult(U=U,
                                  X=X,
                                  Q=Q,
                                  V=Vgerm,
                                  iterations=0,
                                  norm_f=current_norm,
                                  converged=False,
                                  improved=False)

    return result


def helm_coefficients_dpr_path(Ybus: CscMat, Yseries: CscMat, V0: CxVec | None, Vset: CxVec, S0: CxVec, Ysh0: CxVec,
                               pq: IntVec, pv: IntVec, pqv: IntVec, p: IntVec, sl: IntVec, no_slack: IntVec,
                               tolerance: float = 1e-6, max_coeff: int = 30,
                               restart_order: int = 6, max_restarts: int = 20,
                               use_classical_germ: bool = False,
                               allow_dynamic_restart: bool = True,
                               verbose: bool = False, logger: Logger = None) -> DprCoefficientPath:
    """
    Compute DPRHEM coefficients, final voltage state and accepted restart path.

    :param Ybus: Complete admittance matrix.
    :param Yseries: Series-only admittance matrix.
    :param V0: Voltage estimate/set-point vector.
    :param S0: Specified complex bus powers.
    :param Ysh0: Bus shunt admittance vector.
    :param pq: Original PQ bus indices.
    :param pv: Original PV bus indices.
    :param pqv: Original PVQ bus indices.
    :param p: Original P bus indices.
    :param sl: Slack bus indices.
    :param no_slack: Original non-slack bus indices.
    :param tolerance: Target mismatch tolerance.
    :param max_coeff: Total coefficient budget across restarts.
    :param restart_order: Maximum coefficient order per segment.
    :param max_restarts: Maximum number of DPRHEM restarts.
    :param use_classical_germ: Use the classical no-load germ instead of the supplied voltage estimate.
    :param allow_dynamic_restart: Let the residual-ratio rule truncate a segment and restart from its best voltage.
    :param verbose: Store debug information.
    :param logger: Logger object.
    :return: DPRHEM coefficient path for one fixed algebraic model.
    """

    nbus: int = Yseries.shape[0]
    npqpv: int = len(no_slack)
    Ulast: np.ndarray = np.zeros((1, npqpv), dtype=complex)
    Xlast: np.ndarray = np.zeros((1, npqpv), dtype=complex)
    Qlast: np.ndarray = np.zeros((1, npqpv), dtype=complex)
    segments: list[DprSegmentResult] = list()

    if nbus < 2:
        Vbest: CxVec = Vset.copy() if V0 is None else V0.copy()
        iterations: int = 0
        converged: bool = False
    else:
        pq_reduced, pv_reduced, pqv_reduced, p_reduced, pqpv_original = dpr_reduced_bus_indices(
            no_slack=no_slack,
            pq=pq,
            pv=pv,
            pqv=pqv,
            p=p
        )

        # The normal VeraGrid integration uses the supplied voltage estimate as the first DPR germ. The classical flat
        # germ is retained for paper comparisons and direct experiments.
        Vtarget: CxVec = Vset if V0 is None else V0

        if use_classical_germ:
            Vbest = dpr_classical_no_load_germ(Yseries=Yseries, Vset=Vtarget, sl=sl, no_slack=no_slack, pv=pv)
        else:
            Vbest = dpr_safe_voltage_germ(Vtarget, no_slack)

        Vbest[sl] = Vtarget[sl]
        current_norm: float = dpr_power_mismatch(Ybus=Ybus,
                                                 V=Vbest,
                                                 S0=S0,
                                                 no_slack=no_slack,
                                                 pq=pq,
                                                 pqv=pqv,
                                                 Vset=Vset)
        converged = current_norm <= tolerance
        iterations = 0
        restart_count: int = 0
        can_continue: bool = True
        local_restart_order: int = restart_order if restart_order > 0 else max_coeff

        # Outer DPR loop across local analytic segments. The fixed model is not changed here; only the expansion center
        # changes from one accepted segment voltage to the next.
        while can_continue and not converged:
            remaining_order: int = max_coeff - iterations
            segment_order: int = min(local_restart_order, remaining_order) if remaining_order > 0 else 0

            if segment_order > 0 and restart_count <= max_restarts:
                segment: DprSegmentResult = dpr_solve_segment(Ybus=Ybus,
                                                              Yseries=Yseries,
                                                              Vgerm=Vbest,
                                                              Vset=Vset,
                                                              S0=S0,
                                                              Ysh0=Ysh0,
                                                              pq=pq,
                                                              pv=pv,
                                                              pqv=pqv,
                                                              p=p,
                                                              sl=sl,
                                                              no_slack=no_slack,
                                                              pq_reduced=pq_reduced,
                                                              pv_reduced=pv_reduced,
                                                              pqv_reduced=pqv_reduced,
                                                              p_reduced=p_reduced,
                                                              pqpv_original=pqpv_original,
                                                              tolerance=tolerance,
                                                              max_order=segment_order,
                                                              current_norm=current_norm,
                                                              allow_dynamic_restart=allow_dynamic_restart)
                Ulast = segment.U
                Xlast = segment.X
                Qlast = segment.Q
                iterations += max(1, segment.iterations)

                if segment.improved:
                    # Accept the segment output as the next shifted germ. This is the DPRHEM "dynamic power restart".
                    segments.append(segment)
                    Vbest = segment.V
                    current_norm = segment.norm_f
                    converged = segment.converged
                    restart_count += 1
                else:
                    can_continue = False

                if verbose:
                    if logger is not None:
                        logger.add_debug("DPRHEM restart", restart_count)
                        logger.add_debug("DPRHEM norm", current_norm)
                    else:
                        verbose = verbose
                else:
                    verbose = verbose
            else:
                can_continue = False

    return DprCoefficientPath(U=Ulast,
                              X=Xlast,
                              Q=Qlast,
                              V=Vbest,
                              iterations=iterations,
                              converged=converged,
                              segments=segments)


def helm_coefficients_dpr(Ybus: CscMat, Yseries: CscMat, V0: CxVec | None, Vset: CxVec, S0: CxVec, Ysh0: CxVec,
                          pq: IntVec, pv: IntVec, pqv: IntVec, p: IntVec, sl: IntVec, no_slack: IntVec,
                          tolerance: float = 1e-6, max_coeff: int = 30,
                          restart_order: int = 6, max_restarts: int = 20,
                          use_classical_germ: bool = False,
                          allow_dynamic_restart: bool = True,
                          verbose: bool = False, logger: Logger = None) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                                                                  CxVec, int, bool]:
    """
    Compute DPRHEM coefficients and final voltage state.

    This keeps the original tuple-returning interface. Use :func:`helm_coefficients_dpr_path` when the accepted DPR
    restart segments are needed, for example by DPR sigma analysis.

    :param Ybus: Complete admittance matrix.
    :param Yseries: Series-only admittance matrix.
    :param V0: Voltage estimate/set-point vector.
    :param Vset: Voltage set-point vector.
    :param S0: Specified complex bus powers.
    :param Ysh0: Bus shunt admittance vector.
    :param pq: Original PQ bus indices.
    :param pv: Original PV bus indices.
    :param pqv: Original PVQ bus indices.
    :param p: Original P bus indices.
    :param sl: Slack bus indices.
    :param no_slack: Original non-slack bus indices.
    :param tolerance: Target mismatch tolerance.
    :param max_coeff: Total coefficient budget across restarts.
    :param restart_order: Maximum coefficient order per segment.
    :param max_restarts: Maximum number of DPRHEM restarts.
    :param use_classical_germ: Use the classical no-load germ instead of the supplied voltage estimate.
    :param allow_dynamic_restart: Let the residual-ratio rule truncate a segment and restart from its best voltage.
    :param verbose: Store debug information.
    :param logger: Logger object.
    :return: Last segment U, X, Q, final voltage, total iterations and convergence flag.
    """

    path: DprCoefficientPath = helm_coefficients_dpr_path(Ybus=Ybus,
                                                          Yseries=Yseries,
                                                          V0=V0,
                                                          Vset=Vset,
                                                          S0=S0,
                                                          Ysh0=Ysh0,
                                                          pq=pq,
                                                          pv=pv,
                                                          pqv=pqv,
                                                          p=p,
                                                          sl=sl,
                                                          no_slack=no_slack,
                                                          tolerance=tolerance,
                                                          max_coeff=max_coeff,
                                                          restart_order=restart_order,
                                                          max_restarts=max_restarts,
                                                          use_classical_germ=use_classical_germ,
                                                          allow_dynamic_restart=allow_dynamic_restart,
                                                          verbose=verbose,
                                                          logger=logger)

    return path.U, path.X, path.Q, path.V, path.iterations, path.converged


def helm_dpr_fixed_model(nc: NumericalCircuit,
                         Ybus: CscMat, Yf: CscMat, Yt: CscMat, Yshunt_bus: CxVec,
                         Yseries: CscMat, V0: CxVec | None, S0: CxVec, Ysh0: CxVec,
                         pq: IntVec, pv: IntVec, vd: IntVec, no_slack: IntVec,
                         pqv: IntVec | None = None, p: IntVec | None = None,
                         tolerance: float = 1e-6, max_coefficients: int = 30, use_pade: bool = True,
                         restart_order: int = 6, max_restarts: int = 20,
                         use_classical_germ: bool = False,
                         verbose: int = 0, logger: Logger = None) -> NumericPowerFlowResults:
    """
    Solve one fixed-control power flow model with the DPRHEM variant in this module.

    :param nc: Numerical circuit island.
    :param Ybus: Complete admittance matrix.
    :param Yf: Branch-from admittance matrix.
    :param Yt: Branch-to admittance matrix.
    :param Yshunt_bus: Bus shunt admittance vector.
    :param Yseries: Series-only admittance matrix.
    :param V0: Voltage estimate/set-point vector.
    :param S0: Specified complex bus powers.
    :param Ysh0: Bus shunt admittance vector including branch shunt legs.
    :param pq: PQ bus indices.
    :param pv: PV bus indices.
    :param vd: Slack bus indices.
    :param no_slack: Sorted PQ/PV bus indices.
    :param pqv: PVQ bus indices.
    :param p: P bus indices.
    :param tolerance: Target mismatch tolerance.
    :param max_coefficients: Total coefficient budget.
    :param use_pade: Kept for interface compatibility; restarts use direct summation.
    :param restart_order: Maximum coefficient order per segment.
    :param max_restarts: Maximum restart count.
    :param use_classical_germ: Use the classical no-load germ instead of the supplied voltage estimate.
    :param verbose: Verbosity flag.
    :param logger: Logger object.
    :return: Numeric power-flow results for the fixed model.
    """

    start_time: float = time.time()
    Vset: CxVec = nc.bus_data.Vbus

    # Fixed-model solve: these bus sets and matrices must remain constant for the whole coefficient computation.
    # Control changes are handled only by the public helm_dpr wrapper after this function returns.
    active_pqv: IntVec = np.zeros(0, dtype=int) if pqv is None else pqv
    active_p: IntVec = np.zeros(0, dtype=int) if p is None else p

    if nc.bus_data.nbus < 2:
        results: NumericPowerFlowResults = NumericPowerFlowResults(
            V=V0,
            Scalc=S0,
            m=np.ones(nc.nbr, dtype=float),
            tau=np.zeros(nc.nbr, dtype=float),
            Sf=np.zeros(nc.nbr, dtype=complex),
            St=np.zeros(nc.nbr, dtype=complex),
            If=np.zeros(nc.nbr, dtype=complex),
            It=np.zeros(nc.nbr, dtype=complex),
            loading=np.zeros(nc.nbr, dtype=complex),
            losses=np.zeros(nc.nbr, dtype=complex),
            Pfp_vsc=np.zeros(nc.nvsc, dtype=float),
            Pfn_vsc=np.zeros(nc.nvsc, dtype=float),
            St_vsc=np.zeros(nc.nvsc, dtype=complex),
            If_vsc=np.zeros(nc.nvsc, dtype=float),
            It_vsc=np.zeros(nc.nvsc, dtype=complex),
            losses_vsc=np.zeros(nc.nvsc, dtype=float),
            loading_vsc=np.zeros(nc.nvsc, dtype=float),
            Sf_hvdc=np.zeros(nc.nhvdc, dtype=complex),
            St_hvdc=np.zeros(nc.nhvdc, dtype=complex),
            losses_hvdc=np.zeros(nc.nhvdc, dtype=complex),
            loading_hvdc=np.zeros(nc.nhvdc, dtype=complex),
            norm_f=0.0,
            converged=False,
            iterations=0,
            elapsed=0.0
        )
    else:
        U: np.ndarray
        X: np.ndarray
        Q: np.ndarray
        V: CxVec
        iter_: int
        converged: bool

        # Compute the DPR coefficients for one fixed algebraic model. This call may internally restart the HELM
        # expansion center, but it does not apply discrete controls or rebuild the model.
        U, X, Q, V, iter_, converged = helm_coefficients_dpr(Ybus=Ybus,
                                                             Yseries=Yseries,
                                                             V0=V0,
                                                             Vset=Vset,
                                                             S0=S0,
                                                             Ysh0=Ysh0,
                                                             pq=pq,
                                                             pv=pv,
                                                             pqv=active_pqv,
                                                             p=active_p,
                                                             sl=vd,
                                                             no_slack=no_slack,
                                                             tolerance=tolerance,
                                                             max_coeff=max_coefficients,
                                                             restart_order=restart_order,
                                                             max_restarts=max_restarts,
                                                             use_classical_germ=use_classical_germ,
                                                             verbose=bool(verbose),
                                                             logger=logger)

        # Padé across restart boundaries is not meaningful because each segment has its own germ. The argument remains
        # for interface compatibility with the base HELM solver.
        if use_pade:
            use_pade = use_pade
        else:
            use_pade = use_pade

        Scalc: CxVec = cf.compute_power(Ybus, V)

        # Recompute the final mismatch from the physical voltage because the accepted candidate may be a damped or
        # Padé-evaluated point on the last local segment.
        norm_f: float = dpr_power_mismatch(Ybus=Ybus,
                                           V=V,
                                           S0=S0,
                                           no_slack=no_slack,
                                           pq=pq,
                                           pqv=active_pqv,
                                           Vset=Vset)
        converged = norm_f < tolerance
        elapsed: float = time.time() - start_time

        if verbose:
            if logger is not None:
                logger.add_debug("DPRHEM V coefficients\n", U)
                logger.add_debug("DPRHEM X coefficients\n", X)
                logger.add_debug("DPRHEM Q coefficients\n", Q)
            else:
                verbose = verbose
        else:
            verbose = verbose

        Sf, St, If, It, Vbranch, loading, losses, Sbus = cf.power_flow_post_process_nonlinear(
            Sbus=Scalc,
            V=V,
            F=nc.passive_branch_data.F,
            T=nc.passive_branch_data.T,
            pv=pv,
            vd=vd,
            Ybus=Ybus,
            Yf=Yf,
            Yt=Yt,
            Yshunt_bus=Yshunt_bus,
            branch_rates=nc.passive_branch_data.rates,
            Sbase=nc.Sbase
        )

        results = NumericPowerFlowResults(
            V=V,
            Scalc=Scalc * nc.Sbase,
            m=np.ones(nc.nbr, dtype=float),
            tau=np.zeros(nc.nbr, dtype=float),
            Sf=Sf,
            St=St,
            If=If,
            It=It,
            loading=loading,
            losses=losses,
            Pfp_vsc=np.zeros(nc.nvsc, dtype=float),
            Pfn_vsc=np.zeros(nc.nvsc, dtype=float),
            St_vsc=np.zeros(nc.nvsc, dtype=complex),
            If_vsc=np.zeros(nc.nvsc, dtype=float),
            It_vsc=np.zeros(nc.nvsc, dtype=complex),
            losses_vsc=np.zeros(nc.nvsc, dtype=float),
            loading_vsc=np.zeros(nc.nvsc, dtype=float),
            Sf_hvdc=np.zeros(nc.nhvdc, dtype=complex),
            St_hvdc=np.zeros(nc.nhvdc, dtype=complex),
            losses_hvdc=np.zeros(nc.nhvdc, dtype=complex),
            loading_hvdc=np.zeros(nc.nhvdc, dtype=complex),
            norm_f=norm_f,
            converged=converged,
            iterations=iter_,
            elapsed=elapsed
        )

    return results


def helm_dpr(nc: NumericalCircuit,
             Ybus: CscMat, Yf: CscMat, Yt: CscMat, Yshunt_bus: CxVec,
             Yseries: CscMat, V0: CxVec | None, S0: CxVec, Ysh0: CxVec,
             pq: IntVec, pv: IntVec, vd: IntVec, no_slack: IntVec,
             tolerance: float = 1e-6, max_coefficients: int = 30, use_pade: bool = True,
             restart_order: int = 6, max_restarts: int = 20,
             use_classical_germ: bool = False,
             control_q: bool = False, pqv: IntVec | None = None, p: IntVec | None = None,
             Qmin: Vec | None = None, Qmax: Vec | None = None,
             control_discrete_shunts: bool = False, control_qv_droop: bool = False,
             distributed_slack: bool = False, bus_installed_power: Vec | None = None,
             controls_tol: float = 1e-3, max_control_restarts: int = 3,
             verbose: int = 0, logger: Logger = None) -> NumericPowerFlowResults:
    """
    Solve power flow with DPRHEM and apply discrete controls at DPR restart boundaries.

    :param nc: Numerical circuit island.
    :param Ybus: Complete admittance matrix.
    :param Yf: Branch-from admittance matrix.
    :param Yt: Branch-to admittance matrix.
    :param Yshunt_bus: Bus shunt admittance vector.
    :param Yseries: Series-only admittance matrix.
    :param V0: Voltage estimate/set-point vector.
    :param S0: Specified complex bus powers in p.u.
    :param Ysh0: Bus shunt admittance vector including branch shunt legs.
    :param pq: PQ bus indices.
    :param pv: PV bus indices.
    :param vd: Slack bus indices.
    :param no_slack: Sorted PQ/PV bus indices.
    :param tolerance: Target mismatch tolerance.
    :param max_coefficients: Total coefficient budget for each fixed-control DPR solve.
    :param use_pade: Kept for interface compatibility; restarts use direct summation.
    :param restart_order: Maximum coefficient order per DPR segment.
    :param max_restarts: Maximum DPR restart count for each fixed-control solve.
    :param use_classical_germ: Use the classical flat germ instead of the supplied voltage estimate.
    :param control_q: Apply PV-to-PQ reactive limit control at accepted DPR states.
    :param pqv: PQV bus indices used by the Q-limit control.
    :param p: P bus indices used by the Q-limit control.
    :param Qmin: Minimum reactive power limits in p.u.
    :param Qmax: Maximum reactive power limits in p.u.
    :param control_discrete_shunts: Apply discrete shunt controls at accepted DPR states.
    :param control_qv_droop: Apply generator QV droop controls at accepted DPR states.
    :param distributed_slack: Apply one distributed slack correction at an accepted DPR state.
    :param bus_installed_power: Installed power per bus for distributed slack participation.
    :param controls_tol: Residual threshold below which discrete controls are trusted.
    :param max_control_restarts: Maximum outer restarts caused by controls.
    :param verbose: Verbosity flag.
    :param logger: Logger object.
    :return: Numeric power-flow results.
    """

    start_time: float = time.time()

    # Work on active copies so control updates do not mutate the caller's base matrices or base power vector. The
    # public wrapper owns these mutable model states across control restarts.
    active_S0: CxVec = S0.copy()
    active_Ybus: CscMat = Ybus.copy()
    active_Yshunt_bus: CxVec = Yshunt_bus.copy()
    active_Ysh0: CxVec = Ysh0.copy()
    active_adm_view: DprAdmittanceControlView = DprAdmittanceControlView(Ybus=active_Ybus,
                                                                         Yshunt_bus=active_Yshunt_bus)
    active_V0: CxVec | None = None if V0 is None else V0.copy()
    active_pq: IntVec = pq.copy()
    active_pv: IntVec = pv.copy()
    active_pqv: IntVec = np.zeros(0, dtype=int) if pqv is None else pqv.copy()
    active_p: IntVec = np.zeros(0, dtype=int) if p is None else p.copy()
    active_use_classical_germ: bool = use_classical_germ
    control_restart: int = 0
    total_iterations: int = 0
    controls_pending: bool = True
    slack_distributed: bool = False
    discrete_shunt_control: DiscreteShuntControlState | None = None
    qv_droop_control: QvDroopControlState | None = None

    if control_discrete_shunts:
        # Discrete shunts change Ybus and shunt injections. The control view lets the existing control code update the
        # active DPR matrices in place, then the wrapper restarts a fixed-model DPR solve from the accepted voltage.
        discrete_shunt_control = DiscreteShuntControlState(nc=nc)
    else:
        discrete_shunt_control = None

    if control_qv_droop:
        # QV droop changes the specified bus injection S0. It is a model update, so it is applied only after DPR has
        # reached a trustworthy residual for the current fixed model.
        qv_droop_control = QvDroopControlState(S0=active_S0, nc=nc)
    else:
        qv_droop_control = None

    solution: NumericPowerFlowResults = helm_dpr_fixed_model(
        nc=nc,
        Ybus=active_Ybus,
        Yf=Yf,
        Yt=Yt,
        Yshunt_bus=active_Yshunt_bus,
        Yseries=Yseries,
        V0=active_V0,
        S0=active_S0,
        Ysh0=active_Ysh0,
        pq=active_pq,
        pv=active_pv,
        vd=vd,
        no_slack=no_slack,
        pqv=active_pqv,
        p=active_p,
        tolerance=tolerance,
        max_coefficients=max_coefficients,
        use_pade=use_pade,
        restart_order=restart_order,
        max_restarts=max_restarts,
        use_classical_germ=active_use_classical_germ,
        verbose=verbose,
        logger=logger
    )

    while controls_pending and control_restart < max_control_restarts:
        controls_pending = False

        # Controls use physical powers, so only trust them once DPR is close enough to the current fixed model.
        if solution.norm_f < controls_tol:
            if control_q and Qmin is not None and Qmax is not None and (len(active_pv) + len(active_p)) > 0:
                Scalc_pu: CxVec = cf.compute_power(active_Ybus, solution.V)

                # Reactive limits convert voltage-controlled generators to fixed-Q buses, just like the Newton
                # formulation update. This changes the bus-type partition, so another fixed-model DPR solve is needed.
                changed, active_pv, active_pq, active_pqv, active_p = control_q_inside_method(
                    Scalc=Scalc_pu,
                    S0=active_S0,
                    pv=active_pv,
                    pq=active_pq,
                    pqv=active_pqv,
                    p=active_p,
                    Qmin=Qmin,
                    Qmax=Qmax
                )
                if len(changed) > 0:
                    controls_pending = True
                else:
                    controls_pending = controls_pending
            else:
                controls_pending = controls_pending

            if discrete_shunt_control is not None:
                if discrete_shunt_control.apply(Vm=np.abs(solution.V),
                                                adm=active_adm_view,
                                                yshunt_bus=active_Ysh0):
                    controls_pending = True
                else:
                    controls_pending = controls_pending
            else:
                controls_pending = controls_pending

            if qv_droop_control is not None:
                if qv_droop_control.apply(S0=active_S0, Vm=np.abs(solution.V)):
                    controls_pending = True
                else:
                    controls_pending = controls_pending
            else:
                controls_pending = controls_pending

            if distributed_slack and not slack_distributed and bus_installed_power is not None:
                Scalc_pu = cf.compute_power(active_Ybus, solution.V)

                # Slack redistribution changes target active injections. Apply it once, matching the existing HELM and
                # linear solver behavior, then restart DPR from the accepted voltage.
                ok, delta = compute_slack_distribution(
                    Scalc=Scalc_pu,
                    vd=vd,
                    bus_installed_power=bus_installed_power
                )
                if ok:
                    active_S0 += delta
                    slack_distributed = True
                    controls_pending = True
                else:
                    controls_pending = controls_pending
            else:
                controls_pending = controls_pending
        else:
            controls_pending = False

        if controls_pending:
            control_restart += 1
            total_iterations += solution.iterations
            active_V0 = solution.V

            # After the first control update we must restart from the accepted physical voltage, not from the flat germ.
            active_use_classical_germ = False
            solution = helm_dpr_fixed_model(
                nc=nc,
                Ybus=active_Ybus,
                Yf=Yf,
                Yt=Yt,
                Yshunt_bus=active_Yshunt_bus,
                Yseries=Yseries,
                V0=active_V0,
                S0=active_S0,
                Ysh0=active_Ysh0,
                pq=active_pq,
                pv=active_pv,
                vd=vd,
                no_slack=no_slack,
                pqv=active_pqv,
                p=active_p,
                tolerance=tolerance,
                max_coefficients=max_coefficients,
                use_pade=use_pade,
                restart_order=restart_order,
                max_restarts=max_restarts,
                use_classical_germ=active_use_classical_germ,
                verbose=verbose,
                logger=logger
            )
        else:
            controls_pending = controls_pending

    total_iterations += solution.iterations

    solution.iterations = total_iterations
    solution.elapsed = time.time() - start_time

    return solution
