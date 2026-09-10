# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/power_flow_ts_results.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/power_flow_ts_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: json, numpy, pandas, typing, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Simulations.Clustering.clustering_results

## Class: PowerFlowTimeSeriesResults

- Bases: ResultsTemplate
- Summary: No docstring provided.

### Methods

- `apply_new_time_series_rates(self, nc)`
  Summary: Recompute the loading with new rates
- `fill_circuit_info(self, grid)`
  Summary: :param grid:
- `set_at(self, t, results)`
  Summary: Set the results at the step t
- `merge_if(df, arr, ind, cols)`
  Summary: @param df:
- `to_json(self, fname)`
  Summary: Export as json
- `get_ordered_area_names(self)`
  Summary: :return:
- `get_inter_area_flows(self)`
  Summary: :return:
- `get_branch_values_per_area(self, branch_values)`
  Summary: :param branch_values:
- `get_hvdc_values_per_area(self, hvdc_values)`
  Summary: :param hvdc_values:
- `mdl(self, result_type)`
  Summary: :param result_type:
