# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construct the IEEE14 network and its benchmark RMS models."""

from __future__ import annotations

from importlib.machinery import ModuleSpec
from importlib.util import find_spec
from pathlib import Path

import pandas as pd

from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.buses.shunt_template import get_shunt_template
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import get_transformer2w_rms
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
import VeraGridEngine.api as gce

from benchmarks.dynamics_andes.small_signal.IEEE14.ieee14_dynamic_model import get_ieee14_genrou_rms_template


def _get_andes_ieee14_full_xlsx_path() -> Path:
    """Return the ANDES IEEE14 full benchmark workbook path.

    :return: Workbook path in the active ANDES installation.
    """
    case_directory: Path = _get_andes_ieee14_case_directory()
    return case_directory / "ieee14_full.xlsx"


def _get_andes_ieee14_case_directory() -> Path:
    """Locate the benchmark data without importing the ANDES runtime.

    :return: IEEE14 case directory in the active ANDES installation.
    :raises FileNotFoundError: If the ANDES package cannot be located.
    """
    # Resolve the installed package so case paths work across operating systems.
    package_spec: ModuleSpec | None = find_spec("andes")
    if package_spec is None or package_spec.origin is None:
        raise FileNotFoundError("The IEEE14 benchmark requires the ANDES case data in the active Python environment.")
    else:
        return Path(package_spec.origin).resolve().parent / "cases" / "ieee14"


def _build_ieee14_network_from_andes_case() -> gce.MultiCircuit:
    """Build the IEEE14 network explicitly from the ANDES full benchmark workbook."""
    workbook_path: Path = _get_andes_ieee14_full_xlsx_path()
    workbook: pd.ExcelFile = pd.ExcelFile(workbook_path)
    grid: gce.MultiCircuit = gce.MultiCircuit()

    bus_df: pd.DataFrame = pd.read_excel(workbook, sheet_name="Bus")
    slack_df: pd.DataFrame = pd.read_excel(workbook, sheet_name="Slack")
    pv_df: pd.DataFrame = pd.read_excel(workbook, sheet_name="PV")
    pq_df: pd.DataFrame = pd.read_excel(workbook, sheet_name="PQ")
    shunt_df: pd.DataFrame = pd.read_excel(workbook, sheet_name="Shunt")
    line_df: pd.DataFrame = pd.read_excel(workbook, sheet_name="Line")

    slack_bus_numbers: set[int] = set()
    slack_row_count: int = len(slack_df.index)
    slack_row_index: int = 0
    while slack_row_index < slack_row_count:
        slack_bus_numbers.add(int(slack_df.iloc[slack_row_index]["bus"]))
        slack_row_index += 1

    bus_map: dict[int, Bus] = dict()
    bus_row_count: int = len(bus_df.index)
    bus_row_index: int = 0
    while bus_row_index < bus_row_count:
        bus_row = bus_df.iloc[bus_row_index]
        bus_number: int = int(bus_row["idx"])
        bus = Bus(
            name=str(bus_row["name"]),
            Vnom=float(bus_row["Vn"]),
            vmin=float(bus_row["vmin"]),
            vmax=float(bus_row["vmax"]),
            Vm0=float(bus_row["v0"]),
            Va0=float(bus_row["a0"]),
            is_slack=bus_number in slack_bus_numbers,
        )
        grid.add_bus(bus)
        bus_map[bus_number] = bus
        bus_row_index += 1

    slack_generator_count: int = len(slack_df.index)
    slack_generator_index: int = 0
    while slack_generator_index < slack_generator_count:
        slack_row = slack_df.iloc[slack_generator_index]
        generator = Generator(
            name=str(slack_row["name"]),
            P=float(slack_row["p0"]) * 100.0,
            Q=float(slack_row["q0"]) * 100.0,
            vset=float(slack_row["v0"]),
            Snom=float(slack_row["Sn"]),
            Pmax=float(slack_row["pmax"]) * 100.0,
            Pmin=float(slack_row["pmin"]) * 100.0,
            # ANDES PFlow does not enforce the static-generator Q limits in this
            # benchmark. Wide limits prevent VeraGrid's result allocator from
            # clipping the Q value later consumed by GENROU initialization.
            Qmax=999900.0,
            Qmin=-999900.0,
            r1=float(slack_row["ra"]),
            x1=float(slack_row["xs"]),
            freq=60.0,
        )
        grid.add_generator(bus=bus_map[int(slack_row["bus"])], api_obj=generator)
        slack_generator_index += 1

    pv_generator_count: int = len(pv_df.index)
    pv_generator_index: int = 0
    while pv_generator_index < pv_generator_count:
        pv_row = pv_df.iloc[pv_generator_index]
        generator = Generator(
            name=str(pv_row["name"]),
            P=float(pv_row["p0"]) * 100.0,
            Q=float(pv_row["q0"]) * 100.0,
            vset=float(pv_row["v0"]),
            Snom=float(pv_row["Sn"]),
            Pmax=float(pv_row["pmax"]) * 100.0,
            Pmin=float(pv_row["pmin"]) * 100.0,
            # Match the effective ANDES PFlow configuration (no Q-limit
            # enforcement) so the dynamic seed uses the solved generator Q.
            Qmax=999900.0,
            Qmin=-999900.0,
            r1=float(pv_row["ra"]),
            x1=float(pv_row["xs"]),
            freq=60.0,
        )
        grid.add_generator(bus=bus_map[int(pv_row["bus"])], api_obj=generator)
        pv_generator_index += 1

    load_count: int = len(pq_df.index)
    load_index: int = 0
    while load_index < load_count:
        load_row = pq_df.iloc[load_index]
        load = Load(
            name=str(load_row["name"]),
            P=float(load_row["p0"]) * 100.0,
            Q=float(load_row["q0"]) * 100.0,
        )
        grid.add_load(bus=bus_map[int(load_row["bus"])], api_obj=load)
        load_index += 1

    shunt_count: int = len(shunt_df.index)
    shunt_index: int = 0
    while shunt_index < shunt_count:
        shunt_row = shunt_df.iloc[shunt_index]
        shunt = Shunt(
            name=str(shunt_row["name"]),
            G=float(shunt_row["g"]) * 100.0,
            B=float(shunt_row["b"]) * 100.0,
        )
        grid.add_shunt(bus=bus_map[int(shunt_row["bus"])], api_obj=shunt)
        shunt_index += 1

    line_count: int = len(line_df.index)
    line_index: int = 0
    while line_index < line_count:
        line_row = line_df.iloc[line_index]
        if float(line_row["trans"]) != 0.0:
            transformer = Transformer2W(
                name=str(line_row["name"]),
                bus_from=bus_map[int(line_row["bus1"])],
                bus_to=bus_map[int(line_row["bus2"])],
                HV=float(line_row["Vn1"]),
                LV=float(line_row["Vn2"]),
                nominal_power=float(line_row["Sn"]),
                rate=float(line_row["Sn"]),
                r=float(line_row["r"]),
                x=float(line_row["x"]),
                g=float(line_row["g"]),
                b=float(line_row["b"]),
                tap_module=float(line_row["tap"]),
                tap_phase=float(line_row["phi"]),
            )
            grid.add_transformer2w(transformer)
        else:
            line = Line(
                name=str(line_row["name"]),
                bus_from=bus_map[int(line_row["bus1"])],
                bus_to=bus_map[int(line_row["bus2"])],
                r=float(line_row["r"]),
                x=float(line_row["x"]),
                b=float(line_row["b"]),
                rate=float(line_row["Sn"]),
            )
            grid.add_line(line)
        line_index += 1

    return grid


def _assign_ieee14_rms_models(grid: gce.MultiCircuit) -> None:
    """Assign ANDES-aligned RMS models to the IEEE14 grid.

    :param grid: VeraGrid network.
    :return: None.
    """
    bus_list: list[object] = list(grid.buses)
    for bus in bus_list:
        initialize_bus_rms(bus, vf=grid.var_factory)

    generator_count: int = len(grid.generators)
    generator_index: int = 0
    while generator_index < generator_count:
        generator = grid.generators[generator_index]
        generator_block = get_ieee14_genrou_rms_template(
            vfactory=grid.var_factory,
            generator_index=generator_index,
            name=f"ieee14_gen_{generator_index + 1}",
        ).block

        grid.var_factory.add_connections(
            list((generator_block.in_vars[0],)),
            list((generator.bus.rms_model.out_vars[0],)),
        )
        grid.var_factory.add_connections(
            list((generator_block.in_vars[1],)),
            list((generator.bus.rms_model.out_vars[1],)),
        )

        generator_wrapper = generator_block

        generator.rms_model = generator_wrapper
        generator_index += 1

    line_count: int = len(grid.lines)
    line_index: int = 0
    while line_index < line_count:
        line = grid.lines[line_index]
        line_model = get_line_rms_template(grid.var_factory, name=f"ieee14_line_{line_index + 1}").block
        set_rms_model(device=line, model=line_model, var_factory=grid.var_factory)
        line_index += 1

    transformer_count: int = len(grid.transformers2w)
    transformer_index: int = 0
    while transformer_index < transformer_count:
        transformer = grid.transformers2w[transformer_index]
        # IEEE14 has non-unity taps, so its RMS network needs the transformer
        # equations rather than the symmetric line approximation used by Kundur.
        transformer_model = get_transformer2w_rms(grid.var_factory).block
        transformer_model.name = f"ieee14_transformer_{transformer_index + 1}"
        set_rms_model(device=transformer, model=transformer_model, var_factory=grid.var_factory)
        transformer_index += 1

    load_count: int = len(grid.loads)
    load_index: int = 0
    while load_index < load_count:
        load = grid.loads[load_index]
        load_model = get_load_rms_template(grid.var_factory, name=f"ieee14_load_{load_index + 1}").block
        set_rms_model(device=load, model=load_model, var_factory=grid.var_factory)
        load_index += 1

    shunt_count: int = len(grid.shunts)
    shunt_index: int = 0
    while shunt_index < shunt_count:
        shunt = grid.shunts[shunt_index]
        shunt_model = get_shunt_template(
            grid.var_factory,
            name=f"ieee14_shunt_{shunt_index + 1}",
            phasor=False,
        ).block
        shunt_vm = shunt_model.E(VarPowerFlowReferenceType.Vm)
        shunt_p = shunt_model.E(VarPowerFlowReferenceType.P)
        shunt_q = shunt_model.E(VarPowerFlowReferenceType.Q)
        shunt_g = shunt_model.api_obj_mapping[ParamPowerFlowReferenceType.g]
        shunt_b = shunt_model.api_obj_mapping[ParamPowerFlowReferenceType.b]
        shunt_model.event_dict[shunt_g] = grid.var_factory.add_const(
            value=shunt.G / grid.Sbase,
            name="g",
        )
        shunt_model.event_dict[shunt_b] = grid.var_factory.add_const(
            value=shunt.B / grid.Sbase,
            name="b",
        )
        shunt_model.init_eqs[shunt_p] = -shunt_g * shunt_vm ** 2
        shunt_model.init_eqs[shunt_q] = shunt_b * shunt_vm ** 2
        set_rms_model(device=shunt, model=shunt_model, var_factory=grid.var_factory)
        shunt_index += 1



def build_ieee14_rms_benchmark_grid() -> gce.MultiCircuit:
    """Build the IEEE14 RMS-ready benchmark grid.

    :return: RMS-ready grid.
    """
    grid: gce.MultiCircuit = _build_ieee14_network_from_andes_case()
    _assign_ieee14_rms_models(grid)
    return grid
