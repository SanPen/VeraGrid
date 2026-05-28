from __future__ import annotations

import importlib.util
import pathlib
import struct
import sys

import atheris


def _load_raw_functions_module():
    module_path = (
        pathlib.Path(__file__).resolve().parents[1]
        / "src"
        / "VeraGridEngine"
        / "IO"
        / "raw"
        / "raw_functions.py"
    )
    spec = importlib.util.spec_from_file_location("veragrid_raw_functions", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RAW_FUNCTIONS = _load_raw_functions_module()


class _Logger:
    def add_warning(self, *args, **kwargs):
        return None

    def add_error(self, *args, **kwargs):
        return None


def _consume_float(fdp: atheris.FuzzedDataProvider) -> float:
    raw = fdp.ConsumeBytes(8)
    if len(raw) < 8:
        raw = raw.ljust(8, b"\x00")
    return struct.unpack("<d", raw)[0]


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    logger = _Logger()

    RAW_FUNCTIONS.get_psse_transformer_impedances(
        CW=fdp.ConsumeIntInRange(1, 3),
        CZ=fdp.ConsumeIntInRange(1, 3),
        CM=fdp.ConsumeIntInRange(-16, 16),
        V1=_consume_float(fdp),
        V2=_consume_float(fdp),
        sbase=_consume_float(fdp),
        logger=logger,
        code=fdp.ConsumeUnicodeNoSurrogates(32),
        MAG1=_consume_float(fdp),
        MAG2=_consume_float(fdp),
        WINDV1=_consume_float(fdp),
        WINDV2=_consume_float(fdp),
        ANG1=_consume_float(fdp),
        NOMV1=_consume_float(fdp),
        NOMV2=_consume_float(fdp),
        R1_2=_consume_float(fdp),
        X1_2=_consume_float(fdp),
        SBASE1_2=_consume_float(fdp),
    )


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
