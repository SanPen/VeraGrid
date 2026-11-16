# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Check the optional CLU backend against the sparse solver contract."""
import numpy as np
import pytest
from scipy.sparse import csc_matrix
from VeraGridEngine.enumerations import SparseSolver
from VeraGridEngine.Compilers.Gslv.activation import GSLV_AVAILABLE
from VeraGridEngine.Utils.Sparse.sparse_solve import (
    CluLinearSolver, get_available_sparse_solvers, get_linear_solver, get_sparse_type,
)


def test_clu_solutions() -> None:
    """Verify vector, strided matrix, integer and complex right hand sides.

    :return: None.
    """
    if SparseSolver.CLU not in get_available_sparse_solvers():
        pytest.skip("Activated pygslv with CLU is unavailable")
    else:
        pass
    assert SparseSolver.CLU in get_available_sparse_solvers()
    assert get_sparse_type(SparseSolver.CLU) is csc_matrix
    matrix: csc_matrix = csc_matrix([[4, 1], [2, 3]])
    rhs: np.ndarray
    # Strided columns must be made contiguous before calling the native solver.
    for rhs in (np.array([1, 2]), np.arange(8).reshape(2, 4)[:, ::2],
                np.array([1 + 2j, 3 - 1j])):
        solution: np.ndarray = get_linear_solver(SparseSolver.CLU)(matrix, rhs)
        assert solution.shape == rhs.shape
        np.testing.assert_allclose(matrix @ solution, rhs, atol=1e-12)
    complex_matrix: csc_matrix = matrix.astype(complex) * (1 + 1j)
    np.testing.assert_allclose(
        complex_matrix @ get_linear_solver(SparseSolver.CLU)(complex_matrix, np.ones(2)),
        np.ones(2), atol=1e-12,
    )


def test_clu_failures() -> None:
    """Verify failed factorizations and incompatible dimensions are reported.

    :return: None.
    """
    if SparseSolver.CLU not in get_available_sparse_solvers():
        pytest.skip("Activated pygslv with CLU is unavailable")
    else:
        pass
    with pytest.raises(np.linalg.LinAlgError, match="CLU factorization failed"):
        get_linear_solver(SparseSolver.CLU)(csc_matrix([[1., 1.], [1., 1.]]), np.ones(2))
    with pytest.raises(ValueError, match="matching RHS dimensions"):
        get_linear_solver(SparseSolver.CLU)(csc_matrix(np.eye(2)), np.ones(3))


def test_clu_activation_gate() -> None:
    """Check that disabled GSLV leaves CLU unregistered and SciPy usable.

    :return: None.
    """
    if not GSLV_AVAILABLE:
        assert SparseSolver.CLU not in get_available_sparse_solvers()
        matrix: csc_matrix = csc_matrix(np.eye(2))
        np.testing.assert_allclose(
            get_linear_solver(SparseSolver.CLU)(matrix, np.ones(2)), np.ones(2),
        )
    else:
        pass


def test_clu_retained_factors() -> None:
    """Keep solutions correct across RHS, coefficient, pattern and failed updates.

    :return: None.
    """
    if SparseSolver.CLU not in get_available_sparse_solvers():
        pytest.skip("Activated pygslv with CLU is unavailable")
    else:
        pass
    solver: CluLinearSolver = CluLinearSolver()
    matrix: csc_matrix = csc_matrix([[4., 1.], [2., 3.]])
    original: csc_matrix = matrix.copy()
    rhs: np.ndarray = np.array([1., 2.])
    np.testing.assert_allclose(matrix @ solver.solve(matrix, rhs), rhs)
    factorizer: object | None = solver._factorizer
    # New RHS and in-place coefficient changes must keep the native analysis alive.
    rhs *= 2.
    np.testing.assert_allclose(matrix @ solver.solve(matrix, rhs), rhs)
    assert solver._factorizer is factorizer
    assert (matrix != original).nnz == 0
    matrix.data *= 1.1
    np.testing.assert_allclose(matrix @ solver.solve(matrix, rhs), rhs)
    assert solver._factorizer is factorizer
    # A changed pattern requires a fresh analysis, including asymmetric patterns.
    matrix = csc_matrix([[4., 0.], [2., 3.]])
    np.testing.assert_allclose(matrix @ solver.solve(matrix, rhs), rhs)
    assert solver._factorizer is not factorizer
    matrix = csc_matrix([[1., 1.], [1., 2.]])
    solver.solve(matrix, rhs)
    factorizer = solver._factorizer
    matrix.data[0] = 1e-30
    np.testing.assert_allclose(matrix @ solver.solve(matrix, rhs), rhs, atol=1e-12)
    assert solver._factorizer is factorizer
    # Failed updates must invalidate the cache even when retried unchanged.
    matrix.data[:] = 1.
    with pytest.raises(np.linalg.LinAlgError):
        solver.solve(matrix, rhs)
    with pytest.raises(np.linalg.LinAlgError):
        solver.solve(matrix, rhs)
    matrix.data[0] = 4.
    np.testing.assert_allclose(matrix @ solver.solve(matrix, rhs), rhs)


def test_clu_canonicalization() -> None:
    """Clean duplicates and explicit zeros without changing caller-owned buffers.

    :return: None.
    """
    if SparseSolver.CLU not in get_available_sparse_solvers():
        pytest.skip("Activated pygslv with CLU is unavailable")
    else:
        pass
    matrix: csc_matrix = csc_matrix((np.array([2., 0., 2., 1., 3.]),
                                     np.array([0, 1, 0, 0, 1]), np.array([0, 3, 5])), shape=(2, 2))
    data: np.ndarray = matrix.data.copy()
    indices: np.ndarray = matrix.indices.copy()
    pointers: np.ndarray = matrix.indptr.copy()
    rhs: np.ndarray = np.array([1., 2.])
    solution: np.ndarray = get_linear_solver(SparseSolver.CLU)(matrix, rhs)
    np.testing.assert_allclose(matrix @ solution, rhs)
    np.testing.assert_array_equal(matrix.data, data)
    np.testing.assert_array_equal(matrix.indices, indices)
    np.testing.assert_array_equal(matrix.indptr, pointers)
