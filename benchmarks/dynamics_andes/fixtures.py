"""Load the committed ANDES comparison grids without constructing them in a benchmark."""

from pathlib import Path

from VeraGridEngine.IO.file_open import FileOpen

DATA = Path(__file__).resolve().parents[2] / "src" / "tests" / "data" / "dynamics_andes"


def load_benchmark_grid(case: str):
    path = DATA / f"{case.lower()}.veragrid"
    if not path.is_file():
        raise FileNotFoundError(f"Missing benchmark fixture: {path}. Run generate_fixtures.py.")
    return FileOpen(file_name=str(path)).open()
