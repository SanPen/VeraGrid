# VeraGridEngine Module: src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/emt_floquet_operator.py

- Original source path: `src/VeraGridEngine/Simulations/SmallSignalStabilityEmt/emt_floquet_operator.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

EMT Floquet Linear Operators Module.

## Module Surface

- Class count: 3
- Top-level function count: 0
- Representative imports: numpy, scipy.sparse, scipy.sparse.linalg, typing, VeraGridEngine.Simulations.SmallSignalStabilityEmt.emt_floquet_numba_kernels, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: EmtFloquetOperator

- Bases: spla.LinearOperator
- Summary: HPC Matrix-Free Monodromy Operator for abc-frame EMT systems.

### Methods

- `_precompute_from_jit(self, jac_evaluator, static_params, n_ev_params, t_trajectory)`
  Summary: Evaluates and caches sparse LU factorizations using the JIT compiled evaluator
- `_precompute_lu_factorizations(self)`
  Summary: Pre-calculates SuperLU factorizations for the entire periodic trajectory.
- `_matvec(self, v0)`
  Summary: Applies the Monodromy operator to a single vector v0
- `_rmatvec(self, w0)`
  Summary: Adjoint (Backward) integration to extract Left Eigenvectors.

## Class: BlockEmtFloquetOperator

- Bases: spla.LinearOperator
- Summary: Advanced HPC Block Monodromy Operator for EMT Small-Signal Stability.

### Methods

- `_precompute_from_jit(self, jac_evaluator, static_params, n_ev_params, t_trajectory)`
  Summary: Evaluates and caches sparse LU factorizations using the JIT compiled evaluator.
- `_precompute_lu_factorizations(self)`
  Summary: Pre-calculates and caches the Sparse LU factorizations for the Jacobian
- `_matmat(self, X)`
  Summary: Applies the Monodromy operator to a dense block of vectors.
- `_matvec(self, v0)`
  Summary: Fallback routine: If a standard solver (like scipy.sparse.linalg.eigs)

## Class: AkStackBlockEmtFloquetOperator

- Bases: spla.LinearOperator
- Summary: Monodromy operator from an explicit stack of state-transition matrices A_k.

### Methods

- `_matvec(self, x)`
  Summary: Applies the operator to a single 1D vector.
- `_matmat(self, X)`
  Summary: Applies the transition matrix stack to a block of vectors.
- `matmat(self, X)`
  Summary: Public alias for matrix-matrix multiplication.
