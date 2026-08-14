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
    """

    :param model:
    :param cfg:
    :return:
    """
    if not cfg.compile_binary:
        raise ValueError("Source-only FMU packaging is not implemented yet; compile_binary must be True for a standards-compliant FMU")

    snapshot = build_model_snapshot(model)  # type: ignore[arg-type]
    flat_block = flatten_model(snapshot)
    logic_entries = build_logic_entries(flat_block)
    export_model = build_export_model(flat_block, cfg, snapshot, logic_entries)
    validate_export_model(export_model)

    source_dir, build_dir, staging_dir = ensure_build_layout(cfg)
    source_dir.mkdir(parents=True, exist_ok=True)
    staging_root = prepare_fmu_staging_dir(staging_dir)

    emit_c_sources(export_model, cfg, source_dir)
    write_model_description(export_model, staging_root / "modelDescription.xml")
    write_debug_resources(export_model, cfg, staging_root / "resources")

    if cfg.compile_binary:
        library_path = build_shared_library(cfg, source_dir, build_dir)
        binaries_dir = staging_root / "binaries" / cfg.target_platform.value
        binaries_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(library_path, binaries_dir / cfg.library_name)

    output_path = package_fmu(staging_root, cfg.output_path)
    if not cfg.keep_build_dir and cfg.build_dir is None:
        shutil.rmtree(source_dir.parent, ignore_errors=True)
    return output_path
