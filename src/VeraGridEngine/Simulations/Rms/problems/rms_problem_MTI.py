# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple
import os
from itertools import product

import numpy as np

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
        self._mti_bool_param_indices: list[int] = []
        self._mti_bool_guard_compiled_by_param_idx: dict[int, object] = {}
        self._mti_bool_guard_var_positions_by_param_idx: dict[int, np.ndarray] = {}
        self._compile_mti_inequalities()
        self._compile_mti_boolean_guards()
        self._initialize_mti_booleans_at_t0()
        self._mti_incidence: np.ndarray | None = None
        self._mti_solving_order: list[MTISubProblemRow] = []
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
                    # Guard residual convention in MTI is G <= 0 when condition holds.
                    z0[k] = 1.0 if guard_val <= 0.0 else 0.0
            if debug:
                print(f"[MTI-INIT] bool_pos={k} param_idx={idx[k]} guard={guard_val} init_eq={init_val} z0={z0[k]}")

        self.set_mti_boolean_state(z0)
        if debug:
            print("[MTI-INIT] initial z0:", z0)

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
        order = build_connected_subproblem_order(self._mti_incidence)
        if len(order) == 0:
            n_eq, n_vars = self._mti_incidence.shape
            order = build_single_subproblem_order(n_eq=n_eq, n_vars=n_vars)
            print("[MTI-INC] connected-order empty, using single-subproblem fallback")
        self._mti_solving_order = order
        n_sub = len({int(r.subproblem) for r in order}) if len(order) > 0 else 0
        n_subset = len({int(r.subset) for r in order}) if len(order) > 0 else 0
        print(f"[MTI-INC] solving_order_rows={len(order)} subsets={n_subset} subproblems={n_sub}")

    def _build_incidence_from_equation_structure(self) -> np.ndarray:
        """
        Build incidence structurally from equation-variable membership.

        MTI-toolbox-like layout:
            rows = [equalities; inequalities]
            cols = [diff vars; continuous vars; booleans]

        Entry (i, j) is 1 if unknown j appears structurally in equation i.
        """
        n_state = self.get_states_number()
        n_alg = len(self._algebraic_eqs)
        n_eq = n_state + n_alg
        n_ineq = len(self._mti_inequalities_compiled)
        n_diff = self.get_diff_var_number()
        n_vars = self.get_all_vars_number()

        bool_param_indices = list(self.get_mti_boolean_parameter_indices)
        n_bool = len(bool_param_indices)

        # Map boolean UID -> local boolean-column index
        bool_uid_to_local_col: dict[int, int] = {}
        for k, pidx in enumerate(bool_param_indices):
            if 0 <= int(pidx) < len(self._variable_parameters):
                bvar = self._variable_parameters[int(pidx)]
                bool_uid_to_local_col[bvar.uid] = k

        off_diff = 0
        off_vars = n_diff
        off_bool = n_diff + n_vars
        incidence_matrix = np.zeros((n_eq + n_ineq, n_diff + n_vars + n_bool), dtype=int)

        # State equations: toolbox-style structural dependency from the
        # symbolic RHS only (no implicit BE identity injection).
        for i, eq in enumerate(self._state_eqs):
            for v in get_expression_vars(eq):
                didx = self._uid2idx_diff.get(v.uid, None)
                if didx is not None:
                    incidence_matrix[i, off_diff + int(didx)] = 1
                    continue
                idx = self.uid2idx_vars.get(v.uid, None)
                if idx is not None:
                    incidence_matrix[i, off_vars + int(idx)] = 1
                    continue
                bcol = bool_uid_to_local_col.get(v.uid, None)
                if bcol is not None:
                    incidence_matrix[i, off_bool + int(bcol)] = 1

        # Algebraic equations
        for j, eq in enumerate(self._algebraic_eqs):
            row = n_state + j
            for v in get_expression_vars(eq):
                didx = self._uid2idx_diff.get(v.uid, None)
                if didx is not None:
                    incidence_matrix[row, off_diff + int(didx)] = 1
                    continue
                idx = self.uid2idx_vars.get(v.uid, None)
                if idx is not None:
                    incidence_matrix[row, off_vars + int(idx)] = 1
                    continue
                bcol = bool_uid_to_local_col.get(v.uid, None)
                if bcol is not None:
                    incidence_matrix[row, off_bool + int(bcol)] = 1

        # Inequalities
        for j, ineq in enumerate(self._mti_inequalities_compiled):
            row = n_eq + j
            for v in get_expression_vars(ineq):
                didx = self._uid2idx_diff.get(v.uid, None)
                if didx is not None:
                    incidence_matrix[row, off_diff + int(didx)] = 1
                    continue
                idx = self.uid2idx_vars.get(v.uid, None)
                if idx is not None:
                    incidence_matrix[row, off_vars + int(idx)] = 1
                    continue
                bcol = bool_uid_to_local_col.get(v.uid, None)
                if bcol is not None:
                    incidence_matrix[row, off_bool + int(bcol)] = 1

        nnz = int(np.count_nonzero(incidence_matrix))
        print(
            "[MTI-INC] blocks "
            f"eq={n_eq} ineq={n_ineq} diff={n_diff} vars={n_vars} bool={n_bool} nnz={nnz}"
        )
        return incidence_matrix

    def get_mti_solving_order(self) -> list[MTISubProblemRow]:
        return list(self._mti_solving_order)

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

        touched_vars = self._ineq_var_positions[ineq_idx]
        if touched_vars.size == 0:
            n = self.get_all_vars_number()
            all_idx = np.arange(n, dtype=int)
            if debug:
                print(f"[MTI-STAGE] ineq_idx={ineq_idx} touched_vars empty, using full fallback stage")
            return ([(all_idx, all_idx)], [(all_idx, all_idx)], [])

        rows = self._mti_solving_order
        n_diff = self.get_diff_var_number()
        touched_cols = set((n_diff + touched_vars).tolist())
        subset_ids = sorted({int(r.subset) for r in rows if (int(r.var_idx) - 1) in touched_cols})
        if len(subset_ids) == 0:
            n = self.get_all_vars_number()
            all_idx = np.arange(n, dtype=int)
            if debug:
                print(f"[MTI-STAGE] ineq_idx={ineq_idx} no subset hit, using full fallback stage")
            return ([(all_idx, all_idx)], [(all_idx, all_idx)], [])

        event_subset_ids = set(subset_ids)

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
        stage = 0
        for _, _, eqs, vars_ in ordered:
            subsets_here = {int(r.subset) for r in rows if (int(r.eq_idx) - 1) in eqs or (int(r.var_idx) - 1) in vars_}
            n_eq_cont = self.get_states_number() + len(self._algebraic_eqs)
            eqs_cont = sorted([e for e in eqs if 0 <= int(e) < n_eq_cont])
            # Solver state vector only contains continuous vars; drop boolean
            # incidence columns from stage var-index sets.
            n_x = self.get_all_vars_number()
            vars_cont = sorted([int(v) - n_diff for v in vars_ if n_diff <= int(v) < (n_diff + n_x)])
            item = (np.asarray(eqs_cont, dtype=int), np.asarray(vars_cont, dtype=int))
            is_event = len(subsets_here & event_subset_ids) > 0
            if stage == 0 and not is_event:
                previous.append(item)
            elif is_event:
                stage = 1
                event.append(item)
            else:
                stage = 2
                following.append(item)

        if len(event) == 0:
            n = self.get_all_vars_number()
            all_idx = np.arange(n, dtype=int)
            if debug:
                print(f"[MTI-STAGE] ineq_idx={ineq_idx} empty event group, fallback to full event stage")
            return (previous if len(previous) > 0 else [(all_idx, all_idx)], [(all_idx, all_idx)], following)

        if debug:
            print(
                f"[MTI-STAGE] ineq_idx={ineq_idx} touched={touched_vars.size} "
                f"subsets={len(subset_ids)} prev={len(previous)} event={len(event)} foll={len(following)}"
            )

        return previous, event, following

    def _build_inequality_variable_positions(self) -> None:
        self._ineq_var_positions = []
        for ineq in self._mti_inequalities_raw:
            pos = []
            for v in get_expression_vars(ineq):
                idx = self.uid2idx_vars.get(v.uid, None)
                if idx is not None:
                    pos.append(int(idx))
            self._ineq_var_positions.append(np.asarray(sorted(set(pos)), dtype=int))

    def get_event_local_boolean_candidates(self, ineq_idx: int, z_prev: Vec) -> list[np.ndarray]:
        """
        Enumerate boolean candidates local to the subset touched by inequality.

        If structural mapping is unavailable, fall back to full enumeration.
        """
        debug = os.getenv("RMS_MTI_DEBUG", "0").strip() in ("1", "true", "True", "yes", "on")
        n_bool = len(self.get_mti_boolean_parameter_indices)
        if n_bool == 0:
            if debug:
                print("[MTI-LOC-CAND] n_bool=0 -> single empty candidate")
            return [np.zeros(0, dtype=float)]

        if self._mti_incidence is None or len(self._mti_solving_order) == 0:
            if debug:
                print("[MTI-LOC-CAND] no incidence/order -> full enumeration")
            return self.enumerate_all_boolean_candidates()

        if ineq_idx < 0 or ineq_idx >= len(self._ineq_var_positions):
            if debug:
                print(f"[MTI-LOC-CAND] invalid ineq_idx={ineq_idx} -> full enumeration")
            return self.enumerate_all_boolean_candidates()

        touched_vars = self._ineq_var_positions[ineq_idx]
        if touched_vars.size == 0:
            if debug:
                print(f"[MTI-LOC-CAND] ineq_idx={ineq_idx} touched_vars empty -> full enumeration")
            return self.enumerate_all_boolean_candidates()

        subset_ids = set()
        n_diff = self.get_diff_var_number()
        touched_cols = set((n_diff + touched_vars).tolist())
        for row in self._mti_solving_order:
            if (row.var_idx - 1) in touched_cols:
                subset_ids.add(row.subset)
        if len(subset_ids) == 0:
            if debug:
                print(f"[MTI-LOC-CAND] ineq_idx={ineq_idx} no subset hit -> full enumeration")
            return self.enumerate_all_boolean_candidates()

        subset_to_vars: dict[int, set[int]] = {}
        for row in self._mti_solving_order:
            subset_to_vars.setdefault(int(row.subset), set()).add(int(row.var_idx) - 1)

        event_vars: set[int] = set()
        for sid in subset_ids:
            event_vars |= subset_to_vars.get(int(sid), set())

        idx = self.get_mti_boolean_parameter_indices
        local_positions: list[int] = []
        for k, param_idx in enumerate(idx):
            bool_vars = self._mti_bool_guard_var_positions_by_param_idx.get(int(param_idx), np.zeros(0, dtype=int))
            if bool_vars.size == 0:
                continue
            if any(int(v) in event_vars for v in np.asarray(bool_vars, dtype=int)):
                local_positions.append(k)

        if len(local_positions) == 0:
            if debug:
                print(f"[MTI-LOC-CAND] ineq_idx={ineq_idx} no local bool positions -> full enumeration")
            return self.enumerate_all_boolean_candidates()

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
