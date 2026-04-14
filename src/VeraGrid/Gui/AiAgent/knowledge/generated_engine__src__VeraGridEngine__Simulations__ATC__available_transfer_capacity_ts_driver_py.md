# VeraGridEngine Module: src/VeraGridEngine/Simulations/ATC/available_transfer_capacity_ts_driver.py

- Original source path: `src/VeraGridEngine/Simulations/ATC/available_transfer_capacity_ts_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: __future__, numpy, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.LinearFactors.linear_analysis_options, VeraGridEngine.Simulations.LinearFactors.linear_analysis_ts_driver, VeraGridEngine.Simulations.LinearFactors.linear_analysis, VeraGridEngine.Simulations.ATC.available_transfer_capacity_driver, VeraGridEngine.Simulations.ATC.available_transfer_capacity_options, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.Clustering.clustering_results, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: AvailableTransferCapacityTimeSeriesResults

- Bases: ResultsTemplate
- Summary: AvailableTransferCapacityTimeSeriesResults

### Methods

- `clear(self)`
  Summary: Crear the results
- `make_report(self, threshold)`
  Summary: :return:
- `get_dict(self)`
  Summary: Returns a dictionary with the results sorted in a dictionary
- `mdl(self, result_type)`
  Summary: Plot the results

## Class: AvailableTransferCapacityTimeSeriesDriver

- Bases: TimeSeriesDriverTemplate
- Summary: No docstring provided.

### Methods

- `get_steps(self)`
  Summary: Get time steps list of strings
- `run(self)`
  Summary: Run thread
- `cancel(self)`
  Summary: No docstring provided.
