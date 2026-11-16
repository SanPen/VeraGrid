# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Fixed-tolerance algebraic checks for sparse EMT AD retained factors."""

import numpy as np
import pytest

from VeraGridEngine.basic_structures import Mat, Vec
from VeraGridEngine.enumerations import DynamicIntegrationMethod, SparseSolver
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers import solver_AD
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.Sparse.sparse_solve import get_sparse_lu_provider_status
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, piecewise, sin
from VeraGridEngine.Utils.Symbolic.diagnostic import NewtonDiagnosticsConfig
from tests.EMT.test_alignment_step_three_solvers import ForcedEventTracker


def build_ad_chord_problem(cubic: float | None = None, scale: float = 1.0) -> EmtProblemTemplate:
    """Build a canonical symbolic decay block without a physical network.

    :param cubic: Optional algebraic nonlinearity; None gives constant-J state-only decay.
    :param scale: Fixed algebraic row scaling for nonlinear controls.
    :return: Real EMT problem with explicit consistent initial guesses.
    """
    state: Var = Var("ad_reuse_x")
    derivative: Var = Var("ad_reuse_dx", base_var=state)
    time_var: Var = Var("ad_reuse_time")
    block: Block
    if cubic is None:
        block = Block(name="AdReuseDecay", state_vars=list((state,)), diff_vars=list((derivative,)),
                      state_eqs=list((-state,)), parameters=dict())
        block.unify_blocks()
        problem: EmtProblemTemplate = EmtProblemTemplate(sys_block=block, glob_time=time_var,
                                                         static_parameter_values_mapping=dict())
        problem.init_guess[state.uid] = 1.0
    else:
        algebraic: Var = Var("ad_reuse_z")
        parameter: Var = Var("ad_reuse_p")
        block = Block(name="AdReuseNonlinear", state_vars=list((state,)), diff_vars=list((derivative,)),
            state_eqs=list((-state,)), algebraic_vars=list((algebraic,)),
            algebraic_eqs=list((Const(scale) * (algebraic + Const(cubic) * algebraic * algebraic * algebraic - parameter * sin(state)),)),
            parameters=dict(), mode_dict=dict(((parameter, Const(1.0)),)))
        block.unify_blocks()
        problem = EmtProblemTemplate(sys_block=block, glob_time=time_var, static_parameter_values_mapping=dict())
        initial: float = 0.5
        iteration: int
        for iteration in range(40):
            initial -= (initial + cubic * initial ** 3 - float(np.sin(1.0))) / (1.0 + 3.0 * cubic * initial * initial)
        problem.init_guess[state.uid] = 1.0
        problem.init_guess[algebraic.uid] = initial
    return problem


def build_ad_chord_solver(provider: SparseLinearSolverBackendProvider, problem: EmtProblemTemplate,
                          method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeBackEuler,
                          max_iter: int = 15, dense_threshold: int = 0,
                          diagnostics: NewtonDiagnosticsConfig | None = None) -> JitAdSolver:
    """Construct AD with its existing default nonlinear tolerance.

    :param provider: Actual LU provider.
    :param problem: Real symbolic numerical problem.
    :param method: Existing effective integration enum.
    :param max_iter: Per-attempt correction limit for recovery controls.
    :param dense_threshold: Existing dense/sparse route selection.
    :param diagnostics: Existing optional diagnostics configuration.
    :return: AD solver configured for 32 binary-exact substeps.
    """
    solver: JitAdSolver = JitAdSolver(problem=problem, t0=0.0, t_end=0.5, h=1.0 / 64.0,
        method=method, dense_threshold=dense_threshold, newton_max_iter=max_iter,
        newton_diag_config=diagnostics, sparse_solver_backend_provider=provider)
    return solver


@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.Pardiso))
def test_ad_constant_jacobian_reuses_all_backends(solver_type: SparseSolver) -> None:
    """Prove cross-substep work saving independently of confirming solves.

    :param solver_type: Real provider, skipped explicitly if unavailable.
    :return: None; the same implicit decay recurrence must remain satisfied.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        problem: EmtProblemTemplate = build_ad_chord_problem()
        solver: JitAdSolver = build_ad_chord_solver(provider, problem)
        times: Vec
        values: Mat
        derivatives: Mat
        initialized: bool
        converged: bool
        times, values, derivatives, initialized, converged = solver.simulate(x0=np.ones(1), dx0=-np.ones(1))
        assert converged and initialized and times.shape[0] == 33
        expected: Vec = (1.0 + 1.0 / 64.0) ** (-np.arange(33))
        np.testing.assert_allclose(values[:, 0], expected, atol=1e-12, rtol=0.0)
        np.testing.assert_allclose(derivatives[1:, 0], -values[1:, 0], atol=1e-12, rtol=0.0)
        assert solver.get_last_runtime_stats()["jacobian_evaluations"] <= 3.0
        assert solver.get_last_runtime_stats()["factorization_reuse_hits"] >= 31.0
        assert solver._sparse_linear_solver.get_stats()["numeric_factorizations"] + solver._sparse_linear_solver.get_stats()["numeric_refactorizations"] <= 3.0
        assert solver._sparse_linear_solver.get_stats()["solve_calls"] >= 32.0
        print("AD_CHORD", solver_type.name, solver.get_last_runtime_stats(), solver._sparse_linear_solver.get_stats())


def test_ad_bdf2_startup_invalidates() -> None:
    """Refresh factors when BE startup changes to the BDF2 coefficients.

    :return: None; each returned row satisfies the unchanged BDF recurrence.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    solver: JitAdSolver = build_ad_chord_solver(provider, build_ad_chord_problem(), DynamicIntegrationMethod.DaeBDF2)
    result: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate(x0=np.ones(1), dx0=-np.ones(1))
    assert result[4]
    assert solver.get_last_runtime_stats()["forced_factorization_invalidations"] == 1.0
    assert solver.get_last_runtime_stats()["jacobian_evaluations"] == 2.0
    values: Vec = result[1][:, 0]
    np.testing.assert_allclose((1.5 + 1.0 / 64.0) * values[2:] - 2.0 * values[1:-1] + 0.5 * values[:-2], 0.0, atol=1e-12, rtol=0.0)


def test_ad_repeated_run_resets_reuse() -> None:
    """Reset eligibility while retaining independent accepted outputs.

    :return: None; repeated calls reproduce state and derivative values exactly.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    solver: JitAdSolver = build_ad_chord_solver(provider, build_ad_chord_problem())
    first: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate(x0=np.ones(1), dx0=-np.ones(1))
    second: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate(x0=np.ones(1), dx0=-np.ones(1))
    np.testing.assert_array_equal(first[1], second[1])
    np.testing.assert_array_equal(first[2], second[2])
    assert solver.get_last_runtime_stats()["jacobian_evaluations"] == 1.0
    assert solver._sparse_linear_solver.get_stats()["numeric_factorizations"] == 2.0


@pytest.mark.parametrize("backtracking", (False, True))
@pytest.mark.parametrize("dense_threshold", (0, 100))
def test_ad_dense_and_diagnostics_compatibility(backtracking: bool, dense_threshold: int) -> None:
    """Keep the dense path and diagnostic/backtracking paths algebraically correct.

    :param backtracking: Existing optional line-search setting.
    :param dense_threshold: Existing route threshold, without a tolerance change.
    :return: None; accepted history satisfies the same implicit recurrence.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    config: NewtonDiagnosticsConfig = NewtonDiagnosticsConfig(enable_backtracking=backtracking)
    solver: JitAdSolver = build_ad_chord_solver(provider, build_ad_chord_problem(), dense_threshold=dense_threshold, diagnostics=config)
    result: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate(x0=np.ones(1), dx0=-np.ones(1))
    assert result[4]
    np.testing.assert_allclose(result[1][:, 0], (1.0 + 1.0 / 64.0) ** (-np.arange(33)), atol=1e-12, rtol=0.0)
    # Dense solves and Newton diagnostics both keep a fresh Jacobian per correction.
    stats: dict[str, float] = solver.get_last_runtime_stats()
    assert stats["factorization_reuse_hits"] == 0.0
    assert stats["jacobian_evaluations"] >= 32.0


def test_ad_event_step_and_parameter_invalidation() -> None:
    """Refresh at the split event and return to the original full step.

    :return: None; boundary resolution and commits occur once per local interval.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem: EmtProblemTemplate = build_ad_chord_problem(0.0)
    tracker: ForcedEventTracker = ForcedEventTracker(forced_times=(13.0 / 128.0,), change_time=13.0 / 128.0, parameter_value=3.0)
    solver: JitAdSolver = build_ad_chord_solver(provider, problem)
    result: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate(boundary_updater=tracker)
    assert result[4]
    assert solver.get_last_runtime_stats()["forced_factorization_invalidations"] == 2.0
    assert tracker.resolve_calls == list((True,) * 33)
    assert len(tracker.commit_calls) == 33
    assert abs(result[1][-1, 1] - 3.0 * np.sin(result[1][-1, 0])) < 1e-6


def test_ad_failed_retry_preserves_history() -> None:
    """Reject an impossible algebraic constraint without committing trial history.

    :return: None; retry and boundary rejection occur before any failed output row.
    """
    state: Var = Var("ad_reject_x")
    derivative: Var = Var("ad_reject_dx", base_var=state)
    algebraic: Var = Var("ad_reject_z")
    parameter: Var = Var("ad_reject_p")
    block: Block = Block(name="AdImpossibleConstraint", state_vars=list((state,)), diff_vars=list((derivative,)),
        state_eqs=list((-state,)), algebraic_vars=list((algebraic,)), algebraic_eqs=list((algebraic * algebraic - parameter,)),
        parameters=dict(), mode_dict=dict(((parameter, Const(1.0)),)))
    block.unify_blocks()
    problem: EmtProblemTemplate = EmtProblemTemplate(sys_block=block, glob_time=Var("ad_reject_t"), static_parameter_values_mapping=dict())
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    solver: JitAdSolver = build_ad_chord_solver(provider, problem)
    tracker: ForcedEventTracker = ForcedEventTracker(forced_times=tuple(), change_time=2.0 / 64.0, parameter_value=-1.0)
    result: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate(x0=np.ones(2), dx0=-np.ones(1), params0=np.ones(1), boundary_updater=tracker)
    assert not result[4] and result[0].shape[0] == 2
    assert solver.get_last_runtime_stats()["inherited_factor_retries"] == 1.0
    assert tracker.resolve_calls == list((True, False))
    assert tracker.commit_calls == list((1.0 / 64.0,))
    np.testing.assert_allclose(result[2][-1, 0], -result[1][-1, 0], atol=1e-12, rtol=0.0)


def test_ad_cancel_preserves_completed_prefix() -> None:
    """Finalize current-run counters and revoke factors after cancellation.

    :return: None; history/counters describe only the two completed intervals.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    solver: JitAdSolver = JitAdSolver(problem=build_ad_chord_problem(), t0=0.0, t_end=0.5, h=1.0 / 64.0,
        method=DynamicIntegrationMethod.DaeBackEuler, dense_threshold=0,
        cancel_checker=iter((False, False, True)).__next__, sparse_solver_backend_provider=provider)
    result: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate(x0=np.ones(1), dx0=-np.ones(1))
    assert result[0].shape[0] == 3
    assert solver.get_last_runtime_stats()["macro_steps"] == 2.0
    assert solver.get_last_runtime_stats()["jacobian_evaluations"] == 1.0
    with pytest.raises(RuntimeError):
        solver._sparse_linear_solver.solve_retained(np.ones(1))


def test_ad_nonlinear_refresh_and_retry() -> None:
    """Use a small unchanged per-attempt budget to exercise fresh-factor retry.

    :return: None; successful retries leave accepted derivatives and constraints.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem: EmtProblemTemplate = build_ad_chord_problem(10.0, 1e-3)
    solver: JitAdSolver = build_ad_chord_solver(provider, problem, max_iter=2)
    result: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate()
    print("AD_RECOVERY", result[4], solver.get_last_runtime_stats())
    assert result[4]
    assert solver.get_last_runtime_stats()["inherited_factor_retries"] > 0.0
    np.testing.assert_allclose(result[2][1:, 0], -result[1][1:, 0], atol=1e-8, rtol=0.0)
    assert np.max(np.abs(1e-3 * (result[1][:, 1] + 10.0 * result[1][:, 1] ** 3 - np.sin(result[1][:, 0])))) < solver._newton_tolerance


def test_ad_confirmation_restores_derivative_context() -> None:
    """Discard a confirming trial that enters an invalid algebraic band.

    :return: None; accepted state and derivative refer to the same passing point.
    """
    state: Var = Var("confirm_x")
    derivative: Var = Var("confirm_dx", base_var=state)
    algebraic: Var = Var("confirm_z")
    parameter: Var = Var("confirm_p")
    regular: Expr = algebraic * algebraic - parameter
    branches: np.ndarray = np.empty(2, dtype=object)
    branches[0] = Const(100.0)
    branches[1] = regular
    constraint: Expr = Const(1e-3) * piecewise(algebraic, np.array((1.00994, 1.00996)), branches, regular)
    block: Block = Block(name="ConfirmRollbackControl", state_vars=list((state,)), diff_vars=list((derivative,)),
        state_eqs=list((-state,)), algebraic_vars=list((algebraic,)), algebraic_eqs=list((constraint,)),
        parameters=dict(), mode_dict=dict(((parameter, Const(1.0)),)))
    block.unify_blocks()
    problem: EmtProblemTemplate = EmtProblemTemplate(sys_block=block, glob_time=Var("confirm_t"), static_parameter_values_mapping=dict())
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    solver: JitAdSolver = JitAdSolver(problem=problem, t0=0.0, t_end=1.0 / 64.0, h=1.0 / 64.0,
        method=DynamicIntegrationMethod.DaeBackEuler, dense_threshold=0, sparse_solver_backend_provider=provider)
    tracker: ForcedEventTracker = ForcedEventTracker(forced_times=tuple(), change_time=1.0 / 64.0, parameter_value=1.02)
    result: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate(x0=np.ones(2), dx0=-np.ones(1), params0=np.ones(1), boundary_updater=tracker)
    assert result[4] and result[0].shape[0] == 2
    assert solver.get_last_runtime_stats()["confirming_corrections"] == 1.0
    assert result[1][-1, 1] == pytest.approx(1.01, abs=1e-12)
    assert result[2][-1, 0] == pytest.approx(-result[1][-1, 0], abs=1e-12)
    assert tracker.resolve_calls == list((True,))
    with pytest.raises(RuntimeError):
        solver._sparse_linear_solver.solve_retained(np.ones(2))


def test_ad_cold_chord_uses_legacy_recovery() -> None:
    """Recover a cold within-substep chord failure at the unchanged default tolerance.

    :return: None; recovery assembles fresh J for both permitted corrections.
    """
    state: Var = Var("cold_x")
    derivative: Var = Var("cold_dx", base_var=state)
    algebraic: Var = Var("cold_z")
    parameter: Var = Var("cold_p")
    block: Block = Block(name="ColdChordRecovery", state_vars=list((state,)), diff_vars=list((derivative,)),
        state_eqs=list((-state,)), algebraic_vars=list((algebraic,)),
        algebraic_eqs=list((algebraic + Const(20.0) * algebraic * algebraic * algebraic - parameter,)),
        parameters=dict(), mode_dict=dict(((parameter, Const(0.0)),)))
    block.unify_blocks()
    problem: EmtProblemTemplate = EmtProblemTemplate(sys_block=block, glob_time=Var("cold_t"), static_parameter_values_mapping=dict())
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    solver: JitAdSolver = JitAdSolver(problem=problem, t0=0.0, t_end=1.0 / 64.0, h=1.0 / 64.0,
        method=DynamicIntegrationMethod.DaeBackEuler, dense_threshold=0, newton_max_iter=2,
        sparse_solver_backend_provider=provider)
    tracker: ForcedEventTracker = ForcedEventTracker(forced_times=tuple(), change_time=1.0 / 64.0, parameter_value=1.0 / 64.0)
    result: tuple[Vec, Mat, Mat, bool, bool] = solver.simulate(x0=np.array((1.0, 0.0)), dx0=-np.ones(1), params0=np.zeros(1), boundary_updater=tracker)
    assert result[4] and result[0].shape[0] == 2
    assert solver.get_last_runtime_stats()["inherited_factor_retries"] == 1.0
    assert solver.get_last_runtime_stats()["jacobian_evaluations"] == 3.0
    assert solver.get_last_runtime_stats()["confirming_corrections"] == 0.0
    final: float = float(result[1][-1, 1])
    assert abs(final + 20.0 * final ** 3 - 1.0 / 64.0) < solver._newton_tolerance
    assert tracker.resolve_calls == list((True,))
    assert tracker.commit_calls == list((1.0 / 64.0,))


def _failing_sparse_solve(*args: object, **kwargs: object) -> Vec:
    """Stand-in fresh-Jacobian sparse solve that raises like a singular factorization.

    :param args: Positional arguments of solve_sparse_system_once.
    :param kwargs: Keyword arguments of solve_sparse_system_once.
    :return: Never returns.
    """
    raise RuntimeError("Factor is exactly singular")


def test_ad_fresh_jacobian_solver_errors_propagate(monkeypatch: pytest.MonkeyPatch) -> None:
    """A solver error on a fresh Jacobian keeps propagating; only retained-factor failures become retries.

    :param monkeypatch: Replaces the fresh sparse solve with a failing stand-in.
    :return: None.
    """
    monkeypatch.setattr(solver_AD, "solve_sparse_system_once", _failing_sparse_solve)
    solver: JitAdSolver = build_ad_chord_solver(SuperLUSparseBackendProvider(), build_ad_chord_problem())
    with pytest.raises(RuntimeError, match="exactly singular"):
        solver.simulate(x0=np.ones(1), dx0=-np.ones(1))

