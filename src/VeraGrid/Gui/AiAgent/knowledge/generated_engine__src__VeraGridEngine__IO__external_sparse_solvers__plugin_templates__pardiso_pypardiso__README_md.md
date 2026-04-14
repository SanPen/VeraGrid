# VeraGridEngine Doc: Readme

- Original source path: `src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/pardiso_pypardiso/README.md`
- Knowledge kind: generated VeraGridEngine documentation

## Document Content

# PARDISO `pypardiso` Sparse Solver Plugin

This folder contains a VeraGrid EMT sparse-solver plugin template for the
`pypardiso` package.

## What it does

- exposes `SparseSolver.Pardiso` through the EMT sparse backend interface,
- keeps the proprietary or externally licensed solver outside the VeraGrid core,
- provides an immediate A/B integration path against the internal SuperLU backend.

## Current limitations

- this first plugin version wraps the `pypardiso.spsolve` interface,
- it does **not** yet expose symbolic-analysis reuse,
- it does **not** yet expose numeric-only refactorization.

So it is a valid first integration backend, but not yet the final high-performance
PARDISO integration target.

## Installation

From the VeraGrid repository root, install the plugin template into the default
VeraGrid plugin directory with:

```bash
python -m VeraGridEngine.IO.external_sparse_solvers.install_external_sparse_solver_plugin pardiso_pypardiso
```

You can override the destination root with:

```bash
python -m VeraGridEngine.IO.external_sparse_solvers.install_external_sparse_solver_plugin pardiso_pypardiso --destination-root "C:\path\to\plugins"
```

## Expected plugin layout after installation

```text
<plugins root>/sparse_solvers/
  pardiso_pypardiso/
    plugin.json
    backend.py
```
