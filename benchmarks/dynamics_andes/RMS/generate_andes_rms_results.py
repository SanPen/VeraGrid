# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Run any validated ANDES RMS time-domain benchmark from PyCharm."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import andes
import numpy as np

from benchmarks.dynamics_andes.RMS.rms_simulation import case_label
from benchmarks.dynamics_andes.RMS.rms_simulation import engine_results_directory
from benchmarks.dynamics_andes.RMS.rms_simulation import perturbation_state_label
from benchmarks.dynamics_andes.RMS.rms_simulation import rms_timing_phase_names
from benchmarks.dynamics_andes.RMS.rms_simulation import save_rms_timing_repetitions
from benchmarks.dynamics_andes.RMS.rms_simulation import write_key_value_csv
from benchmarks.dynamics_andes.RMS.rms_simulation import write_trajectory_csv


SYSTEM: str = "all"  # "Kundur", "IEEE14", "IEEE39", "NPCC140", "WECC179" or "all"
SCENARIO: str = "all"  # "base", "event" or "all"


def main() -> None:
    """Generate the selected standard ANDES RMS reference trajectories.

    Change ``SYSTEM`` and ``SCENARIO`` at the top of this file before running.

    :return: None.
    """
    repetitions: int = 10

    # Check both visible values so a typo cannot select another case silently.
    valid_systems: tuple[str, ...] = (
        "Kundur",
        "IEEE14",
        "IEEE39",
        "NPCC140",
        "WECC179",
    )
    valid_scenarios: tuple[str, ...] = ("base", "event")
    if SYSTEM == "all" or SYSTEM in valid_systems:
        pass
    else:
        raise ValueError(
            f"Unknown SYSTEM {SYSTEM!r}. Choose one of {valid_systems} or 'all'."
        )
    if SCENARIO == "all" or SCENARIO in valid_scenarios:
        pass
    else:
        raise ValueError(
            f"Unknown SCENARIO {SCENARIO!r}. Choose 'base', 'event' or 'all'."
        )

    # Expand the two visible selections before running the workflow.
    if SYSTEM == "all":
        selected_systems: tuple[str, ...] = valid_systems
    else:
        selected_systems = (SYSTEM,)

    if SCENARIO == "all":
        selected_scenarios: tuple[str, ...] = valid_scenarios
    else:
        selected_scenarios = (SCENARIO,)

    # Run ten complete, independent calculations for every selected scenario.
    # Each repetition reloads the ANDES case and creates a new dynamic problem.
    selected_system: str
    for selected_system in selected_systems:
        selected_scenario: str
        for selected_scenario in selected_scenarios:
            phase_count: int = len(rms_timing_phase_names())
            timing_samples: np.ndarray = np.empty(
                (repetitions, phase_count),
                dtype=float,
            )
            repetition_index: int
            for repetition_index in range(repetitions):
                print(
                    f"\nANDES {selected_system} {selected_scenario}: "
                    f"repetition {repetition_index + 1}/{repetitions}"
                )
                if selected_scenario == "base":
                    timing_samples[repetition_index, :] = run_andes_rms(
                        system_name=selected_system,
                        scenario_name="base",
                    )
                else:
                    timing_samples[repetition_index, :] = run_andes_rms(
                        system_name=selected_system,
                        scenario_name="event",
                        simulation_time=2.0,
                        speed_perturbation_pu=0.0,
                        event_time=0.2,
                        event_state_step_pu=1.0e-4,
                    )

            output_directory: Path = engine_results_directory(
                selected_system,
                "ANDES",
                selected_scenario,
            )
            save_rms_timing_repetitions(
                output_directory=output_directory,
                timing_samples=timing_samples,
            )


def resolve_andes_case_path(system_name: str) -> Path:
    """Resolve the physical ANDES case used by one benchmark preset.

    :param system_name: Selected benchmark system.
    :return: Absolute ANDES-readable case path.
    """
    script_directory: Path = Path(__file__).resolve().parent
    if system_name == "Kundur":
        case_path: Path = script_directory.parent / "kundur_ieee_no_shunt.json"
    elif system_name == "IEEE14":
        case_path = Path(andes.get_case("ieee14/ieee14_full.xlsx"))
    elif system_name == "IEEE39":
        case_path = Path(andes.get_case("ieee39/ieee39_full.xlsx"))
    elif system_name == "NPCC140":
        case_path = Path(andes.get_case("npcc/npcc.xlsx"))
    else:
        case_path = Path(andes.get_case("wecc/wecc_full.xlsx"))
    return case_path.resolve()


def andes_power_flow_tolerance(system_name: str) -> float:
    """Return the strictest established ANDES tolerance for one case.

    :param system_name: Selected benchmark system.
    :return: Newton power-flow tolerance.
    """
    if system_name == "WECC179":
        tolerance: float = 1.0e-10
    else:
        tolerance = 1.0e-13
    return tolerance


def configure_andes_system(
    system: Any,
    system_name: str,
    time_step: float,
    simulation_time: float,
    integration_tolerance: float,
    maximum_iterations: int,
) -> None:
    """Configure constant-power loads and an exact fixed-step Backward Euler run.

    :param system: Loaded ANDES system.
    :param system_name: Selected benchmark system.
    :param time_step: Fixed integration step in seconds.
    :param simulation_time: Final simulation time in seconds.
    :param integration_tolerance: Nonlinear integration tolerance.
    :param maximum_iterations: Maximum nonlinear iterations per step.
    :return: None.
    """
    # These fractions disable ANDES voltage-dependent load conversion so the
    # dynamic case retains the same constant-power model used by VeraGrid.
    system.files.no_output = True
    system.PQ.config.p2p = 1.0
    system.PQ.config.p2i = 0
    system.PQ.config.p2z = 0
    system.PQ.config.q2q = 1.0
    system.PQ.config.q2i = 0
    system.PQ.config.q2z = 0
    system.PFlow.config.tol = andes_power_flow_tolerance(system_name)

    # Both tools now solve the identical implicit Backward Euler formula on an
    # immutable 1 ms grid. Step shrinking and stability early-stop criteria are
    # disabled because VeraGrid does not use them in this benchmark.
    system.TDS.config.method = "backeuler"
    system.TDS.set_method("backeuler")
    system.TDS.config.t0 = 0.0
    system.TDS.config.tf = simulation_time
    system.TDS.config.tstep = time_step
    system.TDS.config.fixt = 1
    system.TDS.config.shrinkt = 0
    system.TDS.config.tol = integration_tolerance
    system.TDS.config.max_iter = maximum_iterations
    system.TDS.config.honest = 1
    system.TDS.config.g_scale = 0
    system.TDS.config.reset_tiny = 0
    system.TDS.config.criteria = 0
    system.TDS.config.no_tqdm = 1
    system.TDS.config.save_every = 1


def disable_andes_case_events(system: Any, simulation_time: float) -> list[str]:
    """Disable case-file switching devices absent from the VeraGrid scenario.

    :param system: Loaded ANDES system before setup.
    :param simulation_time: Benchmark horizon in seconds.
    :return: Labels and counts for disabled event model types.
    """
    disabled_models: list[str] = list()
    event_model_names: tuple[str, ...] = ("Toggle", "Alter", "Fault")
    event_model_name: str
    for event_model_name in event_model_names:
        event_model: Any | None = system.models.get(event_model_name, None)
        if event_model is not None and int(event_model.n) > 0:
            event_index: int
            for event_index in range(int(event_model.n)):
                event_model.u.v[event_index] = 0.0
                # ANDES still registers switch times for inactive event rows.
                # Moving their timers beyond the benchmark horizon preserves
                # the exact uniform grid required for a solver comparison.
                if event_model_name in ("Toggle", "Alter"):
                    event_model.t.v[event_index] = simulation_time + 10.0
                elif event_model_name == "Fault":
                    event_model.tf.v[event_index] = simulation_time + 10.0
                    event_model.tc.v[event_index] = simulation_time + 11.0
                else:
                    pass
            disabled_models.append(f"{event_model_name}:{int(event_model.n)}")
        else:
            pass
    return disabled_models


def select_andes_initial_outputs(system: Any) -> tuple[np.ndarray, np.ndarray]:
    """Select initial variables using the same ANDES Output mask as TDS storage.

    :param system: Initialized ANDES system.
    :return: Initial state and algebraic output rows.
    """
    if int(system.Output.n) > 0:
        initial_states: np.ndarray = np.asarray(system.dae.x[system.Output.xidx], dtype=float)
        initial_algebraics: np.ndarray = np.asarray(system.dae.y[system.Output.yidx], dtype=float)
    else:
        initial_states = np.asarray(system.dae.x, dtype=float).copy()
        initial_algebraics = np.asarray(system.dae.y, dtype=float).copy()
    return initial_states, initial_algebraics


def select_uniform_andes_outputs(
    time_values: np.ndarray,
    state_values: np.ndarray,
    algebraic_values: np.ndarray,
    simulation_time: float,
    time_step: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Select exactly one stored ANDES row for every requested fixed-grid time.

    ANDES can store the final horizon twice when a timed event is present. The
    nonlinear solves still occur on the uniform grid; this function removes the
    duplicate storage row and rejects any missing requested time.

    :param time_values: Raw ANDES stored times including the explicit initial row.
    :param state_values: Raw state trajectories.
    :param algebraic_values: Raw algebraic trajectories.
    :param simulation_time: Final simulation time in seconds.
    :param time_step: Fixed integration step in seconds.
    :return: Uniform times and aligned state/algebraic trajectories.
    """
    step_count: int = int(round(simulation_time / time_step))
    expected_times: np.ndarray = np.arange(step_count + 1, dtype=float) * time_step
    selected_indexes: np.ndarray = np.empty(expected_times.size, dtype=int)
    time_index: int
    for time_index in range(expected_times.size):
        nearest_index: int = int(np.argmin(np.abs(time_values - expected_times[time_index])))
        time_error: float = abs(float(time_values[nearest_index]) - float(expected_times[time_index]))
        if time_error <= 1.0e-10:
            selected_indexes[time_index] = nearest_index
        else:
            raise ValueError(
                f"ANDES did not store requested fixed-grid time {expected_times[time_index]:.12e}."
            )
    return (
        expected_times,
        state_values[selected_indexes, :],
        algebraic_values[selected_indexes, :],
    )


def perturb_first_andes_speed_state(
    system: Any,
    perturbation_pu: float,
    target_label: str,
) -> str:
    """Apply the common initial speed perturbation to the first ANDES machine.

    :param system: Dynamically initialized ANDES system.
    :param perturbation_pu: Additive rotor-speed perturbation in per unit.
    :param target_label: Common physical state label selected for this case.
    :return: Perturbed ANDES state label.
    """
    perturbation_applied: bool = False
    perturbed_label: str = ""
    state_index: int
    for state_index in range(len(system.dae.x_name)):
        state_label: str = str(system.dae.x_name[state_index])
        if not perturbation_applied and state_label == target_label:
            system.dae.x[state_index] = float(system.dae.x[state_index]) + perturbation_pu
            perturbed_label = state_label
            perturbation_applied = True
        else:
            pass
    if perturbation_applied:
        system.vars_to_models()
    else:
        raise ValueError("No ANDES omega state is available for the RMS perturbation.")
    return perturbed_label


def run_andes_rms(
    system_name: str,
    scenario_name: str,
    time_step: float = 0.001,
    simulation_time: float = 1.0,
    integration_tolerance: float = 1.0e-6,
    maximum_iterations: int = 1000,
    speed_perturbation_pu: float = 1.0e-4,
    event_time: float = 0.2,
    event_state_step_pu: float = 1.0e-4,
) -> np.ndarray:
    """Run, time and persist one ANDES RMS time-domain benchmark.

    :param system_name: Benchmark system name.
    :param scenario_name: ``base`` or ``event``.
    :param time_step: Fixed integration step in seconds.
    :param simulation_time: Final simulation time in seconds.
    :param integration_tolerance: Nonlinear integration tolerance.
    :param maximum_iterations: Maximum nonlinear iterations per step.
    :param speed_perturbation_pu: Initial speed perturbation for the base scenario.
    :param event_time: Event application time in seconds.
    :param event_state_step_pu: Event speed-state step in p.u.
    :return: One timing sample aligned with
        :func:`benchmarks.dynamics_andes.RMS.rms_simulation.rms_timing_phase_names`.
    """
    workflow_start: float = time.perf_counter()
    case_path: Path = resolve_andes_case_path(system_name)
    output_directory: Path = engine_results_directory(
        system_name,
        "ANDES",
        scenario_name,
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    # Parsing and object construction are timed independently from system.setup,
    # which creates model addresses and sparse numerical structures in ANDES.
    load_start: float = time.perf_counter()
    system: Any = andes.load(
        str(case_path),
        default_config=True,
        setup=False,
        autogen_stale=False,
    )
    load_seconds: float = time.perf_counter() - load_start
    configure_andes_system(
        system=system,
        system_name=system_name,
        time_step=time_step,
        simulation_time=simulation_time,
        integration_tolerance=integration_tolerance,
        maximum_iterations=maximum_iterations,
    )
    disabled_event_models: list[str] = disable_andes_case_events(
        system=system,
        simulation_time=simulation_time,
    )
    setup_start: float = time.perf_counter()
    setup_success: bool = bool(system.setup())
    setup_seconds: float = time.perf_counter() - setup_start
    if setup_success:
        pass
    else:
        raise RuntimeError(f"ANDES setup failed for {case_path}.")

    # The first solve is the documented cold pass. The second pass is the only
    # power-flow result used to initialize and time the comparable RMS workflow.
    cold_pf_start: float = time.perf_counter()
    cold_pf_success: bool = bool(system.PFlow.run())
    cold_pf_seconds: float = time.perf_counter() - cold_pf_start
    if cold_pf_success:
        pass
    else:
        raise RuntimeError("The cold ANDES power flow did not converge.")
    warm_pf_start: float = time.perf_counter()
    warm_pf_success: bool = bool(system.PFlow.run())
    warm_pf_seconds: float = time.perf_counter() - warm_pf_start
    if warm_pf_success:
        pass
    else:
        raise RuntimeError("The authoritative warm ANDES power flow did not converge.")

    # Explicit TDS.init isolates dynamic model initialization, DAE expansion,
    # sparse-pattern assembly and mass-matrix construction from integration.
    initialization_start: float = time.perf_counter()
    system.TDS.init()
    initialization_seconds: float = time.perf_counter() - initialization_start
    if (
        scenario_name == "base"
        and speed_perturbation_pu != 0.0
    ):
        perturbed_state_label: str = perturb_first_andes_speed_state(
            system=system,
            perturbation_pu=speed_perturbation_pu,
            target_label=perturbation_state_label(system_name),
        )
    else:
        perturbed_state_label = "none"
    initial_states: np.ndarray
    initial_algebraics: np.ndarray
    initial_states, initial_algebraics = select_andes_initial_outputs(system)
    state_labels: list[str] = list(system.dae.x_name_output)
    algebraic_labels: list[str] = list(system.dae.y_name_output)

    # Calling run after explicit initialization uses ANDES resume semantics.
    # Event cases stop exactly at the event time, apply the state discontinuity,
    # and resume on the same fixed grid without using an engine-specific timer.
    integration_start: float = time.perf_counter()
    event_states: np.ndarray | None = None
    event_algebraics: np.ndarray | None = None
    if scenario_name == "base":
        integration_success: bool = bool(system.TDS.run(no_summary=True))
    else:
        system.TDS.config.tf = event_time
        pre_event_success: bool = bool(system.TDS.run(no_summary=True))
        if pre_event_success and bool(system.TDS.converged):
            pass
        else:
            raise RuntimeError("The pre-event ANDES RMS segment did not converge.")
        perturbed_state_label = perturb_first_andes_speed_state(
            system=system,
            perturbation_pu=event_state_step_pu,
            target_label=perturbation_state_label(system_name),
        )
        event_states, event_algebraics = select_andes_initial_outputs(system)
        system.TDS.config.tf = simulation_time
        integration_success = bool(system.TDS.run(no_summary=True))
    integration_seconds: float = time.perf_counter() - integration_start
    stored_time: np.ndarray = np.asarray(system.dae.ts.t, dtype=float)
    stored_states: np.ndarray = np.asarray(system.dae.ts.x, dtype=float)
    stored_algebraics: np.ndarray = np.asarray(system.dae.ts.y, dtype=float)

    # ANDES can attempt a zero-length trailing step when floating-point time
    # accumulation lands infinitesimally below ``tf``. In that case ``run``
    # reports failure even though the requested final sample is already stored.
    # Accept only a complete requested grid; a genuine early termination still
    # raises below and can never enter the benchmark comparison.
    final_time_tolerance: float = max(1.0e-12, time_step * 1.0e-9)
    integration_grid_complete: bool = bool(
        stored_time.size > 0
        and np.isclose(
            stored_time[-1],
            simulation_time,
            rtol=0.0,
            atol=final_time_tolerance,
        )
    )
    raw_integration_converged: bool = bool(integration_success and system.TDS.converged)
    if raw_integration_converged or integration_grid_complete:
        accepted_integration: bool = True
    else:
        raise RuntimeError("The ANDES RMS integration did not produce the complete requested grid.")

    time_values: np.ndarray = np.concatenate((np.zeros(1, dtype=float), stored_time))
    state_values: np.ndarray = np.vstack((initial_states, stored_states))
    algebraic_values: np.ndarray = np.vstack((initial_algebraics, stored_algebraics))
    time_values, state_values, algebraic_values = select_uniform_andes_outputs(
        time_values=time_values,
        state_values=state_values,
        algebraic_values=algebraic_values,
        simulation_time=simulation_time,
        time_step=time_step,
    )
    if event_states is not None and event_algebraics is not None:
        event_index: int = int(round(event_time / time_step))
        state_values[event_index, :] = event_states
        algebraic_values[event_index, :] = event_algebraics
    else:
        pass

    export_start: float = time.perf_counter()
    write_trajectory_csv(
        output_path=output_directory / "state_trajectory.csv",
        time_values=time_values,
        values=state_values,
        labels=state_labels,
    )
    write_trajectory_csv(
        output_path=output_directory / "algebraic_trajectory.csv",
        time_values=time_values,
        values=algebraic_values,
        labels=algebraic_labels,
    )
    export_seconds: float = time.perf_counter() - export_start

    dynamic_problem_preparation_seconds: float = setup_seconds + initialization_seconds
    dynamic_simulation_total_seconds: float = (
        dynamic_problem_preparation_seconds + integration_seconds
    )
    dynamic_results_total_seconds: float = dynamic_simulation_total_seconds + export_seconds
    process_total_seconds: float = time.perf_counter() - workflow_start
    workflow_overhead_seconds: float = max(
        0.0,
        process_total_seconds
        - load_seconds
        - setup_seconds
        - cold_pf_seconds
        - warm_pf_seconds
        - initialization_seconds
        - integration_seconds
        - export_seconds,
    )
    metadata_rows: list[tuple[str, str]] = list()
    metadata_rows.append(("engine", "ANDES"))
    metadata_rows.append(("andes_version", str(andes.__version__)))
    metadata_rows.append(("case", case_label(system_name)))
    metadata_rows.append(("scenario", scenario_name))
    metadata_rows.append(("case_path", str(case_path)))
    metadata_rows.append(("solver", "Backward Euler"))
    metadata_rows.append(("newton_jacobian", "honest: refreshed each iteration"))
    metadata_rows.append(("algebraic_residual_scaling", "disabled"))
    metadata_rows.append(("fixed_step", "True"))
    metadata_rows.append(("adaptive_step_reduction", "False"))
    metadata_rows.append(("time_step_s", f"{time_step:.12e}"))
    metadata_rows.append(("simulation_time_s", f"{simulation_time:.12e}"))
    metadata_rows.append(("integration_tolerance", f"{integration_tolerance:.12e}"))
    metadata_rows.append(("perturbation", scenario_name))
    metadata_rows.append(("perturbed_state", perturbed_state_label))
    metadata_rows.append(("speed_perturbation_pu", f"{speed_perturbation_pu:.12e}"))
    metadata_rows.append(("event_type", scenario_name))
    metadata_rows.append(("event_time_s", f"{event_time:.12e}"))
    metadata_rows.append(("event_state_step_pu", f"{event_state_step_pu:.12e}"))
    metadata_rows.append(("event_target_state", perturbation_state_label(system_name)))
    metadata_rows.append(("sample_count", str(time_values.size)))
    metadata_rows.append(("state_count", str(state_values.shape[1])))
    metadata_rows.append(("algebraic_count", str(algebraic_values.shape[1])))
    metadata_rows.append(("power_flow_source", "second warm solve"))
    metadata_rows.append(("case_file_events", "disabled before applying the selected benchmark scenario"))
    metadata_rows.append(("disabled_event_models", ";".join(disabled_event_models)))
    metadata_rows.append(("well_initialized", str(bool(system.TDS.test_ok))))
    metadata_rows.append(("converged", str(accepted_integration)))
    metadata_rows.append(("andes_raw_run_converged", str(raw_integration_converged)))
    metadata_rows.append(("requested_grid_complete", str(integration_grid_complete)))
    write_key_value_csv(output_directory / "metadata.csv", metadata_rows)
    print(f"ANDES RMS results written to: {output_directory}")
    return np.asarray(
        (
            load_seconds,
            setup_seconds,
            cold_pf_seconds,
            warm_pf_seconds,
            initialization_seconds,
            np.nan,
            dynamic_problem_preparation_seconds,
            integration_seconds,
            export_seconds,
            dynamic_simulation_total_seconds,
            dynamic_results_total_seconds,
            process_total_seconds,
            workflow_overhead_seconds,
            np.nan,
            np.nan,
            np.nan,
        ),
        dtype=float,
    )


if __name__ == "__main__":
    main()
else:
    pass
