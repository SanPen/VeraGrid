# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Run all FMU device import examples and print the generated reports."""

from __future__ import annotations

from pathlib import Path
import sys


if __package__ is None or __package__ == "":
    repo_root = Path(__file__).resolve().parents[6]
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "src"))
else:
    pass


from VeraGridEngine.IO.fmu.importer.examples.common import (
    get_example_output_dir,
    run_emt_cs_example,
    run_emt_me_example,
    run_rms_cs_example,
    run_rms_me_example,
)


def main() -> int:
    """Execute the four FMU device import examples and print their report paths.

    :return: Process exit code.
    """

    output_dir = get_example_output_dir()
    reports = (
        run_rms_cs_example(output_dir),
        run_rms_me_example(output_dir),
        run_emt_cs_example(output_dir),
        run_emt_me_example(output_dir),
    )
    report_path: Path
    for report_path in reports:
        print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
