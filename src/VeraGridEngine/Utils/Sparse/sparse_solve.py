# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Selection of sparse linear solvers by SparseSolver.

Two faces share this single selection point:

- One-shot solves: get_linear_solver returns a stateless f(A, b). Power flow
  and OPF use it.
- Factorisation-reusing providers: resolve_sparse_lu_provider returns a
  provider whose backends analyse a pattern once and refactorise its values.
  EMT, RMS and small-signal use it. The selected provider is used when it is
  available; otherwise the reason is reported and the SciPy SuperLU provider is
  used. Native runtimes are imported lazily, by name only, the first time a
  selection needs them, and the result is cached for the process; installing a
  runtime takes effect after restarting VeraGrid. pygslv CLU is the exception: the
  GSLV activation module checks it when this module is imported.
"""

from __future__ import annotations

import warnings
from functools import lru_cache
from types import ModuleType

import numpy as np
from enum import Enum
from typing import Any, Tuple, Union
from threading import Lock
from weakref import finalize
from collections.abc import Callable
from scipy.sparse import csr_matrix, csc_matrix, spmatrix
from scipy.sparse.linalg import MatrixRankWarning, spsolve
from VeraGridEngine.basic_structures import CscMat, Logger, Vec, Mat, CxVec
from VeraGridEngine.enumerations import SparseSolver
from VeraGridEngine.Compilers.Gslv.activation import GSLV_AVAILABLE, GSLV_UNAVAILABLE_REASON, pg
from VeraGridEngine.Utils.Sparse import clu as clu_numba
from VeraGridEngine.Utils.optional_dependencies import optional_dependency_failure
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import (
    SparseLinearFactorizationHandle, SparseLinearSolverBackend, SparseLinearSolverBackendProvider,
)
from VeraGridEngine.Utils.Symbolic.diagnostic import sparse_lsqr_fallback
from VeraGridEngine.Utils.NumericalMethods.native_lu_runtime_backend import (
    NativeLuRuntimeBackendProvider,
    load_native_lu_runtime,
)


# list of available linear algebra frameworks
available_sparse_solvers = list()


# KLU availability comes from its factorisation-reusing provider (get_available_sparse_solvers).
# Optional native solvers can fail with ABI errors; register Pardiso only after the API loads successfully.
# SciPy remains available when Pardiso cannot be imported.
try:
    from scipy.sparse.linalg import spsolve as scipy_spsolve, spilu, gmres, spsolve_triangular
    available_sparse_solvers.append(SparseSolver.UMFPACK)  # default linsolve solver
    available_sparse_solvers.append(SparseSolver.ILU)
    available_sparse_solvers.append(SparseSolver.SuperLU)
    available_sparse_solvers.append(SparseSolver.GMRES)
    available_sparse_solvers.append(SparseSolver.UMFPACKTriangular)
except ImportError:
    pass
    # print(SparseSolver.BLAS_LAPACK.value + ' failed')


try:
    from pypardiso import PyPardisoSolver, spsolve as pardiso_spsolve
    from pypardiso.pardiso_wrapper import PyPardisoError

    available_sparse_solvers.append(SparseSolver.Pardiso)  # pypardiso
except (ImportError, AttributeError, OSError, RuntimeError, ValueError, TypeError) as error:
    optional_dependency_failure("pypardiso", error)


# Activation owns pygslv version and license checks; older builds may lack CLU.
if GSLV_AVAILABLE:
    try:
        pg.clu.Factorizer
    except AttributeError as error:
        optional_dependency_failure("pygslv.clu", error)
    else:
        available_sparse_solvers.append(SparseSolver.CLU)
else:
    pass

# The Numba CLU port has no native or licensed dependency.
available_sparse_solvers.append(SparseSolver.CLU_Numba)


preferred_type = SparseSolver.SuperLU

if preferred_type not in available_sparse_solvers:
    if len(available_sparse_solvers) > 0:
        preferred_type = available_sparse_solvers[0]
        # print('Falling back to', preferred_type)
    else:
        raise Exception('No linear algebra solver!!!! VeraGrid cannot work without one.')
# print('Using', preferred_type)


def get_available_sparse_solvers() -> list[SparseSolver]:
    """
    Return a copy of the sparse solvers that are available in the current runtime.

    :return: List of available sparse solver enum values (KLU first when its provider is available).
    """
    solver_types: list[SparseSolver] = list()
    klu_provider: SparseLinearSolverBackendProvider | None
    klu_reason: str
    klu_provider, klu_reason = get_sparse_lu_provider_status(SparseSolver.KLU)
    if klu_provider is not None:
        solver_types.append(SparseSolver.KLU)
    else:
        pass
    for solver_type in available_sparse_solvers:
        solver_types.append(solver_type)
    return solver_types


def get_default_sparse_lu_solver() -> SparseSolver:
    """
    Return the default factorisation-reusing sparse LU solver: KLU when its native provider is
    available, otherwise SciPy SuperLU, so the default never triggers an unavailability warning.

    :return: Default sparse LU solver.
    """
    klu_provider: SparseLinearSolverBackendProvider | None
    klu_reason: str
    klu_provider, klu_reason = get_sparse_lu_provider_status(SparseSolver.KLU)
    if klu_provider is not None:
        result: SparseSolver = SparseSolver.KLU
    else:
        result = SparseSolver.SuperLU
    return result


def get_sparse_type(solver_type: SparseSolver = preferred_type):
    """
    GEt sparse matrix type matching the selected sparse linear systems solver
    :param solver_type:
    :return: sparse matrix type
    """
    if solver_type in [SparseSolver.Pardiso, SparseSolver.GMRES]:
        return csr_matrix

    elif solver_type in [SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba, SparseSolver.SuperLU,
                         SparseSolver.ILU, SparseSolver.UMFPACK]:
        return csc_matrix

    else:
        raise Exception('Unknown solver' + str(solver_type))


class CluLinearSolver:
    """Preserve the historical CLU callable through the single common lifecycle.

    A whole-call lock serializes the common mutable phase state, including all RHS
    columns. Complex input retains the existing SuperLU compatibility path.
    """

    __slots__ = ("_solver", "_lock")

    def __init__(self, provider: SparseLinearSolverBackendProvider | None = None) -> None:
        """Create one resident CLU stream without a parallel native or CSC cache.

        :param provider: CLU flavour (licensed native or Numba); the licensed native CLU when None.
        :return: None.
        """
        if provider is None:
            provider = CluSparseBackendProvider()
        else:
            pass
        self._solver: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        self._lock: Lock = Lock()

    @property
    def _factorizer(self) -> SparseLinearSolverBackend | None:
        """Expose the current retained CLU analysis owner for legacy diagnostics.

        :return: Current phase backend, or None before the first factorization.
        """
        manager: SparseFactorizationManager | None = self._solver._factorization_manager
        if manager is None:
            return None
        else:
            return manager._backend

    def solve(self, A: CscMat, b: Union[Vec, Mat]) -> Union[Vec, Mat]:
        """Retain vector/block shape, zero canonicalization and legacy error behavior.

        :param A: Square CSC system matrix; caller storage is never modified.
        :param b: Vector or matrix of real/complex right-hand sides.
        :return: Newly owned solution with the RHS shape.
        :raises ValueError: When dimensions do not match.
        :raises numpy.linalg.LinAlgError: When real CLU factorization/solving fails.
        """
        if np.iscomplexobj(A.data) or np.iscomplexobj(b):
            return get_linear_solver(SparseSolver.SuperLU)(A.astype(np.complex128, copy=False), b)
        else:
            rhs: np.ndarray = np.asarray(b, dtype=np.float64)
            if A.shape[0] != A.shape[1] or rhs.ndim not in (1, 2) or rhs.shape[0] != A.shape[0]:
                raise ValueError("CLU requires a square matrix and matching RHS dimensions")
            else:
                matrix: CscMat = A.astype(np.float64, copy=False)
                if not matrix.has_canonical_format or np.any(matrix.data == 0.0):
                    # Preserve legacy canonicalization only at this callable boundary.
                    matrix = matrix.copy()
                    matrix.sum_duplicates()
                    matrix.eliminate_zeros()
                    matrix.sort_indices()
                else:
                    pass
                rhs_columns: Mat = rhs.reshape((A.shape[0], 1)) if rhs.ndim == 1 else rhs
                solution: Mat = np.empty(rhs_columns.shape, dtype=np.float64, order="F")
                with self._lock:
                    try:
                        if rhs_columns.shape[1] == 0:
                            # The legacy block API validated factors even without
                            # columns. Reuse the vector lifecycle with a zero RHS
                            # so singular input still fails before returning empty.
                            self._solver.solve(matrix, np.zeros(A.shape[0], dtype=np.float64))
                        else:
                            column: int
                            for column in range(rhs_columns.shape[1]):
                                solution[:, column] = self._solver.solve(matrix, rhs_columns[:, column])
                    except RuntimeError as error:
                        raise np.linalg.LinAlgError(str(error)) from error
                    else:
                        pass
                return solution.reshape(rhs.shape)


def clu_linsolver(A: CscMat, b: Union[Vec, Mat]) -> Union[Vec, Mat]:
    """Solve once with serial CLU, or SuperLU when it is unavailable; use get_linear_solver(CLU) for retained factors.

    :param A: Square CSC system matrix.
    :param b: Right hand side vector or matrix.
    :return: Solution with the RHS shape.
    """
    return get_linear_solver(SparseSolver.CLU)(A, b)


def ilu_linsolver(A: CscMat, b: Union[Vec, Mat]) -> Union[Vec, Mat]:
    """
    ILU wrapper function for linear system solve A x = b
    :param A: System matrix
    :param b: right hand side
    :return: solution
    """
    return spilu(A).solve(b)


def gmres_linsolve(A: CscMat, b: Union[Vec, Mat]) -> Union[Vec, Mat]:
    """

    :param A:
    :param b:
    :return:
    """
    x, info = gmres(A, b)
    return x


class SparseProviderLinearSolver:
    """Bind one provider with separate legacy one-shot and phase-resident entry points."""

    __slots__ = ("_provider", "_factorization_manager")

    def __init__(self, provider: SparseLinearSolverBackendProvider) -> None:
        """Retain selection without creating native state until the first resident solve.

        :param provider: Already resolved available sparse LU provider.
        :return: None.
        """
        self._provider: SparseLinearSolverBackendProvider = provider
        self._factorization_manager: SparseFactorizationManager | None = None

    def __call__(self, A: spmatrix, b: Vec) -> Vec:
        """Keep unrelated get_linear_solver consumers on their historical one-shot path.

        :param A: Square sparse matrix.
        :param b: Right-hand-side vector.
        :return: Newly allocated one-shot solution.
        """
        return self._provider.solve_once(A, b)

    def solve(self, matrix: spmatrix, rhs: Vec) -> Vec:
        """Solve one real phase stream through the common validity owner.

        :param matrix: Current square sparse coefficients; input remains untouched.
        :param rhs: Current real vector matching matrix rows.
        :return: Owned solution so later solves cannot overwrite accepted corrections.
        :raises ValueError: When input violates the real square-vector contract.
        :raises RuntimeError: When current coefficients cannot be solved.
        """
        if (matrix.shape[0] != matrix.shape[1] or rhs.ndim != 1
                or rhs.shape[0] != matrix.shape[0] or np.iscomplexobj(matrix.data) or np.iscomplexobj(rhs)):
            raise ValueError("Resident sparse LU requires a real square system and matching vector")
        else:
            system: CscMat = csc_matrix(matrix, dtype=np.float64, copy=False)
            if not system.has_canonical_format:
                system = system.copy()
                system.sum_duplicates()
                system.sort_indices()
            else:
                pass
            if self._factorization_manager is None:
                # Own the snapshot: caller edits must not silently mutate resident coefficients.
                owned_matrix: CscMat = system.copy()
                self._factorization_manager = SparseFactorizationManager(
                    owned_matrix, owned_matrix.data, self._provider)
                current: bool = False
            else:
                current = self._factorization_manager.update_matrix(system)
            if not current:
                self._factorization_manager.factorize()
            else:
                pass
            right_hand_side: Vec = np.ascontiguousarray(rhs, dtype=np.float64)
            solution: Vec = self._factorization_manager.solve(right_hand_side)
            return solution.copy()

    def solve_retained(self, rhs: Vec) -> Vec:
        """Apply factors explicitly retained by the caller's Newton policy.

        This entry point never infers eligibility from a mutable matrix buffer.
        The numerical integrator must invalidate the phase whenever its retained
        Jacobian ceases to be suitable for the current correction.

        :param rhs: Real right-hand side in the resident matrix's row order.
        :return: Owned correction, independent of the phase's reusable buffer.
        :raises ValueError: When the right-hand side violates the vector contract.
        :raises RuntimeError: When factors are missing or the solve is non-finite.
        """
        manager: SparseFactorizationManager | None = self._factorization_manager
        if manager is None or not manager.has_factorization():
            raise RuntimeError("Retained sparse solve requires eligible factors")
        else:
            matrix: CscMat = manager.get_active_matrix()
            if rhs.ndim != 1 or rhs.shape[0] != matrix.shape[0] or np.iscomplexobj(rhs):
                raise ValueError("Retained sparse LU requires a matching real vector")
            else:
                # Non-finite input cannot leave an apparently eligible phase.
                if not np.all(np.isfinite(rhs)):
                    manager.invalidate()
                    raise RuntimeError("Retained sparse solve received non-finite RHS")
                else:
                    right_hand_side: Vec = np.ascontiguousarray(rhs, dtype=np.float64)
                    solution: Vec = manager.solve(right_hand_side)
                    if np.all(np.isfinite(solution)):
                        return solution.copy()
                    else:
                        # The manager already invalidated its non-finite output.
                        raise RuntimeError("Retained sparse solve returned non-finite values")

    def invalidate(self) -> None:
        """Force fresh factors on the next request without sharing state between phases.

        :return: None.
        """
        if self._factorization_manager is not None:
            self._factorization_manager.invalidate()
        else:
            pass

    def get_stats(self) -> dict[str, float]:
        """Expose successful native work and attempts for qualification.

        :return: Current phase counters, empty before the first resident solve.
        """
        if self._factorization_manager is None:
            return dict()
        else:
            return self._factorization_manager.get_stats()


def get_linear_solver(solver_type: SparseSolver = preferred_type) -> Callable[[CscMat, Union[Vec, Mat]], Union[Vec, Mat]]:
    """
    Provide the chosen linear solver_type function pointer to
    solver_type linear systems of the type A x = b, with x = f(A,b)
    SuperLU and KLU are derived from their factorisation-reusing providers.
    Retain the returned CLU callable to reuse its analysis and numeric factors;
    CLU falls back to SuperLU when pygslv CLU is unavailable.
    :param solver_type: SparseSolver option
    :return: function pointer f(A, b)
    """
    if solver_type == SparseSolver.SuperLU or solver_type == SparseSolver.KLU:
        provider: SparseLinearSolverBackendProvider | None
        reason: str
        provider, reason = get_sparse_lu_provider_status(solver_type)
        if provider is not None:
            return SparseProviderLinearSolver(provider)
        else:
            return scipy_spsolve

    elif solver_type == SparseSolver.CLU:
        if solver_type in available_sparse_solvers:
            return CluLinearSolver().solve
        else:
            return get_linear_solver(SparseSolver.SuperLU)

    elif solver_type == SparseSolver.CLU_Numba:
        # Same callable contract as CLU: vector/block RHS, complex input through SuperLU.
        return CluLinearSolver(CluNumbaSparseBackendProvider()).solve

    elif solver_type in available_sparse_solvers:

        if solver_type == SparseSolver.UMFPACK:
            return scipy_spsolve

        elif solver_type == SparseSolver.UMFPACKTriangular:
            return spsolve_triangular

        elif solver_type == SparseSolver.Pardiso:
            return pardiso_spsolve

        elif solver_type == SparseSolver.ILU:
            return ilu_linsolver

        elif solver_type == SparseSolver.GMRES:
            return gmres_linsolve

        else:
            raise Exception('Unrecognized LU solver')

    else:
        return scipy_spsolve


def report_sparse_solver_warning(message: str, logger: Logger | None) -> None:
    """
    Report a sparse solver selection warning.

    :param message: Warning text.
    :param logger: Logger receiving the warning; a RuntimeWarning attributed to the caller of the reporting function is emitted when None.
    :return: None.
    """
    if logger is None:
        warnings.warn(message, RuntimeWarning, stacklevel=3)
    else:
        logger.add_warning(message)


@lru_cache(maxsize=1)
def _load_klu_provider() -> NativeLuRuntimeBackendProvider:
    """
    Load the native KLU runtime once per process.

    :return: KLU provider, available or carrying its unavailability reason.
    """
    runtime: ModuleType | None
    reason: str
    runtime, reason = load_native_lu_runtime("cvxoptklu._klu_native", "cvxoptklu", "veragrid-cvxoptklu")
    return NativeLuRuntimeBackendProvider("native_klu", SparseSolver.KLU, runtime, reason)


def get_sparse_lu_provider_status(solver_type: SparseSolver) -> Tuple[SparseLinearSolverBackendProvider | None, str]:
    """
    Return the factorisation-reusing provider registered for a sparse solver, without any fallback.

    :param solver_type: Requested sparse solver.
    :return: The available provider and an empty reason, or None and the reason it cannot be used.
    """
    if solver_type == SparseSolver.SuperLU:
        result: Tuple[SparseLinearSolverBackendProvider | None, str] = (SuperLUSparseBackendProvider(), "")
    elif solver_type == SparseSolver.KLU:
        native: NativeLuRuntimeBackendProvider = _load_klu_provider()
        if native.is_available():
            result = (native, "")
        else:
            result = (None, native.get_unavailable_reason())
    elif solver_type == SparseSolver.CLU:
        clu_provider: CluSparseBackendProvider = CluSparseBackendProvider()
        if clu_provider.is_available():
            result = (clu_provider, "")
        else:
            result = (None, clu_provider.get_unavailable_reason())
    elif solver_type == SparseSolver.CLU_Numba:
        result = (CluNumbaSparseBackendProvider(), "")
    elif solver_type == SparseSolver.Pardiso:
        pardiso_provider: PardisoSparseBackendProvider = PardisoSparseBackendProvider()
        if pardiso_provider.is_available():
            result = (pardiso_provider, "")
        else:
            result = (None, pardiso_provider.get_unavailable_reason())
    elif solver_type == SparseSolver.UMFPACK:
        result = (None, "the SciPy UMFPACK alias has no registered reusable UMFPACK provider")
    else:
        result = (None, "no factorisation-reusing provider is registered for " + solver_type.value)
    return result


def resolve_sparse_lu_provider(solver_type: SparseSolver, logger: Logger | None) -> SparseLinearSolverBackendProvider:
    """
    Resolve the selected factorisation-reusing provider, falling back to SciPy SuperLU with a reported reason.

    :param solver_type: Requested sparse solver.
    :param logger: Logger receiving the fallback warning; a RuntimeWarning is emitted when None.
    :return: The selected provider when available, otherwise the SciPy SuperLU provider.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is not None:
        result: SparseLinearSolverBackendProvider = provider
    else:
        report_sparse_solver_warning(f"Sparse LU solver {solver_type.value} is unavailable: {reason}. Using SciPy SuperLU.", logger)
        result = SuperLUSparseBackendProvider()
    return result


def solve_sparse_system_once(matrix: spmatrix, rhs: Vec,
                             provider: SparseLinearSolverBackendProvider | None,
                             linear_solver: SparseProviderLinearSolver | None = None) -> Vec:
    """Solve through an optional resident phase while preserving one-shot callers.

    None/SuperLU without a resident session retains the exact scipy.spsolve path,
    including its in-place canonicalization. Numerical RuntimeError retains the
    existing MatrixRankWarning/NaN admission used by Newton recovery policies.

    :param matrix: Current square sparse coefficients.
    :param rhs: Right-hand-side vector.
    :param provider: Selected provider, or None for the historical SuperLU path.
    :param linear_solver: Phase-local resident session, or None for one-shot solving.
    :return: Newly owned correction, or NaNs after numerical factorization failure.
    """
    if linear_solver is None and (provider is None or provider.get_solver_type() == SparseSolver.SuperLU):
        solution: Vec = scipy_spsolve(matrix, rhs)
    else:
        try:
            if linear_solver is not None:
                solution = linear_solver.solve(matrix, rhs)
            elif provider is not None:
                solution = provider.solve_once(matrix, rhs)
            else:
                solution = scipy_spsolve(matrix, rhs)
        except RuntimeError:
            warnings.warn("Matrix is exactly singular", MatrixRankWarning, stacklevel=2)
            solution = np.full(int(matrix.shape[0]), np.nan, dtype=np.float64)
        else:
            pass
    return solution



def safe_spsolve(system_matrix: csc_matrix,
                 rhs: CxVec,
                 logger: Logger | None,
                 context: str,
                 fault_impedance: complex) -> CxVec | None:
    """
    Solve a sparse linear system and report singular/non-finite states as errors.

    :param system_matrix: Sparse system matrix.
    :param rhs: Right-hand side vector.
    :param logger: Logger where the numerical error must be reported.
    :param context: Text identifying the short-circuit solve stage.
    :param fault_impedance: Fault impedance used for the case.
    :return: Solution vector, or ``None`` when the solve is unusable.
    """
    solution: CxVec | None

    with warnings.catch_warnings():
        warnings.filterwarnings("error", category=MatrixRankWarning)

        try:
            solution = np.asarray(spsolve(system_matrix, rhs), dtype=complex)
        except MatrixRankWarning:
            solution = None
        except RuntimeError:
            solution = None
        except ValueError:
            solution = None

    if solution is None:
        if logger is not None:
            logger.add_error(msg="Short-circuit matrix is singular",
                             device=context,
                             value=fault_impedance,
                             expected_value="Non-singular matrix and valid fault impedance")
        else:
            pass
        return None
    else:
        if np.all(np.isfinite(solution)):
            return solution
        else:
            if logger is not None:
                logger.add_error(msg="Short-circuit solve produced non-finite values",
                                 device=context,
                                 value=fault_impedance,
                                 expected_value="Finite solution")
            else:
                pass
            return None


class SparseFactorizationManager:
    """Own one phase's CSC buffers and the validity of its resident LU factors."""

    __slots__ = ("_base_matrix", "_provider", "_backend", "_analysis_handle", "_cached_handle",
                 "_solution_buffer", "_stats", "_retired_backend_stats")

    def __init__(self, base_matrix: CscMat, base_data: Vec,
                 backend_provider: SparseLinearSolverBackendProvider | None = None) -> None:
        """Bind a stable CSC shell without copying structural solver buffers.

        :param base_matrix: Phase-owned canonical real square CSC matrix.
        :param base_data: Live values belonging to that same matrix.
        :param backend_provider: Selected provider, or the existing SuperLU default.
        :return: None.
        """
        self._base_matrix: CscMat = base_matrix
        self._provider: SparseLinearSolverBackendProvider = (
            SuperLUSparseBackendProvider() if backend_provider is None else backend_provider)
        self._backend: SparseLinearSolverBackend = self._provider.create_backend(base_matrix, base_data)
        self._analysis_handle: object | None = None
        self._cached_handle: SparseLinearFactorizationHandle | None = None
        self._solution_buffer: Vec = np.zeros(int(base_matrix.shape[1]), dtype=np.float64)
        # Count successful work separately from attempts, including failed native calls.
        self._stats: dict[str, float] = dict(numeric_factorizations=0.0, numeric_refactorizations=0.0,
            factorization_attempts=0.0, refactor_attempts=0.0, refactor_failures=0.0,
            invalidations=0.0, solve_calls=0.0, solve_attempts=0.0,
            fallback_solves=0.0, pattern_rebuilds=0.0)
        self._retired_backend_stats: dict[str, float] = dict()
        if self._backend.supports_symbolic_analysis_reuse():
            self._analysis_handle = self._backend.analyze(base_matrix)
        else:
            pass

    def invalidate(self) -> None:
        """Discard numeric eligibility; the next requested factors must be fresh.

        :return: None; symbolic state and stable buffers remain owned by this phase.
        """
        self._cached_handle = None
        self._stats["invalidations"] += 1.0

    def has_factorization(self) -> bool:
        """Inspect whether this phase currently owns an eligible numeric handle.

        :return: True only after a successful factorization or refactorization.
        """
        return self._cached_handle is not None

    def update_matrix(self, matrix: CscMat) -> bool:
        """Update a variable-pattern phase using content rather than object identity.

        :param matrix: Current canonical CSC coefficients; caller storage is borrowed.
        :return: True when existing numeric factors already match these coefficients.
        """
        same_pattern: bool = (self._base_matrix.shape == matrix.shape
            and np.array_equal(self._base_matrix.indptr, matrix.indptr)
            and np.array_equal(self._base_matrix.indices, matrix.indices))
        if same_pattern:
            same_values: bool = np.array_equal(self._base_matrix.data, matrix.data)
            if same_values:
                return self.has_factorization()
            else:
                # The old handle remains available only for the immediate refactor attempt.
                np.copyto(self._base_matrix.data, matrix.data)
                self.factorize()
                return True
        else:
            # Reject old numeric eligibility before any fallible preparation.
            # Commit a new pattern only after all its owners are ready; a failed
            # backend/analysis must never pair new coefficients with an old backend.
            self.invalidate()
            updated_matrix: CscMat = matrix.copy()
            updated_backend: SparseLinearSolverBackend = self._provider.create_backend(
                updated_matrix, updated_matrix.data)
            updated_analysis: object | None
            if updated_backend.supports_symbolic_analysis_reuse():
                updated_analysis = updated_backend.analyze(updated_matrix)
            else:
                updated_analysis = None
            updated_solution: Vec = np.zeros(int(matrix.shape[1]), dtype=np.float64)
            key: str
            value: float
            for key, value in self._backend.get_backend_stats().items():
                self._retired_backend_stats[key] = self._retired_backend_stats.get(key, 0.0) + value
            self._base_matrix = updated_matrix
            self._backend = updated_backend
            self._analysis_handle = updated_analysis
            self._solution_buffer = updated_solution
            self._stats["pattern_rebuilds"] += 1.0
            return False

    def factorize(self, force_new: bool = False) -> SparseLinearFactorizationHandle:
        """Refresh current coefficients without retaining failed numeric objects.

        :param force_new: Request full fresh numeric factors instead of pivot replay.
        :return: Successful current-matrix factorization handle.
        :raises RuntimeError: When current coefficients cannot be factorized.
        """
        previous: SparseLinearFactorizationHandle | None = self._cached_handle
        # Refactor may mutate its input in place even when it raises. Clear first.
        self._cached_handle = None
        if not force_new and previous is not None and self._backend.supports_numeric_refactorization():
            self._stats["refactor_attempts"] += 1.0
            try:
                self._cached_handle = self._backend.refactor_numeric(
                    self._base_matrix, self._analysis_handle, previous)
            except (RuntimeError, np.linalg.LinAlgError):
                self._stats["refactor_failures"] += 1.0
            else:
                if self._cached_handle is not None:
                    self._stats["numeric_refactorizations"] += 1.0
                else:
                    pass
        else:
            pass
        if self._cached_handle is None:
            self._stats["factorization_attempts"] += 1.0
            self._cached_handle = self._backend.factorize(self._base_matrix, self._analysis_handle)
            self._stats["numeric_factorizations"] += 1.0
        else:
            pass
        return self._cached_handle

    def solve(self, rhs: Vec) -> Vec:
        """Apply resident factors without assembly, factorization or cache decisions.

        :param rhs: Current real right-hand side in original variable order.
        :return: Borrowed solution buffer, valid until this phase's next solve.
        :raises RuntimeError: If no factors are eligible or native solving fails.
        """
        self._stats["solve_attempts"] += 1.0
        if self._cached_handle is None:
            raise RuntimeError("Sparse solve requires a valid factorization")
        else:
            try:
                self._cached_handle.solve_into(rhs, self._solution_buffer)
            except (RuntimeError, np.linalg.LinAlgError):
                self.invalidate()
                raise
            else:
                if np.all(np.isfinite(self._solution_buffer)):
                    self._stats["solve_calls"] += 1.0
                else:
                    self.invalidate()
        return self._solution_buffer

    def solve_fallback(self, rhs: Vec) -> Vec:
        """Retain the structural solver's existing original-order LSQR recovery.

        :param rhs: Real right-hand side in original matrix order.
        :return: Borrowed fallback solution buffer.
        """
        self._solution_buffer[:] = np.asarray(sparse_lsqr_fallback(self._base_matrix, rhs), dtype=np.float64)
        self._stats["fallback_solves"] += 1.0
        return self._solution_buffer

    def get_active_matrix(self) -> CscMat:
        """Expose the active factor matrix for the existing diagnostic wrappers.

        :return: Backend matrix when factored, otherwise the current original shell.
        """
        if self._cached_handle is None:
            return self._base_matrix
        else:
            return self._cached_handle.get_active_matrix()

    def get_stats(self) -> dict[str, float]:
        """Combine successful phase operations and backend work across pattern changes.

        :return: Fresh statistics mapping; common counters cannot be overwritten.
        """
        result: dict[str, float] = dict(self._stats)
        key: str
        value: float
        for key, value in self._retired_backend_stats.items():
            if key not in self._stats:
                result[key] = value
            else:
                pass
        for key, value in self._backend.get_backend_stats().items():
            if key not in self._stats:
                result[key] = result.get(key, 0.0) + float(value)
            else:
                pass
        return result


class CluFactorizationHandle(SparseLinearFactorizationHandle):
    """Retain a CLU factorizer and its shared matrix lifetime."""

    __slots__ = ("_backend", "_factorizer", "_matrix")

    def __init__(self, backend: "CluSparseBackend", factorizer: Any, matrix: CscMat) -> None:
        """Bind factors to their current phase-owned buffers.

        :param backend: Backend that created the factorizer and reads its status codes.
        :param factorizer: Successfully factorized CLU instance (native or Numba).
        :param matrix: Shared canonical real CSC coefficients.
        :return: None.
        """
        self._backend: CluSparseBackend = backend
        self._factorizer: Any = factorizer
        self._matrix: CscMat = matrix

    def solve_into(self, rhs: Vec, out_solution: Vec) -> None:
        """Perform only native triangular solving into existing output storage.

        :param rhs: Contiguous real right-hand side.
        :param out_solution: Writable caller-owned real solution buffer.
        :return: None.
        :raises RuntimeError: If the native triangular solve fails.
        :raises ValueError: If solve buffers do not contain float64 values.
        """
        if rhs.dtype != np.float64 or out_solution.dtype != np.float64:
            raise ValueError("CLU solve buffers must contain float64 values")
        else:
            pass
        # Some Numba arrays carry equivalent, noncanonical dtype descriptors.
        # Canonical views satisfy the native binding without copying values or
        # weakening its contiguity, alignment and writable-output validation.
        native_rhs: Vec = rhs.view(np.float64)
        native_output: Vec = out_solution.view(np.float64)
        status: Any = self._factorizer.solve(native_rhs, native_output)
        if not self._backend.is_success(status):
            raise RuntimeError("CLU solve failed: " + self._backend.status_text(status))
        else:
            pass

    def get_active_matrix(self) -> CscMat:
        """Return coefficients in the original variable order.

        :return: Phase-owned CSC matrix.
        """
        return self._matrix


class CluSparseBackend(SparseLinearSolverBackend):
    """Own CLU native state; pattern/value validity belongs to the common manager."""

    __slots__ = ("_matrix", "_factorizer", "_analyses")

    def __init__(self, base_matrix: CscMat, base_data: Vec) -> None:
        """Borrow stable phase storage without a second CSC snapshot.

        :param base_matrix: Canonical real square CSC shell.
        :param base_data: Values sharing storage with the shell.
        :return: None.
        """
        # Empty arrays have no overlapping bytes; their shape-valid native
        # factorization must still report a singular all-zero matrix.
        if (base_matrix.dtype != np.float64
                or base_data.shape != base_matrix.data.shape or base_data.dtype != base_matrix.data.dtype
                or (base_data.size > 0 and not np.shares_memory(base_matrix.data, base_data))):
            raise ValueError("CLU requires the matrix's live numeric buffer")
        else:
            pass
        self._matrix: CscMat = base_matrix
        self._factorizer: Any | None = None
        self._analyses: int = 0

    def get_name(self) -> str:
        """Identify this native backend.

        :return: Stable provider name used in diagnostics.
        """
        return "native_clu"

    def get_solver_type(self) -> SparseSolver:
        """Identify the selected enum.

        :return: CLU selection.
        """
        return SparseSolver.CLU

    def is_available(self) -> bool:
        """Respect the existing activation owner.

        :return: Whether the licensed native API is available.
        """
        return SparseSolver.CLU in available_sparse_solvers

    def supports_symbolic_analysis_reuse(self) -> bool:
        """Declare the native factorizer's retained same-pattern analysis.

        :return: True; analysis is performed internally on first factorization.
        """
        return True

    def supports_numeric_refactorization(self) -> bool:
        """Declare the native fixed-pivot replay operation.

        :return: True; failed replay is handled by the common owner.
        """
        return True

    def factorize(self, matrix: CscMat, analysis_handle: object | None) -> SparseLinearFactorizationHandle:
        """Build full numeric factors, selecting fresh pivots for an existing pattern.

        :param matrix: Current stable shell already bound to this backend.
        :param analysis_handle: Unused; CLU owns its native symbolic analysis.
        :return: Handle for a successful current-matrix factorization.
        :raises RuntimeError: If native full factorization fails.
        """
        if self._factorizer is None:
            # Symmetry is a property of the stored pattern, including explicit zeros.
            pattern: CscMat = self._matrix.copy()
            pattern.data.fill(1.0)
            symmetric_pattern: bool = (pattern != pattern.T).nnz == 0
            # Retain the same CSC buffers through a transient metadata shell.
            # NumPy-equivalent float64 descriptors from Numba otherwise fail
            # the native binding's descriptor-identity check. This view is not
            # a second matrix snapshot and observes every live numeric update.
            native_matrix: CscMat = csc_matrix((self._matrix.data.view(np.float64),
                self._matrix.indices, self._matrix.indptr), shape=self._matrix.shape, copy=False)
            self._factorizer = self.create_factorizer(native_matrix, symmetric_pattern)
            status: Any = self._factorizer.factorize()
            if self.is_success(status):
                self._analyses += 1
            else:
                pass
        else:
            # factorize() can replay old pivots: explicit full refresh must repivot.
            status = self.repivot(self._factorizer)
        if not self.is_success(status):
            self._factorizer = None
            raise RuntimeError("CLU factorization failed: " + self.status_text(status))
        else:
            return CluFactorizationHandle(self, self._factorizer, self._matrix)

    def refactor_numeric(self, matrix: CscMat, analysis_handle: object | None,
                         previous_factorization: SparseLinearFactorizationHandle | None) -> SparseLinearFactorizationHandle | None:
        """Replay native pivots without deciding whether coefficients have changed.

        :param matrix: Current stable shell with refreshed values.
        :param analysis_handle: Unused; native symbolic state is retained internally.
        :param previous_factorization: Previously eligible common-owner handle.
        :return: New handle on successful replay, otherwise no eligible factors.
        """
        if self._factorizer is not None and isinstance(previous_factorization, CluFactorizationHandle):
            status: Any = self._factorizer.refactor()
            if self.is_success(status):
                return CluFactorizationHandle(self, self._factorizer, self._matrix)
            else:
                # Never reuse a native object after unsuccessful destructive replay.
                self._factorizer = None
                raise RuntimeError("CLU refactor failed: " + self.status_text(status))
        else:
            return None

    def create_factorizer(self, matrix: CscMat, symmetric_pattern: bool) -> Any:
        """Create the licensed native factorizer bound to the live CSC buffers.

        :param matrix: Metadata shell sharing the phase-owned buffers.
        :param symmetric_pattern: Whether the stored pattern is structurally symmetric.
        :return: Unfactorized native CLU factorizer.
        """
        options: pg.clu.Options = pg.clu.Options()
        options.symmetric_pattern = symmetric_pattern
        return pg.clu.Factorizer(pg.clu.MatrixView(matrix), options)

    def repivot(self, factorizer: Any) -> Any:
        """Choose fresh pivots on the retained analysis.

        :param factorizer: Previously factorized native CLU factorizer.
        :return: Native CLU status.
        """
        return factorizer.repivot()

    def is_success(self, status: Any) -> bool:
        """Tell whether a native CLU call succeeded.

        :param status: Native CLU status.
        :return: True on success.
        """
        return status == pg.clu.Status.success

    def status_text(self, status: Any) -> str:
        """Name a native CLU status for diagnostics.

        :param status: Native CLU status.
        :return: Stable status name.
        """
        return pg.clu.status_name(status)

    def get_backend_stats(self) -> dict[str, float]:
        """Report actual native analysis creation; numeric counts are phase-owned.

        :return: Successful first-factor analysis count.
        """
        return dict(analyses=float(self._analyses))


class CluSparseBackendProvider(SparseLinearSolverBackendProvider):
    """Create licensed CLU backends without owning any simulation factors."""

    __slots__ = ()

    def get_name(self) -> str:
        """Identify this provider.

        :return: Native CLU name.
        """
        return "native_clu"

    def get_solver_type(self) -> SparseSolver:
        """Return the associated option.

        :return: CLU selection.
        """
        return SparseSolver.CLU

    def is_available(self) -> bool:
        """Use the existing activation/API availability decision.

        :return: True for a licensed supported CLU installation.
        """
        return SparseSolver.CLU in available_sparse_solvers

    def get_unavailable_reason(self) -> str:
        """Report activation failure without inspecting license contents.

        :return: Existing activation reason or missing-CLU-API explanation.
        """
        if self.is_available():
            return ""
        elif not GSLV_AVAILABLE:
            return GSLV_UNAVAILABLE_REASON
        else:
            return "installed pygslv does not expose the CLU API"

    def create_backend(self, base_matrix: CscMat, base_data: Vec) -> SparseLinearSolverBackend:
        """Create phase-local native ownership.

        :param base_matrix: Stable real canonical CSC matrix.
        :param base_data: Live matrix values.
        :return: One CLU backend referencing these buffers.
        """
        return CluSparseBackend(base_matrix, base_data)


class CluNumbaSparseBackend(CluSparseBackend):
    """CLU backend running the Numba port in Utils/Sparse/clu.py instead of the licensed library."""

    __slots__ = ()

    def get_name(self) -> str:
        """Identify this backend.

        :return: Stable provider name used in diagnostics.
        """
        return "numba_clu"

    def get_solver_type(self) -> SparseSolver:
        """Identify the selected enum.

        :return: CLU_Numba selection.
        """
        return SparseSolver.CLU_Numba

    def is_available(self) -> bool:
        """The Numba port has no optional dependency.

        :return: True.
        """
        return True

    def create_factorizer(self, matrix: CscMat, symmetric_pattern: bool) -> Any:
        """Create the Numba factorizer bound to the live CSC buffers.

        :param matrix: Metadata shell sharing the phase-owned buffers.
        :param symmetric_pattern: Whether the stored pattern is structurally symmetric.
        :return: Unfactorized Numba CLU factorizer.
        """
        options: clu_numba.Options = clu_numba.Options(symmetric_pattern=symmetric_pattern)
        return clu_numba.Factorizer(matrix, options)

    def repivot(self, factorizer: Any) -> Any:
        """Choose fresh pivots on the retained analysis for the current values.

        :param factorizer: Previously factorized Numba CLU factorizer.
        :return: Numba CLU status.
        """
        return factorizer.repivot(self._matrix)

    def is_success(self, status: Any) -> bool:
        """Tell whether a Numba CLU call succeeded.

        :param status: Numba CLU status.
        :return: True on success.
        """
        return status == clu_numba.Status.SUCCESS

    def status_text(self, status: Any) -> str:
        """Name a Numba CLU status for diagnostics.

        :param status: Numba CLU status.
        :return: Stable status name.
        """
        return clu_numba.status_name(status)


class CluNumbaSparseBackendProvider(SparseLinearSolverBackendProvider):
    """Create Numba CLU backends without owning any simulation factors."""

    __slots__ = ()

    def get_name(self) -> str:
        """Identify this provider.

        :return: Numba CLU name.
        """
        return "numba_clu"

    def get_solver_type(self) -> SparseSolver:
        """Return the associated option.

        :return: CLU_Numba selection.
        """
        return SparseSolver.CLU_Numba

    def is_available(self) -> bool:
        """The Numba port has no optional dependency.

        :return: True.
        """
        return True

    def get_unavailable_reason(self) -> str:
        """Report why the provider cannot be used.

        :return: Empty text; the provider is always available.
        """
        return ""

    def create_backend(self, base_matrix: CscMat, base_data: Vec) -> SparseLinearSolverBackend:
        """Create phase-local Numba CLU ownership.

        :param base_matrix: Stable real canonical CSC matrix.
        :param base_data: Live matrix values.
        :return: One Numba CLU backend referencing these buffers.
        """
        return CluNumbaSparseBackend(base_matrix, base_data)


class PardisoFactorizationHandle(SparseLinearFactorizationHandle):
    """Keep public PyPardiso factors alive for triangular solves."""

    __slots__ = ("_solver", "_matrix")

    def __init__(self, solver: PyPardisoSolver, matrix: CscMat) -> None:
        """Bind successfully factored public solver state.

        :param solver: Resident PyPardiso instance.
        :param matrix: Current canonical real CSC matrix.
        :return: None.
        """
        self._solver: PyPardisoSolver = solver
        self._matrix: CscMat = matrix

    def solve_into(self, rhs: Vec, out_solution: Vec) -> None:
        """Use the public stored-matrix solve path, which performs phase 33.

        :param rhs: Current real vector.
        :param out_solution: Existing output buffer.
        :return: None.
        :raises RuntimeError: If native solving fails.
        """
        try:
            out_solution[:] = self._solver.solve(self._matrix, rhs)
        except PyPardisoError as error:
            raise RuntimeError(str(error)) from error
        else:
            pass

    def get_active_matrix(self) -> CscMat:
        """Expose original-order coefficients.

        :return: Phase-owned CSC matrix.
        """
        return self._matrix


class PardisoSparseBackend(SparseLinearSolverBackend):
    """Use public full factorization and retained solves without inventing refactor."""

    __slots__ = ("_matrix", "_solver", "_has_native_state")

    def __init__(self, base_matrix: CscMat, base_data: Vec) -> None:
        """Bind one stable phase matrix to a private public solver instance.

        :param base_matrix: Real canonical CSC coefficients.
        :param base_data: Values sharing the matrix storage.
        :return: None.
        """
        # Jointly empty buffers have no overlapping bytes but are valid CSC
        # storage. Let the public factorization report numerical singularity.
        if (base_data.shape != base_matrix.data.shape or base_data.dtype != base_matrix.data.dtype
                or (base_data.size > 0 and not np.shares_memory(base_matrix.data, base_data))):
            raise ValueError("Pardiso requires the matrix's live numeric buffer")
        else:
            pass
        if base_matrix.shape[0] != base_matrix.shape[1] or base_matrix.dtype != np.float64:
            raise ValueError("Pardiso requires a square float64 matrix")
        else:
            pass
        self._matrix: CscMat = base_matrix
        self._solver: PyPardisoSolver = PyPardisoSolver()
        self._has_native_state: bool = False
        # The public wrapper has no destructor. Its stored A is a copy, so this
        # callback retains only the solver and cannot keep the watched CSC alive.
        finalize(base_matrix, self._solver.free_memory, True)

    def get_name(self) -> str:
        """Identify the public optional backend.

        :return: Pardiso provider name.
        """
        return "pypardiso"

    def get_solver_type(self) -> SparseSolver:
        """Identify the configured enum.

        :return: Pardiso selection.
        """
        return SparseSolver.Pardiso

    def is_available(self) -> bool:
        """Respect the existing optional-import availability check.

        :return: Whether the public wrapper imported successfully.
        """
        return SparseSolver.Pardiso in available_sparse_solvers

    def factorize(self, matrix: CscMat, analysis_handle: object | None) -> SparseLinearFactorizationHandle:
        """Perform public full factorization of current coefficients.

        :param matrix: Bound stable matrix with current numeric values.
        :param analysis_handle: Unused; the public API provides no symbolic handle.
        :return: Current factors wrapped for retained solves.
        :raises RuntimeError: If Pardiso cannot factorize this matrix.
        """
        try:
            if self._has_native_state:
                self._solver.free_memory(everything=True)
                self._has_native_state = False
            else:
                pass
            # A failed native attempt may allocate state. Keep it cleanup-eligible;
            # only the common manager decides whether factors can actually solve.
            self._has_native_state = True
            self._solver.factorize(self._matrix)
        except (PyPardisoError, ValueError) as error:
            raise RuntimeError(str(error)) from error
        else:
            self._has_native_state = True
            return PardisoFactorizationHandle(self._solver, self._matrix)

    def get_backend_stats(self) -> dict[str, float]:
        """Leave full-factor counts with the common owner; expose no fake analysis.

        :return: Empty backend-specific statistics.
        """
        return dict()


class PardisoSparseBackendProvider(SparseLinearSolverBackendProvider):
    """Create independent public Pardiso instances for numerical phases."""

    __slots__ = ()

    def get_name(self) -> str:
        """Identify the public optional provider.

        :return: Pardiso name.
        """
        return "pypardiso"

    def get_solver_type(self) -> SparseSolver:
        """Identify the configured enum.

        :return: Pardiso selection.
        """
        return SparseSolver.Pardiso

    def is_available(self) -> bool:
        """Inspect existing import availability without a native solve.

        :return: True if the public optional package loaded.
        """
        return SparseSolver.Pardiso in available_sparse_solvers

    def get_unavailable_reason(self) -> str:
        """Explain optional package unavailability.

        :return: Empty when available, otherwise the public API requirement.
        """
        if self.is_available():
            return ""
        else:
            return "pypardiso public solver API is not available"

    def create_backend(self, base_matrix: CscMat, base_data: Vec) -> SparseLinearSolverBackend:
        """Create phase-local Pardiso ownership.

        :param base_matrix: Stable real CSC shell.
        :param base_data: Its live numeric values.
        :return: Backend owning one public PyPardiso instance.
        """
        return PardisoSparseBackend(base_matrix, base_data)
