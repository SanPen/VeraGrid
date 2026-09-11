# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Focused regression for model-owned Thevenin EMT initialization."""

from __future__ import annotations

from typing import Any, cast

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.enumerations import (
    DynamicIntegrationMethod,
    EmtInitializationMethod,
    EmtInitializationStatus,
    EmtSolverTypes,
    ShuntConnectionType,
)
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_shunt_r_emt_template
from VeraGridEngine.Templates.Emt.pi_line_emt_template import get_pi_line_emt_template
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import (
    get_generator_thevenin_rl_emt_template_with_ref,
)
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_template
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_emt_model


def _find_var(device: Any, name: str) -> Any:
    matches = [
        var
        for block in device.emt_model.get_all_blocks()
        for var in block.state_vars + block.algebraic_vars + list(block.event_dict) + block.diff_vars
        if var.name == name
    ]
    assert len(matches) == 1
    return matches[0]


def _build_thevenin_case() -> tuple[EmtProblemDae, gce.Generator]:
    grid = gce.MultiCircuit(name="Thevenin EMT initialization", Sbase=100.0, fbase=50.0)
    source = gce.Bus(name="Source", Vnom=230.0, is_slack=True)
    demand = gce.Bus(name="Demand", Vnom=230.0)
    grid.add_bus(source)
    grid.add_bus(demand)

    line = gce.Line(name="Line", bus_from=source, bus_to=demand, r=0.015, x=0.12, b=0.02, rate=200.0)
    tower = gce.OverheadLineType(name="Tower", Vnom=230.0)
    wire = gce.Wire(name="Conductor", diameter=30.0, r=0.08, max_current=2.0)
    tower.add_wire_relationship(wire, xpos=-8.0, ypos=25.0, phase=1)
    tower.add_wire_relationship(wire, xpos=0.0, ypos=32.0, phase=2)
    tower.add_wire_relationship(wire, xpos=8.0, ypos=25.0, phase=3)
    tower.compute()
    line.apply_template(tower, grid.Sbase, grid.fBase)

    generator = gce.Generator(name="Thevenin source", vset=1.02, Snom=200.0, r1=0.01, x1=0.25, freq=50.0)
    load = gce.Load(name="Load", P=60.0, Q=25.0, P1=20.0, P2=20.0, P3=20.0,
                    Q1=25.0 / 3.0, Q2=25.0 / 3.0, Q3=25.0 / 3.0)
    load.conn = ShuntConnectionType.GroundedStar
    grid.add_line(line)
    grid.add_generator(source, generator)
    grid.add_load(demand, load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)
    set_emt_model(generator, get_generator_thevenin_rl_emt_template_with_ref(grid.var_factory).block, grid.var_factory)
    set_emt_model(
        line,
        get_pi_line_emt_template(grid.var_factory, phN=False, phA=True, phB=True, phC=True).block,
        grid.var_factory,
    )
    set_emt_model(
        load,
        get_shunt_r_emt_template(grid.var_factory, phA=True, phB=True, phC=True).block,
        grid.var_factory,
    )

    power_flow = PowerFlowDriver(grid, gce.PowerFlowOptions(
        solver_type=gce.SolverType.NR, retry_with_other_methods=False,
        tolerance=1e-10, max_iter=50, control_q=False,
    ))
    power_flow.run()
    assert bool(power_flow.results.converged)

    problem = EmtProblemDae(
        grid=grid,
        options=EmtOptions(
            time_step=5e-6, simulation_time=2e-5, tolerance=1e-7,
            solver_type=EmtSolverTypes.Symbolic,
            integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
            initialization_method=EmtInitializationMethod.Explicit,
            verbose=0,
        ),
        pf_results=power_flow.results,
    )
    return problem, generator


def test_thevenin_model_initializes_internal_emf_without_problem_specific_seeding() -> None:
    problem, generator = _build_thevenin_case()
    assert problem.initialization_report is not None
    assert problem.initialization_report.status == EmtInitializationStatus.RESOLVED

    voltage = complex(problem.power_flow_results.voltage[0])
    power = complex(problem.power_flow_results.Sbus[0]) / problem.grid.Sbase
    current = np.conj(power / voltage)
    voltage_peak = np.sqrt(2.0) * abs(voltage)
    current_peak = np.sqrt(2.0) * abs(current)
    phi_v = np.angle(voltage)
    phi = np.angle(current) - phi_v
    e_relative = voltage_peak + complex(generator.R1, generator.X1) * current_peak * np.exp(1j * phi)
    theta_expected = phi_v + np.angle(e_relative)
    emf_peak = abs(e_relative)
    alpha = np.exp(2j * np.pi / 3.0)
    phase_currents = (current, current / alpha, current * alpha)

    expected_values = {
        "i_A": np.sqrt(2.0) * np.imag(phase_currents[0]),
        "i_B": np.sqrt(2.0) * np.imag(phase_currents[1]),
        "i_C": np.sqrt(2.0) * np.imag(phase_currents[2]),
        "theta": theta_expected,
        "e_A": emf_peak * np.sin(theta_expected),
        "e_B": emf_peak * np.sin(theta_expected - 2.0 * np.pi / 3.0),
        "e_C": emf_peak * np.sin(theta_expected + 2.0 * np.pi / 3.0),
    }
    for name, expected in expected_values.items():
        var = _find_var(generator, name)
        actual = problem.get_x0()[problem.get_var_idx(var)]
        np.testing.assert_allclose(actual, expected, rtol=1e-7, atol=1e-9)

    omega_base = 2.0 * np.pi * problem.grid.fBase
    for name, phase_current in zip(("d_i_A", "d_i_B", "d_i_C"), phase_currents):
        var = _find_var(generator, name)
        actual = problem.get_dx0()[problem.get_diff_var_idx(var)]
        expected = omega_base * np.sqrt(2.0) * np.real(phase_current)
        np.testing.assert_allclose(actual, expected, rtol=1e-7, atol=1e-7)

    solver = JitSymbolicSolver(
        problem=problem, t0=0.0, t_end=problem.options.simulation_time,
        h=problem.options.time_step, method=problem.options.integration_method,
        pred_method=DynamicIntegrationMethod.OdeEuler, dense_threshold=0, verbose=False,
    )
    _, values, derivatives, well_initialized, converged = solver.simulate(
        boundary_updater=cast(Any, problem)
    )
    assert well_initialized
    assert converged
    assert np.all(np.isfinite(values))
    assert np.all(np.isfinite(derivatives))
