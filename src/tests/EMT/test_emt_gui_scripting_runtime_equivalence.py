from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

import VeraGridEngine.api as gce
from VeraGrid.Session.dynamic_editor_entries import build_dynamic_editor_entry, get_templates_for_entry
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType
from VeraGridEngine.Devices.Branches.wire import Wire
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Simulations.EMT.emt_driver import EmtSimulationDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_driver_3ph import PowerFlowDriver3Ph
from VeraGridEngine.Templates.Emt.load_zip_emt_template import get_load_ZIP_emt_template
from VeraGridEngine.Templates.Emt.pi_line_emt_template import get_pi_line_emt_template
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template_with_ref
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_template
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_emt_model
from VeraGridEngine.enumerations import BranchImpedanceMode, DynamicIntegrationMethod, DynamicSimulationMode, EmtInitializationMethod, EmtSolverTypes, ShuntConnectionType, SolverType


def _build_two_bus_zip_grid() -> Tuple[MultiCircuit, Generator, Line, Load]:
    """
    Build one shared two-bus EMT benchmark case.

    :return: Grid and the three dynamic devices used by the test.
    :rtype: Tuple[MultiCircuit, Generator, Line, Load]
    """
    grid: MultiCircuit = MultiCircuit(Sbase=2.0, fbase=50.0)
    vnom: float = 10.0

    bus0: Bus = Bus(name="Bus0", Vnom=vnom, is_slack=True)
    bus1: Bus = Bus(name="Bus1", Vnom=vnom)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0: Line = Line(name="line0", bus_from=bus0, bus_to=bus1, length=10.0, rate=900.0)
    tower: OverheadLineType = OverheadLineType(name="Tower", Vnom=vnom)
    wire: Wire = Wire(name="Panther 30/7 ACSR", diameter=21.0, diameter_internal=9.0, is_tube=True, r=0.1363, max_current=1)
    tower.add_wire_relationship(wire=wire, xpos=-12.65, ypos=27.5, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0.0, ypos=27.5, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=12.65, ypos=27.5, phase=3)
    tower.compute()
    line0.apply_template(tower, grid.Sbase, grid.fBase)

    r_ph: float = 100.0
    v_ph: float = vnom / (3.0 ** 0.5)
    p_ph: float = (v_ph ** 2) / r_ph
    q_ph: float = 0.0
    load: Load = Load(name="load", P1=p_ph, P2=p_ph, P3=p_ph, Q1=q_ph, Q2=q_ph, Q3=q_ph)
    load.conn = ShuntConnectionType.GroundedStar

    gen0: Generator = Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50.0, r1=0.001, x1=1.7)

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    grid.add_emt_model(get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory))
    grid.add_emt_model(get_pi_line_emt_template(vf=grid.var_factory, phN=False, phA=True, phB=True, phC=True))
    grid.add_emt_model(get_load_ZIP_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True))

    return grid, gen0, line0, load


def _build_pf_options() -> PowerFlowOptions:
    """
    Build the three-phase power-flow options used by the EMT benchmark.

    :return: Configured power-flow options.
    :rtype: PowerFlowOptions
    """
    return PowerFlowOptions(
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
        branch_impedance_tolerance_mode=BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=False,
        initialize_angles=False,
        generate_report=False,
    )


def _build_emt_options() -> EmtOptions:
    """
    Build the EMT simulation options used by the equivalence test.

    :return: Configured EMT options.
    :rtype: EmtOptions
    """
    return EmtOptions(
        time_step=5e-6,
        simulation_time=2e-4,
        tolerance=1e-6,
        solver_type=EmtSolverTypes.StructuralCompiled,
        integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
        initialization_method=EmtInitializationMethod.PseudoTransient,
        verbose=0,
    )


def _collect_block_signature(block: Block) -> Dict[str, Any]:
    """
    Collect one structural signature from a symbolic block tree.

    :param block: Root symbolic block to inspect.
    :type block: Block
    :return: Comparable structural signature.
    :rtype: Dict[str, Any]
    """
    signature: Dict[str, Any] = dict()
    all_blocks: List[Block] = block.get_all_blocks()

    signature["block_count"] = len(all_blocks)
    signature["state_var_names"] = [var.name for blk in all_blocks for var in blk.state_vars]
    signature["algebraic_var_names"] = [var.name for blk in all_blocks for var in blk.algebraic_vars]
    signature["diff_var_names"] = [var.name for blk in all_blocks for var in blk.diff_vars]
    signature["parameter_names"] = [var.name for blk in all_blocks for var in blk.parameters.keys()]
    signature["event_names"] = [var.name for blk in all_blocks for var in blk.event_dict.keys()]
    signature["root_in_refs"] = [var.ref for var in block.in_vars]
    signature["root_out_refs"] = [var.ref for var in block.out_vars]
    signature["root_mapping_keys"] = list(block.external_mapping.keys())

    return signature


def _run_power_flow(grid: MultiCircuit) -> Any:
    """
    Run the EMT benchmark three-phase power flow.

    :param grid: Network model.
    :type grid: MultiCircuit
    :return: Three-phase power-flow results.
    :rtype: Any
    """
    power_flow: PowerFlowDriver3Ph = PowerFlowDriver3Ph(grid, _build_pf_options())
    power_flow.run()
    return power_flow.results


def _run_emt_driver(grid: MultiCircuit, pf_results_3ph: Any) -> EmtResults:
    """
    Run one EMT simulation and return its results.

    :param grid: Network model.
    :type grid: MultiCircuit
    :param pf_results_3ph: Three-phase power-flow results.
    :type pf_results_3ph: Any
    :return: EMT simulation results.
    :rtype: EmtResults
    """
    driver: EmtSimulationDriver = EmtSimulationDriver(
        grid=grid,
        options=_build_emt_options(),
        pf_results_3ph=pf_results_3ph,
        pf_results=None,
    )
    driver.run()

    if driver.results is None:
        raise AssertionError("EMT driver did not produce results.")
    else:
        return driver.results


def _build_problem(grid: MultiCircuit, pf_results_3ph: Any) -> EmtProblemDae:
    """
    Build one EMT problem for the benchmark grid.

    :param grid: Network model.
    :type grid: MultiCircuit
    :param pf_results_3ph: Three-phase power-flow results.
    :type pf_results_3ph: Any
    :return: EMT problem.
    :rtype: EmtProblemDae
    """
    return EmtProblemDae(grid=grid, options=_build_emt_options(), pf_results_3ph=pf_results_3ph, pf_results=None)


def _get_editor_templates_for_device(grid: MultiCircuit,
                                     device: Any) -> list[Any]:
    """
    Resolve the dynamic-editor template library for one EMT-capable device.

    :param grid: Circuit that owns the device and template library.
    :type grid: MultiCircuit
    :param device: Device to inspect.
    :type device: Any
    :return: Templates exposed by the editor for the given device.
    :rtype: list[Any]
    """
    entry = build_dynamic_editor_entry(api_object=device, circuit=grid)

    if entry is None:
        raise AssertionError("The dynamic editor did not create an EMT entry for the device.")
    else:
        pass

    assert DynamicSimulationMode.EMT in entry.available_modes

    return get_templates_for_entry(entry=entry, mode=DynamicSimulationMode.EMT)


def _find_template_by_name(templates: list[Any], expected_name: str) -> Any:
    """
    Find one named template inside the editor library list.

    :param templates: Templates exposed by the editor library.
    :type templates: list[Any]
    :param expected_name: Name that should be present.
    :type expected_name: str
    :return: Matching template object.
    :rtype: Any
    """
    template_obj: Any
    for template_obj in templates:
        if template_obj.name == expected_name:
            return template_obj
        else:
            pass

    raise AssertionError(f"Template {expected_name} was not exposed by the dynamic editor library.")


def test_emt_gui_and_scripting_follow_same_runtime_workflow() -> None:
    """
    Compare EMT GUI assignment against EMT scripting assembly end to end.

    :return: None.
    :rtype: None
    """
    script_grid: MultiCircuit
    script_gen: Generator
    script_line: Line
    script_load: Load
    script_grid, script_gen, script_line, script_load = _build_two_bus_zip_grid()

    bus_obj: Bus
    for bus_obj in script_grid.buses:
        get_bus_emt_template(script_grid, bus_obj)

    set_emt_model(device=script_gen,
                  model=get_generator_thevenin_rl_emt_template_with_ref(vf=script_grid.var_factory).block,
                  var_factory=script_grid.var_factory)
    set_emt_model(device=script_line,
                  model=get_pi_line_emt_template(vf=script_grid.var_factory, phN=False, phA=True, phB=True, phC=True).block,
                  var_factory=script_grid.var_factory)
    set_emt_model(device=script_load,
                  model=get_load_ZIP_emt_template(vf=script_grid.var_factory, phA=True, phB=True, phC=True).block,
                  var_factory=script_grid.var_factory)

    gui_grid: MultiCircuit
    gui_gen: Generator
    gui_line: Line
    gui_load: Load
    gui_grid, gui_gen, gui_line, gui_load = _build_two_bus_zip_grid()

    gen_templates: list[Any] = _get_editor_templates_for_device(gui_grid, gui_gen)
    line_templates: list[Any] = _get_editor_templates_for_device(gui_grid, gui_line)
    load_templates: list[Any] = _get_editor_templates_for_device(gui_grid, gui_load)

    gen_template_names: list[str] = [template.name for template in gen_templates]
    line_template_names: list[str] = [template.name for template in line_templates]
    load_template_names: list[str] = [template.name for template in load_templates]

    assert "emt_thevenin_eq_generator_template" in gen_template_names
    assert "emt_thevenin_eq_generator_template" not in line_template_names
    assert "emt_thevenin_eq_generator_template" not in load_template_names
    assert "Pi" in line_template_names
    assert "Pi" not in gen_template_names
    assert "Pi" not in load_template_names
    assert "ZIP_Load_EMT_3ph" in load_template_names
    assert "ZIP_Load_EMT_3ph" not in gen_template_names
    assert "ZIP_Load_EMT_3ph" not in line_template_names

    gui_gen_template: Any = _find_template_by_name(gen_templates, "emt_thevenin_eq_generator_template")
    gui_line_template: Any = _find_template_by_name(line_templates, "Pi")
    gui_load_template: Any = _find_template_by_name(load_templates, "ZIP_Load_EMT_3ph")

    gui_gen.emt_template = gui_gen_template
    gui_line.emt_template = gui_line_template
    gui_load.emt_template = gui_load_template

    assert _collect_block_signature(gui_gen.emt_model) == _collect_block_signature(script_gen.emt_model)
    assert _collect_block_signature(gui_line.emt_model) == _collect_block_signature(script_line.emt_model)
    assert _collect_block_signature(gui_load.emt_model) == _collect_block_signature(script_load.emt_model)

    script_pf_results_3ph: Any = _run_power_flow(script_grid)
    gui_pf_results_3ph: Any = _run_power_flow(gui_grid)

    script_problem: EmtProblemDae = _build_problem(script_grid, script_pf_results_3ph)
    gui_problem: EmtProblemDae = _build_problem(gui_grid, gui_pf_results_3ph)

    assert script_problem.get_states_number() == gui_problem.get_states_number()
    assert script_problem.get_algebraic_var_number() == gui_problem.get_algebraic_var_number()
    assert len(script_problem.get_constant_parameters()) == len(gui_problem.get_constant_parameters())
    assert len(script_problem.get_variable_parameters()) == len(gui_problem.get_variable_parameters())

    script_results: EmtResults = _run_emt_driver(script_grid, script_pf_results_3ph)
    gui_results: EmtResults = _run_emt_driver(gui_grid, gui_pf_results_3ph)

    assert len(script_results.variables) == len(gui_results.variables)
    assert len(script_results.diff_variables) == len(gui_results.diff_variables)
    assert list(script_results.variable_array) == list(gui_results.variable_array)
    assert np.array_equal(script_results.has_event_group_results, gui_results.has_event_group_results)
    assert np.allclose(script_results.values, gui_results.values, rtol=1e-8, atol=1e-8)
    assert np.allclose(script_results.diff_values, gui_results.diff_values, rtol=1e-8, atol=1e-8)
