# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cgmes/cgmes_utils.py

- Original source path: `src/VeraGridEngine/IO/cim/cgmes/cgmes_utils.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 31
- Representative imports: __future__, typing, numpy, VeraGridEngine.Devices, VeraGridEngine.IO.cim.cgmes.base, VeraGridEngine.IO.cim.cgmes.cgmes_circuit, VeraGridEngine.IO.cim.cgmes.cgmes_typing, VeraGridEngine.data_logger, VeraGridEngine.Devices.types, VeraGridEngine.IO.cim.cgmes.cgmes_enums

## Function: normalize_cgmes_reference_uuid(reference)

Normalize a CGMES reference into VeraGrid UUID format (no hyphens/underscores).

## Function: is_reference_priority_one(reference_priority)

Check if a referencePriority value represents slack priority 1.

## Function: find_terminal_bus(cgmes_terminal, bus_dict, TopologicalNode_tpe, DCTopologicalNode_tpe)

Find the bus associated to a terminal.

## Function: find_terminal_bus_connectivity_priority(cgmes_terminal, bus_dict, TopologicalNode_tpe, DCTopologicalNode_tpe)

Find the bus associated to a terminal while prioritizing ConnectivityNode.

## Function: find_object_by_idtag(object_list, target_idtag)

Finds an object with the specified idtag

## Function: get_slack_id(machines)

Retrieves the ID of a Topological Node from a list of SynchronousMachines.

## Function: get_operational_limit_kind(op_lim_type)

Read the operational limit kind across CGMES versions.

## Function: build_cgmes_limit_dicts(cgmes_model, device_type, logger)

Builds Rating dictionary for given device type from OperationalLimitSets

## Function: get_pu_values_power_transformer(power_transformer, System_Sbase)

Get the transformer p.u. values

## Function: get_pu_values_power_transformer3w(power_transformer, System_Sbase)

Get the transformer p.u. values

## Function: get_voltage_power_transformer_end(power_transformer_end)

:param power_transformer_end:

## Function: get_pu_values_power_transformer_end(power_transformer_end, Sbase_system)

Get the per-unit values of the equivalent PI model

## Function: get_voltage_ac_line_segment(ac_line_segment, logger)

:param ac_line_segment:

## Function: get_pu_values_ac_line_segment(ac_line_segment, logger, Sbase)

Get the per-unit values of the equivalent PI model

## Function: get_rate_ac_line_segment()

No docstring provided.

## Function: get_voltage_shunt(shunt, logger)

:param shunt:

## Function: get_values_shunt(shunt, logger, Sbase)

Get the per-unit values of the Shunt (per Section)

## Function: get_voltage_terminal(terminal, logger)

Get the voltage of this terminal

## Function: get_nominal_voltage(topological_node, logger)

Try to get the nominal voltage of a TopologicalNode

## Function: get_nominal_voltage_for_cn(cn, logger)

Try to get the nominal voltage of a ConnectivityNode

## Function: base_voltage_to_str(base_voltage)

:param base_voltage:

## Function: extract_base_voltage_value(base_voltage_obj)

Extract nominal voltage value from a BaseVoltage-like object.

## Function: recover_base_voltage_from_container(container_obj)

Recover nominal voltage from a ConnectivityNodeContainer/VoltageLevel-like object.

## Function: recover_base_voltage_from_topological_node(topological_node)

Recover nominal voltage from a TopologicalNode-like object with fallback paths.

## Function: recover_terminal_base_voltage(controlled_terminal)

Recover terminal nominal voltage using tolerant fallback chain.

## Function: get_regulating_control_params(cgmes_elm, cgmes_enums, bus_dict, TopologicalNode_tpe, DCTopologicalNode_tpe, logger, prefer_connectivity_node)

:param cgmes_elm:

## Function: find_object_by_uuid(cgmes_model, object_list, target_uuid)

Finds an object with the specified uuid

## Function: find_object_by_cond_eq_uuid(object_list, cond_eq_target_uuid)

Finds a conducting equipment object with the specified uuid

## Function: find_object_by_vnom(cgmes_model, object_list, target_vnom)

Find object in the base voltages

## Function: find_object_by_attribute(object_list, target_attr_name, target_value)

:param object_list:

## Function: get_ohm_values_power_transformer(r, x, g, b, r0, x0, g0, b0, nominal_power, rated_voltage, Sbase)

Get the transformer ohm values
