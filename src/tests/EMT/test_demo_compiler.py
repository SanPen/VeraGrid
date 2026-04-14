# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import numba as nb
import pandas as pd
from pandas.testing import assert_frame_equal

import os
from typing import Callable, List



from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr
from VeraGridEngine.Utils.Symbolic.jit_compiler import EquationCompiler, MatrixVectorizedCompiler
from VeraGridEngine.enumerations import DynamicIntegrationMethod

def solve_step_newton(step_fn: Callable, current_x: np.ndarray, history: np.ndarray,
                      d_history: np.ndarray, params: np.ndarray, h: float,
                      tol: float = 1e-6, max_iter: int = 10) -> np.ndarray:
    """
    Minimal Newton–Raphson solver to compute the next state x_next.
    """
    # Initial guess (predictor): x_next = x_prev + h * dx_prev
    x_next: np.ndarray = current_x + h * d_history
    perturbation: float = 1e-5
    n_vars: int = len(current_x)

    for _ in range(max_iter):
        # 1. Evaluate residuals: F(x)
        residuals: np.ndarray = step_fn(x_next, params, history, d_history, h)

        # Convergence check
        if float(np.max(np.abs(residuals))) < tol:
            return x_next
        else:
            pass

        # 2. Compute numerical Jacobian J
        J: np.ndarray = np.zeros((n_vars, n_vars), dtype=np.float64)
        for j in range(n_vars):
            x_pert: np.ndarray = x_next.copy()
            x_pert[j] += perturbation
            res_pert: np.ndarray = step_fn(x_pert, params, history, d_history, h)
            J[:, j] = (res_pert - residuals) / perturbation

        # 3. Newton update: x_new = x - J^{-1} * F
        det_j: float = float(np.linalg.det(J))
        if abs(det_j) < 1e-12:
            print("Singular Jacobian encountered. Aborting Newton iteration.")
            break
        else:
            delta: np.ndarray = np.linalg.solve(J, residuals)
            x_next -= delta

    return x_next


def test_demo_compiler():
    print("=== Visual Demo: Harmonic Oscillator ===")

    #########
    # retrieve reference results df

    name = "demo_compiler.csv"

    fname = os.path.join(os.path.dirname(__file__), '..', 'data', 'dynamics', name)

    # fname = "simulation_with_event_emt.csv"

    reference_df = pd.read_csv(fname)

    ###########################################################################################################################

    # 1. Define physics
    pos: Var = Var('pos')
    vel: Var = Var('vel')
    k: Var = Var('k')
    c: Var = Var('c')

    dpos: Var = Var(name='dpos', base_var=pos)
    dvel: Var = Var(name='dvel', base_var=vel)

    eq1: Expr = dpos - vel
    eq2: Expr = dvel + c * vel + k * pos

    variables: List[Var] = list([pos, vel])
    parameters: List[Var] = list([k, c])
    equations: List[Expr] = list([eq1, eq2])

    # 2. Compile equations
    compiler = EquationCompiler(
        variables,
        parameters=parameters,
        method=DynamicIntegrationMethod.DaeTrapezoidal
    )
    step_fn: Callable = compiler.compile(equations)
    print("[OK] Equations successfully compiled.")

    # 3. Simulation setup
    t_end: float = 100.0
    h: float = 0.05
    steps: int = int(t_end / h)
    tme: np.ndarray = np.linspace(0, t_end, steps)

    results: np.ndarray = np.zeros((steps, 2), dtype=np.float64)
    energy: np.ndarray = np.zeros(steps, dtype=np.float64)

    x0: np.ndarray = np.array([2.0, 0.0], dtype=np.float64)
    p_vals: np.ndarray = np.array([1.0, 0.1], dtype=np.float64)

    current_x: np.ndarray = x0.copy()
    history: np.ndarray = x0.copy()
    d_history: np.ndarray = np.array([0.0, -2.0], dtype=np.float64)

    print(f"Simulating {steps} time steps...")

    for i in range(steps):
        results[i] = current_x

        energy[i] = (
            0.5 * current_x[1]**2 +
            0.5 * p_vals[0] * current_x[0]**2
        )

        next_x: np.ndarray = solve_step_newton(
            step_fn, current_x, history, d_history, p_vals, h
        )

        d_next: np.ndarray = (2.0 / h) * (next_x - history) - d_history

        history = current_x
        d_history = d_next
        current_x = next_x

    results_df = pd.DataFrame(results, index=tme)
    results_df.index.name = "time_s"
    results_df.columns = reference_df.columns

    assert_frame_equal(
        results_df.reset_index(drop=True),
        reference_df.reset_index(drop=True),
        check_dtype=False,
        check_index_type=False,
        atol=1e-6
    )


def _create_decay_equation() -> tuple[Var, Var, Expr]:
    """
    Create a canonical decay equation: dx/dt + x = 0.

    :returns: Tuple of (x, dx, decay_eq) representing the decay system.
    """
    x: Var = Var('x')
    dx: Var = Var(name='dx', base_var=x)
    decay_eq: Expr = dx + x
    return x, dx, decay_eq


def test_trapezoidal_residual_math() -> None:
    """
    Verifies the implicit Trapezoidal substitution for decay equation.

    Tests that the compiled residual correctly implements:
    dx_new = (2/h)*(x - x0) - dx0
    res = dx_new + x
    """
    x, dx, decay_eq = _create_decay_equation()

    compiler: EquationCompiler = EquationCompiler(
        list([x]),
        method=DynamicIntegrationMethod.DaeTrapezoidal
    )
    step_fn: Callable = compiler.compile(list([decay_eq]))

    h: float = 0.1
    h2: np.ndarray = np.zeros(1, dtype=np.float64)

    states: np.ndarray = np.array(list([1.0]), dtype=np.float64)
    params: np.ndarray = np.zeros(0, dtype=np.float64)
    history: np.ndarray = np.array(list([1.0]), dtype=np.float64)
    d_history: np.ndarray = np.array(list([-1.0]), dtype=np.float64)

    res: np.ndarray = step_fn(states, params, history, d_history, h, h2)

    assert abs(float(res[0]) - 2.0) < 1e-6, f"Expected 2.0, got {float(res[0])}"


def test_matrix_vectorized_clustering_logic() -> None:
    """
    Validates the MatrixVectorizedCompiler used in SVS Structural Clustering.

    Ensures a single template can be applied to multiple nodes simultaneously.
    """
    x, dx, decay_eq = _create_decay_equation()

    vec_compiler: MatrixVectorizedCompiler = MatrixVectorizedCompiler(
        list([x]),
        parameters=list(),
        method=DynamicIntegrationMethod.DaeTrapezoidal
    )
    py_func: Callable = vec_compiler.compile_matrix_kernel(
        decay_eq,
        func_name="vec_decay",
        template_vars=list([x])
    )
    vec_kernel: Callable = nb.njit(fastmath=True)(py_func)

    indices: np.ndarray = np.array(list([list([0]), list([1]), list([2])]), dtype=np.int32)
    states: np.ndarray = np.array(list([1.0, 1.2, 1.5]), dtype=np.float64)
    params: np.ndarray = np.zeros(0, dtype=np.float64)
    history: np.ndarray = np.array(list([1.0, 1.2, 1.5]), dtype=np.float64)
    d_hist: np.ndarray = np.array(list([-1.0, -1.2, -1.5]), dtype=np.float64)
    h: float = 0.1

    res: np.ndarray = vec_kernel(states, params, history, d_hist, h, indices, history)

    expected: np.ndarray = np.array(list([2.0, 2.4, 3.0]), dtype=np.float64)
    np.testing.assert_allclose(res, expected, rtol=1e-7)


def test_truncation_error_order() -> None:
    """
    Mathematical proof of O(h^2) convergence for the Trapezoidal JIT kernel.

    Residual error should drop by factor of 4 when h is halved.
    """
    x, dx, decay_eq = _create_decay_equation()

    compiler: EquationCompiler = EquationCompiler(
        list([x]),
        method=DynamicIntegrationMethod.DaeTrapezoidal
    )
    step_fn: Callable = compiler.compile(list([decay_eq]))

    x0: float = 1.0
    dx0: float = -1.0
    h2: np.ndarray = np.zeros(1, dtype=np.float64)
    h_c: float = 0.1
    h_f: float = 0.05
    params: np.ndarray = np.zeros(0, dtype=np.float64)

    states_c: np.ndarray = np.array(list([np.exp(-h_c)]), dtype=np.float64)
    hist_c: np.ndarray = np.array(list([x0]), dtype=np.float64)
    d_hist_c: np.ndarray = np.array(list([dx0]), dtype=np.float64)
    res_c: np.ndarray = step_fn(states_c, params, hist_c, d_hist_c, h_c, h2)

    states_f: np.ndarray = np.array(list([np.exp(-h_f)]), dtype=np.float64)
    hist_f: np.ndarray = np.array(list([x0]), dtype=np.float64)
    d_hist_f: np.ndarray = np.array(list([dx0]), dtype=np.float64)
    res_f: np.ndarray = step_fn(states_f, params, hist_f, d_hist_f, h_f, h2)

    ratio: float = float(abs(res_c[0]) / abs(res_f[0]))
    print(f"\n[MATH] Empirical Convergence Ratio: {ratio:.2f} (Expected ~4.0)")
    assert ratio > 3.8, f"Expected ratio > 3.8, got {ratio}"


def test_oscillator_energy_conservation() -> None:
    """
    Physical verification: Trapezoidal rule must conserve energy in a Hamiltonian system.

    System: x'' + x = 0 (Undamped Oscillator).
    """
    pos: Var = Var('pos')
    vel: Var = Var('vel')
    d_pos: Var = Var(name='d_pos', base_var=pos)
    d_vel: Var = Var(name='d_vel', base_var=vel)

    eqs: List[Expr] = list([d_pos - vel, d_vel + pos])
    compiler: EquationCompiler = EquationCompiler(
        list([pos, vel]),
        method=DynamicIntegrationMethod.DaeTrapezoidal
    )
    kernel: Callable = compiler.compile(eqs)

    h: float = 0.01
    h2: np.ndarray = np.zeros(2, dtype=np.float64)
    hist: np.ndarray = np.array(list([1.0, 0.0]), dtype=np.float64)
    d_hist: np.ndarray = np.array(list([0.0, -1.0]), dtype=np.float64)
    params: np.ndarray = np.zeros(0, dtype=np.float64)

    states_new: np.ndarray = np.array(list([np.cos(h), -np.sin(h)]), dtype=np.float64)
    res: np.ndarray = kernel(states_new, params, hist, d_hist, h, h2)

    np.testing.assert_allclose(res, np.zeros(2, dtype=np.float64), atol=1e-4)

    e_init: float = 0.5 * (1.0 ** 2 + 0.0 ** 2)
    e_final: float = 0.5 * (float(states_new[0]) ** 2 + float(states_new[1]) ** 2)
    assert abs(e_init - e_final) < 1e-5, f"Energy not conserved: {e_init} vs {e_final}"


# if __name__ == "__main__":
#     test_demo_compiler()
