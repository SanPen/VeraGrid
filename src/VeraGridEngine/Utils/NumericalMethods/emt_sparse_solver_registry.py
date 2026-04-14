# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict

from VeraGridEngine.Utils.NumericalMethods.emt_sparse_solver_loader import load_sparse_solver_backend_provider
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.enumerations import SparseSolver


def build_internal_sparse_solver_provider_map() -> Dict[SparseSolver, SparseLinearSolverBackendProvider]:
    """
    Build the map of built-in EMT sparse solver providers.

    :return: Built-in provider map.
    :rtype: Dict[SparseSolver, SparseLinearSolverBackendProvider]
    """
    provider_map: Dict[SparseSolver, SparseLinearSolverBackendProvider] = dict()
    provider_map[SparseSolver.SuperLU] = SuperLUSparseBackendProvider()
    return provider_map


def resolve_emt_sparse_solver_backend_provider(
        solver_type: SparseSolver,
        external_plugin_name: str,
        external_plugin_directory: str,
        allow_internal_fallback: bool,
) -> SparseLinearSolverBackendProvider:
    """
    Resolve the EMT sparse solver backend provider.

    :param solver_type: Requested sparse solver type.
    :type solver_type: SparseSolver
    :param external_plugin_name: External plugin name.
    :type external_plugin_name: str
    :param external_plugin_directory: External plugin directory override.
    :type external_plugin_directory: str
    :param allow_internal_fallback: Whether internal fallback is allowed.
    :type allow_internal_fallback: bool
    :return: Resolved backend provider.
    :rtype: SparseLinearSolverBackendProvider
    """
    internal_provider_map: Dict[SparseSolver, SparseLinearSolverBackendProvider] = build_internal_sparse_solver_provider_map()

    if len(external_plugin_name) > 0:
        plugin_provider: SparseLinearSolverBackendProvider

        try:
            plugin_provider = load_sparse_solver_backend_provider(
                plugin_name=external_plugin_name,
                plugin_directory_override=external_plugin_directory,
            )
        except (FileNotFoundError, RuntimeError, AttributeError, TypeError, ValueError):
            if allow_internal_fallback:
                if solver_type in internal_provider_map:
                    return internal_provider_map[solver_type]
                elif SparseSolver.SuperLU in internal_provider_map:
                    return internal_provider_map[SparseSolver.SuperLU]
                else:
                    raise RuntimeError(
                        f"External sparse solver plugin '{external_plugin_name}' could not be loaded and no internal fallback is available"
                    )
            else:
                raise

        if plugin_provider.get_solver_type() == solver_type:
            if plugin_provider.is_available():
                return plugin_provider
            elif allow_internal_fallback:
                if solver_type in internal_provider_map:
                    return internal_provider_map[solver_type]
                elif SparseSolver.SuperLU in internal_provider_map:
                    return internal_provider_map[SparseSolver.SuperLU]
                else:
                    raise RuntimeError(
                        f"External sparse solver plugin '{external_plugin_name}' is unavailable and no internal fallback exists for {solver_type}"
                    )
            else:
                raise RuntimeError(
                    f"External sparse solver plugin '{external_plugin_name}' is unavailable and fallback is disabled"
                )
        else:
            raise ValueError(
                f"External sparse solver plugin '{external_plugin_name}' exposes {plugin_provider.get_solver_type()} instead of requested {solver_type}"
            )
    else:
        pass

    if solver_type in internal_provider_map:
        return internal_provider_map[solver_type]
    elif allow_internal_fallback and SparseSolver.SuperLU in internal_provider_map:
        return internal_provider_map[SparseSolver.SuperLU]
    else:
        raise RuntimeError(f"No EMT sparse solver backend provider available for {solver_type}")
