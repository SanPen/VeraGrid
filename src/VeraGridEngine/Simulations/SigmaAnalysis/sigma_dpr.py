# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
DPRHEM sigma analysis.

Canonical sigma analysis assumes one HELM embedding from the no-load germ to the target system. DPRHEM is different:
it is a sequence of accepted local embeddings around physical restart voltages, as described in the DPRHEM paper:
https://www.sciencedirect.com/science/article/pii/S0142061525004715

This module therefore computes sigma as a DPR path metric. For each accepted segment of the final fixed-control model
it evaluates the standard sigma function locally, then reports the per-bus worst distance over that controlled DPR
path. Control actions are treated as model discontinuities, not analytic continuation segments, so earlier pre-control
segments are discarded when a control restart changes the fixed algebraic model.
"""

import time

import numpy as np

import VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions as cf
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls import (DiscreteShuntControlState,
                                                                                     QvDroopControlState,
                                                                                     compute_slack_distribution,
                                                                                     control_q_inside_method)
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.helm_dpr import (DprAdmittanceControlView,
                                                                            DprCoefficientPath,
                                                                            DprSegmentResult,
                                                                            dpr_power_mismatch,
                                                                            helm_coefficients_dpr_path)
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.helm_power_flow import sigma_function
from VeraGridEngine.basic_structures import CscMat, CxVec, IntVec, Logger, Vec


class DprSigmaPath:
    """
    Sigma values obtained from the accepted DPRHEM segments of one fixed-control model.

    :param sigma_re: Per-bus sigma real coordinate selected from the worst local DPR segment.
    :param sigma_im: Per-bus sigma imaginary coordinate selected from the worst local DPR segment.
    :param distances: Per-bus minimum sigma distance over the accepted DPR path.
    :param segment_distances: Matrix with one distance row per accepted DPR segment.
    """

    __slots__ = ("sigma_re", "sigma_im", "distances", "segment_distances")

    def __init__(self,
                 sigma_re: Vec,
                 sigma_im: Vec,
                 distances: Vec,
                 segment_distances: np.ndarray) -> None:
        """
        Build the DPR sigma path values.

        :param sigma_re: Per-bus sigma real coordinate selected from the worst local DPR segment.
        :param sigma_im: Per-bus sigma imaginary coordinate selected from the worst local DPR segment.
        :param distances: Per-bus minimum sigma distance over the accepted DPR path.
        :param segment_distances: Matrix with one distance row per accepted DPR segment.
        :return: None.
        """

        self.sigma_re: Vec = sigma_re
        self.sigma_im: Vec = sigma_im
        self.distances: Vec = distances
        self.segment_distances: np.ndarray = segment_distances


class DprSigmaResult:
    """
    DPRHEM sigma result for the final controlled model.

    :param V: Final voltage vector used by the settled controlled model.
    :param norm_f: Final power-flow mismatch norm.
    :param converged: True when the final controlled model satisfies the requested tolerance.
    :param iterations: Total coefficient orders consumed, including control restarts.
    :param control_restarts: Number of model restarts caused by controls.
    :param elapsed: Elapsed time in seconds.
    :param sigma_re: Per-bus sigma real coordinate selected from the worst local DPR segment.
    :param sigma_im: Per-bus sigma imaginary coordinate selected from the worst local DPR segment.
    :param distances: Per-bus minimum sigma distance over the accepted DPR path.
    :param segment_distances: Matrix with one distance row per accepted DPR segment.
    """

    __slots__ = ("V", "norm_f", "converged", "iterations", "control_restarts", "elapsed",
                 "sigma_re", "sigma_im", "distances", "segment_distances")

    def __init__(self,
                 V: CxVec,
                 norm_f: float,
                 converged: bool,
                 iterations: int,
                 control_restarts: int,
                 elapsed: float,
                 sigma_path: DprSigmaPath) -> None:
        """
        Build the DPRHEM sigma result.

        :param V: Final voltage vector used by the settled controlled model.
        :param norm_f: Final power-flow mismatch norm.
        :param converged: True when the final controlled model satisfies the requested tolerance.
        :param iterations: Total coefficient orders consumed, including control restarts.
        :param control_restarts: Number of model restarts caused by controls.
        :param elapsed: Elapsed time in seconds.
        :param sigma_path: Computed sigma path values.
        :return: None.
        """

        self.V: CxVec = V
        self.norm_f: float = norm_f
        self.converged: bool = converged
        self.iterations: int = iterations
        self.control_restarts: int = control_restarts
        self.elapsed: float = elapsed
        self.sigma_re: Vec = sigma_path.sigma_re
        self.sigma_im: Vec = sigma_path.sigma_im
        self.distances: Vec = sigma_path.distances
        self.segment_distances: np.ndarray = sigma_path.segment_distances


def dpr_sigma_distance(sigma_re: Vec, sigma_im: Vec) -> Vec:
    """
    Compute the canonical sigma distance without importing the driver at module import time.

    :param sigma_re: Sigma real coordinates.
    :param sigma_im: Sigma imaginary coordinates.
    :return: Distance of each sigma point to the collapse curve.
    """

    from VeraGridEngine.Simulations.SigmaAnalysis.sigma_analysis_driver import sigma_distance

    return sigma_distance(sigma_re, sigma_im)


def dpr_sigma_from_segments(segments: list[DprSegmentResult],
                            Vset: CxVec,
                            sl: IntVec,
                            no_slack: IntVec,
                            nbus: int) -> DprSigmaPath:
    """
    Compute the per-bus worst local sigma values over accepted DPRHEM segments.

    :param segments: Accepted DPRHEM segments for the final fixed-control model.
    :param Vset: Voltage set-point vector.
    :param sl: Slack bus indices.
    :param no_slack: Original non-slack bus indices.
    :param nbus: Number of buses.
    :return: DPR sigma path values.
    """

    valid_segments: list[DprSegmentResult] = list()

    for segment in segments:
        if segment.iterations > 0:
            valid_segments.append(segment)
        else:
            valid_segments = valid_segments

    if len(valid_segments) == 0:
        sigma_re: Vec = np.zeros(nbus, dtype=float)
        sigma_im: Vec = np.zeros(nbus, dtype=float)
        distances: Vec = dpr_sigma_distance(sigma_re=sigma_re, sigma_im=sigma_im)
        segment_distances: np.ndarray = np.zeros((0, nbus), dtype=float)
    else:
        segment_sigma_re: np.ndarray = np.zeros((len(valid_segments), nbus), dtype=float)
        segment_sigma_im: np.ndarray = np.zeros((len(valid_segments), nbus), dtype=float)
        segment_distances = np.zeros((len(valid_segments), nbus), dtype=float)

        # Each DPR restart has its own local coefficient system. The standard sigma function is only meaningful within
        # that segment, so aggregate local distances instead of pretending that the last segment is a global embedding.
        for idx, segment in enumerate(valid_segments):
            sigma: CxVec = sigma_function(segment.U, segment.X, segment.iterations, Vset[sl])
            segment_sigma_re[idx, no_slack] = sigma.real
            segment_sigma_im[idx, no_slack] = sigma.imag
            segment_distances[idx, :] = dpr_sigma_distance(sigma_re=segment_sigma_re[idx, :],
                                                           sigma_im=segment_sigma_im[idx, :])

        worst_segment_idx: np.ndarray = np.argmin(segment_distances, axis=0)
        bus_idx: np.ndarray = np.arange(nbus)
        sigma_re = segment_sigma_re[worst_segment_idx, bus_idx]
        sigma_im = segment_sigma_im[worst_segment_idx, bus_idx]
        distances = segment_distances[worst_segment_idx, bus_idx]

    return DprSigmaPath(sigma_re=sigma_re,
                        sigma_im=sigma_im,
                        distances=distances,
                        segment_distances=segment_distances)


def sigma_dpr_fixed_model(Ybus: CscMat,
                          Yseries: CscMat,
                          V0: CxVec | None,
                          Vset: CxVec,
                          S0: CxVec,
                          Ysh0: CxVec,
                          pq: IntVec,
                          pv: IntVec,
                          pqv: IntVec,
                          p: IntVec,
                          vd: IntVec,
                          no_slack: IntVec,
                          tolerance: float,
                          max_coefficients: int,
                          restart_order: int,
                          max_restarts: int,
                          use_classical_germ: bool,
                          allow_dynamic_restart: bool,
                          verbose: int,
                          logger: Logger | None) -> tuple[DprCoefficientPath, float, bool]:
    """
    Solve one fixed-control DPRHEM model and expose its accepted coefficient path.

    :param Ybus: Complete admittance matrix.
    :param Yseries: Series-only admittance matrix.
    :param V0: Voltage estimate/set-point vector.
    :param Vset: Voltage set-point vector.
    :param S0: Specified complex bus powers in p.u.
    :param Ysh0: Bus shunt admittance vector including branch shunt legs.
    :param pq: PQ bus indices.
    :param pv: PV bus indices.
    :param pqv: PVQ bus indices.
    :param p: P bus indices.
    :param vd: Slack bus indices.
    :param no_slack: Sorted non-slack bus indices.
    :param tolerance: Target mismatch tolerance.
    :param max_coefficients: Total coefficient budget.
    :param restart_order: Maximum coefficient order per DPR segment.
    :param max_restarts: Maximum DPR restart count.
    :param use_classical_germ: Use the classical flat germ instead of the supplied voltage estimate.
    :param allow_dynamic_restart: Let the residual-ratio rule truncate a segment and restart from its best voltage.
    :param verbose: Verbosity flag.
    :param logger: Logger object.
    :return: DPR coefficient path, final mismatch norm and convergence flag.
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
                                                          sl=vd,
                                                          no_slack=no_slack,
                                                          tolerance=tolerance,
                                                          max_coeff=max_coefficients,
                                                          restart_order=restart_order,
                                                          max_restarts=max_restarts,
                                                          use_classical_germ=use_classical_germ,
                                                          allow_dynamic_restart=allow_dynamic_restart,
                                                          verbose=bool(verbose),
                                                          logger=logger)
    norm_f: float = dpr_power_mismatch(Ybus=Ybus,
                                       V=path.V,
                                       S0=S0,
                                       no_slack=no_slack,
                                       pq=pq,
                                       pqv=pqv,
                                       Vset=Vset)
    converged: bool = norm_f < tolerance

    return path, norm_f, converged


def sigma_dpr(nc: NumericalCircuit,
              Ybus: CscMat,
              Yshunt_bus: CxVec,
              Yseries: CscMat,
              V0: CxVec | None,
              S0: CxVec,
              Ysh0: CxVec,
              pq: IntVec,
              pv: IntVec,
              vd: IntVec,
              no_slack: IntVec,
              tolerance: float = 1e-6,
              max_coefficients: int = 30,
              restart_order: int = 6,
              max_restarts: int = 20,
              use_classical_germ: bool = False,
              control_q: bool = False,
              pqv: IntVec | None = None,
              p: IntVec | None = None,
              Qmin: Vec | None = None,
              Qmax: Vec | None = None,
              control_discrete_shunts: bool = False,
              control_qv_droop: bool = False,
              distributed_slack: bool = False,
              bus_installed_power: Vec | None = None,
              controls_tol: float = 1e-3,
              max_control_restarts: int = 3,
              verbose: int = 0,
              logger: Logger | None = None) -> DprSigmaResult:
    """
    Compute DPRHEM sigma analysis after applying the same controls as the DPR power-flow solver.

    :param nc: Numerical circuit island.
    :param Ybus: Complete admittance matrix.
    :param Yshunt_bus: Bus shunt admittance vector.
    :param Yseries: Series-only admittance matrix.
    :param V0: Voltage estimate/set-point vector.
    :param S0: Specified complex bus powers in p.u.
    :param Ysh0: Bus shunt admittance vector including branch shunt legs.
    :param pq: PQ bus indices.
    :param pv: PV bus indices.
    :param vd: Slack bus indices.
    :param no_slack: Sorted non-slack bus indices.
    :param tolerance: Target mismatch tolerance.
    :param max_coefficients: Total coefficient budget for each fixed-control DPR solve.
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
    :return: DPRHEM sigma result for the final controlled model.
    """

    start_time: float = time.time()
    Vset: CxVec = nc.bus_data.Vbus
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

    if control_discrete_shunts:
        discrete_shunt_control: DiscreteShuntControlState | None = DiscreteShuntControlState(nc=nc)
    else:
        discrete_shunt_control = None

    if control_qv_droop:
        qv_droop_control: QvDroopControlState | None = QvDroopControlState(S0=active_S0, nc=nc)
    else:
        qv_droop_control = None

    path, norm_f, converged = sigma_dpr_fixed_model(Ybus=active_Ybus,
                                                    Yseries=Yseries,
                                                    V0=active_V0,
                                                    Vset=Vset,
                                                    S0=active_S0,
                                                    Ysh0=active_Ysh0,
                                                    pq=active_pq,
                                                    pv=active_pv,
                                                    pqv=active_pqv,
                                                    p=active_p,
                                                    vd=vd,
                                                    no_slack=no_slack,
                                                    tolerance=tolerance,
                                                    max_coefficients=max_coefficients,
                                                    restart_order=restart_order,
                                                    max_restarts=max_restarts,
                                                    use_classical_germ=active_use_classical_germ,
                                                    allow_dynamic_restart=True,
                                                    verbose=verbose,
                                                    logger=logger)

    while controls_pending and control_restart < max_control_restarts:
        controls_pending = False

        if norm_f < controls_tol:
            if control_q and Qmin is not None and Qmax is not None and (len(active_pv) + len(active_p)) > 0:
                Scalc_pu: CxVec = cf.compute_power(active_Ybus, path.V)
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
                controls_pending = len(changed) > 0
            else:
                controls_pending = controls_pending

            if discrete_shunt_control is not None:
                if discrete_shunt_control.apply(Vm=np.abs(path.V), adm=active_adm_view, yshunt_bus=active_Ysh0):
                    controls_pending = True
                else:
                    controls_pending = controls_pending
            else:
                controls_pending = controls_pending

            if qv_droop_control is not None:
                if qv_droop_control.apply(S0=active_S0, Vm=np.abs(path.V)):
                    controls_pending = True
                else:
                    controls_pending = controls_pending
            else:
                controls_pending = controls_pending

            if distributed_slack and not slack_distributed and bus_installed_power is not None:
                Scalc_pu = cf.compute_power(active_Ybus, path.V)
                ok, delta = compute_slack_distribution(Scalc=Scalc_pu,
                                                       vd=vd,
                                                       bus_installed_power=bus_installed_power)
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
            total_iterations += path.iterations
            active_V0 = path.V
            active_use_classical_germ = False
            path, norm_f, converged = sigma_dpr_fixed_model(Ybus=active_Ybus,
                                                            Yseries=Yseries,
                                                            V0=active_V0,
                                                            Vset=Vset,
                                                            S0=active_S0,
                                                            Ysh0=active_Ysh0,
                                                            pq=active_pq,
                                                            pv=active_pv,
                                                            pqv=active_pqv,
                                                            p=active_p,
                                                            vd=vd,
                                                            no_slack=no_slack,
                                                            tolerance=tolerance,
                                                            max_coefficients=max_coefficients,
                                                            restart_order=restart_order,
                                                            max_restarts=max_restarts,
                                                            use_classical_germ=active_use_classical_germ,
                                                            allow_dynamic_restart=True,
                                                            verbose=verbose,
                                                            logger=logger)
        else:
            controls_pending = controls_pending

    total_iterations += path.iterations
    pf_norm_f: float = norm_f
    pf_converged: bool = converged

    # Sigma needs continuation coefficients, not the tiny correction coefficients produced by accepted DPR restarts.
    # Once controls have settled, compute one full non-restarting DPR embedding from the no-load germ to the final
    # controlled model and use those coefficients for the sigma Padé system.
    sigma_coeff_path, sigma_norm_f, sigma_converged = sigma_dpr_fixed_model(Ybus=active_Ybus,
                                                                            Yseries=Yseries,
                                                                            V0=None,
                                                                            Vset=Vset,
                                                                            S0=active_S0,
                                                                            Ysh0=active_Ysh0,
                                                                            pq=active_pq,
                                                                            pv=active_pv,
                                                                            pqv=active_pqv,
                                                                            p=active_p,
                                                                            vd=vd,
                                                                            no_slack=no_slack,
                                                                            tolerance=tolerance,
                                                                            max_coefficients=max_coefficients,
                                                                            restart_order=max_coefficients,
                                                                            max_restarts=0,
                                                                            use_classical_germ=True,
                                                                            allow_dynamic_restart=False,
                                                                            verbose=verbose,
                                                                            logger=logger)
    # Sigma coefficients are an analytic diagnostic. Their direct summed voltage may fail the PF tolerance even when
    # the controlled DPR power-flow state has converged; report PF convergence and use the coefficients only for sigma.
    if verbose and logger is not None:
        logger.add_debug("DPR sigma coefficient norm", sigma_norm_f)
        logger.add_debug("DPR sigma coefficient converged", sigma_converged)
    else:
        verbose = verbose

    sigma_path: DprSigmaPath = dpr_sigma_from_segments(segments=sigma_coeff_path.segments,
                                                       Vset=Vset,
                                                       sl=vd,
                                                       no_slack=no_slack,
                                                       nbus=nc.bus_data.nbus)

    return DprSigmaResult(V=path.V,
                          norm_f=pf_norm_f,
                          converged=pf_converged,
                          iterations=total_iterations,
                          control_restarts=control_restart,
                          elapsed=time.time() - start_time,
                          sigma_path=sigma_path)
