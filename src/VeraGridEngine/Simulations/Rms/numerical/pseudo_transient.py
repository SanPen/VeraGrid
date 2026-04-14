# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import scipy.sparse as sp
import time
from scipy.sparse import csc_matrix
from scipy.sparse import linalg as spla
import matplotlib.pyplot as plt

from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Utils.Sparse.csc import pack_4_by_4_scipy
from VeraGridEngine.basic_structures import Vec, Mat
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate


class  PseudoTransient:

    def __init__(self,
                 problem: RmsProblemDae,
                 h: float,
                 dtau0: float,
                 dtau_max: float = 1e2,
                 dtau_min: float = 1e-5,
                 tol: float = 1e-6,
                 max_iter: int = 1000):
        """

        :param problem:
        """
        self.problem = problem
        self.h = h
        self.dtau0 = dtau0
        self.dtau_min = dtau_min
        self.dtau_max = dtau_max
        self.steps = 1000
        self.max_iter_0 = max_iter
        self.tol = tol
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
        """
        :param x: vector or variables' values
        :param dx: vector of diff values
        :param h: step
        :return:
        """

        """
                  state Var    algeb var
        state eq |I - h * J11 | - h* J12  |    | ∆ state var|    | ∆ state eq |
                 |            |           |    |            |    |            |
                 -------------------------- x  |------------|  = |------------|
        algeb eq |J21         | J22       |    | ∆ algeb var|    | ∆ algeb eq |
                 |            |           |    |            |    |            |
        """

        # returns only j22 if no states, returns J if states
        if self.problem.get_states_number() == 0:
            j22: sp.csc_matrix = self.problem.get_j22(x, dx, h)
            return j22

        j11_val: csc_matrix = self.problem.get_j11(x, dx, h)
        j12_val: csc_matrix = self.problem.get_j12(x, dx, h)
        j21_val: csc_matrix = self.problem.get_j21(x, dx, h)
        j22_val: csc_matrix = self.problem.get_j22(x, dx, h)

        I = sp.eye(m=self.problem.get_states_number(), n=self.problem.get_states_number())
        j11: sp.csc_matrix = (I - h * j11_val).tocsc()
        j12: sp.csc_matrix = - h * j12_val
        j21: sp.csc_matrix = j21_val
        j22: sp.csc_matrix = j22_val

        J = pack_4_by_4_scipy(j11, j12, j21, j22)

        return J

    def _jacobian_pseudo_transient(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """
        #We want to build an equivalent of the following Jacobian:
                J11 = delta^-1 * I + Jf
        """
        # Now we have J = -delta^-1 * I - Jf so we need to multiply J by -1.
        J = self._jacobian_implicit(x, dx, h)

        return J
    
    def _rhs_pseudo_transient(self, x: Vec, xn: Vec, dx: Vec, h: float) -> Vec:
        """
        Return 𝑑x/dt given the current *state* vector.
        :param x: get the right-hand-side give a state vector
        :param xn:
        :param h: simulation step
        :return [f_state_update, f_algeb]
        """
        f_algeb = self.problem.rhs_algebraic(x, 0*dx)
        if self.problem.get_states_number() > 0:
            f_state = self.problem.rhs_state(x, dx)
            f_state_update = (x[:self.problem.get_states_number()] - xn[:self.problem.get_states_number()]) / h - f_state
            return np.r_[f_state_update, f_algeb]

        else:
            return f_algeb

    def simulate(self, plot=True):
        x0 = np.empty(self.problem.get_all_vars_number())
        dtau = self.dtau0
        dtau_max = self.dtau_max
        dtau_min = self.dtau_min

        for i, var in enumerate(self.problem.get_algebraic_vars()):
            x0[i] = 1.0 + 0.5 * np.random.rand()

        x0 = np.random.rand(self.problem.get_algebraic_var_number())
        dx0 = np.zeros(self.problem.get_diff_var_number())
        y = np.empty((5, self.problem.get_all_vars_number()))
        step_idx = 0
        x_new = x0.copy()
        xn = x0.copy()
        tries = 0
        
        # Update variable parameters at t=0
        self.problem.update_variable_params(0.0)

        dx_error = 1
        residual = 10
        old_residual = 10

        # history containers
        dtau_hist = list()
        dx_error_hist = list()
        residual_hist = list()
        x_hist = list()
        dx_hist = list()

        while step_idx < self.max_iter_0:
            tries += 1
            solved = False
            if step_idx == 0:
                xlast = xn
                xn = x_new.copy()
            else: 
                xlast = xn
                xn = y[-1]

            # rhs = self.rhs_implicit(xnew_lags, xn_lags, params_current, 1, dtau)
            dx = self.problem.get_dx(xn, xlast, dx0, 1e-3)
            rhs = self._rhs_pseudo_transient(x_new, xlast, dx, dtau)
            if not np.all(np.isfinite(rhs)):
                raise ValueError("NaN or Inf in RHS")
            Jf = self._jacobian_pseudo_transient(x_new, dx, dtau)
            residual = np.linalg.norm(rhs)
            try:
                delta = spla.spsolve(Jf, -rhs)
            except Exception as e:
                raise RuntimeError(f"Linear solver failed at try {tries}: {e}")
            
            solved = np.all(np.isfinite(delta))
            if not solved:
                print("Using LSQR")
                delta, *_ = spla.lsqr(Jf, -rhs)
                solved = np.all(np.isfinite(delta))

            if not solved:  # or not np.all(np.isfinite(delta)):
                print(f'jacobian is {Jf.toarray()}')
                print(f'delta is {delta}')
                print(f'x_new is {x_new}')
                print(f'rhs is {rhs}')
                print(f'residual is {np.linalg.norm(rhs)} try is {tries} and step is {step_idx}')
                raise ValueError(
                    f"Newton step failed at try {tries} and step {step_idx}: delta has NaN/Inf values with dtau {dtau}")
            dx0 = dx
            x_new += delta
            print(f'delta is {delta}')

            if step_idx == 0 and tries % 10 == 1:
                i = np.argmax(rhs)

            newton_residual = np.linalg.norm(rhs, np.inf)

            if solved:
                step_idx += 1
                tries = 0
                y = np.roll(y, shift=-1, axis=0)
                alpha = 1.0
                if step_idx > 2:
                    y[-1] = alpha * x_new + (1 - alpha) * y[-1]
                else:
                    y[-1] = x_new
                x_new = y[-1]

                dx = self.problem.get_dx(xn, xlast, dx, dtau)
                dx_error = np.linalg.norm(dx)
                rhs = self._rhs_pseudo_transient(x_new, xn, dx, dtau)
                residual = np.linalg.norm(rhs)

                # save history
                dtau_hist.append(dtau)
                dx_error_hist.append(dx_error)
                residual_hist.append(residual)
                x_hist.append(x_new.copy())
                dx_hist.append(dx.copy())

                if residual < self.tol:
                    break

                print(f'Convergence achieved for dtau={dtau:.2e},residual={residual:.2e}, step {step_idx}')
                print(f'rhs is {rhs}')
                eps = 1e-14
                avg_residual = 0.8 * old_residual + 0.2 * residual
                ratio = (avg_residual + eps) / residual
                ratio = (old_residual + eps) / residual

                # Default scaling factor
                beta = ratio
                if beta > 1.0:
                    beta = 2
                elif beta < 1.0:
                    beta = 0.5

                print(f'Updating dtau: {dtau} * {beta}')
                if dtau > 0:
                    dtau = min(dtau_max, max(dtau_min, dtau * beta))
                else:
                    dtau = -min(dtau_max, max(dtau_min, -dtau * beta))
                print(f'Updated dtau: {dtau}')

                old_residual = residual

            elif tries > self.max_iter_0:
                print(f'delta is {delta}')
                print(f'failed with dtau = {dtau}')
                raise RuntimeError(f"Max tries reached at dtau={dtau:.2e}, residual={residual:.2e}")

        init_guess = {var: x_new[self.problem.uid2idx_vars[var.uid]] for var in self.problem.get_algebraic_vars()}

        if not plot:
            return x_new, init_guess
        # --- Plotting section ---
        fig, axs = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

        axs[0].semilogy(dx_error_hist, label="||dx||")
        axs[0].set_ylabel("dx error (log)")
        axs[0].legend()

        axs[1].semilogy(residual_hist, label="Residual norm")
        axs[1].set_ylabel("Residual (log)")
        axs[1].legend()

        axs[2].semilogy(dtau_hist, label="dtau")
        axs[2].set_ylabel("dtau")
        axs[2].set_xlabel("Step index")
        axs[2].legend()

        # --- Plot actual variables ---
        x_hist = np.array(x_hist)  # shape: (n_steps, n_vars)
        dx_hist = np.array(dx_hist)  # shape: (n_steps, n_vars)

        nvars = len(self.problem.get_algebraic_vars())
        vars_per_plot = 5
        nplots = (nvars + vars_per_plot - 1) // vars_per_plot

        fig, axs = plt.subplots(nplots, 1, figsize=(10, 2.5 * nplots), sharex=True)

        # if there's only one subplot, axs won't be a list
        if nplots == 1:
            axs = [axs]
        if x_hist.ndim == 1:
            # print('Pseudo Transient finished')
            return x_new, init_guess

        for i in range(nplots):
            start = i * vars_per_plot
            end = min((i + 1) * vars_per_plot, nvars)
            for var in self.problem.get_algebraic_vars()[start:end]:
                axs[i].plot(x_hist[:, self.problem.uid2idx_vars[var.uid]], label=var.name)
            axs[i].set_ylabel("Value")
            axs[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
        axs[-1].set_xlabel("Step index")


        # print('Pseudo Transient finished')

        return x_new, init_guess