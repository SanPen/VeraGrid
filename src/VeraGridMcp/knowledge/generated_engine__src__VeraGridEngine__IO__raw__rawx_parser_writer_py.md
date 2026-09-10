# VeraGridEngine Module: src/VeraGridEngine/IO/raw/rawx_parser_writer.py

- Original source path: `src/VeraGridEngine/IO/raw/rawx_parser_writer.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: typing, json, numpy, VeraGridEngine.IO.raw.raw_functions, VeraGridEngine.basic_structures, VeraGridEngine.Devices, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.IO.raw.devices.psse_circuit, VeraGridEngine.IO.raw.devices.psse_object

## Function: parse_rawx(file_name, logger)

Parse a rawx file from PSSe

## Class: NpEncoder

- Bases: json.JSONEncoder
- Summary: No docstring provided.

### Methods

- `default(self, obj)`
  Summary: No docstring provided.

## Function: write_rawx(file_name, circuit, logger)

RAWx export
