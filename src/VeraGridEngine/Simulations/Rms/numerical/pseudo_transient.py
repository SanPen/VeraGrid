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
        self.weight_network = float(os.getenv("VERAGRID_PSEUDO_WEIGHT_NETWORK", "3.0"))
        self.weight_power = float(os.getenv("VERAGRID_PSEUDO_WEIGHT_POWER", "2.0"))
        self.fixed_var_uids = set(fixed_var_uids or [])
        uid2idx = getattr(self.problem, "uid2idx_vars", {})
        self._fixed_var_indices = sorted([uid2idx[uid] for uid in self.fixed_var_uids if uid in uid2idx])
        self.debug_check_x_new = debug_check_x_new
        self.debug_x_new_abs_max = float(debug_x_new_abs_max)
        self.t: Vec = np.empty(self.steps + 1)
        self.y: Mat = np.empty((self.steps + 1, self.problem.get_all_vars_number()))
        self._singular_report_count = 0

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

        # Prioritize key network and power-balance equations in algebraic block.
        # rhs index = n_states + algebraic_index
        for aidx in (0, 1, 4, 5):
            ridx = n_states + aidx
            if 0 <= ridx < n_rhs:
                w[ridx] = self.weight_network
        for aidx in (2, 3):
            ridx = n_states + aidx
            if 0 <= ridx < n_rhs:
                w[ridx] = max(w[ridx], self.weight_power)
        return w

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

    def _predictor_stable_algebraic_indices(self) -> list[int]:
        """
        Keep algebraic equations that do not explicitly depend on diff vars.
        Mirrors old `_algebraic_eqs_stable` idea.
        """
        algebraic_eqs = self._get_problem_algebraic_eqs()
        diff_vars = self._problem_diff_vars()
        diff_uids = {v.uid for v in diff_vars if isinstance(v, Var)}
        if len(algebraic_eqs) == 0:
            return list()
        if len(diff_uids) == 0:
            return list(range(len(algebraic_eqs)))

        stable = list()
        for i, eq in enumerate(algebraic_eqs):
            vars_in_eq = get_expression_vars(eq)
            uses_diff = any(v.base_var is not None for v in vars_in_eq)
            if not uses_diff:
                stable.append(i)

        return stable

    def _diff_free_equation_indices(self) -> list[int]:
        n_states = int(self.problem.get_states_number())
        algebraic_eqs = self._get_problem_algebraic_eqs()

        diff_vars = self._problem_diff_vars()
        diff_uids = {v.uid for v in diff_vars if isinstance(v, Var)}

        selected = list()

        for j, eq in enumerate(algebraic_eqs):
            vars_in_eq = get_expression_vars(eq)
            uses_diff = any(v.base_var is not None for v in vars_in_eq)
            if not uses_diff:
                selected.append(n_states + j)

        if self.verbose:
            self._dbg(
                f"diff-free equations: selected={len(selected)} / algebraic={len(algebraic_eqs)} "
                f"(n_states_offset={n_states})"
            )
            for rhs_idx in selected:
                self._dbg(f"  diff-free rhs[{rhs_idx}]: {self._rhs_index_equation_repr(int(rhs_idx))}")

        return selected

    def _find_initial_diff_free_feasible_point(self, x0: Vec, max_iter: int = 10) -> Vec:
        x = np.array(x0, dtype=float, copy=True)
        x_ref = np.array(x0, dtype=float, copy=True)
        dx0 = np.zeros(self.problem.get_diff_var_number(), dtype=float)

        eq_idx = self._diff_free_equation_indices()
        if len(eq_idx) == 0:
            self._dbg("diff-free init: no equations selected")
            return self._apply_fixed_mask(x, x_ref)

        n_vars = int(self.problem.get_all_vars_number())
        fixed_cols = set(self._fixed_var_indices)

        # Temporary initialization pins to break near-nullspace directions.
        # This is local to this method (unpins automatically when we return).
        # Prefer reference-like variables (Pref, Vref), then fallback options.
        pin_priority_groups = (
            ("Pm_ref", "Pref", "P_ref"),
            ("UsRefPu", "Vref", "V_ref", "U_ref"),
            ("u_gov1", "dt_1_y_gov1"),
        )
        pinned_indices = list()
        for group in pin_priority_groups:
            pin_idx = None
            for i in range(n_vars):
                if i in fixed_cols:
                    continue
                nm = self._var_index_name(i)
                if any(tok in nm for tok in group):
                    pin_idx = i
                    break
            if pin_idx is not None:
                fixed_cols.add(pin_idx)
                pinned_indices.append(pin_idx)

        if len(pinned_indices) > 0:
            labels = [f"{i}:{self._var_index_name(i)}" for i in pinned_indices]
            self._dbg(f"diff-free init: temporary pins enabled: {labels}")
        else:
            self._dbg("diff-free init: temporary pins not found (Pref/Vref groups)")

        free_cols = [i for i in range(n_vars) if i not in fixed_cols]
        if len(free_cols) == 0:
            self._dbg("diff-free init: no free variables")
            return self._apply_fixed_mask(x, x_ref)

        tol_proj = max(self.tol * 10.0, 1e-8)
        converged = False

        rhs0 = self._rhs_steady(x, dx0)
        if rhs0.size > 0 and np.all(np.isfinite(rhs0)):
            r0 = rhs0[eq_idx]
            r0_inf = float(np.linalg.norm(r0, np.inf)) if r0.size > 0 else 0.0
            self._dbg(
                f"diff-free init start: n_eq={len(eq_idx)}, n_free={len(free_cols)}, residual_inf={r0_inf:.3e}"
            )

        for k in range(max_iter):
            rhs_full = self._rhs_steady(x, dx0)
            if rhs_full.size == 0 or not np.all(np.isfinite(rhs_full)):
                self._dbg(f"diff-free init abort: non-finite rhs at iter={k + 1}")
                break

            r = rhs_full[eq_idx]
            r_inf = float(np.linalg.norm(r, np.inf)) if r.size > 0 else 0.0
            if r_inf <= tol_proj:
                self._dbg(f"diff-free init converged at iter={k + 1}, residual_inf={r_inf:.3e}")
                converged = True
                break

            J_full = self._jacobian_steady(x, dx0).tocsc()
            J_sel = J_full[eq_idx, :][:, free_cols]

            delta_free, *_ = spla.lsqr(
                J_sel,
                -r,
                atol=1e-10,
                btol=1e-10,
                iter_lim=max(200, 2 * len(free_cols))
            )
            delta_free = np.asarray(delta_free, dtype=float)
            if delta_free.size != len(free_cols) or not np.all(np.isfinite(delta_free)):
                self._report_singularity_diagnostics(J_sel.tocsc(), r, x=x, context=f"diff-free init iter={k + 1}")
                self._dbg(f"diff-free init abort: invalid correction at iter={k + 1}")
                break

            best_x = None
            best_r = np.inf
            accepted_alpha = 1.0
            tie_tol = max(1e-12, 1e-10 * max(1.0, r_inf))
            for alpha in (1.0, 0.5, 0.25, 0.1):
                xt = np.array(x, copy=True)
                xt[np.array(free_cols, dtype=int)] += alpha * delta_free
                xt = self._apply_fixed_mask(xt, x_ref)

                rt_full = self._rhs_steady(xt, dx0)
                if not np.all(np.isfinite(rt_full)):
                    continue
                rt = rt_full[eq_idx]
                rt_inf = float(np.linalg.norm(rt, np.inf)) if rt.size > 0 else 0.0

                if best_x is None:
                    best_x = xt
                    best_r = rt_inf
                    accepted_alpha = alpha
                    if rt_inf <= r_inf * (1.0 - 1e-4 * alpha):
                        break
                    continue

                if rt_inf < best_r:
                    best_r = rt_inf
                    best_x = xt
                    accepted_alpha = alpha
                elif abs(rt_inf - best_r) <= tie_tol and alpha > accepted_alpha:
                    # Allow movement along flat/null directions when residual is unchanged.
                    best_x = xt
                    accepted_alpha = alpha
                if rt_inf <= r_inf * (1.0 - 1e-4 * alpha):
                    break

            if best_x is None:
                # No finite trial point; fall back to full step update.
                best_x = np.array(x, copy=True)
                best_x[np.array(free_cols, dtype=int)] += delta_free
                best_x = self._apply_fixed_mask(best_x, x_ref)
                best_r = r_inf
                accepted_alpha = 1.0

            x = best_x
            self._dbg(
                f"diff-free init iter={k + 1}: residual_inf={r_inf:.3e}->{best_r:.3e}, "
                f"|delta|_2={np.linalg.norm(delta_free):.3e}, alpha={accepted_alpha:.2f}"
            )

        rhsf = self._rhs_steady(x, dx0)
        if rhsf.size > 0 and np.all(np.isfinite(rhsf)):
            rf = rhsf[eq_idx]
            rf_inf = float(np.linalg.norm(rf, np.inf)) if rf.size > 0 else 0.0
            self._dbg(f"diff-free init finish: residual_inf={rf_inf:.3e}")

            if not converged and rf_inf > tol_proj:
                abs_rf = np.abs(rf)
                ranked_local = np.argsort(-abs_rf)
                n_show = min(20, ranked_local.size)
                self._dbg(
                    f"diff-free init failed: top {n_show} residual equations "
                    f"(threshold={tol_proj:.3e})"
                )
                for kk in ranked_local[:n_show]:
                    rhs_idx = int(eq_idx[int(kk)])
                    val = float(rf[int(kk)])
                    self._dbg(f"  rhs[{rhs_idx}]={val:+.6e} | {self._rhs_index_equation_repr(rhs_idx)}")

        return self._apply_fixed_mask(x, x_ref)

    def _predictor_project_initial_guess(self, x0: Vec) -> Vec:
        n_states = int(self.problem.get_states_number())
        n_alg = int(self.problem.get_algebraic_var_number())
        if n_alg == 0:
            return x0

        x_proj = np.array(x0, dtype=float, copy=True)
        dx_proj = np.zeros(self.problem.get_diff_var_number(), dtype=float)
        proj_tol = max(self.tol * 10.0, 1e-8)

        stable_idx = self._predictor_stable_algebraic_indices()
        if len(stable_idx) == 0:
            stable_idx = list(range(n_alg))
        self._dbg(f"predictor setup: n_alg={n_alg}, n_stable={len(stable_idx)}")

        for k in range(8):
            r_alg_full = self.problem.rhs_algebraic(x_proj, dx_proj)
            if r_alg_full.size == 0:
                break
            if not np.all(np.isfinite(r_alg_full)):
                self._dbg(f"predictor abort: non-finite algebraic rhs at iter={k + 1}")
                break

            r_alg = r_alg_full[stable_idx]
            rinf = float(np.linalg.norm(r_alg, np.inf)) if r_alg.size > 0 else 0.0
            if rinf <= proj_tol:
                self._dbg(f"predictor converged at iter={k + 1}, residual_inf={rinf:.3e}")
                break

            J22_full = self.problem.get_j22(x_proj, dx_proj, max(abs(self.dtau0), 1e-6)).tocsc()
            Jp = J22_full[stable_idx, :]

            # Predictor Jacobian is generally rectangular on reduced stable set.
            delta_alg, *_ = spla.lsqr(Jp, -r_alg, atol=1e-10, btol=1e-10, iter_lim=max(200, 2 * n_alg))
            delta_alg = np.asarray(delta_alg, dtype=float)
            if delta_alg.size != n_alg or not np.all(np.isfinite(delta_alg)):
                self._report_singularity_diagnostics(Jp.tocsc(), r_alg, x=x_proj, context=f"predictor iter={k + 1}")
                self._dbg(
                    f"predictor abort: invalid correction at iter={k + 1}, "
                    f"delta_size={delta_alg.size}, n_alg={n_alg}"
                )
                break

            best_x = x_proj
            best_rinf = rinf
            for alpha in (1.0, 0.5, 0.25, 0.1):
                xt = np.array(x_proj, copy=True)
                xt[n_states:n_states + n_alg] += alpha * delta_alg
                rt_full = self.problem.rhs_algebraic(xt, dx_proj)
                if not np.all(np.isfinite(rt_full)):
                    continue
                rt = rt_full[stable_idx]
                rt_inf = float(np.linalg.norm(rt, np.inf)) if rt.size > 0 else 0.0
                if rt_inf < best_rinf:
                    best_rinf = rt_inf
                    best_x = xt
                if rt_inf <= rinf * (1.0 - 1e-4 * alpha):
                    break

            x_proj = best_x
            self._dbg(
                f"predictor iter={k + 1}: residual_inf={rinf:.3e}->{best_rinf:.3e}, "
                f"|delta_alg|_2={np.linalg.norm(delta_alg):.3e}"
            )

        return self._apply_fixed_mask(x_proj, x0)

    def _project_feasible_x(self, x: Vec, dx: Vec, x_ref: Vec | None = None, max_iter: int = 4) -> Vec:
        n_states = int(self.problem.get_states_number())
        n_alg = int(self.problem.get_algebraic_var_number())
        if n_alg == 0:
            return np.array(x, dtype=float, copy=True)

        x_proj = np.array(x, dtype=float, copy=True)
        if x_ref is None:
            x_ref = x_proj

        stable_idx = self._predictor_stable_algebraic_indices()
        if len(stable_idx) == 0:
            stable_idx = list(range(n_alg))

        proj_tol = max(self.tol * 5.0, 1e-8)
        dt_jac = max(abs(self.dtau0), 1e-6)
        # Feasibility projection is based on algebraic/stability equations,
        # so derivative terms are neutralized.
        dx_feasible = np.zeros_like(dx)

        for _ in range(max_iter):
            rhs_alg_full = self.problem.rhs_algebraic(x_proj, dx_feasible)
            if rhs_alg_full.size == 0 or not np.all(np.isfinite(rhs_alg_full)):
                break

            rhs_alg = rhs_alg_full[stable_idx]
            residual_inf = float(np.linalg.norm(rhs_alg, np.inf)) if rhs_alg.size > 0 else 0.0
            if residual_inf <= proj_tol:
                break

            J22_full = self.problem.get_j22(x_proj, dx_feasible, dt_jac).tocsc()
            J_proj = J22_full[stable_idx, :]

            delta_alg, *_ = spla.lsqr(J_proj, -rhs_alg, atol=1e-10, btol=1e-10, iter_lim=max(200, 2 * n_alg))
            delta_alg = np.asarray(delta_alg, dtype=float)
            if delta_alg.size != n_alg or not np.all(np.isfinite(delta_alg)):
                break

            best_x = x_proj
            best_residual = residual_inf
            for alpha in (1.0, 0.5, 0.25, 0.1):
                xt = np.array(x_proj, copy=True)
                xt[n_states:n_states + n_alg] += alpha * delta_alg
                xt = self._apply_fixed_mask(xt, x_ref)

                rt_full = self.problem.rhs_algebraic(xt, dx_feasible)
                if not np.all(np.isfinite(rt_full)):
                    continue

                rt = rt_full[stable_idx]
                rt_inf = float(np.linalg.norm(rt, np.inf)) if rt.size > 0 else 0.0
                if rt_inf < best_residual:
                    best_residual = rt_inf
                    best_x = xt
                if rt_inf <= residual_inf * (1.0 - 1e-4 * alpha):
                    break

            x_proj = best_x

        return self._apply_fixed_mask(x_proj, x_ref)

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

    def _report_key_equation_tracking(self, rhs: Vec, x_new: Vec, x_prev: Vec, tag: str) -> None:
        if rhs.size == 0 or x_new.size == 0 or x_prev.size == 0:
            return
        n_states = int(self.problem.get_states_number())
        key_alg = (0, 1, 2, 3, 4, 5, 14)
        entries: list[str] = []
        for aidx in key_alg:
            ridx = n_states + aidx
            if 0 <= ridx < rhs.size:
                entries.append(f"rhs[{ridx}]={rhs[ridx]:+.3e} (alg[{aidx}])")
        if entries:
            print(f"[PseudoTransient][Track] {tag} key equations: {entries}", file=sys.stderr)

        watch_tokens = (
            "deltaGen",
            "omegaGen",
            "VdGen",
            "VqGen",
            "IdGen",
            "IqGen",
            "Psid_prime",
            "Psiq_prime",
            "Eq_prime",
            "Ed_prime",
            "SaGen",
            "Psi_ag",
        )
        vars_all = self._problem_state_vars() + self._problem_algebraic_vars()
        deltas: list[str] = []
        used = set()
        for tok in watch_tokens:
            tok_l = tok.lower()
            hit = None
            for i, var in enumerate(vars_all):
                nm = (getattr(var, "name", "") or "").lower()
                if i in used:
                    continue
                if tok_l in nm:
                    hit = i
                    break
            if hit is None or hit >= x_new.size or hit >= x_prev.size:
                continue
            used.add(hit)
            dv = float(x_new[hit] - x_prev[hit])
            if abs(dv) > 0.0:
                name = getattr(vars_all[hit], "name", f"x[{hit}]")
                deltas.append(f"{name}: dx={dv:+.3e}")
        if deltas:
            print(f"[PseudoTransient][Track] {tag} variable deltas: {deltas}", file=sys.stderr)

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
            I = sp.eye(m=n_states, n=n_states, format="csc")
            j11 = ((1.0 / h) * I - j_full[:n_states, :n_states]).tocsc()
            j12 = (-j_full[:n_states, n_states:n_states + n_alg]).tocsc()
            j21 = j_full[n_states:n_states + n_alg, :n_states].tocsc()
            j22 = j_full[n_states:n_states + n_alg, n_states:n_states + n_alg].tocsc()
            return pack_4_by_4_scipy(j11, j12, j21, j22)

        j11_val: csc_matrix = self.problem.get_j11(x, dx, h)
        j12_val: csc_matrix = self.problem.get_j12(x, dx, h)
        j21_val: csc_matrix = self.problem.get_j21(x, dx, h)
        j22_val: csc_matrix = self.problem.get_j22(x, dx, h)

        I = sp.eye(m=n_states, n=n_states, format="csc")
        j11 = ((1.0 / h) * I - j11_val).tocsc()
        j12 = (-j12_val).tocsc()
        j21 = j21_val.tocsc()
        j22 = j22_val.tocsc()

        return pack_4_by_4_scipy(j11, j12, j21, j22)

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
        n = int(J.shape[0])
        if n == 0:
            return np.array([], dtype=float)

        reg_scales = (0.0, 1e-10, 1e-8, 1e-6)
        I = sp.eye(n, format="csc")

        for reg in reg_scales:
            J_eff = J if reg == 0.0 else (J + reg * I)

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Matrix is exactly singular")
                try:
                    delta = spla.spsolve(J_eff, -rhs)
                except Exception:
                    delta = np.full(rhs.shape, np.nan, dtype=float)

            if np.all(np.isfinite(delta)):
                if reg > 0.0:
                    self._dbg(f"{context}: solved with regularization={reg:.1e}")
                return np.asarray(delta, dtype=float)

            if reg == 0.0:
                self._report_singularity_diagnostics(J, rhs, x=x, context=context)

            damp = reg if reg > 0.0 else 0.0
            delta, *_ = spla.lsqr(J_eff, -rhs, damp=damp, atol=1e-10, btol=1e-10, iter_lim=max(200, 2 * n))


            if np.all(np.isfinite(delta)):
                if reg > 0.0:
                    self._dbg(f"{context}: lsqr solved with regularization={reg:.1e}")
                else:
                    self._dbg(f"{context}: lsqr fallback used")
                return np.asarray(delta, dtype=float)

        self._dbg(f"{context}: failed to solve linear system")
        return np.full(rhs.shape, np.nan, dtype=float)

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

            trial_scales = (1.0, 0.5, 0.25, 0.1)
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
        f_algeb = self.problem.rhs_algebraic(x,  dx)
        h = 1e9
        if self.problem.get_states_number() > 0:
            f_state = self.problem.rhs_state(x, dx)
            f_state_update = (x[:self.problem.get_states_number()] - xn[:self.problem.get_states_number()]) / h - f_state
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

        x0 = self._find_initial_diff_free_feasible_point(x0, max_iter=20)
        #x0 = self._predictor_project_initial_guess(x0)
        #x0 = self._apply_fixed_mask(x0, x0)

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
        y = np.tile(x0, (5, 1))
        step_idx = 0
        x_new = x0.copy()
        xn = x0.copy()
        x_fixed_ref = x0.copy()
        released_fixed_refs = False
        tries = 0
        
        # Update variable parameters at t=0
        self.problem.update_variable_params(0.0)

        dx_error = 1
        residual = 10
        old_residual = 10
        good_step_streak = 0
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

                rhs  = self._rhs_pseudo_transient(x_new, xn, 0 * dx, dtau)
                rhs2 = self._rhs_pseudo_transient(x_new, xn, dx, dtau)
                if rhs_weights is None or rhs_weights.size != rhs.size:
                    rhs_weights = self._build_residual_weights(rhs.size)
                    if self.use_weighted_residual:
                        self._dbg(
                            f"weighted residual enabled: network={self.weight_network:.3g}, "
                            f"power={self.weight_power:.3g}"
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
                delta = self._solve_linear_system(Jf, rhs, x=x_new, context=f"pseudo step={step_idx + 1} try={tries}")
                n_states = int(self.problem.get_states_number())
                g = rhs[n_states:]
                Jg = Jf[n_states:, :]

                alg_lin_res = Jg @ delta + g

                print(
                    "[PseudoTransient diagnostics] algebraic linear solve check: "
                    f"|g|_inf={np.linalg.norm(g, np.inf):.6e}, "
                    f"|Jg*delta+g|_inf={np.linalg.norm(alg_lin_res, np.inf):.6e}"
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
                trial_scales = (1.0, 0.5, 0.25, 0.1, 0.05)
                best_scale = 0.0
                best_x = None
                best_residual = np.inf
                best_rhs = None
                for scale in trial_scales:
                    x_trial = x_new + scale * delta
                    x_trial = self._apply_fixed_mask(x_trial, x_fixed_ref)
                    rhs_trial = self._rhs_pseudo_transient(x_trial, xn, 0 * dx, dtau)
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
                if self.verbose:
                    self._report_key_equation_tracking(rhs, x_new, xn, tag=f"step={step_idx + 1} try={tries}")

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
                    avg_residual = 0.8 * old_residual + 0.2 * residual
                    ratio = (avg_residual + eps) / (residual + eps)

                    # Hysteresis prevents 2x/0.5x ping-pong when ratio hovers near 1.
                    if ratio > 1.20:
                        beta = 1.35
                    elif ratio > 1.05:
                        beta = 1.15
                    elif ratio < 0.80:
                        beta = 0.70
                    elif ratio < 0.95:
                        beta = 0.87
                    else:
                        beta = 1.0

                    # If progress is consistently good, force a gentle dtau ramp-up.
                    # This avoids stalling when ratio remains near 1 due to smoothing.
                    good_step = (residual < 0.995 * old_residual) and (best_scale >= 0.25)
                    if good_step:
                        good_step_streak += 1
                    else:
                        good_step_streak = 0

                    if good_step_streak >= 3 and residual > self.tol:
                        beta = max(beta, 1.20)
                        self._dbg(
                            f"adaptive dtau boost: streak={good_step_streak}, "
                            f"best_scale={best_scale:.2f}, forced_beta={beta:.3e}"
                        )
                        good_step_streak = 0

                    self._dbg(f"adaptive dtau: old={dtau:.3e}, beta={beta:.3e}")
                    dtau_prev = dtau
                    if dtau > 0:
                        dtau = min(dtau_max, max(dtau_min, dtau * beta))
                    else:
                        dtau = -min(dtau_max, max(dtau_min, -dtau * beta))

                    if np.isclose(dtau, dtau_prev, rtol=1e-12, atol=1e-15):
                        dtau_stall_streak += 1
                    else:
                        dtau_stall_streak = 0

                    abs_dtau_prev = abs(dtau_prev)
                    if (
                        dtau_stall_streak >= 3
                        and abs_dtau_prev < 0.999 * dtau_max
                        and residual > self.tol
                        and best_scale >= 0.25
                    ):
                        forced = min(dtau_max, max(dtau_min, abs_dtau_prev * 1.25))
                        dtau = forced if dtau_prev >= 0 else -forced
                        self._dbg(
                            f"adaptive dtau anti-stall: streak={dtau_stall_streak}, "
                            f"best_scale={best_scale:.2f}, forced_dtau={dtau:.3e}"
                        )
                        dtau_stall_streak = 0

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
            if plot:
                self._plot_diagnostics(dtau_hist, dx_error_hist, residual_hist, x_hist, state_eq_hist)
            raise
        finally:
            self._fixed_var_indices = original_fixed_indices

        self._dbg(
            f"finish: steps={step_idx}, final_residual2={residual:.3e}, final_dtau={dtau:.3e}, "
            f"x_inf={np.linalg.norm(x_new, np.inf):.3e}"
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
