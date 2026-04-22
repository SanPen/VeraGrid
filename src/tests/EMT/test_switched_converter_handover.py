# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def _load_support_module() -> Any:
    """
    Load the real switched-converter support module from ``trunk``.

    :return: Loaded support module.
    """
    repo_root: Path = Path(__file__).resolve().parents[3]
    module_path: Path = repo_root / "trunk" / "dynamics_emt" / "support" / "switched_converter_handover_case.py"
    spec = importlib.util.spec_from_file_location("switched_converter_handover_support", module_path)
    module: Any

    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_scripting_module() -> Any:
    """
    Load the real switched-converter scripting module from ``trunk``.

    :return: Loaded scripting module.
    """
    repo_root: Path = Path(__file__).resolve().parents[3]
    module_path: Path = repo_root / "trunk" / "dynamics_emt" / "scripting_vsc_switched_emt.py"
    spec = importlib.util.spec_from_file_location("switched_converter_handover_scripting", module_path)
    module: Any

    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_trunk_support_switched_converter_case_converges_and_satisfies_handover_contract() -> None:
    """
    The shared switched-converter support module must solve and validate the handover case.

    :return: None.
    """
    support_module: Any = _load_support_module()
    trace: Any = support_module.simulate_switched_converter_handover()

    support_module.validate_switched_converter_handover(trace)
    assert trace.well_initialized
    assert trace.converged


def test_trunk_scripting_entry_point_runs_without_plots() -> None:
    """
    The public scripting wrapper must run the switched-converter case without GUI interaction.

    :return: None.
    """
    scripting_module: Any = _load_scripting_module()
    trace: Any = scripting_module.run_switched_vsc_case(
        enable_plots=False,
        save_plot=False,
        open_saved_plot=False,
    )

    assert trace.well_initialized
    assert trace.converged
