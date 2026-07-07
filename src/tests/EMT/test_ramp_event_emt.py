from __future__ import annotations

from typing import Dict

import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Events.emt_event import EmtEvent
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DynamicEventTransitionType
from VeraGridEngine.enumerations import DynamicIntegrationMethod


class RampEventDemoProblem(EmtProblemTemplate):
    """
    Minimal EMT problem used to validate ramp-event runtime updates.

    :param grid: Grid carrying the EMT event collection.
    :param sys_block: Symbolic block solved by the EMT runtime.
    :param glob_time: Global time variable.
    """

    __slots__ = ["grid"]

    def __init__(self, grid: MultiCircuit, sys_block: Block, glob_time: Var) -> None:
        """
        Store the grid and initialize the EMT problem template.

        :param grid: Grid carrying the event group.
        :param sys_block: Root symbolic block.
        :param glob_time: Global time variable.
        :return: None.
        """
        self.grid = grid
        static_parameter_values_mapping: Dict[Var, Const] = dict(sys_block.parameters)
        super().__init__(
            sys_block=sys_block,
            glob_time=glob_time,
            static_parameter_values_mapping=static_parameter_values_mapping,
        )


def build_ramp_event_demo_problem() -> tuple[RampEventDemoProblem, EmtEventsGroup, Var]:
    """
    Build the minimal first-order EMT system driven by one ramp event.

    :return: Problem, event group, and the tracked runtime parameter.
    """
    vf: VarFactory = VarFactory()
    glob_time: Var = vf.add_var("t_glob_ramp_demo")
    u_input: Var = vf.add_var("u_input_ramp_demo")
    x_state: Var = vf.add_var("x_state_ramp_demo")
    dx_state: Var = vf.add_diff_var(name="dx_state_ramp_demo", base_var=x_state)
    y_output: Var = vf.add_var("y_output_ramp_demo")
    root_block: Block = Block(
        name="RampEventDemo",
        state_vars=list([x_state]),
        diff_vars=list([dx_state]),
        state_eqs=list([Const(8.0) * (u_input - x_state)]),
        algebraic_vars=list([y_output]),
        algebraic_eqs=list([y_output - x_state]),
        event_dict=dict({u_input: Const(0.0, name="u_input")}),
        init_eqs=dict({x_state: Const(0.0), y_output: Const(0.0)}),
    )

    # The event group carries one ramp from 0.2 s to 0.5 s so the runtime updater must interpolate in time.
    grid: MultiCircuit = MultiCircuit()
    event_group: EmtEventsGroup = EmtEventsGroup(name="ramp_event_demo")
    grid.add_emt_events_group(event_group)
    grid.add_emt_event(
        EmtEvent(
            parameter=u_input,
            time=0.2,
            end_time=0.5,
            value=1.0,
            group=event_group,
            transition_type=DynamicEventTransitionType.Ramp,
        )
    )

    problem: RampEventDemoProblem = RampEventDemoProblem(grid=grid, sys_block=root_block, glob_time=glob_time)
    problem.set_events_group(event_group)
    problem.init_guess[x_state.uid] = 0.0
    problem.init_guess[y_output.uid] = 0.0
    return problem, event_group, u_input


def evaluate_runtime_parameter_trace(problem: RampEventDemoProblem, parameter: Var, time_values: np.ndarray) -> np.ndarray:
    """
    Evaluate the runtime parameter after the event updater at each sample time.

    :param problem: EMT problem carrying the event update function.
    :param parameter: Runtime parameter being tracked.
    :param time_values: Sample times.
    :return: Parameter trace evaluated at the supplied times.
    """
    runtime_idx: int = problem.uid2idx_event_params[parameter.uid]
    trace: np.ndarray = np.zeros(len(time_values), dtype=float)
    sample_index: int

    # Each sample applies the exact event interpolation path used by the solver-side runtime state updater.
    for sample_index in range(len(time_values)):
        runtime_values: np.ndarray = problem.event_params_values.copy()
        runtime_values = problem.def_event_params_fn(runtime_values, float(time_values[sample_index]))
        trace[sample_index] = float(runtime_values[runtime_idx])

    return trace


def run_ramp_event_case() -> Dict[str, np.ndarray]:
    """
    Simulate the local ramp-event case and collect the traces needed by the assertions.

    :return: Time, runtime-parameter, state, and output traces.
    """
    problem: RampEventDemoProblem
    _event_group: EmtEventsGroup
    parameter: Var
    solver: JitSymbolicSolver
    time_arr: np.ndarray
    y_hist: np.ndarray
    state_idx: int
    output_idx: int
    traces: Dict[str, np.ndarray] = dict()

    problem, _event_group, parameter = build_ramp_event_demo_problem()
    solver = JitSymbolicSolver(
        problem=problem,
        t0=0.0,
        t_end=1.0,
        h=1.0e-3,
        method=DynamicIntegrationMethod.DaeTrapezoidal,
        verbose=False,
    )
    time_arr, y_hist, _dy_hist, _well_initialized, _converged = solver.simulate(boundary_updater=None)
    time_arr = np.asarray(time_arr, dtype=float)
    y_hist = np.asarray(y_hist, dtype=float)
    state_idx = problem.get_var_idx(problem.get_state_vars()[0])
    output_idx = problem.get_var_idx(problem.get_algebraic_vars()[0])

    traces["time"] = time_arr
    traces["u_input"] = evaluate_runtime_parameter_trace(problem=problem, parameter=parameter, time_values=time_arr)
    traces["x_state"] = np.asarray(y_hist[:, state_idx], dtype=float)
    traces["y_output"] = np.asarray(y_hist[:, output_idx], dtype=float)
    return traces


def test_ramp_event_demo_problem_uses_ramp_transition() -> None:
    """
    Verify that the local test problem registers one EMT ramp event.

    :return: None.
    """
    problem: RampEventDemoProblem
    event_group: EmtEventsGroup
    _parameter: Var
    matching_events: list[EmtEvent]

    problem, event_group, _parameter = build_ramp_event_demo_problem()
    matching_events = [evt for evt in problem.grid.emt_events if evt.group is event_group]

    assert len(matching_events) == 1
    assert matching_events[0].transition_type == DynamicEventTransitionType.Ramp
    assert matching_events[0].end_time == 0.5


def test_ramp_event_case_runs_and_ramps_runtime_parameter() -> None:
    """
    Verify that the runtime event parameter ramps and drives the first-order state.

    :return: None.
    """
    traces: Dict[str, np.ndarray] = run_ramp_event_case()
    time_values: np.ndarray = traces["time"]
    ramp_values: np.ndarray = traces["u_input"]
    idx_before: int = int(np.searchsorted(time_values, 0.15))
    idx_mid: int = int(np.searchsorted(time_values, 0.35))
    idx_after: int = int(np.searchsorted(time_values, 0.7))

    assert float(ramp_values[idx_before]) < 0.05
    assert 0.45 < float(ramp_values[idx_mid]) < 0.55
    assert float(ramp_values[idx_after]) > 0.95
    assert float(np.max(traces["x_state"])) > 0.5
