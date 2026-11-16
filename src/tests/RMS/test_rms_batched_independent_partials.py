# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Independent derivative columns in the compiled scalar RMS Jacobian."""

import numpy as np
import pytest
from scipy import sparse

from VeraGridEngine.Simulations.Rms.numerical.rms_batched_ad import RmsBatchedAd
from VeraGridEngine.Simulations.Rms.numerical.rms_ad_backend_numba_comp import RmsEquationAdEvaluator
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_numba_comp import (
    RmsProblemDae as CompiledRmsProblemDae,
)
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_vectorized import RmsProblemDaeVec
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_full_vectorized import RmsProblemDaeFullVec
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_full_vectorized_numba_comp import (
    RmsProblemDaeFullVec as CompiledFullVectorizedRmsProblem,
)
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import RmsInitializationMethod
from tests.Base.test_dynamic_results_save_load import _build_rms_driver


def test_batched_ad_keeps_derivative_input_independent_of_its_base():
    state = Var("state")
    algebraic = Var("algebraic")
    derivative = Var("derivative", base_var=state)
    backend = RmsBatchedAd(
        [-state + 2 * derivative, algebraic + state * derivative],
        [state, algebraic], [], [derivative], independent_derivatives=True,
    )

    values = np.array([3.0, 4.0])
    derivatives = np.array([5.0])
    matrix = backend.evaluate_jacobian(
        values, np.empty(0), values, derivatives, h=0.25)

    assert matrix.shape == (2, 3)
    np.testing.assert_allclose(matrix.toarray(),
                               [[-1.0, 0.0, 2.0], [5.0, 1.0, 3.0]])


def test_one_batched_backend_projects_raw_partials_for_backward_euler():
    state = Var("state")
    algebraic = Var("algebraic")
    derivative = Var("derivative", base_var=state)
    evaluator = RmsEquationAdEvaluator(
        [state], [algebraic], [-state + 2 * derivative],
        [algebraic + state * derivative], [derivative], [], [],
    )
    values = np.array([3.0, 4.0])
    derivatives = np.array([5.0])
    empty = np.empty(0)
    backend = evaluator._backend

    for h in (0.25, 0.5):
        partials = evaluator.evaluate_independent_partials(values, derivatives, empty, empty)
        np.testing.assert_allclose(partials.toarray(),
                                   [[-1.0, 0.0, 2.0], [5.0, 1.0, 3.0]])
        raw = evaluator.evaluate_raw_jacobian(values, derivatives, empty, empty, h)
        np.testing.assert_allclose(raw.toarray(),
                                   [[-1.0 + 2.0 / h, 0.0],
                                    [5.0 + 3.0 / h, 1.0]])
        newton = evaluator.evaluate_jacobian(values, derivatives, values, empty, empty, h)
        np.testing.assert_allclose(newton.toarray(),
                                   [[h - 1.0, 0.0], [5.0 + 3.0 / h, 1.0]])
        assert evaluator._backend is backend


@pytest.mark.parametrize("problem_class", (
    RmsProblemDae, CompiledRmsProblemDae, CompiledFullVectorizedRmsProblem,
))
def test_raw_partials_reconstruct_existing_backward_euler_jacobian(problem_class):
    built = _build_rms_driver()
    problem = problem_class(
        built.grid,
        RmsOptions(time_step=0.01, simulation_time=0.03, tolerance=1e-6,
                   initialization_method=RmsInitializationMethod.Explicit,
                   use_init_values=False),
        built.pf_results,
    )
    problem.set_events_group(built.grid.rms_events_groups[0])
    x, dx = problem.get_x0(), problem.get_dx0()
    j11, j12, j13, j21, j22, j23 = problem.evaluate_jacobian_partials(x, dx)
    if problem_class is CompiledFullVectorizedRmsProblem:
        assert problem._j13_fn_by_types is problem._raw_partial_fns_by_type["j13_raw"]
        assert problem._j23_fn_by_types is problem._raw_partial_fns_by_type["j23_raw"]
    elif problem_class is RmsProblemDae:
        np.testing.assert_allclose(
            problem._j13_fn(x, dx, problem._variable_parameters_values,
                            problem._constant_params, 0.0).toarray(), j13.toarray())
        np.testing.assert_allclose(
            problem._j23_fn(x, dx, problem._variable_parameters_values,
                            problem._constant_params, 0.0).toarray(), j23.toarray())
    np.testing.assert_allclose(
        problem.evaluate_equation_jacobian(x, dx).toarray(),
        sparse.bmat([[j11, j12], [j21, j22]], format="csc").toarray(),
        rtol=1e-10, atol=1e-10,
    )
    bases = [problem.uid2idx_vars[var.base_var.uid] for var in problem._diff_vars]
    derivative_map = sparse.csc_matrix(
        (np.ones(len(bases)), (np.arange(len(bases)), bases)),
        shape=(len(bases), len(x)),
    )
    alpha = 100.0
    reconstructed = (sparse.bmat([[j11, j12], [j21, j22]], format="csc")
                     + alpha * sparse.vstack([j13, j23], format="csc") @ derivative_map)
    b11, b12, b21, b22 = problem.evaluate_jacobian_blocks(x, dx, 1.0 / alpha)
    chained = sparse.bmat([[b11, b12], [b21, b22]], format="csc")

    assert j23.nnz > 0
    expected = (reconstructed if problem_class is not RmsProblemDae else
                sparse.bmat([[j11, j12], [j21, j22]], format="csc"))
    np.testing.assert_allclose(expected.toarray(), chained.toarray(),
                               rtol=1e-10, atol=1e-10)


@pytest.mark.parametrize("problem_class", (
    RmsProblemDaeVec, RmsProblemDaeFullVec, CompiledFullVectorizedRmsProblem,
))
def test_vectorized_derivative_function_maps_are_named(problem_class):
    built = _build_rms_driver()
    problem = problem_class(
        built.grid,
        RmsOptions(time_step=0.01, simulation_time=0.03,
                   initialization_method=RmsInitializationMethod.Explicit,
                   use_init_values=False),
        built.pf_results,
    )
    problem.set_events_group(built.grid.rms_events_groups[0])

    assert problem._j13_fn_by_types is problem._raw_partial_fns_by_type["j13_raw"]
    assert problem._j23_fn_by_types is problem._raw_partial_fns_by_type["j23_raw"]
