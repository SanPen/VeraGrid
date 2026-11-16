# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Check solver projection of independent DAE derivative columns."""

from types import SimpleNamespace

import numpy as np
import pytest
import scipy.sparse as sp

from VeraGridEngine.Simulations.Rms.jacobian_assembler import JacobianAssembler
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.numerical.midpoint import MidpointImplicitIntegration
from VeraGridEngine.Simulations.Rms.numerical.trapezoidal import TrapezoidalImplicitIntegration
from VeraGridEngine.Simulations.Rms.numerical.adaptive_bdf12 import AdaptiveBdf12Integration
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate


class SmallDae(RmsProblemTemplate):
    """One state, one algebraic variable, and first/second derivatives of the state."""

    def __init__(self):
        state = SimpleNamespace(uid=1, base_var=None)
        first = SimpleNamespace(uid=2, base_var=state)
        second = SimpleNamespace(uid=3, base_var=first)
        self._diff_vars = (first, second)
        self.uid2idx_vars = {state.uid: 0}

    def get_diff_vars(self):
        return self._diff_vars

    def get_diff_var_number(self):
        return len(self._diff_vars)

    def get_all_vars_number(self):
        return 2

    def get_states_number(self):
        return 1

    def supports_derivative_jacobian_partials(self):
        return True

    def evaluate_jacobian_partials(self, x, dx, derivative_base_indices=None):
        return tuple(sp.csc_matrix(block) for block in (
            [[-2.0]], [[3.0]], [[4.0, 5.0]],
            [[1.0]], [[1.0]], [[7.0, -2.0]],
        ))

    def evaluate_equations(self, x, dx):
        return np.array([-2 * x[0] + 3 * x[1] + 4 * dx[0] + 5 * dx[1],
                         x[0] + x[1] + 7 * dx[0] - 2 * dx[1]])

    def residual(self, x, history, h):
        first = (x[0] - history[0]) / h
        second = (x[0] - 2 * history[0] + history[1]) / h**2
        f = -2 * x[0] + 3 * x[1] + 4 * first + 5 * second
        g = x[0] + x[1] + 7 * first - 2 * second
        return np.array([x[0] - history[0] - h * f, g])


def test_backward_euler_projects_first_and_second_derivative_columns():
    problem = SmallDae()
    solver = BackEulerImplicitIntegration.__new__(BackEulerImplicitIntegration)
    solver.problem = problem
    solver._jacobian_assembler = JacobianAssembler()
    solver._derivative_base_indices = np.array([0, 0])
    solver._derivative_orders = problem.get_diff_var_orders()
    solver._timings = {"jacobian_blocks_time": 0.0}
    np.testing.assert_array_equal(solver._derivative_orders, [1, 2])

    x = np.array([1.2, -0.3])
    history = np.array([1.0, 0.8])
    h = 0.1
    jacobian = solver._jacobian_implicit(x, np.array([2.0, 20.0]), h)
    assert sp.isspmatrix_csc(jacobian)
    numerical = np.column_stack([
        (problem.residual(x + 1e-7 * np.eye(2)[column], history, h)
         - problem.residual(x - 1e-7 * np.eye(2)[column], history, h)) / 2e-7
        for column in range(2)
    ])
    np.testing.assert_allclose(jacobian.toarray(), numerical, rtol=1e-8, atol=1e-6)


@pytest.mark.parametrize("solver_type", (MidpointImplicitIntegration,
                                          TrapezoidalImplicitIntegration))
def test_second_order_schemes_project_derivative_columns(solver_type):
    problem = SmallDae()
    solver = solver_type.__new__(solver_type)
    solver.problem = problem
    solver._jacobian_assembler = JacobianAssembler()
    solver._derivative_base_indices = problem.get_diff_var_base_indices()
    solver._derivative_orders = problem.get_diff_var_orders()
    previous = np.array([1.0, -0.2])
    older = np.array([0.8, -0.1])
    x = np.array([1.2, -0.3])
    h = 0.1

    def residual(values):
        dx = np.array([(values[0] - previous[0]) / h,
                       (values[0] - 2 * previous[0] + older[0]) / h**2])
        if solver_type is MidpointImplicitIntegration:
            return solver._rhs_implicit(values, previous, dx, h)[0]
        return solver._rhs_implicit(values, dx, previous, h, np.array([0.4]))[0]

    dx = np.array([(x[0] - previous[0]) / h,
                   (x[0] - 2 * previous[0] + older[0]) / h**2])
    evaluation = 0.5 * (x + previous) if solver_type is MidpointImplicitIntegration else x
    actual = solver._jacobian_implicit(evaluation, dx, h)
    assert sp.isspmatrix_csc(actual)
    numerical = np.column_stack([
        (residual(x + 1e-7 * np.eye(2)[column])
         - residual(x - 1e-7 * np.eye(2)[column])) / 2e-7
        for column in range(2)
    ])
    np.testing.assert_allclose(actual.toarray(), numerical, rtol=1e-8, atol=1e-6)


def test_bdf12_projects_first_derivative_column():
    problem = SmallDae()
    problem._diff_vars = problem._diff_vars[:1]
    solver = AdaptiveBdf12Integration.__new__(AdaptiveBdf12Integration)
    solver.problem = problem
    solver.state_count = 1
    solver._uses_derivative_partials = True
    solver._derivative_base_indices = problem.get_diff_var_base_indices()
    solver._derivative_to_variable = sp.csc_matrix([[1.0, 0.0]])
    solver._yp_work = np.empty(2)
    solver._dx_empty = np.empty(1)
    solver._jacobian_assembler = JacobianAssembler()
    # This DAE uses its first derivative in both equation rows.
    problem.evaluate_equations = lambda x, dx: np.array(
        [-2 * x[0] + 3 * x[1] + 4 * dx[0], x[0] + x[1] + 7 * dx[0]])
    problem.evaluate_jacobian_partials = lambda x, dx: tuple(
        sp.csc_matrix(block) for block in (
            [[-2.0]], [[3.0]], [[4.0]], [[1.0]], [[1.0]], [[7.0]]))
    x = np.array([1.2, -0.3])
    alpha = 10.0
    history = np.array([-10.0, 0.0])
    solver._residual(x, alpha, history)
    actual = solver._jacobian(x, alpha)
    numerical = np.column_stack([
        (solver._residual(x + 1e-7 * np.eye(2)[column], alpha, history)
         - solver._residual(x - 1e-7 * np.eye(2)[column], alpha, history)) / 2e-7
        for column in range(2)
    ])
    np.testing.assert_allclose(actual.toarray(), numerical, rtol=1e-8, atol=1e-6)


def test_projection_cache_reuses_and_rebuilds_sparse_maps():
    assembler = JacobianAssembler()
    blocks = (
        sp.csc_matrix([[2.0, 0.0], [0.0, 3.0]]),
        sp.csc_matrix([[4.0], [0.0]]),
        sp.csc_matrix([[5.0, 6.0], [0.0, 7.0]]),
        sp.csc_matrix([[8.0, 0.0]]),
        sp.csc_matrix([[9.0]]),
        sp.csc_matrix([[10.0, 11.0]]),
    )
    chain = sp.csc_matrix(([10.0, 20.0], ([0, 1], [0, 0])), shape=(2, 3))

    def compare(raw):
        j11, j12, j13, j21, j22, j23 = raw
        projected = assembler.project_derivative_partials(2, *raw, chain)
        combined = sp.bmat([[j11, j12], [j21, j22]], format="csc")
        combined += sp.vstack((j13, j23), format="csc") @ chain
        np.testing.assert_allclose(sp.bmat([[projected[0], projected[1]],
                                             [projected[2], projected[3]]],
                                            format="csc").toarray(), combined.toarray())

    compare(blocks)
    assert assembler.get_projection_build_count() == 1
    chain.data *= 0.5
    blocks[2].data *= 2.0
    compare(blocks)
    assert assembler.get_projection_build_count() == 1
    assert assembler.get_projection_fill_count() == 2

    changed = (*blocks[:5], sp.csc_matrix([[10.0, 0.0]]))
    compare(changed)
    assert assembler.get_projection_build_count() == 2
    changed_chain = sp.csc_matrix(([2.0, 3.0], ([0, 1], [0, 1])), shape=(2, 3))
    chain = changed_chain
    compare(changed)
    assert assembler.get_projection_build_count() == 3
