# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""In-house adaptive BDF1/BDF2 integration of the scalar RMS DAE."""

from collections.abc import Callable
import warnings

import numpy as np
import scipy.sparse as sp
from numba import njit
from scipy.sparse.linalg import MatrixRankWarning

from VeraGridEngine.Simulations.Rms.jacobian_assembler import JacobianAssembler
from VeraGridEngine.Simulations.Rms.initialization_rms import project_initial_algebraic_state
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.Sparse.sparse_solve import SparseFactorizationManager


@njit(cache=True)
def prepare_bdf_history(y_previous: np.ndarray, y_older: np.ndarray,
                        a1: float, a2: float, out: np.ndarray) -> None:
    """Compute the step's constant derivative term once, outside Newton."""
    out[:] = a1 * y_previous + a2 * y_older


@njit(cache=True)
def evaluate_bdf_derivatives(y_trial: np.ndarray, a0: float,
                             history_term: np.ndarray,
                             yp_out: np.ndarray) -> None:
    """Calculate the BDF derivative vector for a Newton trial."""
    for i in range(len(y_trial)):
        yp_out[i] = a0 * y_trial[i] + history_term[i]


class AdaptiveBdf12Integration:
    """Use implicit BDF1/BDF2 steps with an embedded error comparison.

    ``h`` sets the saved output interval and maximum internal step. This is a
    small adaptive BDF implementation, not a port of the complete IDA solver.
    """

    def __init__(self, problem, t0: float, t_end: float, h: float, max_iter: int,
                 tolerance: float = 1e-6,
                 absolute_tolerance: float = 1e-6,
                 relative_tolerance: float = 1e-3,
                 cancel_checker: Callable[[], bool] | None = None,
                 sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = None) -> None:
        if h <= 0 or t_end < t0 or max_iter < 1:
            raise ValueError("Adaptive BDF requires positive step and iteration limits")
        self.problem = problem
        self.t0 = t0
        self.t_end = t_end
        self.h = h
        self.max_iter = max_iter
        self.tolerance = tolerance
        self.absolute_tolerance = absolute_tolerance
        self.relative_tolerance = relative_tolerance
        self.cancel_checker = cancel_checker
        self.steps = int(np.ceil((t_end - t0) / h))
        self.t = np.empty(self.steps + 1)
        self.y = np.empty((self.steps + 1, problem.get_all_vars_number()))
        self.state_count = problem.get_states_number()
        self._uses_derivative_partials = bool(problem.get_diff_var_number())
        if self._uses_derivative_partials:
            if (not problem.supports_derivative_jacobian_partials()
                    or np.any(problem.get_diff_var_orders() != 1)):
                raise ValueError("Adaptive BDF requires first-order independent derivative-variable partials")
            bases = problem.get_diff_var_base_indices()
            self._derivative_to_variable = sp.csc_matrix(
                (np.ones(bases.size), (np.arange(bases.size), bases)),
                shape=(bases.size, problem.get_all_vars_number()))
            self._derivative_base_indices = bases
        else:
            self._derivative_to_variable = None
            self._derivative_base_indices = np.empty(0, dtype=np.intp)
        self._yp_work = np.empty(problem.get_all_vars_number(), dtype=float)
        self._dx_empty = np.empty(problem.get_diff_var_number(), dtype=float)
        self._history_work = np.empty(problem.get_all_vars_number(), dtype=float)
        self._jacobian_assembler = JacobianAssembler()
        self._reuse_jacobian = problem.get_all_vars_number() >= 512
        self._cached_alpha = None
        self._cached_factorization = None
        # A direct constructor inherits the problem's resolved LU selection; SuperLU otherwise.
        if sparse_solver_backend_provider is None:
            sparse_solver_backend_provider = problem.get_sparse_solver_backend_provider()
        else:
            pass
        if sparse_solver_backend_provider is None:
            sparse_solver_backend_provider = SuperLUSparseBackendProvider()
        else:
            pass
        self._sparse_solver_backend_provider: SparseLinearSolverBackendProvider = sparse_solver_backend_provider
        self._factor_manager: SparseFactorizationManager | None = None
        self.jacobian_refreshes = 0
        self.jacobian_reuses = 0
        # Compile the two kernels before timing or entering the adaptive loop.
        zero = np.zeros(problem.get_all_vars_number(), dtype=float)
        prepare_bdf_history(zero, zero, 0.0, 0.0, self._history_work)
        evaluate_bdf_derivatives(zero, 0.0, self._history_work, self._yp_work)
        self.accepted_steps = 0
        self.rejected_steps = 0

    def _residual(self, y: np.ndarray, alpha: float, beta: np.ndarray) -> np.ndarray:
        evaluate_bdf_derivatives(y, alpha, beta, self._yp_work)
        yp = self._yp_work
        dx = self._dx_empty
        if self._uses_derivative_partials:
            dx[:] = yp[self._derivative_base_indices]
        residual = np.empty_like(y)
        equations = self.problem.evaluate_equations(y, dx)
        if self.state_count:
            residual[:self.state_count] = yp[:self.state_count] - equations[:self.state_count]
        residual[self.state_count:] = equations[self.state_count:]
        return residual

    def _jacobian(self, y: np.ndarray, alpha: float) -> sp.csc_matrix:
        problem = self.problem
        dx = self._dx_empty
        if self._uses_derivative_partials:
            j11, j12, j13, j21, j22, j23 = problem.evaluate_jacobian_partials(y, dx)
            return self._jacobian_assembler.assemble_jacobian_bdf_partials(
                self.state_count, alpha, j11, j12, j13, j21, j22, j23,
                self._derivative_to_variable)
        j11, j12, j21, j22 = problem.evaluate_jacobian_blocks(y, dx, 1.0)
        if self.state_count == 0:
            return j22.tocsc()
        return self._jacobian_assembler.assemble_jacobian_bdf(
            self.state_count, alpha, j11, j12, j21, j22,
        )

    def _residual_converged(self, residual: np.ndarray, alpha: float) -> bool:
        if not np.all(np.isfinite(residual)):
            return False
        differential_error = (np.max(np.abs(residual[:self.state_count])) / alpha
                              if self.state_count else 0.0)
        algebraic_error = (np.max(np.abs(residual[self.state_count:]))
                           if self.state_count < len(residual) else 0.0)
        return max(differential_error, algebraic_error) < self.tolerance

    def _factorize(self, jacobian: sp.csc_matrix) -> SparseFactorizationManager:
        """Factorize the Newton matrix once with the selected LU provider, keeping its analysis.

        :param jacobian: Current Newton matrix.
        :return: Factor owner holding factors of this matrix.
        """
        if self._factor_manager is None:
            # Own the matrix: a problem may hand back the same template mutated in place on later refreshes.
            owned: sp.csc_matrix = jacobian.copy()
            self._factor_manager = SparseFactorizationManager(owned, owned.data, self._sparse_solver_backend_provider)
            self._factor_manager.factorize()
        elif not self._factor_manager.update_matrix(jacobian):
            # A value change is already refactorized by update_matrix; only a new pattern or lost factors remain.
            self._factor_manager.factorize()
        else:
            pass
        return self._factor_manager

    def _solve(self, alpha: float, beta: np.ndarray,
               guess: np.ndarray) -> np.ndarray | None:
        ratio = alpha / self._cached_alpha if self._cached_alpha is not None else np.inf
        can_reuse = (self._reuse_jacobian and self._cached_factorization is not None
                     and self._factor_manager is not None and self._factor_manager.has_factorization()
                     and 0.6 <= ratio <= 5.0 / 3.0)
        for attempt in range(2 if can_reuse else 1):
            y = guess.copy()
            previous_correction_norm = None
            using_cached = can_reuse and attempt == 0
            for iteration in range(min(self.max_iter, 30)):
                residual = self._residual(y, alpha, beta)
                if not np.all(np.isfinite(residual)):
                    return None
                if iteration == 0:
                    # A small raw residual alone is unsafe for equations with
                    # tiny row scales. Only exact zero needs no correction.
                    if not np.any(residual):
                        return y
                    if using_cached:
                        self.jacobian_reuses += 1
                    else:
                        try:
                            self._cached_factorization = self._factorize(self._jacobian(y, alpha))
                        except (RuntimeError, ValueError):
                            return None
                        self._cached_alpha = alpha
                        self.jacobian_refreshes += 1
                with warnings.catch_warnings():
                    warnings.simplefilter("error", MatrixRankWarning)
                    try:
                        correction = self._factor_manager.solve(-residual).copy()
                    except (MatrixRankWarning, RuntimeError, ValueError):
                        return None
                if not np.all(np.isfinite(correction)):
                    return None
                scale = self.absolute_tolerance + self.relative_tolerance * np.maximum(
                    np.abs(y), np.abs(y + correction),
                )
                correction_norm = float(np.sqrt(np.mean((correction / scale) ** 2)))
                y += correction
                if correction_norm < 0.33e-4:
                    if not using_cached or self._residual_converged(self._residual(y, alpha, beta), alpha):
                        return y
                if previous_correction_norm is None:
                    convergence_factor = 20.0
                else:
                    rate = correction_norm / previous_correction_norm
                    if rate >= 0.9:
                        break
                    convergence_factor = max(1.0, rate / (1.0 - rate))
                if convergence_factor * correction_norm < 0.33:
                    if not using_cached or self._residual_converged(self._residual(y, alpha, beta), alpha):
                        return y
                previous_correction_norm = correction_norm
        return None

    def _error_norm(self, a: np.ndarray, b: np.ndarray) -> float:
        # Only differential coordinates control adaptive step selection;
        # algebraic coordinates are constrained by the nonlinear solve.
        if self.state_count == 0:
            return 0.0
        scale = self.absolute_tolerance + self.relative_tolerance * np.maximum(
            np.abs(a[:self.state_count]), np.abs(b[:self.state_count]),
        )
        return float(np.sqrt(np.mean(((a[:self.state_count] -
                                       b[:self.state_count]) / scale) ** 2)))

    def _bdf2_step(self, current: np.ndarray, previous: np.ndarray,
                   previous_h: float, step: float) -> np.ndarray | None:
        """Solve one variable-step BDF2 equation using the two accepted values."""
        ratio = step / previous_h
        alpha = (1.0 + 2.0 * ratio) / (step * (1.0 + ratio))
        prepare_bdf_history(current, previous, -(1.0 + ratio) / step,
                            ratio * ratio / (step * (1.0 + ratio)),
                            self._history_work)
        predictor = current + ratio * (current - previous)
        return self._solve(alpha, self._history_work, predictor)

    def _candidate(self, current: np.ndarray, previous: np.ndarray | None,
                   previous_h: float | None, step: float,
                   now: float, target_time: float) -> tuple[np.ndarray | None, float, int]:
        target_params = self.problem._variable_parameters_values.copy()
        if previous is not None and previous_h is not None and 0.5 <= step / previous_h <= 2.0:
            full = self._bdf2_step(current, previous, previous_h, step)
            if full is None:
                return None, np.inf, 2
            try:
                midpoint = now + step / 2.0
                self.problem.update_variable_params(midpoint, x_snapshot=current,
                                                    scheduled_t=now)
                self.problem.update(midpoint, current,
                                    self.problem._variable_parameters_values)
                middle = self._bdf2_step(current, previous, previous_h, step / 2.0)
            finally:
                self.problem._variable_parameters_values[:] = target_params
                self.problem.update(target_time, current,
                                    self.problem._variable_parameters_values)
            if middle is None:
                return None, np.inf, 2
            half = self._bdf2_step(middle, current, step / 2.0, step / 2.0)
            if half is None:
                return None, np.inf, 2
            # For a smooth cubic with exact incoming history, the full-step
            # BDF2 error is about 1.6--1.8 times this difference over the
            # supported step-ratio range. Two is a conservative estimate.
            return full, 2.0 * self._error_norm(full, half), 2

        prepare_bdf_history(current, current, -1.0 / step, 0.0, self._history_work)
        first = self._solve(1.0 / step, self._history_work, current)
        if first is None:
            return None, np.inf, 1
        try:
            midpoint = now + step / 2.0
            self.problem.update_variable_params(midpoint, x_snapshot=current,
                                                scheduled_t=now)
            self.problem.update(midpoint, current,
                                self.problem._variable_parameters_values)
            prepare_bdf_history(current, current, -2.0 / step, 0.0,
                                self._history_work)
            middle = self._solve(2.0 / step, self._history_work, current)
        finally:
            self.problem._variable_parameters_values[:] = target_params
            self.problem.update(target_time, current,
                                self.problem._variable_parameters_values)
        if middle is None:
            return None, np.inf, 1
        prepare_bdf_history(middle, middle, -2.0 / step, 0.0,
                            self._history_work)
        half = self._solve(2.0 / step, self._history_work, middle)
        if half is None:
            return None, np.inf, 1
        return half, self._error_norm(half, first), 1

    def simulate(self) -> tuple[np.ndarray, np.ndarray, bool, bool]:
        problem = self.problem
        if problem._fmu_cs_adapters or problem._fmu_me_adapters:
            raise NotImplementedError("Adaptive BDF does not yet manage RMS FMU devices")
        if problem._manufacturer_native_runtime_session is not None:
            raise NotImplementedError("Adaptive BDF does not yet manage manufacturer native runtime models")
        current = problem.get_x0()
        dx0 = problem.get_dx0()
        problem.update_variable_params(self.t0, x_snapshot=current, scheduled_t=self.t0)
        problem.update(self.t0, current, problem._variable_parameters_values)
        current, initialized, residual = project_initial_algebraic_state(
            problem=problem, initial_values=current, differential_values=dx0,
            tolerance=self.tolerance, max_iter=self.max_iter,
            sparse_solver_backend_provider=self._sparse_solver_backend_provider,
        )
        self.t[0] = self.t0
        self.y[0] = current
        if not initialized:
            problem.logger.add_error("RMS algebraic initial projection did not converge",
                                     device="AdaptiveBdf12Integration", value=residual)
            return self.t[:1].copy(), self.y[:1].copy(), False, False

        now = self.t0
        previous = None
        previous_h = None
        next_h = self.h
        for index in range(self.steps):
            if self.cancel_checker is not None and self.cancel_checker():
                return self.t[:index + 1].copy(), self.y[:index + 1].copy(), True, False
            problem.report_progress2(index, self.steps)
            output_time = self.t0 + (index + 1) * self.h
            while now < output_time - 1e-15:
                forced = problem.get_next_forced_event_time(now, output_time)
                boundary = output_time if forced is None else forced
                requested_h = next_h
                step = min(next_h, boundary - now)
                clipped_by_boundary = step < requested_h
                if step <= 0:
                    break
                trial_time = now + step
                at_event = forced is not None and abs(trial_time - forced) < 1e-12
                evaluation_time = np.nextafter(trial_time, now) if at_event else trial_time
                params_before = problem._variable_parameters_values.copy()
                problem.update_variable_params(evaluation_time, x_snapshot=current,
                                               scheduled_t=now)
                problem.update(evaluation_time, current, problem._variable_parameters_values)
                candidate, error, order = self._candidate(current, previous, previous_h,
                                                         step, now, evaluation_time)
                if candidate is None or not np.isfinite(error) or error > 1.0:
                    self.rejected_steps += 1
                    problem._variable_parameters_values[:] = params_before
                    next_h = step * max(0.1, min(0.5, 0.8 / max(error, 1e-12) ** (1.0 / (order + 1))))
                    if next_h < max(1e-12, self.h * 1e-9):
                        problem.logger.add_error("Adaptive BDF minimum internal step reached",
                                                 device="AdaptiveBdf12Integration")
                        return self.t[:index + 1].copy(), self.y[:index + 1].copy(), True, False
                    continue
                self.accepted_steps += 1
                previous, current = current, candidate
                previous_h = step
                now = trial_time
                if at_event:
                    previous = None
                    previous_h = None
                    self._cached_alpha = None
                    self._cached_factorization = None
                    problem.update_variable_params(now, x_snapshot=current,
                                                   scheduled_t=now)
                    problem.update(now, current, problem._variable_parameters_values)
                factor = 2.0 if error == 0.0 else min(2.0, max(0.5, 0.9 / error ** (1.0 / (order + 1))))
                next_h = min(self.h, step * factor)
                if clipped_by_boundary:
                    next_h = max(next_h, requested_h)
            self.t[index + 1] = output_time
            self.y[index + 1] = current
        return self.t.copy(), self.y.copy(), True, True
