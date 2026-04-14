# VeraGridEngine Module: src/VeraGridEngine/DataStructures/numerical_circuit.py

- Original source path: `src/VeraGridEngine/DataStructures/numerical_circuit.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 2
- Representative imports: __future__, typing, enum, numba, numpy, scipy.sparse, VeraGridEngine.Devices, VeraGridEngine.Topology.simulation_indices, VeraGridEngine.Topology.topology, VeraGridEngine.basic_structures, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Topology.topology, VeraGridEngine.Topology.simulation_indices, VeraGridEngine.Topology.admittance_matrices, VeraGridEngine.DataStructures.battery_data

## Function: build_q_limits(nbus, Sbase, gen_idx, q_min_gen, q_max_gen, active_gen, controllable_gen, batt_idx, q_min_batt, q_max_batt, active_batt, controllable_batt, sh_idx, q_min_sh, q_max_sh, active_sh, controllable_sh, hvdc_f, hvdc_t, q_min_hvdc_f, q_max_hvdc_f, q_min_hvdc_t, q_max_hvdc_t, active_hvdc)

:param nbus:

## Function: check_arr(arr, arr_expected, tol, name, test, logger)

:param arr:

## Class: DataStructType

- Bases: Enum
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: NumericalCircuit

- Bases: none
- Summary: Class storing the calculation information of the devices

### Methods

- `propagate_bus_result(self, bus_magnitude)`
  Summary: This function applies the __bus_map_arr to a calculated magnitude to
- `propagate_bus_result_mat(self, bus_magnitude)`
  Summary: This function applies the __bus_map_arr to a calculated magnitude to
- `topology_performed(self)`
  Summary: Flag indicating if topology processing happened here
- `get_reduction_bus_mapping(self)`
  Summary: Get array is used to keep track of the bus topological reduction
- `get_power_injections(self)`
  Summary: Compute the power
- `get_power_injections_pu(self)`
  Summary: Compute the power
- `get_current_injections_pu(self)`
  Summary: :return:
- `get_admittance_injections_pu(self)`
  Summary: :return:
- `get_Yshunt_bus_pu(self)`
  Summary: :return:
- `consolidate_information(self)`
  Summary: Consolidates the information of this object
- `copy(self)`
  Summary: Deep copy of ths object
- `init_idtags_dict(self)`
  Summary: Initialize the internal structure for idtags querying
- `query_idtag(self, idtag)`
  Summary: Query the structure and index where an idtag exists
- `set_investments_status(self, investments_list, status)`
  Summary: Set the status of a list of investments
- `set_con_or_ra_status(self, event_list, revert)`
  Summary: Set the status of a list of contingencies or remedial actions
- `get_simulation_indices(self, Sbus, bus_types, force_only_pq_pv_vd_types)`
  Summary: Get the simulation indices
- `get_connectivity_matrices(self)`
  Summary: Get connectivity matrices
- `get_admittance_matrices(self)`
  Summary: Get Admittance structures
- `get_series_admittance_matrices(self)`
  Summary: :return:
- `get_fast_decoupled_amittances(self)`
  Summary: :return:
- `get_linear_admittance_matrices(self, indices)`
  Summary: Get the linear admittances
- `get_reactive_power_limits(self)`
  Summary: compute the reactive power limits in place
- `compute_adjacency_matrix(self, consider_hvdc_as_island_links)`
  Summary: Compute the adjacency matrix
- `process_reducible_branches(self)`
  Summary: Process the reducible branches (i.e. reduce branches like the switches) in-place
- `get_island(self, bus_idx, logger)`
  Summary: Get the island corresponding to the given buses
- `split_into_islands(self, ignore_single_node_islands, consider_hvdc_as_island_links, logger)`
  Summary: Split circuit into islands
- `compare(self, nc_2, tol)`
  Summary: Compare this numerical circuit with another numerical circuit
- `get_structural_ntc(self, bus_a1_idx, bus_a2_idx)`
  Summary: Get the structural NTC
- `is_dc(self)`
  Summary: Check if this island is DC
