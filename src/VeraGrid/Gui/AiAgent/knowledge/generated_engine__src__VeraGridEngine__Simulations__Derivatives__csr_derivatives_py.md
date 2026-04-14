# VeraGridEngine Module: src/VeraGridEngine/Simulations/Derivatives/csr_derivatives.py

- Original source path: `src/VeraGridEngine/Simulations/Derivatives/csr_derivatives.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 2
- Representative imports: numpy, numba, typing, scipy.sparse, scipy.sparse, VeraGridEngine.basic_structures, VeraGridEngine.Utils.Sparse.csc2

## Function: dSbus_dV_numba_sparse_csr(Yx, Yp, Yj, V, E)

partial derivatives of power injection w.r.t. voltage.

## Function: dSbus_dV_csr(Ybus, V)

Calls functions to calculate dS/dV depending on whether Ybus is sparse or not
