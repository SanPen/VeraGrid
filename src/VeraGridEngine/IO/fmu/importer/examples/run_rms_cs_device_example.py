# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Run the RMS Co-Simulation FMU device example."""

from __future__ import annotations

from pathlib import Path
import sys


if __package__ is None or __package__ == "":
    repo_root = Path(__file__).resolve().parents[6]
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "src"))
else:
    pass


from VeraGridEngine.IO.fmu.importer.examples.common import get_example_output_dir, run_rms_cs_example


def main() -> int:
    """Execute the RMS CS example and print the report path.

    :return: Process exit code.
    """

    report_path = run_rms_cs_example(get_example_output_dir())
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
