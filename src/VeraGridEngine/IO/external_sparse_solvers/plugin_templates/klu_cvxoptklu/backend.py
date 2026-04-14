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
from scipy.sparse import csc_matrix

from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import (
    SparseLinearFactorizationHandle,
    SparseLinearSolverBackend,
    SparseLinearSolverBackendProvider,
)
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import SparseSolver


def get_default_klu_runtime_directory() -> Path:
    """
    Return the default external runtime directory for ``cvxopt`` + ``cvxoptklu``.

    :return: Default external runtime directory.
    :rtype: Path
    """
    return Path.home() / ".VeraGrid" / "external_python_packages" / "klu_cvxoptklu"


def resolve_klu_runtime_directory() -> Path:
    """
    Resolve the external runtime directory for ``cvxopt`` and ``cvxoptklu``.

    :return: External runtime directory.
    :rtype: Path
    """
    override_path: str = os.environ.get("VERAGRID_KLU_CVXOPTKLU_RUNTIME_DIR", "")

    if len(override_path) > 0:
        return Path(override_path)
    else:
        return get_default_klu_runtime_directory()


def ensure_klu_runtime_on_sys_path() -> None:
    """
    Put the external KLU runtime directory on ``sys.path`` when present.

    :return: None.
    :rtype: None
    """
    runtime_directory: Path = resolve_klu_runtime_directory()
    runtime_directory_str: str = str(runtime_directory)

    if runtime_directory.exists():
        if runtime_directory_str in sys.path:
            pass
        else:
            sys.path.insert(0, runtime_directory_str)
    else:
        pass


def is_klu_runtime_available() -> bool:
    """
    Return whether ``cvxopt`` and ``cvxoptklu`` are available.

    :return: ``True`` when both packages can be imported.
    :rtype: bool
    """
    ensure_klu_runtime_on_sys_path()
    cvxopt_spec = importlib.util.find_spec("cvxopt")
    cvxoptklu_spec = importlib.util.find_spec("cvxoptklu")

    if cvxopt_spec is None or cvxoptklu_spec is None:
        return False
    else:
        return True


def get_klu_modules() -> tuple[object, object]:
    """
    Return the imported ``cvxopt`` and ``cvxoptklu`` modules.

    :return: Pair ``(cvxopt_module, cvxoptklu_module)``.
    :rtype: tuple[object, object]
    """
    ensure_klu_runtime_on_sys_path()
    cvxopt_module = importlib.import_module("cvxopt")
    cvxoptklu_module = importlib.import_module("cvxoptklu")
    return cvxopt_module, cvxoptklu_module


KLU_CVXOPTKLU_AVAILABLE: bool = is_klu_runtime_available()


class KluCvxoptFactorizationHandle(SparseLinearFactorizationHandle):
    """
    Sparse factorization handle backed by ``cvxoptklu``.

    This first version delegates each solve to the external KLU wrapper and does
    not yet expose symbolic or numeric-only reuse.
    """

    __slots__ = ["_active_matrix", "_cvxopt_module", "_klu_module", "_stats"]

    def __init__(self, active_matrix: csc_matrix) -> None:
        """
        Build the KLU factorization handle.

        :param active_matrix: Active sparse matrix in EMT solver order.
        :type active_matrix: csc_matrix
        :return: None.
        :rtype: None
        """
        self._active_matrix: csc_matrix = active_matrix
        self._cvxopt_module, self._klu_module = get_klu_modules()
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
        if KLU_CVXOPTKLU_AVAILABLE:
            matrix_coo = self._active_matrix.tocoo()
            cvxopt_matrix = self._cvxopt_module.spmatrix(
                matrix_coo.data,
                matrix_coo.row,
                matrix_coo.col,
                matrix_coo.shape,
                "d",
            )
            cvxopt_rhs = self._cvxopt_module.matrix(rhs)
            self._klu_module.klu.linsolve(cvxopt_matrix, cvxopt_rhs)
            out_solution[:] = np.array(cvxopt_rhs, dtype=np.float64)[:, 0]
            self._stats["solve_calls"] += 1.0
        else:
            raise RuntimeError("cvxopt and cvxoptklu are not available in the current environment")

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


class KluCvxoptBackend(SparseLinearSolverBackend):
    """
    EMT sparse backend backed by ``cvxoptklu``.
    """

    __slots__ = ["_base_matrix", "_base_data", "_stats"]

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
        self._base_matrix: csc_matrix = base_matrix
        self._base_data: Vec = base_data
        self._stats: Dict[str, float] = dict(
            numeric_factorizations=0.0,
            fallback_solves=0.0,
            plugin_available=1.0 if KLU_CVXOPTKLU_AVAILABLE else 0.0,
        )

    def get_name(self) -> str:
        """
        Return the backend name.

        :return: Backend name.
        :rtype: str
        """
        return "klu_cvxoptklu"

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

        :return: ``True`` when ``cvxopt`` and ``cvxoptklu`` are installed.
        :rtype: bool
        """
        return KLU_CVXOPTKLU_AVAILABLE

    def factorize(self, matrix: csc_matrix, analysis_handle: object | None) -> SparseLinearFactorizationHandle:
        """
        Build the KLU factorization handle.

        :param matrix: Sparse matrix in EMT solver order.
        :type matrix: csc_matrix
        :param analysis_handle: Optional symbolic-analysis handle.
        :type analysis_handle: object | None
        :return: KLU factorization handle.
        :rtype: SparseLinearFactorizationHandle
        """
        _unused_analysis_handle: object | None = analysis_handle

        if KLU_CVXOPTKLU_AVAILABLE:
            self._stats["numeric_factorizations"] += 1.0
            return KluCvxoptFactorizationHandle(matrix.astype(np.float64, copy=False).tocsc())
        else:
            raise RuntimeError("cvxopt and cvxoptklu are not available in the current environment")

    def get_backend_stats(self) -> Dict[str, float]:
        """
        Return backend-specific statistics.

        :return: Backend-specific statistics.
        :rtype: Dict[str, float]
        """
        return dict(self._stats)


class KluCvxoptProvider(SparseLinearSolverBackendProvider):
    """
    Provider for the external ``cvxoptklu`` EMT sparse backend.
    """

    __slots__ = []

    def get_name(self) -> str:
        """
        Return the provider name.

        :return: Provider name.
        :rtype: str
        """
        return "klu_cvxoptklu"

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

        :return: ``True`` when the runtime packages are installed.
        :rtype: bool
        """
        return KLU_CVXOPTKLU_AVAILABLE

    def create_backend(self, base_matrix: csc_matrix, base_data: Vec) -> SparseLinearSolverBackend:
        """
        Create the KLU sparse backend.

        :param base_matrix: Reusable EMT Jacobian CSC shell.
        :type base_matrix: csc_matrix
        :param base_data: Reusable EMT Jacobian numeric buffer.
        :type base_data: Vec
        :return: Sparse solver backend.
        :rtype: SparseLinearSolverBackend
        """
        return KluCvxoptBackend(base_matrix=base_matrix, base_data=base_data)
