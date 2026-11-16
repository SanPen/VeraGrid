# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Nonphysical, fixed-tolerance consumer checks for the three supported RMS fx solvers."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.sparse import csc_matrix

from VeraGridEngine.basic_structures import Logger, Mat, Vec
from VeraGridEngine.enumerations import SparseSolver
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Simulations.Rms.numerical import back_euler_fx
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.initialization_rms import solve_rms_newton_correction
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.Sparse.sparse_solve import SparseProviderLinearSolver, get_sparse_lu_provider_status
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, piecewise


class RmsChordProblem(RmsProblemTemplate):
    """Declare x'=-x and z+c*z**3=p(t), with no network or power flow.

    The canonical block declares the equations and variable ordering.
    Scalar and vectorized entry points read the same fixed-size state. These are
    explicit consumer fixtures, not replacements for the real integrator methods.
    """

    __slots__ = ("logger", "sys_block", "algebraic_vars", "_algebraic_eqs", "_variable_parameters_values",
                 "_constant_params", "_fmu_me_adapters", "_fmu_cs_adapters", "_gathered",
                 "cubic", "row_scale", "forced_time", "jump", "reject_after", "reference_column",
                 "me_advances", "cs_advances", "accepted_boundaries", "last_time", "reference_switch_time", "confirmation_case", "square_constraint",
                 "trace_derivatives", "_history_trace", "_history_count")

    def __init__(self, cubic: float = 0.0, row_scale: float = 1.0, confirmation_case: bool = False,
                 square_constraint: bool = False, trace_derivatives: bool = False) -> None:
        """Construct one canonical synthetic equation block and fixed-size buffers.

        :param cubic: Algebraic nonlinearity, independent of solver tolerance.
        :param row_scale: Fixed algebraic scaling for confirming-correction cases.
        :param confirmation_case: Enable a narrow invalid algebraic band control.
        :param square_constraint: Use a square equation for persistent finite rejection.
        :param trace_derivatives: Record the next substep's accepted derivative context.
        :return: None.
        """
        super().__init__()
        self.logger: Logger = Logger()
        state: Var = Var("reuse_x")
        derivative: Var = Var("reuse_dx", base_var=state)
        algebraic: Var = Var("reuse_z")
        target: Var = Var("reuse_p")
        coefficient: Var = Var("reuse_c")
        differentials: list[Var] = list((derivative,))
        if trace_derivatives:
            # Algebraic differentials have an independent accepted-history slot.
            differentials.append(Var("reuse_dz", base_var=algebraic))
        else:
            pass
        equation: Expr
        if confirmation_case:
            regular: Expr = algebraic * algebraic - target
            branches: np.ndarray = np.empty(2, dtype=object)
            branches[0] = Const(100.0)
            branches[1] = regular
            equation = Const(row_scale) * piecewise(algebraic, np.array((1.00994, 1.00996)), branches, regular)
        elif square_constraint:
            equation = Const(row_scale) * (algebraic * algebraic - target)
        else:
            equation = Const(row_scale) * (algebraic + coefficient * algebraic * algebraic * algebraic - target)
        self.sys_block: Block = Block(name="RmsChordAlgebra", state_vars=list((state,)), diff_vars=differentials,
            state_eqs=list((-state,)), algebraic_vars=list((algebraic,)),
            algebraic_eqs=list((equation,)),
            parameters=dict(((coefficient, Const(cubic)),)))
        self.algebraic_vars: list[Var] = self.sys_block.algebraic_vars
        self._algebraic_eqs: list[Expr] = self.sys_block.algebraic_eqs
        self._variable_parameters_values: Vec = np.zeros(1)
        self._constant_params: Vec = np.array((cubic,))
        self._fmu_me_adapters: list[object] = list()
        self._fmu_cs_adapters: list[object] = list()
        self._gathered: Vec = np.zeros(2)
        self.cubic: float = cubic
        self.row_scale: float = row_scale
        self.forced_time: float | None = None
        self.jump: float = 0.0
        self.reject_after: float | None = None
        self.reference_column: int | None = None
        self.me_advances: int = 0
        self.cs_advances: int = 0
        self.accepted_boundaries: int = 0
        self.last_time: float = 0.0
        self.reference_switch_time: float | None = None
        self.confirmation_case: bool = confirmation_case
        self.square_constraint: bool = square_constraint
        self.trace_derivatives: bool = trace_derivatives
        # Three steps, two attempts and twenty corrections fit within this fixed trace.
        self._history_trace: np.ndarray = np.empty((128 if trace_derivatives else 0, 3), dtype=np.float64)
        self._history_count: int = 0

    def get_x0(self) -> Vec:
        """Return a consistent initial state without an initialization solve.

        :return: State x=1 and algebraic z=0.
        """
        initial: Vec = np.array((1.0, 1.0 if self.confirmation_case or self.square_constraint else 0.0))
        return initial

    def get_dx0(self) -> Vec:
        """Read the initial derivative of the declared decay equation.

        :return: The one-element derivative vector.
        """
        if self.trace_derivatives:
            initial: Vec = np.array((-1.0, 0.0))
        else:
            initial = np.array((-1.0,))
        return initial

    def get_states_number(self) -> int:
        """Locate the algebraic block after the canonical state ordering.

        :return: Number of differential states in the block.
        """
        count: int = len(self.sys_block.state_vars)
        return count

    def get_all_vars_number(self) -> int:
        """Size integrator buffers from the declared unknown ordering.

        :return: Differential plus algebraic unknown count.
        """
        count: int = len(self.sys_block.state_vars) + len(self.sys_block.algebraic_vars)
        return count

    def get_diff_var_number(self) -> int:
        """Size the separately ordered derivative buffer.

        :return: Count of declared differentials.
        """
        count: int = len(self.sys_block.diff_vars)
        return count

    def get_algebraic_var_number(self) -> int:
        """Size the algebraic projection block.

        :return: Count of declared algebraic unknowns.
        """
        count: int = len(self.algebraic_vars)
        return count

    def get_dx(self, x: Vec, xn: Vec, dx: Vec, h: float) -> Vec:
        """Apply the current backward difference without committing history.

        :param x: Candidate unknowns.
        :param xn: Accepted predecessor.
        :param dx: Prior derivative context, not modified.
        :param h: Actual substep size.
        :return: Candidate derivative of the one state.
        """
        if self.trace_derivatives:
            if self._history_count < self._history_trace.shape[0]:
                self._history_trace[self._history_count, 0] = self.last_time
                self._history_trace[self._history_count, 1] = dx[1]
                self._history_trace[self._history_count, 2] = x[1]
                self._history_count += 1
            else:
                pass
            result: Vec = (x - xn) / h
        else:
            result = (x[:1] - xn[:1]) / h
        return result

    def rhs_state(self, x: Vec, dx: Vec) -> Vec:
        """Evaluate the declared state equation at the supplied candidate.

        :param x: State followed by algebraic unknown.
        :param dx: Derivative context, absent from this equation.
        :return: The decay rate.
        """
        result: Vec = -x[:1]
        return result

    def rhs_algebraic(self, values: Vec, diff_values: Vec) -> Vec:
        """Evaluate the canonical constraint with current source parameters.

        :param values: Current candidate in canonical order.
        :param diff_values: Derivative context, absent from the constraint.
        :return: Scaled nonlinear algebraic residual.
        """
        z: float = float(values[1])
        if self.confirmation_case:
            if 1.00994 <= z < 1.00996:
                value: float = self.row_scale * 100.0
            else:
                value = self.row_scale * (z * z - self._variable_parameters_values[0])
        elif self.square_constraint:
            value = self.row_scale * (z * z - self._variable_parameters_values[0])
        else:
            value = self.row_scale * (z + self.cubic * z * z * z - self._variable_parameters_values[0])
        result: Vec = np.array((value,))
        return result

    def rhs_state_vec(self) -> Vec:
        """Evaluate the same state equation from the vectorized gather.

        :return: Gathered decay rate.
        """
        result: Vec = -self._gathered[:1]
        return result

    def rhs_algebraic_vec(self, x: Vec, dx: Vec) -> Vec:
        """Keep vectorized residual order identical to the scalar fixture.

        :param x: Candidate unknowns.
        :param dx: Candidate derivatives.
        :return: Canonical algebraic residual.
        """
        self._gathered[:] = x
        return self.rhs_algebraic(x, dx)

    def get_j11(self, x: Vec, dx: Vec, h: float) -> csc_matrix:
        """Differentiate the state equation with respect to its state.

        :param x: Candidate unknowns.
        :param dx: Candidate derivatives.
        :param h: Current step, used by the integrator's implicit assembly.
        :return: State-equation derivative block.
        """
        matrix: csc_matrix = csc_matrix(np.array(((-1.0,),)))
        return matrix

    def get_j12(self, x: Vec, dx: Vec, h: float) -> csc_matrix:
        """Declare no algebraic dependence in the state equation.

        :param x: Candidate unknowns.
        :param dx: Candidate derivatives.
        :param h: Current effective step.
        :return: Empty one-by-one coupling block.
        """
        matrix: csc_matrix = csc_matrix((1, 1), dtype=np.float64)
        return matrix

    def get_j21(self, x: Vec, dx: Vec, h: float) -> csc_matrix:
        """Declare no state dependence in the algebraic constraint.

        :param x: Candidate unknowns.
        :param dx: Candidate derivatives.
        :param h: Current effective step.
        :return: Empty one-by-one coupling block.
        """
        matrix: csc_matrix = csc_matrix((1, 1), dtype=np.float64)
        return matrix

    def get_j22(self, x: Vec, dx: Vec, h: float) -> csc_matrix:
        """Differentiate the declared scaled algebraic constraint.

        :param x: Candidate unknowns.
        :param dx: Candidate derivative context.
        :param h: Current effective step.
        :return: Algebraic derivative block at the supplied point.
        """
        value: float
        if self.confirmation_case:
            if 1.00994 <= float(x[1]) < 1.00996:
                value = 0.0
            else:
                value = self.row_scale * 2.0 * float(x[1])
        elif self.square_constraint:
            value = self.row_scale * 2.0 * float(x[1])
        else:
            value = self.row_scale * (1.0 + 3.0 * self.cubic * float(x[1]) ** 2)
        matrix: csc_matrix = csc_matrix(np.array(((value,),)))
        return matrix

    def get_j11_vec(self, h: float) -> csc_matrix:
        """Differentiate the gathered state equation.

        :param h: Current effective step.
        :return: State block in the vectorized consumer convention.
        """
        matrix: csc_matrix = self.get_j11(self._gathered, np.zeros(1), h)
        return matrix

    def get_j12_vec(self, h: float) -> csc_matrix:
        """Read the zero state-to-algebraic coupling in gathered order.

        :param h: Current effective step.
        :return: Declared empty coupling block.
        """
        matrix: csc_matrix = csc_matrix((1, 1), dtype=np.float64)
        return matrix

    def get_j21_vec(self, x: Vec | float, dx: Vec | None = None, h: float | None = None) -> csc_matrix:
        """Accept both existing vectorized gather call conventions.

        :param x: Candidate vector, or the step in the gathered-only convention.
        :param dx: Candidate derivatives when supplied by FullVec.
        :param h: Effective step when supplied by FullVec.
        :return: Zero coupling, independent of all supplied operands.
        """
        matrix: csc_matrix = csc_matrix((1, 1), dtype=np.float64)
        return matrix

    def get_j22_vec(self, x: Vec, dx: Vec, h: float) -> csc_matrix:
        """Bind the vectorized algebraic derivative to the canonical equation.

        :param x: Current candidate.
        :param dx: Derivative context.
        :param h: Effective substep size.
        :return: Matching algebraic derivative block.
        """
        matrix: csc_matrix = self.get_j22(x, dx, h)
        return matrix

    def update_input_matrices_by_model(self, x: Vec, dx: Vec) -> None:
        """Gather the candidate into fixed storage without changing equations.

        :param x: State and algebraic candidate.
        :param dx: Current derivative context.
        :return: None.
        """
        self._gathered[:] = x


    def update_variable_params(self, t: float, x_snapshot: Vec | None = None, scheduled_t: float | None = None) -> None:
        """Move only the synthetic RHS, with optional event and failure controls.

        :param t: Current target time.
        :param x_snapshot: Candidate snapshot, not mutated.
        :param scheduled_t: Prior accepted scheduling time.
        :return: None.
        """
        self.last_time = t
        if self.confirmation_case:
            if self.trace_derivatives:
                if t <= 1.0 / 64.0:
                    self._variable_parameters_values[0] = 1.0
                elif t <= 2.0 / 64.0:
                    self._variable_parameters_values[0] = 1.02
                else:
                    self._variable_parameters_values[0] = 1.04
            else:
                self._variable_parameters_values[0] = 1.0 if t == 0.0 else 1.02
        elif self.square_constraint:
            self._variable_parameters_values[0] = 1.0
        else:
            self._variable_parameters_values[0] = t
        if self.forced_time is not None and t >= self.forced_time:
            self._variable_parameters_values[0] += self.jump
        else:
            pass
        if self.reject_after is not None and t >= self.reject_after:
            if self.square_constraint:
                self._variable_parameters_values[0] = -1.0
            else:
                self._variable_parameters_values[0] = np.nan
        else:
            pass

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """Keep the synthetic boundary update explicit and non-mutating.

        :param t: Target time.
        :param x: Candidate unknowns.
        :param params: Already updated runtime parameters.
        :return: None.
        """
        self._gathered[:] = x

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> float | None:
        """Expose one exact event without advancing any external model.

        :param t_prev: Accepted local predecessor time.
        :param t_target: Macro target time.
        :return: The event when it lies in this accepted-to-target interval.
        """
        if self.forced_time is not None and t_prev < self.forced_time <= t_target:
            return self.forced_time
        else:
            return None

    def get_small_signal_reference_indices(self) -> tuple[int, int] | None:
        """Expose a declared reference identity for invalidation checks.

        :return: Optional reference coordinate, unused by this square system.
        """
        if self.reference_switch_time is not None and self.last_time >= self.reference_switch_time:
            return (0, 0)
        elif self.reference_column is None:
            return None
        else:
            return (0, self.reference_column)

    def initialize_fmu_cs_devices(self, x_snapshot: Vec, t: float = 0.0) -> None:
        """Reset the explicit Co-Simulation call counter.

        :param x_snapshot: Initial state.
        :param t: Start time.
        :return: None.
        """
        self.cs_advances = 0

    def initialize_fmu_me_devices(self, x_snapshot: Vec, t: float = 0.0) -> None:
        """Reset the explicit Model Exchange call counter.

        :param x_snapshot: Initial state.
        :param t: Start time.
        :return: None.
        """
        self.me_advances = 0
        self._history_count = 0

    def advance_fmu_cs_devices(self, t: float, x_snapshot: Vec, h: float) -> bool:
        """Count advances only when the declared synthetic CS list is nonempty.

        :param t: Accepted predecessor time.
        :param x_snapshot: Accepted predecessor state.
        :param h: Communication step.
        :return: Whether a synthetic CS device advanced.
        """
        if len(self._fmu_cs_adapters) > 0:
            self.cs_advances += 1
            return True
        else:
            return False

    def advance_fmu_me_devices(self, t: float, x_snapshot: Vec, h: float) -> None:
        """Record ME evaluations without introducing hidden mutable model state.

        :param t: Accepted predecessor time.
        :param x_snapshot: Candidate state.
        :param h: Current communication step.
        :return: None.
        """
        if len(self._fmu_me_adapters) > 0:
            self.me_advances += 1
        else:
            pass

    def prepare_fmu_me_state_event_retry(self) -> float | None:
        """Declare that this algebraic fixture has no external state events.

        :return: None; forced events are owned by the explicit time query.
        """
        event_time: float | None = None
        return event_time

    def resolve_fmu_me_devices(self, accepted: bool) -> float | None:
        """Keep ME boundary resolution explicit without external execution.

        :param accepted: Whether the numerical candidate passed.
        :return: No further localization request.
        """
        event_time: float | None = None
        return event_time

    def close_fmu_me_devices(self) -> None:
        """Leave the last gathered state available after synthetic ME closure.

        :return: None; no real FMU was instantiated.
        """
        self._gathered[:] = self._gathered

    def close_fmu_cs_devices(self) -> None:
        """Leave the last gathered state available after synthetic CS closure.

        :return: None; no real FMU was instantiated.
        """
        self._gathered[:] = self._gathered

    def resolve_manufacturer_native_boundary(self, t: float, x: Vec) -> None:
        """Count accepted callbacks without running a native controller.

        :param t: Accepted endpoint time.
        :param x: Accepted endpoint state.
        :return: None.
        """
        self.accepted_boundaries += 1

    def report_progress2(self, iteration: int, total: int) -> None:
        """Keep synthetic runs independent of any GUI or progress callback.

        :param iteration: Current macro index.
        :param total: Number of macro steps.
        :return: None.
        """
        pass


def build_rms_chord_solver(solver_class: type[BackEulerImplicitIntegration],
                           provider: SparseLinearSolverBackendProvider,
                           problem: RmsChordProblem, max_iter: int = 20) -> BackEulerImplicitIntegration:
    """Construct the actual consumer, keeping its default tolerance unchanged.

    :param solver_class: The unified RMS backward-Euler integrator.
    :param provider: Actual LU backend factory.
    :param problem: Complete synthetic problem-facing interface.
    :param max_iter: Per-attempt correction budget for recovery controls.
    :return: Actual solver instance for 32 binary-exact substeps.
    """
    solver: BackEulerImplicitIntegration = solver_class(
        problem=problem, t0=0.0, t_end=0.5, h=1.0 / 64.0, max_iter=max_iter,
        sparse_solver_backend_provider=provider)
    return solver


@pytest.mark.parametrize("solver_class", (BackEulerImplicitIntegration,))
@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba, SparseSolver.Pardiso))
def test_rms_constant_jacobian_reuses_all_backends(solver_class: type[BackEulerImplicitIntegration], solver_type: SparseSolver) -> None:
    """Require absolute cross-substep assembly/LU saving with analytic constraints.

    :param solver_class: Real RMS numerical consumer.
    :param solver_type: Real optional backend; unavailable means a reported skip.
    :return: None; each of 32 accepted intervals requires a numerical correction.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        problem: RmsChordProblem = RmsChordProblem()
        solver: BackEulerImplicitIntegration = build_rms_chord_solver(solver_class, provider, problem)
        times: Vec
        values: Mat
        initialized: bool
        converged: bool
        times, values, initialized, converged = solver.simulate()
        assert initialized and converged and times.shape[0] == 33
        expected: Vec = (1.0 + 1.0 / 64.0) ** (-np.arange(33))
        np.testing.assert_allclose(values[:, 0], expected, atol=1e-12, rtol=0.0)
        np.testing.assert_allclose(values[:, 1], times, atol=1e-12, rtol=0.0)
        assert solver._last_jacobian_evaluations <= 3
        assert solver._last_factorization_reuse_hits >= 31
        assert solver._sparse_linear_solver.get_stats()["numeric_factorizations"] + solver._sparse_linear_solver.get_stats()["numeric_refactorizations"] <= 3.0
        assert solver._sparse_linear_solver.get_stats()["solve_calls"] >= 32.0
        print("RMS_CHORD", solver_class.__module__, solver_type.name, solver._last_jacobian_evaluations,
              solver._last_factorization_reuse_hits, solver._last_confirming_corrections, solver._sparse_linear_solver.get_stats())


@pytest.mark.parametrize("solver_class", (BackEulerImplicitIntegration,))
def test_rms_empty_me_cs_mixed_eligibility(solver_class: type[BackEulerImplicitIntegration]) -> None:
    """Distinguish actual adapters from available no-op lifecycle methods.

    :param solver_class: Real numerical consumer.
    :return: None; external advances are never replayed by a chord retry.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    me_count: int
    cs_count: int
    for me_count, cs_count in ((0, 0), (1, 0), (0, 1), (1, 1)):
        problem: RmsChordProblem = RmsChordProblem()
        problem._fmu_me_adapters = list(object() for index in range(me_count))
        problem._fmu_cs_adapters = list(object() for index in range(cs_count))
        solver: BackEulerImplicitIntegration = build_rms_chord_solver(solver_class, provider, problem)
        result: tuple[Vec, Mat, bool, bool] = solver.simulate()
        assert result[3]
        if me_count + cs_count == 0:
            assert solver._last_jacobian_evaluations <= 3
        else:
            assert solver._last_jacobian_evaluations == 32
            assert solver._last_factorization_reuse_hits == 0
            assert solver._last_inherited_factor_retries == 0
        if cs_count > 0:
            assert problem.cs_advances == 32
        else:
            assert problem.cs_advances == 0


@pytest.mark.parametrize("solver_class", (BackEulerImplicitIntegration,))
def test_rms_repeated_run_resets_reuse(solver_class: type[BackEulerImplicitIntegration]) -> None:
    """Require a newly assembled J and identical values on a repeated run.

    :param solver_class: Real consumer retaining the same resident phase object.
    :return: None; neither candidate values nor eligibility may leak between runs.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem: RmsChordProblem = RmsChordProblem()
    solver: BackEulerImplicitIntegration = build_rms_chord_solver(solver_class, provider, problem)
    first: Mat = solver.simulate()[1].copy()
    second: Mat = solver.simulate()[1].copy()
    np.testing.assert_array_equal(first, second)
    assert solver._last_jacobian_evaluations >= 1
    assert solver._sparse_linear_solver.get_stats()["numeric_factorizations"] == 2.0


@pytest.mark.parametrize("solver_class", (BackEulerImplicitIntegration,))
@pytest.mark.parametrize("finite_failure", (False, True))
def test_rms_failed_retry_preserves_history(solver_class: type[BackEulerImplicitIntegration], finite_failure: bool) -> None:
    """A persistent non-finite residual rejects after exactly one fresh retry.

    :param solver_class: Actual consumer whose history must remain accepted-only.
    :param finite_failure: Try an impossible finite equation or reject before any correction.
    :return: None; returned arrays contain only the completed prefix.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem: RmsChordProblem = RmsChordProblem(square_constraint=finite_failure)
    problem.reject_after = 2.0 / 64.0
    solver: BackEulerImplicitIntegration = build_rms_chord_solver(solver_class, provider, problem)
    result: tuple[Vec, Mat, bool, bool] = solver.simulate()
    assert not result[3] and result[0].shape[0] == 2
    assert solver._last_inherited_factor_retries == (1 if finite_failure else 0)
    assert result[1][-1, 0] == pytest.approx(1.0 / (1.0 + 1.0 / 64.0), abs=1e-12)
    with pytest.raises(RuntimeError):
        solver._sparse_linear_solver.solve_retained(np.ones(2))


@pytest.mark.parametrize("solver_class", (BackEulerImplicitIntegration,))
def test_rms_confirmation_restores_derivative_context(solver_class: type[BackEulerImplicitIntegration]) -> None:
    """Restore a passing candidate when confirmation enters an invalid band.

    :param solver_class: One of the three driver-supported RMS consumers.
    :return: None; the accepted state matches the passing finite iterate.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem: RmsChordProblem = RmsChordProblem(row_scale=1e-4, confirmation_case=True, trace_derivatives=True)
    solver: BackEulerImplicitIntegration = solver_class(problem=problem, t0=0.0, t_end=3.0 / 64.0, h=1.0 / 64.0, max_iter=20,
        sparse_solver_backend_provider=provider)
    result: tuple[Vec, Mat, bool, bool] = solver.simulate()
    assert result[3] and result[0].shape[0] == 4
    assert result[1][2, 1] == pytest.approx(1.01, abs=1e-12)
    third_step: np.ndarray = np.flatnonzero(problem._history_trace[:problem._history_count, 0] == 3.0 / 64.0)
    assert third_step.size > 0 and problem._history_count < 128
    expected_history: float = float((result[1][2, 1] - result[1][1, 1]) / (1.0 / 64.0))
    # Without derivative rollback this input belongs to z=1.00995, not the accepted 1.01.
    assert problem._history_trace[int(third_step[0]), 1] == expected_history
    assert solver._last_confirming_corrections == 3


@pytest.mark.parametrize("solver_type", (SparseSolver.SuperLU, SparseSolver.KLU, SparseSolver.CLU, SparseSolver.CLU_Numba, SparseSolver.Pardiso))
def test_rms_gauge_rhs_scaling(solver_type: SparseSolver) -> None:
    """Keep original augmentation and row/column scaling with retained LU.

    :param solver_type: Actual provider selected for the transformed square matrix.
    :return: None; both changing RHS vectors satisfy the original raw equations.
    """
    provider: SparseLinearSolverBackendProvider | None
    reason: str
    provider, reason = get_sparse_lu_provider_status(solver_type)
    if provider is None:
        pytest.skip(reason)
    else:
        phase: SparseProviderLinearSolver = SparseProviderLinearSolver(provider)
        matrix: csc_matrix = csc_matrix(np.array(((2e3, -1e3, 0.0), (-1e3, 2e3, -1e-2))))
        residual: Vec = np.array((1.5e-3, -2.5e-6))
        first: Vec = solve_rms_newton_correction(matrix, residual, 0, provider, phase)
        second: Vec = solve_rms_newton_correction(matrix, 2.0 * residual, 0, provider, phase)
        np.testing.assert_allclose(matrix @ second, -2.0 * residual, atol=1e-12, rtol=0.0)
        np.testing.assert_allclose(second, 2.0 * first, atol=1e-12, rtol=0.0)
        assert second[0] == 0.0
        assert phase.get_stats()["numeric_factorizations"] == 1.0


@pytest.mark.parametrize("solver_class", (BackEulerImplicitIntegration,))
def test_rms_event_step_and_reference_invalidation(solver_class: type[BackEulerImplicitIntegration]) -> None:
    """Invalidate split-step inputs and independently changed reference identity.

    :param solver_class: Actual numerical consumer.
    :return: None; changed RHS is solved after both invalidation causes.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem: RmsChordProblem = RmsChordProblem()
    problem.forced_time = 13.0 / 128.0
    problem.jump = 0.25
    solver: BackEulerImplicitIntegration = build_rms_chord_solver(solver_class, provider, problem)
    result: tuple[Vec, Mat, bool, bool] = solver.simulate()
    assert result[3]
    expected: Vec = result[0].copy()
    expected[result[0] >= problem.forced_time] += problem.jump
    np.testing.assert_allclose(result[1][:, 1], expected, atol=1e-12, rtol=0.0)
    assert solver._last_forced_factorization_invalidations == 2
    reference_problem: RmsChordProblem = RmsChordProblem()
    reference_problem.reference_switch_time = 0.125
    reference_solver: BackEulerImplicitIntegration = build_rms_chord_solver(solver_class, provider, reference_problem)
    assert reference_solver.simulate()[3]
    assert reference_solver._last_forced_factorization_invalidations == 1


@pytest.mark.parametrize("solver_class", (BackEulerImplicitIntegration,))
def test_rms_nonlinear_refresh_and_retry(solver_class: type[BackEulerImplicitIntegration]) -> None:
    """Exercise real nonlinear refresh at the fixed default tolerance.

    :param solver_class: Actual numerical consumer.
    :return: None; accepted constraints and analytic state remain satisfied.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem: RmsChordProblem = RmsChordProblem(10.0)
    solver: BackEulerImplicitIntegration = build_rms_chord_solver(solver_class, provider, problem, max_iter=2)
    result: tuple[Vec, Mat, bool, bool] = solver.simulate()
    print("RMS_RECOVERY", solver_class.__module__, result[3], solver._last_inherited_factor_retries, solver._last_jacobian_evaluations)
    # The pre-existing fresh-J route is an independent control for budget sufficiency.
    legacy_problem: RmsChordProblem = RmsChordProblem(10.0)
    legacy_problem._fmu_me_adapters = list((object(),))
    legacy_solver: BackEulerImplicitIntegration = build_rms_chord_solver(solver_class, provider, legacy_problem, max_iter=2)
    legacy_result: tuple[Vec, Mat, bool, bool] = legacy_solver.simulate()
    print("RMS_LEGACY_CONTROL", solver_class.__module__, legacy_result[3],
          legacy_result[0].shape[0], legacy_solver._last_jacobian_evaluations,
          legacy_solver.tol, legacy_solver.max_iter_0, legacy_result[1].tolist())
    # Both routes must keep the original limit, including its later legitimate rejection.
    assert result[3] == legacy_result[3]
    np.testing.assert_array_equal(result[0], legacy_result[0])
    assert result[0].shape[0] == 4
    assert solver.tol == legacy_solver.tol and solver.max_iter_0 == legacy_solver.max_iter_0 == 2
    algebraic: Vec = result[1][:, 1]
    assert np.max(np.abs(algebraic + 10.0 * algebraic ** 3 - result[0])) < solver.tol
    legacy_algebraic: Vec = legacy_result[1][:, 1]
    assert np.max(np.abs(legacy_algebraic + 10.0 * legacy_algebraic ** 3 - legacy_result[0])) < legacy_solver.tol
    state_defect: Vec = result[1][1:, 0] - result[1][:-1, 0] + (1.0 / 64.0) * result[1][1:, 0]
    assert np.max(np.abs(state_defect)) < solver.tol
    assert result[0][1] == 1.0 / 64.0
    assert solver._last_jacobian_evaluations > 1
    assert 0 < solver._last_inherited_factor_retries <= result[0].shape[0]


@pytest.mark.parametrize("solver_class", (BackEulerImplicitIntegration,))
def test_rms_cancel_preserves_completed_prefix(solver_class: type[BackEulerImplicitIntegration]) -> None:
    """Cancel through the existing constructor callback after two steps.

    :param solver_class: Real consumer with its unchanged cancellation API.
    :return: None; resident eligibility is revoked at the cancellation boundary.
    """
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem: RmsChordProblem = RmsChordProblem()
    solver: BackEulerImplicitIntegration = solver_class(problem=problem, t0=0.0, t_end=0.5, h=1.0 / 64.0, max_iter=20,
        cancel_checker=iter((False, False, True)).__next__, sparse_solver_backend_provider=provider)
    result: tuple[Vec, Mat, bool, bool] = solver.simulate()
    assert result[0].shape[0] == 3 and solver._last_jacobian_evaluations == 1
    with pytest.raises(RuntimeError):
        solver._sparse_linear_solver.solve_retained(np.ones(2))


def _failing_direct_correction(**kwargs: object) -> Vec:
    """Stand-in direct RMS correction that always fails, so only the regularized fallback can solve.

    :param kwargs: Arguments of solve_rms_newton_correction.
    :return: Never returns.
    """
    raise RuntimeError("direct solve unavailable")


def test_rms_fallback_solve_drops_the_fresh_factors(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the direct solve of a fresh Jacobian fails and the regularized fallback succeeds, nothing is reused.

    :param monkeypatch: Replaces the direct correction with a failing stand-in.
    :return: None.
    """
    monkeypatch.setattr(back_euler_fx, "solve_rms_newton_correction", _failing_direct_correction)
    provider: SparseLinearSolverBackendProvider = SuperLUSparseBackendProvider()
    problem: RmsChordProblem = RmsChordProblem()
    solver: BackEulerImplicitIntegration = build_rms_chord_solver(BackEulerImplicitIntegration, provider, problem)
    result: tuple[Vec, Mat, bool, bool] = solver.simulate()
    assert result[3]
    assert solver._last_factorization_reuse_hits == 0
    assert solver._last_inherited_factor_retries == 0

