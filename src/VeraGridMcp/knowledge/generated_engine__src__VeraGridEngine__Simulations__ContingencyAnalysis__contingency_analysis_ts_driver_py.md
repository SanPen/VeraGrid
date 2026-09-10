# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/contingency_analysis_ts_driver.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/contingency_analysis_ts_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: numpy, numba, typing, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.LinearFactors.linear_analysis, VeraGridEngine.Simulations.LinearFactors.linear_analysis_options, VeraGridEngine.Simulations.ContingencyAnalysis.Methods.linear_contingency_analysis, VeraGridEngine.Simulations.ContingencyAnalysis.Methods.nonlinear_contingency_analysis, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_driver, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_ts_results, VeraGridEngine.enumerations, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.Clustering.clustering_results

## Function: max_abs_per_col(A)

No docstring provided.

## Function: max_abs_per_col_cx(A)

No docstring provided.

## Class: ContingencyAnalysisTimeSeriesDriver

- Bases: TimeSeriesDriverTemplate
- Summary: Contingency Analysis Time Series

### Methods

- `run_nonlinear_contingency_analysis(self)`
  Summary: Run a contingency analysis in series
- `run_linear_contingency_analysis(self)`
  Summary: Run a contingency analysis in series
- `run_contingency_scan(self)`
  Summary: Run a contngency analysis in series
- `run_newton_pa(self)`
  Summary: Run with Newton Power Analytics
- `run_gslv(self)`
  Summary: Run with Newton Power Analytics
- `run(self)`
  Summary: Run contingency analysis time series
