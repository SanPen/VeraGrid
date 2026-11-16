# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""One-shot sparse solves derived from the factorisation-reusing providers (SuperLU and KLU), and CLU falling back to SuperLU."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest
import scipy.sparse as sp
from scipy.sparse.linalg import MatrixRankWarning, spsolve, splu

from VeraGridEngine.basic_structures import CscMat, Vec
from VeraGridEngine.enumerations import SparseSolver
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackend
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackend, SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.Sparse.sparse_solve import (
    CluLinearSolver,
    SparseProviderLinearSolver,
    SparseFactorizationManager,
    clu_linsolver,
    get_available_sparse_solvers,
    get_linear_solver,
    get_sparse_lu_provider_status,
    get_sparse_type,
    solve_sparse_system_once,
)


class _DefaultOneShotProvider(SparseLinearSolverBackendProvider):
    """Provider that keeps the inherited solve_once, backed by the SuperLU backend."""

    __slots__ = []

    def get_name(self) -> str:
        """
        :return: Provider name.
        """
        return "default_one_shot"

    def get_solver_type(self) -> SparseSolver:
        """
        :return: A type other than SuperLU, so solve_sparse_system_once goes through solve_once.
        """
        return SparseSolver.ILU

    def is_available(self) -> bool:
        """
        :return: Always available.
        """
        return True

    def create_backend(self, base_matrix: CscMat, base_data: Vec) -> SparseLinearSolverBackend:
        """
        :param base_matrix: CSC shell.
        :param base_data: Numeric buffer.
        :return: SuperLU backend.
        """
        # Exercise failed pattern construction through the existing test owner.
        if base_matrix.nnz == 0:
            raise RuntimeError("test provider rejects an empty pattern during construction")
        else:
            return SuperLUSparseBackend(base_matrix=base_matrix, base_data=base_data)


def _well_conditioned_system() -> tuple[CscMat, Vec]:
    """
    Build a reproducible, diagonally dominant sparse system.

    :return: Matrix and right-hand side.
    """
    rng: np.random.Generator = np.random.default_rng(5)
    matrix: CscMat = sp.random(80, 80, density=0.06, random_state=7, format="csc") + sp.eye(80, format="csc") * 6.0
    matrix = sp.csc_matrix(matrix)
    rhs: Vec = rng.standard_normal(80)
    return matrix, rhs


def _singular_system() -> tuple[CscMat, Vec]:
    """
    Build an exactly singular 2x2 system.

    :return: Matrix and right-hand side.
    """
    matrix: CscMat = sp.csc_matrix(np.array([[1.0, 2.0], [2.0, 4.0]]))
    rhs: Vec = np.array([1.0, 0.0])
    return matrix, rhs


def test_superlu_one_shot_is_the_provider_splu_call() -> None:
    """SuperLU one-shot is derived from its provider and equals splu(A).solve(b) bit for bit."""
    matrix: CscMat
    rhs: Vec
    matrix, rhs = _well_conditioned_system()
    solver: Callable[[CscMat, Vec], Vec] = get_linear_solver(SparseSolver.SuperLU)
    assert isinstance(solver, SparseProviderLinearSolver)
    assert np.array_equal(solver(matrix, rhs), splu(matrix).solve(rhs))


def test_superlu_one_shot_raises_on_a_singular_matrix() -> None:
    """The one-shot keeps raising RuntimeError for a singular matrix, as callers expect."""
    matrix: CscMat
    rhs: Vec
    matrix, rhs = _singular_system()
    with pytest.raises(RuntimeError):
        get_linear_solver(SparseSolver.SuperLU)(matrix, rhs)


def test_klu_one_shot_follows_its_provider() -> None:
    """KLU one-shot uses the native provider when available and SciPy spsolve otherwise."""
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(SparseSolver.KLU)
    solver: Callable[[CscMat, Vec], Vec] = get_linear_solver(SparseSolver.KLU)
    matrix: CscMat
    rhs: Vec
    matrix, rhs = _well_conditioned_system()
    if provider is None:
        assert len(reason) > 0
        assert solver is spsolve
    else:
        assert isinstance(solver, SparseProviderLinearSolver)
        reference: Vec = spsolve(matrix.copy(), rhs)
        solution: Vec = solver(matrix, rhs)
        assert float(np.max(np.abs(solution - reference))) <= 1e-10 * float(np.max(np.abs(reference)))
        singular_matrix: CscMat
        singular_rhs: Vec
        singular_matrix, singular_rhs = _singular_system()
        with pytest.raises(RuntimeError):
            solver(singular_matrix, singular_rhs)


def test_klu_is_available_exactly_when_its_provider_is() -> None:
    """KLU availability comes from its provider; SuperLU stays available."""
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(SparseSolver.KLU)
    available: list[SparseSolver] = get_available_sparse_solvers()
    assert (SparseSolver.KLU in available) == (provider is not None)
    assert SparseSolver.SuperLU in available


def test_default_solve_once_factorises_a_canonical_copy() -> None:
    """The inherited solve_once solves through create_backend and factorize and leaves the matrix untouched."""
    matrix: CscMat
    rhs: Vec
    matrix, rhs = _well_conditioned_system()
    before: CscMat = matrix.copy()
    solution: Vec = _DefaultOneShotProvider().solve_once(matrix, rhs)
    assert float(np.max(np.abs(matrix @ solution - rhs))) <= 1e-10 * max(1.0, float(np.max(np.abs(rhs))))
    assert (matrix != before).nnz == 0
    singular_matrix: CscMat
    singular_rhs: Vec
    singular_matrix, singular_rhs = _singular_system()
    with pytest.raises(RuntimeError):
        _DefaultOneShotProvider().solve_once(singular_matrix, singular_rhs)


def test_solve_once_through_the_rms_helper_reports_singular_as_nan() -> None:
    """solve_sparse_system_once keeps its contract over solve_once: a singular matrix warns and returns NaN."""
    matrix: CscMat
    rhs: Vec
    matrix, rhs = _singular_system()
    with pytest.warns(MatrixRankWarning):
        solution: Vec = solve_sparse_system_once(matrix, rhs, _DefaultOneShotProvider())
    assert np.all(np.isnan(solution))


def _complex_system() -> tuple[CscMat, Vec]:
    """
    Build a reproducible complex sparse system from the well-conditioned real one.

    :return: Complex matrix and right-hand side.
    """
    matrix: CscMat
    rhs: Vec
    matrix, rhs = _well_conditioned_system()
    complex_matrix: CscMat = sp.csc_matrix(matrix * (1.0 + 0.5j))
    complex_rhs: Vec = rhs * (1.0 - 0.25j)
    return complex_matrix, complex_rhs


def test_clu_uses_csc_storage() -> None:
    """CLU works on CSC matrices."""
    assert get_sparse_type(SparseSolver.CLU) is sp.csc_matrix


def test_clu_falls_back_to_superlu_when_unavailable() -> None:
    """Without pygslv CLU, get_linear_solver(CLU) solves through the SuperLU provider."""
    if SparseSolver.CLU in get_available_sparse_solvers():
        pytest.skip("pygslv CLU is installed; test_clu_solves_real_and_complex_systems covers it")
    else:
        matrix: CscMat
        rhs: Vec
        matrix, rhs = _well_conditioned_system()
        solver: Callable[[CscMat, Vec], Vec] = get_linear_solver(SparseSolver.CLU)
        assert isinstance(solver, SparseProviderLinearSolver)
        assert np.array_equal(solver(matrix, rhs), splu(matrix).solve(rhs))


def test_clu_solves_complex_systems_through_superlu() -> None:
    """CLU is real-only, so CluLinearSolver solves complex systems through SuperLU, with or without pygslv."""
    matrix: CscMat
    rhs: Vec
    matrix, rhs = _complex_system()
    solution: Vec = CluLinearSolver().solve(matrix, rhs)
    assert np.array_equal(solution, splu(matrix).solve(rhs))


def test_clu_solves_real_and_complex_systems() -> None:
    """With pygslv CLU installed, the retained-factor CLU solver matches SuperLU on real and complex systems."""
    if SparseSolver.CLU not in get_available_sparse_solvers():
        pytest.skip("pygslv CLU is not installed")
    else:
        solver: Callable[[CscMat, Vec], Vec] = get_linear_solver(SparseSolver.CLU)
        matrix: CscMat
        rhs: Vec
        for matrix, rhs in (_well_conditioned_system(), _complex_system()):
            reference: Vec = splu(matrix).solve(rhs)
            solution: Vec = solver(matrix, rhs)
            assert float(np.max(np.abs(solution - reference))) <= 1e-10 * float(np.max(np.abs(reference)))

        # Empty blocks still validate/factor current coefficients, including a
        # singular update after a successful retained-factor request.
        legacy_solver: CluLinearSolver = CluLinearSolver()
        real_matrix: CscMat = _well_conditioned_system()[0]
        empty_rhs: np.ndarray = np.empty((real_matrix.shape[0], 0), dtype=np.float64)
        assert legacy_solver.solve(real_matrix, empty_rhs).shape == empty_rhs.shape
        singular: CscMat = real_matrix.copy()
        singular.data[:] = 0.0
        with pytest.raises(np.linalg.LinAlgError):
            legacy_solver.solve(singular, empty_rhs)
        assert legacy_solver.solve(real_matrix, empty_rhs).shape == empty_rhs.shape


def test_clu_one_shot_falls_back_to_superlu_when_unavailable() -> None:
    """Without pygslv CLU, clu_linsolver solves a real system through the SuperLU provider."""
    if SparseSolver.CLU in get_available_sparse_solvers():
        pytest.skip("pygslv CLU is installed; test_clu_solves_real_and_complex_systems covers it")
    else:
        matrix: CscMat
        rhs: Vec
        matrix, rhs = _well_conditioned_system()
        assert np.array_equal(clu_linsolver(matrix, rhs), splu(matrix).solve(rhs))


@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba,
                                         SparseSolver.Pardiso))
def test_resident_lu_same_matrix_reuses_factors(solver_type: SparseSolver) -> None:
    """Two RHS streams on identical coefficients need one successful numeric factor.

    :param solver_type: Real optional backend exercised when physically available.
    :return: None; unavailable runtimes are explicitly skipped, never counted as tested.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        matrix: CscMat
        rhs: Vec
        matrix, rhs = _well_conditioned_system()
        phase: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        first: Vec = phase.solve(matrix, rhs)
        second: Vec = phase.solve(matrix, 2.0 * rhs)
        np.testing.assert_allclose(second, 2.0 * first, rtol=1.0e-12, atol=1.0e-12)
        np.testing.assert_allclose(matrix @ first, rhs, rtol=1.0e-12, atol=1.0e-12)
        stats: dict[str, float] = phase.get_stats()
        assert stats["numeric_factorizations"] == 1.0
        assert stats["numeric_refactorizations"] == 0.0
        assert stats["solve_calls"] == 2.0
        print("RESIDENT_IDENTICAL", solver_type.name, stats)


@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba,
                                         SparseSolver.Pardiso))
def test_resident_lu_value_updates_and_pattern_changes(solver_type: SparseSolver) -> None:
    """Content edits and new shapes cannot reuse stale factors or symbolic state.

    :param solver_type: Backend whose actual resident operations are counted.
    :return: None.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        matrix: CscMat
        rhs: Vec
        matrix, rhs = _well_conditioned_system()
        phase: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        phase.solve(matrix, rhs)
        matrix.data[:] *= 1.125
        correction: Vec = phase.solve(matrix, rhs)
        np.testing.assert_allclose(matrix @ correction, rhs, rtol=1.0e-12, atol=1.0e-12)
        stats: dict[str, float] = phase.get_stats()
        if solver_type in (SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba):
            assert stats["numeric_refactorizations"] == 1.0
            assert stats["numeric_factorizations"] == 1.0
        else:
            assert stats["numeric_refactorizations"] == 0.0
            assert stats["numeric_factorizations"] == 2.0
        # Removing off-diagonal entries changes the pattern at the same shape.
        diagonal: CscMat = sp.eye(matrix.shape[0], format="csc") * 2.0
        np.testing.assert_allclose(phase.solve(diagonal, rhs), rhs / 2.0, atol=1.0e-12)
        expanded: CscMat = sp.eye(matrix.shape[0] + 1, format="csc") * 3.0
        expanded_rhs: Vec = np.ones(expanded.shape[0], dtype=np.float64)
        np.testing.assert_allclose(phase.solve(expanded, expanded_rhs), expanded_rhs / 3.0, atol=1.0e-12)
        assert phase.get_stats()["pattern_rebuilds"] == 2.0
        print("RESIDENT_UPDATES", solver_type.name, phase.get_stats())


@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba,
                                         SparseSolver.Pardiso))
def test_resident_lu_forced_refresh(solver_type: SparseSolver) -> None:
    """Fresh-factor requests must perform full numeric work even for identical A.

    :param solver_type: Available provider whose forced refresh is exercised.
    :return: None.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        matrix: CscMat
        rhs: Vec
        matrix, rhs = _well_conditioned_system()
        manager: SparseFactorizationManager = SparseFactorizationManager(matrix, matrix.data, provider)
        manager.factorize()
        manager.factorize(force_new=True)
        np.testing.assert_allclose(matrix @ manager.solve(rhs), rhs, rtol=1.0e-12, atol=1.0e-12)
        assert manager.get_stats()["numeric_factorizations"] == 2.0
        assert manager.get_stats()["numeric_refactorizations"] == 0.0
        manager.invalidate()
        manager.factorize()
        assert manager.get_stats()["numeric_factorizations"] == 3.0
        print("RESIDENT_FRESH", solver_type.name, manager.get_stats())


@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba,
                                         SparseSolver.Pardiso))
def test_resident_lu_failure_recovery(solver_type: SparseSolver) -> None:
    """Singularity and changed pivots cannot leave damaged numeric state eligible.

    :param solver_type: Real provider exercised through failure and recovery.
    :return: None.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        matrix: CscMat = sp.csc_matrix(np.array(((4.0, 1.0), (1.0, 3.0))))
        rhs: Vec = np.array((1.0, 2.0))
        phase: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        phase.solve(matrix, rhs)
        # Keep the explicit zero stored, so this tests pivot change at the SAME pattern.
        matrix.data[0] = 0.0
        pivot_solution: Vec = phase.solve(matrix, rhs)
        np.testing.assert_allclose(matrix @ pivot_solution, rhs, rtol=1.0e-12, atol=1.0e-12)
        singular: CscMat = sp.csc_matrix(np.array(((1.0, 0.0), (0.0, 0.0))))
        with pytest.raises(RuntimeError):
            phase.solve(singular, rhs)
        # The old broken state must not be used to solve this valid current matrix.
        recovered: Vec = phase.solve(matrix, rhs)
        np.testing.assert_allclose(matrix @ recovered, rhs, rtol=1.0e-12, atol=1.0e-12)
        # Completely empty storage is a numerical singularity, not an ownership
        # error. Repeated requests must never refactor a retained old matrix.
        empty: CscMat = sp.csc_matrix(matrix.shape, dtype=np.float64)
        attempt: int
        for attempt in range(2):
            with pytest.raises(RuntimeError):
                phase.solve(empty, rhs)
        with pytest.raises(RuntimeError):
            SparseProviderLinearSolver(provider).solve(empty, rhs)
        with pytest.warns(MatrixRankWarning):
            rejected: Vec = solve_sparse_system_once(empty, rhs, provider, phase)
        assert np.all(np.isnan(rejected))
        np.testing.assert_allclose(matrix @ phase.solve(matrix, rhs), rhs, rtol=1.0e-12, atol=1.0e-12)

        # A construction failure must leave the old matrix/backend consistently
        # paired and invalid, even when the new pattern is submitted repeatedly.
        construction_phase: SparseProviderLinearSolver = SparseProviderLinearSolver(_DefaultOneShotProvider())
        construction_phase.solve(matrix, rhs)
        for attempt in range(2):
            with pytest.raises(RuntimeError, match="empty pattern during construction"):
                construction_phase.solve(empty, rhs)
        np.testing.assert_allclose(matrix @ construction_phase.solve(matrix, rhs), rhs, rtol=1.0e-12, atol=1.0e-12)
        print("RESIDENT_FAILURE_RECOVERY", solver_type.name, phase.get_stats())


@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba,
                                         SparseSolver.Pardiso))
def test_resident_lu_preserves_input_storage(solver_type: SparseSolver) -> None:
    """Canonicalization is private and later solves cannot overwrite old corrections.

    :param solver_type: Provider operating on duplicate/unsorted caller CSC storage.
    :return: None.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        matrix: CscMat = sp.csc_matrix((np.array((1.0, 2.0, 1.0, 4.0, 1.0)),
            np.array((1, 0, 0, 1, 0), dtype=np.int32), np.array((0, 3, 5), dtype=np.int32)), shape=(2, 2))
        rhs: Vec = np.array((1.0, 2.0))
        data_before: Vec = matrix.data.copy()
        indices_before: np.ndarray = matrix.indices.copy()
        indptr_before: np.ndarray = matrix.indptr.copy()
        phase: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        first: Vec = phase.solve(matrix, rhs)
        first_before: Vec = first.copy()
        second: Vec = phase.solve(matrix, rhs * 3.0)
        np.testing.assert_array_equal(first, first_before)
        np.testing.assert_allclose(second, first * 3.0, atol=1.0e-12)
        np.testing.assert_array_equal(matrix.data, data_before)
        np.testing.assert_array_equal(matrix.indices, indices_before)
        np.testing.assert_array_equal(matrix.indptr, indptr_before)

        # The native CLU binding distinguishes descriptor identity even when
        # NumPy considers the float64 dtype equivalent. Preserve that caller
        # metadata and all values while testing both matrix and RHS views.
        equivalent_dtype: np.dtype[np.float64] = np.dtype(np.float64).newbyteorder("=")
        canonical: CscMat = matrix.copy()
        canonical.sum_duplicates()
        canonical.sort_indices()
        equivalent: CscMat = sp.csc_matrix((canonical.data.view(equivalent_dtype),
            canonical.indices, canonical.indptr), shape=canonical.shape, copy=False)
        equivalent_rhs: Vec = rhs.view(equivalent_dtype)
        saved_dtype: np.dtype[np.float64] = equivalent.data.dtype
        equivalent_data_before: Vec = equivalent.data.copy()
        # A fresh phase must create MatrixView; reusing the earlier factors
        # would exercise only the RHS descriptor and miss the native defect.
        equivalent_phase: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        equivalent_solution: Vec = equivalent_phase.solve(equivalent, equivalent_rhs)
        np.testing.assert_allclose(equivalent @ equivalent_solution, rhs, atol=1.0e-12)
        np.testing.assert_array_equal(equivalent.data, equivalent_data_before)
        # Changed values must reach the retained native matrix storage after
        # the temporary metadata shell used at first factorization is gone.
        equivalent.data[0] += 0.5
        equivalent_data_before = equivalent.data.copy()
        updated_solution: Vec = equivalent_phase.solve(equivalent, equivalent_rhs)
        np.testing.assert_allclose(equivalent @ updated_solution, rhs, atol=1.0e-12)
        assert equivalent.data.dtype is saved_dtype
        np.testing.assert_array_equal(equivalent.data, equivalent_data_before)
        np.testing.assert_array_equal(equivalent_rhs, rhs)
        np.testing.assert_array_equal(matrix.data, data_before)


@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba,
                                         SparseSolver.Pardiso))
def test_resident_lu_optional_provider_capabilities(solver_type: SparseSolver) -> None:
    """A registered selection reports actual public capabilities and backward error.

    :param solver_type: Native/public backend identity requested without fallback.
    :return: None; a skip is explicitly distinct from backend qualification.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        assert provider.get_solver_type() == solver_type
        matrix: CscMat
        rhs: Vec
        matrix, rhs = _well_conditioned_system()
        backend: SparseLinearSolverBackend = provider.create_backend(matrix, matrix.data)
        assert backend.supports_numeric_refactorization() == (solver_type in (SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba))
        phase: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        solution: Vec = phase.solve(matrix, rhs)
        denominator: float = float(np.linalg.norm(matrix.toarray(), np.inf) * np.linalg.norm(solution, np.inf) + np.linalg.norm(rhs, np.inf))
        backward_error: float = float(np.linalg.norm(matrix @ solution - rhs, np.inf) / denominator)
        assert backward_error <= 1.0e-12
        print("RESIDENT_BACKWARD_ERROR", provider.get_name(), backward_error)


def test_clu_numba_is_always_available() -> None:
    """The Numba CLU port has no optional dependency, so its provider is always registered.

    :return: None.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(SparseSolver.CLU_Numba)
    assert provider is not None and reason == ""
    assert provider.get_name() == "numba_clu"
    assert provider.get_solver_type() == SparseSolver.CLU_Numba
    assert SparseSolver.CLU_Numba in get_available_sparse_solvers()
    assert get_sparse_type(SparseSolver.CLU_Numba) is sp.csc_matrix


@pytest.mark.parametrize("solver_type", (SparseSolver.CLU, SparseSolver.CLU_Numba))
def test_clu_forced_refresh_chooses_new_pivots(solver_type: SparseSolver) -> None:
    """A forced refresh must repivot: replaying the old pivots would hit an exact zero.

    :param solver_type: CLU flavour under test.
    :return: None.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        # Same stored pattern (explicit zero kept); the first pivot of the old order becomes zero.
        matrix: CscMat = sp.csc_matrix((np.array([4.0, 1.0, 1.0, 3.0]), np.array([0, 1, 0, 1]), np.array([0, 2, 4])),
                                       shape=(2, 2))
        rhs: Vec = np.array([1.0, 2.0])
        manager: SparseFactorizationManager = SparseFactorizationManager(matrix, matrix.data, provider)
        manager.factorize()
        matrix.data[:] = np.array([0.0, 1.0, 1.0, 3.0])
        manager.update_matrix(matrix)
        manager.factorize(force_new=True)
        np.testing.assert_allclose(matrix @ manager.solve(rhs), rhs, rtol=1.0e-12, atol=1.0e-12)


def test_clu_numba_one_shot_keeps_the_clu_callable_contract() -> None:
    """get_linear_solver(CLU_Numba) solves real block right-hand sides and routes complex systems through SuperLU.

    :return: None.
    """
    solver: Callable[[CscMat, Vec], Vec] = get_linear_solver(SparseSolver.CLU_Numba)
    real: CscMat = sp.csc_matrix(np.array([[4.0, 1.0], [1.0, 3.0]]))
    block: np.ndarray = np.array([[1.0, 0.0], [2.0, 1.0]])
    np.testing.assert_allclose(real @ solver(real, block), block, rtol=1.0e-12, atol=1.0e-12)
    complex_matrix: sp.csc_matrix = sp.csc_matrix(np.array([[4.0 + 1.0j, 1.0], [1.0, 3.0 - 2.0j]]))
    complex_rhs: np.ndarray = np.array([1.0 + 1.0j, 2.0])
    np.testing.assert_allclose(complex_matrix @ solver(complex_matrix, complex_rhs), complex_rhs, rtol=1.0e-12, atol=1.0e-12)

