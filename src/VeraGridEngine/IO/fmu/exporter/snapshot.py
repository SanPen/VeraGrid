# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from VeraGridEngine.IO.fmu.exporter.compat import Block
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicCodec

SNAPSHOT_SCHEMA_VERSION = 1


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


def build_model_snapshot(model: Block) -> Dict[str, object]:
    """Build the versioned declarative FMU snapshot for one symbolic block.

    ``Block.to_dict`` already preserves nullable external mappings, so snapshot
    creation reads the canonical block without temporarily mutating its graph.

    :param model: Canonical symbolic block to serialize.
    :return: Versioned snapshot containing declarative block data and type metadata.
    """
    block_payload: object = model.to_dict()
    block_type_data: Dict[str, object] = dict()
    block_type_data["module"] = type(model).__module__
    block_type_data["qualname"] = type(model).__qualname__

    snapshot: Dict[str, object] = dict()
    snapshot["schema_version"] = SNAPSHOT_SCHEMA_VERSION
    snapshot["block_type"] = block_type_data
    snapshot["block"] = block_payload
    return snapshot


def reconstruct_block(snapshot: Dict[str, object]) -> Block:
    """Reconstruct a symbolic block from a validated declarative snapshot.

    :param snapshot: Versioned snapshot or legacy direct block payload.
    :return: Reconstructed block with procedural logic decoded explicitly.
    """
    block_payload_value: object = snapshot.get("block", snapshot)
    block_payload: Dict[str, object] = _require_string_key_mapping(
        value=block_payload_value,
        context="FMU block snapshot payload",
    )
    return Block.parse(
        data=block_payload,
        procedural_logic_codec=ProceduralLogicCodec(),
    )


def save_snapshot(snapshot: Dict[str, object], path: str | Path) -> Path:
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


def load_snapshot(path: str | Path) -> Dict[str, object]:
    """Load and validate the top-level mapping of one JSON snapshot.

    :param path: Existing UTF-8 snapshot file.
    :return: Snapshot mapping with validated string keys.
    """
    serialized_snapshot: str = Path(path).read_text(encoding="utf-8")
    parsed_snapshot: object = json.loads(serialized_snapshot)
    return _require_string_key_mapping(
        value=parsed_snapshot,
        context="FMU model snapshot",
    )
