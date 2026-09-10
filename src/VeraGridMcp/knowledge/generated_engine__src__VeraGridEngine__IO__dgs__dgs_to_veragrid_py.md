# VeraGridEngine Module: src/VeraGridEngine/IO/dgs/dgs_to_veragrid.py

- Original source path: `src/VeraGridEngine/IO/dgs/dgs_to_veragrid.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 54
- Representative imports: __future__, math, numpy, typing, VeraGridEngine.enumerations, VeraGridEngine.Devices, VeraGridEngine.Devices.Branches.wire, VeraGridEngine.Devices.Branches.overhead_line_type, VeraGridEngine.basic_structures, VeraGridEngine.IO.dgs.dgs_circuit, VeraGridEngine.IO.dgs.dgs_objects

## Function: _ref_id(x)

Extract the referenced object ID from PowerFactory/DGS pointer strings.

## Function: _stacubic_obj_bus_sort_key(cubic)

Return StaCubic ``obj_bus`` as integer sort key.

## Function: _bus_vnom_sort_key(bus)

Return bus nominal voltage sort key.

## Function: _resolve_pointer_dict_value(key, mapping)

Resolve a DGS pointer key using both raw and normalized forms.

## Function: _get_non_empty_name(name, default_value)

Return a non-empty name string.

## Function: _get_parallel_device_count(count)

Return the number of explicit VeraGrid devices to create.

## Function: _get_parallel_device_name(base_name, parallel_index, parallel_count)

Build the explicit device name for a parallel-unit copy.

## Function: _get_parallel_device_idtag(base_id, parallel_index, parallel_count)

Build the explicit idtag for a parallel-unit copy.

## Function: _get_transformer_tap_changer_type(typtr2)

Infer the VeraGrid tap-changer type from PowerFactory magnitude and phase data.

## Function: _get_safe_tap_value(value, fallback_value)

Return a strictly positive finite tap value.

## Function: _sanitize_tap_window(tap_value, tap_min_value, tap_max_value, fallback_tap_value, fallback_tap_min_value, fallback_tap_max_value)

Normalize a tap module and its range into a valid positive interval.

## Function: _apply_branch_tap_state(branch, tap_value, tap_phase, tap_min_value, tap_max_value, tap_phase_min, tap_phase_max)

Apply a full tap state to a VeraGrid transformer-like branch.

## Function: _get_switch_impedance_in_pu(r_ohm, x_ohm, vnom_kv, sbase_mva)

Convert switch impedance from ohms to per-unit.

## Function: _line_section_index_sort_key(section)

Return the section ordering index as float.

## Function: _get_unique_name_mapping(lines, use_characteristic_name)

Build a line-name mapping only for names that are unique in the DGS.

## Function: _resolve_line_section_owner_id(section, line_ids, folder_parent, line_id_by_loc_name, line_id_by_chr_name)

Resolve the owning line of a section using folder ancestry and unique-name fallback.

## Function: get_terminal_ids(element_id, cubics_by_objid)

Get the connected terminal IDs (ElmTerm.ID) for a given branch/injection element ID

## Function: get_branch_buses(elm_id, stacubic_dict, buses, cubics_by_objid, bus_by_term_id)

Function to get the buses from a branch element

## Function: get_injection_bus(elm_id, stacubic_dict, buses, cubics_by_objid, bus_by_term_id)

Function to get the bus from a injection element

## Function: convert_dgs_to_bus(elmterm, pos_by_objid)

Convert ElmTerm to Bus

## Function: convert_dgs_to_sequence_line(typlne)

Convert a TypLne to SequenceLineType

## Function: _bundle_offsets(n_sub, spacing_m)

Generate bundle offsets (dx, dy) in meters for a bundle of subconductors.

## Function: convert_dgs_to_wire(typcon)

Convert a PowerFactory TypCon into a VeraGrid Wire.

## Function: _convert_gearth_us_per_cm_to_resistivity_ohm_m(gearth_us_per_cm)

Convert PowerFactory earth conductivity (uS/cm) to resistivity (Ohm*m).

## Function: convert_dgs_to_overhead_line_type(typtow, typcon_by_id, wire_by_id, default_frequency_hz)

Convert a PowerFactory TypTow into a VeraGrid OverheadLineType.

## Function: _convert_pf_tr2_connection(code)

Convert a PowerFactory 2-character transformer connection code to VeraGrid WindingType.

## Function: convert_dgs_to_transformer_type(typtr2)

Convert a TypTr2 to TransformerType

## Function: _order_hv_lv(bus_a, bus_b, logger, tr_name)

Order two buses as (HV, LV) based on nominal voltage.

## Function: _order_hv_mv_lv(bus_a, bus_b, bus_c, logger, tr_name)

Order three buses as (HV, MV, LV) based on nominal voltage.

## Function: _apply_tr3_winding_connection_data(winding, pf_connection_code, pf_vector_group_angle)

Apply PowerFactory 3W winding connection data to an inner VeraGrid winding.

## Function: _apply_tr3_winding_tap_data(winding, current_position, neutral_position, minimum_position, maximum_position, step_percent, phase_angle_deg)

Apply PowerFactory 3W tap data to an internal VeraGrid winding.

## Function: convert_dgs_to_transformer(tr2, buses, stacubic_dict, templates_dict, typtr2_dict, freq, baseMVA, logger, cubics_by_objid, bus_by_term_id, parallel_index, parallel_count)

Convert ElmTr2 to Transformer2W

## Function: convert_dgs_to_transformer3w(tr3, buses, stacubic_dict, templates_dict, baseMVA, logger, cubics_by_objid, bus_by_term_id, parallel_index, parallel_count)

Convert ElmTr3 to Transformer3W using TypTr3 as template for design values.

## Function: build_switch_by_cubic_id(staswitchs)

Build a dictionary mapping StaCubic.ID -> StaSwitch.

## Function: convert_dgs_to_switches_from_elmcoup(elmcoups, cubics_by_objid, bus_by_term_id, switch_by_cubic_id, typ_switch_by_id, sbase_mva, logger)

Create VeraGrid Switch devices from ElmCoup.

## Function: _convert_pf_switch_graphic_type(iuse, ausage)

Convert PowerFactory/DGS switch usage fields to a VeraGrid SwitchGraphicType.

## Function: convert_dgs_to_switch(stasw, buses, stacubic_dict, logger, cubics_by_objid, bus_by_term_id)

Convert a PowerFactory/DGS StaSwitch into a VeraGrid Switch.

## Function: convert_dgs_to_line(lne, buses, stacubic_dict, templates_dict, overhead_line_type_dict, line_type_by_line_id, line_sections_by_line_id, tower_template_by_line_id, freq, baseMVA, logger, cubics_by_objid, bus_by_term_id, parallel_index, parallel_count)

Convert a PowerFactory/DGS ElmLne into a VeraGrid Line.

## Function: convert_dgs_to_series_reactance(element, buses, bus_by_terminal_id, stacubic_dict, cubics_by_obj_id, typsind_dict, logger, sbase_mva)

Convert a PowerFactory DGS series impedance element into a VeraGrid SeriesReactance device.

## Function: _get_scale_factor(scale0, logger, name)

Interpret PowerFactory/DGS load scaling factor.

## Function: _extract_load_pq(elmlod, logger)

Extract (P, Q) in MW/MVAr from an ElmLod.

## Function: convert_dgs_to_load(elmlod, stacubic_dict, buses, logger, cubics_by_objid, bus_by_term_id)

Convert ElmLod to VeraGrid Load.

## Function: convert_dgs_to_static_gen(elmgenstat, stacubic_dict, buses, logger, cubics_by_objid, bus_by_term_id, parallel_index, parallel_count)

Convert ElmGenstat to VeraGrid Load.

## Function: convert_dgs_to_external_grid(elmxnet, stacubic_dict, buses, logger, cubics_by_objid, bus_by_term_id)

Convert ElmXnet to VeraGrid Load.

## Function: _extract_shunt_gb(elmshnt, f, logger)

Extract (G, B) from an ElmShnt.

## Function: convert_dgs_to_shunt(elmshnt, stacubic_dict, buses, logger, cubics_by_objid, bus_by_term_id, frequency)

Convert ElmShnt to VeraGrid fixed Shunt.

## Function: _build_elmshnt_step_model(elmshnt, logger)

Build the step model (b_steps, initial_step, Bmin, Bmax) for an ElmShnt with ncapx > 1.

## Function: convert_dgs_to_controllable_shunt_from_elmshnt(elmshnt, stacubic_dict, buses, logger, cubics_by_objid, bus_by_term_id, frequency)

Convert stepped ElmShnt (ncapx > 1) to VeraGrid ControllableShunt.

## Function: convert_dgs_to_controllable_shunt(elmsvs, stacubic_dict, buses, logger, cubics_by_objid, bus_by_term_id)

Convert ElmSvs (PowerFactory SVS/SVC) to VeraGrid ControllableShunt.

## Function: _pf_from_pq(p_mw, q_mvar, default)

Compute power factor from (P, Q).

## Function: _interpret_pu_limit(value, baseMVA, reference_abs, logger, name, field)

Interpret a DGS limit that might be in p.u. (on Sbase) or in MW/MVAr.

## Function: convert_dgs_to_generator(elmsym, stacubic_dict, buses, typsym_dict, baseMVA, logger, cubics_by_objid, bus_by_term_id, parallel_index, parallel_count)

Convert ElmSym to VeraGrid Generator.

## Function: convert_dgs_to_asm_generator(elmasm, stacubic_dict, buses, typasmo_dict, baseMVA, logger, cubics_by_objid, bus_by_term_id, parallel_index, parallel_count)

Convert ElmAsm (asynchronous machine) to VeraGrid Generator.

## Function: dgs_to_circuit(path, logger)

:param path:
