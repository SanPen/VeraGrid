# Direct KLU vcpkg Sparse Solver Plugin

This plugin exposes `SparseSolver.KLU` through the EMT sparse backend interface
using the SuiteSparse KLU libraries installed externally through `vcpkg`.

## Expected external native runtime

By default the plugin looks for KLU under:

```text
%USERPROFILE%\.VeraGrid\external_native\vcpkg\installed\x64-windows
```

You can override the root with:

```text
VERAGRID_KLU_VCPKG_ROOT
```

The following DLLs are expected in `<root>\bin`:

- `klu.dll`
- `amd.dll`
- `colamd.dll`
- `btf.dll`
- `suitesparseconfig.dll`

## Installation

Install the plugin template into the VeraGrid plugin folder with:

```bash
python -m VeraGridEngine.IO.external_sparse_solvers.install_external_sparse_solver_plugin klu_vcpkg
```

The native SuiteSparse KLU libraries can then be installed with `vcpkg` into the
external runtime directory.
