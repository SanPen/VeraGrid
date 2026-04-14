from __future__ import annotations

from pathlib import Path
import zipfile

from VeraGridEngine.IO.fmu.exporter.compat import Block, Const, Var
from VeraGridEngine.IO.fmu.exporter.config import ExportConfig
from VeraGridEngine.IO.fmu.exporter.export_ir import build_export_model
from VeraGridEngine.IO.fmu.exporter.flatten import flatten_block
from VeraGridEngine.IO.fmu.exporter.packager import package_fmu, prepare_fmu_staging_dir
from VeraGridEngine.IO.fmu.exporter.procedural_ir import build_logic_entries
from VeraGridEngine.IO.fmu.exporter.snapshot import build_model_snapshot, reconstruct_block
from VeraGridEngine.IO.fmu.exporter.xml_writer import emit_model_description


def build_simple_block() -> Block:
    x = Var("x")
    dx = Var("dx", base_var=x)
    y = Var("y")
    u = Var("u")
    p = Var("p")
    mode = Var("mode")

    child = Block(
        state_vars=[x],
        state_eqs=[-x + u + p],
        algebraic_vars=[y],
        algebraic_eqs=[y - x],
        diff_vars=[dx],
        parameters={p: Const(2.0)},
        init_values={x: Const(1.0), y: Const(1.0)},
        init_eqs={y: x},
        event_dict={mode: Const(1.0)},
        in_vars=[u],
        out_vars=[y],
    )
    return Block(children=[child], name="SimpleModel")


def test_snapshot_roundtrip_and_flatten() -> None:
    block = build_simple_block()
    snapshot = build_model_snapshot(block)
    restored = reconstruct_block(snapshot)
    flat = flatten_block(restored)

    assert len(flat.children) == 0
    assert len(flat.state_vars) == 1
    assert len(flat.algebraic_vars) == 1
    assert len(flat.diff_vars) == 1
    assert len(flat.in_vars) == 1
    assert len(flat.out_vars) == 1
    assert flat.parameters
    assert flat.event_dict


def test_export_ir_and_xml_generation(tmp_path: Path) -> None:
    block = build_simple_block()
    snapshot = build_model_snapshot(block)
    flat = flatten_block(block)
    cfg = ExportConfig(model_name="SimpleModel", output_path=tmp_path / "simple.fmu", compile_binary=False)
    logic_entries = build_logic_entries(flat)
    export_model = build_export_model(flat, cfg, snapshot, logic_entries)
    xml_text = emit_model_description(export_model)

    assert export_model.counts["states"] == 1
    assert export_model.counts["algebraics"] == 1
    assert export_model.counts["inputs"] == 1
    assert export_model.counts["outputs"] == 1
    assert 'modelName="SimpleModel"' in xml_text
    assert "<CoSimulation" in xml_text
    assert 'name="y"' in xml_text


def test_packager_creates_fmu_zip(tmp_path: Path) -> None:
    staging = prepare_fmu_staging_dir(tmp_path / "staging")
    (staging / "modelDescription.xml").write_text("<xml />", encoding="utf-8")
    (staging / "resources" / "manifest.json").write_text("{}", encoding="utf-8")
    output = package_fmu(staging, tmp_path / "demo.fmu")

    assert output.exists()
    with zipfile.ZipFile(output) as archive:
        assert "modelDescription.xml" in archive.namelist()
        assert "resources/manifest.json" in archive.namelist()
