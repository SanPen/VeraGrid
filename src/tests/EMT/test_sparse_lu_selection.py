# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""LU-agnostic sparse solver selection, native LU runtime backends and EMT wiring."""

from __future__ import annotations

import importlib
from types import ModuleType
from secrets import token_hex
from typing import Any, Dict, List

import numpy as np
import pytest
import scipy.sparse as sp
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import splu

import VeraGridEngine.Simulations.EMT.emt_solver_factory as emt_solver_factory
import VeraGridEngine.Utils.NumericalMethods.emt_sparse_solver_registry as sparse_registry
import VeraGridEngine.Utils.NumericalMethods.native_lu_runtime_backend as native_backend_module
import VeraGridEngine.Utils.Sparse.sparse_solve as sparse_solve
from tests.EMT.test_kundur_emt_initialization import _build_kundur_problem
from tests.EMT.test_klu_default import _decay_problem
from tests.EMT.test_emt_initialization_workflow import build_single_state_single_algebraic_problem, run_common_explicit_initialization_for_test
from tests.RMS.test_rms_sparse_lu_selection import CountingProvider
from VeraGridEngine.Utils.Symbolic.explicit_initialization_symbolic import ExplicitInitializationResult
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.initialization_emt import run_emt_native_initialization, EmtInitializationReport
from VeraGridEngine.Simulations.EMT.periodic_initialization_emt import solve_periodic_initialization
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.enumerations import EmtInitializationMethod, EmtInitializationStatus
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import (
    SparseLinearSolverBackend,
    SparseLinearSolverBackendProvider,
)
from VeraGridEngine.Utils.NumericalMethods.native_lu_runtime_backend import (
    NativeLuRuntimeBackendProvider,
    NativeLuRuntimeFactorizationHandle,
    load_native_lu_runtime,
    validate_native_lu_runtime,
)
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import DynamicIntegrationMethod, EmtSolverTypes, SparseSolver


def _fake_analyze(indptr: np.ndarray, indices: np.ndarray, n: int) -> Dict[str, Any]:
    """
    Fake symbolic analysis: remember the pattern.

    :param indptr: CSC column pointer.
    :param indices: CSC row indices.
    :param n: Matrix size.
    :return: Symbolic object.
    """
    return {"indptr": indptr.copy(), "indices": indices.copy(), "n": n}


def _fake_factorize(indptr: np.ndarray, indices: np.ndarray, data: np.ndarray, symbolic: Dict[str, Any]) -> Any:
    """
    Fake numeric factorization with SciPy SuperLU.

    :param indptr: CSC column pointer.
    :param indices: CSC row indices.
    :param data: CSC values.
    :param symbolic: Symbolic object.
    :return: SciPy SuperLU object.
    """
    return splu(csc_matrix((data.copy(), indices, indptr), shape=(symbolic["n"], symbolic["n"])))


def _fake_refactor(indptr: np.ndarray, indices: np.ndarray, data: np.ndarray, symbolic: Dict[str, Any], numeric: Any) -> Any:
    """
    Fake refactorization.

    :param indptr: CSC column pointer.
    :param indices: CSC row indices.
    :param data: CSC values.
    :param symbolic: Symbolic object.
    :param numeric: Previous numeric object (unused).
    :return: New SciPy SuperLU object.
    """
    return _fake_factorize(indptr, indices, data, symbolic)


def _fake_solve_into(numeric: Any, rhs: np.ndarray, out: np.ndarray) -> None:
    """
    Fake solve into a caller buffer.

    :param numeric: SciPy SuperLU object.
    :param rhs: Right-hand side.
    :param out: Output buffer.
    :return: None
    """
    out[:] = numeric.solve(rhs)


def _fake_runtime(name: str) -> ModuleType:
    """
    Build a module object implementing the native LU runtime contract with SciPy.

    :param name: Module name.
    :return: Fake runtime module.
    """
    runtime: ModuleType = ModuleType(name)
    runtime.analyze = _fake_analyze
    runtime.factorize = _fake_factorize
    runtime.refactor = _fake_refactor
    runtime.solve_into = _fake_solve_into
    return runtime


def _random_system(n: int, seed: int) -> csc_matrix:
    """
    Build a well-conditioned canonical random sparse matrix.

    :param n: Matrix size.
    :param seed: Random seed.
    :return: CSC matrix.
    """
    matrix: csc_matrix = (sp.random(n, n, density=0.08, random_state=seed, format="csc") + sp.eye(n, format="csc") * 4.0).tocsc()
    matrix.sort_indices()
    return matrix


class _ImportRaiser:
    """Stand-in for importlib that raises a prepared exception."""

    __slots__ = ("error",)

    def __init__(self, error: BaseException) -> None:
        """
        :param error: Exception raised by import_module.
        """
        self.error: BaseException = error

    def import_module(self, name: str) -> ModuleType:
        """
        Raise the prepared exception.

        :param name: Requested module name.
        :return: Never returns.
        """
        raise self.error


class _FakePluginProvider(SparseLinearSolverBackendProvider):
    """Plugin provider with configurable identity and availability."""

    __slots__ = ("solver_type", "available")

    def __init__(self, solver_type: SparseSolver, available: bool) -> None:
        """
        :param solver_type: Reported solver type.
        :param available: Reported availability.
        """
        self.solver_type: SparseSolver = solver_type
        self.available: bool = available

    def get_name(self) -> str:
        """:return: Provider name."""
        return "fake_plugin"

    def get_solver_type(self) -> SparseSolver:
        """:return: Reported solver type."""
        return self.solver_type

    def is_available(self) -> bool:
        """:return: Reported availability."""
        return self.available

    def create_backend(self, base_matrix: csc_matrix, base_data: np.ndarray) -> SparseLinearSolverBackend:
        """:return: Never used."""
        raise RuntimeError("not used")


class _RecordingAnalyze:
    """Analyze stand-in that records every symbolic object it returns."""

    __slots__ = ("records",)

    def __init__(self) -> None:
        """Create an empty record list."""
        self.records: List[Any] = list()

    def __call__(self, indptr: np.ndarray, indices: np.ndarray, n: int) -> Dict[str, Any]:
        """
        Analyse and record.

        :param indptr: CSC column pointer.
        :param indices: CSC row indices.
        :param n: Matrix size.
        :return: Symbolic object.
        """
        symbolic: Dict[str, Any] = _fake_analyze(indptr, indices, n)
        self.records.append(symbolic)
        return symbolic


class _PluginLoader:
    """load_sparse_solver_backend_provider stand-in returning a prepared provider."""

    __slots__ = ("provider",)

    def __init__(self, provider: SparseLinearSolverBackendProvider) -> None:
        """
        :param provider: Provider to return.
        """
        self.provider: SparseLinearSolverBackendProvider = provider

    def __call__(self, plugin_name: str, plugin_directory_override: str) -> SparseLinearSolverBackendProvider:
        """
        :param plugin_name: Plugin name.
        :param plugin_directory_override: Plugin directory.
        :return: Prepared provider.
        """
        return self.provider


def _failing_plugin_loader(plugin_name: str, plugin_directory_override: str) -> SparseLinearSolverBackendProvider:
    """
    Plugin loader stand-in that cannot find the plugin.

    :param plugin_name: Plugin name.
    :param plugin_directory_override: Plugin directory.
    :return: Never returns.
    """
    raise FileNotFoundError("no plugin " + plugin_name)


class _RecordingSolver:
    """Stand-in solver class recording its keyword arguments."""

    __slots__ = ("kwargs",)

    def __init__(self, **kwargs: Any) -> None:
        """
        :param kwargs: Constructor keyword arguments.
        """
        self.kwargs: Dict[str, Any] = kwargs


def test_native_backend_matches_direct_runtime_calls() -> None:
    """A native LU runtime backend solves exactly like direct calls of the runtime."""
    runtime: ModuleType = _fake_runtime("fake_runtime")
    matrix: csc_matrix = _random_system(40, 4)
    rhs: np.ndarray = np.random.default_rng(1).normal(size=40)
    provider: NativeLuRuntimeBackendProvider = NativeLuRuntimeBackendProvider("fake", SparseSolver.KLU, runtime, "")
    backend: SparseLinearSolverBackend = provider.create_backend(matrix, matrix.data)
    solution: np.ndarray = np.zeros(40)
    backend.factorize(matrix, None).solve_into(rhs, solution)
    direct: np.ndarray = splu(matrix).solve(rhs)
    assert np.array_equal(solution, direct)
    assert backend.supports_symbolic_analysis_reuse()
    assert backend.supports_numeric_refactorization()


def test_handle_keeps_the_symbolic_analysis_and_refactor_reuses_it() -> None:
    """Every factorization handle owns its symbolic analysis; refactorization passes the same object."""
    recording_analyze: _RecordingAnalyze = _RecordingAnalyze()
    recorded: List[Any] = recording_analyze.records
    runtime: ModuleType = _fake_runtime("recording_runtime")
    runtime.analyze = recording_analyze
    matrix: csc_matrix = _random_system(30, 5)
    backend: SparseLinearSolverBackend = NativeLuRuntimeBackendProvider("rec", SparseSolver.KLU, runtime, "").create_backend(matrix, matrix.data)
    handle = backend.factorize(matrix, None)
    assert isinstance(handle, NativeLuRuntimeFactorizationHandle)
    assert len(recorded) == 1
    assert handle.get_symbolic() is recorded[0]
    matrix.data *= 1.05
    refactored = backend.refactor_numeric(matrix, None, handle)
    assert isinstance(refactored, NativeLuRuntimeFactorizationHandle)
    assert refactored.get_symbolic() is recorded[0]
    assert backend.get_backend_stats()["numeric_refactorizations"] == 1.0


def test_create_backend_rejects_invalid_shells() -> None:
    """Non-square, non-canonical shells and copied values are rejected."""
    provider: NativeLuRuntimeBackendProvider = NativeLuRuntimeBackendProvider("fake", SparseSolver.KLU, _fake_runtime("rt"), "")
    matrix: csc_matrix = _random_system(20, 6)
    with pytest.raises(ValueError):
        provider.create_backend(matrix, matrix.data.copy())
    rectangular: csc_matrix = sp.random(3, 4, density=0.5, random_state=1, format="csc")
    with pytest.raises(ValueError):
        provider.create_backend(rectangular, rectangular.data)
    duplicated: csc_matrix = csc_matrix((np.array([1.0, 2.0, 3.0]), np.array([1, 0, 1]), np.array([0, 2, 3])), shape=(2, 2))
    with pytest.raises(ValueError):
        provider.create_backend(duplicated, duplicated.data)
    unavailable: NativeLuRuntimeBackendProvider = NativeLuRuntimeBackendProvider("none", SparseSolver.KLU, None, "missing")
    with pytest.raises(RuntimeError):
        unavailable.create_backend(matrix, matrix.data)


def test_loader_reports_reasons_without_raising(monkeypatch: pytest.MonkeyPatch, recwarn: pytest.WarningsRecorder) -> None:
    """Missing packages, broken installations and incomplete contracts become reasons."""
    monkeypatch.setattr(native_backend_module, "importlib", _ImportRaiser(ModuleNotFoundError("absent", name="cvxoptklu")))
    runtime, reason = load_native_lu_runtime("cvxoptklu._klu_native", "cvxoptklu", "veragrid-cvxoptklu")
    assert runtime is None
    assert reason.startswith("veragrid-cvxoptklu is not installed")
    assert len(recwarn) == 0

    monkeypatch.setattr(native_backend_module, "importlib", _ImportRaiser(ModuleNotFoundError("no submodule", name="cvxoptklu._klu_native")))
    runtime, reason = load_native_lu_runtime("cvxoptklu._klu_native", "cvxoptklu", "veragrid-cvxoptklu")
    assert runtime is None
    assert "veragrid-cvxoptklu" in reason

    for error in (ImportError("x"), AttributeError("x"), OSError("x"), RuntimeError("x"), ValueError("x"), TypeError("x"), SystemError("x")):
        monkeypatch.setattr(native_backend_module, "importlib", _ImportRaiser(error))
        runtime, reason = load_native_lu_runtime("cvxoptklu._klu_native", "cvxoptklu", "veragrid-cvxoptklu")
        assert runtime is None
        assert len(reason) > 0

    monkeypatch.setattr(native_backend_module, "importlib", importlib)
    runtime, reason = load_native_lu_runtime("json", "json", "json")
    assert runtime is None
    assert "native LU contract" in reason
    assert validate_native_lu_runtime(_fake_runtime("complete")) == ""


def test_selection_falls_back_to_superlu_with_a_logged_reason() -> None:
    """A solver without a factorisation-reusing provider logs its reason once per resolution and uses SciPy SuperLU."""
    logger: Logger = Logger()
    provider: SparseLinearSolverBackendProvider = sparse_solve.resolve_sparse_lu_provider(SparseSolver.UMFPACKTriangular, logger)
    assert isinstance(provider, SuperLUSparseBackendProvider)
    assert len(logger) == 1
    assert ("Sparse LU solver UmfPackTriangular is unavailable: no factorisation-reusing provider is registered for UmfPackTriangular. "
            "Using SciPy SuperLU.") in str(logger)
    with pytest.warns(RuntimeWarning, match="Sparse LU solver UmfPackTriangular is unavailable"):
        sparse_solve.resolve_sparse_lu_provider(SparseSolver.UMFPACKTriangular, None)


def test_selection_status_without_fallback() -> None:
    """Optional real LU providers report availability without secretly substituting.

    :return: None; distinct methods and unavailable packages retain a reason.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    available: List[SparseSolver] = sparse_solve.get_available_sparse_solvers()
    solver_type: SparseSolver
    for solver_type in (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.Pardiso,
                        SparseSolver.UMFPACK, SparseSolver.ILU, SparseSolver.GMRES, SparseSolver.UMFPACKTriangular):
        provider, reason = sparse_solve.get_sparse_lu_provider_status(solver_type)
        if solver_type in (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.Pardiso) and solver_type in available:
            assert provider is not None and provider.get_solver_type() == solver_type
            assert reason == ""
        else:
            assert provider is None and len(reason) > 0


def test_klu_provider_is_available_whenever_the_runtime_imports() -> None:
    """No silent skip: the native KLU provider is available exactly when its runtime imports."""
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = sparse_solve.get_sparse_lu_provider_status(SparseSolver.KLU)
    try:
        runtime: ModuleType = importlib.import_module("cvxoptklu._klu_native")
    except ImportError:
        assert provider is None
        assert len(reason) > 0
    else:
        if validate_native_lu_runtime(runtime) == "":
            assert isinstance(provider, NativeLuRuntimeBackendProvider)
            assert provider.get_name() == "native_klu"
        else:
            assert provider is None


def test_sparse_solve_is_the_single_selection_point() -> None:
    """sparse_solve exposes both selection faces and SparseSolver has no GSLV member."""
    assert "GSLV" not in SparseSolver.__members__
    assert callable(sparse_solve.get_linear_solver)
    assert callable(sparse_solve.resolve_sparse_lu_provider)


def test_klu_provider_is_cached_per_process() -> None:
    """When the native KLU runtime is available, its provider object is resolved once per process."""
    first: SparseLinearSolverBackendProvider | None
    first_reason: str
    second: SparseLinearSolverBackendProvider | None
    second_reason: str
    first, first_reason = sparse_solve.get_sparse_lu_provider_status(SparseSolver.KLU)
    second, second_reason = sparse_solve.get_sparse_lu_provider_status(SparseSolver.KLU)
    if first is None:
        assert second is None
        assert second_reason == first_reason
    else:
        assert second is first
        assert first_reason == "" and second_reason == ""


def test_registry_plugin_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plugin failures fall back through the selection layer or raise, as configured."""
    monkeypatch.setattr(sparse_registry, "load_sparse_solver_backend_provider", _failing_plugin_loader)
    logger: Logger = Logger()
    provider = sparse_registry.resolve_emt_sparse_solver_backend_provider(SparseSolver.SuperLU, "missing", "", True, logger)
    assert isinstance(provider, SuperLUSparseBackendProvider)
    assert "could not be loaded" in str(logger)
    with pytest.raises(FileNotFoundError):
        sparse_registry.resolve_emt_sparse_solver_backend_provider(SparseSolver.SuperLU, "missing", "", False, logger)

    monkeypatch.setattr(sparse_registry, "load_sparse_solver_backend_provider", _PluginLoader(_FakePluginProvider(SparseSolver.SuperLU, False)))
    logger = Logger()
    provider = sparse_registry.resolve_emt_sparse_solver_backend_provider(SparseSolver.SuperLU, "fake", "", True, logger)
    assert isinstance(provider, SuperLUSparseBackendProvider)
    assert "plugin reported unavailable without a reason" in str(logger)
    with pytest.raises(RuntimeError):
        sparse_registry.resolve_emt_sparse_solver_backend_provider(SparseSolver.SuperLU, "fake", "", False, None)

    monkeypatch.setattr(sparse_registry, "load_sparse_solver_backend_provider", _PluginLoader(_FakePluginProvider(SparseSolver.Pardiso, True)))
    with pytest.raises(ValueError):
        sparse_registry.resolve_emt_sparse_solver_backend_provider(SparseSolver.SuperLU, "fake", "", True, None)


def test_registry_internal_resolution() -> None:
    """Internal resolution logs and falls back, or raises with the reason when fallback is off."""
    logger: Logger = Logger()
    provider: SparseLinearSolverBackendProvider = sparse_registry.resolve_emt_sparse_solver_backend_provider(SparseSolver.UMFPACKTriangular, "", "", True, logger)
    assert isinstance(provider, SuperLUSparseBackendProvider)
    assert len(logger) == 1
    with pytest.raises(RuntimeError, match="no factorisation-reusing provider is registered for UmfPackTriangular"):
        sparse_registry.resolve_emt_sparse_solver_backend_provider(SparseSolver.UMFPACKTriangular, "", "", False, logger)
    assert isinstance(sparse_registry.resolve_emt_sparse_solver_backend_provider(SparseSolver.SuperLU, "", "", False, None), SuperLUSparseBackendProvider)


def test_factory_passes_logger_and_reports_ignored_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every factory branch forwards selection and reports unavailable-provider fallback."""
    for solver_type in (EmtSolverTypes.StructuralCompiled, EmtSolverTypes.StructuralAD, EmtSolverTypes.Symbolic, EmtSolverTypes.Automatic):
        monkeypatch.setitem(emt_solver_factory.EMT_SOLVER_CLASS_MAP, solver_type, _RecordingSolver)
    structural_logger: Logger = Logger()
    solver: _RecordingSolver = emt_solver_factory.build_emt_solver(options=EmtOptions(solver_type=EmtSolverTypes.StructuralCompiled, sparse_solver=SparseSolver.UMFPACKTriangular),
                                                                   problem=None, t0=0.0, t_end=1.0, h=1.0, logger=structural_logger)
    assert isinstance(solver.kwargs["sparse_solver_backend_provider"], SuperLUSparseBackendProvider)
    assert len(structural_logger) == 1
    symbolic_logger: Logger = Logger()
    emt_solver_factory.build_emt_solver(options=EmtOptions(solver_type=EmtSolverTypes.Symbolic, sparse_solver=SparseSolver.UMFPACKTriangular),
                                        problem=None, t0=0.0, t_end=1.0, h=1.0, logger=symbolic_logger)
    assert "is unavailable:" in str(symbolic_logger)
    assert "ignored" not in str(symbolic_logger)
    assert len(symbolic_logger) == 1
    default_logger: Logger = Logger()
    emt_solver_factory.build_emt_solver(options=EmtOptions(solver_type=EmtSolverTypes.Symbolic), problem=None, t0=0.0, t_end=1.0, h=1.0, logger=default_logger)
    assert len(default_logger) == 0


@pytest.fixture(scope="module")
def kundur_problem() -> EmtProblemDae:
    """
    Build the self-contained Kundur EMT problem once for this module.

    :return: Kundur EMT problem.
    """
    return _build_kundur_problem()[0]


def _klu_provider_or_skip() -> SparseLinearSolverBackendProvider:
    """
    Return the native KLU provider, or skip with the unavailability reason.

    :return: Native KLU provider.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = sparse_solve.get_sparse_lu_provider_status(SparseSolver.KLU)
    if provider is None:
        pytest.skip("native KLU runtime unavailable: " + reason)
    else:
        pass
    assert provider.get_name() == "native_klu"
    return provider


@pytest.mark.parametrize("solver_class", [StructuralCompiledSolver, StructuralVectorizedSolver])
def test_kundur_native_klu_matches_superlu(kundur_problem: EmtProblemDae, solver_class: type) -> None:
    """Both structural solvers converge with native KLU and match the SuperLU trajectories."""
    klu_provider: SparseLinearSolverBackendProvider = _klu_provider_or_skip()
    trajectories: Dict[str, np.ndarray] = dict()
    for label, provider in (("superlu", SuperLUSparseBackendProvider()), ("klu", klu_provider)):
        solver = solver_class(kundur_problem, t0=0.0, t_end=0.001, h=5e-6, method=DynamicIntegrationMethod.DaeTrapezoidal,
                              verbose=False, sparse_solver_backend_provider=provider)
        result = solver.simulate()
        assert result[4]
        trajectories[label] = result[1]
    assert trajectories["superlu"].shape == trajectories["klu"].shape
    assert float(np.max(np.abs(trajectories["superlu"] - trajectories["klu"]))) <= 1e-8


def test_emt_provider_precedes_initialization(kundur_problem: EmtProblemDae) -> None:
    """Construction retains its provider for subsequent initialization and simulation.

    :param kundur_problem: Existing physical EMT fixture, already constructed.
    :return: None.
    """
    provider: SparseLinearSolverBackendProvider | None = kundur_problem.get_sparse_solver_backend_provider(kundur_problem.options.sparse_solver)
    assert provider is not None
    solver: StructuralVectorizedSolver | StructuralCompiledSolver | JitAdSolver | JitSymbolicSolver = emt_solver_factory.build_emt_solver(kundur_problem.options, kundur_problem, 0.0, 1.0e-5, 1.0e-5)
    assert solver._sparse_solver_backend_provider is provider

    # A generic helper must invalidate the binding for every registry input;
    # none of these changes may silently reuse a previously allowed fallback.
    problem: EmtProblemTemplate = _decay_problem()
    options: EmtOptions = EmtOptions(sparse_solver=SparseSolver.SuperLU)
    baseline_provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem.set_sparse_solver_backend_provider(baseline_provider, SparseSolver.SuperLU)
    assert problem.get_sparse_solver_backend_provider(SparseSolver.SuperLU) is baseline_provider
    assert problem.get_sparse_solver_backend_provider(SparseSolver.SuperLU, "missing_plugin") is None
    assert problem.get_sparse_solver_backend_provider(SparseSolver.SuperLU, "", "different_directory") is None
    assert problem.get_sparse_solver_backend_provider(SparseSolver.SuperLU, "", "", False) is None

    options = EmtOptions(sparse_solver=SparseSolver.SuperLU,
        external_sparse_solver_plugin_name="missing_lu_identity_regression_plugin")
    logger: Logger = Logger()
    fallback_solver: StructuralVectorizedSolver | StructuralCompiledSolver | JitAdSolver | JitSymbolicSolver = emt_solver_factory.build_emt_solver(options, problem, 0.0, 1.0e-5, 1.0e-5, logger=logger)
    fallback_provider: SparseLinearSolverBackendProvider | None = problem.get_sparse_solver_backend_provider(
        options.sparse_solver, options.external_sparse_solver_plugin_name,
        options.external_sparse_solver_directory, options.allow_internal_sparse_fallback)
    assert fallback_solver._sparse_solver_backend_provider is fallback_provider
    assert fallback_provider is not baseline_provider
    assert logger.warning_count() == 1
    emt_solver_factory.build_emt_solver(options, problem, 0.0, 1.0e-5, 1.0e-5, logger=logger)
    assert logger.warning_count() == 1

    options = EmtOptions(sparse_solver=SparseSolver.SuperLU,
        external_sparse_solver_plugin_name="missing_lu_identity_regression_plugin",
        external_sparse_solver_directory="missing_lu_identity_regression_directory")
    emt_solver_factory.build_emt_solver(options, problem, 0.0, 1.0e-5, 1.0e-5, logger=logger)
    assert logger.warning_count() == 2
    options = EmtOptions(sparse_solver=SparseSolver.SuperLU,
        external_sparse_solver_plugin_name="missing_lu_identity_regression_plugin",
        external_sparse_solver_directory="missing_lu_identity_regression_directory",
        allow_internal_sparse_fallback=False)
    with pytest.raises(FileNotFoundError):
        emt_solver_factory.build_emt_solver(options, problem, 0.0, 1.0e-5, 1.0e-5, logger=logger)
    with pytest.raises(FileNotFoundError):
        run_emt_native_initialization(problem, options)
    with pytest.raises(FileNotFoundError):
        solve_periodic_initialization(problem, options)


def test_emt_jit_solvers_use_provider() -> None:
    """Both JIT families physically solve their sparse branch with the selected LU.

    :return: None; a nonzero decay state forces real Newton work.
    """
    provider: SparseLinearSolverBackendProvider = _klu_provider_or_skip()
    ad_problem: EmtProblemTemplate = _decay_problem()
    ad_problem.init_guess[ad_problem.get_state_vars()[0].uid] = 1.0
    symbolic_problem: EmtProblemTemplate = _decay_problem()
    symbolic_problem.init_guess[symbolic_problem.get_state_vars()[0].uid] = 1.0
    ad: JitAdSolver = JitAdSolver(ad_problem, 0.0, 5.0e-5, 1.0e-5,
        method=DynamicIntegrationMethod.DaeBackEuler, dense_threshold=0,
        newton_tolerance=1.0e-8, sparse_solver_backend_provider=provider)
    symbolic: JitSymbolicSolver = JitSymbolicSolver(symbolic_problem, 0.0, 5.0e-5, 1.0e-5,
        method=DynamicIntegrationMethod.DaeBackEuler, dense_threshold=0,
        newton_tolerance=1.0e-8, sparse_solver_backend_provider=provider)
    ad_result: tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = ad.simulate()
    symbolic_result: tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = symbolic.simulate()
    assert ad_result[4] and symbolic_result[4]
    np.testing.assert_allclose(ad_result[1], symbolic_result[1], atol=1.0e-8, rtol=1.0e-8)
    assert ad._sparse_linear_solver.get_stats()["solve_calls"] > 0.0
    assert symbolic._sparse_factor_manager is not None
    assert symbolic._sparse_factor_manager.get_stats()["solve_calls"] > 0.0


def test_emt_initialization_uses_provider() -> None:
    """Native reduced initialization reaches a real supplied provider below no dense path.

    :return: None; verify the original physical state/algebraic operating point.
    """
    seed_problem: EmtProblemTemplate = build_single_state_single_algebraic_problem()[0]
    # Persistent initialization keys contain symbol names. Rebuild the same
    # equations with run-local names so this test always measures native work
    # while leaving all user cache entries and global configuration untouched.
    suffix: str = token_hex(8)
    variables: list[Var]
    variable: Var
    for variables in (seed_problem.get_state_vars(), seed_problem.get_algebraic_vars(), seed_problem.get_diff_vars()):
        for variable in variables:
            variable.set_name(variable.name + "_" + suffix)
    problem: EmtProblemTemplate = EmtProblemTemplate(
        sys_block=seed_problem.sys_block, static_parameter_values_mapping=dict(),
        glob_time=Var("time_" + suffix))
    provider: CountingProvider = CountingProvider(_klu_provider_or_skip())
    options: EmtOptions = EmtOptions(initialization_method=EmtInitializationMethod.ConsistentNewton,
        sparse_solver=SparseSolver.KLU, init_dense_threshold=0, init_fix_seeded_states=False)
    problem.set_sparse_solver_backend_provider(provider, SparseSolver.KLU)
    explicit_result: ExplicitInitializationResult = run_common_explicit_initialization_for_test(problem)
    assert explicit_result.converged
    # Explicit propagation already solves y. Perturb its finite seed so native
    # Newton must restore the original y=2 constraint through the selected LU.
    problem.init_guess[problem.get_algebraic_vars()[0].uid] = 3.0
    report: EmtInitializationReport = run_emt_native_initialization(problem, options)
    print("INITIALIZATION_PROVIDER_PHASE", report.status, report.method_used, report.unknown_var_count, report.initial_residual_inf, report.final_residual_inf, report.message)
    assert report.status == EmtInitializationStatus.RESOLVED
    assert not report.persistent_cache_hit
    assert provider.solves > 0 and provider.factorizations > 0
    np.testing.assert_allclose(problem.get_x0(), np.array((2.0, 2.0)), atol=1.0e-9)
    np.testing.assert_allclose(problem.get_dx0(), np.zeros(1), atol=1.0e-9)
