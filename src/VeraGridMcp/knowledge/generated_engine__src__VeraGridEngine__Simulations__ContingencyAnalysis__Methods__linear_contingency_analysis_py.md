# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/linear_contingency_analysis.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/linear_contingency_analysis.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 2
- Representative imports: __future__, typing, numpy, numba, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Simulations.PowerFlow.power_flow_worker, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_results, VeraGridEngine.Simulations.LinearFactors.linear_analysis, VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_options, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: linear_contingency_analysis(nc, options, linear_multiple_contingencies, area_names, bus_area_indices, F, T, report_text, report_progress2, is_cancel, t, t_prob, logger)

Run N-1 simulation in series with HELM, non-linear solution

## Function: linear_contingency_scan_numba(nbr, n_con_groups, Pbus, rates, con_rates, PTDF, LODF, mon_idx, single_con_br_idx, single_con_cg_idx)

Fast contingency scan using the PTDF
