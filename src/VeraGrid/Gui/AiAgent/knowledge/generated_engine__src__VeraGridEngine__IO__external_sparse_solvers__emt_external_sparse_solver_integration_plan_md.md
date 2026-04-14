# VeraGridEngine Doc: Emt External Sparse Solver Integration Plan

- Original source path: `src/VeraGridEngine/IO/external_sparse_solvers/emt_external_sparse_solver_integration_plan.md`
- Knowledge kind: generated VeraGridEngine documentation

## Document Content

# EMT External Sparse Solver Integration Plan

## Goal

Expose external sparse linear solver backends to the EMT engine without copying
license-restricted libraries into VeraGrid. The first integration target is the
`StructuralCompiledSolver` because it already contains the strongest sparse reuse
policy and therefore offers the highest leverage.

This integration documentation lives under `src/VeraGridEngine/IO/external_sparse_solvers`
because the external solver connection is an installation, discovery, and runtime
integration concern rather than an EMT benchmark or demo concern.

## Existing Infrastructure We Reuse

- Sparse solver enum:
  - `src/VeraGridEngine/enumerations.py`
- Basic sparse solver discovery and wrappers:
  - `src/VeraGridEngine/Utils/NumericalMethods/sparse_solve.py`
- Default VeraGrid plugin directory:
  - `src/VeraGridEngine/IO/file_system.py`
- EMT options and solver factory:
  - `src/VeraGridEngine/Simulations/EMT/emt_options.py`
  - `src/VeraGridEngine/Simulations/EMT/emt_solver_factory.py`

The old `sparse_solve.py` layer is intentionally not replaced because it is still
useful for global sparse solver discovery and non-EMT workflows. EMT needs an
additional layer with factorization handles and reuse semantics, which the old
functional wrappers do not provide.

## New EMT Sparse Layer

### 1. Interface

- `src/VeraGridEngine/Utils/NumericalMethods/external_sparse_solver_interface.py`

Defines three abstractions:

- `SparseLinearFactorizationHandle`
- `SparseLinearSolverBackend`
- `SparseLinearSolverBackendProvider`

This is the EMT-specific contract for:

- symbolic analysis reuse,
- numeric refactorization,
- solve into caller-owned buffers,
- backend statistics.

### 2. Internal Baseline Backend

- `src/VeraGridEngine/Utils/NumericalMethods/emt_sparse_superlu_backend.py`

This file adapts the current SuperLU logic into the new interface while
preserving:

- CSC storage,
- ordering reuse,
- numeric factorization reuse,
- solve without changing the EMT policy.

### 3. Plugin Loader

- `src/VeraGridEngine/Utils/NumericalMethods/emt_sparse_solver_loader.py`

This resolves external plugins from:

- the default VeraGrid plugins folder, or
- a user-provided directory override.

The expected folder structure is:

```text
<plugins root>/sparse_solvers/
  <plugin name>/
    plugin.json
    backend.py
```

### 4. Registry

- `src/VeraGridEngine/Utils/NumericalMethods/emt_sparse_solver_registry.py`

This chooses between:

- built-in providers, and
- external plugin providers,

with optional internal fallback.

## EMT Integration Surface

### 1. EMT Options

Added to `src/VeraGridEngine/Simulations/EMT/emt_options.py`:

- `sparse_solver`
- `external_sparse_solver_directory`
- `external_sparse_solver_plugin_name`
- `allow_internal_sparse_fallback`

### 2. EMT Solver Factory

Updated in `src/VeraGridEngine/Simulations/EMT/emt_solver_factory.py`:

- resolves the sparse backend provider from options,
- injects it into `StructuralCompiledSolver`.

### 3. StructuralCompiledSolver

Updated in `src/VeraGridEngine/Simulations/EMT/solvers/structural_compiled_solver.py`:

- accepts `sparse_solver_backend_provider`,
- routes sparse factorization through the generic interface,
- keeps EMT-level policy for invalidation and reuse in VeraGrid.

## What Is Intentionally Deferred

These are **not** part of the first integration phase:

- `StructuralVectorizedSolver` external sparse backend support,
- `JitSymbolicSolver` external sparse backend support,
- `JitAdSolver` external sparse backend support,
- event-local sparse updates,
- regional model-fidelity selection,
- GPU sparse backends.

They should be added only after the compiled path is stable and benchmarked.

## Phase 1 Exit Criteria

The phase is complete when all of the following are true:

1. `StructuralCompiledSolver` runs with the internal SuperLU provider through the new interface.
2. An external plugin can be loaded from a folder and selected through EMT options.
3. Numerical trajectories remain unchanged relative to the internal baseline.
4. Existing EMT benchmark and temporal-similarity suites remain green.
5. Benchmark artifacts can distinguish internal vs external sparse backend usage.

## Immediate Next Engineering Steps

1. Add explicit tests for:
   - plugin loading,
   - fallback behavior,
   - trajectory equivalence between internal and external provider paths.
2. Add one dummy external plugin that wraps SuperLU for integration testing.
3. Implement the first real external plugin path for:
   - `Pardiso`, or
   - `KLU`.
4. Benchmark A/B against internal SuperLU on the EMT corpus.
