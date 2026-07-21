# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from collections.abc import Callable
from itertools import product
from typing import Any

import numpy as np
import scipy.sparse as sp

from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.Rms.problems.rms_problem_MTI import RmsProblemMTI
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicJacobian
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler
from VeraGridEngine.Utils.Symbolic.symbolic import Comparison, Const, Expr, Var, get_expression_vars
from VeraGridEngine.basic_structures import Vec


class EmtProblemMTI(EmtProblemDae):
    """EMT problem exposing the MTI API consumed by ``BackEulerImplicitIntegrationMTI``."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_mti_first_step_zero_dx = True
        self.use_full_dae_event_candidates = True

        self._mti_boolean_params: list[Var] = []
        self._mti_bool_uid2param_idx: dict[int, int] = {}
        self._mti_inequalities_raw: list[Expr | Comparison] = []
        self._mti_inequalities_compiled: list[Expr] = []
        self._rhs_ineq_fn: Callable[[Vec, Vec, Vec, Vec], Vec] | None = None
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
        self._mti_incidence: np.ndarray | None = None
        self._mti_solving_order = []
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

        self._dt = Var(name="dt")
        self._register_mti_boolean_runtime_parameters()
        self._compile_scalar_dae_api()
        self._compile_mti_inequalities()
        self._compile_mti_boolean_guards()
        self._initialize_mti_booleans_at_t0()
        self._build_inequality_variable_positions()

    def _register_mti_boolean_runtime_parameters(self) -> None:
        for blk in self.sys_block.get_all_blocks():
            for bool_var in blk.boolean_guards.keys():
                if bool_var not in self._mti_boolean_params:
                    self._mti_boolean_params.append(bool_var)
                if bool_var.uid in self._uid2idx_vars or bool_var.uid in self._uid2idx_event_params:
                    continue
                self._runtime_all_parameters_source.append(bool_var)
                self._runtime_all_eqs_source.append(Const(0.0))
                self._runtime_mode_uids.add(bool_var.uid)

        if len(self._mti_boolean_params) == 0:
            self._variable_parameters_values = self._event_params_values
            self._constant_params = self._constant_params_values
            self._state_algeb_vars = self.state_and_algebraic_vars()
            return

        self._rebuild_runtime_parameter_partition()
        self._finalize_order_and_maps()
        self._build_runtime_param_vectors()
        self._variable_parameters_values = self._event_params_values
        self._constant_params = self._constant_params_values
        self._state_algeb_vars = self.state_and_algebraic_vars()
        for bool_var in self._mti_boolean_params:
            idx = self._uid2idx_event_params.get(bool_var.uid, None)
            if idx is not None:
                self._mti_bool_uid2param_idx[bool_var.uid] = int(idx)

    def _compile_scalar_dae_api(self) -> None:
        self._state_algeb_vars = self.state_and_algebraic_vars()
        self._constant_params = self._constant_params_values
        self._variable_parameters_values = self._event_params_values
        compiler_names = dict(self._compiler_names_dict)
        compiler_names[self._dt.uid] = "h"
        rms_compiler = RMSCompiler(
            variables=self._state_algeb_vars,
            diff_vars=self._diff_vars,
            v_params=self._variable_parameters,
            c_params=self._constant_parameters,
            dt_var=self._dt,
            compiler_names_dict=compiler_names,
        )
        self._derivative_fn = rms_compiler.compile_derivative_fn(self._uid2idx_vars, "emt_mti_derivative")
        self._rhs_algeb_fn = rms_compiler.compile_rhs(self._algebraic_eqs, "emt_mti_rhs_algeb")
        self._rhs_state_fn = rms_compiler.compile_rhs(self._state_eqs, "emt_mti_rhs_state") if self._state_eqs else None
        self._j11_fn = rms_compiler.compile_sparse_jacobian(self._state_eqs, self._state_vars, "emt_mti_j11") if self._state_eqs else None
        self._j12_fn = rms_compiler.compile_sparse_jacobian(self._state_eqs, self._algebraic_vars, "emt_mti_j12") if self._state_eqs else None
        self._j21_fn = rms_compiler.compile_sparse_jacobian(self._algebraic_eqs, self._state_vars, "emt_mti_j21") if self._state_eqs else None
        self._j22_fn = rms_compiler.compile_sparse_jacobian(self._algebraic_eqs, self._algebraic_vars, "emt_mti_j22")

    def update_variable_params(self, t: float, x_snapshot: Vec | None = None) -> None:
        del x_snapshot
        updated = self.def_event_params_fn(self._variable_parameters_values, float(t))
        bool_idx = set(self.get_mti_boolean_parameter_indices)
        for i in range(updated.size):
            if i not in bool_idx:
                self._variable_parameters_values[i] = updated[i]
        self._event_params_values = self._variable_parameters_values

    def get_dx(self, x: Vec, xn: Vec, dx: Vec, h: float) -> Vec:
        return self._derivative_fn(x, xn, dx, h)

    def rhs_state(self, x: Vec, dx: Vec) -> Vec:
        if self._rhs_state_fn is None:
            return np.zeros(0, dtype=float)
        return self._rhs_state_fn(x, dx, self._variable_parameters_values, self._constant_params)

    def rhs_algebraic(self, x: Vec, dx: Vec) -> Vec:
        return self._rhs_algeb_fn(x, dx, self._variable_parameters_values, self._constant_params)

    def get_j11(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        if self._j11_fn is None:
            return sp.csc_matrix((0, 0))
        return self._j11_fn(x, dx, self._variable_parameters_values, self._constant_params, h)

    def get_j12(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        if self._j12_fn is None:
            return sp.csc_matrix((0, self.get_algebraic_var_number()))
        return self._j12_fn(x, dx, self._variable_parameters_values, self._constant_params, h)

    def get_j21(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        if self._j21_fn is None:
            return sp.csc_matrix((self.get_algebraic_var_number(), 0))
        return self._j21_fn(x, dx, self._variable_parameters_values, self._constant_params, h)

    def get_j22(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        return self._j22_fn(x, dx, self._variable_parameters_values, self._constant_params, h)

    def get_mti_boolean_parameters(self) -> list[object]:
        return list(self._mti_boolean_params)

    @property
    def non_bool_idx_params(self) -> np.ndarray:
        n = len(self._variable_parameters)
        bool_idx = set(self.get_mti_boolean_parameter_indices)
        return np.asarray([i for i in range(n) if i not in bool_idx], dtype=int)

    @staticmethod
    def _normalize_inequality_expression(expr: Expr | Comparison) -> Expr:
        return RmsProblemMTI._normalize_inequality_expression(expr)

    _boolean_value_from_guard = staticmethod(RmsProblemMTI._boolean_value_from_guard)
    _initialize_mti_booleans_at_t0 = RmsProblemMTI._initialize_mti_booleans_at_t0
    _evaluate_boolean_init_from_init_eq = RmsProblemMTI._evaluate_boolean_init_from_init_eq
    _compile_mti_inequalities = RmsProblemMTI._compile_mti_inequalities
    _compile_mti_equality_jacobians = RmsProblemMTI._compile_mti_equality_jacobians
    _compile_mti_boolean_guards = RmsProblemMTI._compile_mti_boolean_guards
    rhs_inequalities = RmsProblemMTI.rhs_inequalities
    compute_mti_equalities = RmsProblemMTI.compute_mti_equalities
    compute_mti_inequalities = RmsProblemMTI.compute_mti_inequalities
    make_mti_direct_state = RmsProblemMTI.make_mti_direct_state
    mti_direct_pack = RmsProblemMTI.mti_direct_pack
    mti_direct_apply = RmsProblemMTI.mti_direct_apply
    compute_mti_direct_equalities = RmsProblemMTI.compute_mti_direct_equalities
    jacobian_mti_direct_equalities = RmsProblemMTI.jacobian_mti_direct_equalities
    update_mti_boolean_state = RmsProblemMTI.update_mti_boolean_state
    get_mti_boolean_parameter_indices = RmsProblemMTI.get_mti_boolean_parameter_indices
    set_mti_boolean_state = RmsProblemMTI.set_mti_boolean_state
    evaluate_boolean_guard = RmsProblemMTI.evaluate_boolean_guard
    has_boolean_guard = RmsProblemMTI.has_boolean_guard
    split_direct_and_coupled_booleans = RmsProblemMTI.split_direct_and_coupled_booleans
    enumerate_all_boolean_candidates = RmsProblemMTI.enumerate_all_boolean_candidates
    total_derivative_inequalities = RmsProblemMTI.total_derivative_inequalities
    build_mti_incidence_and_order = RmsProblemMTI.build_mti_incidence_and_order
    print_mti_solving_order_summary = RmsProblemMTI.print_mti_solving_order_summary
    print_mti_incidence_diagnostics = RmsProblemMTI.print_mti_incidence_diagnostics
    _build_inequality_variable_positions = RmsProblemMTI._build_inequality_variable_positions
    _build_incidence_from_equation_structure = RmsProblemMTI._build_incidence_from_equation_structure
    get_mti_solving_order = RmsProblemMTI.get_mti_solving_order
    _mti_state_diff_vars = RmsProblemMTI._mti_state_diff_vars
    _mti_state_base_uids = RmsProblemMTI._mti_state_base_uids
    _mti_algebraic_vars = RmsProblemMTI._mti_algebraic_vars
    _continuous_var_idx_to_mti_col = RmsProblemMTI._continuous_var_idx_to_mti_col
    _mti_col_to_continuous_var_idx = RmsProblemMTI._mti_col_to_continuous_var_idx
    get_equality_row_indices = RmsProblemMTI.get_equality_row_indices
    get_continuous_equality_row_indices = RmsProblemMTI.get_continuous_equality_row_indices
    get_fixed_boolean_equality_row_indices = RmsProblemMTI.get_fixed_boolean_equality_row_indices
    get_inequality_row_indices = RmsProblemMTI.get_inequality_row_indices
    get_event_solving_stages = RmsProblemMTI.get_event_solving_stages
    get_event_subset_ids = RmsProblemMTI.get_event_subset_ids
    get_group_subset_ids = RmsProblemMTI.get_group_subset_ids
    get_subproblem_boolean_positions = RmsProblemMTI.get_subproblem_boolean_positions
    split_explicit_subproblem_pairs = RmsProblemMTI.split_explicit_subproblem_pairs
    get_event_local_boolean_candidates = RmsProblemMTI.get_event_local_boolean_candidates
    inequalities_satisfied = staticmethod(RmsProblemMTI.inequalities_satisfied)
    _mti_row_kind_label = RmsProblemMTI._mti_row_kind_label
    _mti_row_label = RmsProblemMTI._mti_row_label
    _mti_col_kind = RmsProblemMTI._mti_col_kind
    _mti_col_label = RmsProblemMTI._mti_col_label
    _mti_row_is_network_like = RmsProblemMTI._mti_row_is_network_like
    _mti_row_is_branch_current_like = RmsProblemMTI._mti_row_is_branch_current_like
    _mti_bipartite_component_summary = RmsProblemMTI._mti_bipartite_component_summary
    _print_mti_diag_membership = RmsProblemMTI._print_mti_diag_membership
    _print_mti_diag_edge_counts = RmsProblemMTI._print_mti_diag_edge_counts
    _print_mti_diag_ablation_summary = RmsProblemMTI._print_mti_diag_ablation_summary
    _print_mti_diag_degree_summary = RmsProblemMTI._print_mti_diag_degree_summary
    _print_mti_diag_bridge_candidates = RmsProblemMTI._print_mti_diag_bridge_candidates
