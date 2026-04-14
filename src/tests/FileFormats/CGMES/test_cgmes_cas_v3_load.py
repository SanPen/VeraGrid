# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""CGMES 3.0 Conformity Assessment Scheme import coverage tests."""

from __future__ import annotations

import os
from typing import List

import pytest

from VeraGridEngine.IO.file_open import FileOpen, FileOpenOptions, FileType
from VeraGridEngine.enumerations import CGMESVersions, CgmesTopologyMode


TEST_FILE_FOLDER: str = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_FOLDER: str = "data"
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


@pytest.mark.parametrize(
    "relative_case_folder",
    [
        os.path.join("FullGrid", "FullGrid-Merged"),
        os.path.join("MiniGrid", "MiniGrid-Merged"),
        os.path.join("PowerFlow", "PowerFlow"),
        os.path.join("RealGrid", "RealGrid-Merged"),
        os.path.join("SmallGrid", "SmallGrid-Merged"),
        os.path.join("Svedala", "Svedala-Merged"),
    ],
)
def test_cgmes_cas_v3_cases_load_with_connectivity_nodes(relative_case_folder: str) -> None:
    """
    Load representative CGMES 3.0 CAS cases using ConnectivityNode topology mode.

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
