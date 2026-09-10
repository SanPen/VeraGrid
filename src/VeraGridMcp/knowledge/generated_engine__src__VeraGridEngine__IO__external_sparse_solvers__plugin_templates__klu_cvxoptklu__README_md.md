# VeraGridEngine Doc: Readme

- Original source path: `src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/klu_cvxoptklu/README.md`
- Knowledge kind: generated VeraGridEngine documentation

## Document Content

# KLU `cvxoptklu` Sparse Solver Plugin

This folder contains a VeraGrid EMT sparse-solver plugin template for the
`cvxopt` + `cvxoptklu` runtime.

## What it does

- exposes `SparseSolver.KLU` through the EMT sparse backend interface,
- keeps the external packages outside the VeraGrid core,
- provides a benchmarkable path against the internal SuperLU backend.

## Current limitations

- this first plugin version delegates each solve through the external KLU wrapper,
- it does **not** yet expose symbolic-analysis reuse,
- it does **not** yet expose numeric-only refactorization.

So this is an integration-ready first version, not yet the final high-performance
KLU backend.

## Installation

Install the plugin template into the VeraGrid plugin directory with:

```bash
python -m VeraGridEngine.IO.external_sparse_solvers.install_external_sparse_solver_plugin klu_cvxoptklu
```

Install the external Python runtime into a separate directory with:

```bash
python -m VeraGridEngine.IO.external_sparse_solvers.install_external_sparse_solver_runtime klu_cvxoptklu cvxopt
```

Then install `cvxoptklu` manually into the same runtime directory if needed.

## Runtime lookup

The plugin searches its runtime under:

```text
%USERPROFILE%\.VeraGrid\external_python_packages\klu_cvxoptklu
```

You can override it with:

```text
VERAGRID_KLU_CVXOPTKLU_RUNTIME_DIR
```
