# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import ast
import json
from pathlib import Path

from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import (
    _build_user_dynamic_template_payload_text,
    build_dgs_dynamic_model_import_bundle,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_dynamic_association import (
    DgsDynamicAssociation,
)
from VeraGridEngine.IO.dynamic_model_import_types import (
    DynamicModelImportEntryStatus,
    DynamicModelImportSource,
)
from VeraGridEngine.IO.modelica.dynamic_model_import import (
    _collect_vars_from_modelica_expr,
    build_modelica_dynamic_model_import_bundle,
)
from VeraGridEngine.IO.modelica.modelica_parser import ExternalFunc, LogicExpr
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Func, Func2, Var
from VeraGridEngine.enumerations import (
    DeviceType,
    DgsDynamicAssociationRole,
    DynamicSimulationMode,
)


def test_dynamic_model_import_formats_have_explicit_module_boundaries() -> None:
    """Keep DGS and Modelica entry points in their source-format packages."""

    assert build_dgs_dynamic_model_import_bundle.__module__ == (
        "VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import"
    )
    assert build_modelica_dynamic_model_import_bundle.__module__ == (
        "VeraGridEngine.IO.modelica.dynamic_model_import"
    )


def test_dynamic_model_import_formats_do_not_cross_import_parsers() -> None:
    """Prevent DGS and Modelica implementations from loading each other."""

    dgs_module_path: Path = Path(
        build_dgs_dynamic_model_import_bundle.__code__.co_filename
    )
    modelica_module_path: Path = Path(
        build_modelica_dynamic_model_import_bundle.__code__.co_filename
    )
    dgs_blocks_module_path: Path = (
        dgs_module_path.parents[1] / "dgs_to_blocks.py"
    )
    dgs_tree: ast.Module = ast.parse(
        dgs_module_path.read_text(encoding="utf-8")
    )
    modelica_tree: ast.Module = ast.parse(
        modelica_module_path.read_text(encoding="utf-8")
    )
    dgs_blocks_tree: ast.Module = ast.parse(
        dgs_blocks_module_path.read_text(encoding="utf-8")
    )
    dgs_imports: list[str] = [
        node.module
        for node in ast.walk(dgs_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]
    modelica_imports: list[str] = [
        node.module
        for node in ast.walk(modelica_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]
    dgs_block_imports: list[str] = [
        node.module
        for node in ast.walk(dgs_blocks_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]

    assert not any(
        module_name.startswith("VeraGridEngine.IO.modelica")
        for module_name in dgs_imports
    )
    assert not any(
        module_name.startswith("VeraGridEngine.IO.dgs")
        for module_name in modelica_imports
    )
    assert not any(
        module_name in {
            "VeraGridEngine.Devices.Dynamic.emt_template",
            "VeraGridEngine.Devices.Dynamic.rms_template",
        }
        for module_name in dgs_block_imports
    )


def test_dynamic_model_import_modules_do_not_define_global_values() -> None:
    """Keep import state inside functions and instances."""

    module_paths: list[Path] = [
        Path(build_dgs_dynamic_model_import_bundle.__code__.co_filename),
        Path(build_dgs_dynamic_model_import_bundle.__code__.co_filename).parents[1]
        / "dgs_to_blocks.py",
        Path(build_dgs_dynamic_model_import_bundle.__code__.co_filename).with_name(
            "dgs_dynamic_association.py"
        ),
        Path(build_modelica_dynamic_model_import_bundle.__code__.co_filename),
        Path(__file__).resolve().parents[2]
        / "VeraGridEngine"
        / "IO"
        / "dynamic_model_import_types.py",
        Path(__file__).resolve().parents[2]
        / "VeraGridEngine"
        / "IO"
        / "dynamic_model_import_utils.py",
    ]
    module_path: Path

    for module_path in module_paths:
        module_tree: ast.Module = ast.parse(
            module_path.read_text(encoding="utf-8")
        )
        global_values: list[ast.stmt] = [
            node
            for node in module_tree.body
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        ]
        assert global_values == []


def test_dynamic_dgs_import_uses_available_circuit_methods() -> None:
    """Keep PowerFactory source relations local to the DGS import flow."""

    importer_path: Path = Path(
        build_dgs_dynamic_model_import_bundle.__code__.co_filename
    )
    importer_tree: ast.Module = ast.parse(
        importer_path.read_text(encoding="utf-8")
    )
    unavailable_method_calls: list[str] = [
        node.func.attr
        for node in ast.walk(importer_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr
        in {
            "add_dgs_dynamic_association",
            "get_dgs_dynamic_associations",
        }
    ]

    assert unavailable_method_calls == []


def test_dynamic_model_import_source_contract_is_format_neutral() -> None:
    """Expose source-format identifiers without importing through a parser."""

    assert [source.value for source in DynamicModelImportSource] == [
        "Modelica XML",
        "PowerFactory DGS",
    ]


def test_dynamic_dgs_association_reuses_import_contract_enums() -> None:
    """Reuse neutral import enums instead of duplicating RMS/EMT and status values."""

    association = DgsDynamicAssociation()

    assert association.device_type is DeviceType.DynamicModelHostDevice
    assert association.target_domain is DynamicSimulationMode.RMS
    assert association.status is DynamicModelImportEntryStatus.Skipped
    assert DgsDynamicAssociationRole.__module__ == "VeraGridEngine.enumerations"


def test_modelica_expression_variable_collection_visits_each_node_type() -> None:
    """Collect variables through nested arithmetic, functions and logic."""

    first_var: Var = Var("first_var")
    second_var: Var = Var("second_var")
    third_var: Var = Var("third_var")
    fourth_var: Var = Var("fourth_var")
    expression: LogicExpr = LogicExpr(
        op="and",
        args=(
            first_var + second_var,
            ExternalFunc(
                name="external_modelica_function",
                args=(
                    Func(arg=-third_var, op="sin"),
                    Func2(name="max", arg1=fourth_var, arg2=first_var),
                ),
            ),
        ),
    )
    vars_found: dict[int, Var] = dict()

    _collect_vars_from_modelica_expr(
        expression=expression,
        vars_found=vars_found,
    )

    assert set(vars_found) == {
        first_var.uid,
        second_var.uid,
        third_var.uid,
        fourth_var.uid,
    }


def test_dynamic_model_metadata_remains_declarative_json_data() -> None:
    """Keep persisted dynamic-model metadata as declarative JSON data."""

    source_block: Block = Block(name="Data-only dynamic model")
    payload_text: str = _build_user_dynamic_template_payload_text(
        block=source_block,
        template_name="Data-only dynamic model",
        target_domain=DynamicSimulationMode.RMS,
        device_tpe=DeviceType.GeneratorDevice,
    )
    payload_obj: object = json.loads(payload_text)

    assert isinstance(payload_obj, dict)
    assert payload_obj.get("template_name", None) == "Data-only dynamic model"
    assert payload_obj.get("target_domain", None) == DynamicSimulationMode.RMS.value
    assert payload_obj.get("device_tpe", None) == DeviceType.GeneratorDevice.name
    assert isinstance(payload_obj.get("block_data", None), dict)
