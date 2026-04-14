# VeraGridEngine Module: src/VeraGridEngine/IO/ucte/devices/ucte_node.py

- Original source path: `src/VeraGridEngine/IO/ucte/devices/ucte_node.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: __future__, math, VeraGridEngine.IO.ucte.devices.ucte_base, VeraGridEngine.basic_structures

## Function: get_default_power_limit()

No docstring provided.

## Function: try_parse_voltage(val, name, logger)

Parse a UCTE nominal voltage code or a direct numeric value.

## Class: UcteNode

- Bases: none
- Summary: UcteNode

### Methods

- `_get_voltage_window()`
  Summary: No docstring provided.
- `_looks_fixed_width(self, row)`
  Summary: No docstring provided.
- `_parse_nominal_voltage(self, logger)`
  Summary: No docstring provided.
- `has_load(self)`
  Summary: No docstring provided.
- `is_regulating_voltage(self)`
  Summary: No docstring provided.
- `is_generator(self)`
  Summary: No docstring provided.
- `has_gen(self)`
  Summary: No docstring provided.
- `_normalize_limits(self, value, min_value, max_value)`
  Summary: No docstring provided.
- `normalize(self, logger)`
  Summary: No docstring provided.
- `parse(self, line, logger)`
  Summary: Parse the node record.
