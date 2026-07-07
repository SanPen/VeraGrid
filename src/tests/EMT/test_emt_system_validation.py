# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
Tests for EMT system topology validation in EmtProblemDae.

These tests verify that the validation methods (_validate_emt_models_exist and
_validate_connections) correctly detect topology issues in 5 different scenarios.
"""

import pytest
import os

from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae, EmtTopologyError
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver, PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver_3ph import PowerFlowDriver3Ph
from VeraGridEngine.enumerations import DynamicIntegrationMethod, EmtSolverTypes, ShuntConnectionType, EmtInitializationMethod, EmtLineTypes, ConverterControlType, SolverType
from VeraGridEngine.Templates.Emt.pi_line_emt_template import get_pi_line_emt_template
from VeraGridEngine.Templates.Emt.bergeron_line_emt_template import get_bergeron_line_emt_template
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_shunt_r_emt_template
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template
from VeraGridEngine.Templates.Emt.bus_emt_template import get_bus_emt_template
from VeraGridEngine.Templates.Emt.transformer_emt_template import get_transformer_emt_template
from VeraGridEngine.Templates.Emt.converter_emt_template import get_emt_ideal_converter
from VeraGridEngine.Templates.Emt.dc_load_emt_template import get_dc_load_emt_template
from VeraGridEngine.Templates.templates_common_functions import set_emt_model
import VeraGridEngine.api as gce


def get_default_emt_options() -> EmtOptions:
    """Return default EMT options for testing."""
    return EmtOptions(
        time_step=5e-6,
        simulation_time=0.01,
        tolerance=1e-6,
        solver_type=EmtSolverTypes.Symbolic,
        initialization_method=EmtInitializationMethod.Auto,
        integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
        verbose=0
    )


def run_power_flow(grid: gce.MultiCircuit) -> tuple:
    """Run power flow and return results."""
    pf_options = PowerFlowOptions(
        solver_type=SolverType.NR,
        verbose=False,
        retry_with_other_methods=True,
        max_iter=100,
        tolerance=1e-6,
        control_q=True,
        control_taps_modules=False,
        control_taps_phase=False,
        orthogonalize_controls=False,
    )
    pf_results = gce.power_flow(grid=grid, options=pf_options)

    pf_options_3ph = PowerFlowOptions(
        solver_type=SolverType.NR,
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
    power_flow_3ph = PowerFlowDriver3Ph(grid, pf_options_3ph)
    power_flow_3ph.run()
    pf_res_3ph = power_flow_3ph.results

    return pf_results, pf_res_3ph


# =============================================================================
# TEST 1: scripting_example_thevequiv_piline_Rload_emt
# Positive case - should pass validation without raising EmtTopologyError
# =============================================================================

def test_pi_line_rload_emt_passes_validation():
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    vnom = 10

    bus0 = gce.Bus(name="Bus0", Vnom=vnom, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=vnom)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0 = gce.Line(name="line0", bus_from=bus0, bus_to=bus1, length=10, rate=900.0)

    tower = gce.OverheadLineType(name="Tower", Vnom=vnom)
    wire = gce.Wire(name="Panther 30/7 ACSR", diameter=21.0, diameter_internal=9.0, is_tube=True, r=0.1363, max_current=1)
    tower.add_wire_relationship(wire=wire, xpos=-12.65, ypos=27.5, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0.0, ypos=27.5, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=12.65, ypos=27.5, phase=3)
    tower.compute()
    line0.apply_template(tower, grid.Sbase, grid.fBase)

    v_ph = vnom / (3**0.5)
    R_ph = 100
    P_ph = (v_ph**2) / R_ph
    Q_ph = 0.0
    load = gce.Load(name="load", P=3.0*P_ph, Q=3.0*Q_ph, P1=P_ph, P2=P_ph, P3=P_ph, Q1=Q_ph, Q2=Q_ph, Q3=Q_ph)
    load.conn = ShuntConnectionType.GroundedStar

    gen0 = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50, r1=0.001, x1=1.7)

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template(vf=grid.var_factory).block
    line_mdl = get_pi_line_emt_template(vf = grid.var_factory, phN = False, phA = True, phB = True, phC = True).block
    load_mdl = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True).block


    set_emt_model(device=gen0, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=line0, model=line_mdl, var_factory=grid.var_factory)
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    # Should NOT raise EmtTopologyError - this is a valid topology
    problem = EmtProblemDae(grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3ph=pf_res_3ph)
    assert problem is not None


# =============================================================================
# TEST 2: scripting_example_thevequiv_bergeronline_Rload_emt
# Positive case - should pass validation without raising EmtTopologyError
# =============================================================================

def test_bergeron_line_rload_emt_passes_validation():
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    vnom = 10

    bus0 = gce.Bus(name="Bus0", Vnom=vnom, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=vnom)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0 = gce.Line(name="line0", bus_from=bus0, bus_to=bus1, length=10, rate=900.0)

    tower = gce.OverheadLineType(name="Tower", Vnom=vnom)
    wire = gce.Wire(name="Panther 30/7 ACSR", diameter=21.0, diameter_internal=9.0, is_tube=True, r=0.1363, max_current=1)
    tower.add_wire_relationship(wire=wire, xpos=-12.65, ypos=27.5, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0.0, ypos=27.5, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=12.65, ypos=27.5, phase=3)
    tower.compute()
    line0.apply_template(tower, grid.Sbase, grid.fBase)

    v_ph = vnom / (3**0.5)
    R_ph = 100
    P_ph = (v_ph**2) / R_ph
    Q_ph = 0.0
    load = gce.Load(name="load", P=3.0*P_ph, Q=3.0*Q_ph, P1=P_ph, P2=P_ph, P3=P_ph, Q1=Q_ph, Q2=Q_ph, Q3=Q_ph)
    load.conn = ShuntConnectionType.GroundedStar

    gen0 = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50, r1=0.001, x1=1.7)

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template(vf=grid.var_factory).block
    line_mdl = get_bergeron_line_emt_template(vf=grid.var_factory).block
    load_mdl = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True).block


    set_emt_model(device=gen0, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=line0, model=line_mdl, var_factory=grid.var_factory)
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    # Should NOT raise EmtTopologyError - this is a valid topology
    problem = EmtProblemDae(grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3ph=pf_res_3ph)
    assert problem is not None


# =============================================================================
# TEST 3: scripting_vsc_emt
# Positive case - should pass validation without raising EmtTopologyError
# =============================================================================


def test_vsc_emt_passes_validation():
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)

    bus1_ac = gce.Bus(name="Bus1_AC", Vnom=230.0, is_slack=True)
    bus2_ac = gce.Bus(name="Bus2_AC", Vnom=230.0)
    bus3_dc = gce.Bus(name="Bus3_DC", Vnom=320.0, is_dc=True)
    grid.add_bus(bus1_ac)
    grid.add_bus(bus2_ac)
    grid.add_bus(bus3_dc)

    gen1 = gce.Generator(name="Generator", vset=1.0, Snom=100.0, freq=50.0, r1=0.001, x1=0.4)
    transformer = gce.Transformer2W(name="Transformer", bus_from=bus1_ac, bus_to=bus2_ac, rate=100.0, r=0.01, x=0.1, tap_module=1.0, tap_phase=0.0)

    p_transfer_mw = 30.0
    q_transfer_mvar = 0.0
    vsc = gce.VSC(name="VSC", bus_from=bus3_dc, bus_to=bus2_ac, rate=100.0, control1=ConverterControlType.Qac, control2=ConverterControlType.Vm_dc, control1_val=q_transfer_mvar, control2_val=1.0)

    dc_load = gce.Load(name="DC_Load", P=p_transfer_mw, Q=0.0)

    grid.add_generator(bus1_ac, gen1)
    grid.add_transformer2w(transformer)
    grid.add_vsc(vsc)
    grid.add_load(bus3_dc, dc_load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template(vf=grid.var_factory).block
    trafo_mdl = get_transformer_emt_template(vf=grid.var_factory, name=transformer.name).block
    vsc_mdl = get_emt_ideal_converter(
        vf=grid.var_factory,
        name=vsc.name,
    ).block
    dc_load_mdl = get_dc_load_emt_template(vf=grid.var_factory, name="dc_load_emt").block

    set_emt_model(device=gen1, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=transformer, model=trafo_mdl, var_factory=grid.var_factory)
    set_emt_model(device=vsc, model=vsc_mdl, var_factory=grid.var_factory)
    set_emt_model(device=dc_load, model=dc_load_mdl, var_factory=grid.var_factory)

    # Should NOT raise EmtTopologyError - this is a valid topology
    problem = EmtProblemDae(grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3ph=pf_res_3ph)
    assert problem is not None


# =============================================================================
# TEST 4: scripting_example_validate_connections_phases
# Negative case - should raise EmtTopologyError due to floating phases
# =============================================================================

def test_floating_phases_raises_emt_topology_error():
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    vnom = 10

    bus0 = gce.Bus(name="Bus0", Vnom=vnom, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=vnom)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0 = gce.Line(name="line0", bus_from=bus0, bus_to=bus1, length=10, rate=900.0)

    tower = gce.OverheadLineType(name="Tower", Vnom=vnom)
    wire = gce.Wire(name="Panther 30/7 ACSR", diameter=21.0, diameter_internal=9.0, is_tube=True, r=0.1363, max_current=1)
    tower.add_wire_relationship(wire=wire, xpos=-12.65, ypos=27.5, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0.0, ypos=27.5, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=12.65, ypos=27.5, phase=3)
    tower.compute()
    line0.apply_template(tower, grid.Sbase, grid.fBase)

    v_ph = vnom / (3**0.5)
    R_ph = 100
    P_ph = (v_ph**2) / R_ph
    Q_ph = 0.0
    load = gce.Load(name="load", P=3.0*P_ph, Q=3.0*Q_ph, P1=P_ph, P2=P_ph, P3=P_ph, Q1=Q_ph, Q2=Q_ph, Q3=Q_ph)
    load.conn = ShuntConnectionType.GroundedStar

    gen0 = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50, r1=0.001, x1=1.7)

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template(vf=grid.var_factory).block
    line_mdl = get_pi_line_emt_template(vf = grid.var_factory, phN = False, phA = True, phB = True, phC = True).block
    # Using 1-phase template on 3-phase bus causes floating phases
    load_mdl = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=False, phC=False).block


    set_emt_model(device=gen0, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=line0, model=line_mdl, var_factory=grid.var_factory)
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    # Should raise EmtTopologyError about floating phases
    with pytest.raises(EmtTopologyError, match="Floating bus phases detected"):
        EmtProblemDae(grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3ph=pf_res_3ph)
