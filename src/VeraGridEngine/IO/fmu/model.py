# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import json
from copy import deepcopy
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, TypedDict, cast

from VeraGridEngine.Utils.Symbolic.block import Block, flatten_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicCodec
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.symbolic_io import BlockParser, BlockSaver
from VeraGridEngine.IO.fmu.snapshot_legacy import convert_legacy_snapshot
from VeraGridEngine.basic_structures import Logger


class FmuSnapshotVersion(IntEnum):
    """Identify the self-contained and symbolic-table snapshot formats."""

    SELF_CONTAINED = 1
    SYMBOLIC_TABLES = 2


class FmuBlockType(TypedDict):
    """Serialized Python type identity of the source block."""

    module: str
    qualname: str


class FmuModelSnapshot(TypedDict):
    """FMU source model whose block field contains versioned symbolic data.

    Version one embeds a self-contained block; version two stores the complete
    BlockSaver tables.
    """

    schema_version: int
    block_type: FmuBlockType
    block: Dict[str, Any]


def _require_string_key_mapping(value: object, context: str) -> Dict[str, object]:
    """Validate one JSON object before it crosses into symbolic reconstruction.

    :param value: Parsed JSON value expected to contain a mapping.
    :param context: Domain description included in validation failures.
    :return: Independent mapping whose keys are all strings.
    """
    if isinstance(value, dict):
        validated_mapping: Dict[str, object] = dict()
        raw_key: object
        raw_value: object
        for raw_key, raw_value in value.items():
            if isinstance(raw_key, str):
                validated_mapping[raw_key] = raw_value
            else:
                raise TypeError(f"{context} keys must be strings")
        else:
            pass
        return validated_mapping
    else:
        raise TypeError(f"{context} must be a mapping")


def build_model_snapshot(model: Block) -> FmuModelSnapshot:
    """Build the versioned declarative FMU snapshot for one symbolic block.

    :param model: Canonical symbolic block to serialize.
    :return: Versioned snapshot containing declarative block data and type metadata.
    """
    # The saver normalizes contracts and initialization. Work on an owned copy
    # so exporting cannot alter the live editor or simulation model.
    owned_model: Block = deepcopy(model)
    factory: VarFactory = VarFactory()
    owner: Block
    variables: List[Var]
    variable: Var
    for owner in owned_model.get_all_blocks():
        for variables in (owner.state_vars, owner.algebraic_vars, owner.in_vars,
                          owner.out_vars, owner.reformulated_vars):
            for variable in variables:
                _register_snapshot_variable(factory, variable)
        for variable in owner.diff_vars:
            _register_snapshot_variable(factory, variable)
    saver: BlockSaver = BlockSaver(factory)
    saver.save_block(owned_model)
    # Expressions may introduce additional variables. Close their derivative
    # dependencies and shared-reference table after the saver has found them.
    for variable in tuple(factory.get_vars_dict().values()):
        _register_snapshot_variable(factory, variable)
    for variable in tuple(factory.get_diff_var_dict().values()):
        _register_snapshot_variable(factory, variable)
    # Reconstruct internal alias edges from stable identities. The block does
    # not own the editor's factory, so unrelated editor connections are excluded.
    source_by_uid: Dict[int, Var] = dict()
    for variable in factory.get_vars_dict().values():
        if variable.non_mutable_uid == variable.uid:
            source_by_uid[variable.uid] = variable
        else:
            pass
    for variable in factory.get_vars_dict().values():
        source: Var | None = source_by_uid.get(variable.uid, None)
        if source is not None and source is not variable:
            factory.register_symbolic_connection(source_var=source, target_var=variable)
        else:
            pass
    block_payload: Dict[str, Any] = dict(
        references=saver.get_shared_references_to_save(),
        constants=saver.get_const_to_save(),
        variables=saver.get_vars_to_save(),
        differential_variables=saver.get_diff_vars_to_save(),
        connections=saver.get_connections_to_save(),
        blocks=saver.get_blocks(),
    )
    block_type_data: FmuBlockType = dict()
    block_type_data["module"] = type(model).__module__
    block_type_data["qualname"] = type(model).__qualname__

    snapshot: FmuModelSnapshot = dict()
    snapshot["schema_version"] = int(FmuSnapshotVersion.SYMBOLIC_TABLES)
    snapshot["block_type"] = block_type_data
    snapshot["block"] = block_payload
    return snapshot


def _register_snapshot_variable(factory: VarFactory, variable: Var) -> None:
    """Retain declared variables and the dependencies of derivative chains.

    :param factory: Owned snapshot registry.
    :param variable: Declared or referenced variable to retain.
    :return: None.
    """
    if variable.base_var is None:
        factory.get_vars_dict()[variable.non_mutable_uid] = variable
    else:
        _register_snapshot_variable(factory, variable.base_var)
        factory.get_diff_var_dict()[variable.non_mutable_uid] = variable
    if variable.shared_ref is not None:
        factory.get_references_dict()[variable.shared_ref.name] = variable.shared_ref
    else:
        pass


def reconstruct_block(snapshot: FmuModelSnapshot) -> Block:
    """Reconstruct a symbolic block from a validated declarative snapshot.

    :param snapshot: Versioned snapshot or legacy direct block payload.
    :return: Reconstructed block with procedural logic decoded explicitly.
    """
    version: int = snapshot.get("schema_version", int(FmuSnapshotVersion.SELF_CONTAINED))
    block_payload: Dict[str, Any] = _require_string_key_mapping(
        value=snapshot.get("block", snapshot),
        context="FMU block snapshot payload",
    )
    if version == FmuSnapshotVersion.SELF_CONTAINED:
        block_payload = convert_legacy_snapshot(block_payload)
    elif version == FmuSnapshotVersion.SYMBOLIC_TABLES:
        pass
    else:
        raise ValueError(f"Unsupported FMU snapshot schema version: {version}")

    logger: Logger = Logger()
    parser: BlockParser = BlockParser(VarFactory(), logger=logger, procedural_logic_codec=ProceduralLogicCodec())
    symbolic_data: Dict[str, Any] = dict(
        shared_references=block_payload["references"],
        consts=block_payload["constants"],
        vars=block_payload["variables"],
        diff_vars=block_payload["differential_variables"],
        connections=block_payload["connections"],
        blocks=block_payload["blocks"],
    )
    roots: List[Block] = parser.parse(data=symbolic_data)
    if len(roots) != 1:
        raise ValueError("An FMU snapshot must reconstruct exactly one root block")
    elif logger.error_count() > 0 or logger.warning_count() > 0:
        raise ValueError(f"Incomplete FMU snapshot symbolic data: {logger}")
    else:
        return roots[0]


def save_snapshot(snapshot: FmuModelSnapshot, path: str | Path) -> Path:
    """Persist one declarative snapshot as deterministic UTF-8 JSON.

    :param snapshot: Validated snapshot data to persist.
    :param path: Destination file path.
    :return: Resolved destination represented as a ``Path`` instance.
    """
    output_path: Path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized_snapshot: str = json.dumps(snapshot, indent=2, sort_keys=True)
    output_path.write_text(serialized_snapshot, encoding="utf-8")
    return output_path


def load_snapshot(path: str | Path) -> FmuModelSnapshot:
    """Load and validate the top-level mapping of one JSON snapshot.

    :param path: Existing UTF-8 snapshot file.
    :return: Snapshot mapping with validated string keys.
    """
    serialized_snapshot: str = Path(path).read_text(encoding="utf-8")
    parsed_snapshot: object = json.loads(serialized_snapshot)
    loaded_snapshot: Dict[str, object] = _require_string_key_mapping(
        value=parsed_snapshot,
        context="FMU model snapshot",
    )
    return cast(FmuModelSnapshot, loaded_snapshot)


def _validate_no_duplicate_names(vars_list: List[Var], label: str) -> None:
    """Execute the `_validate_no_duplicate_names` operation.

    :param vars_list: Function input.
    :param label: Function input.
    :return: Function result.
    """
    names = [var.name for var in vars_list]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"Duplicate {label} names in flattened model: {', '.join(duplicates)}")


def validate_flat_block(block: Block) -> None:
    """Execute the `validate_flat_block` operation.

    :param block: Function input.
    :return: Function result.
    """
    _validate_no_duplicate_names(block.state_vars, "state")
    _validate_no_duplicate_names(block.algebraic_vars, "algebraic")
    _validate_no_duplicate_names(block.diff_vars, "differential")

    if len(block.state_vars) != len(block.state_eqs):
        raise ValueError(
            f"FMU export requires one state equation per state variable; got {len(block.state_vars)} states and {len(block.state_eqs)} state equations"
        )
    if len(block.algebraic_vars) != len(block.algebraic_eqs):
        raise ValueError(
            f"FMU export requires one algebraic equation per algebraic variable; got {len(block.algebraic_vars)} algebraics and {len(block.algebraic_eqs)} algebraic equations"
        )

    known_uids = {var.uid for var in block.state_vars + block.algebraic_vars + block.diff_vars}
    known_uids.update(var.uid for var in block.parameters.keys())
    known_uids.update(var.uid for var in block.event_dict.keys())
    known_uids.update(var.uid for var in block.mode_dict.keys())

    missing_outputs = sorted(var.name for var in block.out_vars if var.uid not in known_uids)
    if missing_outputs:
        raise ValueError(f"Output vars must exist in the flattened model symbol table: {', '.join(missing_outputs)}")

    missing_params = sorted(var.name for var, value in block.parameters.items() if not isinstance(value, Const) or value.value is None)
    if missing_params:
        raise ValueError(f"Constant parameters without concrete values are not exportable: {', '.join(missing_params)}")


def flatten_model(snapshot: FmuModelSnapshot) -> Block:
    """Execute the `flatten_model` operation.

    :param snapshot: Function input.
    :return: Function result.
    """
    block_copy: Block = reconstruct_block(snapshot)
    flat_block: Block = flatten_block(block_copy)
    validate_flat_block(flat_block)
    return flat_block
