# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cgmes/veragrid_to_cgmes.py

- Original source path: `src/VeraGridEngine/IO/cim/cgmes/veragrid_to_cgmes.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 41
- Representative imports: typing, numpy, VeraGridEngine.Devices, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Devices, VeraGridEngine.Devices.Parents.branch_parent, VeraGridEngine.IO.cim.cgmes.base, VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_2_4_15_assets, VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_3_0_0_assets, VeraGridEngine.IO.cim.cgmes.cgmes_circuit, VeraGridEngine.IO.cim.cgmes.cgmes_typing, VeraGridEngine.IO.cim.cgmes.cgmes_create_instances, VeraGridEngine.IO.cim.cgmes.cgmes_enums, VeraGridEngine.IO.cim.cgmes.cgmes_enums, VeraGridEngine.IO.cim.cgmes.cgmes_utils, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions

## Function: set_declared_cgmes_property(cgmes_object, property_name, property_value, logger, context)

Assign a CGMES property only when the concrete CGMES object declares it.

## Function: find_fallback_voltage_level_for_bus(cgmes_model, bus, logger)

Find a fallback VoltageLevel for buses without a direct VoltageLevel link.

## Function: get_transformer_tap_values_for_cgmes_export(mc_elm, logger)

Return TapChanger values for CGMES export while preserving fixed tap modules.

## Function: should_export_tap_changer(mc_elm)

Determine if a transformer or winding tap changer should be exported.

## Function: create_cgmes_tap_changer_for_transformer_end(mc_elm, pte, cgmes_model, ver, logger)

Create and add tap changer objects for a transformer end.

## Function: find_terminals_by_conducting_equipment_uuid(cgmes_model, cond_eq_target_uuid)

Return every terminal associated to the given conducting-equipment UUID.

## Function: get_vsc_voltage_target(gc_vsc)

Derive the VSC AC-side target voltage in per unit from the VeraGrid controls.

## Function: get_vsc_power_target(gc_vsc)

Derive the VSC active-power target in MW from the VeraGrid controls.

## Function: get_or_create_dc_topological_node(cgmes_model, dc_bus, ver, logger)

Reuse the exported DC topological node for a DC bus or create it if missing.

## Function: get_or_create_dc_node(cgmes_model, dc_bus, dc_tp, dc_equipment_container, ver, logger)

Reuse the exported DC node for a DC bus or create it if missing.

## Function: get_or_create_external_network_injection(multicircuit_model, cgmes_model, ver, logger)

Export every VeraGrid external grid as an ExternalNetworkInjection.

## Function: convert_vsc_devices_to_cgmes(multicircuit_model, cgmes_model, ver, logger)

Export native VeraGrid VSC devices to CGMES VsConverter objects.

## Function: convert_dc_lines_to_cgmes(multicircuit_model, cgmes_model, ver, logger)

Export native VeraGrid DC lines to CGMES DCLine/DCLineSegment objects.

## Function: export_sv_statuses(gc_model, cgmes_model, ver)

Export SvStatus for every source object that maps directly to a CGMES conducting equipment.

## Function: get_cgmes_geograpical_regions(multi_circuit_model, cgmes_model, ver, logger)

:param multi_circuit_model:

## Function: get_cgmes_sub_geographical_regions(multi_circuit_model, cgmes_model, ver, logger)

:param multi_circuit_model:

## Function: get_base_voltage_from_boundary(cgmes_model, vnom, ver)

:param cgmes_model:

## Function: get_cgmes_base_voltages(multi_circuit_model, cgmes_model, ver, logger)

:param multi_circuit_model:

## Function: get_cgmes_substations(multi_circuit_model, cgmes_model, ver, logger)

:param multi_circuit_model:

## Function: get_cgmes_voltage_levels(multi_circuit_model, cgmes_model, ver, logger)

:param multi_circuit_model:

## Function: get_cgmes_tp_nodes(multi_circuit_model, cgmes_model, ver, logger)

Convert gcdev Buses to CGMES Topological Nodes

## Function: get_cgmes_cn_nodes_from_tp_nodes(multi_circuit_model, cgmes_model, ver, logger)

Export one ConnectivityNode for every TopologicalNode

## Function: get_cgmes_loads(multicircuit_model, cgmes_model, ver, logger)

Converts every Multi Circuit load into CGMES ConformLoad.

## Function: get_cgmes_equivalent_injections(multicircuit_model, cgmes_model, ver, logger)

Converts every Multi Circuit external grid

## Function: get_cgmes_ac_line_segments(multicircuit_model, cgmes_model, op_lim_types, ver, logger)

Converts every Multi Circuit line

## Function: get_cgmes_generators(multicircuit_model, cgmes_model, ver, logger)

Converts Multi Circuit generators

## Function: get_cgmes_power_transformers(grid, cgmes_model, op_lim_types, ver, logger)

Creates all transformer related CGMES classes from VeraGrid transformer.

## Function: get_cgmes_current_limits(cgmes_model, cgmes_elm, mc_elm, op_lim_types, ver, logger)

Export Current Limits to CGMES for Branches.

## Function: get_cgmes_operational_limit_types(cgmes_model, ver)

Creates three kind of Operational limit type for Cgmes Export.

## Function: get_cgmes_equivalent_shunts(multicircuit_model, cgmes_model, ver, logger)

Converts Multi Circuit shunts

## Function: get_cgmes_linear_and_non_linear_shunts(multicircuit_model, cgmes_model, ver, logger)

Convert VeraGrid controllable shunts to CGMES NonlinearShuntCompensator.

## Function: get_cgmes_breakers(multicircuit_model, cgmes_model, ver, logger)

Converts every Multi Circuit Switch into CGMES Breaker.

## Function: get_cgmes_sv_voltages(multi_circuit_model, cgmes_model, pf_results, ver, logger)

Creates a CgmesCircuit SvVoltage_list

## Function: get_cgmes_sv_power_flow_1(multi_circuit, nc, cgmes_model, pf_results, ver, logger)

For single-terminal devices:

## Function: get_cgmes_sv_power_flow_2(multi_circuit, nc, cgmes_model, pf_results, ver, logger)

For Branches:

## Function: get_cgmes_sv_tap_step(multi_circuit, nc, cgmes_model, pf_results, ver, logger)

:param multi_circuit:

## Function: get_cgmes_sv_shunt_compensator_sections(cgmes_model, ver)

:param cgmes_model:

## Function: get_cgmes_topological_island(multicircuit_model, nc, cgmes_model, ver, logger)

:param multicircuit_model:

## Function: make_coordinate_system(cgmes_model, ver, logger)

:param cgmes_model:

## Function: convert_hvdc_line_to_cgmes(multicircuit_model, cgmes_model, ver, logger)

Converts simplified HVDC line to two VSConverters inside DCConverterUnits,

## Function: veragrid_to_cgmes(gc_model, num_circ, pf_results, cgmes_model, logger)

Converts the input Multi circuit to a new CGMES Circuit.
