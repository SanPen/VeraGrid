# VeraGridEngine Module: src/VeraGridEngine/IO/raw/veragrid_to_raw.py

- Original source path: `src/VeraGridEngine/IO/raw/veragrid_to_raw.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 15
- Representative imports: math, numpy, typing, itertools, scipy.sparse, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.IO.raw.devices, VeraGridEngine.IO.raw.devices.psse_circuit, VeraGridEngine.Devices, VeraGridEngine.Devices.types, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: get_area(area, i)

:param area:

## Function: get_zone(zone, i)

:param zone:

## Function: get_psse_bus(bus, area_dict, zones_dict, suggested_psse_number)

:param bus:

## Function: get_psse_load(load, bus_dict, id_number)

:param load:

## Function: get_psse_load_from_external_grid(load, bus_dict, id_number)

:param load:

## Function: get_psse_fixed_shunt(shunt, bus_dict, id_number)

:param shunt:

## Function: get_psse_switched_shunt(shunt, bus_dict)

:param shunt:

## Function: get_psse_generator(generator, bus_dict, id_number)

:param generator:

## Function: get_psse_transformer2w(transformer, bus_dict, ckt)

:param transformer:

## Function: get_psse_transformer3w(transformer, bus_dict)

:param transformer:

## Function: get_psse_branch(branch, bus_dict, ckt)

:param branch:

## Function: get_vsc_dc_line(hvdc_line, bus_dict)

:param hvdc_line:

## Function: get_psse_two_terminal_dc_line(hvdc_line, bus_dict)

:param hvdc_line:

## Function: get_psse_facts(upfc, bus_dict)

:param upfc:

## Class: RawCounter

- Bases: none
- Summary: Items to count stuff for the raw files

### Methods

- `psse_numbers_dict(self)`
  Summary: :return:
- `register_psse_number(self, bus, psse_I)`
  Summary: :param bus:
- `get_next_psse_number(self)`
  Summary: :return:
- `get_suggested_psse_number(self, bus, logger)`
  Summary: :param bus:
- `get_id(self, bus)`
  Summary: Query the dictionary for the internal number and increase that number for the next time
- `get_ckt(self, branch)`
  Summary: Count the circuit number in the PSSe sense

## Function: veragrid_to_raw(grid, logger)

Convert MultiCircuit to PSSeCircuit
