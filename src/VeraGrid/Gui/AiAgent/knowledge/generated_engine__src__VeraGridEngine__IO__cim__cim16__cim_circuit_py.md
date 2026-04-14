# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cim16/cim_circuit.py

- Original source path: `src/VeraGridEngine/IO/cim/cim16/cim_circuit.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: enum, chardet, pandas, VeraGridEngine.basic_structures, VeraGridEngine.IO.cim.cim16.cim_devices

## Class: CIMCircuit

- Bases: none
- Summary: No docstring provided.

### Methods

- `emit_text(self, val)`
  Summary: No docstring provided.
- `emit_progress(self, val)`
  Summary: No docstring provided.
- `clear(self)`
  Summary: Clear the circuit
- `check_type(xml, class_types, starter, ender)`
  Summary: Checks if we are starting an object of the predefined types
- `find_references(self)`
  Summary: Replaces the references in the "actual" properties of the objects
- `parse_xml_text(self, text_lines)`
  Summary: Fill the XML into the objects
- `parse_file(self, file_name)`
  Summary: Parse CIM file and add all the recognised objects
- `get_data_frames_dictionary(self)`
  Summary: Get dictionary of DataFrames
- `to_excel(self, fname)`
  Summary: :param fname:
