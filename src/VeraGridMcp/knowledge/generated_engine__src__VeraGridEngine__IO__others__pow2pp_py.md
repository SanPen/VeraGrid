# VeraGridEngine Module: src/VeraGridEngine/IO/others/pow2pp.py

- Original source path: `src/VeraGridEngine/IO/others/pow2pp.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 24
- Representative imports: math, traceback, numpy, typing, pandas, VeraGridEngine.basic_structures, VeraGridEngine.IO.others.helper_pow2pp, VeraGridEngine.Utils.Symbolic

## Function: find_bus_ids(element_table, pandapower_net, target_column_name, column_name_element_table)

Simplified version that doesn't rely on the identifier column

## Function: get_bus_index(pandapower_net, bus_id)

Get pandapower bus index from powsybl bus ID

## Function: convert_to_pandapower(network)

Convert pypowsybl network to pandapower network

## Function: create_buses(pandapower_net, powsybl_net)

Create buses from pypowsybl network, handling UUID suffixes

## Function: create_loads(pandapower_net, powsybl_net)

Create loads from pypowsybl network

## Function: create_generators(pandapower_net, powsybl_net)

Create generators from pypowsybl network, excluding slack generators

## Function: create_lines(pandapower_net, powsybl_net)

Create lines from pypowsybl network

## Function: identify_slack_generators(powsybl_net, generators, bus)

Identify slack generators based on extensions or other criteria

## Function: create_2w_transformers(pandapower_net, powsybl_net)

No docstring provided.

## Function: calculate_short_circuit_voltage(trafo_table)

Calculate short circuit voltage parameters for transformers with proper defaults

## Function: calculate_iron_losses_and_open_loop_losses(trafo_table)

Calculate iron losses with proper defaults

## Function: create_shunts(pandapower_net, powsybl_net)

No docstring provided.

## Function: map_element_type(powsybl_type)

Map powsybl element types to pandapower element types

## Function: create_or_get_bus_for_node(pandapower_net, node_id, nb_topology, powsybl_net)

Create or get a pandapower bus for a node

## Function: create_intermediate_bus(pandapower_net, vl_id, powsybl_net)

Create an intermediate bus for element-element switches

## Function: get_pandapower_bus_index(pandapower_net, bus_id)

Get pandapower bus index from powsybl bus ID

## Function: create_3w_transformers(pandapower_net, powsybl_net)

Create 3-winding transformers with proper parameter conversion and tap changer handling.

## Function: add_tap_parameters_for_3w_ratio_tap_changer(powsybl_net, trafo_table)

Add ratio tap changer parameters for 3-winding transformers

## Function: add_tap_parameters_for_3w_phase_tap_changer(powsybl_net, trafo_table)

Add phase tap changer parameters for 3-winding transformers

## Function: calculate_3w_impedance_parameters(trafo_table, conv, ref_winding, Sbase_common)

Convert star-leg impedances (r1,x1,r2,x2,r3,x3 in ohm) to vk_/vkr_ percent fields.

## Function: calculate_3w_iron_losses(trafo_table)

Calculate iron losses for 3-winding transformers

## Function: add_tap_parameters_for_ratio_tap_changer(powsybl_net, trafo_table)

Comprehensive ratio tap changer parameter calculation

## Function: add_tap_parameters_for_phase_tap_changer(powsybl_net, trafo_table)

Comprehensive phase tap changer parameter calculation

## Function: calculate_detailed_tap_parameters(trafo_table, idx, steps, tap_type)

Map powsybl tap data to pandapower so that the *current tap position* is accurate.
