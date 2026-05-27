# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import numpy as np
import scipy.linalg as la
from scipy import sparse

from VeraGridEngine.Simulations.Rms.problems.rms_problem_phasor import RmsProblemPhasor
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var, Const, BinOp, UnOp, get_expr_factors


class RmsProblemMultilinear(RmsProblemPhasor):
    """
    Phasor RMS problem with multilinear-oriented utilities.

    This class keeps the regular symbolic compilation from ``RmsProblemPhasor``
    and adds lightweight operating-point extraction and small-signal helpers
    inspired by ``PolynomialMatrixBuilder`` but without SciPy dependencies.
    """

    def _ensure_multilinear_index_cache(self) -> None:
        """Build and cache multilinear index maps reused across methods."""
        if hasattr(self, "_ml_uid_to_idx_full"):
            return

        all_vars_sa = list(self._state_vars) + list(self._algebraic_vars)
        all_basis_vars = all_vars_sa + list(self._diff_vars)
        n_state_alg = len(all_vars_sa)

        self._ml_all_vars_sa = all_vars_sa
        self._ml_all_basis_vars = all_basis_vars
        self._ml_idx_vars = [self._uid2idx_vars[v.uid] for v in all_vars_sa]
        self._ml_uid_to_basis_idx = {v.uid: i for i, v in enumerate(all_basis_vars)}

    def build_multilinear_matrices(self) -> tuple[sparse.csc_matrix, sparse.csr_matrix]:
        """
        Build (S, Phi) multilinear matrices from problem equations.

        S encodes monomial structure (variables x monomials),
        Phi encodes equation coefficients (equations x monomials).
        """
        self._ensure_multilinear_index_cache()
        all_eqs = list(self._state_eqs) + list(self._algebraic_eqs)
        all_vars = self._ml_all_basis_vars
        uid_to_idx = self._ml_uid_to_basis_idx

        subs_map: dict = {}
        for p, val in zip(self._variable_parameters, self._variable_parameters_values):
            subs_map[p] = Const(float(val))
        for p, val in zip(self._constant_parameters, self._constant_params):
            subs_map[p] = Const(float(val))
        all_eqs = [eq.subs(subs_map) for eq in all_eqs]

        param_by_uid: dict[int, float] = {}
        for p, val in zip(self._variable_parameters, self._variable_parameters_values):
            param_by_uid[p.uid] = float(val)
        for p, val in zip(self._constant_parameters, self._constant_params):
            param_by_uid[p.uid] = float(val)

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
        return S, Phi

    def _term_to_monomial(
        self,
        factors: list[Expr],
        base_gain: float,
        uid_to_idx: dict[int, int],
        param_by_uid: dict[int, float],
    ) -> tuple[tuple[tuple[int, float], ...] | None, float]:
        """Map a symbolic product term to sparse monomial tuple and gain."""
        gain = float(base_gain)
        sparse_weights: dict[int, float] = {}

        for f in factors:
            # Normalize division by scalar constants: (expr / c) -> expr, gain *= 1/c.
            if isinstance(f, BinOp) and f.op == "/":
                den = f.right.simplify()
                if isinstance(den, Const) and den.value is not None:
                    den_val = float(den.value)
                    if abs(den_val) <= 1e-15:
                        return None, gain
                    gain /= den_val
                    f = f.left.simplify()

            f_vars_all = f.get_vars()
            if len(f_vars_all) == 0:
                gain *= self._expr_to_float(f)
                continue

            subs_local: dict = {}
            state_vars: list[Var] = []
            for v in f_vars_all:
                if v.uid in uid_to_idx:
                    state_vars.append(v)
                elif v.uid in param_by_uid:
                    subs_local[v] = Const(param_by_uid[v.uid])
                else:
                    # Unknown symbol: cannot classify term safely.
                    return None, gain

            f_reduced = f.subs(subs_local).simplify()

            if len(state_vars) == 0:
                gain *= self._expr_to_float(f_reduced)
                continue

            if len(state_vars) != 1:
                return None, gain

            s = state_vars[0]
            idx = uid_to_idx.get(s.uid)
            if idx is None:
                return None, gain

            b_expr = f_reduced.diff(s).subs({s: Const(0)}).simplify()
            a_expr = f_reduced.subs({s: Const(0)}).simplify()
            b_val = self._expr_to_float(b_expr)
            a_val = self._expr_to_float(a_expr)
            scale = abs(a_val) + abs(b_val)
            if scale == 0.0:
                scale = 1.0

            sparse_weights[idx] = b_val / scale
            gain *= scale

        monom_tuple = tuple(sorted(sparse_weights.items()))
        return monom_tuple, gain

    def _collect_monomials(self, expr: Expr) -> list[Expr]:
        """
        Recursively expand into monomial terms.

        Returns a list of expressions where each element is a product-like term
        with no top-level additive structure remaining.
        """
        if isinstance(expr, BinOp):
            if expr.op == "+":
                return self._collect_monomials(expr.left) + self._collect_monomials(expr.right)

            if expr.op == "-":
                left_terms = self._collect_monomials(expr.left)
                right_terms = self._collect_monomials(expr.right)
                neg_right = [(Const(-1.0) * t).simplify() for t in right_terms]
                return left_terms + neg_right

            if expr.op == "*":
                left_terms = self._collect_monomials(expr.left)
                right_terms = self._collect_monomials(expr.right)
                out: list[Expr] = []
                for lt in left_terms:
                    for rt in right_terms:
                        out.append((lt * rt).simplify())
                return out

            if expr.op == "/":
                den = expr.right.simplify()
                if isinstance(den, Const) and den.value is not None:
                    den_val = float(den.value)
                    if abs(den_val) <= 1e-15:
                        return [expr]
                    num_terms = self._collect_monomials(expr.left)
                    scale = Const(1.0 / den_val)
                    return [(scale * t).simplify() for t in num_terms]
                return [expr]

            return [expr]

        if isinstance(expr, UnOp) and expr.op == "-":
            inner_terms = self._collect_monomials(expr.operand)
            return [(Const(-1.0) * t).simplify() for t in inner_terms]

        return [expr]

    @staticmethod
    def _expr_to_float(expr: Expr) -> float:
        """Evaluate expression expected to be scalar constant after substitutions."""
        simp = expr.simplify()
        if isinstance(simp, Const):
            if simp.value is None:
                raise ValueError("Encountered undefined Const while building multilinear matrices")
            return float(simp.value)
        if isinstance(simp, UnOp) and simp.op == "-" and isinstance(simp.operand, Const):
            if simp.operand.value is None:
                raise ValueError("Encountered undefined negated Const while building multilinear matrices")
            return float(-simp.operand.value)
        raise ValueError(f"Expected constant scalar expression, got: {simp}")

    def linearize_multilinear(self, x: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Linearize using multilinear matrices S/Phi and return (E, A, EABC).
        """
        self._ensure_multilinear_index_cache()
        S, Phi = self.build_multilinear_matrices()
        if x is None:
            x = self.get_x0()
        x_vec = np.asarray(x, dtype=float)
        n_state_alg = len(self._state_vars) + len(self._algebraic_vars)
        n_diff = len(self._diff_vars)

        if len(x_vec) != n_state_alg:
            raise ValueError(f"Expected x of size {n_state_alg}, got {len(x_vec)}")

        # Diff variables are evaluated at the operating point. For now, use zeros
        # (steady-state convention) in the multilinear evaluation vector.
        v = np.zeros(n_state_alg + n_diff, dtype=float)
        v[:n_state_alg] = x_vec

        F = self._compute_jacobian_sparse_from_S(S, v)
        EABC = (Phi @ F.T).toarray()

        all_vars = self._ml_all_vars_sa
        idx_vars = self._ml_idx_vars
        ordered_pairs = sorted(zip(idx_vars, all_vars), key=lambda t: t[0])
        idx_vars_ordered = [idx for idx, _ in ordered_pairs]
        vars_ordered = [v for _, v in ordered_pairs]

        n_eq = EABC.shape[0]
        cols_to_take = len(idx_vars_ordered)
        dim = max(n_eq, cols_to_take)

        A = EABC[:, idx_vars_ordered[:cols_to_take]].copy()
        if A.shape[0] != dim or A.shape[1] != dim:
            A_pad = np.zeros((dim, dim), dtype=float)
            A_pad[:A.shape[0], :A.shape[1]] = A
            A = A_pad

        # Build descriptor E with explicit projection matrix using the same
        # diff->base convention as get_E_matrix.
        P = np.zeros((EABC.shape[1], cols_to_take), dtype=float)
        uid_to_basis_idx = self._ml_uid_to_basis_idx
        for dvar in self._diff_vars:
            base_var = dvar.base_var
            if base_var is None:
                continue
            dest_col = self._uid2idx_vars.get(base_var.uid)
            if dest_col is None or dest_col >= cols_to_take:
                continue
            deriv_idx = uid_to_basis_idx.get(dvar.uid)
            if deriv_idx is None:
                continue
            P[deriv_idx, dest_col] += 1.0

        E = EABC @ P

        n_states = len(self._state_vars)
        E[:n_states, :n_states] -= np.eye(n_states, dtype=E.dtype)

        if E.shape[0] != dim or E.shape[1] != dim:
            E_pad = np.zeros((dim, dim), dtype=float)
            E_pad[:E.shape[0], :E.shape[1]] = E
            E = E_pad

        return E, A, EABC

    def get_E_matrix(self, x: np.ndarray, dx: np.ndarray):
        E, _, _ = self.linearize_multilinear(x=np.asarray(x, dtype=float))
        return E

    def get_static_state_matrix(self, x: np.ndarray, dx: np.ndarray):
        _, A, _ = self.linearize_multilinear(x=np.asarray(x, dtype=float))
        return A

    @staticmethod
    def _compute_jacobian_sparse_from_S(S: sparse.csc_matrix, v: np.ndarray) -> sparse.csc_matrix:
        """Sparse multilinear Jacobian equivalent to PolynomialMatrixBuilder logic."""
        n_vars, n_mon = S.shape
        data = S.data
        indices = S.indices
        indptr = S.indptr

        col_prod = np.ones(n_mon, dtype=float)
        for j in range(n_mon):
            start = indptr[j]
            end = indptr[j + 1]
            prod = 1.0
            for p in range(start, end):
                i = indices[p]
                s_ij = data[p]
                prod *= (s_ij * v[i] + (1.0 - abs(s_ij)))
            col_prod[j] = prod

        f_row: list[int] = []
        f_col: list[int] = []
        f_val: list[float] = []

        for j in range(n_mon):
            start = indptr[j]
            end = indptr[j + 1]
            if start == end:
                continue

            zero_hits = 0
            zero_pos = -1
            for p in range(start, end):
                i = indices[p]
                s_ij = data[p]
                x_ij = s_ij * v[i] + (1.0 - abs(s_ij))
                if abs(x_ij) <= 1e-12:
                    zero_hits += 1
                    zero_pos = p

            for p in range(start, end):
                i = indices[p]
                s_ij = data[p]
                x_ij = s_ij * v[i] + (1.0 - abs(s_ij))

                if abs(x_ij) > 1e-12:
                    val = s_ij * col_prod[j] / x_ij
                    f_row.append(i)
                    f_col.append(j)
                    f_val.append(val)
                elif zero_hits == 1 and p == zero_pos:
                    prod_other = 1.0
                    for q in range(start, end):
                        if q == p:
                            continue
                        iq = indices[q]
                        s_iq = data[q]
                        x_iq = s_iq * v[iq] + (1.0 - abs(s_iq))
                        prod_other *= x_iq
                    val = s_ij * prod_other
                    f_row.append(i)
                    f_col.append(j)
                    f_val.append(val)

        return sparse.csc_matrix((f_val, (f_row, f_col)), shape=(n_vars, n_mon))

    def compute_stability_multilinear(self,
                                      x: np.ndarray | None = None,
                                      tol: float = 1e-6,
                                      a_regularization: float = 1e-8,
                                      filter_infinite: bool = True,
                                      inf_threshold: float = 1e6) -> tuple[np.ndarray, bool, float]:
        """Compute stability using multilinear S/Phi linearization path."""
        E, A, _ = self.linearize_multilinear(x=x)
        if a_regularization > 0.0:
            A = A + a_regularization * np.eye(A.shape[0], dtype=A.dtype)
        eigvals, _ = la.eig(A, -E)

        if filter_infinite:
            mask = np.isfinite(eigvals) & (np.abs(eigvals) < inf_threshold)
            eigvals = eigvals[mask]

        if len(eigvals) == 0:
            return eigvals, False, float("nan")

        margin = float(np.max(np.real(eigvals)))
        stable = bool(margin < -tol)
        return eigvals, stable, margin

    def compute_eigenvalues_symbolic(self,
                                     x: np.ndarray | None = None,
                                     dx: np.ndarray | None = None,
                                     filter_infinite: bool = True,
                                     inf_threshold: float = 1e6) -> np.ndarray:
        """
        Compute descriptor eigenvalues from symbolic Jacobians.

        Solves ``A v = lambda E v`` directly (generalized eig), mirroring the
        descriptor workflow used by the polynomial builder and RMS SSS paths.
        """
        A, E = self.linearize_symbolic(x=x, dx=dx)
        eigenvalues, _ = la.eig(A, E)

        if not filter_infinite:
            return eigenvalues

        finite_mask = np.isfinite(eigenvalues) & (np.abs(eigenvalues) < inf_threshold)
        return eigenvalues[finite_mask]

    def compute_stability_symbolic(self,
                                   x: np.ndarray | None = None,
                                   dx: np.ndarray | None = None,
                                   tol: float = 1e-6) -> tuple[np.ndarray, bool, float]:
        """Return eigenvalues, stability flag, and rightmost real-part margin."""
        eigenvalues = self.compute_eigenvalues_symbolic(x=x, dx=dx, filter_infinite=True)
        if len(eigenvalues) == 0:
            return eigenvalues, False, float("nan")

        margin = float(np.max(np.real(eigenvalues)))
        stable = bool(margin < -tol)
        return eigenvalues, stable, margin
