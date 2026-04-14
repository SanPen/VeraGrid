# VeraGridEngine Module: src/VeraGridEngine/IO/others/pypsa_parser.py

- Original source path: `src/VeraGridEngine/IO/others/pypsa_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 3
- Representative imports: math, numpy, datetime, collections.abc, typing, pyproj, VeraGridEngine.Devices.Injections.battery, VeraGridEngine.Devices.Injections.shunt, VeraGridEngine.Devices.Aggregation.branch_group, VeraGridEngine.basic_structures, VeraGridEngine.Devices.Branches.transformer, VeraGridEngine.Devices.Branches.hvdc_line, VeraGridEngine.enumerations, VeraGridEngine.Devices.Branches.line, VeraGridEngine.Devices.Injections.load, VeraGridEngine.Devices.Injections.generator

## Class: PyPSAParser

- Bases: none
- Summary: PyPSAParser

### Methods

- `_parse_date(raw)`
  Summary: No docstring provided.
- `_is_active(data)`
  Summary: Returns whether the given component is active. This feature is only
- `_parse_countries(self)`
  Summary: Parses the country data from the PyPSA network.
- `_parse_buses(self)`
  Summary: Parses the bus data from the PyPSA network.
- `_parse_generators(self)`
  Summary: Parses the generator row from the PyPSA network.
- `_parse_storage_units(self)`
  Summary: Parses the storage units data from the PyPSA network.
- `_parse_stores(self)`
  Summary: Parses the stores data from the PyPSA network.
- `_parse_loads(self)`
  Summary: Parses the load data from the PyPSA network.
- `_parse_line_types(self)`
  Summary: Parses the line type data from the PyPSA network.
- `_parse_lines(self)`
  Summary: Parses the line data from the PyPSA network.
- `_parse_hvdc(self)`
  Summary: Parses the HVDC data from the PyPSA network.
- `_parse_transformer_types(self)`
  Summary: Parses the transformer type data from the PyPSA network.
- `_parse_transformers(self)`
  Summary: Parses the transformer data from the PyPSA network.
- `_parse_shunts(self)`
  Summary: Parses the shunt impedances row from the PyPSA network.
- `parse(self)`
  Summary: Parses the PyPSA network.

## Function: pypsa2veragrid(network, logger)

:param network:

## Function: parse_pypsa_netcdf(file_path, logger)

Parses the netCDF file using the PyPSA library.

## Function: parse_pypsa_hdf5(file_path, logger)

Parses the HDF5 store file using the PyPSA library.
