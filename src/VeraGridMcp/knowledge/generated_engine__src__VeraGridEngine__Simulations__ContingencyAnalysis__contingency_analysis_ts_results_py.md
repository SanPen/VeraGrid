# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/contingency_analysis_ts_results.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/contingency_analysis_ts_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, pandas, typing, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.ContingencyAnalysis.contingencies_report, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Simulations.Clustering.clustering_results

## Class: ContingencyAnalysisTimeSeriesResults

- Bases: ResultsTemplate
- Summary: Contingency analysis time series results

### Methods

- `nbus(self)`
  Summary: Number of buses
- `nbranch(self)`
  Summary: Number of branches
- `ncon(self)`
  Summary: Number of contingencies
- `apply_new_time_series_rates(self, nc)`
  Summary: Apply new rates
- `mdl(self, result_type)`
  Summary: Plot the results
