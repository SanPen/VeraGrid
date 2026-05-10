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
import numpy as np
import warnings

from scipy.sparse.linalg import MatrixRankWarning

from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtInterfaceValidationError, EmtProblemDae, EmtTopologyError
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver_3ph import PowerFlowDriver3Ph
from VeraGridEngine.enumerations import DynamicIntegrationMethod, EmtSolverTypes, ShuntConnectionType, EmtInitializationMethod, \
    ConverterControlType, SolverType, VarPowerFlowRefferenceType
from VeraGridEngine.Templates.Emt.pi_line_emt_template import get_pi_line_emt_template
from VeraGridEngine.Templates.Emt.bergeron_line_emt_template import get_bergeron_line_emt_template
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_shunt_r_emt_template
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_template
from VeraGridEngine.Templates.Emt.transformer_emt_template import get_transformer_emt_template
from VeraGridEngine.Templates.Emt.converter_emt_template import get_emt_ideal_converter
from VeraGridEngine.Templates.Emt.converter_switched_emt_template import get_switched_emt_converter
from VeraGridEngine.Templates.Emt.dc_load_emt_template import get_dc_load_emt_template
from VeraGridEngine.Templates.Emt.dc_line_emt_template import get_dc_line_emt_template
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_emt_model
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.basic_structures import Logger
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


def get_switched_converter_emt_options() -> EmtOptions:
    """Return lightweight EMT options for the switched-converter validation test."""
    return EmtOptions(
        time_step=1e-5,
        simulation_time=1.2e-3,
        tolerance=1e-6,
        solver_type=EmtSolverTypes.Symbolic,
        initialization_method=EmtInitializationMethod.Explicit,
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        verbose=0,
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
    with warnings.catch_warnings():
        # The retry battery intentionally explores several numerical methods.
        # Some rejected candidates emit transient numeric warnings before the
        # driver falls back to a converged solution, which is the behavior this
        # validation helper cares about.
        warnings.filterwarnings(
            "ignore",
            message="overflow encountered in scalar multiply",
            category=RuntimeWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in multiply",
            category=RuntimeWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in scalar divide",
            category=RuntimeWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="Matrix is exactly singular",
            category=MatrixRankWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="Unable to factorize HELM coefficients matrix :/",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in divide",
            category=RuntimeWarning,
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


def _build_interface_validation_problem(grid: gce.MultiCircuit) -> EmtProblemDae:
    """Build one minimal problem instance used only for EMT interface validation."""
    problem: EmtProblemDae = EmtProblemDae.__new__(EmtProblemDae)
    problem.grid = grid
    problem.logger = Logger()
    return problem


def _make_ref_var(reference: VarPowerFlowRefferenceType, name_suffix: str) -> Var:
    """Create one symbolic variable for a test EMT external reference."""
    return Var(name=f"{reference.value}_{name_suffix}", reference=reference)


def _make_external_mapping_block(refs: list[VarPowerFlowRefferenceType], name_suffix: str) -> Block:
    """Create one minimal EMT block exposing the requested external references."""
    external_mapping: dict[VarPowerFlowRefferenceType, Var] = dict()
    out_vars: list[Var] = list()
    reference: VarPowerFlowRefferenceType

    for reference in refs:
        var = _make_ref_var(reference, name_suffix)
        external_mapping[reference] = var
        out_vars.append(var)

    return Block(external_mapping=external_mapping, out_vars=out_vars)


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


def _find_name_in_block(name: str, block: Block) -> Var | None:
    """
    Return one symbolic variable from a block hierarchy by name.

    :param name: Requested symbolic-variable name.
    :param block: Root symbolic block.
    :return: Matching variable or ``None``.
    """
    variable: Var
    child_block: Block
    nested_result: Var | None

    for variable_list in [block.in_vars, block.out_vars, block.algebraic_vars, block.state_vars, block.diff_vars]:
        for variable in variable_list:
            if variable.name == name:
                return variable
            else:
                pass

    for variable in list(block.event_dict.keys()):
        if variable.name == name:
            return variable
        else:
            pass

    for child_block in block.children:
        nested_result = _find_name_in_block(name, child_block)
        if nested_result is not None:
            return nested_result
        else:
            pass

    return None


def test_switched_vsc_emt_passes_validation_and_switches_gates() -> None:
    """
    Verify that the switched EMT converter integrates in a normal VSC case and produces gate commutations.

    :return: None.
    """
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)

    bus1_ac = gce.Bus(name="Bus1_AC", Vnom=230.0, is_slack=True)
    bus2_ac = gce.Bus(name="Bus2_AC", Vnom=230.0)
    bus3_dc = gce.Bus(name="Bus3_DC", Vnom=320.0, is_dc=True)
    grid.add_bus(bus1_ac)
    grid.add_bus(bus2_ac)
    grid.add_bus(bus3_dc)

    gen1 = gce.Generator(name="Generator", vset=1.0, Snom=100.0, freq=50.0, r1=0.001, x1=0.4)
    transformer = gce.Transformer2W(name="Transformer", bus_from=bus1_ac, bus_to=bus2_ac, rate=100.0, r=0.01, x=0.1, tap_module=1.0, tap_phase=0.0)
    vsc = gce.VSC(name="VSC", bus_from=bus3_dc, bus_to=bus2_ac, rate=100.0, control1=ConverterControlType.Qac, control2=ConverterControlType.Vm_dc, control1_val=0.0, control2_val=1.0)
    dc_load = gce.Load(name="DC_Load", P=30.0, Q=0.0)

    grid.add_generator(bus1_ac, gen1)
    grid.add_transformer2w(transformer)
    grid.add_vsc(vsc)
    grid.add_load(bus3_dc, dc_load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_options = PowerFlowOptions(
        solver_type=SolverType.NR,
        verbose=False,
        retry_with_other_methods=False,
        max_iter=25,
        tolerance=1e-5,
        control_q=False,
        control_taps_modules=False,
        control_taps_phase=False,
        orthogonalize_controls=False,
    )
    pf_results = gce.power_flow(grid=grid, options=pf_options)
    pf_res_3ph = None

    gen_mdl = get_generator_thevenin_rl_emt_template(vf=grid.var_factory).block
    trafo_mdl = get_transformer_emt_template(vf=grid.var_factory, name=transformer.name).block
    vsc_mdl = get_switched_emt_converter(vf=grid.var_factory, name=vsc.name).block
    dc_load_mdl = get_dc_load_emt_template(vf=grid.var_factory, name="dc_load_emt_switched").block

    set_emt_model(device=gen1, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=transformer, model=trafo_mdl, var_factory=grid.var_factory)
    set_emt_model(device=vsc, model=vsc_mdl, var_factory=grid.var_factory)
    set_emt_model(device=dc_load, model=dc_load_mdl, var_factory=grid.var_factory)

    switched_options = get_switched_converter_emt_options()
    problem = EmtProblemDae(grid=grid, options=switched_options, pf_results=pf_results, pf_results_3Ph=pf_res_3ph)
    assert problem is not None

    gate_a_var = _find_name_in_block("gate_a_VSC", vsc.emt_model)
    gate_b_var = _find_name_in_block("gate_b_VSC", vsc.emt_model)
    gate_c_var = _find_name_in_block("gate_c_VSC", vsc.emt_model)
    i_A_var = _find_name_in_block("i_A_VSC", vsc.emt_model)
    i_B_var = _find_name_in_block("i_B_VSC", vsc.emt_model)
    i_C_var = _find_name_in_block("i_C_VSC", vsc.emt_model)
    v_dc_var = _find_name_in_block("v_dc_VSC", vsc.emt_model)

    assert gate_a_var is not None
    assert gate_b_var is not None
    assert gate_c_var is not None
    assert i_A_var is not None
    assert i_B_var is not None
    assert i_C_var is not None
    assert v_dc_var is not None
    assert problem.initialization_report is not None
    assert float(problem.initialization_report.initial_residual_inf) <= 1.0e-8
    assert float(problem.initialization_report.final_residual_inf) <= 1.0e-8

    problem.reset_boundary_update_state(0.0)
    x0 = problem.get_x0()
    runtime_values = problem.event_params_values.copy()
    constant_values = np.asarray([const.value for const in problem.get_parameters_values()], dtype=float)
    full_params = np.concatenate((runtime_values, constant_values))
    runtime_mode_map = {var.name: var for var in problem.get_runtime_mode_parameters()}
    gate_a_mode_idx = problem.uid2idx_event_params[runtime_mode_map["gate_a_mode_VSC_plant_bridge"].uid]
    gate_b_mode_idx = problem.uid2idx_event_params[runtime_mode_map["gate_b_mode_VSC_plant_bridge"].uid]
    gate_c_mode_idx = problem.uid2idx_event_params[runtime_mode_map["gate_c_mode_VSC_plant_bridge"].uid]
    switching_enabled_idx = problem.uid2idx_event_params[runtime_mode_map["switching_enabled_mode_VSC"].uid]
    gate_a_trace = list()
    gate_b_trace = list()
    gate_c_trace = list()

    for time_s in np.linspace(0.0, switched_options.simulation_time, 121):
        problem.update(float(time_s), x0.copy(), full_params)
        gate_a_trace.append(float(full_params[gate_a_mode_idx]))
        gate_b_trace.append(float(full_params[gate_b_mode_idx]))
        gate_c_trace.append(float(full_params[gate_c_mode_idx]))

    assert float(full_params[switching_enabled_idx]) > 0.5
    assert float(np.max(np.asarray(gate_a_trace)) - np.min(np.asarray(gate_a_trace))) > 0.5
    assert float(np.max(np.asarray(gate_b_trace)) - np.min(np.asarray(gate_b_trace))) > 0.5
    assert float(np.max(np.asarray(gate_c_trace)) - np.min(np.asarray(gate_c_trace))) > 0.5
    assert np.isfinite(float(x0[problem.get_var_idx(v_dc_var)]))
    assert np.isfinite(float(x0[problem.get_var_idx(i_A_var)]))
    assert np.isfinite(float(x0[problem.get_var_idx(i_B_var)]))
    assert np.isfinite(float(x0[problem.get_var_idx(i_C_var)]))


def test_set_emt_model_connects_dc_line_terminal_voltages():
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)

    bus_from_dc = gce.Bus(name="BusFromDC", Vnom=320.0, is_dc=True)
    bus_to_dc = gce.Bus(name="BusToDC", Vnom=320.0, is_dc=True)
    grid.add_bus(bus_from_dc)
    grid.add_bus(bus_to_dc)

    get_bus_emt_template(grid, bus_from_dc)
    get_bus_emt_template(grid, bus_to_dc)

    dc_line = gce.DcLine(name="DC_Line", bus_from=bus_from_dc, bus_to=bus_to_dc, r=0.02, rate=100.0)
    line_mdl = get_dc_line_emt_template(vf=grid.var_factory, name=dc_line.name).block

    set_emt_model(device=dc_line, model=line_mdl, var_factory=grid.var_factory)

    assert dc_line.emt_model.E(VarPowerFlowRefferenceType.Vf_dc).uid == bus_from_dc.emt_model.E(VarPowerFlowRefferenceType.Vdc).uid
    assert dc_line.emt_model.E(VarPowerFlowRefferenceType.Vt_dc).uid == bus_to_dc.emt_model.E(VarPowerFlowRefferenceType.Vdc).uid


def test_dc_line_emt_passes_validation_and_initializes_branch_currents():
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)

    bus_ac = gce.Bus(name="Bus_AC", Vnom=230.0, is_slack=True)
    bus_dc_from = gce.Bus(name="Bus_DC_From", Vnom=320.0, is_dc=True)
    bus_dc_to = gce.Bus(name="Bus_DC_To", Vnom=320.0, is_dc=True)
    grid.add_bus(bus_ac)
    grid.add_bus(bus_dc_from)
    grid.add_bus(bus_dc_to)

    gen = gce.Generator(name="Generator", vset=1.0, Snom=100.0, freq=50.0, r1=0.001, x1=0.4)
    vsc = gce.VSC(
        name="VSC",
        bus_from=bus_dc_from,
        bus_to=bus_ac,
        rate=100.0,
        control1=ConverterControlType.Qac,
        control2=ConverterControlType.Vm_dc,
        control1_val=0.0,
        control2_val=1.0,
    )
    dc_line = gce.DcLine(name="DC_Line", bus_from=bus_dc_from, bus_to=bus_dc_to, r=0.02, rate=100.0)
    dc_load = gce.Load(name="DC_Load", P=30.0, Q=0.0)

    grid.add_generator(bus_ac, gen)
    grid.add_vsc(vsc)
    grid.add_dc_line(dc_line)
    grid.add_load(bus_dc_to, dc_load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template(vf=grid.var_factory).block
    vsc_mdl = get_emt_ideal_converter(vf=grid.var_factory, name=vsc.name).block
    dc_line_mdl = get_dc_line_emt_template(vf=grid.var_factory, name=dc_line.name).block
    dc_load_mdl = get_dc_load_emt_template(vf=grid.var_factory, name="dc_load_emt").block

    set_emt_model(device=gen, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=vsc, model=vsc_mdl, var_factory=grid.var_factory)
    set_emt_model(device=dc_line, model=dc_line_mdl, var_factory=grid.var_factory)
    set_emt_model(device=dc_load, model=dc_load_mdl, var_factory=grid.var_factory)

    problem = EmtProblemDae(grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3Ph=pf_res_3ph)
    assert problem is not None

    if_dc_var = dc_line.emt_model.E(VarPowerFlowRefferenceType.If_dc)
    it_dc_var = dc_line.emt_model.E(VarPowerFlowRefferenceType.It_dc)

    assert if_dc_var is not None
    assert it_dc_var is not None
    assert if_dc_var.uid in problem.init_guess
    assert it_dc_var.uid in problem.init_guess
    assert abs(problem.init_guess[if_dc_var.uid] + problem.init_guess[it_dc_var.uid]) < 1e-9


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


def test_interface_validation_accepts_compatible_ac_abc_injection() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusABC", Vnom=20.0)
    load = gce.Load(name="LoadABC", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.v_B,
        VarPowerFlowRefferenceType.v_C,
    ], "bus_abc")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.v_B,
        VarPowerFlowRefferenceType.v_C,
        VarPowerFlowRefferenceType.i_A,
        VarPowerFlowRefferenceType.i_B,
        VarPowerFlowRefferenceType.i_C,
    ], "load_abc")

    problem = _build_interface_validation_problem(grid)
    problem._validate_dynamic_emt_interfaces()


def test_interface_validation_accepts_compatible_ac_abcn_injection() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusABCN", Vnom=20.0)
    load = gce.Load(name="LoadABCN", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.v_N,
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.v_B,
        VarPowerFlowRefferenceType.v_C,
    ], "bus_abcn")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.v_N,
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.v_B,
        VarPowerFlowRefferenceType.v_C,
        VarPowerFlowRefferenceType.i_N,
        VarPowerFlowRefferenceType.i_A,
        VarPowerFlowRefferenceType.i_B,
        VarPowerFlowRefferenceType.i_C,
    ], "load_abcn")

    problem = _build_interface_validation_problem(grid)
    problem._validate_dynamic_emt_interfaces()


def test_interface_validation_rejects_neutral_without_bus_support() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusNoNeutral", Vnom=20.0)
    load = gce.Load(name="LoadNeutral", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.v_B,
        VarPowerFlowRefferenceType.v_C,
    ], "bus_noneutral")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.v_N,
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.v_B,
        VarPowerFlowRefferenceType.v_C,
        VarPowerFlowRefferenceType.i_N,
        VarPowerFlowRefferenceType.i_A,
        VarPowerFlowRefferenceType.i_B,
        VarPowerFlowRefferenceType.i_C,
    ], "load_noneutral")

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="BusNoNeutral"):
        problem._validate_dynamic_emt_interfaces()


def test_interface_validation_rejects_dc_refs_on_ac_bus() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="AcBus", Vnom=20.0)
    load = gce.Load(name="DcStyledLoad", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.v_B,
        VarPowerFlowRefferenceType.v_C,
    ], "ac_bus")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.Vdc,
        VarPowerFlowRefferenceType.Idc,
    ], "dc_load_on_ac")

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="DC"):
        problem._validate_dynamic_emt_interfaces()


def test_interface_validation_rejects_ac_refs_on_dc_bus() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="DcBus", Vnom=320.0, is_dc=True)
    load = gce.Load(name="AcStyledLoad", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.Vdc,
    ], "dc_bus")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.i_A,
    ], "ac_load_on_dc")

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="AC phase"):
        problem._validate_dynamic_emt_interfaces()


def test_interface_validation_rejects_shared_dc_branch_collision() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus_from = gce.Bus(name="DcFrom", Vnom=320.0, is_dc=True)
    bus_to = gce.Bus(name="DcTo", Vnom=320.0, is_dc=True)
    dc_line = gce.DcLine(name="SharedDcBranch", bus_from=bus_from, bus_to=bus_to, r=0.01, rate=100.0)
    grid.add_bus(bus_from)
    grid.add_bus(bus_to)
    grid.add_dc_line(dc_line)

    bus_from.emt_model = _make_external_mapping_block([VarPowerFlowRefferenceType.Vdc], "dc_from")
    bus_to.emt_model = _make_external_mapping_block([VarPowerFlowRefferenceType.Vdc], "dc_to")
    dc_line.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.Vdc,
        VarPowerFlowRefferenceType.Idc,
    ], "shared_dc_branch")

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="Use If_dc and It_dc instead"):
        problem._validate_dynamic_emt_interfaces()


def test_set_emt_model_connects_single_bus_ac_injection_refs() -> None:
    """Single-bus AC EMT injections must bind their voltage inputs to the bus shell."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusABC", Vnom=20.0)
    load = gce.Load(name="LoadABC", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.v_B,
        VarPowerFlowRefferenceType.v_C,
    ], "bus_connect_abc")

    load_mdl = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True).block
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    assert load.emt_model.external_mapping[VarPowerFlowRefferenceType.v_A].uid == bus.emt_model.external_mapping[VarPowerFlowRefferenceType.v_A].uid
    assert load.emt_model.external_mapping[VarPowerFlowRefferenceType.v_B].uid == bus.emt_model.external_mapping[VarPowerFlowRefferenceType.v_B].uid
    assert load.emt_model.external_mapping[VarPowerFlowRefferenceType.v_C].uid == bus.emt_model.external_mapping[VarPowerFlowRefferenceType.v_C].uid


def test_set_emt_model_connects_single_bus_dc_injection_refs() -> None:
    """Single-bus DC EMT injections must bind their DC input to the bus shell."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusDC", Vnom=320.0, is_dc=True)
    load = gce.Load(name="LoadDC", P=10.0, Q=0.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowRefferenceType.Vdc,
    ], "bus_connect_dc")

    load_mdl = get_dc_load_emt_template(vf=grid.var_factory).block
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    assert load.emt_model.external_mapping[VarPowerFlowRefferenceType.Vdc].uid == bus.emt_model.external_mapping[VarPowerFlowRefferenceType.Vdc].uid


def test_emt_template_setter_allows_gui_order_injection_branch_injection() -> None:
    """The GUI EMT template setter must tolerate generator-line-load assignment order."""
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    bus0 = gce.Bus(name="Bus0", Vnom=10.0, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=10.0)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0 = gce.Line(name="line0", bus_from=bus0, bus_to=bus1, length=10.0, rate=900.0)
    load = gce.Load(name="load", P=10.0, Q=1.0)
    gen0 = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50.0, r1=0.001, x1=1.7)

    tower = gce.OverheadLineType(name="Tower", Vnom=10.0)
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

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    gen0.emt_template = get_generator_thevenin_rl_emt_template(vf=grid.var_factory)
    assert not gen0.emt_model.empty()
    assert len(bus0.get_pending_emt_devices()) == 1

    line0.emt_template = get_pi_line_emt_template(vf=grid.var_factory, phN=False, phA=True, phB=True, phC=True)
    load.emt_template = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True)

    assert len(bus0.get_pending_emt_devices()) == 0
    assert len(bus1.get_pending_emt_devices()) == 0
    assert not line0.emt_model.empty()
    assert not load.emt_model.empty()

    assert gen0.emt_model.external_mapping[VarPowerFlowRefferenceType.v_A].uid == bus0.emt_model.external_mapping[VarPowerFlowRefferenceType.v_A].uid
    assert gen0.emt_model.external_mapping[VarPowerFlowRefferenceType.v_B].uid == bus0.emt_model.external_mapping[VarPowerFlowRefferenceType.v_B].uid
    assert gen0.emt_model.external_mapping[VarPowerFlowRefferenceType.v_C].uid == bus0.emt_model.external_mapping[VarPowerFlowRefferenceType.v_C].uid
    assert load.emt_model.external_mapping[VarPowerFlowRefferenceType.v_A].uid == bus1.emt_model.external_mapping[VarPowerFlowRefferenceType.v_A].uid
    assert load.emt_model.external_mapping[VarPowerFlowRefferenceType.v_B].uid == bus1.emt_model.external_mapping[VarPowerFlowRefferenceType.v_B].uid
    assert load.emt_model.external_mapping[VarPowerFlowRefferenceType.v_C].uid == bus1.emt_model.external_mapping[VarPowerFlowRefferenceType.v_C].uid
