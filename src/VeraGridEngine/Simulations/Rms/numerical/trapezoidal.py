# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import time
import scipy.sparse as sp
from scipy.sparse import csc_matrix

from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Utils.Sparse.csc import pack_4_by_4_scipy
from VeraGridEngine.basic_structures import Vec, Mat


class TrapezoidalImplicitIntegration:

    def __init__(self,
                 problem: RmsProblemDae,
                 t0: float,
                 t_end: float,
                 h: float,
                 max_iter: int,
                 tolerance: float = 1e-7,
                 dx0_init: Vec | None = None,
                 use_fd_jacobian: bool = True,
                 use_chain_rule_jacobian: bool = True):
        self.problem = problem
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

    def _rhs_implicit(self,
                      x: Vec,
                      dx: Vec,
                      xn: Vec,
                      h: float,
                      f_state_prev: Vec | None) -> tuple[Vec, Vec]:
        x_mid = 0.5 * (x + xn)
        f_algeb = self.problem.rhs_algebraic(x_mid, dx)

        if self.problem.get_states_number() > 0:
            f_state = self.problem.rhs_state(x_mid, dx)
            if f_state_prev is None:
                f_state_prev = f_state
            f_state_update = x[:self.problem.get_states_number()] - xn[:self.problem.get_states_number()] - 0.5 * h * (f_state + f_state_prev)
            return np.r_[f_state_update, f_algeb], x_mid

        return f_algeb, x_mid

    def _jacobian_implicit(self,
                           x_mid: Vec,
                           dx: Vec,
                           h: float) -> sp.csc_matrix:
        if self.problem.get_states_number() == 0:
            j22: sp.csc_matrix = self.problem.get_j22(x_mid, dx, h)
            return 0.5 * j22

        j11_val: csc_matrix = self.problem.get_j11(x_mid, dx, h)
        j12_val: csc_matrix = self.problem.get_j12(x_mid, dx, h)
        j21_val: csc_matrix = self.problem.get_j21(x_mid, dx, h)
        j22_val: csc_matrix = self.problem.get_j22(x_mid, dx, h)

        I = sp.eye(m=self.problem.get_states_number(), n=self.problem.get_states_number())
        j11: sp.csc_matrix = (I - 0.5 * h * j11_val).tocsc()
        j12: sp.csc_matrix = -0.5 * h * j12_val
        j21: sp.csc_matrix = 0.5 * j21_val
        j22: sp.csc_matrix = 0.5 * j22_val

        return pack_4_by_4_scipy(j11, j12, j21, j22)

    def _jacobian_fd(self,
                     x_new: Vec,
                     x_prev: Vec,
                     dx_last: Vec,
                     h_eff: float,
                     f_state_prev: Vec | None,
                     rhs_base: Vec) -> sp.csc_matrix:
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
                             x_mid: Vec) -> sp.csc_matrix:
        # Base Jacobian includes midpoint 0.5 factors for x-dependence only.
        J_base = self._jacobian_implicit(x_mid, dx, h_eff).toarray()

        rhs_base, _ = self._rhs_implicit(x_new, dx, x_prev, h_eff, f_state_prev)
        n_res = rhs_base.size
        n_dx = dx.size
        n_x = x_new.size

        # B = dR/ddx (finite differences)
        B = np.zeros((n_res, n_dx), dtype=float)
        eps = 1e-7
        for k in range(n_dx):
            dx_pert = dx.copy()
            step = eps * (1.0 + abs(float(dx[k])))
            dx_pert[k] += step
            rhs_pert, _ = self._rhs_implicit(x_new, dx_pert, x_prev, h_eff, f_state_prev)
            B[:, k] = (rhs_pert - rhs_base) / step

        # C = ddx/dx_new (finite differences)
        C = np.zeros((n_dx, n_x), dtype=float)
        for j in range(n_x):
            x_pert = x_new.copy()
            step = eps * (1.0 + abs(float(x_new[j])))
            x_pert[j] += step
            dx_pert = self.problem.get_dx(x_pert, x_prev, dx_last, h_eff)
            C[:, j] = (dx_pert - dx) / step

        J = J_base + (B @ C)
        return sp.csc_matrix(J)

    def simulate(self):
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

                    self.problem.update(t_curr, x_new, self.problem._variable_parameters_values)

                    if has_fmu_cs:
                        self.problem.advance_fmu_cs_devices(t=t_local_prev, x_snapshot=x_prev, h=h_eff)
                    if has_fmu_me:
                        self.problem.advance_fmu_me_devices(t=t_local_prev, x_snapshot=x_prev, h=h_eff)

                    n_iter = 0
                    substep_converged = False

                    dx_prev = dx_last.copy()

                    f_state_prev = None
                    if self.problem.get_states_number() > 0:
                        f_state_prev = self.problem.rhs_state(x_prev, dx_prev)

                    while not substep_converged and n_iter < self.max_iter_0:
                        dx = self.problem.get_dx(x_new, x_prev, dx_last, h_eff)

                        rhs, x_mid = self._rhs_implicit(x_new, dx, x_prev, h_eff, f_state_prev)
                        residual = np.linalg.norm(rhs, np.inf)
                        substep_converged = residual < self.tol

                        if step_idx == 0 and is_first_local_step and (not substep_converged):
                            well_initialized = False

                        if not substep_converged:
                            if self.use_fd_jacobian:
                                Jf = self._jacobian_fd(x_new, x_prev, dx_last, h_eff, f_state_prev, rhs)
                            elif self.use_chain_rule_jacobian:
                                Jf = self._jacobian_chain_rule(x_new, x_prev, dx, dx_last, h_eff, f_state_prev, x_mid)
                            else:
                                Jf = self._jacobian_implicit(x_mid, dx, h_eff)

                            delta = sp.linalg.spsolve(Jf, -rhs)
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
                        dx_last = dx.copy()
                        x_prev = x_new.copy()
                        t_local_prev = t_curr
                        is_first_local_step = False
                    else:
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
