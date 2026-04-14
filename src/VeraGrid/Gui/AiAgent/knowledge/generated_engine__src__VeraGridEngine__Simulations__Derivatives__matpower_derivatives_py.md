# VeraGridEngine Module: src/VeraGridEngine/Simulations/Derivatives/matpower_derivatives.py

- Original source path: `src/VeraGridEngine/Simulations/Derivatives/matpower_derivatives.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 9
- Representative imports: numpy, typing, scipy.sparse, VeraGridEngine.basic_structures

## Function: dSbus_dV_matpower(Ybus, V)

Derivatives of the power Injections w.r.t the voltage

## Function: dSbr_dV_matpower(Yf, Yt, V, F, T, Cf, Ct)

Derivatives of the branch power w.r.t the branch voltage modules and angles

## Function: dSf_dV_matpower(Yf, V, F, Cf, Vc, diagVc, diagE, diagV)

Derivatives of the branch power "from" w.r.t the branch voltage modules and angles

## Function: dIbr_dV_matpower(Yf, Yt, V)

Computes partial derivatives of branch currents w.r.t. voltage

## Function: dSt_dV_matpower(Yt, V, T, Ct, Vc, diagVc, diagE, diagV)

Derivatives of the branch power "to" w.r.t the branch voltage modules and angles

## Function: dS_dm_matpower(V, Cf, Ct, R, X, B, Beq, k2, m, tau)

:param V:

## Function: dS_dtau_matpower(V, Cf, Ct, R, X, k2, m, tau)

Ybus = Cf' * Yf + Ct' * Yt + diag(Ysh)

## Function: dS_dbeq_matpower(V, Cf, Ct, k2, m)

:param V:

## Function: Jacobian(Ybus, V, idx_dP, idx_dQ, idx_dVa, idx_dVm)

Computes the system Jacobian matrix in polar coordinates
