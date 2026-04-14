# VeraGridEngine Module: src/VeraGridEngine/IO/dgs/veragrid_to_dgs.py

- Original source path: `src/VeraGridEngine/IO/dgs/veragrid_to_dgs.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 32
- Representative imports: __future__, math, typing, numpy, VeraGridEngine.Devices, VeraGridEngine.basic_structures, VeraGridEngine.IO.dgs.dgs_circuit, VeraGridEngine.IO.dgs.dgs_objects, VeraGridEngine.enumerations, VeraGridEngine.Devices.Branches.transformer_type

## Function: _winding_type_to_pf_code(winding_type)

Convert a VeraGrid winding connection to the PowerFactory/DGS code.

## Function: _switch_graphic_type_to_pf_usage(graphic_type)

Convert a VeraGrid switch graphic type into PowerFactory usage fields.

## Function: _add_element_cubicles_with_state(dgs_grid, element_id, dgs_buses, switch_state, switch_type_id, switch_iuse, switch_usage)

Add cubicles and patch the generated StaSwitch state metadata.

## Function: _get_bus_voltage_for_branch(bus_from, bus_to)

Return the representative nominal voltage for a two-terminal branch.

## Function: _get_bus_voltage_for_injection(bus)

Return the nominal voltage of an injection bus.

## Function: _get_tap_phase_step_angle(tc_type, asymmetry_angle_deg)

Convert a VeraGrid tap changer mode into the PowerFactory ``phitr`` angle.

## Function: _set_tr2_type_connections_from_branch(tr, tpe)

Fill the DGS 2W transformer connection fields from the branch orientation.

## Function: _set_tr2_tap_control_fields_from_vgrid(tr, element, t)

Fill the DGS transformer control fields from the VeraGrid branch control state.

## Function: _get_tr3_winding_tap_fields_from_vgrid(winding)

Export a VeraGrid winding tap changer into PowerFactory 3W winding tap fields.

## Function: _get_transformer3w_side_sort_key(side_data)

Return the nominal-voltage sort key for a 3W transformer side.

## Function: _get_line_export_length(line)

Return the DGS-exported line length.

## Function: _build_sequence_line_type_from_branch(line, new_id, sbase_mva)

Build a DGS line type from a VeraGrid line object.

## Function: _get_transformer_export_nominal_power(transformer, sbase_mva)

Return the nominal transformer rating to use when exporting short-circuit data.

## Function: _convert_branch_impedance_to_elm_sind(branch, new_id, fold_id, sbase_mva, t)

Convert a VeraGrid series reactance into a DGS ``ElmSind``.

## Function: _convert_switch_to_dgs_type(switch, new_id, fold_id, sbase_mva)

Convert a VeraGrid switch electrical data into a DGS ``TypSwitch``.

## Function: convert_bus(bus, new_id, t)

:param bus:

## Function: convert_bus_graphic(elm_term, bus, new_id)

:param elm_term:

## Function: convert_shunt(shunt, new_id, ushnm_kv, t)

Export VeraGrid fixed Shunt to PowerFactory ElmShnt.

## Function: convert_load(load, new_id, t)

:param load:

## Function: convert_static_gen(stagen, new_id, t)

:param stagen:

## Function: convert_gen_to_static_gen(gen, new_id, t)

:param gen:

## Function: convert_battery(batt, new_id, t)

:param batt:

## Function: convert_generator(gen, tpe_new_id, new_id, bus_v_controlled, Sbase, t)

:param gen:

## Function: convert_sequence_line(seq, new_id)

:param seq:

## Function: convert_transformer_type(tr, new_id)

:param tr:

## Function: _set_tr2_tap_fields_from_vgrid(tr, tpe, e)

Set tap fields in TypTr2 and ElmTr2.

## Function: _build_typtr3_and_elmtr3(tr3, type_id, element_id, fold_id, t)

Convert a VeraGrid 3W transformer into DGS ``TypTr3`` and ``ElmTr3`` objects.

## Function: _convert_external_grid(external_grid, new_id, fold_id, t)

Convert a VeraGrid external grid into a DGS ``ElmXnet``.

## Function: _convert_controllable_shunt_to_dgs(shunt, new_id, fold_id, t)

Convert a VeraGrid controllable shunt into a DGS ``ElmShnt`` or ``ElmSvs``.

## Function: generate_diesel_dsl_composite(dgs_grid, name, net_id)

Generate a diesel composite

## Function: generate_pv_dsl_composite(dgs_grid, name, net_id)

Generate a PV composite

## Function: circuit_to_dgs(grid, t, convert_gen_to_elmgenstat)

Convert MultiCircuit to DgsCircuit
