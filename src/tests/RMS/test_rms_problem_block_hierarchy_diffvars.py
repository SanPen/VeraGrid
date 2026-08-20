from __future__ import annotations

import VeraGridEngine.api as gce

from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms


def _build_minimal_pf_grid_with_generator(generator_block: Block) -> tuple[gce.MultiCircuit, object]:
    grid = gce.MultiCircuit()

    bus1 = Bus(name="Bus1", Vnom=69.0, is_slack=True, Vm0=1.0, Va0=0.0)
    bus2 = Bus(name="Bus2", Vnom=69.0, Vm0=1.0, Va0=0.0)
    grid.add_bus(bus1)
    grid.add_bus(bus2)

    initialize_bus_rms(bus1, vf=grid.var_factory)
    initialize_bus_rms(bus2, vf=grid.var_factory)

    line = Line(name="Line12", bus_from=bus1, bus_to=bus2, r=0.01, x=0.1, b=0.0, rate=100.0)
    line_model = get_line_rms_template(grid.var_factory, name="line_rms_test").block
    grid.var_factory.add_connections([line_model.in_vars[0]], [bus1.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line_model.in_vars[1]], [bus1.rms_model.out_vars[1]])
    grid.var_factory.add_connections([line_model.in_vars[2]], [bus2.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line_model.in_vars[3]], [bus2.rms_model.out_vars[1]])
    line.rms_model = line_model
    grid.add_line(line)

    generator = Generator(name="Gen1", P=0.0, Q=0.0, vset=1.0, Snom=100.0, r1=0.0, x1=0.1, freq=60.0)
    grid.var_factory.add_connections([generator_block.in_vars[0]], [bus1.rms_model.out_vars[0]])
    grid.var_factory.add_connections([generator_block.in_vars[1]], [bus1.rms_model.out_vars[1]])
    generator.rms_model = generator_block
    grid.add_generator(bus=bus1, api_obj=generator)

    pf_options = PowerFlowOptions(
        solver_type=gce.SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=True,
        tolerance=1e-6,
        max_iter=25,
        control_q=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=False,
        orthogonalize_controls=True,
        apply_temperature_correction=False,
        branch_impedance_tolerance_mode=gce.BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=False,
        initialize_angles=False,
        generate_report=False,
    )
    pf_results = gce.power_flow(grid, options=pf_options)
    return grid, pf_results


def _build_problem(generator_block: Block) -> RmsProblemDae:
    grid, pf_results = _build_minimal_pf_grid_with_generator(generator_block)
    rms_options = RmsOptions(simulation_time=0.1, time_step=0.01, verbose=0)
    return RmsProblemDae(grid=grid, options=rms_options, pf_results=pf_results)


def test_nested_child_diff_var_registration() -> None:
    vf = gce.MultiCircuit().var_factory
    vm = vf.add_var("Vm")
    va = vf.add_var("Va")
    p = vf.add_var("P")
    q = vf.add_var("Q")
    x = vf.add_var("x")
    dx = vf.add_diff_var("dx", base_var=x)

    child = Block(
        state_vars=[x],
        diff_vars=[dx],
        state_eqs=[-x],
        algebraic_vars=[p, q],
        algebraic_eqs=[p, q],
        in_vars=[vm, va],
        out_vars=[p, q],
        name="ChildWithDiffVar",
    )
    root = Block(children=[child], in_vars=[vm, va], out_vars=[p, q], name="RootWrapper")

    problem = _build_problem(root)

    assert problem.get_diff_var_number() == 1
    assert problem.get_diff_vars()[0].uid == dx.uid


def test_attaching_only_child_discards_root_only_diff_var_metadata() -> None:
    vf = gce.MultiCircuit().var_factory
    vm = vf.add_var("Vm")
    va = vf.add_var("Va")
    p = vf.add_var("P")
    q = vf.add_var("Q")
    x = vf.add_var("x")
    dx = vf.add_diff_var("dx", base_var=x)

    child = Block(
        state_vars=[x],
        state_eqs=[-x],
        algebraic_vars=[p, q],
        algebraic_eqs=[p, q],
        in_vars=[vm, va],
        out_vars=[p, q],
        name="ChildWithoutDiffVar",
    )
    root = Block(children=[child], diff_vars=[dx], in_vars=[vm, va], out_vars=[p, q], name="RootOnlyDiffVar")

    problem = _build_problem(root.children[0])

    assert problem.get_diff_var_number() == 0


def test_attaching_complete_wrapper_preserves_child_diff_var_registration() -> None:
    vf = gce.MultiCircuit().var_factory
    vm = vf.add_var("Vm")
    va = vf.add_var("Va")
    p = vf.add_var("P")
    q = vf.add_var("Q")
    x = vf.add_var("x")
    dx = vf.add_diff_var("dx", base_var=x)

    child = Block(
        state_vars=[x],
        diff_vars=[dx],
        state_eqs=[-x],
        algebraic_vars=[p, q],
        algebraic_eqs=[p, q],
        in_vars=[vm, va],
        out_vars=[p, q],
        name="ChildDiffVarPreserved",
    )
    root = Block(children=[child], in_vars=[vm, va], out_vars=[p, q], name="RootWrapperPreserved")

    problem = _build_problem(root)

    assert problem.get_diff_var_number() == 1
    assert problem.get_diff_vars()[0].uid == dx.uid
