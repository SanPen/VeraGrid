# VeraGridEngine Module: src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/klu_vcpkg/backend.py

- Original source path: `src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/klu_vcpkg/backend.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 4
- Top-level function count: 7
- Representative imports: __future__, ctypes, os, pathlib, typing, numpy, scipy.sparse, VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Class: KluCommon

- Bases: ct.Structure
- Summary: ``klu_common`` structure for the 32-bit index / real KLU API.

### Methods

- No methods detected.

## Function: get_default_klu_native_root()

Return the default external native root containing vcpkg-installed KLU binaries.

## Function: resolve_klu_native_root()

Resolve the native root containing KLU binaries.

## Function: get_klu_bin_directory()

Return the directory containing KLU DLLs.

## Function: get_klu_include_directory()

Return the directory containing KLU headers.

## Function: add_klu_dll_directory()

Add the KLU DLL directory to the process DLL search path.

## Function: is_klu_vcpkg_runtime_available()

Return whether the required KLU DLL set is available.

## Function: load_klu_library()

Load the native KLU DLL and bind the required function signatures.

## Class: KluVcpkgFactorizationHandle

- Bases: SparseLinearFactorizationHandle
- Summary: Factorization handle backed by the native KLU DLL.

### Methods

- `solve_into(self, rhs, out_solution)`
  Summary: Solve the sparse system into the caller-owned output buffer.
- `get_active_matrix(self)`
  Summary: Return the matrix associated with the factorization handle.
- `get_stats(self)`
  Summary: Return factorization-handle statistics.

## Class: KluVcpkgBackend

- Bases: SparseLinearSolverBackend
- Summary: EMT sparse backend backed by SuiteSparse KLU installed through vcpkg.

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
  Summary: Return whether numeric-only refactorization is supported.
- `analyze(self, matrix)`
  Summary: Build the reusable KLU symbolic analysis object.
- `factorize(self, matrix, analysis_handle)`
  Summary: Build the KLU numeric factorization.
- `refactor_numeric(self, matrix, analysis_handle, previous_factorization)`
  Summary: Rebuild only the numeric factorization when supported.
- `get_backend_stats(self)`
  Summary: Return backend-specific statistics.

## Class: KluVcpkgProvider

- Bases: SparseLinearSolverBackendProvider
- Summary: Provider for the direct vcpkg-backed KLU EMT sparse backend.

### Methods

- `get_name(self)`
  Summary: Return the provider name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type.
- `is_available(self)`
  Summary: Return whether the provider is available.
- `create_backend(self, base_matrix, base_data)`
  Summary: Create the direct KLU sparse backend.
