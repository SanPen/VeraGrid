# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Roundtrip tests that start from CGMES, export back to CGMES, and re-import the result."""

from __future__ import annotations

import os

import VeraGridEngine.api as gc
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.IO.file_save import FileSave, FileSavingOptions, FileType
from VeraGridEngine.Simulations import PowerFlowOptions
from VeraGridEngine.Simulations.driver_template import DriverToSave
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import CGMESVersions, SimulationTypes, SolverType


def create_file_save_options(boundary_zip_path: str) -> FileSavingOptions:
    """Create CGMES export options that include the standard EQ/OP/TP/SV/SSH profiles."""
    options = FileSavingOptions(file_type=FileType.CGMES)
    options.cgmes_one_file_per_profile = False
    options.cgmes_profiles = [
        CgmesProfileType.EQ,
        CgmesProfileType.OP,
        CgmesProfileType.TP,
        CgmesProfileType.SV,
        CgmesProfileType.SSH,
    ]
    options.cgmes_version = CGMESVersions.v2_4_15
    options.cgmes_boundary_set = boundary_zip_path
    return options


def create_file_open_options() -> FileOpenOptions:
    """Create the CGMES import options used for both the original and round-tripped files."""
    return FileOpenOptions(
        cgmes_map_areas_like_raw=True,
        cgmes_try_to_map_dc_to_hvdc_line=True,
        psse_adjust_taps_to_discrete_positions=True,
        file_type=FileType.CGMES,
        cgmes_version=CGMESVersions.v2_4_15,
    )


def get_power_flow_options() -> PowerFlowOptions:
    """Create a deterministic power-flow configuration for CGMES roundtrip validation."""
    return PowerFlowOptions(
        solver_type=SolverType.NR,
        retry_with_other_methods=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=False,
        ignore_single_node_islands=True,
    )


def run_import_export_test(import_path: str | list[str],
                           export_fname: str,
                           boundary_zip_path: str) -> None:
    """Import CGMES, export it again, re-import it, and compare both resulting numerical circuits."""
    logger = Logger()

    if isinstance(import_path, list):
        initial_import_files = import_path
    else:
        initial_import_files = [import_path, boundary_zip_path]

    circuit_1 = gc.FileOpen(file_name=initial_import_files, options=create_file_open_options()).open()
    assert circuit_1 is not None
    circuit_1.buses.sort(key=lambda obj: obj.name)
    numerical_circuit_1 = gc.compile_numerical_circuit_at(circuit_1)

    power_flow_options = get_power_flow_options()
    power_flow_results = gc.power_flow(circuit_1, power_flow_options)

    pf_session_data = DriverToSave(name="powerflow results",
                                   tpe=SimulationTypes.PowerFlow_run,
                                   results=power_flow_results,
                                   logger=logger)

    save_options = create_file_save_options(boundary_zip_path)
    save_options.sessions_data.append(pf_session_data)

    cgmes_export = FileSave(circuit=circuit_1,
                            file_name=export_fname,
                            options=save_options)
    cgmes_export.save()

    circuit_2 = gc.FileOpen(file_name=[export_fname, boundary_zip_path], options=create_file_open_options()).open()
    assert circuit_2 is not None
    circuit_2.buses.sort(key=lambda obj: obj.name)
    if circuit_1.buses[0].name != circuit_2.buses[0].name:
        circuit_2.buses.append(circuit_2.buses.pop(0))
    numerical_circuit_2 = gc.compile_numerical_circuit_at(circuit_2)

    circuits_match, circuit_logger = circuit_1.compare_circuits(circuit_2)
    if circuits_match:
        print("/nOK! SUCCESS for Multi Circuit!/n")
    else:
        circuit_logger.print()

    numerical_match, numerical_logger = numerical_circuit_1.compare(nc_2=numerical_circuit_2, tol=1e-4)
    if numerical_match:
        print("\nOK! SUCCESS for Numerical Circuit!\n")
    else:
        numerical_logger.print()

        print("Buses")
        print(numerical_circuit_1.bus_data.names)
        print(numerical_circuit_2.bus_data.names)
        print("Loads")
        print(numerical_circuit_1.load_data.names)
        print(numerical_circuit_2.load_data.names)
        print("Gens")
        print(numerical_circuit_1.generator_data.names)
        print(numerical_circuit_2.generator_data.names)

        injections_1 = numerical_circuit_1.get_power_injections_pu()
        injections_2 = numerical_circuit_2.get_power_injections_pu()
        admittance_1 = numerical_circuit_1.get_admittance_matrices()
        admittance_2 = numerical_circuit_2.get_admittance_matrices()

        print("Sbus1")
        print(injections_1)
        print("Sbus2")
        print(injections_2)
        print("S_diff")
        print(injections_2 - injections_1)
        print("Y1")
        print(admittance_1.Ybus.toarray())
        print("Y2")
        print(admittance_2.Ybus.toarray())
        print("Y_diff")
        print(admittance_2.Ybus.toarray() - admittance_1.Ybus.toarray())

    assert numerical_match


def test_cgmes_roundtrip():
    """Roundtrip the public micro-grid CGMES case and keep the re-imported numerical circuit equivalent."""

    test_grid_name = "micro_grid_NL_T1.zip"
    boundary_set_name = "micro_grid_BD.zip"

    cgmes_path = os.path.join("data", "grids", "CGMES_2_4_15", test_grid_name)
    boundary_path = os.path.join("data", "grids", "CGMES_2_4_15", boundary_set_name)
    export_name = os.path.join("data", "output", "cgmes_export_result", f"{test_grid_name[:-4]}_GC.zip")

    if not os.path.exists(os.path.dirname(export_name)):
        os.makedirs(os.path.dirname(export_name))

    run_import_export_test(cgmes_path, export_name, boundary_path)
