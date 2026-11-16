"""Ten fresh vectorized BDF1–5 VeraGrid RMS runs matching the Julia event cases."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from time import perf_counter

import numpy as np

from run_rms_time_series import CASES, DATA, prepare_case
from VeraGridEngine.Simulations.Rms.numerical.adaptive_bdf15 import AdaptiveBdf15Integration
from VeraGridEngine.Simulations.Rms.rms_problem_factory import build_rms_problem
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler, RMSCompilerVec
from VeraGridEngine.enumerations import DynamicIntegrationMethod, RmsProblemTypes

OUT = Path(__file__).resolve().parent / "results" / "ten_run_timing" / "veragrid.csv"


def run_case(name: str, repetition: int, duration: float | None = None,
             backend: str = "vectorized") -> dict[str, object]:
    start = perf_counter()
    grid, pf, events, options, observable = prepare_case(name)
    setup = perf_counter() - start
    options.problem_type = RmsProblemTypes.PowerBalanceVectorized
    options.integration_method = DynamicIntegrationMethod.DaeAdaptiveBdf15
    options.time_step = {"2_bus": .02, "3_bus": .02, "ieee9": .01, "wecc_240": .01}[name]
    options.bdf_absolute_tolerance = 1e-6
    options.bdf_relative_tolerance = 1e-3
    if duration is not None:
        if duration <= 1.0 or duration > options.simulation_time:
            raise ValueError("Duration must exceed the 1-second event and not exceed the case horizon")
        options.simulation_time = duration

    compile_times = {"rhs_compile_s": 0.0, "jacobian_compile_s": 0.0}
    originals = {}
    for cls in (RMSCompiler, RMSCompilerVec):
        for method, key in (("compile_rhs", "rhs_compile_s"),
                            ("compile_sparse_jacobian", "jacobian_compile_s")):
            original = getattr(cls, method)
            originals[cls, method] = original

            def wrapped(self, *args, _original=original, _key=key, **kwargs):
                start = perf_counter()
                try:
                    return _original(self, *args, **kwargs)
                finally:
                    compile_times[_key] += perf_counter() - start
            setattr(cls, method, wrapped)
    if backend == "numba-scalar":
        from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_numba_comp import RmsProblemDae
        problem_class = RmsProblemDae
    elif backend == "numba-full-vectorized":
        from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_full_vectorized_numba_comp import RmsProblemDaeFullVec
        problem_class = RmsProblemDaeFullVec
    elif backend == "vectorized":
        problem_class = None
    else:
        raise ValueError(f"Unknown RMS backend: {backend}")
    try:
        start = perf_counter()
        constructor = problem_class or build_rms_problem
        problem = constructor(grid=grid, options=options, pf_results=pf,
                              progress_signal=None)
        problem.set_events_group(events)
        problem.reset_boundary_update_state(0.0)
        build = perf_counter() - start
    finally:
        for (cls, method), original in originals.items():
            setattr(cls, method, original)

    solver = AdaptiveBdf15Integration(
        problem=problem, t0=0.0, t_end=options.simulation_time,
        h=options.time_step, max_iter=options.max_iter,
        tolerance=options.tolerance,
        absolute_tolerance=options.bdf_absolute_tolerance,
        relative_tolerance=options.bdf_relative_tolerance,
        maximum_order=5, maximum_step=options.time_step,
        linear_solver="sparse",
    )
    integration_times = {"rhs_evaluation_s": 0.0,
                         "jacobian_evaluation_s": 0.0,
                         "linear_solver_s": 0.0}
    wrapped_methods = {}
    for method, key in (("_evaluate_residual", "rhs_evaluation_s"),
                        ("_jacobian", "jacobian_evaluation_s"),
                        ("_factorize", "linear_solver_s"),
                        ("_linear_solve", "linear_solver_s")):
        original = getattr(AdaptiveBdf15Integration, method)
        wrapped_methods[method] = original

        def wrapped(self, *args, _original=original, _key=key, **kwargs):
            start = perf_counter()
            try:
                return _original(self, *args, **kwargs)
            finally:
                integration_times[_key] += perf_counter() - start
        setattr(AdaptiveBdf15Integration, method, wrapped)
    try:
        start = perf_counter()
        times, values, initialized, converged = solver.simulate()
        integration = perf_counter() - start
    finally:
        for method, original in wrapped_methods.items():
            setattr(AdaptiveBdf15Integration, method, original)
    if not initialized or not converged:
        raise RuntimeError(f"{name} repetition {repetition}: initialized={initialized}, converged={converged}")
    observed = values[:, problem.uid2idx_vars[observable]]
    with (DATA / f"{name}_rms_time_series.csv").open(newline="", encoding="utf-8") as stream:
        reference = list(csv.DictReader(stream))
    reference_time = np.asarray([float(row["time"]) for row in reference])
    reference_value = np.asarray([float(row["value"]) for row in reference])
    keep = reference_time <= options.simulation_time + 1e-12
    reference_time, reference_value = reference_time[keep], reference_value[keep]
    error = np.interp(reference_time, times, observed) - reference_value
    return {
        "case": name, "repetition": repetition,
        "setup_s": setup, "problem_build_s": build,
        **compile_times,
        "other_problem_build_s": build - sum(compile_times.values()),
        "integration_s": integration,
        **integration_times,
        "other_integration_s": integration - sum(integration_times.values()),
        "accepted_steps": solver.accepted_steps,
        "rejected_steps": solver.rejected_steps,
        "residual_evaluations": solver.residual_evaluations,
        "jacobian_refreshes": solver.jacobian_refreshes,
        "linear_iterations": solver.linear_iterations,
        "nonlinear_iterations": solver.nonlinear_iterations,
        "order_counts": ";".join(str(int(value)) for value in solver.order_counts),
        "total_s": setup + build + integration,
        "rmse": float(np.sqrt(np.mean(error**2))),
        "max_abs_error": float(np.max(np.abs(error))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, action="append")
    parser.add_argument("--duration", type=float)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--backend", choices=("vectorized", "numba-scalar",
                                              "numba-full-vectorized"),
                        default="vectorized")
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = None
        for repetition in range(1, args.repetitions + 1):
            for name in args.case or CASES:
                row = run_case(name, repetition, args.duration, args.backend)
                if writer is None:
                    writer = csv.DictWriter(stream, fieldnames=list(row))
                    writer.writeheader()
                writer.writerow(row)
                stream.flush()
                print(f"{name} {repetition}/{args.repetitions} total={row['total_s']:.3f}s "
                      f"rmse={row['rmse']:.6g}", flush=True)


if __name__ == "__main__":
    main()
