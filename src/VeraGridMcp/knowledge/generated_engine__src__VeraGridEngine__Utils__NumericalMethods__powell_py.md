# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/powell.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/powell.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 3
- Representative imports: time, numpy, typing, VeraGridEngine.basic_structures, VeraGridEngine.Utils.NumericalMethods.sparse_solve, VeraGridEngine.basic_structures, VeraGridEngine.Utils.NumericalMethods.common

## Function: compute_beta(a, b, delta)

compute the beta parameter

## Function: compute_hdl(hgn, hsd, g, alpha, delta, f_error)

Compute the Hdl vector

## Function: powell_dog_leg(func, func_args, x0, tol, max_iter, trust_region_radius, verbose, logger)

Powell's Dog leg algorithm to solve:
