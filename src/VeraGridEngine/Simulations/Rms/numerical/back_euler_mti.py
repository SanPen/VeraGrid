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

from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.problems.rms_problem_MTI import RmsProblemMTI
from VeraGridEngine.basic_structures import Mat, Vec
from VeraGridEngine.Utils.Symbolic.symbolic import get_expression_vars


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
        self.debug_residuals = os.getenv("RMS_MTI_DEBUG_RESIDUALS", "0").strip() in ("1", "true", "True", "yes", "on")
        self.compare = os.getenv("RMS_MTI_COMPARE", "0").strip() in ("1", "true", "True", "yes", "on")
        try:
            # 0 means: no candidate cap (toolbox-like all-candidates check)
            self.debug_max_cands = int(os.getenv("RMS_MTI_DEBUG_MAX_CANDS", "0"))
        except Exception:
            self.debug_max_cands = 0
        self._debug_x0_ref: Vec | None = None
        self._debug_first_eval_done = False
        self.max_iter_0 = 100

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

        order = np.argsort(np.abs(arr))[::-1]
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
                                uid_bindings[vr.uid] = float(self.problem._constant_params[p_idx])
                                continue
                            e_idx = self.problem._uid2idx_event_params.get(vr.uid, None)
                            if e_idx is not None:
                                uid_bindings[vr.uid] = float(self.problem._variable_parameters_values[e_idx])
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
                                vars_preview.append(f"{vr.name}=cprms[{p_idx}]={self.problem._constant_params[p_idx]:+.3e}")
                                continue
                            e_idx = self.problem._uid2idx_event_params.get(vr.uid, None)
                            if e_idx is not None:
                                vars_preview.append(f"{vr.name}=vprms[{e_idx}]={self.problem._variable_parameters_values[e_idx]:+.3e}")
                        if len(vars_preview) > 0:
                            print("     bindings: " + ", ".join(vars_preview[:12]))
            except Exception as ex:
                print(f"     symbolic-check-failed: {ex}")

    def _newton_step(self, x_new: Vec, x_prev: Vec, dx: Vec, h_eff: float) -> tuple[Vec, float]:
        rhs = self.problem.compute_mti_equalities(x_new, dx, x_prev, h_eff)
        if rhs.size == 0:
            return x_new, 0.0
        if not np.all(np.isfinite(rhs)):
            return x_new, np.inf
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
            delta, *_ = sp.linalg.lsqr(jf, -rhs)
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

        for it in range(self.max_iter_0):
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
            if self.debug:
                it_ms = (time.perf_counter() - it_t0) * 1e3
                print(f"[MTI-NEWTON] it={it + 1}/{self.max_iter_0} res={residual:.6e} iter_ms={it_ms:.3f}")

            if self.debug_residuals and residual >= max(self.tol, 1e-6):
                self._debug_print_top_residuals(rhs, top_k=12, tag="fixed-z", x_eval=x_new, dx_eval=dx)
            if residual < max(self.tol, 1e-6):
                if self.debug:
                    print(f"[MTI-NEWTON] converged in {it + 1} iterations")
                return True, x_new, dx, residual

            x_new, _ = self._newton_step(x_new=x_new, x_prev=x_prev, dx=dx, h_eff=h_eff)
            if not np.all(np.isfinite(x_new)):
                return False, x_new, dx, np.inf
            dx_out = dx.copy()

        if self.debug:
            print(f"[MTI-NEWTON] failed after {self.max_iter_0} iterations; last_res={residual:.6e}")
        return False, x_new, dx_out, residual

    def _solve_continuous_with_fallback(
        self,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        force_zero_dx: bool = False,
    ) -> tuple[bool, Vec, Vec, float]:
        seeds = [x_prev.copy()]

        best = (False, x_prev.copy(), dx_last.copy(), np.inf)
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

    def _try_event_total_derivative_candidates(
        self,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        z_prev: Vec,
        force_zero_dx: bool,
    ) -> tuple[bool, Vec, Vec, Vec, float, Vec, Vec]:
        g_now = self.problem.compute_mti_inequalities(x_prev, dx_last, x_prev, h_eff)
        if g_now is not None and len(g_now) > 0:
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

        if self.debug:
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
                self.problem.set_mti_boolean_state(z_candidate)

                x_try = x_stage.copy()
                dx_try = dx_stage.copy()
                ok = True
                res_try = np.inf

                for eqg, varg in event_groups:
                    ok, x_try, dx_try, res_try = self._solve_subproblem_fix_z(
                        x_seed=x_try,
                        x_prev=x_prev,
                        dx_last=dx_try,
                        h_eff=h_eff,
                        eq_idx=np.asarray(eqg, dtype=int),
                        var_idx=np.asarray(varg, dtype=int),
                        force_zero_dx=force_zero_dx,
                    )
                    if not ok:
                        break

                if ok:
                    for eqg, varg in foll_groups:
                        ok, x_try, dx_try, res_try = self._solve_subproblem_fix_z(
                            x_seed=x_try,
                            x_prev=x_prev,
                            dx_last=dx_try,
                            h_eff=h_eff,
                            eq_idx=np.asarray(eqg, dtype=int),
                            var_idx=np.asarray(varg, dtype=int),
                            force_zero_dx=force_zero_dx,
                        )
                        if not ok:
                            break

                if ok:
                    ok, x_try, dx_try, res_try = self._solve_continuous_with_fallback(
                        x_prev=x_try,
                        dx_last=dx_try,
                        h_eff=h_eff,
                        force_zero_dx=force_zero_dx,
                    )
                if not ok:
                    if self.debug:
                        print(
                            f"[MTI-CAND] idx={cand_idx} z={np.asarray(z_candidate, dtype=int)} "
                            f"decision=solve_fail res={res_try:.3e}"
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
            return False, x_prev, dx_last, z_prev

        ok_evt, x_evt, dx_evt, z_evt = try_candidates(candidates)
        if ok_evt:
            return True, x_evt, dx_evt, z_evt, best_fail_res, best_fail_x, best_fail_dx

        # MATLAB toolbox uses event-local combinations first; if no feasible
        # candidate is found, broaden to all combinations before giving up.
        all_candidates = self.problem.enumerate_all_boolean_candidates()
        if self.debug:
            print(f"[MTI-CAND] fallback=full n_cands={len(all_candidates)}")
        all_candidates.sort(key=lambda zc: self._hamming_distance(np.asarray(zc, dtype=float), z_prev))
        ok_all, x_all, dx_all, z_all = try_candidates(all_candidates)
        if ok_all:
            return True, x_all, dx_all, z_all, best_fail_res, best_fail_x, best_fail_dx

        return False, x_prev, dx_last, z_prev, best_fail_res, best_fail_x, best_fail_dx

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

        for _ in range(self.max_iter_0):
            if force_zero_dx:
                dx = np.zeros_like(dx_last)
            else:
                dx = self.problem.get_dx(x_new, x_prev, dx_last, h_eff)

            rhs = self._rhs_implicit(x_new, dx, x_prev, h_eff)
            residual = float(np.linalg.norm(rhs, np.inf))
            if residual < max(self.tol, 1e-6):
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
                delta = sp.linalg.lsqr(jf, -rhs)[0]
            if not np.all(np.isfinite(delta)):
                delta, *_ = sp.linalg.lsqr(jf, -rhs)
            if not np.all(np.isfinite(delta)):
                if self.debug:
                    print("[MTI] plain DAE linear solve returned non-finite delta")
                return False, x_new, dx, np.inf

            x_new = x_new + delta
            if not np.all(np.isfinite(x_new)):
                if self.debug:
                    print("[MTI] plain DAE update produced non-finite x")
                return False, x_new, dx, np.inf

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

    def _solve_subproblem_fix_z(
        self,
        x_seed: Vec,
        x_prev: Vec,
        dx_last: Vec,
        h_eff: float,
        eq_idx: np.ndarray,
        var_idx: np.ndarray,
        force_zero_dx: bool = False,
    ) -> tuple[bool, Vec, Vec, float]:
        if eq_idx.size == 0 or var_idx.size == 0:
            dx = self.problem.get_dx(x_seed, x_prev, dx_last, h_eff) if not force_zero_dx else np.zeros_like(dx_last)
            return True, x_seed.copy(), dx, 0.0

        x_new = x_seed.copy()
        dx_out = dx_last.copy()
        residual = np.inf
        for _ in range(self.max_iter_0):
            dx = np.zeros_like(dx_last) if force_zero_dx else self.problem.get_dx(x_new, x_prev, dx_last, h_eff)
            rhs_full = self.problem.compute_mti_equalities(x_new, dx, x_prev, h_eff)
            if rhs_full.size == 0 or not np.all(np.isfinite(rhs_full)):
                return False, x_new, dx, np.inf

            rhs = np.asarray(rhs_full, dtype=float)[eq_idx]
            residual = float(np.linalg.norm(rhs, np.inf)) if rhs.size > 0 else 0.0
            if residual < max(self.tol, 1e-6):
                return True, x_new, dx, residual

            j_full = self._jacobian_implicit(x_new, dx, h_eff).tocsr()
            j_sub = j_full[eq_idx, :][:, var_idx]
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("error", category=MatrixRankWarning)
                    delta_sub = sp.linalg.spsolve(j_sub, -rhs)
            except Exception:
                delta_sub, *_ = sp.linalg.lsqr(j_sub, -rhs)
            if not np.all(np.isfinite(delta_sub)):
                return False, x_new, dx, np.inf

            x_trial = x_new.copy()
            x_trial[var_idx] = x_trial[var_idx] + np.asarray(delta_sub, dtype=float)
            if not np.all(np.isfinite(x_trial)):
                return False, x_new, dx, np.inf

            x_new = x_trial
            dx_out = dx.copy()

        return False, x_new, dx_out, residual

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

        x0: Vec = self.problem.get_x0()
        dx0: Vec = np.zeros(self.problem.get_diff_var_number(), dtype=float)
        self._debug_x0_ref = x0.copy()
        self._debug_first_eval_done = False

        self.t[0] = self.t0
        self.y[0, :] = x0.copy()

        # Initialization quality is assessed from algebraic consistency at t0,
        # not by whether the first dynamic integration step converges.
        try:
            f0_alg = np.asarray(self.problem.rhs_algebraic(x0, dx0), dtype=float)
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
        if n_bool_from_problem > 0 and self.problem._variable_parameters_values is not None:
            for k, idx in enumerate(self.problem.get_mti_boolean_parameter_indices):
                z0[k] = float(self.problem._variable_parameters_values[idx])
        elif n_bool_from_problem > 0:
            z0 = self.problem.update_mti_boolean_state(x0, dx0, x0, self.h)
            if z0 is None:
                z0 = np.zeros(n_bool_from_problem, dtype=float)
        z0 = self._to_binary_boolean_state(z0)
        print(f"[MTI] Initial z0 ({len(z0)} booleans): {z0}")

        if len(self.problem.get_mti_boolean_parameter_indices) > 0:
            try:
                self.problem.build_mti_incidence_and_order(x0, dx0, self.h)
            except Exception:
                pass

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
            force_zero_dx = bool(step_idx == 0)

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
                    self.problem.update_variable_params(t=t_local_prev, x_snapshot=x_local)
                except TypeError:
                    self.problem.update_variable_params(t_local_prev)
                try:
                    self.problem.update(t_curr, x_local, self.problem._variable_parameters_values)
                except Exception:
                    pass

                bool_indices = self.problem.get_mti_boolean_parameter_indices
                n_bool = len(bool_indices)
                accepted_x: Vec | None = None
                accepted_dx: Vec | None = None
                accepted_z: Vec | None = None
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

                event_needed = True
                if ok_fix:
                    g_fix = self.problem.compute_mti_inequalities(x_fix, dx_fix, x_local, h_eff)
                    if self.problem.inequalities_satisfied(g_fix, tol=self.inequality_tolerance):
                        h_safe = max(float(h_eff), 1e-12)
                        xpp_fix = (np.asarray(dx_fix, dtype=float) - np.asarray(dx_last, dtype=float)) / h_safe
                        dg_fix = self.problem.total_derivative_inequalities(x_fix, dx_fix, xpp=xpp_fix)
                        active_fix = np.asarray(g_fix) >= -1e-9
                        if not (dg_fix.size > 0 and np.any(active_fix) and np.any(np.asarray(dg_fix)[active_fix] > 0.0)):
                            accepted_x = x_fix
                            accepted_dx = dx_fix
                            accepted_z = z_prev.copy()
                            converged = True
                            event_needed = False

                if event_needed:
                    ok_evt, x_evt, dx_evt, z_evt, best_fail_res_evt, best_fail_x_evt, best_fail_dx_evt = self._try_event_total_derivative_candidates(
                        x_prev=x_local,
                        dx_last=dx_last,
                        h_eff=h_eff,
                        z_prev=z_prev,
                        force_zero_dx=force_zero_dx and is_first_local_step,
                    )
                    if np.isfinite(best_fail_res_evt) and best_fail_res_evt < best_fail_res:
                        best_fail_res = best_fail_res_evt
                        best_fail_x = best_fail_x_evt
                        best_fail_dx = best_fail_dx_evt
                    if ok_evt:
                        accepted_x = x_evt
                        accepted_dx = dx_evt
                        accepted_z = z_evt
                        converged = True

                if not converged or accepted_x is None or accepted_dx is None:
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
                t_local_prev = t_curr
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

        return self.t[: last_completed_idx + 1], self.y[: last_completed_idx + 1, :], well_initialized, converged
