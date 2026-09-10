# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cgmes/cgmes_data_parser.py

- Original source path: `src/VeraGridEngine/IO/cim/cgmes/cgmes_data_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 9
- Representative imports: os, zipfile, typing, VeraGridEngine.data_logger, VeraGridEngine.IO.base.base_circuit, VeraGridEngine.enumerations

## Function: find_id(child)

Try to find the ID of an element

## Function: find_class_name(child)

Try to find the CIM class name

## Function: fix_child_result_datatype(child_result)

No docstring provided.

## Function: _convert_leaf_value(value)

Convert XML leaf text to the expected scalar type.

## Function: _append_unique_value(container, key, value)

Append a value in a stable manner, preserving scalar form when unique.

## Function: parse_xml_stream_to_dict(xml_stream)

Parse XML stream to CGMES dictionary format using streaming events.

## Function: merge(A, B, logger, log_overwriting_values)

Modify A using B

## Function: sort_cgmes_files(links)

Sorts the CIM files in the preferred reading order

## Function: process_cgmes_file_data(file_name, file_cgmes_data, cgmes2_4_15_uri, cgmes3_0_0_uri, parsed_data, data, boundary_set, logger, log_overwriting_values)

Process one parsed CGMES file dictionary and route objects to normal/boundary stores.

## Class: CgmesDataParser

- Bases: BaseCircuit
- Summary: Class to read any cgmes-like set of files

### Methods

- `emit_text(self, val)`
  Summary: Emit text via the callback
- `emit_progress(self, val)`
  Summary: Emit floating point values via the callback
- `load_files(self, files)`
  Summary: Load CIM file
