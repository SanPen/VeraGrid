# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Fixed-pattern assembly of the scalar RMS Backward Euler implicit Jacobian, compared bit for bit with the SciPy expression."""

from __future__ import annotations

import time

import numpy as np
import pytest
import scipy.sparse as sp
from scipy.sparse import csc_matrix, csr_matrix

import VeraGridEngine.api as gce
from tests.Base.test_dynamic_results_save_load import _build_rms_driver
from tests.Base.test_load_save_load_dynamic_versions import _build_dynamic_version_power_flow_options
from tests.RMS.test_simulation_with_event import find_name_in_block
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.jacobian_assembler import (
    JacobianAssembler,
    _csc_storage_is_consistent,
)
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.rms_driver import RmsSimulationDriver
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Utils.Sparse.csc import pack_4_by_4_scipy
from VeraGridEngine.basic_structures import Mat, Vec
from VeraGridEngine.enumerations import DynamicIntegrationMethod, RmsInitializationMethod


class SparseReferenceBackEuler(BackEulerImplicitIntegration):
    """Independent SciPy assembly of the raw Jacobian partials."""

    __slots__ = ()

    def _jacobian_implicit(self, x: Vec, dx: Vec, h: float) -> sp.csc_matrix:
        j11, j12, j13, j21, j22, j23 = self.problem.evaluate_jacobian_partials(x, dx)
        bases = []
        for derivative in self.problem.get_diff_vars():
            base = derivative
            while base.base_var is not None:
                base = base.base_var
            bases.append(self.problem.uid2idx_vars[base.uid])
        orders = self.problem.get_diff_var_orders()
        chain = sp.csc_matrix((h ** (-orders.astype(float)),
                               (np.arange(len(bases)), bases)),
                              shape=(len(bases), self.problem.get_all_vars_number()))
        raw = sp.bmat([[j11, j12], [j21, j22]], format="csc")
        projected = raw + sp.vstack([j13, j23], format="csc") @ chain
        ns = self.problem.get_states_number()
        return _reference_expression(ns, h, projected[:ns, :ns],
                                     projected[:ns, ns:], projected[ns:, :ns],
                                     projected[ns:, ns:])


def _reference_expression(ns: int, h: float, j11: sp.spmatrix, j12: sp.spmatrix, j21: sp.spmatrix, j22: sp.spmatrix) -> csc_matrix:
    """
    Evaluate the HEAD assembly expression that the assembler replaces.

    :param ns: Number of states.
    :param h: Integration step.
    :param j11: State/state block.
    :param j12: State/algebraic block.
    :param j21: Algebraic/state block.
    :param j22: Algebraic/algebraic block.
    :return: Packed matrix.
    """
    identity: sp.dia_matrix = sp.eye(m=ns, n=ns)
    return pack_4_by_4_scipy((identity - h * j11).tocsc(), - h * j12, j21, j22)


def _assert_identical(result: csc_matrix, reference: csc_matrix) -> None:
    """
    Assert identical canonical pattern, int32 index arrays and identical value bits.

    :param result: Matrix from the assembler.
    :param reference: Matrix from the reference expression.
    :return: None.
    """
    assert result.indices.dtype == np.int32 and result.indptr.dtype == np.int32
    assert result.data.dtype == np.float64
    left: csc_matrix = result.copy()
    right: csc_matrix = reference.copy()
    left.sort_indices()
    right.sort_indices()
    assert left.shape == right.shape
    assert np.array_equal(left.indptr, right.indptr)
    assert np.array_equal(left.indices, right.indices)
    assert np.array_equal(left.data.view(np.int64), right.data.view(np.int64))


def _random_block(n_rows: int, n_cols: int, seed: int, density: float) -> csc_matrix:
    """
    Build a canonical CSC block with non-zero float64 values.

    :param n_rows: Number of rows.
    :param n_cols: Number of columns.
    :param seed: Random seed.
    :param density: Fraction of stored entries.
    :return: Canonical CSC block.
    """
    generator: np.random.Generator = np.random.default_rng(seed)
    block: csc_matrix = sp.random(n_rows, n_cols, density=density, random_state=seed, format="csc", dtype=np.float64)
    block.data[:] = generator.uniform(0.5, 2.0, block.nnz) * generator.choice(np.array([-1.0, 1.0]), block.nnz)
    block.sort_indices()
    return block


def _assemble_and_compare(assembler: JacobianAssembler, ns: int, h: float, j11: sp.spmatrix, j12: sp.spmatrix,
                          j21: sp.spmatrix, j22: sp.spmatrix) -> csc_matrix:
    """
    Assemble with the assembler, compare with the reference expression and return the result.

    :param assembler: Assembler under test.
    :param ns: Number of states.
    :param h: Integration step.
    :param j11: State/state block.
    :param j12: State/algebraic block.
    :param j21: Algebraic/state block.
    :param j22: Algebraic/algebraic block.
    :return: Assembled matrix.
    """
    reference: csc_matrix = _reference_expression(ns, h, j11, j12, j21, j22)
    result: csc_matrix = assembler.assemble_jacobian_implicit(ns, h, j11, j12, j21, j22)
    _assert_identical(result, reference)
    return result


def _small_blocks() -> tuple[csc_matrix, csc_matrix, csc_matrix, csc_matrix]:
    """
    Build small deterministic blocks: 3 states, 2 algebraic variables, J11 without a diagonal entry in column 2.

    :return: J11, J12, J21 and J22.
    """
    j11: csc_matrix = csc_matrix(np.array([[2.0, 0.5, 0.0], [0.0, -1.5, 0.25], [0.75, 0.0, 0.0]]))
    j12: csc_matrix = csc_matrix(np.array([[0.0, 1.0], [-2.0, 0.0], [0.5, 0.5]]))
    j21: csc_matrix = csc_matrix(np.array([[1.0, 0.0, -1.0], [0.0, 3.0, 0.0]]))
    j22: csc_matrix = csc_matrix(np.array([[4.0, 1.0], [1.0, 5.0]]))
    return j11, j12, j21, j22


def test_random_canonical_blocks_use_the_fast_path() -> None:
    """
    Random canonical blocks, including empty J12 or J21 and missing J11 diagonal entries, are identical on the fast path.

    :return: None.
    """
    seed: int
    for seed in range(6):
        assembler: JacobianAssembler = JacobianAssembler()
        ns: int = 4 + seed
        na: int = 3 + seed
        j11: csc_matrix = _random_block(ns, ns, seed, 0.3)
        j12: csc_matrix = _random_block(ns, na, seed + 10, 0.3) if seed % 3 != 1 else csc_matrix((ns, na), dtype=np.float64)
        j21: csc_matrix = _random_block(na, ns, seed + 20, 0.3) if seed % 3 != 2 else csc_matrix((na, ns), dtype=np.float64)
        j22: csc_matrix = _random_block(na, na, seed + 30, 0.5)
        h: float
        for h in (1.0e-3, 2.5e-2, 0.1):
            _assemble_and_compare(assembler, ns, h, j11, j12, j21, j22)
        assert assembler.get_pattern_build_count() == 1
        assert assembler.get_fast_assembly_count() == 3
        assert assembler.get_fallback_assembly_count() == 0


def test_zero_in_the_identity_block_falls_back() -> None:
    """
    An explicit zero off-diagonal J11 value, or a diagonal with h*J11_ii == 1, uses the SciPy expression, whose pattern drops it.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    assembler: JacobianAssembler = JacobianAssembler()
    j11.data[1] = 0.0
    result: csc_matrix = _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    assert result.nnz == _reference_expression(3, 0.01, j11, j12, j21, j22).nnz
    j11.data[1] = 0.75
    j11.data[0] = 4.0
    _assemble_and_compare(assembler, 3, 0.25, j11, j12, j21, j22)
    assert assembler.get_fallback_assembly_count() == 2
    assert assembler.get_fast_assembly_count() == 0


def test_nan_and_infinite_values_keep_their_bits() -> None:
    """
    NaN (with its sign) and infinite J11 values give the same bits as the SciPy subtraction.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    j11.data[0] = np.copysign(np.nan, -1.0)
    j11.data[1] = np.inf
    j11.data[2] = -np.inf
    j11.data[3] = np.nan
    assembler: JacobianAssembler = JacobianAssembler()
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    assert assembler.get_fast_assembly_count() == 1


def test_explicit_zeros_outside_the_identity_block_use_the_fast_path() -> None:
    """
    Explicit zeros in J12 (giving -0.0), J21 and J22 are kept with their sign on the fast path.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    j12.data[0] = 0.0
    j21.data[0] = 0.0
    j22.data[0] = -0.0
    assembler: JacobianAssembler = JacobianAssembler()
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    assert assembler.get_fast_assembly_count() == 1


def test_non_canonical_or_other_format_blocks_fall_back() -> None:
    """
    Duplicate entries, unsorted indices, storage longer than indptr[-1] and a CSR J11 use the SciPy expression.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    duplicated: csc_matrix = csc_matrix((np.array([1.0, 2.0, 3.0]), np.array([0, 0, 1]), np.array([0, 2, 3])), shape=(2, 2))
    unsorted: csc_matrix = csc_matrix((np.array([1.0, 2.0, 3.0]), np.array([1, 0, 1]), np.array([0, 2, 3])), shape=(2, 2))
    longer: csc_matrix = j22.copy()
    # Shorten the last column in place so the value and index arrays hold one entry more than indptr[-1].
    longer.indptr[-1] -= 1
    assembler: JacobianAssembler = JacobianAssembler()
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, duplicated)
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, unsorted)
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, longer)
    _assemble_and_compare(assembler, 3, 0.01, csr_matrix(j11), j12, j21, j22)
    assert assembler.get_fast_assembly_count() == 0
    assert assembler.get_fallback_assembly_count() == 4


def test_wrong_length_indptr_is_not_consistent_storage() -> None:
    """
    An indptr whose length is not columns + 1 is rejected by the storage check (it cannot be built through SciPy).

    :return: None.
    """
    assert not _csc_storage_is_consistent(np.array([0, 1]), np.array([0]), np.array([1.0]), (2, 2))
    assert not _csc_storage_is_consistent(np.array([1, 1, 1]), np.array([0]), np.array([1.0]), (2, 2))
    assert _csc_storage_is_consistent(np.array([0, 1, 1]), np.array([0]), np.array([1.0]), (2, 2))


def test_non_csc_off_diagonal_blocks_raise_like_today() -> None:
    """
    A CSR J12, J21 or J22 raises the AssertionError of pack_4_by_4_scipy, as the replaced expression does.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    assembler: JacobianAssembler = JacobianAssembler()
    with pytest.raises(AssertionError):
        _reference_expression(3, 0.01, j11, csr_matrix(j12), j21, j22)
    with pytest.raises(AssertionError):
        assembler.assemble_jacobian_implicit(3, 0.01, j11, csr_matrix(j12), j21, j22)
    with pytest.raises(AssertionError):
        assembler.assemble_jacobian_implicit(3, 0.01, j11, j12, csr_matrix(j21), j22)
    with pytest.raises(AssertionError):
        assembler.assemble_jacobian_implicit(3, 0.01, j11, j12, j21, csr_matrix(j22))


def test_zero_algebraic_dimension_and_non_square_j22() -> None:
    """
    Blocks with no algebraic variables and a non-square J22 (rows + 1 == columns) are identical.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    assembler: JacobianAssembler = JacobianAssembler()
    _assemble_and_compare(assembler, 3, 0.01, j11, csc_matrix((3, 0), dtype=np.float64), csc_matrix((0, 3), dtype=np.float64),
                          csc_matrix((0, 0), dtype=np.float64))
    _assemble_and_compare(JacobianAssembler(), 3, 0.01, j11, _random_block(3, 3, 7, 0.5), j21,
                          _random_block(2, 3, 8, 0.6))


def test_pattern_changes_rebuild() -> None:
    """
    An alternating J11 pattern and an in-place rewrite of J11 indices to another canonical pattern rebuild the maps.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    other: csc_matrix = csc_matrix(np.array([[2.0, 0.0, 0.0], [0.5, -1.5, 0.25], [0.0, 0.0, 1.0]]))
    assembler: JacobianAssembler = JacobianAssembler()
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    _assemble_and_compare(assembler, 3, 0.01, other, j12, j21, j22)
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    assert assembler.get_pattern_build_count() == 3
    # Column 0 of J11 stores rows (0, 2); rewriting row 2 to row 1 in place keeps a canonical pattern.
    j11.indices[1] = 1
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    assert assembler.get_pattern_build_count() == 4
    assert assembler.get_fast_assembly_count() == 4


def test_in_place_rewrite_to_non_canonical_falls_back() -> None:
    """
    After a fast-path call, rewriting J11 indices in place into duplicates, or out of range, uses the SciPy expression.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    assembler: JacobianAssembler = JacobianAssembler()
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    # Column 0 of J11 stores rows (0, 2); making both 0 creates a duplicate entry on the same object.
    j11.indices[1] = 0
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    assert assembler.get_fast_assembly_count() == 1
    assert assembler.get_fallback_assembly_count() == 1


def test_malformed_blocks_fall_back_like_today() -> None:
    """
    A decreasing indptr or an out-of-range row index falls back and behaves exactly like the replaced expression.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    # J21 has three columns with indptr (0, 1, 2, 3); lowering the third pointer makes indptr decrease.
    decreasing: csc_matrix = j21.copy()
    decreasing.indptr[2] = 0
    out_of_range: csc_matrix = j21.copy()
    out_of_range.indices[0] = 7
    malformed: csc_matrix
    for malformed in (decreasing, out_of_range):
        assembler: JacobianAssembler = JacobianAssembler()
        reference_error: type | None = None
        reference: csc_matrix | None = None
        try:
            reference = _reference_expression(3, 0.01, j11, j12, malformed, j22)
        except (ValueError, IndexError, AssertionError) as error:
            reference_error = type(error)
        if reference_error is None and reference is not None:
            _assert_identical(assembler.assemble_jacobian_implicit(3, 0.01, j11, j12, malformed, j22), reference)
        else:
            with pytest.raises(reference_error):
                assembler.assemble_jacobian_implicit(3, 0.01, j11, j12, malformed, j22)
        assert assembler.get_fast_assembly_count() == 0


def test_fast_fallback_fast_sequence_on_the_same_objects() -> None:
    """
    A zero-triggered fallback between two fast-path calls on the same objects leaves the pattern valid.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    assembler: JacobianAssembler = JacobianAssembler()
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    saved: float = float(j11.data[1])
    j11.data[1] = 0.0
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    j11.data[1] = saved
    _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    assert assembler.get_pattern_build_count() == 1
    assert assembler.get_fast_assembly_count() == 2
    assert assembler.get_fallback_assembly_count() == 1


def test_returned_matrices_are_independent_and_canonical() -> None:
    """
    Mutating a returned matrix does not change the next result; results are canonical float64 with int32 indices.

    :return: None.
    """
    j11: csc_matrix
    j12: csc_matrix
    j21: csc_matrix
    j22: csc_matrix
    j11, j12, j21, j22 = _small_blocks()
    assembler: JacobianAssembler = JacobianAssembler()
    first: csc_matrix = assembler.assemble_jacobian_implicit(3, 0.01, j11, j12, j21, j22)
    assert first.has_canonical_format
    first.data[:] = 99.0
    first.indices[:] = 0
    second: csc_matrix = _assemble_and_compare(assembler, 3, 0.01, j11, j12, j21, j22)
    assert not np.shares_memory(first.data, second.data)


def test_zero_states_fall_back() -> None:
    """
    ns == 0 uses the SciPy expression and gives the same matrix.

    :return: None.
    """
    assembler: JacobianAssembler = JacobianAssembler()
    j22: csc_matrix = _random_block(3, 3, 5, 0.6)
    _assemble_and_compare(assembler, 0, 0.01, csc_matrix((0, 0), dtype=np.float64), csc_matrix((0, 3), dtype=np.float64),
                          csc_matrix((3, 0), dtype=np.float64), j22)
    assert assembler.get_fallback_assembly_count() == 1


def _two_bus_problem() -> tuple[RmsProblemDae, RmsOptions]:
    """
    Build a fresh RMS problem of the Base 2-bus system with its load event.

    :return: Problem ready for simulation and the options of the Base driver.
    """
    driver: RmsSimulationDriver = _build_rms_driver()
    grid: MultiCircuit = driver.grid
    problem: RmsProblemDae = RmsProblemDae(grid=grid, options=driver.options, pf_results=driver.pf_results)
    problem.set_events_group(grid.rms_events_groups[0])
    problem.reset_boundary_update_state(0.0)
    return problem, driver.options


def _kundur_problem(options: RmsOptions) -> RmsProblemDae:
    """
    Build a fresh Kundur RMS problem with a 10 percent step of the first load's Pl0 at 0.1 s.

    The archive is opened relative to the working directory set by the test conftest (src/tests).

    :param options: RMS options of the run.
    :return: Problem ready for simulation.
    """
    grid: MultiCircuit = gce.open_file("data/dynamic_versions/kundur_rms_6_5_29.veragrid")
    group: RmsEventsGroup = RmsEventsGroup(name="load step")
    grid.add_rms_events_group(group)
    load: gce.Load = grid.get_loads()[0]
    grid.add_rms_event(RmsEvent(device=load, parameter=find_name_in_block("Pl0", load.rms_model), time=0.1,
                                value=-1.1 * load.P / grid.Sbase, group=group))
    power_flow: PowerFlowDriver = PowerFlowDriver(grid=grid, options=_build_dynamic_version_power_flow_options())
    power_flow.run()
    problem: RmsProblemDae = RmsProblemDae(grid=grid, options=options, pf_results=power_flow.results)
    problem.set_events_group(group)
    problem.reset_boundary_update_state(0.0)
    return problem


def _simulate(solver: BackEulerImplicitIntegration) -> Mat:
    """
    Run a solver and return its trajectory after checking convergence.

    :param solver: Solver to run.
    :return: State trajectory.
    """
    t: Vec
    y: Mat
    well_initialized: bool
    converged: bool
    t, y, well_initialized, converged = solver.simulate()
    assert well_initialized and converged
    return y


def test_solver_jacobian_matches_the_replaced_expression() -> None:
    """
    On the Base 2-bus system, compare the solver with independent sparse assembly.

    :return: None.
    """
    problem: RmsProblemDae
    options: RmsOptions
    problem, options = _two_bus_problem()
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(problem=problem, t0=0, t_end=0.2, h=options.time_step,
                                                                        max_iter=options.max_iter, tolerance=options.tolerance)
    y: Mat = _simulate(solver)
    dx: Vec = np.zeros(y.shape[1])
    row: int
    for row in (0, 100, 150, y.shape[0] - 1):
        h: float
        for h in (1.0e-3, 5.0e-4):
            x: Vec = y[row].copy()
            reference = SparseReferenceBackEuler._jacobian_implicit(solver, x, dx, h)
            np.testing.assert_allclose(solver._jacobian_implicit(x, dx, h).toarray(),
                                       reference.toarray(), rtol=1e-12, atol=1e-12)


def test_bdf_jacobian_uses_current_derivative_coefficient() -> None:
    """BDF1/BDF2 coefficients change only the state diagonal of the DAE matrix."""
    j11 = sp.csc_matrix([[2.0, 0.0], [3.0, 4.0]])
    j12 = sp.csc_matrix([[5.0], [6.0]])
    j21 = sp.csc_matrix([[7.0, 8.0]])
    j22 = sp.csc_matrix([[9.0]])
    assembler = JacobianAssembler()
    for c in (100.0, 150.0):
        expected = sp.bmat(
            [[c * sp.eye(2, format="csc") - j11, -j12], [j21, j22]],
            format="csc",
        )
        actual = assembler.assemble_jacobian_bdf(2, c, j11, j12, j21, j22)
        np.testing.assert_array_equal(actual.toarray(), expected.toarray())
    assert assembler.get_pattern_build_count() == 1
    assert assembler.get_fast_assembly_count() == 2


def test_bdf_native_fill_matches_sparse_reference_and_reuses_pattern() -> None:
    """Compare CSC storage, not just dense values, over changing BDF coefficients."""
    assembler = JacobianAssembler()
    ns, na = 12, 7
    blocks = (_random_block(ns, ns, 41, 0.25),
              _random_block(ns, na, 42, 0.2),
              _random_block(na, ns, 43, 0.2),
              _random_block(na, na, 44, 0.3))
    j11, j12, j21, j22 = blocks
    for coefficient in (0.4, 2.0, 100.0, 1.3):
        reference = pack_4_by_4_scipy(
            (coefficient * sp.eye(ns, format="csc") - j11).tocsc(),
            -j12, j21, j22)
        actual = assembler.assemble_jacobian_bdf(ns, coefficient, *blocks)
        _assert_identical(actual, reference)
    assert assembler.get_pattern_build_count() == 1
    assert assembler.get_fast_assembly_count() == 4


def test_bdf_native_fill_falls_back_when_state_diagonal_cancels() -> None:
    assembler = JacobianAssembler()
    j11 = csc_matrix([[2.0]])
    empty_top = csc_matrix((1, 0))
    empty_left = csc_matrix((0, 1))
    empty_bottom = csc_matrix((0, 0))
    actual = assembler.assemble_jacobian_bdf(
        1, 2.0, j11, empty_top, empty_left, empty_bottom)
    assert actual.toarray()[0, 0] == 0.0
    assert assembler.get_fallback_assembly_count() == 1


def test_two_bus_trajectory_matches_sparse_reference() -> None:
    """
    The production solver and an independent sparse reference agree on a fresh 2-bus problem.

    :return: None.
    """
    production_problem: RmsProblemDae
    reference_problem: RmsProblemDae
    options: RmsOptions
    production_problem, options = _two_bus_problem()
    reference_problem, options = _two_bus_problem()
    production: BackEulerImplicitIntegration = BackEulerImplicitIntegration(problem=production_problem, t0=0, t_end=0.2, h=options.time_step,
                                                                            max_iter=options.max_iter, tolerance=options.tolerance)
    reference: SparseReferenceBackEuler = SparseReferenceBackEuler(problem=reference_problem, t0=0, t_end=0.2, h=options.time_step,
                                                               max_iter=options.max_iter, tolerance=options.tolerance)
    y_production: Mat = _simulate(production)
    y_reference: Mat = _simulate(reference)
    np.testing.assert_allclose(y_production, y_reference, rtol=1e-8, atol=1e-8)


def test_kundur_trajectory_matches_sparse_reference() -> None:
    """
    The production solver and the sparse reference agree on a Kundur RMS problem with a load step.

    :return: None.
    """
    # 1.0 s with a 1 ms step, as in the case lab and benchmark.
    options: RmsOptions = RmsOptions(time_step=1.0e-3, simulation_time=1.0, tolerance=1.0e-6,
                                     integration_method=DynamicIntegrationMethod.DaeBackEuler,
                                     initialization_method=RmsInitializationMethod.Explicit, use_init_values=False,
                                     max_iter=1000, verbose=0)
    production: BackEulerImplicitIntegration = BackEulerImplicitIntegration(problem=_kundur_problem(options), t0=0, t_end=options.simulation_time,
                                                                            h=options.time_step, max_iter=options.max_iter, tolerance=options.tolerance)
    reference: SparseReferenceBackEuler = SparseReferenceBackEuler(problem=_kundur_problem(options), t0=0, t_end=options.simulation_time,
                                                               h=options.time_step, max_iter=options.max_iter, tolerance=options.tolerance)
    y_production: Mat = _simulate(production)
    y_reference: Mat = _simulate(reference)
    np.testing.assert_allclose(y_production, y_reference, rtol=1e-8, atol=1e-8)
    assert production._jacobian_assembler.get_fast_assembly_count() > 0
