"""Time the compiled scalar RMS AD problem with Backward Euler."""

from __future__ import annotations

import argparse
from time import perf_counter

from run_rms_time_series import prepare_case

from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_numba_comp import RmsProblemDae


def run_case(name: str, duration: float) -> None:
    start = perf_counter()
    grid, power_flow, events, options, observable = prepare_case(name)
    options.simulation_time = duration
    setup = perf_counter() - start

    start = perf_counter()
    problem = RmsProblemDae(grid=grid, options=options, pf_results=power_flow)
    problem.set_events_group(events)
    problem.reset_boundary_update_state(0.0)
    build = perf_counter() - start

    solver = BackEulerImplicitIntegration(
        problem=problem, t0=0.0, t_end=duration, h=options.time_step,
        max_iter=options.max_iter, tolerance=options.tolerance,
    )
    start = perf_counter()
    times, values, initialized, converged = solver.simulate()
    integration = perf_counter() - start
    last_observable = values[-1, problem.uid2idx_vars[observable]]
    print(f"{name}: setup={setup:.3f}s build={build:.3f}s "
          f"integration={integration:.3f}s steps={len(times) - 1} "
          f"initialized={initialized} converged={converged} "
          f"last_observable={last_observable:.12g} "
          f"jacobian={solver._timings['jacobian_time']:.3f}s", flush=True)
    if not initialized or not converged:
        raise RuntimeError(f"{name}: compiled AD simulation did not complete")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("ieee9", "wecc_240"), action="append")
    parser.add_argument("--duration", type=float, default=5.0)
    args = parser.parse_args()
    if args.duration <= 1.0:
        parser.error("--duration must be greater than the event time of 1 s")
    for name in args.case or ("ieee9", "wecc_240"):
        run_case(name, args.duration)


if __name__ == "__main__":
    main()
