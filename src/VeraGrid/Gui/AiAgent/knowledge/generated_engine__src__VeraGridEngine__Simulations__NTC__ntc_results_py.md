# VeraGridEngine Module: src/VeraGridEngine/Simulations/NTC/ntc_results.py

- Original source path: `src/VeraGridEngine/Simulations/NTC/ntc_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: typing, numpy, pandas, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: OptimalNetTransferCapacityResults

- Bases: ResultsTemplate
- Summary: OPF results.

### Methods

- `get_bus_df(self)`
  Summary: Get a DataFrame with the buses results
- `get_branch_df(self)`
  Summary: Get a DataFrame with the branches results
- `get_hvdc_df(self)`
  Summary: Get a DataFrame with the battery results
- `mdl(self, result_type)`
  Summary: Plot the results
