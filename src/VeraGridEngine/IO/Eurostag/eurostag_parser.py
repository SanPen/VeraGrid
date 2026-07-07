from __future__ import annotations

from pathlib import Path
from typing import Iterable

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.Eurostag.Devices.eurostag_circuit import EurostagCircuit
from VeraGridEngine.IO.Eurostag.eurostag_to_veragrid import eurostag_to_veragrid


def resolve_eurostag_files(files: str | Iterable[str]) -> tuple[Path, Path]:
    if isinstance(files, str):
        paths = [Path(files)]
    else:
        paths = [Path(file_name) for file_name in files]

    ech_path = next((path for path in paths if path.suffix.lower() == ".ech"), None)
    dta_path = next((path for path in paths if path.suffix.lower() == ".dta"), None)

    if ech_path is None and dta_path is None:
        raise ValueError("Eurostag import needs at least one .ech or .dta file")

    if ech_path is None and dta_path is not None:
        ech_path = dta_path.with_suffix(".ech")
    if dta_path is None and ech_path is not None:
        dta_path = ech_path.with_suffix(".dta")

    if ech_path is None or dta_path is None or not ech_path.exists() or not dta_path.exists():
        raise FileNotFoundError(f"Eurostag pair not found for {files!r}")

    return ech_path, dta_path


def open_eurostag(files: str | Iterable[str], logger: Logger = Logger()):
    ech_path, dta_path = resolve_eurostag_files(files)
    eurostag_grid = EurostagCircuit()
    eurostag_grid.read_files(ech_file=ech_path, dta_file=dta_path, logger=logger)
    return eurostag_to_veragrid(eurostag_grid=eurostag_grid, logger=logger)
