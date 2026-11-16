# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""IEEE14 RMS case from the ANDES full workbook, shared by the RMS solver tests."""

from __future__ import annotations

from importlib.machinery import ModuleSpec
from importlib.util import find_spec
from pathlib import Path
from typing import Any, List

import numpy as np
import pandas as pd

import VeraGridEngine.api as gce
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.buses.shunt_template import get_shunt_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_esst3a_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_exst1_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_genrou_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_tgov1_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Esst3aRmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Exst1RmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import GenrouExciterType
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import GenrouRmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import get_complete_genrou_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Tgov1RmsParameters
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import get_transformer2w_rms
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model


def _get_genrou_parameters() -> tuple[GenrouRmsParameters, ...]:
    """Return GENROU parameters in IEEE14 generator order.

    :return: Five IEEE14 GENROU parameter sets.
    """
    return (
        GenrouRmsParameters(60.0, 0.0, 8.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.23, 0.8, 0.23, 6.5, 0.06, 0.2, 0.05),
        GenrouRmsParameters(60.0, 0.0, 13.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.28, 0.8, 0.28, 6.5, 0.06, 0.2, 0.05),
        GenrouRmsParameters(60.0, 0.0, 10.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.34, 0.8, 0.34, 6.5, 0.06, 0.2, 0.05),
        GenrouRmsParameters(60.0, 0.0, 10.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.28, 0.8, 0.28, 6.5, 0.06, 0.2, 0.05),
        GenrouRmsParameters(60.0, 0.0, 10.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.34, 0.8, 0.34, 6.5, 0.06, 0.2, 0.05),
    )


def _get_tgov1_parameters() -> tuple[Tgov1RmsParameters, ...]:
    """Return TGOV1 parameters in IEEE14 generator order.

    :return: Five IEEE14 TGOV1 parameter sets.
    """
    return (
        Tgov1RmsParameters(1.0, 0.05, 1.05, 0.3, 0.05, 1.0, 2.1, 0.0),
        Tgov1RmsParameters(1.0, 0.05, 1.2, 0.0, 0.1, 1.0, 2.1, 0.0),
        Tgov1RmsParameters(1.0, 0.05, 1.2, 0.0, 0.1, 1.0, 2.1, 0.0),
        Tgov1RmsParameters(1.0, 0.05, 1.05, 0.3, 0.05, 1.0, 2.1, 0.0),
        Tgov1RmsParameters(1.0, 0.05, 1.05, 0.3, 0.05, 1.0, 2.1, 0.0),
    )


def _get_exst1_parameters() -> Exst1RmsParameters:
    """Return the IEEE14 EXST1 parameter set.

    :return: EXST1 parameters for generator two.
    """
    return Exst1RmsParameters(
        0.02, 99.0, -99.0, 0.0, 0.02, 50.0, 0.02, 9999.0, -9999.0, 0.0, 0.01, 1.0
    )


def _get_esst3a_parameters() -> Esst3aRmsParameters:
    """Return the IEEE14 zero-TA ESST3A parameter set.

    :return: Shared ESST3A parameters for four generators.
    """
    return Esst3aRmsParameters(
        0.02, 0.2, -0.2, 8.0, 1.0, 5.0, 20.0, 0.0, 99.0, -99.0,
        1.0, 3.67, 0.435, 5.48, 0.01, 0.0098, 3.86, 3.33, 0.4, 99.0, 0.0
    )


def _get_exciter_types() -> tuple[GenrouExciterType, ...]:
    """Return excitation-system selections in IEEE14 generator order.

    :return: Five excitation-system selections.
    """
    return (
        GenrouExciterType.ESST3A,
        GenrouExciterType.EXST1,
        GenrouExciterType.ESST3A,
        GenrouExciterType.ESST3A,
        GenrouExciterType.ESST3A,
    )


def get_ieee14_genrou_rms_template(
    vfactory: VarFactory,
    generator_index: int,
    name: str | None = None,
) -> RmsModelTemplate:
    """Build and configure one IEEE14 GENROU generator assembly.

    :param vfactory: Shared symbolic variable factory.
    :param generator_index: Zero-based generator index in the IEEE14 inventory.
    :param name: Optional wrapper name.
    :return: Configured GENROU, TGOV1 and excitation-system assembly.
    :raises IndexError: If ``generator_index`` is outside 0..4.
    """
    genrou_parameters: tuple[GenrouRmsParameters, ...] = _get_genrou_parameters()
    tgov1_parameters: tuple[Tgov1RmsParameters, ...] = _get_tgov1_parameters()
    exciter_types: tuple[GenrouExciterType, ...] = _get_exciter_types()
    if generator_index < 0 or generator_index >= len(genrou_parameters):
        raise IndexError(
            f"IEEE14 generator_index must be in 0..{len(genrou_parameters) - 1}; "
            f"received {generator_index}."
        )
    else:
        pass

    if name is None:
        model_name: str = f"ieee14_GENROU_{generator_index + 1}"
    else:
        model_name = name
    exciter_type: GenrouExciterType = exciter_types[generator_index]
    template: RmsModelTemplate = get_complete_genrou_rms_template(
        vfactory=vfactory,
        exciter_type=exciter_type,
        name=model_name,
    )
    machine_block: Block = template.block.children[0]
    governor_block: Block = template.block.children[1]
    exciter_block: Block = template.block.children[2]

    configure_genrou_block(machine_block, genrou_parameters[generator_index], vfactory)
    configure_tgov1_block(governor_block, tgov1_parameters[generator_index], vfactory)
    if exciter_type is GenrouExciterType.ESST3A:
        configure_esst3a_block(exciter_block, _get_esst3a_parameters(), vfactory)
    else:
        configure_exst1_block(exciter_block, _get_exst1_parameters(), vfactory)
    return template


def assign_ieee14_rms_models(grid: gce.MultiCircuit, event_generator: Generator) -> Block:
    """Assign ANDES-aligned RMS models to the IEEE14 grid.

    :param grid: VeraGrid network.
    :param event_generator: First generator whose rotor speed receives the event.
    :return: Dynamic model assigned to the event generator.
    """
    bus_list: List[object] = list(grid.buses)
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

        generator.rms_model = generator_block
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

    return event_generator.rms_model


def get_andes_ieee14_full_xlsx_path() -> Path | None:
    """Locate the ANDES IEEE14 full workbook without importing the ANDES runtime.

    :return: Workbook path in the active ANDES installation, or None when ANDES is absent.
    """
    # Resolve the installed package so case paths work across operating systems.
    package_spec: ModuleSpec | None = find_spec("andes")
    if package_spec is None or package_spec.origin is None:
        return None
    else:
        return Path(package_spec.origin).resolve().parent / "cases" / "ieee14" / "ieee14_full.xlsx"


def build_ieee14_network_from_andes_case(workbook_path: Path) -> tuple[gce.MultiCircuit, Generator]:
    """Build the IEEE14 network from the ANDES full benchmark workbook.

    :param workbook_path: ANDES ``ieee14_full.xlsx`` workbook.
    :return: Network and its first generator, corresponding to GENROU 1.
    """
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

    # ANDES PFlow does not enforce the static-generator Q limits in this
    # benchmark. Wide limits prevent VeraGrid's result allocator from
    # clipping the Q value later consumed by GENROU initialization.
    generator_df: pd.DataFrame
    for generator_df in (slack_df, pv_df):
        generator_row_count: int = len(generator_df.index)
        generator_row_index: int = 0
        while generator_row_index < generator_row_count:
            generator_row = generator_df.iloc[generator_row_index]
            generator = Generator(
                name=str(generator_row["name"]),
                P=float(generator_row["p0"]) * 100.0,
                Q=float(generator_row["q0"]) * 100.0,
                vset=float(generator_row["v0"]),
                Snom=float(generator_row["Sn"]),
                Pmax=float(generator_row["pmax"]) * 100.0,
                Pmin=float(generator_row["pmin"]) * 100.0,
                Qmax=999900.0,
                Qmin=-999900.0,
                r1=float(generator_row["ra"]),
                x1=float(generator_row["xs"]),
                freq=60.0,
            )
            grid.add_generator(bus=bus_map[int(generator_row["bus"])], api_obj=generator)
            generator_row_index += 1

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

    return grid, grid.generators[0]


def build_ieee14_power_flow_options() -> PowerFlowOptions:
    """Build the tight, control-free power-flow options that seed the IEEE14 RMS case.

    :return: Power-flow options.
    """
    return PowerFlowOptions(
        solver_type=gce.SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=True,
        tolerance=1e-14,
        max_iter=25,
        control_q=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=False,
        orthogonalize_controls=False,
        apply_temperature_correction=False,
        branch_impedance_tolerance_mode=gce.BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=True,
        initialize_angles=False,
        generate_report=False,
    )


def set_initial_vector(problem: RmsProblemDae, values: np.ndarray) -> None:
    """Replace the DAE initial vector with one accepted integration snapshot.

    :param problem: Initialized VeraGrid RMS problem.
    :param values: State-then-algebraic snapshot in solver order.
    :return: None.
    :raises ValueError: If the snapshot size differs from the DAE variable count.
    """
    if values.size == problem.get_all_vars_number():
        pass
    else:
        raise ValueError("The accepted RMS snapshot does not match the DAE variable count.")
    state_count: int = len(problem.state_vars)
    state_index: int
    for state_index in range(state_count):
        state_variable: Any = problem.state_vars[state_index]
        problem.init_guess[state_variable.uid] = float(values[state_index])
    algebraic_index: int
    for algebraic_index in range(len(problem.algebraic_vars)):
        algebraic_variable: Any = problem.algebraic_vars[algebraic_index]
        problem.init_guess[algebraic_variable.uid] = float(values[state_count + algebraic_index])
