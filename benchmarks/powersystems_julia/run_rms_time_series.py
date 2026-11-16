"""Compare VeraGrid RMS event trajectories with saved PowerSimulationsDynamics.jl runs."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
DATA = SRC / "tests" / "data" / "powersystems_julia"
CASES = ("2_bus", "3_bus", "ieee9", "wecc_240")
JULIA_TIMINGS = DATA / "julia_rms_time_series_timings.csv"

from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.rms_problem_factory import build_rms_problem
from VeraGridEngine.enumerations import VarPowerFlowReferenceType

from run_small_signal import (power_flow_options, prepare_wecc_static_power_flow,
                              seed_wecc_rms_operating_point)


def event_parameter(device, name):
    for block in device.rms_model.get_all_blocks():
        for parameter in block.event_dict:
            if parameter.name == name:
                return parameter
    raise KeyError(f"{device.name}: RMS event parameter {name!r} is missing")


def julia_timing(name: str) -> dict[str, float]:
    """Read the single saved after-first-run Julia measurement for a case."""
    with JULIA_TIMINGS.open(newline="", encoding="utf-8") as stream:
        rows = [row for row in csv.DictReader(stream)
                if row["case"] == name and int(row["repetition"]) == 2]
    if len(rows) != 1:
        raise ValueError(f"{name}: expected one after-first-run Julia timing")
    return {key: float(rows[0][key]) for key in
            ("build_seconds", "compilation_seconds", "compute_seconds", "total_seconds")}


def prepare_case(name):
    grid = FileOpen(file_name=str(DATA / f"{name}.veragrid")).open()
    admittances = prepare_wecc_static_power_flow(grid) if name == "wecc_240" else None
    pf_options = power_flow_options()
    if name == "wecc_240":
        pf_options.retry_with_other_methods = True
        pf_options.max_iter = 100
        pf_options.control_Q = True
    power_flow = PowerFlowDriver(grid, pf_options)
    power_flow.run()
    if not power_flow.results.converged:
        raise RuntimeError(f"{name}: power flow did not converge")
    if admittances is not None:
        seed_wecc_rms_operating_point(grid, power_flow.results, admittances)

    if name == "2_bus":
        source = grid.external_grids[0]
        bus_index = grid.get_bus_index_dict()[source.bus]
        source.P = -power_flow.results.Sbus[bus_index].real
        source.Q = -power_flow.results.Sbus[bus_index].imag
        device = grid.generators[0]
        parameter_name, event_value = "mechanical_torque", 0.55
        observable = next(var.uid for var in device.rms_model.state_vars
                          if var.name == "delta")
        duration, step, tolerance = 10.0, 0.0005, 1e-10
    elif name == "3_bus":
        source = grid.external_grids[0]
        slack = source.bus
        flow = 0j
        for index, branch in enumerate(grid.get_branches_iter(
                add_vsc=False, add_hvdc=False, add_switch=True)):
            if branch.bus_from is slack:
                flow += power_flow.results.Sf[index]
            if branch.bus_to is slack:
                flow += power_flow.results.St[index]
        voltage = abs(power_flow.results.voltage[grid.get_bus_index_dict()[slack]])
        shunt = sum(complex(-item.G, item.B) * voltage**2
                    for item in grid.shunts if item.bus is slack)
        source.P = -(flow - shunt).real
        source.Q = -(flow - shunt).imag
        device = next(gen for gen in grid.generators if gen.name == "generator-103-1")
        parameter_name, event_value = "P_ref", 0.85
        bus = next(bus for bus in grid.buses if bus.code == "102")
        observable = bus.rms_model.external_mapping[VarPowerFlowReferenceType.Vm].uid
        duration, step, tolerance = 10.0, 0.001, 1e-10
    elif name == "ieee9":
        device = next(gen for gen in grid.generators if gen.name == "2_1")
        parameter_name, event_value = "P_ref", 0.78
        bus = next(bus for bus in grid.buses if bus.code == "5")
        observable = bus.rms_model.external_mapping[VarPowerFlowReferenceType.Vm].uid
        duration, step, tolerance = 2.0, 0.001, 1e-6
    else:
        # PowerSimulationsDynamics.jl trips circuit 1 between buses 1101 and
        # 1401; the saved VeraGrid fixture uses the same RAW circuit label.
        device = next(line for line in grid.lines if line.code == "1101_1401_1")
        parameter_name, event_value = "u", 0.0
        bus = next(bus for bus in grid.buses if bus.code == "1101")
        observable = bus.rms_model.external_mapping[VarPowerFlowReferenceType.Vm].uid
        duration, step, tolerance = 20.0, 0.01, 1e-6

    group = RmsEventsGroup(name="powersystems_julia_time_series")
    grid.add_rms_events_group(group)
    grid.add_rms_event(RmsEvent(
        device=device, parameter=event_parameter(device, parameter_name),
        time=1.0, value=event_value, group=group, force_step_alignment=True,
    ))
    options = RmsOptions(time_step=step, simulation_time=duration,
                         tolerance=tolerance, max_iter=1000, verbose=0)
    return grid, power_flow.results, group, options, observable


def run_case(name: str, trajectory_path: Path | None = None,
             newton_convergence: str = "residual",
             rms_tolerance: float | None = None) -> dict[str, object]:
    start = perf_counter()
    grid, pf_results, group, options, observable = prepare_case(name)
    options.use_weighted_newton_correction = newton_convergence == "ida-weighted"
    if rms_tolerance is not None:
        if not math.isfinite(rms_tolerance) or rms_tolerance <= 0:
            raise ValueError("RMS tolerance must be finite and positive")
        options.tolerance = rms_tolerance
    setup_seconds = perf_counter() - start
    start = perf_counter()
    problem = build_rms_problem(grid=grid, options=options, pf_results=pf_results,
                                progress_signal=None)
    problem.set_events_group(group)
    problem.reset_boundary_update_state(0.0)
    compilation_seconds = perf_counter() - start

    solver = BackEulerImplicitIntegration(
        problem=problem, t0=0.0, t_end=options.simulation_time,
        h=options.time_step, max_iter=options.max_iter,
        tolerance=options.tolerance,
        weighted_newton_tolerances=(
            options.weighted_newton_absolute_tolerance,
            options.weighted_newton_relative_tolerance,
        ) if options.use_weighted_newton_correction else None,
    )
    start = perf_counter()
    time, values, well_initialized, converged = solver.simulate()
    integration_seconds = perf_counter() - start
    if not well_initialized or not converged:
        raise RuntimeError(f"{name}: RMS initialization={well_initialized}, "
                           f"integration convergence={converged}")
    observed = values[:, problem.uid2idx_vars[observable]]
    with (DATA / f"{name}_rms_time_series.csv").open(newline="", encoding="utf-8") as stream:
        reference = list(csv.DictReader(stream))
    reference_time = np.asarray([float(row["time"]) for row in reference])
    reference_value = np.asarray([float(row["value"]) for row in reference])
    if not np.all(np.diff(reference_time) > 0):
        raise ValueError(f"{name}: Julia reference times are not strictly increasing")
    if reference_time[0] < time[0] or reference_time[-1] > time[-1] + 1e-9:
        raise ValueError(f"{name}: Julia reference exceeds the simulated time range")
    compared = np.interp(reference_time, time, observed)
    error = compared - reference_value
    if trajectory_path is not None:
        trajectory_path.parent.mkdir(parents=True, exist_ok=True)
        with trajectory_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("time_s", "julia", "veragrid", "error"))
            writer.writerows(zip(reference_time, reference_value, compared, error))
    julia = julia_timing(name)
    return {
        "case": name, "newton_convergence": newton_convergence,
        "rms_tolerance": options.tolerance,
        "samples": len(reference_time),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "max_abs_error": float(np.max(np.abs(error))),
        "veragrid_setup_seconds": setup_seconds,
        "veragrid_rms_build_seconds": compilation_seconds,
        "veragrid_integration_seconds": integration_seconds,
        "veragrid_total_seconds": setup_seconds + compilation_seconds + integration_seconds,
        "julia_build_seconds": julia["build_seconds"],
        "julia_compilation_seconds": julia["compilation_seconds"],
        "julia_compute_seconds": julia["compute_seconds"],
        "julia_total_seconds": julia["total_seconds"],
        "observed_integration_time_ratio": integration_seconds / julia["compute_seconds"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, action="append",
                        help="Case to run; default: all four")
    parser.add_argument("--output", type=Path, help="Optional CSV summary")
    parser.add_argument("--trajectory-dir", type=Path,
                        help="Optional directory for time-aligned comparison CSVs")
    parser.add_argument("--newton-convergence", choices=("residual", "ida-weighted"),
                        default="residual", help="VeraGrid Newton stopping rule")
    parser.add_argument("--rms-tolerance", type=float,
                        help="Override VeraGrid Newton residual and initial projection tolerance")
    args = parser.parse_args()
    if args.rms_tolerance is not None and (
        not math.isfinite(args.rms_tolerance) or args.rms_tolerance <= 0
    ):
        parser.error("--rms-tolerance must be finite and positive")
    results = [run_case(name, args.trajectory_dir / f"{name}.csv"
                        if args.trajectory_dir else None, args.newton_convergence,
                        args.rms_tolerance)
               for name in (args.case or CASES)]
    for result in results:
        print(f"{result['case']} [{result['newton_convergence']}, "
              f"tolerance={result['rms_tolerance']:.6g}]: {result['samples']} samples, "
              f"RMSE={result['rmse']:.6g}, max error={result['max_abs_error']:.6g}")
        print("  phase                    VeraGrid [s]     Julia [s]")
        print(f"  setup/build              {result['veragrid_setup_seconds']:12.6g}  "
              f"{result['julia_build_seconds']:12.6g}")
        print(f"  RMS build/compilation    {result['veragrid_rms_build_seconds']:12.6g}  "
              f"{result['julia_compilation_seconds']:12.6g}")
        print(f"  integration/compute      {result['veragrid_integration_seconds']:12.6g}  "
              f"{result['julia_compute_seconds']:12.6g}")
        print(f"  total                    {result['veragrid_total_seconds']:12.6g}  "
              f"{result['julia_total_seconds']:12.6g}")
        print(f"  unmatched-setup integration time ratio (VeraGrid/Julia): "
              f"{result['observed_integration_time_ratio']:.6g}x")
    print("Julia times are saved after-first-run measurements from the sibling checkout; "
          "VeraGrid times are measured here. Julia uses adaptive Sundials IDA with "
          "dtmax=0.01 s for WECC 240. VeraGrid uses fixed-step Backward Euler; "
          "neither VeraGrid Newton stopping rule reproduces IDA's integration "
          "error control. The ratio is not a like-for-like solver speed comparison.")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=tuple(results[0]))
            writer.writeheader()
            writer.writerows(results)


if __name__ == "__main__":
    main()
