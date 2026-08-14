# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from argparse import ArgumentParser
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

from VeraGridEngine.IO.fmu.exporter.api import export_fmu
from VeraGridEngine.IO.fmu.exporter.config import ExportConfig, IntegrationMethod, TargetPlatform, detect_target_platform
from VeraGridEngine.IO.fmu.exporter.host_validation import validate_exported_pilot
from VeraGridEngine.IO.fmu.exporter.real_pilots import get_pilot_model, pilot_output_path


def _load_module(module_arg: str) -> Any:
    module_path = Path(module_arg)
    if module_path.suffix == ".py" and module_path.exists():
        spec = spec_from_file_location(module_path.stem, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not import module from {module_arg}")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return import_module(module_arg)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Export a VeraGrid Block model as FMI 2.0 Co-Simulation")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--pilot", choices=["rms", "emt"], help="Built-in VeraGrid FMU pilot to export")
    source_group.add_argument("--module", help="Importable module name or path to a Python file")
    parser.add_argument("--factory", help="Callable returning the root Block instance")
    parser.add_argument("--model-name")
    parser.add_argument("--output")
    parser.add_argument("--step-size", type=float, default=1e-4)
    parser.add_argument("--method", choices=[method.value for method in IntegrationMethod], default=IntegrationMethod.BACKWARD_EULER.value)
    parser.add_argument("--target-platform", choices=[platform.value for platform in TargetPlatform], default=None)
    parser.add_argument("--build-dir", default=None)
    parser.add_argument("--staging-dir", default=None)
    parser.add_argument("--model-identifier", default=None)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--keep-build-dir", action="store_true")
    parser.add_argument("--skip-compile", action="store_true")
    parser.add_argument("--validate", action="store_true", help="Run FMPy validation after exporting a built-in pilot")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    target_platform = TargetPlatform(args.target_platform) if args.target_platform else detect_target_platform()

    if args.pilot:
        pilot = get_pilot_model(args.pilot)
        output_path = Path(args.output) if args.output else pilot_output_path(Path.cwd() / "dist", pilot)
        if args.validate:
            cfg = ExportConfig(
                model_name=args.model_name or pilot.name,
                output_path=output_path,
                fixed_step=args.step_size,
                integration_method=IntegrationMethod(args.method),
                target_platform=target_platform,
                build_dir=Path(args.build_dir) if args.build_dir else None,
                staging_dir=Path(args.staging_dir) if args.staging_dir else None,
                model_identifier=args.model_identifier,
                debug=args.debug,
                keep_build_dir=args.keep_build_dir,
                compile_binary=not args.skip_compile,
            )
            built_path = export_fmu(pilot.model, cfg)
            report = validate_exported_pilot(args.pilot, built_path)
            print(report)
            return 0

        cfg = ExportConfig(
            model_name=args.model_name or pilot.name,
            output_path=output_path,
            fixed_step=args.step_size,
            integration_method=IntegrationMethod(args.method),
            target_platform=target_platform,
            build_dir=Path(args.build_dir) if args.build_dir else None,
            staging_dir=Path(args.staging_dir) if args.staging_dir else None,
            model_identifier=args.model_identifier,
            debug=args.debug,
            keep_build_dir=args.keep_build_dir,
            compile_binary=not args.skip_compile,
        )
        built_path = export_fmu(pilot.model, cfg)
        print(built_path)
        return 0

    if not args.module or not args.factory:
        parser.error("--module and --factory are required when --pilot is not used")
    if not args.model_name or not args.output:
        parser.error("--model-name and --output are required when exporting from --module/--factory")

    module = _load_module(args.module)
    factory = getattr(module, args.factory, None)
    if factory is None or not callable(factory):
        parser.error(f"Factory {args.factory!r} was not found or is not callable")

    cfg = ExportConfig(
        model_name=args.model_name,
        output_path=Path(args.output),
        fixed_step=args.step_size,
        integration_method=IntegrationMethod(args.method),
        target_platform=target_platform,
        build_dir=Path(args.build_dir) if args.build_dir else None,
        staging_dir=Path(args.staging_dir) if args.staging_dir else None,
        model_identifier=args.model_identifier,
        debug=args.debug,
        keep_build_dir=args.keep_build_dir,
        compile_binary=not args.skip_compile,
    )
    output_path = export_fmu(factory(), cfg)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
