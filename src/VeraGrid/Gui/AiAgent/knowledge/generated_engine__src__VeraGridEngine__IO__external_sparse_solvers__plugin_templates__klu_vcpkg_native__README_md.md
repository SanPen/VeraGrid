# VeraGridEngine Doc: Readme

- Original source path: `src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/klu_vcpkg_native/README.md`
- Knowledge kind: generated VeraGridEngine documentation

## Document Content

# Direct KLU Native vcpkg Plugin

This plugin loads KLU through a native Python extension that links directly
against the SuiteSparse KLU libraries installed externally with `vcpkg`.

## Goal

Avoid the fragile `cvxoptklu` path and provide a cleaner EMT-facing KLU backend.

## Expected external native runtime

By default the native plugin expects the SuiteSparse install root at:

```text
%USERPROFILE%\.VeraGrid\external_native\vcpkg\installed\x64-windows
```

## Build

Build the native plugin with:

```bat
build_native_plugin.cmd
```

Install the plugin template into the VeraGrid plugin folder with:

```bash
python -m VeraGridEngine.IO.external_sparse_solvers.install_external_sparse_solver_plugin klu_vcpkg_native
```

The built extension is written to:

```text
native_build\klu_native_backend*.pyd
```

## Runtime

At runtime the plugin loads the native extension and uses the vcpkg-installed
KLU DLLs.
