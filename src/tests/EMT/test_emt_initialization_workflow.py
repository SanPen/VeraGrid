# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, Tuple

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver_3ph import PowerFlowDriver3Ph
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_template
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_shunt_r_emt_template
from VeraGridEngine.Templates.Emt.load_zip_emt_template import get_load_ZIP_emt_template
from VeraGridEngine.Templates.Emt.pi_line_emt_template import get_pi_line_emt_template
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template_with_ref
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicVector
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_emt_model
from VeraGridEngine.enumerations import DynamicIntegrationMethod, EmtSolverTypes, ShuntConnectionType, EmtInitializationMethod, EmtInitializationStatus

from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.initialization_emt import (
    _collect_reduced_initialization_problem,
    run_emt_explicit_initialization,
    run_emt_native_initialization,
)


class GenericEmtProblem(EmtProblemTemplate):
    """
    Minimal EMT problem implementation used by initialization workflow tests.
    """
    __slots__ = []


class SimpleInitializationContext:
    """
    Typed container for the tiny EMT initialization test problems.

    :ivar _x_var: State variable.
    :ivar _y_var: Algebraic variable.
    :ivar _dx_var: Differential variable.
    """
    __slots__ = ["_x_var", "_y_var", "_dx_var"]

    def __init__(self, x_var: Var, y_var: Var, dx_var: Var) -> None:
        """
        Build one simple initialization context.

        :param x_var: State variable.
        :param y_var: Algebraic variable.
        :param dx_var: Differential variable.
        """
        self._x_var: Var = x_var
        self._y_var: Var = y_var
        self._dx_var: Var = dx_var

    def get_x_var(self) -> Var:
        """Return the state variable."""
        return self._x_var

    def get_y_var(self) -> Var:
        """Return the algebraic variable."""
        return self._y_var

    def get_dx_var(self) -> Var:
        """Return the differential variable."""
        return self._dx_var


class TwoBusRealEmtContext:
    """
    Typed container for the real two-bus EMT benchmark case.

    :ivar _grid: Multi-circuit container.
    :ivar _bus0: Slack bus.
    :ivar _bus1: Load bus.
    :ivar _line0: EMT line.
    :ivar _load: EMT load.
    :ivar _gen0: EMT generator.
    :ivar _gen_mdl: Generator EMT block.
    :ivar _line_mdl: Line EMT block.
    :ivar _load_mdl: Load EMT block.
    :ivar _pf_results: Power-flow results object.
    """
    __slots__ = ["_grid", "_bus0", "_bus1", "_line0", "_load", "_gen0", "_gen_mdl", "_line_mdl", "_load_mdl", "_pf_results"]

    def __init__(
            self,
            grid: gce.MultiCircuit,
            bus0: gce.Bus,
            bus1: gce.Bus,
            line0: gce.Line,
            load: gce.Load,
            gen0: gce.Generator,
            gen_mdl: Block,
            line_mdl: Block,
            load_mdl: Block,
            pf_results: object,
    ) -> None:
        """
        Build one real-case context bundle.

        :param grid: Multi-circuit container.
        :param bus0: Slack bus.
        :param bus1: Load bus.
        :param line0: EMT line.
        :param load: EMT load.
        :param gen0: EMT generator.
        :param gen_mdl: Generator EMT block.
        :param line_mdl: Line EMT block.
        :param load_mdl: Load EMT block.
        :param pf_results: Power-flow results object.
        """
        self._grid: gce.MultiCircuit = grid
        self._bus0: gce.Bus = bus0
        self._bus1: gce.Bus = bus1
        self._line0: gce.Line = line0
        self._load: gce.Load = load
        self._gen0: gce.Generator = gen0
        self._gen_mdl: Block = gen_mdl
        self._line_mdl: Block = line_mdl
        self._load_mdl: Block = load_mdl
        self._pf_results: object = pf_results

    def get_grid(self) -> gce.MultiCircuit:
        """Return the grid object."""
        return self._grid

    def get_pf_results(self) -> object:
        """Return the power-flow results object."""
        return self._pf_results


class InitializationBenchmarkRecord:
    """
    Record of initialization benchmark results.

    :ivar _case_name: Name identifier for the test case.
    :ivar _method_name: Name of the initialization method used.
    :ivar _status_name: Final status of the initialization.
    :ivar _residual_inf: Infinity-norm of algebraic residual after initialization.
    :ivar _dx0_inf: Infinity-norm of derivative vector at initialization.
    :ivar _elapsed_s: Wall-clock time elapsed during initialization.
    """
    __slots__ = ["_case_name", "_method_name", "_status_name", "_residual_inf", "_dx0_inf", "_elapsed_s"]

    def __init__(
            self,
            case_name: str,
            method_name: str,
            status_name: str,
            residual_inf: float,
            dx0_inf: float,
            elapsed_s: float,
    ) -> None:
        self._case_name: str = case_name
        self._method_name: str = method_name
        self._status_name: str = status_name
        self._residual_inf: float = float(residual_inf)
        self._dx0_inf: float = float(dx0_inf)
        self._elapsed_s: float = float(elapsed_s)

    def get_case_name(self) -> str:
        """Return the case name."""
        return self._case_name

    def get_method_name(self) -> str:
        """Return the method name."""
        return self._method_name

    def get_status_name(self) -> str:
        """Return the status name."""
        return self._status_name

    def get_residual_inf(self) -> float:
        """Return the residual infinity-norm."""
        return self._residual_inf

    def get_dx0_inf(self) -> float:
        """Return the dx0 infinity-norm."""
        return self._dx0_inf

    def get_elapsed_s(self) -> float:
        """Return the elapsed time in seconds."""
        return self._elapsed_s


def build_single_state_single_algebraic_problem() -> Tuple[GenericEmtProblem, SimpleInitializationContext]:
    """
    Build a tiny EMT problem where explicit initialization resolves the state and
    consistent initialization resolves one algebraic variable.

    The problem consists of:
    - State variable x with differential dx
    - Algebraic variable y linked by equation y = x
    - Algebraic equation y = 2.0
    - Initial condition x = 2.0

    :returns: Tuple of (problem, context) where problem is the EMT problem
              and context contains variable references.
    """
    var_factory: VarFactory = VarFactory()
    x_var: Var = var_factory.add_var("x")
    y_var: Var = var_factory.add_var("y")
    dx_var: Var = var_factory.add_diff_var(name="d_x", base_var=x_var)

    block = Block(
        name="SingleStateSingleAlgebraicInit",
        state_vars=[x_var],
        diff_vars=[dx_var],
        state_eqs=[y_var - x_var],
        algebraic_vars=[y_var],
        algebraic_eqs=[y_var - Const(2.0)],
        init_eqs={x_var: Const(2.0)},
    )
    static_parameter_values_mapping: Dict[Var, Const] = dict()
    problem = GenericEmtProblem(
        sys_block=block,
        glob_time=var_factory.add_var("t_glob_init_0"),
        static_parameter_values_mapping=static_parameter_values_mapping,
    )
    context = SimpleInitializationContext(x_var=x_var, y_var=y_var, dx_var=dx_var)
    return problem, context


def build_unresolved_state_problem() -> Tuple[GenericEmtProblem, SimpleInitializationContext]:
    """
    Build a tiny EMT problem where one state is left unresolved and must be solved
    from the steady-state condition.

    The problem has no explicit initial conditions, requiring the
    initialization algorithm to find a consistent equilibrium.

    :returns: Tuple of (problem, context) where problem is the EMT problem
              and context contains variable references.
    """
    var_factory: VarFactory = VarFactory()
    x_var: Var = var_factory.add_var("x_eq")
    y_var: Var = var_factory.add_var("y_eq")
    dx_var: Var = var_factory.add_diff_var(name="d_x_eq", base_var=x_var)

    block = Block(
        name="UnresolvedStateEquilibriumInit",
        state_vars=[x_var],
        diff_vars=[dx_var],
        state_eqs=[y_var - x_var],
        algebraic_vars=[y_var],
        algebraic_eqs=[y_var - Const(3.0)],
    )
    static_parameter_values_mapping: Dict[Var, Const] = dict()
    problem = GenericEmtProblem(
        sys_block=block,
        glob_time=var_factory.add_var("t_glob_init_1"),
        static_parameter_values_mapping=static_parameter_values_mapping,
    )
    context = SimpleInitializationContext(x_var=x_var, y_var=y_var, dx_var=dx_var)
    return problem, context


def evaluate_algebraic_residual_inf(problem: EmtProblemTemplate) -> float:
    """
    Evaluate the infinity-norm of the algebraic residual at the current stored
    initialization point.

    :param problem: EMT problem to evaluate.
    :returns: Maximum absolute residual value, or 0.0 if no algebraic equations.
    """
    algebraic_eqs: list[Expr] = problem.get_algebraic_eqs()
    if len(algebraic_eqs) == 0:
        return 0.0
    else:
        residual_fn = SymbolicVector(
            eqs=algebraic_eqs,
            compiler_names_dict=problem._compiler_names_dict,
            alias_names_dict=problem._alias_names_dict,
            VARS_NAME=problem.VARS_NAME,
            DIFF_NAME=problem.DIFF_NAME,
            EVENT_PARAMS_NAME=problem.VARIABLE_PARAMS_NAME,
            PARAMS_NAME=problem.CONSTANT_PARAMS_NAME,
        )
        x0: np.ndarray = problem.get_x0()
        dx0: np.ndarray = problem.get_dx0()
        runtime_params: np.ndarray = problem.event_params_values.copy()
        runtime_params = problem.def_event_params_fn(runtime_params, 0.0)
        constant_params: np.ndarray = np.asarray([float(item.value) for item in problem.get_parameters_values()], dtype=np.float64)
        residual: np.ndarray = residual_fn(x0, dx0, runtime_params, constant_params)
        return float(np.max(np.abs(residual)))


def build_two_bus_real_emt_case(
        zip_load: bool = True,
        initialization_method: EmtInitializationMethod = EmtInitializationMethod.Auto,
) -> Tuple[EmtProblemDae, TwoBusRealEmtContext]:
    """
    Build the standard real EMT two-bus benchmark case used by snapshot and
    initialization tests.

    Creates a grid with a slack generator at bus0 and a load at bus1,
    connected by a transmission line. Power flow is run to obtain
    initial operating point.

    :param zip_load: If True, use ZIP load model; otherwise use RLC shunt.
    :param initialization_method: EMT initialization method to use.
    :returns: Tuple of (problem, context) with EMT problem and grid context.
    """
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)

    vnom: float = 10.0
    bus0 = gce.Bus(name="Bus0", Vnom=vnom, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=vnom)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0 = gce.Line(name="line0", bus_from=bus0, bus_to=bus1, length=10, rate=900.0)

    tower = gce.OverheadLineType(name="Tower", Vnom=vnom)
    wire = gce.Wire(
        name="Panther 30/7 ACSR",
        diameter=21.0,
        diameter_internal=9.0,
        is_tube=True,
        r=0.1363,
        max_current=1,
    )
    tower.add_wire_relationship(wire=wire, xpos=-12.65, ypos=27.5, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0.0, ypos=27.5, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=12.65, ypos=27.5, phase=3)
    tower.compute()
    line0.apply_template(tower, grid.Sbase, grid.fBase)

    r_ph: float = 100.0
    v_ph: float = vnom / (3.0 ** 0.5)
    p_ph: float = (v_ph ** 2) / r_ph
    load = gce.Load(name="load", P1=p_ph, P2=p_ph, P3=p_ph, Q1=0.0, Q2=0.0, Q3=0.0)
    load.conn = ShuntConnectionType.GroundedStar

    gen0 = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50, r1=0.001, x1=1.7)

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    gen_mdl = get_generator_thevenin_rl_emt_template_with_ref(vf = grid.var_factory).block
    line_mdl = get_pi_line_emt_template(vf = grid.var_factory, phN = False, phA = True, phB = True, phC = True).block
    if zip_load:
        load_mdl = get_load_ZIP_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True).block
    else:
        load_mdl = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True).block

    set_emt_model(device=gen0, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=line0, model=line_mdl, var_factory=grid.var_factory)
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    pf_options = PowerFlowOptions(
        solver_type=gce.SolverType.NR,
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
        generate_report=False,
    )
    power_flow = PowerFlowDriver3Ph(grid, pf_options)
    power_flow.run()
    pf_results = power_flow.results

    options = EmtOptions(
        time_step=5e-6,
        simulation_time=2e-4,
        tolerance=1e-6,
        solver_type=EmtSolverTypes.StructuralCompiled,
        integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
        initialization_method=initialization_method,
        verbose=0,
    )
    problem = EmtProblemDae(grid=grid, options=options, pf_results_3ph=pf_results, pf_results=None)

    context = TwoBusRealEmtContext(
        grid=grid,
        bus0=bus0,
        bus1=bus1,
        line0=line0,
        load=load,
        gen0=gen0,
        gen_mdl=gen_mdl,
        line_mdl=line_mdl,
        load_mdl=load_mdl,
        pf_results=pf_results,
    )
    return problem, context


def test_consistent_newton_initializes_missing_algebraic_and_dx0() -> None:
    """
    Test that Consistent Newton initializes missing algebraic variable and dx0.

    Verifies that the Consistent Newton method correctly resolves
    a simple problem with one state and one algebraic variable,
    producing x = 2.0, y = 2.0, and dx = 0.0.
    """
    problem, context = build_single_state_single_algebraic_problem()
    options = EmtOptions(initialization_method=EmtInitializationMethod.ConsistentNewton)

    run_emt_explicit_initialization(problem)
    report = run_emt_native_initialization(problem, options)

    idx_x = problem.get_var_idx(context.get_x_var())
    idx_y = problem.get_var_idx(context.get_y_var())
    idx_dx = problem.get_diff_var_idx(context.get_dx_var())

    x0 = problem.get_x0()
    dx0 = problem.get_dx0()

    assert report.status == EmtInitializationStatus.RESOLVED
    assert abs(x0[idx_x] - 2.0) < 1e-9
    assert abs(x0[idx_y] - 2.0) < 1e-9
    assert abs(dx0[idx_dx] - 0.0) < 1e-9


def test_reduced_initialization_problem_keeps_seeded_algebraic_equations() -> None:
    """
    The reduced EMT initialization system must always include algebraic equations.

    Seeded PF guesses are only starting points; they must not suppress the
    algebraic correction stage when consistency equations are still present.
    """

    class _ProblemStub:
        __slots__ = ("init_guess", "sys_block", "_state_vars", "_state_eqs", "_algebraic_vars", "_algebraic_eqs")

        def __init__(self) -> None:
            state_var = Var("state_seeded")
            algebraic_var = Var("alg_seeded")
            self.init_guess = dict({state_var.uid: 3.0, algebraic_var.uid: 2.0})
            self.sys_block = Block()
            self.sys_block.init_eqs = dict()
            self._state_vars = list([state_var])
            self._state_eqs = list([Const(0.0)])
            self._algebraic_vars = list([algebraic_var])
            self._algebraic_eqs = list([algebraic_var - Const(1.0)])

        def get_state_vars(self) -> list[Var]:
            return self._state_vars

        def get_state_eqs(self) -> list[Const]:
            return self._state_eqs

        def get_algebraic_vars(self) -> list[Var]:
            return self._algebraic_vars

        def get_algebraic_eqs(self) -> list[Expr]:
            return self._algebraic_eqs

    payload = _collect_reduced_initialization_problem(_ProblemStub(), allow_state_equilibrium=True)

    assert payload is not None
    unknown_vars, residual_eqs, state_unknown_mask = payload
    assert [var.name for var in unknown_vars] == ["alg_seeded"]
    assert len(residual_eqs) == 1
    assert state_unknown_mask.tolist() == [0.0]


def test_consistent_newton_uses_state_equilibrium_for_unresolved_states() -> None:
    """
    Test that Consistent Newton uses state equilibrium for unresolved states.

    Verifies that when no explicit initial conditions are provided,
    the method finds the steady-state equilibrium with x = 3.0, y = 3.0.
    """
    problem, context = build_unresolved_state_problem()
    options = EmtOptions(initialization_method=EmtInitializationMethod.ConsistentNewton)

    report = run_emt_native_initialization(problem, options)

    idx_x = problem.get_var_idx(context.get_x_var())
    idx_y = problem.get_var_idx(context.get_y_var())
    idx_dx = problem.get_diff_var_idx(context.get_dx_var())

    x0 = problem.get_x0()
    dx0 = problem.get_dx0()

    assert report.status == EmtInitializationStatus.RESOLVED
    assert abs(x0[idx_x] - 3.0) < 1e-9
    assert abs(x0[idx_y] - 3.0) < 1e-9
    assert abs(dx0[idx_dx] - 0.0) < 1e-9


def test_pseudo_transient_method_converges_on_simple_problem() -> None:
    """
    Test that Pseudo Transient method converges on simple problem.

    Verifies that the Pseudo Transient initialization method
    successfully resolves the same problem with residual below tolerance.
    """
    problem, _ = build_unresolved_state_problem()
    options = EmtOptions(
        initialization_method=EmtInitializationMethod.PseudoTransient,
        init_newton_tol=1e-8,
        init_ptc_max_iter=80,
    )

    report = run_emt_native_initialization(problem, options)

    assert report.status == EmtInitializationStatus.RESOLVED
    assert report.method_used == EmtInitializationMethod.PseudoTransient
    assert report.final_residual_inf <= options.init_newton_tol


def test_auto_initialization_is_not_worse_than_explicit_on_real_case() -> None:
    """
    Test that Auto initialization is comparable to Explicit on real case.

    Verifies that the Auto initialization method produces results
    comparable to Explicit initialization on a realistic two-bus grid.
    """
    explicit_problem, _ = build_two_bus_real_emt_case(
        zip_load=True,
        initialization_method=EmtInitializationMethod.Explicit,
    )
    auto_problem, _ = build_two_bus_real_emt_case(
        zip_load=True,
        initialization_method=EmtInitializationMethod.Auto,
    )

    explicit_res = evaluate_algebraic_residual_inf(explicit_problem)
    auto_res = evaluate_algebraic_residual_inf(auto_problem)

    assert np.isfinite(explicit_res)
    assert np.isfinite(auto_res)
    assert auto_res <= explicit_res + 1.0e-8
    assert auto_problem.initialization_report is not None
    assert auto_problem.initialization_report.status in {EmtInitializationStatus.RESOLVED, EmtInitializationStatus.FAILED}


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
