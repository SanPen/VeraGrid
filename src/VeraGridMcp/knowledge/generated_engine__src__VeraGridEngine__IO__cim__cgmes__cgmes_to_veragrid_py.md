# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cgmes/cgmes_to_veragrid.py

- Original source path: `src/VeraGridEngine/IO/cim/cgmes/cgmes_to_veragrid.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 27
- Representative imports: __future__, typing, numpy, VeraGridEngine.IO.cim.cgmes.cgmes_enums, VeraGridEngine, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.Devices, VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_2_4_15_assets, VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_3_0_0_assets, VeraGridEngine.IO.cim.cgmes.cgmes_circuit, VeraGridEngine.IO.cim.cgmes.cgmes_typing, VeraGridEngine.IO.cim.cgmes.cgmes_utils, VeraGridEngine.data_logger, VeraGridEngine.enumerations

## Class: Cn2BusBarLookup

- Bases: none
- Summary: Class to properly match the ConnectivityNodes to the BusBars

### Methods

- `fill(self, cgmes_model)`
  Summary: :param cgmes_model:
- `add_cn(self, bus)`
  Summary: :param bus:
- `add_bus(self, bus)`
  Summary: :param bus:
- `get_busbar_cn(self, bb_id)`
  Summary: Get the associated ConnectivityNode object
- `get_busbar_bus(self, bb_id)`
  Summary: Get the associated Bus object

## Function: get_gcdev_voltage_dict(cgmes_model, logger)

Builds up voltage dictionary.

## Function: get_gcdev_device_to_terminal_dict(cgmes_model, logger)

Dictionary relating the conducting equipment to the terminal object(s)

## Function: get_gcdev_dc_device_to_terminal_dict(cgmes_model, logger)

Dictionary relating the DC conducting equipment to the DC terminal object(s)

## Function: find_associated_buses(cgmes_elm, device_to_terminal_dict, bus_dict, TopologicalNode_tpe, DCTopologicalNode_tpe, logger, cgmes_version)

This function finds the buses connected to a device

## Function: get_gcdev_buses(cgmes_model, gc_model, v_dict, cn_look_up, cgmes_topology_mode, skip_dc_import, buses_to_skip, default_nominal_voltage, logger)

Convert the TopologicalNodes to Buses (CalculationNodes)

## Function: get_gcdev_dc_connectivity_nodes(cgmes_model, gc_model, skip_dc_import, dc_bus_dict, logger)

Convert the DC Nodes to DC Connectivity nodes

## Function: get_gcdev_dc_lines(cgmes_model, gcdev_model, dc_bus_dict, device_to_terminal_dict, logger)

Convert the CGMES DCLineSegment to gcdev DC Line

## Function: get_gcdev_vsc_converters(cgmes_model, gcdev_model, dc_bus_dict, dc_device_to_terminal_dict, bus_dict, device_to_terminal_dict, logger)

Convert the CGMES VcConverter to gcdev VSConverter

## Function: get_gcdev_hvdc_from_dcline_and_vscs(cgmes_model, gcdev_model, dc_bus_dict, dc_device_to_terminal_dict, bus_dict, device_to_terminal_dict, logger)

Convert the CGMES VcConverter to gcdev simplified HVDC lines

## Function: get_gcdev_branch_groups(cgmes_model, gcdev_model)

Convert to gcdev BranchGroups from CGMES

## Function: get_gcdev_loads(cgmes_model, gcdev_model, bus_dict, device_to_terminal_dict, logger)

Convert the CGMES loads to gcdev

## Function: get_gcdev_generators(cgmes_model, gcdev_model, bus_dict, device_to_terminal_dict, logger)

Convert the CGMES generators to gcdev

## Function: get_gcdev_external_grids(cgmes_model, gcdev_model, calc_node_dict, device_to_terminal_dict, logger)

Convert the CGMES loads to gcdev

## Function: get_gcdev_ac_lines(cgmes_model, gcdev_model, bus_dict, device_to_terminal_dict, logger, Sbase)

Convert the CGMES ac lines to gcdev

## Function: get_gcdev_ac_transformers(cgmes_model, gcdev_model, bus_dict, device_to_terminal_dict, logger, Sbase)

Convert the CGMES ac lines to gcdev

## Function: get_tap_step_voltage_increment(tap_changer)

Read the tap step-voltage increment without mutating the imported CGMES object.

## Function: get_transformer_tap_changers(cgmes_model, gcdev_model, bus_dict, logger)

Process Tap Changer Classes from CGMES and put them into VeraGrid transformers.

## Function: get_gcdev_shunts(cgmes_model, gcdev_model, calc_node_dict, device_to_terminal_dict, logger)

Convert the CGMES equivalent shunts to gcdev shunts,

## Function: get_gcdev_controllable_shunts(cgmes_model, gcdev_model, bus_dict, device_to_terminal_dict, logger, Sbase)

Convert the CGMES linear and non-linear shunt compensators

## Function: get_gcdev_switches(cgmes_model, gcdev_model, bus_dict, device_to_terminal_dict, logger)

Convert the CGMES switching devices to gcdev

## Function: get_gcdev_substations(cgmes_model, gcdev_model, logger)

Convert the CGMES substations to gcdev substations

## Function: get_gcdev_voltage_levels(cgmes_model, gcdev_model, logger)

Convert the CGMES voltage levels to gcdev voltage levels

## Function: get_gcdev_busbars(cgmes_model, gcdev_model, calc_node_dict, device_to_terminal_dict, create_busbar_section_for_every_connectivity_node, logger)

Convert the CGMES busbars to gcdev busbars

## Function: get_gcdev_countries(cgmes_model, gcdev_model)

Convert the CGMES GeoGraphicalRegions to gcdev Country

## Function: get_gcdev_community(cgmes_model, gcdev_model)

Convert the CGMES SubGeographicalRegions to gcdev Community

## Function: get_header_mas(cgmes_model, gcdev_model, logger)

:param cgmes_model:

## Function: cgmes_to_veragrid(cgmes_model, map_dc_to_hvdc_line, logger, cgmes_topology_mode, create_busbar_section_for_every_connectivity_node)

Convert CGMES model to gcdev
