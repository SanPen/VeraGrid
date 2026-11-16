# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from pathlib import Path

import numpy as np

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.matpower.devices.generator import MatpowerGenerator
from VeraGridEngine.IO.matpower.matpower_utils import normalize_matpower_float
from VeraGridEngine.IO.matpower.veragrid_to_matpower import write_matpower_case_file

from . import MATPOWER_FIXTURES
from ..roundtrip_pf_utils import run_export_roundtrip_power_flow_test


def export_matpower_roundtrip_file(circuit: MultiCircuit, file_name: str) -> None:
    """
    Export one circuit to MATPOWER for the power-flow roundtrip test.

    :param circuit: Circuit to export.
    :param file_name: Target MATPOWER file path.
    :return: None.
    """
    write_matpower_case_file(file_name=file_name, circuit=circuit, t_idx=None)


def test_matpower_scalar_normalization_converts_text_and_numeric_infinity() -> None:
    """Convert MATPOWER's signed infinity tokens into finite device values.

    :return: None.
    """
    assert normalize_matpower_float('Inf') == 1.0e6
    assert normalize_matpower_float(np.inf) == 1.0e6
    assert normalize_matpower_float('-Inf') == -1.0e6
    assert normalize_matpower_float(-np.inf) == -1.0e6


def test_matpower_generator_unbounded_limits_are_finite() -> None:
    """Convert MATPOWER's infinite generator limits into usable VeraGrid values.

    :return: None.
    """
    generator: MatpowerGenerator = MatpowerGenerator()
    row: list[float] = [1.0, 0.0, 0.0, np.inf, -np.inf, 1.0, 100.0, 1.0, np.inf, -np.inf]

    # Parse the complete mandatory MATPOWER generator record including unlimited P and Q bounds.
    generator.parse_row(row=row)

    assert generator.qmax == 1.0e6
    assert generator.qmin == -1.0e6
    assert generator.pmax == 1.0e6
    assert generator.pmin == -1.0e6


def test_matpower_ieee14_power_flow_roundtrip(tmp_path: Path) -> None:
    """
    Export IEEE 14 to MATPOWER, re-import it, and preserve the power-flow solution.

    :param tmp_path: Pytest temporary directory.
    :return: None.
    """
    import_path: Path = MATPOWER_FIXTURES / "case14.matpower"
    export_path: Path = tmp_path / "ieee14_roundtrip.m"

    # Use the native MATPOWER IEEE14 fixture so the roundtrip check isolates MATPOWER export-import behavior.
    run_export_roundtrip_power_flow_test(import_file_name=str(import_path),
                                         export_file_name=str(export_path),
                                         export_func=export_matpower_roundtrip_file)
