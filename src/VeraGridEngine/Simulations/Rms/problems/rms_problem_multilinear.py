# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import scipy.linalg as la
from scipy import sparse
from VeraGridEngine.Simulations.Rms.problems.rms_problem_phasor import RmsProblemPhasor
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var, Const, BinOp, UnOp, get_expr_factors

try:
    from numba import njit
except ImportError:  # pragma: no cover - optional acceleration
    njit = None


if njit is not None:
    @njit(cache=True)
    def _compute_monomial_rank_products_numba(
        base_product: np.ndarray,
        ratio_matrix: np.ndarray,
        signs: np.ndarray,
        active_indptr: np.ndarray,
        active_indices: np.ndarray,
    ) -> np.ndarray:
        n_mon = signs.shape[0]
        rank = base_product.shape[0]
        out = np.empty((n_mon, rank), dtype=np.float64)

        for mon_idx in range(n_mon):
            for r in range(rank):
                out[mon_idx, r] = base_product[r]

            start = active_indptr[mon_idx]
            end = active_indptr[mon_idx + 1]
            for ptr in range(start, end):
                var_idx = active_indices[ptr]
                for r in range(rank):
                    out[mon_idx, r] *= ratio_matrix[var_idx, r]

            sign_val = signs[mon_idx]
            for r in range(rank):
                out[mon_idx, r] *= sign_val

        return out

@dataclass(slots=True)
class SparseCoefficientTensor:
    """
    Sparse coordinate representation of the coefficient tensor H.

    H has shape:

        (n_eq, 2, 2, ..., 2)

    The first mode is the equation index. Each following mode corresponds to
    the local basis [1, x_i] of one variable.
    """

    coords: np.ndarray
    values: np.ndarray
    shape: tuple[int, ...]

@dataclass(slots=True)
class CpnFitDiagnostics:
    """
    Diagnostics from the implicit CP/CPN ALS fitting process.
    """

    relative_changes: list[float]
    iterations: int
    converged: bool


@dataclass(slots=True)
class MultilinearCpTensor:
    """
    CP factor representation of a multilinear coefficient tensor.
    """

    weights: np.ndarray
    factors: list[np.ndarray]


class MultilinearCpnApproximator:
    """
    Implicit CP/CPN approximator for a sparse multilinear representation.

    The exact multilinear residual is assumed to be represented as:

        f(x) = Phi @ varphi(x)

    where:
        - S has shape (n_vars, n_mon)
        - Phi has shape (n_eq, n_mon)
        - each column of S defines one multilinear monomial

    The equivalent coefficient tensor H has shape:

        (n_eq, 2, 2, ..., 2)

    with one binary basis mode [1, x_i] per variable. This class fits a CP/CPN
    approximation of H without ever constructing H explicitly.

    The fitted CP tensor has factors:

        factors[0]     -> equation factor, shape (n_eq, rank)
        factors[i + 1] -> variable i factor, shape (2, rank)
    """

    def __init__(
        self,
        S: sparse.csc_matrix,
        Phi: sparse.csr_matrix,
    ) -> None:
        """
        Create the approximator from the exact sparse multilinear matrices.

        Parameters
        ----------
        S
            Monomial structure matrix with shape ``(n_vars, n_mon)``.
        Phi
            Equation-by-monomial coefficient matrix with shape ``(n_eq, n_mon)``.
        """
        if sparse.isspmatrix_csc(S):
            self.S = S
        else:
            self.S = S.tocsc()

        if sparse.isspmatrix_csr(Phi):
            self.Phi = Phi
        else:
            self.Phi = Phi.tocsr()

        self.n_vars, self.n_mon = self.S.shape
        self.n_eq, n_mon_phi = self.Phi.shape

        if self.n_mon != n_mon_phi:
            raise ValueError(
                f"S and Phi have incompatible monomial dimensions: "
                f"S has {self.n_mon}, Phi has {n_mon_phi}."
            )

        self._Phi_csc = self.Phi.tocsc()
        self._S_csr = self.S.tocsr()

        self.cp_tensor = None
        self.diagnostics: CpnFitDiagnostics | None = None

    def exact_phi_from_s(
        self,
        x: np.ndarray,
    ) -> np.ndarray:
        """
        Evaluate the exact monomial basis vector varphi(x) from S.

        Returns
        -------
        np.ndarray
            Monomial vector with shape ``(n_mon,)``.
        """
        if x.shape[0] != self.n_vars:
            raise ValueError(
                f"x has size {x.shape[0]}, but S has {self.n_vars} variables."
            )

        varphi = np.ones(self.n_mon, dtype=float)

        for mon_idx in range(self.n_mon):
            start = self.S.indptr[mon_idx]
            end = self.S.indptr[mon_idx + 1]

            value = 1.0

            for ptr in range(start, end):
                var_idx = int(self.S.indices[ptr])
                s_val = float(self.S.data[ptr])
                value *= s_val * x[var_idx] + (1.0 - abs(s_val))

            varphi[mon_idx] = value

        return varphi

    def exact_residual(
        self,
        x: np.ndarray,
    ) -> np.ndarray:
        """
        Evaluate the exact residual f(x) = Phi @ varphi(x).

        This is useful for validating the CPN approximation.
        """
        varphi = self.exact_phi_from_s(x=x)
        residual = self.Phi @ varphi
        return np.asarray(residual, dtype=float).reshape(-1)

    def _safe_divide_rank_vector(
        self,
        numerator: np.ndarray,
        denominator: np.ndarray,
        zero_tol: float,
    ) -> np.ndarray:
        """
        Divide two rank vectors with protection against near-zero denominators.
        """
        # Keep denominator sign while clipping magnitude away from zero.
        # This avoids boolean indexing and conditional branches in this hot path.
        safe_denominator = np.copysign(
            np.maximum(np.abs(denominator), zero_tol),
            denominator,
        )
        return numerator / safe_denominator

    def _solve_als_factor_update(
        self,
        mttkrp: np.ndarray,
        normal_matrix: np.ndarray,
        ridge: float,
    ) -> np.ndarray:
        """
        Solve one ALS normal-equation update.
        """
        rank = normal_matrix.shape[0]
        regularised_matrix = normal_matrix.copy()
        regularised_matrix[np.arange(rank), np.arange(rank)] += ridge

        return np.linalg.solve(
            regularised_matrix.T,
            mttkrp.T,
        ).T

    def _hadamard_gram_product(
        self,
        factors: list[np.ndarray],
    ) -> np.ndarray:
        """
        Compute Hadamard product of factor Gram matrices.
        """
        rank = factors[0].shape[1]
        result = np.ones((rank, rank), dtype=float)

        for factor in factors:
            result *= factor.T @ factor

        return result

    def _build_implicit_metadata(
        self,
        zero_tol: float,
    ) -> tuple[np.ndarray, list[np.ndarray], np.ndarray]:
        """
        Build metadata required by implicit CP-ALS.

        Returns
        -------
        tuple[np.ndarray, list[np.ndarray], np.ndarray]
            signs
                Monomial signs/gains with shape ``(n_mon,)``.
            active_monomials_by_var
                Monomial indices where each variable appears.
            active_variables_by_mon
                Active variable indices for each monomial.
        """
        signs = np.ones(self.n_mon, dtype=float)
        active_variables_by_mon: list[np.ndarray] = list()

        for mon_idx in range(self.n_mon):
            start = self.S.indptr[mon_idx]
            end = self.S.indptr[mon_idx + 1]

            active_vars: list[int] = list()
            monomial_gain = 1.0

            for ptr in range(start, end):
                var_idx = int(self.S.indices[ptr])
                s_val = float(self.S.data[ptr])

                if abs(s_val) > zero_tol:
                    active_vars.append(var_idx)
                    monomial_gain *= s_val

            signs[mon_idx] = monomial_gain
            active_variables_by_mon.append(np.asarray(active_vars, dtype=np.int64))

        active_monomials_by_var: list[np.ndarray] = list()

        for var_idx in range(self.n_vars):
            start = self._S_csr.indptr[var_idx]
            end = self._S_csr.indptr[var_idx + 1]
            active_monomials_by_var.append(
                self._S_csr.indices[start:end].astype(np.int64)
            )

        return (
            signs,
            active_monomials_by_var,
            np.asarray(active_variables_by_mon, dtype=object),
        )

    def _flatten_active_variables_by_mon(
        self,
        active_variables_by_mon: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        active_indptr = np.zeros(self.n_mon + 1, dtype=np.int64)
        total = 0
        for mon_idx in range(self.n_mon):
            total += len(active_variables_by_mon[mon_idx])
            active_indptr[mon_idx + 1] = total

        active_indices = np.empty(total, dtype=np.int64)
        cursor = 0
        for mon_idx in range(self.n_mon):
            arr = active_variables_by_mon[mon_idx]
            n = len(arr)
            if n > 0:
                active_indices[cursor:cursor + n] = arr
                cursor += n

        return active_indptr, active_indices

    def _compute_monomial_rank_products(
        self,
        variable_factors: list[np.ndarray],
        signs: np.ndarray,
        active_variables_by_mon: np.ndarray,
        active_indptr: np.ndarray | None,
        active_indices: np.ndarray | None,
        zero_tol: float,
    ) -> np.ndarray:
        """
        Compute monomial rank products without constructing H.

        For each monomial j and rank r:

            P[j, r] = sign_j * prod_i A_i[b_i(j), r]

        with b_i(j) = 1 when variable i appears in monomial j, otherwise 0.
        """
        rank = variable_factors[0].shape[1]
        base_product = np.ones(rank, dtype=float)
        ratio_matrix = np.empty((self.n_vars, rank), dtype=float)

        for var_idx, factor in enumerate(variable_factors):
            base_product *= factor[0, :]
            ratio_matrix[var_idx, :] = self._safe_divide_rank_vector(
                numerator=factor[1, :],
                denominator=factor[0, :],
                zero_tol=zero_tol,
            )

        if njit is not None and active_indptr is not None and active_indices is not None:
            return _compute_monomial_rank_products_numba(
                base_product=base_product,
                ratio_matrix=ratio_matrix,
                signs=signs,
                active_indptr=active_indptr,
                active_indices=active_indices,
            )

        rank_products = np.empty((self.n_mon, rank), dtype=float)

        for mon_idx in range(self.n_mon):
            product = base_product.copy()
            active_vars = active_variables_by_mon[mon_idx]

            for var_idx in active_vars:
                product *= ratio_matrix[int(var_idx), :]

            rank_products[mon_idx, :] = signs[mon_idx] * product

        return rank_products

    def _normalise_variable_factors_into_equation_factor(
        self,
        equation_factor: np.ndarray,
        variable_factors: list[np.ndarray],
        zero_tol: float,
    ) -> tuple[np.ndarray, list[np.ndarray]]:
        """
        Normalise variable-factor columns and absorb scale into equation factor.
        """
        scaled_equation_factor = equation_factor.copy()
        scaled_variable_factors: list[np.ndarray] = list()

        for factor in variable_factors:
            scaled_factor = factor.copy()
            column_norms = np.linalg.norm(scaled_factor, axis=0)
            safe_norms = column_norms.copy()
            small_mask = safe_norms <= zero_tol

            if np.any(small_mask):
                safe_norms[small_mask] = 1.0

            scaled_factor = scaled_factor / safe_norms[np.newaxis, :]
            scaled_equation_factor = scaled_equation_factor * safe_norms[np.newaxis, :]

            scaled_variable_factors.append(scaled_factor)

        return scaled_equation_factor, scaled_variable_factors

    def _finalise_as_cptensor(
        self,
        equation_factor: np.ndarray,
        variable_factors: list[np.ndarray],
        zero_tol: float,
    ) -> MultilinearCpTensor:
        """
        Convert raw factors into a normalized CP tensor representation.
        """
        factors = [equation_factor.copy()] + [factor.copy() for factor in variable_factors]
        rank = equation_factor.shape[1]
        weights = np.ones(rank, dtype=float)

        for factor_idx, factor in enumerate(factors):
            column_norms = np.linalg.norm(factor, axis=0)
            safe_norms = column_norms.copy()
            small_mask = safe_norms <= zero_tol

            if np.any(small_mask):
                safe_norms[small_mask] = 1.0

            factors[factor_idx] = factor / safe_norms[np.newaxis, :]
            weights *= safe_norms

        return MultilinearCpTensor(weights=weights, factors=factors)

    def fit(
        self,
        rank: int,
        max_iter: int = 30,
        tol: float = 1e-7,
        ridge: float = 1e-10,
        random_state: int = 0,
        zero_tol: float = 1e-12,
        verbose: bool = True,
    ):
        """
        Fit an implicit CP/CPN approximation of H.

        Returns
        -------
        MultilinearCpTensor
            Fitted CP tensor.
        """
        rng = np.random.default_rng(random_state)

        signs, active_monomials_by_var, active_variables_by_mon = (
            self._build_implicit_metadata(zero_tol=zero_tol)
        )
        active_indptr, active_indices = self._flatten_active_variables_by_mon(
            active_variables_by_mon=active_variables_by_mon,
        )

        equation_factor = rng.standard_normal((self.n_eq, rank))

        variable_factors: list[np.ndarray] = list()

        for _ in range(self.n_vars):
            factor = np.empty((2, rank), dtype=float)
            factor[0, :] = 1.0 + 0.01 * rng.standard_normal(rank)
            factor[1, :] = 0.10 * rng.standard_normal(rank)
            variable_factors.append(factor)

        equation_factor, variable_factors = (
            self._normalise_variable_factors_into_equation_factor(
                equation_factor=equation_factor,
                variable_factors=variable_factors,
                zero_tol=zero_tol,
            )
        )

        previous_equation_factor = equation_factor.copy()
        previous_variable_factors = [factor.copy() for factor in variable_factors]

        relative_changes: list[float] = list()
        converged = False

        for iteration in range(max_iter):
            monomial_rank_products = self._compute_monomial_rank_products(
                variable_factors=variable_factors,
                signs=signs,
                active_variables_by_mon=active_variables_by_mon,
                active_indptr=active_indptr,
                active_indices=active_indices,
                zero_tol=zero_tol,
            )

            mttkrp_equation = self.Phi @ monomial_rank_products
            normal_equation = self._hadamard_gram_product(variable_factors)

            equation_factor = self._solve_als_factor_update(
                mttkrp=mttkrp_equation,
                normal_matrix=normal_equation,
                ridge=ridge,
            )

            phi_transpose_times_equation = self.Phi.T @ equation_factor

            for var_idx in range(self.n_vars):
                monomial_rank_products = self._compute_monomial_rank_products(
                    variable_factors=variable_factors,
                    signs=signs,
                    active_variables_by_mon=active_variables_by_mon,
                    active_indptr=active_indptr,
                    active_indices=active_indices,
                    zero_tol=zero_tol,
                )

                weighted_products = (
                    phi_transpose_times_equation * monomial_rank_products
                )

                total_weighted_product = np.sum(weighted_products, axis=0)
                active_mon_indices = active_monomials_by_var[var_idx]

                if active_mon_indices.size > 0:
                    active_weighted_product = np.sum(
                        weighted_products[active_mon_indices, :],
                        axis=0,
                    )
                else:
                    active_weighted_product = np.zeros(rank, dtype=float)

                current_factor = variable_factors[var_idx]

                row_zero = self._safe_divide_rank_vector(
                    numerator=total_weighted_product - active_weighted_product,
                    denominator=current_factor[0, :],
                    zero_tol=zero_tol,
                )

                row_one = self._safe_divide_rank_vector(
                    numerator=active_weighted_product,
                    denominator=current_factor[1, :],
                    zero_tol=zero_tol,
                )

                mttkrp_variable = np.vstack((row_zero, row_one))

                other_factors: list[np.ndarray] = [equation_factor]

                for other_idx, other_factor in enumerate(variable_factors):
                    if other_idx != var_idx:
                        other_factors.append(other_factor)

                normal_variable = self._hadamard_gram_product(other_factors)

                variable_factors[var_idx] = self._solve_als_factor_update(
                    mttkrp=mttkrp_variable,
                    normal_matrix=normal_variable,
                    ridge=ridge,
                )


            equation_factor, variable_factors = (
                self._normalise_variable_factors_into_equation_factor(
                    equation_factor=equation_factor,
                    variable_factors=variable_factors,
                    zero_tol=zero_tol,
                )
            )

            equation_change = np.linalg.norm(equation_factor - previous_equation_factor)
            equation_norm = max(np.linalg.norm(previous_equation_factor), zero_tol)

            variable_change = 0.0
            variable_norm = 0.0

            for factor, previous_factor in zip(
                variable_factors,
                previous_variable_factors,
            ):
                variable_change += np.linalg.norm(factor - previous_factor)
                variable_norm += np.linalg.norm(previous_factor)

            relative_change = (
                equation_change + variable_change
            ) / max(equation_norm + variable_norm, zero_tol)

            relative_changes.append(float(relative_change))

            if verbose:
                print(
                    f"[implicit CPN ALS] iter={iteration + 1:03d}, "
                    f"relative_change={relative_change:.6e}"
                )

            if relative_change < tol:
                converged = True
                break

            previous_equation_factor = equation_factor.copy()
            previous_variable_factors = [factor.copy() for factor in variable_factors]

        self.cp_tensor = self._finalise_as_cptensor(
            equation_factor=equation_factor,
            variable_factors=variable_factors,
            zero_tol=zero_tol,
        )

        self.diagnostics = CpnFitDiagnostics(
            relative_changes=relative_changes,
            iterations=len(relative_changes),
            converged=converged,
        )

        return self.cp_tensor

    def evaluate_residual(
        self,
        x: np.ndarray,
        cp_tensor: MultilinearCpTensor | None = None,
    ) -> np.ndarray:
        """
        Evaluate the approximate residual from a fitted CP tensor.

        If ``cp_tensor`` is not provided, this method uses the last fitted tensor.
        """
        if cp_tensor is None:
            if self.cp_tensor is None:
                raise ValueError("No CP tensor provided and no fitted tensor is stored.")
            cp_tensor = self.cp_tensor

        weights = np.asarray(cp_tensor.weights, dtype=float)
        factors = [np.asarray(factor, dtype=float) for factor in cp_tensor.factors]

        equation_factor = factors[0]
        variable_factors = factors[1:]

        if x.shape[0] != len(variable_factors):
            raise ValueError(
                f"x has {x.shape[0]} variables, but CP tensor has "
                f"{len(variable_factors)} variable modes."
            )

        rank_product = np.ones(weights.shape[0], dtype=float)

        for var_idx, factor in enumerate(variable_factors):
            rank_product *= factor[0, :] + factor[1, :] * x[var_idx]

        residual = equation_factor @ (weights * rank_product)

        return np.asarray(residual, dtype=float).reshape(-1)

    def relative_residual_error(
        self,
        x: np.ndarray,
        cp_tensor=None,
        norm_floor: float = 1e-12,
    ) -> float:
        """
        Compare exact S/Phi residual against the CPN approximation.
        """
        exact = self.exact_residual(x=x)
        approx = self.evaluate_residual(x=x, cp_tensor=cp_tensor)

        return float(
            np.linalg.norm(exact - approx) / max(np.linalg.norm(exact), norm_floor)
        )
    
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
        self.S = S
        self.Phi = Phi
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
    
    def build_sparse_h_from_s_phi(
        self,
        zero_tol: float = 1e-12,
    ) -> SparseCoefficientTensor:
        """
        Build the exact sparse coordinate representation of the coefficient tensor H.

        The exact multilinear representation is:

            f(x) = Phi @ varphi(x)

        where:
            - S defines the monomial basis varphi(x)
            - Phi contains the equation-by-monomial coefficients

        The tensor H has shape:

            (n_eq, 2, 2, ..., 2)

        where:
            - mode 0 is the equation mode
            - mode i + 1 corresponds to the local basis [1, x_i]

        Returns
        -------
        SparseCoefficientTensor
            Sparse coordinate representation of H.
        """
        S = self.S
        Phi = self.Phi

        if not sparse.isspmatrix_csc(S):
            S = S.tocsc()

        if not sparse.isspmatrix_csr(Phi):
            Phi = Phi.tocsr()

        n_vars, n_mon_s = S.shape
        n_eq, n_mon_phi = Phi.shape

        if n_mon_s != n_mon_phi:
            raise ValueError(
                f"S and Phi have incompatible monomial dimensions: "
                f"S has {n_mon_s}, Phi has {n_mon_phi}."
            )

        Phi_csc = Phi.tocsc()

        coord_to_value: dict[tuple[int, ...], float] = dict()

        for mon_idx in range(n_mon_s):
            s_start = S.indptr[mon_idx]
            s_end = S.indptr[mon_idx + 1]

            binary_index = np.zeros(n_vars, dtype=np.int8)
            monomial_gain = 1.0

            for ptr in range(s_start, s_end):
                var_idx = int(S.indices[ptr])
                s_val = float(S.data[ptr])

                if abs(s_val) > zero_tol:
                    binary_index[var_idx] = 1
                    monomial_gain *= s_val
                else:
                    pass

            phi_start = Phi_csc.indptr[mon_idx]
            phi_end = Phi_csc.indptr[mon_idx + 1]

            for ptr in range(phi_start, phi_end):
                eq_idx = int(Phi_csc.indices[ptr])
                phi_val = float(Phi_csc.data[ptr])
                h_val = phi_val * monomial_gain

                if abs(h_val) > zero_tol:
                    coord = tuple([eq_idx] + binary_index.astype(int).tolist())
                    previous_value = coord_to_value.get(coord, 0.0)
                    coord_to_value[coord] = previous_value + h_val
                else:
                    pass

        coords: list[tuple[int, ...]] = list()
        values: list[float] = list()

        for coord, value in coord_to_value.items():
            if abs(value) > zero_tol:
                coords.append(coord)
                values.append(value)
            else:
                pass

        if len(coords) == 0:
            raise ValueError("The coefficient tensor H has no non-zero entries.")

        return SparseCoefficientTensor(
            coords=np.asarray(coords, dtype=np.int64),
            values=np.asarray(values, dtype=float),
            shape=tuple([n_eq] + [2 for _ in range(n_vars)]),
        )


    def fit_cptensor_from_s_phi(
        self,
        rank: int,
        max_iter: int = 30,
        tol: float = 1e-7,
        ridge: float = 1e-10,
        random_state: int = 0,
        zero_tol: float = 1e-12,
        verbose: bool = True,
    ):
        """
        Fit a CP/CPN approximation of the multilinear coefficient tensor H.

        This is a convenience wrapper around ``MultilinearCpnApproximator``. The
        fitting algorithm is implemented outside this class to keep
        ``RmsProblemMultilinear`` focused on the exact multilinear model.

        Returns
        -------
        MultilinearCpTensor
            Fitted CP tensor approximating the coefficient tensor H.
        """

        S, Phi = self.build_multilinear_matrices()

        approximator = MultilinearCpnApproximator(
            S=S,
            Phi=Phi,
        )

        cp_tensor = approximator.fit(
            rank=rank,
            max_iter=max_iter,
            tol=tol,
            ridge=ridge,
            random_state=random_state,
            zero_tol=zero_tol,
            verbose=verbose,
        )

        self._last_cpn_approximator = approximator
        self._last_cp_tensor = cp_tensor

        return cp_tensor

    def evaluate_residual_from_cptensor(
        self,
        x: np.ndarray,
        cp_tensor: MultilinearCpTensor,
    ) -> np.ndarray:
        """
        Evaluate the approximate residual from a CP tensor.

        This implements:

            q_r = prod_i (A_i[0, r] + A_i[1, r] * x_i)
            f   = B @ (weights * q)

        where:
            - B = factors[0]
            - A_i = factors[i + 1]

        Parameters
        ----------
        x
            Variable vector with shape ``(n_vars,)``.
        cp_tensor
            CP tensor representing the approximate coefficient tensor H.

        Returns
        -------
        np.ndarray
            Approximate residual vector with shape ``(n_eq,)``.
        """
        weights = np.asarray(cp_tensor.weights, dtype=float)
        factors = [np.asarray(factor, dtype=float) for factor in cp_tensor.factors]

        equation_factor = factors[0]
        variable_factors = factors[1:]

        n_vars = len(variable_factors)

        if x.shape[0] != n_vars:
            raise ValueError(
                f"x has {x.shape[0]} variables, but CP tensor has {n_vars} variable modes."
            )

        rank_product = np.ones(weights.shape[0], dtype=float)

        for var_idx, factor in enumerate(variable_factors):
            rank_product *= factor[0, :] + factor[1, :] * x[var_idx]

        residual = equation_factor @ (weights * rank_product)

        return np.asarray(residual, dtype=float).reshape(-1)


    def exact_phi_from_s(
        self,
        x: np.ndarray,
    ) -> np.ndarray:
        """
        Evaluate the exact monomial basis vector varphi(x) from S.

        The matrix S has shape:

            (n_vars, n_mon)

        Each column j of S defines one multilinear monomial:

            varphi_j(x) = prod_i (S[i, j] * x_i + 1 - abs(S[i, j]))

        If S[i, j] = 0, the local factor is 1.
        If S[i, j] = 1, the local factor is x_i.
        If S[i, j] = -1, the local factor is -x_i.

        Parameters
        ----------
        x
            Variable vector with shape ``(n_vars,)``.

        Returns
        -------
        np.ndarray
            Monomial basis vector with shape ``(n_mon,)``.
        """
        if sparse.isspmatrix_csc(self.S):
            S_csc = self.S
        else:
            S_csc = self.S.tocsc()

        n_vars, n_mon = S_csc.shape

        if x.shape[0] != n_vars:
            raise ValueError(
                f"x has size {x.shape[0]}, but S has {n_vars} variables."
            )

        varphi = np.ones(n_mon, dtype=float)

        data = S_csc.data
        indices = S_csc.indices
        indptr = S_csc.indptr

        for mon_idx in range(n_mon):
            start = indptr[mon_idx]
            end = indptr[mon_idx + 1]

            value = 1.0

            for ptr in range(start, end):
                var_idx = int(indices[ptr])
                s_val = float(data[ptr])
                value *= s_val * x[var_idx] + (1.0 - abs(s_val))

            varphi[mon_idx] = value

        return varphi


    def exact_residual_from_s_phi(
        self,
        x: np.ndarray,
        ) -> np.ndarray:
        """
        Evaluate the exact residual f(x) = Phi @ varphi(x).

        This is the exact residual of the sparse multilinear representation,
        not the CP/CPN approximation.
        """
        varphi = self.exact_phi_from_s(x=x)
        residual = self.Phi @ varphi
        return np.asarray(residual, dtype=float).reshape(-1)
    
    def linearize_multilinear(
        self,
        x: np.ndarray | None = None,
        sparse_output: bool = False,
    ) -> tuple[np.ndarray | sparse.csc_matrix, np.ndarray | sparse.csc_matrix, np.ndarray | sparse.csc_matrix]:
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
        EABC_sparse = (Phi @ F.T).tocsc()

        all_vars = self._ml_all_vars_sa
        idx_vars = self._ml_idx_vars
        ordered_pairs = sorted(zip(idx_vars, all_vars), key=lambda t: t[0])
        idx_vars_ordered = [idx for idx, _ in ordered_pairs]
        vars_ordered = [v for _, v in ordered_pairs]

        n_eq = EABC_sparse.shape[0]
        cols_to_take = len(idx_vars_ordered)
        dim = max(n_eq, cols_to_take)

        A_sparse = EABC_sparse[:, idx_vars_ordered[:cols_to_take]].tocsc()
        if A_sparse.shape[0] != dim or A_sparse.shape[1] != dim:
            if A_sparse.shape[1] < dim:
                right_pad = sparse.csc_matrix((A_sparse.shape[0], dim - A_sparse.shape[1]), dtype=float)
                A_sparse = sparse.hstack([A_sparse, right_pad], format="csc")
            if A_sparse.shape[0] < dim:
                bottom_pad = sparse.csc_matrix((dim - A_sparse.shape[0], dim), dtype=float)
                A_sparse = sparse.vstack([A_sparse, bottom_pad], format="csc")

        # Build descriptor E with explicit projection matrix using the same
        # diff->base convention as get_E_matrix.
        p_row: list[int] = []
        p_col: list[int] = []
        p_val: list[float] = []
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
            p_row.append(deriv_idx)
            p_col.append(dest_col)
            p_val.append(1.0)

        P = sparse.csc_matrix((p_val, (p_row, p_col)), shape=(EABC_sparse.shape[1], cols_to_take), dtype=float)

        E_sparse = (EABC_sparse @ P).tocsc()

        n_states = len(self._state_vars)
        if n_states > 0:
            diag_rows = np.arange(n_states, dtype=np.int64)
            I_state = sparse.csc_matrix((np.ones(n_states, dtype=float), (diag_rows, diag_rows)), shape=(dim, dim))
        else:
            I_state = sparse.csc_matrix((dim, dim), dtype=float)

        if E_sparse.shape[0] != dim or E_sparse.shape[1] != dim:
            if E_sparse.shape[1] < dim:
                right_pad = sparse.csc_matrix((E_sparse.shape[0], dim - E_sparse.shape[1]), dtype=float)
                E_sparse = sparse.hstack([E_sparse, right_pad], format="csc")
            if E_sparse.shape[0] < dim:
                bottom_pad = sparse.csc_matrix((dim - E_sparse.shape[0], dim), dtype=float)
                E_sparse = sparse.vstack([E_sparse, bottom_pad], format="csc")

        E_sparse = E_sparse - I_state

        if sparse_output:
            return E_sparse, A_sparse, EABC_sparse

        return E_sparse.toarray(), A_sparse.toarray(), EABC_sparse.toarray()

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
