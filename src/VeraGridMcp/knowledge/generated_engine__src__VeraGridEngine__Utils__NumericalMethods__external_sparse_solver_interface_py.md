# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/external_sparse_solver_interface.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/external_sparse_solver_interface.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 0
- Representative imports: __future__, typing, scipy.sparse, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: SparseLinearFactorizationHandle

- Bases: none
- Summary: Abstract sparse factorization handle used by EMT sparse backends.

### Methods

- `solve_into(self, rhs, out_solution)`
  Summary: Solve the factored sparse system into a caller-owned output buffer.
- `get_active_matrix(self)`
  Summary: Return the sparse matrix associated with the active factorization path.
- `get_stats(self)`
  Summary: Return factorization-handle statistics.

## Class: SparseLinearSolverBackend

- Bases: none
- Summary: Abstract sparse linear solver backend used by EMT solvers.

### Methods

- `get_name(self)`
  Summary: Return the human-readable backend name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type associated with this backend.
- `is_available(self)`
  Summary: Return whether the backend can be used in the current process.
- `requires_csc(self)`
  Summary: Return whether the backend expects CSC matrices.
- `supports_symbolic_analysis_reuse(self)`
  Summary: Return whether the backend exposes reusable symbolic analysis.
- `supports_numeric_refactorization(self)`
  Summary: Return whether the backend supports numeric-only refactorization.
- `analyze(self, matrix)`
  Summary: Perform reusable symbolic analysis on the sparse matrix if supported.
- `factorize(self, matrix, analysis_handle)`
  Summary: Build a sparse factorization handle for the current numeric values.
- `refactor_numeric(self, matrix, analysis_handle, previous_factorization)`
  Summary: Rebuild only the numeric factorization when supported.
- `get_backend_stats(self)`
  Summary: Return backend-specific statistics.

## Class: SparseLinearSolverBackendProvider

- Bases: none
- Summary: Factory object that creates EMT sparse solver backends.

### Methods

- `get_name(self)`
  Summary: Return the provider name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type associated with the provider.
- `is_available(self)`
  Summary: Return whether the provider is available.
- `create_backend(self, base_matrix, base_data)`
  Summary: Create one sparse backend bound to the EMT Jacobian buffers.
