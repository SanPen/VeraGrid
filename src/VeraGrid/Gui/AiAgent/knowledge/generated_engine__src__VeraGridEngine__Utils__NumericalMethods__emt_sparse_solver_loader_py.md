# VeraGridEngine Module: src/VeraGridEngine/Utils/NumericalMethods/emt_sparse_solver_loader.py

- Original source path: `src/VeraGridEngine/Utils/NumericalMethods/emt_sparse_solver_loader.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 5
- Representative imports: __future__, importlib.util, json, os, sys, pathlib, typing, VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface, VeraGridEngine.enumerations

## Class: SparseSolverPluginManifest

- Bases: none
- Summary: Parsed manifest of one external EMT sparse solver plugin.

### Methods

- `get_name(self)`
  Summary: Return the plugin name.
- `get_solver_type(self)`
  Summary: Return the sparse solver type.
- `get_module_name(self)`
  Summary: Return the module name.
- `get_class_name(self)`
  Summary: Return the provider class name.
- `get_version(self)`
  Summary: Return the plugin version string.

## Function: get_default_sparse_solver_plugins_directory()

Return the default directory containing EMT sparse solver plugins.

## Function: resolve_sparse_solver_plugins_directory(custom_directory)

Resolve the sparse-solver plugin directory.

## Function: read_sparse_solver_plugin_manifest(plugin_directory)

Read and validate one sparse-solver plugin manifest.

## Function: load_sparse_solver_backend_provider_from_plugin(plugin_directory, manifest)

Load a sparse-solver backend provider from one plugin directory.

## Function: load_sparse_solver_backend_provider(plugin_name, plugin_directory_override)

Load one sparse-solver backend provider by plugin name.
