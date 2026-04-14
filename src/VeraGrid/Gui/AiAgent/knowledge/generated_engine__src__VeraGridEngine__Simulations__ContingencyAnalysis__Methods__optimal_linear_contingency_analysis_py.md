# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/optimal_linear_contingency_analysis.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/optimal_linear_contingency_analysis.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 1
- Representative imports: __future__, typing, numpy, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_results, VeraGridEngine.Simulations.LinearFactors.linear_analysis, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_options, VeraGridEngine.Simulations.OPF.Formulations.linear_opf_ts, VeraGridEngine.Simulations.OPF.opf_options, VeraGridEngine.basic_structures

## Function: optimal_linear_contingency_analysis(grid, options, opf_options, linear_multiple_contingencies, calling_class, t, t_prob, logger)

Run N-1 simulation in series with HELM, non-linear solution
