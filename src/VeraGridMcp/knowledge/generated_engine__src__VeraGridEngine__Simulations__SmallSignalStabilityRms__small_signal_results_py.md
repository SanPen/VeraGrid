# VeraGridEngine Module: src/VeraGridEngine/Simulations/SmallSignalStabilityRms/small_signal_results.py

- Original source path: `src/VeraGridEngine/Simulations/SmallSignalStabilityRms/small_signal_results.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: numpy, math, matplotlib, typing, VeraGridEngine.Simulations.results_table, VeraGridEngine.Simulations.results_template, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Utils.Symbolic.symbolic

## Class: SPlotInteractionHandler

- Bases: none
- Summary: Handles interactive annotations and hover events for S-Domain stability plots.

### Methods

- `update_annotation(self, ind)`
  Summary: Updates the annotation text and position based on the hovered point.
- `on_hover(self, event)`
  Summary: Hover event callback logic.

## Class: SmallSignalStabilityRmsResults

- Bases: ResultsTemplate
- Summary: Small-signal Analysis results storage and visualization.

### Methods

- `mdl(self, result_type)`
  Summary: Export the results as a ResultsTable for plotting.
