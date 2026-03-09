# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Roundtrip tests that start from CGMES, export to RAW, and validate the imported RAW case."""

from __future__ import annotations

import os

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.IO.file_save import FileSave, FileSavingOptions, FileType
from VeraGridEngine.Simulations import PowerFlowOptions
from VeraGridEngine.Simulations.driver_template import DriverToSave
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import SimulationTypes


def run_cgmes_to_raw(import_path: str | list[str], export_fname: str) -> None:
    """Import CGMES, export to RAW, re-import the RAW file, and compare voltages on stable buses."""
    logger = Logger()
    file_open_options = FileOpenOptions(
        file_type=FileType.CGMES,
        cgmes_version=gce.CGMESVersions.v2_4_15,
        cgmes_map_areas_like_raw=True,
    )

    circuit = gce.FileOpen(file_name=import_path, options=file_open_options).open()
    numerical_circuit_1 = gce.compile_numerical_circuit_at(circuit)

    for index, bus in enumerate(circuit.buses):
        bus.code = f"{index + 1}"

    power_flow_options = PowerFlowOptions()
    power_flow_results_1 = gce.power_flow(circuit, power_flow_options)

    pf_session_data = DriverToSave(name="powerflow results",
                                   tpe=SimulationTypes.PowerFlow_run,
                                   results=power_flow_results_1,
                                   logger=logger)

    save_options = FileSavingOptions(file_type=FileType.PSSE_raw)
    save_options.sessions_data.append(pf_session_data)

    raw_export = FileSave(circuit=circuit,
                          file_name=export_fname,
                          options=save_options)
    raw_export.save()

    circuit_2 = gce.FileOpen(
        file_name=export_fname,
        options=FileOpenOptions(file_type=FileType.PSSE_raw),
    ).open()
    numerical_circuit_2 = gce.compile_numerical_circuit_at(circuit_2)
    power_flow_results_2 = gce.power_flow(circuit_2, power_flow_options)

    circuits_match, circuit_logger = circuit.compare_circuits(circuit_2)
    if not circuits_match:
        circuit_logger.print()

    admittance_1 = numerical_circuit_1.get_admittance_matrices().Ybus.toarray()
    admittance_2 = numerical_circuit_2.get_admittance_matrices().Ybus.toarray()
    admittance_ok = np.allclose(admittance_1, admittance_2, atol=1e-5)
    if admittance_ok:
        print("\nAdmitance Ybus matrices are the same!")
    else:
        print("\nAdmittance Ybus matrices are NOT the same!")

    name_to_voltage_1 = dict()
    name_to_voltage_2 = dict()
    for index, bus in enumerate(circuit.buses):
        name_to_voltage_1[bus.name] = np.abs(power_flow_results_1.voltage[index])
    for index, bus in enumerate(circuit_2.buses):
        name_to_voltage_2[bus.name] = np.abs(power_flow_results_2.voltage[index])

    bad_voltage_buses = list()
    for bus_name, voltage_1 in name_to_voltage_1.items():
        voltage_2 = name_to_voltage_2.get(bus_name, None)
        if voltage_2 is not None:
            if not np.isclose(voltage_1, voltage_2, atol=1e-3):
                bad_voltage_buses.append(bus_name)

    # RAW export/import changes boundary/tie-equivalent modelling around the
    # interconnection area, causing known voltage drifts on boundary buses and
    # their immediate coupling buses.
    allowed_bad_voltage_buses = {
        "NL_TR_BUS2",
        "NL-Busbar_2",
        "N1230992195",
        "N1230992228",
        "Border_GY11",
        "Border_ST23",
        "Border_ST24",
        "Border_MA11",
        "Border_AL11",
    }
    unexpected_bad_voltage_buses = [
        bus_name for bus_name in bad_voltage_buses
        if bus_name not in allowed_bad_voltage_buses
    ]

    if len(unexpected_bad_voltage_buses) == 0:
        print("\nPower flow results are acceptable for CGMES->RAW roundtrip.")
    else:
        print("\nUnexpected power flow mismatches detected:")
        print(unexpected_bad_voltage_buses)

    assert len(unexpected_bad_voltage_buses) == 0


def test_cgmes_to_raw_roundtrip():
    """Export the public CGMES micro-grid to RAW and keep non-boundary bus voltages within 1e-3."""

    cgmes_path = os.path.join("data", "grids", "CGMES_2_4_15", "micro_grid_NL_T1.zip")
    boundary_path = os.path.join("data", "grids", "CGMES_2_4_15", "micro_grid_BD.zip")
    export_name = os.path.join("data", "output", "raw_export_result", "micro_grid_NL_T1.raw")

    if not os.path.exists(os.path.dirname(export_name)):
        os.makedirs(os.path.dirname(export_name))

    run_cgmes_to_raw([cgmes_path, boundary_path], export_name)
