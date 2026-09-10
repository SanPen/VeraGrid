# VeraGridEngine Module: src/VeraGridEngine/IO/epc/epc_parser.py

- Original source path: `src/VeraGridEngine/IO/epc/epc_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 14
- Representative imports: chardet, os, typing, numpy, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Devices

## Function: interpret_line(line, splitter)

Split text into arguments and parse each of them to an appropriate format (int, float or string)

## Function: find_between(s, start, end)

:param s:

## Function: split_line(lne)

:param lne:

## Function: parse_substations(data_lst)

:param data_lst:

## Function: parse_areas(data_lst)

:param data_lst:

## Function: parse_zones(data_lst)

:param data_lst:

## Function: parse_buses(data_lst, substations_dict, area_dict, zone_dict)

:param data_lst:

## Function: parse_dc_buses(data_lst)

:param data_lst:

## Function: parse_transformers(data_lst, buses_dict)

:param data_lst:

## Function: parse_branches(data_lst, buses_dict)

:param data_lst:

## Function: parse_dc_lines(data_lst, buses_dict, Sbase)

:param data_lst:

## Function: parse_dc_converters(data_lst, buses_dict, dc_buses_dict)

:param data_lst:

## Function: parse_loads(data_lst, buses_dict)

:param data_lst:

## Function: parse_generators(data_lst, buses_dict, bus_volt)

:param data_lst:

## Class: PowerWorldParser

- Bases: none
- Summary: PowerWorldParser

### Methods

- `read_and_split(self)`
  Summary: Read the text file and split it into sections
- `parse_case(self)`
  Summary: EPC power world case
