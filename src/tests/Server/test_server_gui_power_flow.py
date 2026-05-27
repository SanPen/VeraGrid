from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = Path(__file__).with_name("server_gui_power_flow_runner.py")


def test_gui_loaded_grid_runs_power_flow_through_server(tmp_path: Path) -> None:
    """
    Verify one real GUI-loaded grid can be submitted to the server power-flow endpoint.
    """
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = env.get("QT_QPA_PLATFORM", "offscreen")
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)

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
        [sys.executable, str(RUNNER)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise AssertionError(
            f"Server GUI power-flow runner failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
