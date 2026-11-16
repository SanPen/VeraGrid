# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""The AD and symbolic derivatives of u**v stay exact and finite at negative and zero bases."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any, Dict, List, Tuple

import numpy as np
import numpy.typing as npt
import pytest
from numba import njit

from tests.EMT.test_discretization_verify import make_solver
from tests.EMT.test_structural_compiled_solver import build_full_params
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver, evaluate_batched_residual
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver, evaluate_batched_residual as evaluate_ad_residual
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import (
    StructuralVectorizedSolver,
    build_residual_evaluator,
    evaluate_vectorized_residual,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicJacobian
from VeraGridEngine.Utils.Symbolic.jit_compiler import EagerEquationCompiler, EquationCompiler
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Expr, UnOp, Var


def _fixed_values() -> Tuple[float, float, float]:
    """
    Return the fixed evaluation values: the exponent parameter p, the exponent unknown y and the third unknown z.

    :return: Values of p, y and z.
    """
    return 2.0, 2.0, 0.7


def _power_partials(x: float, y: float) -> Tuple[float, float | None]:
    """
    Return the partials of x**y, the y partial only where it is defined (x > 0).

    :param x: Base value.
    :param y: Exponent value.
    :return: Partials with respect to x and y.
    """
    return y * x ** (y - 1.0), ((x ** y) * math.log(x)) if x > 0.0 else None


def _exact_partials(label: str, x: float) -> Tuple[float | None, float | None, float | None]:
    """
    Return the exact partials of a case with respect to x, y and z, or None where a partial is not tested.

    :param label: Case label.
    :param x: Base value (y and z are fixed).
    :return: Partials with respect to x, y and z.
    """
    exponent: float
    y: float
    z: float
    exponent, y, z = _fixed_values()
    dx: float
    dy: float | None
    dx, dy = _power_partials(x, y)
    value: float = x ** y
    result: Tuple[float | None, float | None, float | None]
    if label == "x**p":
        result = (exponent * x ** (exponent - 1.0), 0.0, 0.0)
    elif label == "x**(-1)":
        result = ((-1.0 / (x * x)) if x != 0.0 else None, 0.0, 0.0)
    elif label == "x**(1.5*2)":
        result = (3.0 * x * x, 0.0, 0.0)
    elif label == "x**0":
        result = (0.0, 0.0, 0.0)
    elif label == "2**y":
        result = (0.0, (2.0 ** y) * math.log(2.0), 0.0)
    elif label == "x**y":
        result = (dx, dy, 0.0)
    elif label == "z-x**y":
        result = (-dx, (-dy) if dy is not None else None, 1.0)
    elif label == "-(x**y)":
        result = (-dx, (-dy) if dy is not None else None, 0.0)
    elif label == "z*x**y":
        result = (z * dx, (z * dy) if dy is not None else None, value)
    elif label == "(x**y)/z":
        result = (dx / z, (dy / z) if dy is not None else None, -value / (z * z))
    elif label == "(z*z+1)**z":
        base: float = z * z + 1.0
        result = (0.0, 0.0, (base ** z) * (math.log(base) + 2.0 * z * z / base))
    else:
        raise ValueError(label)
    return result


def _power_cases(x: Var, y: Var, z: Var, p: Var) -> List[Tuple[str, Expr]]:
    """
    Build '**' cases with parameter, unary, constant-expression, zero and unknown exponents, and both partials under
    '-', unary '-', '*' and '/'.

    :param x: Base unknown.
    :param y: Exponent unknown.
    :param z: Third unknown.
    :param p: Exponent parameter.
    :return: Labelled expressions.
    """
    power: Expr = BinOp(x, "**", y)
    return list((
        ("x**p", BinOp(x, "**", p)),
        ("x**(-1)", BinOp(x, "**", UnOp("-", Const(1.0)))),
        ("x**(1.5*2)", BinOp(x, "**", BinOp(Const(1.5), "*", Const(2.0)))),
        ("x**0", BinOp(x, "**", Const(0.0))),
        ("2**y", BinOp(Const(2.0), "**", y)),
        ("x**y", power),
        ("z-x**y", BinOp(z, "-", power)),
        ("-(x**y)", UnOp("-", power)),
        ("z*x**y", BinOp(z, "*", power)),
        ("(x**y)/z", BinOp(power, "/", z)),
        ("(z*z+1)**z", BinOp(BinOp(BinOp(z, "*", z), "+", Const(1.0)), "**", z)),
    ))


def _check_jvp(jvp: npt.NDArray[np.float64], cases: List[Tuple[str, Expr]], x_value: float, column: int, kernel_label: str) -> None:
    """
    Compare one Jacobian-vector product against the exact partials of every case.

    :param jvp: Product for the unit seed of column.
    :param cases: Labelled expressions in kernel order.
    :param x_value: Base value.
    :param column: Seeded unknown (0 x, 1 y, 2 z).
    :param kernel_label: Kernel description for the assertion message.
    :return: None.
    """
    position: int
    case: Tuple[str, Expr]
    for position, case in enumerate(cases):
        label: str = case[0]
        exact: float | None = _exact_partials(label, x_value)[column]
        if exact is not None:
            assert float(jvp[position]) == pytest.approx(exact, rel=1e-12, abs=1e-12), (kernel_label, label, x_value, column)
        else:
            pass


def test_ad_kernels_give_exact_power_partials_at_negative_and_zero_bases() -> None:
    """
    The AD kernels give the exact partials of u**v: EagerEquationCompiler compiled with numba fastmath as the solvers
    compile it, and EquationCompiler, with run-time seeds (CSE on and off) and active indices.

    :return: None.
    """
    exponent: float
    y_value: float
    z_value: float
    exponent, y_value, z_value = _fixed_values()
    x: Var = Var("adp_x")
    y: Var = Var("adp_y")
    z: Var = Var("adp_z")
    p: Var = Var("adp_p")
    cases: List[Tuple[str, Expr]] = _power_cases(x, y, z, p)
    equations: List[Expr] = list(expr for _, expr in cases)
    params: npt.NDArray[np.float64] = np.array((exponent,))
    zeros: npt.NDArray[np.float64] = np.zeros(3)
    method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeTrapezoidal
    eager: EagerEquationCompiler = EagerEquationCompiler(variables=list((x, y, z)), parameters=list((p,)), method=method)
    compiler: EquationCompiler = EquationCompiler(list((x, y, z)), list((p,)), list(), method)
    eager_kernels: List[Tuple[str, Callable[..., Any]]] = list()
    python_kernels: List[Tuple[str, Callable[..., Any], int | None]] = list()
    use_cse: bool
    for use_cse in (False, True):
        python_function: Callable[..., Any]
        signature: object
        python_function, signature = eager.compile_ad_kernel(equations, func_name="power_ad", use_cse=use_cse, active_indices=None)
        eager_kernels.append((f"eager cse={use_cse}", njit(signature, cache=False, fastmath=True)(python_function)))
        python_kernels.append((f"python cse={use_cse}", compiler.compile_ad_kernel(equations, use_cse=use_cse), None))
    column: int
    for column in range(3):
        python_kernels.append((f"python active={column}", compiler.compile_ad_kernel(equations, use_cse=False, active_indices=set((column,))), column))
    x_value: float
    for x_value in (-0.5, 0.0, 0.5):
        states: npt.NDArray[np.float64] = np.array((x_value, y_value, z_value))
        for column in range(3):
            seeds: npt.NDArray[np.float64] = np.zeros(3)
            seeds[column] = 1.0
            kernel_label: str
            kernel: Callable[..., Any]
            for kernel_label, kernel in eager_kernels:
                out: npt.NDArray[np.float64] = np.zeros(len(equations))
                kernel(states, seeds, params, states.copy(), zeros, 0.01, out, states.copy())
                _check_jvp(out, cases, x_value, column, kernel_label)
            active: int | None
            for kernel_label, kernel, active in python_kernels:
                if active is None or active == column:
                    jvp: npt.NDArray[np.float64] = np.asarray(kernel(states, seeds, params, states, zeros, 0.01, states)).ravel()
                    _check_jvp(jvp, cases, x_value, column, kernel_label)
                else:
                    pass


def test_symbolic_power_partials_are_exact_at_negative_and_zero_bases() -> None:
    """
    Expr.diff gives the exact partials of u**v at negative and zero bases.

    :return: None.
    """
    exponent: float
    y_value: float
    z_value: float
    exponent, y_value, z_value = _fixed_values()
    x: Var = Var("sdp_x")
    y: Var = Var("sdp_y")
    z: Var = Var("sdp_z")
    p: Var = Var("sdp_p")
    cases: List[Tuple[str, Expr]] = _power_cases(x, y, z, p)
    x_value: float
    for x_value in (-0.5, 0.0, 0.5):
        bindings: Dict[int, float] = dict(((x.uid, x_value), (y.uid, y_value), (z.uid, z_value), (p.uid, exponent)))
        label: str
        expr: Expr
        for label, expr in cases:
            column: int
            variable: Var
            for column, variable in enumerate((x, y, z)):
                exact: float | None = _exact_partials(label, x_value)[column]
                if exact is not None:
                    value: float = float(expr.diff(variable).eval_uid(bindings))
                    assert value == pytest.approx(exact, rel=1e-12, abs=1e-12), (label, x_value, column)
                else:
                    pass



@pytest.mark.parametrize("use_jit", (True, False))
def test_symbolic_jacobian_gives_exact_power_partials(use_jit: bool) -> None:
    """
    SymbolicJacobian, compiled by numba or run as Python, gives the exact partials of u**v: exponent-independent cases
    at negative, zero and positive bases, and every case at a positive base.

    :param use_jit: Whether the Jacobian is compiled by numba.
    :return: None.
    """
    exponent: float
    y_value: float
    z_value: float
    exponent, y_value, z_value = _fixed_values()
    x: Var = Var("sjp_x")
    y: Var = Var("sjp_y")
    z: Var = Var("sjp_z")
    p: Var = Var("sjp_p")
    cases: List[Tuple[str, Expr]] = _power_cases(x, y, z, p)
    names: Dict[int, str] = dict(((x.uid, "values[0]"), (y.uid, "values[1]"), (z.uid, "values[2]"), (p.uid, "params[0]")))
    aliases: Dict[int, str] = dict(((x.uid, "x0"), (y.uid, "y0"), (z.uid, "z0"), (p.uid, "p0")))
    defined_everywhere: List[Tuple[str, Expr]] = list(case for case in cases if case[0] in ("x**p", "x**(1.5*2)", "x**0", "(z*z+1)**z"))
    params: npt.NDArray[np.float64] = np.array((exponent,))
    empty: npt.NDArray[np.float64] = np.zeros(0)
    selection: List[Tuple[str, Expr]]
    x_values: Tuple[float, ...]
    for selection, x_values in ((defined_everywhere, (-0.5, 0.0, 0.5)), (cases, (0.5,))):
        jacobian: SymbolicJacobian = SymbolicJacobian(list(expr for _, expr in selection), list((x, y, z)), dict(names), dict(aliases),
                                                      "values", "diff", "events", "params", use_jit=use_jit)
        x_value: float
        for x_value in x_values:
            matrix: npt.NDArray[np.float64] = jacobian(np.array((x_value, y_value, z_value)), empty, empty, params, 0.01).toarray()
            row: int
            case: Tuple[str, Expr]
            for row, case in enumerate(selection):
                label: str = case[0]
                column: int
                for column in range(3):
                    exact: float | None = _exact_partials(label, x_value)[column]
                    if exact is not None:
                        assert float(matrix[row, column]) == pytest.approx(exact, rel=1e-12, abs=1e-12), (use_jit, label, x_value, column)
                    else:
                        pass


def _power_block() -> Tuple[Block, List[Var]]:
    """
    Build a decaying state x and algebraic rows with parameter, constant-expression, zero and unknown exponents.

    Rows: y0 = x**p, y1 = x**(1.5*2), y2 = x**0, y3 = (x*x + 1)**x (both partials in one column), y4 = x**w and
    w = 2 (the exponent partial of x**w is undefined for x <= 0).

    :return: Block and its unknowns in solver order (state first).
    """
    exponent: float = _fixed_values()[0]
    x: Var = Var("pdb_x")
    dx: Var = Var("pdb_dx", base_var=x)
    p: Var = Var("pdb_p")
    w: Var = Var("pdb_w")
    expressions: List[Expr] = list((
        BinOp(x, "**", p),
        BinOp(x, "**", BinOp(Const(1.5), "*", Const(2.0))),
        BinOp(x, "**", Const(0.0)),
        BinOp(BinOp(BinOp(x, "*", x), "+", Const(1.0)), "**", x),
        BinOp(x, "**", w),
    ))
    algebraic: List[Var] = list()
    equations: List[Expr] = list()
    position: int
    expr: Expr
    for position, expr in enumerate(expressions):
        variable: Var = Var(f"pdb_y{position}")
        algebraic.append(variable)
        equations.append(variable - expr)
    algebraic.append(w)
    equations.append(w - Const(exponent))
    block: Block = Block(name="PowerDerivative", state_vars=list((x,)), diff_vars=list((dx,)), state_eqs=list((-x,)),
                         algebraic_vars=algebraic, algebraic_eqs=equations, parameters=dict(((p, Const(exponent)),)))
    return block, list((x,)) + algebraic


def _jacobian(solver: Any, method: DynamicIntegrationMethod, state: npt.NDArray[np.float64], params: npt.NDArray[np.float64],
              previous: npt.NDArray[np.float64], slope: npt.NDArray[np.float64], h: float) -> npt.NDArray[np.float64]:
    """
    Return a solver's dense Jacobian at a point.

    :param solver: EMT solver.
    :param method: Integration method.
    :param state: Evaluation point.
    :param params: Full parameter vector.
    :param previous: Previous unknowns (also used two steps back).
    :param slope: Derivative history of the states.
    :param h: Step size.
    :return: Dense Jacobian.
    """
    analytic: npt.NDArray[np.float64]
    if isinstance(solver, JitSymbolicSolver):
        solver.build_jit_kernel(method)
        solver._build_jit_symbolic_hybrid(method, False)
        analytic = np.asarray(solver.jit_jacobian_symbolic[f"{method}_False"].evaluate(state, params, previous, slope, h, previous)).copy()
    elif isinstance(solver, JitAdSolver):
        solver.build_jit_ad(method=method)
        analytic = solver.jit_jacobian_ad[method](state, params, previous, slope, h, previous).toarray().copy()
    elif isinstance(solver, StructuralVectorizedSolver):
        solver.auto_detect_vectorization(method)
        analytic = solver.vec_jacobian(state, params, previous, slope, h, previous).toarray().copy()
    else:
        solver._build_vectorized_backend(method)
        analytic = solver._jacobian_evaluator.evaluate(state, params, previous, slope, h, previous).toarray().copy()
    return analytic


def _residual(solver: Any, method: DynamicIntegrationMethod, state: npt.NDArray[np.float64], params: npt.NDArray[np.float64],
              previous: npt.NDArray[np.float64], slope: npt.NDArray[np.float64], h: float) -> npt.NDArray[np.float64]:
    """
    Return a solver's own residual at a point.

    :param solver: EMT solver whose kernels are already built by _jacobian.
    :param method: Integration method.
    :param state: Evaluation point.
    :param params: Full parameter vector.
    :param previous: Previous unknowns (also used two steps back).
    :param slope: Derivative history of the states.
    :param h: Step size.
    :return: Residual vector.
    """
    residual: npt.NDArray[np.float64] = np.zeros(state.shape[0], dtype=np.float64)
    if isinstance(solver, JitSymbolicSolver):
        evaluate_batched_residual(solver.jit_kernels[method], state, params, previous, slope, h, previous, residual)
    elif isinstance(solver, JitAdSolver):
        evaluate_ad_residual(solver.jit_kernels_ad[method], state, params, previous, slope, h, previous, residual)
    elif isinstance(solver, StructuralVectorizedSolver):
        evaluate_vectorized_residual(build_residual_evaluator(solver.fused_residual, solver.vec_flat_args), state, params, previous, slope, h,
                                     previous, residual)
    else:
        solver._residual_assembler.evaluate(state, params, previous, slope, h, previous, residual)
    return residual


@pytest.mark.parametrize("solver_class", (JitSymbolicSolver, JitAdSolver, StructuralVectorizedSolver, StructuralCompiledSolver))
@pytest.mark.parametrize("method", (DynamicIntegrationMethod.DaeTrapezoidal, DynamicIntegrationMethod.DaeBackEuler, DynamicIntegrationMethod.DaeBDF2))
def test_power_jacobian_is_finite_and_exact_at_negative_and_zero_bases(solver_class: type, method: DynamicIntegrationMethod) -> None:
    """
    Each EMT solver's Jacobian of the power rows is finite and equals central differences of its own residual, except
    the undefined exponent partial of x**w at x <= 0.

    :param solver_class: EMT solver class.
    :param method: Integration method.
    :return: None.
    """
    exponent: float = _fixed_values()[0]
    block: Block
    unknowns: List[Var]
    block, unknowns = _power_block()
    solver: Any
    problem: EmtProblemTemplate
    solver, problem = make_solver(solver_class, block, 0.02, 0.01, method, 1e-10, 0)
    params: npt.NDArray[np.float64] = build_full_params(problem)
    slope: npt.NDArray[np.float64] = np.full(len(problem.get_diff_vars()), 0.3)
    n: int = len(unknowns)
    undefined: npt.NDArray[np.bool_] = np.zeros((n, n), dtype=np.bool_)
    undefined[n - 2, n - 1] = True
    x_value: float
    for x_value in (-0.5, 0.0):
        state: npt.NDArray[np.float64] = np.linspace(0.4, 1.2, n)
        state[0] = x_value
        state[n - 1] = exponent
        previous: npt.NDArray[np.float64] = state - 0.01
        analytic: npt.NDArray[np.float64] = _jacobian(solver, method, state, params, previous, slope, 0.01)
        numeric: npt.NDArray[np.float64] = np.zeros_like(analytic)
        column: int
        for column in range(n):
            step: float = 1.0e-6 * max(1.0, abs(float(state[column])))
            plus: npt.NDArray[np.float64] = state.copy()
            plus[column] += step
            minus: npt.NDArray[np.float64] = state.copy()
            minus[column] -= step
            numeric[:, column] = (_residual(solver, method, plus, params, previous, slope, 0.01)
                                  - _residual(solver, method, minus, params, previous, slope, 0.01)) / (2.0 * step)
        assert bool(np.all(np.isfinite(analytic[~undefined]))), (x_value, analytic)
        np.testing.assert_allclose(analytic[~undefined], numeric[~undefined], rtol=1e-6, atol=1e-8)
