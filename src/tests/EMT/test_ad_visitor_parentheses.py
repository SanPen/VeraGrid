# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""AD Jacobians keep non-associative operands parenthesized (ADVisitor value strings)."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import numpy.typing as npt
import pytest

from tests.EMT.test_discretization_verify import make_solver
from tests.EMT.test_structural_compiled_solver import build_full_params
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver, evaluate_batched_residual as evaluate_ad_residual
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import (
    StructuralVectorizedSolver,
    build_residual_evaluator,
    evaluate_vectorized_residual,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.jit_compiler import EquationCompiler
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, exp, heaviside, sin


def _pattern_block() -> Tuple[Block, List[Var]]:
    """
    Build a block whose rows exercise every channel of the parenthesization defect.

    Channels: '-' and '/' right operands inside '*', '/' and '**'; zero-left '-';
    function arguments (sin, exp); the Kundur shape heaviside(x - (y - z)) * x;
    propagation through '+'; and a repeated pattern that becomes a CSE temporary.

    :return: Block and its unknowns in solver order (states first).
    """
    x1: Var = Var("pat_x1")
    x2: Var = Var("pat_x2")
    d1: Var = Var("pat_d1", base_var=x1)
    d2: Var = Var("pat_d2", base_var=x2)
    names: List[str] = list(("y_minus_minus", "y_minus_plus", "y_div_mul", "y_div_div", "y_zero_left", "y_sin", "y_exp", "y_heaviside",
                             "y_plus_chain", "y_cse_a", "y_cse_b", "y_power"))
    algebraic: List[Var] = list()
    name: str
    for name in names:
        algebraic.append(Var(name))
    repeated: Expr = x2 - (x1 - x2)
    equations: List[Expr] = list((
        algebraic[0] - x1 * (x2 - (x1 - x2 * x2)),
        algebraic[1] - x1 * (x2 - (x1 + Const(0.5))),
        algebraic[2] - x2 * (x1 / (x2 * x1)),
        algebraic[3] - x2 * (x1 / (x2 / Const(3.0))),
        algebraic[4] - (Const(0.0) - (x1 + x2)) * x2,
        algebraic[5] - sin(x1 - (x2 - x1 * x1)),
        algebraic[6] - exp(x2 - (x1 - Const(0.2))),
        algebraic[7] - heaviside(x1 - (x2 - Const(1.0))) * x1,
        algebraic[8] - x1 * (algebraic[0] + (x2 - (x1 - x2))),
        algebraic[9] - x1 * repeated,
        algebraic[10] - x2 * (x2 - (x1 - x2)),
        algebraic[11] - (x2 - (x1 - x2 * x2)) ** Const(2.0),
    ))
    block: Block = Block(name="ParenthesisPatterns", state_vars=list((x1, x2)), diff_vars=list((d1, d2)),
                         state_eqs=list((-x1 + algebraic[0], -x2 + Const(0.1) * algebraic[1])),
                         algebraic_vars=algebraic, algebraic_eqs=equations, parameters=dict())
    return block, list((x1, x2)) + algebraic


def _jacobian_and_residual(solver: object, method: DynamicIntegrationMethod, state: npt.NDArray, params: npt.NDArray, previous: npt.NDArray,
                           slope: npt.NDArray, h: float, previous2: npt.NDArray) -> Tuple[npt.NDArray, List[npt.NDArray]]:
    """
    Return the AD Jacobian of a solver and its residual at +/- column perturbations.

    :param solver: AD solver (JitAdSolver, StructuralVectorizedSolver or StructuralCompiledSolver).
    :param method: Integration method.
    :param state: Evaluation point.
    :param params: Full parameter vector.
    :param previous: Previous unknowns.
    :param slope: Derivative history of the states.
    :param h: Step size.
    :param previous2: Unknowns two steps back.
    :return: Dense AD Jacobian and the central-difference columns.
    """
    n: int = state.shape[0]
    columns: List[npt.NDArray] = list()
    residual: npt.NDArray[np.float64] = np.empty(n)
    if isinstance(solver, JitAdSolver):
        solver.build_jit_ad(method=method)
        analytic: npt.NDArray = solver.jit_jacobian_ad[method](state, params, previous, slope, h, previous2).toarray().copy()
    elif isinstance(solver, StructuralVectorizedSolver):
        solver.auto_detect_vectorization(method)
        analytic = solver.vec_jacobian(state, params, previous, slope, h, previous2).toarray().copy()
    else:
        solver._build_vectorized_backend(method)
        analytic = solver._jacobian_evaluator.evaluate(state, params, previous, slope, h, previous2).toarray().copy()
    column: int
    for column in range(n):
        step: float = 1.0e-7 * max(1.0, abs(float(state[column])))
        samples: List[npt.NDArray] = list()
        sign: float
        for sign in (1.0, -1.0):
            trial: npt.NDArray[np.float64] = state.copy()
            trial[column] += sign * step
            if isinstance(solver, JitAdSolver):
                evaluate_ad_residual(solver.jit_kernels_ad[method], trial, params, previous, slope, h, previous2, residual)
            elif isinstance(solver, StructuralVectorizedSolver):
                evaluate_vectorized_residual(build_residual_evaluator(solver.fused_residual, solver.vec_flat_args), trial, params, previous, slope, h,
                                             previous2, residual)
            else:
                solver._residual_assembler.evaluate(trial, params, previous, slope, h, previous2, residual)
            samples.append(residual.copy())
        columns.append((samples[0] - samples[1]) / (2.0 * step))
    return analytic, columns


@pytest.mark.parametrize("solver_class", (JitAdSolver, StructuralVectorizedSolver, StructuralCompiledSolver))
@pytest.mark.parametrize("method", (DynamicIntegrationMethod.DaeTrapezoidal, DynamicIntegrationMethod.DaeBackEuler, DynamicIntegrationMethod.DaeBDF2))
def test_ad_jacobian_matches_central_differences_on_every_channel(solver_class: type, method: DynamicIntegrationMethod) -> None:
    """
    Each AD solver's Jacobian equals central differences of its own residual on every defect channel.

    :param solver_class: AD solver class.
    :param method: Integration method.
    :return: None.
    """
    block: Block
    unknowns: List[Var]
    block, unknowns = _pattern_block()
    solver: object
    problem: EmtProblemTemplate
    solver, problem = make_solver(solver_class, block, 0.3, 0.01, method, 1e-10, 0)
    state: npt.NDArray[np.float64] = np.linspace(0.4, 1.5, len(unknowns))
    state[0] = 0.4
    state[1] = 0.7
    previous: npt.NDArray[np.float64] = state - 0.01
    previous2: npt.NDArray[np.float64] = state - 0.02
    slope: npt.NDArray[np.float64] = np.full(len(problem.get_diff_vars()), 0.3)
    params: npt.NDArray[np.float64] = build_full_params(problem)

    # Heaviside argument x1 - (x2 - 1) stays far from its switching surface.
    assert abs(state[0] - (state[1] - 1.0)) >= 1.0e-3

    analytic: npt.NDArray
    columns: List[npt.NDArray]
    analytic, columns = _jacobian_and_residual(solver, method, state, params, previous, slope, 0.01, previous2)
    numeric: npt.NDArray[np.float64] = np.column_stack(columns)
    floor: npt.NDArray[np.float64] = 1.0e-8 * np.maximum(1.0, np.max(np.abs(numeric), axis=1, keepdims=True))
    np.testing.assert_allclose(analytic, numeric, rtol=1.0e-6, atol=float(np.max(floor)))


def test_zero_left_minus_through_compile_ad_kernel() -> None:
    """
    compile_ad_kernel differentiates (0 - (a + b)) * a correctly (zero-left '-' value string).

    :return: None.
    """
    a: Var = Var("zl_a")
    b: Var = Var("zl_b")
    equation: Expr = (Const(0.0) - (a + b)) * a
    compiler: EquationCompiler = EquationCompiler(list((a, b)), list(), list(), DynamicIntegrationMethod.DaeTrapezoidal)
    kernel: object = compiler.compile_ad_kernel(list((equation,)), use_cse=False)
    states: npt.NDArray[np.float64] = np.array((0.4, 0.9))
    empty: npt.NDArray[np.float64] = np.zeros(0)
    column: int
    for column in range(2):
        seeds: npt.NDArray[np.float64] = np.zeros(2)
        seeds[column] = 1.0
        result: object = kernel(states, seeds, empty, states, empty, 0.01, states)
        jvp: float = float(np.asarray(result).ravel()[0])
        expected: float = -(2.0 * states[0] + states[1]) if column == 0 else -states[0]
        assert abs(jvp - expected) <= 1.0e-12
