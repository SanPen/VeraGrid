# VeraGridEngine Module: src/VeraGridEngine/Topology/VoltageLevels/vl_creation_common_functions.py

- Original source path: `src/VeraGridEngine/Topology/VoltageLevels/vl_creation_common_functions.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 4
- Representative imports: __future__, typing, VeraGridEngine.Devices, VeraGridEngine, VeraGridEngine.enumerations, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices.types, VeraGridEngine.Topology.VoltageLevels.single_bar, VeraGridEngine.Topology.VoltageLevels.double_bar, VeraGridEngine.Topology.VoltageLevels.breaker_and_a_half, VeraGridEngine.Topology.VoltageLevels.ring, VeraGridEngine.enumerations

## Function: transform_bus_to_connectivity_grid(grid, busbar)

Transform a BusBar into multiple Connectivity buses connected by branches.

## Function: transform_bus_into_voltage_level(grid, bus, vl_type, add_disconnectors, bar_by_segments, skip_injections_reconnection, enable_transfer_bus, reducible_branches, bay_assignments, x0, y0)

Transform a bus into a voltage level

## Function: _store_voltage_level_data(voltage, conn_buses, all_buses, vl_type, conn_buses_by_voltage, bars_by_voltage, vl_type_by_voltage)

Helper function to store voltage level data (connection buses, bars, and type)

## Function: create_substation(grid, se_name, se_code, lat, lon, vl_templates, buses_to_replace, x0, y0)

Create a complete substation
