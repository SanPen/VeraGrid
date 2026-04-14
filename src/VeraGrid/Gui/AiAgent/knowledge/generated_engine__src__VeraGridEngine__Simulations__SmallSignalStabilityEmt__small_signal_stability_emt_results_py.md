# VeraGridEngine Module: src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/small_signal_stability_emt_results.py

- Original source path: `src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/small_signal_stability_emt_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: numpy, matplotlib, typing, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Utils.Symbolic.symbolic

## Class: SmallSignalStabilityEmtResults

- Bases: ResultsTemplate
- Summary: Container and processor for EMT Floquet Small-Signal Stability results.

### Methods

- `_compute_pf(self)`
  Summary: Calculates bi-orthonormal Participation Factors.
- `mdl(self, result_type)`
  Summary: Export results as ResultsTable for the VeraGrid UI/Engine.
- `report_stability(self)`
  Summary: Generates a standard stability report string based on the spectral radius.
- `validate_spectral_gaps(self, h_step)`
  Summary: Evaluates the metric compactness of ALL calculated modes.
