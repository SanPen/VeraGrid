# VeraGridEngine Module: src/VeraGridEngine/IO/raw/raw_to_veragrid.py

- Original source path: `src/VeraGridEngine/IO/raw/raw_to_veragrid.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 11
- Representative imports: numpy, math, typing, VeraGridEngine.basic_structures, VeraGridEngine.Devices, VeraGridEngine.Topology, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.IO.raw.devices.branch, VeraGridEngine.IO.raw.devices.bus, VeraGridEngine.IO.raw.devices.facts, VeraGridEngine.IO.raw.devices.generator, VeraGridEngine.IO.raw.devices.load, VeraGridEngine.IO.raw.devices.fixed_shunt, VeraGridEngine.IO.raw.devices.switched_shunt, VeraGridEngine.IO.raw.devices.transformer, VeraGridEngine.IO.raw.devices.two_terminal_dc_line

## Function: get_veragrid_bus(psse_bus, area_dict, zone_dict, logger)

:return:

## Function: get_veragrid_load(psse_load, bus, logger)

Return VeraGrid Load object

## Function: get_veragrid_shunt_fixed(psse_elm, bus, logger)

Return VeraGrid Shunt object

## Function: get_veragrid_shunt_switched(psse_elm, bus, psse_bus_dict, logger)

:param psse_elm:

## Function: get_veragrid_generator(psse_elm, psse_bus_dict, logger)

:param psse_elm:

## Function: get_veragrid_transformer(psse_elm, psse_bus_dict, Sbase, logger, adjust_taps_to_discrete_positions, simple_naming, flatten_virtual_taps)

:param psse_elm:

## Function: get_veragrid_line(psse_elm, psse_bus_dict, Sbase, logger, simple_naming)

:param psse_elm:

## Function: get_hvdc_from_vscdc(psse_elm, psse_bus_dict, Sbase, logger)

Get equivalent object

## Function: get_hvdc_from_twotermdc(psse_elm, psse_bus_dict, Sbase, logger)

:param psse_elm:

## Function: get_upfc_from_facts(psse_elm, psse_bus_dict, Sbase, logger, circuit)

Get equivalent object

## Function: psse_to_veragrid(psse_circuit, logger, branch_connection_voltage_tolerance, adjust_taps_to_discrete_positions, use_short_names, flatten_virtual_taps)

:param psse_circuit: PsseCircuit instance
