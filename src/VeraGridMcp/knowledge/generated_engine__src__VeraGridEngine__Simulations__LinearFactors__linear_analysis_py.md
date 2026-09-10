# VeraGridEngine Module: src/VeraGridEngine/Simulations/LinearFactors/linear_analysis.py

- Original source path: `src/VeraGridEngine/Simulations/LinearFactors/linear_analysis.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 5
- Top-level function count: 7
- Representative imports: __future__, numpy, numba, warnings, scipy.sparse, typing, scipy.sparse, scipy.sparse.linalg, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Devices.Aggregation.contingency_group, VeraGridEngine.Devices.Aggregation.contingency, VeraGridEngine.Simulations.Derivatives.ac_jacobian, VeraGridEngine.Simulations.Derivatives.csc_derivatives

## Function: make_contingency_flows(base_flow, lodf_factors, ptdf_factors, injections, threshold)

Compute the general contingency flows

## Function: make_jacobian_ptdf(Ybus, Yf, F, T, V, pq, pv, distribute_slack)

Compute the AC-PTDF

## Function: make_ptdf(Bpqpv, Bf, no_slack, distribute_slack)

Build the PTDF matrix

## Function: make_acdc_ptdf(nc, logger, distribute_slack)

Build the ACDC PTDF matrix

## Function: make_lodf(Cf, Ct, PTDF, correct_values, numerical_zero)

Compute the LODF matrix

## Function: make_transfer_limits(ptdf, flows, rates)

Compute the maximum transfer limits of each branch in normal operation

## Function: create_M_numba(lodf, branch_contingency_indices)

:param lodf:

## Class: LinearAnalysis

- Bases: none
- Summary: Linear Analysis

### Methods

- `get_transfer_limits(self, flows, rates)`
  Summary: Compute the maximum transfer limits of each branch in normal operation
- `get_flows(self, Sbus, P_hvdc, P_vsc)`
  Summary: Compute the time series branch Sf using the PTDF
- `get_flows2d(self, Sbus, P_hvdc, P_vsc)`
  Summary: Compute the time series branch Sf using the PTDF
- `get_injections(self, flows)`
  Summary: Get injections that satisfy the flows
- `get_injections_2d(self, flows)`
  Summary: Get injections that satisfy the flows

## Class: LinearMultiContingency

- Bases: none
- Summary: LinearMultiContingency

### Methods

- `has_injection_contingencies(self)`
  Summary: Check if this multi-contingency has bus injection modifications
- `get_contingency_flows(self, base_branches_flow, injections, hvdc_flow, vsc_flow)`
  Summary: Get contingency flows
- `get_lp_contingency_flows(self, base_flow, injections, hvdc_flow, vsc_flow)`
  Summary: Get contingency flows using the LP interface equations
- `get_alpha_n1(self, dP, dT)`
  Summary: Compute the N-1 sensitivities to the inter-area exchange

## Class: ContingencyIndices

- Bases: none
- Summary: Contingency indices

### Methods

- No methods detected.

## Class: LinearMultiContingencies

- Bases: none
- Summary: LinearMultiContingencies

### Methods

- `contingency_group_dict(self)`
  Summary: get the contingency grooups dictionary
- `get_contingency_group_names(self)`
  Summary: Returns a list of the names of the used contingency groups
- `compute(self, lin, ptdf_threshold, lodf_threshold)`
  Summary: Make the LODF with any contingency combination using the declared contingency objects
- `get_single_con_branch_idx(self)`
  Summary: Get the branch index array and the contingency group it belongs array

## Class: LinearAnalysisTs

- Bases: none
- Summary: Class to compute the different linear states of a grid

### Methods

- `get_linear_analysis_at(self, t_idx)`
  Summary: :param t_idx:
- `get_flows_at(self, t_idx, P)`
  Summary: Get the flows at a time step
- `get_branch_flow_ts(self, branch_idx, bus_idx, P)`
  Summary: Get the flow time series of a single branch given the injection time series of a single bus
- `get_flows_ts(self, P, progress_func, progress_text)`
  Summary: Get the flow time series of all branches given the injection time series all buses
- `get_injections_ts(self, flows_ts)`
  Summary: Get the flow time series of all branches given the injection time series all buses
