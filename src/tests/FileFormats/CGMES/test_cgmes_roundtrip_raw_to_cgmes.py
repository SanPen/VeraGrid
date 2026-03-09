# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Roundtrip tests that start from RAW, export to CGMES, and validate the imported CGMES case."""

from __future__ import annotations

import os

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.IO.file_open import FileOpen, FileOpenOptions
from VeraGridEngine.IO.file_save import FileSave, FileSavingOptions, FileType
from VeraGridEngine.Simulations import PowerFlowOptions
from VeraGridEngine.Simulations.driver_template import DriverToSave
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import CGMESVersions, SimulationTypes, SolverType


def create_file_save_options(boundary_zip_path: str) -> FileSavingOptions:
    """Create CGMES export options for the RAW-to-CGMES roundtrip tests."""
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


def create_file_open_options(file_type: FileType,
                             cgmes_version: CGMESVersions | None = None) -> FileOpenOptions:
    """Create the import options used by both the RAW source case and the CGMES roundtrip case."""
    return FileOpenOptions(
        cgmes_map_areas_like_raw=True,
        cgmes_try_to_map_dc_to_hvdc_line=True,
        psse_adjust_taps_to_discrete_positions=True,
        file_type=file_type,
        cgmes_version=cgmes_version,
    )


def get_power_flow_options() -> PowerFlowOptions:
    """Create a stable power-flow configuration for the RAW-to-CGMES roundtrip checks."""
    return PowerFlowOptions(
        solver_type=SolverType.NR,
        retry_with_other_methods=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=False,
        ignore_single_node_islands=True,
    )


def run_raw_to_cgmes(import_path: str | list[str],
                     export_fname: str,
                     boundary_zip_path: str) -> None:
    """Import RAW, export to CGMES, re-import it, and compare numerical circuits and voltages."""
    raw_open_options = create_file_open_options(file_type=FileType.PSSE_raw)

    file_open_1 = FileOpen(file_name=import_path, options=raw_open_options)
    circuit_1 = file_open_1.open()

    power_flow_options = get_power_flow_options()
    power_flow_results_1 = gce.power_flow(circuit_1, power_flow_options)
    assert power_flow_results_1.converged

    logger_saving = Logger()
    pf_session_data = DriverToSave(name="powerflow results",
                                   tpe=SimulationTypes.PowerFlow_run,
                                   results=power_flow_results_1,
                                   logger=logger_saving)

    save_options = create_file_save_options(boundary_zip_path)
    save_options.sessions_data.append(pf_session_data)

    cgmes_export = FileSave(circuit=circuit_1,
                            file_name=export_fname,
                            options=save_options)
    cgmes_export.save()
    logger_saving.print()

    cgmes_open_options = create_file_open_options(
        file_type=FileType.CGMES,
        cgmes_version=CGMESVersions.v2_4_15,
    )

    file_open_2 = FileOpen(file_name=[export_fname, boundary_zip_path], options=cgmes_open_options)
    circuit_2 = file_open_2.open()
    power_flow_results_2 = gce.power_flow(circuit_2, power_flow_options)

    circuits_match, circuit_logger = circuit_1.compare_circuits(circuit_2)
    if not circuits_match:
        print("\nMulti Circuits are not equal!\n")
        circuit_logger.print()

    numerical_circuit_1 = gce.compile_numerical_circuit_at(circuit_1)
    numerical_circuit_2 = gce.compile_numerical_circuit_at(circuit_2)

    numerical_match, numerical_logger = numerical_circuit_1.compare(nc_2=numerical_circuit_2, tol=1e-6)
    if numerical_match:
        print("\nOK! SUCCESS for Numerical Circuit!\n")
    else:
        print("\nNumerical Circuits are not equal!\n")
        numerical_logger.print()

        admittance_1 = numerical_circuit_1.get_admittance_matrices()
        admittance_2 = numerical_circuit_2.get_admittance_matrices()
        injections_1 = numerical_circuit_1.get_power_injections()
        injections_2 = numerical_circuit_2.get_power_injections()
        print("Buses")
        print(numerical_circuit_1.bus_data.names)
        print(numerical_circuit_2.bus_data.names)
        print("Loads")
        print(numerical_circuit_1.load_data.names)
        print(numerical_circuit_2.load_data.names)
        print("Gens")
        print(numerical_circuit_1.generator_data.names)
        print(numerical_circuit_2.generator_data.names)
        print("Sbus1")
        print(injections_1)
        print("Sbus2")
        print(injections_2)
        print("S_diff")
        print(injections_1 - injections_2)
        print("Y1")
        print(admittance_1.Ybus.A)
        print("Y2")
        print(admittance_2.Ybus.A)
        print("Y_diff", admittance_2.Ybus.A - admittance_1.Ybus.A)
        mask = ~np.isclose(admittance_1.Ybus.A, admittance_2.Ybus.A, atol=1e-4, rtol=0)
        print("Y1_elements", admittance_1.Ybus.A[mask])
        print("Y2_elements", admittance_2.Ybus.A[mask])
        print("Y_diff", admittance_1.Ybus.A[mask] - admittance_2.Ybus.A[mask])

    power_flow_match = np.allclose(np.abs(power_flow_results_1.voltage),
                                   np.abs(power_flow_results_2.voltage),
                                   atol=1e-5)
    if power_flow_match:
        print("\nOK! SUCCESS for PowerFlow results!\n")
    else:
        print("Tap modules")
        print(power_flow_results_1.tap_module)
        print(power_flow_results_2.tap_module)
        print("Tap phase")
        print(power_flow_results_1.tap_angle)
        print(power_flow_results_2.tap_angle)

        print("\nVoltages")
        print(np.abs(power_flow_results_1.voltage))
        print(np.abs(power_flow_results_2.voltage))
        print("Voltage abs diff")
        print(np.abs(power_flow_results_2.voltage) - np.abs(power_flow_results_1.voltage))

    assert power_flow_match


def test_raw_to_cgmes_cross_roundtrip():
    """Export the public IEEE 14 RAW case to CGMES and preserve the original voltage solution."""

    test_grid_name = "IEEE_14_v35_3_nudox_1_hvdc_desf_rates_fs_ss"
    boundary_path = os.path.join("data", "grids", "CGMES_2_4_15", "BD_IEEE_Grids.zip")

    raw_path = os.path.join("data", "grids", "RAW", f"{test_grid_name}.raw")
    export_name = os.path.join(
        "data", "output", "raw_to_cgmes_export_results",
        f"{test_grid_name}_from_raw_GC.zip",
    )

    if not os.path.exists(os.path.dirname(export_name)):
        os.makedirs(os.path.dirname(export_name))

    run_raw_to_cgmes(raw_path, export_name, boundary_path)
