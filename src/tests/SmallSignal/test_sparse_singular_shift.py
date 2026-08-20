from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_driver import (
    compute_state_matrix,
    run_sparse_small_signal_stability,
)
from VeraGridEngine.basic_structures import Vec


class SingularStandardSmallSignalProblem:
    """
    Minimal standard RMS problem containing one exact zero mode.
    """

    __slots__ = ("matrix",)

    def __init__(self) -> None:
        """
        Initialize a diagonal state matrix with one singular eigenvalue.

        :return: None.
        """
        self.matrix: sp.csc_matrix = sp.diags(
            np.array([0.0, -1.0, -2.0, -3.0, -4.0], dtype=float),
            format="csc",
        )

    def get_static_state_matrix(self, x: Vec, dx: Vec) -> sp.csc_matrix:
        """
        Return the singular augmented matrix.

        :param x: Unused state point.
        :param dx: Unused derivative point.
        :return: Singular CSC state matrix.
        """
        return self.matrix

    def get_diff_var_number(self) -> int:
        """
        Return the standard, non-generalized problem marker.

        :return: Zero differential-variable nodes.
        """
        return 0

    def get_states_number(self) -> int:
        """
        Return the number of state variables.

        :return: State-matrix dimension.
        """
        return self.matrix.shape[0]

    def get_small_signal_reference_indices(self) -> tuple[int, int] | None:
        """
        Return no electrical angle gauge for the state-only fixture.

        :return: ``None`` because the matrix contains no algebraic variables.
        """
        return None


class AlgebraicallySingularStandardSmallSignalProblem:
    """
    Minimal augmented problem whose algebraic block has one gauge freedom.
    """

    __slots__ = ("matrix",)

    def __init__(self) -> None:
        """
        Initialize three states and two algebraic variables with one null row.

        :return: None.
        """
        self.matrix: sp.csc_matrix = sp.diags(
            np.array([-1.0, -2.0, -3.0, 0.0, 1.0], dtype=float),
            format="csc",
        )

    def get_static_state_matrix(self, x: Vec, dx: Vec) -> sp.csc_matrix:
        """
        Return the algebraically singular augmented matrix.

        :param x: Unused state point.
        :param dx: Unused derivative point.
        :return: Singular CSC augmented matrix.
        """
        return self.matrix

    def get_diff_var_number(self) -> int:
        """
        Return the standard, non-generalized problem marker.

        :return: Zero differential-variable nodes.
        """
        return 0

    def get_states_number(self) -> int:
        """
        Return the differential-state subspace size.

        :return: Three state variables.
        """
        return 3

    def get_small_signal_reference_indices(self) -> tuple[int, int] | None:
        """
        Return no explicit gauge constraint for the structural-defect fixture.

        :return: ``None`` so the general regularization fallback is exercised.
        """
        return None


class AngleGaugeStandardSmallSignalProblem:
    """
    Minimal augmented problem with an exact electrical angle gauge.
    """

    __slots__ = ("matrix",)

    def __init__(self) -> None:
        """
        Initialize three states and a rank-one two-angle algebraic block.

        :return: None.
        """
        state_matrix: sp.csc_matrix = sp.diags(
            np.array([-1.0, -2.0, -3.0], dtype=float),
            format="csc",
        )
        angle_block: sp.csc_matrix = sp.csc_matrix(
            np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=float),
        )
        self.matrix: sp.csc_matrix = sp.block_diag((state_matrix, angle_block), format="csc")

    def get_static_state_matrix(self, x: Vec, dx: Vec) -> sp.csc_matrix:
        """
        Return the numerically singular augmented matrix.

        :param x: Unused state point.
        :param dx: Unused derivative point.
        :return: Singular CSC augmented matrix.
        """
        return self.matrix

    def get_diff_var_number(self) -> int:
        """
        Return the standard, non-generalized problem marker.

        :return: Zero differential-variable nodes.
        """
        return 0

    def get_states_number(self) -> int:
        """
        Return the differential-state subspace size.

        :return: Three state variables.
        """
        return 3

    def get_small_signal_reference_indices(self) -> tuple[int, int] | None:
        """
        Select the first angle equation and variable as the numerical gauge.

        :return: Augmented-matrix reference row and column.
        """
        return 3, 3


class DenseAngleGaugeSmallSignalProblem:
    """
    Minimal dense-path DAE whose algebraic Jacobian has an angle gauge.
    """

    __slots__ = ("state_jacobian", "state_to_algebraic", "algebraic_to_state", "algebraic_jacobian")

    def __init__(self) -> None:
        """
        Initialize one state and two gauge-equivalent algebraic angles.

        :return: None.
        """
        self.state_jacobian: sp.csc_matrix = sp.csc_matrix(np.array([[-2.0]], dtype=float))
        self.state_to_algebraic: sp.csc_matrix = sp.csc_matrix(np.zeros((1, 2), dtype=float))
        self.algebraic_to_state: sp.csc_matrix = sp.csc_matrix(np.zeros((2, 1), dtype=float))
        self.algebraic_jacobian: sp.csc_matrix = sp.csc_matrix(
            np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=float),
        )

    def get_dt_value(self) -> float:
        """
        Return the arbitrary linearization step used by the fixture.

        :return: Unit time step.
        """
        return 1.0

    def get_j11(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Return the state Jacobian."""
        return self.state_jacobian

    def get_j12(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Return the state-to-algebraic Jacobian."""
        return self.state_to_algebraic

    def get_j21(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Return the algebraic-to-state Jacobian."""
        return self.algebraic_to_state

    def get_j22(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        """Return the exactly singular algebraic Jacobian."""
        return self.algebraic_jacobian

    def get_diff_var_number(self) -> int:
        """Return zero explicit differential variables."""
        return 0

    def get_states_number(self) -> int:
        """Return one state variable."""
        return 1

    def get_small_signal_reference_indices(self) -> tuple[int, int] | None:
        """Return the augmented reference row and column."""
        return 1, 1


def test_sparse_standard_solver_shifts_exact_zero_mode() -> None:
    """
    Verify sparse shift-invert retries away from a singular zero shift.

    :return: None.
    """
    problem: SingularStandardSmallSignalProblem = SingularStandardSmallSignalProblem()
    empty_point: Vec = np.zeros(5, dtype=float)

    (eigenvalues,
     right_eigenvectors,
     participation_factors,
     damping_ratios,
     conjugate_frequencies,
     state_matrix,
     reduced_state_matrix) = run_sparse_small_signal_stability(
        problem=problem,
        x=empty_point,
        dx=empty_point,
        k=1,
        verbose=0,
    )

    assert eigenvalues.shape == (1,)
    assert np.isclose(eigenvalues[0], 0.0, atol=1.0e-7)
    assert right_eigenvectors.shape == (5, 1)
    assert participation_factors.shape == (5, 1)
    assert damping_ratios.shape == (1,)
    assert conjugate_frequencies.shape == (1,)
    assert state_matrix.size == 0
    assert reduced_state_matrix is None


def test_sparse_standard_solver_regularizes_algebraic_gauge() -> None:
    """
    Verify sparse shift-invert falls back when only the algebraic block is singular.

    :return: None.
    """
    problem: AlgebraicallySingularStandardSmallSignalProblem = AlgebraicallySingularStandardSmallSignalProblem()
    empty_point: Vec = np.zeros(5, dtype=float)

    eigenvalues, right_eigenvectors, participation_factors, _, _, _, _ = run_sparse_small_signal_stability(
        problem=problem,
        x=empty_point,
        dx=empty_point,
        k=1,
        verbose=0,
    )

    assert eigenvalues.shape == (1,)
    assert np.isclose(eigenvalues[0], -1.0, atol=1.0e-6)
    assert right_eigenvectors.shape == (3, 1)
    assert participation_factors.shape == (3, 1)


def test_sparse_standard_solver_fixes_exact_angle_gauge() -> None:
    """
    Verify the slack-angle row removes a numerical network gauge singularity.

    :return: None.
    """
    problem: AngleGaugeStandardSmallSignalProblem = AngleGaugeStandardSmallSignalProblem()
    empty_point: Vec = np.zeros(5, dtype=float)

    eigenvalues, right_eigenvectors, participation_factors, _, _, _, _ = run_sparse_small_signal_stability(
        problem=problem,
        x=empty_point,
        dx=empty_point,
        k=1,
        verbose=0,
    )

    assert eigenvalues.shape == (1,)
    assert np.isclose(eigenvalues[0], -1.0, atol=1.0e-7)
    assert right_eigenvectors.shape == (3, 1)
    assert participation_factors.shape == (3, 1)


def test_dense_state_matrix_fixes_exact_angle_gauge_after_lu_failure() -> None:
    """
    Verify dense reduction retries a singular algebraic block with the slack reference.

    :return: None.
    """
    problem: DenseAngleGaugeSmallSignalProblem = DenseAngleGaugeSmallSignalProblem()
    empty_point: Vec = np.zeros(3, dtype=float)

    balanced_matrix, original_matrix = compute_state_matrix(
        problem=problem,
        x=empty_point,
        dx=empty_point,
    )

    assert balanced_matrix.shape == (1, 1)
    assert original_matrix.shape == (1, 1)
    assert np.isclose(balanced_matrix[0, 0], -2.0)
    assert np.isclose(original_matrix[0, 0], -2.0)


def test_dense_state_matrix_reports_when_gauge_fix_cannot_make_gy_invertible() -> None:
    """
    Verify an irreducible algebraic singularity recommends the sparse DAE path.

    :return: None.
    """
    problem: DenseAngleGaugeSmallSignalProblem = DenseAngleGaugeSmallSignalProblem()
    problem.algebraic_jacobian = sp.csc_matrix(np.zeros((2, 2), dtype=float))
    empty_point: Vec = np.zeros(3, dtype=float)

    with pytest.raises(RuntimeError, match="Select a positive number of modes"):
        compute_state_matrix(
            problem=problem,
            x=empty_point,
            dx=empty_point,
        )
