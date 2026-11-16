# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import time
from typing import Dict
import scipy.sparse as sp
from numba import njit
from scipy.sparse import csc_matrix
from collections.abc import Callable

from VeraGridEngine.Utils.Sparse.sparse_solve import SparseProviderLinearSolver, solve_sparse_system_once
from VeraGridEngine.Utils.NumericalMethods.newton_factor_reuse import (
    get_adaptive_recompute_threshold,
    needs_confirming_correction,
    confirms_with_fresh_factors,
    factorization_inputs_changed,
    needs_factor_refresh,
)
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Simulations.Rms.initialization_rms import (
    project_initial_algebraic_state,
    solve_rms_newton_correction,
)
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.basic_structures import Vec, Mat
from VeraGridEngine.Simulations.Rms.jacobian_assembler import JacobianAssembler


@njit(cache=True, fastmath=False, error_model="numpy")
def discretize_residual(values: np.ndarray, previous: np.ndarray, h: float,
                        state_count: int, output: np.ndarray) -> None:
    """Replace raw differential equation rows with Backward Euler residuals."""
    for row in range(state_count):
        output[row] = values[row] - previous[row] - h * output[row]


@njit(cache=True, fastmath=False, error_model="numpy")
def discretize_jacobian(raw: np.ndarray, rows: np.ndarray, diagonal: np.ndarray,
                        h: float, state_count: int, output: np.ndarray) -> None:
    """Fill a fixed CSC Newton matrix from raw equation derivatives."""
    for entry in range(raw.size):
        if rows[entry] < state_count:
            output[entry] = -h * raw[entry]
        else:
            output[entry] = raw[entry]
    for entry in range(diagonal.size):
        output[diagonal[entry]] += 1.0


@njit(cache=True, fastmath=False, error_model="numpy")
def project_derivative_columns(raw: np.ndarray, destinations: np.ndarray,
                               orders: np.ndarray, h: float,
                               projected: np.ndarray) -> None:
    """Apply the Backward Euler derivative chain to independent AD columns."""
    projected[:] = 0.0
    for entry in range(raw.size):
        order = orders[entry]
        if order == 0:
            projected[destinations[entry]] += raw[entry]
        elif h != 0.0:
            projected[destinations[entry]] += raw[entry] / (h ** order)


class BackEulerImplicitIntegration:
    """
    Backward Euler implicit integration solver.
    """
    __slots__ = (
        "problem",
        "t0",
        "h",
        "max_iter_0",
        "steps",
        "t",
        "y",
        "tol",
        "_cancel_checker",
        "_sparse_solver_backend_provider",
        "_sparse_linear_solver",
        "_regularized_linear_solver",
        "_last_jacobian_evaluations",
        "_last_factorization_reuse_hits",
        "_last_forced_factorization_invalidations",
        "_last_inherited_factor_retries",
        "_last_confirming_corrections",
        "_timings",
        "_jacobian_assembler",
        "_derivative_base_indices",
        "_derivative_orders",
        "_residual",
        "_fixed_jacobian_pattern",
    )

    def __init__(self,
                 problem: RmsProblemTemplate,
                 t0: float,
                 t_end: float,
                 h: float,
                 max_iter: int,
                 tolerance: float = 1e-7,
                 cancel_checker: Callable[[], bool] | None = None,
                 sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = None) -> None:
        """
        Initializes an object to solve a given DAE (Differential-Algebraic Equation) problem using numerical
        methods. This constructor sets up the time grid and prepares storage for results.

        :param problem: The DAE solver problem instance containing the system equations and other solver
            configurations.
        :type problem: RmsProblemTemplate
        :param t0: The initial time of the simulation.
        :type t0: float
        :param t_end: The final time of the simulation.
        :type t_end: float
        :param h: The time step size to be used for the simulation.
        :type h: float
        :param max_iter: Maximum local Newton corrections; also the iteration
            limit passed to the existing initial projection.
        :type max_iter: int
        :param tolerance: Non-linear residual tolerance used by the Newton loop.
        :type tolerance: float
        :param cancel_checker: Optional cancellation callback checked at each macro time step.
        :type cancel_checker: Callable[[], bool] | None
        :param sparse_solver_backend_provider: Sparse LU provider; None inherits the problem selection or uses SuperLU.
        :type sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None
        :return: None
        :rtype: None
        """

        # if not problem.is_initialized():
        #     raise Exception('Problem is not initialized')

        self._timings: Dict[str, float] = {
            "jacobian_time": 0.0,
            "rhs_time": 0.0,
            "lag_update_time": 0.0,
            "linear_solver_time": 0.0,
            "initial_step_time": 0.0,
            "rhs_algeb_time": 0.0,
            "rhs_state_time": 0.0,
            "rhs_evaluation_time": 0.0,
            "jacobian_blocks_time": 0.0,
            "jac_j11_time": 0.0,
            "jac_j12_time": 0.0,
            "jac_j21_time": 0.0,
            "jac_j22_time": 0.0,
        }
        self.problem: RmsProblemTemplate = problem
        self.t0: float = t0
        self.h: float = h
        self.max_iter_0: int = max_iter
        self.steps: int = int(np.ceil((t_end - t0) / h))
        self.t: Vec = np.empty(self.steps + 1)
        self.y: Mat = np.empty((self.steps + 1, self.problem.get_all_vars_number()))
        self.tol: float = tolerance
        self._cancel_checker: Callable[[], bool] | None = cancel_checker
        self._sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = sparse_solver_backend_provider
        self._jacobian_assembler: JacobianAssembler = JacobianAssembler()
        self._residual = np.empty(0, dtype=float)
        self._fixed_jacobian_pattern = problem.has_fixed_equation_jacobian_pattern()
        self._derivative_base_indices = None
        self._derivative_orders = None
        if self.problem.get_diff_var_number() and self.problem.supports_derivative_jacobian_partials():
            self._derivative_base_indices = self.problem.get_diff_var_base_indices()
            self._derivative_orders = self.problem.get_diff_var_orders()

        # A direct constructor inherits the problem's already-resolved selection.
        if self._sparse_solver_backend_provider is None:
            self._sparse_solver_backend_provider = problem.get_sparse_solver_backend_provider()
        else:
            pass

        resolved_provider: SparseLinearSolverBackendProvider = (
            SuperLUSparseBackendProvider()
            if self._sparse_solver_backend_provider is None
            else self._sparse_solver_backend_provider
        )

        # Each temporal integrator owns its own factors; projections own another phase.
        self._sparse_linear_solver: SparseProviderLinearSolver = SparseProviderLinearSolver(resolved_provider)
        self._regularized_linear_solver: SparseProviderLinearSolver = SparseProviderLinearSolver(resolved_provider)

        # Work counters of the last simulate call (chord Newton reuse).
        self._last_jacobian_evaluations: int = 0
        self._last_factorization_reuse_hits: int = 0
        self._last_forced_factorization_invalidations: int = 0
        self._last_inherited_factor_retries: int = 0
        self._last_confirming_corrections: int = 0

    def get_timings(self) -> Dict[str, float]:
        return self._timings

    def _rhs_implicit(self,
                      x: Vec,
                      dx: Vec,
                      xn: Vec,
                      h: float) -> Vec:
        """Return a solver-owned residual buffer, overwritten on the next call."""
        _t0 = time.time()
        equations = self.problem.evaluate_equations(x, dx)
        if self._residual.shape != equations.shape:
            self._residual = np.empty_like(equations)
        residual = self._residual
        residual[:] = equations
        discretize_residual(x, xn, h, self.problem.get_states_number(), residual)
        self._timings["rhs_evaluation_time"] += time.time() - _t0
        return residual

    def _jacobian_implicit(self,
                           x: Vec,
                           dx: Vec,
                           h: float) -> sp.csc_matrix:
        """Form the Backward Euler Newton matrix from raw problem derivatives."""
        t0 = time.time()
        derivative_bases = self._derivative_base_indices
        assembler = self._jacobian_assembler
        if self.problem.get_diff_var_number() == 0:
            raw = self.problem.evaluate_equation_jacobian(x, dx)
            matrix = assembler.assemble_jacobian_implicit_raw(
                self.problem.get_states_number(), h, raw,
                fixed_pattern=self._fixed_jacobian_pattern)
        elif derivative_bases is not None:
            j11, j12, j13, j21, j22, j23 = self.problem.evaluate_jacobian_partials(x, dx)
            positions = np.arange(derivative_bases.size)
            chain = sp.csc_matrix(
                (h ** (-self._derivative_orders.astype(float)),
                 (positions, derivative_bases)),
                shape=(positions.size, self.problem.get_all_vars_number())
            )
            matrix = assembler.assemble_jacobian_implicit_partials(
                self.problem.get_states_number(), h,
                j11, j12, j13, j21, j22, j23, chain
            )
        else:
            j11, j12, j21, j22 = self.problem.evaluate_jacobian_blocks(x, dx, h)
            n_states = self.problem.get_states_number()
            matrix = (j22 if n_states == 0 else
                      assembler.assemble_jacobian_implicit(n_states, h, j11, j12, j21, j22))
        self._timings["jacobian_blocks_time"] += time.time() - t0
        return matrix

    def _solve_linear_correction(self, jacobian: sp.csc_matrix, residual: Vec,
                                 reference_column: int | None, direct_failed: bool = False) -> Vec:
        """Try the direct solve (unless the caller has just seen it fail), regularization, then least squares."""
        delta = np.full(jacobian.shape[1], np.nan)
        if direct_failed:
            pass
        else:
            try:
                delta = solve_rms_newton_correction(
                    jacobian=jacobian,
                    residual=residual,
                    reference_column=reference_column,
                    sparse_solver_backend_provider=self._sparse_solver_backend_provider,
                    linear_solver=self._sparse_linear_solver,
                )
            except (RuntimeError, ValueError, np.linalg.LinAlgError):
                pass
        if np.all(np.isfinite(delta)):
            return delta

        if jacobian.shape[0] == jacobian.shape[1]:
            lam = 1e-4
            while lam <= 1e-1:
                try:
                    delta = solve_sparse_system_once(
                        (jacobian + lam * sp.eye(jacobian.shape[0], format="csc")).tocsc(),
                        -residual,
                        self._sparse_solver_backend_provider,
                        self._regularized_linear_solver,
                    )
                except (RuntimeError, ValueError, np.linalg.LinAlgError):
                    pass
                if np.all(np.isfinite(delta)):
                    return delta
                lam *= 1000.0

        try:
            delta = sp.linalg.lsqr(jacobian, -residual)[0]
        except (RuntimeError, ValueError, np.linalg.LinAlgError):
            pass
        return delta

    def simulate(self) -> tuple[Vec, Mat, bool, bool]:
        """Integrate accepted local steps with a bounded Newton correction count.

        The final allowed correction is checked against the configured strict
        tolerance. Failed steps expose only initial and completed macro samples.

        :return: Matching time/state prefixes, initial projection status and
            convergence status of the requested trajectory.
        """
        converged: bool = False
        completed_samples: int = 1

        x0: Vec = self.problem.get_x0()

        # we assume steady state
        dx0: Vec = np.zeros(self.problem.get_diff_var_number(), dtype=float)
        self.problem.update_variable_params(
            t=self.t0,
            x_snapshot=x0,
            scheduled_t=self.t0,
        )
        self.problem.update_with_current_parameters(self.t0, x0)
        initial_residual: float
        x0, well_initialized, initial_residual = project_initial_algebraic_state(
            problem=self.problem,
            initial_values=x0,
            differential_values=dx0,
            tolerance=self.tol,
            max_iter=self.max_iter_0,
            sparse_solver_backend_provider=self._sparse_solver_backend_provider,
        )
        if well_initialized:
            pass
        else:
            self.problem.logger.add_error(
                msg="RMS algebraic initial projection did not converge",
                device=type(self).__name__,
                value=initial_residual,
                expected_value=self.tol,
            )

        # timing accumulators
        self._timings = {
            "jacobian_time": 0.0,
            "rhs_time": 0.0,
            "lag_update_time": 0.0,
            "linear_solver_time": 0.0,
            "initial_step_time": 0.0,
            "rhs_algeb_time": 0.0,
            "rhs_state_time": 0.0,
            "rhs_evaluation_time": 0.0,
            "jacobian_blocks_time": 0.0,
            "jac_j11_time": 0.0,
            "jac_j12_time": 0.0,
            "jac_j21_time": 0.0,
            "jac_j22_time": 0.0,
        }
        timings = self._timings

        self.t[0] = self.t0
        dx = dx0.copy()
        dx_last = dx0.copy()
        residual = 0.0
        self.y[0, :] = x0.copy()

        # This numerical phase owns eligibility; prior simulate calls cannot lend it.
        self._sparse_linear_solver.invalidate()
        self._regularized_linear_solver.invalidate()
        self._last_jacobian_evaluations = 0
        self._last_factorization_reuse_hits = 0
        self._last_forced_factorization_invalidations = 0
        self._last_inherited_factor_retries = 0
        self._last_confirming_corrections = 0
        # Active FMI adapters carry external state, so they keep the fresh-Jacobian path.
        reuse_enabled: bool = (len(self.problem._fmu_me_adapters) == 0
                               and len(self.problem._fmu_cs_adapters) == 0)
        cached_jacobian: sp.csc_matrix | None = None
        factorization_step: float = 0.0
        factorization_reference: tuple[int, int] | None = None
        last_macro_iterations: int = 0
        runtime_count: int = self.problem._variable_parameters_values.shape[0]
        if self.problem._constant_params is None:
            constant_count: int = 0
        else:
            constant_count = self.problem._constant_params.shape[0]
        full_parameters: Vec = np.empty(runtime_count + constant_count, dtype=np.float64)
        factorization_parameters: Vec = np.empty_like(full_parameters)
        attempt_seed: Vec = np.empty_like(x0)
        confirming_state: Vec = np.empty_like(x0)
        confirming_derivatives: Vec = np.empty_like(dx0)

        has_fmu_cs = True
        has_fmu_me = True

        try:
            self.problem.initialize_fmu_cs_devices(x0, self.t0)
        except AttributeError:
            has_fmu_cs = False

        try:
            self.problem.initialize_fmu_me_devices(x0, self.t0)
        except AttributeError:
            has_fmu_me = False

        try:
            # pr = profile.Profile()
            # pr.disable()
            # pr.enable()
            for step_idx in range(self.steps):
                if self._cancel_checker is not None and self._cancel_checker():
                    self._sparse_linear_solver.invalidate()
                    self._regularized_linear_solver.invalidate()
                    return self.t[:step_idx + 1].copy(), self.y[:step_idx + 1, :].copy(), well_initialized, converged

                self.problem.report_progress2(step_idx, self.steps)

                t_current_macro: float = self.t[step_idx]
                # Derive every macro boundary from the integer step index so
                # floating-point accumulation cannot activate an event early.
                t_macro_target: float = self.t0 + float(step_idx + 1) * self.h

                x_prev = self.y[step_idx, :].copy()
                x_new = x_prev.copy()
                t_local_prev = t_current_macro
                is_first_local_step = True
                dx_last = dx
                substep_converged = True

                while t_local_prev < (t_macro_target - 1e-15):
                    forced_event_time: float | None = self.problem.get_next_forced_event_time(
                        t_local_prev,
                        t_macro_target,
                    )

                    if forced_event_time is None:
                        t_curr = t_macro_target
                    else:
                        t_curr = forced_event_time

                    h_eff: float = t_curr - t_local_prev
                    if h_eff <= 0.0:
                        self.problem.logger.add_error(
                            msg=(f"Invalid RMS local step size {h_eff:g} s at "
                                 f"time {t_local_prev:g} s (macro step {step_idx + 1}). "
                                 f"Completed results through "
                                 f"{self.t[completed_samples - 1]:g} s are retained; "
                                 f"the failed step is omitted."),
                            device=type(self).__name__,
                        )
                        substep_converged = False
                        converged = False
                        break

                    # Continuous controls use the local target so a step at an
                    # accepted boundary drives the immediately following
                    # interval. Scheduled modes retain the previous time view
                    # because their latches own separate boundary semantics.
                    self.problem.update_variable_params(t=t_curr,
                                                        x_snapshot=x_new,
                                                        scheduled_t=t_local_prev)

                    self.problem.update_with_current_parameters(t_curr, x_new)

                    if has_fmu_me:
                        self.problem.advance_fmu_me_devices(t=t_local_prev, x_snapshot=x_prev, h=h_eff)
                        state_event_retry_time: float | None = (
                            self.problem.prepare_fmu_me_state_event_retry()
                        )
                    else:
                        state_event_retry_time = None
                    co_simulation_advanced: bool = False
                    if has_fmu_cs and state_event_retry_time is None:
                        co_simulation_advanced = (
                            self.problem.advance_fmu_cs_devices(
                                t=t_local_prev,
                                x_snapshot=x_prev,
                                h=h_eff,
                            )
                        )
                    else:
                        pass

                    # Retained factors are valid only for the same step, parameters and gauge.
                    allow_reuse: bool = reuse_enabled
                    current_reference: tuple[int, int] | None = self.problem.get_small_signal_reference_indices()
                    full_parameters[:runtime_count] = self.problem._variable_parameters_values
                    if constant_count > 0:
                        full_parameters[runtime_count:] = self.problem._constant_params
                    else:
                        pass
                    if cached_jacobian is not None:
                        inputs_changed: bool = factorization_inputs_changed(
                            True, forced_event_time is not None, full_parameters,
                            factorization_parameters, h_eff, factorization_step)
                        if not allow_reuse or inputs_changed or current_reference != factorization_reference:
                            cached_jacobian = None
                            self._sparse_linear_solver.invalidate()
                            self._last_forced_factorization_invalidations += 1
                        else:
                            pass
                    else:
                        pass
                    attempt_seed[:] = x_new
                    n_iter: int = 0
                    tol: float = self.tol
                    attempt: int
                    for attempt in range(2):
                        # A failed attempt on retained factors retries once with fresh Jacobians.
                        n_iter = 0
                        substep_converged = state_event_retry_time is not None
                        last_residual: float = 1.0
                        attempt_reused_jacobian: bool = False
                        confirming_done: bool = False
                        confirming_pending: bool = False
                        confirming_fresh: bool = False
                        # Validate the last corrected point, even when no further
                        # correction is permitted, before resolving the FMI boundary.
                        while not substep_converged:
                            # A confirming trial may be discarded without publishing it.
                            if confirming_pending and not np.all(np.isfinite(x_new)):
                                x_new[:] = confirming_state
                                dx[:] = confirming_derivatives
                                substep_converged = True
                                cached_jacobian = None
                                self._sparse_linear_solver.invalidate()
                                break
                            else:
                                pass
                            if not np.all(np.isfinite(x_new)):
                                if not attempt_reused_jacobian or attempt > 0:
                                    self.problem.logger.add_error(
                                        msg=(f"Non-finite RMS candidate at {t_curr:g} s "
                                             f"(macro step {step_idx + 1}); the failed step is omitted."),
                                        device=type(self).__name__,
                                    )
                                else:
                                    pass
                                break
                            else:
                                pass
                            if step_idx == 0 and is_first_local_step:
                                dx = dx0.copy()
                            else:
                                dx = self.problem.get_dx(x_new, x_prev, dx_last, h_eff)

                            rhs_start = time.time()
                            rhs = self._rhs_implicit(x_new, dx, x_prev, h_eff)
                            rhs_end = time.time()
                            timings["rhs_time"] += rhs_end - rhs_start

                            # A full finite residual is required before either
                            # acceptance or a Jacobian evaluation can be safe.
                            if confirming_pending and not np.all(np.isfinite(rhs)):
                                x_new[:] = confirming_state
                                dx[:] = confirming_derivatives
                                substep_converged = True
                                cached_jacobian = None
                                self._sparse_linear_solver.invalidate()
                                break
                            else:
                                pass
                            if not np.all(np.isfinite(rhs)):
                                if not attempt_reused_jacobian or attempt > 0:
                                    self.problem.logger.add_error(
                                        msg=(f"Non-finite RMS residual at {t_curr:g} s "
                                             f"(macro step {step_idx + 1}); the failed step is omitted."),
                                        device=type(self).__name__,
                                    )
                                else:
                                    pass
                                break
                            else:
                                pass
                            residual = np.linalg.norm(rhs, np.inf)
                            substep_converged = residual < tol
                            if substep_converged and allow_reuse and attempt == 0 and needs_confirming_correction(
                                    False, confirming_done, n_iter, self.max_iter_0):
                                # Chord acceptance on weakly scaled rows: take one confirming correction.
                                confirming_done = True
                                confirming_pending = True
                                confirming_fresh = confirms_with_fresh_factors(residual, last_residual)
                                confirming_state[:] = x_new
                                confirming_derivatives[:] = dx
                                substep_converged = False
                                self._last_confirming_corrections += 1
                            elif not substep_converged and confirming_pending:
                                # The confirming correction broke the residual: restore the passing iterate.
                                x_new[:] = confirming_state
                                dx[:] = confirming_derivatives
                                substep_converged = True
                                cached_jacobian = None
                                self._sparse_linear_solver.invalidate()
                                break
                            else:
                                pass

                            if not substep_converged:
                                # The residual check consumes no correction budget;
                                # never assemble a Jacobian after that budget is spent.
                                if n_iter >= self.max_iter_0:
                                    if not attempt_reused_jacobian or attempt > 0:
                                        self.problem.logger.add_error(
                                            msg=(f"RMS Newton correction budget exhausted at {t_curr:g} s "
                                                 f"(macro step {step_idx + 1}); the failed step is omitted."),
                                            device=type(self).__name__,
                                            value=residual,
                                            expected_value=tol,
                                        )
                                    else:
                                        pass
                                    break
                                else:
                                    pass
                                refresh_factors: bool = (
                                        attempt > 0 or not allow_reuse or cached_jacobian is None
                                        or needs_factor_refresh(n_iter, residual, last_residual,
                                                                get_adaptive_recompute_threshold(last_macro_iterations),
                                                                tol, self.max_iter_0 - n_iter)
                                        or (confirming_pending and confirming_fresh))
                                Jf: sp.csc_matrix
                                if refresh_factors:
                                    jac_start = time.time()
                                    if allow_reuse:
                                        # Own the retained matrix; the assembler may hand back a reused buffer.
                                        cached_jacobian = self._jacobian_implicit(x_new, dx, h_eff).copy()
                                        Jf = cached_jacobian
                                    else:
                                        # Reuse disabled (active FMI adapters): nothing is retained.
                                        Jf = self._jacobian_implicit(x_new, dx, h_eff)
                                    timings["jacobian_time"] += time.time() - jac_start
                                    self._last_jacobian_evaluations += 1
                                    factorization_parameters[:] = full_parameters
                                    factorization_step = h_eff
                                    factorization_reference = current_reference
                                    if confirming_pending and confirming_fresh:
                                        self._sparse_linear_solver.invalidate()
                                    else:
                                        pass
                                elif cached_jacobian is not None:
                                    Jf = cached_jacobian
                                    attempt_reused_jacobian = True
                                    self._last_factorization_reuse_hits += 1
                                else:
                                    raise RuntimeError("RMS chord Newton has no retained Jacobian to reuse")
                                reference_indices: tuple[int, int] | None = (
                                    self.problem.get_small_signal_reference_indices()
                                )
                                reference_column: int | None
                                if reference_indices is not None:
                                    reference_column = reference_indices[1]
                                else:
                                    reference_column = None

                                if not np.all(np.isfinite(Jf.data)):
                                    cached_jacobian = None
                                    self._sparse_linear_solver.invalidate()
                                    if confirming_pending:
                                        x_new[:] = confirming_state
                                        dx[:] = confirming_derivatives
                                        substep_converged = True
                                    else:
                                        pass
                                    break
                                else:
                                    pass
                                direct_eligible: bool = (Jf.shape[0] == Jf.shape[1]
                                                         or (Jf.shape[0] + 1 == Jf.shape[
                                            1] and current_reference is not None
                                                             and 0 <= current_reference[1] < Jf.shape[1]))
                                linear_start = time.time()
                                delta: Vec
                                # The direct solve owns the retained factors; try it first in both cases.
                                try:
                                    delta = solve_rms_newton_correction(
                                        jacobian=Jf,
                                        residual=rhs,
                                        reference_column=reference_column,
                                        sparse_solver_backend_provider=self._sparse_solver_backend_provider,
                                        linear_solver=self._sparse_linear_solver,
                                    )
                                except (RuntimeError, ValueError, np.linalg.LinAlgError):
                                    delta = np.full(Jf.shape[1], np.nan)
                                if refresh_factors and not np.all(np.isfinite(delta)):
                                    # A fresh Jacobian whose direct solve failed: drop it and use the regularized
                                    # and least-squares fallbacks, so no later correction reuses these factors.
                                    cached_jacobian = None
                                    self._sparse_linear_solver.invalidate()
                                    delta = self._solve_linear_correction(Jf, rhs, reference_column, direct_failed=True)
                                else:
                                    pass
                                linear_end = time.time()
                                timings["linear_solver_time"] += linear_end - linear_start
                                solved = np.all(np.isfinite(delta))
                                if not direct_eligible:
                                    # The rectangular least-squares branch creates no LU to retain.
                                    cached_jacobian = None
                                    self._sparse_linear_solver.invalidate()
                                else:
                                    pass

                                if not solved:
                                    cached_jacobian = None
                                    self._sparse_linear_solver.invalidate()
                                    if confirming_pending:
                                        x_new[:] = confirming_state
                                        dx[:] = confirming_derivatives
                                        substep_converged = True
                                        break
                                    elif attempt_reused_jacobian and attempt == 0:
                                        # Retry with fresh Jacobians before reporting a failure.
                                        break
                                    else:
                                        pass
                                    nonfinite_rhs = np.flatnonzero(~np.isfinite(rhs)).tolist()
                                    self.problem.logger.add_error(
                                        msg=(f"RMS linear solve returned non-finite values at "
                                             f"time {t_curr:g} s (macro step {step_idx + 1}); "
                                             f"Jacobian shape={Jf.shape}, "
                                             f"non-finite RHS indices={nonfinite_rhs}. "
                                             f"Completed results through "
                                             f"{self.t[completed_samples - 1]:g} s are retained; "
                                             f"the failed step is omitted."),
                                        device=type(self).__name__,
                                    )
                                    substep_converged = False
                                    break
                                else:
                                    pass

                                # Bound large Newton corrections at discontinuities. A full
                                # step can jump to the zero-voltage power-balance root.
                                correction_max = np.max(np.abs(delta))
                                if correction_max > 1.0:
                                    delta = delta / correction_max
                                else:
                                    pass
                                previous_candidate: Vec = x_new.copy()
                                x_new += delta
                                # A finite correction below the current floating-point resolution cannot improve the residual.
                                if np.array_equal(x_new, previous_candidate):
                                    if confirming_pending:
                                        substep_converged = True
                                    elif not attempt_reused_jacobian or attempt > 0:
                                        self.problem.logger.add_error(
                                            msg=(f"RMS Newton correction did not change the candidate at "
                                                 f"{t_curr:g} s (macro step {step_idx + 1}); "
                                                 f"the failed step is omitted."),
                                            device=type(self).__name__,
                                        )
                                    else:
                                        pass
                                    break
                                else:
                                    pass
                                # Finite operands can overflow during the correction;
                                # reject before presenting this point to FMI ME inputs.
                                if not confirming_pending and not np.all(np.isfinite(x_new)):
                                    if not attempt_reused_jacobian or attempt > 0:
                                        self.problem.logger.add_error(
                                            msg=(f"Non-finite corrected RMS candidate at {t_curr:g} s "
                                                 f"(macro step {step_idx + 1}); the failed step is omitted."),
                                            device=type(self).__name__,
                                        )
                                    else:
                                        pass
                                    break
                                else:
                                    pass
                                if has_fmu_me:
                                    # Replace the candidate with outputs evaluated
                                    # from the corrected network iterate before the
                                    # next residual is formed.
                                    self.problem.advance_fmu_me_devices(
                                        t=t_local_prev,
                                        x_snapshot=x_new,
                                        h=h_eff,
                                    )
                                    state_event_retry_time = (
                                        self.problem.prepare_fmu_me_state_event_retry()
                                    )
                                    if state_event_retry_time is not None:
                                        if co_simulation_advanced:
                                            raise RuntimeError(
                                                "RMS FMI ME state event cannot retry after "
                                                f"Co-Simulation devices advanced at {t_curr:g} s"
                                            )
                                        else:
                                            substep_converged = True
                                    else:
                                        pass
                                else:
                                    pass
                                last_residual = float(residual)
                                n_iter += 1
                            else:
                                pass

                        if substep_converged or not attempt_reused_jacobian or attempt > 0 or state_event_retry_time is not None:
                            break
                        else:
                            x_new[:] = attempt_seed
                            cached_jacobian = None
                            self._sparse_linear_solver.invalidate()
                            self._regularized_linear_solver.invalidate()
                            self._last_inherited_factor_retries += 1
                    if substep_converged and state_event_retry_time is None:
                        last_macro_iterations = n_iter
                    else:
                        cached_jacobian = None
                        self._sparse_linear_solver.invalidate()

                    if substep_converged:
                        if state_event_retry_time is None:
                            if has_fmu_me:
                                self.problem.resolve_fmu_me_devices(accepted=True)
                            else:
                                pass
                            self.problem.resolve_manufacturer_native_boundary(
                                t=float(t_curr), x=x_new,
                            )
                            dx_last = dx.copy()
                            x_prev = x_new.copy()
                            t_local_prev = t_curr
                            is_first_local_step = False
                        else:
                            # Keep the accepted network point unchanged; the
                            # next local iteration targets the localized event.
                            x_new = x_prev.copy()
                    else:
                        if has_fmu_me:
                            self.problem.resolve_fmu_me_devices(accepted=False)
                        else:
                            pass
                        print(f"Failed to converge at step {step_idx} and n_iter is {n_iter}")
                        print(f"Residual is {residual}")
                        converged = False
                        break

                if not substep_converged:
                    break

                lag_update_start = time.time()
                # print(f'converged is {True} at step {step_idx} with {n_iter} iterations')

                self.y[step_idx + 1, :] = x_prev
                self.t[step_idx + 1] = t_macro_target

                lag_update_end = time.time()
                timings["lag_update_time"] += lag_update_end - lag_update_start
                converged = True
                completed_samples = step_idx + 2

            # pr.disable()
            # pr.dump_stats("profile_ieee14_simulation_1_second_rms_events.pstat")

        finally:
            if has_fmu_cs:
                self.problem.close_fmu_cs_devices()
            if has_fmu_me:
                self.problem.close_fmu_me_devices()

        return (self.t[:completed_samples],
                self.y[:completed_samples, :],
                well_initialized, converged)
