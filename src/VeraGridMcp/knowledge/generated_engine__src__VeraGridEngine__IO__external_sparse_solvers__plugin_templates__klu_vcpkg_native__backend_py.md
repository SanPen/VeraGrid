# VeraGridEngine Module: src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/klu_vcpkg_native/backend.py

- Original source path: `src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/klu_vcpkg_native/backend.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 6
- Representative imports: __future__, importlib.machinery, importlib.util, os, pathlib, typing, scipy.sparse, VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: get_plugin_directory()

Return the directory containing this plugin backend.

## Function: get_native_build_directory()

Return the directory where the native KLU extension is expected.

## Function: get_vcpkg_root()

Return the vcpkg install root used by the native KLU plugin.

## Function: get_native_extension_path()

Return the compiled native extension path when present.

## Function: load_native_backend_module()

Load the compiled native KLU backend module.

## Function: is_native_klu_backend_available()

Return whether the native KLU backend is buildable and loadable.

## Class: NativeKluFactorizationHandle

- Bases: SparseLinearFactorizationHandle
- Summary: EMT sparse factorization handle backed by the native KLU extension.

### Methods

- `solve_into(self, rhs, out_solution)`
  Summary: Solve the sparse system into the caller-owned output buffer.
- `get_active_matrix(self)`
  Summary: Return the active sparse matrix.
- `get_stats(self)`
  Summary: Return factorization-handle statistics.

## Class: KluVcpkgNativeBackend

- Bases: SparseLinearSolverBackend
- Summary: EMT sparse backend backed by the native KLU extension module.

### Methods

- `get_name(self)`
  Summary: Return the backend name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type.
- `is_available(self)`
  Summary: Return whether the backend is available.
- `supports_symbolic_analysis_reuse(self)`
  Summary: Return whether symbolic analysis can be reused.
- `supports_numeric_refactorization(self)`
  Summary: Return whether numeric refactorization is supported.
- `analyze(self, matrix)`
  Summary: Build a reusable symbolic analysis handle.
- `factorize(self, matrix, analysis_handle)`
  Summary: Build a numeric KLU factorization handle.
- `refactor_numeric(self, matrix, analysis_handle, previous_factorization)`
  Summary: Rebuild only the numeric factorization when supported.
- `get_backend_stats(self)`
  Summary: Return backend-specific statistics.

## Class: KluVcpkgNativeProvider

- Bases: SparseLinearSolverBackendProvider
- Summary: Provider for the native vcpkg-backed KLU EMT sparse backend.

### Methods

- `get_name(self)`
  Summary: Return the provider name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type.
- `is_available(self)`
  Summary: Return whether the provider is available.
- `create_backend(self, base_matrix, base_data)`
  Summary: Create the native KLU sparse backend.
