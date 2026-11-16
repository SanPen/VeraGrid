# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Optional third-party installations must not prevent engine startup."""

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('failure', ('absent', 'ImportError', 'AttributeError', 'OSError',
                                   'RuntimeError', 'ValueError', 'TypeError', 'missing_api',
                                   'missing_dependency'))
def test_broken_optional_dependencies_do_not_break_startup(failure: str) -> None:
    """Import the engine with isolated, deliberately broken third-party modules.

    :param failure: Missing package, missing export, or import failure to reproduce.
    :return: None.
    """
    source_root: Path = Path(__file__).resolve().parents[1]
    command: list[str] = [sys.executable, '-m', 'tests.optional_dependencies_worker', failure]
    result: subprocess.CompletedProcess[str] = subprocess.run(
        command, cwd=source_root, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'optional dependency startup passed' in result.stdout
    assert 'Optional integration disabled' not in result.stderr


def test_pypsa_missing_format_api_is_reported() -> None:
    """Keep missing reader methods from escaping as an AttributeError.

    :return: None.
    """
    source_root: Path = Path(__file__).resolve().parents[1]
    command: list[str] = [
        sys.executable,
        '-m',
        'tests.optional_dependencies_worker',
        'missing_format_api',
    ]
    result: subprocess.CompletedProcess[str] = subprocess.run(
        command, cwd=source_root, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_installed_pandapower_still_imports_projects(tmp_path: Path) -> None:
    """Round-trip a real network through the optional JSON reader when installed.

    :param tmp_path: Temporary project directory.
    :return: None.
    """
    from VeraGridEngine.IO.others.pandapower_parser import PANDAPOWER_AVAILABLE, Panda2VeraGrid
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit

    if PANDAPOWER_AVAILABLE:
        import pandapower as pp

        network: pp.pandapowerNet = pp.create_empty_network(f_hz=60.0)
        try:
            bus_index: int = pp.create_bus(network, vn_kv=110.0, name='Test bus')
        except TypeError as error:
            error_message: str = str(error)
            # PandaPower 3.4 is incompatible with the pandas 3 stack required by installed PyPSA.
            if "Invalid value 'True' for dtype 'float64'" in error_message:
                pytest.skip('pandapower cannot create networks with the installed pandas version')
            else:
                raise
        pp.create_ext_grid(network, bus_index)
        pp.create_load(network, bus_index, p_mw=5.0, q_mvar=1.0)
        file_name: str = str(tmp_path / 'network.json')
        pp.to_json(network, file_name)

        parser: Panda2VeraGrid = Panda2VeraGrid(file_name)
        grid: MultiCircuit = parser.get_multicircuit()
        assert grid.get_bus_number() == 1
        assert grid.get_loads_number() == 1
        assert grid.fBase == 60.0
        assert grid.loads[0].P == 5.0
    else:
        pytest.skip('pandapower integration is unavailable')
