from __future__ import annotations

from pathlib import Path


def read_text_with_fallback(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def clean_text(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def slice_text(row: str, a: int, b: int) -> str:
    if a >= len(row):
        return ""
    return clean_text(row[a:min(b, len(row))])


def slice_float(row: str, a: int, b: int, default: float = 0.0) -> float:
    chunk = slice_text(row, a, b)
    if chunk == "":
        return default
    try:
        return float(chunk)
    except ValueError:
        return default


def slice_int(row: str, a: int, b: int, default: int = 0) -> int:
    chunk = slice_text(row, a, b)
    if chunk == "":
        return default
    try:
        return int(chunk)
    except ValueError:
        try:
            return int(float(chunk))
        except ValueError:
            return default


def is_closed(opening_code: str | None) -> bool:
    return clean_text(opening_code) not in {">", "<", "-"}
