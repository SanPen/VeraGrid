"""Author the ANDES comparison grids; this script is never run by benchmarks.

Run from the repository root with ``PYTHONPATH=src:. python benchmarks/dynamics_andes/generate_fixtures.py``.
"""

from VeraGridEngine.IO.file_save import FileSave

from benchmarks.dynamics_andes.fixtures import DATA
from benchmarks.dynamics_andes.small_signal.Kundur.kundur_benchmark_case import build_kundur_rms_benchmark_grid
from benchmarks.dynamics_andes.small_signal.IEEE14.ieee14_benchmark_case import build_ieee14_rms_benchmark_grid
from benchmarks.dynamics_andes.small_signal.IEEE39.ieee39_benchmark_case import build_ieee39_rms_benchmark_grid
from benchmarks.dynamics_andes.small_signal.NPCC140.npcc140_benchmark_case import build_npcc140_rms_benchmark_grid
from benchmarks.dynamics_andes.small_signal.WECC179.wecc179_benchmark_case import build_wecc179_rms_benchmark_grid


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    for name, builder in (
        ("kundur", build_kundur_rms_benchmark_grid),
        ("ieee14", build_ieee14_rms_benchmark_grid),
        ("ieee39", build_ieee39_rms_benchmark_grid),
        ("npcc140", build_npcc140_rms_benchmark_grid),
        ("wecc179", build_wecc179_rms_benchmark_grid),
    ):
        path = DATA / f"{name}.veragrid"
        logger = FileSave(circuit=builder(), file_name=str(path)).save()
        if logger.has_errors():
            raise RuntimeError(f"Failed to save {path}: {logger}")
        print(path)


if __name__ == "__main__":
    main()
