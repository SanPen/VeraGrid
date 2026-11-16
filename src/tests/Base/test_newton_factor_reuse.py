# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Real-provider retained solves without target-network or physical fixtures."""

import numpy as np
import pytest
from scipy.sparse import csc_matrix

from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import SparseSolver
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.NumericalMethods.newton_factor_reuse import get_adaptive_recompute_threshold, needs_factor_refresh
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import needs_factor_refresh as structural_refresh
from VeraGridEngine.Utils.Sparse.sparse_solve import SparseProviderLinearSolver, get_sparse_lu_provider_status


def test_shared_policy_preserves_structural_decisions() -> None:
    """Keep existing structural import sites bound to the one shared owner.

    :return: None; identity rules out a copied policy implementation.
    """
    assert structural_refresh is needs_factor_refresh


def test_adaptive_recompute_threshold_keeps_the_structural_policy() -> None:
    """Few-iteration substeps tolerate slower contraction before a refresh, as in the structural solvers.

    :return: None.
    """
    assert get_adaptive_recompute_threshold(1) == 0.8
    assert get_adaptive_recompute_threshold(2) == 0.8
    assert get_adaptive_recompute_threshold(3) == 0.6
    assert get_adaptive_recompute_threshold(4) == 0.6
    assert get_adaptive_recompute_threshold(5) == 0.5

@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.Pardiso))
def test_retained_solve_requires_eligible_factors(solver_type: SparseSolver) -> None:
    """Change only RHS, preserve output ownership, and reject missing eligibility.

    :param solver_type: Real backend, explicitly skipped when unavailable.
    :return: None; exact successful work counters must describe two solves.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        phase: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        matrix: csc_matrix = csc_matrix(np.array(((4.0, 1.0), (1.0, 3.0))))
        rhs: Vec = np.array((1.0, 2.0))
        with pytest.raises(RuntimeError):
            phase.solve_retained(rhs)
        first: Vec = phase.solve(matrix, rhs)
        saved: Vec = first.copy()
        second: Vec = phase.solve_retained(2.0 * rhs)
        np.testing.assert_allclose(matrix @ second, 2.0 * rhs, atol=1e-12, rtol=0.0)
        np.testing.assert_array_equal(first, saved)
        assert phase.get_stats()["numeric_factorizations"] == 1.0
        assert phase.get_stats()["numeric_refactorizations"] == 0.0
        assert phase.get_stats()["solve_calls"] == 2.0
        phase.invalidate()
        with pytest.raises(RuntimeError):
            phase.solve_retained(rhs)


@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.Pardiso))
def test_retained_solve_failure_invalidates(solver_type: SparseSolver) -> None:
    """Non-finite input cannot leave factors eligible for a later retained solve.

    :param solver_type: Real backend used for successful factorization and recovery.
    :return: None; recovery requires fresh numeric factors.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        phase: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        matrix: csc_matrix = csc_matrix(np.array(((2.0, 0.0), (0.0, 3.0))))
        rhs: Vec = np.ones(2)
        phase.solve(matrix, rhs)
        with pytest.raises(RuntimeError):
            phase.solve_retained(np.full(2, np.nan))
        with pytest.raises(RuntimeError):
            phase.solve_retained(rhs)
        recovered: Vec = phase.solve(matrix, rhs)
        np.testing.assert_allclose(matrix @ recovered, rhs, atol=1e-12, rtol=0.0)
        assert phase.get_stats()["numeric_factorizations"] == 2.0
