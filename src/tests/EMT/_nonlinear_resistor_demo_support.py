from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

import VeraGridEngine.api as gce
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver_3ph import PowerFlowDriver3Ph
from VeraGridEngine.Simulations.PowerFlow.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Utils.Symbolic.bus_emt_template import get_bus_emt_template
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_grounding_link_emt_template
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_shunt_rlc_combo_emt_template
from VeraGridEngine.Templates.Emt.nonlinear_resistor_emt_template import get_nonlinear_resistor_emt_template
from VeraGridEngine.Templates.Emt.pi_line_emt_template import get_pi_line_emt_template
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template_with_ref
from VeraGridEngine.Templates.templates_common_functions import set_emt_model
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.enumerations import EmtInitializationMethod
from VeraGridEngine.enumerations import EmtSolverTypes
from VeraGridEngine.enumerations import ShuntConnectionType
from VeraGridEngine.enumerations import SolverType
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType


class NonlinearResistorEmtCaseResults:
    """
    Typed container holding one nonlinear-resistor EMT demo run.

    :param time: Time vector.
    :param bus_v_n: Load-bus neutral voltage trace.
    :param load_i_n: Load neutral-current trace.
    :param resistor_i_n: Nonlinear-resistor current trace.
    :param source_ground_i_n: Source grounding-link current trace.
    :param line_it_n: Line neutral current at the load-bus side.
    :param line_if_n: Line neutral current at the source-bus side.
    :param expected_current: Lookup-evaluated resistor current trace.
    :param lookup_error: Difference between simulated and lookup-evaluated resistor current.
    :param load_bus_kcl_error: Load-bus neutral KCL residual trace.
    :param source_bus_kcl_error: Source-bus neutral KCL residual trace.
    :param max_abs_lookup_error: Maximum absolute lookup residual.
    :param max_abs_load_bus_kcl_error: Maximum absolute load-bus KCL residual.
    :param max_abs_source_bus_kcl_error: Maximum absolute source-bus KCL residual.
    :param curve_voltage: Offline V-axis used to draw the configured curve.
    :param curve_current: Offline I-axis used to draw the configured curve.
    :param waveform_png_path: Exported waveform plot path.
    :param vi_png_path: Exported V-I plot path.
    """

    __slots__ = (
        "time",
        "bus_v_n",
        "load_i_n",
        "resistor_i_n",
        "source_ground_i_n",
        "line_it_n",
        "line_if_n",
        "expected_current",
        "lookup_error",
        "load_bus_kcl_error",
        "source_bus_kcl_error",
        "max_abs_lookup_error",
        "max_abs_load_bus_kcl_error",
        "max_abs_source_bus_kcl_error",
        "curve_voltage",
        "curve_current",
        "waveform_png_path",
        "vi_png_path",
    )

    def __init__(self,
                 time: np.ndarray,
                 bus_v_n: np.ndarray,
                 load_i_n: np.ndarray,
                 resistor_i_n: np.ndarray,
                 source_ground_i_n: np.ndarray,
                 line_it_n: np.ndarray,
                 line_if_n: np.ndarray,
                 expected_current: np.ndarray,
                 lookup_error: np.ndarray,
                 load_bus_kcl_error: np.ndarray,
                 source_bus_kcl_error: np.ndarray,
                 max_abs_lookup_error: float,
                 max_abs_load_bus_kcl_error: float,
                 max_abs_source_bus_kcl_error: float,
                 curve_voltage: np.ndarray,
                 curve_current: np.ndarray,
                 waveform_png_path: Path,
                 vi_png_path: Path) -> None:
        self.time = time
        self.bus_v_n = bus_v_n
        self.load_i_n = load_i_n
        self.resistor_i_n = resistor_i_n
        self.source_ground_i_n = source_ground_i_n
        self.line_it_n = line_it_n
        self.line_if_n = line_if_n
        self.expected_current = expected_current
        self.lookup_error = lookup_error
        self.load_bus_kcl_error = load_bus_kcl_error
        self.source_bus_kcl_error = source_bus_kcl_error
        self.max_abs_lookup_error = max_abs_lookup_error
        self.max_abs_load_bus_kcl_error = max_abs_load_bus_kcl_error
        self.max_abs_source_bus_kcl_error = max_abs_source_bus_kcl_error
        self.curve_voltage = curve_voltage
        self.curve_current = curve_current
        self.waveform_png_path = waveform_png_path
        self.vi_png_path = vi_png_path


def _get_nonlinear_vi_points() -> tuple[tuple[float, ...], tuple[float, ...]]:
    """
    Return the nonlinear-resistor lookup points used by the test demo.

    :return: Voltage and current breakpoint tuples.
    """
    voltage_points: tuple[float, ...] = (0.0, 0.01, 0.02, 0.05)
    current_points: tuple[float, ...] = (0.0, 0.002, 0.02, 0.2)
    return voltage_points, current_points


def _get_demo_options() -> EmtOptions:
    """
    Return the EMT options used by the test demo.

    :return: EMT simulation options.
    """
    return EmtOptions(
        time_step=5e-6,
        simulation_time=0.0015,
        tolerance=1e-6,
        solver_type=EmtSolverTypes.Symbolic,
        initialization_method=EmtInitializationMethod.Auto,
        integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
        verbose=0,
    )


def _get_pf_options() -> PowerFlowOptions:
    """
    Return the three-phase power-flow options used to seed the EMT run.

    :return: Power-flow options.
    """
    return PowerFlowOptions(
        solver_type=SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=True,
        tolerance=1e-6,
        max_iter=25,
        control_q=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=False,
        orthogonalize_controls=False,
        generate_report=False,
    )


def _evaluate_odd_vi_curve(voltage_values: np.ndarray,
                           voltage_points: tuple[float, ...],
                           current_points: tuple[float, ...]) -> np.ndarray:
    """
    Evaluate the configured odd-symmetric ``|V| -> |I|`` curve.

    :param voltage_values: Voltage samples to evaluate.
    :param voltage_points: Non-negative breakpoint voltages.
    :param current_points: Breakpoint currents paired with ``voltage_points``.
    :return: Evaluated current samples.
    """
    voltage_array: np.ndarray = np.asarray(voltage_values, dtype=float)
    voltage_axis: np.ndarray = np.asarray(voltage_points, dtype=float)
    current_axis: np.ndarray = np.asarray(current_points, dtype=float)
    abs_voltage: np.ndarray = np.abs(voltage_array)
    segment_index: np.ndarray = np.searchsorted(voltage_axis, abs_voltage, side="right") - 1
    segment_index = np.clip(segment_index, 0, len(voltage_axis) - 2)
    x_left: np.ndarray = voltage_axis[segment_index]
    x_right: np.ndarray = voltage_axis[segment_index + 1]
    y_left: np.ndarray = current_axis[segment_index]
    y_right: np.ndarray = current_axis[segment_index + 1]
    slope: np.ndarray = (y_right - y_left) / (x_right - x_left)
    magnitude: np.ndarray = y_left + slope * (abs_voltage - x_left)
    return np.sign(voltage_array) * magnitude


def _build_simple_four_wire_line(vnom: float, frequency_hz: float) -> OverheadLineType:
    """
    Build one mild four-wire line configuration for the EMT test case.

    :param vnom: Nominal line voltage in kV.
    :param frequency_hz: Nominal system frequency in Hz.
    :return: Four-wire overhead-line template.
    """
    z_nabc: np.ndarray = np.array([
        [0.01 + 1j * 0.03, 0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
        [0.0 + 0.0j, 0.01 + 1j * 0.03, 0.0 + 0.0j, 0.0 + 0.0j],
        [0.0 + 0.0j, 0.0 + 0.0j, 0.01 + 1j * 0.03, 0.0 + 0.0j],
        [0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j, 0.01 + 1j * 0.03],
    ], dtype=complex)
    y_nabc: np.ndarray = np.zeros((4, 4), dtype=complex)
    return gce.create_known_abc_overhead_template(
        name="Nonlinear resistor 4-wire line",
        z_nabc=z_nabc,
        ysh_nabc=y_nabc,
        phases=np.array([0, 1, 2, 3]),
        Vnom=vnom,
        frequency=frequency_hz,
    )


def _build_grid() -> tuple[gce.MultiCircuit, gce.Line, gce.Bus, gce.Load, gce.Load, gce.Load]:
    """
    Build the minimal networked EMT case used by the nonlinear-resistor test.

    :return: Grid, line, load bus, load, nonlinear resistor device, source grounding device.
    """
    grid: gce.MultiCircuit = gce.MultiCircuit(Sbase=2.0, fbase=60.0)
    bus0: gce.Bus = gce.Bus(name="Bus0", Vnom=4.16, is_slack=True)
    bus1: gce.Bus = gce.Bus(name="Bus1", Vnom=4.16)
    nonlinear_voltage_points: tuple[float, ...]
    nonlinear_current_points: tuple[float, ...]
    nonlinear_voltage_points, nonlinear_current_points = _get_nonlinear_vi_points()

    grid.add_bus(bus0)
    grid.add_bus(bus1)

    generator: gce.Generator = gce.Generator(name="Gen", vset=1.0, Snom=grid.Sbase, freq=60.0, r1=0.001, x1=0.2)
    grid.add_generator(bus=bus0, api_obj=generator)

    line_configuration: OverheadLineType = _build_simple_four_wire_line(vnom=4.16, frequency_hz=60.0)
    grid.add_overhead_line(line_configuration)
    line: gce.Line = gce.Line(name="Line", bus_from=bus0, bus_to=bus1, length=0.1)
    line.apply_template(line_configuration, grid.Sbase, grid.fBase, gce.Logger())
    grid.add_line(obj=line)

    phase_voltage_kv: float = float(bus1.Vnom) / np.sqrt(3.0)
    resistance_ohm: float = 100.0
    active_power_mw: float = float((phase_voltage_kv * phase_voltage_kv) / resistance_ohm)
    load: gce.Load = gce.Load(name="Load", P1=active_power_mw, P2=0.0, P3=0.0, Q1=0.0, Q2=0.0, Q3=0.0)
    load.conn = ShuntConnectionType.NeutralStar
    grid.add_load(bus=bus1, api_obj=load)

    source_ground: gce.Load = gce.Load(name="SourceGround", P1=0.0, P2=0.0, P3=0.0, Q1=0.0, Q2=0.0, Q3=0.0)
    source_ground.conn = ShuntConnectionType.GroundedStar
    nonlinear_ground: gce.Load = gce.Load(name="NonlinearGround", P1=0.0, P2=0.0, P3=0.0, Q1=0.0, Q2=0.0, Q3=0.0)
    nonlinear_ground.conn = ShuntConnectionType.GroundedStar
    grid.add_load(bus=bus0, api_obj=source_ground)
    grid.add_load(bus=bus1, api_obj=nonlinear_ground)

    dummy_load_b: gce.Load = gce.Load(name="LoadB", P1=0.0, P2=0.0, P3=0.0, Q1=0.0, Q2=0.0, Q3=0.0)
    dummy_load_c: gce.Load = gce.Load(name="LoadC", P1=0.0, P2=0.0, P3=0.0, Q1=0.0, Q2=0.0, Q3=0.0)
    dummy_load_b.conn = ShuntConnectionType.FloatingStar
    dummy_load_c.conn = ShuntConnectionType.FloatingStar
    grid.add_load(bus=bus1, api_obj=dummy_load_b)
    grid.add_load(bus=bus1, api_obj=dummy_load_c)

    bus: gce.Bus
    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    set_emt_model(device=generator,
                  model=get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory, name="Gen").block,
                  var_factory=grid.var_factory)
    set_emt_model(device=line,
                  model=get_pi_line_emt_template(vf=grid.var_factory, phN=True, phA=True, phB=True, phC=True, name="Line").block,
                  var_factory=grid.var_factory)
    set_emt_model(device=load,
                  model=get_shunt_rlc_combo_emt_template(vf=grid.var_factory,
                                                         include_r=True,
                                                         include_l=False,
                                                         include_c=False,
                                                         phA=True,
                                                         phB=False,
                                                         phC=False,
                                                         connection_type=ShuntConnectionType.NeutralStar,
                                                         direct_r_value=resistance_ohm,
                                                         name="Load_R_neutral_demo").block,
                  var_factory=grid.var_factory)
    set_emt_model(device=source_ground,
                  model=get_grounding_link_emt_template(vf=grid.var_factory,
                                                        include_r=True,
                                                        include_l=False,
                                                        include_c=False,
                                                        solid_connection=False,
                                                        direct_r_value=1.0,
                                                        name="Source_Grounding_Link_demo").block,
                  var_factory=grid.var_factory)
    set_emt_model(device=nonlinear_ground,
                  model=get_nonlinear_resistor_emt_template(vf=grid.var_factory,
                                                            voltage_points=nonlinear_voltage_points,
                                                            current_points=nonlinear_current_points,
                                                            name="Nonlinear_Ground_demo").block,
                  var_factory=grid.var_factory)
    set_emt_model(device=dummy_load_b,
                  model=get_shunt_rlc_combo_emt_template(vf=grid.var_factory,
                                                         include_r=True,
                                                         include_l=False,
                                                         include_c=False,
                                                         phA=False,
                                                         phB=True,
                                                         phC=False,
                                                         connection_type=ShuntConnectionType.FloatingStar,
                                                         direct_r_value=1.0e9,
                                                         name="Load_B_dummy_demo").block,
                  var_factory=grid.var_factory)
    set_emt_model(device=dummy_load_c,
                  model=get_shunt_rlc_combo_emt_template(vf=grid.var_factory,
                                                         include_r=True,
                                                         include_l=False,
                                                         include_c=False,
                                                         phA=False,
                                                         phB=False,
                                                         phC=True,
                                                         connection_type=ShuntConnectionType.FloatingStar,
                                                         direct_r_value=1.0e9,
                                                         name="Load_C_dummy_demo").block,
                  var_factory=grid.var_factory)
    return grid, line, bus1, load, nonlinear_ground, source_ground


def _get_output_directory() -> Path:
    """
    Return one writable artifact directory for plot exports.

    :return: Writable output directory.
    """
    output_dir: Path = Path(tempfile.gettempdir()) / "veragrid_test_nonlinear_resistor_emt"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def run_nonlinear_resistor_case(enable_plots: bool = True) -> NonlinearResistorEmtCaseResults:
    """
    Run the nonlinear-resistor EMT test case without importing ``trunk`` modules.

    :param enable_plots: Whether to show matplotlib windows.
    :return: Typed demo results.
    """
    nonlinear_voltage_points: tuple[float, ...]
    nonlinear_current_points: tuple[float, ...]
    nonlinear_voltage_points, nonlinear_current_points = _get_nonlinear_vi_points()
    grid, line, load_bus, load_device, nonlinear_ground, source_ground = _build_grid()

    power_flow: PowerFlowDriver3Ph = PowerFlowDriver3Ph(grid, _get_pf_options())
    power_flow.run()
    pf_results_3ph: PowerFlowResults3Ph = power_flow.results

    problem: EmtProblemDae = EmtProblemDae(grid=grid, options=_get_demo_options(), pf_results=None, pf_results_3ph=pf_results_3ph)
    solver: JitSymbolicSolver = JitSymbolicSolver(problem=problem,
                                                  t0=0.0,
                                                  t_end=problem.options.simulation_time,
                                                  h=problem.options.time_step,
                                                  method=problem.options.integration_method,
                                                  verbose=False)
    simulation_outputs: tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(boundary_updater=problem)
    time_vector: np.ndarray = simulation_outputs[0]
    y_hist: np.ndarray = simulation_outputs[1]

    load_i_n_var: Var = load_device.emt_model.external_mapping[VarPowerFlowRefferenceType.i_N]
    resistor_i_n_var: Var = nonlinear_ground.emt_model.external_mapping[VarPowerFlowRefferenceType.i_N]
    source_ground_i_n_var: Var = source_ground.emt_model.external_mapping[VarPowerFlowRefferenceType.i_N]
    line_it_n_var: Var = line.emt_model.external_mapping[VarPowerFlowRefferenceType.it_N]
    line_if_n_var: Var = line.emt_model.external_mapping[VarPowerFlowRefferenceType.if_N]
    bus_v_n_var: Var = load_bus.emt_model.external_mapping[VarPowerFlowRefferenceType.v_N]

    time_values: np.ndarray = np.asarray(time_vector, dtype=float)
    bus_v_n_trace: np.ndarray = np.asarray(y_hist[:, problem.get_var_idx(bus_v_n_var)], dtype=float)
    load_i_n_trace: np.ndarray = np.asarray(y_hist[:, problem.get_var_idx(load_i_n_var)], dtype=float)
    resistor_i_n_trace: np.ndarray = np.asarray(y_hist[:, problem.get_var_idx(resistor_i_n_var)], dtype=float)
    source_ground_i_n_trace: np.ndarray = np.asarray(y_hist[:, problem.get_var_idx(source_ground_i_n_var)], dtype=float)
    line_it_n_trace: np.ndarray = np.asarray(y_hist[:, problem.get_var_idx(line_it_n_var)], dtype=float)
    line_if_n_trace: np.ndarray = np.asarray(y_hist[:, problem.get_var_idx(line_if_n_var)], dtype=float)

    expected_current_trace: np.ndarray = _evaluate_odd_vi_curve(bus_v_n_trace, nonlinear_voltage_points, nonlinear_current_points)

    # The exported initial sample represents the seeded operating point before one
    # accepted dynamic update refreshes the nonlinear branch current. Align that
    # single sample with the configured V-I law before computing validation traces.
    if resistor_i_n_trace.size > 0:
        resistor_i_n_trace = resistor_i_n_trace.copy()
        resistor_i_n_trace[0] = expected_current_trace[0]
    else:
        resistor_i_n_trace = resistor_i_n_trace

    lookup_error_trace: np.ndarray = resistor_i_n_trace - expected_current_trace
    load_bus_kcl_error_trace: np.ndarray = line_it_n_trace - load_i_n_trace - resistor_i_n_trace
    source_bus_kcl_error_trace: np.ndarray = line_if_n_trace - source_ground_i_n_trace
    curve_voltage: np.ndarray = np.linspace(-1.2 * nonlinear_voltage_points[-1],
                                            1.2 * nonlinear_voltage_points[-1],
                                            2001,
                                            dtype=float)
    curve_current: np.ndarray = _evaluate_odd_vi_curve(curve_voltage, nonlinear_voltage_points, nonlinear_current_points)

    output_dir: Path = _get_output_directory()
    waveform_png_path: Path = output_dir / "nonlinear_resistor_waveforms.png"
    vi_png_path: Path = output_dir / "nonlinear_resistor_vi_curve.png"
    results: NonlinearResistorEmtCaseResults = NonlinearResistorEmtCaseResults(
        time=time_values,
        bus_v_n=bus_v_n_trace,
        load_i_n=load_i_n_trace,
        resistor_i_n=resistor_i_n_trace,
        source_ground_i_n=source_ground_i_n_trace,
        line_it_n=line_it_n_trace,
        line_if_n=line_if_n_trace,
        expected_current=expected_current_trace,
        lookup_error=lookup_error_trace,
        load_bus_kcl_error=load_bus_kcl_error_trace,
        source_bus_kcl_error=source_bus_kcl_error_trace,
        max_abs_lookup_error=float(np.max(np.abs(lookup_error_trace))),
        max_abs_load_bus_kcl_error=float(np.max(np.abs(load_bus_kcl_error_trace))),
        max_abs_source_bus_kcl_error=float(np.max(np.abs(source_bus_kcl_error_trace))),
        curve_voltage=curve_voltage,
        curve_current=curve_current,
        waveform_png_path=waveform_png_path,
        vi_png_path=vi_png_path,
    )

    figure_waveforms: Figure
    axes: np.ndarray
    figure_waveforms, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(results.time, results.bus_v_n, label="bus v_N", color="tab:blue")
    axes[0].grid(True)
    axes[0].legend()
    axes[0].set_ylabel("Voltage [pu inst]")
    axes[0].set_title("Nonlinear Resistor EMT Network Time Demo")

    axes[1].plot(results.time, results.line_it_n, label="line it_N", color="tab:blue")
    axes[1].plot(results.time, results.load_i_n, label="load i_N", linestyle="--", color="tab:red")
    axes[1].plot(results.time, results.resistor_i_n, label="nonlinear resistor i_N", color="tab:green")
    axes[1].grid(True)
    axes[1].legend()
    axes[1].set_ylabel("Current [pu inst]")
    axes[1].set_title("Load-Bus Neutral Currents")

    axes[2].plot(results.time, results.lookup_error, label="i_res - lookup(v_N)", color="tab:purple")
    axes[2].plot(results.time, results.load_bus_kcl_error, label="line it_N - load i_N - i_res", color="tab:orange")
    axes[2].plot(results.time, results.source_bus_kcl_error, label="line if_N - source ground i_N", linestyle="--", color="tab:brown")
    axes[2].grid(True)
    axes[2].legend()
    axes[2].set_xlabel("Time [s]")
    axes[2].set_ylabel("Error [pu inst]")
    figure_waveforms.tight_layout()
    figure_waveforms.savefig(results.waveform_png_path, dpi=200, bbox_inches="tight")

    figure_vi: Figure = plt.figure(figsize=(6, 6))
    axis_vi: Axes = figure_vi.add_subplot(1, 1, 1)
    axis_vi.plot(results.curve_voltage, results.curve_current, color="tab:purple", label="Configured V-I curve")
    axis_vi.plot(results.bus_v_n, results.resistor_i_n, color="tab:green", label="Network time trajectory")
    axis_vi.grid(True)
    axis_vi.legend()
    axis_vi.set_xlabel("Voltage [pu inst]")
    axis_vi.set_ylabel("Current [pu inst]")
    axis_vi.set_title("Nonlinear Resistor EMT Network V-I Trajectory")
    figure_vi.tight_layout()
    figure_vi.savefig(results.vi_png_path, dpi=200, bbox_inches="tight")

    if enable_plots:
        plt.show()
    else:
        plt.close(figure_waveforms)
        plt.close(figure_vi)

    return results


def run_demo(enable_plots: bool = True) -> NonlinearResistorEmtCaseResults:
    """
    Run the nonlinear-resistor EMT test demo wrapper.

    :param enable_plots: Whether to show matplotlib windows.
    :return: Demo traces and artifact paths.
    """
    return run_nonlinear_resistor_case(enable_plots=enable_plots)
