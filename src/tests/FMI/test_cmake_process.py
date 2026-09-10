# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Process-tree ownership tests for the source-built FMI 3 fixture."""

from __future__ import annotations

from importlib.machinery import ModuleSpec
from importlib.util import find_spec
from pathlib import Path
import sys
import time

import pytest

from tests.FMI.cmake_process import (
    FmiThreeCmakeCommandResult,
    run_fmi_three_cmake_command,
)
from tests.FMI.fmi_three_compiled_fixture import (
    resolve_fmi_three_test_cmake_executable,
)


def test_fmi_three_cmake_resolver_uses_importable_package_native_binary() -> None:
    """Resolve the package-owned CMake binary instead of its Python launcher.

    :return: None.
    """

    cmake_executable: Path | None = resolve_fmi_three_test_cmake_executable()
    if cmake_executable is not None:
        pass
    else:
        pytest.skip("The active Python environment has no native CMake binary")
    cmake_module_spec: ModuleSpec | None = find_spec("cmake")
    assert cmake_module_spec is not None
    assert cmake_module_spec.submodule_search_locations is not None
    cmake_package_locations: tuple[str, ...] = tuple(
        cmake_module_spec.submodule_search_locations
    )
    assert len(cmake_package_locations) == 1
    if sys.platform.startswith("win"):
        cmake_relative_path: str = "data/bin/cmake.exe"
    else:
        cmake_relative_path = "data/bin/cmake"
    expected_executable: Path = (
        Path(cmake_package_locations[0]) / cmake_relative_path
    ).resolve(strict=True)

    assert cmake_executable == expected_executable


def test_fmi_three_cmake_timeout_terminates_descendant_process(
    tmp_path: Path,
) -> None:
    """Terminate a sleeping CMake descendant before it can write its marker.

    :param tmp_path: Isolated directory for scripts, log, and marker files.
    :return: None.
    """

    cmake_executable: Path | None = resolve_fmi_three_test_cmake_executable()
    if cmake_executable is not None:
        pass
    else:
        pytest.skip("The active Python environment has no native CMake binary")
    child_started_marker: Path = tmp_path / "child-started.txt"
    child_completed_marker: Path = tmp_path / "child-completed.txt"
    child_script_path: Path = tmp_path / "cmake-child.cmake"
    parent_script_path: Path = tmp_path / "cmake-parent.cmake"
    child_script_text: str = (
        f'file(WRITE "{child_started_marker.as_posix()}" "started")\n'
        'execute_process(COMMAND "${CMAKE_COMMAND}" -E sleep 4)\n'
        f'file(WRITE "{child_completed_marker.as_posix()}" "completed")\n'
    )
    parent_script_text: str = (
        f'execute_process(COMMAND "${{CMAKE_COMMAND}}" -P '
        f'"{child_script_path.as_posix()}")\n'
    )
    child_script_path.write_text(child_script_text, encoding="utf-8")
    parent_script_path.write_text(parent_script_text, encoding="utf-8")

    command_result: FmiThreeCmakeCommandResult = run_fmi_three_cmake_command(
        command=(str(cmake_executable), "-P", str(parent_script_path)),
        log_path=tmp_path / "cmake-timeout.log",
        command_timeout_seconds=2.0,
        termination_grace_seconds=10.0,
    )

    assert command_result.timed_out
    assert child_started_marker.is_file()
    time.sleep(5.0)
    assert not child_completed_marker.exists()
