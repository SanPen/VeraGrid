# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cgmes/cgmes_create_instances.py

- Original source path: `src/VeraGridEngine/IO/cim/cgmes/cgmes_create_instances.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

Collection of functions to create new CGMES instances for CGMES export.

## Module Surface

- Class count: 0
- Top-level function count: 27
- Representative imports: numpy, datetime, typing, VeraGridEngine, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.IO.cim.cgmes.base, VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_2_4_15_assets, VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_3_0_0_assets, VeraGridEngine.IO.cim.cgmes.cgmes_circuit, VeraGridEngine.IO.cim.cgmes.cgmes_typing, VeraGridEngine.IO.cim.cgmes.cgmes_enums, VeraGridEngine.IO.cim.cgmes.cgmes_utils, VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.full_model, VeraGridEngine.Devices, VeraGridEngine.enumerations, VeraGridEngine.data_logger

## Function: find_topological_node_for_bus(cgmes_model, mc_bus)

Resolve the TopologicalNode for a bus.

## Function: create_cgmes_headers(cgmes_model, mas_names, profiles_to_export, logger, desc, scenario_time, version, modeller_url)

:param cgmes_model:

## Function: create_cgmes_terminal(mc_bus, seq_num, cond_eq, cgmes_model, ver, logger)

Creates a new Terminal in CGMES model,

## Function: create_cgmes_load_response_char(load, cgmes_model, ver)

:param load:

## Function: create_cgmes_generating_unit(gen, cgmes_model, ver)

Creates the appropriate CGMES GeneratingUnit object

## Function: create_cgmes_regulating_control(cgmes_elm, mc_gen, cgmes_model, ver, logger)

Create Regulating Control for a CGMES device

## Function: create_cgmes_tap_changer_control(tap_changer, tcc_mode, tcc_enabled, mc_trafo, cgmes_model, ver, logger)

Create Tap Changer Control for Tap changers.

## Function: create_cgmes_current_limit(terminal, rate_mw, op_limit_type, cgmes_model, ver, logger)

:param terminal: Cgmes Terminal

## Function: create_operational_limit_set(terminal, cgmes_model, ver, logger)

:param terminal:

## Function: create_cgmes_operational_limit_type(cgmes_model, ver)

:param cgmes_model: CgmesModel

## Function: create_cgmes_dc_tp_node(tp_name, tp_description, cgmes_model, ver, logger)

Creates a DCTopologicalNode from a gcdev Bus

## Function: create_cgmes_dc_node(cn_name, cn_description, cgmes_model, dc_tp, dc_ec, ver, logger)

Creates a DCTopologicalNode from a gcdev Bus

## Function: create_cgmes_vsc_converter(cgmes_model, gc_vsc, p_set, v_set, ver, logger)

Creates a new Voltage-source converter

## Function: create_cgmes_acdc_converter_terminal(cgmes_model, mc_dc_bus, seq_num, dc_node, dc_cond_eq, ver, logger)

Creates a new ACDCConverterDCTerminal in CGMES model,

## Function: create_cgmes_dc_line(cgmes_model, ver, logger)

Creates a new CGMES DCLine

## Function: create_cgmes_dc_line_segment(cgmes_model, mc_elm, dc_tp_1, dc_node_1, dc_tp_2, dc_node_2, eq_cont, ver, logger)

Creates a new CGMES DCLineSegment

## Function: create_cgmes_dc_terminal(cgmes_model, dc_tp, dc_node, dc_cond_eq, seq_num, ver, logger)

Creates a new CGMES DCTerminal

## Function: create_cgmes_dc_converter_unit(cgmes_model, ver, logger)

Creates a new CGMES DCConverterUnit

## Function: create_cgmes_location(cgmes_model, device, longitude, latitude, ver, logger)

:param cgmes_model:

## Function: create_sv_power_flow(cgmes_model, p, q, terminal, ver)

Creates a SvPowerFlow instance

## Function: create_sv_shunt_compensator_sections(cgmes_model, sections, cgmes_shunt_compensator, ver)

Creates a SvShuntCompensatorSections instance

## Function: create_sv_status(cgmes_model, in_service, cgmes_conducting_equipment, ver)

Creates a SvStatus instance

## Function: create_cgmes_conform_load_group(cgmes_model, ver, logger)

:param cgmes_model:

## Function: create_cgmes_non_conform_load_group(cgmes_model, ver, logger)

:param cgmes_model:

## Function: create_cgmes_sub_load_area(cgmes_model, ver, logger)

:param cgmes_model:

## Function: create_cgmes_load_area(cgmes_model, ver, logger)

:param cgmes_model:

## Function: create_cgmes_nonlinear_sc_point(section_num, b, g, nl_sc, cgmes_model, ver)

:param section_num:
