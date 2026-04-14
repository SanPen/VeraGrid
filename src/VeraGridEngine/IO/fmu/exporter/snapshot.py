# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .compat import Block

SNAPSHOT_SCHEMA_VERSION = 1


def build_model_snapshot(model: Block) -> dict[str, Any]:
    sanitized_mappings: list[tuple[Any, str, dict[Any, Any]]] = []

    def _walk(block: Any) -> list[Any]:
        blocks = [block]
        for child in getattr(block, "children", []) or []:
            blocks.extend(_walk(child))
        return blocks

    for block in _walk(model):
        for attr_name in ("external_mapping", "api_obj_mapping"):
            mapping = getattr(block, attr_name, None)
            if isinstance(mapping, dict) and any(value is None for value in mapping.values()):
                sanitized_mappings.append((block, attr_name, dict(mapping)))
                setattr(block, attr_name, {key: value for key, value in mapping.items() if value is not None})

    try:
        block_payload = model.to_dict()
    finally:
        for block, attr_name, original in sanitized_mappings:
            setattr(block, attr_name, original)

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "block_type": {
            "module": type(model).__module__,
            "qualname": type(model).__qualname__,
        },
        "block": block_payload,
    }


def reconstruct_block(snapshot: dict[str, Any]) -> Block:
    block_payload = snapshot.get("block", snapshot)
    return Block.parse(block_payload)


def save_snapshot(snapshot: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def load_snapshot(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
