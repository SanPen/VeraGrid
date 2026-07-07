# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import importlib.util
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest


def _load_demo_module() -> Any:
    repo_root = Path(__file__).resolve().parents[3]
    demo_path = repo_root / "trunk" / "implicit_solver_test_EMT" / "Demos" / "demo_scalability_nodes.py"
    spec = importlib.util.spec_from_file_location("demo_scalability_nodes_demo", demo_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _eval_expr(expr: Any, **values: float) -> float:
    return float(expr.eval(**values))


@pytest.fixture(scope="module")
def demo_module() -> Any:
    """Load the real demo module under test from `trunk/`."""
    return _load_demo_module()


def test_create_linear_chain_builds_the_exact_mass_spring_damper_system(demo_module: Any) -> None:
    """
    The demo benchmark is scientifically about one specific repeated linear model.

    This test checks the exact state ordering and the exact force law that the
    benchmark compiles and simulates. If the model equations change, the demo's
    numerical meaning changes and this test must fail.
    """
    vf = demo_module.VarFactory()
    block = demo_module.create_linear_chain(n_masses=3, vf=vf)

    assert block.name == "Linear_N3"
    assert [var.name for var in block.state_vars] == ["x_0", "v_0", "x_1", "v_1", "x_2", "v_2"]
    assert [var.name for var in block.diff_vars] == ["d_x_0", "d_v_0", "d_x_1", "d_v_1", "d_x_2", "d_v_2"]
    assert len(block.state_eqs) == 6

    sample = {
        "x_0": 0.30,
        "v_0": -0.70,
        "x_1": -0.10,
        "v_1": 0.20,
        "x_2": 0.40,
        "v_2": -0.50,
    }

    expected = [
        sample["v_0"],
        5000.0 * (0.0 - sample["x_0"]) + 5000.0 * (sample["x_1"] - sample["x_0"]) - 0.5 * sample["v_0"],
        sample["v_1"],
        5000.0 * (sample["x_0"] - sample["x_1"]) + 5000.0 * (sample["x_2"] - sample["x_1"]) - 0.5 * sample["v_1"],
        sample["v_2"],
        5000.0 * (sample["x_1"] - sample["x_2"]) + 5000.0 * (0.0 - sample["x_2"]) - 0.5 * sample["v_2"],
    ]

    actual = [_eval_expr(expr, **sample) for expr in block.state_eqs]
    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-12)


def test_compute_steps_and_break_even_runs_follow_the_demo_formula(demo_module: Any) -> None:
    """
    The benchmark summary is defined by these utility formulas.

    The test checks the exact branch logic used by the demo, not just that the
    functions return something finite.
    """
    assert demo_module.compute_steps(0.0, 1.0e-3, 3.0e-4) == 4
    assert demo_module.compute_steps(0.0, 1.0e-3, 2.5e-4) == 4

    assert demo_module.break_even_runs(1.0, 2.0, 3.0, 4.0) == 0.0
    assert demo_module.break_even_runs(3.0, 4.0, 1.0, 2.0) == np.inf
    assert demo_module.break_even_runs(5.0, 1.0, 1.0, 3.0) == pytest.approx(2.0)
    assert demo_module.break_even_runs(5.0, 2.0, 1.0, 2.0) == np.inf
    assert demo_module.break_even_runs(1.0, 4.0, 3.0, 2.0) == pytest.approx(1.0)


def test_setup_initial_condition_installs_the_exact_sinusoidal_displacement_profile(demo_module: Any) -> None:
    """
    The only non-zero initial data in the demo are the sinusoidal node positions.

    This test checks the exact amplitude, phase convention, state placement and
    copy semantics of the overridden `get_x0` callable.
    """
    n_nodes = 4
    vf = demo_module.VarFactory()
    block = demo_module.create_linear_chain(n_masses=n_nodes, vf=vf)
    block.unify_blocks()
    problem = demo_module.GenericEmtProblem(sys_block=block, glob_time=demo_module.Var("t_glob"))

    demo_module.setup_initial_condition(problem, block, n_nodes)

    expected = np.zeros(2 * n_nodes, dtype=np.float64)
    expected[0::2] = 0.5 * np.sin(2.0 * np.pi * np.arange(n_nodes) / n_nodes)

    first = problem.get_x0()
    second = problem.get_x0()

    np.testing.assert_allclose(first, expected, rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(second, expected, rtol=0.0, atol=1e-12)

    # The demo intentionally replaces `get_x0` with a copy-returning callable.
    # Mutating one returned array must not mutate later calls.
    first[0] = 123.0
    np.testing.assert_allclose(problem.get_x0(), expected, rtol=0.0, atol=1e-12)


def test_run_backend_ad_uses_the_measured_simulation_output_for_metrics(
    demo_module: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The AD benchmark contract is:
    - build the AD kernel,
    - do one warm-up simulation inside setup time,
    - do one measured simulation,
    - derive activity from the measured trajectory,
    - derive `sim_s` from wall-clock time when no solver-specific pure-loop timer exists.
    """

    class FakeAdSolver:
        instances = []

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
            self.build_calls += 1

        def simulate(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
            self.simulate_calls += 1
            if self.simulate_calls == 1:
                y_arr = np.array([[9.0, -9.0]], dtype=np.float64)
            else:
                y_arr = np.array([[1.0, -2.0], [3.0, -4.0]], dtype=np.float64)
            return np.array([0.0], dtype=np.float64), y_arr, np.zeros_like(y_arr)

    perf_values = iter([10.0, 13.0, 20.0, 24.0])

    with patch.object(demo_module, "JitAdSolver", FakeAdSolver), patch.object(
        demo_module.time,
        "perf_counter",
        lambda: next(perf_values),
    ):
        result = demo_module.run_backend(
            label="LIN",
            n_nodes=5,
            vectorized=False,
            t_end=1.1e-3,
            h=2.0e-4,
            verbose=False,
        )

    solver = FakeAdSolver.instances[-1]
    measured_y = np.array([[1.0, -2.0], [3.0, -4.0]], dtype=np.float64)
    expected_steps = demo_module.compute_steps(0.0, 1.1e-3, 2.0e-4)
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


def test_run_backend_vectorized_uses_solver_pure_loop_time_and_configures_vectorization(
    demo_module: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The vectorized benchmark contract differs from AD in two crucial ways:
    - it must call `auto_detect_vectorization` for the target integration method,
    - if the solver exposes `last_pure_sim_time`, that exact value defines `sim_s`.
    """

    class FakeVectorizedSolver:
        instances = []

        def __init__(self, problem: Any, t0: float, t_end: float, h: float, method: Any, verbose: bool) -> None:
            self.problem = problem
            self.t0 = t0
            self.t_end = t_end
            self.h = h
            self.method = method
            self.verbose = verbose
            self.auto_detect_calls = []
            self.simulate_calls = 0
            self.last_pure_sim_time = 0.125
            type(self).instances.append(self)

        def auto_detect_vectorization(self, method: Any) -> None:
            self.auto_detect_calls.append(method)

        def simulate(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
            self.simulate_calls += 1
            if self.simulate_calls == 1:
                y_arr = np.array([[100.0]], dtype=np.float64)
            else:
                y_arr = np.array([[-2.0, 6.0], [4.0, -8.0]], dtype=np.float64)
            return np.array([0.0], dtype=np.float64), y_arr, np.zeros_like(y_arr)

    perf_values = iter([100.0, 106.0, 200.0])

    with patch.object(demo_module, "StructuralVectorizedSolver", FakeVectorizedSolver), patch.object(
        demo_module.time,
        "perf_counter",
        lambda: next(perf_values),
    ):
        result = demo_module.run_backend(
            label="LIN",
            n_nodes=8,
            vectorized=True,
            t_end=9.0e-4,
            h=2.0e-4,
            verbose=False,
        )

    solver = FakeVectorizedSolver.instances[-1]
    measured_y = np.array([[-2.0, 6.0], [4.0, -8.0]], dtype=np.float64)
    expected_steps = demo_module.compute_steps(0.0, 9.0e-4, 2.0e-4)
    expected_activity = float(np.mean(np.abs(measured_y)))

    assert solver.auto_detect_calls == [demo_module.DynamicIntegrationMethod.DaeTrapezoidal]
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


def test_main_executes_the_exact_experiment_matrix(demo_module: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The demo's public experiment plan is fixed in `main()`.

    This test verifies the exact five `(h, t_end)` cases, the fixed node count
    `N_LIN = 500`, the AD-then-VEC execution order, and the summary labels that
    describe each benchmark case.
    """
    run_calls: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    def fake_run_backend(label: str, n_nodes: int, vectorized: bool, t_end: float, h: float, verbose: bool) -> dict[str, Any]:
        result = {
            "mode": "VEC" if vectorized else "AD",
            "setup_s": 1.0 if vectorized else 2.0,
            "sim_s": 3.0 if vectorized else 4.0,
            "total_s": 4.0 if vectorized else 6.0,
            "ms_step": 5.0 if vectorized else 7.0,
            "n_steps": demo_module.compute_steps(0.0, t_end, h),
            "activity": 9.0 if vectorized else 8.0,
        }
        run_calls.append(
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

    def fake_print_case_summary(case_name: str, ad: dict[str, Any], vec: dict[str, Any]) -> None:
        summaries.append({"case_name": case_name, "ad": ad, "vec": vec})

    with patch.object(demo_module, "run_backend", fake_run_backend), patch.object(
        demo_module,
        "print_case_summary",
        fake_print_case_summary,
    ):
        demo_module.main()

    expected_experiments = [
        {"h": 1e-7, "t_end": 1e-4, "name": "1k steps"},
        {"h": 1e-7, "t_end": 1e-3, "name": "10k steps"},
        {"h": 1e-7, "t_end": 5e-3, "name": "50k steps"},
        {"h": 1e-8, "t_end": 1e-3, "name": "100k steps"},
        {"h": 1e-8, "t_end": 2e-3, "name": "200k steps"},
    ]

    assert len(run_calls) == 10
    assert len(summaries) == 5

    for index, cfg in enumerate(expected_experiments):
        ad_call = run_calls[2 * index]
        vec_call = run_calls[2 * index + 1]

        # The demo benchmark always uses the fixed repeated linear system with 500 nodes.
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

        assert summaries[index]["case_name"] == f"Linear N=500, h={cfg['h']:.1e}, t_end={cfg['t_end']:.1e}"
        assert summaries[index]["ad"] is ad_call["result"]
        assert summaries[index]["vec"] is vec_call["result"]
