from __future__ import annotations

from pathlib import Path

import pytest

from VeraGridEngine.IO.fmu.exporter.build import host_build_capable
from VeraGridEngine.IO.fmu.importer.examples.common import run_rms_cs_example


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
def test_rms_fmu_example_runs_end_to_end(tmp_path: Path) -> None:
    """
    Export one FMU, attach it to a load, and run the RMS example end to end.

    :param tmp_path: Temporary pytest output directory.
    :return: None.
    """

    pytest.importorskip("fmpy")

    report_path = run_rms_cs_example(tmp_path)
    report_text = report_path.read_text(encoding="utf-8")

    assert report_path.exists()
    assert "mode = CoSimulation" in report_text
    assert "final_time = " in report_text
