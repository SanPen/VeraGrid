# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple
import os
from itertools import product

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components

from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Comparison, Const, get_expression_vars
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicJacobian
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.problems.rms_problem_phasor import RmsProblemPhasor
from VeraGridEngine.Simulations.Rms.problems.mti_hybrid_structure import (
    MTISubProblemRow,
    build_incidence_from_jacobian,
    build_connected_subproblem_order,
    build_single_subproblem_order,
)


class RmsProblemMTI(RmsProblemPhasor):
    """
    RMS problem exposing MTI-style equality/inequality evaluation.

    Equalities are the same implicit residuals used by the DAE solver.
    Inequalities are compiled locally in this MTI class from
    ``Block.inequalities`` and evaluated at runtime via ``rhs_inequalities``.
    """

    def __init__(self, *args, **kwargs):
        # Must be defined before super().__init__ because the base constructor
        # calls add_variables_to_compilation_dicts(), which is overridden here.
        self._mti_boolean_params: list[object] = []
        self._mti_bool_uid2param_idx: dict[int, int] = {}
        super().__init__(*args, **kwargs)
        self._mti_inequalities_raw: list[Expr | Comparison] = []
        self._mti_inequalities_compiled: list[Expr] = []
        self._rhs_ineq_fn = None
        self._j_ineq_x_fn = None
        self._j_ineq_dx_fn = None
        self._j_ineq_x_static_fn = None
        self._j_ineq_dx_static_fn = None
        self._j_eq_x_static_fn = None
        self._j_eq_dx_static_fn = None
        self._mti_bool_param_indices: list[int] = []
        self._mti_bool_guard_compiled_by_param_idx: dict[int, object] = {}
        self._mti_bool_guard_var_positions_by_param_idx: dict[int, np.ndarray] = {}
        self._mti_incidence_includes_inequalities = False
        self._compile_mti_inequalities()
        self._compile_mti_equality_jacobians()
        self._compile_mti_boolean_guards()
        self._initialize_mti_booleans_at_t0()
        self._mti_incidence: np.ndarray | None = None
        self._mti_solving_order: list[MTISubProblemRow] = []
        self._mti_xp_vars: list[object] = []
        self._mti_y_vars: list[object] = []
        self._mti_incidence_bool_param_indices: list[int] = []
        self._mti_diff_uid_to_xp_col: dict[int, int] = {}
        self._mti_base_uid_to_xp_col: dict[int, int] = {}
        self._mti_alg_uid_to_y_col: dict[int, int] = {}
        self._mti_bool_uid_to_local_col: dict[int, int] = {}
        self._mti_continuous_var_idx_to_col: dict[int, int] = {}
        self._mti_col_to_continuous_var_idx_map: dict[int, int] = {}
        self._mti_col_meta: list[tuple[str, int, object | None]] = []
        self._mti_row_meta: list[tuple[str, int]] = []
        self._mti_base_xp_incidence_mask: np.ndarray | None = None
        self._ineq_var_positions: list[np.ndarray] = []
        self._build_inequality_variable_positions()

    def add_variables_to_compilation_dicts(self, elm, mdl):
        super().add_variables_to_compilation_dicts(elm=elm, mdl=mdl)
        ineq_uids: set[int] = set()
        for ineq in mdl.inequalities:
            vars_in_ineq = get_expression_vars(ineq)
            for v in vars_in_ineq:
                ineq_uids.add(v.uid)

        for ep in mdl.boolean_guards.keys():
            if ep not in self._mti_boolean_params:
                self._mti_boolean_params.append(ep)
            # If already represented in vars-space, do not remap the UID to
            # vprms-space; preserve base compiler mapping.
            if ep.uid in self._uid2idx_vars:
                continue
            if ep.uid in self._mti_bool_uid2param_idx:
                continue
            param_idx = len(self._variable_parameters)
            self._compiler_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}[{param_idx}]"
            self._alias_names_dict[ep.uid] = f"{self.VARIABLE_PARAMS_NAME}_{param_idx}"
            self._uid2idx_event_params[ep.uid] = param_idx
            self._mti_bool_uid2param_idx[ep.uid] = param_idx
            self._variable_parameters.append(ep)
            self._event_parameters_eqs.append(Const(0.0))

    def get_mti_boolean_parameters(self) -> list[object]:
        return list(self._mti_boolean_params)

    @property
    def non_bool_idx_params(self) -> np.ndarray:
        n = len(self._variable_parameters)
        bool_idx = set(self.get_mti_boolean_parameter_indices)
        return np.asarray([i for i in range(n) if i not in bool_idx], dtype=int)

    def update_variable_params(self, t: float, x_snapshot: Vec | None = None):
        # MTI booleans are controlled explicitly by event/candidate logic.
        # Refresh only non-boolean variable parameters here.
        evt_vals = self._event_params_fn(self._variable_parameters_values, t)
        idx = self.non_bool_idx_params
        self._variable_parameters_values[idx] = np.asarray(evt_vals, dtype=float)[idx]

    def set_events_group(self, rms_events_group):
        """
        Keep base phasor event-group behavior, then re-apply MTI boolean init.

        The base implementation recompiles event parameters and rebuilds
        `_variable_parameters_values`, which can reset MTI boolean entries.
        """
        super().set_events_group(rms_events_group)
        self._initialize_mti_booleans_at_t0()

    def _mti_boolean_values(self, x_snapshot: Vec | None = None) -> Vec:
        # Return currently assigned boolean parameter values. Candidate updates
        # are applied explicitly through set_mti_boolean_state().
        if self._variable_parameters_values is None:
            return np.zeros(0, dtype=float)
        bool_idx = self.get_mti_boolean_parameter_indices
        n_bool = len(bool_idx)
        if n_bool == 0:
            return np.zeros(0, dtype=float)
        return np.asarray(self._variable_parameters_values[np.asarray(bool_idx, dtype=int)], dtype=float)

    def _initialize_mti_booleans_at_t0(self) -> None:
        """
        Initialize MTI boolean runtime parameters from their guards at x0.

        This avoids starting Newton with inconsistent all-zero mode values when
        many booleans are present.
        """
        if self._variable_parameters_values is None:
            return

        idx = self.get_mti_boolean_parameter_indices       
        if len(idx) == 0:
            return

        x0 = self.get_x0()
        dx0 = np.zeros(self.get_diff_var_number(), dtype=float)
        debug = os.getenv("RMS_MTI_DEBUG", "0").strip() in ("1", "true", "True", "yes", "on")
        if debug:
            print("[MTI-INIT] x0:", x0)

        z0 = np.zeros(len(idx), dtype=float)
        for k in range(len(idx)):
            init_val = self._evaluate_boolean_init_from_init_eq(bool_position=k, x=x0)
            if init_val is not None:
                z0[k] = 1.0 if float(init_val) >= 0.5 else 0.0
                guard_val = self.evaluate_boolean_guard(bool_position=k, x=x0, dx=dx0)
            else:
                guard_val = self.evaluate_boolean_guard(bool_position=k, x=x0, dx=dx0)
                if guard_val is None:
                    # Keep existing value when no dedicated guard exists.
                    current = float(self._variable_parameters_values[idx[k]])
                    z0[k] = 1.0 if current >= 0.5 else 0.0
                else:
                    z0[k] = self._boolean_value_from_guard(guard_val)
            if debug:
                print(f"[MTI-INIT] bool_pos={k} param_idx={idx[k]} guard={guard_val} init_eq={init_val} z0={z0[k]}")

        self.set_mti_boolean_state(z0)
        if debug:
            print("[MTI-INIT] initial z0:", z0)

    @staticmethod
    def _boolean_value_from_guard(guard_val: float) -> float:
        """Interpret direct 0/1 guards, otherwise fall back to G <= 0 residuals."""
        val = float(guard_val)
        if abs(val) <= 1e-12 or abs(val - 1.0) <= 1e-12:
            return 1.0 if val >= 0.5 else 0.0
        return 1.0 if val <= 0.0 else 0.0

    def _evaluate_boolean_init_from_init_eq(self, bool_position: int, x: Vec) -> float | None:
        idx = self.get_mti_boolean_parameter_indices
        if bool_position < 0 or bool_position >= len(idx):
            return None
        param_idx = int(idx[bool_position])
        if param_idx < 0 or param_idx >= len(self._variable_parameters):
            return None
        bool_var = self._variable_parameters[param_idx]

        for blk in self.sys_block.get_all_blocks():
            init_eq = getattr(blk, "init_eqs", {}).get(bool_var, None)
            if init_eq is None:
                continue
            if isinstance(init_eq, Const) and init_eq.value is not None:
                return float(init_eq.value)
            if isinstance(init_eq, Expr):
                try:
                    uid_bindings: dict[int, float] = {}
                    for vr in get_expression_vars(init_eq):
                        v_idx = self.uid2idx_vars.get(vr.uid, None)
                        if v_idx is not None:
                            uid_bindings[vr.uid] = float(x[v_idx])
                            continue
                        p_idx = self._uid2idx_params.get(vr.uid, None)
                        if p_idx is not None:
                            uid_bindings[vr.uid] = float(self._constant_params[p_idx])
                            continue
                        e_idx = self._uid2idx_event_params.get(vr.uid, None)
                        if e_idx is not None:
                            uid_bindings[vr.uid] = float(self._variable_parameters_values[e_idx])
                    return float(init_eq.eval_uid(uid_bindings))
                except Exception:
                    return None
        return None

    def _compile_mti_inequalities(self) -> None:
        self._mti_inequalities_raw = []
        for blk in self.sys_block.get_all_blocks():
            if hasattr(blk, "inequalities") and blk.inequalities:
                self._mti_inequalities_raw.extend(blk.inequalities)

        self._mti_inequalities_compiled = [self._normalize_inequality_expression(eq) for eq in self._mti_inequalities_raw]
        if len(self._mti_inequalities_compiled) == 0:
            self._rhs_ineq_fn = None
            return

        rms_compiler = RMSCompiler(
            variables=self._state_algeb_vars,
            diff_vars=self._diff_vars,
            v_params=self._variable_parameters,
            c_params=self._constant_parameters,
            dt_var=self._dt,
            compiler_names_dict=self._compiler_names_dict,
        )
        self._rhs_ineq_fn = rms_compiler.compile_rhs(self._mti_inequalities_compiled, "rhs_mti_ineq")
        self._j_ineq_x_fn = rms_compiler.compile_sparse_jacobian(
            eqs=self._mti_inequalities_compiled,
            wrt_vars=self._state_algeb_vars,
            func_name="jac_mti_ineq_x",
        )
        self._j_ineq_dx_fn = rms_compiler.compile_sparse_jacobian(
            eqs=self._mti_inequalities_compiled,
            wrt_vars=self._diff_vars,
            func_name="jac_mti_ineq_dx",
        )

        # Static Jacobians (no chain-rule expansion), analogous to get_E_matrix.
        self._j_ineq_x_static_fn = SymbolicJacobian(
            eqs=self._mti_inequalities_compiled,
            variables=self._state_algeb_vars,
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
            VARS_NAME=self.VARS_NAME,
            DIFF_NAME=self.DIFF_NAME,
            EVENT_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
            PARAMS_NAME=self.CONSTANT_PARAMS_NAME,
            static=True,
        )
        self._j_ineq_dx_static_fn = SymbolicJacobian(
            eqs=self._mti_inequalities_compiled,
            variables=self._diff_vars,
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
            VARS_NAME=self.VARS_NAME,
            DIFF_NAME=self.DIFF_NAME,
            EVENT_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
            PARAMS_NAME=self.CONSTANT_PARAMS_NAME,
            static=True,
        )

    def _compile_mti_equality_jacobians(self) -> None:
        eqs = list(self._state_eqs) + list(self._algebraic_eqs)
        if len(eqs) == 0:
            self._j_eq_x_static_fn = None
            self._j_eq_dx_static_fn = None
            return

        self._j_eq_x_static_fn = SymbolicJacobian(
            eqs=eqs,
            variables=self._state_algeb_vars,
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
            VARS_NAME=self.VARS_NAME,
            DIFF_NAME=self.DIFF_NAME,
            EVENT_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
            PARAMS_NAME=self.CONSTANT_PARAMS_NAME,
            static=True,
        )
        self._j_eq_dx_static_fn = SymbolicJacobian(
            eqs=eqs,
            variables=self._diff_vars,
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
            VARS_NAME=self.VARS_NAME,
            DIFF_NAME=self.DIFF_NAME,
            EVENT_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
            PARAMS_NAME=self.CONSTANT_PARAMS_NAME,
            static=True,
        )

    def _compile_mti_boolean_guards(self) -> None:
        self._mti_bool_param_indices = []
        self._mti_bool_guard_compiled_by_param_idx = {}
        self._mti_bool_guard_var_positions_by_param_idx = {}

        rms_compiler = RMSCompiler(
            variables=self._state_algeb_vars,
            diff_vars=self._diff_vars,
            v_params=self._variable_parameters,
            c_params=self._constant_parameters,
            dt_var=self._dt,
            compiler_names_dict=self._compiler_names_dict,
        )

        for blk in self.sys_block.get_all_blocks():
            for bool_var, guard_expr in blk.boolean_guards.items():
                param_idx = self._mti_bool_uid2param_idx.get(bool_var.uid, None)
                if param_idx is None:
                    continue
                if int(param_idx) not in self._mti_bool_param_indices:
                    self._mti_bool_param_indices.append(int(param_idx))

                guard_residual = self._normalize_inequality_expression(guard_expr)
                self._mti_bool_guard_compiled_by_param_idx[int(param_idx)] = rms_compiler.compile_rhs(
                    [guard_residual],
                    f"rhs_mti_guard_{int(param_idx)}",
                )

                pos = []
                try:
                    for v in get_expression_vars(guard_expr):
                        vidx = self.uid2idx_vars.get(v.uid, None)
                        if vidx is not None:
                            pos.append(int(vidx))
                except Exception:
                    pass
                self._mti_bool_guard_var_positions_by_param_idx[int(param_idx)] = np.asarray(sorted(set(pos)), dtype=int)

        self._mti_bool_param_indices.sort()

    @staticmethod
    def _normalize_inequality_expression(expr: Expr | Comparison) -> Expr:
        if isinstance(expr, Comparison):
            return expr.to_residual()
        if isinstance(expr, Expr):
            return expr
        raise TypeError(f"Unsupported inequality type: {type(expr).__name__}")

    def rhs_inequalities(self, x: Vec, dx: Vec) -> Vec:
        if self._rhs_ineq_fn is None:
            return np.zeros(0, dtype=float)
        return self._rhs_ineq_fn(x, dx, self._variable_parameters_values, self._constant_params)

    def compute_mti_equalities(self, x: Vec, dx: Vec, xn: Vec, h: float) -> Vec:
        """
        Compute equality residual vector F.
        """
        f_algeb = self.rhs_algebraic(x, dx)
        if self.get_states_number() > 0:
            f_state = self.rhs_state(x, dx)
            f_state_update = x[: self.get_states_number()] - xn[: self.get_states_number()] - h * f_state
            return np.r_[f_state_update, f_algeb]
        return np.asarray(f_algeb, dtype=float)

    def compute_mti_inequalities(self, x: Vec, dx: Vec, xn: Vec, h: float) -> Vec:
        """
        Compute inequality vector G (constraint convention: G <= 0).
        """
        return np.asarray(self.rhs_inequalities(x, dx), dtype=float)

    def make_mti_direct_state(self, x_ref: Vec, dx_ref: Vec) -> tuple[Vec, Vec]:
        return np.asarray(x_ref, dtype=float).copy(), np.asarray(dx_ref, dtype=float).copy()

    def mti_direct_pack(self, x: Vec, dx: Vec, var_idx: np.ndarray) -> Vec:
        vals: list[float] = []
        for idx in np.asarray(var_idx, dtype=int):
            col = self._mti_continuous_var_idx_to_col.get(int(idx), None)
            if col is None:
                vals.append(float(np.asarray(x, dtype=float)[int(idx)]))
                continue
            if col < len(self._mti_xp_vars):
                dvar = self._mti_xp_vars[int(col)]
                didx = self._uid2idx_diff.get(dvar.uid, None)
                vals.append(float(np.asarray(dx, dtype=float)[int(didx)]) if didx is not None else 0.0)
            else:
                vals.append(float(np.asarray(x, dtype=float)[int(idx)]))
        return np.asarray(vals, dtype=float)

    def mti_direct_apply(self, w: Vec, x_ref: Vec, dx_ref: Vec, var_idx: np.ndarray) -> tuple[Vec, Vec]:
        x = np.asarray(x_ref, dtype=float).copy()
        dx = np.asarray(dx_ref, dtype=float).copy()
        for val, idx in zip(np.asarray(w, dtype=float), np.asarray(var_idx, dtype=int)):
            col = self._mti_continuous_var_idx_to_col.get(int(idx), None)
            if col is None:
                x[int(idx)] = float(val)
                continue
            if col < len(self._mti_xp_vars):
                dvar = self._mti_xp_vars[int(col)]
                didx = self._uid2idx_diff.get(dvar.uid, None)
                if didx is not None:
                    dx[int(didx)] = float(val)
            else:
                x[int(idx)] = float(val)
        return x, dx

    def compute_mti_direct_equalities(self, x: Vec, dx: Vec) -> Vec:
        f_algeb = self.rhs_algebraic(x, dx)
        if len(self._state_eqs) > 0:
            f_state = self.rhs_state(x, dx)
            return np.r_[f_state, f_algeb]
        return np.asarray(f_algeb, dtype=float)

    def jacobian_mti_direct_equalities(self, x: Vec, dx: Vec, var_idx: np.ndarray) -> sp.csr_matrix:
        rows = len(self._state_eqs) + len(self._algebraic_eqs)
        cols: list[sp.spmatrix] = []
        jx = self._j_eq_x_static_fn(x, dx, self._variable_parameters_values, self._constant_params, 0.0).tocsr() if self._j_eq_x_static_fn is not None else None
        jdx = self._j_eq_dx_static_fn(x, dx, self._variable_parameters_values, self._constant_params, 0.0).tocsr() if self._j_eq_dx_static_fn is not None else None
        for idx in np.asarray(var_idx, dtype=int):
            col = self._mti_continuous_var_idx_to_col.get(int(idx), None)
            if col is not None and col < len(self._mti_xp_vars):
                dvar = self._mti_xp_vars[int(col)]
                didx = self._uid2idx_diff.get(dvar.uid, None)
                cols.append(jdx[:, int(didx)] if (jdx is not None and didx is not None) else sp.csr_matrix((rows, 1)))
            else:
                cols.append(jx[:, int(idx)] if jx is not None else sp.csr_matrix((rows, 1)))
        if len(cols) == 0:
            return sp.csr_matrix((rows, 0))
        return sp.hstack(cols, format="csr")

    def update_mti_boolean_state(self, x: Vec, dx: Vec, xn: Vec, h: float) -> Vec:
        """
        Update MTI boolean parameters using inequality feasibility only.

        This mirrors MTI-style logic where region/mode selection is driven by
        inequality residuals (G <= 0), not by direct boolean guard evaluation.
        """
        if self._variable_parameters_values is None:
            return np.zeros(0, dtype=float)

        idx = self.get_mti_boolean_parameter_indices
        n_bool = len(idx)
        if n_bool == 0:
            return np.zeros(0, dtype=float)

        z_prev = np.array([
            1.0 if float(self._variable_parameters_values[i]) >= 0.5 else 0.0
            for i in idx
        ], dtype=float)

        best_z = z_prev.copy()
        best_violation = np.inf
        best_hamming = np.inf

        for bits in product((0.0, 1.0), repeat=n_bool):
            z_try = np.asarray(bits, dtype=float)
            self.set_mti_boolean_state(z_try)
            g = self.compute_mti_inequalities(x, dx, xn, h)
            violation = float(np.max(g)) if g is not None and len(g) > 0 else -np.inf
            hamming = int(np.sum(z_try != z_prev))

            if (violation < best_violation) or (violation == best_violation and hamming < best_hamming):
                best_violation = violation
                best_hamming = hamming
                best_z = z_try.copy()

        self.set_mti_boolean_state(best_z)
        return best_z

    @property
    def get_mti_boolean_parameter_indices(self) -> list[int]:
        return list(self._mti_bool_param_indices)

    def set_mti_boolean_state(self, z: Vec) -> None:
        idx = self.get_mti_boolean_parameter_indices
        if len(idx) == 0 or self._variable_parameters_values is None:
            return
        for k, i in enumerate(idx):
            self._variable_parameters_values[i] = float(z[k])

    def evaluate_boolean_guard(self, bool_position: int, x: Vec, dx: Vec) -> float | None:
        idx = self.get_mti_boolean_parameter_indices
        if bool_position < 0 or bool_position >= len(idx):
            return None

        param_idx = idx[bool_position]
        guard_fn = self._mti_bool_guard_compiled_by_param_idx.get(param_idx, None)
        if guard_fn is None:
            return None

        out = guard_fn(x, dx, self._variable_parameters_values, self._constant_params)
        if out is None or len(out) == 0:
            return None
        return float(out[0])

    def has_boolean_guard(self, bool_position: int) -> bool:
        idx = self.get_mti_boolean_parameter_indices
        if bool_position < 0 or bool_position >= len(idx):
            return False
        return idx[bool_position] in self._mti_bool_guard_compiled_by_param_idx

    def split_direct_and_coupled_booleans(self) -> tuple[list[int], list[int]]:
        """
        Return all booleans as coupled for inequality-driven MTI selection.
        """
        n_bool = len(self.get_mti_boolean_parameter_indices)
        return [], list(range(n_bool))

    def enumerate_all_boolean_candidates(self) -> list[np.ndarray]:
        n_bool = len(self.get_mti_boolean_parameter_indices)
        if n_bool == 0:
            return [np.zeros(0, dtype=float)]
        return [np.asarray(bits, dtype=float) for bits in product((0.0, 1.0), repeat=n_bool)]

    def total_derivative_inequalities(self, x: Vec, dx: Vec, xpp: Vec | None = None) -> Vec:
        """
        Jacobian-based approximation of dG/dt for active inequality checks.

        Uses dG/dt = (dG/dx) * xdot + (dG/ddx) * xddot.
        When xpp is not available from the event-stage linearization, xpp=0 is
        used as a conservative fallback.
        """
        g0 = self.compute_mti_inequalities(x, dx, x, 0.0)
        if g0 is None or len(g0) == 0:
            return np.zeros(0, dtype=float)

        if self._j_ineq_x_static_fn is None and self._j_ineq_dx_static_fn is None:
            return np.zeros_like(np.asarray(g0, dtype=float))

        x_arr = np.asarray(x, dtype=float)
        dx_arr = np.asarray(dx, dtype=float)
        xpp_arr = np.zeros_like(dx_arr) if xpp is None else np.asarray(xpp, dtype=float)

        dg = np.zeros_like(np.asarray(g0, dtype=float))
        if self._j_ineq_x_static_fn is not None:
            jx = self._j_ineq_x_static_fn(x_arr, dx_arr, self._variable_parameters_values, self._constant_params, 0.0)
            # dG/dx multiplies xdot over the full vars-space. In this solver,
            # `dx` may carry only differential-variable derivatives, so sizes
            # can differ. Build a compatible surrogate xdot to avoid crashes.
            if jx.shape[1] == dx_arr.size:
                xdot_arr = dx_arr
            else:
                xdot_arr = np.zeros(jx.shape[1], dtype=float)
                ncopy = min(jx.shape[1], dx_arr.size)
                if ncopy > 0:
                    xdot_arr[:ncopy] = dx_arr[:ncopy]
            dg = dg + np.asarray(jx @ xdot_arr, dtype=float).reshape(-1)
        if self._j_ineq_dx_static_fn is not None:
            jdx = self._j_ineq_dx_static_fn(x_arr, dx_arr, self._variable_parameters_values, self._constant_params, 0.0)
            if jdx.shape[1] == xpp_arr.size:
                xpp_mul = xpp_arr
            else:
                xpp_mul = np.zeros(jdx.shape[1], dtype=float)
                ncopy = min(jdx.shape[1], xpp_arr.size)
                if ncopy > 0:
                    xpp_mul[:ncopy] = xpp_arr[:ncopy]
            dg = dg + np.asarray(jdx @ xpp_mul, dtype=float).reshape(-1)
        return dg

    def build_mti_incidence_and_order(self, x: Vec, dx: Vec, h: float) -> None:
        self._mti_incidence = self._build_incidence_from_equation_structure()
        n_eq, n_var = self._mti_incidence.shape
        nnz = int(np.count_nonzero(self._mti_incidence))
        print(f"[MTI-INC] shape=({n_eq},{n_var}) nnz={nnz}")
        if n_eq != n_var:
            raise ValueError(
                "MTI incidence must be square: "
                f"n_rows(eq+ineq)={n_eq}, n_cols(xp+y+z)={n_var}. "
                "Check boolean/inequality model balance."
            )
        order = build_connected_subproblem_order(self._mti_incidence)
        if len(order) == 0:
            n_eq, n_vars = self._mti_incidence.shape
            order = build_single_subproblem_order(n_eq=n_eq, n_vars=n_vars)
            print("[MTI-INC] connected-order empty, using single-subproblem fallback")
        self._mti_solving_order = order
        n_sub = len({int(r.subproblem) for r in order}) if len(order) > 0 else 0
        n_subset = len({int(r.subset) for r in order}) if len(order) > 0 else 0
        print(f"[MTI-INC] solving_order_rows={len(order)} subsets={n_subset} subproblems={n_sub}")
        if os.getenv("RMS_MTI_INCIDENCE_DIAG", "0").strip() in ("1", "true", "True", "yes", "on"):
            self.print_mti_incidence_diagnostics()

    def print_mti_solving_order_summary(self) -> None:
        order = list(getattr(self, "_mti_solving_order", []) or [])
        if len(order) == 0:
            print("[MTI-ORDER-DETAIL] empty")
            return

        print("[MTI-ORDER-DETAIL] subproblem decomposition")
        by_subproblem: dict[int, list] = {}
        for row in order:
            by_subproblem.setdefault(int(row.subproblem), []).append(row)

        for sub_id in sorted(by_subproblem):
            rows = by_subproblem[sub_id]
            subsets = sorted(set(int(r.subset) for r in rows))
            n_explicit = sum(1 for r in rows if int(r.explicit) == 1)
            row_counts = {"eq": 0, "ineq": 0, "unknown": 0}
            col_counts = {"xp": 0, "y": 0, "z": 0, "unknown": 0}
            eq_indices: list[int] = []
            ineq_indices: list[int] = []

            for item in rows:
                row_idx = int(item.eq_idx) - 1
                if 0 <= row_idx < len(self._mti_row_meta):
                    kind, local_idx = self._mti_row_meta[row_idx]
                    row_counts[kind if kind in row_counts else "unknown"] += 1
                    if kind == "eq":
                        eq_indices.append(int(local_idx))
                    elif kind == "ineq":
                        ineq_indices.append(int(local_idx))
                else:
                    row_counts["unknown"] += 1

                col_idx = int(item.var_idx) - 1
                if 0 <= col_idx < len(self._mti_col_meta):
                    kind = str(self._mti_col_meta[col_idx][0])
                    col_counts[kind if kind in col_counts else "unknown"] += 1
                else:
                    col_counts["unknown"] += 1

            print(
                f"[MTI-ORDER-DETAIL] subproblem={sub_id} subsets={subsets} rows={len(rows)} "
                f"explicit={n_explicit} eq={row_counts['eq']} ineq={row_counts['ineq']} "
                f"vars_xp={col_counts['xp']} vars_y={col_counts['y']} vars_z={col_counts['z']}"
            )
            if len(eq_indices) > 0:
                print(
                    f"[MTI-ORDER-DETAIL]   eq_range={min(eq_indices)}..{max(eq_indices)} "
                    f"eq_count={len(set(eq_indices))}"
                )
            if len(ineq_indices) > 0:
                print(
                    f"[MTI-ORDER-DETAIL]   ineq_indices={sorted(set(ineq_indices))}"
                )

    def print_mti_incidence_diagnostics(self) -> None:
        inc = self._mti_incidence
        order = list(getattr(self, "_mti_solving_order", []) or [])
        if inc is None or inc.size == 0 or len(order) == 0:
            print("[MTI-DIAG] empty incidence/order")
            return

        by_subproblem: dict[int, list[MTISubProblemRow]] = {}
        for item in order:
            by_subproblem.setdefault(int(item.subproblem), []).append(item)
        largest_sub, largest_rows = max(by_subproblem.items(), key=lambda kv: len(kv[1]))
        block_rows = np.asarray(sorted({int(r.eq_idx) - 1 for r in largest_rows}), dtype=int)
        block_cols = np.asarray(sorted({int(r.var_idx) - 1 for r in largest_rows}), dtype=int)
        block = inc[np.ix_(block_rows, block_cols)] if block_rows.size and block_cols.size else np.zeros((0, 0), dtype=int)

        print(
            f"[MTI-DIAG] largest_subproblem={largest_sub} rows={block_rows.size} "
            f"cols={block_cols.size} nnz={int(np.count_nonzero(block))}"
        )
        self._print_mti_diag_membership(block_rows, block_cols)
        self._print_mti_diag_edge_counts(inc, block_rows, block_cols)
        self._print_mti_diag_ablation_summary(inc)
        self._print_mti_diag_degree_summary(inc, block_rows, block_cols)
        self._print_mti_diag_bridge_candidates(inc, block_rows, block_cols)

    def _print_mti_diag_membership(self, rows: np.ndarray, cols: np.ndarray) -> None:
        row_counts: dict[str, int] = {}
        col_counts: dict[str, int] = {}
        row_preview: list[str] = []
        col_preview: list[str] = []

        for r in rows.tolist():
            label = self._mti_row_kind_label(int(r))
            row_counts[label] = row_counts.get(label, 0) + 1
            if len(row_preview) < 12:
                row_preview.append(self._mti_row_label(int(r)))
        for c in cols.tolist():
            kind = self._mti_col_kind(int(c))
            col_counts[kind] = col_counts.get(kind, 0) + 1
            if len(col_preview) < 12:
                col_preview.append(self._mti_col_label(int(c)))

        print(f"[MTI-DIAG] row_kinds={row_counts}")
        print(f"[MTI-DIAG] col_kinds={col_counts}")
        print(f"[MTI-DIAG] rows_head={row_preview}")
        print(f"[MTI-DIAG] cols_head={col_preview}")

    def _print_mti_diag_edge_counts(self, inc: np.ndarray, rows: np.ndarray, cols: np.ndarray) -> None:
        if rows.size == 0 or cols.size == 0:
            return
        block = inc[np.ix_(rows, cols)]
        counts_by_col_kind: dict[str, int] = {}
        counts_by_row_kind: dict[str, int] = {}
        for local_col, col in enumerate(cols.tolist()):
            kind = self._mti_col_kind(int(col))
            counts_by_col_kind[kind] = counts_by_col_kind.get(kind, 0) + int(np.count_nonzero(block[:, local_col]))
        for local_row, row in enumerate(rows.tolist()):
            kind = self._mti_row_kind_label(int(row))
            counts_by_row_kind[kind] = counts_by_row_kind.get(kind, 0) + int(np.count_nonzero(block[local_row, :]))
        print(f"[MTI-DIAG] block_edges_by_col_kind={counts_by_col_kind}")
        print(f"[MTI-DIAG] block_edges_by_row_kind={counts_by_row_kind}")

    def _print_mti_diag_ablation_summary(self, inc: np.ndarray) -> None:
        ablations: list[tuple[str, np.ndarray]] = [("original", inc.copy())]

        if self._mti_base_xp_incidence_mask is not None and self._mti_base_xp_incidence_mask.shape == inc.shape:
            m = inc.copy()
            m[self._mti_base_xp_incidence_mask] = 0
            ablations.append(("remove_base_x_to_xp_edges", m))

        z_cols = [i for i in range(inc.shape[1]) if self._mti_col_kind(i) == "z"]
        if z_cols:
            m = inc.copy()
            m[:, np.asarray(z_cols, dtype=int)] = 0
            ablations.append(("remove_boolean_columns", m))

        ineq_rows = [i for i in range(inc.shape[0]) if self._mti_row_kind_label(i) == "ineq"]
        if ineq_rows:
            m = inc.copy()
            m[np.asarray(ineq_rows, dtype=int), :] = 0
            ablations.append(("remove_inequality_rows", m))

        network_rows = [i for i in range(inc.shape[0]) if self._mti_row_is_network_like(i, inc)]
        if network_rows:
            m = inc.copy()
            m[np.asarray(network_rows, dtype=int), :] = 0
            ablations.append(("remove_network_like_rows", m))

        branch_rows = [i for i in range(inc.shape[0]) if self._mti_row_is_branch_current_like(i, inc)]
        if branch_rows:
            m = inc.copy()
            m[np.asarray(branch_rows, dtype=int), :] = 0
            ablations.append(("remove_branch_current_like_rows", m))

        print("[MTI-DIAG] component ablations")
        for name, mat in ablations:
            summary = self._mti_bipartite_component_summary(mat)
            print(
                f"[MTI-DIAG]   {name}: row_components={summary['row_components']} "
                f"largest_rows={summary['largest_rows']} sizes_head={summary['sizes_head']} "
                f"nonzero_rows={summary['nonzero_rows']} nonzero_cols={summary['nonzero_cols']}"
            )

    def _print_mti_diag_degree_summary(self, inc: np.ndarray, rows: np.ndarray, cols: np.ndarray) -> None:
        if rows.size == 0 or cols.size == 0:
            return
        block = inc[np.ix_(rows, cols)]
        row_deg = np.asarray(block.sum(axis=1), dtype=int).reshape(-1)
        col_deg = np.asarray(block.sum(axis=0), dtype=int).reshape(-1)
        top_rows = np.argsort(-row_deg, kind="stable")[:15]
        top_cols = np.argsort(-col_deg, kind="stable")[:15]
        print("[MTI-DIAG] high_degree_rows")
        for idx in top_rows.tolist():
            if int(row_deg[idx]) <= 0:
                continue
            print(f"[MTI-DIAG]   degree={int(row_deg[idx])} {self._mti_row_label(int(rows[idx]))}")
        print("[MTI-DIAG] high_degree_cols")
        for idx in top_cols.tolist():
            if int(col_deg[idx]) <= 0:
                continue
            print(f"[MTI-DIAG]   degree={int(col_deg[idx])} {self._mti_col_label(int(cols[idx]))}")

    def _print_mti_diag_bridge_candidates(self, inc: np.ndarray, rows: np.ndarray, cols: np.ndarray) -> None:
        if rows.size == 0 or cols.size == 0:
            return
        block = inc[np.ix_(rows, cols)]
        base = self._mti_bipartite_component_summary(block)
        base_largest = int(base["largest_rows"])
        row_deg = np.asarray(block.sum(axis=1), dtype=int).reshape(-1)
        col_deg = np.asarray(block.sum(axis=0), dtype=int).reshape(-1)
        row_candidates = np.argsort(-row_deg, kind="stable")[:30]
        col_candidates = np.argsort(-col_deg, kind="stable")[:30]

        row_effects: list[tuple[int, int, int, int]] = []
        for idx in row_candidates.tolist():
            if int(row_deg[idx]) <= 0:
                continue
            m = block.copy()
            m[int(idx), :] = 0
            s = self._mti_bipartite_component_summary(m)
            row_effects.append((int(s["row_components"]), base_largest - int(s["largest_rows"]), int(row_deg[idx]), int(idx)))

        col_effects: list[tuple[int, int, int, int]] = []
        for idx in col_candidates.tolist():
            if int(col_deg[idx]) <= 0:
                continue
            m = block.copy()
            m[:, int(idx)] = 0
            s = self._mti_bipartite_component_summary(m)
            col_effects.append((int(s["row_components"]), base_largest - int(s["largest_rows"]), int(col_deg[idx]), int(idx)))

        row_effects.sort(reverse=True)
        col_effects.sort(reverse=True)
        print("[MTI-DIAG] row_bridge_candidates")
        for comps, largest_drop, degree, idx in row_effects[:10]:
            print(
                f"[MTI-DIAG]   comps_after={comps} largest_drop={largest_drop} "
                f"degree={degree} {self._mti_row_label(int(rows[idx]))}"
            )
        print("[MTI-DIAG] col_bridge_candidates")
        for comps, largest_drop, degree, idx in col_effects[:10]:
            print(
                f"[MTI-DIAG]   comps_after={comps} largest_drop={largest_drop} "
                f"degree={degree} {self._mti_col_label(int(cols[idx]))}"
            )

    def _mti_bipartite_component_summary(self, incidence: np.ndarray) -> dict[str, object]:
        mat = (np.asarray(incidence) != 0).astype(int)
        n_row, n_col = mat.shape
        if n_row == 0 or n_col == 0:
            return {"row_components": 0, "largest_rows": 0, "sizes_head": [], "nonzero_rows": 0, "nonzero_cols": 0}

        coo = sp.coo_matrix(mat)
        upper = sp.csr_matrix((np.ones(coo.nnz, dtype=int), (coo.row, n_row + coo.col)), shape=(n_row + n_col, n_row + n_col))
        graph = upper + upper.T
        n_comp, labels = connected_components(graph, directed=False, return_labels=True)
        row_deg = np.asarray(mat.sum(axis=1), dtype=int).reshape(-1)
        col_deg = np.asarray(mat.sum(axis=0), dtype=int).reshape(-1)
        active_rows = np.where(row_deg > 0)[0]
        active_cols = np.where(col_deg > 0)[0]

        sizes: list[int] = []
        for comp in range(int(n_comp)):
            row_count = int(np.sum(labels[:n_row] == comp))
            col_count = int(np.sum(labels[n_row:] == comp))
            if row_count > 0 and col_count > 0:
                sizes.append(row_count)
        sizes.sort(reverse=True)
        return {
            "row_components": len(sizes),
            "largest_rows": sizes[0] if sizes else 0,
            "sizes_head": sizes[:8],
            "nonzero_rows": int(active_rows.size),
            "nonzero_cols": int(active_cols.size),
        }

    def _mti_row_kind_label(self, row: int) -> str:
        if 0 <= row < len(self._mti_row_meta):
            kind, local_idx = self._mti_row_meta[row]
            if kind == "eq":
                n_state = len(self._state_eqs)
                return "state_eq" if int(local_idx) < n_state else "alg_eq"
            return str(kind)
        return "unknown"

    def _mti_row_label(self, row: int) -> str:
        if 0 <= row < len(self._mti_row_meta):
            kind, local_idx = self._mti_row_meta[row]
            if kind == "eq":
                n_state = len(self._state_eqs)
                if int(local_idx) < n_state:
                    return f"row={row}:state_eq[{int(local_idx)}]"
                return f"row={row}:alg_eq[{int(local_idx) - n_state}]"
            return f"row={row}:ineq[{int(local_idx)}]"
        return f"row={row}:unknown"

    def _mti_col_kind(self, col: int) -> str:
        if 0 <= col < len(self._mti_col_meta):
            return str(self._mti_col_meta[col][0])
        return "unknown"

    def _mti_col_label(self, col: int) -> str:
        if 0 <= col < len(self._mti_col_meta):
            kind, local_idx, obj = self._mti_col_meta[col]
            return f"col={col}:{kind}[{int(local_idx)}]:{self._mti_obj_name(obj)}"
        return f"col={col}:unknown"

    @staticmethod
    def _mti_obj_name(obj: object | None) -> str:
        if obj is None:
            return "None"
        for attr in ("name", "idtag", "code", "device", "label"):
            val = getattr(obj, attr, None)
            if val is not None:
                text = str(val)
                if len(text) > 0:
                    return text
        return type(obj).__name__

    def _mti_row_is_network_like(self, row: int, inc: np.ndarray) -> bool:
        if self._mti_row_kind_label(row) != "alg_eq":
            return False
        cols = np.where(inc[int(row), :] != 0)[0]
        names = [self._mti_col_label(int(c)) for c in cols.tolist()]
        return any(":Vr" in name or ":Vi" in name or "Vr" in name or "Vi" in name for name in names)

    def _mti_row_is_branch_current_like(self, row: int, inc: np.ndarray) -> bool:
        if self._mti_row_kind_label(row) != "alg_eq":
            return False
        cols = np.where(inc[int(row), :] != 0)[0]
        names = [self._mti_col_label(int(c)) for c in cols.tolist()]
        needles = ("Irf", "Iif", "Irt", "Iit", "branch")
        return any(any(needle in name for needle in needles) for name in names)

    def _build_incidence_from_equation_structure(self) -> np.ndarray:
        """
        Build incidence structurally from equation-variable membership.

        MTI-toolbox-like layout:
            rows = [equalities; inequalities]
            cols = [state-derivative unknowns xp; algebraic unknowns y; booleans z]

        Entry (i, j) is 1 if unknown j appears structurally in equation i.
        """
        n_state_eq = len(self._state_eqs)
        n_alg = len(self._algebraic_eqs)
        n_eq = n_state_eq + n_alg
        n_ineq = len(self._mti_inequalities_compiled)
        state_diff_vars = self._mti_state_diff_vars()
        mti_alg_vars = self._mti_algebraic_vars()
        n_xp = len(state_diff_vars)
        n_y = len(mti_alg_vars)

        bool_param_indices = list(self.get_mti_boolean_parameter_indices)
        n_bool = len(bool_param_indices)
        n_col = n_xp + n_y + n_bool
        include_ineq_rows = True
        self._mti_incidence_includes_inequalities = True

        diff_uid_to_xp_col: dict[int, int] = {}
        base_uid_to_xp_col: dict[int, int] = {}
        for k, dvar in enumerate(state_diff_vars):
            diff_uid_to_xp_col[dvar.uid] = k
            base_var = dvar.base_var
            if base_var is not None:
                base_uid_to_xp_col[base_var.uid] = k

        alg_uid_to_y_col: dict[int, int] = {}
        for k, var in enumerate(mti_alg_vars):
            alg_uid_to_y_col[var.uid] = k

        # Map boolean UID -> local boolean-column index
        bool_uid_to_local_col: dict[int, int] = {}
        for k, pidx in enumerate(bool_param_indices):
            if 0 <= int(pidx) < len(self._variable_parameters):
                bvar = self._variable_parameters[int(pidx)]
                bool_uid_to_local_col[bvar.uid] = k

        self._mti_xp_vars = list(state_diff_vars)
        self._mti_y_vars = list(mti_alg_vars)
        self._mti_incidence_bool_param_indices = [int(i) for i in bool_param_indices]
        self._mti_diff_uid_to_xp_col = dict(diff_uid_to_xp_col)
        self._mti_base_uid_to_xp_col = dict(base_uid_to_xp_col)
        self._mti_alg_uid_to_y_col = dict(alg_uid_to_y_col)
        self._mti_bool_uid_to_local_col = dict(bool_uid_to_local_col)

        off_diff = 0
        off_alg = n_xp
        off_bool = n_xp + n_y
        n_rows = n_eq + (n_ineq if include_ineq_rows else 0)
        incidence_matrix = np.zeros((n_rows, n_col), dtype=int)
        base_xp_mask = np.zeros((n_rows, n_col), dtype=bool)

        self._mti_col_meta = []
        self._mti_continuous_var_idx_to_col = {}
        self._mti_col_to_continuous_var_idx_map = {}
        for k, dvar in enumerate(state_diff_vars):
            self._mti_col_meta.append(("xp", k, dvar))
            base_var = getattr(dvar, "base_var", None)
            if base_var is not None:
                var_idx = self.uid2idx_vars.get(base_var.uid, None)
                if var_idx is not None:
                    self._mti_continuous_var_idx_to_col[int(var_idx)] = off_diff + k
                    self._mti_col_to_continuous_var_idx_map[off_diff + k] = int(var_idx)
        for k, var in enumerate(mti_alg_vars):
            self._mti_col_meta.append(("y", k, var))
            var_idx = self.uid2idx_vars.get(var.uid, None)
            if var_idx is not None:
                self._mti_continuous_var_idx_to_col[int(var_idx)] = off_alg + k
                self._mti_col_to_continuous_var_idx_map[off_alg + k] = int(var_idx)
        for k, pidx in enumerate(bool_param_indices):
            bvar = self._variable_parameters[int(pidx)] if 0 <= int(pidx) < len(self._variable_parameters) else None
            self._mti_col_meta.append(("z", int(pidx), bvar))

        self._mti_row_meta = [("eq", i) for i in range(n_eq)]
        if include_ineq_rows:
            self._mti_row_meta.extend(("ineq", i) for i in range(n_ineq))

        # State equations: toolbox-style structural dependency from the
        # symbolic RHS only (no implicit BE identity injection).
        for i, eq in enumerate(self._state_eqs):
            for v in get_expression_vars(eq):
                if v.uid in diff_uid_to_xp_col:
                    incidence_matrix[i, off_diff + int(diff_uid_to_xp_col[v.uid])] = 1
                elif v.uid in base_uid_to_xp_col:
                    col = off_diff + int(base_uid_to_xp_col[v.uid])
                    incidence_matrix[i, col] = 1
                    base_xp_mask[i, col] = True
                elif v.uid in alg_uid_to_y_col:
                    incidence_matrix[i, off_alg + int(alg_uid_to_y_col[v.uid])] = 1
                elif v.uid in bool_uid_to_local_col:
                    incidence_matrix[i, off_bool + int(bool_uid_to_local_col[v.uid])] = 1

        # Algebraic equations
        for j, eq in enumerate(self._algebraic_eqs):
            row = n_state_eq + j
            for v in get_expression_vars(eq):
                if v.uid in diff_uid_to_xp_col:
                    incidence_matrix[row, off_diff + int(diff_uid_to_xp_col[v.uid])] = 1
                elif v.uid in base_uid_to_xp_col:
                    col = off_diff + int(base_uid_to_xp_col[v.uid])
                    incidence_matrix[row, col] = 1
                    base_xp_mask[row, col] = True
                elif v.uid in alg_uid_to_y_col:
                    incidence_matrix[row, off_alg + int(alg_uid_to_y_col[v.uid])] = 1
                elif v.uid in bool_uid_to_local_col:
                    incidence_matrix[row, off_bool + int(bool_uid_to_local_col[v.uid])] = 1

        if include_ineq_rows:
            # Inequalities
            for j, ineq in enumerate(self._mti_inequalities_compiled):
                row = n_eq + j
                for v in get_expression_vars(ineq):
                    if v.uid in diff_uid_to_xp_col:
                        incidence_matrix[row, off_diff + int(diff_uid_to_xp_col[v.uid])] = 1
                    elif v.uid in base_uid_to_xp_col:
                        col = off_diff + int(base_uid_to_xp_col[v.uid])
                        incidence_matrix[row, col] = 1
                        base_xp_mask[row, col] = True
                    elif v.uid in alg_uid_to_y_col:
                        incidence_matrix[row, off_alg + int(alg_uid_to_y_col[v.uid])] = 1
                    elif v.uid in bool_uid_to_local_col:
                        incidence_matrix[row, off_bool + int(bool_uid_to_local_col[v.uid])] = 1

        nnz = int(np.count_nonzero(incidence_matrix))
        print(
            "[MTI-INC] blocks "
            f"eq={n_eq} ineq={n_ineq} ineq_rows={int(include_ineq_rows)} "
            f"xp={n_xp} y={n_y} bool={n_bool} nnz={nnz}"
        )
        self._mti_base_xp_incidence_mask = base_xp_mask
        return incidence_matrix

    def get_mti_solving_order(self) -> list[MTISubProblemRow]:
        return list(self._mti_solving_order)

    def _mti_state_diff_vars(self) -> list[object]:
        """State derivative unknowns xp are DiffVars with an explicit base_var."""
        return [v for v in self._diff_vars if v.base_var is not None]

    def _mti_state_base_uids(self) -> set[int]:
        return {v.base_var.uid for v in self._mti_state_diff_vars() if v.base_var is not None}

    def _mti_algebraic_vars(self) -> list[object]:
        """MTI algebraic unknowns y are continuous vars excluding state bases."""
        state_base_uids = self._mti_state_base_uids()
        return [v for v in self._state_algeb_vars if v.uid not in state_base_uids]

    def _continuous_var_idx_to_mti_col(self, var_idx: int) -> int | None:
        """Map full continuous x-vector index to MTI incidence column [xp;y;z]."""
        if int(var_idx) < 0 or int(var_idx) >= self.get_all_vars_number():
            return None
        return self._mti_continuous_var_idx_to_col.get(int(var_idx), None)

    def _mti_col_to_continuous_var_idx(self, col_idx: int) -> int | None:
        """Map MTI incidence column [xp;y;z] to full continuous x-vector index."""
        return self._mti_col_to_continuous_var_idx_map.get(int(col_idx), None)

    def get_equality_row_indices(self, row_idx: np.ndarray) -> np.ndarray:
        """Map MTI incidence row indices to equality residual row indices."""
        if len(self._mti_row_meta) == 0:
            n_eq = self.get_states_number() + len(self._algebraic_eqs)
            rows = np.asarray(row_idx, dtype=int)
            return np.asarray(sorted(set(int(r) for r in rows if 0 <= int(r) < n_eq)), dtype=int)
        out: list[int] = []
        for row in np.asarray(row_idx, dtype=int):
            r = int(row)
            if 0 <= r < len(self._mti_row_meta):
                kind, local_idx = self._mti_row_meta[r]
                if kind == "eq":
                    out.append(int(local_idx))
        return np.asarray(sorted(set(out)), dtype=int)

    def get_continuous_equality_row_indices(self, row_idx: np.ndarray) -> np.ndarray:
        """Return equality rows that still involve continuous unknowns [xp;y]."""
        eq_rows = self.get_equality_row_indices(row_idx)
        if self._mti_incidence is None or eq_rows.size == 0:
            return eq_rows
        n_cont_cols = len(self._mti_xp_vars) + len(self._mti_y_vars)
        if n_cont_cols <= 0:
            return np.zeros(0, dtype=int)

        out: list[int] = []
        for eq_local in eq_rows:
            inc_row = int(eq_local)
            if 0 <= inc_row < self._mti_incidence.shape[0]:
                if np.any(self._mti_incidence[inc_row, :n_cont_cols] != 0):
                    out.append(int(eq_local))
        return np.asarray(sorted(set(out)), dtype=int)

    def get_fixed_boolean_equality_row_indices(self, row_idx: np.ndarray) -> np.ndarray:
        """Return equality rows that only constrain fixed boolean columns."""
        eq_rows = self.get_equality_row_indices(row_idx)
        cont_rows = set(self.get_continuous_equality_row_indices(row_idx).tolist())
        return np.asarray([int(r) for r in eq_rows if int(r) not in cont_rows], dtype=int)

    def get_inequality_row_indices(self, row_idx: np.ndarray) -> np.ndarray:
        """Map MTI incidence row indices to inequality residual row indices."""
        if len(self._mti_row_meta) == 0:
            return np.zeros(0, dtype=int)
        out: list[int] = []
        for row in np.asarray(row_idx, dtype=int):
            r = int(row)
            if 0 <= r < len(self._mti_row_meta):
                kind, local_idx = self._mti_row_meta[r]
                if kind == "ineq":
                    out.append(int(local_idx))
        return np.asarray(sorted(set(out)), dtype=int)

    def get_event_solving_stages(self, ineq_idx: int) -> tuple[list[tuple[np.ndarray, np.ndarray]], list[tuple[np.ndarray, np.ndarray]], list[tuple[np.ndarray, np.ndarray]]]:
        """
        Return (previous, event, following) stage groups from current solving order.

        Each group entry is (eq_indices0, var_indices0) with 0-based indices.
        """
        debug = os.getenv("RMS_MTI_DEBUG", "0").strip() in ("1", "true", "True", "yes", "on")

        if self._mti_incidence is None or len(self._mti_solving_order) == 0:
            n = self.get_all_vars_number()
            all_idx = np.arange(n, dtype=int)
            if debug:
                print("[MTI-STAGE] no incidence/solving order, returning full fallback stage")
            return ([(all_idx, all_idx)], [(all_idx, all_idx)], [])

        if ineq_idx < 0 or ineq_idx >= len(self._ineq_var_positions):
            n = self.get_all_vars_number()
            all_idx = np.arange(n, dtype=int)
            if debug:
                print(f"[MTI-STAGE] invalid ineq_idx={ineq_idx}, using full fallback stage")
            return ([(all_idx, all_idx)], [(all_idx, all_idx)], [])

        rows = self._mti_solving_order
        n_eq = self.get_states_number() + len(self._algebraic_eqs)
        ineq_row = n_eq + int(ineq_idx)
        event_rows = [r for r in rows if (int(r.eq_idx) - 1) == ineq_row]
        if len(event_rows) == 0:
            n = self.get_all_vars_number()
            all_idx = np.arange(n, dtype=int)
            if debug:
                print(f"[MTI-STAGE] ineq_idx={ineq_idx} no inequality-row hit, using full fallback stage")
            return ([(all_idx, all_idx)], [(all_idx, all_idx)], [])

        event_subproblem = int(event_rows[0].subproblem)
        event_subset = int(event_rows[0].subset)

        group_map: dict[int, tuple[set[int], set[int], int]] = {}
        for i, r in enumerate(rows):
            spid = int(r.subproblem)
            if spid not in group_map:
                group_map[spid] = (set(), set(), i)
            eqs, vars_, first_i = group_map[spid]
            eqs.add(int(r.eq_idx) - 1)
            vars_.add(int(r.var_idx) - 1)
            if i < first_i:
                first_i = i
            group_map[spid] = (eqs, vars_, first_i)

        ordered = sorted([(spid, data[2], data[0], data[1]) for spid, data in group_map.items()], key=lambda x: x[1])

        previous: list[tuple[np.ndarray, np.ndarray]] = []
        event: list[tuple[np.ndarray, np.ndarray]] = []
        following: list[tuple[np.ndarray, np.ndarray]] = []
        for spid, _, eqs, vars_ in ordered:
            # Solver state vector only contains continuous vars; drop boolean
            # incidence columns from stage var-index sets and map [xp;y] to x.
            vars_cont = sorted({
                mapped
                for mapped in (self._mti_col_to_continuous_var_idx(int(v)) for v in vars_)
                if mapped is not None
            })
            item = (np.asarray(sorted(eqs), dtype=int), np.asarray(vars_cont, dtype=int))
            if int(spid) < event_subproblem:
                previous.append(item)
            elif int(spid) == event_subproblem:
                event.append(item)
            else:
                following.append(item)

        if len(event) == 0:
            n = self.get_all_vars_number()
            all_idx = np.arange(n, dtype=int)
            if debug:
                print(f"[MTI-STAGE] ineq_idx={ineq_idx} empty event group, fallback to full event stage")
            return (previous if len(previous) > 0 else [(all_idx, all_idx)], [(all_idx, all_idx)], following)

        if debug:
            print(
                f"[MTI-STAGE] ineq_idx={ineq_idx} row={ineq_row} subset={event_subset} "
                f"subproblem={event_subproblem} prev={len(previous)} event={len(event)} foll={len(following)}"
            )

        return previous, event, following

    def get_event_subset_ids(self, ineq_idx: int) -> set[int]:
        """Return solving-order subset ids touched by an inequality."""
        if self._mti_incidence is None or len(self._mti_solving_order) == 0:
            return set()
        if ineq_idx < 0 or ineq_idx >= len(self._ineq_var_positions):
            return set()
        touched_vars = self._ineq_var_positions[ineq_idx]
        if touched_vars.size == 0:
            return set()
        touched_cols = {
            col for col in (self._continuous_var_idx_to_mti_col(int(v)) for v in touched_vars) if col is not None
        }
        return {int(r.subset) for r in self._mti_solving_order if (int(r.var_idx) - 1) in touched_cols}

    def get_group_subset_ids(self, eq_idx: np.ndarray, var_idx: np.ndarray) -> set[int]:
        """Return solving-order subset ids touched by a stage group."""
        if len(self._mti_solving_order) == 0:
            return set()
        eq_set = set(np.asarray(eq_idx, dtype=int).tolist())
        col_set = {
            col for col in (self._continuous_var_idx_to_mti_col(int(v)) for v in np.asarray(var_idx, dtype=int)) if col is not None
        }
        return {
            int(r.subset)
            for r in self._mti_solving_order
            if (int(r.eq_idx) - 1) in eq_set or (int(r.var_idx) - 1) in col_set
        }

    def get_subproblem_boolean_positions(self, eq_idx: np.ndarray, var_idx: np.ndarray) -> list[int]:
        """
        Return local boolean positions structurally coupled to a subproblem.

        The solver works in continuous variable space, while the MTI incidence
        matrix is [diff vars; continuous vars; booleans]. This method maps a
        continuous subproblem back to boolean incidence columns so following
        subproblems can use toolbox-like variable-z propagation.
        """
        if self._mti_incidence is None:
            return []

        n_xp = len(self._mti_state_diff_vars())
        n_y = len(self._mti_algebraic_vars())
        bool_idx = list(self.get_mti_boolean_parameter_indices)
        if len(bool_idx) == 0:
            return []

        bool_col0 = n_xp + n_y
        eq_idx_arr = np.asarray(eq_idx, dtype=int)
        var_idx_arr = np.asarray(var_idx, dtype=int)
        row_hits = set(eq_idx_arr[(eq_idx_arr >= 0) & (eq_idx_arr < self._mti_incidence.shape[0])].tolist())
        cont_cols = {
            col for col in (self._continuous_var_idx_to_mti_col(int(v)) for v in var_idx_arr) if col is not None
        }

        if len(cont_cols) > 0:
            for row in self._mti_solving_order:
                if (int(row.var_idx) - 1) in cont_cols:
                    row_hits.add(int(row.eq_idx) - 1)

        out: list[int] = []
        for k in range(len(bool_idx)):
            col = bool_col0 + k
            if col >= self._mti_incidence.shape[1]:
                continue
            if any(self._mti_incidence[r, col] != 0 for r in row_hits):
                out.append(k)
        return out

    def split_explicit_subproblem_pairs(
        self,
        eq_idx: np.ndarray,
        var_idx: np.ndarray,
    ) -> tuple[list[tuple[int, int]], np.ndarray, np.ndarray]:
        """
        Split a subproblem into toolbox-marked explicit pairs and implicit rest.

        Returns explicit (eq0, var0) pairs in continuous variable space, followed
        by remaining equation and continuous-variable indices.
        """
        if len(self._mti_solving_order) == 0:
            return [], np.asarray(eq_idx, dtype=int), np.asarray(var_idx, dtype=int)

        eq_set = set(np.asarray(eq_idx, dtype=int).tolist())
        var_set = set(np.asarray(var_idx, dtype=int).tolist())
        n_xp = len(self._mti_state_diff_vars())
        n_y = len(self._mti_algebraic_vars())

        pairs: list[tuple[int, int]] = []
        used_eq: set[int] = set()
        used_var: set[int] = set()
        for row in self._mti_solving_order:
            if int(row.explicit) != 1:
                continue
            eq0 = int(row.eq_idx) - 1
            col0 = int(row.var_idx) - 1
            if not (0 <= col0 < n_xp + n_y):
                continue
            mapped = self._mti_col_to_continuous_var_idx(col0)
            if mapped is None:
                continue
            var0 = int(mapped)
            if eq0 in eq_set and var0 in var_set:
                pairs.append((eq0, var0))
                used_eq.add(eq0)
                used_var.add(var0)

        rest_eq = np.asarray([i for i in np.asarray(eq_idx, dtype=int) if int(i) not in used_eq], dtype=int)
        rest_var = np.asarray([i for i in np.asarray(var_idx, dtype=int) if int(i) not in used_var], dtype=int)
        return pairs, rest_eq, rest_var

    def _build_inequality_variable_positions(self) -> None:
        self._ineq_var_positions = []
        self._ineq_bool_positions = []
        bool_param_indices = list(self.get_mti_boolean_parameter_indices)
        bool_uid_to_position = {
            getattr(self._variable_parameters[int(param_idx)], "uid", None): int(k)
            for k, param_idx in enumerate(bool_param_indices)
            if 0 <= int(param_idx) < len(self._variable_parameters)
        }
        for ineq in self._mti_inequalities_raw:
            pos = []
            bool_pos = []
            for v in get_expression_vars(ineq):
                idx = self.uid2idx_vars.get(v.uid, None)
                if idx is not None:
                    pos.append(int(idx))
                bpos = bool_uid_to_position.get(v.uid, None)
                if bpos is not None:
                    bool_pos.append(int(bpos))
            self._ineq_var_positions.append(np.asarray(sorted(set(pos)), dtype=int))
            self._ineq_bool_positions.append(np.asarray(sorted(set(bool_pos)), dtype=int))

    def get_event_local_boolean_candidates(self, ineq_idx: int, z_prev: Vec) -> list[np.ndarray]:
        """
        Enumerate boolean candidates local to the subset touched by inequality.

        Prefer direct guard/inequality variable overlap. A coarse solving order
        can collapse to one subset, and using that subset would enumerate every
        boolean in the model.
        """
        debug = os.getenv("RMS_MTI_DEBUG", "0").strip() in ("1", "true", "True", "yes", "on")
        n_bool = len(self.get_mti_boolean_parameter_indices)
        if n_bool == 0:
            if debug:
                print("[MTI-LOC-CAND] n_bool=0 -> single empty candidate")
            return [np.zeros(0, dtype=float)]

        if self._mti_incidence is None or len(self._mti_solving_order) == 0:
            if debug:
                print("[MTI-LOC-CAND] no incidence/order -> keep previous z")
            return [np.asarray(z_prev, dtype=float).copy()]

        if ineq_idx < 0 or ineq_idx >= len(self._ineq_var_positions):
            if debug:
                print(f"[MTI-LOC-CAND] invalid ineq_idx={ineq_idx} -> keep previous z")
            return [np.asarray(z_prev, dtype=float).copy()]

        touched_vars = self._ineq_var_positions[ineq_idx]
        if touched_vars.size == 0:
            if debug:
                print(f"[MTI-LOC-CAND] ineq_idx={ineq_idx} touched_vars empty -> keep previous z")
            return [np.asarray(z_prev, dtype=float).copy()]

        idx = self.get_mti_boolean_parameter_indices
        touched_var_set = set(np.asarray(touched_vars, dtype=int).tolist())
        direct_positions: list[int] = []
        for k, param_idx in enumerate(idx):
            bool_vars = self._mti_bool_guard_var_positions_by_param_idx.get(int(param_idx), np.zeros(0, dtype=int))
            if bool_vars.size == 0:
                continue
            if len(set(np.asarray(bool_vars, dtype=int).tolist()) & touched_var_set) > 0:
                direct_positions.append(k)

        ineq_bool_positions = getattr(self, "_ineq_bool_positions", [])
        if ineq_idx < len(ineq_bool_positions):
            direct_ineq_positions = [int(i) for i in np.asarray(ineq_bool_positions[ineq_idx], dtype=int)]
        else:
            direct_ineq_positions = []

        if len(direct_positions) > 0:
            local_positions = sorted(set(direct_positions) | set(direct_ineq_positions))
        else:
            local_positions = direct_ineq_positions

        subset_ids = set()
        touched_cols = {
            col for col in (self._continuous_var_idx_to_mti_col(int(v)) for v in touched_vars) if col is not None
        }
        for row in self._mti_solving_order:
            if (row.var_idx - 1) in touched_cols:
                subset_ids.add(row.subset)
        if len(subset_ids) == 0:
            if debug:
                print(f"[MTI-LOC-CAND] ineq_idx={ineq_idx} no subset hit -> keep previous z")
            return [np.asarray(z_prev, dtype=float).copy()]

        subset_to_vars: dict[int, set[int]] = {}
        for row in self._mti_solving_order:
            subset_to_vars.setdefault(int(row.subset), set()).add(int(row.var_idx) - 1)

        event_vars: set[int] = set()
        for sid in subset_ids:
            event_vars |= subset_to_vars.get(int(sid), set())

        if len(local_positions) == 0:
            for k, param_idx in enumerate(idx):
                bool_vars = self._mti_bool_guard_var_positions_by_param_idx.get(int(param_idx), np.zeros(0, dtype=int))
                if bool_vars.size == 0:
                    continue
                bool_cols = {
                    col for col in (self._continuous_var_idx_to_mti_col(int(v)) for v in np.asarray(bool_vars, dtype=int)) if col is not None
                }
                if len(bool_cols & event_vars) > 0:
                    local_positions.append(k)

        if len(local_positions) == 0:
            if debug:
                print(f"[MTI-LOC-CAND] ineq_idx={ineq_idx} no local bool positions -> keep previous z")
            return [np.asarray(z_prev, dtype=float).copy()]

        max_local = int(os.getenv("RMS_MTI_MAX_LOCAL_BOOL_ENUM", "16"))
        if len(local_positions) > max_local:
            if len(direct_positions) > 0 and len(direct_positions) <= max_local:
                local_positions = direct_positions
            else:
                if debug:
                    print(
                        f"[MTI-LOC-CAND] ineq_idx={ineq_idx} local={len(local_positions)} "
                        f"exceeds max={max_local} -> keep previous z"
                    )
                return [np.asarray(z_prev, dtype=float).copy()]

        z_prev_arr = np.asarray(z_prev, dtype=float)
        out: list[np.ndarray] = []
        for bits in product((0.0, 1.0), repeat=len(local_positions)):
            z = z_prev_arr.copy()
            for k, p in enumerate(local_positions):
                z[p] = float(bits[k])
            out.append(z)
        if debug:
            print(
                f"[MTI-LOC-CAND] ineq_idx={ineq_idx} n_bool={n_bool} local={len(local_positions)} "
                f"candidates={len(out)}"
            )
        return out

    def evaluate_mti_step(self, x: Vec, dx: Vec, xn: Vec, h: float) -> Tuple[Vec, Vec, Vec]:
        """
        Evaluate one MTI step and return (F, G, z).
        """
        f = self.compute_mti_equalities(x, dx, xn, h)
        g = self.compute_mti_inequalities(x, dx, xn, h)
        z = self.update_mti_boolean_state(x, dx, xn, h)
        return f, g, z

    @staticmethod
    def inequalities_satisfied(g: Vec, tol: float = 1e-9) -> bool:
        """
        Check if all inequalities satisfy G <= tol.
        """
        if g is None or len(g) == 0:
            return True
        return bool(np.all(np.asarray(g) <= tol))
