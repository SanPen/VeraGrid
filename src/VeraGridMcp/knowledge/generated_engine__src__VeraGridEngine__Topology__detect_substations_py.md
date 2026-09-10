# VeraGridEngine Module: src/VeraGridEngine/Topology/detect_substations.py

- Original source path: `src/VeraGridEngine/Topology/detect_substations.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 3
- Representative imports: __future__, typing, numpy, VeraGridEngine.Devices, VeraGridEngine.enumerations, VeraGridEngine.Devices.types, VeraGridEngine.Topology.topology, VeraGridEngine.basic_structures, scipy.sparse

## Function: get_bus_group_substation(bus_indices, buses)

Given a list of buses, return the first substation available

## Function: detect_substations(grid, r_x_threshold)

Given a Grid with buses, it will detect all the missing substations and voltage levels

## Function: detect_facilities(grid)

Create facilities automatically
