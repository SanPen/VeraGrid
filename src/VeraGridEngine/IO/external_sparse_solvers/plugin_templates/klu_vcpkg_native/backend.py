# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
from typing import Any, Dict

from scipy.sparse import csc_matrix

from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import (
    SparseLinearFactorizationHandle,
    SparseLinearSolverBackend,
    SparseLinearSolverBackendProvider,
)
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import SparseSolver


def get_plugin_directory() -> Path:
    """
    Return the directory containing this plugin backend.

    :return: Plugin directory.
    :rtype: Path
    """
    return Path(__file__).resolve().parent


def get_native_build_directory() -> Path:
    """
    Return the directory where the native KLU extension is expected.

    :return: Native build directory.
    :rtype: Path
    """
    return get_plugin_directory() / "native_build"


def get_vcpkg_root() -> Path:
    """
    Return the vcpkg install root used by the native KLU plugin.

    :return: vcpkg install root.
    :rtype: Path
    """
    override_root: str = os.environ.get("VERAGRID_KLU_VCPKG_ROOT", "")

    if len(override_root) > 0:
        return Path(override_root)
    else:
        return Path.home() / ".VeraGrid" / "external_native" / "vcpkg" / "installed" / "x64-windows"


def get_native_extension_path() -> Path | None:
    """
    Return the compiled native extension path when present.

    :return: Native extension path or ``None``.
    :rtype: Path | None
    """
    build_directory: Path = get_native_build_directory()
    suffixes = importlib.machinery.EXTENSION_SUFFIXES
    suffix_index: int = 0

    while suffix_index < len(suffixes):
        candidate_path: Path = build_directory / f"klu_native_backend{suffixes[suffix_index]}"

        if candidate_path.exists():
            return candidate_path
        else:
            pass

        suffix_index += 1

    return None


def load_native_backend_module() -> Any:
    """
    Load the compiled native KLU backend module.

    :return: Native backend module.
    :rtype: Any
    """
    extension_path: Path | None = get_native_extension_path()

    if extension_path is None:
        raise FileNotFoundError("Native KLU backend module was not built")
    else:
        pass

    dll_directory: Path = get_vcpkg_root() / "bin"

    if dll_directory.exists():
        os.add_dll_directory(str(dll_directory))
    else:
        pass

    spec = importlib.util.spec_from_file_location("klu_native_backend", extension_path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to create import spec for native KLU backend: {extension_path}")
    else:
        pass

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_native_klu_backend_available() -> bool:
    """
    Return whether the native KLU backend is buildable and loadable.

    :return: ``True`` when the native backend is available.
    :rtype: bool
    """
    extension_path: Path | None = get_native_extension_path()
    vcpkg_root: Path = get_vcpkg_root()
    required_paths = [
        vcpkg_root / "include" / "suitesparse" / "klu.h",
        vcpkg_root / "lib" / "klu.lib",
        vcpkg_root / "lib" / "amd.lib",
        vcpkg_root / "lib" / "colamd.lib",
        vcpkg_root / "lib" / "btf.lib",
        vcpkg_root / "lib" / "suitesparseconfig.lib",
    ]
    path_index: int = 0

    if extension_path is None:
        return False
    else:
        pass

    while path_index < len(required_paths):
        if required_paths[path_index].exists():
            pass
        else:
            return False

        path_index += 1

    return True


class NativeKluFactorizationHandle(SparseLinearFactorizationHandle):
    """
    EMT sparse factorization handle backed by the native KLU extension.
    """

    __slots__ = ["_native_handle", "_active_matrix", "_stats"]

    def __init__(self, native_handle: object, active_matrix: csc_matrix) -> None:
        """
        Build the native KLU factorization handle.

        :param native_handle: Native factorization handle.
        :type native_handle: object
        :param active_matrix: Active sparse matrix.
        :type active_matrix: csc_matrix
        :return: None.
        :rtype: None
        """
        self._native_handle = native_handle
        self._active_matrix = active_matrix
        self._stats: Dict[str, float] = dict(solve_calls=0.0)

    def solve_into(self, rhs: Vec, out_solution: Vec) -> None:
        """
        Solve the sparse system into the caller-owned output buffer.

        :param rhs: Right-hand side vector.
        :type rhs: Vec
        :param out_solution: Caller-owned output buffer.
        :type out_solution: Vec
        :return: None.
        :rtype: None
        """
        solution = self._native_handle.solve(rhs)
        out_solution[:] = solution
        self._stats["solve_calls"] += 1.0

    def get_active_matrix(self) -> csc_matrix:
        """
        Return the active sparse matrix.

        :return: Active sparse matrix.
        :rtype: csc_matrix
        """
        return self._active_matrix

    def get_stats(self) -> Dict[str, float]:
        """
        Return factorization-handle statistics.

        :return: Factorization-handle statistics.
        :rtype: Dict[str, float]
        """
        return dict(self._stats)


class KluVcpkgNativeBackend(SparseLinearSolverBackend):
    """
    EMT sparse backend backed by the native KLU extension module.
    """

    __slots__ = ["_native_module", "_base_matrix", "_base_data", "_symbolic_handle", "_stats"]

    def __init__(self, base_matrix: csc_matrix, base_data: Vec) -> None:
        """
        Build the native KLU EMT sparse backend.

        :param base_matrix: Reusable EMT Jacobian CSC shell.
        :type base_matrix: csc_matrix
        :param base_data: Reusable EMT Jacobian numeric buffer.
        :type base_data: Vec
        :return: None.
        :rtype: None
        """
        self._native_module = load_native_backend_module()
        self._base_matrix = base_matrix
        self._base_data = base_data
        self._symbolic_handle: object | None = None
        self._stats: Dict[str, float] = dict(
            symbolic_analyses=0.0,
            numeric_factorizations=0.0,
            numeric_refactorizations=0.0,
            plugin_available=1.0 if is_native_klu_backend_available() else 0.0,
        )

    def get_name(self) -> str:
        """
        Return the backend name.

        :return: Backend name.
        :rtype: str
        """
        return "klu_vcpkg_native"

    def get_solver_type(self) -> SparseSolver:
        """
        Return the sparse solver type.

        :return: Sparse solver type.
        :rtype: SparseSolver
        """
        return SparseSolver.KLU

    def is_available(self) -> bool:
        """
        Return whether the backend is available.

        :return: ``True`` when the native extension is available.
        :rtype: bool
        """
        return is_native_klu_backend_available()

    def supports_symbolic_analysis_reuse(self) -> bool:
        """
        Return whether symbolic analysis can be reused.

        :return: ``True``.
        :rtype: bool
        """
        return True

    def supports_numeric_refactorization(self) -> bool:
        """
        Return whether numeric refactorization is supported.

        :return: ``True``.
        :rtype: bool
        """
        return True

    def analyze(self, matrix: csc_matrix) -> object | None:
        """
        Build a reusable symbolic analysis handle.

        :param matrix: Sparse matrix in EMT solver order.
        :type matrix: csc_matrix
        :return: Symbolic-analysis handle.
        :rtype: object | None
        """
        self._symbolic_handle = self._native_module.analyze(matrix.indptr, matrix.indices, int(matrix.shape[1]))
        self._stats["symbolic_analyses"] += 1.0
        return self._symbolic_handle

    def factorize(self, matrix: csc_matrix, analysis_handle: object | None) -> SparseLinearFactorizationHandle:
        """
        Build a numeric KLU factorization handle.

        :param matrix: Sparse matrix in EMT solver order.
        :type matrix: csc_matrix
        :param analysis_handle: Optional symbolic-analysis handle.
        :type analysis_handle: object | None
        :return: Numeric KLU factorization handle.
        :rtype: SparseLinearFactorizationHandle
        """
        if analysis_handle is None:
            analysis_handle = self.analyze(matrix)
        else:
            pass

        native_handle = self._native_module.factorize(matrix.indptr, matrix.indices, matrix.data, analysis_handle)
        self._stats["numeric_factorizations"] += 1.0
        return NativeKluFactorizationHandle(native_handle, matrix)

    def refactor_numeric(
            self,
            matrix: csc_matrix,
            analysis_handle: object | None,
            previous_factorization: SparseLinearFactorizationHandle | None,
    ) -> SparseLinearFactorizationHandle | None:
        """
        Rebuild only the numeric factorization when supported.

        :param matrix: Sparse matrix in EMT solver order.
        :type matrix: csc_matrix
        :param analysis_handle: Optional symbolic-analysis handle.
        :type analysis_handle: object | None
        :param previous_factorization: Previous factorization handle.
        :type previous_factorization: SparseLinearFactorizationHandle | None
        :return: Updated factorization handle or ``None``.
        :rtype: SparseLinearFactorizationHandle | None
        """
        if isinstance(previous_factorization, NativeKluFactorizationHandle):
            pass
        else:
            return None

        if analysis_handle is None:
            return None
        else:
            pass

        native_handle = self._native_module.refactor(matrix.indptr, matrix.indices, matrix.data, analysis_handle, previous_factorization._native_handle)

        if native_handle is None:
            return None
        else:
            self._stats["numeric_refactorizations"] += 1.0
            return NativeKluFactorizationHandle(native_handle, matrix)

    def get_backend_stats(self) -> Dict[str, float]:
        """
        Return backend-specific statistics.

        :return: Backend-specific statistics.
        :rtype: Dict[str, float]
        """
        return dict(self._stats)


class KluVcpkgNativeProvider(SparseLinearSolverBackendProvider):
    """
    Provider for the native vcpkg-backed KLU EMT sparse backend.
    """

    __slots__ = []

    def get_name(self) -> str:
        """
        Return the provider name.

        :return: Provider name.
        :rtype: str
        """
        return "klu_vcpkg_native"

    def get_solver_type(self) -> SparseSolver:
        """
        Return the sparse solver type.

        :return: Sparse solver type.
        :rtype: SparseSolver
        """
        return SparseSolver.KLU

    def is_available(self) -> bool:
        """
        Return whether the provider is available.

        :return: ``True`` when the native extension is available.
        :rtype: bool
        """
        return is_native_klu_backend_available()

    def create_backend(self, base_matrix: csc_matrix, base_data: Vec) -> SparseLinearSolverBackend:
        """
        Create the native KLU sparse backend.

        :param base_matrix: Reusable EMT Jacobian CSC shell.
        :type base_matrix: csc_matrix
        :param base_data: Reusable EMT Jacobian numeric buffer.
        :type base_data: Vec
        :return: Sparse solver backend.
        :rtype: SparseLinearSolverBackend
        """
        return KluVcpkgNativeBackend(base_matrix=base_matrix, base_data=base_data)
