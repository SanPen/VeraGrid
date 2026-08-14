# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from argparse import ArgumentParser
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from VeraGridEngine.IO.fmu.exporter_me.api import export_fmu_me
from VeraGridEngine.IO.fmu.exporter_me.config import ExportConfig


def _load_module(module_path: Path):
    spec = spec_from_file_location(module_path.stem, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import module from {module_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Export a VeraGrid Block model as FMI 2.0 Model Exchange")
    parser.add_argument("--module", required=True, help="Path to a Python module that builds the model")
    parser.add_argument("--factory", required=True, help="Factory callable that returns the Block model")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--relative-tolerance", type=float, default=1e-6)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    module = _load_module(Path(args.module))
    factory = getattr(module, args.factory)
    model = factory()
    output = export_fmu_me(
        model,
        ExportConfig(
            model_name=args.model_name,
            output_path=Path(args.output),
            relative_tolerance=args.relative_tolerance,
        ),
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
