# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Accepted-step history updates and finite checks of the structural EMT solver loops."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pytest

from tests.EMT.test_discretization_verify import GenericEmtProblem, make_solver
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Simulations.EMT.solvers import structural_compiled_solver
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.diagnostic import NewtonDiagnosticsConfig
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


@pytest.mark.parametrize("bad_value", (np.nan, np.inf, -np.inf))
@pytest.mark.parametrize("position", (0, 3, 6))
def test_all_finite_detects_every_non_finite_entry(bad_value: float, position: int) -> None:
    """
    The finite check finds a NaN or infinite entry at the start, in the middle and at the end of a vector.

    :param bad_value: Non-finite value.
    :param position: Index of the non-finite entry.
    """
    values: np.ndarray = np.linspace(-1.0e300, 1.0e300, 7)
    assert structural_compiled_solver._all_finite(values)
    values[position] = bad_value
    assert not structural_compiled_solver._all_finite(values)
    assert structural_compiled_solver._all_finite(values) == bool(np.all(np.isfinite(values)))


def test_all_finite_accepts_empty_and_extreme_finite_vectors() -> None:
    """An empty vector is finite, and so are the largest, smallest and subnormal magnitudes and signed zeros."""
    extremes: np.ndarray = np.array((np.finfo(np.float64).max, -np.finfo(np.float64).max, np.finfo(np.float64).tiny,
                                     5.0e-324, -0.0, 0.0))
    assert structural_compiled_solver._all_finite(np.empty(0))
    assert structural_compiled_solver._all_finite(extremes)


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
@pytest.mark.parametrize("dense_threshold", (0, 100))
@pytest.mark.parametrize("same_order", (True, False))
def test_structural_trapezoidal_history_follows_the_accepted_states(
        solver_class: type[StructuralVectorizedSolver] | type[StructuralCompiledSolver], dense_threshold: int,
        same_order: bool) -> None:
    """
    Every derivative a structural solver publishes under the trapezoidal rule is the trapezoidal update of the
    accepted states, bit for bit, and the run covers the horizon and satisfies the model, whether the derivatives are
    declared in the state order or in the opposite one.

    :param solver_class: Structural EMT solver.
    :param dense_threshold: Force sparse (0) or dense (100) linear solves.
    :param same_order: Declare the derivatives in the state order instead of the opposite one.
    """
    slow: Var = Var("trap_slow")
    fast: Var = Var("trap_fast")
    dslow: Var = Var("trap_dslow", base_var=slow)
    dfast: Var = Var("trap_dfast", base_var=fast)
    block: Block = Block(name="TrapHistory", state_vars=list((slow, fast)), state_eqs=list((-slow, -2.0 * fast)),
                         diff_vars=list((dslow, dfast) if same_order else (dfast, dslow)), parameters=dict())
    solver: StructuralVectorizedSolver | StructuralCompiledSolver
    problem: GenericEmtProblem
    solver, problem = make_solver(solver_class, block, 0.5, 0.01, DynamicIntegrationMethod.DaeTrapezoidal,
                                  1e-10, dense_threshold)
    pairs: Tuple[Tuple[int, int], ...] = ((problem.uid2idx_diff[dslow.uid], problem.uid2idx_vars[slow.uid]),
                                          (problem.uid2idx_diff[dfast.uid], problem.uid2idx_vars[fast.uid]))
    seed: np.ndarray = np.empty(2)
    seed[problem.uid2idx_vars[slow.uid]] = 1.0
    seed[problem.uid2idx_vars[fast.uid]] = 2.0
    slope: np.ndarray = np.empty(2)
    slope[problem.uid2idx_diff[dslow.uid]] = -1.0
    slope[problem.uid2idx_diff[dfast.uid]] = -4.0
    times: np.ndarray
    values: np.ndarray
    derivatives: np.ndarray
    well: bool
    converged: bool
    times, values, derivatives, well, converged = solver.simulate(x0=seed, dx0=slope)
    assert well and converged and times.size == 51
    step: int
    diff_index: int
    base_index: int
    for step in range(times.size - 1):
        h_eff: float = float(times[step + 1] - times[step])
        for diff_index, base_index in pairs:
            expected: float = ((2.0 / h_eff) * (values[step + 1, base_index] - values[step, base_index])
                               - derivatives[step, diff_index])
            assert derivatives[step + 1, diff_index] == expected
    np.testing.assert_allclose(derivatives[1:, pairs[0][0]] + values[1:, pairs[0][1]], 0.0, atol=1e-9, rtol=0)
    np.testing.assert_allclose(derivatives[1:, pairs[1][0]] + 2.0 * values[1:, pairs[1][1]], 0.0, atol=1e-9, rtol=0)


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
@pytest.mark.parametrize("same_order", (True, False))
def test_structural_trapezoidal_direct_residual_follows_the_derivative_order(
        solver_class: type[StructuralVectorizedSolver] | type[StructuralCompiledSolver], same_order: bool) -> None:
    """
    Twenty-four decays with distinct rates take the ungrouped (direct) residual path; under the trapezoidal rule the
    states follow the exact one-step recurrence and the published derivatives the model, in either declaration order.

    :param solver_class: Structural EMT solver.
    :param same_order: Declare the derivatives in the state order instead of the opposite one.
    """
    n_decays: int = 24
    h: float = 0.01
    states: List[Var] = list([Var(f"direct_x{i}") for i in range(n_decays)])
    derivatives_declared: List[Var] = list([Var(f"direct_dx{i}", base_var=x) for i, x in enumerate(states)])
    rates: np.ndarray = 1.0 + 0.25 * np.arange(n_decays)
    block: Block = Block(name="DirectResidual", state_vars=states,
                         state_eqs=list([Const(-float(rate)) * x for rate, x in zip(rates, states)]),
                         diff_vars=derivatives_declared if same_order else list(reversed(derivatives_declared)),
                         parameters=dict())
    solver: StructuralVectorizedSolver | StructuralCompiledSolver
    problem: GenericEmtProblem
    solver, problem = make_solver(solver_class, block, 0.5, h, DynamicIntegrationMethod.DaeTrapezoidal, 1e-10, 0)
    state_indices: List[int] = list([problem.uid2idx_vars[x.uid] for x in states])
    diff_indices: List[int] = list([problem.uid2idx_diff[d.uid] for d in derivatives_declared])
    seed: np.ndarray = np.empty(n_decays)
    seed[state_indices] = 1.0
    slope: np.ndarray = np.empty(n_decays)
    slope[diff_indices] = -rates
    times: np.ndarray
    values: np.ndarray
    derivatives: np.ndarray
    well: bool
    converged: bool
    times, values, derivatives, well, converged = solver.simulate(x0=seed, dx0=slope)
    assert well and converged and times.size == 51
    ratio: np.ndarray = (1.0 - 0.5 * h * rates) / (1.0 + 0.5 * h * rates)
    np.testing.assert_allclose(values[:, state_indices], ratio[np.newaxis, :] ** np.arange(times.size)[:, np.newaxis],
                               atol=1e-12, rtol=0)
    np.testing.assert_allclose(derivatives[1:, diff_indices] + rates[np.newaxis, :] * values[1:, state_indices], 0.0,
                               atol=1e-8, rtol=0)


# StructuralAD's default predictor already is the explicit Euler one; StructuralCompiled's default copies the state.
@pytest.mark.parametrize("solver_class, pred_method", ((StructuralVectorizedSolver, None),
                                                       (StructuralCompiledSolver, None),
                                                       (StructuralCompiledSolver, DynamicIntegrationMethod.OdeEuler)))
@pytest.mark.parametrize("method", (DynamicIntegrationMethod.DaeTrapezoidal, DynamicIntegrationMethod.DaeBackEuler,
                                    DynamicIntegrationMethod.DaeBDF2))
def test_structural_run_does_not_depend_on_the_derivative_order(
        solver_class: type[StructuralVectorizedSolver] | type[StructuralCompiledSolver],
        method: DynamicIntegrationMethod, pred_method: DynamicIntegrationMethod | None) -> None:
    """
    On s' = -s f, f' = -2 f, z = f' s a structural solver produces the same states bit for bit, the same derivatives
    per declared derivative and the same Newton work whether the derivatives are declared in the state order or in the
    opposite one: the kernels, the predictor and the Jacobian read one derivative history.

    :param solver_class: Structural EMT solver.
    :param method: Integration rule.
    :param pred_method: Solver default predictor (None) or the explicit Euler predictor.
    """
    values_by_order: List[np.ndarray] = list()
    derivatives_by_order: List[np.ndarray] = list()
    work_by_order: List[Dict[str, float]] = list()
    same_order: bool
    for same_order in (True, False):
        s: Var = Var("order_s")
        f: Var = Var("order_f")
        z: Var = Var("order_z")
        ds: Var = Var("order_ds", base_var=s)
        df: Var = Var("order_df", base_var=f)
        block: Block = Block(name="OrderInvariance", state_vars=list((s, f)), state_eqs=list((-(s * f), -2.0 * f)),
                             diff_vars=list((ds, df) if same_order else (df, ds)), algebraic_vars=list((z,)),
                             algebraic_eqs=list((z - df * s,)), parameters=dict())
        block.unify_blocks()
        problem: GenericEmtProblem = GenericEmtProblem(sys_block=block, glob_time=Var("t"),
                                                       static_parameter_values_mapping=dict(block.parameters))
        solver: StructuralVectorizedSolver | StructuralCompiledSolver = solver_class(
            problem, t0=0.0, t_end=0.2, h=0.01, method=method, pred_method=pred_method, newton_tolerance=1e-12,
            dense_threshold=0, newton_diag_config=NewtonDiagnosticsConfig())
        assert list(problem.uid2idx_vars[v.uid] for v in (s, f, z)) == list((0, 1, 2))
        seed: np.ndarray = np.array((1.0, 0.5, -1.0))
        slope: np.ndarray = np.empty(2)
        slope[problem.uid2idx_diff[ds.uid]] = -0.5
        slope[problem.uid2idx_diff[df.uid]] = -1.0
        times: np.ndarray
        values: np.ndarray
        derivatives: np.ndarray
        well: bool
        converged: bool
        times, values, derivatives, well, converged = solver.simulate(x0=seed, dx0=slope)
        assert well and converged and times.size == 21
        values_by_order.append(values)
        derivatives_by_order.append(derivatives[:, list((problem.uid2idx_diff[ds.uid], problem.uid2idx_diff[df.uid]))])
        work: Dict[str, float] = dict()
        key: str
        value: float
        for key, value in solver.get_last_runtime_stats().items():
            if not key.endswith("_s"):
                work[key] = value
            else:
                pass
        work_by_order.append(work)
    assert np.array_equal(values_by_order[0], values_by_order[1])
    assert np.array_equal(derivatives_by_order[0], derivatives_by_order[1])
    assert work_by_order[0] == work_by_order[1]


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
@pytest.mark.parametrize("method", (DynamicIntegrationMethod.DaeTrapezoidal, DynamicIntegrationMethod.DaeBackEuler,
                                    DynamicIntegrationMethod.DaeBDF2))
def test_structural_partially_declared_derivatives_are_rejected_only_by_the_trapezoidal_rule(
        solver_class: type[StructuralVectorizedSolver] | type[StructuralCompiledSolver],
        method: DynamicIntegrationMethod) -> None:
    """
    A block that declares a derivative for one state but not for the other is rejected when the trapezoidal solver is
    built, before any kernel is compiled, with an error naming the undeclared state; the backward Euler and BDF2 rules,
    whose kernels do not read the derivative history, integrate it and publish the declared derivative.

    :param solver_class: Structural EMT solver.
    :param method: Integration rule.
    """
    declared: Var = Var("partial_declared")
    undeclared: Var = Var("partial_undeclared")
    ddeclared: Var = Var("partial_ddeclared", base_var=declared)
    block: Block = Block(name="PartialDerivatives", state_vars=list((declared, undeclared)),
                         state_eqs=list((-declared, -2.0 * undeclared)), diff_vars=list((ddeclared,)),
                         parameters=dict())
    if method == DynamicIntegrationMethod.DaeTrapezoidal:
        with pytest.raises(ValueError, match="partial_undeclared"):
            make_solver(solver_class, block, 0.1, 0.01, method, 1e-10, 0)
    else:
        solver: StructuralVectorizedSolver | StructuralCompiledSolver
        problem: GenericEmtProblem
        solver, problem = make_solver(solver_class, block, 0.1, 0.01, method, 1e-10, 0)
        times: np.ndarray
        values: np.ndarray
        derivatives: np.ndarray
        well: bool
        converged: bool
        times, values, derivatives, well, converged = solver.simulate(x0=np.array((1.0, 2.0)), dx0=-np.ones(1))
        assert well and converged and times.size == 11
        declared_index: int = problem.uid2idx_vars[declared.uid]
        undeclared_index: int = problem.uid2idx_vars[undeclared.uid]
        np.testing.assert_allclose(derivatives[1:, problem.uid2idx_diff[ddeclared.uid]] + values[1:, declared_index],
                                   0.0, atol=1e-8, rtol=0)
        if method == DynamicIntegrationMethod.DaeBackEuler:
            steps: np.ndarray = np.arange(times.size)
            np.testing.assert_allclose(values[:, declared_index], 1.01 ** -steps, atol=1e-12, rtol=0)
            np.testing.assert_allclose(values[:, undeclared_index], 2.0 * 1.02 ** -steps, atol=1e-12, rtol=0)
        else:
            np.testing.assert_allclose(values[:, undeclared_index], 2.0 * np.exp(-2.0 * times), atol=1e-3, rtol=0)


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
@pytest.mark.parametrize("method", (DynamicIntegrationMethod.DaeTrapezoidal, DynamicIntegrationMethod.DaeBackEuler))
@pytest.mark.parametrize("same_order", (True, False))
def test_structural_derivative_of_an_algebraic_variable_follows_the_rule(
        solver_class: type[StructuralVectorizedSolver] | type[StructuralCompiledSolver],
        method: DynamicIntegrationMethod, same_order: bool) -> None:
    """
    A derivative declared on an algebraic variable (y = 2 x with x' = -x) is discretized and published like a state
    derivative: its published value and the algebraic variable w = y' both equal -2 x, in either declaration order.

    :param solver_class: Structural EMT solver.
    :param method: Trapezoidal or backward Euler rule.
    :param same_order: Declare the state derivative before the algebraic one instead of after it.
    """
    x: Var = Var("algebraic_base_x")
    y: Var = Var("algebraic_base_y")
    w: Var = Var("algebraic_base_w")
    dx: Var = Var("algebraic_base_dx", base_var=x)
    dy: Var = Var("algebraic_base_dy", base_var=y)
    block: Block = Block(name="AlgebraicBaseDerivative", state_vars=list((x,)), state_eqs=list((-x,)),
                         diff_vars=list((dx, dy) if same_order else (dy, dx)), algebraic_vars=list((y, w)),
                         algebraic_eqs=list((y - 2.0 * x, w - dy)), parameters=dict())
    solver: StructuralVectorizedSolver | StructuralCompiledSolver
    problem: GenericEmtProblem
    solver, problem = make_solver(solver_class, block, 0.2, 0.01, method, 1e-12, 0)
    seed: np.ndarray = np.empty(3)
    seed[problem.uid2idx_vars[x.uid]] = 1.0
    seed[problem.uid2idx_vars[y.uid]] = 2.0
    seed[problem.uid2idx_vars[w.uid]] = -2.0
    slope: np.ndarray = np.empty(2)
    slope[problem.uid2idx_diff[dx.uid]] = -1.0
    slope[problem.uid2idx_diff[dy.uid]] = -2.0
    times: np.ndarray
    values: np.ndarray
    derivatives: np.ndarray
    well: bool
    converged: bool
    times, values, derivatives, well, converged = solver.simulate(x0=seed, dx0=slope)
    assert well and converged and times.size == 21
    state: np.ndarray = values[1:, problem.uid2idx_vars[x.uid]]
    np.testing.assert_allclose(derivatives[1:, problem.uid2idx_diff[dy.uid]] + 2.0 * state, 0.0, atol=1e-8, rtol=0)
    np.testing.assert_allclose(values[1:, problem.uid2idx_vars[w.uid]] + 2.0 * state, 0.0, atol=1e-8, rtol=0)


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
@pytest.mark.parametrize("method", (DynamicIntegrationMethod.DaeTrapezoidal, DynamicIntegrationMethod.DaeBackEuler))
def test_structural_history_without_declared_derivatives_stays_in_runtime_order(
        solver_class: type[StructuralVectorizedSolver] | type[StructuralCompiledSolver],
        method: DynamicIntegrationMethod) -> None:
    """
    A block that declares no derivative keeps the caller's derivative vector, in runtime-variable order, as the history:
    x' = -x from x = 1 with slope -1 follows the exact one-step recurrence of the rule.

    :param solver_class: Structural EMT solver.
    :param method: Trapezoidal or backward Euler rule.
    """
    h: float = 0.1
    x: Var = Var("legacy_x")
    block: Block = Block(name="LegacyHistory", state_vars=list((x,)), state_eqs=list((-x,)), parameters=dict())
    solver: StructuralVectorizedSolver | StructuralCompiledSolver
    problem: GenericEmtProblem
    solver, problem = make_solver(solver_class, block, 0.5, h, method, 1e-10, 0)
    assert len(problem.get_diff_vars()) == 0
    times: np.ndarray
    values: np.ndarray
    derivatives: np.ndarray
    well: bool
    converged: bool
    times, values, derivatives, well, converged = solver.simulate(x0=np.ones(1), dx0=-np.ones(1))
    assert well and converged and times.size == 6
    ratio: float
    if method == DynamicIntegrationMethod.DaeTrapezoidal:
        ratio = (1.0 - 0.5 * h) / (1.0 + 0.5 * h)
    else:
        ratio = 1.0 / (1.0 + h)
    np.testing.assert_allclose(values[:, 0], ratio ** np.arange(times.size), atol=1e-12, rtol=0)


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
@pytest.mark.parametrize("dense_threshold", (0, 100))
def test_newton_stops_on_a_non_finite_residual(solver_class: type, dense_threshold: int) -> None:
    """
    A NaN parameter makes the first residual non-finite: the structural solvers reject the step before evaluating any
    Jacobian instead of spending the correction budget.

    :param solver_class: Structural EMT solver class.
    :param dense_threshold: Force sparse (0) or dense (100) linear solves.
    """
    x: Var = Var("nan_x")
    k: Var = Var("nan_k")
    block: Block = Block(name="NanDecay", state_vars=list((x,)), state_eqs=list((-k * x,)),
                         parameters=dict({k: Const(np.nan)}))
    solver: StructuralVectorizedSolver | StructuralCompiledSolver
    problem: GenericEmtProblem
    solver, problem = make_solver(solver_class, block, 0.05, 0.01, DynamicIntegrationMethod.DaeBackEuler, 1e-10,
                                  dense_threshold)
    result: Tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(x0=np.ones(1), dx0=np.zeros(1))
    assert not result[3] and not result[4]
    assert result[0].size == 1
    assert solver.get_last_runtime_stats()["jacobian_evaluations"] == 0.0
