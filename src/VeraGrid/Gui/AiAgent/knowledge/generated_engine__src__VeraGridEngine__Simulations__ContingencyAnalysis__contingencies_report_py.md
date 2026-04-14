# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/contingencies_report.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/contingencies_report.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 2
- Representative imports: numpy, numba, pandas, scipy.sparse, typing, VeraGridEngine.basic_structures, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Devices, VeraGridEngine.Simulations.LinearFactors.linear_analysis, VeraGridEngine.Simulations.ContingencyAnalysis.Methods.srap, VeraGridEngine.Utils.Sparse.csc_numba

## Function: get_ptdf_comp_numba(data, indices, indptr, PTDF, m, bd_indices)

This computes the compensatd PTDF for a single branch

## Function: get_ptdf_comp(mon_br_idx, branch_indices, mlodf_factors, PTDF)

Get the compensated PTDF values for a single monitored branch

## Class: ContingencyTableEntry

- Bases: none
- Summary: Entry of a contingency report

### Methods

- `get_headers(self)`
  Summary: Get the headers
- `to_list(self, time_array, time_format)`
  Summary: Get a list representation of this entry
- `to_string_list(self, time_array, time_format)`
  Summary: Get list of string values
- `to_array(self, time_array, time_format)`
  Summary: Get array of string values

## Class: ContingencyResultsReport

- Bases: none
- Summary: Contingency results report table

### Methods

- `add_entry(self, entry)`
  Summary: Add contingencies entry
- `add(self, time_index, t_prob, mon_idx, con_group_idx, area_from, area_to, base_name, contingency_name, base_rating, contingency_rating, srap_rating, base_flow, post_contingency_flow, post_srap_flow, base_loading, post_contingency_loading, post_srap_loading, msg_ov, msg_srap, srap_power, solved_by_srap)`
  Summary: Add report data
- `merge(self, other)`
  Summary: Add another ContingencyResultsReport in-place
- `size(self)`
  Summary: Get the size
- `n_cols(self)`
  Summary: Number of columns
- `get_headers()`
  Summary: Get the headers
- `get_index(self)`
  Summary: Get the index
- `get_data(self, time_array, time_format)`
  Summary: Get data as list of lists of strings
- `get_df(self, time_array, time_format)`
  Summary: Get data as pandas DataFrame
- `get_summary_table(self, time_array, time_format)`
  Summary: :param time_array:
- `analyze(self, t, t_prob, mon_idx, nc, base_flow, base_loading, contingency_flows, contingency_loadings, contingency_group_idx, contingency_group, using_srap, srap_ratings, srap_max_power, srap_deadband, contingency_deadband, srap_revert_to_nominal_rating, multi_contingency, PTDF, available_power, srap_used_power, F, T, bus_area_indices, area_names, top_n, detailed_massive_report)`
  Summary: Analyze contingency results and add them to the report
