# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Relicap CGMES 3.0 load and power-flow regression tests."""

from __future__ import annotations

import os
from typing import Dict, List

import VeraGridEngine.api as gce
from VeraGridEngine.IO.file_open import FileOpen, FileOpenOptions, FileType
from VeraGridEngine.Simulations import PowerFlowOptions
from VeraGridEngine.enumerations import CGMESVersions, SolverType


def get_relicap_base_folder() -> str:
    """
    Return the absolute path of the local Relicap test dataset.

    :return: Relicap base folder path.
    """
    test_file_folder: str = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(
        os.path.join(
            test_file_folder,
            "..",
            "..",
            "data",
            "grids",
            "CGMES_3_0",
            "Relicap",
        )
    )


def build_case_files(base_folder: str, relative_files: List[str]) -> List[str]:
    """
    Build absolute file paths for one Relicap case.

    :param base_folder: Relicap base folder.
    :param relative_files: Case file paths relative to the Relicap base folder.
    :return: Absolute file paths.
    """
    absolute_files: List[str] = list()
    relative_file: str
    for relative_file in relative_files:
        absolute_files.append(os.path.join(base_folder, relative_file))
    return absolute_files


def get_relicap_cases(base_folder: str) -> Dict[str, List[str]]:
    """
    Build the Relicap case matrix used by the legacy ``run_relicap_grids`` script.

    :param base_folder: Relicap base folder.
    :return: Mapping from case name to absolute file list.
    """
    return {
        "Belgovia": build_case_files(base_folder, [
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_TP_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_SSH_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z__Belgovia_EQ_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_SV_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Belgovia.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Britheim": build_case_files(base_folder, [
            "Britheim/Grid/cimxml/20220615T2230Z_2D_Britheim_TP_1.xml",
            "Britheim/Grid/cimxml/20220615T2230Z_2D_Britheim_SSH_1.xml",
            "Britheim/Grid/cimxml/20220615T2230Z__Britheim_EQ_1.xml",
            "Britheim/Grid/cimxml/20220615T2230Z_2D_Britheim_SV_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Britheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Espheim": build_case_files(base_folder, [
            "Espheim/Grid/cimxml/20220615T2230Z__Espheim_EQ_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z_2D_Espheim_SSH_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z_2D_Espheim_SV_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z_2D_Espheim_TP_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Espheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Espheim-Portheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "DC-Espheim-Svedala": build_case_files(base_folder, [
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z_2D_HVDC-Espheim-Svedala_TP_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z_2D_HVDC-Espheim-Svedala_SV_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z_2D_HVDC-Espheim-Svedala_SSH_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z__HVDC-Espheim-Svedala_EQ_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Espheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Espheim-Portheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Espheim + DC-Espheim-Svedala": build_case_files(base_folder, [
            "Espheim/Grid/cimxml/20220615T2230Z__Espheim_EQ_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z_2D_Espheim_SSH_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z_2D_Espheim_SV_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z_2D_Espheim_TP_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z_2D_HVDC-Espheim-Svedala_TP_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z_2D_HVDC-Espheim-Svedala_SV_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z_2D_HVDC-Espheim-Svedala_SSH_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z__HVDC-Espheim-Svedala_EQ_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Espheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Espheim-Portheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Galia": build_case_files(base_folder, [
            "Galia/Grid/cimxml/20220615T2230Z_2D_Galia_TP_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z_2D_Galia_SSH_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z__Galia_EQ_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z_2D_Galia_SV_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Britheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Nordheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "DC-Nordheim-Galia": build_case_files(base_folder, [
            "DC-Nordheim-Galia/Grid/cimxml/20220615T2230Z_2D_HVDC-Nordheim-Galia_SSH_1.xml",
            "DC-Nordheim-Galia/Grid/cimxml/20220615T2230Z_2D_HVDC-Nordheim-Galia_TP_1.xml",
            "DC-Nordheim-Galia/Grid/cimxml/20220615T2230Z__HVDC-Nordheim-Galia_EQ_1.xml",
            "DC-Nordheim-Galia/Grid/cimxml/20220615T2230Z_2D_HVDC-Nordheim-Galia_SV_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Britheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Nordheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Jotunheim": build_case_files(base_folder, [
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_Svedala_SSH_2.xml",
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_Britheim_SSH_2.xml",
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_Jotunheim_TP_1.xml",
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_Belgovia_SSH_2.xml",
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_HVDC_Espheim-Svedala_SSH_2.xml",
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_HVDC_Nordheim-Galia_SSH_2.xml",
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_Jotunheim_SV_1.xml",
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_Espheim_SSH_2.xml",
            "Jotunheim/Grid/cimxml/20241223T0642Z_2D_Portheim_SSH_2.xml",
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_Nordheim_SSH_2.xml",
            "Jotunheim/Grid/cimxml/20220615T2230Z_2D_Galia_SSH_2.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Britheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Espheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Espheim-Portheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Nordheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Nordheim": build_case_files(base_folder, [
            "Nordheim/Grid/cimxml/20220615T2230Z_2D_Nordheim_SV_1.xml",
            "Nordheim/Grid/cimxml/20220615T2230Z_2D_Nordheim_SSH_1.xml",
            "Nordheim/Grid/cimxml/20220615T2230Z__Nordheim_EQ_1.xml",
            "Nordheim/Grid/cimxml/20220615T2230Z_2D_Nordheim_TP_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Nordheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Portheim": build_case_files(base_folder, [
            "Portheim/Grid/cimxml/20241223T0642Z_2D_Portheim_EQ_1.xml",
            "Portheim/Grid/cimxml/20241223T0642Z_2D_Portheim_SSH_1.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Svedala": build_case_files(base_folder, [
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SV_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_TP_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SSH_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z__Svedala_EQ_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Espheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Belgovia.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Svedala + DC-Espheim-Svedala": build_case_files(base_folder, [
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SV_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_TP_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SSH_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z__Svedala_EQ_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z_2D_HVDC-Espheim-Svedala_TP_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z_2D_HVDC-Espheim-Svedala_SV_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z_2D_HVDC-Espheim-Svedala_SSH_1.xml",
            "DC-Espheim-Svedala/Grid/cimxml/20220615T2230Z__HVDC-Espheim-Svedala_EQ_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Espheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Espheim-Portheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Combination 1 (Belgovia + Svedala)": build_case_files(base_folder, [
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_TP_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_SSH_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z__Belgovia_EQ_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_SV_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SV_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_TP_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SSH_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z__Svedala_EQ_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Espheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Combination 2 (Belgovia + Svedala +Galia)": build_case_files(base_folder, [
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_TP_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_SSH_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z__Belgovia_EQ_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_SV_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SV_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_TP_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SSH_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z__Svedala_EQ_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z_2D_Galia_TP_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z_2D_Galia_SSH_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z__Galia_EQ_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z_2D_Galia_SV_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Espheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Britheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Nordheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
        "Combination 3 (Belgovia + Svedala +Galia + Espheim + Britheim )": build_case_files(base_folder, [
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_TP_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_SSH_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z__Belgovia_EQ_1.xml",
            "Belgovia/Grid/cimxml/20220615T2230Z_2D_Belgovia_SV_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SV_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_TP_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z_2D_Svedala_SSH_1.xml",
            "Svedala/Grid/cimxml/20220615T2230Z__Svedala_EQ_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z_2D_Galia_TP_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z_2D_Galia_SSH_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z__Galia_EQ_1.xml",
            "Galia/Grid/cimxml/20220615T2230Z_2D_Galia_SV_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z__Espheim_EQ_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z_2D_Espheim_SSH_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z_2D_Espheim_SV_1.xml",
            "Espheim/Grid/cimxml/20220615T2230Z_2D_Espheim_TP_1.xml",
            "Britheim/Grid/cimxml/20220615T2230Z_2D_Britheim_TP_1.xml",
            "Britheim/Grid/cimxml/20220615T2230Z_2D_Britheim_SSH_1.xml",
            "Britheim/Grid/cimxml/20220615T2230Z__Britheim_EQ_1.xml",
            "Britheim/Grid/cimxml/20220615T2230Z_2D_Britheim_SV_1.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Belgovia.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Svedala-Espheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Britheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Galia-Nordheim.xml",
            "boundaryData/Grid/cimxml/Boundary_Border-Espheim-Portheim.xml",
            "commonData/Grid/cimxml/Grid_CommonData_CGM-CD.xml",
        ]),
    }


def create_cgmes_open_options() -> FileOpenOptions:
    """
    Build file-open options for Relicap CGMES 3.0 tests.

    :return: File-open options.
    """
    return FileOpenOptions(
        file_type=FileType.CGMES,
        cgmes_version=CGMESVersions.v3_0_0,
    )


def create_power_flow_options() -> PowerFlowOptions:
    """
    Build power-flow options for Relicap CGMES 3.0 tests.

    :return: Power-flow options.
    """
    return PowerFlowOptions(
        tolerance=1e-6,
        solver_type=SolverType.NR,
        retry_with_other_methods=False,
        ignore_single_node_islands=True,
    )


def test_relicap_grids_load_and_run_power_flow() -> None:
    """
    Load Relicap CGMES 3.0 test cases and verify that power-flow execution completes.

    :return: Nothing.
    """
    base_folder: str = get_relicap_base_folder()
    cases: Dict[str, List[str]] = get_relicap_cases(base_folder=base_folder)
    file_open_options: FileOpenOptions = create_cgmes_open_options()
    power_flow_options: PowerFlowOptions = create_power_flow_options()
    power_flow_tolerance: float = float(power_flow_options.tolerance)

    non_converged_cases: List[str] = list()
    high_error_cases: List[str] = list()

    case_name: str
    case_files: List[str]
    for case_name, case_files in cases.items():
        case_file: str
        for case_file in case_files:
            if os.path.isfile(case_file):
                pass
            else:
                assert False, f"{case_name}: missing file {case_file}"

        grid = FileOpen(file_name=case_files, options=file_open_options).open()

        if grid is None:
            assert False, f"{case_name}: FileOpen returned None"
        else:
            power_flow_results = gce.power_flow(grid, power_flow_options)

            if power_flow_results is None:
                assert False, f"{case_name}: power_flow returned None"
            else:
                if power_flow_results.converged:
                    pass
                else:
                    non_converged_cases.append(
                        f"{case_name}: converged={power_flow_results.converged}, error={power_flow_results.error}"
                    )

                if power_flow_results.error < power_flow_tolerance:
                    pass
                else:
                    high_error_cases.append(
                        f"{case_name}: error={power_flow_results.error}, tolerance={power_flow_tolerance}"
                    )

    assert len(non_converged_cases) == 0, "Relicap non-converged cases:\n" + "\n".join(non_converged_cases)
    assert len(high_error_cases) == 0, "Relicap high-error cases:\n" + "\n".join(high_error_cases)
