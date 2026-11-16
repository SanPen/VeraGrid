#!/usr/bin/env python3
"""Compare nonlinear WSCC EMT Floquet modes with the STAMP RMS reference.

Periodic shooting is adapted from STAMP_Public's
``scripts/solve_veragrid_stamp_wscc_emt_periodic.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import numpy as np
from scipy import linalg
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "src" / "tests" / "data" / "stamp_wscc"
RIGHTMOST_MODES = 10

from VeraGridEngine.IO.file_open import FileOpen


def _wrap_periodic_angle_defects(problem, defect):
    result = defect.copy()
    for index, variable in enumerate(problem.get_state_vars()):
        if "theta_grid" in variable.name or "theta_abs" in variable.name:
            result[index] = (result[index] + np.pi) % (2.0*np.pi) - np.pi
    return result


def _simulate_cycle(problem, options, period):
    from VeraGridEngine.Simulations.EMT.emt_solver_factory import build_emt_solver

    solver = build_emt_solver(options=options, problem=problem, t0=0.0,
                              t_end=period, h=options.time_step,
                              method=options.integration_method)
    time, values, derivatives, initialized, converged = solver.simulate(
        boundary_updater=problem)
    if not initialized or not converged:
        raise RuntimeError("Periodic shooting cycle did not converge")
    return solver, time, values, derivatives


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=0)
    parser.add_argument("--initial-state", type=Path, default=DATA / "emt_periodic_x0.csv",
                        help="Periodic state CSV; defaults to the committed nonlinear orbit")
    parser.add_argument("--output", type=Path, help="Optional CSV for computed Floquet modes")
    parser.add_argument("--save-periodic-state", type=Path, help="Optional CSV for corrected orbit state")
    parser.add_argument("--time-step", type=float, default=20e-6)
    args = parser.parse_args()

    from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
    from VeraGridEngine.Simulations.EMT.initialization_emt import _compute_missing_dx0
    from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
    from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
    from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
    from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_driver_3ph import PowerFlowDriver3Ph
    from VeraGridEngine.Simulations.SmallSignalStabilityEmt.emt_floquet_operator import BlockEmtFloquetOperator
    from VeraGridEngine.enumerations import (DynamicIntegrationMethod,
                                             EmtInitializationMethod,
                                             EmtSolverTypes)

    grid = FileOpen(file_name=str(DATA / "wscc_emt.veragrid")).open()
    pf_options = PowerFlowOptions(retry_with_other_methods=True)
    pf = PowerFlowDriver(grid, pf_options); pf.run()
    pf3 = PowerFlowDriver3Ph(grid, pf_options); pf3.run()
    if not pf.results.converged or not pf3.results.converged:
        raise RuntimeError("EMT initialization power flow did not converge")
    options = EmtOptions(
        time_step=args.time_step, simulation_time=1.0/grid.fBase,
        tolerance=1e-9, solver_type=EmtSolverTypes.StructuralAD,
        integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
        initialization_method=EmtInitializationMethod.Explicit, verbose=0)
    problem = EmtProblemDae(grid=grid, options=options, pf_results=pf.results,
                            pf_results_3ph=pf3.results)
    period = 1.0/grid.fBase
    nstate = problem.get_states_number()
    static_params = np.asarray(
        [float(parameter.value) for parameter in problem.get_parameters_values()])

    if args.initial_state is not None:
        loaded_x0 = np.loadtxt(args.initial_state, delimiter=",")
        all_variables = problem.get_state_vars() + problem.get_algebraic_vars()
        if loaded_x0.shape != (len(all_variables),):
            raise ValueError(f"Initial-state shape {loaded_x0.shape} does not match "
                             f"the EMT variable count {(len(all_variables),)}")
        for variable, value in zip(all_variables, loaded_x0):
            problem.init_guess[variable.uid] = float(value)
        _compute_missing_dx0(
            problem=problem, report=problem.initialization_report,
            x_full=problem.get_x0(), dx_full=problem.get_dx0(),
            runtime_params=problem.event_params_values.copy(),
            constant_params=static_params, include_existing=True)

    for iteration in range(args.iterations):
        solver, time, values, derivatives = _simulate_cycle(problem, options, period)
        defect = _wrap_periodic_angle_defects(
            problem, values[-1, :nstate]-values[0, :nstate])
        print(f"shooting iteration {iteration}: defect_inf={np.max(np.abs(defect)):.12e}")

        jacobian = problem.get_floquet_jacobian_evaluator(solver.vec_jacobian)
        operator = BlockEmtFloquetOperator(
            problem=problem, trajectory=values, h=args.time_step,
            n_states=nstate, method=options.integration_method,
            jac_evaluator=jacobian, static_params=static_params,
            n_event_params=problem.get_variable_parameter_number(),
            t_trajectory=time)
        monodromy = operator.matmat(np.eye(nstate))
        correction, _, _, _ = linalg.lstsq(
            monodromy-np.eye(nstate), -defect, cond=1.0e-10,
            lapack_driver="gelsd")
        print(f"  correction_inf={np.max(np.abs(correction)):.12e}")

        corrected_states = values[0, :nstate] + correction
        for variable, value in zip(problem.get_state_vars(), corrected_states):
            problem.init_guess[variable.uid] = float(value)
        _compute_missing_dx0(
            problem=problem, report=problem.initialization_report,
            x_full=problem.get_x0(), dx_full=problem.get_dx0(),
            runtime_params=problem.event_params_values.copy(),
            constant_params=static_params, include_existing=True)

    final_solver, final_time, values, _ = _simulate_cycle(problem, options, period)
    # Shooting corrects differential states. Close the full DAE orbit by
    # replaying the period-end algebraic solution at t=0; otherwise the first
    # implicit step visibly moves bus voltages from the stale PF algebraics to
    # the corrected periodic manifold.
    for variable, value in zip(problem.get_algebraic_vars(), values[-1, nstate:]):
        problem.init_guess[variable.uid] = float(value)
    _compute_missing_dx0(
        problem=problem, report=problem.initialization_report,
        x_full=problem.get_x0(), dx_full=problem.get_dx0(),
        runtime_params=problem.event_params_values.copy(),
        constant_params=static_params, include_existing=True)
    final_solver, final_time, values, _ = _simulate_cycle(problem, options, period)
    final_defect = _wrap_periodic_angle_defects(
        problem, values[-1, :nstate]-values[0, :nstate])
    print(f"final periodic defect_inf={np.max(np.abs(final_defect)):.12e}")
    if args.save_periodic_state:
        args.save_periodic_state.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(args.save_periodic_state, problem.get_x0(), delimiter=",")

    # An abc waveform is periodic rather than constant, but its synchronous-dq
    # representation must not jump at the first accepted endpoint.
    theta_var = next(variable for variable in grid.generators[0].emt_model.state_vars
                     if "theta_grid" in variable.name)
    theta = values[:2, problem.get_var_idx(theta_var)]
    shift = 2.0*np.pi/3.0
    for bus in grid.buses:
        indices = [problem.get_var_idx(variable)
                   for variable in bus.emt_model.out_vars[:3]]
        va, vb, vc = (values[:2, index] for index in indices)
        vq = (2.0/3.0)*(np.sin(theta)*va
                         + np.sin(theta-shift)*vb
                         + np.sin(theta+shift)*vc)
        vd = -(2.0/3.0)*(np.cos(theta)*va
                          + np.cos(theta-shift)*vb
                          + np.cos(theta+shift)*vc)
        print(f"corrected first-step dq {bus.name}: "
              f"delta_vq={vq[1]-vq[0]:+.12e}, "
              f"delta_vd={vd[1]-vd[0]:+.12e}")

    jacobian = problem.get_floquet_jacobian_evaluator(final_solver.vec_jacobian)
    operator = BlockEmtFloquetOperator(
        problem=problem, trajectory=values, h=args.time_step,
        n_states=nstate, method=options.integration_method,
        jac_evaluator=jacobian, static_params=static_params,
        n_event_params=problem.get_variable_parameter_number(),
        t_trajectory=final_time)
    multipliers = linalg.eigvals(operator.matmat(np.eye(nstate)))
    exponents = np.log(multipliers.astype(complex)) / period
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(args.output, np.c_[exponents.real, exponents.imag],
                   delimiter=",", header="real,imag", comments="")

    reference = np.loadtxt(DATA / "stamp_rms_eigenvalues.csv", delimiter=",",
                           skiprows=1, usecols=(1, 2))
    stamp = reference[:, 0] + 1j * reference[:, 1]
    omega = 2 * np.pi * grid.fBase
    stamp = stamp.real + 1j * ((stamp.imag + omega / 2) % omega - omega / 2)
    selected = stamp[np.argsort(stamp.real)[::-1][:RIGHTMOST_MODES]]
    rows, columns = linear_sum_assignment(np.abs(selected[:, None] - exponents[None, :]))
    distances = np.abs(selected[rows] - exponents[columns])
    print(f"STAMP reference modes: {len(stamp)}; VeraGrid EMT modes: {len(exponents)}")
    print(f"Compared rightmost STAMP modes: {RIGHTMOST_MODES}")
    print(f"Median modal distance: {np.median(distances):.6g} s^-1")
    print(f"Maximum modal distance: {np.max(distances):.6g} s^-1")
    for reference_index, emt_index, distance in zip(rows, columns, distances):
        print(f"  STAMP {selected[reference_index]:+.6f} -> "
              f"EMT {exponents[emt_index]:+.6f}; distance={distance:.6g} s^-1")


if __name__ == "__main__":
    main()
