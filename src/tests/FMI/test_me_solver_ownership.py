"""Focused contracts for simulation-owned FMI Model Exchange integration."""

from __future__ import annotations

import math
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from VeraGridEngine.IO.fmu.importer.emt_boundary import CompositeEmtBoundaryUpdater
from VeraGridEngine.IO.fmu.importer.errors import FmuModeError
from VeraGridEngine.IO.fmu.importer.model_exchange import (
    FmuMeDeviceAdapter,
    FmuMeSolverPolicy,
    _build_fmu_me_solver_policy,
    _prepare_rms_fmu_me_state_event_retry,
)
from VeraGridEngine.IO.fmu.importer.runtime_coordinator import (
    FmiThreeModelExchangeCoordinator,
)
from VeraGridEngine.IO.fmu.importer.runtime_host import FmiTwoEventUpdate
from VeraGridEngine.IO.fmu.importer.runtime_profile import FmuMeEvaluationBudget
from VeraGridEngine.IO.fmu.importer.runtime_protocol import (
    FmiThreeWorkerCompletedIntegratorStepResult,
    FmiThreeWorkerDiscreteStatesResult,
)
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.enumerations import DynamicIntegrationMethod, VarPowerFlowReferenceType


def _evaluate_linear_decay_derivative(
    time_value: float,
    continuous_state_values: tuple[float, ...],
    writable_values: tuple[float, ...],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Evaluate the autonomous linear decay used by solver contracts.

    :param time_value: Finite solver probe time.
    :param continuous_state_values: Continuous state presented by the solver.
    :param writable_values: One-element tuple containing the decay rate.
    :return: Linear derivatives and an empty readable-output tuple.
    """

    if math.isfinite(time_value) and len(writable_values) == 1:
        decay_rate: float = writable_values[0]
    else:
        raise AssertionError("Linear-decay probe has an invalid contract")
    derivative_values: list[float] = [0.0] * len(continuous_state_values)
    state_index: int
    for state_index in range(len(continuous_state_values)):
        derivative_values[state_index] = (
            -decay_rate * continuous_state_values[state_index]
        )
    return tuple(derivative_values), tuple()


def _build_mock_backward_euler_adapter(
    solver_policy: FmuMeSolverPolicy | None = None,
) -> tuple[FmuMeDeviceAdapter, Mock]:
    """Build a runtime-free adapter for deterministic solver evaluation.

    :param solver_policy: Optional policy override for boundary tests.
    :return: Adapter and coordinator mock exposing all solver probes.
    """

    if solver_policy is None:
        active_policy: FmuMeSolverPolicy = FmuMeSolverPolicy(
            integration_method=DynamicIntegrationMethod.DaeBackEuler,
            absolute_tolerance=1.0e-8,
            relative_tolerance=1.0e-8,
            maximum_newton_iterations=20,
            maximum_continuous_states=128,
        )
    else:
        active_policy = solver_policy
    coordinator: Mock = Mock()
    coordinator.evaluate_probe.side_effect = _evaluate_linear_decay_derivative
    adapter: FmuMeDeviceAdapter = object.__new__(FmuMeDeviceAdapter)
    adapter.spec = SimpleNamespace(
        input_variable_names=("decay_rate",),
        output_variable_names=tuple(),
        output_bindings=tuple(),
        maximum_event_iterations=2,
    )
    adapter.solver_policy = active_policy
    adapter.runtime_host = None
    adapter.fmi_three_coordinator = coordinator
    adapter.localized_state_event_time = None
    adapter.fmi_two_next_event_time = None
    return adapter, coordinator


def _evaluate_linear_test_event_indicator(
    time_value: float,
    continuous_state_values: tuple[float, ...],
    point_is_presented: bool,
    evaluation_budget: FmuMeEvaluationBudget,
) -> tuple[float, ...]:
    """Evaluate two independent state indicators during localization.

    :param time_value: Probe time supplied by the localization algorithm.
    :param continuous_state_values: Backward Euler continuous-state vector.
    :param point_is_presented: Whether the solver already presented the point.
    :param evaluation_budget: Shared evaluation budget passed by the adapter.
    :return: Indicators crossing when the state decays through 0.7 and 0.6.
    """

    if math.isfinite(time_value) and point_is_presented:
        pass
    else:
        raise AssertionError("Synthetic localization probe was not presented")
    if evaluation_budget.get_consumed_count() > 0:
        evaluation_budget.consume()
    else:
        raise AssertionError("Synthetic localization received an unused budget")
    return (
        continuous_state_values[0] - 0.7,
        continuous_state_values[0] - 0.6,
    )


def _evaluate_constant_test_derivative(
    time_value: float,
    continuous_state_values: tuple[float, ...],
    writable_values: tuple[float, ...],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Return a constant derivative for method-consistent localization.

    :param time_value: Finite probe time.
    :param continuous_state_values: Current continuous states.
    :param writable_values: Empty synthetic writable vector.
    :return: Constant derivatives and no readable values.
    """

    if math.isfinite(time_value) and len(writable_values) == 0:
        pass
    else:
        raise AssertionError("Synthetic derivative probe is invalid")
    derivative_values: list[float] = [3.0] * len(continuous_state_values)
    return tuple(derivative_values), tuple()


def _build_synthetic_localization_adapter(
    accepted_time: float,
    candidate_time: float,
    accepted_states: tuple[float, ...],
    candidate_states: tuple[float, ...],
    accepted_indicators: tuple[float, ...],
    candidate_indicators: tuple[float, ...],
) -> tuple[FmuMeDeviceAdapter, Mock]:
    """Build one bounded localization adapter without opening an FMU.

    :param accepted_time: Stored accepted time.
    :param candidate_time: Stored candidate time.
    :param accepted_states: Accepted continuous states.
    :param candidate_states: Candidate continuous states.
    :param accepted_indicators: Accepted indicator vector.
    :param candidate_indicators: Candidate indicator vector.
    :return: Synthetic adapter and its coordinator mock.
    """

    coordinator: Mock = Mock()
    coordinator.has_pending_candidate.return_value = True
    if len(accepted_states) == 0:
        coordinator.evaluate_probe.side_effect = _evaluate_constant_test_derivative
        input_variable_names: tuple[str, ...] = tuple()
        accepted_input_values: tuple[float, ...] = tuple()
    else:
        coordinator.evaluate_probe.side_effect = _evaluate_linear_decay_derivative
        input_variable_names = ("decay_rate",)
        accepted_input_values = (1.0,)
    coordinator.evaluate_event_indicators_probe.side_effect = (
        _evaluate_linear_test_event_indicator
    )
    adapter: FmuMeDeviceAdapter = object.__new__(FmuMeDeviceAdapter)
    adapter.spec = SimpleNamespace(
        input_variable_names=input_variable_names,
        output_variable_names=tuple(),
    )
    adapter.solver_policy = FmuMeSolverPolicy(
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        absolute_tolerance=1.0e-8,
        relative_tolerance=1.0e-8,
        maximum_newton_iterations=20,
        maximum_continuous_states=128,
    )
    adapter.runtime_host = None
    adapter.fmi_three_coordinator = coordinator
    adapter.state_vector = np.array(candidate_states, dtype=float)
    adapter.pending_time = candidate_time
    adapter.pending_candidate_state_values = candidate_states
    candidate_derivative_values: list[float] = [0.0] * len(candidate_states)
    candidate_state_index: int
    for candidate_state_index in range(len(candidate_states)):
        candidate_derivative_values[candidate_state_index] = (
            -candidate_states[candidate_state_index]
        )
    adapter.pending_candidate_derivative_values = tuple(candidate_derivative_values)
    adapter.pending_candidate_readable_values = tuple()
    adapter.pending_candidate_event_indicators = candidate_indicators
    adapter.pending_accepted_time = accepted_time
    adapter.pending_accepted_state_values = accepted_states
    adapter.pending_accepted_input_values = accepted_input_values
    accepted_derivative_values: list[float] = [0.0] * len(accepted_states)
    accepted_state_index: int
    for accepted_state_index in range(len(accepted_states)):
        accepted_derivative_values[accepted_state_index] = (
            -accepted_states[accepted_state_index]
        )
    adapter.pending_accepted_derivative_values = tuple(accepted_derivative_values)
    adapter.pending_accepted_readable_values = tuple()
    adapter.pending_accepted_event_indicators = accepted_indicators
    adapter.localized_state_event_time = None
    adapter.fmi_two_next_event_time = None
    adapter.fmi_two_accepted_derivative_values = None
    adapter.fmi_two_accepted_readable_values = None
    adapter.fmi_two_accepted_event_indicators = None
    adapter.initialized = True
    return adapter, coordinator


def _evaluate_time_test_event_indicator(
    time_value: float,
    continuous_state_values: tuple[float, ...],
    point_is_presented: bool,
    evaluation_budget: FmuMeEvaluationBudget,
) -> tuple[float, ...]:
    """Evaluate one time-only indicator for a zero-state FMU.

    :param time_value: Probe time supplied by localization.
    :param continuous_state_values: Empty continuous-state vector.
    :param point_is_presented: Whether the point is already visible.
    :param evaluation_budget: Shared runtime-call budget.
    :return: One indicator crossing at 0.4 seconds.
    """

    if (
        len(continuous_state_values) == 0
        and point_is_presented
        and math.isfinite(time_value)
    ):
        evaluation_budget.consume()
    else:
        raise AssertionError("Synthetic zero-state probe is invalid")
    return (time_value - 0.4,)


def test_fmi_me_option_policy_schema() -> None:
    """Keep RMS and EMT Model Exchange policy defaults identical and persisted.

    :return: None.
    """

    rms_options: RmsOptions = RmsOptions()
    emt_options: EmtOptions = EmtOptions()
    expected_values: tuple[float | int, ...] = (
        1.0e-8,
        1.0e-8,
        20,
        128,
        100000,
    )
    rms_values: tuple[float | int, ...] = (
        rms_options.fmi_me_newton_absolute_tolerance,
        rms_options.fmi_me_newton_relative_tolerance,
        rms_options.fmi_me_newton_max_iterations,
        rms_options.fmi_me_max_continuous_states,
        rms_options.fmi_me_max_runtime_evaluations_per_step,
    )
    emt_values: tuple[float | int, ...] = (
        emt_options.fmi_me_newton_absolute_tolerance,
        emt_options.fmi_me_newton_relative_tolerance,
        emt_options.fmi_me_newton_max_iterations,
        emt_options.fmi_me_max_continuous_states,
        emt_options.fmi_me_max_runtime_evaluations_per_step,
    )
    persisted_keys: tuple[str, ...] = (
        "fmi_me_newton_absolute_tolerance",
        "fmi_me_newton_relative_tolerance",
        "fmi_me_newton_max_iterations",
        "fmi_me_max_continuous_states",
        "fmi_me_max_runtime_evaluations_per_step",
    )

    assert rms_values == expected_values
    assert emt_values == expected_values
    for persisted_key in persisted_keys:
        assert persisted_key in rms_options.registered_properties
        assert persisted_key in emt_options.registered_properties

    # Policies copy validated owner options without retaining the problem.
    rms_policy: FmuMeSolverPolicy = _build_fmu_me_solver_policy(rms_options)
    emt_me_options: EmtOptions = EmtOptions(
        integration_method=DynamicIntegrationMethod.DaeBackEuler
    )
    emt_policy: FmuMeSolverPolicy = _build_fmu_me_solver_policy(emt_me_options)
    assert rms_policy.maximum_continuous_states == 128
    assert emt_policy.integration_method == DynamicIntegrationMethod.DaeBackEuler
    assert RmsOptions(
        fmi_me_max_runtime_evaluations_per_step=100001
    ).fmi_me_max_runtime_evaluations_per_step == 100001

    # Invalid values fail at the owner or policy boundary before native use.
    with pytest.raises(ValueError, match="absolute tolerance"):
        RmsOptions(fmi_me_newton_absolute_tolerance=0.0)
    with pytest.raises(ValueError, match="relative tolerance"):
        EmtOptions(fmi_me_newton_relative_tolerance=math.nan)
    with pytest.raises(ValueError, match="iteration limit"):
        RmsOptions(fmi_me_newton_max_iterations=True)
    with pytest.raises(ValueError, match="state limit"):
        EmtOptions(fmi_me_max_continuous_states=129)
    with pytest.raises(ValueError, match="runtime evaluation limit"):
        RmsOptions(fmi_me_max_runtime_evaluations_per_step=10_000_001)
    with pytest.raises(ValueError, match="absolute tolerance"):
        FmuMeSolverPolicy(
            integration_method=DynamicIntegrationMethod.DaeBackEuler,
            absolute_tolerance=math.inf,
            relative_tolerance=1.0e-8,
            maximum_newton_iterations=20,
            maximum_continuous_states=128,
        )


def test_fmi_me_policy_rejects_unsupported_method_before_runtime() -> None:
    """Reject attached Model Exchange use under another solver family.

    :return: None.
    """

    with pytest.raises(FmuModeError, match="DaeBackEuler"):
        FmuMeSolverPolicy(
            integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
            absolute_tolerance=1.0e-8,
            relative_tolerance=1.0e-8,
            maximum_newton_iterations=20,
            maximum_continuous_states=128,
        )


def test_fmi_me_runtime_budget_call_mapping() -> None:
    """Map FMI 2 and FMI 3 native transactions and keep them fail-closed.

    :return: None.
    """

    evaluation_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(2)

    evaluation_budget.consume()
    evaluation_budget.consume()
    assert evaluation_budget.get_consumed_count() == 2
    with pytest.raises(FmuModeError, match="before the next native call"):
        evaluation_budget.consume()
    assert evaluation_budget.get_consumed_count() == 2

    fmi_three_adapter: FmuMeDeviceAdapter
    fmi_three_coordinator: Mock
    fmi_three_adapter, fmi_three_coordinator = (
        _build_mock_backward_euler_adapter()
    )
    fmi_three_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(1)
    fmi_three_derivatives: np.ndarray
    ignored_readable_values: tuple[float, ...] | None
    fmi_three_derivatives, ignored_readable_values = (
        fmi_three_adapter._evaluate_derivatives_for_state(
            time_value=0.25,
            state_values=np.array([2.0], dtype=float),
            input_values=dict(decay_rate=0.5),
            evaluation_budget=fmi_three_budget,
        )
    )
    assert fmi_three_derivatives.tolist() == pytest.approx([-1.0])
    assert fmi_three_budget.get_consumed_count() == 1
    fmi_three_coordinator.evaluate_probe.assert_called_once()

    fmi_two_adapter: FmuMeDeviceAdapter
    ignored_coordinator: Mock
    fmi_two_adapter, ignored_coordinator = _build_mock_backward_euler_adapter()
    runtime_host: Mock = Mock()
    runtime_host.get_derivatives.return_value = [-1.0]
    runtime_host.get_real.return_value = dict()
    fmi_two_adapter.runtime_host = runtime_host
    fmi_two_adapter.fmi_three_coordinator = None
    fmi_two_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(1)
    fmi_two_derivatives: np.ndarray
    fmi_two_derivatives, ignored_readable_values = (
        fmi_two_adapter._evaluate_derivatives_for_state(
            time_value=0.25,
            state_values=np.array([2.0], dtype=float),
            input_values=dict(decay_rate=0.5),
            evaluation_budget=fmi_two_budget,
        )
    )
    assert fmi_two_derivatives.tolist() == pytest.approx([-1.0])
    assert fmi_two_budget.get_consumed_count() == 1
    runtime_host.set_time.assert_called_once_with(0.25)
    runtime_host.set_continuous_states.assert_called_once_with([2.0])
    runtime_host.get_derivatives.assert_called_once()

    # The largest supported Backward Euler solve has one initial probe, one
    # base residual, and one Jacobian column plus one corrected residual per
    # Newton iteration. A non-retained localization probe adds one indicator.
    maximum_state_count: int = 128
    maximum_newton_iterations: int = 20
    retained_endpoint_evaluation_bound: int = (
        2 + maximum_newton_iterations * (maximum_state_count + 1)
    )
    non_retained_point_evaluation_bound: int = (
        retained_endpoint_evaluation_bound + 1
    )
    assert retained_endpoint_evaluation_bound == 2582
    assert non_retained_point_evaluation_bound == 2583

    # Drive the actual Newton loop through all 20 iterations. Each synthetic
    # Jacobian is the identity, while the last corrected residual converges
    # only on iteration 20, making the theoretical bound observable.
    bound_policy: FmuMeSolverPolicy = FmuMeSolverPolicy(
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        absolute_tolerance=1.0e-8,
        relative_tolerance=1.0e-8,
        maximum_newton_iterations=maximum_newton_iterations,
        maximum_continuous_states=maximum_state_count,
    )
    bound_adapter: FmuMeDeviceAdapter
    bound_coordinator: Mock
    bound_adapter, bound_coordinator = _build_mock_backward_euler_adapter(
        solver_policy=bound_policy
    )
    bound_probe_results: list[
        tuple[tuple[float, ...], tuple[float, ...]]
    ] = [(tuple(), tuple())] * retained_endpoint_evaluation_bound
    zero_derivatives: tuple[float, ...] = tuple(
        [0.0] * maximum_state_count
    )
    bound_probe_results[0] = (zero_derivatives, tuple())
    bound_probe_results[1] = (
        tuple([1.0] * maximum_state_count),
        tuple(),
    )
    probe_result_index: int = 2
    bound_iteration_index: int
    for bound_iteration_index in range(maximum_newton_iterations):
        jacobian_derivative_value: float = float(bound_iteration_index + 1)
        jacobian_derivatives: tuple[float, ...] = tuple(
            [jacobian_derivative_value] * maximum_state_count
        )
        jacobian_column_index: int
        for jacobian_column_index in range(maximum_state_count):
            bound_probe_results[probe_result_index] = (
                jacobian_derivatives,
                tuple(),
            )
            probe_result_index += 1
        if bound_iteration_index == maximum_newton_iterations - 1:
            endpoint_derivative_value: float = float(
                maximum_newton_iterations
            )
        else:
            endpoint_derivative_value = float(bound_iteration_index + 2)
        bound_probe_results[probe_result_index] = (
            tuple([endpoint_derivative_value] * maximum_state_count),
            tuple(),
        )
        probe_result_index += 1
    assert probe_result_index == retained_endpoint_evaluation_bound

    bound_coordinator.evaluate_probe.side_effect = bound_probe_results.copy()
    retained_bound_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(2582)
    retained_bound_states: np.ndarray
    retained_bound_derivatives: np.ndarray
    retained_bound_readable_values: tuple[float, ...] | None
    (
        retained_bound_states,
        retained_bound_derivatives,
        retained_bound_readable_values,
    ) = bound_adapter._solve_backward_euler_candidate(
        current_time=0.0,
        step_size=0.1,
        accepted_state_values=np.zeros(maximum_state_count, dtype=float),
        input_values=dict(decay_rate=1.0),
        evaluation_budget=retained_bound_budget,
    )
    assert retained_bound_states.tolist() == pytest.approx(
        [2.0] * maximum_state_count
    )
    assert retained_bound_derivatives.tolist() == pytest.approx(
        [20.0] * maximum_state_count
    )
    assert retained_bound_readable_values == tuple()
    assert bound_coordinator.evaluate_probe.call_count == 2582
    assert retained_bound_budget.get_consumed_count() == 2582
    with pytest.raises(FmuModeError, match="before the next native call"):
        retained_bound_budget.consume()

    # The FMI 3 retained candidate transaction adds exactly one charge after
    # the maximal point solve, producing the 2583 non-retained boundary.
    bound_coordinator.reset_mock()
    bound_coordinator.evaluate_probe.side_effect = bound_probe_results.copy()
    bound_coordinator.get_accepted_point.return_value = (
        0.0,
        tuple([0.0] * maximum_state_count),
        (1.0,),
        tuple(),
        (0.5,),
        tuple([1.0] * maximum_state_count),
        zero_derivatives,
    )
    bound_coordinator.evaluate_candidate.return_value = (
        tuple([20.0] * maximum_state_count),
        tuple(),
        (0.25,),
    )
    bound_adapter.state_vector = np.zeros(maximum_state_count, dtype=float)
    non_retained_bound_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(2583)
    bound_adapter._prepare_bound_step(
        current_time=0.0,
        step_size=0.1,
        input_values=dict(decay_rate=1.0),
        evaluation_budget=non_retained_bound_budget,
    )
    assert bound_coordinator.evaluate_probe.call_count == 2582
    bound_coordinator.evaluate_candidate.assert_called_once()
    assert non_retained_bound_budget.get_consumed_count() == 2583

    default_limit_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(100000)
    default_operation_index: int
    for default_operation_index in range(100000):
        default_limit_budget.consume()
    with pytest.raises(FmuModeError, match="before the next native call"):
        default_limit_budget.consume()
    raised_limit_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(100001)
    raised_operation_index: int
    for raised_operation_index in range(100001):
        raised_limit_budget.consume()
    assert raised_limit_budget.get_consumed_count() == 100001

    # FMI 2 exposes output and indicator reads separately after the solver
    # probes, while FMI 3 groups candidate derivatives and outputs and adds one
    # compound candidate transaction for the indicator and retained snapshot.
    retained_fmi_two_adapter: FmuMeDeviceAdapter
    retained_fmi_two_coordinator: Mock
    retained_fmi_two_adapter, retained_fmi_two_coordinator = (
        _build_mock_backward_euler_adapter()
    )
    retained_fmi_two_runtime: Mock = Mock()
    retained_fmi_two_runtime.get_derivatives.return_value = [-1.0]
    retained_fmi_two_runtime.get_real.return_value = dict()
    retained_fmi_two_runtime.get_event_indicators.return_value = (0.25,)
    retained_fmi_two_adapter.runtime_host = retained_fmi_two_runtime
    retained_fmi_two_adapter.fmi_three_coordinator = None
    retained_fmi_two_adapter.state_vector = np.array([1.0], dtype=float)
    retained_fmi_two_adapter.fmi_two_accepted_derivative_values = (-1.0,)
    retained_fmi_two_adapter.fmi_two_accepted_readable_values = tuple()
    retained_fmi_two_adapter.fmi_two_accepted_event_indicators = (0.5,)
    retained_fmi_two_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(20)
    retained_fmi_two_adapter._prepare_bound_step(
        current_time=0.0,
        step_size=0.5,
        input_values=dict(decay_rate=1.0),
        evaluation_budget=retained_fmi_two_budget,
    )
    retained_fmi_two_solver_calls: int = (
        retained_fmi_two_runtime.get_derivatives.call_count
    )
    assert retained_fmi_two_runtime.set_time.call_count == (
        retained_fmi_two_solver_calls
    )
    assert retained_fmi_two_runtime.set_continuous_states.call_count == (
        retained_fmi_two_solver_calls
    )
    assert retained_fmi_two_runtime.get_real.call_count == (
        retained_fmi_two_solver_calls + 1
    )
    assert retained_fmi_two_runtime.get_event_indicators.call_count == 1
    assert retained_fmi_two_budget.get_consumed_count() == (
        retained_fmi_two_solver_calls + 2
    )

    # FMI 2 has no native checkpoint contract. Rejection therefore restores
    # and validates the accepted visible point with one compound evaluation
    # plus one indicator read.
    retained_fmi_two_runtime.reset_mock()
    retained_fmi_two_runtime.get_derivatives.return_value = [-1.0]
    retained_fmi_two_runtime.get_real.return_value = dict()
    retained_fmi_two_runtime.get_event_indicators.return_value = (0.5,)
    fmi_two_rejection_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(2)
    retained_fmi_two_adapter.resolve_pending_step(
        accepted=False,
        evaluation_budget=fmi_two_rejection_budget,
    )
    assert fmi_two_rejection_budget.get_consumed_count() == 2
    assert retained_fmi_two_runtime.get_derivatives.call_count == 1
    assert retained_fmi_two_runtime.get_real.call_count == 1
    assert retained_fmi_two_runtime.get_event_indicators.call_count == 1

    # A smooth accepted FMI 2 candidate requires no native transition when
    # completedIntegratorStep is not declared by the FMU.
    retained_fmi_two_runtime.get_event_indicators.return_value = (0.25,)
    smooth_candidate_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(20)
    retained_fmi_two_adapter._prepare_bound_step(
        current_time=0.0,
        step_size=0.5,
        input_values=dict(decay_rate=1.0),
        evaluation_budget=smooth_candidate_budget,
    )
    retained_fmi_two_runtime.reset_mock()
    retained_fmi_two_runtime.needs_completed_integrator_step.return_value = False
    fmi_two_smooth_acceptance_budget: FmuMeEvaluationBudget = (
        FmuMeEvaluationBudget(1)
    )
    retained_fmi_two_adapter.resolve_pending_step(
        accepted=True,
        evaluation_budget=fmi_two_smooth_acceptance_budget,
    )
    assert fmi_two_smooth_acceptance_budget.get_consumed_count() == 0
    retained_fmi_two_runtime.completed_integrator_step.assert_not_called()
    retained_fmi_two_runtime.enter_event_mode.assert_not_called()

    # The optional completedIntegratorStep boundary has one charge even when
    # it does not request Event Mode.
    completed_candidate_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(20)
    retained_fmi_two_runtime.get_derivatives.return_value = [-1.0]
    retained_fmi_two_runtime.get_real.return_value = dict()
    retained_fmi_two_runtime.get_event_indicators.return_value = (0.25,)
    retained_fmi_two_adapter._prepare_bound_step(
        current_time=0.5,
        step_size=0.5,
        input_values=dict(decay_rate=1.0),
        evaluation_budget=completed_candidate_budget,
    )
    retained_fmi_two_runtime.reset_mock()
    retained_fmi_two_runtime.needs_completed_integrator_step.return_value = True
    retained_fmi_two_runtime.completed_integrator_step.return_value = (
        False,
        False,
    )
    fmi_two_completed_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(1)
    retained_fmi_two_adapter.resolve_pending_step(
        accepted=True,
        evaluation_budget=fmi_two_completed_budget,
    )
    assert fmi_two_completed_budget.get_consumed_count() == 1
    retained_fmi_two_runtime.completed_integrator_step.assert_called_once()
    retained_fmi_two_runtime.enter_event_mode.assert_not_called()

    # Event acceptance charges entry, one discrete update, return to
    # continuous time, state read, derivative/output evaluation, and indicator.
    event_candidate_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(20)
    retained_fmi_two_runtime.get_derivatives.return_value = [-1.0]
    retained_fmi_two_runtime.get_real.return_value = dict()
    retained_fmi_two_runtime.get_event_indicators.return_value = (0.25,)
    retained_fmi_two_adapter._prepare_bound_step(
        current_time=1.0,
        step_size=0.5,
        input_values=dict(decay_rate=1.0),
        evaluation_budget=event_candidate_budget,
    )
    event_state_value: float = float(retained_fmi_two_adapter.state_vector[0])
    retained_fmi_two_runtime.reset_mock()
    retained_fmi_two_runtime.needs_completed_integrator_step.return_value = False
    retained_fmi_two_runtime.new_discrete_states.return_value = FmiTwoEventUpdate(
        discrete_states_need_update=False,
        terminate_simulation=False,
        nominals_changed=False,
        states_changed=False,
        next_event_time=None,
    )
    retained_fmi_two_runtime.get_continuous_states.return_value = [
        event_state_value
    ]
    retained_fmi_two_runtime.get_derivatives.return_value = [-1.0]
    retained_fmi_two_runtime.get_real.return_value = dict()
    retained_fmi_two_runtime.get_event_indicators.return_value = (0.25,)
    fmi_two_event_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(6)
    retained_fmi_two_adapter.resolve_pending_step(
        accepted=True,
        importer_detected_event=True,
        evaluation_budget=fmi_two_event_budget,
    )
    assert fmi_two_event_budget.get_consumed_count() == 6
    retained_fmi_two_runtime.enter_event_mode.assert_called_once()
    retained_fmi_two_runtime.new_discrete_states.assert_called_once()
    retained_fmi_two_runtime.enter_continuous_time_mode.assert_called_once()
    retained_fmi_two_runtime.get_continuous_states.assert_called_once()
    retained_fmi_two_runtime.get_derivatives.assert_called_once()
    retained_fmi_two_runtime.get_real.assert_called_once()
    retained_fmi_two_runtime.get_event_indicators.assert_called_once()

    retained_fmi_three_adapter: FmuMeDeviceAdapter
    retained_fmi_three_coordinator: Mock
    retained_fmi_three_adapter, retained_fmi_three_coordinator = (
        _build_mock_backward_euler_adapter()
    )
    retained_fmi_three_adapter.state_vector = np.array([1.0], dtype=float)
    retained_fmi_three_coordinator.get_accepted_point.return_value = (
        0.0,
        (1.0,),
        (1.0,),
        tuple(),
        (0.5,),
        (1.0,),
        (-1.0,),
    )
    retained_fmi_three_coordinator.evaluate_candidate.return_value = (
        (-2.0 / 3.0,),
        tuple(),
        (0.25,),
    )
    retained_fmi_three_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(20)
    retained_fmi_three_adapter._prepare_bound_step(
        current_time=0.0,
        step_size=0.5,
        input_values=dict(decay_rate=1.0),
        evaluation_budget=retained_fmi_three_budget,
    )
    retained_fmi_three_solver_calls: int = (
        retained_fmi_three_coordinator.evaluate_probe.call_count
    )
    retained_fmi_three_coordinator.evaluate_candidate.assert_called_once()
    assert retained_fmi_three_budget.get_consumed_count() == (
        retained_fmi_three_solver_calls + 1
    )

    # Exercise every FMI 3 checkpoint/no-checkpoint branch that adds charges
    # outside the numerical solve: initialization, both localization forms,
    # rejection, smooth acceptance, and event acceptance.
    checkpoint_is_supported: bool
    for checkpoint_is_supported in (True, False):
        coordinator_session: Mock = Mock()
        coordinator_session.supports_fmu_state_checkpoint.return_value = (
            checkpoint_is_supported
        )
        coordinator_session.update_model_exchange_discrete_states.return_value = (
            FmiThreeWorkerDiscreteStatesResult(
                discrete_states_need_update=False,
                terminate_simulation=False,
                nominals_of_continuous_states_changed=False,
                values_of_continuous_states_changed=False,
                next_event_time_defined=False,
                next_event_time=0.0,
            )
        )
        coordinator_session.read_model_exchange_state_and_values.return_value = (
            (1.0,),
            (2.0,),
        )
        coordinator_session.get_model_exchange_event_indicators.return_value = (
            0.25,
        )
        coordinator_session.get_model_exchange_continuous_state_nominals.return_value = (
            1.0,
        )
        coordinator_session.evaluate_model_exchange.return_value = (
            (-1.0,),
            (2.0,),
        )
        coordinator_session.needs_completed_integrator_step.return_value = False
        coordinator_session.complete_model_exchange_integrator_step.return_value = (
            FmiThreeWorkerCompletedIntegratorStepResult(
                enter_event_mode=False,
                terminate_simulation=False,
            )
        )
        runtime_coordinator: FmiThreeModelExchangeCoordinator = (
            FmiThreeModelExchangeCoordinator(
                session=coordinator_session,
                maximum_event_iterations=2,
            )
        )
        initialization_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(20)
        runtime_coordinator.initialize(
            start_time=0.0,
            stop_time=1.0,
            relative_tolerance=1.0e-6,
            initial_writable_values=(1.0,),
            evaluation_budget=initialization_budget,
        )
        expected_initialization_charge: int = (
            9 if checkpoint_is_supported else 8
        )
        assert initialization_budget.get_consumed_count() == (
            expected_initialization_charge
        )
        assert coordinator_session.initialize_model_exchange.call_count == 1
        assert coordinator_session.update_model_exchange_discrete_states.call_count == 1
        assert coordinator_session.read_model_exchange_state_and_values.call_count == 1
        assert coordinator_session.evaluate_model_exchange.call_count == 1
        assert coordinator_session.get_model_exchange_event_indicators.call_count == 2
        assert coordinator_session.save_checkpoint.call_count == int(
            checkpoint_is_supported
        )

        runtime_coordinator.evaluate_candidate(
            time_value=0.25,
            continuous_state_values=(0.8,),
            writable_values=(1.0,),
            presented_derivative_values=(-0.8,),
            presented_readable_values=(2.0,),
        )
        coordinator_session.reset_mock()
        coordinator_session.evaluate_model_exchange.return_value = (
            (-0.8,),
            (2.0,),
        )
        presented_probe_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(10)
        runtime_coordinator.evaluate_event_indicators_probe(
            time_value=0.125,
            continuous_state_values=(0.9,),
            point_is_presented=True,
            evaluation_budget=presented_probe_budget,
        )
        expected_presented_probe_charge: int = (
            4 if checkpoint_is_supported else 3
        )
        assert presented_probe_budget.get_consumed_count() == (
            expected_presented_probe_charge
        )
        assert coordinator_session.evaluate_model_exchange.call_count == 1
        assert coordinator_session.get_model_exchange_event_indicators.call_count == 2
        assert coordinator_session.restore_checkpoint.call_count == int(
            checkpoint_is_supported
        )

        coordinator_session.evaluate_model_exchange.return_value = (
            (-1.0,),
            (2.0,),
        )
        rejection_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(3)
        runtime_coordinator.reject_candidate(evaluation_budget=rejection_budget)
        expected_rejection_charge: int = 1 if checkpoint_is_supported else 2
        assert rejection_budget.get_consumed_count() == expected_rejection_charge

        runtime_coordinator.evaluate_candidate(
            time_value=0.25,
            continuous_state_values=(0.8,),
            writable_values=(1.0,),
            presented_derivative_values=(-0.8,),
            presented_readable_values=(2.0,),
        )
        coordinator_session.reset_mock()
        coordinator_session.evaluate_model_exchange.return_value = (
            (-0.8,),
            (2.0,),
        )
        non_presented_probe_budget: FmuMeEvaluationBudget = (
            FmuMeEvaluationBudget(10)
        )
        runtime_coordinator.evaluate_event_indicators_probe(
            time_value=0.125,
            continuous_state_values=(0.9,),
            point_is_presented=False,
            evaluation_budget=non_presented_probe_budget,
        )
        expected_non_presented_probe_charge: int = (
            5 if checkpoint_is_supported else 4
        )
        assert non_presented_probe_budget.get_consumed_count() == (
            expected_non_presented_probe_charge
        )
        assert coordinator_session.evaluate_model_exchange.call_count == 2
        assert coordinator_session.get_model_exchange_event_indicators.call_count == 2
        coordinator_session.evaluate_model_exchange.return_value = (
            (-1.0,),
            (2.0,),
        )
        second_rejection_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(3)
        runtime_coordinator.reject_candidate(
            evaluation_budget=second_rejection_budget
        )
        assert second_rejection_budget.get_consumed_count() == (
            expected_rejection_charge
        )

        runtime_coordinator.evaluate_candidate(
            time_value=0.25,
            continuous_state_values=(0.8,),
            writable_values=(1.0,),
            presented_derivative_values=(-0.8,),
            presented_readable_values=(2.0,),
        )
        coordinator_session.reset_mock()
        coordinator_session.needs_completed_integrator_step.return_value = True
        smooth_acceptance_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(3)
        runtime_coordinator.accept_candidate(
            importer_detected_event=False,
            evaluation_budget=smooth_acceptance_budget,
        )
        expected_smooth_acceptance_charge: int = (
            2 if checkpoint_is_supported else 1
        )
        assert smooth_acceptance_budget.get_consumed_count() == (
            expected_smooth_acceptance_charge
        )
        assert coordinator_session.complete_model_exchange_integrator_step.call_count == 1
        assert coordinator_session.save_checkpoint.call_count == int(
            checkpoint_is_supported
        )

        runtime_coordinator.evaluate_candidate(
            time_value=0.5,
            continuous_state_values=(0.6,),
            writable_values=(1.0,),
            presented_derivative_values=(-0.6,),
            presented_readable_values=(2.0,),
        )
        coordinator_session.reset_mock()
        coordinator_session.needs_completed_integrator_step.return_value = False
        coordinator_session.evaluate_model_exchange.return_value = (
            (-1.0,),
            (2.0,),
        )
        event_acceptance_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(10)
        runtime_coordinator.accept_candidate(
            importer_detected_event=True,
            evaluation_budget=event_acceptance_budget,
        )
        expected_event_acceptance_charge: int = (
            8 if checkpoint_is_supported else 7
        )
        assert event_acceptance_budget.get_consumed_count() == (
            expected_event_acceptance_charge
        )
        assert coordinator_session.enter_model_exchange_event_mode.call_count == 1
        assert coordinator_session.update_model_exchange_discrete_states.call_count == 1
        assert coordinator_session.read_model_exchange_state_and_values.call_count == 1
        assert coordinator_session.get_model_exchange_event_indicators.call_count == 1
        assert coordinator_session.evaluate_model_exchange.call_count == 1
        assert coordinator_session.save_checkpoint.call_count == int(
            checkpoint_is_supported
        )


def test_backward_euler_matches_analytic_decay() -> None:
    """Match the exact Backward Euler solution of scalar linear decay.

    :return: None.
    """

    adapter: FmuMeDeviceAdapter
    coordinator: Mock
    adapter, coordinator = _build_mock_backward_euler_adapter()
    evaluation_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(10)
    candidate_states: np.ndarray
    endpoint_derivatives: np.ndarray
    readable_values: tuple[float, ...] | None
    candidate_states, endpoint_derivatives, readable_values = (
        adapter._solve_backward_euler_candidate(
            current_time=0.0,
            step_size=0.1,
            accepted_state_values=np.array([1.0], dtype=float),
            input_values=dict(decay_rate=2.0),
            evaluation_budget=evaluation_budget,
        )
    )

    expected_state: float = 1.0 / 1.2
    assert candidate_states.tolist() == pytest.approx([expected_state])
    assert endpoint_derivatives.tolist() == pytest.approx([-2.0 * expected_state])
    assert readable_values == tuple()
    assert coordinator.evaluate_probe.call_count == 4
    assert evaluation_budget.get_consumed_count() == 4


def test_backward_euler_newton_exact_iterates_and_probe_order() -> None:
    """Expose predictor, perturbation, and corrected endpoint probe order.

    :return: None.
    """

    adapter: FmuMeDeviceAdapter
    coordinator: Mock
    adapter, coordinator = _build_mock_backward_euler_adapter()
    evaluation_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(10)
    candidate_states: np.ndarray
    ignored_derivatives: np.ndarray
    ignored_readable_values: tuple[float, ...] | None
    candidate_states, ignored_derivatives, ignored_readable_values = (
        adapter._solve_backward_euler_candidate(
            current_time=0.0,
            step_size=0.25,
            accepted_state_values=np.array([2.0], dtype=float),
            input_values=dict(decay_rate=0.5),
            evaluation_budget=evaluation_budget,
        )
    )

    probe_calls: list[object] = coordinator.evaluate_probe.call_args_list
    probe_times: list[float] = [
        float(probe_call.kwargs["time_value"])
        for probe_call in probe_calls
    ]
    probe_states: list[float] = [
        float(probe_call.kwargs["continuous_state_values"][0])
        for probe_call in probe_calls
    ]
    assert probe_times == pytest.approx([0.0, 0.25, 0.25, 0.25])
    assert probe_states[0] == pytest.approx(2.0)
    assert probe_states[1] == pytest.approx(1.75)
    assert probe_states[2] > probe_states[1]
    assert probe_states[3] == pytest.approx(2.0 / 1.125)
    assert candidate_states.tolist() == pytest.approx([2.0 / 1.125])


def test_backward_euler_scaled_vector_and_zero_state() -> None:
    """Solve disparate state scales and the zero-state endpoint path.

    :return: None.
    """

    adapter: FmuMeDeviceAdapter
    ignored_coordinator: Mock
    adapter, ignored_coordinator = _build_mock_backward_euler_adapter()
    evaluation_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(20)
    accepted_states: np.ndarray = np.array([1.0e-12, 1.0e6], dtype=float)
    candidate_states: np.ndarray
    ignored_derivatives: np.ndarray
    ignored_readable_values: tuple[float, ...] | None
    candidate_states, ignored_derivatives, ignored_readable_values = (
        adapter._solve_backward_euler_candidate(
            current_time=1.0,
            step_size=0.2,
            accepted_state_values=accepted_states,
            input_values=dict(decay_rate=0.25),
            evaluation_budget=evaluation_budget,
        )
    )
    assert candidate_states.tolist() == pytest.approx(
        (accepted_states / 1.05).tolist()
    )

    zero_adapter: FmuMeDeviceAdapter
    zero_coordinator: Mock
    zero_adapter, zero_coordinator = _build_mock_backward_euler_adapter()
    zero_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(1)
    zero_states: np.ndarray
    zero_derivatives: np.ndarray
    zero_readable_values: tuple[float, ...] | None
    zero_states, zero_derivatives, zero_readable_values = (
        zero_adapter._solve_backward_euler_candidate(
            current_time=0.0,
            step_size=0.1,
            accepted_state_values=np.zeros(0, dtype=float),
            input_values=dict(decay_rate=0.25),
            evaluation_budget=zero_budget,
        )
    )
    assert zero_states.size == 0
    assert zero_derivatives.size == 0
    assert zero_readable_values == tuple()
    assert zero_coordinator.evaluate_probe.call_count == 1
    assert zero_budget.get_consumed_count() == 1


def test_backward_euler_rejects_nonfinite_singular_and_exhausted() -> None:
    """Fail closed for non-finite, singular, and unconverged solves.

    :return: None.
    """

    nonfinite_adapter: FmuMeDeviceAdapter
    nonfinite_coordinator: Mock
    nonfinite_adapter, nonfinite_coordinator = _build_mock_backward_euler_adapter()
    nonfinite_coordinator.evaluate_probe.side_effect = None
    nonfinite_coordinator.evaluate_probe.return_value = ((math.nan,), tuple())
    with pytest.raises(FmuModeError, match="derivative vector"):
        nonfinite_adapter._solve_backward_euler_candidate(
            current_time=0.0,
            step_size=1.0,
            accepted_state_values=np.array([1.0], dtype=float),
            input_values=dict(decay_rate=1.0),
            evaluation_budget=FmuMeEvaluationBudget(10),
        )

    singular_adapter: FmuMeDeviceAdapter
    singular_coordinator: Mock
    singular_adapter, singular_coordinator = _build_mock_backward_euler_adapter()
    perturbation: float = math.sqrt(np.finfo(np.float64).eps)
    singular_coordinator.evaluate_probe.side_effect = [
        ((0.0,), tuple()),
        ((1.0,), tuple()),
        ((1.0 + perturbation,), tuple()),
    ]
    with pytest.raises(FmuModeError, match="Jacobian is singular"):
        singular_adapter._solve_backward_euler_candidate(
            current_time=0.0,
            step_size=1.0,
            accepted_state_values=np.array([1.0], dtype=float),
            input_values=dict(decay_rate=1.0),
            evaluation_budget=FmuMeEvaluationBudget(10),
        )

    exhausted_policy: FmuMeSolverPolicy = FmuMeSolverPolicy(
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        maximum_newton_iterations=1,
        maximum_continuous_states=128,
    )
    exhausted_adapter: FmuMeDeviceAdapter
    exhausted_coordinator: Mock
    exhausted_adapter, exhausted_coordinator = _build_mock_backward_euler_adapter(
        exhausted_policy
    )
    exhausted_coordinator.evaluate_probe.side_effect = [
        ((0.0,), tuple()),
        ((1.0,), tuple()),
        ((1.0,), tuple()),
        ((0.0,), tuple()),
    ]
    with pytest.raises(FmuModeError, match="iteration limit was exhausted"):
        exhausted_adapter._solve_backward_euler_candidate(
            current_time=0.0,
            step_size=1.0,
            accepted_state_values=np.array([1.0], dtype=float),
            input_values=dict(decay_rate=1.0),
            evaluation_budget=FmuMeEvaluationBudget(10),
        )


def test_backward_euler_state_and_shared_evaluation_bounds() -> None:
    """Enforce the 128-state and shared-call limits at exact boundaries.

    :return: None.
    """

    adapter: FmuMeDeviceAdapter
    coordinator: Mock
    adapter, coordinator = _build_mock_backward_euler_adapter()
    bounded_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(2)
    bounded_states: np.ndarray
    ignored_derivatives: np.ndarray
    ignored_readable_values: tuple[float, ...] | None
    bounded_states, ignored_derivatives, ignored_readable_values = (
        adapter._solve_backward_euler_candidate(
            current_time=0.0,
            step_size=0.1,
            accepted_state_values=np.zeros(128, dtype=float),
            input_values=dict(decay_rate=0.0),
            evaluation_budget=bounded_budget,
        )
    )
    assert bounded_states.size == 128
    assert bounded_budget.get_consumed_count() == 2

    coordinator.reset_mock()
    rejected_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(2)
    with pytest.raises(FmuModeError, match="state count exceeds"):
        adapter._solve_backward_euler_candidate(
            current_time=0.0,
            step_size=0.1,
            accepted_state_values=np.zeros(129, dtype=float),
            input_values=dict(decay_rate=0.0),
            evaluation_budget=rejected_budget,
        )
    coordinator.evaluate_probe.assert_not_called()
    assert rejected_budget.get_consumed_count() == 0

    owner_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(100000)
    operation_index: int
    for operation_index in range(100000):
        owner_budget.consume()
    assert operation_index == 99999
    assert owner_budget.get_consumed_count() == 100000
    with pytest.raises(FmuModeError, match="before the next native call"):
        owner_budget.consume()
    assert owner_budget.get_consumed_count() == 100000


def test_fmi_me_budget_survives_localized_retry_rms() -> None:
    """Share one RMS budget across localization and coordinated rollback.

    :return: None.
    """

    localized_times: tuple[float, float, float] = (0.5, 0.5000000001, 0.75)
    wrappers: list[SimpleNamespace] = [SimpleNamespace()] * 3
    wrapper_index: int
    for wrapper_index in range(3):
        runtime_adapter: Mock = Mock()
        runtime_adapter.get_pending_state_event_time.return_value = (
            localized_times[wrapper_index]
        )
        runtime_adapter.prepare_state_event_retry.return_value = (1.0,)
        mapped_outputs: dict[VarPowerFlowReferenceType, float] = dict()
        mapped_outputs[VarPowerFlowReferenceType.P] = 1.0
        runtime_adapter._map_bound_output_values.return_value = mapped_outputs
        wrappers[wrapper_index] = SimpleNamespace(
            runtime_adapter=runtime_adapter,
            last_outputs=dict(),
            apply_outputs=Mock(),
        )
    shared_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(100000)
    problem: SimpleNamespace = SimpleNamespace(
        _fmu_me_adapters=wrappers,
        _variable_parameters_values=np.zeros(1, dtype=float),
        _last_variable_parameters_values=None,
        _fmu_me_evaluation_budget=shared_budget,
    )

    retry_time: float | None = _prepare_rms_fmu_me_state_event_retry(
        problem=problem,
        state_event_time_tolerance=1.0e-9,
        state_event_max_iterations=40,
    )

    assert retry_time == pytest.approx(0.5)
    expected_event_times: tuple[float | None, ...] = (0.5, 0.5, None)
    wrapper: SimpleNamespace
    for wrapper_index in range(3):
        wrapper = wrappers[wrapper_index]
        wrapper.runtime_adapter.prepare_state_event_retry.assert_called_once_with(
            event_time=expected_event_times[wrapper_index],
            evaluation_budget=shared_budget,
        )
        wrapper.apply_outputs.assert_called_once()


def test_fmi_me_budget_survives_localized_retry_emt() -> None:
    """Keep the EMT ME budget through retry before advancing CS.

    :return: None.
    """

    problem: SimpleNamespace = SimpleNamespace(
        emt_boundary_update=Mock(),
        options=SimpleNamespace(
            fmi_state_event_time_tolerance=1.0e-9,
            fmi_state_event_max_iterations=40,
            fmi_me_max_runtime_evaluations_per_step=100000,
        ),
    )
    cs_outputs: dict[VarPowerFlowReferenceType, float] = dict()
    cs_outputs[VarPowerFlowReferenceType.P] = 2.0
    cs_adapter: Mock = Mock()
    cs_adapter.last_time = 0.0
    cs_adapter.advance.return_value = cs_outputs
    me_outputs: dict[VarPowerFlowReferenceType, float] = dict()
    me_outputs[VarPowerFlowReferenceType.P] = 1.0
    me_runtime_adapter: Mock = Mock()
    me_runtime_adapter.get_pending_state_event_time.return_value = 0.5
    me_runtime_adapter.prepare_state_event_retry.return_value = (1.0,)
    me_runtime_adapter._map_bound_output_values.return_value = me_outputs
    me_adapter: Mock = Mock()
    me_adapter.last_time = 0.0
    me_adapter.pending_previous_time = 0.0
    me_adapter.runtime_adapter = me_runtime_adapter
    me_adapter.advance.return_value = me_outputs
    updater: CompositeEmtBoundaryUpdater = CompositeEmtBoundaryUpdater(
        problem=problem,
        cs_adapters=[cs_adapter],
        me_adapters=[me_adapter],
    )
    updater.initialized = True
    params: np.ndarray = np.zeros(1, dtype=float)

    retry_time: float | None = updater.update(
        time_value=1.0,
        x_snapshot=np.zeros(1, dtype=float),
        full_params=params,
    )
    assert retry_time == pytest.approx(0.5)
    me_adapter.advance.assert_called_once()
    cs_adapter.advance.assert_not_called()
    me_runtime_adapter.prepare_state_event_retry.assert_called_once_with(
        event_time=0.5,
        evaluation_budget=updater.me_evaluation_budget,
    )

    me_runtime_adapter.get_pending_state_event_time.return_value = None
    updater.update(
        time_value=0.5,
        x_snapshot=np.zeros(1, dtype=float),
        full_params=params,
    )
    cs_adapter.advance.assert_called_once()

    initial_adapter: Mock = Mock()
    initial_adapter.pending_previous_time = None
    initial_updater: CompositeEmtBoundaryUpdater = CompositeEmtBoundaryUpdater(
        problem=SimpleNamespace(),
        cs_adapters=list(),
        me_adapters=[initial_adapter],
    )
    initial_retry_time: float | None = initial_updater.resolve_step(
        accepted=True,
        params=np.zeros(1, dtype=float),
    )
    assert initial_retry_time is None
    initial_adapter.resolve_step.assert_not_called()


def test_state_event_localization_supports_one_transition_per_indicator() -> None:
    """Give each crossing one bracket and reject an insufficient bound early.

    :return: None.
    """

    adapter: FmuMeDeviceAdapter
    coordinator: Mock
    adapter, coordinator = _build_synthetic_localization_adapter(
        accepted_time=0.0,
        candidate_time=1.0,
        accepted_states=(1.0,),
        candidate_states=(0.5,),
        accepted_indicators=(0.3, 0.4),
        candidate_indicators=(-0.2, -0.1),
    )
    assert adapter._get_pending_state_event_crossing_indices() == (0, 1)
    evaluation_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(100000)
    localized_time: float | None = adapter.get_pending_state_event_time(
        time_tolerance=1.0e-9,
        maximum_iterations=40,
        evaluation_budget=evaluation_budget,
    )
    assert localized_time == pytest.approx(3.0 / 7.0, abs=1.0e-9)
    assert coordinator.evaluate_event_indicators_probe.call_count == 60

    coordinator.reset_mock()
    preflight_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(100000)
    with pytest.raises(
        FmuModeError,
        match="localization bound cannot meet its tolerance",
    ):
        adapter.get_pending_state_event_time(
            time_tolerance=1.0e-12,
            maximum_iterations=1,
            evaluation_budget=preflight_budget,
        )
    coordinator.evaluate_probe.assert_not_called()
    coordinator.evaluate_event_indicators_probe.assert_not_called()
    assert preflight_budget.get_consumed_count() == 0

    # Endpoint signs alone cannot identify the earliest of three transitions.
    transition_times: tuple[float, float, float] = (0.2, 0.5, 0.8)
    full_start_value: float = (-0.2) * (-0.5) * (-0.8)
    full_end_value: float = 0.8 * 0.5 * 0.2
    assert adapter._get_pending_state_event_crossing_indices(
        accepted_indicators=(full_start_value,),
        candidate_indicators=(full_end_value,),
    ) == (0,)
    reduced_transition_count: int = 0
    transition_time: float
    for transition_time in transition_times:
        if 0.0 < transition_time <= 0.3:
            reduced_transition_count += 1
        else:
            pass
    assert reduced_transition_count == 1
    reduced_end_value: float = 0.1 * (-0.2) * (-0.5)
    assert full_start_value < 0.0 < reduced_end_value


def test_backward_euler_localization_uses_method_consistent_midpoint_fmi_two() -> None:
    """Localize FMI 2 by solving every midpoint with Backward Euler.

    :return: None.
    """

    adapter: FmuMeDeviceAdapter
    ignored_coordinator: Mock
    adapter, ignored_coordinator = _build_synthetic_localization_adapter(
        accepted_time=0.0,
        candidate_time=1.0,
        accepted_states=(1.0,),
        candidate_states=(0.5,),
        accepted_indicators=(0.3,),
        candidate_indicators=(-0.2,),
    )
    runtime_host: Mock = Mock()
    perturbation: float = math.sqrt(np.finfo(np.float64).eps)
    presented_states: tuple[float, ...] = (
        1.0, 0.5, 0.5 + perturbation, 2.0 / 3.0, 0.5,
        1.0, 0.75, 0.75 + perturbation, 0.8, 0.5,
        1.0, 0.625, 0.625 + perturbation, 1.0 / 1.375, 0.5,
    )
    derivative_results: list[list[float]] = [
        [-presented_state] for presented_state in presented_states
    ]
    runtime_host.get_derivatives.side_effect = derivative_results
    runtime_host.get_real.return_value = dict()
    runtime_host.get_event_indicators.side_effect = [
        (2.0 / 3.0 - 0.7,),
        (-0.2,),
        (0.1,),
        (-0.2,),
        (1.0 / 1.375 - 0.7,),
        (-0.2,),
    ]
    adapter.runtime_host = runtime_host
    adapter.fmi_three_coordinator = None
    evaluation_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(21)

    localized_time: float | None = adapter.get_pending_state_event_time(
        time_tolerance=0.125,
        maximum_iterations=3,
        evaluation_budget=evaluation_budget,
    )

    assert localized_time == pytest.approx(0.5)
    assert runtime_host.get_derivatives.call_count == 15
    assert runtime_host.get_event_indicators.call_count == 6
    assert evaluation_budget.get_consumed_count() == 21
    state_calls: list[object] = runtime_host.set_continuous_states.call_args_list
    state_call_index: int
    for state_call_index in range(len(state_calls)):
        assert state_calls[state_call_index].args[0] == pytest.approx(
            [presented_states[state_call_index]]
        )
        assert derivative_results[state_call_index][0] == pytest.approx(
            -presented_states[state_call_index]
        )
    event_state_indices: tuple[int, ...] = (3, 4, 8, 9, 13, 14)
    event_results: tuple[float, ...] = (
        2.0 / 3.0 - 0.7, -0.2, 0.1, -0.2,
        1.0 / 1.375 - 0.7, -0.2,
    )
    event_result_index: int
    for event_result_index in range(len(event_results)):
        assert event_results[event_result_index] == pytest.approx(
            presented_states[event_state_indices[event_result_index]] - 0.7
        )
    interpolated_midpoint_indicator: float = 0.75 - 0.7
    backward_euler_midpoint_indicator: float = 2.0 / 3.0 - 0.7
    assert interpolated_midpoint_indicator > 0.0
    assert backward_euler_midpoint_indicator < 0.0


def test_backward_euler_localization_uses_method_consistent_midpoint_fmi_three() -> None:
    """Localize FMI 3 stateful and zero-state probes with solver midpoints.

    :return: None.
    """

    adapter: FmuMeDeviceAdapter
    coordinator: Mock
    adapter, coordinator = _build_synthetic_localization_adapter(
        accepted_time=0.0,
        candidate_time=1.0,
        accepted_states=(1.0,),
        candidate_states=(0.5,),
        accepted_indicators=(0.3, 0.4),
        candidate_indicators=(-0.2, -0.1),
    )
    evaluation_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(100000)
    localized_time: float | None = adapter.get_pending_state_event_time(
        time_tolerance=1.0e-9,
        maximum_iterations=40,
        evaluation_budget=evaluation_budget,
    )
    assert localized_time == pytest.approx(3.0 / 7.0, abs=1.0e-9)
    interpolated_midpoint_indicator: float = 0.75 - 0.7
    backward_euler_midpoint_indicator: float = 2.0 / 3.0 - 0.7
    assert interpolated_midpoint_indicator > 0.0
    assert backward_euler_midpoint_indicator < 0.0
    probe_call: object
    for probe_call in coordinator.evaluate_event_indicators_probe.call_args_list:
        assert probe_call.kwargs["point_is_presented"]

    zero_adapter: FmuMeDeviceAdapter
    zero_coordinator: Mock
    zero_adapter, zero_coordinator = _build_synthetic_localization_adapter(
        accepted_time=0.0,
        candidate_time=1.0,
        accepted_states=tuple(),
        candidate_states=tuple(),
        accepted_indicators=(-0.4,),
        candidate_indicators=(0.6,),
    )
    zero_coordinator.evaluate_event_indicators_probe.side_effect = (
        _evaluate_time_test_event_indicator
    )
    zero_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(10)
    zero_localized_time: float | None = zero_adapter.get_pending_state_event_time(
        time_tolerance=0.125,
        maximum_iterations=3,
        evaluation_budget=zero_budget,
    )
    assert zero_localized_time == pytest.approx(0.5)
    assert zero_coordinator.evaluate_probe.call_count == 3
    assert zero_coordinator.evaluate_event_indicators_probe.call_count == 3
