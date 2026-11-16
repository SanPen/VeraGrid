# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Read native DGS exports as rows keyed by object path, for comparing two exports in tests."""

from __future__ import annotations

import csv
from pathlib import Path


def _read_rows(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Read DGS table rows keyed by table name and exported FID.

    :param path: Native DGS export.
    :return: Rows by (table, FID).
    """
    csv.field_size_limit(10_000_000)
    rows: dict[tuple[str, str], dict[str, str]] = dict()
    table: str = ""
    columns: list[str] = list()
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as stream:
        line_number: int
        line: str
        for line_number, line in enumerate(stream, start=1):
            if line.startswith("$$"):
                header: list[str] = next(csv.reader([line[2:].rstrip("\r\n")], delimiter=";"))
                table = header[0]
                columns = list(field.rsplit("(", 1)[0] for field in header[1:])
            elif line.startswith("  ") and table:
                fields: list[str] = next(csv.reader([line.strip()], delimiter=";"))
                if len(fields) != len(columns):
                    raise ValueError(f"{path}:{line_number}: {table} has {len(fields)} values "
                                     f"for {len(columns)} columns")
                else:
                    pass
                row: dict[str, str] = dict(zip(columns, fields))
                fid: str | None = row.get("FID", None)
                if not fid:
                    raise ValueError(f"{path}:{line_number}: {table} has no FID")
                elif (table, fid) in rows:
                    raise ValueError(f"{path}:{line_number}: duplicate {table} FID {fid}")
                else:
                    rows[(table, fid)] = row
            else:
                pass
    return rows


def _object_path(fid: str, by_id: dict[str, tuple[str, dict[str, str]]], paths: dict[str, str],
                 visiting: set[str], path: Path) -> str:
    """Name one object by its folder hierarchy instead of its export-specific FID.

    :param fid: Exported object FID, or any value that is not one.
    :param by_id: Rows by FID.
    :param paths: Resolved paths, extended in place.
    :param visiting: FIDs on the current resolution chain.
    :param path: Export being read, for diagnostics.
    :return: Hierarchical object path, or the value itself when it names no object.
    """
    if fid in paths:
        return paths[fid]
    elif fid not in by_id:
        return fid
    elif fid in visiting:
        raise ValueError(f"{path}: cyclic folder references at FID {fid}")
    else:
        visiting.add(fid)
        table: str = by_id[fid][0]
        row: dict[str, str] = by_id[fid][1]
        parent: str = row.get("fold_id", "")
        name: str = row.get("loc_name", row.get("Descr", fid))
        if parent:
            result: str = f"{_object_path(parent, by_id, paths, visiting, path)}/{table}:{name}"
        else:
            result = f"{table}:{name}"
        visiting.remove(fid)
        paths[fid] = result
        return result


def read_rows_by_path(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Normalize native IDs and pointer columns using the object hierarchy.

    PowerFactory can renumber FIDs between exports even when only one parameter
    changes. References are resolved before comparing, and ambiguous object paths
    are rejected instead of silently matching the wrong instances.

    :param path: Native DGS export.
    :return: Rows by (table, object path), pointer columns resolved to object paths.
    """
    rows: dict[tuple[str, str], dict[str, str]] = _read_rows(path)
    reference_columns: dict[str, set[str]] = dict()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        line: str
        for line in stream:
            if line.startswith("$$"):
                header: list[str] = next(csv.reader([line[2:].rstrip("\r\n")], delimiter=";"))
                reference_columns[header[0]] = set(field.rsplit("(", 1)[0] for field in header[1:]
                                                   if field.endswith("(p)"))
            else:
                pass
    by_id: dict[str, tuple[str, dict[str, str]]] = dict()
    for (table, fid), row in rows.items():
        if fid in by_id:
            raise ValueError(f"{path}: FID {fid} is not globally unique")
        else:
            by_id[fid] = (table, row)
    paths: dict[str, str] = dict()
    visiting: set[str] = set()
    normalized: dict[tuple[str, str], dict[str, str]] = dict()
    for (table, fid), row in rows.items():
        key: tuple[str, str] = (table, _object_path(fid, by_id, paths, visiting, path))
        if key in normalized:
            raise ValueError(f"{path}: ambiguous object path {key[1]}")
        else:
            normalized[key] = dict(
                (column, _object_path(value, by_id, paths, visiting, path)
                 if column in reference_columns[table] else value)
                for column, value in row.items() if column not in {"FID", "ID"})
    return normalized
