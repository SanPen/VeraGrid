# VeraGridEngine Module: src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/pardiso_pypardiso/backend.py

- Original source path: `src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/pardiso_pypardiso/backend.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 5
- Representative imports: __future__, importlib, importlib.util, os, sys, pathlib, typing, numpy, scipy.sparse, VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: get_default_pardiso_runtime_directory()

Return the default external runtime directory for ``pypardiso``.

## Function: resolve_pardiso_runtime_directory()

Resolve the external runtime directory for ``pypardiso``.

## Function: ensure_pardiso_runtime_on_sys_path()

Put the external ``pypardiso`` runtime directory on ``sys.path`` when present.

## Function: is_pardiso_runtime_available()

Return whether ``pypardiso`` is available after injecting the external runtime directory.

## Function: get_pardiso_linear_solver()

Return the ``pypardiso`` sparse solve function.

## Class: PardisoPyFactorizationHandle

- Bases: SparseLinearFactorizationHandle
- Summary: Sparse factorization handle backed by the ``pypardiso`` solve interface.

### Methods

- `solve_into(self, rhs, out_solution)`
  Summary: Solve the sparse system into the caller-owned output buffer.
- `get_active_matrix(self)`
  Summary: Return the matrix associated with the handle.
- `get_stats(self)`
  Summary: Return factorization-handle statistics.

## Class: PardisoPyBackend

- Bases: SparseLinearSolverBackend
- Summary: EMT sparse backend backed by ``pypardiso``.

### Methods

- `get_name(self)`
  Summary: Return the backend name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type.
- `is_available(self)`
  Summary: Return whether the backend is available.
- `requires_csc(self)`
  Summary: Return whether the backend expects CSC matrices.
- `factorize(self, matrix, analysis_handle)`
  Summary: Build the PARDISO factorization handle.
- `get_backend_stats(self)`
  Summary: Return backend-specific statistics.

## Class: PardisoPyProvider

- Bases: SparseLinearSolverBackendProvider
- Summary: Provider for the external ``pypardiso`` EMT sparse backend.

### Methods

- `get_name(self)`
  Summary: Return the provider name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type.
- `is_available(self)`
  Summary: Return whether the provider is available.
- `create_backend(self, base_matrix, base_data)`
  Summary: Create the PARDISO sparse backend.
