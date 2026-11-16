# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
File handling shared by the interchange artifacts exported for external solvers.

Artifacts are directories of raw little-endian array files plus a canonical
``manifest.json`` written last. Readers fail closed with ``ValueError``: they
only open fixed names, read with bounds, reject links and junctions, and check
canonical bytes, key sets, counts, sizes and hashes.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from typing import BinaryIO, Dict, Set

import numpy as np
import numpy.typing as npt

from VeraGridEngine.Utils.canonical_json import canonical_json_bytes


def write_file_atomically(path: str, data: bytes) -> None:
    """
    Write bytes through a temporary file replaced into place.

    :param path: Destination path.
    :param data: Bytes to write.
    """
    temporary_path: str = path + ".tmp"
    handle: BinaryIO
    with open(temporary_path, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary_path, path)


def read_bounded_regular_file(path: str, limit: int) -> bytes:
    """
    Read a regular, non-link file of at most ``limit`` bytes.

    The file is checked with ``os.lstat``, opened in binary mode, its descriptor
    compared with the ``lstat`` result and read with at most ``st_size + 1``
    bytes (never more than ``limit + 1``), so a file that grew is detected
    without allocating a buffer of the full limit.

    :param path: File path.
    :param limit: Maximum accepted size in bytes.
    :return: File contents.
    :raises ValueError: When the file is missing, a link, not a regular file,
        too large, replaced between checks, or cannot be read.
    """
    try:
        link_status: os.stat_result = os.lstat(path)
    except OSError as error:
        raise ValueError("Cannot inspect " + os.path.basename(path)) from error

    if stat.S_ISLNK(link_status.st_mode):
        raise ValueError(os.path.basename(path) + " is a symbolic link")
    elif not stat.S_ISREG(link_status.st_mode):
        raise ValueError(os.path.basename(path) + " is not a regular file")
    elif link_status.st_size > limit:
        raise ValueError(os.path.basename(path) + " exceeds its size limit")
    else:
        pass

    try:
        handle: BinaryIO
        with open(path, "rb") as handle:
            open_status: os.stat_result = os.fstat(handle.fileno())
            data: bytes = handle.read(link_status.st_size + 1)
    except OSError as error:
        raise ValueError("Cannot read " + os.path.basename(path)) from error

    if open_status.st_size != link_status.st_size:
        raise ValueError(os.path.basename(path) + " changed while it was opened")
    elif link_status.st_ino != 0 and (open_status.st_ino != link_status.st_ino or open_status.st_dev != link_status.st_dev):
        raise ValueError(os.path.basename(path) + " was replaced while it was opened")
    elif len(data) > limit:
        raise ValueError(os.path.basename(path) + " exceeds its size limit")
    elif len(data) != link_status.st_size:
        raise ValueError(os.path.basename(path) + " changed while it was read")
    else:
        return data


def validate_artifact_directory(directory: str) -> None:
    """
    Check that an artifact path is a real directory, neither a link nor a junction.

    :param directory: Artifact directory.
    :raises ValueError: When the path cannot be inspected or is not a plain directory.
    """
    try:
        directory_status: os.stat_result = os.lstat(directory)
    except OSError as error:
        raise ValueError("Cannot inspect the artifact directory") from error
    if stat.S_ISLNK(directory_status.st_mode):
        raise ValueError("The artifact directory is a symbolic link")
    elif not stat.S_ISDIR(directory_status.st_mode):
        raise ValueError("The artifact path is not a directory")
    elif os.name == "nt" and directory_status.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT:
        raise ValueError("The artifact directory is a junction")
    else:
        pass


def require_count(value: object, name: str) -> int:
    """
    Check that a manifest count is an int (not bool) and non-negative.

    :param value: Parsed manifest value.
    :param name: Field name used in error messages.
    :return: The count.
    :raises ValueError: When the value is not a non-negative int.
    """
    if type(value) is not int or value < 0:
        raise ValueError(name + " must be a non-negative int")
    else:
        return value


def require_key_set(container: object, expected: Set[str], name: str) -> Dict[str, object]:
    """
    Check that a parsed manifest container is a dict with exactly the expected keys.

    :param container: Parsed manifest value.
    :param expected: Expected key set.
    :param name: Container name used in error messages.
    :return: The container.
    :raises ValueError: When the value is not a dict or its keys differ.
    """
    if type(container) is not dict:
        raise ValueError(name + " must be a JSON object")
    elif set(container.keys()) != expected:
        raise ValueError(name + " keys differ from the expected set")
    else:
        return container


def read_canonical_manifest(directory: str, expected_keys: Set[str], maximum_manifest_bytes: int) -> Dict[str, object]:
    """
    Read manifest.json with a bounded read, strict JSON, a fixed key set and canonical bytes.

    The payload hash is verified separately by each reader at its own point.

    :param directory: Artifact directory.
    :param expected_keys: Exact manifest key set.
    :param maximum_manifest_bytes: Maximum size of manifest.json.
    :return: Parsed manifest.
    :raises ValueError: When the manifest is missing, malformed, not canonical or has other keys.
    """
    manifest_bytes: bytes = read_bounded_regular_file(os.path.join(directory, "manifest.json"), maximum_manifest_bytes)
    try:
        parsed: object = json.loads(manifest_bytes.decode("utf-8"))
    except (ValueError, RecursionError) as error:
        raise ValueError("manifest.json is not valid UTF-8 JSON") from error
    manifest: Dict[str, object] = require_key_set(parsed, expected_keys, "manifest")
    if canonical_json_bytes(manifest) != manifest_bytes:
        raise ValueError("manifest.json is not in canonical form")
    else:
        return manifest


def verify_manifest_payload_hash(manifest: Dict[str, object]) -> None:
    """
    Check manifest_payload_sha256 against the canonical bytes of the rest of the manifest.

    :param manifest: Parsed manifest containing manifest_payload_sha256.
    :raises ValueError: When the hash differs.
    """
    payload: Dict[str, object] = dict(manifest)
    payload.pop("manifest_payload_sha256")
    if manifest["manifest_payload_sha256"] != hashlib.sha256(canonical_json_bytes(payload)).hexdigest():
        raise ValueError("manifest_payload_sha256 differs")
    else:
        pass


def read_declared_array_file(directory: str, file_name: str, entry: object, dtype: np.dtype, maximum_file_bytes: int) -> npt.NDArray:
    """
    Read one array file declared in the manifest and decode it from little-endian.

    :param directory: Artifact directory.
    :param file_name: Fixed file name (never taken from the manifest).
    :param entry: Manifest entry with exactly byte_count, element_count and sha256.
    :param dtype: Native element dtype; its item size fixes the expected byte count.
    :param maximum_file_bytes: Maximum size of the file.
    :return: Decoded array in native byte order.
    :raises ValueError: When the entry, the size or the hash does not match.
    """
    hex_digits: str = "0123456789abcdef"
    declared: Dict[str, object] = require_key_set(entry, set(("byte_count", "element_count", "sha256")), file_name)
    byte_count: int = require_count(declared["byte_count"], file_name + " byte_count")
    element_count: int = require_count(declared["element_count"], file_name + " element_count")
    digest: object = declared["sha256"]
    if type(digest) is not str or len(digest) != 64 or not set(digest).issubset(set(hex_digits)):
        raise ValueError(file_name + " sha256 must be 64 lowercase hex characters")
    else:
        pass
    data: bytes = read_bounded_regular_file(os.path.join(directory, file_name), maximum_file_bytes)
    if len(data) != byte_count or len(data) != dtype.itemsize * element_count:
        raise ValueError(file_name + " size differs from the manifest")
    elif hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(file_name + " sha256 differs")
    else:
        return np.frombuffer(data, dtype=dtype.newbyteorder("<")).astype(dtype)
