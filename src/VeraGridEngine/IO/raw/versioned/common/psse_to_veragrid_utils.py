# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any, TypeVar

T = TypeVar("T")


def clean_psse_name(value: Any) -> str:
    """Normalize quoted/blank PSSE labels in a single place."""
    return str(value).replace("'", "").strip()


def as_active_flag(value: Any, default: bool = True) -> bool:
    """Robust conversion from RAW status fields to bool."""
    if value is None:
        return default
    try:
        return bool(int(value))
    except Exception:
        return default


def get_required(mapping: dict[Any, T], key: Any, what: str) -> T:
    """Strict dictionary lookup with explicit context."""
    if key not in mapping:
        raise KeyError(f"Missing required {what}: {key}")
    return mapping[key]


def nz(value: Any, default: float = 0.0) -> float:
    """Return numeric value or default when missing/invalid."""
    try:
        return float(value)
    except Exception:
        return default
