from __future__ import annotations

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_bundle import build_jmarti_fit_bundle
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_frequency_samples import build_jmarti_frequency_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_loewner_seed import build_jmarti_mode_loewner_seed
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import build_jmarti_modal_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import estimate_jmarti_mode_delays
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import JMartiHistoryRuntime
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import get_jmarti_block_runtime_data
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import set_jmarti_block_fit_bundle
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import build_jmarti_mode_vector_fit
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver_3ph import PowerFlowDriver3Ph
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_template
from VeraGridEngine.Templates.Emt.jmarti_line_emt_template import get_jmarti_line_emt_template
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_shunt_rlc_combo_emt_template
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_emt_model
from VeraGridEngine.enumerations import DynamicIntegrationMethod, EmtInitializationMethod, EmtSolverTypes, ShuntConnectionType, SolverType


def _evaluate_scalar_rational_response(frequency_hz: np.ndarray,
                                       poles_s: np.ndarray,
                                       residues: np.ndarray,
                                       constant_term: complex = 0.0 + 0.0j) -> np.ndarray:
    """
    Evaluate one scalar rational response on the imaginary axis.

    :param frequency_hz: Frequency grid in Hz.
    :param poles_s: Continuous-time poles.
    :param residues: Residues paired with ``poles_s``.
    :param constant_term: Optional constant term.
    :return: Complex response samples.
    """
    angular_frequency: np.ndarray = 2.0 * np.pi * frequency_hz
    response: np.ndarray = np.zeros(frequency_hz.size, dtype=np.complex128)
    sample_index: int = 0
    pole_index: int
    s_value: complex

    while sample_index < frequency_hz.size:
        s_value = 1j * angular_frequency[sample_index]
        response[sample_index] = complex(constant_term)
        pole_index = 0

        while pole_index < poles_s.size:
            response[sample_index] = response[sample_index] + residues[pole_index] / (s_value - poles_s[pole_index])
            pole_index += 1

        sample_index += 1

    return response


def _build_jmarti_fit_bundle_for_three_phase_line() -> object:
    """
    Build one synthetic three-mode JMARTI fit bundle suitable for EMT integration tests.

    :return: Offline JMARTI fit bundle.
    """
    frequency_hz: np.ndarray = np.asarray([10.0, 40.0, 80.0, 160.0, 320.0, 640.0], dtype=np.float64)
    z_per_length: np.ndarray = np.zeros((frequency_hz.size, 3, 3), dtype=np.complex128)
    y_per_length: np.ndarray = np.zeros((frequency_hz.size, 3, 3), dtype=np.complex128)
    sample_index: int = 0
    options = JMartiFitOptions(forced_model_order=1, vf_max_iterations=6)
    yc_mode_responses = [
        _evaluate_scalar_rational_response(frequency_hz, np.asarray([-50.0 + 0.0j], dtype=np.complex128), np.asarray([0.30 + 0.0j], dtype=np.complex128), constant_term=0.10 + 0.0j),
        _evaluate_scalar_rational_response(frequency_hz, np.asarray([-120.0 + 0.0j], dtype=np.complex128), np.asarray([0.15 + 0.0j], dtype=np.complex128), constant_term=0.08 + 0.0j),
        _evaluate_scalar_rational_response(frequency_hz, np.asarray([-200.0 + 0.0j], dtype=np.complex128), np.asarray([0.10 + 0.0j], dtype=np.complex128), constant_term=0.07 + 0.0j),
    ]
    hres_mode_responses = [
        _evaluate_scalar_rational_response(frequency_hz, np.asarray([-80.0 + 0.0j], dtype=np.complex128), np.asarray([0.020 + 0.0j], dtype=np.complex128), constant_term=0.85 + 0.0j),
        _evaluate_scalar_rational_response(frequency_hz, np.asarray([-160.0 + 0.0j], dtype=np.complex128), np.asarray([0.010 + 0.0j], dtype=np.complex128), constant_term=0.75 + 0.0j),
        _evaluate_scalar_rational_response(frequency_hz, np.asarray([-240.0 + 0.0j], dtype=np.complex128), np.asarray([0.008 + 0.0j], dtype=np.complex128), constant_term=0.65 + 0.0j),
    ]
    mode_index: int
    samples = None
    modal_samples = None
    mode_delays = None
    yc_fits = list()
    hres_fits = list()

    while sample_index < frequency_hz.size:
        z_per_length[sample_index, :, :] = np.diag(np.asarray([
            1.0 + 0.2j * float(sample_index + 1),
            2.0 + 0.3j * float(sample_index + 1),
            3.0 + 0.4j * float(sample_index + 1),
        ], dtype=np.complex128))
        y_per_length[sample_index, :, :] = np.diag(np.asarray([
            yc_mode_responses[0][sample_index] * yc_mode_responses[0][sample_index],
            yc_mode_responses[1][sample_index] * yc_mode_responses[1][sample_index],
            yc_mode_responses[2][sample_index] * yc_mode_responses[2][sample_index],
        ], dtype=np.complex128))
        sample_index += 1

    samples = build_jmarti_frequency_samples(
        frequency_hz=frequency_hz,
        z_per_length=z_per_length,
        y_per_length=y_per_length,
        line_length_m=1000.0,
        phase_labels=("A", "B", "C"),
    )
    modal_samples = build_jmarti_modal_samples(samples=samples, options=options)
    mode_delays = estimate_jmarti_mode_delays(modal_samples, options=options)

    mode_index = 0
    while mode_index < 3:
        yc_fits.append(
            build_jmarti_mode_vector_fit(
                frequency_hz=frequency_hz,
                response_values=modal_samples.get_yc_modal()[:, mode_index],
                loewner_seed=build_jmarti_mode_loewner_seed(
                    frequency_hz,
                    modal_samples.get_yc_modal()[:, mode_index],
                    "Yc",
                    mode_index,
                    options,
                ),
                options=options,
            )
        )
        hres_fits.append(
            build_jmarti_mode_vector_fit(
                frequency_hz=frequency_hz,
                response_values=hres_mode_responses[mode_index],
                loewner_seed=build_jmarti_mode_loewner_seed(
                    frequency_hz,
                    hres_mode_responses[mode_index],
                    "Hres",
                    mode_index,
                    options,
                ),
                options=options,
            )
        )
        mode_index += 1

    return build_jmarti_fit_bundle(
        modal_samples=modal_samples,
        mode_delays=mode_delays,
        yc_fits=yc_fits,
        hres_fits=hres_fits,
    )


def test_jmarti_emt_problem_builds_one_history_runtime_and_runs_short_simulation() -> None:
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    bus0 = gce.Bus(name="Bus0", Vnom=10.0, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=10.0)
    generator = gce.Generator(name="Gen", vset=1.0, Snom=grid.Sbase, freq=50.0, r1=0.001, x1=0.2)
    line_template = gce.create_known_abc_overhead_template(
        name="JMartiDemoLine",
        z_nabc=np.array([
            [0.01 + 1j * 0.03, 0.0 + 0.0j, 0.0 + 0.0j],
            [0.0 + 0.0j, 0.01 + 1j * 0.03, 0.0 + 0.0j],
            [0.0 + 0.0j, 0.0 + 0.0j, 0.01 + 1j * 0.03],
        ], dtype=complex),
        ysh_nabc=np.zeros((3, 3), dtype=complex),
        phases=np.array([1, 2, 3]),
        Vnom=10.0,
        frequency=50.0,
    )
    line = gce.Line(name="Line", bus_from=bus0, bus_to=bus1, length=0.1)
    load = gce.Load(name="Load", P1=0.05, P2=0.05, P3=0.05, Q1=0.0, Q2=0.0, Q3=0.0)
    load.conn = ShuntConnectionType.FloatingStar
    pf_options = PowerFlowOptions(
        solver_type=SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=True,
        tolerance=1.0e-6,
        max_iter=25,
        control_q=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=False,
        orthogonalize_controls=False,
        generate_report=False,
    )
    emt_options = EmtOptions(
        time_step=1.0e-4,
        simulation_time=3.0e-4,
        tolerance=1.0e-6,
        solver_type=EmtSolverTypes.Symbolic,
        initialization_method=EmtInitializationMethod.Auto,
        integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
        verbose=0,
    )

    grid.add_bus(bus0)
    grid.add_bus(bus1)
    grid.add_generator(bus=bus0, api_obj=generator)
    grid.add_overhead_line(line_template)
    line.apply_template(line_template, grid.Sbase, grid.fBase, gce.Logger())
    grid.add_line(obj=line)
    grid.add_load(bus=bus1, api_obj=load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    set_emt_model(device=generator, model=get_generator_thevenin_rl_emt_template(vf=grid.var_factory, name="Gen").block, var_factory=grid.var_factory)
    line_model = get_jmarti_line_emt_template(vf=grid.var_factory, phN=False, phA=True, phB=True, phC=True, name="Line").block
    set_jmarti_block_fit_bundle(line_model, _build_jmarti_fit_bundle_for_three_phase_line())
    set_emt_model(device=line, model=line_model, var_factory=grid.var_factory)
    set_emt_model(
        device=load,
        model=get_shunt_rlc_combo_emt_template(
            vf=grid.var_factory,
            include_r=True,
            include_l=False,
            include_c=False,
            phA=True,
            phB=True,
            phC=True,
            connection_type=ShuntConnectionType.FloatingStar,
            direct_r_value=100.0,
            name="Load_R_demo",
        ).block,
        var_factory=grid.var_factory,
    )

    original_line_model = line.emt_model
    original_api_mapping = dict(line.emt_model.api_obj_mapping)
    original_parameter_keys = set(line.emt_model.parameters.keys())
    original_event_keys = set(line.emt_model.event_dict.keys())

    power_flow = PowerFlowDriver3Ph(grid, pf_options)
    power_flow.run()
    problem = EmtProblemDae(grid=grid, options=emt_options, pf_results=None, pf_results_3ph=power_flow.results)
    working_line_model = problem._working_emt_models[id(line)]

    assert len(problem.history_models) == 1
    assert isinstance(problem.history_models[0], JMartiHistoryRuntime)
    assert line.emt_model is original_line_model
    assert dict(line.emt_model.api_obj_mapping) == original_api_mapping
    assert set(line.emt_model.parameters.keys()) == original_parameter_keys
    assert set(line.emt_model.event_dict.keys()) == original_event_keys
    assert working_line_model is not line.emt_model
    assert get_jmarti_block_runtime_data(line.emt_model) is None
    assert get_jmarti_block_runtime_data(working_line_model) is not None

    solver = JitSymbolicSolver(
        problem=problem,
        t0=0.0,
        t_end=problem.options.simulation_time,
        h=problem.options.time_step,
        method=problem.options.integration_method,
        verbose=False,
    )
    time_vector, state_history, _diff_history, converged, _diag = solver.simulate(boundary_updater=problem)

    assert len(time_vector) > 1
    assert np.isfinite(state_history).all()
    assert converged is True
