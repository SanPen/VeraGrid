"""Time the STAMP WSCC load-step RMS trajectory in VeraGrid.

The STAMP Load-1 parallel-resistance step adds R/DR in parallel with R, so
DR=0.01 raises its conductance by 1 percent at t=0.01 s.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from time import perf_counter

import numpy as np

from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.enumerations import VarPowerFlowReferenceType

from run_rms import build_initialized_problem


def run(duration: float, step: float, output_dir: Path,
        tolerance: float = 1e-8, max_iter: int = 100) -> None:
    setup_start = perf_counter()
    problem, initial = build_initialized_problem()
    grid = problem.grid
    load = next(item for item in grid.loads if item.name == "Load1")
    conductance = next(parameter for block in load.rms_model.get_all_blocks()
                       for parameter in block.event_dict
                       if parameter.name == "Load1.G0")
    vm_var = load.bus.rms_model.external_mapping[VarPowerFlowReferenceType.Vm]
    voltage = initial[problem.uid2idx_vars[vm_var.uid]]
    baseline = load.P / grid.Sbase / voltage**2
    group = RmsEventsGroup(name="stamp_wscc_load_step")
    grid.add_rms_events_group(group)
    grid.add_rms_event(RmsEvent(
        device=load, parameter=conductance, time=0.01,
        value=baseline * 1.01, group=group, force_step_alignment=True,
    ))
    for variable, value in zip((*problem.state_vars, *problem.algebraic_vars), initial):
        problem.init_guess[variable.uid] = float(value)
    problem.set_events_group(group)
    problem.reset_boundary_update_state(0.0)
    speed = next(var for var in problem.state_vars if str(var) == "STAMP_SG1.w_pu")
    setup_seconds = perf_counter() - setup_start

    solver = BackEulerImplicitIntegration(
        problem=problem, t0=0.0, t_end=duration, h=step,
        max_iter=max_iter, tolerance=tolerance,
    )
    start = perf_counter()
    time, values, initialized, converged = solver.simulate()
    simulation_seconds = perf_counter() - start
    if not initialized or not converged:
        raise RuntimeError(f"VeraGrid RMS run failed: initialized={initialized}, "
                           f"converged={converged}; last time={time[-1]:g} s")
    omega = values[:, problem.uid2idx_vars[speed.uid]]
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "veragrid_trajectory.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("time_s", "sg_speed_pu"))
        writer.writerows(zip(time, omega))
    with (output_dir / "veragrid_timing.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("implementation", "setup_seconds", "simulation_seconds",
                         "total_seconds", "step_s", "duration_s", "samples",
                         "newton_tolerance", "max_iter"))
        writer.writerow(("VeraGrid", setup_seconds, simulation_seconds,
                         setup_seconds + simulation_seconds, step, duration, len(time),
                         tolerance, max_iter))
    print(f"VeraGrid: initialized={initialized}, converged={converged}, "
          f"samples={len(time)}, setup={setup_seconds:.6g}s, "
          f"simulation={simulation_seconds:.6g}s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=0.3)
    parser.add_argument("--step", type=float, default=1e-5)
    parser.add_argument("--tolerance", type=float, default=1e-8)
    parser.add_argument("--max-iter", type=int, default=100)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.duration <= 0.01 or args.step <= 0 or args.tolerance <= 0 or args.max_iter < 1:
        parser.error("duration must exceed 0.01 s; step, tolerance, and max-iter must be positive")
    run(args.duration, args.step, args.output_dir, args.tolerance, args.max_iter)


if __name__ == "__main__":
    main()
