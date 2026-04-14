# VeraGridEngine Module: src/VeraGridEngine/IO/others/pandapower_parser.py

- Original source path: `src/VeraGridEngine/IO/others/pandapower_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 4
- Representative imports: __future__, math, typing, sqlite3, json, numpy, pandas, VeraGridEngine.Devices, VeraGridEngine.enumerations, VeraGridEngine.Devices.types, VeraGridEngine.basic_structures

## Function: is_pandapower_pickle(file_path)

Check if a file is pandapower Pickle

## Function: is_pandapower_json(file_path)

Check if a file is pandapower JSON

## Function: is_pandapower_sqlite(file_path)

Check if a file is pandapower SQLite

## Function: is_pandapower_file(file_path)

Check if this is a pandapower file

## Class: Panda2VeraGrid

- Bases: none
- Summary: No docstring provided.

### Methods

- `register(self, panda_type, panda_code, api_obj)`
  Summary: Register a panda object and it's associated VeraGrid object
- `get_api_object_by_registry(self, panda_type, panda_code)`
  Summary: Get a previously registered veragrid object from a pandapower table-key
- `parse_buses(self, grid)`
  Summary: Add buses to the VeraGrid grid based on Pandapower data
- `parse_external_grids(self, grid, bus_dictionary)`
  Summary: Add external grid (slack bus) generators to the VeraGrid grid
- `parse_loads(self, grid, bus_dictionary)`
  Summary: Add loads to the VeraGrid grid based on Pandapower data
- `parse_shunts(self, grid, bus_dictionary)`
  Summary: Add shunts to the VeraGrid grid based on Pandapower data
- `parse_lines(self, grid, bus_dictionary)`
  Summary: Add lines (conductors) to the VeraGrid grid
- `parse_impedances(self, grid, bus_dictionary)`
  Summary: Add impedances to the VeraGrid grid
- `parse_storage(self, grid, bus_dictionary)`
  Summary: Add storages to the VeraGrid grid
- `parse_generators(self, grid, bus_dictionary)`
  Summary: Add synchronous generators (row) to the VeraGrid grid
- `parse_static_generators(self, grid, bus_dictionary)`
  Summary: Add synchronous generators (row) to the VeraGrid grid
- `parse_transformers(self, grid, bus_dictionary)`
  Summary: Add transformers to the VeraGrid grid
- `extract_tap_changers(self, row)`
  Summary: # Tap changer mapping (pandapower → GridCal)
- `parse_transformers3W(self, grid, bus_dictionary)`
  Summary: Add 3W transformers to the VeraGrid grid
- `parse_switches(self, grid, bus_dictionary)`
  Summary: See: https://pandapower.readthedocs.io/en/latest/elements/switch.html
- `parse_measurements(self, grid)`
  Summary: :param grid:
- `get_multicircuit(self, convert_switches)`
  Summary: Get a VeraGrid Multi-circuit from a PandaPower grid
