from __future__ import annotations

import numpy as np

from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Templates.Rms.load_rms_template import get_load_rms_template
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
from VeraGridEngine.enumerations import DynamicEventTransitionType
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.enumerations import RmsInitializationMethod
import VeraGridEngine.api as gce


def _find_name_in_block(name: str, block: Block) -> Var | None:
    """
    Find one variable by name inside a block hierarchy.

    The real RMS script resolves event targets and plotted outputs by variable
    name. The test uses the same lookup strategy so that it exercises the exact
    runtime parameter path used by the load ramp script instead of relying on a
    synthetic standalone block.

    :param name: Variable name to locate.
    :param block: Root block to inspect.
    :return: Matching variable or ``None``.
    """
    variable: Var

    for variable in block.algebraic_vars + block.state_vars + list(block.event_dict.keys()):
        if name == variable.name:
            return variable
        else:
            pass

    child_block: Block

    for child_block in block.children:
        child_result: Var | None = _find_name_in_block(name=name, block=child_block)
        if child_result is not None:
            return child_result
        else:
            pass

    return None


def _build_real_load_ramp_problem() -> tuple[RmsProblemDae, Var, Var]:
    """
    Build the real RMS load-model scenario used by the debugging script.

    The failure was not in a generic symbolic ramp expression alone. It depended
    on how the RMS load template registers ``Pl0`` through ``event_dict`` and on
    how the RMS problem classifies that parameter. The test therefore reproduces
    the actual device-model chain so the classification, compilation and runtime
    evaluation stages are all exercised together.

    :return: Prepared problem, runtime event parameter and algebraic load output.
    """
    grid: MultiCircuit = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus_slack: Bus = gce.Bus(name="Bus0", Vnom=10.0, is_slack=True)
    bus_load: Bus = gce.Bus(name="Bus1", Vnom=10.0)
    load: Load = gce.Load(P=9.999999, Q=0.999999)
    event_group: RmsEventsGroup = RmsEventsGroup(name="rms_ramp_demo")

    grid.add_bus(bus_slack)
    grid.add_bus(bus_load)
    grid.add_load(bus=bus_load, api_obj=load)
    grid.add_rms_events_group(event_group)

    bus: Bus

    for bus in grid.buses:
        initialize_bus_rms(bus, vf=grid.var_factory)

    load_model: Block = get_load_rms_template(grid.var_factory).block
    set_rms_model(device=load, model=load_model, var_factory=grid.var_factory)

    parameter_pl0: Var | None = _find_name_in_block(name="Pl0", block=load_model)
    output_pl: Var | None = _find_name_in_block(name="Pl", block=load_model)

    if parameter_pl0 is None:
        raise AssertionError("Expected load event parameter 'Pl0' was not found.")
    else:
        pass

    if output_pl is None:
        raise AssertionError("Expected load algebraic output 'Pl' was not found.")
    else:
        pass

    event: RmsEvent = RmsEvent(device=load,
                               parameter=parameter_pl0,
                               time=0.1,
                               end_time=0.2,
                               value=-0.06,
                               group=event_group,
                               transition_type=DynamicEventTransitionType.Ramp)
    grid.add_rms_event(event)

    options_pf = gce.PowerFlowOptions(solver_type=gce.SolverType.NR,
                                      retry_with_other_methods=False,
                                      verbose=0,
                                      initialize_with_existing_solution=True,
                                      tolerance=1e-6,
                                      max_iter=25,
                                      control_q=False,
                                      control_taps_modules=True,
                                      control_taps_phase=True,
                                      control_remote_voltage=True,
                                      orthogonalize_controls=True,
                                      apply_temperature_correction=True,
                                      branch_impedance_tolerance_mode=gce.BranchImpedanceMode.Specified,
                                      distributed_slack=False,
                                      ignore_single_node_islands=False,
                                      trust_radius=1.0,
                                      backtracking_parameter=0.05,
                                      use_stored_guess=False,
                                      initialize_angles=False,
                                      generate_report=False)
    pf_results = gce.power_flow(grid, options=options_pf)

    options_rms: RmsOptions = RmsOptions(time_step=1.0e-3,
                                         simulation_time=1.0,
                                         tolerance=1.0e-6,
                                         integration_method=DynamicIntegrationMethod.DaeBackEuler,
                                         initialization_method=RmsInitializationMethod.Explicit,
                                         use_init_values=False,
                                         max_iter=1000,
                                         verbose=0)

    problem: RmsProblemDae = RmsProblemDae(grid=grid,
                                           options=options_rms,
                                           pf_results=pf_results)
    problem.set_events_group(event_group)
    problem.reset_boundary_update_state(0.0)

    return problem, parameter_pl0, output_pl


def _evaluate_runtime_trace(problem: RmsProblemDae,
                            runtime_parameter: Var,
                            time_values: np.ndarray) -> np.ndarray:
    """
    Evaluate one compiled RMS runtime parameter trace.

    The runtime event-parameter function is the canonical source that tells
    whether the solver sees a step or a ramp. The test samples this function at
    explicit times so the expected linear profile can be checked numerically.

    :param problem: Prepared RMS problem.
    :param runtime_parameter: Runtime parameter to inspect.
    :param time_values: Sample times.
    :return: Evaluated runtime trace.
    """
    runtime_index: int = problem.uid2idx_event_params[runtime_parameter.uid]
    trace: np.ndarray = np.zeros(len(time_values), dtype=float)
    sample_index: int = 0

    while sample_index < len(time_values):
        runtime_values: np.ndarray = problem._variable_parameters_values.copy()
        runtime_values = problem.def_event_params_fn(runtime_values, float(time_values[sample_index]))
        trace[sample_index] = float(runtime_values[runtime_index])
        sample_index += 1

    return trace


def _evaluate_algebraic_output_trace(problem: RmsProblemDae,
                                     runtime_parameter: Var,
                                     algebraic_output: Var,
                                     time_values: np.ndarray) -> np.ndarray:
    """
    Evaluate the algebraic load output driven by one runtime ramp parameter.

    The real bug report came from the plotted load power, not only from the raw
    runtime parameter. This helper therefore propagates the sampled runtime value
    into the algebraic equation of the load block so the test confirms that the
    downstream symbolic equation sees the same ramp.

    :param problem: Prepared RMS problem.
    :param runtime_parameter: Runtime parameter to sample.
    :param algebraic_output: Algebraic output depending on the runtime parameter.
    :param time_values: Sample times.
    :return: Evaluated algebraic output trace.
    """
    runtime_index: int = problem.uid2idx_event_params[runtime_parameter.uid]
    output_index: int = problem.get_var_idx(algebraic_output)
    trace: np.ndarray = np.zeros(len(time_values), dtype=float)
    state_vector: np.ndarray = problem.get_x0().copy()
    sample_index: int = 0

    while sample_index < len(time_values):
        runtime_values: np.ndarray = problem._variable_parameters_values.copy()
        runtime_values = problem.def_event_params_fn(runtime_values, float(time_values[sample_index]))
        state_vector[output_index] = float(runtime_values[runtime_index])
        trace[sample_index] = float(state_vector[output_index])
        sample_index += 1

    return trace


def test_rms_load_ramp_event_is_classified_as_continuous() -> None:
    """
    Verify that the real RMS load parameter follows the continuous event path.

    The historical bug came from classifying ``Pl0`` as a discrete parameter
    because its initialization expression referenced the algebraic load output.
    This assertion guards the exact registration state required for a continuous
    ramp to exist at all.

    :return: None.
    """
    problem: RmsProblemDae
    runtime_parameter: Var
    algebraic_output: Var

    problem, runtime_parameter, algebraic_output = _build_real_load_ramp_problem()

    assert runtime_parameter.uid in problem._continuous_event_parameter_uids
    assert runtime_parameter.uid not in problem._discrete_event_parameter_uids
    assert problem.uid2idx_event_params[runtime_parameter.uid] < problem.get_variable_parameter_number()
    assert algebraic_output.uid in problem.uid2idx_vars


def test_rms_load_ramp_runtime_trace_matches_expected_linear_profile() -> None:
    """
    Verify exact runtime samples for the real RMS load ramp event.

    The event starts from the initialized steady-state load power near ``-0.1``
    pu, ramps linearly to ``-0.06`` pu on ``[0.1, 0.2]`` seconds, and then holds
    the final value. Exact sample checks make the test sensitive to regressions
    that would otherwise still satisfy a vague intermediate-value assertion.

    :return: None.
    """
    problem: RmsProblemDae
    runtime_parameter: Var
    algebraic_output: Var
    time_values: np.ndarray = np.array([0.0, 0.1, 0.125, 0.15, 0.175, 0.2, 0.25], dtype=float)
    trace: np.ndarray
    expected_trace: np.ndarray

    problem, runtime_parameter, algebraic_output = _build_real_load_ramp_problem()
    trace = _evaluate_runtime_trace(problem=problem,
                                    runtime_parameter=runtime_parameter,
                                    time_values=time_values)
    expected_trace = np.array([-0.09999999,
                               -0.09999999,
                               -0.0899999925,
                               -0.079999995,
                               -0.0699999975,
                               -0.06,
                               -0.06], dtype=float)

    assert np.allclose(trace, expected_trace, atol=1.0e-9, rtol=0.0)


def test_rms_load_ramp_algebraic_output_matches_runtime_parameter() -> None:
    """
    Verify that the load algebraic output follows the ramped runtime parameter.

    A correct fix must not stop at compiling the runtime parameter alone. The
    consuming algebraic equation ``Pl - Pl0 = 0`` must see the same values so the
    plotted load power uses the continuous ramp rather than a step-latched proxy.

    :return: None.
    """
    problem: RmsProblemDae
    runtime_parameter: Var
    algebraic_output: Var
    time_values: np.ndarray = np.array([0.0, 0.1, 0.125, 0.15, 0.175, 0.2, 0.25], dtype=float)
    runtime_trace: np.ndarray
    output_trace: np.ndarray

    problem, runtime_parameter, algebraic_output = _build_real_load_ramp_problem()
    runtime_trace = _evaluate_runtime_trace(problem=problem,
                                            runtime_parameter=runtime_parameter,
                                            time_values=time_values)
    output_trace = _evaluate_algebraic_output_trace(problem=problem,
                                                    runtime_parameter=runtime_parameter,
                                                    algebraic_output=algebraic_output,
                                                    time_values=time_values)

    assert np.allclose(output_trace, runtime_trace, atol=1.0e-12, rtol=0.0)
