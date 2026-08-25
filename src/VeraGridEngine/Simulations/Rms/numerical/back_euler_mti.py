# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import os
from itertools import product
import warnings
import time

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import MatrixRankWarning
from scipy.optimize import least_squares

from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.basic_structures import Mat, Vec
from VeraGridEngine.Utils.Symbolic.symbolic import get_expression_vars

try:
    from VeraGridEngine.Simulations.Rms.problems.rms_problem_MTI import RmsProblemMTI
except ImportError:  # pragma: no cover - keeps the solver usable without RMS imports in EMT-only contexts.
    RmsProblemMTI = object


class BackEulerImplicitIntegrationMTI(BackEulerImplicitIntegration):
    """
    Backward Euler variant with MTI inequality/mode checks.

    This solver keeps the same Newton/Jacobian structure as
    ``BackEulerImplicitIntegration`` and adds a post-Newton MTI feasibility
    gate based on inequality residuals ``G <= tol``.
    """

    def __init__(
        self,
        problem: RmsProblemMTI,
        t0: float,
        t_end: float,
        h: float,
        max_iter: int,
        tolerance: float = 1e-7,
        inequality_tolerance: float = 1e-9,
    ):
        super().__init__(
            problem=problem,
            t0=t0,
            t_end=t_end,
            h=h,
            max_iter=max_iter,
            tolerance=tolerance,
        )
        self.problem: RmsProblemMTI = problem
        self.inequality_tolerance = inequality_tolerance
        self.z: Mat = np.empty((self.steps + 1, 0), dtype=float)
        self.debug = os.getenv("RMS_MTI_DEBUG", "0").strip() in ("1", "true", "True", "yes", "on")
        self.debug_solve = os.getenv("RMS_MTI_DEBUG_SOLVE", "0").strip() in ("1", "true", "True", "yes", "on")
        self.debug_newton = os.getenv("RMS_MTI_DEBUG_NEWTON", "0").strip() in ("1", "true", "True", "yes", "on")
        self.debug_residuals = os.getenv("RMS_MTI_DEBUG_RESIDUALS", "0").strip() in ("1", "true", "True", "yes", "on")
        self.compare = os.getenv("RMS_MTI_COMPARE", "0").strip() in ("1", "true", "True", "yes", "on")
        self.iteration_summary = os.getenv("RMS_MTI_ITER_SUMMARY", "0").strip() in ("1", "true", "True", "yes", "on")
        self._iteration_stats: dict[str, int] = {}
        try:
            # 0 means: no candidate cap (toolbox-like all-candidates check)
            self.debug_max_cands = int(os.getenv("RMS_MTI_DEBUG_MAX_CANDS", "0"))
        except Exception:
            self.debug_max_cands = 0
        self.polish_candidates = os.getenv("RMS_MTI_POLISH_CANDIDATES", "0").strip() in (
            "1", "true", "True", "yes", "on"
        )
        self.use_nonlinear_subproblem_lsq = os.getenv("RMS_MTI_NONLINEAR_SUBPROBLEM_LSQ", "0").strip() in (
            "1", "true", "True", "yes", "on"
        )
        self.use_direct_xp_subproblem = os.getenv("RMS_MTI_DIRECT_XP_SOLVE", "0").strip() in (
            "1", "true", "True", "yes", "on"
        )
        self.use_subproblem_line_search = os.getenv("RMS_MTI_SUBPROBLEM_LINE_SEARCH", "0").strip() in (
            "1", "true", "True", "yes", "on"
        )
        self.use_full_fixed_z_mti_rows = os.getenv("RMS_MTI_FULL_FIXED_Z_ROWS", "0").strip() in (
            "1", "true", "True", "yes", "on"
        )
        self._debug_x0_ref: Vec | None = None
        self._debug_first_eval_done = False
        self._last_subproblem_fail_reason = "solve_fail"
        self._last_subproblem_context = ""
        self._debug_subproblem_label_prints = 0
        self.mti_newton_tol = max(self.tol, float(os.getenv("RMS_MTI_NEWTON_TOL", "1e-6")))
        try:
            self.mti_solve_tol = self.mti_newton_tol * max(1.0, float(os.getenv("RMS_MTI_SOLVE_TOL_FACTOR", "200.0")))
        except Exception:
            self.mti_solve_tol = 200.0 * self.mti_newton_tol
        try:
            default_mti_max_iter = max(int(self.max_iter_0), 300)
            self.mti_max_iter = max(default_mti_max_iter, int(os.getenv("RMS_MTI_MAX_ITER", str(default_mti_max_iter))))
        except Exception:
            self.mti_max_iter = max(int(self.max_iter_0), 300)
        try:
            self.mti_lsqr_iter_lim = max(1, int(os.getenv("RMS_MTI_LSQR_ITER", "100")))
        except Exception:
            self.mti_lsqr_iter_lim = 100
        try:
            self.event_bisect_iter = max(1, int(os.getenv("RMS_MTI_EVENT_BISECT_ITER", "20")))
        except Exception:
            self.event_bisect_iter = 20

    def _count_iteration_stat(self, name: str, amount: int = 1) -> None:
        if self.iteration_summary:
            self._iteration_stats[name] = self._iteration_stats.get(name, 0) + int(amount)

    def _runtime_parameter_values(self) -> Vec | None:
        """Return the problem runtime-parameter vector for RMS or EMT problems."""
        if hasattr(self.problem, "_variable_parameters_values"):
            return getattr(self.problem, "_variable_parameters_values")
        if hasattr(self.problem, "_event_params_values"):
            return getattr(self.problem, "_event_params_values")
        if hasattr(self.problem, "event_params_values"):
            return getattr(self.problem, "event_params_values")
        return None

    def _constant_parameter_values(self) -> Vec | None:
        """Return the problem static-parameter vector for RMS or EMT problems."""
        if hasattr(self.problem, "_constant_params"):
            return getattr(self.problem, "_constant_params")
        if hasattr(self.problem, "_constant_params_values"):
            return getattr(self.problem, "_constant_params_values")
        if hasattr(self.problem, "get_parameters_values"):
            try:
                return np.asarray([float(c.value) for c in self.problem.get_parameters_values()], dtype=float)
            except Exception:
                return None
        return None

    def _update_problem_boundary(self, t_curr: float, x_snapshot: Vec) -> None:
        """Call the RMS or EMT boundary update hook with the active runtime vector."""
        runtime_params = self._runtime_parameter_values()
        if runtime_params is None:
            return

        # EMT boundary updaters operate on the full parameter vector, while RMS
        # problem hooks operate directly on runtime parameters. Prefer the EMT
        # full-vector contract when static parameters are available and persist
        # the updated runtime slice back into the active MTI parameter vector.
        try:
            constant_params = self._constant_parameter_values()
            if constant_params is None:
                self.problem.update(t_curr, x_snapshot, runtime_params)
            else:
                full_params = np.concatenate(
                    (
                        np.asarray(runtime_params, dtype=float),
                        np.asarray(constant_params, dtype=float),
                    )
                )
                self.problem.update(t_curr, x_snapshot, full_params)
                runtime_params[:] = full_params[: len(runtime_params)]
        except Exception:
            return

    def _get_boolean_state_from_problem(self, bool_indices: list[int]) -> Vec | None:
        """Read boolean values from the active runtime vector."""
        runtime_params = self._runtime_parameter_values()
        if runtime_params is None:
            return None
        out = np.zeros(len(bool_indices), dtype=float)
        for k, idx in enumerate(bool_indices):
            out[k] = float(runtime_params[int(idx)])
        return out

    def _rhs_implicit(self, x: Vec, dx: Vec, xn: Vec, h: float) -> Vec:
        """Prefer a problem-provided MTI equality residual, otherwise use the RMS base residual."""
        if hasattr(self.problem, "compute_mti_equalities"):
            return np.asarray(self.problem.compute_mti_equalities(x, dx, xn, h), dtype=float)
        return super()._rhs_implicit(x=x, dx=dx, xn=xn, h=h)

    def _jacobian_implicit(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Prefer a full MTI Jacobian hook, otherwise use the RMS block Jacobian path."""
        self._count_iteration_stat("full_jacobian_builds")
        jac_fn = getattr(self.problem, "jacobian_mti_equalities", None)
        if jac_fn is not None:
            jac = jac_fn(x, dx, h)
            return jac.tocsc() if sp.issparse(jac) else sp.csc_matrix(jac)
        return super()._jacobian_implicit(x=x, dx=dx, h=h)

    def _debug_print_top_residuals(
        self,
        rhs: Vec,
        top_k: int = 10,
        tag: str = "",
        x_eval: Vec | None = None,
        dx_eval: Vec | None = None,
    ) -> None:
        if top_k <= 0:
            return
        if not self.debug:
            return
        arr = np.asarray(rhs, dtype=float)
        if arr.size == 0:
            return
        n_state = int(self.problem.get_states_number())
        x_bind = np.asarray(self.y[0], dtype=float) if x_eval is None else np.asarray(x_eval, dtype=float)
        dx_bind = np.zeros(self.problem.get_diff_var_number(), dtype=float) if dx_eval is None else np.asarray(dx_eval, dtype=float)
        state_eqs = getattr(self.problem, "_state_eqs", [])
        algeb_eqs = getattr(self.problem, "_algebraic_eqs", [])

        def _eq_text(i: int) -> str:
            try:
                if i < n_state:
                    if i < len(state_eqs):
                        return f"state_update[{i}] from f_state: {state_eqs[i]}"
                    return f"state_update[{i}]"
                j = i - n_state
                if j < len(algeb_eqs):
                    return f"algeb[{j}]: {algeb_eqs[j]}"
                return f"algeb[{j}]"
            except Exception:
                return "<eq unavailable>"

        order = np.argsort(np.abs(arr), kind="stable")[::-1]
        k = min(top_k, arr.size)
        print(f"[MTI-RHS] {tag} top {k} residual entries (idx: value):")
        for i in order[:k]:
            ii = int(i)
            print(f"  {ii}: {arr[ii]:+.6e}")
            print(f"     eq: {_eq_text(ii)}")

            # Binding sanity check: compare compiled residual entry vs direct
            # symbolic eval with current uid bindings.
            try:
                if ii >= n_state:
                    j = ii - n_state
                    if 0 <= j < len(algeb_eqs):
                        eq = algeb_eqs[j]
                        uid_bindings: dict[int, float] = {}
                        for vr in get_expression_vars(eq):
                            v_idx = self.problem.uid2idx_vars.get(vr.uid, None)
                            if v_idx is not None:
                                uid_bindings[vr.uid] = float(x_bind[v_idx])
                                continue
                            d_idx = self.problem._uid2idx_diff.get(vr.uid, None)
                            if d_idx is not None:
                                uid_bindings[vr.uid] = float(dx_bind[d_idx])
                                continue
                            p_idx = self.problem._uid2idx_params.get(vr.uid, None)
                            if p_idx is not None:
                                constant_params = self._constant_parameter_values()
                                if constant_params is not None:
                                    uid_bindings[vr.uid] = float(constant_params[p_idx])
                                continue
                            e_idx = self.problem._uid2idx_event_params.get(vr.uid, None)
                            if e_idx is not None:
                                runtime_params = self._runtime_parameter_values()
                                if runtime_params is not None:
                                    uid_bindings[vr.uid] = float(runtime_params[e_idx])
                        sym_val = float(eq.eval_uid(uid_bindings))
                        print(f"     compiled={arr[ii]:+.6e} symbolic={sym_val:+.6e} diff={(arr[ii]-sym_val):+.6e}")

                        vars_preview = []
                        for vr in get_expression_vars(eq):
                            v_idx = self.problem.uid2idx_vars.get(vr.uid, None)
                            if v_idx is not None:
                                vars_preview.append(f"{vr.name}=vars[{v_idx}]={x_bind[v_idx]:+.3e}")
                                continue
                            d_idx = self.problem._uid2idx_diff.get(vr.uid, None)
                            if d_idx is not None:
                                vars_preview.append(f"{vr.name}=diff[{d_idx}]={dx_bind[d_idx]:+.3e}")
                                continue
                            p_idx = self.problem._uid2idx_params.get(vr.uid, None)
                            if p_idx is not None:
                                constant_params = self._constant_parameter_values()
                                if constant_params is not None:
                                    vars_preview.append(f"{vr.name}=cprms[{p_idx}]={constant_params[p_idx]:+.3e}")
                                continue
                            e_idx = self.problem._uid2idx_event_params.get(vr.uid, None)
                            if e_idx is not None:
                                runtime_params = self._runtime_parameter_values()
                                if runtime_params is not None:
                                    vars_preview.append(f"{vr.name}=vprms[{e_idx}]={runtime_params[e_idx]:+.3e}")
                        if len(vars_preview) > 0:
                            print("     bindings: " + ", ".join(vars_preview[:12]))
            except Exception as ex:
                print(f"     symbolic-check-failed: {ex}")

    def _newton_step(
        self,
        x_new: Vec,
        x_prev: Vec,
        dx: Vec,
        h_eff: float,
        rhs: Vec | None = None,
        residual: float | None = None,
    ) -> tuple[Vec, float]:
        if rhs is None:
            rhs = self.problem.compute_mti_equalities(x_new, dx, x_prev, h_eff)
        if rhs.size == 0:
            return x_new, 0.0
        if not np.all(np.isfinite(rhs)):
            return x_new, np.inf
        if residual is None:
            residual = float(np.linalg.norm(rhs, np.inf))
        if residual < self.tol:
            return x_new, residual

        jf = self._jacobian_implicit(x_new, dx, h_eff)
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("error", category=MatrixRankWarning)
                delta = sp.linalg.spsolve(jf, -rhs)
        except (MatrixRankWarning, RuntimeError, ValueError):
            delta = np.full_like(x_new, np.nan, dtype=float)
        if not np.all(np.isfinite(delta)):
            delta, *_ = sp.linalg.lsqr(jf, -rhs, iter_lim=self.mti_lsqr_iter_lim, atol=self.mti_solve_tol, btol=self.mti_solve_tol)
        if not np.all(np.isfinite(delta)):
            return x_new, np.inf

        x_next = x_new + delta
        if not np.all(np.isfinite(x_next)):
            return x_new, np.inf
        return x_next, residual

    def _solve_continuous_for_fixed_boolean(
        self,
        x_seed: Vec,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        force_zero_dx: bool = False,
    ) -> tuple[bool, Vec, Vec, float]:
        x_new = x_seed.copy()
        residual = np.inf
        dx_out = dx_last.copy()

        for it in range(int(self.mti_max_iter)):
            self._count_iteration_stat("continuous_fixed_z_iterations")
            it_t0 = time.perf_counter()
            if force_zero_dx:
                dx = np.zeros_like(dx_last)
            else:
                dx = self.problem.get_dx(x_new, x_prev, dx_last, h_eff)

            if self.debug and not self._debug_first_eval_done and self._debug_x0_ref is not None:
                x0_ref = np.asarray(self._debug_x0_ref, dtype=float)
                xnew_arr = np.asarray(x_new, dtype=float)
                xprev_arr = np.asarray(x_prev, dtype=float)
                d_xnew_x0 = float(np.linalg.norm(xnew_arr - x0_ref, np.inf)) if xnew_arr.size == x0_ref.size else np.inf
                d_xprev_x0 = float(np.linalg.norm(xprev_arr - x0_ref, np.inf)) if xprev_arr.size == x0_ref.size else np.inf
                d_xnew_xprev = float(np.linalg.norm(xnew_arr - xprev_arr, np.inf)) if xnew_arr.size == xprev_arr.size else np.inf
                print(
                    "[INIT-CHECK-STEP0] first compute_mti_equalities input "
                    f"||x_new-x0||inf={d_xnew_x0:.6e} "
                    f"||x_prev-x0||inf={d_xprev_x0:.6e} "
                    f"||x_new-x_prev||inf={d_xnew_xprev:.6e}"
                )
                self._debug_first_eval_done = True

            rhs = self.problem.compute_mti_equalities(x_new, dx, x_prev, h_eff)
            residual = float(np.linalg.norm(rhs, np.inf)) if rhs.size > 0 else 0.0
            if self.debug_newton:
                it_ms = (time.perf_counter() - it_t0) * 1e3
                print(f"[MTI-NEWTON] it={it + 1}/{self.mti_max_iter} res={residual:.6e} iter_ms={it_ms:.3f}")

            if self.debug_residuals and residual >= max(self.tol, 1e-6):
                self._debug_print_top_residuals(rhs, top_k=12, tag="fixed-z", x_eval=x_new, dx_eval=dx)
            if residual < self.mti_newton_tol:
                if self.debug_newton:
                    print(f"[MTI-NEWTON] converged in {it + 1} iterations")
                return True, x_new, dx, residual

            x_new, _ = self._newton_step(x_new=x_new, x_prev=x_prev, dx=dx, h_eff=h_eff, rhs=rhs, residual=residual)
            if not np.all(np.isfinite(x_new)):
                return False, x_new, dx, np.inf
            dx_out = dx.copy()

        if self.debug_newton:
            print(f"[MTI-NEWTON] failed after {int(self.mti_max_iter)} iterations; last_res={residual:.6e}")
        dx = np.zeros_like(dx_last) if force_zero_dx else self.problem.get_dx(x_new, x_prev, dx_last, h_eff)
        rhs = self.problem.compute_mti_equalities(x_new, dx, x_prev, h_eff)
        if rhs.size > 0 and np.all(np.isfinite(rhs)):
            residual = float(np.linalg.norm(rhs, np.inf))
            if residual < self.mti_newton_tol:
                return True, x_new, dx, residual
            dx_out = dx.copy()
        if self.debug:
            print(f"[MTI-NEWTON] fixed-boolean failed final_residual={residual:.6e}")
        return False, x_new, dx_out, residual

    def _solve_continuous_with_fallback(
        self,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        force_zero_dx: bool = False,
    ) -> tuple[bool, Vec, Vec, float]:
        ok_mti = False
        x_mti = np.asarray(x_prev, dtype=float).copy()
        dx_mti = np.asarray(dx_last, dtype=float).copy()
        res_mti = np.inf
        if self.use_full_fixed_z_mti_rows:
            ok_mti, x_mti, dx_mti, res_mti = self._solve_full_fixed_z_mti_rows(
                x_prev=x_prev,
                dx_last=dx_last,
                h_eff=h_eff,
                force_zero_dx=force_zero_dx,
            )
            if ok_mti:
                return True, x_mti, dx_mti, res_mti

        seeds = [x_prev.copy()]

        best = (ok_mti, x_mti, dx_mti, res_mti)
        for seed in seeds:
            ok, x_try, dx_try, res = self._solve_continuous_for_fixed_boolean(
                seed,
                x_prev,
                dx_last,
                h_eff,
                force_zero_dx=force_zero_dx,
            )
            if ok:
                return True, x_try, dx_try, res
            if res < best[3]:
                best = (ok, x_try, dx_try, res)
        return best

    def _solve_full_fixed_z_mti_rows(
        self,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        force_zero_dx: bool = False,
    ) -> tuple[bool, Vec, Vec, float]:
        row_meta = getattr(self.problem, "_mti_row_meta", [])
        col_meta = getattr(self.problem, "_mti_col_meta", [])
        n_xp = len(getattr(self.problem, "_mti_xp_vars", []))
        n_y = len(getattr(self.problem, "_mti_y_vars", []))
        if len(row_meta) == 0 or len(col_meta) == 0 or (n_xp + n_y) <= 0:
            return False, np.asarray(x_prev, dtype=float).copy(), np.asarray(dx_last, dtype=float).copy(), np.inf

        raw_rows = np.arange(len(row_meta), dtype=int)
        var_idx: list[int] = []
        for col in range(n_xp + n_y):
            idx = self.problem._mti_col_to_continuous_var_idx(col)
            if idx is not None:
                var_idx.append(int(idx))

        if len(var_idx) == 0:
            return False, np.asarray(x_prev, dtype=float).copy(), np.asarray(dx_last, dtype=float).copy(), np.inf

        if self.debug_solve:
            eq_rows = self.problem.get_continuous_equality_row_indices(raw_rows)
            fixed_bool_eq = self.problem.get_fixed_boolean_equality_row_indices(raw_rows)
            ineq_rows = self.problem.get_inequality_row_indices(raw_rows)
            print(
                f"[MTI-FIXZ-FULL] rows={raw_rows.size} eq_rows={eq_rows.size} "
                f"fixed_bool_eq={fixed_bool_eq.size} ineq_rows={ineq_rows.size} vars={len(var_idx)}"
            )

        return self._solve_subproblem_fix_z(
            x_seed=np.asarray(x_prev, dtype=float).copy(),
            x_prev=x_prev,
            dx_last=dx_last,
            h_eff=h_eff,
            eq_idx=raw_rows,
            var_idx=np.asarray(sorted(set(var_idx)), dtype=int),
            force_zero_dx=force_zero_dx,
            check_inequalities=False,
        )

    def _detect_inequality_event(
        self,
        g_end: Vec,
        dg_end: Vec,
    ) -> tuple[bool, int]:
        g_arr = np.asarray(g_end, dtype=float)
        if g_arr.size == 0 or not np.all(np.isfinite(g_arr)):
            return False, -1

        violated = np.where(g_arr > self.inequality_tolerance)[0]
        if violated.size > 0:
            idx = int(violated[np.argmax(g_arr[violated])])
            return True, idx

        dg_arr = np.asarray(dg_end, dtype=float)
        if dg_arr.size == g_arr.size and np.all(np.isfinite(dg_arr)):
            active = np.where(g_arr >= -1e-9)[0]
            outgoing = active[dg_arr[active] > 0.0] if active.size > 0 else np.zeros(0, dtype=int)
            if outgoing.size > 0:
                idx = int(outgoing[np.argmax(dg_arr[outgoing])])
                return True, idx

        return False, -1

    def _locate_inequality_event(
        self,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        z_prev: Vec,
        event_idx: int,
        x_end: Vec,
        dx_end: Vec,
        force_zero_dx: bool = False,
    ) -> tuple[bool, float, Vec, Vec, int]:
        """
        Locate the first fixed-z inequality crossing inside a BackEuler segment.

        This approximates MATLAB's ODE event localization for the implicit Euler
        path: solve the fixed-z DAE at intermediate step lengths and bisect the
        scalar event function G[event_idx]. Boolean candidates are deliberately
        not generated here; this only finds the event time that will trigger MTI
        event handling.
        """
        if event_idx < 0:
            return False, h_eff, x_end, dx_end, event_idx

        self.problem.set_mti_boolean_state(z_prev)
        g0 = self.problem.compute_mti_inequalities(x_prev, dx_last, x_prev, 0.0)
        g0_arr = np.asarray(g0, dtype=float)
        if event_idx >= g0_arr.size:
            return False, h_eff, x_end, dx_end, event_idx

        g0_val = float(g0_arr[event_idx])
        if g0_val >= -self.inequality_tolerance:
            return True, 0.0, np.asarray(x_prev, dtype=float).copy(), np.asarray(dx_last, dtype=float).copy(), event_idx

        g1 = self.problem.compute_mti_inequalities(x_end, dx_end, x_prev, h_eff)
        g1_arr = np.asarray(g1, dtype=float)
        if event_idx >= g1_arr.size:
            return False, h_eff, x_end, dx_end, event_idx
        if float(g1_arr[event_idx]) < -self.inequality_tolerance:
            return True, h_eff, np.asarray(x_end, dtype=float).copy(), np.asarray(dx_end, dtype=float).copy(), event_idx

        n_iter = int(getattr(self, "event_bisect_iter", 20))

        lo = 0.0
        hi = float(h_eff)
        x_hi = np.asarray(x_end, dtype=float).copy()
        dx_hi = np.asarray(dx_end, dtype=float).copy()
        for _ in range(n_iter):
            hm = 0.5 * (lo + hi)
            if hm <= 0.0:
                break
            self.problem.set_mti_boolean_state(z_prev)
            ok_mid, x_mid, dx_mid, _ = self._solve_continuous_with_fallback(
                x_prev=x_prev,
                dx_last=dx_last,
                h_eff=hm,
                force_zero_dx=force_zero_dx,
            )
            if not ok_mid:
                hi = hm
                continue
            g_mid = self.problem.compute_mti_inequalities(x_mid, dx_mid, x_prev, hm)
            g_mid_arr = np.asarray(g_mid, dtype=float)
            if event_idx >= g_mid_arr.size:
                return False, h_eff, x_end, dx_end, event_idx
            if float(g_mid_arr[event_idx]) >= -self.inequality_tolerance:
                hi = hm
                x_hi = np.asarray(x_mid, dtype=float).copy()
                dx_hi = np.asarray(dx_mid, dtype=float).copy()
            else:
                lo = hm

        if self.debug_solve:
            print(
                f"[MTI-EVENT-LOC] ineq={event_idx} h={h_eff:.6e} "
                f"h_event={hi:.6e}"
            )
        return True, hi, x_hi, dx_hi, event_idx

    def _event_total_derivative(
        self,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        z_prev: Vec,
        force_zero_dx: bool,
        forced_ineq_idx: int | None = None,
        require_z_change: bool = False,
    ) -> tuple[bool, Vec, Vec, Vec, float, Vec, Vec]:
        """
        MATLAB eventTotalDerivative-style event handler.

        Flow mirrors the toolbox control structure:
        previous fixed-Z subproblems -> event candidate-Z subproblem ->
        following fixed/variable-Z subproblems -> G/DG acceptance.
        """
        g_now = self.problem.compute_mti_inequalities(x_prev, dx_last, x_prev, h_eff)
        if forced_ineq_idx is not None:
            ie = int(forced_ineq_idx)
        elif g_now is not None and len(g_now) > 0:
            g_now_arr = np.asarray(g_now, dtype=float)
            active_idx = np.where(g_now_arr >= -self.inequality_tolerance)[0]
            if active_idx.size > 0:
                ie = int(active_idx[int(np.argmax(g_now_arr[active_idx]))])
            else:
                ie = int(np.argmax(g_now_arr))
        else:
            ie = 0

        candidates = self.problem.get_event_local_boolean_candidates(ie, z_prev)
        candidates.sort(key=lambda zc: self._hamming_distance(np.asarray(zc, dtype=float), z_prev))

        if self.debug_solve:
            n_bool = len(z_prev)
            full_count = (2 ** n_bool) if n_bool > 0 else 1
            n_cands = len(candidates)
            n_local_bools = -1
            if n_cands > 0 and (n_cands & (n_cands - 1)) == 0:
                n_local_bools = int(np.log2(n_cands))
            scope = "full" if n_cands == full_count else "local"
            print(
                f"[MTI-CAND] source={scope} ie={ie} n_cands={n_cands} "
                f"n_local_bools={n_local_bools} n_total_bools={n_bool}"
            )

        event_subset_ids = self.problem.get_event_subset_ids(ie)
        prev_groups, event_groups, foll_groups = self.problem.get_event_solving_stages(ie)

        x_stage = x_prev.copy()
        dx_stage = dx_last.copy()
        for eqg, varg in prev_groups:
            okg, x_stage, dx_stage, _ = self._solve_subproblem_fix_z(
                x_seed=x_stage,
                x_prev=x_prev,
                dx_last=dx_stage,
                h_eff=h_eff,
                eq_idx=np.asarray(eqg, dtype=int),
                var_idx=np.asarray(varg, dtype=int),
                force_zero_dx=force_zero_dx,
                direct_xp_solve=self.use_direct_xp_subproblem,
            )
            if not okg:
                break

        best_fail_res = np.inf
        best_fail_x = x_prev.copy()
        best_fail_dx = dx_last.copy()
        first_fail_dumped = False

        def try_candidates(cands: list[np.ndarray]) -> tuple[bool, Vec, Vec, Vec]:
            nonlocal best_fail_res, best_fail_x, best_fail_dx, first_fail_dumped
            max_iter_cands = len(cands)
            if self.debug and self.debug_max_cands > 0:
                max_iter_cands = min(max_iter_cands, int(self.debug_max_cands))
            for cand_idx, z_candidate in enumerate(cands):
                if cand_idx >= max_iter_cands:
                    if self.debug:
                        print(f"[MTI-CAND] debug_limit_reached={max_iter_cands}")
                    break
                if require_z_change and self._hamming_distance(np.asarray(z_candidate, dtype=float), z_prev) == 0:
                    if self.debug:
                        print(
                            f"[MTI-CAND] idx={cand_idx} z={np.asarray(z_candidate, dtype=int)} "
                            f"decision=no_z_change_at_event"
                        )
                    continue
                self.problem.set_mti_boolean_state(z_candidate)

                x_try = x_stage.copy()
                dx_try = dx_stage.copy()
                ok = True
                res_try = np.inf

                if getattr(self.problem, "use_full_dae_event_candidates", False):
                    ok, x_try, dx_try, res_try = self._solve_plain_dae_for_seed(
                        x_seed=x_try,
                        x_prev=x_prev,
                        dx_last=dx_last,
                        h_eff=h_eff,
                        force_zero_dx=force_zero_dx,
                    )
                else:
                    for group_i, (eqg, varg) in enumerate(event_groups):
                        ok, x_try, dx_try, res_try = self._solve_subproblem_fix_z(
                            x_seed=x_try,
                            x_prev=x_prev,
                            dx_last=dx_try,
                            h_eff=h_eff,
                            eq_idx=np.asarray(eqg, dtype=int),
                            var_idx=np.asarray(varg, dtype=int),
                            force_zero_dx=force_zero_dx,
                            check_inequalities=False,
                            direct_xp_solve=self.use_direct_xp_subproblem,
                        )
                        if not ok:
                            if self.debug:
                                print(
                                    f"[MTI-SUBFAIL] stage=event group={group_i} "
                                    f"rows={len(np.asarray(eqg, dtype=int))} vars={len(np.asarray(varg, dtype=int))} "
                                    f"reason={getattr(self, '_last_subproblem_fail_reason', 'solve_fail')} res={res_try:.6e}"
                                )
                            break

                if ok and not getattr(self.problem, "use_full_dae_event_candidates", False):
                    z_follow = np.asarray(z_candidate, dtype=float).copy()
                    for group_i, (eqg, varg) in enumerate(foll_groups):
                        eq_arr = np.asarray(eqg, dtype=int)
                        var_arr = np.asarray(varg, dtype=int)
                        bool_positions = self.problem.get_subproblem_boolean_positions(eq_arr, var_arr)
                        group_subset_ids = self.problem.get_group_subset_ids(eq_arr, var_arr)
                        if len(group_subset_ids & event_subset_ids) > 0:
                            ok, x_try, dx_try, z_follow, res_try = self._solve_subproblem_variable_z(
                                x_seed=x_try,
                                x_prev=x_prev,
                                dx_last=dx_try,
                                h_eff=h_eff,
                                z_seed=z_follow,
                                eq_idx=eq_arr,
                                var_idx=var_arr,
                                force_zero_dx=force_zero_dx,
                                direct_xp_solve=self.use_direct_xp_subproblem,
                            )
                        else:
                            self.problem.set_mti_boolean_state(z_follow)
                            ok, x_try, dx_try, res_try = self._solve_subproblem_fix_z(
                                x_seed=x_try,
                                x_prev=x_prev,
                                dx_last=dx_try,
                                h_eff=h_eff,
                                eq_idx=eq_arr,
                                var_idx=var_arr,
                                force_zero_dx=force_zero_dx,
                                direct_xp_solve=self.use_direct_xp_subproblem,
                            )
                        if not ok:
                            if self.debug:
                                print(
                                    f"[MTI-SUBFAIL] stage=following group={group_i} "
                                    f"rows={eq_arr.size} vars={var_arr.size} local_bools={len(bool_positions)} "
                                    f"reason={getattr(self, '_last_subproblem_fail_reason', 'solve_fail')} res={res_try:.6e}"
                                )
                            break
                    if ok:
                        self.problem.set_mti_boolean_state(z_follow)
                        z_candidate = z_follow

                if ok and self.polish_candidates:
                    ok, x_try, dx_try, res_try = self._solve_continuous_with_fallback(
                        x_prev=x_try,
                        dx_last=dx_try,
                        h_eff=h_eff,
                        force_zero_dx=force_zero_dx,
                    )
                elif ok:
                    rhs_try = self.problem.compute_mti_equalities(x_try, dx_try, x_prev, h_eff)
                    res_try = float(np.linalg.norm(rhs_try, np.inf)) if rhs_try.size > 0 else 0.0
                if not ok:
                    if self.debug:
                        fail_reason = getattr(self, "_last_subproblem_fail_reason", "solve_fail")
                        print(
                            f"[MTI-CAND] idx={cand_idx} z={np.asarray(z_candidate, dtype=int)} "
                            f"decision={fail_reason} res={res_try:.3e}"
                        )
                        if not first_fail_dumped:
                            first_fail_dumped = True
                            rhs_dbg = self.problem.compute_mti_equalities(x_try, dx_try, x_prev, h_eff)
                            if self.debug_residuals:
                                self._debug_print_top_residuals(rhs_dbg, top_k=12, tag="first-candidate-fail", x_eval=x_try, dx_eval=dx_try)
                    if np.isfinite(res_try) and res_try < best_fail_res:
                        best_fail_res = res_try
                        best_fail_x = x_try
                        best_fail_dx = dx_try
                    continue

                g_try = self.problem.compute_mti_inequalities(x_try, dx_try, x_prev, h_eff)
                if not self.problem.inequalities_satisfied(g_try, tol=self.inequality_tolerance):
                    if self.debug:
                        g_arr = np.asarray(g_try, dtype=float)
                        g_max = float(np.max(g_arr)) if g_arr.size > 0 else -np.inf
                        g_idx = int(np.argmax(g_arr)) if g_arr.size > 0 else -1
                        ineq_txt = "<unavailable>"
                        if g_idx >= 0:
                            ineq_list = getattr(self.problem, "_mti_inequalities_raw", None)
                            if ineq_list is None or len(ineq_list) == 0:
                                ineq_list = getattr(self.problem, "_mti_inequalities_compiled", None)
                            try:
                                if ineq_list is not None and g_idx < len(ineq_list):
                                    ineq_txt = str(ineq_list[g_idx])
                            except Exception:
                                ineq_txt = "<stringify-failed>"
                        print(
                            f"[MTI-CAND] idx={cand_idx} z={np.asarray(z_candidate, dtype=int)} "
                            f"decision=ineq_fail maxG={g_max:.3e} at ineq[{g_idx}]"
                        )
                        if g_idx >= 0:
                            print(f"  ineq[{g_idx}] expr: {ineq_txt}")
                    continue

                h_safe = max(float(h_eff), 1e-12)
                xpp_try = (np.asarray(dx_try, dtype=float) - np.asarray(dx_last, dtype=float)) / h_safe
                dg_try = self.problem.total_derivative_inequalities(x_try, dx_try, xpp=xpp_try)
                active = np.asarray(g_try) >= -1e-9
                if dg_try.size > 0 and np.any(active) and np.any(np.asarray(dg_try)[active] > 0.0):
                    if self.debug:
                        dg_active_max = float(np.max(np.asarray(dg_try, dtype=float)[active]))
                        print(
                            f"[MTI-CAND] idx={cand_idx} z={np.asarray(z_candidate, dtype=int)} "
                            f"decision=dg_fail maxDGactive={dg_active_max:.3e}"
                        )
                    continue

                if self.debug:
                    g_arr = np.asarray(g_try, dtype=float)
                    g_max = float(np.max(g_arr)) if g_arr.size > 0 else -np.inf
                    dg_active_max = float(np.max(np.asarray(dg_try, dtype=float)[active])) if (dg_try.size > 0 and np.any(active)) else -np.inf
                    print(
                        f"[MTI-CAND] idx={cand_idx} z={np.asarray(z_candidate, dtype=int)} "
                        f"decision=accepted maxG={g_max:.3e} maxDGactive={dg_active_max:.3e}"
                    )

                return True, x_try, dx_try, np.asarray(z_candidate, dtype=float)
            return False, best_fail_x, best_fail_dx, z_prev

        ok_evt, x_evt, dx_evt, z_evt = try_candidates(candidates)
        if ok_evt:
            return True, x_evt, dx_evt, z_evt, best_fail_res, best_fail_x, best_fail_dx

        if self.debug_solve:
            print("[MTI-CAND] no local candidate accepted; skipping full boolean enumeration")
        return False, x_prev, dx_last, z_prev, best_fail_res, best_fail_x, best_fail_dx

    def _try_event_total_derivative_candidates(
        self,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        z_prev: Vec,
        force_zero_dx: bool,
    ) -> tuple[bool, Vec, Vec, Vec, float, Vec, Vec]:
        return self._event_total_derivative(
            x_prev=x_prev,
            dx_last=dx_last,
            h_eff=h_eff,
            z_prev=z_prev,
            force_zero_dx=force_zero_dx,
        )

    def _solve_plain_dae_for_seed(
        self,
        x_seed: Vec,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        force_zero_dx: bool = False,
    ) -> tuple[bool, Vec, Vec, float]:
        x_new = x_seed.copy()
        residual = np.inf
        dx_out = dx_last.copy()

        for _ in range(self.mti_max_iter):
            self._count_iteration_stat("plain_dae_iterations")
            if force_zero_dx:
                dx = np.zeros_like(dx_last)
            else:
                dx = self.problem.get_dx(x_new, x_prev, dx_last, h_eff)

            rhs = self._rhs_implicit(x_new, dx, x_prev, h_eff)
            residual = float(np.linalg.norm(rhs, np.inf))
            if residual <= self.mti_solve_tol:
                return True, x_new, dx, residual

            jf = self._jacobian_implicit(x_new, dx, h_eff)
            
            m, n = jf.shape

            if rhs.size != m:
                raise ValueError(
                    f"Dimension mismatch: jf has shape {jf.shape}, "
                    f"but rhs has length {rhs.size}. "
                    f"Need len(rhs) == jf.shape[0]."
                )

            if m == n:
                # Standard square sparse solve
                delta = sp.linalg.spsolve(jf, -rhs)
            else:
                # Rectangular system: solve least-squares min ||jf @ delta + rhs||
                delta = sp.linalg.lsqr(jf, -rhs, iter_lim=self.mti_lsqr_iter_lim, atol=self.mti_solve_tol, btol=self.mti_solve_tol)[0]
            if not np.all(np.isfinite(delta)):
                delta, *_ = sp.linalg.lsqr(jf, -rhs, iter_lim=self.mti_lsqr_iter_lim, atol=self.mti_solve_tol, btol=self.mti_solve_tol)
            if not np.all(np.isfinite(delta)):
                if self.debug_solve:
                    print("[MTI] plain DAE linear solve returned non-finite delta")
                return False, x_new, dx, np.inf

            x_new = x_new + delta
            if not np.all(np.isfinite(x_new)):
                if self.debug:
                    print("[MTI] plain DAE update produced non-finite x")
                return False, x_new, dx, np.inf

            dx_out = dx.copy()

        dx = np.zeros_like(dx_last) if force_zero_dx else self.problem.get_dx(x_new, x_prev, dx_last, h_eff)
        rhs_full = self.problem.compute_mti_equalities(x_new, dx, x_prev, h_eff)
        if rhs_full.size > 0 and np.all(np.isfinite(rhs_full)):
            rhs = np.asarray(rhs_full, dtype=float)
            residual = float(np.linalg.norm(rhs, np.inf)) if rhs.size > 0 else 0.0
            if residual <= self.mti_solve_tol:
                return True, x_new, dx, residual
            dx_out = dx.copy()
        return False, x_new, dx_out, residual

    def _solve_plain_dae(
        self,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        force_zero_dx: bool = False,
    ) -> tuple[bool, Vec, Vec, float]:
        # Keep behavior aligned with BackEulerImplicitIntegration:
        # start Newton from previous converged point only.
        return self._solve_plain_dae_for_seed(
            x_prev.copy(),
            x_prev,
            dx_last,
            h_eff,
            force_zero_dx=force_zero_dx,
        )

    def _debug_problem_row_label(self, row: int) -> str:
        label_fn = getattr(self.problem, "_mti_row_label", None)
        if callable(label_fn):
            try:
                return str(label_fn(int(row)))
            except Exception:
                pass
        return f"row={int(row)}"

    def _debug_problem_var_label(self, var: int) -> str:
        map_fn = getattr(self.problem, "_continuous_var_idx_to_mti_col", None)
        label_fn = getattr(self.problem, "_mti_col_label", None)
        if callable(map_fn) and callable(label_fn):
            try:
                col = map_fn(int(var))
                if col is not None:
                    return str(label_fn(int(col)))
            except Exception:
                pass
        vars_ = getattr(self.problem, "_state_algeb_vars", None)
        if vars_ is not None and 0 <= int(var) < len(vars_):
            obj = vars_[int(var)]
            name = getattr(obj, "name", None)
            if name is not None:
                return f"var={int(var)}:{name}"
        return f"var={int(var)}"

    def _debug_print_subproblem_labels(self, raw_eq_idx: np.ndarray, eq_idx: np.ndarray, var_idx: np.ndarray) -> None:
        eq_labels = ", ".join(self._debug_problem_row_label(int(i)) for i in np.asarray(eq_idx, dtype=int)[:12])
        var_labels = ", ".join(self._debug_problem_var_label(int(i)) for i in np.asarray(var_idx, dtype=int)[:12])
        print(
            f"[MTI-SUBLABELS] raw_eq={len(raw_eq_idx)} eq={len(eq_idx)} var={len(var_idx)} "
            f"eq_head=[{eq_labels}] var_head=[{var_labels}]"
        )

    def _debug_print_subproblem_residuals(self, rhs: np.ndarray, eq_idx: np.ndarray, limit: int = 8) -> None:
        rhs_arr = np.asarray(rhs, dtype=float)
        eq_arr = np.asarray(eq_idx, dtype=int)
        if rhs_arr.size == 0 or eq_arr.size == 0:
            return
        order = np.argsort(-np.abs(rhs_arr), kind="stable")[: int(limit)]
        labels = []
        for pos in order.tolist():
            labels.append(f"{self._debug_problem_row_label(int(eq_arr[int(pos)]))}={rhs_arr[int(pos)]:.6e}")
        print(f"[MTI-SUBRES] {'; '.join(labels)}")

    def _solve_subproblem_fix_z(
        self,
        x_seed: Vec,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        eq_idx: np.ndarray,
        var_idx: np.ndarray,
        force_zero_dx: bool = False,
        check_inequalities: bool = False,
        direct_xp_solve: bool = False,
    ) -> tuple[bool, Vec, Vec, float]:
        self._last_subproblem_fail_reason = "solve_fail"
        self._last_subproblem_context = "fix-z"
        raw_eq_idx = np.asarray(eq_idx, dtype=int)
        ineq_idx = self.problem.get_inequality_row_indices(raw_eq_idx)
        fixed_bool_eq_idx = self.problem.get_fixed_boolean_equality_row_indices(raw_eq_idx)
        eq_idx = self.problem.get_continuous_equality_row_indices(raw_eq_idx)
        var_idx = np.asarray(var_idx, dtype=int)
        if self.debug_solve:
            print(
                f"[MTI-SUB] kind=fix-z raw_rows={raw_eq_idx.size} eq_rows={eq_idx.size} "
                f"fixed_bool_eq={fixed_bool_eq_idx.size} ineq_rows={ineq_idx.size} "
                f"vars={var_idx.size} checkG={int(check_inequalities)}"
            )
        if eq_idx.size == 0 or var_idx.size == 0:
            dx = self.problem.get_dx(x_seed, x_prev, dx_last, h_eff) if not force_zero_dx else np.zeros_like(dx_last)
            if check_inequalities:
                g_max = self._subproblem_inequality_violation(x_seed, dx, x_prev, h_eff, ineq_idx)
                if g_max > self.inequality_tolerance:
                    self._last_subproblem_fail_reason = "ineq_fail"
                    return False, x_seed.copy(), dx, g_max
            bool_res = self._fixed_boolean_equality_residual(x_seed, dx, x_prev, h_eff, fixed_bool_eq_idx)
            if bool_res > self.mti_solve_tol:
                self._last_subproblem_fail_reason = "bool_eq_fail"
                return False, x_seed.copy(), dx, bool_res
            return True, x_seed.copy(), dx, 0.0

        if self.debug_solve and self._debug_subproblem_label_prints < 5:
            self._debug_print_subproblem_labels(raw_eq_idx=raw_eq_idx, eq_idx=eq_idx, var_idx=var_idx)
            self._debug_subproblem_label_prints += 1

        if direct_xp_solve and not force_zero_dx:
            ok_direct, x_direct, dx_direct, res_direct = self._solve_subproblem_fix_z_direct_xp(
                x_seed=x_seed,
                x_prev=x_prev,
                dx_last=dx_last,
                h_eff=h_eff,
                eq_idx=eq_idx,
                var_idx=var_idx,
                ineq_idx=ineq_idx,
                fixed_bool_eq_idx=fixed_bool_eq_idx,
                check_inequalities=check_inequalities,
            )
            if ok_direct or np.isfinite(res_direct):
                return ok_direct, x_direct, dx_direct, res_direct

        x_new = x_seed.copy()
        dx_out = dx_last.copy()
        residual = np.inf

        explicit_pairs, eq_idx, var_idx = self.problem.split_explicit_subproblem_pairs(eq_idx=eq_idx, var_idx=var_idx)
        if self.debug_solve:
            print(
                f"[MTI-SUBSPLIT] explicit_pairs={len(explicit_pairs)} "
                f"rest_eq={eq_idx.size} rest_var={var_idx.size}"
            )
        for eq0, var0 in explicit_pairs:
            for it in range(self.mti_max_iter):
                self._count_iteration_stat("subproblem_explicit_iterations")
                dx = np.zeros_like(dx_last) if force_zero_dx else self.problem.get_dx(x_new, x_prev, dx_last, h_eff)
                rhs_full = self.problem.compute_mti_equalities(x_new, dx, x_prev, h_eff)
                if rhs_full.size == 0 or not np.all(np.isfinite(rhs_full)):
                    return False, x_new, dx, np.inf
                rhs = np.asarray([float(rhs_full[int(eq0)])], dtype=float)
                residual = abs(float(rhs[0]))
                if self.debug_solve:
                    g_max = self._subproblem_inequality_violation(x_new, dx, x_prev, h_eff, ineq_idx)
                    print(
                        f"[MTI-SUBERR] phase=explicit it={it + 1}/{self.mti_max_iter} "
                        f"eq=1 var=1 res={residual:.6e} localG={g_max:.6e}"
                    )
                if residual <= self.mti_solve_tol:
                    dx_out = dx.copy()
                    break

                j_full = self._jacobian_implicit(x_new, dx, h_eff).tocsr()
                deriv = float(j_full[int(eq0), int(var0)])
                if abs(deriv) <= 1e-14 or not np.isfinite(deriv):
                    delta_sub, *_ = sp.linalg.lsqr(j_full[[int(eq0)], :][:, [int(var0)]], -rhs, iter_lim=self.mti_lsqr_iter_lim, atol=self.mti_solve_tol, btol=self.mti_solve_tol)
                    delta = float(delta_sub[0]) if len(delta_sub) > 0 else np.nan
                else:
                    delta = -float(rhs[0]) / deriv
                if not np.isfinite(delta):
                    return False, x_new, dx, np.inf
                x_new[int(var0)] += delta
                if not np.all(np.isfinite(x_new)):
                    return False, x_new, dx, np.inf
                dx_out = dx.copy()
            else:
                return False, x_new, dx_out, residual

        if eq_idx.size == 0 or var_idx.size == 0:
            dx = self.problem.get_dx(x_new, x_prev, dx_last, h_eff) if not force_zero_dx else np.zeros_like(dx_last)
            rhs_full = self.problem.compute_mti_equalities(x_new, dx, x_prev, h_eff)
            if rhs_full.size > 0 and np.all(np.isfinite(rhs_full)):
                eq_eval = self.problem.get_equality_row_indices(raw_eq_idx)
                rhs = np.asarray(rhs_full, dtype=float)[eq_eval] if eq_eval.size > 0 else np.zeros(0, dtype=float)
                residual = float(np.linalg.norm(rhs, np.inf)) if rhs.size > 0 else 0.0
            if self.debug_solve:
                g_max = self._subproblem_inequality_violation(x_new, dx, x_prev, h_eff, ineq_idx)
                print(
                    f"[MTI-SUBERR] phase=early-return eq={eq_idx.size} var={var_idx.size} "
                    f"res={residual:.6e} localG={g_max:.6e}"
                )
            if check_inequalities:
                g_max = self._subproblem_inequality_violation(x_new, dx, x_prev, h_eff, ineq_idx)
                if g_max > self.inequality_tolerance:
                    self._last_subproblem_fail_reason = "ineq_fail"
                    return False, x_new, dx, max(residual if np.isfinite(residual) else 0.0, g_max)
            bool_res = self._fixed_boolean_equality_residual(x_new, dx, x_prev, h_eff, fixed_bool_eq_idx)
            if bool_res > self.mti_solve_tol:
                self._last_subproblem_fail_reason = "bool_eq_fail"
                return False, x_new, dx, max(residual if np.isfinite(residual) else 0.0, bool_res)
            return True, x_new, dx, residual if np.isfinite(residual) else 0.0

        if self.use_nonlinear_subproblem_lsq and eq_idx.size != var_idx.size:
            ok_lsq, x_lsq, dx_lsq, res_lsq = self._solve_subproblem_nonlinear_lsq(
                x_seed=x_new,
                x_prev=x_prev,
                dx_last=dx_last,
                h_eff=h_eff,
                eq_idx=eq_idx,
                var_idx=var_idx,
                ineq_idx=ineq_idx,
                force_zero_dx=force_zero_dx,
                check_inequalities=check_inequalities,
            )
            if ok_lsq or np.isfinite(res_lsq):
                return ok_lsq, x_lsq, dx_lsq, res_lsq

        for it in range(self.mti_max_iter):
            self._count_iteration_stat("subproblem_implicit_iterations")
            dx = np.zeros_like(dx_last) if force_zero_dx else self.problem.get_dx(x_new, x_prev, dx_last, h_eff)
            rhs_full = self.problem.compute_mti_equalities(x_new, dx, x_prev, h_eff)
            if rhs_full.size == 0 or not np.all(np.isfinite(rhs_full)):
                return False, x_new, dx, np.inf

            rhs = np.asarray(rhs_full, dtype=float)[eq_idx]
            residual = float(np.linalg.norm(rhs, np.inf)) if rhs.size > 0 else 0.0
            g_max_dbg = self._subproblem_inequality_violation(x_new, dx, x_prev, h_eff, ineq_idx)
            if self.debug_solve:
                print(
                    f"[MTI-SUBERR] phase=implicit it={it + 1}/{self.mti_max_iter} "
                    f"eq={eq_idx.size} var={var_idx.size} res={residual:.6e} localG={g_max_dbg:.6e}"
                )
                if it in (0, self.mti_max_iter - 1):
                    self._debug_print_subproblem_residuals(rhs=rhs, eq_idx=eq_idx, limit=8)
            if residual <= self.mti_solve_tol:
                bool_res = self._fixed_boolean_equality_residual(x_new, dx, x_prev, h_eff, fixed_bool_eq_idx)
                if bool_res > self.mti_solve_tol:
                    self._last_subproblem_fail_reason = "bool_eq_fail"
                    return False, x_new, dx, max(residual, bool_res)
                if check_inequalities:
                    g_max = self._subproblem_inequality_violation(x_new, dx, x_prev, h_eff, ineq_idx)
                    if g_max > self.inequality_tolerance:
                        self._last_subproblem_fail_reason = "ineq_fail"
                        return False, x_new, dx, max(residual, g_max)
                return True, x_new, dx, residual

            j_full = self._jacobian_implicit(x_new, dx, h_eff).tocsr()
            j_sub = j_full[eq_idx, :][:, var_idx]
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("error", category=MatrixRankWarning)
                    delta_sub = sp.linalg.spsolve(j_sub, -rhs)
            except Exception:
                delta_sub, *_ = sp.linalg.lsqr(j_sub, -rhs, iter_lim=self.mti_lsqr_iter_lim, atol=self.mti_solve_tol, btol=self.mti_solve_tol)
            if not np.all(np.isfinite(delta_sub)):
                return False, x_new, dx, np.inf

            delta_sub = np.asarray(delta_sub, dtype=float)
            if self.use_subproblem_line_search:
                best_x = None
                best_res = np.inf
                for alpha in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125):
                    x_trial = x_new.copy()
                    x_trial[var_idx] = x_trial[var_idx] + alpha * delta_sub
                    if not np.all(np.isfinite(x_trial)):
                        continue
                    dx_trial = np.zeros_like(dx_last) if force_zero_dx else self.problem.get_dx(x_trial, x_prev, dx_last, h_eff)
                    rhs_trial_full = self.problem.compute_mti_equalities(x_trial, dx_trial, x_prev, h_eff)
                    if rhs_trial_full.size == 0 or not np.all(np.isfinite(rhs_trial_full)):
                        continue
                    rhs_trial = np.asarray(rhs_trial_full, dtype=float)[eq_idx]
                    trial_res = float(np.linalg.norm(rhs_trial, np.inf)) if rhs_trial.size > 0 else 0.0
                    if trial_res < best_res:
                        best_x = x_trial
                        best_res = trial_res
                    if trial_res <= residual:
                        break
                if best_x is None:
                    return False, x_new, dx, np.inf
                x_trial = best_x
            else:
                x_trial = x_new.copy()
                x_trial[var_idx] = x_trial[var_idx] + delta_sub
                if not np.all(np.isfinite(x_trial)):
                    return False, x_new, dx, np.inf

            x_new = x_trial
            dx_out = dx.copy()

        if self.debug_solve:
            print(f"[MTI-SUBFAIL] kind=fix-z final_residual={residual:.6e}")
        return False, x_new, dx_out, residual

    def _solve_subproblem_fix_z_direct_xp(
        self,
        x_seed: Vec,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        eq_idx: np.ndarray,
        var_idx: np.ndarray,
        ineq_idx: np.ndarray,
        fixed_bool_eq_idx: np.ndarray,
        check_inequalities: bool,
    ) -> tuple[bool, Vec, Vec, float]:
        x_ref, dx_ref = self.problem.make_mti_direct_state(x_seed, dx_last)
        w = self.problem.mti_direct_pack(x_seed, dx_last, var_idx)
        residual = np.inf
        x_eval = x_seed.copy()
        dx_eval = dx_last.copy()

        for it in range(self.mti_max_iter):
            self._count_iteration_stat("subproblem_direct_xp_iterations")
            x_eval, dx_eval = self.problem.mti_direct_apply(w, x_ref, dx_ref, var_idx)
            rhs_full = self.problem.compute_mti_direct_equalities(x_eval, dx_eval)
            if rhs_full.size == 0 or not np.all(np.isfinite(rhs_full)):
                return False, x_eval, dx_eval, np.inf
            rhs = np.asarray(rhs_full, dtype=float)[eq_idx]
            residual = float(np.linalg.norm(rhs, np.inf)) if rhs.size > 0 else 0.0
            if self.debug_solve:
                g_max_dbg = self._subproblem_inequality_violation(x_eval, dx_eval, x_prev, h_eff, ineq_idx)
                print(
                    f"[MTI-SUBERR] phase=direct-xp it={it + 1}/{self.mti_max_iter} "
                    f"eq={eq_idx.size} var={var_idx.size} res={residual:.6e} localG={g_max_dbg:.6e}"
                )
            if residual <= self.mti_solve_tol:
                bool_res = self._fixed_boolean_equality_residual(x_eval, dx_eval, x_prev, h_eff, fixed_bool_eq_idx)
                if bool_res > self.mti_solve_tol:
                    self._last_subproblem_fail_reason = "bool_eq_fail"
                    return False, x_eval, dx_eval, max(residual, bool_res)
                if check_inequalities:
                    g_max = self._subproblem_inequality_violation(x_eval, dx_eval, x_prev, h_eff, ineq_idx)
                    if g_max > self.inequality_tolerance:
                        self._last_subproblem_fail_reason = "ineq_fail"
                        return False, x_eval, dx_eval, max(residual, g_max)
                return True, x_eval, dx_eval, residual

            j_full = self.problem.jacobian_mti_direct_equalities(x_eval, dx_eval, var_idx).tocsr()
            j_sub = j_full[eq_idx, :]
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("error", category=MatrixRankWarning)
                    delta = sp.linalg.spsolve(j_sub, -rhs)
            except Exception:
                delta, *_ = sp.linalg.lsqr(j_sub, -rhs, iter_lim=self.mti_lsqr_iter_lim, atol=self.mti_solve_tol, btol=self.mti_solve_tol)
            if not np.all(np.isfinite(delta)):
                return False, x_eval, dx_eval, np.inf
            w = w + np.asarray(delta, dtype=float)

        if self.debug_solve:
            print(f"[MTI-SUBFAIL] kind=direct-xp final_residual={residual:.6e}")
        return False, x_eval, dx_eval, residual

    def _solve_subproblem_nonlinear_lsq(
        self,
        x_seed: Vec,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        eq_idx: np.ndarray,
        var_idx: np.ndarray,
        ineq_idx: np.ndarray,
        force_zero_dx: bool,
        check_inequalities: bool,
    ) -> tuple[bool, Vec, Vec, float]:
        eq_idx = np.asarray(eq_idx, dtype=int)
        var_idx = np.asarray(var_idx, dtype=int)
        if eq_idx.size == 0 or var_idx.size == 0:
            dx = self.problem.get_dx(x_seed, x_prev, dx_last, h_eff) if not force_zero_dx else np.zeros_like(dx_last)
            return True, x_seed.copy(), dx, 0.0

        x0_sub = np.asarray(x_seed[var_idx], dtype=float)

        def residual_fn(x_sub: Vec) -> Vec:
            x_eval = x_seed.copy()
            x_eval[var_idx] = np.asarray(x_sub, dtype=float)
            dx_eval = np.zeros_like(dx_last) if force_zero_dx else self.problem.get_dx(x_eval, x_prev, dx_last, h_eff)
            rhs_full = self.problem.compute_mti_equalities(x_eval, dx_eval, x_prev, h_eff)
            if rhs_full.size == 0 or not np.all(np.isfinite(rhs_full)):
                return np.full(eq_idx.size, 1e20, dtype=float)
            rhs = np.asarray(rhs_full, dtype=float)[eq_idx]
            if not np.all(np.isfinite(rhs)):
                return np.full(eq_idx.size, 1e20, dtype=float)
            return rhs

        def jac_fn(x_sub: Vec):
            x_eval = x_seed.copy()
            x_eval[var_idx] = np.asarray(x_sub, dtype=float)
            dx_eval = np.zeros_like(dx_last) if force_zero_dx else self.problem.get_dx(x_eval, x_prev, dx_last, h_eff)
            return self._jacobian_implicit(x_eval, dx_eval, h_eff).tocsr()[eq_idx, :][:, var_idx]

        try:
            max_nfev = max(int(var_idx.size) * 1000, 4000)
            result = least_squares(
                residual_fn,
                x0_sub,
                jac=jac_fn,
                method="trf",
                ftol=np.finfo(float).eps,
                xtol=np.sqrt(np.finfo(float).eps),
                gtol=np.sqrt(np.finfo(float).eps),
                max_nfev=max_nfev,
            )
        except Exception:
            return False, x_seed.copy(), dx_last.copy(), np.inf

        x_new = x_seed.copy()
        x_new[var_idx] = np.asarray(result.x, dtype=float)
        dx = np.zeros_like(dx_last) if force_zero_dx else self.problem.get_dx(x_new, x_prev, dx_last, h_eff)
        rhs = residual_fn(result.x)
        residual = float(np.linalg.norm(rhs, np.inf)) if rhs.size > 0 else 0.0
        if not np.all(np.isfinite(x_new)) or not np.all(np.isfinite(dx)) or not np.isfinite(residual):
            return False, x_new, dx, np.inf

        if residual <= self.mti_solve_tol:
            if check_inequalities:
                g_max = self._subproblem_inequality_violation(x_new, dx, x_prev, h_eff, ineq_idx)
                if g_max > self.inequality_tolerance:
                    return False, x_new, dx, max(residual, g_max)
            return True, x_new, dx, residual
        return False, x_new, dx, residual

    def _subproblem_inequality_violation(
        self,
        x: Vec,
        dx: Vec,
        x_prev: Vec,
        h_eff: float,
        ineq_idx: np.ndarray,
    ) -> float:
        ineq_idx = np.asarray(ineq_idx, dtype=int)
        if ineq_idx.size == 0:
            return -np.inf
        g = self.problem.compute_mti_inequalities(x, dx, x_prev, h_eff)
        if g is None or len(g) == 0:
            return -np.inf
        g_arr = np.asarray(g, dtype=float)
        valid = ineq_idx[(ineq_idx >= 0) & (ineq_idx < g_arr.size)]
        if valid.size == 0:
            return -np.inf
        return float(np.max(g_arr[valid]))

    def _fixed_boolean_equality_residual(
        self,
        x: Vec,
        dx: Vec,
        x_prev: Vec,
        h_eff: float,
        eq_idx: np.ndarray,
    ) -> float:
        eq_idx = np.asarray(eq_idx, dtype=int)
        if eq_idx.size == 0:
            return 0.0
        rhs_full = self.problem.compute_mti_equalities(x, dx, x_prev, h_eff)
        if rhs_full.size == 0 or not np.all(np.isfinite(rhs_full)):
            return np.inf
        valid = eq_idx[(eq_idx >= 0) & (eq_idx < rhs_full.size)]
        if valid.size == 0:
            return 0.0
        return float(np.linalg.norm(np.asarray(rhs_full, dtype=float)[valid], np.inf))

    def _solve_subproblem_variable_z(
        self,
        x_seed: Vec,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        z_seed: Vec,
        eq_idx: np.ndarray,
        var_idx: np.ndarray,
        force_zero_dx: bool = False,
        direct_xp_solve: bool = False,
    ) -> tuple[bool, Vec, Vec, Vec, float]:
        self._last_subproblem_context = "variable-z"
        bool_positions = self.problem.get_subproblem_boolean_positions(eq_idx=eq_idx, var_idx=var_idx)
        if self.debug:
            eq_rows = self.problem.get_equality_row_indices(np.asarray(eq_idx, dtype=int))
            ineq_rows = self.problem.get_inequality_row_indices(np.asarray(eq_idx, dtype=int))
            print(
                f"[MTI-SUB] kind=variable-z raw_rows={len(np.asarray(eq_idx, dtype=int))} "
                f"eq_rows={eq_rows.size} ineq_rows={ineq_rows.size} vars={len(np.asarray(var_idx, dtype=int))} "
                f"local_bools={len(bool_positions)}"
            )
        if len(bool_positions) == 0:
            ok, x_try, dx_try, res = self._solve_subproblem_fix_z(
                x_seed=x_seed,
                x_prev=x_prev,
                dx_last=dx_last,
                h_eff=h_eff,
                eq_idx=eq_idx,
                var_idx=var_idx,
                force_zero_dx=force_zero_dx,
                check_inequalities=True,
                direct_xp_solve=direct_xp_solve,
            )
            return ok, x_try, dx_try, np.asarray(z_seed, dtype=float).copy(), res

        z0 = np.asarray(z_seed, dtype=float).copy()
        combinations = []
        for bits in product((0.0, 1.0), repeat=len(bool_positions)):
            z = z0.copy()
            for k, pos in enumerate(bool_positions):
                z[int(pos)] = float(bits[k])
            combinations.append(z)
        combinations.sort(key=lambda zc: self._hamming_distance(zc, z0))

        best = (False, x_seed.copy(), dx_last.copy(), z0.copy(), np.inf)
        local_ineq_idx = self.problem.get_inequality_row_indices(np.asarray(eq_idx, dtype=int))
        for z_candidate in combinations:
            self._last_subproblem_fail_reason = "solve_fail"
            self.problem.set_mti_boolean_state(z_candidate)
            ok, x_try, dx_try, res = self._solve_subproblem_fix_z(
                x_seed=x_seed,
                x_prev=x_prev,
                dx_last=dx_last,
                h_eff=h_eff,
                eq_idx=eq_idx,
                var_idx=var_idx,
                force_zero_dx=force_zero_dx,
                check_inequalities=False,
                direct_xp_solve=direct_xp_solve,
            )
            if not ok:
                if np.isfinite(res) and res < best[4]:
                    best = (False, x_try, dx_try, z_candidate.copy(), res)
                continue

            g_max = self._subproblem_inequality_violation(x_try, dx_try, x_prev, h_eff, local_ineq_idx)
            if g_max <= max(self.inequality_tolerance, 2.0 * np.finfo(float).eps):
                return True, x_try, dx_try, z_candidate.copy(), res

            self._last_subproblem_fail_reason = "ineq_fail"
            if np.isfinite(res) and (res + max(0.0, g_max)) < best[4]:
                best = (False, x_try, dx_try, z_candidate.copy(), res + max(0.0, g_max))

        return best

    @staticmethod
    def _hamming_distance(a: Vec, b: Vec) -> int:
        return int(np.sum(np.asarray(a, dtype=int) != np.asarray(b, dtype=int)))

    def _enumerate_boolean_candidates(self, z_prev: Vec) -> list[np.ndarray]:
        n_bool = len(z_prev)
        if n_bool == 0:
            return [np.zeros(0, dtype=float)]
        if n_bool == 1:
            return [np.array([0.0]), np.array([1.0])]

        candidates = [np.asarray(bits, dtype=float) for bits in product((0.0, 1.0), repeat=n_bool)]
        candidates.sort(key=lambda zc: self._hamming_distance(zc, z_prev))
        return candidates

    @staticmethod
    def _merge_boolean_vectors(base_z: Vec, positions: list[int], values: Vec) -> np.ndarray:
        z = np.asarray(base_z, dtype=float).copy()
        for k, pos in enumerate(positions):
            z[pos] = float(values[k])
        return z

    @staticmethod
    def _to_binary_boolean_state(z: Vec) -> np.ndarray:
        z_arr = np.asarray(z, dtype=float)
        if z_arr.size == 0:
            return z_arr.copy()
        return (z_arr >= 0.5).astype(float)

    def _direct_boolean_test_single(self, x_prev: Vec, dx_last: Vec) -> np.ndarray:
        z0 = np.array([0.0], dtype=float)
        self.problem.set_mti_boolean_state(z0)
        guard0 = self.problem.evaluate_boolean_guard(bool_position=0, x=x_prev, dx=dx_last)
        if guard0 is not None:
            if guard0 <= self.inequality_tolerance:
                return np.array([1.0], dtype=float)
            return z0

        g0 = self.problem.compute_mti_inequalities(x_prev, dx_last, x_prev, self.h)
        if g0.size == 0 or float(np.max(g0)) <= self.inequality_tolerance:
            return np.array([1.0], dtype=float)
        return z0

    def _resolve_direct_booleans(self, z_prev: Vec, x_prev: Vec, dx_last: Vec, direct_positions: list[int]) -> np.ndarray:
        z = np.asarray(z_prev, dtype=float).copy()
        for pos in direct_positions:
            g0 = None
            z_try0 = z.copy()
            z_try0[pos] = 0.0
            self.problem.set_mti_boolean_state(z_try0)
            guard0 = self.problem.evaluate_boolean_guard(bool_position=pos, x=x_prev, dx=dx_last)
            if guard0 is None:
                g0 = self.problem.compute_mti_inequalities(x_prev, dx_last, x_prev, self.h)
            if guard0 is not None:
                if guard0 <= self.inequality_tolerance:
                    z[pos] = 1.0
                else:
                    z[pos] = 0.0
            else:
                if g0.size == 0 or float(np.max(g0)) <= self.inequality_tolerance:
                    z[pos] = 1.0
                else:
                    z[pos] = 0.0
        return z

    def simulate(self):
        converged = False
        well_initialized = True
        self._iteration_stats = {}

        self._timings = {
            "jacobian_time": 0.0,
            "rhs_time": 0.0,
            "lag_update_time": 0.0,
            "linear_solver_time": 0.0,
            "initial_step_time": 0.0,
            "rhs_algeb_time": 0.0,
            "rhs_state_time": 0.0,
            "jac_j11_time": 0.0,
            "jac_j12_time": 0.0,
            "jac_j21_time": 0.0,
            "jac_j22_time": 0.0,
        }

        try:
            self.problem.reset_boundary_update_state(float(self.t0))
        except Exception:
            pass

        x0: Vec = self.problem.get_x0()
        dx0: Vec = np.zeros(self.problem.get_diff_var_number(), dtype=float)
        self._debug_x0_ref = x0.copy()
        self._debug_first_eval_done = False

        try:
            self.problem.update_variable_params(t=float(self.t0), x_snapshot=x0)
        except TypeError:
            self.problem.update_variable_params(float(self.t0))
        except Exception:
            pass
        self._update_problem_boundary(t_curr=float(self.t0), x_snapshot=x0)

        self.t[0] = self.t0
        self.y[0, :] = x0.copy()

        # Initialization quality is assessed from algebraic consistency at t0,
        # not by whether the first dynamic integration step converges.
        try:
            if hasattr(self.problem, "rhs_algebraic"):
                f0_alg = np.asarray(self.problem.rhs_algebraic(x0, dx0), dtype=float)
            else:
                f0_alg = np.asarray(self.problem.compute_mti_equalities(x0, dx0, x0, 0.0), dtype=float)
            if f0_alg.size > 0:
                r0 = float(np.linalg.norm(f0_alg, np.inf))
                well_initialized = bool(np.isfinite(r0) and r0 <= max(self.tol, 1e-6))
        except Exception:
            well_initialized = False

        # Re-apply MTI boolean initialization at simulation start to avoid
        # later parameter refreshes collapsing boolean mode values to defaults.
        try:
            self.problem._initialize_mti_booleans_at_t0()
        except Exception:
            pass

        n_bool_from_problem = len(self.problem.get_mti_boolean_parameter_indices)
        z0 = np.zeros(n_bool_from_problem, dtype=float)
        z0_from_problem = self._get_boolean_state_from_problem(self.problem.get_mti_boolean_parameter_indices)
        if n_bool_from_problem > 0 and z0_from_problem is not None:
            z0 = z0_from_problem
        elif n_bool_from_problem > 0:
            z0 = self.problem.update_mti_boolean_state(x0, dx0, x0, self.h)
            if z0 is None:
                z0 = np.zeros(n_bool_from_problem, dtype=float)
        z0 = self._to_binary_boolean_state(z0)
        print(f"[MTI] Initial z0 ({len(z0)} booleans): {z0}")

        if len(self.problem.get_mti_boolean_parameter_indices) > 0:
            try:
                self.problem.build_mti_incidence_and_order(x0, dx0, self.h)
            except Exception as ex:
                raise RuntimeError(f"Failed to build MTI incidence/solving order: {ex}") from ex
            if os.getenv("RMS_MTI_ORDER_ONLY", "0").strip() in ("1", "true", "True", "yes", "on"):
                self.problem.print_mti_solving_order_summary()
                raise SystemExit(0)

        self.z = np.full((self.steps + 1, len(z0)), np.nan, dtype=float)
        if len(z0) > 0:
            self.z[0, :] = z0

        dx_last = dx0.copy()
        z_prev = z0.copy()
        last_completed_idx = 0

        for step_idx in range(self.steps):
            self.problem.report_progress2(step_idx, self.steps)

            t_prev = self.t[step_idx]
            t_macro_target = t_prev + self.h

            x_prev = self.y[step_idx, :].copy()
            x_local = x_prev.copy()
            t_local_prev = t_prev
            converged = False
            is_first_local_step = True
            force_zero_dx = bool(step_idx == 0 and not getattr(self.problem, "disable_mti_first_step_zero_dx", False))

            while t_local_prev < (t_macro_target - 1e-15):
                forced_event_time: float | None = self.problem.get_next_forced_event_time(
                    t_local_prev,
                    t_macro_target,
                )
                if forced_event_time is None:
                    t_curr = t_macro_target
                else:
                    t_curr = forced_event_time

                h_eff = t_curr - t_local_prev
                if h_eff <= 0.0:
                    break

                try:
                    self.problem.update_variable_params(t=t_curr, x_snapshot=x_local)
                except TypeError:
                    self.problem.update_variable_params(t_curr)
                self._update_problem_boundary(t_curr=t_curr, x_snapshot=x_local)

                bool_indices = self.problem.get_mti_boolean_parameter_indices
                n_bool = len(bool_indices)
                accepted_x: Vec | None = None
                accepted_dx: Vec | None = None
                accepted_z: Vec | None = None
                accepted_t_curr = t_curr
                # MATLAB-aligned intent: keep current z unless event handling is needed.
                self.problem.set_mti_boolean_state(z_prev)
                ok_fix, x_fix, dx_fix, res_fix = self._solve_continuous_with_fallback(
                    x_prev=x_local,
                    dx_last=dx_last,
                    h_eff=h_eff,
                    force_zero_dx=force_zero_dx and is_first_local_step,
                )

                best_fail_res = np.inf
                best_fail_x = x_local.copy()
                best_fail_dx = dx_last.copy()
                if np.isfinite(res_fix):
                    best_fail_res = float(res_fix)
                    best_fail_x = x_fix
                    best_fail_dx = dx_fix

                event_needed = False
                event_idx = -1
                if ok_fix:
                    g_fix = self.problem.compute_mti_inequalities(x_fix, dx_fix, x_local, h_eff)
                    h_safe = max(float(h_eff), 1e-12)
                    xpp_fix = (np.asarray(dx_fix, dtype=float) - np.asarray(dx_last, dtype=float)) / h_safe
                    dg_fix = self.problem.total_derivative_inequalities(x_fix, dx_fix, xpp=xpp_fix)
                    event_needed, event_idx = self._detect_inequality_event(g_fix, dg_fix)
                    if not event_needed:
                        accepted_x = x_fix
                        accepted_dx = dx_fix
                        accepted_z = z_prev.copy()
                        converged = True
                elif n_bool > 0:
                    # If fixed-z Newton cannot solve the continuous equations,
                    # the current boolean assignment may be inconsistent. In
                    # that case restore the previous MTI behavior and let the
                    # event handler enumerate local candidates immediately.
                    event_needed = True

                if event_needed:
                    if ok_fix:
                        ok_loc, h_event, x_event, dx_event, event_idx = self._locate_inequality_event(
                            x_prev=x_local,
                            dx_last=dx_last,
                            h_eff=h_eff,
                            z_prev=z_prev,
                            event_idx=event_idx,
                            x_end=x_fix,
                            dx_end=dx_fix,
                            force_zero_dx=force_zero_dx and is_first_local_step,
                        )
                        if self.debug:
                            print(
                                f"[MTI-EVENT-SPLIT] mode=localized ineq={event_idx} "
                                f"h_eff={float(h_eff):.6e} h_event={float(h_event):.6e} "
                                f"remaining={max(0.0, float(h_eff) - float(h_event)):.6e}"
                            )
                    else:
                        ok_loc = True
                        remaining_h = float(h_eff)
                        x_event = x_local
                        dx_event = dx_last
                        if self.debug:
                            print(
                                f"[MTI-EVENT-SPLIT] mode=unlocalized-recovery "
                                f"h_eff={float(h_eff):.6e} reason=fixed_z_solve_failed"
                            )

                    if ok_loc:
                        if ok_fix:
                            remaining_h = max(0.0, float(h_eff) - float(h_event))
                            require_z_change = float(h_event) <= 1e-12
                            # Match MATLAB's split/restart flow: eventTotalDerivative
                            # resolves the mode and derivatives at the event instant;
                            # the post-event continuous segment is solved separately.
                            event_solve_h = max(min(float(h_eff), 1e-9), 1e-12)
                        else:
                            require_z_change = False
                            # No fixed-z trajectory exists to localize against;
                            # keep the prior candidate solve semantics for this
                            # recovery path rather than inventing an event time.
                            event_solve_h = float(h_eff)
                        if self.debug:
                            print(
                                f"[MTI-EVENT-SOLVE] ineq={event_idx if ok_fix else 'auto'} "
                                f"event_solve_h={float(event_solve_h):.6e} "
                                f"post_remaining={float(remaining_h):.6e}"
                            )
                        ok_evt, x_evt, dx_evt, z_evt, best_fail_res_evt, best_fail_x_evt, best_fail_dx_evt = self._event_total_derivative(
                            x_prev=x_event,
                            dx_last=dx_event,
                            h_eff=event_solve_h,
                            z_prev=z_prev,
                            force_zero_dx=False,
                            forced_ineq_idx=event_idx if ok_fix else None,
                            require_z_change=require_z_change,
                        )
                    else:
                        ok_evt = False
                        x_evt = x_fix
                        dx_evt = dx_fix
                        z_evt = z_prev.copy()
                        best_fail_res_evt = best_fail_res
                        best_fail_x_evt = x_fix
                        best_fail_dx_evt = dx_fix

                    if ok_evt and ok_loc:
                        if not ok_fix:
                            accepted_x = x_evt
                            accepted_dx = dx_evt
                            converged = True
                        else:
                            accepted_x = x_evt
                            accepted_dx = dx_evt
                            accepted_t_curr = t_local_prev + float(h_event)
                            made_progress = accepted_t_curr > t_local_prev + 1e-15
                            changed_z = self._hamming_distance(np.asarray(z_evt, dtype=float), z_prev) > 0
                            converged = bool(made_progress or changed_z)
                            if self.debug:
                                print(
                                    f"[MTI-RESTART] accepted_event_time={float(accepted_t_curr):.6e} "
                                    f"remaining={float(remaining_h):.6e} progress={int(made_progress)} z_change={int(changed_z)}"
                                )
                        if converged:
                            accepted_z = z_evt
                    if np.isfinite(best_fail_res_evt) and best_fail_res_evt < best_fail_res:
                        best_fail_res = best_fail_res_evt
                        best_fail_x = best_fail_x_evt
                        best_fail_dx = best_fail_dx_evt

                if not converged or accepted_x is None or accepted_dx is None:
                    if self.debug:
                        print(f"[MTI-FALLBACK] mode=plain_dae h_eff={float(h_eff):.6e}")
                    ok_dae, x_dae, dx_dae, res_dae = self._solve_plain_dae(
                        x_prev=x_local,
                        dx_last=dx_last,
                        h_eff=h_eff,
                        force_zero_dx=force_zero_dx and is_first_local_step,
                    )
                    if ok_dae:
                        accepted_x = x_dae
                        accepted_dx = dx_dae
                        accepted_z = z_prev.copy()
                        converged = True
                    if np.isfinite(res_dae) and res_dae < best_fail_res:
                        best_fail_res = res_dae
                        best_fail_x = x_dae
                        best_fail_dx = dx_dae

                if not converged or accepted_x is None or accepted_dx is None:
                    if self.compare:
                        f_mti = self.problem.compute_mti_equalities(best_fail_x, best_fail_dx, x_local, h_eff)
                        f_dae = self._rhs_implicit(best_fail_x, best_fail_dx, x_local, h_eff)
                        n_mti = float(np.linalg.norm(f_mti, np.inf)) if f_mti.size > 0 else 0.0
                        n_dae = float(np.linalg.norm(f_dae, np.inf)) if f_dae.size > 0 else 0.0
                        diff = float(np.linalg.norm(np.asarray(f_mti) - np.asarray(f_dae), np.inf)) if f_mti.size == f_dae.size else np.inf
                        j = self._jacobian_implicit(best_fail_x, best_fail_dx, h_eff)
                        j_dense = j.toarray() if sp.issparse(j) else np.asarray(j)
                        rank = int(np.linalg.matrix_rank(j_dense))
                        cond = float(np.linalg.cond(j_dense)) if j_dense.size > 0 else np.nan
                        print(
                            f"[MTI-COMPARE] step={step_idx} t={t_curr:.6f} "
                            f"||F_mti||inf={n_mti:.3e} ||F_dae||inf={n_dae:.3e} "
                            f"||F_mti-F_dae||inf={diff:.3e} rank(J)={rank}/{j_dense.shape[0]} cond(J)={cond:.3e}"
                        )
                    break

                x_local = accepted_x
                dx_last = accepted_dx
                t_local_prev = accepted_t_curr
                is_first_local_step = False
                if accepted_z is not None and len(accepted_z) > 0:
                    z_prev = np.asarray(accepted_z, dtype=float)
                else:
                    z_prev = np.zeros(0, dtype=float)

            if t_local_prev < (t_macro_target - 1e-15):
                break

            self.y[step_idx + 1, :] = x_local
            self.t[step_idx + 1] = t_macro_target
            last_completed_idx = step_idx + 1

            if len(z_prev) > 0:
                self.z[step_idx + 1, :] = z_prev
            else:
                z_prev = np.zeros(0, dtype=float)

        if self.iteration_summary:
            print(f"[MTI-ITER] mti_max_iter={int(self.mti_max_iter)} event_bisect_iter={int(self.event_bisect_iter)}")
            for name in sorted(self._iteration_stats):
                print(f"[MTI-ITER] {name}={self._iteration_stats[name]}")
        return self.t[: last_completed_idx + 1], self.y[: last_completed_idx + 1, :], well_initialized, converged
