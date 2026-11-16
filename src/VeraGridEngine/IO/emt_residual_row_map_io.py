# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
File artifact of the EMT residual row map.

The artifact is a directory with raw little-endian int32 files
(``row_affinity.i32le``, ``opaque_rows.i32le``,
``nonlinear_support_columns.i32le``) and a canonical ``manifest.json`` written
last. The reader fails closed with ``ValueError`` on any integrity, structure,
limit or identity mismatch and only opens the fixed file names.
"""

from __future__ import annotations

import hashlib
import os
from typing import Dict, List, Set, Tuple

import numpy as np
import numpy.typing as npt

from VeraGridEngine.enumerations import ResidualRowAffinityCode
from VeraGridEngine.IO.native_artifact_files import (
    read_canonical_manifest,
    read_declared_array_file,
    require_count,
    require_key_set,
    validate_artifact_directory,
    verify_manifest_payload_hash,
    write_file_atomically,
)
from VeraGridEngine.Simulations.EMT.problems.emt_residual_row_classification import EmtResidualRowMap
from VeraGridEngine.Utils.canonical_json import canonical_json_bytes


def _affinity_code_table() -> Dict[str, int]:
    """
    Return the affinity code table written to and expected in the manifest.

    :return: Code name to integer code.
    """
    table: Dict[str, int] = dict()
    code: ResidualRowAffinityCode
    for code in ResidualRowAffinityCode:
        table[code.name] = int(code)
    return table


def write_emt_residual_row_map(row_map: EmtResidualRowMap, directory: str) -> str:
    """
    Write a residual row map as little-endian int32 files and a canonical manifest.

    :param row_map: Residual row map to write.
    :param directory: Destination directory, created when missing.
    :return: Path of the written manifest.json.
    """
    os.makedirs(directory, exist_ok=True)
    arrays: List[Tuple[str, npt.NDArray[np.int32]]] = list()
    arrays.append(("row_affinity.i32le", row_map.get_row_affinity()))
    arrays.append(("opaque_rows.i32le", row_map.get_opaque_rows()))
    arrays.append(("nonlinear_support_columns.i32le", row_map.get_nonlinear_support_columns()))

    # Array files first, each replaced into place.
    files: Dict[str, Dict[str, object]] = dict()
    file_name: str
    values: npt.NDArray[np.int32]
    for file_name, values in arrays:
        data: bytes = values.astype("<i4").tobytes()
        write_file_atomically(os.path.join(directory, file_name), data)
        entry: Dict[str, object] = dict()
        entry["byte_count"] = len(data)
        entry["element_count"] = int(values.shape[0])
        entry["sha256"] = hashlib.sha256(data).hexdigest()
        files[file_name] = entry

    # Canonical manifest last, carrying the hash of its own payload.
    manifest: Dict[str, object] = dict()
    manifest["schema"] = row_map.get_schema()
    manifest["model_identity"] = row_map.get_model_identity()
    manifest["n_rows"] = row_map.get_n_rows()
    manifest["n_columns"] = row_map.get_n_columns()
    manifest["state_row_count"] = row_map.get_state_row_count()
    manifest["affinity_codes"] = _affinity_code_table()
    manifest["encoding"] = "int32-little-endian"
    manifest["layout_fingerprint"] = row_map.get_layout_fingerprint()
    manifest["semantics"] = row_map.get_semantics()
    manifest["files"] = files
    manifest["manifest_payload_sha256"] = hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()

    manifest_path: str = os.path.join(directory, "manifest.json")
    write_file_atomically(manifest_path, canonical_json_bytes(manifest))
    return manifest_path


def read_emt_residual_row_map(directory: str,
                              expected_model_identity: str,
                              maximum_file_bytes: int = 268435456,
                              maximum_manifest_bytes: int = 1048576) -> EmtResidualRowMap:
    """
    Read and validate a residual row map artifact.

    :param directory: Artifact directory.
    :param expected_model_identity: Model identity the map must be bound to.
    :param maximum_file_bytes: Maximum size of each array file.
    :param maximum_manifest_bytes: Maximum size of manifest.json.
    :return: Validated residual row map with native int32 arrays.
    :raises ValueError: On any integrity, structure, limit or identity mismatch.
    """
    file_names: Tuple[str, str, str] = ("row_affinity.i32le", "opaque_rows.i32le", "nonlinear_support_columns.i32le")
    manifest_keys: Set[str] = set(("schema", "model_identity", "n_rows", "n_columns", "state_row_count", "affinity_codes", "encoding",
                                   "layout_fingerprint", "semantics", "files", "manifest_payload_sha256"))

    # Directory: a real directory, neither a symbolic link nor a junction.
    validate_artifact_directory(directory)

    # Manifest: bounded read, strict JSON, canonical bytes, fixed key sets.
    manifest: Dict[str, object] = read_canonical_manifest(directory, manifest_keys, maximum_manifest_bytes)
    n_rows: int = require_count(manifest["n_rows"], "n_rows")
    n_columns: int = require_count(manifest["n_columns"], "n_columns")
    state_row_count: int = require_count(manifest["state_row_count"], "state_row_count")
    files: Dict[str, object] = require_key_set(manifest["files"], set(file_names), "files")
    if manifest["encoding"] != "int32-little-endian":
        raise ValueError("Unsupported encoding")
    elif manifest["affinity_codes"] != _affinity_code_table():
        raise ValueError("The affinity code table differs")
    else:
        pass
    verify_manifest_payload_hash(manifest)

    # Array files: fixed names, declared sizes and hashes, little-endian decoding.
    decoded: Dict[str, npt.NDArray[np.int32]] = dict()
    file_name: str
    for file_name in file_names:
        decoded[file_name] = read_declared_array_file(directory, file_name, files[file_name], np.dtype(np.int32), maximum_file_bytes)

    # Structural invariants, then semantics, fingerprint and identity.
    row_map: EmtResidualRowMap = EmtResidualRowMap(
        model_identity=manifest["model_identity"],
        n_rows=n_rows,
        n_columns=n_columns,
        state_row_count=state_row_count,
        row_affinity=decoded["row_affinity.i32le"],
        opaque_rows=decoded["opaque_rows.i32le"],
        nonlinear_support_columns=decoded["nonlinear_support_columns.i32le"],
    )
    if manifest["schema"] != row_map.get_schema():
        raise ValueError("Unsupported schema")
    elif manifest["semantics"] != row_map.get_semantics():
        raise ValueError("The semantic note differs")
    elif manifest["layout_fingerprint"] != row_map.get_layout_fingerprint():
        raise ValueError("layout_fingerprint differs")
    elif row_map.get_model_identity() != expected_model_identity:
        raise ValueError("model_identity differs from the expected identity")
    else:
        return row_map
