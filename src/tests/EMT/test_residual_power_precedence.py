# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Residual code generators keep unary and negative-literal operands of '**' parenthesized."""

from __future__ import annotations

import ast
from collections.abc import Callable
from typing import Any, Dict, List, Tuple

import numpy as np
import numpy.typing as npt
import pytest

from tests.EMT.test_discretization_verify import make_solver
from tests.EMT.test_structural_compiled_solver import build_full_params
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver, evaluate_batched_residual
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.jit_compiler import (EquationCompiler, MatrixVectorizedVisitor, RuntimeParameterToPythonVisitor,
                                                        SymbolicToPythonVisitor, TrapezoidalMethod)
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Expr, UnOp, Var, _precedence, expression2numba


def _power_cases(x: Var, y: Var, a: Var, b: Var, c: Var) -> List[Tuple[str, Expr]]:
    """
    Build the '**' cases: unary and negative-literal operands (Python and numpy scalars) and unaffected controls.

    :return: Labelled expressions.
    """
    return list((
        ("(-x)**2", BinOp(UnOp("-", x), "**", Const(2.0))),
        ("(-x)**y", BinOp(UnOp("-", x), "**", y)),
        ("Const(-2)**y", BinOp(Const(-2.0), "**", y)),
        ("Const(-2)**Const(2)", BinOp(Const(-2.0), "**", Const(2.0))),
        ("y*(-x)**2", BinOp(y, "*", BinOp(UnOp("-", x), "**", Const(2.0)))),
        ("Const(np.float64(-2))**y", BinOp(Const(np.float64(-2.0)), "**", y)),
        ("Const(np.int64(-3))**Const(2)", BinOp(Const(np.int64(-3)), "**", Const(2.0))),
        ("folded(-np.float64(2))**y", BinOp(UnOp("-", Const(np.float64(2.0))).simplify(), "**", y)),
        ("(-x)**3", BinOp(UnOp("-", x), "**", Const(3.0))),
        ("x**Const(-2)", BinOp(x, "**", Const(-2.0))),
        ("-(x**2)", UnOp("-", BinOp(x, "**", Const(2.0)))),
        ("(a-b)**2", BinOp(BinOp(a, "-", b), "**", Const(2.0))),
        ("a**(b-c)", BinOp(a, "**", BinOp(b, "-", c))),
        ("(a**b)**c", BinOp(BinOp(a, "**", b), "**", c)),
        ("a**(b**c)", BinOp(a, "**", BinOp(b, "**", c))),
    ))


def test_negative_literal_precedence_is_decided_by_value() -> None:
    """_precedence treats Python and numpy negative scalars and -0.0 as unary, and non-negative scalars as atoms."""
    value: Any
    for value in (-2.0, -3, -0.0, np.float64(-2.0), np.float64(-0.0), np.int64(-3), np.float32(-1.5)):
        assert _precedence(Const(value)) == 25
    for value in (2.0, 0.0, np.float64(2.0), np.int64(3)):
        assert _precedence(Const(value)) == 100


def test_residual_visitors_and_compiler_emit_power_operands_correctly() -> None:
    """Every residual emitter is syntactically valid and EquationCompiler evaluates each '**' case exactly."""
    x: Var = Var("pp_x")
    y: Var = Var("pp_y")
    a: Var = Var("pp_a")
    b: Var = Var("pp_b")
    c: Var = Var("pp_c")
    variables: List[Var] = list((x, y, a, b, c))
    values: npt.NDArray[np.float64] = np.array((0.7, 2.0, 1.3, 0.4, 0.9))
    index: Dict[int, int] = dict()
    names: Dict[int, str] = dict()
    position: int
    variable: Var
    bindings: Dict[int, float] = dict()
    for position, variable in enumerate(variables):
        index[variable.uid] = position
        names[variable.uid] = f"states[{position}]"
        bindings[variable.uid] = float(values[position])
    cases: List[Tuple[str, Expr]] = _power_cases(x, y, a, b, c)
    label: str
    expr: Expr
    for label, expr in cases:
        codes: List[str] = list((SymbolicToPythonVisitor(index, dict(), TrapezoidalMethod()).visit(expr),
                                 MatrixVectorizedVisitor(index, dict(), TrapezoidalMethod(), index).visit(expr),
                                 RuntimeParameterToPythonVisitor(index, dict(), set()).visit(expr),
                                 expression2numba(expr, names)))
        code: str
        for code in codes:
            # The compiler below evaluates equivalent expressions; here only validate emitted Python syntax.
            ast.parse(code, mode='eval')
    compiler: EquationCompiler = EquationCompiler(variables, list(), list(), DynamicIntegrationMethod.DaeTrapezoidal)
    use_cse: bool
    for use_cse in (False, True):
        kernel: Callable[..., Any] = compiler.compile(list(expr for _, expr in cases), use_cse=use_cse)
        result: npt.NDArray[np.float64] = np.asarray(kernel(values, np.zeros(0), values, np.zeros(5), 0.01, values)).ravel()
        for (label, expr), value in zip(cases, result):
            assert float(value) == pytest.approx(float(expr.eval_uid(bindings)), rel=1e-12, abs=1e-12), label


def _power_block() -> Tuple[Block, Var, List[Var], List[Expr]]:
    """
    Build a decaying state x and algebraic rows y_i = f_i(x) whose f_i contain unary or negative-literal operands of '**'.

    :return: Block, state, algebraic variables and their exact expressions.
    """
    x: Var = Var("ppb_x")
    dx: Var = Var("ppb_dx", base_var=x)
    expressions: List[Expr] = list((
        BinOp(UnOp("-", x), "**", Const(2.0)),
        BinOp(x, "*", BinOp(UnOp("-", x), "**", Const(2.0))),
        BinOp(BinOp(Const(-2.0), "**", Const(2.0)), "*", x),
        BinOp(BinOp(Const(np.float64(-2.0)), "**", Const(2.0)), "*", x),
        BinOp(BinOp(UnOp("-", Const(np.float64(2.0))).simplify(), "**", Const(2.0)), "*", x),
        BinOp(UnOp("-", x), "**", Const(3.0)),
    ))
    algebraic: List[Var] = list()
    equations: List[Expr] = list()
    position: int
    expr: Expr
    for position, expr in enumerate(expressions):
        variable: Var = Var(f"ppb_y{position}")
        algebraic.append(variable)
        equations.append(variable - expr)
    block: Block = Block(name="PowerPrecedence", state_vars=list((x,)), diff_vars=list((dx,)), state_eqs=list((-x,)),
                         algebraic_vars=algebraic, algebraic_eqs=equations, parameters=dict())
    return block, x, algebraic, expressions


@pytest.mark.parametrize("solver_class", (JitSymbolicSolver, JitAdSolver, StructuralVectorizedSolver, StructuralCompiledSolver))
@pytest.mark.parametrize("method", (DynamicIntegrationMethod.DaeTrapezoidal, DynamicIntegrationMethod.DaeBackEuler, DynamicIntegrationMethod.DaeBDF2))
def test_every_solver_tracks_the_exact_power_rows(solver_class: type, method: DynamicIntegrationMethod) -> None:
    """Each EMT solver's algebraic trajectory equals the exact '**' expressions of its state at every step."""
    block: Block
    x: Var
    algebraic: List[Var]
    expressions: List[Expr]
    block, x, algebraic, expressions = _power_block()
    solver: Any
    problem: EmtProblemTemplate
    solver, problem = make_solver(solver_class, block, 0.05, 0.01, method, 1e-12, 0)
    x0: npt.NDArray[np.float64] = problem.get_x0()
    x0[0] = 0.7
    expr: Expr
    position: int
    for position, expr in enumerate(expressions):
        x0[1 + position] = float(expr.eval(ppb_x=0.7))
    dx0: npt.NDArray[np.float64] = np.zeros(len(problem.get_diff_vars()), dtype=np.float64)
    dx0[0] = -0.7
    params0: npt.NDArray[np.float64] = np.zeros(problem.get_variable_parameter_number(), dtype=np.float64)
    times: npt.NDArray[np.float64]
    values: npt.NDArray[np.float64]
    derivatives: npt.NDArray[np.float64]
    well: bool
    converged: bool
    times, values, derivatives, well, converged = solver.simulate(x0=x0, dx0=dx0, params0=params0)
    assert well and converged
    step: int
    for step in range(values.shape[0]):
        state: float = float(values[step, 0])
        for position, expr in enumerate(expressions):
            assert values[step, 1 + position] == pytest.approx(float(expr.eval(ppb_x=state)), rel=1e-8, abs=1e-10)


def test_symbolic_jacobian_of_power_rows_matches_central_differences() -> None:
    """JitSymbolicSolver's symbolic Jacobian of the '**' rows equals central differences of its own residual."""
    block: Block
    x: Var
    algebraic: List[Var]
    expressions: List[Expr]
    block, x, algebraic, expressions = _power_block()
    method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeTrapezoidal
    solver: JitSymbolicSolver
    problem: EmtProblemTemplate
    solver, problem = make_solver(JitSymbolicSolver, block, 0.02, 0.01, method, 1e-12, 0)
    x0: npt.NDArray[np.float64] = problem.get_x0()
    x0[0] = 0.7
    position: int
    expr: Expr
    for position, expr in enumerate(expressions):
        x0[1 + position] = float(expr.eval(ppb_x=0.7))
    dx0: npt.NDArray[np.float64] = np.zeros(len(problem.get_diff_vars()), dtype=np.float64)
    dx0[0] = -0.7
    params0: npt.NDArray[np.float64] = np.zeros(problem.get_variable_parameter_number(), dtype=np.float64)
    solver.simulate(x0=x0, dx0=dx0, params0=params0)
    evaluator: Any = next(iter(solver.jit_jacobian_symbolic.values()))
    kernels: List[Any] = solver.jit_kernels[method]
    params: npt.NDArray[np.float64] = build_full_params(problem)
    state: npt.NDArray[np.float64] = x0.copy()
    state[0] = 0.55
    previous: npt.NDArray[np.float64] = x0.copy()
    slope: npt.NDArray[np.float64] = dx0.copy()
    matrix: Any = evaluator.evaluate(state, params, previous, slope, 0.01, previous)
    analytic: npt.NDArray[np.float64] = matrix.toarray() if evaluator.use_sparse else np.asarray(matrix)
    numeric: npt.NDArray[np.float64] = np.zeros_like(analytic)
    residual: npt.NDArray[np.float64] = np.zeros(state.shape[0], dtype=np.float64)
    column: int
    for column in range(state.shape[0]):
        delta: float = 1.0e-7 * max(1.0, abs(float(state[column])))
        plus: npt.NDArray[np.float64] = state.copy()
        plus[column] += delta
        evaluate_batched_residual(kernels, plus, params, previous, slope, 0.01, previous, residual)
        upper: npt.NDArray[np.float64] = residual.copy()
        minus: npt.NDArray[np.float64] = state.copy()
        minus[column] -= delta
        evaluate_batched_residual(kernels, minus, params, previous, slope, 0.01, previous, residual)
        numeric[:, column] = (upper - residual) / (2.0 * delta)
    np.testing.assert_allclose(analytic, numeric, rtol=1e-6, atol=1e-7)
