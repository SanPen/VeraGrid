# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Check the residuals and Newton matrices of the two second-order schemes."""

import numpy as np
import pytest
from scipy.sparse import csc_matrix

from VeraGridEngine.Simulations.Rms.jacobian_assembler import JacobianAssembler
from VeraGridEngine.Simulations.Rms.numerical.midpoint import MidpointImplicitIntegration
from VeraGridEngine.Simulations.Rms.numerical.trapezoidal import TrapezoidalImplicitIntegration


class _Problem:
    def supports_derivative_jacobian_partials(self):
        return False

    def get_states_number(self):
        return 1

    def get_diff_var_number(self):
        return 0

    def rhs_state(self, x, dx):
        return np.array([x[0] ** 2 + x[1]])

    def rhs_algebraic(self, x, dx):
        return np.array([x[1] - x[0] ** 2])

    def evaluate_equations(self, x, dx):
        return np.r_[self.rhs_state(x, dx), self.rhs_algebraic(x, dx)]

    def evaluate_jacobian_blocks(self, x, dx, h):
        return (csc_matrix([[2 * x[0]]]), csc_matrix([[1.0]]),
                csc_matrix([[-2 * x[0]]]), csc_matrix([[1.0]]))

    def get_jacobian(self, x, dx, h):
        return csc_matrix([[1 - 2 * h * x[0], -h], [-2 * x[0], 1]])


def test_midpoint_uses_midpoint_equations_and_half_step_jacobian():
    solver = MidpointImplicitIntegration.__new__(MidpointImplicitIntegration)
    solver._jacobian_assembler = JacobianAssembler()
    solver.problem = _Problem()
    previous = np.array([1.0, 1.0])
    current = np.array([1.2, 1.4])
    h = 0.1

    residual, evaluation_point = solver._rhs_implicit(current, previous, np.empty(0), h)
    np.testing.assert_allclose(evaluation_point, [1.1, 1.2])
    np.testing.assert_allclose(residual, [0.2 - h * (1.1 ** 2 + 1.2), 1.2 - 1.1 ** 2])
    np.testing.assert_allclose(
        solver._jacobian_implicit(evaluation_point, np.empty(0), h).toarray(),
        [[1 - h * 1.1, -0.5 * h], [-1.1, 0.5]],
    )
    assert solver._jacobian_assembler.get_pattern_build_count() == 1
    solver._jacobian_implicit(evaluation_point, np.empty(0), h)
    assert solver._jacobian_assembler.get_fast_assembly_count() == 2


def test_trapezoidal_uses_endpoint_equations_and_full_algebraic_jacobian():
    solver = TrapezoidalImplicitIntegration.__new__(TrapezoidalImplicitIntegration)
    solver._jacobian_assembler = JacobianAssembler()
    solver.problem = _Problem()
    previous = np.array([1.0, 1.0])
    current = np.array([1.2, 1.4])
    h = 0.1
    previous_slope = solver.problem.rhs_state(previous, np.empty(0))

    residual, evaluation_point = solver._rhs_implicit(current, np.empty(0), previous, h, previous_slope)
    np.testing.assert_allclose(evaluation_point, current)
    np.testing.assert_allclose(residual, [0.2 - 0.5 * h * (1.2 ** 2 + 1.4 + 2.0),
                                          1.4 - 1.2 ** 2])
    np.testing.assert_allclose(
        solver._jacobian_implicit(evaluation_point, np.empty(0), h).toarray(),
        [[1 - h * 1.2, -0.5 * h], [-2 * 1.2, 1]],
    )
    assert solver._jacobian_assembler.get_pattern_build_count() == 1
    solver._jacobian_implicit(evaluation_point, np.empty(0), h)
    assert solver._jacobian_assembler.get_fast_assembly_count() == 2


def test_algebraic_only_trapezoidal_keeps_full_constraint_jacobian():
    class AlgebraicProblem:
        def get_states_number(self):
            return 0

        def get_diff_var_number(self):
            return 0

        def rhs_algebraic(self, x, dx):
            return np.array([2 * x[0]])

        def evaluate_equations(self, x, dx):
            return self.rhs_algebraic(x, dx)

        def evaluate_jacobian_blocks(self, x, dx, h):
            return None, None, None, csc_matrix([[2.0]])

        def get_jacobian(self, x, dx, h):
            return csc_matrix([[2.0]])

    solver = TrapezoidalImplicitIntegration.__new__(TrapezoidalImplicitIntegration)
    solver._jacobian_assembler = JacobianAssembler()
    solver.problem = AlgebraicProblem()
    residual, _ = solver._rhs_implicit(np.array([3.0]), np.empty(0), np.array([1.0]), 0.1, None)
    np.testing.assert_allclose(residual, [6.0])
    np.testing.assert_allclose(solver._jacobian_implicit(np.array([3.0]), np.empty(0), 0.1).toarray(), [[2.0]])


def test_trapezoidal_jacobian_keeps_the_derivative_chain():
    class DerivativeProblem:
        def get_states_number(self):
            return 1

        def get_diff_var_number(self):
            return 1

        def rhs_state(self, x, dx):
            return np.array([x[0] + 2 * dx[0]])

        def rhs_algebraic(self, x, dx):
            return np.empty(0)

        def evaluate_equations(self, x, dx):
            return self.rhs_state(x, dx)

        def supports_derivative_jacobian_partials(self):
            return True

        def evaluate_jacobian_partials(self, x, dx):
            empty_row = csc_matrix((1, 0))
            empty_column = csc_matrix((0, 1))
            return (csc_matrix([[1.0]]), empty_row, csc_matrix([[2.0]]),
                    empty_column, csc_matrix((0, 0)), empty_column)

        def get_all_vars_number(self):
            return 1

    solver = TrapezoidalImplicitIntegration.__new__(TrapezoidalImplicitIntegration)
    solver._jacobian_assembler = JacobianAssembler()
    solver.problem = DerivativeProblem()
    solver._derivative_base_indices = np.array([0])
    solver._derivative_orders = np.array([1])
    previous = np.array([1.0])
    current = np.array([1.2])
    h = 0.1
    dx = (current - previous) / h
    previous_slope = np.array([1.0])
    residual, _ = solver._rhs_implicit(current, dx, previous, h, previous_slope)
    perturbed = current + 1e-7
    perturbed_dx = (perturbed - previous) / h
    perturbed_residual, _ = solver._rhs_implicit(perturbed, perturbed_dx, previous, h, previous_slope)
    numerical_derivative = (perturbed_residual - residual) / 1e-7
    np.testing.assert_allclose(solver._jacobian_implicit(current, dx, h).toarray()[0, 0],
                               numerical_derivative[0], rtol=1e-6)


def test_midpoint_rejects_backward_euler_chain_for_derivative_symbols():
    class DerivativeProblem(_Problem):
        def get_diff_var_number(self):
            return 1

    solver = MidpointImplicitIntegration.__new__(MidpointImplicitIntegration)
    solver._jacobian_assembler = JacobianAssembler()
    solver.problem = DerivativeProblem()
    with pytest.raises(ValueError, match="separate derivative-variable Jacobian blocks"):
        solver._jacobian_implicit(np.array([1.0, 1.0]), np.array([0.0]), 0.1)


def test_half_step_assembly_adds_missing_state_diagonal_without_mutating_input():
    newton = csc_matrix([[0.0, -2.0], [3.0, 4.0]])
    original = newton.copy()

    midpoint = JacobianAssembler.assemble_jacobian_midpoint(1, newton)
    trapezoidal = JacobianAssembler.assemble_jacobian_trapezoidal(1, newton)

    np.testing.assert_allclose(midpoint.toarray(), [[0.5, -1.0], [1.5, 2.0]])
    np.testing.assert_allclose(trapezoidal.toarray(), [[0.5, -1.0], [3.0, 4.0]])
    np.testing.assert_array_equal(newton.toarray(), original.toarray())


@pytest.mark.parametrize(
    ("method", "expected"),
    [("assemble_jacobian_midpoint_blocks", [[0.0, -0.5], [1.5, 2.0]]),
     ("assemble_jacobian_trapezoidal_blocks", [[0.0, -0.5], [3.0, 4.0]])],
)
def test_half_step_block_kernel_falls_back_when_state_diagonal_cancels(method, expected):
    assembler = JacobianAssembler()
    blocks = (csc_matrix([[2.0]]), csc_matrix([[1.0]]),
              csc_matrix([[3.0]]), csc_matrix([[4.0]]))
    result = getattr(assembler, method)(1, 1.0, *blocks)
    np.testing.assert_allclose(result.toarray(), expected)
    assert assembler.get_fallback_assembly_count() == 1
