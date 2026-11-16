# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
File artifact of the native EMT program (schema veragrid-gslv-emt-program-v1).

The artifact is a directory of raw little-endian int32/float64 files and a
canonical ``manifest.json`` written last. The reader fails closed with
``ValueError`` on any integrity, structure, limit or identity mismatch and only
opens the fixed file names.
"""

from __future__ import annotations

import hashlib
import os
from typing import Dict, List, Set, Tuple

import numpy as np
import numpy.typing as npt

from VeraGridEngine.enumerations import EmtNativeOpcode
from VeraGridEngine.IO.native_artifact_files import (
    read_canonical_manifest,
    read_declared_array_file,
    require_count,
    require_key_set,
    validate_artifact_directory,
    verify_manifest_payload_hash,
    write_file_atomically,
)
from VeraGridEngine.Simulations.EMT.problems.emt_native_program import EmtNativeProgram
from VeraGridEngine.Utils.canonical_json import canonical_json_bytes


def _opcode_table() -> Dict[str, int]:
    """
    Return the opcode table written to and expected in the manifest.

    :return: Opcode name to integer code.
    """
    table: Dict[str, int] = dict()
    opcode: EmtNativeOpcode
    for opcode in EmtNativeOpcode:
        table[opcode.name] = int(opcode)
    return table


def _program_arrays(program: EmtNativeProgram) -> List[Tuple[str, npt.NDArray, np.dtype]]:
    """
    Return the fixed file names, arrays and element dtypes of a program.

    :param program: Native program.
    :return: (file name, array, dtype) in file order.
    """
    int32: np.dtype = np.dtype(np.int32)
    float64: np.dtype = np.dtype(np.float64)
    arrays: List[Tuple[str, npt.NDArray, np.dtype]] = list()
    arrays.append(("instructions.i32le", program.get_instructions(), int32))
    arrays.append(("instruction_literals.f64le", program.get_instruction_literals(), float64))
    arrays.append(("groups.i32le", program.get_groups(), int32))
    arrays.append(("runtime_map.i32le", program.get_runtime_map(), int32))
    arrays.append(("parameter_map.i32le", program.get_parameter_map(), int32))
    arrays.append(("residual_map.i32le", program.get_residual_map(), int32))
    arrays.append(("column_pointers.i32le", program.get_column_pointers(), int32))
    arrays.append(("row_indices.i32le", program.get_row_indices(), int32))
    arrays.append(("literal_parameter_values.f64le", program.get_literal_parameter_values(), float64))
    arrays.append(("group_affinity.i32le", program.get_group_affinity(), int32))
    return arrays


def _semantics() -> str:
    """
    Return the semantic note written to and expected in the manifest.

    :return: Note.
    """
    return ("DIFFERENTIAL evaluates the discretised derivative of its state with the evaluator's integration method and step; the program "
            "carries neither. The parameter vector is [event | constant | literal]; the caller supplies the event and constant part every "
            "step and the literal tail comes from literal_parameter_values. The BDF2 startup-step convention is an obligation of the "
            "consumer (GSLV M2).")


def write_emt_native_program(program: EmtNativeProgram, directory: str) -> str:
    """
    Write a native program as little-endian files and a canonical manifest written last.

    :param program: Native program.
    :param directory: Destination directory, created when missing.
    :return: Path of the written manifest.json.
    """
    os.makedirs(directory, exist_ok=True)

    # Array files first, each replaced into place.
    files: Dict[str, Dict[str, object]] = dict()
    file_name: str
    values: npt.NDArray
    dtype: np.dtype
    for file_name, values, dtype in _program_arrays(program):
        data: bytes = values.astype(dtype.newbyteorder("<")).tobytes()
        write_file_atomically(os.path.join(directory, file_name), data)
        entry: Dict[str, object] = dict()
        entry["byte_count"] = len(data)
        entry["element_count"] = int(values.shape[0])
        entry["sha256"] = hashlib.sha256(data).hexdigest()
        files[file_name] = entry

    # Canonical manifest last, carrying the hash of its own payload.
    manifest: Dict[str, object] = dict()
    manifest["schema"] = program.get_schema()
    manifest["model_identity"] = program.get_model_identity()
    manifest["n_unknowns"] = program.get_n_unknowns()
    manifest["n_states"] = program.get_n_states()
    manifest["n_event_parameters"] = program.get_n_event_parameters()
    manifest["n_constant_parameters"] = program.get_n_constant_parameters()
    manifest["n_literal_parameters"] = program.get_n_literal_parameters()
    manifest["opcodes"] = _opcode_table()
    manifest["encoding"] = "little-endian"
    manifest["fingerprint"] = program.get_fingerprint()
    manifest["semantics"] = _semantics()
    manifest["files"] = files
    manifest["manifest_payload_sha256"] = hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()

    manifest_path: str = os.path.join(directory, "manifest.json")
    write_file_atomically(manifest_path, canonical_json_bytes(manifest))
    return manifest_path


def read_emt_native_program(directory: str,
                            expected_model_identity: str,
                            maximum_file_bytes: int = 268435456,
                            maximum_manifest_bytes: int = 1048576) -> EmtNativeProgram:
    """
    Read and validate a native program artifact.

    :param directory: Artifact directory.
    :param expected_model_identity: Model identity the program must be bound to.
    :param maximum_file_bytes: Maximum size of each array file.
    :param maximum_manifest_bytes: Maximum size of manifest.json.
    :return: Validated native program.
    :raises ValueError: On any integrity, structure, limit or identity mismatch.
    """
    int32: np.dtype = np.dtype(np.int32)
    float64: np.dtype = np.dtype(np.float64)
    file_dtypes: List[Tuple[str, np.dtype]] = list((("instructions.i32le", int32), ("instruction_literals.f64le", float64),
                                                    ("groups.i32le", int32), ("runtime_map.i32le", int32), ("parameter_map.i32le", int32),
                                                    ("residual_map.i32le", int32), ("column_pointers.i32le", int32), ("row_indices.i32le", int32),
                                                    ("literal_parameter_values.f64le", float64), ("group_affinity.i32le", int32)))
    file_names: Set[str] = set()
    file_entry: Tuple[str, np.dtype]
    for file_entry in file_dtypes:
        file_names.add(file_entry[0])
    manifest_keys: Set[str] = set(("schema", "model_identity", "n_unknowns", "n_states", "n_event_parameters", "n_constant_parameters",
                                   "n_literal_parameters", "opcodes", "encoding", "fingerprint", "semantics", "files", "manifest_payload_sha256"))

    # Directory and manifest: plain directory, bounded canonical JSON, fixed key sets.
    validate_artifact_directory(directory)
    manifest: Dict[str, object] = read_canonical_manifest(directory, manifest_keys, maximum_manifest_bytes)
    n_unknowns: int = require_count(manifest["n_unknowns"], "n_unknowns")
    n_states: int = require_count(manifest["n_states"], "n_states")
    n_event_parameters: int = require_count(manifest["n_event_parameters"], "n_event_parameters")
    n_constant_parameters: int = require_count(manifest["n_constant_parameters"], "n_constant_parameters")
    n_literal_parameters: int = require_count(manifest["n_literal_parameters"], "n_literal_parameters")
    files: Dict[str, object] = require_key_set(manifest["files"], file_names, "files")
    if manifest["encoding"] != "little-endian":
        raise ValueError("Unsupported encoding")
    elif manifest["opcodes"] != _opcode_table():
        raise ValueError("The opcode table differs")
    elif manifest["semantics"] != _semantics():
        raise ValueError("The semantic note differs")
    else:
        pass
    verify_manifest_payload_hash(manifest)

    # Array files: fixed names, declared sizes and hashes, little-endian decoding.
    decoded: Dict[str, npt.NDArray] = dict()
    for file_entry in file_dtypes:
        decoded[file_entry[0]] = read_declared_array_file(directory, file_entry[0], files[file_entry[0]], file_entry[1], maximum_file_bytes)

    # Structural rules, then counts, schema, fingerprint and identity.
    program: EmtNativeProgram = EmtNativeProgram(
        model_identity=manifest["model_identity"],
        n_unknowns=n_unknowns,
        n_states=n_states,
        n_event_parameters=n_event_parameters,
        n_constant_parameters=n_constant_parameters,
        instructions=decoded["instructions.i32le"],
        instruction_literals=decoded["instruction_literals.f64le"],
        groups=decoded["groups.i32le"],
        runtime_map=decoded["runtime_map.i32le"],
        parameter_map=decoded["parameter_map.i32le"],
        residual_map=decoded["residual_map.i32le"],
        column_pointers=decoded["column_pointers.i32le"],
        row_indices=decoded["row_indices.i32le"],
        literal_parameter_values=decoded["literal_parameter_values.f64le"],
        group_affinity=decoded["group_affinity.i32le"],
    )
    if program.get_n_literal_parameters() != n_literal_parameters:
        raise ValueError("n_literal_parameters differs from literal_parameter_values")
    elif manifest["schema"] != program.get_schema():
        raise ValueError("Unsupported schema")
    elif manifest["fingerprint"] != program.get_fingerprint():
        raise ValueError("fingerprint differs")
    elif program.get_model_identity() != expected_model_identity:
        raise ValueError("model_identity differs from the expected identity")
    else:
        return program
