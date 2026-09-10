# VeraGridEngine Module: src/VeraGridEngine/IO/ucte/ucte_to_veragrid.py

- Original source path: `src/VeraGridEngine/IO/ucte/ucte_to_veragrid.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 25
- Representative imports: __future__, math, collections, typing, numpy, VeraGridEngine.Devices, VeraGridEngine.Devices.Branches.sequence_line_type, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.IO.ucte.devices.ucte_base, VeraGridEngine.IO.ucte.devices.ucte_circuit, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: is_xnode_code(node_code)

No docstring provided.

## Function: get_line_min_z()

No docstring provided.

## Function: get_default_power_limit()

No docstring provided.

## Function: get_current_limit_a(current_limit)

No docstring provided.

## Function: get_current_limit_ka(current_limit)

No docstring provided.

## Function: same_nominal_voltage(bus_f, bus_t, tol)

No docstring provided.

## Function: compute_switch_rate(bus_f, bus_t, current_limit)

No docstring provided.

## Function: build_xnode_active_line_counts(ucte_grid, logger)

No docstring provided.

## Function: build_technologies(grid)

No docstring provided.

## Function: parse_nodes(ucte_grid, grid, logger)

Create buses and their injections.

## Function: add_switch(grid, code, name, current_limit, bus_f, bus_t, active, reducible)

No docstring provided.

## Function: add_switch_from_line(grid, ucte_elm, bus_f, bus_t, active, reducible)

No docstring provided.

## Function: add_switch_from_transformer(grid, ucte_elm, bus_f, bus_t, active, reducible)

No docstring provided.

## Function: add_standard_line(grid, ucte_elm, bus_f, bus_t, active, reducible, logger)

No docstring provided.

## Function: parse_lines(ucte_grid, grid, bus_dict, logger)

Parse UCTE lines and couplers.

## Function: has_zero_transformer_impedance(ucte_elm, tol)

No docstring provided.

## Function: compute_tap_span(regulator, tap_tables)

No docstring provided.

## Function: choose_tap_number(regulator)

No docstring provided.

## Function: build_tap_changer_type(regulator)

No docstring provided.

## Function: build_current_tap_state(regulator, tap_type)

No docstring provided.

## Function: apply_tap_table(elm, ucte_elm, tap_tables, low_tap_position, current_tap_number, logger)

No docstring provided.

## Function: build_transformer_tap_data(ucte_elm, regulator, tap_tables, bus_f, logger)

No docstring provided.

## Function: parse_transformer(ucte_grid, grid, bus_dict, logger)

Parse UCTE transformers.

## Function: parse_exchange_power(ucte_grid, grid, bus_dict, logger)

Exchange powers are currently ignored by the VeraGrid UCTE importer.

## Function: convert_ucte_to_veragrid(ucte_grid, logger)

Convert UCTE grid to VeraGrid.
