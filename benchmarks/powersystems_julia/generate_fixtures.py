"""Export the PowerSimulationsDynamics.jl comparison grids to VeraGrid files.

This authoring script expects the sibling ``power systems julia`` repository
on ``PYTHONPATH``. Benchmark runs use only the committed files it produces.
"""

from __future__ import annotations

from pathlib import Path
import csv
import shutil

from VeraGridEngine.IO.file_save import FileSave
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model

import run_veragrid_ieee9_powersystems_models as ieee9
import run_veragrid_omib_powersystems_models as omib
import run_veragrid_three_bus_powersystems_models as three_bus
import wecc240_fixture as wecc240
from veragrid_templates.powersystems_small_case_generators import (
    get_thevenin_source_rms_template,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT.parent / "power systems julia"
DATA = ROOT / "src" / "tests" / "data" / "powersystems_julia"


def normalize_three_bus_impedance_loads(grid) -> None:
    """Match PSD's ZIP-load admittance normalization at the PF voltage.

    PowerSimulationsDynamics evaluates an impedance term ``P + jQ`` as an
    admittance divided by the squared power-flow voltage magnitude.  All three
    buses in this case have a fixed voltage-magnitude target, so apply that
    normalization to both the static shunts and their saved RMS parameters.
    """
    voltage_targets = {
        item.bus: item.Vm for item in grid.external_grids
    }
    voltage_targets.update({
        item.bus: item.Vset for item in grid.generators
    })
    for shunt in grid.shunts:
        scale = voltage_targets[shunt.bus] ** 2
        shunt.G /= scale
        shunt.B /= scale
        for parameter, value in shunt.rms_model.event_dict.items():
            if parameter.name == "g":
                value.value = shunt.G / grid.Sbase
            elif parameter.name == "b":
                value.value = shunt.B / grid.Sbase


def restore_two_bus_thevenin_source(grid) -> None:
    """Use the finite source impedance stored by the Julia OMIB case."""
    source = grid.external_grids[0]
    model = get_thevenin_source_rms_template(
        grid.var_factory,
        name="OMIB PowerSystems Thevenin source",
        resistance=0.0,
        reactance=5.0e-6,
    ).block
    set_rms_model(source, model, grid.var_factory)


def set_external_grid_operating_point(grid, power_flow) -> None:
    """Persist the solved slack-device P/Q used by RMS initialization."""
    if not grid.external_grids:
        return
    source = grid.external_grids[0]
    slack = source.bus
    if len(grid.buses) == 2:
        index = grid.get_bus_index_dict()[slack]
        source.P = float(-power_flow.results.Sbus[index].real)
        source.Q = float(-power_flow.results.Sbus[index].imag)
        return

    flow = 0j
    for index, branch in enumerate(grid.get_branches_iter(
            add_vsc=False, add_hvdc=False, add_switch=True)):
        if branch.bus_from is slack:
            flow += power_flow.results.Sf[index]
        if branch.bus_to is slack:
            flow += power_flow.results.St[index]
    vm = abs(power_flow.results.voltage[grid.get_bus_index_dict()[slack]])
    shunt = sum(complex(-item.G, item.B) * vm**2
                for item in grid.shunts if item.bus is slack)
    source.P = float(-(flow - shunt).real)
    source.Q = float(-(flow - shunt).imag)


def export_case(name: str, grid) -> None:
    power_flow = PowerFlowDriver(grid, ieee9.build_power_flow_options())
    power_flow.run()
    if not power_flow.results.converged:
        raise RuntimeError(f"{name}: power flow did not converge")
    set_external_grid_operating_point(grid, power_flow)
    path = DATA / f"{name}.veragrid"
    logger = FileSave(circuit=grid, file_name=str(path)).save()
    if logger.has_errors():
        raise RuntimeError(f"Failed to save {path}: {logger}")
    print(path)


def main() -> None:
    if not SOURCE_ROOT.is_dir():
        raise FileNotFoundError(f"Source checkout not found: {SOURCE_ROOT}")
    DATA.mkdir(parents=True, exist_ok=True)
    two_bus_grid = omib.build_grid()
    restore_two_bus_thevenin_source(two_bus_grid)
    export_case("2_bus", two_bus_grid)
    three_bus_grid = three_bus.build_grid()
    normalize_three_bus_impedance_loads(three_bus_grid)
    export_case("3_bus", three_bus_grid)
    export_case("ieee9", ieee9.build_ieee9_grid(ieee9.default_ieee9_raw_path()))
    wecc_grid = wecc240.build_prepared_grid()
    export_case("wecc_240", wecc_grid)
    with (DATA / "wecc_240_static_loads.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("name", "P", "Q"))
        writer.writerows((name, p, q) for name, (p, q) in
                         sorted(wecc240.build_prepared_grid.static_load_pq.items()))
    for case in ("2_bus", "3_bus", "ieee9", "wecc_240"):
        source = SOURCE_ROOT / "results" / case / "small_signal_eigenvalues.csv"
        destination = DATA / f"{case}_eigenvalues.csv"
        shutil.copyfile(source, destination)
        print(destination)
    timing_source = SOURCE_ROOT / "results/benchmarks/powersystems_small_signal_timings.csv"
    timing_destination = DATA / "julia_small_signal_timings.csv"
    wecc_timing_rows = []
    if timing_destination.exists():
        with timing_destination.open(newline="", encoding="utf-8") as stream:
            wecc_timing_rows = [row for row in csv.DictReader(stream)
                                if row["case"] == "wecc_240"]
    shutil.copyfile(timing_source, timing_destination)
    if wecc_timing_rows:
        with timing_destination.open("a", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=wecc_timing_rows[0].keys())
            writer.writerows(wecc_timing_rows)
    print(timing_destination)


if __name__ == "__main__":
    main()
