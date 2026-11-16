# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Check native category AD, nodal accumulation and FullVec trajectory equivalence."""

import warnings
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csc_matrix
from typing import Callable


from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import RmsInitializationMethod
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_full_vectorized import RmsProblemDaeFullVec as LegacyProblem
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_full_vectorized_numba_comp import RmsProblemDaeFullVec as NativeProblem
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration as LegacySolver
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration as NativeSolver
from VeraGridEngine.Simulations.Rms.numerical.rms_category_ad_numba_comp import (
    CategoryAdSpec, CategoryRowTarget, FullVecCategoryAdJacobian, NewtonCscAssembler,
)
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from tests.RMS._ieee14_andes_rms_case import (
    assign_ieee14_rms_models, build_ieee14_network_from_andes_case, build_ieee14_power_flow_options,
    get_andes_ieee14_full_xlsx_path, set_initial_vector,
)


@pytest.mark.parametrize("h", (0.001, 0.025))
def test_native_category_uses_instance_parameters_and_global_column_roles(h: float) -> None:
    """Respect local/global order, derivative chains and unequal instance parameters.

    :param h: Effective step size.
    :return: None.
    """
    x: Var = Var("instance_x")
    y: Var = Var("instance_y")
    dx: Var = Var("instance_dx", base_var=x)
    gain: Var = Var("instance_gain")
    targets: list[CategoryRowTarget] = list((
        CategoryRowTarget(0, 0, 0, 1.0), CategoryRowTarget(0, 1, 1, 1.0),
        CategoryRowTarget(1, 0, 2, 1.0), CategoryRowTarget(1, 1, 3, 1.0),
    ))
    spec: CategoryAdSpec = CategoryAdSpec(
        1, list((gain * x + y, x * x + y + dx)), list((y, x)), list((dx,)),
        list((gain,)), list(), np.array(((2, 3), (0, 1))), targets,
    )
    backend: FullVecCategoryAdJacobian = FullVecCategoryAdJacobian(list((spec,)), 2, 2, list())
    inputs: dict[int, list[np.ndarray]] = dict(((1, list((
        np.array(((3.0, 5.0), (2.0, 4.0))), np.array(((0.1, 0.2),)),
        np.array(((2.0, 3.0),)), np.empty((0, 2)),
    ))),))
    blocks: tuple[csc_matrix, ...] = backend.evaluate(inputs, h)
    np.testing.assert_allclose(blocks[0].toarray(), ((2.0, 0.0), (0.0, 3.0)))
    np.testing.assert_allclose(blocks[1].toarray(), np.eye(2))
    np.testing.assert_allclose(blocks[2].toarray(), ((4.0 + 1.0 / h, 0.0), (0.0, 8.0 + 1.0 / h)))
    np.testing.assert_allclose(blocks[3].toarray(), np.eye(2))
    pointers: tuple[np.ndarray, ...] = tuple(matrix.indptr for matrix in blocks)
    data: tuple[np.ndarray, ...] = tuple(matrix.data for matrix in blocks)
    second: tuple[csc_matrix, ...] = backend.evaluate(inputs, h)
    index: int
    for index in range(4):
        assert second[index] is blocks[index]
        assert second[index].indptr is pointers[index]
        assert second[index].data is data[index]
    assert backend.get_evaluation_count() == 2
    assert len(backend._plans[0].compiler.kernel.nopython_signatures) == 1


def test_native_category_accumulates_shared_bus_and_direct_nodal_terms() -> None:
    """Add rather than overwrite shared-bus contributions and reset them on reevaluation.

    :return: None.
    """
    voltage: Var = Var("shared_voltage")
    gain: Var = Var("terminal_gain")
    spec: CategoryAdSpec = CategoryAdSpec(
        1, list((gain * voltage * voltage,)), list((voltage,)), list(), list((gain,)), list(),
        np.array(((0, 0),)),
        list((CategoryRowTarget(0, 0, 0, -1.0), CategoryRowTarget(0, 1, 0, -1.0))),
    )
    backend: FullVecCategoryAdJacobian = FullVecCategoryAdJacobian(
        list((spec,)), 0, 1, list(((0, 0, 1.0),)),
    )
    inputs: dict[int, list[np.ndarray]] = dict(((1, list((
        np.array(((2.0, 2.0),)), np.empty((0, 2)), np.array(((1.0, 2.0),)), np.empty((0, 2)),
    ))),))
    np.testing.assert_allclose(backend.evaluate(inputs, 0.01)[3].toarray(), ((-11.0,),))
    inputs[1][0][:] = 3.0
    inputs[1][2][:] = np.array(((2.0, 3.0),))
    np.testing.assert_allclose(backend.evaluate(inputs, 0.01)[3].toarray(), ((-29.0,),))


@pytest.fixture(scope="module")
def ieee14_problems() -> tuple[NativeProblem, LegacyProblem]:
    """Initialize native and unchanged FullVec problems on identical physical models.

    :return: Native problem and reference FullVec problem.
    """
    workbook_path: Path | None = get_andes_ieee14_full_xlsx_path()
    if workbook_path is None:
        reason: str = "IEEE14 RMS cases excluded: ANDES (source of ieee14_full.xlsx) is not installed"
        warnings.warn(reason, UserWarning)
        pytest.skip(reason)
    else:
        pass
    grid: MultiCircuit
    generator: Generator
    grid, generator = build_ieee14_network_from_andes_case(workbook_path)
    assign_ieee14_rms_models(grid, generator)
    pf: PowerFlowDriver = PowerFlowDriver(grid, build_ieee14_power_flow_options())
    pf.run()
    assert pf.results.converged
    options: RmsOptions = RmsOptions(time_step=0.001, simulation_time=1.0, tolerance=1e-6,
                                     initialization_method=RmsInitializationMethod.Explicit,
                                     use_init_values=False, max_iter=1000)
    native: NativeProblem = NativeProblem(grid, options, pf.results, logger=Logger())
    native.set_events_group(RmsEventsGroup(name="native_category_validation"))
    reference: LegacyProblem = LegacyProblem(grid, options, pf.results, logger=Logger())
    reference.set_events_group(RmsEventsGroup(name="reference_category_validation"))
    return native, reference


@pytest.mark.parametrize("h", (0.001, 0.0025))
def test_ieee14_category_blocks_match_scalar_equations(ieee14_problems: tuple[NativeProblem, LegacyProblem], h: float) -> None:
    """Validate complete blocks, including shared nodal rows, at nonuniform candidates.

    :param ieee14_problems: Initialized problems.
    :param h: Effective step size.
    :return: None.
    """
    problem: NativeProblem = ieee14_problems[0]
    compiler: RMSCompiler = RMSCompiler(
        problem._state_vars + problem._algebraic_vars, problem._diff_vars,
        problem._variable_parameters, problem._constant_parameters, problem._compiler_names_dict.copy(),
    )
    functions: tuple[Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float], csc_matrix], ...] = (
        compiler.compile_sparse_jacobian(problem._state_eqs, problem._state_vars, "category_reference_j11"),
        compiler.compile_sparse_jacobian(problem._state_eqs, problem._algebraic_vars, "category_reference_j12"),
        compiler.compile_sparse_jacobian(problem._algebraic_eqs, problem._state_vars, "category_reference_j21"),
        compiler.compile_sparse_jacobian(problem._algebraic_eqs, problem._algebraic_vars, "category_reference_j22"),
    )
    initial: np.ndarray = problem.get_x0()
    case: int
    for case in range(3):
        values: np.ndarray = initial.copy()
        if case == 1:
            values[1] += 1e-4
        elif case == 2:
            values += 1e-6 * np.sin(np.arange(values.size))
        else:
            pass
        derivatives: np.ndarray = problem.get_dx(values, initial, np.zeros(problem.get_diff_var_number()), h)
        problem.update_variable_params(t=0.2, x_snapshot=values, scheduled_t=0.2)
        problem.update(0.2, values, problem._variable_parameters_values)
        actual: tuple[csc_matrix, ...] = problem.evaluate_jacobian_blocks_numba(values, derivatives, h)
        index: int
        for index in range(4):
            expected: csc_matrix = functions[index](values, derivatives, problem._variable_parameters_values,
                                                    problem._constant_params, h)
            np.testing.assert_allclose(actual[index].toarray(), expected.toarray(), rtol=1e-8, atol=1e-9)
    statistics: list[tuple[int, int, int]] = problem.get_category_ad_backend().get_statistics()
    assert len(statistics) == 6
    assert sorted(instance_count for _, _, instance_count in statistics) == list((1, 2, 4, 4, 11, 16))


def test_ieee14_native_solver_evaluates_categories_once(ieee14_problems: tuple[NativeProblem, LegacyProblem]) -> None:
    """Request four blocks in one evaluation and reuse the residual's input gather.

    :param ieee14_problems: Initialized problems.
    :return: None.
    """
    problem: NativeProblem = ieee14_problems[0]
    values: np.ndarray = problem.get_x0()
    derivatives: np.ndarray = np.zeros(problem.get_diff_var_number())
    solver: NativeSolver = NativeSolver(problem, 0.0, 0.001, 0.001, 1000)
    solver._timings = dict(rhs_evaluation_time=0.0, jacobian_blocks_time=0.0)
    solver._rhs_implicit(values, derivatives, values, 0.001)
    before: int = problem.get_category_ad_backend().get_evaluation_count()
    solver._jacobian_implicit(values, derivatives, 0.001)
    assert problem.get_category_ad_backend().get_evaluation_count() == before + 1


def test_ieee14_native_event_trajectory_matches_fullvec(ieee14_problems: tuple[NativeProblem, LegacyProblem]) -> None:
    """Preserve all variables and the exact rotor-speed jump across both segments.

    :param ieee14_problems: Native and reference problems.
    :return: None.
    """
    native: NativeProblem = ieee14_problems[0]
    reference: LegacyProblem = ieee14_problems[1]
    trajectories: list[np.ndarray] = list()
    problem: NativeProblem | LegacyProblem
    solver_class: type[NativeSolver] | type[LegacySolver]
    for problem, solver_class in ((native, NativeSolver), (reference, LegacySolver)):
        initial: np.ndarray = problem.get_x0()
        problem.reset_boundary_update_state(0.0)
        pre: tuple[np.ndarray, np.ndarray, bool, bool] = solver_class(problem, 0.0, 0.2, 0.001, 1000, 1e-6).simulate()
        assert pre[2] and pre[3]
        set_initial_vector(problem, pre[1][-1])
        problem.init_guess[problem.state_vars[1].uid] += 1e-4
        post: tuple[np.ndarray, np.ndarray, bool, bool] = solver_class(problem, 0.2, 1.0, 0.001, 1000, 1e-6).simulate()
        assert post[2] and post[3]
        np.testing.assert_allclose(post[1][0, 1] - pre[1][-1, 1], 1e-4, atol=1e-12)
        trajectories.append(np.vstack((pre[1][:-1], post[1])))
        set_initial_vector(problem, initial)
    permutation: np.ndarray = np.empty(native.get_all_vars_number(), dtype=np.int64)
    uid: int
    index: int
    for uid, index in native.uid2idx_vars.items():
        permutation[index] = reference.uid2idx_vars[uid]
    np.testing.assert_allclose(trajectories[0], trajectories[1][:, permutation], rtol=1e-7, atol=1e-8)


def test_ieee14_native_rejects_exhausted_correction_budget(ieee14_problems: tuple[NativeProblem, LegacyProblem]) -> None:
    """Preserve initial states and omit a failed step without committing its candidate.

    :param ieee14_problems: Native and unchanged FullVec problems.
    :return: None.
    """
    problem: NativeProblem = ieee14_problems[0]
    initial: np.ndarray = problem.get_x0()
    perturbed: np.ndarray = initial.copy()
    perturbed[1] += 1e-4
    set_initial_vector(problem, perturbed)
    problem.reset_boundary_update_state(0.0)
    solver: NativeSolver = NativeSolver(problem, 0.0, 0.005, 0.001, 0, 1e-6)
    output: tuple[np.ndarray, np.ndarray, bool, bool] = solver.simulate()
    assert not output[3]
    assert output[0].size == 1
    np.testing.assert_allclose(output[1][0, :56], perturbed[:56])
    set_initial_vector(problem, initial)


def test_native_residual_matches_reference_and_reuses_buffer(
        ieee14_problems: tuple[NativeProblem, LegacyProblem]) -> None:
    """Compare raw equations and discretization after perturbing all variables.

    :param ieee14_problems: Prepared native and reference problems.
    :return: None.
    """
    native: NativeProblem = ieee14_problems[0]
    reference: LegacyProblem = ieee14_problems[1]
    values: np.ndarray = native.get_x0().copy()
    previous: np.ndarray = values.copy()
    values += np.linspace(-1e-5, 1e-5, values.size)
    derivatives: np.ndarray = np.zeros(native.get_diff_var_number())
    reference_values: np.ndarray = reference.get_x0().copy()
    uid: int
    index: int
    for uid, index in native.uid2idx_vars.items():
        reference_values[reference.uid2idx_vars[uid]] = values[index]
    # Compare equation values in their shared model-equation ordering.
    reference.update_input_matrices_by_model(reference_values, derivatives)
    algebraic: np.ndarray = reference.rhs_algebraic_vec(reference_values, derivatives).copy()
    differential: np.ndarray = reference.rhs_state_vec().copy()
    native.update_input_matrices_by_model(values, derivatives)
    native_algebraic: np.ndarray = native.rhs_algebraic_vec(values, derivatives)
    saved_algebraic: np.ndarray = native_algebraic.copy()
    np.testing.assert_allclose(native_algebraic, algebraic, rtol=1e-9, atol=1e-9)
    np.testing.assert_allclose(native.rhs_state_vec(), differential, rtol=1e-9, atol=1e-9)
    np.testing.assert_array_equal(native_algebraic, saved_algebraic)
    step: float = 0.001
    residual: np.ndarray = native.evaluate_implicit_residual_numba(values, derivatives, previous, step)
    state_count: int = native.get_states_number()
    np.testing.assert_allclose(residual[:state_count],
                               values[:state_count] - previous[:state_count] - step * differential,
                               rtol=1e-9, atol=1e-10)
    np.testing.assert_allclose(residual[state_count:], algebraic, rtol=1e-9, atol=1e-9)
    assert native.evaluate_implicit_residual_numba(values, derivatives, previous, step) is residual
    np.testing.assert_array_equal(native_algebraic, saved_algebraic)


@pytest.mark.parametrize("state_count,algebraic_count", ((2, 2), (0, 2), (2, 0), (0, 0)))
def test_persistent_newton_csc_matches_block_formula(state_count: int, algebraic_count: int) -> None:
    """Preserve structure, identity-only diagonals and values across changing steps.

    :param state_count: Differential block dimension.
    :param algebraic_count: Algebraic block dimension.
    :return: None.
    """
    # Sparse zeros deliberately omit state diagonals from the derivative pattern.
    j11: csc_matrix = csc_matrix(np.triu(np.ones((state_count, state_count)), k=1))
    j12: csc_matrix = csc_matrix(np.full((state_count, algebraic_count), 2.0))
    j21: csc_matrix = csc_matrix(np.full((algebraic_count, state_count), 3.0))
    j22: csc_matrix = csc_matrix(np.eye(algebraic_count) * 4.0)
    blocks: tuple[csc_matrix, ...] = (j11, j12, j21, j22)
    assembler: NewtonCscAssembler = NewtonCscAssembler(blocks, state_count)
    actual: csc_matrix = assembler.evaluate(blocks, 0.001)
    data: np.ndarray = actual.data
    indices: np.ndarray = actual.indices
    indptr: np.ndarray = actual.indptr
    step: float
    for step in (0.001, 0.02, 0.0):
        expected: np.ndarray = np.block([
            [np.eye(state_count) - step * j11.toarray(), -step * j12.toarray()],
            [j21.toarray(), j22.toarray()],
        ])
        assert assembler.evaluate(blocks, step) is actual
        np.testing.assert_allclose(actual.toarray(), expected)
        assert actual.data is data
        assert actual.indices is indices
        assert actual.indptr is indptr
        assert actual.has_canonical_format
    # Overwrite every structural derivative with zero to expose stale values.
    block: csc_matrix
    for block in blocks:
        block.data.fill(0.0)
    assembler.evaluate(blocks, 0.1)
    expected_zero: np.ndarray = np.zeros((state_count + algebraic_count, state_count + algebraic_count))
    expected_zero[:state_count, :state_count] = np.eye(state_count)
    np.testing.assert_array_equal(actual.toarray(), expected_zero)


@pytest.mark.parametrize("step", (0.001, 0.0025))
def test_ieee14_persistent_newton_matches_blocks(
        ieee14_problems: tuple[NativeProblem, LegacyProblem], step: float) -> None:
    """Compare the global Newton matrix with the previous four-block formula.

    :param ieee14_problems: Prepared IEEE14 native and reference problems.
    :param step: Effective integration step.
    :return: None.
    """
    problem: NativeProblem = ieee14_problems[0]
    initial: np.ndarray = problem.get_x0().copy()
    values: np.ndarray = initial + 1e-6 * np.sin(np.arange(initial.size))
    derivatives: np.ndarray = problem.get_dx(
        values, initial, np.zeros(problem.get_diff_var_number()), step)
    blocks: tuple[csc_matrix, ...] = problem.evaluate_jacobian_blocks_numba(values, derivatives, step)
    state_count: int = problem.get_states_number()
    expected: np.ndarray = np.block([
        [np.eye(state_count) - step * blocks[0].toarray(), -step * blocks[1].toarray()],
        [blocks[2].toarray(), blocks[3].toarray()],
    ])
    backend: FullVecCategoryAdJacobian = problem.get_category_ad_backend()
    before: int = backend.get_evaluation_count()
    actual: csc_matrix = problem.evaluate_newton_matrix_numba(values, derivatives, step)
    assert backend.get_evaluation_count() == before + 1
    np.testing.assert_allclose(actual.toarray(), expected, rtol=1e-12, atol=1e-12)
    data: np.ndarray = actual.data
    indices: np.ndarray = actual.indices
    indptr: np.ndarray = actual.indptr
    assert problem.evaluate_newton_matrix_numba(values, derivatives, step) is actual
    assert actual.data is data
    assert actual.indices is indices
    assert actual.indptr is indptr


def test_coordinator_preserves_buffers_and_refreshes_runtime_parameters() -> None:
    """Keep category constants fixed and refresh runtime values at the same time.

    :return: None.
    """
    # Two instances use unequal parameters and both contribute to a shared balance.
    x: Var = Var("coordinator_x")
    gain: Var = Var("coordinator_gain")
    bias: Var = Var("coordinator_bias")
    spec: CategoryAdSpec = CategoryAdSpec(
        7, list((gain * x + bias,)), list((x,)), list(), list((gain,)), list((bias,)),
        np.array(((0, 1),), dtype=np.int64),
        list((CategoryRowTarget(0, 0, 0, 1.0), CategoryRowTarget(0, 1, 0, 1.0))),
    )
    backend: FullVecCategoryAdJacobian = FullVecCategoryAdJacobian(
        list((spec,)), 0, 2, list(((0, 0, -1.0),)))
    inputs: dict[int, list[np.ndarray]] = dict()
    empty_maps: dict[int, np.ndarray] = dict()
    parameter_maps: dict[int, np.ndarray] = dict(((7, np.array(((0, 1),), dtype=np.int64)),))
    constants: np.ndarray = np.array((3.0, 4.0))
    runtime: np.ndarray = np.array((2.0, 5.0))
    values: np.ndarray = np.array((1.0, 2.0))
    derivatives: np.ndarray = np.empty(0)
    backend.prepare_category_inputs(inputs, empty_maps, parameter_maps, parameter_maps,
                                    constants, values, derivatives, runtime)
    buffers: tuple[np.ndarray, ...] = tuple(inputs[7])
    residual: np.ndarray = backend.evaluate_coordinated_residual(
        values, derivatives, values, runtime, 0.01)
    np.testing.assert_allclose(residual, (18.0, 0.0))
    # Immutable constants are not recopied; the variable candidate is gathered in place.
    constants[:] = 999.0
    values[:] = (2.0, 3.0)
    runtime[:] = (7.0, 11.0)
    backend.invalidate_runtime_parameters()
    assert backend.evaluate_coordinated_residual(values, derivatives, values, runtime, 0.01) is residual
    np.testing.assert_allclose(residual, (52.0, 0.0))
    np.testing.assert_array_equal(inputs[7][3], ((3.0, 4.0),))
    index: int
    for index in range(4):
        assert inputs[7][index] is buffers[index]
    # The next Jacobian uses exactly the inputs left by the residual coordinator.
    np.testing.assert_allclose(backend.evaluate(inputs, 0.01)[3].toarray(), ((6.0, 11.0), (0.0, 0.0)))
    assert len(backend._coordinator.nopython_signatures) == 1


def test_ieee14_coordinator_keeps_all_category_input_buffers(
        ieee14_problems: tuple[NativeProblem, LegacyProblem]) -> None:
    """Retain category input storage through residuals and repeated boundary updates.

    :param ieee14_problems: Prepared IEEE14 problems.
    :return: None.
    """
    problem: NativeProblem = ieee14_problems[0]
    snapshots: dict[int, tuple[np.ndarray, ...]] = dict(
        (uid, tuple(buffers)) for uid, buffers in problem._input_matrices_by_model.items())
    values: np.ndarray = problem.get_x0().copy()
    derivatives: np.ndarray = np.zeros(problem.get_diff_var_number())
    attempt: int
    for attempt in range(2):
        problem.update_variable_params(0.2, values, 0.2)
        problem.update(0.2, values, problem._variable_parameters_values)
        problem.evaluate_implicit_residual_numba(values, derivatives, values, 0.001)
        problem.evaluate_newton_matrix_numba(values, derivatives, 0.001, reuse_gather=True)
        uid: int
        old_buffers: tuple[np.ndarray, ...]
        for uid, old_buffers in snapshots.items():
            index: int
            for index in range(4):
                assert problem._input_matrices_by_model[uid][index] is old_buffers[index]
