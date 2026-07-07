# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple
import os

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import BoundaryUpdateWrapper, JitSymbolicSolver
from VeraGridEngine.Utils.procedural_logic import (
    aflipflop,
    DelayedThresholdLatchLogic,
    bool_and,
    bool_or,
    build_boundary_updater_from_block,
    flipflop,
    lastvalue,
    picdro,
    reset,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DynamicIntegrationMethod


class GenericEmtProblem(EmtProblemTemplate):
    """Minimal generic EMT problem used for demo purposes."""

    __slots__ = []


class TracingBoundaryUpdater(BoundaryUpdateWrapper):
    """Wrapper that records selected runtime-parameter traces."""

    __slots__ = ["base_updater", "tracked_indices", "trace_t", "trace_values"]

    def __init__(self, base_updater: BoundaryUpdateWrapper, tracked_indices: Dict[str, int]) -> None:
        self.base_updater = base_updater
        self.tracked_indices = tracked_indices
        self.trace_t: List[float] = []
        self.trace_values: Dict[str, List[float]] = {name: [] for name in tracked_indices.keys()}

    def update(self, t: float, x: np.ndarray, params: np.ndarray) -> None:
        self.base_updater.update(t, x, params)
        self.trace_t.append(float(t))
        for name, idx in self.tracked_indices.items():
            self.trace_values[name].append(float(params[idx]))

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        return self.base_updater.get_next_forced_event_time(t_prev, t_target)

    def get_trace(self, name: str) -> np.ndarray:
        return np.asarray(self.trace_values[name], dtype=float)


def _first_true_time(time_array: np.ndarray, signal: np.ndarray, threshold: float = 0.5) -> Optional[float]:
    idx = np.flatnonzero(signal > threshold)
    if len(idx) == 0:
        return None
    return float(time_array[int(idx[0])])


def _first_cross_time(time_array: np.ndarray, signal: np.ndarray, threshold: float) -> Optional[float]:
    idx = np.flatnonzero(signal >= threshold)
    if len(idx) == 0:
        return None
    return float(time_array[int(idx[0])])


def _add_vertical_marker(ax: plt.Axes, time_value: Optional[float], text: str, *, color: str, linestyle: str) -> None:
    if time_value is None:
        return
    ax.axvline(time_value, color=color, linestyle=linestyle, linewidth=1.4, label=f"{text} = {time_value:.4f} s")


class RichProtectionChainWrapper(BoundaryUpdateWrapper):
    """
    Rich protection chain with comparator, timer, latch, retained mode, and optional reset.

    Logic
    -----
    1. Comparator:
       comparator = measured_value >= threshold

    2. Timer:
       When the comparator rises and there is no active timer, a delayed trip time is scheduled.

    3. Latch:
       When the delayed trip time is reached, the protection latches and the controlled mode is set to 0.

    4. Optional reset:
       If ``reset_delay`` is not None, a reset is scheduled at:
           reset_time = trip_time + reset_delay
       When reset happens, the latch is cleared and the mode returns to 1.

    Notes
    -----
    - The wrapper stores internal traces so the logical chain can be plotted afterwards.
    - The solver can force exact substep alignment at both trip and reset times.
    """

    __slots__ = [
        "mode_idx",
        "monitored_idx",
        "threshold",
        "delay",
        "reset_delay",
        "pickup_time",
        "pending_trip_time",
        "pending_reset_time",
        "tripped",
        "trip_applied_time",
        "trip_applied_solver_time",
        "reset_applied_time",
        "reset_applied_solver_time",
        "last_t_prev",
        "trace_t",
        "trace_measure",
        "trace_comparator",
        "trace_timer_armed",
        "trace_latched",
        "trace_mode",
    ]

    def __init__(
        self,
        problem: EmtProblemTemplate,
        monitored_var: Var,
        mode_var: Var,
        threshold: float,
        delay: float,
        reset_delay: Optional[float] = None,
    ) -> None:
        self.mode_idx: int = problem.uid2idx_event_params[mode_var.uid]
        self.monitored_idx: int = problem.get_var_idx(monitored_var)
        self.threshold: float = float(threshold)
        self.delay: float = float(delay)
        self.reset_delay: Optional[float] = None if reset_delay is None else float(reset_delay)

        self.pickup_time: Optional[float] = None
        self.pending_trip_time: Optional[float] = None
        self.pending_reset_time: Optional[float] = None

        self.tripped: bool = False
        self.trip_applied_time: Optional[float] = None
        self.trip_applied_solver_time: Optional[float] = None
        self.reset_applied_time: Optional[float] = None
        self.reset_applied_solver_time: Optional[float] = None

        self.last_t_prev: Optional[float] = None

        self.trace_t: List[float] = []
        self.trace_measure: List[float] = []
        self.trace_comparator: List[float] = []
        self.trace_timer_armed: List[float] = []
        self.trace_latched: List[float] = []
        self.trace_mode: List[float] = []

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        """
        Return a forced-alignment time if a pending trip or reset lies inside the current EMT step.
        """
        self.last_t_prev = float(t_prev)

        candidate_times: List[float] = []

        if self.pending_trip_time is not None and t_prev < self.pending_trip_time <= t_target:
            candidate_times.append(float(self.pending_trip_time))

        if self.pending_reset_time is not None and t_prev < self.pending_reset_time <= t_target:
            candidate_times.append(float(self.pending_reset_time))

        if len(candidate_times) == 0:
            return None

        return min(candidate_times)

    def _append_trace_point(
            self,
            trace_time: float,
            measured_value: float,
            comparator: float,
            timer_armed: float,
            latched: float,
            mode_value: float,
    ) -> None:
        """
        Append one logic sample to the plotting traces.
        """
        self.trace_t.append(float(trace_time))
        self.trace_measure.append(float(measured_value))
        self.trace_comparator.append(float(comparator))
        self.trace_timer_armed.append(float(timer_armed))
        self.trace_latched.append(float(latched))
        self.trace_mode.append(float(mode_value))

    def _record_sample_trace(
            self,
            sample_time: float,
            measured_value: float,
            params: np.ndarray,
    ) -> None:
        """
        Record the logical state at the physical sample time associated with x.
        """
        comparator: float = 1.0 if measured_value >= self.threshold else 0.0
        timer_armed: float = 1.0 if self.pending_trip_time is not None else 0.0
        latched: float = 1.0 if self.tripped else 0.0
        mode_value: float = float(params[self.mode_idx])

        self._append_trace_point(
            trace_time=sample_time,
            measured_value=measured_value,
            comparator=comparator,
            timer_armed=timer_armed,
            latched=latched,
            mode_value=mode_value,
        )

    def get_trace_arrays(
        self,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Return recorded logic traces as numpy arrays.
        """
        return (
            np.asarray(self.trace_t, dtype=float),
            np.asarray(self.trace_measure, dtype=float),
            np.asarray(self.trace_comparator, dtype=float),
            np.asarray(self.trace_timer_armed, dtype=float),
            np.asarray(self.trace_latched, dtype=float),
            np.asarray(self.trace_mode, dtype=float),
        )

    def update(self, t: float, x: np.ndarray, params: np.ndarray) -> None:
        """
        Update the protection chain and the retained runtime mode.

        Important
        ---------
        - ``x`` corresponds to the previously accepted state, i.e. to ``sample_time``.
        - Therefore comparator/timer traces must be recorded at ``sample_time``.
        - Trip/reset actions, however, must be recorded at the actual event time ``t``.
        """
        tol: float = 1.0e-15
        sample_time: float = float(self.last_t_prev if self.last_t_prev is not None else t)
        measured_value: float = float(x[self.monitored_idx])
        comparator_on: bool = measured_value >= self.threshold
        comparator_value: float = 1.0 if comparator_on else 0.0

        # Case 1: protection already latched
        if self.tripped:
            params[self.mode_idx] = 0.0

            # Optional reset event
            if self.pending_reset_time is not None and t >= (self.pending_reset_time - tol):
                self.tripped = False
                self.reset_applied_time = float(self.pending_reset_time)
                self.reset_applied_solver_time = float(t)

                self.pickup_time = None
                self.pending_trip_time = None
                self.pending_reset_time = None

                params[self.mode_idx] = 1.0

                # Record the reset exactly at the event time
                self._append_trace_point(
                    trace_time=t,
                    measured_value=measured_value,
                    comparator=comparator_value,
                    timer_armed=0.0,
                    latched=0.0,
                    mode_value=1.0,
                )
                return

            # Normal latched evolution: record at physical sample time
            self._record_sample_trace(
                sample_time=sample_time,
                measured_value=measured_value,
                params=params,
            )
            return

        # Case 2: not latched yet, evaluate comparator and timer
        if comparator_on:
            if self.pickup_time is None:
                self.pickup_time = sample_time
                self.pending_trip_time = sample_time + self.delay
        else:
            self.pickup_time = None
            self.pending_trip_time = None

        # Apply trip if the delayed trip time is reached
        if self.pending_trip_time is not None and t >= (self.pending_trip_time - tol):
            self.tripped = True
            self.trip_applied_time = float(self.pending_trip_time)
            self.trip_applied_solver_time = float(t)
            params[self.mode_idx] = 0.0

            if self.reset_delay is not None:
                self.pending_reset_time = self.trip_applied_time + self.reset_delay

            self.pending_trip_time = None

            # Record the trip exactly at the event time
            self._append_trace_point(
                trace_time=t,
                measured_value=measured_value,
                comparator=comparator_value,
                timer_armed=0.0,
                latched=1.0,
                mode_value=0.0,
            )
            return

        # Normal non-tripped case
        params[self.mode_idx] = 1.0
        self._record_sample_trace(
            sample_time=sample_time,
            measured_value=measured_value,
            params=params,
        )


def create_integrator_trip_system(vf: VarFactory) -> Tuple[Block, Dict[str, Var]]:
    """
    Demo system where the protection freezes the integrator.

    Dynamics
    --------
    x_i_dot = mode_int_enable * k_i * (ref - y)
    y_dot   = (x_i - y) / tau
    """
    x_i: Var = vf.add_var("x_i")
    y: Var = vf.add_var("y")

    d_x_i: Var = vf.add_diff_var(name="d_x_i", base_var=x_i)
    d_y: Var = vf.add_diff_var(name="d_y", base_var=y)

    mode_int_enable: Var = vf.add_var("mode_int_enable")

    ref: Var = vf.add_var("ref")
    k_i: Var = vf.add_var("k_i")
    tau: Var = vf.add_var("tau")

    state_vars: List[Var] = [x_i, y]
    diff_vars: List[Var] = [d_x_i, d_y]
    state_eqs: List[Expr] = [
        mode_int_enable * k_i * (ref - y),
        (x_i - y) / tau,
    ]

    parameters: Dict[Var, Const] = {
        ref: Const(1.0),
        k_i: Const(200.0),
        tau: Const(2.0e-3),
    }

    mode_dict: Dict[Var, Const] = {
        mode_int_enable: Const(1.0),
    }

    block = Block(
        name="ModeProtectionIntegratorDemo",
        state_vars=state_vars,
        diff_vars=diff_vars,
        state_eqs=state_eqs,
        parameters=parameters,
        mode_dict=mode_dict,
    )

    return block, {
        "x_i": x_i,
        "y": y,
        "d_x_i": d_x_i,
        "d_y": d_y,
        "mode_var": mode_int_enable,
    }


def create_antiwindup_trip_system(vf: VarFactory) -> Tuple[Block, Dict[str, Var]]:
    """
    Demo system where the protection disables an anti-windup branch.

    Dynamics
    --------
    x_i_dot   = k_i * (ref - y) - mode_aw_enable * k_aw * (x_i - u_act)
    u_act_dot = (x_i - u_act) / tau_act
    y_dot     = (u_act - y) / tau_y
    """
    x_i: Var = vf.add_var("x_i_aw")
    u_act: Var = vf.add_var("u_act_aw")
    y: Var = vf.add_var("y_aw")

    d_x_i: Var = vf.add_diff_var(name="d_x_i_aw", base_var=x_i)
    d_u_act: Var = vf.add_diff_var(name="d_u_act_aw", base_var=u_act)
    d_y: Var = vf.add_diff_var(name="d_y_aw", base_var=y)

    mode_aw_enable: Var = vf.add_var("mode_aw_enable")

    ref: Var = vf.add_var("ref_aw")
    k_i: Var = vf.add_var("k_i_aw")
    k_aw: Var = vf.add_var("k_aw")
    tau_act: Var = vf.add_var("tau_act")
    tau_y: Var = vf.add_var("tau_y")

    state_vars: List[Var] = [x_i, u_act, y]
    diff_vars: List[Var] = [d_x_i, d_u_act, d_y]
    state_eqs: List[Expr] = [
        k_i * (ref - y) - mode_aw_enable * k_aw * (x_i - u_act),
        (x_i - u_act) / tau_act,
        (u_act - y) / tau_y,
    ]

    parameters: Dict[Var, Const] = {
        ref: Const(1.0),
        k_i: Const(200.0),
        k_aw: Const(150.0),
        tau_act: Const(4.0e-3),
        tau_y: Const(2.0e-3),
    }

    mode_dict: Dict[Var, Const] = {
        mode_aw_enable: Const(1.0),
    }

    block = Block(
        name="ModeProtectionAntiWindupDemo",
        state_vars=state_vars,
        diff_vars=diff_vars,
        state_eqs=state_eqs,
        parameters=parameters,
        mode_dict=mode_dict,
    )

    return block, {
        "x_i": x_i,
        "u_act": u_act,
        "y": y,
        "d_x_i": d_x_i,
        "d_u_act": d_u_act,
        "d_y": d_y,
        "mode_var": mode_aw_enable,
    }


def create_boolean_operator_logic_system(vf: VarFactory) -> Tuple[Block, Dict[str, Var]]:
    """
    Demo system using the new procedural helpers with explicit AND/OR logic.

    Logic
    -----
    - `trip_fast = picdro(x_fast > 0.65, 1 ms, 0)`
    - `trip_and = picdro((x_fast > 0.45) AND (x_slow > 0.30), 2 ms, 0)`
    - `master_trip = flipflop(trip_fast OR trip_and, 0)`
    - `x_mem_dot = (1 - master_trip) * k_mem * (x_fast - x_mem)`
    - `x_mem_last = lastvalue(x_mem)`
    - `reset(x_mem, master_trip > 0.5, 0)`
    """
    x_fast: Var = vf.add_var("x_fast_bool")
    x_slow: Var = vf.add_var("x_slow_bool")
    x_mem: Var = vf.add_var("x_mem_bool")

    d_x_fast: Var = vf.add_diff_var(name="d_x_fast_bool", base_var=x_fast)
    d_x_slow: Var = vf.add_diff_var(name="d_x_slow_bool", base_var=x_slow)
    d_x_mem: Var = vf.add_diff_var(name="d_x_mem_bool", base_var=x_mem)

    trip_fast: Var = vf.add_var("trip_fast")
    trip_and: Var = vf.add_var("trip_and")
    master_trip: Var = vf.add_var("master_trip")
    x_mem_last: Var = vf.add_var("x_mem_last")

    tau_fast: Var = vf.add_var("tau_fast_bool")
    tau_slow: Var = vf.add_var("tau_slow_bool")
    k_mem: Var = vf.add_var("k_mem_bool")

    block = Block(
        name="BooleanOperatorProceduralDemo",
        state_vars=[x_fast, x_slow, x_mem],
        diff_vars=[d_x_fast, d_x_slow, d_x_mem],
        state_eqs=[
            (Const(1.0) - x_fast) / tau_fast,
            (Const(1.0) - x_slow) / tau_slow,
            (Const(1.0) - master_trip) * k_mem * (x_fast - x_mem),
        ],
        parameters={
            tau_fast: Const(3.0e-3),
            tau_slow: Const(8.0e-3),
            k_mem: Const(120.0),
        },
        mode_dict={
            trip_fast: Const(0.0),
            trip_and: Const(0.0),
            master_trip: Const(0.0),
            x_mem_last: Const(0.0),
        },
    )

    block.procedural_logic = [
        picdro(x_fast > 0.65, 1.0e-3, 0.0, output=trip_fast, name="trip_fast_channel"),
        picdro(
            bool_and(x_fast > 0.45, x_slow > 0.30),
            2.0e-3,
            0.0,
            output=trip_and,
            name="trip_and_channel",
        ),
        flipflop(
            bool_or(trip_fast > 0.5, trip_and > 0.5),
            0.0,
            output=master_trip,
            name="master_trip_latch",
        ),
        lastvalue(x_mem, output=x_mem_last, name="x_mem_last_sample"),
        reset(x_mem, master_trip > 0.5, 0.0, name="x_mem_reset"),
    ]

    return block, {
        "x_fast": x_fast,
        "x_slow": x_slow,
        "x_mem": x_mem,
        "d_x_fast": d_x_fast,
        "d_x_slow": d_x_slow,
        "d_x_mem": d_x_mem,
        "trip_fast": trip_fast,
        "trip_and": trip_and,
        "master_trip": master_trip,
        "x_mem_last": x_mem_last,
    }


def create_analog_flipflop_logic_system(vf: VarFactory) -> Tuple[Block, Dict[str, Var]]:
    """
    Demo system for `aflipflop(x, boolset, boolreset)`.

    Logic
    -----
    - `set`   when `x_in > 0.45`
    - `reset` when `x_reset > 0.70`
    - `y_hold = aflipflop(x_in, set, reset)`

    Expected behavior
    -----------------
    - before set: `y_hold = x_in`
    - after set:  `y_hold` stores the value of `x_in` at the set instant
    - after reset: `y_hold` follows `x_in` again
    """
    x_in: Var = vf.add_var("x_in_af_demo")
    x_reset: Var = vf.add_var("x_reset_af_demo")

    d_x_in: Var = vf.add_diff_var(name="d_x_in_af_demo", base_var=x_in)
    d_x_reset: Var = vf.add_diff_var(name="d_x_reset_af_demo", base_var=x_reset)

    y_hold: Var = vf.add_var("y_hold_af_demo")
    ff_state: Var = vf.add_var("ff_state_af_demo")

    tau_rise: Var = vf.add_var("tau_rise_af_demo")
    tau_fall: Var = vf.add_var("tau_fall_af_demo")
    tau_reset: Var = vf.add_var("tau_reset_af_demo")

    set_expr = x_in > 0.45
    reset_expr = x_reset > 0.70

    block = Block(
        name="AnalogFlipFlopProceduralDemo",
        state_vars=[x_in, x_reset],
        diff_vars=[d_x_in, d_x_reset],
        state_eqs=[
            (Const(1.0) - ff_state) * (Const(1.0) - x_in) / tau_rise - ff_state * x_in / tau_fall,
            (Const(1.0) - x_reset) / tau_reset,
        ],
        parameters={
            tau_rise: Const(2.5e-3),
            tau_fall: Const(1.5e-3),
            tau_reset: Const(7.5e-3),
        },
        mode_dict={
            y_hold: Const(0.0),
            ff_state: Const(0.0),
        },
    )

    block.procedural_logic = [
        aflipflop(x_in, set_expr, reset_expr, output=y_hold, name="analog_hold"),
        flipflop(set_expr, reset_expr, output=ff_state, name="analog_hold_state"),
    ]

    return block, {
        "x_in": x_in,
        "x_reset": x_reset,
        "y_hold": y_hold,
        "ff_state": ff_state,
    }


def run_case(
    builder,
    threshold: float,
    delay: float,
    t_end: float,
    dt: float,
    reset_delay: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, EmtProblemTemplate, Dict[str, Var], DelayedThresholdLatchLogic]:
    """
    Build, simulate, and return a demo case.
    """
    vf = VarFactory()
    block, vars_map = builder(vf=vf)
    logic = DelayedThresholdLatchLogic(
        monitored_var_name=vars_map["y"].name,
        mode_var_name=vars_map["mode_var"].name,
        threshold=threshold,
        delay=delay,
        reset_delay=reset_delay,
        name=f"logic_{block.name}",
    )
    block.procedural_logic = [logic]
    block.unify_blocks()

    glob_time: Var = vf.add_var("t_glob")
    static_parameter_values_mapping: Dict[Var, Const] = dict(block.parameters)
    problem = GenericEmtProblem(
        sys_block=block,
        glob_time=glob_time,
        static_parameter_values_mapping=static_parameter_values_mapping,
    )

    solver = JitSymbolicSolver(
        problem=problem,
        t0=0.0,
        t_end=t_end,
        h=dt,
        method=DynamicIntegrationMethod.DaeTrapezoidal,
        verbose=False,
    )

    protection = build_boundary_updater_from_block(problem)
    assert protection is not None

    params0 = problem.event_params_values.copy()
    t, y_hist, dy_hist, _, _ = solver.simulate(params0=params0, boundary_updater=protection)

    return t, y_hist, dy_hist, problem, vars_map, logic


def run_boolean_operator_case(
    t_end: float,
    dt: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, EmtProblemTemplate, Dict[str, Var], TracingBoundaryUpdater]:
    """Build and run the helper-based AND/OR procedural demo."""
    vf = VarFactory()
    block, vars_map = create_boolean_operator_logic_system(vf=vf)
    block.unify_blocks()

    static_parameter_values_mapping: Dict[Var, Const] = dict(block.parameters)
    problem = GenericEmtProblem(
        sys_block=block,
        glob_time=vf.add_var("t_glob_bool_demo"),
        static_parameter_values_mapping=static_parameter_values_mapping,
    )
    base_updater = build_boundary_updater_from_block(problem)
    assert base_updater is not None

    tracked_indices = {
        "trip_fast": problem.uid2idx_event_params[vars_map["trip_fast"].uid],
        "trip_and": problem.uid2idx_event_params[vars_map["trip_and"].uid],
        "master_trip": problem.uid2idx_event_params[vars_map["master_trip"].uid],
        "x_mem_last": problem.uid2idx_event_params[vars_map["x_mem_last"].uid],
    }
    tracing_updater = TracingBoundaryUpdater(base_updater=base_updater, tracked_indices=tracked_indices)

    solver = JitSymbolicSolver(
        problem=problem,
        t0=0.0,
        t_end=t_end,
        h=dt,
        method=DynamicIntegrationMethod.DaeTrapezoidal,
        verbose=False,
    )

    params0 = problem.event_params_values.copy()
    t, y_hist, dy_hist, _, _ = solver.simulate(params0=params0, boundary_updater=tracing_updater)
    return t, y_hist, dy_hist, problem, vars_map, tracing_updater


def run_analog_flipflop_case(
    t_end: float,
    dt: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, EmtProblemTemplate, Dict[str, Var], TracingBoundaryUpdater]:
    """Build and run the helper-based aflipflop demo."""
    vf = VarFactory()
    block, vars_map = create_analog_flipflop_logic_system(vf=vf)
    block.unify_blocks()

    static_parameter_values_mapping: Dict[Var, Const] = dict(block.parameters)
    problem = GenericEmtProblem(
        sys_block=block,
        glob_time=vf.add_var("t_glob_af_demo"),
        static_parameter_values_mapping=static_parameter_values_mapping,
    )
    base_updater = build_boundary_updater_from_block(problem)
    assert base_updater is not None

    tracked_indices = {
        "y_hold": problem.uid2idx_event_params[vars_map["y_hold"].uid],
        "ff_state": problem.uid2idx_event_params[vars_map["ff_state"].uid],
    }
    tracing_updater = TracingBoundaryUpdater(base_updater=base_updater, tracked_indices=tracked_indices)

    solver = JitSymbolicSolver(
        problem=problem,
        t0=0.0,
        t_end=t_end,
        h=dt,
        method=DynamicIntegrationMethod.DaeTrapezoidal,
        verbose=False,
    )

    params0 = problem.event_params_values.copy()
    t, y_hist, dy_hist, _, _ = solver.simulate(params0=params0, boundary_updater=tracing_updater)
    return t, y_hist, dy_hist, problem, vars_map, tracing_updater


def add_event_lines(ax: plt.Axes, protection: DelayedThresholdLatchLogic) -> None:
    """
    Add vertical lines for pickup, trip, and optional reset.
    """
    if protection.pickup_time is not None:
        ax.axvline(
            protection.pickup_time,
            linestyle=":",
            linewidth=1.5,
            label=f"pickup = {protection.pickup_time:.6f} s",
        )

    if protection.trip_applied_time is not None:
        ax.axvline(
            protection.trip_applied_time,
            linestyle="--",
            linewidth=1.5,
            label=f"trip = {protection.trip_applied_time:.6f} s",
        )

    if protection.reset_applied_time is not None:
        ax.axvline(
            protection.reset_applied_time,
            linestyle="-.",
            linewidth=1.5,
            label=f"reset = {protection.reset_applied_time:.6f} s",
        )


def plot_logic_panel(
    ax: plt.Axes,
    protection: DelayedThresholdLatchLogic,
) -> None:
    """
    Plot internal logic signals of the protection chain.
    """
    logic_t, _, comparator, timer_armed, latched, mode_value = protection.get_trace_arrays()

    ax.step(logic_t, comparator + 0.0, where="post", label="comparator")
    ax.step(logic_t, timer_armed + 1.2, where="post", label="timer armed")
    ax.step(logic_t, latched + 2.4, where="post", label="latch")
    ax.step(logic_t, mode_value + 3.6, where="post", label="mode")

    add_event_lines(ax=ax, protection=protection)

    ax.set_yticks([0.5, 1.7, 2.9, 4.1])
    ax.set_yticklabels(["cmp", "timer", "latch", "mode"])
    ax.set_ylim(-0.2, 4.8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Logic")
    ax.grid(True)
    ax.legend(loc="upper right")


def plot_integrator_case(
    t: np.ndarray,
    y_hist: np.ndarray,
    dy_hist: np.ndarray,
    problem: EmtProblemTemplate,
    vars_map: Dict[str, Var],
    protection: DelayedThresholdLatchLogic,
) -> None:
    """
    Plot the integrator-freeze demo plus its internal logic.
    """
    idx_x_i: int = problem.get_var_idx(vars_map["x_i"])
    idx_y: int = problem.get_var_idx(vars_map["y"])
    idx_d_x_i: int = problem.get_diff_var_idx(vars_map["d_x_i"])

    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(11, 8),
        sharex=True,
        height_ratios=[3.0, 1.6],
    )

    ax_dyn = axes[0]
    ax_logic = axes[1]

    ax_dyn.plot(t, y_hist[:, idx_x_i], label="x_i")
    ax_dyn.plot(t, y_hist[:, idx_y], label="y")
    ax_dyn.plot(t, dy_hist[:, idx_d_x_i], label="d_x_i")
    ax_dyn.axhline(protection.threshold, linestyle=":", linewidth=1.2, label=f"threshold = {protection.threshold:.3f}")

    add_event_lines(ax=ax_dyn, protection=protection)

    ax_dyn.set_title("Demo 1: Protection freezes integrator")
    ax_dyn.set_ylabel("Value")
    ax_dyn.grid(True)
    ax_dyn.legend(loc="upper right")

    plot_logic_panel(ax=ax_logic, protection=protection)

    fig.tight_layout()


def plot_antiwindup_case(
    t: np.ndarray,
    y_hist: np.ndarray,
    dy_hist: np.ndarray,
    problem: EmtProblemTemplate,
    vars_map: Dict[str, Var],
    protection: DelayedThresholdLatchLogic,
) -> None:
    """
    Plot the anti-windup-disable demo plus its internal logic.
    """
    idx_x_i: int = problem.get_var_idx(vars_map["x_i"])
    idx_u_act: int = problem.get_var_idx(vars_map["u_act"])
    idx_y: int = problem.get_var_idx(vars_map["y"])
    idx_d_x_i: int = problem.get_diff_var_idx(vars_map["d_x_i"])

    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(11, 8),
        sharex=True,
        height_ratios=[3.0, 1.6],
    )

    ax_dyn = axes[0]
    ax_logic = axes[1]

    ax_dyn.plot(t, y_hist[:, idx_x_i], label="x_i")
    ax_dyn.plot(t, y_hist[:, idx_u_act], label="u_act")
    ax_dyn.plot(t, y_hist[:, idx_y], label="y")
    ax_dyn.plot(t, dy_hist[:, idx_d_x_i], label="d_x_i")
    ax_dyn.axhline(protection.threshold, linestyle=":", linewidth=1.2, label=f"threshold = {protection.threshold:.3f}")

    add_event_lines(ax=ax_dyn, protection=protection)

    ax_dyn.set_title("Demo 2: Protection disables anti-windup branch")
    ax_dyn.set_ylabel("Value")
    ax_dyn.grid(True)
    ax_dyn.legend(loc="upper right")

    plot_logic_panel(ax=ax_logic, protection=protection)

    fig.tight_layout()


def plot_boolean_operator_case(
    t: np.ndarray,
    y_hist: np.ndarray,
    problem: EmtProblemTemplate,
    vars_map: Dict[str, Var],
    tracing_updater: TracingBoundaryUpdater,
) -> None:
    """Plot the helper-based AND/OR procedural demo."""
    idx_x_fast: int = problem.get_var_idx(vars_map["x_fast"])
    idx_x_slow: int = problem.get_var_idx(vars_map["x_slow"])
    idx_x_mem: int = problem.get_var_idx(vars_map["x_mem"])

    logic_t = np.asarray(tracing_updater.trace_t, dtype=float)
    trip_fast = tracing_updater.get_trace("trip_fast")
    trip_and = tracing_updater.get_trace("trip_and")
    master_trip = tracing_updater.get_trace("master_trip")
    x_mem_last = tracing_updater.get_trace("x_mem_last")

    x_fast_hist = y_hist[:, idx_x_fast]
    x_slow_hist = y_hist[:, idx_x_slow]
    x_mem_hist = y_hist[:, idx_x_mem]

    t_fast_pickup = _first_cross_time(t, x_fast_hist, 0.65)
    t_and_pickup = _first_true_time(t, ((x_fast_hist > 0.45) & (x_slow_hist > 0.30)).astype(float))
    t_fast_trip = _first_true_time(logic_t, trip_fast)
    t_and_trip = _first_true_time(logic_t, trip_and)
    t_master_trip = _first_true_time(logic_t, master_trip)

    x_mem_last_before_trip: Optional[float] = None
    if t_master_trip is not None:
        idx_trip = np.where(np.isclose(logic_t, t_master_trip))[0]
        if len(idx_trip) > 0:
            x_mem_last_before_trip = float(x_mem_last[int(idx_trip[0])])

    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(11, 8),
        sharex=True,
        height_ratios=[3.0, 1.6],
    )

    ax_dyn = axes[0]
    ax_logic = axes[1]

    ax_dyn.plot(t, x_fast_hist, label="x_fast")
    ax_dyn.plot(t, x_slow_hist, label="x_slow")
    ax_dyn.plot(t, x_mem_hist, label="x_mem")
    ax_dyn.step(logic_t, x_mem_last, where="post", linestyle="--", label="lastvalue(x_mem)")
    ax_dyn.axhline(0.65, linestyle=":", linewidth=1.1, label="trip_fast threshold")
    ax_dyn.axhline(0.45, linestyle=":", linewidth=1.1, label="AND fast threshold")
    ax_dyn.axhline(0.30, linestyle="-.", linewidth=1.1, label="AND slow threshold")
    if x_mem_last_before_trip is not None:
        ax_dyn.axhline(
            x_mem_last_before_trip,
            color="tab:red",
            linestyle="--",
            linewidth=1.1,
            label=f"last sample before reset = {x_mem_last_before_trip:.4f}",
        )

    _add_vertical_marker(ax_dyn, t_fast_pickup, "fast pickup start", color="tab:blue", linestyle=":")
    _add_vertical_marker(ax_dyn, t_and_pickup, "AND pickup start", color="tab:orange", linestyle=":")
    _add_vertical_marker(ax_dyn, t_fast_trip, "fast trip", color="tab:blue", linestyle="--")
    _add_vertical_marker(ax_dyn, t_and_trip, "AND trip", color="tab:orange", linestyle="--")
    _add_vertical_marker(ax_dyn, t_master_trip, "master latch / reset", color="tab:green", linestyle="-.")
    ax_dyn.set_title("Demo 3: Procedural helpers with AND / OR / reset / lastvalue")
    ax_dyn.set_ylabel("Value")
    ax_dyn.grid(True)
    ax_dyn.legend(loc="upper right")

    ax_logic.step(logic_t, trip_fast + 0.0, where="post", label="trip_fast = picdro(x_fast > 0.65)")
    ax_logic.step(logic_t, trip_and + 1.2, where="post", label="trip_and = picdro((x_fast > 0.45) AND (x_slow > 0.30))")
    ax_logic.step(logic_t, master_trip + 2.4, where="post", label="master_trip = flipflop(trip_fast OR trip_and, 0)")
    _add_vertical_marker(ax_logic, t_fast_pickup, "fast pickup start", color="tab:blue", linestyle=":")
    _add_vertical_marker(ax_logic, t_and_pickup, "AND pickup start", color="tab:orange", linestyle=":")
    _add_vertical_marker(ax_logic, t_fast_trip, "fast trip", color="tab:blue", linestyle="--")
    _add_vertical_marker(ax_logic, t_and_trip, "AND trip", color="tab:orange", linestyle="--")
    _add_vertical_marker(ax_logic, t_master_trip, "master latch / reset", color="tab:green", linestyle="-.")
    ax_logic.set_yticks([0.5, 1.7, 2.9])
    ax_logic.set_yticklabels(["fast", "and", "or latch"])
    ax_logic.set_ylim(-0.2, 3.6)
    ax_logic.set_xlabel("Time [s]")
    ax_logic.set_ylabel("Logic")
    ax_logic.grid(True)
    ax_logic.legend(loc="upper right")

    fig.tight_layout()


def plot_analog_flipflop_case(
    t: np.ndarray,
    y_hist: np.ndarray,
    problem: EmtProblemTemplate,
    vars_map: Dict[str, Var],
    tracing_updater: TracingBoundaryUpdater,
) -> None:
    """Plot the helper-based aflipflop demo."""
    idx_x_in: int = problem.get_var_idx(vars_map["x_in"])
    idx_x_reset: int = problem.get_var_idx(vars_map["x_reset"])

    x_in_hist = y_hist[:, idx_x_in]
    x_reset_hist = y_hist[:, idx_x_reset]
    logic_t = np.asarray(tracing_updater.trace_t, dtype=float)
    y_hold = tracing_updater.get_trace("y_hold")
    ff_state = tracing_updater.get_trace("ff_state")

    t_set = _first_true_time(logic_t, ff_state)
    t_reset = None
    reset_idx = np.flatnonzero((ff_state[:-1] > 0.5) & (ff_state[1:] < 0.5)) if len(ff_state) >= 2 else np.array([], dtype=int)
    if len(reset_idx) > 0:
        t_reset = float(logic_t[int(reset_idx[0]) + 1])

    held_value = None
    if t_set is not None:
        idx_hold = np.where(np.isclose(logic_t, t_set))[0]
        if len(idx_hold) > 0:
            held_value = float(y_hold[int(idx_hold[0])])

    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(11, 8),
        sharex=True,
        height_ratios=[3.0, 1.6],
    )

    ax_dyn = axes[0]
    ax_logic = axes[1]

    ax_dyn.plot(t, x_in_hist, label="x_in")
    ax_dyn.plot(t, x_reset_hist, label="x_reset")
    ax_dyn.step(logic_t, y_hold, where="post", linestyle="--", linewidth=2.0, label="y_hold = aflipflop(x_in, set, reset)")
    ax_dyn.axhline(0.45, linestyle=":", linewidth=1.1, label="set threshold")
    ax_dyn.axhline(0.70, linestyle="-.", linewidth=1.1, label="reset threshold")
    if held_value is not None:
        ax_dyn.axhline(held_value, color="tab:red", linestyle="--", linewidth=1.1, label=f"held value = {held_value:.4f}")
    _add_vertical_marker(ax_dyn, t_set, "set / capture", color="tab:blue", linestyle="--")
    _add_vertical_marker(ax_dyn, t_reset, "reset / release", color="tab:orange", linestyle="-.")
    ax_dyn.set_title("Demo 4: aflipflop stores and releases an analog value")
    ax_dyn.set_ylabel("Value")
    ax_dyn.grid(True)
    ax_dyn.legend(loc="upper right")

    set_signal = (x_in_hist > 0.45).astype(float)
    reset_signal = (x_reset_hist > 0.70).astype(float)
    ax_logic.step(t, set_signal + 0.0, where="post", label="set = (x_in > 0.45)")
    ax_logic.step(t, reset_signal + 1.2, where="post", label="reset = (x_reset > 0.70)")
    ax_logic.step(logic_t, ff_state + 2.4, where="post", label="internal state")
    _add_vertical_marker(ax_logic, t_set, "set / capture", color="tab:blue", linestyle="--")
    _add_vertical_marker(ax_logic, t_reset, "reset / release", color="tab:orange", linestyle="-.")
    ax_logic.set_yticks([0.5, 1.7, 2.9])
    ax_logic.set_yticklabels(["set", "reset", "state"])
    ax_logic.set_ylim(-0.2, 3.6)
    ax_logic.set_xlabel("Time [s]")
    ax_logic.set_ylabel("Logic")
    ax_logic.grid(True)
    ax_logic.legend(loc="upper right")

    fig.tight_layout()


def print_boolean_operator_summary(tracing_updater: TracingBoundaryUpdater) -> None:
    """Print a compact summary of the helper-based boolean demo."""
    logic_t = np.asarray(tracing_updater.trace_t, dtype=float)
    trip_fast = tracing_updater.get_trace("trip_fast")
    trip_and = tracing_updater.get_trace("trip_and")
    master_trip = tracing_updater.get_trace("master_trip")
    x_mem_last = tracing_updater.get_trace("x_mem_last")

    t_fast_trip = _first_true_time(logic_t, trip_fast)
    t_and_trip = _first_true_time(logic_t, trip_and)
    t_master_trip = _first_true_time(logic_t, master_trip)

    print("=== Demo 3: AND / OR helper-based procedural logic ===")
    print("trip_fast = picdro(x_fast > 0.65, 1e-3, 0)")
    print("trip_and  = picdro(bool_and(x_fast > 0.45, x_slow > 0.30), 2e-3, 0)")
    print("master    = flipflop(bool_or(trip_fast > 0.5, trip_and > 0.5), 0)")
    print("x_mem_dot = (1 - master_trip) * k_mem * (x_fast - x_mem)")
    print(f"fast trip time:         {t_fast_trip}")
    print(f"and trip time:          {t_and_trip}")
    print(f"master trip time:       {t_master_trip}")
    print(f"final trip_fast:         {trip_fast[-1] if len(trip_fast) else 'n/a'}")
    print(f"final trip_and:          {trip_and[-1] if len(trip_and) else 'n/a'}")
    print(f"final master_trip:       {master_trip[-1] if len(master_trip) else 'n/a'}")
    print(f"final lastvalue(x_mem):  {x_mem_last[-1] if len(x_mem_last) else 'n/a'}")
    print("")


def print_analog_flipflop_summary(tracing_updater: TracingBoundaryUpdater) -> None:
    """Print a compact summary of the aflipflop demo."""
    logic_t = np.asarray(tracing_updater.trace_t, dtype=float)
    y_hold = tracing_updater.get_trace("y_hold")
    ff_state = tracing_updater.get_trace("ff_state")

    t_set = _first_true_time(logic_t, ff_state)
    t_reset = None
    reset_idx = np.flatnonzero((ff_state[:-1] > 0.5) & (ff_state[1:] < 0.5)) if len(ff_state) >= 2 else np.array([], dtype=int)
    if len(reset_idx) > 0:
        t_reset = float(logic_t[int(reset_idx[0]) + 1])

    held_value = None
    if t_set is not None:
        idx_hold = np.where(np.isclose(logic_t, t_set))[0]
        if len(idx_hold) > 0:
            held_value = float(y_hold[int(idx_hold[0])])

    print("=== Demo 4: aflipflop analog memory ===")
    print("y_hold = aflipflop(x_in, x_in > 0.45, x_reset > 0.70)")
    print(f"set time:              {t_set}")
    print(f"reset time:            {t_reset}")
    print(f"captured value:        {held_value}")
    print(f"final aflipflop value: {y_hold[-1] if len(y_hold) else 'n/a'}")
    print("")


def print_case_summary(name: str, protection: DelayedThresholdLatchLogic) -> None:
    """
    Print a compact summary of the protection sequence.
    """
    print(f"=== {name} ===")
    print(f"pickup_time:             {protection.pickup_time}")
    print(f"trip_applied_time:       {protection.trip_applied_time}")
    print(f"trip_solver_time:        {protection.trip_applied_solver_time}")
    print(f"reset_applied_time:      {protection.reset_applied_time}")
    print(f"reset_solver_time:       {protection.reset_applied_solver_time}")
    print(f"final_latched_state:     {protection.tripped}")
    print("")


def test_modes_procedural_logic() -> None:
    """
    Run the two demos.

    Notes
    -----
    To demonstrate the optional reset, you can set for example:
        reset_delay = 8.0e-3
    in one of the calls below.
    """
    # retrieve reference results df
    name = "modes_procedural_logic.csv"
    fname = os.path.join(os.path.dirname(__file__), '..', 'data', 'dynamics', name)
    reference_df = pd.read_csv(fname)

    dt: float = 1.0e-3

    t1, y1, dy1, problem1, vars1, prot1 = run_case(
        builder=create_integrator_trip_system,
        threshold=0.20,
        delay=1.5e-3,
        t_end=2.0e-2,
        dt=dt,
        reset_delay=None,
    )

    t2, y2, dy2, problem2, vars2, prot2 = run_case(
        builder=create_antiwindup_trip_system,
        threshold=0.12,
        delay=1.5e-3,
        t_end=3.0e-2,
        dt=dt,
        reset_delay=None,
    )

    t3, y3, _, problem3, vars3, tracing3 = run_boolean_operator_case(
        t_end=2.0e-2,
        dt=dt,
    )

    t4, y4, _, problem4, vars4, tracing4 = run_analog_flipflop_case(
        t_end=2.0e-2,
        dt=dt,
    )

    df1 = pd.DataFrame(
        np.concatenate((y1, dy1), axis=1),
        index=t1,
        columns=[f"y1{i}" for i in range(y1.shape[1])] + [f"dy1{i}" for i in range(dy1.shape[1])]
    )
    df2 = pd.DataFrame(
        np.concatenate((y2, dy2), axis=1),
        index=t2,
        columns=[f"y2{i}" for i in range(y2.shape[1])] + [f"dy2{i}" for i in range(dy2.shape[1])]
    )
    df3 = pd.DataFrame(
        y3,
        index=t3,
        columns=[f"y3{i}" for i in range(y3.shape[1])]
    )
    df4 = pd.DataFrame(
        y4,
        index=t4,
        columns=[f"y4{i}" for i in range(y4.shape[1])]
    )

    results_df = pd.concat((df1, df2, df3, df4), axis=1)
    # results_df.to_csv("modes_procedural_logic_FROMTEST.csv", index=False)

    assert_frame_equal(
        results_df.reset_index(drop=True),
        reference_df.reset_index(drop=True),
        check_dtype=False,
        check_index_type=False,
        atol=1e-6
    )


