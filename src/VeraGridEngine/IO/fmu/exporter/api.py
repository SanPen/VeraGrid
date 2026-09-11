# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from pathlib import Path
import shutil

from VeraGridEngine.IO.fmu.exporter.build import build_shared_library, emit_c_sources, ensure_build_layout, write_debug_resources
from VeraGridEngine.IO.fmu.exporter.config import ExportConfig
from VeraGridEngine.IO.fmu.exporter.export_ir import build_export_model
from VeraGridEngine.IO.fmu.exporter.flatten import flatten_model
from VeraGridEngine.IO.fmu.exporter.packager import package_fmu, prepare_fmu_staging_dir
from VeraGridEngine.IO.fmu.exporter.procedural_ir import build_logic_entries
from VeraGridEngine.IO.fmu.exporter.snapshot import build_model_snapshot
from VeraGridEngine.IO.fmu.exporter.validate import validate_export_model
from VeraGridEngine.IO.fmu.exporter.xml_writer import write_model_description


def export_fmu(model: object, cfg: ExportConfig) -> Path:
    """Export one model as a compiled Co-Simulation FMU.

    :param model: VeraGrid model that owns the symbolic export block.
    :param cfg: Co-Simulation export and build configuration.
    :return: Path of the packaged FMU archive.
    """
    if not cfg.compile_binary:
        raise ValueError("Source-only FMU packaging is not implemented yet; compile_binary must be True for a standards-compliant FMU")

    snapshot = build_model_snapshot(model)  # type: ignore[arg-type]
    flat_block = flatten_model(snapshot)
    logic_entries = build_logic_entries(flat_block)
    export_model = build_export_model(flat_block, cfg, snapshot, logic_entries)
    validate_export_model(export_model)

    source_dir, build_dir, staging_dir = ensure_build_layout(cfg)
    automatic_build_root: bool = cfg.build_dir is None
    build_root: Path = source_dir.parent
    export_completed: bool = False

    try:
        # All generated inputs and staging artifacts live below the one build
        # root so the exporter can release its complete temporary ownership.
        source_dir.mkdir(parents=True, exist_ok=True)
        staging_root: Path = prepare_fmu_staging_dir(staging_dir)

        emit_c_sources(export_model, cfg, source_dir)
        write_model_description(export_model, staging_root / "modelDescription.xml")
        write_debug_resources(export_model, cfg, staging_root / "resources")

        if cfg.compile_binary:
            library_path: Path = build_shared_library(cfg, source_dir, build_dir)
            binaries_dir: Path = staging_root / "binaries" / cfg.target_platform.value
            binaries_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(library_path, binaries_dir / cfg.library_name)
        else:
            pass

        output_path: Path = package_fmu(staging_root, cfg.output_path)
        export_completed = True
        return output_path
    finally:
        if automatic_build_root and not cfg.keep_build_dir:
            # A cleanup error is observable after a successful export. During
            # an export failure it must not replace the primary exception.
            shutil.rmtree(build_root, ignore_errors=not export_completed)
        else:
            pass
