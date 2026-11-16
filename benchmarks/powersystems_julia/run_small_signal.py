"""Run the PowerSimulationsDynamics.jl RMS modal comparisons."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
from scipy.optimize import linear_sum_assignment


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
DATA = SRC / "tests" / "data" / "powersystems_julia"
CASES = ("2_bus", "3_bus", "ieee9", "wecc_240")
# The compact WECC port targets the stability-relevant right edge.  Its full
# spectrum is still calculated and its total dimension is reported.
REAL_PART_MINIMUM = {"wecc_240": -0.1}

# Direct-run defaults. Edit these values to configure ``python run_small_signal.py``
# without command-line arguments. Command-line options override them.
DEFAULT_CASES = CASES
DEFAULT_SSA_VARIANT = "dense"  # "dense", "sparse", or "both"
DEFAULT_SPARSE_MODES = 100
MEASURE_TIME = False
TIMING_RUNS = 20

from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_driver import (
    SmallSignalStabilityRmsDriver,
)
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_options import (
    RmsSmallSignalStabilityOptions,
)
from VeraGridEngine.enumerations import BranchImpedanceMode, DeviceType, SolverType


def prepare_wecc_static_power_flow(grid) -> dict[object, tuple[float, float]]:
    """Restore the static load convention used to solve the WECC RAW case."""
    admittances = {}
    with (DATA / "wecc_240_static_loads.csv").open(
            newline="", encoding="utf-8") as stream:
        static_loads = {row["name"]: (float(row["P"]), float(row["Q"]))
                        for row in csv.DictReader(stream)}
    for load in grid.loads:
        values = {parameter.name: value.value
                  for parameter, value in load.rms_model.event_dict.items()}
        conductance = float(values["zload_conductance"])
        susceptance = float(values["zload_susceptance"])
        admittances[load] = conductance, susceptance
        load.P, load.Q = static_loads[load.name]
    return admittances


def seed_wecc_rms_operating_point(grid, results, admittances) -> None:
    """Convert solved WECC values to the per-unit RMS model convention."""
    bus_index = grid.get_bus_index_dict()
    for load, (conductance, susceptance) in admittances.items():
        vm = abs(results.voltage[bus_index[load.bus]])
        load.P = -conductance * vm**2
        load.Q = -susceptance * vm**2
    bus_index = grid.get_bus_index_dict()
    powers_from = []
    powers_to = []
    for branch in grid.get_branches_iter(
            add_vsc=False, add_hvdc=False, add_switch=True):
        if not branch.active:
            powers_from.append(0.0j)
            powers_to.append(0.0j)
            continue
        voltage_from = results.voltage[bus_index[branch.bus_from]]
        voltage_to = results.voltage[bus_index[branch.bus_to]]
        admittance = 1 / complex(branch.R, branch.X)
        if branch.device_type == DeviceType.Transformer2WDevice:
            virtual_from, virtual_to = branch.get_virtual_taps()
            tap = branch.tap_module
            phase = branch.tap_phase
            shunt = complex(branch.G, branch.B) / 2
            current_from = ((admittance + shunt) * voltage_from /
                            (tap * virtual_from)**2 - admittance * voltage_to /
                            (tap * virtual_from * virtual_to) * np.exp(1j * phase))
            current_to = ((admittance + shunt) * voltage_to / virtual_to**2 -
                          admittance * voltage_from /
                          (tap * virtual_from * virtual_to) * np.exp(-1j * phase))
        else:
            current_from = ((voltage_from - voltage_to) * admittance +
                            1j * branch.B * voltage_from / 2)
            current_to = ((voltage_to - voltage_from) * admittance +
                          1j * branch.B * voltage_to / 2)
        powers_from.append(voltage_from * np.conj(current_from))
        powers_to.append(voltage_to * np.conj(current_to))
    results.Sf = np.asarray(powers_from, dtype=complex) * grid.Sbase
    results.St = np.asarray(powers_to, dtype=complex) * grid.Sbase


def power_flow_options() -> PowerFlowOptions:
    return PowerFlowOptions(
        solver_type=SolverType.NR,
        retry_with_other_methods=False,
        initialize_with_existing_solution=True,
        tolerance=1e-8,
        max_iter=50,
        control_q=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=False,
        apply_temperature_correction=False,
        branch_impedance_tolerance_mode=BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=False,
        initialize_angles=True,
        generate_report=False,
    )


def read_modes(path: Path) -> np.ndarray:
    with path.open(newline="", encoding="utf-8") as stream:
        return np.asarray([
            complex(float(row["real"]), float(row["imag"]))
            for row in csv.DictReader(stream)
        ])


def run_case(name: str, variant: str = "dense",
             sparse_modes: int = 50) -> dict[str, object]:
    setup_start = perf_counter() if MEASURE_TIME else None
    grid = FileOpen(file_name=str(DATA / f"{name}.veragrid")).open()
    wecc_admittances = (prepare_wecc_static_power_flow(grid)
                        if name == "wecc_240" else None)
    pf_options = power_flow_options()
    if name == "wecc_240":
        pf_options.retry_with_other_methods = True
        pf_options.max_iter = 100
        pf_options.control_Q = True
    power_flow = PowerFlowDriver(grid, pf_options)
    power_flow.run()
    if not power_flow.results.converged:
        raise RuntimeError(f"{name}: power flow did not converge")
    if wecc_admittances is not None:
        seed_wecc_rms_operating_point(grid, power_flow.results,
                                      wecc_admittances)

    driver = SmallSignalStabilityRmsDriver(
        grid=grid,
        rms_options=RmsOptions(
            time_step=0.001, simulation_time=10.0,
            tolerance=1e-6, max_iter=1000, verbose=0),
        sss_options=RmsSmallSignalStabilityOptions(
            k=None if variant == "dense" else sparse_modes,
            ss_assessment_time=0.0),
        pf_results=power_flow.results,
    )
    modal_dimension = (driver.problem.get_states_number() +
                       driver.problem.get_diff_var_number())
    if variant == "sparse" and driver.k >= modal_dimension - 1:
        raise ValueError(
            f"{name}: sparse SSA requires fewer than {modal_dimension - 1} "
            f"requested modes; received {driver.k}"
        )
    setup_seconds = perf_counter() - setup_start if MEASURE_TIME else None
    initial = driver.problem.get_x0()
    derivatives = np.zeros_like(initial)
    state_residual = float(np.max(np.abs(
        driver.problem.rhs_state(initial, derivatives))))
    algebraic_residual = float(np.max(np.abs(
        driver.problem.rhs_algebraic(initial, derivatives))))
    driver.run()
    veragrid = np.asarray(driver.results.eigenvalues, dtype=complex).reshape(-1)
    timings = []
    if MEASURE_TIME:
        for _ in range(TIMING_RUNS):
            start = perf_counter()
            driver.run()
            timings.append(perf_counter() - start)
    reference = read_modes(DATA / f"{name}_eigenvalues.csv")
    if variant == "dense":
        real_minimum = REAL_PART_MINIMUM.get(name)
        comparison_pool = (reference if real_minimum is None else
                           reference[reference.real >= real_minimum])
        reference_indices, veragrid_indices = linear_sum_assignment(
            np.abs(comparison_pool[:, None] - veragrid[None, :]))
        matched_reference = comparison_pool[reference_indices]
    else:
        real_minimum = None
        veragrid_indices, reference_indices = linear_sum_assignment(
            np.abs(veragrid[:, None] - reference[None, :]))
        matched_reference = reference[reference_indices]
    matched_veragrid = veragrid[veragrid_indices]
    distances = np.abs(matched_reference - matched_veragrid)
    rightmost = int(np.argmax(matched_reference.real))
    julia_ssa_seconds = None
    if MEASURE_TIME and variant == "dense":
        with (DATA / "julia_small_signal_timings.csv").open(
                newline="", encoding="utf-8") as stream:
            julia_samples = [row for row in csv.DictReader(stream)
                             if row["case"] == name and int(row["repetition"]) == 2]
        if len(julia_samples) != 1:
            raise ValueError(f"Expected one after-first-run Julia SSA timing for {name}")
        julia_ssa_seconds = float(julia_samples[0]["eigen_seconds"])
    return {
        "case": name,
        "variant": variant,
        "reference_modes": len(reference),
        "veragrid_modes": len(veragrid),
        "state_residual": state_residual,
        "algebraic_residual": algebraic_residual,
        "median_distance": float(np.median(distances)),
        "maximum_distance": float(np.max(distances)),
        "compared_modes": len(distances),
        "comparison_real_minimum": real_minimum,
        "rightmost_reference": matched_reference[rightmost],
        "rightmost_veragrid": matched_veragrid[rightmost],
        "rightmost_distance": float(distances[rightmost]),
        "veragrid_setup_seconds": setup_seconds,
        "veragrid_ssa_median_seconds": float(np.median(timings)) if MEASURE_TIME else None,
        "julia_reference_ssa_seconds": julia_ssa_seconds,
        "veragrid_to_julia_ssa_ratio": (
            float(np.median(timings)) / julia_ssa_seconds
            if MEASURE_TIME and variant == "dense" else None),
        "timing_samples": tuple(timings),
        "matches": tuple(
            (reference_value, veragrid_value, float(distance))
            for reference_value, veragrid_value, distance in
            zip(matched_reference, matched_veragrid, distances)
        ),
    }


def print_result(result: dict[str, object]) -> None:
    print(f"\n{result['case']} [{result['variant']}]")
    print(f"  modes: Julia={result['reference_modes']}, "
          f"VeraGrid={result['veragrid_modes']}")
    if result["comparison_real_minimum"] is not None:
        print(f"  comparison window: {result['compared_modes']} Julia modes with "
              f"real(lambda) >= {result['comparison_real_minimum']:.6g} s^-1")
    print(f"  initial residuals: state={result['state_residual']:.6g}, "
          f"algebraic={result['algebraic_residual']:.6g}")
    print(f"  modal distance: median={result['median_distance']:.6g} s^-1, "
          f"maximum={result['maximum_distance']:.6g} s^-1")
    print(f"  rightmost: Julia={result['rightmost_reference']:+.9g}, "
          f"VeraGrid={result['rightmost_veragrid']:+.9g}, "
          f"distance={result['rightmost_distance']:.6g} s^-1")
    if MEASURE_TIME:
        print(f"  VeraGrid setup: {result['veragrid_setup_seconds']:.6g} s")
        print(f"  VeraGrid SSA median ({len(result['timing_samples'])} after-first-run measurements): "
              f"{result['veragrid_ssa_median_seconds']:.6g} s")
        if result["julia_reference_ssa_seconds"] is None:
            print("  Julia SSA reference: unavailable for this case")
        else:
            print(f"  Julia SSA reference (one after-first-run source measurement): "
                  f"{result['julia_reference_ssa_seconds']:.6g} s")
            print(f"  VeraGrid/Julia SSA time ratio: "
                  f"{result['veragrid_to_julia_ssa_ratio']:.6g}x")
    print("  largest assigned distances:")
    matches = sorted(result["matches"], key=lambda item: item[2], reverse=True)
    for reference, veragrid, distance in matches[:min(5, len(matches))]:
        print(f"    Julia={reference:+.9g}, VeraGrid={veragrid:+.9g}, "
              f"distance={distance:.6g} s^-1")


def write_summary(path: Path, results: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "case", "variant", "reference_modes", "veragrid_modes", "compared_modes",
        "comparison_real_minimum", "state_residual",
        "algebraic_residual", "median_distance", "maximum_distance",
        "rightmost_reference_real", "rightmost_reference_imag",
        "rightmost_veragrid_real", "rightmost_veragrid_imag",
        "rightmost_distance",
        "veragrid_setup_seconds", "veragrid_ssa_median_seconds",
        "julia_reference_ssa_seconds", "veragrid_to_julia_ssa_ratio",
    )
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for result in results:
            reference = complex(result["rightmost_reference"])
            veragrid = complex(result["rightmost_veragrid"])
            writer.writerow({
                **{field: result[field] for field in fields[:10]},
                "rightmost_reference_real": reference.real,
                "rightmost_reference_imag": reference.imag,
                "rightmost_veragrid_real": veragrid.real,
                "rightmost_veragrid_imag": veragrid.imag,
                "rightmost_distance": result["rightmost_distance"],
                "veragrid_setup_seconds": result["veragrid_setup_seconds"],
                "veragrid_ssa_median_seconds": result["veragrid_ssa_median_seconds"],
                "julia_reference_ssa_seconds": result["julia_reference_ssa_seconds"],
                "veragrid_to_julia_ssa_ratio": result["veragrid_to_julia_ssa_ratio"],
            })


def main() -> None:
    global MEASURE_TIME, TIMING_RUNS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, action="append",
                        help="Run one or more cases; default: all")
    parser.add_argument("--output", type=Path,
                        help="Optional CSV summary path")
    parser.add_argument("--measure-time", action="store_true", default=MEASURE_TIME,
                        help="Time after-first-run VeraGrid eigenanalysis runs and compare with Julia")
    parser.add_argument("--timing-runs", type=int, default=TIMING_RUNS,
                        help=f"Number of after-first-run VeraGrid timing runs; default: {TIMING_RUNS}")
    parser.add_argument("--ssa-variant", choices=("dense", "sparse", "both"),
                        default=DEFAULT_SSA_VARIANT,
                        help=f"SSA solver variant; default: {DEFAULT_SSA_VARIANT}")
    parser.add_argument("--sparse-modes", type=int, default=DEFAULT_SPARSE_MODES,
                        help=("Number of modes requested from sparse SSA; "
                              f"default: {DEFAULT_SPARSE_MODES}"))
    arguments = parser.parse_args()
    if arguments.timing_runs < 1:
        parser.error("--timing-runs must be at least 1")
    if arguments.sparse_modes < 1:
        parser.error("--sparse-modes must be at least 1")
    MEASURE_TIME = arguments.measure_time
    TIMING_RUNS = arguments.timing_runs
    variants = (("dense", "sparse") if arguments.ssa_variant == "both"
                else (arguments.ssa_variant,))
    selected_cases = tuple(arguments.case) if arguments.case else DEFAULT_CASES
    results = [run_case(name, variant, arguments.sparse_modes)
               for name in selected_cases
               for variant in variants]
    for result in results:
        print_result(result)
    if arguments.output:
        write_summary(arguments.output, results)
        print(f"\nCSV written to {arguments.output.resolve()}")
    if MEASURE_TIME and arguments.ssa_variant == "both":
        for name in selected_cases:
            dense = next(result for result in results
                         if result["case"] == name and result["variant"] == "dense")
            sparse = next(result for result in results
                          if result["case"] == name and result["variant"] == "sparse")
            ratio = (dense["veragrid_ssa_median_seconds"] /
                     sparse["veragrid_ssa_median_seconds"])
            print(f"{name}: sparse/dense VeraGrid speedup={ratio:.6g}x")
    if MEASURE_TIME:
        print("VeraGrid reports the median of the requested after-first-run "
              "measurements. The saved Julia timing applies to dense SSA only.")


if __name__ == "__main__":
    main()
