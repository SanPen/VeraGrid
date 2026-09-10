# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/helm_contingency_analysis.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/helm_contingency_analysis.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 1
- Representative imports: __future__, numpy, typing, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Compilers.circuit_to_data, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_results, VeraGridEngine.Simulations.ContingencyAnalysis.Methods.helm_contingencies, VeraGridEngine.Simulations.PowerFlow.power_flow_worker, VeraGridEngine.Simulations.PowerFlow.power_flow_options, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_options, VeraGridEngine.enumerations

## Function: helm_contingency_analysis(grid, options, calling_class, opf_results, t, t_prob)

Run N-1 simulation in series with HELM, non-linear solution
