#!/usr/bin/env python3
"""Compare the saved nonlinear WSCC RMS grid with STAMP's 88 eigenvalues.

Dynamic-network initialization is adapted from STAMP_Public's
``scripts/benchmark_veragrid_wscc_ssa.py``.
"""

import csv
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import scipy.linalg as la
from scipy.optimize import root
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "src" / "tests" / "data" / "stamp_wscc"
MEASURE_TIME = False
TIMING_RUNS = 20

from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.enumerations import SolverType

STAMP_LOADS = ((2, 125.0, 50.0), (3, 90.0, 30.0), (5, 100.0, 35.0))


def power_flow_options():
    return PowerFlowOptions(
        solver_type=SolverType.NR, retry_with_other_methods=False,
        tolerance=1e-10, max_iter=50, control_q=False,
        control_taps_modules=False, control_taps_phase=False,
        control_remote_voltage=False, distributed_slack=False,
        initialize_angles=True, use_stored_guess=False,
    )


def build_initialized_problem():
    from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
    from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
    from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
    from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions

    grid = FileOpen(file_name=str(DATA / "wscc_rms.veragrid")).open()
    power_flow = PowerFlowDriver(grid, power_flow_options())
    power_flow.run()
    if not power_flow.results.converged:
        raise RuntimeError("RMS power flow did not converge")
    problem = RmsProblemDae(grid, RmsOptions(time_step=0.001), power_flow.results)
    problem.set_events_group(RmsEventsGroup("full_dynamic_network_benchmark"))
    vector = problem.get_x0()
    nx = len(problem.state_vars)
    state_index = {str(variable): index for index, variable in enumerate(problem.state_vars)}
    buses = {int(bus.name.removeprefix("Bus")): index for index, bus in enumerate(grid.buses)}

    for branch, line in enumerate(grid.lines):
        f = grid.buses.index(line.bus_from)
        voltage = power_flow.results.voltage[f]
        vq, vd = voltage.real, -voltage.imag
        power = power_flow.results.Sf[branch] / grid.Sbase
        denominator = vq * vq + vd * vd
        total_iq = (power.real * vq - power.imag * vd) / denominator
        total_id = (power.real * vd + power.imag * vq) / denominator
        bus_f = int(line.bus_from.name.removeprefix("Bus"))
        bus_t = int(line.bus_to.name.removeprefix("Bus"))
        name = f"NET.{min(bus_f, bus_t)}{max(bus_f, bus_t)}"
        vector[state_index[f"{name}.iq"]] = total_iq - line.B * vd / 2.0
        vector[state_index[f"{name}.id"]] = total_id + line.B * vq / 2.0

    for load_number, (bus_number, p_mw, q_mvar) in enumerate(STAMP_LOADS, 1):
        voltage = power_flow.results.voltage[buses[bus_number]]
        vq, vd = voltage.real, -voltage.imag
        p, q = p_mw / grid.Sbase, q_mvar / grid.Sbase
        denominator = vq * vq + vd * vd
        conductance = p / denominator
        vector[state_index[f"Load{load_number}.ilq"]] = ((p * vq - q * vd) / denominator
                                                          - conductance * vq)
        vector[state_index[f"Load{load_number}.ild"]] = ((p * vd + q * vq) / denominator
                                                          - conductance * vd)
    for bus_number, bus_index in buses.items():
        voltage = power_flow.results.voltage[bus_index]
        vector[state_index[f"STAMP bus capacitor {bus_number}.vc_q"]] = voltage.real
        vector[state_index[f"STAMP bus capacitor {bus_number}.vc_d"]] = -voltage.imag

    solved = root(
        lambda y: problem.rhs_algebraic(
            np.r_[vector[:nx], y], np.zeros_like(vector)),
        vector[nx:].copy(),
    )
    if not solved.success:
        raise RuntimeError(solved.message)
    vector[nx:] = solved.x
    return problem, vector


def matrices(problem, vector):
    dx = np.zeros(problem.get_diff_var_number())
    step = problem.get_dt_value()
    fx = problem.get_j11(vector, dx, step).toarray()
    fy = problem.get_j12(vector, dx, step).toarray()
    gx = problem.get_j21(vector, dx, step).toarray()
    gy = problem.get_j22(vector, dx, step).toarray()
    reduced = fx - fy @ np.linalg.solve(gy, gx)
    return reduced


def main() -> None:
    setup_start = perf_counter() if MEASURE_TIME else None
    problem, vector = build_initialized_problem()
    matrix = matrices(problem, vector)
    setup_seconds = perf_counter() - setup_start if MEASURE_TIME else None
    modes = la.eigvals(matrix)
    reference = np.loadtxt(DATA / "stamp_rms_eigenvalues.csv", delimiter=",",
                           skiprows=1, usecols=(1, 2))
    stamp = reference[:, 0] + 1j * reference[:, 1]
    rows, columns = linear_sum_assignment(np.abs(stamp[:, None] - modes[None, :]))
    distances = np.abs(stamp[rows] - modes[columns])
    print(f"STAMP modes: {len(stamp)}; VeraGrid modes: {len(modes)}")
    print(f"Median modal distance: {np.median(distances):.6g} s^-1")
    print(f"Maximum modal distance: {np.max(distances):.6g} s^-1")
    print(f"Within 1e-5 s^-1: {len(modes) == len(stamp) == 88 and np.max(distances) < 1e-5}")
    if MEASURE_TIME:
        print(f"VeraGrid initialization and matrix construction: {setup_seconds:.9g} s")

        # Match the scope of STAMP's saved eig(A) samples: the initialized matrix
        # is ready before the timer starts. This does not time model construction.
        la.eigvals(matrix)
        timings = []
        for _ in range(TIMING_RUNS):
            start = perf_counter()
            la.eigvals(matrix)
            timings.append(perf_counter() - start)
        print(f"VeraGrid dense eig median ({TIMING_RUNS} warmed runs): "
              f"{np.median(timings):.9g} s")

        with (DATA / "stamp_rms_runtime_multivac.csv").open(
                newline="", encoding="utf-8") as stream:
            samples = list(csv.DictReader(stream))
        if not samples or any(row["implementation"] != "STAMP" for row in samples):
            raise ValueError("Invalid STAMP runtime reference samples")
        stamp_timings = [float(row["eig_seconds"]) for row in samples]
        print(f"STAMP dense eig reference median ({len(stamp_timings)} Multivac runs): "
              f"{np.median(stamp_timings):.9g} s")
        print("Timing comparison: saved STAMP samples are from Multivac; "
              "VeraGrid samples are from this run. No cross-machine speed ratio is inferred.")


if __name__ == "__main__":
    main()
