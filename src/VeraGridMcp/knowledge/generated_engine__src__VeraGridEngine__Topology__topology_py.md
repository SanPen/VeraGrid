# VeraGridEngine Module: src/VeraGridEngine/Topology/topology.py

- Original source path: `src/VeraGridEngine/Topology/topology.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 18
- Representative imports: __future__, typing, numpy, numba, scipy.sparse, scipy.sparse, VeraGridEngine.basic_structures

## Function: find_islands_numba(node_number, indptr, indices, active)

Method to get the islands of a graph

## Function: get_elements_of_the_island_numba(n_rows, indptr, indices, island, active)

Get the element indices of the island

## Function: find_islands(adj, active)

Method to get the islands of a graph

## Function: get_elements_of_the_island(C_element_bus, island, active)

Get the branch indices of the island

## Function: get_island_monopole_indices(bus_map, elm_active, elm_bus)

:param bus_map:

## Function: get_island_branch_indices(bus_map, elm_active, F, T)

:param bus_map:

## Function: build_reducible_branches_C_coo(F, T, reducible, active)

Build the COO coordinates of the C matrix

## Function: build_branches_C_coo_2(bus_active, F1, T1, active1, F2, T2, FN2, active2)

Build the COO coordinates of the C matrix

## Function: build_branches_C_coo_3(bus_active, F1, T1, active1, F2, T2, FN2, active2, F3, T3, active3)

Build the COO coordinates of the C matrix

## Function: get_adjacency_matrix(C_branch_bus_f, C_branch_bus_t, branch_active, bus_active)

Compute the adjacency matrix

## Function: find_different_states(states_array)

Find the different branch states in time that may lead to different islands

## Function: get_csr_bus_indices(C)

Get the bus indices given a CSR shunt-element->bus connectivity matrix

## Class: ConnectivityMatrices

- Bases: none
- Summary: Connectivity matrices

### Methods

- `Cf(self)`
  Summary: Get the connectivity from matrix
- `Ct(self)`
  Summary: Get the connectivity to matrix
- `C(self)`
  Summary: Adjacency matrix
- `get_adjacency(self, bus_active)`
  Summary: :param bus_active:

## Function: compute_connectivity(branch_active, Cf_, Ct_)

Compute the from and to connectivity matrices applying the branch states

## Function: compute_connectivity_flexible(branch_active, Cf_, Ct_, hvdc_active, Cf_hvdc, Ct_hvdc, vsc_active, Cf_vsc, Ct_vsc)

Compute the from and to connectivity matrices applying the branch states

## Function: sum_per_bus(nbus, bus_indices, magnitude)

Summation of magnitudes per bus (real)

## Function: sum_per_bus_cx(nbus, bus_indices, magnitude)

Summation of magnitudes per bus (complex)

## Function: sum_per_bus_bool(nbus, bus_indices, magnitude)

Summation of magnitudes per bus (bool)

## Function: dev_per_bus(nbus, bus_indices)

Summation of magnitudes per bus (bool)
