# VeraGridEngine Module: src/VeraGridEngine/Topology/GridReduction/ptdf_grid_reduction.py

- Original source path: `src/VeraGridEngine/Topology/GridReduction/ptdf_grid_reduction.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 13
- Representative imports: __future__, numpy, networkx, typing, VeraGridEngine.basic_structures, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Devices.Injections.generator, VeraGridEngine.Devices.Injections.battery, VeraGridEngine.Devices.Injections.static_generator, VeraGridEngine.Devices.Injections.load, VeraGridEngine.Simulations.LinearFactors.linear_analysis

## Function: get_Pgen(grid)

Get the complex bus power Injections due to the generation with and without srap

## Function: get_Pgen_ts(grid)

Get the complex bus power Injections due to the generation with and without srap

## Function: get_Pload(grid)

Get the complex bus power Injections due to the load with sign

## Function: get_Pload_ts(grid)

Get the complex bus power Injections due to the load with sign

## Function: relocate_injections(grid, reduction_bus_indices)

Relocate injection devices (generators, loads, etc.) from external buses to internal buses

## Function: _collapse_loads(loads, bus, has_ts, nt)

Sum loads into a single collapsed load with time-series support.

## Function: _collapse_generators(generators, bus, has_ts, nt, srap_enabled)

Sum generators into a single collapsed generator with time-series support.

## Function: compact_devices_after_reduction(grid, relocated_device_ids, compensation_prefix)

Compact devices on each bus after PTDF reduction.

## Function: get_reduction_sets(grid, reduction_bus_indices, add_vsc, add_hvdc, add_switch)

Generate the set of bus indices for grid reduction

## Function: ptdf_reduction(grid, reduction_bus_indices, tol)

In-place Grid reduction using the PTDF injection mirroring

## Function: ptdf_reduction_ree_bad(grid, reduction_bus_indices, tol)

In-place Grid reduction using the PTDF injection mirroring

## Function: ptdf_reduction_ree_less_bad(grid, reduction_bus_indices, tol)

In-place Grid reduction using the PTDF injection mirroring

## Function: ptdf_reduction_projected(grid, reduction_bus_indices, tol, distribute_slack, compact_devices)

In-place Grid reduction using the PTDF injection by projecting
