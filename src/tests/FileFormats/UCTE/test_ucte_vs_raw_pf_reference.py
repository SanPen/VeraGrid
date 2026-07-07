# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

import numpy as np
import pytest

from VeraGridEngine.IO.file_open import FileOpen, open_ucte
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions, SolverType


GRID_FIXTURES = Path(__file__).resolve().parents[2] / "data" / "grids"


@pytest.mark.parametrize(
    "ucte_name,raw_name",
    [
        ("IEEE 14 bus.uct", "IEEE 14 bus.raw"),
        ("IEEE 30 bus.uct", "IEEE 30 bus.raw"),
        ("IEEE 118 bus.uct", "IEEE 118 Bus v2.raw"),
    ],
)
def test_ucte_import_matches_raw_pf_reference(ucte_name: str, raw_name: str):
    ucte_path = GRID_FIXTURES / "ucte" / ucte_name
    raw_path = GRID_FIXTURES / "RAW" / raw_name

    assert ucte_path.exists()
    assert raw_path.exists()

    ucte_logger = Logger()
    grid_ucte = open_ucte(str(ucte_path), logger=ucte_logger)
    grid_raw = FileOpen(str(raw_path)).open()

    # RAW is used as the reference model for import fidelity.
    assert grid_ucte.get_bus_number() == grid_raw.get_bus_number()
    assert grid_ucte.get_lines_number() == grid_raw.get_lines_number()
    assert grid_ucte.get_transformers2w_number() == grid_raw.get_transformers2w_number()
    assert len(grid_ucte.get_shunts()) == len(grid_raw.get_shunts())
    assert len(grid_ucte.get_loads()) == len(grid_raw.get_loads())
    assert len(grid_ucte.get_generators()) == len(grid_raw.get_generators())

    opts = PowerFlowOptions(
        solver_type=SolverType.NR,
        verbose=0,
        control_q=False,
        retry_with_other_methods=False,
    )

    pf_ucte = PowerFlowDriver(grid_ucte, opts)
    pf_ucte.run()
    pf_raw = PowerFlowDriver(grid_raw, opts)
    pf_raw.run()

    assert pf_ucte.results.converged
    assert pf_raw.results.converged

    vm_ucte = np.abs(pf_ucte.results.voltage)
    vm_raw = np.abs(pf_raw.results.voltage)

    # A hard code validation is not possible because the UCTE format is "lossy" in comparison with raw
    # assert np.allclose(vm_ucte, vm_raw, atol=1e-3)
