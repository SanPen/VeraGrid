# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# ==============================================================================
# Mathematical Verification Suite for VeraGrid Unified Solvers
# ==============================================================================

from typing import List, Tuple, Any

import numpy as np
import pytest

from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate

from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import BoundaryUpdateWrapper
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory


class GenericEmtProblem(EmtProblemTemplate):
    __slots__ = list()


# --- Boundary Condition Wrappers ---
class FreezeParameterWrapper(BoundaryUpdateWrapper):
    __slots__ = ['idx_k', 'threshold']

    def __init__(self, idx_k: int, threshold: float):
        self.idx_k: int = idx_k
        self.threshold: float = threshold

    def update(self, t: float, x: np.ndarray, params: np.ndarray) -> None:
        if t > self.threshold:
            params[self.idx_k] = 0.0
        else:
            pass


class SyncTimeWrapper(BoundaryUpdateWrapper):
    __slots__ = ['idx_t']

    def __init__(self, idx_t: int):
        self.idx_t: int = idx_t

    def update(self, t: float, x: np.ndarray, params: np.ndarray) -> None:
        params[self.idx_t] = t


# --- Unit Test Suite ---
def create_decay_system(k_val: float = 1.0) -> Tuple[Block, Var, Var]:
    x: Var = Var("x")
    k: Var = Var("k")
    block: Block = Block(
        name="DecayUnit",
        state_vars=list([x]),
        state_eqs=list([-k * x]),
        parameters=dict({k: Const(k_val)})
    )
    return block, x, k


SOLVERS_TO_TEST: List[Any] = list([JitAdSolver, StructuralVectorizedSolver])


def make_solver(
    solver_class: Any,
    block: Block,
    t_end: float,
    h: float,
    method: DynamicIntegrationMethod,
) -> Tuple[Any, GenericEmtProblem]:
    """Helper to construct a BaseProblem and initialize the chosen solver."""
    block.unify_blocks()
    problem: GenericEmtProblem = GenericEmtProblem(block, Var("t"))
    solver: Any = solver_class(problem, t0=0.0, t_end=t_end, h=h, method=method)
    return solver, problem


@pytest.mark.parametrize("solver_class", SOLVERS_TO_TEST, ids=lambda cls: cls.__name__)
def test_01_backward_euler_math(solver_class: Any) -> None:
    h: float = 0.1
    block, _, _ = create_decay_system(k_val=1.0)
    solver, prob = make_solver(solver_class, block, h, h, DynamicIntegrationMethod.DaeBackEuler)

    x0: np.ndarray = prob.get_x0()
    x0[0] = 1.0
    dx0: np.ndarray = np.zeros_like(x0, dtype=np.float64)
    dx0[0] = -1.0
    p0: np.ndarray = np.zeros(prob.get_variable_parameter_number(), dtype=np.float64)

    _, y, _ = solver.simulate(x0=x0, dx0=dx0, params0=p0)

    x_numeric: float = float(y[-1, 0])
    x_expected: float = 1.0 / (1.0 + h)
    assert x_numeric == pytest.approx(x_expected, abs=5e-8)


@pytest.mark.parametrize("solver_class", SOLVERS_TO_TEST, ids=lambda cls: cls.__name__)
def test_02_trapezoid_math(solver_class: Any) -> None:
    h: float = 0.1
    block, _, _ = create_decay_system(k_val=1.0)
    solver, prob = make_solver(solver_class, block, h, h, DynamicIntegrationMethod.DaeTrapezoidal)

    x0: np.ndarray = prob.get_x0()
    x0[0] = 1.0
    dx0: np.ndarray = np.zeros_like(x0, dtype=np.float64)
    dx0[0] = -1.0
    p0: np.ndarray = np.zeros(prob.get_variable_parameter_number(), dtype=np.float64)

    _, y, _ = solver.simulate(x0=x0, dx0=dx0, params0=p0)

    x_numeric: float = float(y[-1, 0])
    factor: float = (1.0 - h / 2.0) / (1.0 + h / 2.0)
    x_expected: float = 1.0 * factor
    assert x_numeric == pytest.approx(x_expected, abs=5e-8)


@pytest.mark.parametrize("solver_class", SOLVERS_TO_TEST, ids=lambda cls: cls.__name__)
def test_03_boundary_update_fn(solver_class: Any) -> None:
    block, _, k = create_decay_system(k_val=1.0)
    solver, prob = make_solver(solver_class, block, 1.0, 0.1, DynamicIntegrationMethod.DaeBackEuler)

    idx_k: int = prob.uid2idx_params.get(k.uid, 0)
    freeze_updater: FreezeParameterWrapper = FreezeParameterWrapper(idx_k=idx_k, threshold=0.5)

    x0: np.ndarray = prob.get_x0()
    x0[0] = 1.0
    dx0: np.ndarray = np.zeros_like(x0, dtype=np.float64)
    dx0[0] = -1.0
    p0: np.ndarray = np.zeros(prob.get_variable_parameter_number(), dtype=np.float64)

    _, y, _ = solver.simulate(x0=x0, dx0=dx0, params0=p0, boundary_updater=freeze_updater)

    y_06: float = float(y[6, 0])
    y_10: float = float(y[-1, 0])
    assert y_06 == pytest.approx(y_10, abs=5e-7)


@pytest.mark.parametrize("solver_class", SOLVERS_TO_TEST, ids=lambda cls: cls.__name__)
def test_04_convergence_order(solver_class: Any) -> None:
    block, _, _ = create_decay_system(k_val=1.0)
    t_target: float = 1.0
    exact_sol: float = float(np.exp(-1.0))

    solver_c, prob_c = make_solver(solver_class, block, t_target, 0.1, DynamicIntegrationMethod.DaeTrapezoidal)
    x0_c: np.ndarray = prob_c.get_x0()
    dx0_c: np.ndarray = np.zeros_like(x0_c, dtype=np.float64)
    x0_c[0] = 1.0
    dx0_c[0] = -1.0
    p0_c: np.ndarray = np.zeros(prob_c.get_variable_parameter_number(), dtype=np.float64)
    _, y_c, _ = solver_c.simulate(x0=x0_c, dx0=dx0_c, params0=p0_c)
    err_c: float = abs(float(y_c[-1, 0]) - exact_sol)

    solver_f, prob_f = make_solver(solver_class, block, t_target, 0.05, DynamicIntegrationMethod.DaeTrapezoidal)
    x0_f: np.ndarray = prob_f.get_x0()
    dx0_f: np.ndarray = np.zeros_like(x0_f, dtype=np.float64)
    x0_f[0] = 1.0
    dx0_f[0] = -1.0
    p0_f: np.ndarray = np.zeros(prob_f.get_variable_parameter_number(), dtype=np.float64)
    _, y_f, _ = solver_f.simulate(x0=x0_f, dx0=dx0_f, params0=p0_f)
    err_f: float = abs(float(y_f[-1, 0]) - exact_sol)

    ratio: float = err_c / err_f
    assert ratio > 3.8


@pytest.mark.parametrize("solver_class", SOLVERS_TO_TEST, ids=lambda cls: cls.__name__)
def test_05_stiff_system_stability(solver_class: Any) -> None:
    x: Var = Var("x")
    stiff_block: Block = Block(name="Stiff", state_vars=list([x]), state_eqs=list([(-1000) * x]), parameters=dict())

    solver, prob = make_solver(solver_class, stiff_block, 1.0, 0.1, DynamicIntegrationMethod.DaeBackEuler)
    x0: np.ndarray = prob.get_x0()
    x0[0] = 1.0
    dx0: np.ndarray = np.zeros_like(x0, dtype=np.float64)
    p0: np.ndarray = np.zeros(prob.get_variable_parameter_number(), dtype=np.float64)

    _, y, _ = solver.simulate(x0=x0, dx0=dx0, params0=p0)

    assert abs(float(y[-1, 0])) < 1e-2


@pytest.mark.parametrize("solver_class", SOLVERS_TO_TEST, ids=lambda cls: cls.__name__)
def test_06_nonlinear_jacobian(solver_class: Any) -> None:
    x: Var = Var("x")
    nl_block: Block = Block(name="NonLinear", state_vars=list([x]), state_eqs=list([x * x]), parameters=dict())

    solver, prob = make_solver(solver_class, nl_block, 0.5, 0.01, DynamicIntegrationMethod.DaeTrapezoidal)
    x0: np.ndarray = prob.get_x0()
    x0[0] = 1.0
    dx0: np.ndarray = np.ones_like(x0, dtype=np.float64)
    p0: np.ndarray = np.zeros(prob.get_variable_parameter_number(), dtype=np.float64)

    _, y, _ = solver.simulate(x0=x0, dx0=dx0, params0=p0)

    assert float(y[-1, 0]) == pytest.approx(2.0, abs=0.05)


@pytest.mark.parametrize("solver_class", SOLVERS_TO_TEST, ids=lambda cls: cls.__name__)
def test_07_energy_conservation(solver_class: Any) -> None:
    vf: VarFactory = VarFactory()
    x: Var = vf.add_var("pos")
    v: Var = vf.add_var("vel")
    dx: Var = vf.add_diff_var(name="d_pos", base_var=x)
    dv: Var = vf.add_diff_var(name="d_vel", base_var=v)
    osc_block: Block = Block(
        name="Oscillator",
        state_vars=list([x, v]),
        state_eqs=list([v, -x]),
        diff_vars=list([dx, dv]),
        parameters=dict(),
    )

    solver_trap, prob_trap = make_solver(solver_class, osc_block, 20.0, 0.1, DynamicIntegrationMethod.DaeTrapezoidal)
    x0: np.ndarray = prob_trap.get_x0()
    dx0: np.ndarray = np.zeros_like(x0, dtype=np.float64)
    x0[0] = 1.0
    dx0[1] = -1.0
    p0: np.ndarray = np.zeros(prob_trap.get_variable_parameter_number(), dtype=np.float64)

    _, y_trap, _ = solver_trap.simulate(x0=x0, dx0=dx0, params0=p0)
    amp_trap: float = float(np.max(np.abs(y_trap[-20:, 0])))
    assert amp_trap > 0.95

    solver_be, prob_be = make_solver(solver_class, osc_block, 20.0, 0.1, DynamicIntegrationMethod.DaeBackEuler)
    x0_be: np.ndarray = prob_be.get_x0()
    dx0_be: np.ndarray = np.zeros_like(x0_be, dtype=np.float64)
    x0_be[0] = 1.0
    dx0_be[1] = -1.0
    p0_be: np.ndarray = np.zeros(prob_be.get_variable_parameter_number(), dtype=np.float64)

    _, y_be, _ = solver_be.simulate(x0=x0_be, dx0=dx0_be, params0=p0_be)
    amp_be: float = float(np.max(np.abs(y_be[-20:, 0])))
    assert amp_be < 0.5


@pytest.mark.parametrize("solver_class", SOLVERS_TO_TEST, ids=lambda cls: cls.__name__)
def test_08_time_dependent_forcing(solver_class: Any) -> None:
    x: Var = Var("x")
    t_driver: Var = Var("t_driver")
    forcing_block: Block = Block(
        name="Forcing",
        state_vars=list([x]),
        state_eqs=list([t_driver]),
        event_dict=dict({t_driver: Const(0.0)}),
        parameters=dict(),
    )

    solver, prob = make_solver(solver_class, forcing_block, 2.0, 0.1, DynamicIntegrationMethod.DaeTrapezoidal)

    idx_t: int = prob.uid2idx_event_params.get(t_driver.uid, 0)
    sync_updater: SyncTimeWrapper = SyncTimeWrapper(idx_t=idx_t)

    x0: np.ndarray = prob.get_x0()
    dx0: np.ndarray = np.zeros_like(x0, dtype=np.float64)
    p0: np.ndarray = np.zeros(prob.get_variable_parameter_number(), dtype=np.float64)

    _, y, _ = solver.simulate(x0=x0, dx0=dx0, params0=p0, boundary_updater=sync_updater)

    expected: float = (2.0 ** 2) / 2.0
    assert float(y[-1, 0]) == pytest.approx(expected, abs=5e-3)
