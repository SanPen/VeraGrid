# VeraGridEngine Module: src/VeraGridEngine/IO/ucte/devices/ucte_base.py

- Original source path: `src/VeraGridEngine/IO/ucte/devices/ucte_base.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 13
- Representative imports: __future__, math, VeraGridEngine.basic_structures

## Function: is_defined_number(value)

Check if a numeric value is defined.

## Function: coalesce_number(value, fallback)

Return the fallback for undefined numeric values.

## Function: _sub_chunk(line, a, b)

Extract a fixed-width chunk and report whether the full slice was available.

## Function: try_float(val, device, prop_name, logger, fallback_value)

Parse a float and log malformed values.

## Function: try_optional_float(val, device, prop_name, logger, fallback_value)

Parse an optional float without logging on blank values.

## Function: sub_float(line, a, b, device, prop_name, logger, fallback_value)

Try to get a value from a substring.

## Function: sub_optional_float(line, a, b, device, prop_name, logger, fallback_value)

Try to get an optional float from a substring.

## Function: try_int(val, device, prop_name, logger, fallback_value)

Parse an integer, accepting float-looking strings as a salvage path.

## Function: try_optional_int(val, device, prop_name, logger, fallback_value)

Parse an optional integer without logging on blank values.

## Function: sub_int(line, a, b, device, prop_name, logger, fallback_value)

Try to get a value from a substring.

## Function: sub_optional_int(line, a, b, device, prop_name, logger, fallback_value)

Try to get an optional integer from a substring.

## Function: sub_str(line, a, b, device, prop_name, logger, fallback_value)

Try to get a value from a substring.

## Function: ucte_split(line, prefix_lengths, total_fields, greedy_tail, skip_all_separators)

Split malformed UCTE rows while preserving fixed-width identifiers.
