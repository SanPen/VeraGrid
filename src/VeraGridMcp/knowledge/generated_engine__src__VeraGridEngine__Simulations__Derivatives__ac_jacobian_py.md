# VeraGridEngine Module: src/VeraGridEngine/Simulations/Derivatives/ac_jacobian.py

- Original source path: `src/VeraGridEngine/Simulations/Derivatives/ac_jacobian.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 6
- Representative imports: numba, numpy, numpy, scipy.sparse, VeraGridEngine.Simulations.Derivatives.csr_derivatives, VeraGridEngine.Simulations.Derivatives.csc_derivatives, VeraGridEngine.basic_structures, VeraGridEngine.Utils.NumericalMethods.common, VeraGridEngine.Utils.Sparse.csc2

## Function: create_J_csr(nbus, dS_dVm_x, dS_dVa_x, Yp, Yj, pvpq, pq, Jx, Jj, Jp)

Calculates Jacobian in CSR format.

## Function: AC_jacobian_csr(Ybus, V, pvpq, pq)

Create the AC Jacobian function with no embedded controls

## Function: create_J_csc(nbus, Yx, Yp, Yi, V, pvpq, pq)

Calculates Jacobian in CSC format.

## Function: AC_jacobian(Ybus, V, pvpq, pq)

Create the AC Jacobian function with no embedded controls

## Function: create_J_vc_csc(nbus, Yx, Yp, Yi, V, idx_dtheta, idx_dVm, idx_dP, idx_dQ)

Calculates Jacobian in CSC format.

## Function: AC_jacobianVc(Ybus, V, idx_dtheta, idx_dVm, idx_dQ)

Create the AC Jacobian function with no embedded controls
