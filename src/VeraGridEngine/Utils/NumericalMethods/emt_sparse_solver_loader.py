# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.enumerations import SparseSolver


class SparseSolverPluginManifest:
    """
    Parsed manifest of one external EMT sparse solver plugin.
    """

    __slots__ = ["_name", "_solver_type", "_module_name", "_class_name", "_version"]

    def __init__(self, name: str, solver_type: SparseSolver, module_name: str, class_name: str, version: str) -> None:
        """
        Build the plugin manifest object.

        :param name: Plugin name.
        :type name: str
        :param solver_type: Sparse solver type exposed by the plugin.
        :type solver_type: SparseSolver
        :param module_name: Python module file name without extension.
        :type module_name: str
        :param class_name: Provider class name.
        :type class_name: str
        :param version: Plugin version string.
        :type version: str
        :return: None.
        :rtype: None
        """
        self._name: str = name
        self._solver_type: SparseSolver = solver_type
        self._module_name: str = module_name
        self._class_name: str = class_name
        self._version: str = version

    def get_name(self) -> str:
        """
        Return the plugin name.

        :return: Plugin name.
        :rtype: str
        """
        return self._name

    def get_solver_type(self) -> SparseSolver:
        """
        Return the sparse solver type.

        :return: Sparse solver type.
        :rtype: SparseSolver
        """
        return self._solver_type

    def get_module_name(self) -> str:
        """
        Return the module name.

        :return: Module name.
        :rtype: str
        """
        return self._module_name

    def get_class_name(self) -> str:
        """
        Return the provider class name.

        :return: Provider class name.
        :rtype: str
        """
        return self._class_name

    def get_version(self) -> str:
        """
        Return the plugin version string.

        :return: Plugin version string.
        :rtype: str
        """
        return self._version


def get_default_sparse_solver_plugins_directory() -> Path:
    """
    Return the default directory containing EMT sparse solver plugins.

    :return: Default sparse-solver plugin directory.
    :rtype: Path
    """
    plugin_root: Path = Path.home() / ".VeraGrid" / "plugins" / "sparse_solvers"
    os.makedirs(plugin_root, exist_ok=True)
    return plugin_root


def resolve_sparse_solver_plugins_directory(custom_directory: str) -> Path:
    """
    Resolve the sparse-solver plugin directory.

    :param custom_directory: User-provided plugin directory.
    :type custom_directory: str
    :return: Resolved plugin directory.
    :rtype: Path
    """
    if len(custom_directory) > 0:
        return Path(custom_directory)
    else:
        return get_default_sparse_solver_plugins_directory()


def read_sparse_solver_plugin_manifest(plugin_directory: Path) -> SparseSolverPluginManifest:
    """
    Read and validate one sparse-solver plugin manifest.

    :param plugin_directory: Plugin directory.
    :type plugin_directory: Path
    :return: Parsed manifest.
    :rtype: SparseSolverPluginManifest
    """
    manifest_path: Path = plugin_directory / "plugin.json"

    if manifest_path.exists():
        pass
    else:
        raise FileNotFoundError(f"Sparse solver plugin manifest not found: {manifest_path}")

    raw_data_any: Any
    with open(manifest_path, "r", encoding="utf-8") as json_file:
        raw_data_any = json.load(json_file)

    if isinstance(raw_data_any, dict):
        raw_data: Dict[str, Any] = dict(raw_data_any)
    else:
        raise TypeError(f"Sparse solver plugin manifest must be a JSON object: {manifest_path}")

    if "name" in raw_data and "solver_type" in raw_data and "module" in raw_data and "class_name" in raw_data and "version" in raw_data:
        solver_type: SparseSolver = SparseSolver[str(raw_data["solver_type"])]
        return SparseSolverPluginManifest(
            name=str(raw_data["name"]),
            solver_type=solver_type,
            module_name=str(raw_data["module"]),
            class_name=str(raw_data["class_name"]),
            version=str(raw_data["version"]),
        )
    else:
        raise ValueError(f"Sparse solver plugin manifest is missing required fields: {manifest_path}")


def load_sparse_solver_backend_provider_from_plugin(
        plugin_directory: Path,
        manifest: SparseSolverPluginManifest,
) -> SparseLinearSolverBackendProvider:
    """
    Load a sparse-solver backend provider from one plugin directory.

    :param plugin_directory: Plugin directory.
    :type plugin_directory: Path
    :param manifest: Parsed plugin manifest.
    :type manifest: SparseSolverPluginManifest
    :return: Sparse solver backend provider.
    :rtype: SparseLinearSolverBackendProvider
    """
    module_path: Path = plugin_directory / f"{manifest.get_module_name()}.py"
    spec = importlib.util.spec_from_file_location(
        f"emt_sparse_plugin_{manifest.get_name()}_{manifest.get_version()}",
        module_path,
    )

    if spec is None:
        raise RuntimeError(f"Unable to create import spec for sparse solver plugin: {module_path}")
    else:
        pass

    if spec.loader is None:
        raise RuntimeError(f"Sparse solver plugin spec has no loader: {module_path}")
    else:
        pass

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    if manifest.get_class_name() in module.__dict__:
        provider_class: Any = module.__dict__[manifest.get_class_name()]
    else:
        raise AttributeError(
            f"Sparse solver plugin provider class '{manifest.get_class_name()}' not found in {module_path}"
        )

    provider_obj: Any = provider_class()

    if isinstance(provider_obj, SparseLinearSolverBackendProvider):
        return provider_obj
    else:
        raise TypeError(
            f"Sparse solver plugin provider '{manifest.get_class_name()}' does not implement SparseLinearSolverBackendProvider"
        )


def load_sparse_solver_backend_provider(
        plugin_name: str,
        plugin_directory_override: str,
) -> SparseLinearSolverBackendProvider:
    """
    Load one sparse-solver backend provider by plugin name.

    :param plugin_name: Plugin name.
    :type plugin_name: str
    :param plugin_directory_override: Optional plugin-directory override.
    :type plugin_directory_override: str
    :return: Sparse solver backend provider.
    :rtype: SparseLinearSolverBackendProvider
    """
    root_directory: Path = resolve_sparse_solver_plugins_directory(plugin_directory_override)
    plugin_directory: Path = root_directory / plugin_name
    manifest: SparseSolverPluginManifest = read_sparse_solver_plugin_manifest(plugin_directory)
    return load_sparse_solver_backend_provider_from_plugin(plugin_directory, manifest)
