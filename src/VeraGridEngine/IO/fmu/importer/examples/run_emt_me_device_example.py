# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Run the EMT Model Exchange FMU device example."""

from __future__ import annotations

from pathlib import Path
import sys
import types


if __package__ is None or __package__ == "":
    repo_root = Path(__file__).resolve().parents[6]
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "src"))
else:
    pass


networkx_module = sys.modules.get("networkx", None)
if networkx_module is None:
    sys.modules["networkx"] = types.ModuleType("networkx")
else:
    pass

matplotlib_module = sys.modules.get("matplotlib", None)
if matplotlib_module is None:
    matplotlib_module = types.ModuleType("matplotlib")
    sys.modules["matplotlib"] = matplotlib_module
else:
    pass

for submodule_name in ("pyplot", "colors", "cm"):
    full_name = f"matplotlib.{submodule_name}"
    submodule = sys.modules.get(full_name, None)
    if submodule is None:
        submodule = types.ModuleType(full_name)
        sys.modules[full_name] = submodule
    else:
        pass
    setattr(matplotlib_module, submodule_name, submodule)

pyplot_module = sys.modules["matplotlib.pyplot"]
if hasattr(pyplot_module, "axis"):
    pass
else:
    setattr(pyplot_module, "axis", object)


from VeraGridEngine.IO.fmu.importer.examples.common import get_example_output_dir, run_emt_me_example


def main() -> int:
    """Execute the EMT ME example and print the report path.

    :return: Process exit code.
    """

    report_path = run_emt_me_example(get_example_output_dir())
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
