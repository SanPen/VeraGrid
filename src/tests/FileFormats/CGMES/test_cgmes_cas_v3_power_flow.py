# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""CGMES 3.0 Conformity Assessment Scheme power-flow smoke tests."""

from __future__ import annotations

import os
from typing import List

import VeraGridEngine.api as gce
from VeraGridEngine.IO.file_open import FileOpen, FileOpenOptions, FileType
from VeraGridEngine.Simulations import PowerFlowOptions
from VeraGridEngine.enumerations import CGMESVersions, CgmesTopologyMode, SolverType


TEST_FILE_FOLDER: str = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_FOLDER: str = os.path.abspath(os.path.join(TEST_FILE_FOLDER, "..", "..", "data"))
CGMES_CAS_V3_BASE_FOLDER: str = os.path.join(
    TEST_DATA_FOLDER,
    "grids",
    "CGMES_ConformityAssessmentScheme_TestConfigurations_v3-0-3",
    "v3.0",
)


def get_cgmes_v3_case_files(case_folder: str) -> List[str]:
    """
    Collect the XML profile files for one CGMES 3.0 CAS case.

    :param case_folder: Folder containing one merged CGMES case
    :return: Sorted XML file list
    """
    file_names: List[str] = list()
    entry_name: str
    for entry_name in sorted(os.listdir(case_folder)):
        if entry_name.lower().endswith(".xml"):
            file_names.append(os.path.join(case_folder, entry_name))

    return file_names


def create_cgmes_v3_open_options() -> FileOpenOptions:
    """
    Build the file-open options for CGMES 3.0 CAS imports.

    :return: File-open options
    """
    return FileOpenOptions(
        file_type=FileType.CGMES,
        cgmes_version=CGMESVersions.v3_0_0,
        cgmes_topology_mode=CgmesTopologyMode.ConnectivityNode,
        cgmes_try_to_map_dc_to_hvdc_line=True,
        cgmes_map_areas_like_raw=True,
        psse_adjust_taps_to_discrete_positions=True,
    )


def create_power_flow_options() -> PowerFlowOptions:
    """
    Build stable power-flow options for CGMES 3.0 CAS smoke tests.

    :return: Power-flow options
    """
    return PowerFlowOptions(
        solver_type=SolverType.NR,
        retry_with_other_methods=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=False,
        ignore_single_node_islands=True,
    )


def run_cgmes_cas_v3_power_flow_case(relative_case_folder: str) -> None:
    """
    Load selected CGMES 3.0 CAS cases and verify that power flow executes cleanly.

    :param relative_case_folder: Case folder relative to the CGMES 3.0 CAS base
    :return: Nothing
    """
    case_folder: str = os.path.join(CGMES_CAS_V3_BASE_FOLDER, relative_case_folder)
    files: List[str] = get_cgmes_v3_case_files(case_folder=case_folder)

    assert len(files) > 0

    file_open = FileOpen(file_name=files, options=create_cgmes_v3_open_options())
    grid = file_open.open()

    assert grid is not None
    assert len(grid.buses) > 0

    power_flow_results = gce.power_flow(grid, create_power_flow_options())

    assert power_flow_results is not None
    assert len(power_flow_results.voltage) == len(grid.buses)


def test_cgmes_cas_v3_power_flow_case_runs_power_flow() -> None:
    """
    Load the CGMES 3.0 PowerFlow conformance case and verify that power flow executes.

    :return: Nothing
    """
    run_cgmes_cas_v3_power_flow_case(os.path.join("PowerFlow", "PowerFlow"))


def test_cgmes_cas_v3_pst_linear_type1_runs_power_flow() -> None:
    """
    Load the CGMES 3.0 PST linear type 1 case and verify that power flow executes.

    :return: Nothing
    """
    run_cgmes_cas_v3_power_flow_case(os.path.join("PST", "PST_PhaseTapChangerLinear_Type1"))


def test_cgmes_cas_v3_pst_linear_type2_runs_power_flow() -> None:
    """
    Load the CGMES 3.0 PST linear type 2 case and verify that power flow executes.

    :return: Nothing
    """
    run_cgmes_cas_v3_power_flow_case(os.path.join("PST", "PST_PhaseTapChangerLinear_Type2"))


def test_cgmes_cas_v3_pst_table_type3_runs_power_flow() -> None:
    """
    Load the CGMES 3.0 PST table type 3 case and verify that power flow executes.

    :return: Nothing
    """
    run_cgmes_cas_v3_power_flow_case(os.path.join("PST", "PST_PhaseTapChangerTable_Type3"))
