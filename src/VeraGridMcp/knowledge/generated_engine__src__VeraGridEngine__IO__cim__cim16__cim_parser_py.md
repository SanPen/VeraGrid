# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cim16/cim_parser.py

- Original source path: `src/VeraGridEngine/IO/cim/cim16/cim_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 6
- Representative imports: os, math, typing, VeraGridEngine.basic_structures, VeraGridEngine.IO.veragrid.zip_interface, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices, VeraGridEngine.IO.cim.cim16.cim_devices, VeraGridEngine.IO.cim.cim16.cim_circuit, VeraGridEngine.data_logger

## Function: read_cim_files(cim_files, logger)

Reads a list of .zip or xml into a dictionary of file name -> list of text lines

## Function: sort_cim_files(file_names)

Sorts the CIM files in the preferred reading order

## Function: get_elements(d, keys)

No docstring provided.

## Function: any_in_dict(d, keys)

No docstring provided.

## Function: try_buses(b1, b2, bus_duct)

No docstring provided.

## Function: try_bus(b1, bus_duct)

No docstring provided.

## Class: CIMExport

- Bases: none
- Summary: No docstring provided.

### Methods

- `save(self, file_name)`
  Summary: Save XML CIM version of a grid

## Class: CIMImport

- Bases: none
- Summary: No docstring provided.

### Methods

- `emit_text(self, val)`
  Summary: No docstring provided.
- `emit_progress(self, val)`
  Summary: No docstring provided.
- `parse_model(cim, circuit)`
  Summary: :param cim:
- `parse_bus_bars(self, cim, circuit)`
  Summary: :param cim:
- `parse_ac_line_segment(self, cim, circuit, busbar_dict)`
  Summary: :param cim:
- `parse_power_transformer(self, cim, circuit, busbar_dict, logger)`
  Summary: :param cim:
- `parse_switches(self, cim, circuit, busbar_dict)`
  Summary: :param cim:
- `parse_loads(self, cim, circuit, busbar_dict)`
  Summary: :param cim:
- `parse_shunts(self, cim, circuit, busbar_dict)`
  Summary: :param cim:
- `parse_generators(self, cim, circuit, busbar_dict)`
  Summary: :param cim:
- `load_cim_file(self, cim_files)`
  Summary: Load CIM file
