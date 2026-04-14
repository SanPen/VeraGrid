# VeraGridEngine Module: src/VeraGridEngine/IO/base/units.py

- Original source path: `src/VeraGridEngine/IO/base/units.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 1
- Representative imports: enum

## Class: UnitSymbol

- Bases: Enum
- Summary: Unit symbol

### Methods

- `argparse(s)`
  Summary: No docstring provided.
- `list(cls)`
  Summary: No docstring provided.

## Class: UnitMultiplier

- Bases: Enum
- Summary: Unit multiplier

### Methods

- `argparse(s)`
  Summary: No docstring provided.
- `list(cls)`
  Summary: No docstring provided.
- `toNum(self)`
  Summary: No docstring provided.

## Function: UnitMultiplier2num(val)

Convert unit multiplier to the corresponding number

## Class: Unit

- Bases: none
- Summary: General unit

### Methods

- `has_unit(self)`
  Summary: Has units?
- `get_unit(self)`
  Summary: :return:
- `get_kv()`
  Summary: No docstring provided.
- `get_km()`
  Summary: No docstring provided.
- `get_pu()`
  Summary: No docstring provided.
- `get_ohm()`
  Summary: No docstring provided.
- `get_deg()`
  Summary: No docstring provided.
- `get_rad()`
  Summary: No docstring provided.
- `get_percent()`
  Summary: No docstring provided.
- `get_a()`
  Summary: No docstring provided.
- `get_kw()`
  Summary: No docstring provided.
- `get_mw()`
  Summary: No docstring provided.
- `get_mva()`
  Summary: No docstring provided.
- `get_mvar()`
  Summary: No docstring provided.
