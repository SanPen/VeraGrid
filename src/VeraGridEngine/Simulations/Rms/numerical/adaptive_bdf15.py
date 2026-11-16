# SPDX-License-Identifier: MPL-2.0 AND BSD-3-Clause
# Portions translated from SUNDIALS IDA v7.9.0 (ida.c, ida_nls.c, ida_ls.c).
# Copyright (c) 2025-2026, Lawrence Livermore National Security,
# University of Maryland Baltimore County, and the SUNDIALS contributors.
# Copyright (c) 2013-2025, Lawrence Livermore National Security and
# Southern Methodist University.
# Copyright (c) 2002-2013, Lawrence Livermore National Security.
# See SUNDIALS_LICENSE.txt in this directory for redistribution terms.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Variable-order BDF1--5 for the semi-explicit RMS DAE."""

from collections.abc import Callable
import warnings

import numpy as np
import scipy.sparse as sp
from numba import njit
from scipy.sparse.linalg import LinearOperator, gmres
from scipy import linalg
from scipy.optimize import brentq
from numpy.polynomial.polynomial import polymul, polyval, polyder

from VeraGridEngine.IO.fmu.profile import FmuMeEvaluationBudget
from VeraGridEngine.Simulations.Rms.jacobian_assembler import JacobianAssembler
from VeraGridEngine.Simulations.Rms.initialization_rms import project_initial_algebraic_state
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.Sparse.sparse_solve import SparseFactorizationManager
from VeraGridEngine.Utils.Sparse.sparse_solve import solve_sparse_system_once


@njit(cache=True)
def evaluate_bdf_derivatives(y_trial: np.ndarray, a0: float,
                             history_term: np.ndarray,
                             yp_out: np.ndarray) -> None:
    """Calculate the BDF derivative vector for a Newton trial."""
    yp_out[:] = a0 * y_trial + history_term


@njit(cache=True, fastmath=False, error_model="numpy")
def discretize_bdf_residual(derivatives: np.ndarray, state_count: int,
                            output: np.ndarray) -> None:
    """Replace raw state equations with BDF derivative minus state RHS."""
    for row in range(state_count):
        output[row] = derivatives[row] - output[row]


@njit(cache=True)
def predict(phi, gamma, order):
    y = phi[0].copy()
    yp = np.zeros_like(y)
    for j in range(1, order + 1):
        y += phi[j]
        yp += gamma[j] * phi[j]
    return y, yp


@njit(cache=True)
def update_history(phi, correction, order, maximum_order):
    if order < maximum_order:
        phi[order + 1] = correction
    phi[order] += correction
    for j in range(order - 1, -1, -1):
        phi[j] += phi[j + 1]


class AdaptiveBdf15Integration:
    """Self-contained variable-order BDF1--5 RMS solver.

    This class owns initialization, modified Newton iteration, fixed-leading-
    coefficient BDF history, timestep/order control, roots and dense output.
    Model Exchange states share the network solve. Co-Simulation and procedural
    rollback still require separate support.
    """

    def __init__(self, problem, t0: float, t_end: float, h: float, max_iter: int,
                 tolerance: float = 1e-6,
                 absolute_tolerance: float = 1e-6,
                 relative_tolerance: float = 1e-3,
                 cancel_checker: Callable[[], bool] | None = None, *,
                 initial_step: float | None = None, minimum_step: float = 0.0,
                 maximum_step: float | None = None,
                 maximum_order: int = 5, maximum_steps: int = 100000,
                 maximum_failures: int = 10, suppress_algebraic: bool = False,
                 weight_function: Callable | None = None, constraints: np.ndarray | None = None,
                 roots: Callable | None = None, root_directions=None, root_terminal=None,
                 root_time_tolerance: float = 1e-10, maximum_root_iterations: int = 100,
                 linear_solver: str = "sparse", jacobian_vector_product: Callable | None = None,
                 preconditioner: Callable | None = None,
                 sparse_solver_backend_provider=None) -> None:
        if (not np.isfinite(h) or not np.isfinite(t0) or not np.isfinite(t_end)
                or h <= 0 or t_end < t0 or not isinstance(max_iter, (int, np.integer)) or max_iter < 1):
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
        self.network_count = problem.get_all_vars_number()
        self._fmu_adapters = list(problem._fmu_me_adapters)
        self._fmu_slices: list[slice] = []
        self._fmu_budget = None
        self._trial_time = t0
        self._differential_indices = np.arange(self.state_count)
        self.fmu_y = np.empty((self.steps + 1, 0))
        self.fmu_event_retries = 0
        self._forced_event_times = problem.get_forced_event_times()
        self._derivative_base_indices = np.empty(problem.get_diff_var_number(), dtype=np.intp)
        self._uses_derivative_partials = bool(
            problem.get_diff_var_number()
            and problem.supports_derivative_jacobian_partials())
        if problem.get_diff_var_number() and not self._uses_derivative_partials:
            equations = problem._state_eqs + problem._algebraic_eqs
            derivatives = {v.uid for v in problem._diff_vars}
            if not equations or not derivatives or any(
                    v.uid in derivatives for equation in equations for v in equation.get_vars()):
                raise ValueError("Adaptive BDF requires semi-explicit equations without derivative symbols on the RHS")
        if self._uses_derivative_partials:
            if np.any(problem.get_diff_var_orders() != 1):
                raise ValueError("Adaptive BDF supports first-order derivative variables only")
            self._derivative_base_indices[:] = problem.get_diff_var_base_indices()
            self._differential_indices = np.unique(np.r_[self._differential_indices,
                                                          self._derivative_base_indices])
            if self._fmu_adapters:
                raise NotImplementedError("Adaptive BDF does not support FMU coupling with vectorized derivative variables")
        if self._uses_derivative_partials:
            positions = np.arange(problem.get_diff_var_number())
            self._derivative_to_variable = sp.csc_matrix(
                (np.ones(positions.size), (positions, self._derivative_base_indices)),
                shape=(positions.size, self.network_count))
        else:
            self._derivative_to_variable = None
        self._yp_work = np.empty(problem.get_all_vars_number(), dtype=float)
        self._dx_work = np.zeros(problem.get_diff_var_number(), dtype=float)
        self._jacobian_assembler = JacobianAssembler()
        self.jacobian_refreshes = 0
        self.jacobian_reuses = 0
        # Compile the two kernels before timing or entering the adaptive loop.
        zero = np.zeros(problem.get_all_vars_number(), dtype=float)
        evaluate_bdf_derivatives(zero, 0.0, zero, self._yp_work)
        if problem.get_diff_var_number() == 0:
            discretize_bdf_residual(self._yp_work, self.state_count, zero.copy())
        self.accepted_steps = 0
        self.rejected_steps = 0

        self.order_counts = np.zeros(5, dtype=int)
        self.last_order = 1
        self.last_failure = None
        if (not np.isfinite(h) or not np.isfinite(t0) or not np.isfinite(t_end)
                or not np.isfinite(minimum_step) or minimum_step < 0 or minimum_step > h
                or any(not isinstance(value, (int, np.integer)) for value in
                       (maximum_order, maximum_steps, maximum_failures, maximum_root_iterations))
                or not 1 <= maximum_order <= 5 or maximum_steps < 1 or maximum_failures < 1):
            raise ValueError("Invalid BDF step, order or work limits")
        if initial_step is not None and (not np.isfinite(initial_step) or initial_step <= 0):
            raise ValueError("Initial step must be finite and positive")
        if linear_solver not in ("sparse", "dense", "gmres"):
            raise ValueError("Linear solver must be sparse, dense or gmres")
        if (not np.isfinite(relative_tolerance) or relative_tolerance < 0
                or not np.all(np.isfinite(absolute_tolerance)) or np.any(np.asarray(absolute_tolerance) < 0)):
            raise ValueError("BDF tolerances must be finite and nonnegative")
        if not np.isfinite(root_time_tolerance) or root_time_tolerance <= 0 or maximum_root_iterations < 1:
            raise ValueError("Invalid root localization limits")
        self.initial_step, self.min_step = initial_step, minimum_step
        self.max_order, self.maximum_steps, self.max_failures = maximum_order, maximum_steps, maximum_failures
        self.max_step = min(h, h if maximum_step is None else maximum_step)
        if not np.isfinite(self.max_step) or self.max_step <= 0 or minimum_step > self.max_step:
            raise ValueError("Invalid maximum BDF step")
        if initial_step is not None and initial_step > self.max_step:
            raise ValueError("Initial step exceeds the maximum BDF step")
        self.max_newton_iterations = max_iter
        self.suppress_algebraic, self.weight_function = suppress_algebraic, weight_function
        self.constraints = None if constraints is None else np.asarray(constraints)
        self.roots, self.root_directions, self.root_terminal = roots, root_directions, root_terminal
        self.root_time_tolerance, self.maximum_root_iterations = root_time_tolerance, maximum_root_iterations
        self.root_values = None
        self.root_events = []
        self.terminal_time = None
        self.stop_reason = None
        self.linear_solver, self.jvp, self.preconditioner = linear_solver, jacobian_vector_product, preconditioner
        # A direct constructor inherits the problem's resolved LU selection; SuperLU otherwise.
        if sparse_solver_backend_provider is None:
            sparse_solver_backend_provider = problem.get_sparse_solver_backend_provider()
        else:
            pass
        if sparse_solver_backend_provider is None:
            sparse_solver_backend_provider = SuperLUSparseBackendProvider()
        else:
            pass
        self.sparse_solver_backend_provider: SparseLinearSolverBackendProvider = sparse_solver_backend_provider
        self._factor_manager: SparseFactorizationManager | None = None
        self.residual_evaluations = self.nonlinear_iterations = self.linear_iterations = 0
        self.error_failures = self.nonlinear_failures = self.constraint_failures = 0
        self.tolerance_scale_factor = 1.0
        self.last_error = 0.0

    def _residual(self, y: np.ndarray, alpha: float, beta: np.ndarray) -> np.ndarray:
        self.residual_evaluations += 1
        evaluate_bdf_derivatives(y, alpha, beta, self._yp_work)
        yp = self._yp_work
        dx = self._dx_work
        if self._uses_derivative_partials:
            dx[:] = yp[self._derivative_base_indices]
        residual = np.empty_like(y)
        network = y[:self.network_count]
        if self._fmu_adapters:
            for adapter, indices in zip(self._fmu_adapters, self._fmu_slices):
                derivatives, outputs = adapter.runtime_adapter.evaluate_external_point(
                    self._trial_time, y[indices], adapter._build_input_values(network),
                    self._fmu_budget,
                )
                adapter.apply_outputs(self.problem._variable_parameters_values, outputs)
                residual[indices] = yp[indices] - derivatives
        residual[:self.network_count] = self.problem.evaluate_equations(network, dx)
        if self.problem.get_diff_var_number() == 0:
            discretize_bdf_residual(yp, self.state_count, residual)
        else:
            residual[:self.state_count] = yp[:self.state_count] - residual[:self.state_count]
        return residual

    def _jacobian(self, y: np.ndarray, alpha: float) -> sp.csc_matrix:
        problem = self.problem
        dx = self._dx_work
        if self._fmu_adapters:
            # Include direct feedthrough and both network/FMU coupling blocks.
            # A numerical baseline is used until FMU directional derivatives are wired.
            zero = np.zeros_like(y)
            base = self._residual(y, 0.0, zero)
            columns = []
            for index in range(len(y)):
                trial = y.copy()
                delta = np.sqrt(np.finfo(float).eps) * max(1.0, abs(y[index]))
                trial[index] += delta
                columns.append((self._residual(trial, 0.0, zero) - base) / delta)
            self._residual(y, 0.0, zero)
            diagonal = np.zeros(len(y))
            diagonal[:self.state_count] = alpha
            diagonal[self.network_count:] = alpha
            return sp.csc_matrix(np.column_stack(columns)) + sp.diags(diagonal, format="csc")
        if self._uses_derivative_partials:
            j11, j12, j13, j21, j22, j23 = problem.evaluate_jacobian_partials(
                y[:self.network_count], dx, self._derivative_base_indices)
            return self._jacobian_assembler.assemble_jacobian_bdf_partials(
                self.state_count, alpha, j11, j12, j13, j21, j22, j23,
                self._derivative_to_variable)
        else:
            j11, j12, j21, j22 = problem.evaluate_jacobian_blocks(
                y[:self.network_count], dx, 1.0)
        if self.state_count == 0:
            return j22.tocsc()
        return self._jacobian_assembler.assemble_jacobian_bdf(
            self.state_count, alpha, j11, j12, j21, j22,
        )

    def _store_output(self, index: int, value: np.ndarray) -> None:
        self.y[index] = value[:self.network_count]
        self.fmu_y[index] = value[self.network_count:]

    def _begin_fmu_step(self, now: float, current: np.ndarray) -> None:
        if not self._fmu_adapters:
            return
        if self._fmu_budget is None:
            self._fmu_budget = FmuMeEvaluationBudget(
                self.problem.options.fmi_me_max_runtime_evaluations_per_step)
        for adapter, indices in zip(self._fmu_adapters, self._fmu_slices):
            adapter.runtime_adapter.prepare_external_candidate(
                now, now, current[indices],
                adapter._build_input_values(current[:self.network_count]), self._fmu_budget)

    def _stage_fmu_candidate(self, now: float, target: float,
                             candidate: np.ndarray) -> list[bool]:
        crossings = []
        for adapter, indices in zip(self._fmu_adapters, self._fmu_slices):
            runtime = adapter.runtime_adapter
            outputs = runtime.prepare_external_candidate(
                now, target, candidate[indices],
                adapter._build_input_values(candidate[:self.network_count]), self._fmu_budget)
            adapter.apply_outputs(self.problem._variable_parameters_values, outputs)
            crossings.append(bool(runtime._get_pending_state_event_crossing_indices()))
        return crossings

    def _resolve_fmu_step(self, accepted: bool, value: np.ndarray,
                          crossings: list[bool] | None = None,
                          complete_integrator_step: bool = True) -> bool:
        changed = False
        for index, (adapter, indices) in enumerate(zip(self._fmu_adapters, self._fmu_slices)):
            runtime = adapter.runtime_adapter
            before_derivatives = runtime.pending_candidate_derivative_values
            before_readings = runtime.pending_candidate_readable_values
            readings = runtime.resolve_pending_step(
                accepted, importer_detected_event=bool(crossings and crossings[index]),
                evaluation_budget=self._fmu_budget,
                complete_integrator_step=complete_integrator_step)
            if readings is not None:
                outputs = runtime.map_bound_output_values(readings)
                adapter.last_outputs = dict(outputs)
                adapter.apply_outputs(self.problem._variable_parameters_values, outputs)
            if accepted:
                changed |= readings != before_readings
                states = runtime.get_state_vector()
                changed |= not np.array_equal(value[indices], states)
                value[indices] = states
                after_derivatives = (runtime.fmi_three_coordinator.get_accepted_point()[6]
                                     if runtime.fmi_three_coordinator is not None else
                                     runtime.fmi_two_accepted_derivative_values)
                changed |= before_derivatives != after_derivatives
        return changed

    def _project_fmu_algebraic(self, value: np.ndarray) -> np.ndarray:
        """Project network algebraic coordinates with current FMU feedthrough."""
        algebraic = slice(self.state_count, self.network_count)
        zero = np.zeros_like(value)
        for _ in range(self.max_iter):
            residual = self._residual(value, 0.0, zero)[algebraic]
            if not len(residual) or np.max(np.abs(residual)) < self.tolerance:
                return value
            jacobian = self._jacobian(value, 0.0)[algebraic, algebraic]
            step: np.ndarray = solve_sparse_system_once(jacobian.tocsc(), residual, self.sparse_solver_backend_provider)
            if not np.all(np.isfinite(step)):
                raise RuntimeError("BDF FMU algebraic projection hit a singular Jacobian")
            else:
                pass
            value[algebraic] -= step
        raise RuntimeError("BDF FMU algebraic projection did not converge")

    def _synchronize_fmu_point(self, now: float, value: np.ndarray) -> np.ndarray:
        """Reproject feedthrough after initialization or an accepted discontinuity.

        No integrator-step notification is sent for these zero-time iterations.
        Input-induced FMU events may change states, requiring another projection.
        """
        self._trial_time = now
        for _ in range(self.max_iter):
            self._begin_fmu_step(now, value)
            value = self._project_fmu_algebraic(value)
            crossings = self._stage_fmu_candidate(now, now, value)
            changed = self._resolve_fmu_step(True, value, crossings,
                                             complete_integrator_step=False)
            if not changed:
                return value
        raise RuntimeError("BDF FMU input-event iteration did not converge")

    def simulate(self) -> tuple[np.ndarray, np.ndarray, bool, bool]:
        try:
            result = self._simulate()
        except BaseException:
            self._close_runtime()
            raise
        self._close_runtime()
        self.fmu_y = self.fmu_y[:len(result[0])].copy()
        return result

    def _close_runtime(self) -> None:
        if self._fmu_adapters:
            self.problem.close_fmu_me_devices()

    def _weights(self, y):
        if self.weight_function is None:
            scale = self._absolute_tolerances + self.relative_tolerance * np.abs(y)
            if np.any(scale <= 0):
                raise ValueError("Every component needs a positive error scale")
            weights = 1.0 / scale
        else:
            weights = np.asarray(self.weight_function(y), dtype=float)
        if weights.shape != y.shape or np.any(weights <= 0) or not np.all(np.isfinite(weights)):
            raise ValueError("Error weights must be finite positive values matching y")
        return weights

    def norm(self, vector, mask=False):
        scaled = vector * self.weights
        if mask and self.suppress_algebraic:
            scaled = scaled * self._differential_mask
        return float(np.sqrt(np.dot(scaled, scaled) / self._size))

    def _coefficients(self):
        k, h = self.order, self._step_size
        if h != self.used_h or k != self.used_order:
            self.ns = 0
        self.ns = min(self.ns + 1, self.used_order + 2)
        if k + 1 >= self.ns:
            self._beta[0] = self._alpha[0] = self._sigma[0] = 1.0
            self._gamma[0] = 0.0
            temp = h
            for i in range(1, k + 1):
                old = self._psi[i - 1]
                self._psi[i - 1] = temp
                self._beta[i] = self._beta[i - 1] * temp / old
                temp = old + h
                self._alpha[i] = h / temp
                self._sigma[i] = i * self._sigma[i - 1] * self._alpha[i]
                self._gamma[i] = self._gamma[i - 1] + self._alpha[i - 1] / h
            self._psi[k] = temp
        alphas = -sum(1.0 / i for i in range(1, k + 1))
        alpha0 = -sum(self._alpha[:k])
        old_cj = self.cj
        self.cj = -alphas / h
        if self.cj != old_cj:
            self.convergence_factor = 100.0
        ck = max(abs(self._alpha[k] + alphas - alpha0), self._alpha[k])
        self._phi[self.ns:k + 1] *= self._beta[self.ns:k + 1, None]
        return ck

    def _restore(self):
        for j in range(1, self.order + 1):
            self._psi[j - 1] = self._psi[j] - self._step_size
        self._phi[self.ns:self.order + 1] /= self._beta[self.ns:self.order + 1, None]

    def _test_error(self, correction, ck):
        k = self.order
        norm = self.norm(correction, mask=True)
        error = self._sigma[k] * norm
        lower_error = 0.0
        proposed = k
        if k > 1:
            delta = self._phi[k] + correction
            lower_error = self._sigma[k - 1] * self.norm(delta, mask=True)
            if k > 2:
                lower2 = self._sigma[k - 2] * self.norm(self._phi[k - 1] + delta, mask=True)
                if max(k * lower_error, (k - 1) * lower2) <= (k + 1) * error:
                    proposed = k - 1
            elif k * lower_error <= 0.5 * (k + 1) * error:
                proposed = k - 1
        return ck * norm, error, lower_error, proposed

    def _complete(self, correction, error, lower_error, proposed):
        k, h = self.order, self._step_size
        difference = k - self.used_order
        self.used_order, self.used_h = k, h
        self.segment_steps += 1
        self.accepted_steps += 1
        self.order_counts[k - 1] += 1
        if proposed == k - 1 or k == self.max_order:
            self.phase = 1
        if self.phase == 0:
            if self.segment_steps > 1:
                self.order += 1
                self._step_size = min(self.max_step, 2 * h)
        else:
            next_error = error
            if proposed == k - 1:
                self.order = k - 1
                next_error = lower_error
            elif k < self.max_order and k + 1 < self.ns and difference != 1:
                upper_error = self.norm(correction - self._phi[k + 1], mask=True) / (k + 2)
                if k == 1:
                    if (k + 2) * upper_error < 0.5 * (k + 1) * error:
                        self.order, next_error = k + 1, upper_error
                elif k * lower_error <= min((k + 1) * error, (k + 2) * upper_error):
                    self.order, next_error = k - 1, lower_error
                elif (k + 2) * upper_error < (k + 1) * error:
                    self.order, next_error = k + 1, upper_error
            ratio = (2 * next_error + 1e-4) ** (-1.0 / (self.order + 1))
            if ratio >= 2.0:
                self._step_size = min(self.max_step, 2.0 * h)
            elif ratio <= 1.0:
                self._step_size = max(self.min_step, h * max(0.5, min(0.9, ratio)))
        update_history(self._phi, correction, k, self.max_order)
        self.last_order = k

    def interpolate(self, time, derivative=0):
        """Return the accepted polynomial or its derivative within the last step."""
        fuzz = 100 * np.finfo(float).eps * (abs(self._time) + abs(self.used_h))
        if time < self._time - self.used_h - fuzz or time > self._time + fuzz:
            raise ValueError("Dense output is restricted to the last accepted step")
        k = max(1, self.used_order)
        if not 0 <= derivative <= k:
            raise ValueError("Requested derivative exceeds the interpolation order")
        # Product polynomial in delta; recurrence also provides derivatives up
        # to order k without finite differences or a second history structure.
        polynomial = np.array([1.0])
        result = np.zeros(self._size)
        for j in range(k + 1):
            result += polyval(time - self._time, polyder(polynomial, derivative)) * self._phi[j]
            if j < k:
                shift = 0.0 if j == 0 else self._psi[j - 1]
                polynomial = polymul(polynomial, np.array([shift, 1.0]) / self._psi[j])
        return result

    def prepare_initial_step(self, first_output):
        """IDA's automatic first step uses distance to the first requested output."""
        if self._automatic_initial_step and first_output > self._time:
            old_h = self._step_size
            self._step_size = max(self.min_step, min(self._step_size, 0.001 * (first_output - self._time)))
            self._phi[1] *= self._step_size / old_h
            self._psi[0] = self._step_size
            self.cj = 1.0 / self._step_size
            self._automatic_initial_step = False

    def _constraints_satisfied(self, value: np.ndarray) -> bool:
        if self.constraints is None:
            return True
        signed = value * np.sign(self.constraints)
        return bool(np.all(signed[np.abs(self.constraints) == 1] >= 0)
                    and np.all(signed[np.abs(self.constraints) == 2] > 0))

    def _evaluate_residual(self, time, value, derivative):
        self._trial_time = time
        residual = self._residual(value, 0.0, derivative)
        if residual.shape != value.shape:
            raise ValueError("Residual must match the combined state-vector shape")
        if not np.all(np.isfinite(residual)):
            raise FloatingPointError("Non-finite BDF residual")
        return residual

    def _factorize(self, matrix):
        if self.linear_solver == "dense":
            with warnings.catch_warnings():
                warnings.simplefilter("error", linalg.LinAlgWarning)
                return linalg.lu_factor(matrix.toarray())
        matrix = matrix.tocsc()
        if self._factor_manager is None:
            # Own the matrix: a problem may hand back the same template mutated in place on later refreshes.
            owned: sp.csc_matrix = matrix.copy()
            self._factor_manager = SparseFactorizationManager(owned, owned.data, self.sparse_solver_backend_provider)
            self._factor_manager.factorize()
        elif not self._factor_manager.update_matrix(matrix):
            # A value change is already refactorized by update_matrix; only a new pattern or lost factors remain.
            self._factor_manager.factorize()
        else:
            pass
        return self._factor_manager

    def _linear_solve(self, rhs):
        self.linear_iterations += 1
        if self.linear_solver == "dense":
            return linalg.lu_solve(self.factorization, rhs)
        try:
            return self._factor_manager.solve(rhs).copy()
        except RuntimeError:
            # Factors invalidated by an earlier non-finite solve: reject this correction like a failed solve.
            return np.full(rhs.shape, np.nan)

    def _newton(self, target, prediction, derivative):
        """Modified Newton with IDA's correction-rate test and cj rescaling."""
        reuse = (self.factorization is not None and self.cached_cj is not None
                 and .6 <= self.cj / self.cached_cj <= 5.0 / 3.0
                 and self.linear_solver != "gmres")
        for attempt in range(2 if reuse else 1):
            cached = reuse and attempt == 0
            if cached:
                self.jacobian_reuses += 1
            correction = np.zeros(self._size)
            first_norm = None
            for iteration in range(self.max_newton_iterations):
                value = prediction + correction
                slope = derivative + self.cj * correction
                try:
                    residual = self._evaluate_residual(target, value, slope)
                    if self.linear_solver == "gmres":
                        delta = self._krylov_correction(target, value, slope, residual)
                        if delta is None:
                            break
                    else:
                        if iteration == 0 and not cached:
                            matrix = self._jacobian(value, self.cj)
                            self.jacobian_refreshes += 1
                            try:
                                self.factorization = self._factorize(matrix)
                            except (RuntimeError, ValueError, linalg.LinAlgError, linalg.LinAlgWarning):
                                break
                            self.cached_cj = self.cj
                            self.convergence_factor = 20.0
                        delta = self._linear_solve(-residual)
                        delta *= 2.0 / (1.0 + self.cj / self.cached_cj)
                except (FloatingPointError, linalg.LinAlgError):
                    break
                if not np.all(np.isfinite(delta)):
                    break
                correction += delta
                self.nonlinear_iterations += 1
                norm = self.norm(delta)
                if iteration == 0:
                    first_norm = norm
                    if norm <= .33e-8:
                        return correction
                else:
                    rate = (norm / max(first_norm, np.finfo(float).tiny)) ** (1.0 / iteration)
                    if rate > .9:
                        break
                    self.convergence_factor = rate / (1.0 - rate)
                if self.convergence_factor * norm <= .33:
                    return correction
        return None

    def _krylov_correction(self, target, value, slope, residual):
        """Solve Newton's equation in weighted coordinates using GMRES."""
        def product(vector):
            physical = vector / self.weights
            if self.jvp is not None:
                result = self.jvp(target, value, slope, self.cj, physical)
            else:
                length = self.norm(physical)
                if length == 0:
                    return np.zeros_like(vector)
                epsilon = np.sqrt(np.finfo(float).eps) / length
                perturbed = self._evaluate_residual(target, value + epsilon * physical,
                                                    slope + self.cj * epsilon * physical)
                result = (perturbed - residual) / epsilon
            return result * self.weights

        matrix = LinearOperator((self._size, self._size), matvec=product)
        inverse = None
        if self.preconditioner is not None:
            supplied = self.preconditioner(target, value, slope, self.cj)
            inverse = LinearOperator((self._size, self._size),
                                     matvec=lambda vector: self.weights * (supplied @ (vector / self.weights)))
        def count_iteration(_residual):
            self.linear_iterations += 1

        delta, status = gmres(matrix, -residual * self.weights, M=inverse, rtol=0.,
                              atol=.05 * .33 * np.sqrt(self._size), maxiter=100,
                              callback=count_iteration, callback_type="pr_norm")
        return None if status else delta / self.weights

    def _initialize_history(self, time, value, first_output):
        """Start a divided-difference segment with a consistent DAE slope."""
        self._time, self._size = time, len(value)
        self._absolute_tolerances = np.broadcast_to(np.asarray(self.absolute_tolerance, dtype=float), value.shape).copy()
        self._differential_mask = np.zeros(self._size, dtype=bool)
        self._differential_mask[self._differential_indices] = True
        self.weights = self._weights(value)
        if self.constraints is not None:
            if self.constraints.shape != value.shape or not np.all(np.isin(self.constraints, [-2, -1, 0, 1, 2])):
                raise ValueError("Constraints must match the combined vector and contain 0, ±1 or ±2")
            if not self._constraints_satisfied(value):
                raise ValueError("Initial state violates the sign constraints")
        if self._fmu_adapters and self._fmu_budget is None:
            self._fmu_budget = FmuMeEvaluationBudget(self.problem.options.fmi_me_max_runtime_evaluations_per_step)
        slope = -self._evaluate_residual(time, value, np.zeros_like(value))
        slope[~self._differential_mask] = 0.
        default_step = min(self.max_step, .5 / max(self.norm(slope, mask=True), 1e-300))
        self._step_size = min(self.max_step, max(self.min_step, self.initial_step or default_step))
        self._automatic_initial_step = self.initial_step is None
        self._phi = np.zeros((6, self._size))
        self._phi[0], self._phi[1] = value, self._step_size * slope
        self._psi = np.zeros(6)
        self._psi[0] = self._step_size
        self._alpha, self._beta, self._sigma = np.ones(6), np.ones(6), np.ones(6)
        self._gamma = np.zeros(6)
        self.order, self.used_order, self.used_h = 1, 0, 0.
        self.ns = self.phase = self.segment_steps = 0
        self.cj = 1. / self._step_size
        self.cached_cj = self.factorization = None
        self.convergence_factor = 20.
        self.prepare_initial_step(first_output)
        predict(self._phi, self._gamma, 1)
        update_history(self._phi.copy(), np.zeros_like(value), 1, self.max_order)
        if self.roots is not None:
            self.root_values = self._root_values_at(time, value, slope)
            self.root_directions = np.broadcast_to(0 if self.root_directions is None else self.root_directions,
                                                   self.root_values.shape).copy()
            self.root_terminal = np.broadcast_to(False if self.root_terminal is None else self.root_terminal,
                                                 self.root_values.shape).copy()
            if not np.all(np.isin(self.root_directions, [-1, 0, 1])):
                raise ValueError("Root directions must be -1, 0 or 1")

    def _root_values_at(self, time, value, derivative):
        result = np.atleast_1d(np.asarray(self.roots(time, value, derivative), dtype=float))
        if result.ndim != 1 or not np.all(np.isfinite(result)):
            raise ValueError("Root callback must return a finite vector")
        if self.root_values is not None and result.shape != self.root_values.shape:
            raise ValueError("Root callback must preserve its vector shape")
        return result

    def _trial_polynomial(self, time, endpoint, phi, derivative=0):
        polynomial = np.array([1.])
        value = np.zeros(self._size)
        for index in range(self.order + 1):
            value += polyval(time - endpoint, polyder(polynomial, derivative)) * phi[index]
            if index < self.order:
                shift = 0. if index == 0 else self._psi[index - 1]
                polynomial = polymul(polynomial, np.array([shift, 1.]) / self._psi[index])
        return value

    def _locate_roots(self, endpoint, correction):
        if self.roots is None:
            return [], None
        phi = self._phi.copy()
        update_history(phi, correction, self.order, self.max_order)
        def values_at(time):
            return self._root_values_at(time, self._trial_polynomial(time, endpoint, phi),
                                       self._trial_polynomial(time, endpoint, phi, 1))
        new_values = values_at(endpoint)
        located = []
        for index, (left, right) in enumerate(zip(self.root_values, new_values)):
            direction = int(np.sign(right - left))
            if left != 0 and (right == 0 or np.signbit(left) != np.signbit(right)) and (
                    self.root_directions[index] == 0 or self.root_directions[index] == direction):
                root = brentq(lambda time: values_at(time)[index], self._time, endpoint,
                              xtol=self.root_time_tolerance, rtol=4*np.finfo(float).eps,
                              maxiter=self.maximum_root_iterations)
                located.append((root, index, direction))
        return sorted(located), new_values

    def _reject_step(self, kind, attempted_order, error, lower_error, proposed, counts):
        self._restore()
        self.phase = 1
        self.rejected_steps += 1
        counts[kind] += 1
        if kind == "error":
            self.error_failures += 1
            self.order = proposed if counts[kind] < 3 else 1
            chosen_error = lower_error if proposed < attempted_order else error
            ratio = (np.clip(.9 * (2*chosen_error + 1e-4) ** (-1. / (self.order + 1)), .25, .9)
                     if counts[kind] == 1 else .25)
        else:
            self.constraint_failures += int(kind == "constraint")
            self.nonlinear_failures += int(kind == "nonlinear")
            ratio = .25
        previous = self._step_size
        self.last_failure = (self._time, previous, self.order, kind)
        if counts[kind] >= self.max_failures or previous <= self.min_step:
            return False
        self._resize_step(max(self.min_step, previous * ratio))
        return True

    def _resize_step(self, step):
        if self.segment_steps == 0:
            self._phi[1] *= step / self._step_size
            self._psi[0] = step
        self._step_size = step

    def _failure_result(self, output_index, reason):
        self.stop_reason = reason
        if self.problem.logger is not None:
            self.problem.logger.add_error(reason, device="AdaptiveBdf15Integration")
        return self.t[:output_index].copy(), self.y[:output_index].copy(), True, False

    def _simulate(self) -> tuple[np.ndarray, np.ndarray, bool, bool]:
        problem = self.problem
        if problem._fmu_cs_adapters:
            raise NotImplementedError("Adaptive BDF Co-Simulation requires a communication/rollback strategy")
        if problem._manufacturer_native_runtime_session is not None:
            raise NotImplementedError("Adaptive BDF does not yet manage manufacturer native runtime models")
        current = problem.get_x0()
        problem.update_variable_params(self.t0, x_snapshot=current, scheduled_t=self.t0)
        problem.update(self.t0, current, problem._variable_parameters_values)
        current, initialized, residual = project_initial_algebraic_state(
            problem, current, problem.get_dx0(), self.tolerance, self.max_iter,
            sparse_solver_backend_provider=self.sparse_solver_backend_provider)
        self.t[0] = self.t0
        self._store_output(0, current)
        if not initialized:
            self.stop_reason = "Initial algebraic projection failed"
            return self.t[:1].copy(), self.y[:1].copy(), False, False
        if self._fmu_adapters:
            problem.initialize_fmu_me_devices(current, self.t0)
            states = [adapter.runtime_adapter.get_state_vector() for adapter in self._fmu_adapters]
            offset = self.network_count
            for state in states:
                self._fmu_slices.append(slice(offset, offset + len(state)))
                offset += len(state)
            current = np.concatenate([current, *states])
            self._differential_indices = np.r_[self._differential_indices, np.arange(self.network_count, offset)]
            self._yp_work = np.empty(offset)
            self.fmu_y = np.empty((self.steps + 1, offset - self.network_count))
            current = self._synchronize_fmu_point(self.t0, current)
            self._store_output(0, current)
        self._initialize_history(self.t0, current, min(self.t0 + self.h, self.t_end))
        self._fmu_budget = None
        output_index = 1
        failures = dict(error=0, nonlinear=0, constraint=0)
        root_boundary = None
        root_iterations = 0
        while self._time < self.t_end:
            if self.cancel_checker is not None and self.cancel_checker():
                self.stop_reason = "cancelled"
                return self.t[:output_index].copy(), self.y[:output_index].copy(), True, False
            if self.accepted_steps >= self.maximum_steps:
                return self._failure_result(output_index, "Maximum BDF step count exceeded")
            problem.report_progress2(output_index - 1, self.steps)
            forced = problem.get_next_forced_event_time(self._time, self.t_end)
            scheduled = next((time for time in self._forced_event_times if self._time < time <= self.t_end), None)
            if scheduled is not None:
                forced = scheduled if forced is None else min(forced, scheduled)
            boundary = self.t_end if forced is None else forced
            if root_boundary is not None:
                boundary = min(boundary, root_boundary)
            self._resize_step(min(self._step_size, boundary - self._time))
            if self._step_size < self.min_step or self._time + self._step_size == self._time:
                return self._failure_result(output_index, "BDF timestep is below the allowed or representable minimum")
            self.weights = self._weights(current)
            accuracy = np.finfo(float).eps * self.norm(current)
            if accuracy > 1.:
                self.tolerance_scale_factor = 2*accuracy
                return self._failure_result(output_index, "BDF tolerances are below floating-point resolution")
            now, step, attempted_order = self._time, self._step_size, self.order
            trial_time = min(now + step, boundary)
            at_event = forced is not None and trial_time == forced
            evaluation_time = np.nextafter(trial_time, now) if at_event else trial_time
            parameters = problem._variable_parameters_values.copy()
            self._begin_fmu_step(now, current)
            problem.update_variable_params(evaluation_time, x_snapshot=current[:self.network_count], scheduled_t=now)
            problem.update(evaluation_time, current[:self.network_count], problem._variable_parameters_values)
            ck = self._coefficients()
            prediction, derivative = predict(self._phi, self._gamma, self.order)
            correction = self._newton(evaluation_time, prediction, derivative)
            kind, error, lower_error, proposed = "nonlinear", np.inf, np.inf, self.order
            if correction is not None:
                candidate = prediction + correction
                if not self._constraints_satisfied(candidate):
                    kind = "constraint"
                else:
                    tested, error, lower_error, proposed = self._test_error(correction, ck)
                    kind = "accepted" if np.isfinite(tested) and tested <= 1. else "error"
            if kind != "accepted":
                self._resolve_fmu_step(False, current)
                problem._variable_parameters_values[:] = parameters
                if not self._reject_step(kind, attempted_order, error, lower_error, proposed, failures):
                    return self._failure_result(output_index, f"Too many BDF {kind} failures at t={now:g}")
                continue
            crossings = self._stage_fmu_candidate(now, trial_time, candidate)
            events, new_root_values = self._locate_roots(trial_time, correction)
            terminal_roots = [event[0] for event in events if self.root_terminal[event[1]]]
            terminal = min(terminal_roots, default=None)
            event_tolerance = (max(problem.options.fmi_state_event_time_tolerance,
                                   16*np.spacing(max(1., abs(trial_time)))) if self._fmu_adapters else 0.)
            shorten_fmu = any(crossings) and step > event_tolerance
            shorten_terminal = terminal is not None and trial_time - terminal > max(2*self.root_time_tolerance, 32*np.spacing(max(1., abs(trial_time))))
            if shorten_fmu or shorten_terminal:
                self._resolve_fmu_step(False, current)
                problem._variable_parameters_values[:] = parameters
                self._restore()
                root_iterations += 1
                limit = (problem.options.fmi_state_event_max_iterations if shorten_fmu
                         else self.maximum_root_iterations)
                if root_iterations > limit:
                    return self._failure_result(output_index, "BDF root localization did not converge")
                if shorten_fmu:
                    self.fmu_event_retries += 1
                root_boundary = (trial_time if shorten_fmu else
                                 max(terminal, now + max(self.root_time_tolerance,
                                                        16*np.spacing(max(1., abs(now))))))
                self._resize_step(step / 2 if shorten_fmu else root_boundary - now)
                self.factorization = self.cached_cj = None
                continue
            pre_event = candidate.copy()
            runtime_changed = self._resolve_fmu_step(True, candidate, crossings)
            at_event = at_event or any(crossings) or runtime_changed
            self._time = trial_time
            self.last_error = tested
            self._complete(correction, error, lower_error, proposed)
            # History still represents the pre-event polynomial for dense output.
            if at_event:
                # RMS scheduled samples belong to the left branch. Restart
                # history from the right branch after saving that sample.
                right_time = trial_time + 32*np.finfo(float).eps*max(1., abs(trial_time))
                problem.update_variable_params(right_time, x_snapshot=candidate[:self.network_count], scheduled_t=right_time)
                problem.update(right_time, candidate[:self.network_count], problem._variable_parameters_values)
                if self._fmu_adapters:
                    candidate = self._synchronize_fmu_point(trial_time, candidate)
                else:
                    candidate, projected, _ = project_initial_algebraic_state(
                        problem, candidate, problem.get_dx0(), self.tolerance, self.max_iter,
                        sparse_solver_backend_provider=self.sparse_solver_backend_provider)
                    if not projected:
                        return self._failure_result(output_index, "Post-event algebraic projection failed")
            current = candidate
            self.root_events.extend(events)
            self.root_values = new_root_values
            while output_index <= self.steps:
                output_time = min(self.t0 + output_index * self.h, self.t_end)
                if output_time > trial_time:
                    break
                self.t[output_index] = output_time
                at_scheduled_sample = scheduled is not None and output_time == scheduled
                output_value = (pre_event if at_scheduled_sample else current) if output_time == trial_time else self.interpolate(output_time)
                self._store_output(output_index, output_value)
                output_index += 1
            if terminal is not None:
                self.terminal_time = trial_time
                self.stop_reason = "terminal-root"
                if self.t[output_index - 1] != trial_time:
                    self.t[output_index] = trial_time
                    self._store_output(output_index, current)
                    output_index += 1
                self._fmu_budget = None
                return self.t[:output_index].copy(), self.y[:output_index].copy(), True, True
            if at_event:
                root_boundary, root_iterations = None, 0
                self._initialize_history(trial_time, current, min(trial_time + self.h, self.t_end))
            elif root_boundary is not None:
                gap = root_boundary - trial_time
                if gap <= 0:
                    root_boundary, root_iterations = None, 0
                else:
                    self._resize_step(min(self._step_size, gap if gap <= event_tolerance else gap/2))
            self._fmu_budget = None
            failures = dict(error=0, nonlinear=0, constraint=0)
        self.stop_reason = "end-time"
        return self.t[:output_index].copy(), self.y[:output_index].copy(), True, True
