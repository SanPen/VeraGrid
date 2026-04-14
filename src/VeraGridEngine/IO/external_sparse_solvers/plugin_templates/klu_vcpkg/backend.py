# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import ctypes as ct
import os
from pathlib import Path
from typing import Dict

import numpy as np
from scipy.sparse import csc_matrix

from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import (
    SparseLinearFactorizationHandle,
    SparseLinearSolverBackend,
    SparseLinearSolverBackendProvider,
)
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import SparseSolver


class KluCommon(ct.Structure):
    """
    ``klu_common`` structure for the 32-bit index / real KLU API.
    """

    _fields_ = [
        ("tol", ct.c_double),
        ("memgrow", ct.c_double),
        ("initmem_amd", ct.c_double),
        ("initmem", ct.c_double),
        ("maxwork", ct.c_double),
        ("btf", ct.c_int),
        ("ordering", ct.c_int),
        ("scale", ct.c_int),
        ("user_order", ct.c_void_p),
        ("user_data", ct.c_void_p),
        ("halt_if_singular", ct.c_int),
        ("status", ct.c_int),
        ("nrealloc", ct.c_int),
        ("structural_rank", ct.c_int32),
        ("numerical_rank", ct.c_int32),
        ("singular_col", ct.c_int32),
        ("noffdiag", ct.c_int32),
        ("flops", ct.c_double),
        ("rcond", ct.c_double),
        ("condest", ct.c_double),
        ("rgrowth", ct.c_double),
        ("work", ct.c_double),
        ("memusage", ct.c_size_t),
        ("mempeak", ct.c_size_t),
    ]


def get_default_klu_native_root() -> Path:
    """
    Return the default external native root containing vcpkg-installed KLU binaries.

    :return: Default native root.
    :rtype: Path
    """
    return Path.home() / ".VeraGrid" / "external_native" / "vcpkg" / "installed" / "x64-windows"


def resolve_klu_native_root() -> Path:
    """
    Resolve the native root containing KLU binaries.

    :return: Native root.
    :rtype: Path
    """
    override_path: str = os.environ.get("VERAGRID_KLU_VCPKG_ROOT", "")

    if len(override_path) > 0:
        return Path(override_path)
    else:
        return get_default_klu_native_root()


def get_klu_bin_directory() -> Path:
    """
    Return the directory containing KLU DLLs.

    :return: DLL directory.
    :rtype: Path
    """
    return resolve_klu_native_root() / "bin"


def get_klu_include_directory() -> Path:
    """
    Return the directory containing KLU headers.

    :return: Include directory.
    :rtype: Path
    """
    return resolve_klu_native_root() / "include" / "suitesparse"


def add_klu_dll_directory() -> None:
    """
    Add the KLU DLL directory to the process DLL search path.

    :return: None.
    :rtype: None
    """
    dll_directory: Path = get_klu_bin_directory()

    if dll_directory.exists():
        os.add_dll_directory(str(dll_directory))
    else:
        pass


def is_klu_vcpkg_runtime_available() -> bool:
    """
    Return whether the required KLU DLL set is available.

    :return: ``True`` when the runtime is available.
    :rtype: bool
    """
    dll_directory: Path = get_klu_bin_directory()
    required_files = [
        dll_directory / "klu.dll",
        dll_directory / "amd.dll",
        dll_directory / "colamd.dll",
        dll_directory / "btf.dll",
        dll_directory / "suitesparseconfig.dll",
    ]
    path_index: int = 0

    while path_index < len(required_files):
        if required_files[path_index].exists():
            pass
        else:
            return False
        path_index += 1

    return True


def load_klu_library() -> ct.WinDLL:
    """
    Load the native KLU DLL and bind the required function signatures.

    :return: Loaded KLU DLL wrapper.
    :rtype: ct.WinDLL
    """
    add_klu_dll_directory()
    dll_path: Path = get_klu_bin_directory() / "klu.dll"
    klu_dll: ct.WinDLL = ct.WinDLL(str(dll_path))

    klu_dll.klu_defaults.argtypes = [ct.POINTER(KluCommon)]
    klu_dll.klu_defaults.restype = ct.c_int
    klu_dll.klu_analyze.argtypes = [ct.c_int32, ct.POINTER(ct.c_int32), ct.POINTER(ct.c_int32), ct.POINTER(KluCommon)]
    klu_dll.klu_analyze.restype = ct.c_void_p
    klu_dll.klu_factor.argtypes = [
        ct.POINTER(ct.c_int32),
        ct.POINTER(ct.c_int32),
        ct.POINTER(ct.c_double),
        ct.c_void_p,
        ct.POINTER(KluCommon),
    ]
    klu_dll.klu_factor.restype = ct.c_void_p
    klu_dll.klu_refactor.argtypes = [
        ct.POINTER(ct.c_int32),
        ct.POINTER(ct.c_int32),
        ct.POINTER(ct.c_double),
        ct.c_void_p,
        ct.c_void_p,
        ct.POINTER(KluCommon),
    ]
    klu_dll.klu_refactor.restype = ct.c_int
    klu_dll.klu_solve.argtypes = [ct.c_void_p, ct.c_void_p, ct.c_int32, ct.c_int32, ct.POINTER(ct.c_double), ct.POINTER(KluCommon)]
    klu_dll.klu_solve.restype = ct.c_int
    klu_dll.klu_free_symbolic.argtypes = [ct.POINTER(ct.c_void_p), ct.POINTER(KluCommon)]
    klu_dll.klu_free_symbolic.restype = ct.c_int
    klu_dll.klu_free_numeric.argtypes = [ct.POINTER(ct.c_void_p), ct.POINTER(KluCommon)]
    klu_dll.klu_free_numeric.restype = ct.c_int
    return klu_dll


class KluVcpkgFactorizationHandle(SparseLinearFactorizationHandle):
    """
    Factorization handle backed by the native KLU DLL.
    """

    __slots__ = ["_klu_dll", "_active_matrix", "_symbolic_ptr", "_numeric_ptr", "_stats"]

    def __init__(
            self,
            klu_dll: ct.WinDLL,
            active_matrix: csc_matrix,
            symbolic_ptr: ct.c_void_p,
            numeric_ptr: ct.c_void_p,
    ) -> None:
        """
        Build the KLU factorization handle.

        :param klu_dll: Loaded KLU DLL wrapper.
        :type klu_dll: ct.WinDLL
        :param active_matrix: Active sparse matrix.
        :type active_matrix: csc_matrix
        :param symbolic_ptr: Opaque KLU symbolic pointer.
        :type symbolic_ptr: ct.c_void_p
        :param numeric_ptr: Opaque KLU numeric pointer.
        :type numeric_ptr: ct.c_void_p
        :return: None.
        :rtype: None
        """
        self._klu_dll: ct.WinDLL = klu_dll
        self._active_matrix: csc_matrix = active_matrix
        self._symbolic_ptr: ct.c_void_p = symbolic_ptr
        self._numeric_ptr: ct.c_void_p = numeric_ptr
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
        rhs_buffer: np.ndarray = np.array(rhs, dtype=np.float64, copy=True)
        common: KluCommon = KluCommon()
        success: int = self._klu_dll.klu_defaults(ct.byref(common))

        if success == 0:
            raise RuntimeError("KLU defaults initialization failed during solve")
        else:
            pass

        success = self._klu_dll.klu_solve(
            self._symbolic_ptr,
            self._numeric_ptr,
            int(self._active_matrix.shape[0]),
            1,
            rhs_buffer.ctypes.data_as(ct.POINTER(ct.c_double)),
            ct.byref(common),
        )

        if success == 0:
            raise RuntimeError(f"KLU solve failed with status {common.status}")
        else:
            out_solution[:] = rhs_buffer
            self._stats["solve_calls"] += 1.0

    def get_active_matrix(self) -> csc_matrix:
        """
        Return the matrix associated with the factorization handle.

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

    def __del__(self) -> None:
        """
        Release native KLU factorization objects.

        :return: None.
        :rtype: None
        """
        common: KluCommon = KluCommon()
        success: int = 0

        if hasattr(self, "_klu_dll"):
            success = self._klu_dll.klu_defaults(ct.byref(common))
        else:
            success = success

        if success == 0:
            return
        else:
            pass

        if hasattr(self, "_numeric_ptr") and self._numeric_ptr is not None:
            numeric_ptr_ptr = ct.c_void_p(self._numeric_ptr)
            self._klu_dll.klu_free_numeric(ct.byref(numeric_ptr_ptr), ct.byref(common))
        else:
            pass


class KluVcpkgBackend(SparseLinearSolverBackend):
    """
    EMT sparse backend backed by SuiteSparse KLU installed through vcpkg.
    """

    __slots__ = ["_klu_dll", "_base_matrix", "_base_data", "_symbolic_ptr", "_stats"]

    def __init__(self, base_matrix: csc_matrix, base_data: Vec) -> None:
        """
        Build the KLU EMT sparse backend.

        :param base_matrix: Reusable EMT Jacobian CSC shell.
        :type base_matrix: csc_matrix
        :param base_data: Reusable EMT Jacobian numeric buffer.
        :type base_data: Vec
        :return: None.
        :rtype: None
        """
        self._klu_dll: ct.WinDLL = load_klu_library()
        self._base_matrix: csc_matrix = base_matrix
        self._base_data: Vec = base_data
        self._symbolic_ptr: ct.c_void_p | None = None
        self._stats: Dict[str, float] = dict(
            numeric_factorizations=0.0,
            symbolic_analyses=0.0,
            numeric_refactorizations=0.0,
            plugin_available=1.0 if is_klu_vcpkg_runtime_available() else 0.0,
        )

    def get_name(self) -> str:
        """
        Return the backend name.

        :return: Backend name.
        :rtype: str
        """
        return "klu_vcpkg"

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

        :return: ``True`` when the SuiteSparse KLU DLLs are available.
        :rtype: bool
        """
        return is_klu_vcpkg_runtime_available()

    def supports_symbolic_analysis_reuse(self) -> bool:
        """
        Return whether symbolic analysis can be reused.

        :return: ``True``.
        :rtype: bool
        """
        return True

    def supports_numeric_refactorization(self) -> bool:
        """
        Return whether numeric-only refactorization is supported.

        :return: ``True``.
        :rtype: bool
        """
        return True

    def analyze(self, matrix: csc_matrix) -> ct.c_void_p | None:
        """
        Build the reusable KLU symbolic analysis object.

        :param matrix: Sparse matrix in EMT solver order.
        :type matrix: csc_matrix
        :return: Opaque symbolic-analysis pointer.
        :rtype: ct.c_void_p | None
        """
        common: KluCommon = KluCommon()
        success: int = self._klu_dll.klu_defaults(ct.byref(common))

        if success == 0:
            raise RuntimeError("KLU defaults initialization failed during analysis")
        else:
            pass

        symbolic_ptr = self._klu_dll.klu_analyze(
            int(matrix.shape[1]),
            matrix.indptr.astype(np.int32, copy=False).ctypes.data_as(ct.POINTER(ct.c_int32)),
            matrix.indices.astype(np.int32, copy=False).ctypes.data_as(ct.POINTER(ct.c_int32)),
            ct.byref(common),
        )

        if symbolic_ptr is None or symbolic_ptr == 0:
            raise RuntimeError(f"KLU symbolic analysis failed with status {common.status}")
        else:
            self._symbolic_ptr = ct.c_void_p(symbolic_ptr)
            self._stats["symbolic_analyses"] += 1.0
            return self._symbolic_ptr

    def factorize(self, matrix: csc_matrix, analysis_handle: object | None) -> SparseLinearFactorizationHandle:
        """
        Build the KLU numeric factorization.

        :param matrix: Sparse matrix in EMT solver order.
        :type matrix: csc_matrix
        :param analysis_handle: Optional symbolic-analysis handle.
        :type analysis_handle: object | None
        :return: KLU factorization handle.
        :rtype: SparseLinearFactorizationHandle
        """
        common: KluCommon = KluCommon()
        success: int = self._klu_dll.klu_defaults(ct.byref(common))

        if success == 0:
            raise RuntimeError("KLU defaults initialization failed during factorization")
        else:
            pass

        if analysis_handle is None:
            symbolic_ptr = self.analyze(matrix)
        else:
            symbolic_ptr = analysis_handle

        numeric_ptr = self._klu_dll.klu_factor(
            matrix.indptr.astype(np.int32, copy=False).ctypes.data_as(ct.POINTER(ct.c_int32)),
            matrix.indices.astype(np.int32, copy=False).ctypes.data_as(ct.POINTER(ct.c_int32)),
            matrix.data.astype(np.float64, copy=False).ctypes.data_as(ct.POINTER(ct.c_double)),
            symbolic_ptr,
            ct.byref(common),
        )

        if numeric_ptr is None or numeric_ptr == 0:
            raise RuntimeError(f"KLU numeric factorization failed with status {common.status}")
        else:
            self._stats["numeric_factorizations"] += 1.0
            return KluVcpkgFactorizationHandle(self._klu_dll, matrix, symbolic_ptr, ct.c_void_p(numeric_ptr))

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
        _unused_matrix: csc_matrix = matrix
        _unused_analysis_handle: object | None = analysis_handle
        _unused_previous_factorization: SparseLinearFactorizationHandle | None = previous_factorization
        return None

    def get_backend_stats(self) -> Dict[str, float]:
        """
        Return backend-specific statistics.

        :return: Backend-specific statistics.
        :rtype: Dict[str, float]
        """
        return dict(self._stats)


class KluVcpkgProvider(SparseLinearSolverBackendProvider):
    """
    Provider for the direct vcpkg-backed KLU EMT sparse backend.
    """

    __slots__ = []

    def get_name(self) -> str:
        """
        Return the provider name.

        :return: Provider name.
        :rtype: str
        """
        return "klu_vcpkg"

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

        :return: ``True`` when the KLU DLL runtime is available.
        :rtype: bool
        """
        return is_klu_vcpkg_runtime_available()

    def create_backend(self, base_matrix: csc_matrix, base_data: Vec) -> SparseLinearSolverBackend:
        """
        Create the direct KLU sparse backend.

        :param base_matrix: Reusable EMT Jacobian CSC shell.
        :type base_matrix: csc_matrix
        :param base_data: Reusable EMT Jacobian numeric buffer.
        :type base_data: Vec
        :return: Sparse solver backend.
        :rtype: SparseLinearSolverBackend
        """
        return KluVcpkgBackend(base_matrix=base_matrix, base_data=base_data)
