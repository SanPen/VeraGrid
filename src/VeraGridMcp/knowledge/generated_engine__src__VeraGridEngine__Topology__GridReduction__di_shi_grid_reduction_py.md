# VeraGridEngine Module: src/VeraGridEngine/Topology/GridReduction/di_shi_grid_reduction.py

- Original source path: `src/VeraGridEngine/Topology/GridReduction/di_shi_grid_reduction.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 7
- Representative imports: __future__, numpy, typing, scipy.sparse.linalg, scipy.sparse, networkx, VeraGridEngine.Devices, VeraGridEngine.basic_structures, VeraGridEngine.Compilers.circuit_to_data

## Function: ward_reduction_non_linear(nc, e_buses, b_buses, i_buses, voltage, Sbus)

:param nc:

## Function: ward_reduction_linear(Ybus, e_buses, b_buses, i_buses)

:param Ybus:

## Function: ward_reduction_linear2(Ybus, e_buses, i_buses)

:param Ybus:

## Function: get_reduction_sets_1(nc, reduction_bus_indices)

Generate the set of bus indices for grid reduction

## Function: create_new_boundary_branches(grid, b_buses, Yeq_1, Ybbp_1, tol, use_linear)

:param grid:

## Function: find_gen_relocation(grid, reduction_bus_indices)

Relocate generators

## Function: di_shi_reduction(grid, reduction_bus_indices, V0, tol)

In-place Grid reduction using the Di-Shi equivalent model
