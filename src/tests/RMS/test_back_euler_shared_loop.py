# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Backward Euler formulations use one integration and Newton policy."""

import numpy as np
from scipy import sparse
from unittest.mock import Mock
from VeraGridEngine.Simulations.Rms.numerical import back_euler_fx

from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import (
    BackEulerImplicitIntegration,
)
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import (
    RmsProblemTemplate,
)
from VeraGridEngine.Simulations.Rms.jacobian_assembler import JacobianAssembler


class _NoDerivativeProblem(RmsProblemTemplate):
    def get_diff_var_number(self):
        return 0

    def get_states_number(self):
        return 1

    def evaluate_equations(self, x, dx):
        return np.array([2.0 * x[0], x[1] - x[0]])

    def evaluate_jacobian_blocks(self, x, dx, h):
        return (sparse.csc_matrix([[2.0]]), sparse.csc_matrix([[0.0]]),
                sparse.csc_matrix([[-1.0]]), sparse.csc_matrix([[1.0]]))

    def evaluate_backward_euler_residual(self, x, dx, xn, h):
        raise AssertionError("The solver owns Backward Euler for derivative-free equations")

    def get_jacobian(self, x, dx, h):
        raise AssertionError("The solver owns the Newton assembly")


def test_no_derivative_problem_uses_solver_owned_discretization():
    problem = _NoDerivativeProblem()
    solver = BackEulerImplicitIntegration.__new__(BackEulerImplicitIntegration)
    solver.problem = problem
    solver._timings = {"rhs_evaluation_time": 0.0, "jacobian_blocks_time": 0.0}
    solver._jacobian_assembler = JacobianAssembler()
    solver._derivative_base_indices = None
    solver._derivative_orders = None
    solver._residual = np.empty(0)
    solver._fixed_jacobian_pattern = problem.has_fixed_equation_jacobian_pattern()
    x = np.array([3.0, 4.0])
    previous = np.array([2.0, 4.0])
    dx = np.empty(0)
    np.testing.assert_allclose(solver._rhs_implicit(x, dx, previous, 0.1), [0.4, 1.0])
    np.testing.assert_allclose(solver._jacobian_implicit(x, dx, 0.1).toarray(),
                               [[0.8, 0.0], [-1.0, 1.0]])


class _ReusableRawProblem(_NoDerivativeProblem):
    def __init__(self):
        self.raw = sparse.csc_matrix([[2.0, 0.0], [-1.0, 1.0]])

    def evaluate_equation_jacobian(self, x, dx):
        return self.raw

    def has_fixed_equation_jacobian_pattern(self):
        return True

    def evaluate_jacobian_blocks(self, x, dx, h):
        raise AssertionError("Full raw Jacobian should avoid block extraction")


def test_reusable_raw_jacobian_keeps_cached_implicit_pattern():
    problem = _ReusableRawProblem()
    solver = BackEulerImplicitIntegration.__new__(BackEulerImplicitIntegration)
    solver.problem = problem
    solver._timings = {"rhs_evaluation_time": 0.0, "jacobian_blocks_time": 0.0}
    solver._jacobian_assembler = JacobianAssembler()
    solver._derivative_base_indices = None
    solver._derivative_orders = None
    solver._residual = np.empty(0)
    solver._fixed_jacobian_pattern = problem.has_fixed_equation_jacobian_pattern()
    x, dx, previous = np.array([3.0, 4.0]), np.empty(0), np.array([2.0, 4.0])
    np.testing.assert_allclose(solver._rhs_implicit(x, dx, previous, 0.1), [0.4, 1.0])
    residual = solver._residual
    assert solver._rhs_implicit(x, dx, previous, 0.2) is residual
    np.testing.assert_allclose(residual, [-0.2, 1.0])
    first = solver._jacobian_implicit(x, dx, 0.1)
    np.testing.assert_allclose(first.toarray(), [[0.8, 0.0], [-1.0, 1.0]])
    second = solver._jacobian_implicit(x, dx, 0.2)
    assert first is second
    np.testing.assert_allclose(second.toarray(), [[0.6, 0.0], [-1.0, 1.0]])
    np.testing.assert_allclose(problem.raw.toarray(), [[2.0, 0.0], [-1.0, 1.0]])


def test_linear_fallback_reaches_lsqr_after_failed_direct_and_regularized_solves(monkeypatch):
    calls = Mock()
    direct = Mock(side_effect=RuntimeError("singular"))
    regularized = Mock(return_value=np.array([np.nan]))
    least_squares = Mock(return_value=(np.array([2.0]),))
    calls.attach_mock(direct, "direct")
    calls.attach_mock(regularized, "regularized")
    calls.attach_mock(least_squares, "lsqr")

    monkeypatch.setattr(back_euler_fx, "solve_rms_newton_correction", direct)
    monkeypatch.setattr(back_euler_fx, "solve_sparse_system_once", regularized)
    monkeypatch.setattr(back_euler_fx.sp.linalg, "lsqr", least_squares)
    solver = BackEulerImplicitIntegration.__new__(BackEulerImplicitIntegration)
    solver._sparse_solver_backend_provider = None
    solver._sparse_linear_solver = None
    solver._regularized_linear_solver = None
    correction = solver._solve_linear_correction(sparse.csc_matrix([[1.0]]), np.array([1.0]), None)
    np.testing.assert_array_equal(correction, [2.0])
    assert [call[0] for call in calls.mock_calls] == ["direct", "regularized", "regularized", "lsqr"]


def test_full_raw_assembly_inserts_missing_identity_and_rebuilds_changed_pattern():
    assembler = JacobianAssembler()
    raw = sparse.csc_matrix([[0.0, 2.0], [3.0, 4.0]])
    first = assembler.assemble_jacobian_implicit_raw(1, 0.5, raw)
    np.testing.assert_allclose(first.toarray(), [[1.0, -1.0], [3.0, 4.0]])
    # A fresh matrix with the same structure must reuse the cached output.
    assert assembler.assemble_jacobian_implicit_raw(1, 0.25, raw.copy()) is first
    np.testing.assert_allclose(first.toarray(), [[1.0, -0.5], [3.0, 4.0]])
    changed = sparse.csc_matrix([[2.0, 0.0], [0.0, 4.0]])
    second = assembler.assemble_jacobian_implicit_raw(1, 0.5, changed)
    np.testing.assert_allclose(second.toarray(), [[0.0, 0.0], [0.0, 4.0]])


def test_fixed_raw_pattern_accepts_new_structure_as_new_matrix():
    assembler = JacobianAssembler()
    raw = sparse.csc_matrix([[2.0, 0.0], [3.0, 4.0]])
    first = assembler.assemble_jacobian_implicit_raw(1, 0.5, raw, fixed_pattern=True)
    raw.data *= 2.0
    assert assembler.assemble_jacobian_implicit_raw(1, 0.25, raw, fixed_pattern=True) is first
    np.testing.assert_allclose(first.toarray(), [[0.0, 0.0], [6.0, 8.0]])
    replacement = sparse.csc_matrix([[0.0, 2.0], [3.0, 4.0]])
    second = assembler.assemble_jacobian_implicit_raw(1, 0.5, replacement, fixed_pattern=True)
    np.testing.assert_allclose(second.toarray(), [[1.0, -1.0], [3.0, 4.0]])
    assert assembler.assemble_jacobian_implicit_raw(1, 0.25, replacement, fixed_pattern=True) is second
    np.testing.assert_allclose(second.toarray(), [[1.0, -0.5], [3.0, 4.0]])
