# VeraGridEngine Module: src/VeraGridEngine/IO/matpower/legacy/matpower_parser.py

- Original source path: `src/VeraGridEngine/IO/matpower/legacy/matpower_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 15
- Representative imports: typing, numpy, pandas, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices, VeraGridEngine.IO.matpower.legacy.matpower_branch_definitions, VeraGridEngine.IO.matpower.legacy.matpower_bus_definitions, VeraGridEngine.IO.matpower.legacy.matpower_gen_definitions

## Function: find_between(s, first, last)

Find sting between two sub-strings

## Function: txt2mat(txt, line_splitter, to_float)

:param txt:

## Function: parse_areas_data(circuit, data, logger)

Parse Matpower / FUBM Matpower area data into VeraGrid

## Function: parse_buses_data(circuit, data, area_idx_dict, logger)

Parse Matpower / FUBM Matpower bus data into VeraGrid

## Function: parse_generators(circuit, data, bus_idx_dict, logger)

Parse Matpower / FUBM Matpower generator data into VeraGrid

## Function: parse_branches_data(circuit, data, bus_idx_dict, logger)

Parse Matpower / FUBM Matpower branch data into VeraGrid

## Function: interpret_data_v1(data, logger)

Pass the loaded table-like data to the  structures

## Function: read_matpower_file(filename, logger)

Read a Matpower case and return the structures

## Function: parse_matpower_file(filename, export)

Args:

## Function: arr_to_dict(hdr, arr)

Match header-data pair into a dictionary

## Function: get_matpower_case_data(filename, force_linear_cost)

Parse matpower .m file and get the case data structure

## Function: get_buses(circuit)

Get matpower buses structure

## Function: get_generation(circuit, bus_dict)

Get generation and generation cost data

## Function: get_branches(circuit, bus_dict)

:param circuit:

## Function: to_matpower(circuit, logger)

:param circuit:
