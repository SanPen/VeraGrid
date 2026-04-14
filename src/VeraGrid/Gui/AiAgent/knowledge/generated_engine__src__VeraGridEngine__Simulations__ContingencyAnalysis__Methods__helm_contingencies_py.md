# VeraGridEngine Module: src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/helm_contingencies.py

- Original source path: `src/VeraGridEngine/Simulations/ContingencyAnalysis/Methods/helm_contingencies.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: numpy, scipy, typing, VeraGridEngine.basic_structures, VeraGridEngine.DataStructures.numerical_circuit, VeraGridEngine.Topology.admittance_matrices, VeraGridEngine.Simulations.PowerFlow.NumericalMethods.helm_power_flow

## Function: calc_V_outage(nc, If, Ybus, Yf, sys_mat_factorization, V0, S0, Uini, Xini, Yslack, Vslack, vec_P, vec_Q, Ysh, vec_W, pq, pv, vd, pqpv, pqpv_original, pq_original, contingency_br_indices)

Calculate the voltage due to outages in a non-linear manner with HELM.

## Class: HelmVariations

- Bases: none
- Summary: Class to quickly evaluate topological variations based on HELM coefficients

### Methods

- `initialize(self)`
  Summary: No docstring provided.
- `compute_variations(self, contingency_br_indices)`
  Summary: Compute a branch contingency
