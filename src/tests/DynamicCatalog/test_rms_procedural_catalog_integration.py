from __future__ import annotations

import numpy as np
import pytest

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import get_complete_generator_template_rms
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.BasicBlockCatalog import get_basic_block_catalog_descriptor_by_key
from VeraGridEngine.Templates.BasicBlockCatalog import load_basic_block_catalog_template
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.procedural_logic import build_boundary_updater_from_block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.enumerations import RmsInitializationMethod
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType

import VeraGridEngine.api as gce

pytestmark = pytest.mark.filterwarnings("error")


def _passthrough_event_params(values: np.ndarray, _: float) -> np.ndarray:
    """
    Return the runtime parameter vector without applying any extra transformation.

    :param values: Runtime parameter vector.
    :param _: Current time.
    :returns: Unmodified parameter vector.
    """

    return values


def _build_procedural_catalog_load_rms_template(vf: VarFactory,
                                                name: str = "Catalog procedural load") -> tuple[RmsModelTemplate, Var, Var, Var]:
    """
    Build one RMS load wrapper that uses a procedural catalog block to gate active power.
    """

    template = RmsModelTemplate(name=name)
    template.tpe = DeviceType.LoadDevice

    vm = vf.add_var(f"Vm_{name}")
    va = vf.add_var(f"Va_{name}")
    p_ref = vf.add_var(f"P_ref_{name}")
    q_ref = vf.add_var(f"Q_ref_{name}")
    p_out = vf.add_var(f"P_out_{name}")
    q_out = vf.add_var(f"Q_out_{name}")
    p_ref_const = vf.add_var(f"P_ref_const_{name}")
    q_ref_const = vf.add_var(f"Q_ref_const_{name}")

    enable_descriptor = get_basic_block_catalog_descriptor_by_key()["enable_signal"]
    enable_template = load_basic_block_catalog_template(enable_descriptor, vf, name=f"{name} enable")
    enable_block = enable_template.block
    enable_param = next(iter(enable_block.event_dict.keys()))
    enable_mode = next(iter(enable_block.mode_dict.keys()))
    enable_block.event_dict[enable_param] = vf.add_const(1.0, name="Enable")
    enable_block.mode_dict[enable_mode] = vf.add_const(1.0, name="Enable mode")
    enable_block.connect([enable_block.in_vars[0]], [p_ref])
    enable_block.init_eqs[enable_block.out_vars[0]] = p_ref

    template.block = Block(
        children=[enable_block],
        in_vars=[vm, va],
        algebraic_vars=[p_ref, q_ref, p_out, q_out],
        algebraic_eqs=[
            p_ref - p_ref_const,
            q_ref - q_ref_const,
            p_out - enable_block.out_vars[0],
            q_out - q_ref,
        ],
        init_eqs={
            p_ref: p_ref_const,
            q_ref: q_ref_const,
            p_out: enable_block.out_vars[0],
            q_out: q_ref,
        },
        out_vars=[p_out, q_out],
        name=name,
    )
    template.block.event_dict[p_ref_const] = vf.add_const(-0.10, name="P_ref")
    template.block.event_dict[q_ref_const] = vf.add_const(-0.01, name="Q_ref")
    template.block.external_mapping = {
        VarPowerFlowRefferenceType.Vm: vm,
        VarPowerFlowRefferenceType.Va: va,
        VarPowerFlowRefferenceType.P: p_out,
        VarPowerFlowRefferenceType.Q: q_out,
    }

    return template, enable_param, enable_mode, p_out


def test_rms_update_variable_params_applies_catalog_procedural_logic() -> None:
    descriptor = get_basic_block_catalog_descriptor_by_key()["enable_signal_fixed"]
    template = load_basic_block_catalog_template(descriptor, VarFactory())
    problem = RmsProblemDae.__new__(RmsProblemDae)
    runtime_parameters = list(template.block.event_dict.keys()) + list(template.block.mode_dict.keys())
    ordered_vars = list()

    for candidate in template.block.in_vars + template.block.out_vars + template.block.algebraic_vars + template.block.state_vars:
        if candidate.uid not in {var.uid for var in ordered_vars}:
            ordered_vars.append(candidate)
        else:
            pass

    problem.sys_block = template.block
    problem._glob_time = Var("glob_time")
    problem._uid2idx_vars = {var.uid: idx for idx, var in enumerate(ordered_vars)}
    problem._uid2idx_event_params = {var.uid: idx for idx, var in enumerate(runtime_parameters)}
    problem._variable_parameters = runtime_parameters
    problem._parameters_values = list()
    problem._constant_params = np.zeros(0, dtype=float)
    problem._variable_parameters_values = np.array([1.0, 0.0], dtype=float)
    problem._event_params_fn = _passthrough_event_params
    problem._block_boundary_updater = build_boundary_updater_from_block(problem)

    RmsProblemDae.update_variable_params(problem, t=0.0, x_snapshot=np.zeros(len(ordered_vars), dtype=float))

    assert problem._variable_parameters_values[0] == 1.0
    assert problem._variable_parameters_values[1] == 1.0


def test_rms_catalog_procedural_logic_changes_load_output_during_real_simulation() -> None:
    grid = gce.MultiCircuit(Sbase=100, fbase=50.0)

    bus0 = gce.Bus(name="Bus0", Vnom=10, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=10)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    for bus in grid.buses:
        initialize_bus_rms(bus, vf=grid.var_factory)

    line0 = gce.Line(
        name="line 0-2",
        bus_from=bus0,
        bus_to=bus1,
        r=0.029585798816568046,
        x=0.07100591715976332,
        b=0.03,
        rate=900.0,
    )

    load = gce.Load(P=10.0, Q=1.0)
    gen0 = gce.Generator(
        name="Gen0",
        P=10.0,
        vset=1.0,
        Snom=900,
        x1=0.86138701,
        r1=0.3,
        freq=50.0,
    )

    genqec_mdl = get_complete_generator_template_rms(grid.var_factory).block
    line_mdl = get_line_rms_template(grid.var_factory).block
    load_mdl, enable_param, enable_mode, p_out = _build_procedural_catalog_load_rms_template(grid.var_factory)

    genqec_mdl.connect([genqec_mdl.in_vars[0]], [bus0.rms_model.out_vars[0]])
    genqec_mdl.connect([genqec_mdl.in_vars[1]], [bus0.rms_model.out_vars[1]])
    line_mdl.connect([line_mdl.in_vars[0]], [bus0.rms_model.out_vars[0]])
    line_mdl.connect([line_mdl.in_vars[1]], [bus0.rms_model.out_vars[1]])
    line_mdl.connect([line_mdl.in_vars[2]], [bus1.rms_model.out_vars[0]])
    line_mdl.connect([line_mdl.in_vars[3]], [bus1.rms_model.out_vars[1]])

    big_gen = Block(children=[genqec_mdl])
    big_gen.external_mapping.update({VarPowerFlowRefferenceType.P: genqec_mdl.out_vars[0]})
    big_gen.external_mapping.update({VarPowerFlowRefferenceType.Q: genqec_mdl.out_vars[1]})

    line0.rms_model = line_mdl
    load.rms_model = load_mdl.block
    gen0.rms_model = big_gen

    events_group = RmsEventsGroup("catalog-procedural-rms")
    disable_event = RmsEvent(device=load, parameter=enable_param, time=0.05, value=0.0, group=events_group)
    grid.add_rms_event(disable_event)

    grid.add_line(line0)
    grid.add_load(bus=bus1, api_obj=load)
    grid.add_generator(bus=bus0, api_obj=gen0)

    options = gce.PowerFlowOptions(
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
    pf_results = gce.power_flow(grid, options=options)

    rms_options = RmsOptions(
        time_step=0.001,
        simulation_time=0.12,
        tolerance=1e-6,
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        initialization_method=RmsInitializationMethod.Explicit,
        use_init_values=False,
        max_iter=1000,
        verbose=0,
    )
    problem = RmsProblemDae(grid=grid, options=rms_options, pf_results=pf_results)
    problem.set_events_group(events_group)

    solver = BackEulerImplicitIntegration(
        problem=problem,
        t0=0.0,
        t_end=rms_options.simulation_time,
        h=rms_options.time_step,
        max_iter=rms_options.max_iter,
    )

    time_s, state_traj, well_initialized, converged = solver.simulate()

    assert converged
    assert np.isfinite(state_traj).all()

    p_index = problem.get_var_idx(p_out)
    p_trace = state_traj[:, p_index]
    pre_event = p_trace[time_s <= 0.040]
    post_event = p_trace[time_s >= 0.080]

    assert np.mean(pre_event) < -0.08
    assert np.max(np.abs(post_event)) < 1e-6

    mode_idx = problem.uid2idx_event_params[enable_mode.uid]
    assert problem._variable_parameters_values[mode_idx] == 0.0
