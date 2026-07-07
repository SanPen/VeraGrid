from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = Path(__file__).with_name("diagram_widget_storage_runner.py")


def _run_gui_scenario(tmp_path: Path, scenario: str) -> None:
    """
    Run one real GUI regression scenario in an isolated child process.
    """
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = env.get("QT_QPA_PLATFORM", "offscreen")

    python_path_entries = [
        str(REPO_ROOT / "src"),
        str(REPO_ROOT / "src" / "tests"),
    ]
    existing_pythonpath = env.get("PYTHONPATH", "")
    if existing_pythonpath:
        python_path_entries.append(existing_pythonpath)
    else:
        pass
    env["PYTHONPATH"] = os.pathsep.join(python_path_entries)

    result = subprocess.run(
        [sys.executable, str(RUNNER), scenario, str(tmp_path)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise AssertionError(
            f"Scenario {scenario!r} failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def test_create_circuit_stored_diagrams_keeps_only_widgets(tmp_path: Path) -> None:
    """
    Verify stored circuit diagrams are materialized into real schematic widgets on load.
    """
    _run_gui_scenario(tmp_path=tmp_path, scenario="create_stored_diagrams")


def test_remove_diagram_deletes_selected_non_active_stored_diagram(tmp_path: Path) -> None:
    """
    Verify removing a selected non-active stored diagram updates both the widget list and the circuit.
    """
    _run_gui_scenario(tmp_path=tmp_path, scenario="remove_non_active_diagram")


def test_delete_selected_db_table_objects_updates_all_open_diagrams(tmp_path: Path) -> None:
    """
    Verify deleting a DB-selected object propagates through every open diagram widget.
    """
    _run_gui_scenario(tmp_path=tmp_path, scenario="delete_db_object")


def test_activate_scenario_does_not_create_schematic_when_scenario_has_no_diagrams(tmp_path: Path) -> None:
    """
    Verify activating a scenario with no stored diagrams leaves the GUI diagram-free.
    """
    _run_gui_scenario(tmp_path=tmp_path, scenario="activate_scenario_without_diagrams")
