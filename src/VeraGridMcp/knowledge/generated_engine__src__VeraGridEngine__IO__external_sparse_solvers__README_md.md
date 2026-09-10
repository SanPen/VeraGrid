# VeraGridEngine Doc: Readme

- Original source path: `src/VeraGridEngine/IO/external_sparse_solvers/README.md`
- Knowledge kind: generated VeraGridEngine documentation

## Document Content

# External Sparse Solvers

This folder centralizes the repository-side assets required to integrate sparse
linear solver backends that must remain outside the VeraGrid core tree for
licensing or deployment reasons.

## Why this folder lives under `IO`

The external sparse solver connection is fundamentally an integration and
deployment concern:

- it defines how VeraGrid discovers external plugin assets,
- how those assets are installed into user-space plugin folders,
- and how licensed or native dependencies remain outside the VeraGrid source tree.

That makes `IO/external_sparse_solvers` a more appropriate long-term location
than `trunk/dynamics_emt`, which should stay focused on EMT cases, demos,
benchmarks, and research artifacts.

## Contents

- `install_external_sparse_solver_plugin.py`
  - installs repository plugin templates into the VeraGrid user plugin folder.
- `install_external_sparse_solver_runtime.py`
  - installs Python runtime packages outside the VeraGrid repository.
- `plugin_templates/`
  - sparse solver plugin templates such as `pardiso_pypardiso`, `klu_cvxoptklu`,
    `klu_vcpkg`, and `klu_vcpkg_native`.
- `tools/`
  - auxiliary scripts used for local toolchain or native-runtime setup.
- `GETTING_STARTED.md`
  - step-by-step, from-scratch installation and validation guide.

## Default locations used by VeraGrid

### External plugin folder

```text
%USERPROFILE%\.VeraGrid\plugins\sparse_solvers
```

### External Python runtimes

```text
%USERPROFILE%\.VeraGrid\external_python_packages
```

### External native runtimes

```text
%USERPROFILE%\.VeraGrid\external_native
```

## Current recommendation

- Keep `SuperLU` as the default internal backend.
- Use `pardiso_pypardiso` as the first external high-performance backend.
- Treat `klu_vcpkg_native` as the recommended KLU path for Windows.
