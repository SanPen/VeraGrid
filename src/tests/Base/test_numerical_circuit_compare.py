# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

import numpy as np

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.IO.file_open import FileOpen


TESTS_ROOT: Path = Path(__file__).resolve().parents[1]
DATA_ROOT: Path = TESTS_ROOT / "data"


def _build_case14_numerical_circuit():
    grid = FileOpen(file_name=str(DATA_ROOT / "grids" / "Matpower" / "case14.matpower")).open()
    return compile_numerical_circuit_at(circuit=grid)


def test_compare_mode_idtag_ignores_branch_order() -> None:
    nc_1 = _build_case14_numerical_circuit()
    nc_2 = nc_1.copy()

    bus_idx = np.arange(nc_2.bus_data.nbus, dtype=int)
    bus_map = np.arange(nc_2.bus_data.nbus, dtype=int)
    br_idx = np.arange(nc_2.passive_branch_data.nelm - 1, -1, -1, dtype=int)
    logger = Logger()

    nc_2.passive_branch_data = nc_2.passive_branch_data.slice(elm_idx=br_idx, bus_idx=bus_idx,
                                                              bus_map=bus_map, logger=logger)
    nc_2.active_branch_data = nc_2.active_branch_data.slice(elm_idx=br_idx, bus_idx=bus_idx,
                                                            bus_map=bus_map, logger=logger)
    nc_2.consolidate_information()

    ok_strict, _ = nc_1.compare(nc_2=nc_2, tol=1e-6)
    ok_idtag, idtag_logger = nc_1.compare(nc_2=nc_2, tol=1e-6, by_idtag=True)

    assert not ok_strict
    assert ok_idtag, idtag_logger


def test_compare_mode_idtag_ignores_missing_loads_outside_common_subset() -> None:
    nc_1 = _build_case14_numerical_circuit()
    nc_2 = nc_1.copy()

    bus_idx = np.arange(nc_2.bus_data.nbus, dtype=int)
    bus_map = np.arange(nc_2.bus_data.nbus, dtype=int)
    load_idx = np.arange(nc_2.load_data.nelm - 1, dtype=int)

    nc_2.load_data = nc_2.load_data.slice(elm_idx=load_idx, bus_idx=bus_idx, bus_map=bus_map)
    nc_2.consolidate_information()

    ok_strict, _ = nc_1.compare(nc_2=nc_2, tol=1e-6)
    ok_idtag, idtag_logger = nc_1.compare(nc_2=nc_2, tol=1e-6, by_idtag=True)

    assert not ok_strict
    assert ok_idtag, idtag_logger


def test_compare_sums_detects_dropped_injections() -> None:
    nc_1 = _build_case14_numerical_circuit()
    nc_2 = nc_1.copy()

    bus_idx = np.arange(nc_2.bus_data.nbus, dtype=int)
    bus_map = np.arange(nc_2.bus_data.nbus, dtype=int)
    load_idx = np.arange(nc_2.load_data.nelm - 1, dtype=int)

    nc_2.load_data = nc_2.load_data.slice(elm_idx=load_idx, bus_idx=bus_idx, bus_map=bus_map)
    nc_2.consolidate_information()

    ok_idtag, _ = nc_1.compare(nc_2=nc_2, tol=1e-6, by_idtag=True)
    ok_sums, sums_logger = nc_1.compare_sums(nc_2=nc_2, tol=1e-6)

    assert ok_idtag
    assert not ok_sums
    assert sums_logger.error_count() > 0
