"""Refresh the saved nonlinear STAMP WSCC grids from a STAMP_Public checkout.

This is an authoring tool. The benchmark runners use only the committed files.
Run with VeraGrid/src and STAMP_Public on PYTHONPATH.
"""

from pathlib import Path
import shutil

from veragrid_stamp.wscc_case import build_stamp_wscc_grid
from veragrid_stamp.emt_case import build_stamp_wscc_emt_grid
from VeraGridEngine.IO.file_save import FileSave


ROOT = Path(__file__).resolve().parents[2]
STAMP_ROOT = ROOT.parent / "STAMP_Public"
SOURCE_DATA = STAMP_ROOT / "veragrid_stamp" / "data"
DATA = ROOT / "src" / "tests" / "data" / "stamp_wscc"


def write_grid(name: str, grid) -> None:
    # These nearly open sequence impedances make the legacy balanced case
    # compatible with current three-phase PF initialization. They have no
    # material effect on the positive-sequence operating point.
    for generator in grid.generators:
        generator.R0 = generator.R2 = 0.0
        generator.X0 = generator.X2 = 1e6
    path = SOURCE_DATA / name
    logger = FileSave(circuit=grid, file_name=str(path)).save()
    if logger.has_errors():
        raise RuntimeError(f"Failed to save {path}: {logger}")
    print(path)
    shutil.copyfile(path, DATA / name)
    print(DATA / name)


def main() -> None:
    if not STAMP_ROOT.is_dir():
        raise FileNotFoundError(f"STAMP_Public checkout not found: {STAMP_ROOT}")
    DATA.mkdir(parents=True, exist_ok=True)
    SOURCE_DATA.mkdir(parents=True, exist_ok=True)
    write_grid("wscc_rms.veragrid", build_stamp_wscc_grid(
        dynamic_lines=True, full_dynamic_network=True,
        nonlinear_converters=True))
    write_grid("wscc_emt.veragrid", build_stamp_wscc_emt_grid(
        nonlinear_converters=True))
    source = STAMP_ROOT / "STAMP/02_results/multivac/WSCC_SG_GFOR_GFOL_eigenvalues.csv"
    shutil.copyfile(source, DATA / "stamp_rms_eigenvalues.csv")
    print(DATA / "stamp_rms_eigenvalues.csv")
    timing_source = STAMP_ROOT / "STAMP/02_results/comparison/benchmark_stamp_multivac.csv"
    shutil.copyfile(timing_source, DATA / "stamp_rms_runtime_multivac.csv")
    print(DATA / "stamp_rms_runtime_multivac.csv")


if __name__ == "__main__":
    main()
