# VeraGridEngine Module: src/VeraGridEngine/IO/dgs/dgs_circuit.py

- Original source path: `src/VeraGridEngine/IO/dgs/dgs_circuit.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: __future__, sys, os, pathlib, typing, VeraGridEngine.IO.dgs.dgs_objects

## Function: _populate_from_pf_object(pf_obj, dgs_cls)

Populate a DGSElement subclass from a PowerFactory API object,

## Function: parse_header(line)

Parse $$ header line and return property -> index map.

## Class: DgsCircuit

- Bases: none
- Summary: Strongly-typed container for a PowerFactory DGS file.

### Methods

- `new_id(self)`
  Summary: :return:
- `add_element_cubicles(self, element_id, dgs_buses)`
  Summary: Add cubicles + their StaSwitch objects.
- `parse_dgs(self, path)`
  Summary: Parse a DGS file and populate the typed lists.
- `write_dgs(self, path)`
  Summary: Write the circuit back to a DGS file.
- `from_api(self, study_case_name, pf_path)`
  Summary: Populate this (empty) PfCircuit from an active PowerFactory application.
