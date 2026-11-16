# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Validate global native dispatch across independently compiled RMS batches."""

from unittest.mock import patch

import numpy as np
from scipy.sparse import csc_matrix

from VeraGridEngine.Simulations.Rms.numerical.rms_ad_backend_numba_comp import RmsEquationAdEvaluator
from VeraGridEngine.Simulations.Rms.numerical.rms_category_ad_numba_comp import (
    CategoryAdSpec, CategoryRowTarget, FullVecCategoryAdJacobian,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var


def _reference_residual(values: np.ndarray, previous: np.ndarray,
                        gain: float, constant: float, h: float) -> np.ndarray:
    """Evaluate an independent nonlinear residual with a derivative input.

    :param values: Candidate state and algebraic values.
    :param previous: Previous accepted values.
    :param gain: Runtime event parameter.
    :param constant: Constant parameter.
    :param h: Integration step.
    :return: Backward Euler residual.
    """
    result: np.ndarray = np.empty(9)
    result[0] = values[0] - previous[0] - h * (gain * values[0] + values[1] ** 2)
    result[1] = values[1] - previous[1] - h * (-values[1] + values[2])
    row: int
    for row in range(2, 9):
        result[row] = values[row] ** 2 + values[row - 1] + constant
    result[8] += (values[1] - previous[1]) / h
    return result


def test_scalar_global_coordinator_matches_finite_differences_and_refreshes_buffers() -> None:
    """Cross compilation groups, colors and event updates without Python dispatch loops.

    :return: None.
    """
    variables: list[Var] = list(Var(f"global_x{index}") for index in range(9))
    derivative: Var = Var("global_dx", base_var=variables[1])
    gain: Var = Var("global_gain")
    constant: Var = Var("global_constant")
    algebraic: list[Expr] = list(variables[row] * variables[row] + variables[row - 1] + constant
                                for row in range(2, 9))
    algebraic[-1] = algebraic[-1] + derivative
    backend: RmsEquationAdEvaluator = RmsEquationAdEvaluator(
        variables[:2], variables[2:],
        list((gain * variables[0] + variables[1] * variables[1], -variables[1] + variables[2])),
        algebraic, list((derivative,)), list((gain,)), list((constant,)), batch_size=1,
    )
    # Nine batches exceed the default eight-batch worker group. Runtime must
    # nevertheless use one coordinator, with an ABI independent of this count.
    assert len(backend.get_batch_statistics()) == 9
    previous: np.ndarray = np.linspace(0.1, 0.9, 9)
    values: np.ndarray = previous + 0.2
    runtime: np.ndarray = np.array((2.0,))
    constants: np.ndarray = np.array((0.25,))
    h: float = 0.03
    derivatives: np.ndarray = np.array(((values[1] - previous[1]) / h,))
    residual: np.ndarray = backend.evaluate_residual(values, derivatives, previous, runtime, constants, h)
    expected: np.ndarray = _reference_residual(values, previous, runtime[0], constants[0], h)
    np.testing.assert_allclose(residual, expected)
    matrix: csc_matrix = backend.evaluate_jacobian(values, derivatives, previous, runtime, constants, h)
    expected_jacobian: np.ndarray = np.empty((9, 9))
    epsilon: float = 1e-6
    column: int
    for column in range(9):
        plus: np.ndarray = values.copy()
        minus: np.ndarray = values.copy()
        plus[column] += epsilon
        minus[column] -= epsilon
        expected_jacobian[:, column] = (
            _reference_residual(plus, previous, runtime[0], constants[0], h)
            - _reference_residual(minus, previous, runtime[0], constants[0], h)
        ) / (2.0 * epsilon)
    np.testing.assert_allclose(matrix.toarray(), expected_jacobian, atol=1e-8)
    data: np.ndarray = matrix.data
    indices: np.ndarray = matrix.indices
    pointers: np.ndarray = matrix.indptr
    # An event changes a derivative from nonzero to zero. Every evaluation must
    # overwrite the persistent storage, including those vanished contributions.
    runtime[0] = 0.0
    values[:] = 0.0
    h = 0.01
    derivatives[0] = (values[1] - previous[1]) / h
    second: np.ndarray = backend.evaluate_residual(values, derivatives, previous, runtime, constants, h)
    assert second is residual
    np.testing.assert_allclose(second, _reference_residual(values, previous, runtime[0], constants[0], h))
    repeated: csc_matrix = backend.evaluate_jacobian(values, derivatives, previous, runtime, constants, h)
    assert repeated is matrix
    assert repeated.data is data and repeated.indices is indices and repeated.indptr is pointers
    assert repeated[0, 0] == 1.0
    assert repeated[0, 1] == 0.0
    assert repeated[8, 1] == 1.0 / h
    # Raw equation diagnostics must remain separate from implicit discretization.
    raw: np.ndarray = backend.evaluate_raw_residual(values, derivatives, runtime, constants)
    np.testing.assert_allclose(raw[:2], (0.0, 0.0))
    raw_matrix: csc_matrix = backend.evaluate_raw_jacobian(values, derivatives, runtime, constants, h)
    assert raw_matrix[0, 0] == 0.0
    assert raw_matrix[8, 1] == 1.0 / h
    # Verify the optimization's actual boundary: nine batches and two compiler
    # groups still produce one native entry for each complete evaluation.
    coordinator = backend._backend._coordinator
    assert coordinator is not None
    assert len(coordinator._residual.nopython_signatures) == 1
    assert len(coordinator._jacobian.nopython_signatures) == 1
    with (patch.object(coordinator, "_residual", wraps=coordinator._residual) as residual_call,
          patch.object(coordinator, "_jacobian", wraps=coordinator._jacobian) as jacobian_call):
        backend.evaluate_residual(values, derivatives, previous, runtime, constants, h)
        backend.evaluate_jacobian(values, derivatives, previous, runtime, constants, h)
    assert residual_call.call_count == 1
    assert jacobian_call.call_count == 1


def test_vectorized_global_jacobian_accumulates_categories_and_assembles_newton() -> None:
    """Combine unequal category layouts, shared rows and changed runtime gains.

    :return: None.
    """
    x: Var = Var("category_x")
    y: Var = Var("category_y")
    dx: Var = Var("category_dx", base_var=x)
    gain: Var = Var("category_gain")
    other_gain: Var = Var("category_other_gain")
    first: CategoryAdSpec = CategoryAdSpec(
        10, list((gain * x + y, x * x + y + dx)), list((y, x)), list((dx,)),
        list((gain,)), list(), np.array(((1,), (0,))),
        list((CategoryRowTarget(0, 0, 0, 1.0), CategoryRowTarget(1, 0, 1, 1.0))),
    )
    second: CategoryAdSpec = CategoryAdSpec(
        20, list((other_gain * y * y,)), list((y,)), list(), list((other_gain,)), list(),
        np.array(((1,),)), list((CategoryRowTarget(0, 0, 1, -1.0),)),
    )
    backend: FullVecCategoryAdJacobian = FullVecCategoryAdJacobian(
        list((first, second)), 1, 1, list(((1, 1, 2.0),)),
    )
    inputs: dict[int, list[np.ndarray]] = dict()
    derivative_maps: dict[int, np.ndarray] = dict(((10, np.array(((0,),))),))
    runtime_maps: dict[int, np.ndarray] = dict(((10, np.array(((0,),))), (20, np.array(((1,),)))))
    constants: np.ndarray = np.empty(0)
    values: np.ndarray = np.array((2.0, 4.0))
    derivatives: np.ndarray = np.array((0.5,))
    runtime: np.ndarray = np.array((2.0, 3.0))
    backend.prepare_category_inputs(inputs, derivative_maps, runtime_maps, dict(),
                                    constants, values, derivatives, runtime)
    h: float = 0.02
    backend.evaluate_coordinated_residual(values, derivatives, values, runtime, h)
    matrix: csc_matrix = backend.evaluate_newton(inputs, h)
    np.testing.assert_allclose(matrix.toarray(), ((1.0 - h * 2.0, -h), (4.0 + 1.0 / h, 3.0 - 24.0)))
    data: np.ndarray = matrix.data
    pointers: np.ndarray = matrix.indptr
    runtime[:] = 0.0
    values[:] = 0.0
    h = 0.05
    backend.invalidate_runtime_parameters()
    backend.evaluate_coordinated_residual(values, derivatives, values, runtime, h)
    repeated: csc_matrix = backend.evaluate_newton(inputs, h)
    assert repeated is matrix and repeated.data is data and repeated.indptr is pointers
    np.testing.assert_allclose(repeated.toarray(), ((1.0, -h), (1.0 / h, 3.0)))
    assert backend.get_evaluation_count() == 2
    assert len(backend._jacobian_coordinator.nopython_signatures) == 1
    with patch.object(FullVecCategoryAdJacobian, "_evaluate_native_jacobian",
                      autospec=True, side_effect=FullVecCategoryAdJacobian._evaluate_native_jacobian) as native_call:
        backend.evaluate_newton(inputs, h)
    assert native_call.call_count == 1


def test_vectorized_global_jacobian_accepts_only_fixed_entries() -> None:
    """Keep fixed network equations valid even when no model category exists.

    :return: None.
    """
    backend: FullVecCategoryAdJacobian = FullVecCategoryAdJacobian(
        list(), 1, 1, list(((1, 1, 2.0),)),
    )
    np.testing.assert_allclose(backend.evaluate_newton(dict(), 0.01).toarray(), ((1.0, 0.0), (0.0, 2.0)))
