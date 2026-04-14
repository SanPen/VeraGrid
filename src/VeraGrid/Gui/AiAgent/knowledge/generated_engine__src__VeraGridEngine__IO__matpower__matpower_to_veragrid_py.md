# VeraGridEngine Module: src/VeraGridEngine/IO/matpower/matpower_to_veragrid.py

- Original source path: `src/VeraGridEngine/IO/matpower/matpower_to_veragrid.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 8
- Representative imports: typing, numpy, math, VeraGridEngine.IO.matpower.matpower_circuit, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.Devices, VeraGridEngine.basic_structures

## Function: convert_areas(circuit, m_grid)

Parse Matpower / FUBM Matpower area data into VeraGrid

## Function: convert_buses(circuit, m_grid, area_idx_dict)

Parse Matpower / FUBM Matpower bus data into VeraGrid

## Function: convert_dc_buses(circuit, m_grid, area_idx_dict, freq)

Parse Matpower / FUBM Matpower bus data into VeraGrid

## Function: convert_generators(circuit, m_grid, bus_idx_dict)

Parse Matpower / FUBM Matpower generator data into VeraGrid

## Function: convert_branches(circuit, m_grid, bus_idx_dict, logger)

Parse Matpower / FUBM Matpower branch data into VeraGrid

## Function: convert_dc_branches(circuit, m_grid, dc_bus_dict, logger)

:param circuit:

## Function: convert_converters(circuit, m_grid, bus_dict, dc_bus_dict, logger)

No docstring provided.

## Function: matpower_to_veragrid(m_grid, logger)

:param m_grid:
