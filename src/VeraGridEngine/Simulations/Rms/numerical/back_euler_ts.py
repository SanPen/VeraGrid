# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import scipy.sparse as sp
import time

from VeraGridEngine.Utils.Sparse.sparse_solve import SparseProviderLinearSolver, solve_sparse_system_once
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.basic_structures import Vec, Mat


class BackEulerImplicitTensygrid:
    """
    Backward Euler implicit integration using TensyGrid.
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
    )

    def __init__(self,
                 problem: RmsProblemDae,
                 t0: float,
                 t_end: float,
                 h: float,
                 max_iter: int, sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = None) -> None:
        """:param problem:

        :param sparse_solver_backend_provider: Optional resolved LU provider; inherit the problem binding when absent, then use the existing SuperLU default. Factors belong to this numerical phase.
        :return: None; initialize an independent numerical phase.
        """
        self.problem = problem
        self._sparse_solver_backend_provider: SparseLinearSolverBackendProvider | None = sparse_solver_backend_provider
        # A direct constructor inherits the problem's already-resolved selection.
        if self._sparse_solver_backend_provider is None and isinstance(problem, RmsProblemTemplate):
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

    def _rhs_implicit(self,
                      x: Vec,
                      dx: Vec,
                      xn: Vec,
                      h: float) -> Vec:
        """
        Return 𝑑x/dt given the current *state* vector.
        :param x: get the right-hand-side give a state vector
        :param dx:
        :param xn:
        :return f_state_update or f_algeb
        """
        f_algeb = self.problem.rhs_algebraic(x, dx)

        if self.problem.get_states_number() > 0:
            f_state = self.problem.rhs_state(x, dx)
            f_state_update = x[:self.problem.get_states_number()] - xn[:self.problem.get_states_number()] - h * f_state
            return np.r_[f_state_update, f_algeb]

        else:
            return f_algeb

    def _jacobian_implicit(self,
                           x: Vec,
                           dx: Vec,
                           h: float) -> sp.csc_matrix:
        """Return the problem's Backward Euler Newton matrix."""
        return self.problem.get_jacobian(x, dx, h)

    def simulate(self):
        """

        :return:
        """
        converged: bool = False
        well_initialized: bool  = True

        x0: Vec = self.problem.get_x0()

        # we assume steady state
        dx0: Vec = np.zeros(self.problem.get_diff_var_number(), dtype=float)

        # timing accumulators
        timings = {
            "jacobian_time": 0.0,
            "rhs_time": 0.0,
            "lag_update_time": 0.0,
            "linear_solver_time": 0.0,
            "initial_step_time": 0.0,
        }

        self.t[0] = self.t0
        self.y[0, :] = x0.copy()
        dx = dx0.copy()
        dx_last = dx0.copy()
        x_new = x0.copy()
        residual = 0.0

        for step_idx in range(self.steps):

            converged = False
            n_iter = 0
            current_time = self.t[step_idx]
            dx_last = dx 
            self.problem.update_variable_params_ts(x_new,t=current_time)

            xn = self.y[step_idx, :]
            tol = 1e-7

            while not converged and n_iter < self.max_iter_0:
                if step_idx == 0:
                    dx = dx0.copy()
                else:
                    dx = self.problem.get_dx(x_new, xn, dx_last, self.h)

                # ---------------- rhs calculation ----------------
                rhs_start = time.time()
                rhs = self._rhs_implicit(x_new, dx, xn, self.h)

                rhs_end = time.time()
                timings["rhs_time"] += rhs_end - rhs_start
                # -------------------------------------------------

                residual = np.linalg.norm(rhs, np.inf)
                converged = residual < tol
                Jf = self._jacobian_implicit(x_new, dx, self.h)

                ### print info ###
                if step_idx == 0:
                    Jf = self._jacobian_implicit(x_new, dx, self.h)
                    delta: Vec = solve_sparse_system_once(Jf, -rhs, self._sparse_solver_backend_provider, self._sparse_linear_solver)
                    if converged:
                        # print("System well initialized.")
                        # print(f"x is {x_new}")
                        pass
                    else:
                        well_initialized = False
                        print(f"System bad initialized. DAE resiudal is {residual}.")
                        print(f'rhs is {rhs}')
                        non_zero_indexes = np.where(np.abs(rhs) > 1e-7)[0]
                        all_eq = self.problem._state_eqs + self.problem._algebraic_eqs
                        print("eqs are")
                        for i in non_zero_indexes:
                            eq = all_eq[i]
                            print(f"eq {eq} with error {rhs[i]}")
                            print("")


                if not converged:

                    solved = False
                    linear_start = time.time()
                    delta: Vec = solve_sparse_system_once(Jf, -rhs, self._sparse_solver_backend_provider, self._sparse_linear_solver)
                    linear_end = time.time()
                    timings["linear_solver_time"] += linear_end - linear_start
                    solved = np.all(np.isfinite(delta))

                    if not solved:
                        delta, *_ = sp.linalg.lsqr(Jf, -rhs)
                        solved = np.all(np.isfinite(delta))
                        u, s, vh = np.linalg.svd(Jf.toarray() if sp.issparse(Jf) else Jf)
                        singular_dirs = np.where(s < tol)[0]
                        for i in singular_dirs:
                            v = vh.T[:, i]  # variable-space vector
                            abs_v = np.abs(v)
                            dominant_idx = np.argsort(abs_v, kind="stable")[::-1][:5]  # top 5 vars
                            print(f"\nSingular direction {i}, σ={s[i]:.3e}")
                            for j in dominant_idx:
                                if j < self.problem.get_algebraic_var_number():
                                    algeb_vars = self.problem.algebraic_vars
                                    var_name = algeb_vars[j].name
                                    print(f"  {var_name:20s} {v[j]:+.3e}")
                        print("Using LSQR")
                        print(f"residual is {residual} for timestep {step_idx}")

                    if not solved:
                        nan_indices = np.where(np.isnan(rhs))[0]
                        # nan_indices = np.where(np.abs(rhs) > 1e-2)[0]
                        nan_eqs = [self.problem._algebraic_eqs[i] for i in nan_indices]
                        print(f'Jf is {Jf}')
                        raise ValueError(
                            f"spsolve returned non-finite values (NaN or Inf).\n"
                            f"delta = {delta}\n"
                            f"rhs = {rhs}\n"
                            f"Jacobian shape = {Jf.shape}\n"
                            f"NaNs found at indices {nan_indices.tolist()} in equations:\n{nan_eqs}",
                        )

                    if not solved:
                        print("Failed to solve linear system even with regularization.")
                        break


                    x_new += delta
                    n_iter += 1

            if converged:

                lag_update_start = time.time()
                # print(f'converged is {converged} at step {step_idx} and iter {n_iter}')

                self.y[step_idx + 1, :] = x_new

                self.t[step_idx + 1] = self.t[step_idx] + self.h

                dx_last = dx.copy()
                lag_update_end = time.time()
                timings["lag_update_time"] += lag_update_end - lag_update_start

            else:
                print(f"Failed to converge at step {step_idx} and n_iter is {n_iter}")
                print(f'Residual is {residual}')
                break

        return self.t, self.y, well_initialized, converged
