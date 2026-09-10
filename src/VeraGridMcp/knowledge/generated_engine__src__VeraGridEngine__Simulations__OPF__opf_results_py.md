# VeraGridEngine Module: src/VeraGridEngine/Simulations/OPF/opf_results.py

- Original source path: `src/VeraGridEngine/Simulations/OPF/opf_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, pandas, matplotlib, matplotlib.colors, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: OptimalPowerFlowResults

- Bases: ResultsTemplate
- Summary: No docstring provided.

### Methods

- `phase_shift(self)`
  Summary: Cover for old API
- `get_bus_df(self)`
  Summary: Get a DataFrame with the buses results
- `get_branch_df(self)`
  Summary: Get a DataFrame with the branches results
- `get_gen_df(self)`
  Summary: Get a DataFrame with the generator results
- `get_batt_df(self)`
  Summary: Get a DataFrame with the battery results
- `get_hvdc_df(self)`
  Summary: Get a DataFrame with the battery results
- `mdl(self, result_type)`
  Summary: Plot the results
