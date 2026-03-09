# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Import-level CGMES tests that only validate loading and power-flow execution."""

import os

import VeraGridEngine.api as gce


def test_load_and_run_pf() -> None:
    """Load the selected public CGMES packages and verify each can complete a power flow cleanly."""

    base_folder = os.path.abspath(
        os.path.join("data", "grids", "CGMES_2_4_15", "TestConfigurations_packageCASv2.0")
    )

    logger = gce.Logger()

    packs = [
        {"BD": os.path.join(base_folder, "MicroGrid", "BaseCase_BC",
                            "CGMES_v2.4.15_MicroGridTestConfiguration_BD_v2.zip"),
         "Files": [
             os.path.join(base_folder, "MicroGrid", "BaseCase_BC",
                          "CGMES_v2.4.15_MicroGridTestConfiguration_BC_NL_v2.zip"),
         ]
         },
    ]

    number_of_cases = 0
    failures = 0
    for data in packs:
        boundary_set = data["BD"]
        files = data["Files"]

        for file_name in files:
            if boundary_set == "":
                file_list = [file_name]
            else:
                file_list = [boundary_set, file_name]

            number_of_cases += 1

            try:
                grid = gce.open_file(filename=file_list)
            except Exception as error:
                logger.add_error(msg="Failed loading - " + str(error), device=os.path.basename(file_name))
                grid = None
                failures += 1

            if grid is not None:
                try:
                    gce.power_flow(grid)
                except Exception as error:
                    logger.add_error(msg="Failed PF - " + str(error), device=os.path.basename(file_name))
                    failures += 1

    if logger.has_logs():
        logger.print()
        print(f"Failed {failures} out of {number_of_cases}, {failures / number_of_cases * 100:.2f}%")

    assert not logger.has_logs()
