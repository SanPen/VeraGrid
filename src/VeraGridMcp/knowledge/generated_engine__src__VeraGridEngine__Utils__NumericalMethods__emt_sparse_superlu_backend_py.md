# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/emt_sparse_superlu_backend.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/emt_sparse_superlu_backend.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 2
- Representative imports: __future__, typing, numpy, scipy.sparse, scipy.sparse.linalg, VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: _permute_csc_data_by_columns(source_data, source_indptr, column_perm, target_indptr, target_data)

Reorder CSC numeric values according to a persistent column permutation.

## Function: _scatter_permuted_solution_to_original_order(permuted_solution, inverse_column_perm, out_solution)

Scatter a solution computed on a column-permuted system back to original order.

## Class: SuperLUFactorizationHandle

- Bases: SparseLinearFactorizationHandle
- Summary: Factorization handle backed by SciPy SuperLU.

### Methods

- `solve_into(self, rhs, out_solution)`
  Summary: Solve the sparse system into a caller-owned output buffer.
- `get_active_matrix(self)`
  Summary: Return the sparse matrix associated with the current factorization.

## Class: SuperLUSparseBackend

- Bases: SparseLinearSolverBackend
- Summary: EMT sparse backend backed by SciPy SuperLU.

### Methods

- `get_name(self)`
  Summary: Return the backend name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type.
- `is_available(self)`
  Summary: Return whether the backend is available.
- `supports_symbolic_analysis_reuse(self)`
  Summary: Return whether this backend supports persistent symbolic reuse.
- `_try_build_persistent_ordering(self, lu_obj)`
  Summary: Store one persistent column ordering discovered by SuperLU.
- `factorize(self, matrix, analysis_handle)`
  Summary: Factorize the current EMT Jacobian.
- `get_backend_stats(self)`
  Summary: Return backend-specific statistics.

## Class: SuperLUSparseBackendProvider

- Bases: SparseLinearSolverBackendProvider
- Summary: Provider for the internal SuperLU EMT sparse backend.

### Methods

- `get_name(self)`
  Summary: Return the provider name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type.
- `is_available(self)`
  Summary: Return whether the provider is available.
- `create_backend(self, base_matrix, base_data)`
  Summary: Create the internal SuperLU sparse backend.
