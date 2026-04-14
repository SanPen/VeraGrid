# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/power_flow_results_3ph.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/power_flow_results_3ph.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: numpy, pandas, matplotlib, matplotlib.colors, typing, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: get_3p_indices(length_3p)

get the 3-phase indexing

## Class: PowerFlowResults3Ph

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
- `get_bus_df(self)`
  Summary: Get a DataFrame with the buses results
- `get_branch_df(self)`
  Summary: Get a DataFrame with the branches results
- `get_voltage_3ph_df(self)`
  Summary: Get a DataFrame with the buses results, Vm in p.u., Va in deg
- `get_load_neutral_voltage_df(self)`
  Summary: Get a DataFrame with the load neutral voltage results, Vm in p.u., Va in deg
- `get_shunt_neutral_voltage_df(self)`
  Summary: Get a DataFrame with the load neutral voltage results, Vm in p.u., Va in deg
- `get_current_3ph_df(self)`
  Summary: Get a DataFrame with the current results in p.u.
- `get_voltage_unbalance_factor_df(self)`
  Summary: Get the Voltage Unbalance Factor (VUF)
- `get_current_unbalance_factor_df(self)`
  Summary: Get the Current Unbalance Factor (IUF)
- `export_all(self)`
  Summary: Exports all the results to DataFrames.
- `compare(self, other, tol)`
  Summary: Compare this results with another
- `mdl(self, result_type)`
  Summary: get the ResultsTable model
