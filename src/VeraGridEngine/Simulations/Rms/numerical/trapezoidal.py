# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import time
import scipy.sparse as sp
from numba import njit

from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Simulations.Rms.jacobian_assembler import JacobianAssembler
from VeraGridEngine.Utils.Sparse.sparse_solve import SparseProviderLinearSolver, solve_sparse_system_once
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.basic_structures import Vec, Mat


@njit(cache=True, fastmath=False, error_model="numpy")
def discretize_trapezoidal_residual(values: np.ndarray, previous: np.ndarray,
                                    previous_slope: np.ndarray, h: float,
                                    state_count: int, output: np.ndarray) -> None:
    """Replace raw endpoint state equations with trapezoidal residuals."""
    for row in range(state_count):
        output[row] = values[row] - previous[row] - 0.5 * h * (output[row] + previous_slope[row])


class TrapezoidalImplicitIntegration:
    """
    Trapezoidal implicit integration solver.
    """
    __slots__ = (
        "problem",
        "_sparse_solver_backend_provider",
        "_sparse_linear_solver",
        "t0",
        "h",
        "max_iter_0",
        "steps",
        "t",
        "y",
        "tol",
        "dx0_init",
        "use_fd_jacobian",
        "use_chain_rule_jacobian",
        "_jacobian_assembler",
        "_derivative_base_indices",
        "_derivative_orders",
    )

    def __init__(self,
                 problem: RmsProblemTemplate,
                 t0: float,
                 t_end: float,
                 h: float,
                 max_iter: int,
                 tolerance: float = 1e-7,
                 dx0_init: Vec | None = None,
                 use_fd_jacobian: bool = False,
                 use_chain_rule_jacobian: bool = True, sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = None) -> None:
        """:param problem:
        :param t0:
        :param t_end:
        :param h:
        :param max_iter:
        :param tolerance:
        :param dx0_init:
        :param use_fd_jacobian:
        :param use_chain_rule_jacobian:

        :param sparse_solver_backend_provider: Optional resolved LU provider; inherit the problem binding when absent, then use the existing SuperLU default. Factors belong to this numerical phase.
        :return: None; initialize an independent numerical phase.
        """
        self.problem = problem
        self._sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = sparse_solver_backend_provider
        # A direct constructor inherits the problem's already-resolved selection.
        if self._sparse_solver_backend_provider is None:
            self._sparse_solver_backend_provider = problem.get_sparse_solver_backend_provider()
        else:
            pass
        resolved_provider: SparseLinearSolverBackendProvider = (
            SuperLUSparseBackendProvider() if self._sparse_solver_backend_provider is None
            else self._sparse_solver_backend_provider)
        # Each temporal integrator owns its own factors; projections own another phase.
        self._sparse_linear_solver: SparseProviderLinearSolver = SparseProviderLinearSolver(resolved_provider)
        self.t0 = t0
        self.h = h
        self.max_iter_0 = max_iter
        self.steps = int(np.ceil((t_end - t0) / h))
        self.t: Vec = np.empty(self.steps + 1)
        self.y: Mat = np.empty((self.steps + 1, self.problem.get_all_vars_number()))
        self.tol = tolerance
        self.dx0_init = dx0_init
        self.use_fd_jacobian = use_fd_jacobian
        self.use_chain_rule_jacobian = use_chain_rule_jacobian
        self._jacobian_assembler = JacobianAssembler()
        self._derivative_base_indices = (problem.get_diff_var_base_indices()
                                         if problem.get_diff_var_number() else np.empty(0, dtype=np.intp))
        self._derivative_orders = (problem.get_diff_var_orders()
                                   if problem.get_diff_var_number() else np.empty(0, dtype=np.intp))

    def _rhs_implicit(self,
                      x: Vec,
                      dx: Vec,
                      xn: Vec,
                      h: float,
                      f_state_prev: Vec | None) -> tuple[Vec, Vec]:
        """Evaluate ``x - xn - h*(f(x) + f(xn))/2`` and ``g(x)``."""
        n_states = self.problem.get_states_number()
        if n_states and f_state_prev is None:
            raise ValueError("Trapezoidal integration requires the previous state derivative")
        residual = np.array(self.problem.evaluate_equations(x, dx), copy=True)
        previous_slope = f_state_prev if f_state_prev is not None else np.empty(0)
        discretize_trapezoidal_residual(x, xn, previous_slope, h, n_states, residual)
        return residual, x

    def _jacobian_implicit(self,
                           x_new: Vec,
                           dx: Vec,
                           h: float) -> sp.csc_matrix:
        """Assemble the endpoint Jacobian from raw equation blocks."""
        n_states = self.problem.get_states_number()
        assembler = self._jacobian_assembler
        if self.problem.get_diff_var_number():
            if not self.problem.supports_derivative_jacobian_partials():
                raise ValueError("Trapezoidal requires separate derivative-variable Jacobian blocks")
            bases = self._derivative_base_indices
            chain = sp.csc_matrix(
                (h ** (-self._derivative_orders.astype(float)),
                 (np.arange(bases.size), bases)),
                shape=(bases.size, self.problem.get_all_vars_number()))
            blocks = self.problem.evaluate_jacobian_partials(x_new, dx)
            return assembler.assemble_jacobian_trapezoidal_partials(n_states, h, *blocks, chain)
        blocks = self.problem.evaluate_jacobian_blocks(x_new, dx, h)
        if n_states == 0:
            return blocks[3]
        return assembler.assemble_jacobian_trapezoidal_blocks(n_states, h, *blocks)

    def _jacobian_fd(self,
                     x_new: Vec,
                     x_prev: Vec,
                     dx_last: Vec,
                     h_eff: float,
                     f_state_prev: Vec | None,
                     rhs_base: Vec) -> sp.csc_matrix:
        """

        :param x_new:
        :param x_prev:
        :param dx_last:
        :param h_eff:
        :param f_state_prev:
        :param rhs_base:
        :return:
        """
        n = x_new.size
        m = rhs_base.size
        J = np.zeros((m, n), dtype=float)
        base_eps = 1e-7

        for j in range(n):
            x_pert = x_new.copy()
            step = base_eps * (1.0 + abs(float(x_new[j])))
            x_pert[j] += step
            dx_pert = self.problem.get_dx(x_pert, x_prev, dx_last, h_eff)
            rhs_pert, _ = self._rhs_implicit(x_pert, dx_pert, x_prev, h_eff, f_state_prev)
            J[:, j] = (rhs_pert - rhs_base) / step

        return sp.csc_matrix(J)

    def _jacobian_chain_rule(self,
                             x_new: Vec,
                             x_prev: Vec,
                             dx: Vec,
                             dx_last: Vec,
                             h_eff: float,
                             f_state_prev: Vec | None,
                             x_eval: Vec) -> sp.csc_matrix:
        """Assemble the endpoint Jacobian with the method's derivative chain."""
        return self._jacobian_implicit(x_eval, dx, h_eff)

    def simulate(self):
        """

        :return:
        """
        converged: bool = False
        well_initialized: bool = True

        x0: Vec = self.problem.get_x0()
        if self.dx0_init is None:
            dx0: Vec = np.zeros(self.problem.get_diff_var_number(), dtype=float)
        else:
            dx0 = np.array(self.dx0_init, dtype=float, copy=True)

        self.t[0] = self.t0
        self.y[0, :] = x0.copy()
        dx = dx0.copy()
        dx_last = dx0.copy()
        residual = 0.0

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
            for step_idx in range(self.steps):
                self.problem.report_progress2(step_idx, self.steps)

                t_current_macro: float = self.t[step_idx]
                t_macro_target: float = t_current_macro + self.h

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
                        raise RuntimeError(f"Invalid local step size h_eff={h_eff} while integrating RMS macro step {step_idx}.")

                    try:
                        self.problem.update_variable_params(t=t_local_prev, x_snapshot=x_new)
                    except TypeError:
                        self.problem.update_variable_params(t_local_prev)

                    dx_prev = dx_last.copy()
                    f_state_prev = None
                    if self.problem.get_states_number() > 0:
                        f_state_prev = self.problem.rhs_state(x_prev, dx_prev).copy()

                    self.problem.update(t_curr, x_new, self.problem._variable_parameters_values)

                    if has_fmu_me:
                        self.problem.advance_fmu_me_devices(t=t_local_prev, x_snapshot=x_prev, h=h_eff)
                        state_event_retry_time: float | None = (
                            self.problem.prepare_fmu_me_state_event_retry()
                        )
                    else:
                        state_event_retry_time = None
                    if has_fmu_cs and state_event_retry_time is None:
                        self.problem.advance_fmu_cs_devices(t=t_local_prev, x_snapshot=x_prev, h=h_eff)
                    else:
                        pass

                    n_iter = 0
                    substep_converged = state_event_retry_time is not None

                    while not substep_converged and n_iter < self.max_iter_0:
                        dx = self.problem.get_dx(x_new, x_prev, dx_last, h_eff)

                        rhs, x_eval = self._rhs_implicit(x_new, dx, x_prev, h_eff, f_state_prev)
                        residual = np.linalg.norm(rhs, np.inf)
                        substep_converged = residual < self.tol

                        if step_idx == 0 and is_first_local_step and (not substep_converged):
                            well_initialized = False

                        if not substep_converged:
                            if (self.use_fd_jacobian or
                                    (self.problem.get_diff_var_number() and
                                     not self.problem.supports_derivative_jacobian_partials())):
                                Jf = self._jacobian_fd(x_new, x_prev, dx_last, h_eff, f_state_prev, rhs)
                            elif self.use_chain_rule_jacobian:
                                Jf = self._jacobian_chain_rule(x_new, x_prev, dx, dx_last, h_eff, f_state_prev, x_eval)
                            else:
                                Jf = self._jacobian_implicit(x_eval, dx, h_eff)

                            delta: Vec = solve_sparse_system_once(Jf, -rhs, self._sparse_solver_backend_provider, self._sparse_linear_solver)
                            solved = np.all(np.isfinite(delta))
                            if not solved:
                                delta, *_ = sp.linalg.lsqr(Jf, -rhs)
                                solved = np.all(np.isfinite(delta))
                            if not solved:
                                break

                            # Damped Newton line-search to improve robustness.
                            accepted = False
                            alpha = 1.0
                            base_res = residual
                            for _ in range(8):
                                x_trial = x_new + alpha * delta
                                dx_trial = self.problem.get_dx(x_trial, x_prev, dx_last, h_eff)

                                rhs_trial, _ = self._rhs_implicit(x_trial, dx_trial, x_prev, h_eff, f_state_prev)
                                trial_res = np.linalg.norm(rhs_trial, np.inf)
                                if np.isfinite(trial_res) and trial_res < base_res:
                                    x_new = x_trial
                                    accepted = True
                                    break
                                alpha *= 0.5

                            if not accepted:
                                break
                            n_iter += 1

                    if substep_converged:
                        if state_event_retry_time is None:
                            if has_fmu_me:
                                self.problem.resolve_fmu_me_devices(accepted=True)
                            else:
                                pass
                            dx_last = dx.copy()
                            x_prev = x_new.copy()
                            t_local_prev = t_curr
                            is_first_local_step = False
                        else:
                            x_new = x_prev.copy()
                    else:
                        if has_fmu_me:
                            self.problem.resolve_fmu_me_devices(accepted=False)
                        else:
                            pass
                        converged = False
                        break

                if not substep_converged:
                    break

                self.y[step_idx + 1, :] = x_prev
                self.t[step_idx + 1] = t_macro_target
                converged = True
        finally:
            if has_fmu_cs:
                self.problem.close_fmu_cs_devices()
            if has_fmu_me:
                self.problem.close_fmu_me_devices()

        return self.t, self.y, well_initialized, converged
