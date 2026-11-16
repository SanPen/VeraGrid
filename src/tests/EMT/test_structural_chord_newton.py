# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Chord Newton in the sparse structural EMT path: retained factors across steps, refresh rules and a confirming correction."""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pytest

from tests.EMT.test_alignment_step_three_solvers import ForcedEventTracker
from tests.EMT.test_discretization_verify import GenericEmtProblem, make_solver
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var, sin


def _weak_row_block(eps: float, cubic: float, amplitude: float) -> Block:
    """
    Build x' = -x with the weakly scaled algebraic row eps * (z + cubic * z^3 - amplitude * sin(x)) = 0.

    A residual below the tolerance on that row still allows a state error of up to tolerance / eps.

    :param eps: Row scale.
    :param cubic: Cubic coefficient (0 gives a row linear in z).
    :param amplitude: Excitation amplitude.
    :return: Block.
    """
    x: Var = Var("chord_x")
    dx: Var = Var("chord_dx", base_var=x)
    z: Var = Var("chord_z")
    return Block(name="ChordWeakRow", state_vars=list((x,)), diff_vars=list((dx,)), state_eqs=list((-x,)),
                 algebraic_vars=list((z,)),
                 algebraic_eqs=list((Const(eps) * (z + Const(cubic) * z * z * z - Const(amplitude) * sin(x)),)),
                 parameters=dict())


def _consistent_z(cubic: float, amplitude: float) -> float:
    """
    Solve z + cubic * z^3 = amplitude * sin(1) by Newton for a consistent initial algebraic state.

    :param cubic: Cubic coefficient.
    :param amplitude: Excitation amplitude.
    :return: Initial z.
    """
    z: float = 0.5
    target: float = amplitude * float(np.sin(1.0))
    iteration: int
    for iteration in range(200):
        z = z - (z + cubic * z ** 3 - target) / (1.0 + 3.0 * cubic * z * z)
    return z


def _simulate(solver_class: type, cubic: float, amplitude: float, h: float,
              tolerance: float) -> Tuple[np.ndarray, Dict[str, float], bool]:
    """
    Simulate the weak-row system (eps 1e-3) on the sparse path (dense threshold 0) with the trapezoidal rule.

    :param solver_class: Structural solver class.
    :param cubic: Cubic coefficient.
    :param amplitude: Excitation amplitude.
    :param h: Time step.
    :param tolerance: Newton residual tolerance.
    :return: Trajectory, runtime statistics and convergence flag.
    """
    solver: StructuralVectorizedSolver | StructuralCompiledSolver
    problem: GenericEmtProblem
    solver, problem = make_solver(solver_class, _weak_row_block(1e-3, cubic, amplitude), 2.0, h,
                                  DynamicIntegrationMethod.DaeTrapezoidal, tolerance, 0)
    result: Tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(
        x0=np.array((1.0, _consistent_z(cubic, amplitude))), dx0=np.array((-1.0,)))
    return np.asarray(result[1]), solver.get_last_runtime_stats(), bool(result[4])


@pytest.mark.parametrize("h", (0.01, 0.05))
@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
def test_linear_weak_row_state_error_stays_within_the_tolerance(solver_class: type, h: float) -> None:
    """
    On a weak row linear in z, the trajectory at tolerance 1e-6 matches a tolerance-1e-12 reference within 1e-6,
    although the residual test alone accepts a state error up to 1e-3.

    :param solver_class: Structural solver class.
    :param h: Time step.
    """
    trajectory: np.ndarray
    reference: np.ndarray
    stats: Dict[str, float]
    converged: bool
    trajectory, stats, converged = _simulate(solver_class, 0.0, 1.0, h, 1e-6)
    assert converged
    reference, stats, converged = _simulate(solver_class, 0.0, 1.0, h, 1e-12)
    assert converged
    assert float(np.max(np.abs(trajectory - reference))) <= 1e-6


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
def test_nonlinear_weak_row_converges_at_a_tight_tolerance(solver_class: type) -> None:
    """
    A slowly contracting chord must not exhaust the correction budget: the factors are refreshed when the observed
    contraction cannot reach the tolerance in the corrections left.

    :param solver_class: Structural solver class.
    """
    trajectory: np.ndarray
    stats: Dict[str, float]
    converged: bool
    trajectory, stats, converged = _simulate(solver_class, 10.0, 1.0, 0.05, 1e-12)
    assert converged
    assert trajectory.shape == (41, 2)


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
def test_nonlinear_weak_row_state_error_at_the_default_tolerance(solver_class: type) -> None:
    """
    On a weak row nonlinear in z, the trajectory at tolerance 1e-6 matches a tolerance-1e-12 reference within 2e-6.

    :param solver_class: Structural solver class.
    """
    trajectory: np.ndarray
    reference: np.ndarray
    stats: Dict[str, float]
    converged: bool
    trajectory, stats, converged = _simulate(solver_class, 1000.0, 5.0, 0.2, 1e-6)
    assert converged
    reference, stats, converged = _simulate(solver_class, 1000.0, 5.0, 0.2, 1e-12)
    assert converged
    assert float(np.max(np.abs(trajectory - reference))) <= 2e-6


def test_structural_ad_keeps_the_sparse_factorization_across_steps() -> None:
    """StructuralAD evaluates far fewer Jacobians than steps on the sparse path, as StructuralCompiled does."""
    trajectory: np.ndarray
    stats: Dict[str, float]
    converged: bool
    trajectory, stats, converged = _simulate(StructuralVectorizedSolver, 0.0, 1.0, 0.01, 1e-6)
    assert converged
    assert stats["macro_steps"] == 200.0
    assert stats["jacobian_evaluations"] < 0.25 * stats["macro_steps"]
    assert stats["factorization_reuse_hits"] > 0.0


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
def test_factors_are_refreshed_when_the_step_or_aligned_parameters_change(solver_class: type) -> None:
    """
    Fresh factors start the aligned substep at 0.25 (new parameter and step) and the first full step after it (step size
    back to 0.1), and no other substep.

    :param solver_class: Structural solver class.
    """
    x: Var = Var("align_x")
    dx: Var = Var("align_dx", base_var=x)
    z: Var = Var("align_z")
    p: Var = Var("align_p")
    block: Block = Block(name="ChordAlignment", state_vars=list((x,)), diff_vars=list((dx,)), state_eqs=list((-x,)),
                         algebraic_vars=list((z,)), algebraic_eqs=list((z * z * z + z - p,)), parameters=dict(),
                         mode_dict=dict(((p, Const(1.0)),)))
    block.unify_blocks()
    problem: EmtProblemTemplate = EmtProblemTemplate(sys_block=block, glob_time=Var("align_time"),
                                                    static_parameter_values_mapping=dict())
    tracker: ForcedEventTracker = ForcedEventTracker(forced_times=(0.25,), change_time=0.25, parameter_value=3.0)
    solver: StructuralVectorizedSolver | StructuralCompiledSolver = solver_class(
        problem=problem, t0=0.0, t_end=0.4, h=0.1, method=DynamicIntegrationMethod.DaeTrapezoidal, dense_threshold=0,
        newton_tolerance=1e-10)
    result: Tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(
        x0=np.array((1.0, 0.6823278038280193)), dx0=np.array((-1.0,)), params0=np.ones(1), boundary_updater=tracker)
    assert result[4]
    manager_stats: Dict[str, float] = solver._sparse_factorization_manager.get_stats()
    assert manager_stats["invalidations"] == 2.0
    assert float(np.asarray(result[1])[-1, 1]) == pytest.approx(1.2134116627622296, abs=1e-8)
    if solver_class is StructuralCompiledSolver:
        assert solver.get_last_runtime_stats()["forced_factorization_invalidations"] == 2.0
    else:
        pass


class _MovingParameterTracker(ForcedEventTracker):
    """Boundary updater whose runtime parameter moves slightly on every substep, like a held output sampled each step."""

    __slots__ = ()

    def update(self, t: float, x_prev: np.ndarray, full_params: np.ndarray) -> float | None:
        """
        Prepare the substep and move the parameter.

        :param t: Target time.
        :param x_prev: Last accepted state.
        :param full_params: Mutable parameter buffer.
        :return: None.
        """
        retry_time: float | None = super().update(t, x_prev, full_params)
        full_params[0] = 1.0 + 1e-3 * float(np.sin(10.0 * float(t)))
        return retry_time


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
def test_parameters_moving_on_every_substep_do_not_force_factorizations(solver_class: type) -> None:
    """
    Parameters that move on ordinary substeps are left to the refresh rules: far fewer Jacobians than steps.

    :param solver_class: Structural solver class.
    """
    x: Var = Var("moving_x")
    dx: Var = Var("moving_dx", base_var=x)
    z: Var = Var("moving_z")
    p: Var = Var("moving_p")
    block: Block = Block(name="ChordMoving", state_vars=list((x,)), diff_vars=list((dx,)), state_eqs=list((-x,)),
                         algebraic_vars=list((z,)), algebraic_eqs=list((Const(1e-3) * (p * z * z * z + z - sin(x)),)),
                         parameters=dict(), mode_dict=dict(((p, Const(1.0)),)))
    block.unify_blocks()
    problem: EmtProblemTemplate = EmtProblemTemplate(sys_block=block, glob_time=Var("moving_time"),
                                                    static_parameter_values_mapping=dict())
    solver: StructuralVectorizedSolver | StructuralCompiledSolver = solver_class(
        problem=problem, t0=0.0, t_end=2.0, h=0.01, method=DynamicIntegrationMethod.DaeTrapezoidal, dense_threshold=0,
        newton_tolerance=1e-6)
    result: Tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(
        x0=np.array((1.0, _consistent_z(1.0, 1.0))), dx0=np.array((-1.0,)), params0=np.ones(1),
        boundary_updater=_MovingParameterTracker(forced_times=tuple()))
    assert result[4]
    assert solver.get_last_runtime_stats()["jacobian_evaluations"] < 50.0


def test_structural_ad_repeated_runs_are_identical() -> None:
    """Factors and the iteration count do not carry over between simulate() calls of one StructuralAD instance."""
    block: Block = _weak_row_block(1e-3, 10.0, 1.0)
    block.unify_blocks()
    problem: GenericEmtProblem = GenericEmtProblem(sys_block=block, glob_time=Var("t"),
                                                   static_parameter_values_mapping=dict(block.parameters))
    solver: StructuralVectorizedSolver = StructuralVectorizedSolver(
        problem, t0=0.0, t_end=1.0, h=0.05, method=DynamicIntegrationMethod.DaeTrapezoidal, newton_tolerance=1e-6,
        dense_threshold=0)
    first: Tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(
        x0=np.array((1.0, _consistent_z(10.0, 1.0))), dx0=np.array((-1.0,)))
    second: Tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(
        x0=np.array((1.0, _consistent_z(10.0, 1.0))), dx0=np.array((-1.0,)))
    assert first[4] and second[4]
    np.testing.assert_array_equal(np.asarray(first[1]), np.asarray(second[1]))


@pytest.mark.parametrize("eps, p_new, h", ((1e-3, 1000.0, 0.1), (1.0, 10.0, 0.01)))
@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
def test_parameter_jump_on_the_step_grid_converges(solver_class: type, eps: float, p_new: float, h: float) -> None:
    """
    A parameter that jumps at a grid time (no aligned substep) leaves stale factors behind; the substep still
    converges, and the final algebraic state satisfies the new equation.

    :param solver_class: Structural solver class.
    :param eps: Row scale.
    :param p_new: Parameter value after the jump.
    :param h: Time step.
    """
    x: Var = Var("jump_x")
    dx: Var = Var("jump_dx", base_var=x)
    z: Var = Var("jump_z")
    p: Var = Var("jump_p")
    block: Block = Block(name="ChordJump", state_vars=list((x,)), diff_vars=list((dx,)), state_eqs=list((-x,)),
                         algebraic_vars=list((z,)), algebraic_eqs=list((Const(eps) * (p * z * z * z + z - sin(x)),)),
                         parameters=dict(), mode_dict=dict(((p, Const(1.0)),)))
    block.unify_blocks()
    problem: EmtProblemTemplate = EmtProblemTemplate(sys_block=block, glob_time=Var("jump_time"),
                                                    static_parameter_values_mapping=dict())
    tracker: ForcedEventTracker = ForcedEventTracker(forced_times=tuple(), change_time=0.25, parameter_value=p_new)
    solver: StructuralVectorizedSolver | StructuralCompiledSolver = solver_class(
        problem=problem, t0=0.0, t_end=0.6, h=h, method=DynamicIntegrationMethod.DaeTrapezoidal, dense_threshold=0,
        newton_tolerance=1e-6)
    result: Tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(
        x0=np.array((1.0, _consistent_z(1.0, 1.0))), dx0=np.array((-1.0,)), params0=np.ones(1), boundary_updater=tracker)
    assert result[4]
    final: np.ndarray = np.asarray(result[1])[-1]
    assert abs(eps * (p_new * final[1] ** 3 + final[1] - np.sin(final[0]))) < 1e-6


@pytest.mark.parametrize("solver_class", (StructuralVectorizedSolver, StructuralCompiledSolver))
def test_small_correction_budget_retries_with_fresh_factors(solver_class: type) -> None:
    """
    With a budget of two corrections, a substep that fails on inherited factors is retried from the accepted
    history with fresh factors and converges.

    :param solver_class: Structural solver class.
    """
    block: Block = _weak_row_block(1e-3, 10.0, 1.0)
    block.unify_blocks()
    problem: GenericEmtProblem = GenericEmtProblem(sys_block=block, glob_time=Var("t"),
                                                   static_parameter_values_mapping=dict(block.parameters))
    solver: StructuralVectorizedSolver | StructuralCompiledSolver = solver_class(
        problem, t0=0.0, t_end=2.0, h=0.05, method=DynamicIntegrationMethod.DaeTrapezoidal, newton_tolerance=1e-6,
        dense_threshold=0, newton_max_iter=2)
    result: Tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(
        x0=np.array((1.0, _consistent_z(10.0, 1.0))), dx0=np.array((-1.0,)))
    assert result[4]
    assert solver.get_last_runtime_stats()["inherited_factor_retries"] > 0.0
