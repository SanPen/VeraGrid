# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Independent periodic constraints for smooth autonomous EMT models.

Seed assignments (init_eqs) are deliberately absent from the residual. Each
cycle sample satisfies the original algebraic equations and f(x,z) - D*x = 0.
D is a Fourier differentiation matrix, allowing unbalanced phase waveforms and
rotor-frame harmonics. This is a cycle-based formulation, not instantaneous
consistency or time-domain settling. Currently validated on synchronous-machine
Kundur with torque-tracking governors and fixed PF rotor phase references.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import MatrixRankWarning

from VeraGridEngine.Utils.Sparse.sparse_solve import SparseProviderLinearSolver, solve_sparse_system_once
from VeraGridEngine.Utils.NumericalMethods.external_sparse_solver_interface import SparseLinearSolverBackendProvider
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_solver_registry import resolve_emt_sparse_solver_backend_provider
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.enumerations import EmtInitializationMethod
from VeraGridEngine.Simulations.EMT.initialization_emt import _emt_phase_groups, _emt_is_absolute_angle
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicJacobian, SymbolicVector


@dataclass
class _PeriodicResidualEvaluator:
    """Evaluate the original DAE on a Fourier-collocated cycle."""

    residual_fn: SymbolicVector
    jacobian_fn: SymbolicJacobian
    initial: np.ndarray
    initial_derivatives: np.ndarray
    runtime: np.ndarray
    constants: np.ndarray
    columns: np.ndarray
    angle_rows: np.ndarray
    state_count: int
    omega: float
    scale_matrix: sp.spmatrix
    derivative_matrix: sp.csc_matrix

    def evaluate(self, orbit: np.ndarray, phases: np.ndarray,
                 state_derivatives: np.ndarray,
                 with_jacobian: bool = False) -> tuple[np.ndarray, sp.csc_matrix | None]:
        residual = np.empty_like(orbit)
        jacobians = []
        compiled_values = self.initial.copy()

        for sample, phase in enumerate(phases):
            compiled_values[self.columns] = orbit[sample]
            compiled_values[self.columns[self.angle_rows]] += phase
            residual[sample] = self.residual_fn(
                compiled_values, self.initial_derivatives, self.runtime, self.constants
            )
            if with_jacobian:
                jacobians.append(self.scale_matrix @ self.jacobian_fn(
                    compiled_values, self.initial_derivatives, self.runtime, self.constants, 0.0,
                ).copy())

        residual[:, :self.state_count] -= state_derivatives
        residual[:, self.angle_rows] -= self.omega
        jacobian = (sp.block_diag(jacobians, format="csc") - self.derivative_matrix
                    if with_jacobian else None)
        return residual, jacobian


def _validate_periodic_problem(problem: EmtProblemTemplate, options: EmtOptions,
                               states: list, variables: list, equations: list,
                               omega: float) -> np.ndarray:
    """Check the cycle solver's assumptions and identify absolute angle states."""
    samples = options.init_periodic_samples
    if options.init_fix_pf_bus_voltages:
        raise ValueError("Periodic initialization solves bus waveforms; fixed PF voltages are unsupported")
    if not isinstance(samples, int) or samples < 9 or samples % 2 == 0:
        raise ValueError("Use an odd number of at least nine collocation samples")
    if options.initialization_method == EmtInitializationMethod.PseudoTransient:
        if not (0 < options.init_ptc_dtau_min <= options.init_ptc_dtau0 <= options.init_ptc_dtau_max):
            raise ValueError("Periodic pseudo-transient requires positive, ordered pseudo-time steps")
    if len(equations) != len(variables):
        raise ValueError("Periodic initialization requires a square DAE")

    angle_rows = np.asarray([i for i, var in enumerate(states) if _emt_is_absolute_angle(var)], dtype=int)
    if not len(angle_rows):
        raise ValueError("Periodic initialization requires an absolute phase state")

    forbidden = {var.uid for var in problem.get_diff_vars()} | {problem.glob_time.uid}
    if any(forbidden.intersection(var.uid for var in eq.get_vars()) for eq in equations):
        raise ValueError("Periodic initialization requires autonomous explicit state equations")
    if any(problem.glob_time.uid in {var.uid for var in eq.get_vars()}
           for eq in problem.sys_block.event_dict.values()):
        raise ValueError("Periodic initialization does not support time-dependent runtime parameters")
    if not np.isfinite(omega) or omega <= 0:
        raise ValueError("Periodic initialization requires a positive, finite base frequency")
    return angle_rows


def solve_periodic_initialization(
    problem: EmtProblemTemplate, options: EmtOptions,
) -> dict[str, float | int]:
    """Solve a periodic orbit and apply its t=0 state and derivatives atomically.

    Fourier collocation permits negative/zero sequence and rotor-frame ripple.
    The unknown rotor angles are periodic corrections to omega*t. The Kundur
    torque-tracking governors leave each machine's mean phase free; retain its
    PF initial phase with a bordered Newton system. All physical equations,
    including the bordered rows, must pass before applying any result.

    The collocation solution is also checked halfway between all sample nodes
    to detect unresolved harmonics. Raise on failure and retain the PF seeds.
    """
    sparse_provider: SparseLinearSolverBackendProvider | None = problem.get_sparse_solver_backend_provider(
            options.sparse_solver, options.external_sparse_solver_plugin_name,
            options.external_sparse_solver_directory, options.allow_internal_sparse_fallback)
    if sparse_provider is None:
        sparse_provider = resolve_emt_sparse_solver_backend_provider(
            solver_type=options.sparse_solver,
            external_plugin_name=options.external_sparse_solver_plugin_name,
            external_plugin_directory=options.external_sparse_solver_directory,
            allow_internal_fallback=options.allow_internal_sparse_fallback,
            logger=None,
        )
        problem.set_sparse_solver_backend_provider(
            sparse_provider, options.sparse_solver, options.external_sparse_solver_plugin_name,
            options.external_sparse_solver_directory, options.allow_internal_sparse_fallback)
    # The bordered collocation system owns factors independently of time simulation.
    linear_solver: SparseProviderLinearSolver = SparseProviderLinearSolver(sparse_provider)
    samples = options.init_periodic_samples
    tolerance = options.init_newton_tol
    use_ptc = options.initialization_method == EmtInitializationMethod.PseudoTransient
    max_iterations = options.init_ptc_max_iter if use_ptc else options.init_newton_max_iter
    dtau = options.init_ptc_dtau0
    states = problem.get_state_vars()
    variables = states + problem.get_algebraic_vars()
    equations = problem.get_state_eqs() + problem.get_algebraic_eqs()
    state_count, variable_count = len(states), len(variables)
    omega = 2.0 * np.pi * problem.grid.fBase
    angle_rows = _validate_periodic_problem(problem, options, states, variables, equations, omega)

    columns = np.asarray([problem.get_var_idx(var) for var in variables])
    positions = {var.uid: i for i, var in enumerate(variables)}
    initial = problem.get_x0().copy()
    initial_derivatives = problem.get_dx0().copy()
    runtime = problem.event_params_values.copy()
    constants = np.asarray([value.value for value in problem.get_parameters_values()], dtype=float)
    phases = 2.0 * np.pi * np.arange(samples) / samples
    modes = np.fft.fftfreq(samples, 1.0 / samples)
    differentiation = np.fft.ifft(
        (1j * omega * modes)[:, None] * np.fft.fft(np.eye(samples), axis=0), axis=0,
    ).real
    orbit = np.tile(initial[columns], (samples, 1))
    # This balanced rotation is only the Newton starting guess. The solve is
    # unrestricted across phases and determines the unbalanced waveforms.
    devices = (list(problem.grid.buses) + list(problem.grid.lines)
               + list(problem.grid.transformers2w) + list(problem.grid.loads)
               + list(problem.grid.generators))
    for device in devices:
        for block in device.emt_model.get_all_blocks():
            for a, b, c in _emt_phase_groups(block.state_vars + block.algebraic_vars):
                if a.name[0].islower() and all(var.uid in positions for var in (a, b, c)):
                    for var, plus, minus in ((a, c, b), (b, a, c), (c, b, a)):
                        orbit[:, positions[var.uid]] = (
                            initial[problem.get_var_idx(var)] * np.cos(phases)
                            + (initial[problem.get_var_idx(plus)] - initial[problem.get_var_idx(minus)])
                            / np.sqrt(3.0) * np.sin(phases)
                        )

    compiler_options = dict(
        compiler_names_dict=problem.get_compiler_names_dict().copy(),
        alias_names_dict=problem.get_alias_names_dict().copy(),
        VARS_NAME=problem.VARS_NAME, DIFF_NAME=problem.DIFF_NAME,
        EVENT_PARAMS_NAME=problem.VARIABLE_PARAMS_NAME, PARAMS_NAME=problem.CONSTANT_PARAMS_NAME,
        use_jit=False,
    )
    residual_fn = SymbolicVector(eqs=equations, **compiler_options)
    jacobian_fn = SymbolicJacobian(eqs=equations, variables=variables, static=True, **compiler_options)
    # Electrical state derivatives have units per second; scale their rows to
    # the same order as the algebraic equations for the linear solve only.
    row_scale = np.r_[np.full(state_count, 1.0 / omega), np.ones(variable_count - state_count)]
    scale_matrix = sp.diags(row_scale)
    mass = sp.diags(np.r_[np.full(state_count, 1.0 / omega), np.zeros(variable_count - state_count)])
    derivative_matrix = sp.kron(sp.csc_matrix(differentiation), mass, format="csc")
    pseudo_mass = sp.kron(sp.eye(samples), mass, format="csc")
    phase_constraints = sp.csc_matrix(
        (np.ones(len(angle_rows)), (np.arange(len(angle_rows)), angle_rows)),
        shape=(len(angle_rows), samples * variable_count),
    )
    initial_angles = orbit[0, angle_rows].copy()
    evaluator = _PeriodicResidualEvaluator(
        residual_fn=residual_fn, jacobian_fn=jacobian_fn,
        initial=initial, initial_derivatives=initial_derivatives,
        runtime=runtime, constants=constants, columns=columns,
        angle_rows=angle_rows, state_count=state_count, omega=omega,
        scale_matrix=scale_matrix, derivative_matrix=derivative_matrix,
    )

    initial_residual = None
    for iteration in range(max_iterations + 1):
        residual, jacobian = evaluator.evaluate(
            orbit, phases, differentiation @ orbit[:, :state_count], True
        )
        residual_norm = float(np.max(np.abs(residual)))
        if initial_residual is None:
            initial_residual = residual_norm
        if np.isfinite(residual_norm) and residual_norm <= tolerance:
            break
        if not np.isfinite(residual_norm) or iteration == max_iterations:
            raise RuntimeError(f"Periodic initialization failed: residual {residual_norm:.3e}")
        if use_ptc:
            jacobian = jacobian - pseudo_mass / dtau
        bordered = sp.bmat([[jacobian, phase_constraints.T], [phase_constraints, None]], format="csc")
        with warnings.catch_warnings():
            warnings.simplefilter("error", MatrixRankWarning)
            step: np.ndarray = solve_sparse_system_once(bordered, np.r_[
                -(residual * row_scale).ravel(), initial_angles - orbit[0, angle_rows],
            ], sparse_provider, linear_solver)[:samples * variable_count].reshape(samples, variable_count)
        old_norm = np.max(np.abs(residual * row_scale))
        for factor in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125):
            trial = orbit + factor * step
            trial_residual, _ = evaluator.evaluate(
                trial, phases, differentiation @ trial[:, :state_count]
            )
            if np.max(np.abs(trial_residual * row_scale)) < old_norm:
                orbit = trial
                if use_ptc:
                    dtau = min(options.init_ptc_dtau_max, dtau * 2.0)
                break
        else:
            if use_ptc and dtau > options.init_ptc_dtau_min:
                dtau = max(options.init_ptc_dtau_min, dtau * 0.25)
            else:
                raise RuntimeError(
                    f"Periodic initialization step failed at iteration {iteration}: residual {residual_norm:.3e}"
                )

    coefficients = np.fft.fft(orbit, axis=0) / samples
    midpoint_phases = phases + np.pi / samples
    basis = np.exp(1j * midpoint_phases[:, None] * modes)
    midpoint_orbit = (basis @ coefficients).real
    midpoint_derivatives = (basis @ ((1j * omega * modes)[:, None] * coefficients[:, :state_count])).real
    midpoint_residual, _ = evaluator.evaluate(
        midpoint_orbit, midpoint_phases, midpoint_derivatives
    )
    midpoint_norm = float(np.max(np.abs(midpoint_residual)))
    if not np.isfinite(midpoint_norm) or midpoint_norm > tolerance:
        raise RuntimeError(
            f"Periodic residual between samples is {midpoint_norm:.3e}; increase samples"
        )

    corrected_initial = initial.copy()
    corrected_initial[columns] = orbit[0]
    derivatives = differentiation @ orbit[:, :state_count]
    derivatives[:, angle_rows] += omega
    corrected_derivatives = initial_derivatives.copy()
    for differential in problem.get_diff_vars():
        if differential.base_var is not None and differential.base_var.uid in positions:
            corrected_derivatives[problem.get_diff_var_idx(differential)] = derivatives[
                0, positions[differential.base_var.uid]
            ]
    problem.set_x0(corrected_initial)
    problem.set_dx0(corrected_derivatives)
    return {
        "iterations": iteration,
        "samples": samples,
        "unknowns": samples * variable_count,
        "initial_residual": initial_residual,
        "final_residual": max(residual_norm, midpoint_norm),
    }
