# VeraGridEngine Module: src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/powell_fx.py

- Original source path: `src/VeraGridEngine/Simulations/PowerFlow/NumericalMethods/powell_fx.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 3
- Representative imports: time, typing, numpy, VeraGridEngine.Utils.NumericalMethods.sparse_solve, VeraGridEngine.Simulations.PowerFlow.power_flow_results, VeraGridEngine.Simulations.PowerFlow.Formulations.pf_formulation_template, VeraGridEngine.Utils.Sparse.csc2, VeraGridEngine.basic_structures, VeraGridEngine.Utils.NumericalMethods.common

## Function: compute_beta(a, b, delta)

compute the beta parameter

## Function: compute_hdl(hgn, hsd, g, alpha, delta, f_error)

Compute the Hdl vector

## Function: powell_fx(problem, tol, max_iter, trust, verbose, logger)

Powell's Dog leg algorithm to solve:
