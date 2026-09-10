# VeraGridEngine Module: src/VeraGridEngine/Simulations/StateEstimation/state_estimation_results.py

- Original source path: `src/VeraGridEngine/Simulations/StateEstimation/state_estimation_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: numpy, pandas, matplotlib, matplotlib.colors, typing, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: NumericStateEstimationResults

- Bases: none
- Summary: NumericStateEstimationResults, used to return values from the numerical methods

### Methods

- No methods detected.

## Class: StateEstimationResults

- Bases: ResultsTemplate
- Summary: No docstring provided.

### Methods

- `converged(self)`
  Summary: Check if converged in all modes
- `error(self)`
  Summary: Check if converged in all modes
- `elapsed(self)`
  Summary: Check if converged in all modes
- `iterations(self)`
  Summary: Check if converged in all modes
- `apply_from_island(self, results, b_idx, br_idx, hvdc_idx, vsc_idx)`
  Summary: Apply results from another island circuit to the circuit results represented
- `get_report_dataframe(self, island_idx)`
  Summary: Get a DataFrame containing the convergence report.
- `get_overload_score(self, branch_prices)`
  Summary: Compute the cost of overload
- `get_bus_df(self)`
  Summary: Get a DataFrame with the buses results
- `get_branch_df(self)`
  Summary: Get a DataFrame with the branches results
- `mdl(self, result_type)`
  Summary: get the ResultsTable model
- `export_all(self)`
  Summary: Exports all the results to DataFrames.
- `compare(self, other, tol)`
  Summary: Compare this results with another
