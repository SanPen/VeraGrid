from __future__ import annotations

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.Simulations.Rms.rms_driver import RmsSimulationDriver
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import get_complete_generator_template_rms
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_rms_template import get_load_rms_template
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.block_helpers import to_explicit
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.enumerations import RmsInitializationMethod


def _build_complete_generator_grid_without_init_equations() -> gce.MultiCircuit:
    """
    Build the complete-generator pseudo-transient regression grid.

    :return: Grid with RMS models assigned and generator ``init_eqs`` cleared.
    """
    grid: gce.MultiCircuit = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus0: gce.Bus = gce.Bus(name="Bus0", Vnom=90.0, is_slack=True)
    bus1: gce.Bus = gce.Bus(name="Bus1", Vnom=90.0)

    initialize_bus_rms(bus0, vf=grid.var_factory)
    initialize_bus_rms(bus1, vf=grid.var_factory)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line: gce.Line = gce.Line(
        name="Line0-1",
        bus_from=bus0,
        bus_to=bus1,
        r=0.029585798816568046,
        x=0.07100591715976332,
        b=0.03,
        rate=900.0,
    )
    grid.add_line(line)

    load: gce.Load = gce.Load(name="Load1", P=10.0, Q=1.0)
    grid.add_load(bus=bus1, api_obj=load)

    generator: gce.Generator = gce.Generator(
        name="Gen0",
        P=100.0,
        vset=1.0,
        Snom=900.0,
        r1=0.3,
        x1=0.86138701,
        freq=50.0,
    )
    grid.add_generator(bus=bus0, api_obj=generator)

    set_rms_model(
        device=line,
        model=get_line_rms_template(grid.var_factory, name=line.name).block,
        var_factory=grid.var_factory,
    )
    set_rms_model(
        device=load,
        model=get_load_rms_template(grid.var_factory, name=load.name).block,
        var_factory=grid.var_factory,
    )

    generator_model: Block = get_complete_generator_template_rms(grid.var_factory, name=generator.name).block
    generator_model = to_explicit(generator_model, grid.var_factory)
    for block in generator_model.get_all_blocks():
        block.init_eqs = dict()

    set_rms_model(
        device=generator,
        model=generator_model,
        var_factory=grid.var_factory,
    )
    grid.add_rms_events_group(gce.RmsEventsGroup(name="BaseCase"))

    return grid


def test_pseudo_transient_initializes_complete_generator_without_init_equations() -> None:
    """
    Test pseudo-transient initialization on the complete-generator RMS script model.

    The script builds the complete synchronous-generator RMS template and clears
    its ``init_eqs`` before assigning it to the grid, so this test exercises the
    intended pseudo-transient fallback path without relying on symbolic explicit
    initialization equations.

    :return: None.
    """
    grid: gce.MultiCircuit = _build_complete_generator_grid_without_init_equations()
    power_flow_options: gce.PowerFlowOptions = gce.PowerFlowOptions(
        solver_type=gce.SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        tolerance=1.0e-6,
        max_iter=25,
        control_q=False,
        distributed_slack=False,
    )
    power_flow_results = gce.power_flow(grid, options=power_flow_options)

    assert bool(power_flow_results.converged)

    rms_options: gce.RmsOptions = gce.RmsOptions(
        time_step=0.01,
        simulation_time=0.01,
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        initialization_method=RmsInitializationMethod.PseudoTransient,
        max_iter=1000,
        tolerance=1.0e-8,
        verbose=0,
    )
    rms_driver: RmsSimulationDriver = RmsSimulationDriver(
        grid=grid,
        options=rms_options,
        pf_results=power_flow_results,
    )
    rms_driver.run()

    problem: RmsProblemDae | None = rms_driver.problem
    assert problem is not None

    x0: Vec = problem.get_x0()
    assert x0.size == problem.get_all_vars_number()
    assert bool(np.all(np.isfinite(x0)))
    assert bool(np.all(rms_driver.results.converged))
