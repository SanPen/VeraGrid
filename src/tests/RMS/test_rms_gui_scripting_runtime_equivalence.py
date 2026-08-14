from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

import VeraGridEngine.api as gce
from VeraGrid.Session.dynamic_editor_entries import build_dynamic_editor_entry, get_templates_for_entry
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Simulations.Rms.rms_driver import RmsSimulationDriver
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import get_complete_generator_template_rms
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_rms_template import get_load_rms_template
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
from VeraGridEngine.enumerations import BranchImpedanceMode, DynamicIntegrationMethod, DynamicSimulationMode, RmsInitializationMethod, SolverType


def _build_two_bus_rms_grid() -> Tuple[MultiCircuit, Generator, Any, Load]:
    """
    Build one shared two-bus RMS benchmark case.

    :return: Grid and the three dynamic devices used by the test.
    :rtype: Tuple[MultiCircuit, Generator, Any, Load]
    """
    grid: MultiCircuit = gce.MultiCircuit(Sbase=100.0, fbase=50.0)

    bus0: Bus = gce.Bus(name="Bus0", Vnom=10.0, is_slack=True)
    bus1: Bus = gce.Bus(name="Bus1", Vnom=10.0)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    bus_obj: Bus
    for bus_obj in grid.buses:
        initialize_bus_rms(bus_obj, vf=grid.var_factory)

    line0 = gce.Line(name="line 0-2", bus_from=bus0, bus_to=bus1, r=0.029585, x=0.071005, b=0.03, rate=900.0)
    grid.add_line(line0)

    load: Load = gce.Load(P=9.999999, Q=0.999999)
    grid.add_load(bus=bus1, api_obj=load)

    gen0: Generator = gce.Generator(name="Gen0", P=10.0, vset=1.0, Snom=900.0, x1=0.86138701, r1=0.3, freq=50.0)
    grid.add_generator(bus=bus0, api_obj=gen0)

    grid.add_rms_model(get_complete_generator_template_rms(grid.var_factory))
    grid.add_rms_model(get_line_rms_template(grid.var_factory))
    grid.add_rms_model(get_load_rms_template(grid.var_factory))

    return grid, gen0, line0, load


def _build_rms_pf_options() -> PowerFlowOptions:
    """
    Build the RMS benchmark power-flow options.

    :return: Configured power-flow options.
    :rtype: PowerFlowOptions
    """
    return gce.PowerFlowOptions(
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


def _build_rms_options() -> RmsOptions:
    """
    Build the RMS simulation options used by the equivalence test.

    :return: Configured RMS options.
    :rtype: RmsOptions
    """
    return RmsOptions(
        time_step=0.001,
        simulation_time=0.02,
        tolerance=1e-6,
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        initialization_method=RmsInitializationMethod.Explicit,
        use_init_values=False,
        max_iter=1000,
        verbose=0,
    )


def _collect_block_signature(block: Block) -> Dict[str, Any]:
    """
    Collect one structural signature from a symbolic RMS block tree.

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
    signature["parameter_names"] = [var.name for blk in all_blocks for var in blk.parameters.keys()]
    signature["event_names"] = [var.name for blk in all_blocks for var in blk.event_dict.keys()]
    signature["root_in_refs"] = [var.ref for var in block.in_vars]
    signature["root_out_refs"] = [var.ref for var in block.out_vars]
    signature["root_mapping_keys"] = list(block.external_mapping.keys())

    return signature


def _run_rms_driver(grid: MultiCircuit) -> Tuple[RmsResults, RmsProblemDae]:
    """
    Run one RMS simulation and return both results and built problem.

    :param grid: Network model.
    :type grid: MultiCircuit
    :return: RMS simulation results and problem instance.
    :rtype: Tuple[RmsResults, RmsProblemDae]
    """
    pf_results: Any = gce.power_flow(grid, options=_build_rms_pf_options())
    driver: RmsSimulationDriver = RmsSimulationDriver(grid=grid, options=_build_rms_options(), pf_results=pf_results)
    driver.run()

    if driver.results is None:
        raise AssertionError("RMS driver did not produce results.")
    else:
        problem: RmsProblemDae = RmsProblemDae(grid=grid, options=_build_rms_options(), pf_results=pf_results)
        return driver.results, problem


def _get_editor_templates_for_device(grid: MultiCircuit,
                                     device: Any) -> list[Any]:
    """
    Resolve the dynamic-editor template library for one RMS-capable device.

    :param grid: Circuit that owns the device and template library.
    :type grid: MultiCircuit
    :param device: Device to inspect.
    :type device: Any
    :return: Templates exposed by the editor for the given device.
    :rtype: list[Any]
    """
    entry = build_dynamic_editor_entry(api_object=device, circuit=grid)

    if entry is None:
        raise AssertionError("The dynamic editor did not create an RMS entry for the device.")
    else:
        pass

    assert DynamicSimulationMode.RMS in entry.available_modes

    return get_templates_for_entry(entry=entry, mode=DynamicSimulationMode.RMS)


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


def test_rms_gui_and_scripting_follow_same_runtime_workflow() -> None:
    """
    Compare RMS GUI assignment against RMS scripting assembly end to end.

    :return: None.
    :rtype: None
    """
    script_grid: MultiCircuit
    script_gen: Generator
    script_line: Any
    script_load: Load
    script_grid, script_gen, script_line, script_load = _build_two_bus_rms_grid()

    set_rms_model(device=script_gen,
                  model=get_complete_generator_template_rms(script_grid.var_factory).block,
                  var_factory=script_grid.var_factory)
    set_rms_model(device=script_line,
                  model=get_line_rms_template(script_grid.var_factory).block,
                  var_factory=script_grid.var_factory)
    set_rms_model(device=script_load,
                  model=get_load_rms_template(script_grid.var_factory).block,
                  var_factory=script_grid.var_factory)

    gui_grid: MultiCircuit
    gui_gen: Generator
    gui_line: Any
    gui_load: Load
    gui_grid, gui_gen, gui_line, gui_load = _build_two_bus_rms_grid()

    gen_templates: list[Any] = _get_editor_templates_for_device(gui_grid, gui_gen)
    line_templates: list[Any] = _get_editor_templates_for_device(gui_grid, gui_line)
    load_templates: list[Any] = _get_editor_templates_for_device(gui_grid, gui_load)

    gen_template_names: list[str] = [template.name for template in gen_templates]
    line_template_names: list[str] = [template.name for template in line_templates]
    load_template_names: list[str] = [template.name for template in load_templates]

    assert "complete_generator_rms_template" in gen_template_names
    assert "complete_generator_rms_template" not in line_template_names
    assert "complete_generator_rms_template" not in load_template_names
    assert "Line_rms_template" in line_template_names
    assert "Line_rms_template" not in gen_template_names
    assert "Line_rms_template" not in load_template_names
    assert "Load rms template" in load_template_names
    assert "Load rms template" not in gen_template_names
    assert "Load rms template" not in line_template_names

    gui_gen_template: Any = _find_template_by_name(gen_templates, "complete_generator_rms_template")
    gui_line_template: Any = _find_template_by_name(line_templates, "Line_rms_template")
    gui_load_template: Any = _find_template_by_name(load_templates, "Load rms template")

    gui_gen.rms_template = gui_gen_template
    gui_line.rms_template = gui_line_template
    gui_load.rms_template = gui_load_template

    assert _collect_block_signature(gui_gen.rms_model) == _collect_block_signature(script_gen.rms_model)
    assert _collect_block_signature(gui_line.rms_model) == _collect_block_signature(script_line.rms_model)
    assert _collect_block_signature(gui_load.rms_model) == _collect_block_signature(script_load.rms_model)

    script_results: RmsResults
    script_problem: RmsProblemDae
    script_results, script_problem = _run_rms_driver(script_grid)

    gui_results: RmsResults
    gui_problem: RmsProblemDae
    gui_results, gui_problem = _run_rms_driver(gui_grid)

    assert script_problem.get_states_number() == gui_problem.get_states_number()
    assert script_problem.get_algebraic_var_number() == gui_problem.get_algebraic_var_number()
    assert len(script_problem._variable_parameters) == len(gui_problem._variable_parameters)
    assert len(script_results.variables) == len(gui_results.variables)
    assert list(script_results.variable_array) == list(gui_results.variable_array)
    assert np.array_equal(script_results.has_event_group_results, gui_results.has_event_group_results)
    assert np.allclose(script_results.values, gui_results.values, rtol=1e-8, atol=1e-8)
