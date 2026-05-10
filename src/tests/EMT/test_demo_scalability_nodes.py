# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import time
from typing import Any
from typing import Dict
from unittest.mock import patch

import numpy as np
import pytest
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DynamicIntegrationMethod


class GenericEmtProblem(EmtProblemTemplate):
    """
    Minimal EMT problem used by the local scalability benchmark tests.

    :return: None.
    """

    __slots__ = list()


class InitialConditionGetter:
    """
    Copy-returning wrapper used to preserve defensive `get_x0` semantics.

    :param x0: Stored initial-condition vector.
    """

    __slots__ = ["_x0"]

    def __init__(self, x0: np.ndarray) -> None:
        """
        Store the initial-condition vector.

        :param x0: Stored initial-condition vector.
        :return: None.
        """
        self._x0 = x0

    def __call__(self) -> np.ndarray:
        """
        Return a defensive copy of the stored vector.

        :return: Initial-condition copy.
        """
        return self._x0.copy()


class FakeAdSolver:
    """
    Test double for the AD benchmark path.

    :param problem: EMT problem.
    :param t0: Initial time.
    :param t_end: Final time.
    :param h: Time step.
    :param method: Integration method.
    :param verbose: Verbosity flag.
    """

    __slots__ = ["problem", "t0", "t_end", "h", "method", "verbose", "build_calls", "simulate_calls"]
    instances: list["FakeAdSolver"] = list()

    def __init__(self, problem: Any, t0: float, t_end: float, h: float, method: Any, verbose: bool) -> None:
        self.problem = problem
        self.t0 = t0
        self.t_end = t_end
        self.h = h
        self.method = method
        self.verbose = verbose
        self.build_calls = 0
        self.simulate_calls = 0
        type(self).instances.append(self)

    def build_jit_ad(self) -> None:
        """
        Record the AD build step.

        :return: None.
        """
        self.build_calls += 1

    def simulate(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Return a warm-up trace followed by a measured trace.

        :return: Time, state, and derivative arrays.
        """
        y_arr: np.ndarray

        self.simulate_calls += 1
        if self.simulate_calls == 1:
            y_arr = np.array([[9.0, -9.0]], dtype=np.float64)
        else:
            y_arr = np.array([[1.0, -2.0], [3.0, -4.0]], dtype=np.float64)

        return np.array([0.0], dtype=np.float64), y_arr, np.zeros_like(y_arr)


class FakeVectorizedSolver:
    """
    Test double for the vectorized benchmark path.

    :param problem: EMT problem.
    :param t0: Initial time.
    :param t_end: Final time.
    :param h: Time step.
    :param method: Integration method.
    :param verbose: Verbosity flag.
    """

    __slots__ = ["problem", "t0", "t_end", "h", "method", "verbose", "auto_detect_calls", "simulate_calls", "last_pure_sim_time"]
    instances: list["FakeVectorizedSolver"] = list()

    def __init__(self, problem: Any, t0: float, t_end: float, h: float, method: Any, verbose: bool) -> None:
        self.problem = problem
        self.t0 = t0
        self.t_end = t_end
        self.h = h
        self.method = method
        self.verbose = verbose
        self.auto_detect_calls = list()
        self.simulate_calls = 0
        self.last_pure_sim_time = 0.125
        type(self).instances.append(self)

    def auto_detect_vectorization(self, method: Any) -> None:
        """
        Record the method passed to vectorization auto-detection.

        :param method: Integration method.
        :return: None.
        """
        self.auto_detect_calls.append(method)

    def simulate(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Return a warm-up trace followed by a measured trace.

        :return: Time, state, and derivative arrays.
        """
        y_arr: np.ndarray

        self.simulate_calls += 1
        if self.simulate_calls == 1:
            y_arr = np.array([[100.0]], dtype=np.float64)
        else:
            y_arr = np.array([[-2.0, 6.0], [4.0, -8.0]], dtype=np.float64)

        return np.array([0.0], dtype=np.float64), y_arr, np.zeros_like(y_arr)


class BenchmarkCallRecorder:
    """
    Recorder used to validate the fixed experiment matrix in `main()`.

    :return: None.
    """

    __slots__ = ["run_calls", "summaries"]

    def __init__(self) -> None:
        """
        Initialize the stored call collections.

        :return: None.
        """
        self.run_calls: list[dict[str, Any]] = list()
        self.summaries: list[dict[str, Any]] = list()

    def run_backend(self, label: str, n_nodes: int, vectorized: bool, t_end: float, h: float, verbose: bool) -> dict[str, Any]:
        """
        Record one backend invocation and return deterministic summary data.

        :param label: Benchmark label.
        :param n_nodes: Number of masses.
        :param vectorized: Backend selection flag.
        :param t_end: Final time.
        :param h: Time step.
        :param verbose: Verbosity flag.
        :return: Deterministic benchmark summary.
        """
        result: dict[str, Any] = {
            "mode": "VEC" if vectorized else "AD",
            "setup_s": 1.0 if vectorized else 2.0,
            "sim_s": 3.0 if vectorized else 4.0,
            "total_s": 4.0 if vectorized else 6.0,
            "ms_step": 5.0 if vectorized else 7.0,
            "n_steps": compute_steps(0.0, t_end, h),
            "activity": 9.0 if vectorized else 8.0,
        }
        self.run_calls.append(
            {
                "label": label,
                "n_nodes": n_nodes,
                "vectorized": vectorized,
                "t_end": t_end,
                "h": h,
                "verbose": verbose,
                "result": result,
            }
        )
        return result

    def print_case_summary(self, case_name: str, ad: dict[str, Any], vec: dict[str, Any]) -> None:
        """
        Record one printed case summary.

        :param case_name: Printed case label.
        :param ad: AD summary.
        :param vec: Vectorized summary.
        :return: None.
        """
        self.summaries.append({"case_name": case_name, "ad": ad, "vec": vec})


def _eval_expr(expr: Any, values: dict[str, float]) -> float:
    """
    Evaluate one symbolic expression for the supplied sample point.

    :param expr: Symbolic expression.
    :param values: Sample values keyed by variable name.
    :return: Evaluated scalar.
    """
    return float(expr.eval(**values))


def create_linear_chain(n_masses: int, vf: VarFactory) -> Block:
    """
    Build the repeated linear mass-spring-damper benchmark model.

    :param n_masses: Number of masses in the chain.
    :param vf: Shared symbolic variable factory.
    :return: Root symbolic block.
    """
    pos_vars: list[Var] = list()
    d_pos_vars: list[Var] = list()
    vel_vars: list[Var] = list()
    d_vel_vars: list[Var] = list()
    state_vars: list[Var] = list()
    diff_vars: list[Var] = list()
    state_eqs: list[Expr] = list()
    spring_k: Const = Const(5000.0)
    damping_c: Const = Const(0.5)
    mass_index: int

    # The benchmark repeats one linear second-order cell, so the test rebuilds the exact symbolic ordering locally.
    for mass_index in range(n_masses):
        pos_vars.append(vf.add_var(f"x_{mass_index}"))
        d_pos_vars.append(vf.add_diff_var(name=f"d_x_{mass_index}", base_var=pos_vars[mass_index]))
        vel_vars.append(vf.add_var(f"v_{mass_index}"))
        d_vel_vars.append(vf.add_diff_var(name=f"d_v_{mass_index}", base_var=vel_vars[mass_index]))

    for mass_index in range(n_masses):
        x_left: Expr
        x_right: Expr
        force_expr: Expr

        if mass_index > 0:
            x_left = pos_vars[mass_index - 1]
        else:
            x_left = Const(0.0)

        if mass_index < n_masses - 1:
            x_right = pos_vars[mass_index + 1]
        else:
            x_right = Const(0.0)

        force_expr = spring_k * (x_left - pos_vars[mass_index]) + spring_k * (x_right - pos_vars[mass_index]) - damping_c * vel_vars[mass_index]
        state_vars.append(pos_vars[mass_index])
        diff_vars.append(d_pos_vars[mass_index])
        state_vars.append(vel_vars[mass_index])
        diff_vars.append(d_vel_vars[mass_index])
        state_eqs.append(vel_vars[mass_index])
        state_eqs.append(force_expr)

    return Block(
        name=f"Linear_N{n_masses}",
        state_vars=state_vars,
        state_eqs=state_eqs,
        diff_vars=diff_vars,
        parameters=dict(),
    )


def compute_steps(t0: float, t_end: float, h: float) -> int:
    """
    Compute the benchmark step count using the demo rounding rule.

    :param t0: Initial time.
    :param t_end: Final time.
    :param h: Integration step.
    :return: Number of steps.
    """
    return int(np.ceil((t_end - t0) / h))


def break_even_runs(vec_setup: float, vec_sim: float, ad_setup: float, ad_sim: float) -> float:
    """
    Compute the run count where vectorized and AD cumulative times are equal.

    :param vec_setup: Vectorized setup time.
    :param vec_sim: Vectorized simulation time.
    :param ad_setup: AD setup time.
    :param ad_sim: AD simulation time.
    :return: Break-even run count or ``np.inf``.
    """
    denominator: float
    runs_value: float

    if vec_setup <= ad_setup and vec_sim <= ad_sim:
        return 0.0
    else:
        pass

    if vec_setup >= ad_setup and vec_sim >= ad_sim:
        return np.inf
    else:
        pass

    denominator = ad_sim - vec_sim
    if abs(denominator) < 1.0e-15:
        return np.inf
    else:
        runs_value = (vec_setup - ad_setup) / denominator

    if runs_value < 0.0:
        return np.inf
    else:
        return runs_value


def setup_initial_condition(problem: GenericEmtProblem, block: Block, n_nodes: int) -> None:
    """
    Install the sinusoidal displacement profile used by the benchmark.

    :param problem: Target EMT problem.
    :param block: Root symbolic block containing the state ordering.
    :param n_nodes: Number of masses in the chain.
    :return: None.
    """
    x0: np.ndarray = problem.get_x0()
    node_index: int

    # Only position states receive non-zero data; velocity states remain zero to match the benchmark contract.
    for node_index in range(n_nodes):
        state_index: int = 2 * node_index
        position_var: Var = block.state_vars[state_index]
        if position_var.uid in problem.uid2idx_vars:
            x0[problem.get_var_idx(position_var)] = 0.5 * np.sin(2.0 * np.pi * node_index / max(n_nodes, 1))
        else:
            pass

    problem.get_x0 = InitialConditionGetter(x0)


def run_backend(label: str, n_nodes: int, vectorized: bool, t_end: float, h: float, verbose: bool = False) -> Dict[str, Any]:
    """
    Execute the local AD or vectorized benchmark path.

    :param label: Benchmark label used in result metadata.
    :param n_nodes: Number of masses in the chain.
    :param vectorized: Select the vectorized backend when ``True``.
    :param t_end: Final simulation time.
    :param h: Time step.
    :param verbose: Solver verbosity flag.
    :return: Benchmark summary dictionary.
    """
    vf: VarFactory = VarFactory()
    block: Block = create_linear_chain(n_masses=n_nodes, vf=vf)
    t_sym: Var = Var("t_glob")
    static_parameter_values_mapping: Dict[Var, Const] = dict(block.parameters)
    problem: GenericEmtProblem
    x0: np.ndarray
    dx0: np.ndarray
    params0: np.ndarray
    target_method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeTrapezoidal
    solver: Any
    setup_s: float
    n_steps: int
    t_arr: np.ndarray
    y_arr: np.ndarray
    dy_arr: np.ndarray
    sim_s: float
    total_s: float
    ms_step: float
    activity: float
    setup_start: float = time.perf_counter()
    sim_start: float
    mode_text: str = "VEC" if vectorized else "AD"
    _unused_label: str = label

    block.unify_blocks()
    problem = GenericEmtProblem(
        sys_block=block,
        glob_time=t_sym,
        static_parameter_values_mapping=static_parameter_values_mapping,
    )
    setup_initial_condition(problem=problem, block=block, n_nodes=n_nodes)

    # The benchmark prepares these arrays before simulation. Keeping the preparation preserves the exact setup path.
    x0 = problem.get_x0()
    dx0 = np.zeros_like(x0, dtype=np.float64)
    params0 = np.zeros(problem.get_variable_parameter_number(), dtype=np.float64)
    _unused_sizes: tuple[int, int, int] = (len(x0), len(dx0), len(params0))

    if vectorized:
        solver = StructuralVectorizedSolver(problem, t0=0.0, t_end=t_end, h=h, method=target_method, verbose=verbose)
        solver.auto_detect_vectorization(method=target_method)
    else:
        solver = JitAdSolver(problem, t0=0.0, t_end=t_end, h=h, method=target_method, verbose=verbose)
        solver.build_jit_ad()

    solver.simulate()
    setup_s = time.perf_counter() - setup_start
    n_steps = compute_steps(0.0, t_end, h)
    sim_start = time.perf_counter()
    t_arr, y_arr, dy_arr = solver.simulate()
    _unused_shapes: tuple[int, int] = (len(t_arr), len(dy_arr))

    if vectorized and hasattr(solver, "last_pure_sim_time"):
        sim_s = float(solver.last_pure_sim_time)
    else:
        sim_s = time.perf_counter() - sim_start

    total_s = setup_s + sim_s
    ms_step = (sim_s / max(n_steps, 1)) * 1000.0
    activity = float(np.mean(np.abs(y_arr)))
    return {
        "mode": mode_text,
        "setup_s": setup_s,
        "sim_s": sim_s,
        "total_s": total_s,
        "ms_step": ms_step,
        "n_steps": n_steps,
        "activity": activity,
    }


def print_case_summary(case_name: str, ad: Dict[str, Any], vec: Dict[str, Any]) -> None:
    """
    Print the benchmark summary for one experiment case.

    :param case_name: Case label.
    :param ad: AD benchmark summary.
    :param vec: Vectorized benchmark summary.
    :return: None.
    """
    break_even_value: float = break_even_runs(vec["setup_s"], vec["sim_s"], ad["setup_s"], ad["sim_s"])
    one_shot: str = "AD" if ad["total_s"] <= vec["total_s"] else "VEC"
    throughput: str = "AD" if ad["sim_s"] <= vec["sim_s"] else "VEC"

    print("\n" + "-" * 96)
    print(f"[Summary] {case_name}")
    print("-" * 96)
    print(f"{'Mode':<8}{'Setup [s]':>14}{'Sim [s]':>14}{'Total [s]':>14}{'ms/step':>14}{'steps':>12}")
    print(f"{'AD':<8}{ad['setup_s']:>14.4f}{ad['sim_s']:>14.4f}{ad['total_s']:>14.4f}{ad['ms_step']:>14.6f}{ad['n_steps']:>12d}")
    print(f"{'VEC':<8}{vec['setup_s']:>14.4f}{vec['sim_s']:>14.4f}{vec['total_s']:>14.4f}{vec['ms_step']:>14.6f}{vec['n_steps']:>12d}")

    if break_even_value == 0.0:
        print("\nBreak-even VEC vs AD: 0.00 runs (VEC is dominant in both Setup and Sim!)")
    else:
        if np.isfinite(break_even_value):
            print(f"\nBreak-even VEC vs AD: ~{break_even_value:.2f} runs")
        else:
            print("\nBreak-even VEC vs AD: Does not compensate (VEC is slower in throughput)")

    print(f"Best one-shot (Setup+Sim): {one_shot}")
    print(f"Best throughput (Sim only): {throughput}")


def main() -> None:
    """
    Execute the fixed five-case experiment matrix.

    :return: None.
    """
    n_lin: int = 500
    experiments: list[dict[str, Any]] = list([
        dict({"h": 1e-7, "t_end": 1e-4, "name": "1k steps"}),
        dict({"h": 1e-7, "t_end": 1e-3, "name": "10k steps"}),
        dict({"h": 1e-7, "t_end": 5e-3, "name": "50k steps"}),
        dict({"h": 1e-8, "t_end": 1e-3, "name": "100k steps"}),
        dict({"h": 1e-8, "t_end": 2e-3, "name": "200k steps"}),
    ])
    cfg: dict[str, Any]

    for cfg in experiments:
        h: float = float(cfg["h"])
        t_end: float = float(cfg["t_end"])
        ad: Dict[str, Any] = run_backend(label="LIN", n_nodes=n_lin, vectorized=False, t_end=t_end, h=h, verbose=False)
        vec: Dict[str, Any] = run_backend(label="LIN", n_nodes=n_lin, vectorized=True, t_end=t_end, h=h, verbose=False)
        print_case_summary(case_name=f"Linear N={n_lin}, h={h:.1e}, t_end={t_end:.1e}", ad=ad, vec=vec)


def test_create_linear_chain_builds_the_exact_mass_spring_damper_system() -> None:
    """
    Verify the exact repeated linear model assembled by the benchmark helpers.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    block: Block = create_linear_chain(n_masses=3, vf=vf)
    sample: dict[str, float] = {
        "x_0": 0.30,
        "v_0": -0.70,
        "x_1": -0.10,
        "v_1": 0.20,
        "x_2": 0.40,
        "v_2": -0.50,
    }
    expected: list[float] = [
        sample["v_0"],
        5000.0 * (0.0 - sample["x_0"]) + 5000.0 * (sample["x_1"] - sample["x_0"]) - 0.5 * sample["v_0"],
        sample["v_1"],
        5000.0 * (sample["x_0"] - sample["x_1"]) + 5000.0 * (sample["x_2"] - sample["x_1"]) - 0.5 * sample["v_1"],
        sample["v_2"],
        5000.0 * (sample["x_1"] - sample["x_2"]) + 5000.0 * (0.0 - sample["x_2"]) - 0.5 * sample["v_2"],
    ]
    actual: list[float] = [_eval_expr(expr, sample) for expr in block.state_eqs]

    assert block.name == "Linear_N3"
    assert [var.name for var in block.state_vars] == ["x_0", "v_0", "x_1", "v_1", "x_2", "v_2"]
    assert [var.name for var in block.diff_vars] == ["d_x_0", "d_v_0", "d_x_1", "d_v_1", "d_x_2", "d_v_2"]
    assert len(block.state_eqs) == 6
    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1.0e-12)


def test_compute_steps_and_break_even_runs_follow_the_demo_formula() -> None:
    """
    Verify the fixed benchmark utility formulas and branches.

    :return: None.
    """
    assert compute_steps(0.0, 1.0e-3, 3.0e-4) == 4
    assert compute_steps(0.0, 1.0e-3, 2.5e-4) == 4
    assert break_even_runs(1.0, 2.0, 3.0, 4.0) == 0.0
    assert break_even_runs(3.0, 4.0, 1.0, 2.0) == np.inf
    assert break_even_runs(5.0, 1.0, 1.0, 3.0) == pytest.approx(2.0)
    assert break_even_runs(5.0, 2.0, 1.0, 2.0) == np.inf
    assert break_even_runs(1.0, 4.0, 3.0, 2.0) == pytest.approx(1.0)


def test_setup_initial_condition_installs_the_exact_sinusoidal_displacement_profile() -> None:
    """
    Verify the exact sinusoidal initial displacement profile and copy semantics.

    :return: None.
    """
    n_nodes: int = 4
    vf: VarFactory = VarFactory()
    block: Block = create_linear_chain(n_masses=n_nodes, vf=vf)
    static_parameter_values_mapping: Dict[Var, Const] = dict()
    problem: GenericEmtProblem
    expected: np.ndarray
    first: np.ndarray
    second: np.ndarray

    block.unify_blocks()
    problem = GenericEmtProblem(
        sys_block=block,
        glob_time=Var("t_glob"),
        static_parameter_values_mapping=static_parameter_values_mapping,
    )
    setup_initial_condition(problem=problem, block=block, n_nodes=n_nodes)
    expected = np.zeros(2 * n_nodes, dtype=np.float64)
    expected[0::2] = 0.5 * np.sin(2.0 * np.pi * np.arange(n_nodes) / n_nodes)
    first = problem.get_x0()
    second = problem.get_x0()

    np.testing.assert_allclose(first, expected, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(second, expected, rtol=0.0, atol=1.0e-12)
    first[0] = 123.0
    np.testing.assert_allclose(problem.get_x0(), expected, rtol=0.0, atol=1.0e-12)


def test_run_backend_ad_uses_the_measured_simulation_output_for_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verify the AD benchmark contract for setup timing and measured-trajectory metrics.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    perf_values: Any = iter([10.0, 13.0, 20.0, 24.0])
    result: Dict[str, Any]
    solver: FakeAdSolver
    measured_y: np.ndarray = np.array([[1.0, -2.0], [3.0, -4.0]], dtype=np.float64)
    expected_steps: int
    expected_activity: float
    _unused_monkeypatch: pytest.MonkeyPatch = monkeypatch

    FakeAdSolver.instances = list()
    with patch(__name__ + ".JitAdSolver", FakeAdSolver), patch.object(time, "perf_counter", lambda: next(perf_values)):
        result = run_backend(label="LIN", n_nodes=5, vectorized=False, t_end=1.1e-3, h=2.0e-4, verbose=False)

    solver = FakeAdSolver.instances[-1]
    expected_steps = compute_steps(0.0, 1.1e-3, 2.0e-4)
    expected_activity = float(np.mean(np.abs(measured_y)))
    assert solver.build_calls == 1
    assert solver.simulate_calls == 2
    assert result == {
        "mode": "AD",
        "setup_s": 3.0,
        "sim_s": 4.0,
        "total_s": 7.0,
        "ms_step": (4.0 / expected_steps) * 1000.0,
        "n_steps": expected_steps,
        "activity": expected_activity,
    }


def test_run_backend_vectorized_uses_solver_pure_loop_time_and_configures_vectorization(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verify the vectorized benchmark contract for auto-detection and pure-loop timing.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    perf_values: Any = iter([100.0, 106.0, 200.0])
    result: Dict[str, Any]
    solver: FakeVectorizedSolver
    measured_y: np.ndarray = np.array([[-2.0, 6.0], [4.0, -8.0]], dtype=np.float64)
    expected_steps: int
    expected_activity: float
    _unused_monkeypatch: pytest.MonkeyPatch = monkeypatch

    FakeVectorizedSolver.instances = list()
    with patch(__name__ + ".StructuralVectorizedSolver", FakeVectorizedSolver), patch.object(time, "perf_counter", lambda: next(perf_values)):
        result = run_backend(label="LIN", n_nodes=8, vectorized=True, t_end=9.0e-4, h=2.0e-4, verbose=False)

    solver = FakeVectorizedSolver.instances[-1]
    expected_steps = compute_steps(0.0, 9.0e-4, 2.0e-4)
    expected_activity = float(np.mean(np.abs(measured_y)))
    assert solver.auto_detect_calls == [DynamicIntegrationMethod.DaeTrapezoidal]
    assert solver.simulate_calls == 2
    assert result == {
        "mode": "VEC",
        "setup_s": 6.0,
        "sim_s": 0.125,
        "total_s": 6.125,
        "ms_step": (0.125 / expected_steps) * 1000.0,
        "n_steps": expected_steps,
        "activity": expected_activity,
    }


def test_main_executes_the_exact_experiment_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verify the fixed five-case experiment matrix and AD-then-VEC execution order.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    recorder: BenchmarkCallRecorder = BenchmarkCallRecorder()
    expected_experiments: list[dict[str, Any]] = [
        {"h": 1e-7, "t_end": 1e-4, "name": "1k steps"},
        {"h": 1e-7, "t_end": 1e-3, "name": "10k steps"},
        {"h": 1e-7, "t_end": 5e-3, "name": "50k steps"},
        {"h": 1e-8, "t_end": 1e-3, "name": "100k steps"},
        {"h": 1e-8, "t_end": 2e-3, "name": "200k steps"},
    ]
    index: int
    cfg: dict[str, Any]
    ad_call: dict[str, Any]
    vec_call: dict[str, Any]
    _unused_monkeypatch: pytest.MonkeyPatch = monkeypatch

    with patch(__name__ + ".run_backend", recorder.run_backend), patch(__name__ + ".print_case_summary", recorder.print_case_summary):
        main()

    assert len(recorder.run_calls) == 10
    assert len(recorder.summaries) == 5

    for index, cfg in enumerate(expected_experiments):
        ad_call = recorder.run_calls[2 * index]
        vec_call = recorder.run_calls[2 * index + 1]
        assert ad_call["label"] == "LIN"
        assert ad_call["n_nodes"] == 500
        assert ad_call["vectorized"] is False
        assert ad_call["t_end"] == cfg["t_end"]
        assert ad_call["h"] == cfg["h"]
        assert ad_call["verbose"] is False
        assert vec_call["label"] == "LIN"
        assert vec_call["n_nodes"] == 500
        assert vec_call["vectorized"] is True
        assert vec_call["t_end"] == cfg["t_end"]
        assert vec_call["h"] == cfg["h"]
        assert vec_call["verbose"] is False
        assert recorder.summaries[index]["case_name"] == f"Linear N=500, h={cfg['h']:.1e}, t_end={cfg['t_end']:.1e}"
        assert recorder.summaries[index]["ad"] is ad_call["result"]
        assert recorder.summaries[index]["vec"] is vec_call["result"]
