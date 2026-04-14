# VeraGridEngine Module: src/VeraGridEngine/Simulations/ShortCircuitStudies/short_circuit_results.py

- Original source path: `src/VeraGridEngine/Simulations/ShortCircuitStudies/short_circuit_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, pandas, VeraGridEngine.Simulations.results_template, VeraGridEngine.Simulations.results_table, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_basic_formulation_3ph

## Class: ShortCircuitResults

- Bases: ResultsTemplate
- Summary: No docstring provided.

### Methods

- `elapsed(self)`
  Summary: Check if converged in all modes
- `apply_from_island(self, sc_idx, results, b_idx, br_idx, hvdc_idx, vsc_idx)`
  Summary: Apply results from another island circuit to the circuit results represented
- `mdl(self, result_type)`
  Summary: :param result_type:
- `get_voltage_df(self, sc_idx)`
  Summary: :param sc_idx:
- `get_current_df(self, sc_idx)`
  Summary: :param sc_idx:
- `get_voltage_3ph_df(self, sc_idx)`
  Summary: :param sc_idx:
- `export_all(self)`
  Summary: Exports all the results to DataFrames.
