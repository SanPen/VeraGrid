# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math

from VeraGridEngine.basic_structures import Logger


def is_defined_number(value: float | int | None) -> bool:
    """
    Check if a numeric value is defined.
    """
    if value is None:
        return False

    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def coalesce_number(value: float | int | None, fallback: float | int):
    """
    Return the fallback for undefined numeric values.
    """
    return value if is_defined_number(value) else fallback


def _sub_chunk(line: str, a: int, b: int) -> tuple[str, bool]:
    """
    Extract a fixed-width chunk and report whether the full slice was available.
    """
    row = line.rstrip("\r\n")

    if a >= len(row):
        return "", False

    end = min(b, len(row))
    return row[a:end].strip(), len(row) >= b


def try_float(val: str, device: str, prop_name: str, logger: Logger, fallback_value: float = 0):
    """
    Parse a float and log malformed values.
    """
    chunk = val.strip()

    try:
        return float(chunk)
    except ValueError as e:
        logger.add_error(msg=str(e),
                         device=device,
                         device_property=prop_name,
                         value=chunk)
        return fallback_value


def try_optional_float(val: str,
                       device: str,
                       prop_name: str,
                       logger: Logger,
                       fallback_value: float = math.nan) -> float:
    """
    Parse an optional float without logging on blank values.
    """
    chunk = val.strip()

    if chunk == "":
        return fallback_value

    return try_float(chunk, device, prop_name, logger, fallback_value)


def sub_float(line: str, a: int, b: int, device: str, prop_name: str, logger: Logger,
              fallback_value: float = 0.0) -> float:
    """
    Try to get a value from a substring.
    """
    chunk, complete = _sub_chunk(line, a, b)

    if chunk == "":
        if complete:
            logger.add_error(msg="Property not provided",
                             device=device,
                             device_property=prop_name,
                             value=line)
        else:
            logger.add_warning(msg=f"Could not parse property <{prop_name}> "
                                   f"because the file row is too short, "
                                   f"setting fallback value",
                               device=device,
                               device_property=prop_name,
                               value=line,
                               expected_value=b)
        return fallback_value

    return try_float(chunk, device, prop_name, logger, fallback_value)


def sub_optional_float(line: str, a: int, b: int, device: str, prop_name: str, logger: Logger,
                       fallback_value: float = math.nan) -> float:
    """
    Try to get an optional float from a substring.
    """
    chunk, _ = _sub_chunk(line, a, b)

    if chunk == "":
        return fallback_value

    return try_float(chunk, device, prop_name, logger, fallback_value)


def try_int(val: str, device: str, prop_name: str, logger: Logger, fallback_value: int = 0):
    """
    Parse an integer, accepting float-looking strings as a salvage path.
    """
    chunk = val.strip()

    try:
        return int(chunk)
    except ValueError:
        val2 = try_float(val=chunk,
                         device=device,
                         prop_name=prop_name,
                         logger=logger,
                         fallback_value=0)

        try:
            return int(val2)
        except ValueError as e:
            logger.add_error(msg=str(e),
                             device=device,
                             device_property=prop_name,
                             value=chunk)
            return fallback_value


def try_optional_int(val: str,
                     device: str,
                     prop_name: str,
                     logger: Logger,
                     fallback_value: int | None = None) -> int | None:
    """
    Parse an optional integer without logging on blank values.
    """
    chunk = val.strip()

    if chunk == "":
        return fallback_value

    return try_int(chunk, device, prop_name, logger, 0 if fallback_value is None else fallback_value)


def sub_int(line: str, a: int, b: int, device: str, prop_name: str, logger: Logger,
            fallback_value: int = 0) -> int:
    """
    Try to get a value from a substring.
    """
    chunk, complete = _sub_chunk(line, a, b)

    if chunk == "":
        if complete:
            logger.add_error(msg="Property not provided",
                             device=device,
                             device_property=prop_name,
                             value=line)
        else:
            logger.add_error(msg=f"Could not parse <{prop_name}> because the file row is too short",
                             device=device,
                             device_property=prop_name,
                             value=line,
                             expected_value=b)
        return fallback_value

    return try_int(chunk, device, prop_name, logger, fallback_value)


def sub_optional_int(line: str, a: int, b: int, device: str, prop_name: str, logger: Logger,
                     fallback_value: int | None = None) -> int | None:
    """
    Try to get an optional integer from a substring.
    """
    chunk, _ = _sub_chunk(line, a, b)

    if chunk == "":
        return fallback_value

    return try_int(chunk, device, prop_name, logger, 0 if fallback_value is None else fallback_value)


def sub_str(line: str, a: int, b: int, device: str, prop_name: str, logger: Logger,
            fallback_value: str = "") -> str:
    """
    Try to get a value from a substring.
    """
    chunk, complete = _sub_chunk(line, a, b)

    if complete or chunk != "":
        return chunk

    if prop_name != "":
        logger.add_error(msg=f"Could not parse <{prop_name}> because the file row is too short",
                         device=device,
                         device_property=prop_name,
                         value=line,
                         expected_value=b)

    return fallback_value


def ucte_split(line: str,
               prefix_lengths: tuple[int, ...] = (),
               total_fields: int | None = None,
               greedy_tail: bool = False,
               skip_all_separators: bool = False) -> list[str]:
    """
    Split malformed UCTE rows while preserving fixed-width identifiers.

    The standard is fixed-width, but many files are right-trimmed or collapse
    separators. This helper keeps the left-most fixed-width fields intact and
    only tokenizes the remainder.
    """
    row = line.rstrip("\r\n")
    fields: list[str] = list()
    cursor = 0

    for length in prefix_lengths:
        if cursor >= len(row):
            fields.append("")
        else:
            end = min(cursor + length, len(row))
            fields.append(row[cursor:end].strip())
            cursor = end

        if cursor < len(row) and row[cursor].isspace():
            cursor += 1
            if skip_all_separators:
                while cursor < len(row) and row[cursor].isspace():
                    cursor += 1

    remainder = row[cursor:].split()

    if total_fields is None:
        return fields + remainder

    remaining_fields = max(total_fields - len(fields), 0)
    if remaining_fields == 0:
        return fields[:total_fields]

    if greedy_tail and len(remainder) > remaining_fields:
        fields.extend(remainder[:remaining_fields - 1])
        fields.append(" ".join(remainder[remaining_fields - 1:]))
    else:
        fields.extend(remainder[:remaining_fields])

    if len(fields) < total_fields:
        fields.extend([""] * (total_fields - len(fields)))

    return fields
