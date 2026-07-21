# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import scipy.sparse as sp
import time
import warnings
import sys
import os
from scipy.sparse import csc_matrix
from scipy.sparse import linalg as spla
import matplotlib.pyplot as plt

from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Utils.Sparse.csc import pack_4_by_4_scipy
from VeraGridEngine.Utils.Symbolic.symbolic import get_expression_vars, Var, Const, BinOp
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
                 reference_error_tol: float = 3.0,
                 max_iter: int = 1000,
                 verbose: bool = True,
                 fixed_var_uids: list[int] | None = None,
                 debug_check_x_new: bool = False,
                 debug_x_new_abs_max: float = 1e6):
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
        self.reference_error_tol = float(reference_error_tol)
        self.verbose = verbose
        self.use_weighted_residual = os.getenv("VERAGRID_PSEUDO_WEIGHTED_RESIDUAL", "0").lower() in {"1", "true", "yes", "on"}
        self.weight_algebraic = float(os.getenv("VERAGRID_PSEUDO_WEIGHT_ALGEBRAIC", "10.0"))
        self.use_weighted_linear_solve = os.getenv("VERAGRID_PSEUDO_WEIGHTED_LINEAR_SOLVE", "0").lower() in {"1", "true", "yes", "on"}
        self.linear_solve_state_weight = float(os.getenv("VERAGRID_PSEUDO_LINEAR_STATE_WEIGHT", "1.0"))
        self.linear_solve_algebraic_weight = float(os.getenv("VERAGRID_PSEUDO_LINEAR_ALGEBRAIC_WEIGHT", "10.0"))
        self.use_state_tau_scaling = os.getenv("VERAGRID_PSEUDO_STATE_TAU_SCALING", "1").lower() in {"1", "true", "yes", "on"}
        self.use_state_tau_dtau_scale = os.getenv("VERAGRID_PSEUDO_STATE_TAU_DTAU_SCALE", "0").lower() in {"1", "true", "yes", "on"}
        self.state_tau_min = float(os.getenv("VERAGRID_PSEUDO_STATE_TAU_MIN", str(dtau_min)))
        state_tau_max_default = "inf" if self.use_state_tau_dtau_scale else str(dtau_max)
        self.state_tau_max = float(os.getenv("VERAGRID_PSEUDO_STATE_TAU_MAX", state_tau_max_default))
        self.state_tau_eps = float(os.getenv("VERAGRID_PSEUDO_STATE_TAU_EPS", "1e-12"))
        self.allow_lsqr_fallback = os.getenv("PSEUDO_ALLOW_LSQR", "1").lower() in {"1", "true", "yes", "on"}
        self.use_svd_diagnostics = os.getenv("VERAGRID_PSEUDO_SVD_DIAGNOSTICS", "0").lower() in {"1", "true", "yes", "on"}
        self.svd_diagnostics_limit = int(os.getenv("VERAGRID_PSEUDO_SVD_DIAGNOSTICS_LIMIT", "5"))
        self.linear_solve_damp = float(os.getenv("VERAGRID_PSEUDO_LINEAR_DAMP", "1e-6"))
        self.dtau_ser_min_factor = float(os.getenv("VERAGRID_PSEUDO_DTAU_SER_MIN_FACTOR", "0.5"))
        self.dtau_ser_max_factor = float(os.getenv("VERAGRID_PSEUDO_DTAU_SER_MAX_FACTOR", "5.0"))
        self.dtau_stall_ratio = float(os.getenv("VERAGRID_PSEUDO_DTAU_STALL_RATIO", "1.02"))
        self.dtau_stall_steps = int(os.getenv("VERAGRID_PSEUDO_DTAU_STALL_STEPS", "5"))
        self.dtau_stall_boost = float(os.getenv("VERAGRID_PSEUDO_DTAU_STALL_BOOST", "2.0"))
        self.fixed_var_uids = set(fixed_var_uids or [])
        uid2idx = self.problem.uid2idx_vars
        self._fixed_var_indices = sorted([uid2idx[uid] for uid in self.fixed_var_uids if uid in uid2idx])
        self.debug_check_x_new = debug_check_x_new
        self.debug_x_new_abs_max = float(debug_x_new_abs_max)
        self.t: Vec = np.empty(self.steps + 1)
        self.y: Mat = np.empty((self.steps + 1, self.problem.get_all_vars_number()))
        self.state_tau: Vec = np.full(int(self.problem.get_states_number()), float(dtau0), dtype=float)
        self._singular_report_count = 0
        self._svd_report_count = 0

    def _apply_fixed_mask(self, x: Vec, x_ref: Vec) -> Vec:
        if len(self._fixed_var_indices) == 0:
            return x
        for idx in self._fixed_var_indices:
            if 0 <= idx < x.size and 0 <= idx < x_ref.size:
                x[idx] = x_ref[idx]
        return x

    def _check_fixed_drift(self, x: Vec, x_ref: Vec, where: str) -> None:
        if len(self._fixed_var_indices) == 0:
            return
        bad = []
        for idx in self._fixed_var_indices:
            if 0 <= idx < x.size and 0 <= idx < x_ref.size:
                d = float(abs(x[idx] - x_ref[idx]))
                if d > 1e-14:
                    bad.append((idx, d, float(x[idx]), float(x_ref[idx])))
        if bad:
            preview = [f"{self._var_index_name(i)}: x={vx:+.6e}, ref={vr:+.6e}, drift={d:.3e}" for i, d, vx, vr in bad[:6]]
            raise ValueError(f"Fixed variable drift detected at {where}: {preview}")

    def _dbg(self, msg: str) -> None:
        if self.verbose:
            print(f"[PseudoTransient] {msg}")

    def _build_residual_weights(self, n_rhs: int) -> np.ndarray:
        w = np.ones(n_rhs, dtype=float)
        if not self.use_weighted_residual:
            return w
        n_states = int(self.problem.get_states_number())
        if n_states < n_rhs:
            w[n_states:] = self.weight_algebraic
        return w

    def _build_linear_solve_weights(self, n_rhs: int) -> np.ndarray:
        w = np.ones(n_rhs, dtype=float)
        if not self.use_weighted_linear_solve:
            return w

        n_states = int(self.problem.get_states_number())
        if n_states > 0:
            w[:min(n_states, n_rhs)] = self.linear_solve_state_weight
        if n_states < n_rhs:
            w[n_states:] = self.linear_solve_algebraic_weight
        return w

    def _apply_linear_solve_weights(self, J: sp.csc_matrix, rhs: Vec, w: np.ndarray) -> tuple[sp.csc_matrix, Vec]:
        if w.size != rhs.size or not self.use_weighted_linear_solve:
            return J, rhs
        if np.all(w == 1.0):
            return J, rhs
        W = sp.diags(w, format="csc")
        return (W @ J).tocsc(), w * rhs

    @staticmethod
    def _weighted_norm(v: np.ndarray, w: np.ndarray) -> float:
        return float(np.linalg.norm(w * v))

    def _get_problem_state_eqs(self):
        if hasattr(self.problem, "_state_eqs"):
            return list(self.problem._state_eqs)
        if hasattr(self.problem, "block") and hasattr(self.problem.block, "state_eqs"):
            return list(self.problem.block.state_eqs)
        return list()

    def _get_problem_algebraic_eqs(self):
        if hasattr(self.problem, "_algebraic_eqs"):
            return list(self.problem._algebraic_eqs)
        if hasattr(self.problem, "block") and hasattr(self.problem.block, "algebraic_eqs"):
            return list(self.problem.block.algebraic_eqs)
        return list()

    def _get_problem_state_vars(self):
        if hasattr(self.problem, "_state_vars"):
            return list(self.problem._state_vars)
        if hasattr(self.problem, "block") and hasattr(self.problem.block, "state_vars"):
            return list(self.problem.block.state_vars)
        return list()

    def _rhs_index_equation_repr(self, rhs_idx: int) -> str:
        n_states = int(self.problem.get_states_number())
        state_eqs = self._get_problem_state_eqs()
        algebraic_eqs = self._get_problem_algebraic_eqs()
        state_vars = self._get_problem_state_vars()

        if rhs_idx < n_states:
            base_eq = state_eqs[rhs_idx] if rhs_idx < len(state_eqs) else "<unknown state eq>"
            state_name = state_vars[rhs_idx].name if rhs_idx < len(state_vars) else f"x[{rhs_idx}]"
            return f"state_update({state_name}): x - x_prev - h*({base_eq})"

        alg_idx = rhs_idx - n_states
        if 0 <= alg_idx < len(algebraic_eqs):
            return f"algebraic[{alg_idx}]: {algebraic_eqs[alg_idx]}"

        return f"rhs[{rhs_idx}]: <unknown equation>"

    def _expr_begin_repr(self, expr) -> str:
        begin_fn = getattr(expr, "begin", None)
        if callable(begin_fn):
            try:
                return str(begin_fn())
            except Exception:
                pass

        if isinstance(expr, BinOp) and expr.op == "-":
            return str(expr.left)

        if isinstance(expr, Var):
            return expr.name

        return str(expr)

    def _rhs_index_equation_begin(self, rhs_idx: int) -> str:
        n_states = int(self.problem.get_states_number())
        state_eqs = self._get_problem_state_eqs()
        algebraic_eqs = self._get_problem_algebraic_eqs()
        state_vars = self._get_problem_state_vars()

        if rhs_idx < n_states:
            state_name = state_vars[rhs_idx].name if rhs_idx < len(state_vars) else f"x[{rhs_idx}]"
            if rhs_idx < len(state_eqs):
                return f"state_update({state_name})"
            return f"state_update[{rhs_idx}]"

        alg_idx = rhs_idx - n_states
        if 0 <= alg_idx < len(algebraic_eqs):
            head = self._expr_begin_repr(algebraic_eqs[alg_idx])
            return f"algebraic[{alg_idx}]: {head}"

        return f"rhs[{rhs_idx}]"

    def _var_value_debug(self, var: Var, x: Vec) -> str:
        local_vars = self._get_problem_state_vars() + self._problem_algebraic_vars()
        local_uid2idx = {v.uid: i for i, v in enumerate(local_vars)}

        if var.uid in local_uid2idx:
            i = local_uid2idx[var.uid]
            if 0 <= i < len(x):
                return f"{var.name}={x[i]}(x_local[{i}])"

        uid2idx_vars = getattr(self.problem, "uid2idx_vars", None)
        if isinstance(uid2idx_vars, dict) and var.uid in uid2idx_vars:
            i = uid2idx_vars[var.uid]
            if 0 <= i < len(x):
                return f"{var.name}={x[i]}(x_global[{i}])"

        uid2idx_evt = getattr(self.problem, "_uid2idx_event_params", None)
        vparams = getattr(self.problem, "_variable_parameters_values", None)
        if isinstance(uid2idx_evt, dict) and var.uid in uid2idx_evt and vparams is not None:
            i = uid2idx_evt[var.uid]
            if 0 <= i < len(vparams):
                return f"{var.name}={vparams[i]}(vprms[{i}])"

        uid2idx_params = getattr(self.problem, "_uid2idx_params", None)
        cparams = getattr(self.problem, "_constant_params", None)
        if isinstance(uid2idx_params, dict) and var.uid in uid2idx_params and cparams is not None:
            i = uid2idx_params[var.uid]
            if 0 <= i < len(cparams):
                return f"{var.name}={cparams[i]}(cprms[{i}])"

        return f"{var.name}=<unresolved>"

    def _rhs_index_equation_vars_debug(self, rhs_idx: int, x: Vec) -> list[str]:
        n_states = int(self.problem.get_states_number())
        eq = None
        if rhs_idx < n_states:
            state_eqs = self._get_problem_state_eqs()
            if rhs_idx < len(state_eqs):
                eq = state_eqs[rhs_idx]
        else:
            alg_idx = rhs_idx - n_states
            algebraic_eqs = self._get_problem_algebraic_eqs()
            if 0 <= alg_idx < len(algebraic_eqs):
                eq = algebraic_eqs[alg_idx]

        if eq is None or isinstance(eq, Const):
            return list()

        try:
            vars_in_eq = get_expression_vars(eq)
        except Exception:
            return list()

        debug_items: list[str] = list()
        seen = set()
        for vr in vars_in_eq:
            if not isinstance(vr, Var):
                continue
            if vr.uid in seen:
                continue
            seen.add(vr.uid)
            debug_items.append(self._var_value_debug(vr, x))

        return debug_items

    def _debug_check_x_new(self, x_new: Vec, step_idx: int, tries: int, dtau: float) -> None:
        if not self.debug_check_x_new:
            return

        bad_idx = np.where(~np.isfinite(x_new))[0]
        if bad_idx.size > 0:
            bad_vals = x_new[bad_idx]
            raise ValueError(
                "NaN or Inf in x_new"
                f" (step={step_idx}, try={tries}, dtau={dtau:.3e}, "
                f"bad_idx={bad_idx.tolist()}, bad_vals={bad_vals.tolist()})"
            )

        large_idx = np.where(np.abs(x_new) > self.debug_x_new_abs_max)[0]
        if large_idx.size > 0:
            large_vals = x_new[large_idx]
            raise ValueError(
                "x_new magnitude too large"
                f" (step={step_idx}, try={tries}, dtau={dtau:.3e}, abs_max={self.debug_x_new_abs_max:.3e}, "
                f"large_idx={large_idx.tolist()}, large_vals={large_vals.tolist()})"
            )

    def _problem_algebraic_vars(self):
        algeb = getattr(self.problem, "algebraic_vars", None)
        if callable(algeb):
            return list(algeb())
        if algeb is not None:
            return list(algeb)

        getter = getattr(self.problem, "get_algebraic_vars", None)
        if callable(getter):
            return list(getter())

        return list()

    def _problem_state_vars(self):
        states = getattr(self.problem, "state_vars", None)
        if callable(states):
            return list(states())
        if states is not None:
            return list(states)

        return list()

    def _problem_diff_vars(self):
        diff_vars = getattr(self.problem, "_diff_vars", None)
        if diff_vars is not None:
            return list(diff_vars)

        getter = getattr(self.problem, "get_diff_vars", None)
        if callable(getter):
            return list(getter())

        return list()

    def _find_reference_pin_indices(self) -> list[int]:
        n_vars = int(self.problem.get_all_vars_number())
        groups = (
            ("Pm_ref", "Pref", "P_ref"),
            ("UsRefPu", "Vref", "V_ref", "U_ref"),
            ("u_exciter3", "y_exciter3"),
        )
        found: list[int] = list()
        used = set(self._fixed_var_indices)
        for group in groups:
            idx = None
            for i in range(n_vars):
                if i in used:
                    continue
                nm = self._var_index_name(i)
                if any(tok in nm for tok in group):
                    idx = i
                    break
            if idx is not None:
                found.append(idx)
                used.add(idx)
        return found

    def _var_index_name(self, idx: int) -> str:
        vars_all = self._problem_state_vars() + self._problem_algebraic_vars()
        if 0 <= idx < len(vars_all):
            return vars_all[idx].name
        return f"x[{idx}]"

    def _report_selected_var_values(self, x: Vec, labels: tuple[str, ...]) -> None:
        vars_all = self._problem_state_vars() + self._problem_algebraic_vars()
        if len(vars_all) == 0 or x.size == 0:
            return

        matches: list[str] = []
        used_idx: set[int] = set()
        for token in labels:
            token_l = token.lower()
            hit_idx = None

            # Prefer exact/canonical prefix match (e.g. Id*), avoid accidental matches like Psid*.
            for i, var in enumerate(vars_all):
                name = (getattr(var, "name", "") or "").strip()
                if i in used_idx:
                    continue
                if name.lower().startswith(token_l):
                    hit_idx = i
                    break

            # Fallback: contains token when prefix is unavailable.
            if hit_idx is None:
                for i, var in enumerate(vars_all):
                    name = (getattr(var, "name", "") or "").strip()
                    if i in used_idx:
                        continue
                    if token_l in name.lower():
                        hit_idx = i
                        break

            if hit_idx is not None:
                used_idx.add(hit_idx)
                name = getattr(vars_all[hit_idx], "name", "") or f"x[{hit_idx}]"
                val = float(x[hit_idx]) if 0 <= hit_idx < x.size else float("nan")
                matches.append(f"{name}={val:+.6e}")
            else:
                matches.append(f"{token}=<not found>")

        if matches:
            print(
                f"[PseudoTransient][Singular] selected vars: {matches}",
                file=sys.stderr,
            )

    def _report_piecewise_activity(self, rhs: Vec) -> None:
        if rhs.size == 0 or not np.all(np.isfinite(rhs)):
            return

        n_states = int(self.problem.get_states_number())
        n_rhs = int(rhs.size)
        piecewise_rows: list[tuple[int, float, str]] = []
        for i in range(n_states, n_rhs):
            eq_txt = self._rhs_index_equation_repr(i)
            if "heaviside" in eq_txt:
                piecewise_rows.append((i, float(rhs[i]), eq_txt))

        if len(piecewise_rows) == 0:
            return

        piecewise_rows.sort(key=lambda t: abs(t[1]), reverse=True)
        top = piecewise_rows[:12]
        payload = [f"rhs[{i}]={v:+.3e} | {eq}" for i, v, eq in top]
        print(
            f"[PseudoTransient][Singular] piecewise/heaviside residuals (top {len(top)}): {payload}",
            file=sys.stderr,
        )

    def _report_singularity_diagnostics(self, J: sp.csc_matrix, rhs: Vec, x: Vec, context: str) -> None:
        # Print diagnostics at every failing step/try during debugging.
        self._singular_report_count += 1

        try:
            row_abs = np.asarray(np.abs(J).sum(axis=1)).ravel()
            col_abs = np.asarray(np.abs(J).sum(axis=0)).ravel()
            near_zero_rows = np.where(row_abs < 1e-14)[0]
            near_zero_cols = np.where(col_abs < 1e-14)[0]

            print(f"[PseudoTransient][Singular] context={context}", file=sys.stderr)
            print(
                f"[PseudoTransient][Singular] shape={J.shape}, nnz={J.nnz}, "
                f"near_zero_rows={int(near_zero_rows.size)}, near_zero_cols={int(near_zero_cols.size)}",
                file=sys.stderr,
            )

            if near_zero_rows.size > 0:
                preview = near_zero_rows[:8]
                row_labels = [self._rhs_index_equation_begin(int(i)) for i in preview]
                print(
                    f"[PseudoTransient][Singular] zero-like rows (first {len(preview)}): {row_labels}",
                    file=sys.stderr,
                )

            if near_zero_cols.size > 0:
                preview = near_zero_cols[:8]
                col_labels = [self._var_index_name(int(i)) for i in preview]
                print(
                    f"[PseudoTransient][Singular] zero-like cols (first {len(preview)}): {col_labels}",
                    file=sys.stderr,
                )

            if rhs.size > 0 and np.all(np.isfinite(rhs)):
                idx = np.argsort(np.abs(rhs))[::-1][:8]
                top_rhs = [f"{self._rhs_index_equation_repr(int(i))}: {rhs[int(i)]:+.3e}" for i in idx]
                print(f"[PseudoTransient][Singular] largest rhs entries: {top_rhs}", file=sys.stderr)
                self._report_piecewise_activity(rhs)

            self._report_selected_var_values(x, labels=("Vd", "Vq", "Id", "Iq"))

            # Show equations most directly coupled to Vf-like variables.
            vf_cols = [i for i in range(J.shape[1]) if "vf" in self._var_index_name(i).lower()]
            if len(vf_cols) > 0:
                for c in vf_cols[:3]:
                    col = J.getcol(c)
                    if col.nnz == 0:
                        print(
                            f"[PseudoTransient][Singular] Vf-coupled column {self._var_index_name(c)} has no nonzeros",
                            file=sys.stderr,
                        )
                        continue
                    rows = col.indices
                    vals = col.data
                    order = np.argsort(np.abs(vals))[::-1]
                    top = order[:8]
                    eqs = [
                        f"{self._rhs_index_equation_repr(int(rows[k]))}: d/d{self._var_index_name(c)}={vals[k]:+.3e}"
                        for k in top
                    ]
                    print(
                        f"[PseudoTransient][Singular] equations coupled to {self._var_index_name(c)}: {eqs}",
                        file=sys.stderr,
                    )

            # SVD-based diagnostics for moderate size systems.
            n = J.shape[0]
            if n <= 220:
                dense = J.toarray()
                _, s, vh = np.linalg.svd(dense, full_matrices=False)
                smin = float(s[-1]) if s.size > 0 else float("nan")
                smax = float(s[0]) if s.size > 0 else float("nan")
                cond = float(smax / smin) if s.size > 0 and smin > 0 else float("inf")
                print(
                    f"[PseudoTransient][Singular] svd sigma_max={smax:.3e}, sigma_min={smin:.3e}, cond~={cond:.3e}",
                    file=sys.stderr,
                )

                if s.size > 0:
                    cut = max(1e-12, 1e-10 * smax)
                    singular_dirs = np.where(s < cut)[0]
                    if singular_dirs.size > 0:
                        i = int(singular_dirs[0])
                        v = vh.T[:, i]
                        dom = np.argsort(np.abs(v))[::-1][:8]
                        dom_vars = [f"{self._var_index_name(int(j))}: {v[int(j)]:+.3e}" for j in dom]
                        print(
                            f"[PseudoTransient][Singular] dominant variables in null-like direction: {dom_vars}",
                            file=sys.stderr,
                        )

                        # Quantify residual component aligned with left null-like direction.
                        # For SVD J = U S V^T, near-null row-space direction is u_i.
                        if rhs.size == J.shape[0]:
                            u_i = dense @ v
                            n_u = float(np.linalg.norm(u_i))
                            if n_u > 0 and np.all(np.isfinite(u_i)) and np.all(np.isfinite(rhs)):
                                u_i = u_i / n_u
                                rhs_norm = float(np.linalg.norm(rhs))
                                coeff = float(np.dot(u_i, rhs))
                                rhs_along = abs(coeff)
                                rhs_orth = float(np.sqrt(max(rhs_norm * rhs_norm - rhs_along * rhs_along, 0.0)))
                                frac = rhs_along / max(rhs_norm, 1e-30)
                                print(
                                    "[PseudoTransient][Singular] rhs projection: "
                                    f"|rhs|_2={rhs_norm:.3e}, |along_null_left|={rhs_along:.3e}, "
                                    f"|orthogonal|={rhs_orth:.3e}, along_frac={frac:.3e}",
                                    file=sys.stderr,
                                )
        except Exception as e:
            print(f"[PseudoTransient][Singular] diagnostics failed: {e}", file=sys.stderr)

    def _report_svd_diagnostics(self,
                                J: sp.csc_matrix,
                                rhs: Vec,
                                J_solve: sp.csc_matrix,
                                rhs_solve: Vec,
                                context: str,
                                force: bool = False) -> None:
        def emit(msg: str) -> None:
            if force:
                print(f"[PseudoTransient]{msg}", file=sys.stderr)
            else:
                self._dbg(msg)

        if not force and not self.use_svd_diagnostics:
            return
        if not force and self._svd_report_count >= self.svd_diagnostics_limit:
            return
        if J_solve.shape[0] == 0 or J_solve.shape[1] == 0 or J_solve.shape[0] > 240 or J_solve.shape[1] > 240:
            if force:
                emit(f"[SVD] {context}: skipped, solve matrix shape={J_solve.shape} outside diagnostic limit")
            return
        if rhs_solve.size != J_solve.shape[0] or not np.all(np.isfinite(rhs_solve)):
            if force:
                emit(
                    f"[SVD] {context}: skipped, rhs size/finite check failed "
                    f"(rhs_size={rhs_solve.size}, matrix_rows={J_solve.shape[0]})"
                )
            return

        self._svd_report_count += 1
        try:
            A = J_solve.toarray()
            b = -np.array(rhs_solve, dtype=float, copy=False)
            u, s, vh = np.linalg.svd(A, full_matrices=True)
            smax = float(s[0]) if s.size > 0 else 0.0
            tol = max(A.shape) * np.finfo(float).eps * max(smax, 1.0)
            rank = int(np.sum(s > tol))
            smin = float(s[-1]) if s.size > 0 else 0.0
            cond = float(smax / smin) if smin > 0.0 else float("inf")

            delta_lstsq, *_ = np.linalg.lstsq(A, b, rcond=None)
            residual_vec = A @ delta_lstsq - b
            residual_norm = float(np.linalg.norm(residual_vec))
            b_norm = float(np.linalg.norm(b))
            residual_frac = residual_norm / max(b_norm, 1e-30)
            preview_s = [f"{val:.3e}" for val in s[:min(6, s.size)]]
            tail_s = [f"{val:.3e}" for val in s[max(0, s.size - 6):]]

            emit(
                f"[SVD] {context}: shape={A.shape}, rank={rank}, sigma_max={smax:.3e}, "
                f"sigma_min={smin:.3e}, cond~={cond:.3e}, weighted_lstsq_res={residual_norm:.3e}, "
                f"weighted_res_frac={residual_frac:.3e}, sigma_head={preview_s}, sigma_tail={tail_s}"
            )

            if vh.size > 0 and s.size > 0:
                v_min = vh[min(rank, vh.shape[0] - 1), :] if rank < vh.shape[0] else vh[-1, :]
                dom = np.argsort(np.abs(v_min))[::-1][:8]
                dom_vars = [f"{self._var_index_name(int(j))}: {v_min[int(j)]:+.3e}" for j in dom]
                emit(f"[SVD] {context}: weak right-singular variables={dom_vars}")

            if u.size > 0 and s.size > 0:
                n_weak = min(3, s.size, u.shape[1])
                for sv_idx in range(s.size - n_weak, s.size):
                    left_vec = u[:, sv_idx]
                    dom_rows = np.argsort(np.abs(left_vec))[::-1][:8]
                    row_labels = [
                        f"{self._rhs_index_equation_begin(int(i))}: {left_vec[int(i)]:+.3e}, rhs={rhs_solve[int(i)]:+.3e}"
                        for i in dom_rows
                    ]
                    emit(
                        f"[SVD] {context}: weak equation rows sigma[{sv_idx}]={s[sv_idx]:.3e}, "
                        f"dominant_rows={row_labels}"
                    )

            left_null_start = rank
            if u.shape[1] > left_null_start:
                coeffs = u[:, left_null_start:].T @ b
                if coeffs.size > 0:
                    order = np.argsort(np.abs(coeffs))[::-1]
                    for pos in order[:min(3, order.size)]:
                        left_vec = u[:, left_null_start + int(pos)]
                        coeff = float(coeffs[int(pos)])
                        dom_rows = np.argsort(np.abs(left_vec))[::-1][:8]
                        row_labels = [
                            f"{self._rhs_index_equation_begin(int(i))}: {left_vec[int(i)]:+.3e}"
                            for i in dom_rows
                        ]
                        emit(
                            f"[SVD] {context}: left-null coeff={coeff:+.3e}, "
                            f"dominant_rows={row_labels}"
                        )

            if J.shape == J_solve.shape and rhs.size == rhs_solve.size:
                return

            A0 = J.toarray()
            b0 = -np.array(rhs, dtype=float, copy=False)
            if b0.size == A0.shape[0]:
                delta0, *_ = np.linalg.lstsq(A0, b0, rcond=None)
                r0 = A0 @ delta0 - b0
                r0_norm = float(np.linalg.norm(r0))
                b0_norm = float(np.linalg.norm(b0))
                emit(
                    f"[SVD] {context}: unweighted_lstsq_res={r0_norm:.3e}, "
                    f"unweighted_res_frac={r0_norm / max(b0_norm, 1e-30):.3e}"
                )
        except Exception as exc:
            emit(f"[SVD] {context}: diagnostics failed ({exc})")

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
        Jacobian for pseudo-transient residual:

            r_state = (x - x_prev) / h - f(x, y)
            r_alg   = g(x, y)

        therefore:
            J11 = (1/h) I - d f / d x
            J12 = - d f / d y
            J21 = d g / d x
            J22 = d g / d y
        """
        n_states = self.problem.get_states_number()
        if n_states == 0:
            return self.problem.get_j22(x, dx, h)

        # For initialization problems with numerical Jacobian, compute once and split.
        # This avoids recomputing 4 separate finite-difference Jacobians and mixing them.
        jac_full_fn = getattr(self.problem, "_compute_numerical_jacobian", None)
        if callable(jac_full_fn):
            j_full = jac_full_fn(x, dx, h).tocsc()
            n_total = j_full.shape[0]
            n_alg = n_total - n_states
            tau_diag = self._state_tau_inv_diag(n_states, h)
            j11 = (tau_diag - j_full[:n_states, :n_states]).tocsc()
            j12 = (-j_full[:n_states, n_states:n_states + n_alg]).tocsc()
            j21 = j_full[n_states:n_states + n_alg, :n_states].tocsc()
            j22 = j_full[n_states:n_states + n_alg, n_states:n_states + n_alg].tocsc()
            return pack_4_by_4_scipy(j11, j12, j21, j22)

        j11_val: csc_matrix = self.problem.get_j11(x, dx, h)
        j12_val: csc_matrix = self.problem.get_j12(x, dx, h)
        j21_val: csc_matrix = self.problem.get_j21(x, dx, h)
        j22_val: csc_matrix = self.problem.get_j22(x, dx, h)

        tau_diag = self._state_tau_inv_diag(n_states, h)
        j11 = (tau_diag - j11_val).tocsc()
        j12 = (-j12_val).tocsc()
        j21 = j21_val.tocsc()
        j22 = j22_val.tocsc()

        return pack_4_by_4_scipy(j11, j12, j21, j22)

    def _state_tau_inv_diag(self, n_states: int, h: float) -> sp.csc_matrix:
        if n_states <= 0:
            return sp.csc_matrix((0, 0))
        tau = self._state_tau_vector(n_states, h)
        return sp.diags(1.0 / tau, format="csc")

    def _state_tau_vector(self, n_states: int, h: float) -> np.ndarray:
        if not self.use_state_tau_scaling:
            return np.full(n_states, h, dtype=float)
        if self.state_tau.size != n_states:
            self.state_tau = np.full(n_states, h, dtype=float)
        return self.state_tau

    def _update_state_tau_from_derivative(self, f_state: Vec, dtau: float, step_idx: int) -> None:
        if not self.use_state_tau_scaling:
            return
        n_states = int(self.problem.get_states_number())
        if n_states <= 0 or f_state.size < n_states:
            return

        numerator = abs(dtau) if self.use_state_tau_dtau_scale else 1.0
        tau = numerator / (0.01+ np.abs(f_state[:n_states]) + self.state_tau_eps)
        tau = np.clip(tau, self.state_tau_min, 1e10)
        if self.state_tau.size != n_states or np.any(tau != self.state_tau):
            self.state_tau = tau
            if self.verbose and (step_idx <= 5 or step_idx % 25 == 0):
                state_vars = self._problem_state_vars()
                preview = []
                for i in range(min(n_states, 8)):
                    name = state_vars[i].name if i < len(state_vars) else f"state[{i}]"
                    preview.append(f"{name}: tau={tau[i]:.3e}, f={f_state[i]:+.3e}")
                self._dbg(f"state tau step={step_idx}: {preview}")

    def _rhs_steady(self, x: Vec, dx: Vec) -> Vec:
        f_algeb = self.problem.rhs_algebraic(x, dx)
        if self.problem.get_states_number() > 0:
            f_state = self.problem.rhs_state(x, dx)
            return np.r_[f_state, f_algeb]
        return f_algeb

    def _jacobian_steady(self, x: Vec, dx: Vec) -> sp.csc_matrix:
        jac_full_fn = getattr(self.problem, "_compute_numerical_jacobian", None)
        if callable(jac_full_fn):
            return jac_full_fn(x, dx, self.h).tocsc()

        if self.problem.get_states_number() == 0:
            return self.problem.get_j22(x, dx, self.h)

        j11 = self.problem.get_j11(x, dx, self.h).tocsc()
        j12 = self.problem.get_j12(x, dx, self.h).tocsc()
        j21 = self.problem.get_j21(x, dx, self.h).tocsc()
        j22 = self.problem.get_j22(x, dx, self.h).tocsc()

        return pack_4_by_4_scipy(j11, j12, j21, j22)

    def _solve_linear_system(self, J: sp.csc_matrix, rhs: Vec, x: Vec, context: str) -> np.ndarray:
        solve_weights = self._build_linear_solve_weights(rhs.size)
        J_solve, rhs_solve = self._apply_linear_solve_weights(J, rhs, solve_weights)
        m = int(J.shape[0])
        n = int(J.shape[1])
        if m == 0 or n == 0:
            return np.array([], dtype=float)

        self._report_svd_diagnostics(J, rhs, J_solve, rhs_solve, context)

        def solve_lsqr(reason: str) -> np.ndarray:
            if not self.allow_lsqr_fallback:
                raise RuntimeError(f"{context}: singular linear system in pseudo-transient ({reason})")

            self._dbg(f"{context}: {reason}; trying lsqr fallback")
            delta_lsqr, *_ = spla.lsqr(
                J_solve,
                -rhs_solve,
                damp=self.linear_solve_damp,
                atol=1e-10,
                btol=1e-10,
                iter_lim=max(200, 2 * max(m, n)),
            )
            if np.all(np.isfinite(delta_lsqr)):
                self._dbg(f"{context}: lsqr fallback succeeded")
                return np.asarray(delta_lsqr, dtype=float)
            raise RuntimeError(f"{context}: lsqr fallback failed after {reason}")

        # Rectangular systems cannot be solved by spsolve; use least-squares.
        if m != n:
            return solve_lsqr(f"rectangular Jacobian {J.shape}")

        if self.linear_solve_damp > 0.0:
            return solve_lsqr(f"regularized damped solve requested (damp={self.linear_solve_damp:.3e})")

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Matrix is exactly singular")
            try:
                delta = spla.spsolve(J_solve, -rhs_solve)
            except Exception as exc:
                self._report_singularity_diagnostics(J, rhs, x=x, context=context)
                try:
                    return solve_lsqr(f"spsolve failed ({exc})")
                except RuntimeError as fallback_exc:
                    raise fallback_exc from exc

        if not np.all(np.isfinite(delta)):
            self._report_singularity_diagnostics(J, rhs, x=x, context=context)
            return solve_lsqr("non-finite spsolve result")

        return np.asarray(delta, dtype=float)

    def _newton_polish(self, x: Vec, tol: float, max_iter: int = 8) -> tuple[Vec, float]:
        dx = np.zeros(self.problem.get_diff_var_number(), dtype=float)
        for k in range(max_iter):
            rhs = self._rhs_steady(x, dx)
            if not np.all(np.isfinite(rhs)):
                self._dbg(f"newton polish abort: non-finite rhs at iter={k + 1}")
                break

            res_inf = float(np.linalg.norm(rhs, np.inf)) if rhs.size > 0 else 0.0
            if res_inf <= tol:
                self._dbg(f"newton polish converged at iter={k + 1}, residual_inf={res_inf:.3e}")
                return x, res_inf

            J = self._jacobian_steady(x, dx)
            delta = self._solve_linear_system(J, rhs, x=x, context=f"newton_polish iter={k + 1}")
            solved = np.all(np.isfinite(delta))
            if not solved:
                self._dbg(f"newton polish abort: linear solve failed at iter={k + 1}")
                break

            trial_scales = (1.0)
            best_x = x
            best_res = np.inf
            for scale in trial_scales:
                xt = x + scale * delta
                rt = self._rhs_steady(xt, dx)
                if not np.all(np.isfinite(rt)):
                    continue
                rinf = float(np.linalg.norm(rt, np.inf)) if rt.size > 0 else 0.0
                if rinf < best_res:
                    best_res = rinf
                    best_x = xt
                if rinf <= res_inf * (1.0 - 1e-4 * scale):
                    break

            x = best_x
            self._dbg(
                f"newton polish iter={k + 1}: residual_inf={res_inf:.3e}->{best_res:.3e}, "
                f"|delta|_2={np.linalg.norm(delta):.3e}"
            )

        rhs_final = self._rhs_steady(x, dx)
        final_inf = float(np.linalg.norm(rhs_final, np.inf)) if rhs_final.size > 0 and np.all(np.isfinite(rhs_final)) else np.inf
        return x, final_inf
    
    def _rhs_pseudo_transient(self, x: Vec, xn: Vec, dx: Vec, h: float) -> Vec:
        """
        Return 𝑑x/dt given the current *state* vector.
        :param x: get the right-hand-side give a state vector
        :param xn:
        :param h: simulation step
        :return [f_state_update, f_algeb]
        """
        f_algeb = self.problem.rhs_algebraic(x,  0*dx)
        if self.problem.get_states_number() > 0:
            f_state = self.problem.rhs_state(x, 0*dx)
            n_states = self.problem.get_states_number()
            tau = self._state_tau_vector(n_states, h)
            f_state_update = (x[:n_states] - xn[:n_states]) / tau - f_state
            f_state_update = -f_state
            return np.r_[f_state_update, f_algeb]

        else:
            return f_algeb

    def _plot_diagnostics(self,
                          dtau_hist: list[float],
                          dx_error_hist: list[float],
                          residual_hist: list[float],
                          x_hist: list[np.ndarray],
                          state_eq_hist: list[np.ndarray]) -> None:
        fig, axs = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

        if len(dx_error_hist) > 0:
            axs[0].semilogy(dx_error_hist, label="||dx||")
        axs[0].set_ylabel("dx error (log)")
        axs[0].legend()

        if len(residual_hist) > 0:
            axs[1].semilogy(residual_hist, label="Residual norm")
        axs[1].set_ylabel("Residual (log)")
        axs[1].legend()

        if len(dtau_hist) > 0:
            axs[2].semilogy(dtau_hist, label="dtau")
        axs[2].set_ylabel("dtau")
        axs[2].set_xlabel("Step index")
        axs[2].legend()

        x_hist_arr = np.array(x_hist)
        if x_hist_arr.size == 0 or x_hist_arr.ndim < 2:
            return

        state_vars = self._problem_state_vars()
        n_state_vars = len(state_vars)
        algeb_vars = self._problem_algebraic_vars()
        n_algeb_vars = len(algeb_vars)
        vars_per_plot = 5

        if n_state_vars > 0:
            nplots_state = (n_state_vars + vars_per_plot - 1) // vars_per_plot
            fig_state, axs_state = plt.subplots(nplots_state, 1, figsize=(10, 2.5 * nplots_state), sharex=True)
            if nplots_state == 1:
                axs_state = [axs_state]
            for i in range(nplots_state):
                start = i * vars_per_plot
                end = min((i + 1) * vars_per_plot, n_state_vars)
                for var in state_vars[start:end]:
                    axs_state[i].plot(x_hist_arr[:, self.problem.uid2idx_vars[var.uid]], label=var.name)
                axs_state[i].set_ylabel("Value")
                axs_state[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
            axs_state[-1].set_xlabel("Step index")

        if n_algeb_vars > 0:
            nplots_algeb = (n_algeb_vars + vars_per_plot - 1) // vars_per_plot
            fig_algeb, axs_algeb = plt.subplots(nplots_algeb, 1, figsize=(10, 2.5 * nplots_algeb), sharex=True)
            if nplots_algeb == 1:
                axs_algeb = [axs_algeb]
            for i in range(nplots_algeb):
                start = i * vars_per_plot
                end = min((i + 1) * vars_per_plot, n_algeb_vars)
                for var in algeb_vars[start:end]:
                    axs_algeb[i].plot(x_hist_arr[:, self.problem.uid2idx_vars[var.uid]], label=var.name)
                axs_algeb[i].set_ylabel("Value")
                axs_algeb[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
            axs_algeb[-1].set_xlabel("Step index")

        state_eq_hist_arr = np.array(state_eq_hist)
        n_state_eqs = int(self.problem.get_states_number())
        if n_state_eqs > 0 and state_eq_hist_arr.size > 0 and state_eq_hist_arr.ndim == 2:
            nplots_state_eq = (n_state_eqs + vars_per_plot - 1) // vars_per_plot
            fig_state_eq, axs_state_eq = plt.subplots(nplots_state_eq, 1, figsize=(10, 2.5 * nplots_state_eq), sharex=True)
            if nplots_state_eq == 1:
                axs_state_eq = [axs_state_eq]

            state_vars = self._problem_state_vars()
            labels = list()
            for i in range(n_state_eqs):
                if i < len(state_vars):
                    labels.append(f"state_update({state_vars[i].name})")
                else:
                    labels.append(f"state_update[{i}]")

            for i in range(nplots_state_eq):
                start = i * vars_per_plot
                end = min((i + 1) * vars_per_plot, n_state_eqs)
                for j in range(start, end):
                    axs_state_eq[i].plot(state_eq_hist_arr[:, j], label=labels[j])
                axs_state_eq[i].axhline(0.0, color="k", linewidth=0.8, alpha=0.4)
                axs_state_eq[i].set_ylabel("Eq value")
                axs_state_eq[i].legend(loc="best", fontsize="x-small", ncol=2, frameon=False)
            axs_state_eq[-1].set_xlabel("Step index")
        plt.show()

    def _report_failure_svd_diagnostics(self, x: Vec, xn: Vec, dx: Vec, dtau: float, context: str) -> None:
        try:
            rhs = self._rhs_pseudo_transient(x, xn, dx, dtau)
            if not np.all(np.isfinite(rhs)):
                print(f"[PseudoTransient][SVD] {context}: skipped, non-finite rhs", file=sys.stderr)
                return

            J = self._jacobian_pseudo_transient(x, dx, dtau)
            solve_weights = self._build_linear_solve_weights(rhs.size)
            J_solve, rhs_solve = self._apply_linear_solve_weights(J, rhs, solve_weights)
            self._report_svd_diagnostics(J, rhs, J_solve, rhs_solve, context=context, force=True)
        except Exception as exc:
            print(f"[PseudoTransient][SVD] {context}: diagnostics failed ({exc})", file=sys.stderr)

    def _report_rhs_offenders(self,
                              x: Vec,
                              xn: Vec,
                              dx: Vec,
                              dtau: float,
                              top_n: int = 20) -> None:
        rhs = self._rhs_pseudo_transient(x, xn, 0*dx, dtau)
        if rhs.size == 0:
            print("[PseudoTransient] Final RHS offenders: none (empty RHS)")
            return

        if not np.all(np.isfinite(rhs)):
            bad_idx = np.where(~np.isfinite(rhs))[0]
            print(f"[PseudoTransient] Final RHS has NaN/Inf at indices: {bad_idx.tolist()}")
            return

        threshold = max(self.tol, 1e-12)
        abs_rhs = np.abs(rhs)
        offenders = np.where(abs_rhs > threshold)[0]

        if offenders.size == 0:
            print(f"[PseudoTransient] Final RHS offenders: none above threshold={threshold:.3e}")
            return

        ranked = offenders[np.argsort(-abs_rhs[offenders])]
        n_show = min(int(top_n), ranked.size)
        print(f"[PseudoTransient] Final RHS offenders (top {n_show}, threshold={threshold:.3e}):")
        for i in ranked[:n_show]:
            eq_repr = self._rhs_index_equation_repr(int(i))
            print(f"  - rhs[{int(i)}] = {rhs[int(i)]:+.6e} | {eq_repr}")

    def simulate(self, plot=True, x0: Vec | None = None):
        original_fixed_indices = list(self._fixed_var_indices)
        n_vars = self.problem.get_all_vars_number()
        if x0 is None:
            get_x0 = getattr(self.problem, "get_x0", None)
            if callable(get_x0):
                x0 = np.array(get_x0(), dtype=float, copy=True)
            else:
                x0 = np.random.rand(n_vars, dtype=float)
        else:
            x0 = np.array(x0, dtype=float, copy=True)

        if x0.size != n_vars:
            raise ValueError(f"Invalid x0 size for pseudo-transient: got {x0.size}, expected {n_vars}")

        x0 = self._apply_fixed_mask(x0, x0)


        if len(self._fixed_var_indices) > 0:
            fixed_preview = [
                f"{self._var_index_name(i)}={x0[i]:+.6e}" for i in self._fixed_var_indices[:8]
                if 0 <= i < x0.size
            ]
            self._dbg(f"fixed mask active: n_fixed={len(self._fixed_var_indices)}, x0={fixed_preview}")

        self._dbg(
            f"start: n_vars={n_vars}, n_states={self.problem.get_states_number()}, "
            f"n_algebraic={self.problem.get_algebraic_var_number()}, n_diff={self.problem.get_diff_var_number()}, "
            f"dtau0={self.dtau0:.3e}, tol={self.tol:.3e}, max_iter={self.max_iter_0}"
        )

        dtau = self.dtau0
        dtau_max = self.dtau_max
        dtau_min = self.dtau_min
        dx0 = np.zeros(self.problem.get_diff_var_number())
        dx = dx0.copy()
        y = np.tile(x0, (5, 1))
        step_idx = 0
        x_new = x0.copy()
        xn = x_new.copy()
        x_fixed_ref = x_new.copy()
        released_fixed_refs = False
        tries = 0
        
        # Update variable parameters at t=0
        self.problem.update_variable_params(0.0)

        dx_error = 1
        residual = 10
        old_residual = 10
        dtau_stall_streak = 0
        rhs_weights: np.ndarray | None = None

        # history containers
        dtau_hist = list()
        dx_error_hist = list()
        residual_hist = list()
        x_hist = list()
        dx_hist = list()
        state_eq_hist = list()

        try:
            while step_idx < self.max_iter_0:
                tries += 1
                solved = False
                run_newton_raphson = (tries % 10 == 0) or (residual > 10 * self.tol and tries > 1)
                if step_idx == 0:
                    xlast = xn
                    xn = x_new.copy()
                    dx = np.zeros(self.problem.get_diff_var_number())
                else:
                    dx = self.problem.get_dx(xn, xlast, dx0, dtau) # or 1e-3 and fixed?
                    try:
                        xlast = y[-2].copy()
                    except:
                        xlast = xn 
                    xn = y[-1].copy()

                if self.problem.get_states_number() > 0:
                    self._update_state_tau_from_derivative(self.problem.rhs_state(x_new, dx), dtau=dtau, step_idx=step_idx)
                rhs  = self._rhs_pseudo_transient(x_new, xn, dx, dtau)
                rhs2 = rhs
                if rhs_weights is None or rhs_weights.size != rhs.size:
                    rhs_weights = self._build_residual_weights(rhs.size)
                    if self.use_weighted_residual:
                        self._dbg(
                            f"weighted residual enabled: algebraic={self.weight_algebraic:.3g}"
                        )
                residual2 = self._weighted_norm(rhs2, rhs_weights)
                if not np.all(np.isfinite(rhs)):
                    bad_idx = np.where(~np.isfinite(rhs))[0]
                    bad_vals = rhs[bad_idx] if bad_idx.size > 0 else np.array([])
                    bad_eqs = [self._rhs_index_equation_repr(int(i)) for i in bad_idx]
                    bad_eq_vars = [self._rhs_index_equation_vars_debug(int(i), x_new) for i in bad_idx]
                    raise ValueError(
                        "NaN or Inf in RHS"
                        f" (step={step_idx}, try={tries}, dtau={dtau:.3e}, "
                        f"bad_idx={bad_idx.tolist()}, bad_vals={bad_vals.tolist()}, "
                        f"bad_eqs={bad_eqs}, bad_eq_vars={bad_eq_vars})"
                    )
                Jf = self._jacobian_pseudo_transient(x_new, dx, dtau)
                residual = self._weighted_norm(rhs, rhs_weights)

                # Structural guard: ensure linear solve dimensions match state vector.
                if Jf.shape[0] != rhs.size or Jf.shape[1] != x_new.size:
                    eq_preview = [self._rhs_index_equation_begin(i) for i in range(min(8, rhs.size))]
                    var_preview = [self._var_index_name(i) for i in range(min(8, x_new.size))]
                    unmatched = []
                    if Jf.shape[1] < x_new.size:
                        unmatched = [self._var_index_name(i) for i in range(Jf.shape[1], x_new.size)]
                    raise ValueError(
                        "PseudoTransient dimension mismatch before linear solve: "
                        f"J={Jf.shape}, rhs={rhs.size}, x={x_new.size}, "
                        f"n_states={self.problem.get_states_number()}, "
                        f"n_algebraic={self.problem.get_algebraic_var_number()}, "
                        f"n_vars={self.problem.get_all_vars_number()}, "
                        f"eq_preview={eq_preview}, var_preview={var_preview}, "
                        f"unmatched_var_tail={unmatched}"
                    )

                delta = self._solve_linear_system(Jf, rhs, x=x_new, context=f"pseudo step={step_idx + 1} try={tries}")

                if delta.size != x_new.size:
                    raise ValueError(
                        "PseudoTransient linear step size mismatch: "
                        f"delta={delta.size}, x={x_new.size}, J={Jf.shape}, rhs={rhs.size}"
                    )
                solved = np.all(np.isfinite(delta))

                if not solved:  # or not np.all(np.isfinite(delta)):
                    if self.verbose:
                        print(f'jacobian is {Jf.toarray()}')
                        print(f'delta is {delta}')
                        print(f'x_new is {x_new}')
                        print(f'rhs is {rhs}')
                        print(f'residual is {np.linalg.norm(rhs)} try is {tries} and step is {step_idx}')
                    raise ValueError(
                        f"Newton step failed at try {tries} and step {step_idx}: delta has NaN/Inf values with dtau {dtau}")
                dx0 = dx
                base_residual = residual
                trial_scales = (1.0, 0.5, 0.25, 0.125, 0.0625)
                best_scale = 0.0
                best_x = None
                best_residual = np.inf
                best_rhs = None
                for scale in trial_scales:
                    x_trial = x_new + scale * delta
                    x_trial = self._apply_fixed_mask(x_trial, x_fixed_ref)
                    rhs_trial = self._rhs_pseudo_transient(x_trial, xn, dx, dtau)
                    if not np.all(np.isfinite(rhs_trial)):
                        continue
                    residual_trial = self._weighted_norm(rhs_trial, rhs_weights)
                    if residual_trial < best_residual:
                        best_residual = residual_trial
                        best_scale = scale
                        best_x = x_trial
                        best_rhs = rhs_trial
                    if residual_trial <= base_residual * (1.0 - 1e-4 * scale):
                        break

                if best_x is None:
                    raise ValueError(
                        f"Line-search failed at try {tries} and step {step_idx}: no finite trial residual"
                    )

                x_new = self._apply_fixed_mask(best_x, x_fixed_ref)
                self._check_fixed_drift(x_new, x_fixed_ref, where=f"step={step_idx + 1} try={tries} accepted")
                rhs = best_rhs
                residual = best_residual
                if best_scale < 1.0:
                    self._dbg(
                        f"step damping: scale={best_scale:.2f}, residual2={base_residual:.3e}->{best_residual:.3e}"
                    )

                newton_residual = np.linalg.norm(rhs, np.inf)
                self._dbg(
                    f"step={step_idx + 1} try={tries}: residual2={residual:.3e}, "
                    f"residual_inf={newton_residual:.3e}, |delta|_2={np.linalg.norm(delta):.3e}, dtau={dtau:.3e}"
                )
                if (
                    (not released_fixed_refs)
                    and len(self._fixed_var_indices) > 0
                    and np.isfinite(newton_residual)
                    and newton_residual < self.reference_error_tol
                ):
                    released_fixed_refs = True
                    self._dbg(
                        f"releasing fixed reference mask at step={step_idx + 1} "
                        f"(residual_inf={newton_residual:.3e} < {self.reference_error_tol:.3e})"
                    )
                    self._fixed_var_indices = []

                if step_idx == 0 and tries % 10 == 1:
                    i = np.argmax(rhs)

                if solved:
                    step_idx += 1
                    tries = 0
                    y = np.roll(y, shift=-1, axis=0)
                    alpha = 1.0
                    if step_idx > 2:
                        y[-1] = alpha * x_new + (1 - alpha) * y[-1]
                    else:
                        y[-1] = x_new
                    x_new = self._apply_fixed_mask(y[-1], x_fixed_ref)
                    self._check_fixed_drift(x_new, x_fixed_ref, where=f"step={step_idx} rollout")
                    xn = x_new.copy()
                    
                    dx = self.problem.get_dx(xn, xlast, dx, dtau)
                    dx_error = np.linalg.norm(dx)
                    f_state_tau = self.problem.rhs_state(x_new, dx)
                    self._update_state_tau_from_derivative(f_state_tau, dtau=dtau, step_idx=step_idx)
                    rhs = self._rhs_pseudo_transient(x_new, xn, dx, dtau)
                    residual = self._weighted_norm(rhs, rhs_weights)

                    # save history
                    dtau_hist.append(dtau)
                    dx_error_hist.append(dx_error)
                    residual_hist.append(residual)
                    x_hist.append(x_new.copy())
                    dx_hist.append(dx.copy())
                    n_states = int(self.problem.get_states_number())
                    if n_states > 0:
                        state_eq_hist.append(rhs[:n_states].copy())

                    if residual < self.tol:
                        break

                    self._dbg(
                        f"accepted step={step_idx}: residual2={residual:.3e}, dx_error={dx_error:.3e}, dtau={dtau:.3e}"
                    )
                    eps = 1e-14
                    residual_before = float(base_residual) if np.isfinite(base_residual) else float(old_residual)
                    if not np.isfinite(residual_before) or residual_before <= 0.0:
                        residual_before = max(float(residual), eps)
                    beta_raw = (residual_before + eps) / (float(residual) + eps)
                    beta = float(np.clip(
                        beta_raw,
                        max(self.dtau_ser_min_factor, eps),
                        max(self.dtau_ser_max_factor, self.dtau_ser_min_factor),
                    ))

                    if 1.0 <= beta_raw < max(self.dtau_stall_ratio, 1.0) and residual > self.tol:
                        dtau_stall_streak += 1
                    else:
                        dtau_stall_streak = 0

                    if (
                        self.dtau_stall_steps > 0
                        and dtau_stall_streak >= self.dtau_stall_steps
                        and abs(dtau) < dtau_max
                    ):
                        beta = max(beta, max(self.dtau_stall_boost, 1.0))
                        self._dbg(
                            f"adaptive dtau stall boost: streak={dtau_stall_streak}, "
                            f"boost_beta={beta:.3e}"
                        )
                        dtau_stall_streak = 0

                    self._dbg(
                        f"adaptive dtau SER: old={dtau:.3e}, "
                        f"res_before={residual_before:.3e}, res_after={residual:.3e}, "
                        f"ratio={beta_raw:.3e}, beta={beta:.3e}"
                    )
                    dtau_prev = dtau
                    if dtau > 0:
                        dtau = min(dtau_max, max(dtau_min, dtau * beta))
                    else:
                        dtau = -min(dtau_max, max(dtau_min, -dtau * beta))

                    if abs(dtau) >= 0.999 * dtau_max:
                        self._dbg(f"adaptive dtau capped at dtau_max={dtau_max:.3e}")
                    self._dbg(f"adaptive dtau: new={dtau:.3e}")

                    old_residual = residual

                elif tries > self.max_iter_0:
                    if self.verbose:
                        print(f'delta is {delta}')
                        print(f'failed with dtau = {dtau}')
                    self._dbg(
                        f"max tries reached at step={step_idx}, dtau={dtau:.2e}, residual2={residual:.2e}; "
                        f"ending pseudo-transient loop"
                    )
                    break
        except Exception:
            self._report_failure_svd_diagnostics(
                x=x_new,
                xn=xn,
                dx=dx,
                dtau=dtau,
                context=f"failed run exception at step={step_idx} try={tries}",
            )
            if plot:
                self._plot_diagnostics(dtau_hist, dx_error_hist, residual_hist, x_hist, state_eq_hist)
            raise
        finally:
            self._fixed_var_indices = original_fixed_indices

        self._dbg(
            f"finish: steps={step_idx}, final_residual2={residual:.3e}, final_dtau={dtau:.3e}, "
            f"x_inf={np.linalg.norm(x_new, np.inf):.3e}"
        )
        if residual > self.tol:
            self._report_failure_svd_diagnostics(
                x=x_new,
                xn=xn,
                dx=dx,
                dtau=dtau,
                context=f"failed run final step={step_idx} residual={residual:.3e}",
            )
            self._report_rhs_offenders(x=x_new, xn=xn, dx=dx, dtau=dtau)

        init_guess = dict()
        for var in self._problem_state_vars() + self._problem_algebraic_vars():
            if var.uid not in self.problem.uid2idx_vars:
                continue
            idx = self.problem.uid2idx_vars[var.uid]
            if 0 <= idx < x_new.size:
                init_guess[var] = x_new[idx]

        if plot:
            self._plot_diagnostics(dtau_hist, dx_error_hist, residual_hist, x_hist, state_eq_hist)

        return x_new, init_guess
