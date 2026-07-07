# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import numpy as np
from scipy import sparse

from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.Rms.problems.rms_problem_multilinear import (
    RmsProblemMultilinear,
)
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Utils.Symbolic.symbolic import Const, get_expr_factors


class EmtProblemMultilinear(EmtProblemDae):
    """
    EMT DAE problem with multilinear-oriented utilities.

    This class keeps the regular EMT symbolic assembly from ``EmtProblemDae``
    and adds the same sparse multilinear matrix extraction helpers used by
    ``RmsProblemMultilinear``. The EMT-specific part is parameter substitution:
    EMT runtime and constant values are stored in ``_event_params_values`` and
    ``_constant_params_values``.
    """

    def _ensure_multilinear_index_cache(self) -> None:
        """Build and cache multilinear index maps reused across methods."""
        if hasattr(self, "_ml_uid_to_idx_full"):
            return

        all_vars_sa = list(self._state_vars) + list(self._algebraic_vars)
        all_basis_vars = all_vars_sa + list(self._diff_vars)

        self._ml_all_vars_sa = all_vars_sa
        self._ml_all_basis_vars = all_basis_vars
        self._ml_idx_vars = [self._uid2idx_vars[v.uid] for v in all_vars_sa]
        self._ml_uid_to_basis_idx = {v.uid: i for i, v in enumerate(all_basis_vars)}
        self._ml_uid_to_idx_full = dict(self._ml_uid_to_basis_idx)

    def build_multilinear_matrices(self) -> tuple[sparse.csc_matrix, sparse.csr_matrix]:
        """
        Build ``(S, Phi)`` multilinear matrices from the EMT problem equations.

        ``S`` encodes monomial structure as ``variables x monomials`` and
        ``Phi`` encodes equation coefficients as ``equations x monomials``.
        """
        self._ensure_multilinear_index_cache()
        all_eqs = list(self._state_eqs) + list(self._algebraic_eqs)
        all_vars = self._ml_all_basis_vars
        uid_to_idx = self._ml_uid_to_basis_idx

        param_by_uid: dict[int, float] = {}
        subs_map: dict = {}

        for p, val in zip(self._variable_parameters, self._event_params_values):
            value = float(val)
            param_by_uid[p.uid] = value
            subs_map[p] = Const(value)

        for p, val in zip(self._constant_parameters, self._constant_params_values):
            value = float(val)
            param_by_uid[p.uid] = value
            subs_map[p] = Const(value)

        all_eqs = [eq.subs(subs_map) for eq in all_eqs]

        s_cols: list[tuple[tuple[int, float], ...]] = []
        monom_to_idx: dict[tuple[tuple[int, float], ...], int] = {}
        phi_rows: list[dict[int, float]] = []

        for eq in all_eqs:
            eq_row: dict[int, float] = {}
            mono_terms = self._collect_monomials(eq.simplify())

            for mono in mono_terms:
                monom_tuple, gain = self._term_to_monomial(
                    factors=get_expr_factors(mono),
                    base_gain=1.0,
                    uid_to_idx=uid_to_idx,
                    param_by_uid=param_by_uid,
                )
                if monom_tuple is None:
                    continue

                col_idx = monom_to_idx.get(monom_tuple)
                if col_idx is None:
                    col_idx = len(s_cols)
                    monom_to_idx[monom_tuple] = col_idx
                    s_cols.append(monom_tuple)

                eq_row[col_idx] = eq_row.get(col_idx, 0.0) + gain

            phi_rows.append(eq_row)

        n_vars = len(all_vars)
        n_mon = len(s_cols)
        n_eq = len(all_eqs)

        s_row: list[int] = []
        s_col: list[int] = []
        s_val: list[float] = []
        for j, mon in enumerate(s_cols):
            for i, val in mon:
                s_row.append(i)
                s_col.append(j)
                s_val.append(val)

        p_row: list[int] = []
        p_col: list[int] = []
        p_val: list[float] = []
        for i, row in enumerate(phi_rows):
            for j, val in row.items():
                p_row.append(i)
                p_col.append(j)
                p_val.append(val)

        S = sparse.csc_matrix((s_val, (s_row, s_col)), shape=(n_vars, n_mon))
        Phi = sparse.csr_matrix((p_val, (p_row, p_col)), shape=(n_eq, n_mon))
        self.S = S
        self.Phi = Phi
        return S, Phi

    def linearize_matrices(self) -> tuple[sparse.csr_matrix, sparse.csc_matrix]:
        """Return ``(Phi, S)`` for callers that use the linearize-matrices API name."""
        S, Phi = self.build_multilinear_matrices()
        return Phi, S

    def get_floquet_jacobian_evaluator(self, default_jacobian_evaluator=None):
        """Return an EMT Floquet Jacobian evaluator backed by multilinear ``S/Phi``.

        The returned callable follows the compiled EMT Jacobian evaluator signature
        used by ``BlockEmtFloquetOperator`` and returns the discrete residual
        Jacobian for the current integration method.
        """
        self._ensure_multilinear_index_cache()
        S, Phi = self.build_multilinear_matrices()

        n_state_alg = len(self._state_vars) + len(self._algebraic_vars)
        n_states = len(self._state_vars)
        n_diff = len(self._diff_vars)
        uid_to_col = {var.uid: idx for idx, var in enumerate(self._ml_all_vars_sa)}

        p_row: list[int] = []
        p_col: list[int] = []
        p_val: list[float] = []
        for diff_idx, diff_var in enumerate(self._diff_vars):
            base_var = diff_var.base_var
            if base_var is None:
                continue
            col = uid_to_col.get(base_var.uid)
            if col is None:
                continue
            p_row.append(diff_idx)
            p_col.append(col)
            p_val.append(1.0)

        diff_to_state_alg = sparse.csc_matrix((p_val, (p_row, p_col)), shape=(n_diff, n_state_alg), dtype=float)

        def _alpha(h: float) -> float:
            method = self.options.integration_method
            if method == DynamicIntegrationMethod.DaeTrapezoidal:
                return 2.0 / h
            if method == DynamicIntegrationMethod.DaeBDF2:
                return 1.5 / h
            return 1.0 / h

        def _history_derivatives(d_history) -> np.ndarray:
            values = np.zeros(n_state_alg, dtype=float)
            if d_history is None:
                return values

            raw = np.asarray(d_history, dtype=float)
            if raw.size >= n_state_alg:
                values[:] = raw[:n_state_alg]
                return values

            for diff_idx, diff_var in enumerate(self._diff_vars):
                if diff_idx >= raw.size:
                    break
                base_var = diff_var.base_var
                if base_var is None:
                    continue
                col = uid_to_col.get(base_var.uid)
                if col is not None:
                    values[col] = raw[diff_idx]
            return values

        def _diff_values(states, history, d_history, h: float, history2):
            method = self.options.integration_method
            x = np.asarray(states, dtype=float)[:n_state_alg]
            x_prev = x if history is None else np.asarray(history, dtype=float)[:n_state_alg]
            if method == DynamicIntegrationMethod.DaeTrapezoidal:
                dx_prev = _history_derivatives(d_history)
                dx_full = (2.0 / h) * (x - x_prev) - dx_prev
            elif method == DynamicIntegrationMethod.DaeBDF2:
                x_prev2 = x_prev if history2 is None else np.asarray(history2, dtype=float)[:n_state_alg]
                dx_full = (1.5 * x - 2.0 * x_prev + 0.5 * x_prev2) / h
            else:
                dx_full = (x - x_prev) / h

            values = np.zeros(n_diff, dtype=float)
            for diff_idx, diff_var in enumerate(self._diff_vars):
                base_var = diff_var.base_var
                if base_var is None:
                    continue
                col = uid_to_col.get(base_var.uid)
                if col is not None:
                    values[diff_idx] = dx_full[col]
            return values

        def multilinear_jacobian(states, params=None, history=None, d_history=None, h=None, history2=None):
            step = float(self.options.time_step if h is None else h)
            state_alg = np.asarray(states, dtype=float)[:n_state_alg]
            basis = np.zeros(n_state_alg + n_diff, dtype=float)
            basis[:n_state_alg] = state_alg
            basis[n_state_alg:] = _diff_values(
                states=states,
                history=history,
                d_history=d_history,
                h=step,
                history2=history2,
            )

            dvarphi_dz = self._compute_jacobian_sparse_from_S(S, basis)
            residual_jac = (Phi @ dvarphi_dz.T).tocsc()
            alpha = _alpha(step)
            jac_state_alg = residual_jac[:, :n_state_alg]
            jac_diff = residual_jac[:, n_state_alg:]
            jac = (jac_state_alg + alpha * (jac_diff @ diff_to_state_alg)).tolil()
            if n_states > 0:
                jac[:n_states, :] = -jac[:n_states, :]
                for row in range(n_states):
                    jac[row, row] = jac[row, row] + alpha
            return jac.tocsc()

        return multilinear_jacobian

    def get_floquet_ak_stack(self, trajectory, h, jac_evaluator=None, static_params=None):
        """Force the existing LU-cached Floquet operator for multilinear EMT.

        The current explicit ``A_k`` stack shortcut is a one-step state-map path,
        while the LU operator already handles the trapezoidal/BDF history terms used
        by EMT simulations. Returning ``None`` keeps the driver polymorphic and routes
        it through ``get_floquet_jacobian_evaluator``.
        """
        return None

    _term_to_monomial = RmsProblemMultilinear._term_to_monomial
    _collect_monomials = RmsProblemMultilinear._collect_monomials
    _expr_to_float = staticmethod(RmsProblemMultilinear._expr_to_float)
    build_sparse_h_from_s_phi = RmsProblemMultilinear.build_sparse_h_from_s_phi
    fit_cptensor_from_s_phi = RmsProblemMultilinear.fit_cptensor_from_s_phi
    evaluate_residual_from_cptensor = RmsProblemMultilinear.evaluate_residual_from_cptensor
    exact_phi_from_s = RmsProblemMultilinear.exact_phi_from_s
    exact_residual_from_s_phi = RmsProblemMultilinear.exact_residual_from_s_phi
    linearize_multilinear = RmsProblemMultilinear.linearize_multilinear
    get_E_matrix = RmsProblemMultilinear.get_E_matrix
    get_static_state_matrix = RmsProblemMultilinear.get_static_state_matrix
    _compute_jacobian_sparse_from_S = staticmethod(RmsProblemMultilinear._compute_jacobian_sparse_from_S)


__all__ = [
    "EmtProblemMultilinear",
]
