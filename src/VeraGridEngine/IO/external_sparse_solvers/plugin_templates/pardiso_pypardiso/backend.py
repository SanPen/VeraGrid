# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict

import numpy as np
from scipy.sparse import csc_matrix, csr_matrix

from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import (
    SparseLinearFactorizationHandle,
    SparseLinearSolverBackend,
    SparseLinearSolverBackendProvider,
)
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import SparseSolver


def get_default_pardiso_runtime_directory() -> Path:
    """
    Return the default external runtime directory for ``pypardiso``.

    :return: Default external runtime directory.
    :rtype: Path
    """
    return Path.home() / ".VeraGrid" / "external_python_packages" / "pardiso_pypardiso"


def resolve_pardiso_runtime_directory() -> Path:
    """
    Resolve the external runtime directory for ``pypardiso``.

    :return: External runtime directory.
    :rtype: Path
    """
    override_path: str = os.environ.get("VERAGRID_PARDISO_PYPARDISO_RUNTIME_DIR", "")

    if len(override_path) > 0:
        return Path(override_path)
    else:
        return get_default_pardiso_runtime_directory()


def ensure_pardiso_runtime_on_sys_path() -> None:
    """
    Put the external ``pypardiso`` runtime directory on ``sys.path`` when present.

    :return: None.
    :rtype: None
    """
    runtime_directory: Path = resolve_pardiso_runtime_directory()
    runtime_directory_str: str = str(runtime_directory)

    if runtime_directory.exists():
        if runtime_directory_str in sys.path:
            pass
        else:
            sys.path.insert(0, runtime_directory_str)
    else:
        pass


def is_pardiso_runtime_available() -> bool:
    """
    Return whether ``pypardiso`` is available after injecting the external runtime directory.

    :return: ``True`` when ``pypardiso`` can be imported.
    :rtype: bool
    """
    ensure_pardiso_runtime_on_sys_path()
    spec = importlib.util.find_spec("pypardiso")

    if spec is None:
        return False
    else:
        return True


def get_pardiso_linear_solver():
    """
    Return the ``pypardiso`` sparse solve function.

    :return: ``pypardiso.spsolve``.
    :rtype: object
    """
    ensure_pardiso_runtime_on_sys_path()
    pypardiso_module = importlib.import_module("pypardiso")
    return pypardiso_module.spsolve


PARDISO_PYPARDISO_AVAILABLE: bool = is_pardiso_runtime_available()


class PardisoPyFactorizationHandle(SparseLinearFactorizationHandle):
    """
    Sparse factorization handle backed by the ``pypardiso`` solve interface.

    This handle stores the active sparse matrix and delegates each solve to the
    external library. It does not currently expose symbolic or numeric-only reuse,
    but it already provides a stable integration path for EMT benchmarking and
    future richer PARDISO wrappers.
    """

    __slots__ = ["_active_matrix", "_linear_solver", "_stats"]

    def __init__(self, active_matrix: csc_matrix) -> None:
        """
        Build the PARDISO factorization handle.

        :param active_matrix: Active sparse matrix in EMT solver order.
        :type active_matrix: csc_matrix
        :return: None.
        :rtype: None
        """
        self._active_matrix: csc_matrix = active_matrix
        self._linear_solver = get_pardiso_linear_solver()
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
        if PARDISO_PYPARDISO_AVAILABLE:
            raw_solution: Vec = np.asarray(self._linear_solver(self._active_matrix, rhs), dtype=np.float64)
            out_solution[:] = raw_solution
            self._stats["solve_calls"] += 1.0
        else:
            raise RuntimeError("pypardiso is not available in the current environment")

    def get_active_matrix(self) -> csc_matrix:
        """
        Return the matrix associated with the handle.

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


class PardisoPyBackend(SparseLinearSolverBackend):
    """
    EMT sparse backend backed by ``pypardiso``.
    """

    __slots__ = ["_base_matrix", "_base_data", "_stats"]

    def __init__(self, base_matrix: csc_matrix, base_data: Vec) -> None:
        """
        Build the PARDISO EMT sparse backend.

        :param base_matrix: Reusable EMT Jacobian CSC shell.
        :type base_matrix: csc_matrix
        :param base_data: Reusable EMT Jacobian numeric buffer.
        :type base_data: Vec
        :return: None.
        :rtype: None
        """
        self._base_matrix: csc_matrix = base_matrix
        self._base_data: Vec = base_data
        self._stats: Dict[str, float] = dict(
            numeric_factorizations=0.0,
            fallback_solves=0.0,
            plugin_available=1.0 if PARDISO_PYPARDISO_AVAILABLE else 0.0,
        )

    def get_name(self) -> str:
        """
        Return the backend name.

        :return: Backend name.
        :rtype: str
        """
        return "pardiso_pypardiso"

    def get_solver_type(self) -> SparseSolver:
        """
        Return the sparse solver type.

        :return: Sparse solver type.
        :rtype: SparseSolver
        """
        return SparseSolver.Pardiso

    def is_available(self) -> bool:
        """
        Return whether the backend is available.

        :return: ``True`` when ``pypardiso`` is installed.
        :rtype: bool
        """
        return PARDISO_PYPARDISO_AVAILABLE

    def requires_csc(self) -> bool:
        """
        Return whether the backend expects CSC matrices.

        :return: ``False`` because the wrapper accepts the native Pardiso sparse type.
        :rtype: bool
        """
        return False

    def factorize(self, matrix: csc_matrix, analysis_handle: object | None) -> SparseLinearFactorizationHandle:
        """
        Build the PARDISO factorization handle.

        :param matrix: Sparse matrix in EMT solver order.
        :type matrix: csc_matrix
        :param analysis_handle: Optional symbolic-analysis handle.
        :type analysis_handle: object | None
        :return: PARDISO factorization handle.
        :rtype: SparseLinearFactorizationHandle
        """
        _unused_analysis_handle: object | None = analysis_handle

        if PARDISO_PYPARDISO_AVAILABLE:
            active_matrix = csr_matrix(matrix.astype(np.float64, copy=False))
            self._stats["numeric_factorizations"] += 1.0
            return PardisoPyFactorizationHandle(active_matrix)
        else:
            raise RuntimeError("pypardiso is not available in the current environment")

    def get_backend_stats(self) -> Dict[str, float]:
        """
        Return backend-specific statistics.

        :return: Backend-specific statistics.
        :rtype: Dict[str, float]
        """
        return dict(self._stats)


class PardisoPyProvider(SparseLinearSolverBackendProvider):
    """
    Provider for the external ``pypardiso`` EMT sparse backend.
    """

    __slots__ = []

    def get_name(self) -> str:
        """
        Return the provider name.

        :return: Provider name.
        :rtype: str
        """
        return "pardiso_pypardiso"

    def get_solver_type(self) -> SparseSolver:
        """
        Return the sparse solver type.

        :return: Sparse solver type.
        :rtype: SparseSolver
        """
        return SparseSolver.Pardiso

    def is_available(self) -> bool:
        """
        Return whether the provider is available.

        :return: ``True`` when ``pypardiso`` is installed.
        :rtype: bool
        """
        return PARDISO_PYPARDISO_AVAILABLE

    def create_backend(self, base_matrix: csc_matrix, base_data: Vec) -> SparseLinearSolverBackend:
        """
        Create the PARDISO sparse backend.

        :param base_matrix: Reusable EMT Jacobian CSC shell.
        :type base_matrix: csc_matrix
        :param base_data: Reusable EMT Jacobian numeric buffer.
        :type base_data: Vec
        :return: Sparse solver backend.
        :rtype: SparseLinearSolverBackend
        """
        return PardisoPyBackend(base_matrix=base_matrix, base_data=base_data)
