import numpy as np
import scipy.sparse as sp

from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import project_initial_algebraic_state
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.explicit_initialization_symbolic import (
    build_explicit_external_uid_values,
    build_explicit_init_graph,
    evaluate_explicit_init_equation,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import sampled_value


class DirectAlgebraicProjectionProblem(RmsProblemTemplate):
    """Minimal RMS problem exposing one direct algebraic constraint."""

    __slots__ = ()

    def get_states_number(self) -> int:
        """Return the single fixed state count.

        :return: One state variable.
        """
        return 1

    def rhs_algebraic(self, values: np.ndarray, diff_values: np.ndarray) -> np.ndarray:
        """Evaluate ``algebraic - 2 * state``.

        :param values: State and algebraic values.
        :param diff_values: Unused differential values.
        :return: Single algebraic residual.
        """
        _unused_diff_values: np.ndarray = diff_values
        return np.array([values[1] - 2.0 * values[0]], dtype=float)

    def get_j22(
            self,
            x: np.ndarray,
            dx: np.ndarray,
            h: float,
    ) -> sp.csc_matrix:
        """Return the algebraic Jacobian.

        :param x: Unused state and algebraic values.
        :param dx: Unused differential values.
        :param h: Unused integration step.
        :return: Unit sparse Jacobian.
        """
        _unused_x: np.ndarray = x
        _unused_dx: np.ndarray = dx
        _unused_h: float = h
        return sp.csc_matrix(np.array([[1.0]], dtype=float))


def test_direct_algebraic_dependency_precedes_explicit_initialization() -> None:
    """Resolve an algebraic bridge before an ``inc``-style state seed.

    :return: None.
    """
    physical_signal: Var = Var("physical_signal")
    algebraic_bridge: Var = Var("algebraic_bridge")
    controller_state: Var = Var("controller_state")
    block: Block = Block(
        state_vars=list((controller_state,)),
        state_eqs=list((Const(0.0),)),
        algebraic_vars=list((physical_signal, algebraic_bridge)),
        algebraic_eqs=list((algebraic_bridge - physical_signal,)),
        init_eqs=dict((
            (physical_signal, Const(0.275)),
            (controller_state, algebraic_bridge),
        )),
        name="Direct algebraic initialization dependency",
    )

    init_vars: dict[Var, Expr | Const]
    dependencies: dict[Var, list[Var]]
    topological_order: list[Var]
    init_events: dict[Var, Expr | Const]
    init_vars, dependencies, topological_order, init_events = build_explicit_init_graph(mdl=block)

    assert init_vars[algebraic_bridge] is physical_signal
    assert dependencies[algebraic_bridge] == list((physical_signal,))
    assert topological_order.index(physical_signal) < topological_order.index(algebraic_bridge)
    assert topological_order.index(algebraic_bridge) < topological_order.index(controller_state)
    assert len(init_events) == 0


def test_sampled_mode_source_selects_explicit_initialization_branch() -> None:
    """Evaluate a sampled mode source before a dependent state initializer.

    :return: None.
    """
    selected_output: Var = Var("selected_output")
    sampled_mode: Var = Var("sampled_mode")
    controller_state: Var = Var("controller_state")
    block: Block = Block(
        state_vars=list((controller_state,)),
        state_eqs=list((Const(0.0),)),
        algebraic_vars=list((selected_output,)),
        algebraic_eqs=list((selected_output - Const(1.0),)),
        init_eqs=dict(((controller_state, sampled_mode * Const(2.0)),)),
        mode_dict=dict(((sampled_mode, Const(0.0)),)),
        procedural_logic=list((
            sampled_value(
                output=sampled_mode,
                source=selected_output,
            ),
        )),
        name="Sampled mode initialization dependency",
    )

    init_vars: dict[Var, Expr | Const]
    dependencies: dict[Var, list[Var]]
    topological_order: list[Var]
    init_events: dict[Var, Expr | Const]
    init_vars, dependencies, topological_order, init_events = build_explicit_init_graph(mdl=block)

    selected_output_equation: Expr | Const = init_vars[selected_output]
    assert isinstance(selected_output_equation, Const)
    assert selected_output_equation.value == 1.0
    assert init_vars[sampled_mode] is selected_output
    assert dependencies[sampled_mode] == list((selected_output,))
    assert topological_order.index(selected_output) < topological_order.index(sampled_mode)
    assert topological_order.index(sampled_mode) < topological_order.index(controller_state)
    assert init_events[sampled_mode] is selected_output


def test_direct_algebraic_initialization_preserves_external_seed() -> None:
    """Consume a power-flow seed without replacing it from a direct residual.

    :return: None.
    """
    physical_power: Var = Var("physical_power")
    measured_power: Var = Var("measured_power")
    controller_state: Var = Var("controller_state")
    block: Block = Block(
        state_vars=list((controller_state,)),
        state_eqs=list((Const(0.0),)),
        algebraic_vars=list((physical_power, measured_power)),
        algebraic_eqs=list((
            physical_power - Const(0.0),
            measured_power - physical_power,
        )),
        init_eqs=dict(((controller_state, measured_power),)),
        name="Externally seeded physical power",
    )

    init_vars: dict[Var, Expr | Const]
    dependencies: dict[Var, list[Var]]
    topological_order: list[Var]
    init_events: dict[Var, Expr | Const]
    init_vars, dependencies, topological_order, init_events = build_explicit_init_graph(
        mdl=block,
        preserved_var_uids=set((physical_power.uid,)),
    )

    assert physical_power not in init_vars
    assert init_vars[measured_power] is physical_power
    assert dependencies[measured_power] == list()
    assert topological_order.index(measured_power) < topological_order.index(controller_state)
    assert len(init_events) == 0


def test_explicit_initialization_binds_external_time_by_exact_uid() -> None:
    """Evaluate an imported ``time()`` expression at the RMS startup instant.

    :return: None.
    """
    global_time: Var = Var("glob_time")
    sampled_time: Var = Var("sampled_time")
    block: Block = Block(
        algebraic_vars=list((sampled_time,)),
        algebraic_eqs=list((sampled_time - global_time,)),
        name="External startup time",
    )
    external_uid_values: dict[int, float] = build_explicit_external_uid_values(
        mdl=block,
        external_name_values=dict((("glob_time", 0.0),)),
    )

    assert external_uid_values == dict(((global_time.uid, 0.0),))
    result: float | int | complex | None = evaluate_explicit_init_equation(
        eq=global_time,
        event_params_array=np.zeros(0, dtype=float),
        x=np.zeros(1, dtype=float),
        params_array=np.zeros(0, dtype=float),
        dx=np.zeros(0, dtype=float),
        uid2idx_event_params=dict(),
        uid2idx_vars=dict(((sampled_time.uid, 0),)),
        uid2idx_params=dict(),
        uid2idx_diff=dict(),
        external_uid_values=external_uid_values,
    )
    assert result == 0.0


def test_initial_algebraic_projection_preserves_states() -> None:
    """Project algebraics without changing explicitly initialized states.

    :return: None.
    """
    problem: DirectAlgebraicProjectionProblem = DirectAlgebraicProjectionProblem()
    initial_values: np.ndarray = np.array([3.0, 0.0], dtype=float)
    differential_values: np.ndarray = np.zeros(0, dtype=float)
    projected_values: np.ndarray
    converged: bool
    residual_inf: float

    projected_values, converged, residual_inf = project_initial_algebraic_state(
        problem=problem,
        initial_values=initial_values,
        differential_values=differential_values,
        tolerance=1.0e-12,
        max_iter=5,
    )

    assert converged
    assert residual_inf <= 1.0e-12
    assert projected_values[0] == 3.0
    assert projected_values[1] == 6.0
