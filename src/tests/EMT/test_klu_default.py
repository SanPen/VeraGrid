# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""KLU is the default EMT sparse solver when installed, SuperLU otherwise, and explicit choices are kept."""

from __future__ import annotations

import pytest

from tests.EMT.test_discretization_verify import GenericEmtProblem
from VeraGridEngine.enumerations import EmtSolverTypes, SparseSolver
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.emt_solver_factory import build_emt_solver
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.Sparse.sparse_solve import get_sparse_lu_provider_status
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def _expected_default() -> SparseSolver:
    """
    Return the expected default sparse solver: KLU when its native provider is available, otherwise SuperLU.

    :return: Expected default.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(SparseSolver.KLU)
    expected: SparseSolver
    if provider is not None:
        expected = SparseSolver.KLU
    else:
        expected = SparseSolver.SuperLU
    return expected


def test_default_sparse_solver_is_klu_exactly_when_available(recwarn: pytest.WarningsRecorder) -> None:
    """
    The EMT default is KLU when its provider is available and SuperLU otherwise, chosen without an unavailability
    warning; an explicit choice is kept.

    :param recwarn: pytest warnings recorder.
    """
    assert EmtOptions().sparse_solver == _expected_default()
    assert _count_warnings(recwarn, "is unavailable") == 0
    assert EmtOptions(sparse_solver=SparseSolver.SuperLU).sparse_solver == SparseSolver.SuperLU


def _decay_problem() -> GenericEmtProblem:
    """
    Build the smallest EMT problem: one decaying state.

    :return: Problem.
    """
    state: Var = Var("kld_x")
    derivative: Var = Var("kld_dx", base_var=state)
    block: Block = Block(name="KluDefaultDecay", state_vars=list((state,)), diff_vars=list((derivative,)), state_eqs=list((-state,)),
                         algebraic_vars=list(), algebraic_eqs=list(), parameters=dict())
    block.unify_blocks()
    return GenericEmtProblem(sys_block=block, glob_time=Var("t"), static_parameter_values_mapping=dict(block.parameters))


def _count_warnings(recorder: pytest.WarningsRecorder, fragment: str) -> int:
    """
    Count the recorded warnings whose message contains a fragment.

    :param recorder: pytest warnings recorder.
    :param fragment: Message fragment.
    :return: Number of matching warnings.
    """
    count: int = 0
    record: object
    for record in recorder.list:
        if fragment in str(record.message):
            count += 1
        else:
            pass
    return count


def test_factory_reports_only_sparse_solvers_it_cannot_honour(recwarn: pytest.WarningsRecorder) -> None:
    """
    A JIT solver honours available selections and warns once for unavailable providers.

    :param recwarn: pytest warnings recorder.
    """
    problem: GenericEmtProblem = _decay_problem()
    build_emt_solver(EmtOptions(solver_type=EmtSolverTypes.Symbolic), problem, 0.0, 1e-4, 1e-5)
    assert _count_warnings(recwarn, "is ignored by the") == 0
    build_emt_solver(EmtOptions(solver_type=EmtSolverTypes.Symbolic, sparse_solver=SparseSolver.SuperLU), problem, 0.0, 1e-4, 1e-5)
    assert _count_warnings(recwarn, "is ignored by the") == 0
    build_emt_solver(EmtOptions(solver_type=EmtSolverTypes.Symbolic, sparse_solver=SparseSolver.UMFPACKTriangular), problem, 0.0, 1e-4, 1e-5)
    assert _count_warnings(recwarn, "is unavailable:") == 1
    build_emt_solver(EmtOptions(solver_type=EmtSolverTypes.Symbolic, sparse_solver=SparseSolver.UMFPACKTriangular), problem, 0.0, 1e-4, 1e-5)
    assert _count_warnings(recwarn, "is unavailable:") == 1
