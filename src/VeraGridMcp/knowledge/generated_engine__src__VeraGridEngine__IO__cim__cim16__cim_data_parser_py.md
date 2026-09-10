# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cim16/cim_data_parser.py

- Original source path: `src/VeraGridEngine/IO/cim/cim16/cim_data_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 6
- Representative imports: os, collections.abc, typing, xml.etree.ElementTree, VeraGridEngine.data_logger, VeraGridEngine.IO.base.base_circuit, VeraGridEngine.IO.veragrid.zip_interface

## Function: find_id(child)

Try to find the ID of an element

## Function: find_class_name(child)

Try to find the CIM class name

## Function: parse_xml_to_dict(xml_element)

Parse element into dictionary

## Function: merge(A, B, logger)

Modify A using B

## Function: read_cim_files(cim_files)

Reads a list of .zip or xml into a dictionary of file name -> list of text lines

## Function: sort_cim_files(file_names)

Sorts the CIM files in the preferred reading order

## Class: CimDataParser

- Bases: BaseCircuit
- Summary: Class to read any cim-like set of files

### Methods

- `emit_text(self, val)`
  Summary: :param val:
- `emit_progress(self, val)`
  Summary: :param val:
- `parse_xml_text(self, text_lines)`
  Summary: Fill the XML into the objects
- `load_cim_file(self, cim_files)`
  Summary: Load CIM file
