# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

import pytest

from VeraGridEngine.IO.file_open import open_ucte
from VeraGridEngine.basic_structures import Logger, LogSeverity


UCTE_FIXTURES = Path(__file__).resolve().parents[2] / "data" / "grids" / "ucte"
FILES = [
    "test_ucte_AL.uct",
    "test_ucte_DE.uct",
    "test_ucte_DK.uct",
    "test_ucte_ES.uct",
    "test_ucte_FR.uct",
    "test_ucte_HR.uct",
    "test_ucte_HU.uct",
    "test_ucte_IT.uct",
    "test_ucte_LU.uct",
    "test_ucte_NL.uct",
    "test_ucte_RS.uct",
]


def get_errors(logger: Logger) -> list[str]:
    return [entry.msg for entry in logger.entries if entry.severity == LogSeverity.Error]


@pytest.mark.parametrize("fixture_name", FILES)
def test_pandapower_country_fixture_loads_without_errors(fixture_name: str):
    logger = Logger()
    fixture_path = UCTE_FIXTURES / fixture_name

    assert fixture_path.exists()

    grid = open_ucte(str(fixture_path), logger=logger)

    assert len(grid.get_buses()) > 0
    assert grid.get_lines_number() + grid.get_transformers2w_number() + grid.get_switches_number() > 0
    assert get_errors(logger) == []
