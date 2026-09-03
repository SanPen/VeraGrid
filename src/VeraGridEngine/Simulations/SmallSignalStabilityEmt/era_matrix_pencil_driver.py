# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import scipy.linalg as la
from numpy.lib.stride_tricks import sliding_window_view

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_core import (
    build_empty_complex_matrix,
    build_empty_complex_vector,
    build_empty_float_vector,
    extract_matrix_pencil_results_from_data,
    resolve_nominal_frequency_hz,
)
from VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_options import EraMatrixPencilOptions
from VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_results import EraMatrixPencilResults
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.basic_structures import CxVec, Mat, Vec
from VeraGridEngine.enumerations import SimulationTypes


def select_dominant_observable(y_data: np.ndarray) -> np.ndarray:
    """
    Legacy helper that selects one dominant observable by variance.

    The new engine is fully MIMO and no longer depends on this reduction, but
    the function is preserved for backward compatibility with existing callers.

    :param y_data: Real observation matrix with shape ``(n_samples, n_states)``.
    :return: One-dimensional dominant observable.
    """
    variances: np.ndarray = np.var(y_data, axis=0)
    best_index: int = int(np.argmax(variances))
    dominant_signal: np.ndarray = np.asarray(y_data[:, best_index], dtype=np.float64)
    return dominant_signal


def build_hankel_zero_copy(y_signal: np.ndarray, window_length: int) -> np.ndarray:
    """
    Legacy helper that builds a scalar Hankel view.

    The new solver uses a MIMO block-Hankel matrix, but the helper is preserved
    so older diagnostic scripts can still inspect the scalar construction.

    :param y_signal: Scalar observation signal.
    :param window_length: Hankel window length.
    :return: Sliding-window Hankel view.
    """
    hankel_view: np.ndarray = sliding_window_view(y_signal, window_shape=window_length)
    return hankel_view


def build_empty_era_results(observable_names: List[str] | None = None) -> EraMatrixPencilResults:
    """
    Build an empty public results object.

    :param observable_names: Optional observable labels.
    :return: Empty results object.
    """
    names_list: List[str]

    if observable_names is not None:
        names_list = list(observable_names)
    else:
        names_list = list()

    return EraMatrixPencilResults(
        eigenvalues_s=build_empty_complex_vector(),
        residues=build_empty_complex_matrix(),
        modal_energy=build_empty_float_vector(),
        reconstruction_errors=build_empty_float_vector(),
        band_low_hz=build_empty_float_vector(),
        band_high_hz=build_empty_float_vector(),
        selected_orders=np.zeros(0, dtype=np.int_),
        observable_count_per_mode=np.zeros(0, dtype=np.int_),
        observable_names=names_list,
    )


def extract_observable_names(problem: EmtProblemTemplate) -> List[str]:
    """
    Extract the ordered state-variable labels from the EMT problem.

    :param problem: EMT problem definition.
    :return: Ordered list of state labels.
    """
    names_list: List[str] = list()

    if isinstance(problem, EmtProblemTemplate):
        state_vars = problem.get_state_vars()
        state_index: int = 0
        n_states: int = len(state_vars)

        while state_index < n_states:
            names_list.append(str(state_vars[state_index]))
            state_index += 1
    else:
        names_list = list()

    return names_list


def simulate_emt_state_history(solver: StructuralVectorizedSolver,
                               n_states: int) -> Tuple[Vec, Mat]:
    """
    Run the EMT solver and slice the differential-state block.

    :param solver: EMT structural solver.
    :param n_states: Number of differential states.
    :return: Tuple ``(time_vector, state_history)``.
    """
    time_vector: Vec
    full_state_history: Mat
    derivative_history: Mat
    time_vector, full_state_history, derivative_history = solver.simulate()
    del derivative_history

    if n_states > 0:
        dense_state_history: Mat = np.asarray(full_state_history[:, :n_states], dtype=np.float64)
    else:
        dense_state_history = np.zeros((full_state_history.shape[0], 0), dtype=np.float64)

    return np.asarray(time_vector, dtype=np.float64), dense_state_history


def unpack_dense_state_matrix(y_full_tuples: list,
                              n_states: int) -> Mat:
    """
    Convert the solver output into one dense real matrix.

    :param y_full_tuples: Raw solver state history.
    :param n_states: Number of differential states.
    :return: Dense state matrix.
    """
    n_samples: int = len(y_full_tuples)
    dense_signal: Mat = np.zeros((n_samples, n_states), dtype=np.float64)
    sample_index: int = 0

    # The conversion is explicit because the solver may return either a raw
    # vector or a tuple ``(state_vector, extra_data)`` depending on the mode.
    while sample_index < n_samples:
        current_sample = y_full_tuples[sample_index]

        if isinstance(current_sample, tuple):
            dense_signal[sample_index, :] = np.asarray(current_sample[0], dtype=np.float64)
        else:
            dense_signal[sample_index, :] = np.asarray(current_sample, dtype=np.float64)

        sample_index += 1

    return dense_signal


def extract_matrix_pencil_poles(y_signal: np.ndarray,
                                dt: float,
                                max_modes: int,
                                tol_deflation: float) -> CxVec:
    """
    Compatibility wrapper around the new EMT matrix-pencil engine.

    The wrapper keeps the legacy scalar API alive while internally using the
    refactored MIMO/TLS extraction path on a single observable channel.

    :param y_signal: Scalar observation signal.
    :param dt: Sampling time step.
    :param max_modes: Maximum number of retained modes.
    :param tol_deflation: Numerical singular-value floor.
    :return: Continuous-time pole vector.
    """
    n_samples: int = int(y_signal.shape[0])

    if n_samples >= 4 and dt > 0.0:
        time_data: Vec = dt * np.arange(n_samples, dtype=np.float64)
        legacy_options: EraMatrixPencilOptions = EraMatrixPencilOptions(
            decimation_factor=1,
            tol_deflation=tol_deflation,
            max_modes=max_modes,
            use_notch_filtering=False,
            use_forward_backward=True,
            maximum_observables=1,
        )
        nyquist_hz: float = 0.5 / dt
        legacy_options.set_analysis_bands(((0.0, 0.95 * nyquist_hz),))
        legacy_results: EraMatrixPencilResults = extract_matrix_pencil_results_from_data(
            time_data=time_data,
            y_data=np.asarray(y_signal.reshape(-1, 1), dtype=np.float64),
            era_options=legacy_options,
            nominal_frequency_hz=0.0,
            observable_names=list(['Legacy Observable']),
        )
        s_poles: CxVec = legacy_results.get_eigenvalues()
    else:
        s_poles = build_empty_complex_vector()

    return s_poles


class EraMatrixPencilDriver(DriverTemplate):
    """
    EMT driver for the frequency-zooming forward-backward TLS matrix pencil.

    The driver is intentionally thin: it only runs the EMT simulation and then
    delegates the modal extraction to the pure stateless core module.
    """

    __slots__ = (
        '_grid',
        '_problem',
        '_emt_options',
        '_era_options',
        '_results',
    )

    name = 'ERA Matrix Pencil EMT Simulation'
    tpe = SimulationTypes.RmsSmallSignal_run

    def __init__(self,
                 grid: MultiCircuit,
                 problem: EmtProblemTemplate,
                 emt_options: EmtOptions,
                 era_options: EraMatrixPencilOptions) -> None:
        """
        Initialize the EMT ERA driver.

        :param grid: Multi-circuit grid model.
        :param problem: EMT problem definition.
        :param emt_options: EMT simulation options.
        :param era_options: Matrix-pencil extraction options.
        :return: None.
        """
        DriverTemplate.__init__(self, grid=grid)
        self._grid: MultiCircuit = grid
        self._problem: EmtProblemTemplate = problem
        self._emt_options: EmtOptions = emt_options
        self._era_options: EraMatrixPencilOptions = era_options
        self._results: EraMatrixPencilResults | None = None

    def get_results(self) -> EraMatrixPencilResults | None:
        """
        Return the latest extraction results.

        :return: Results object or ``None``.
        """
        return self._results

    def run(self) -> None:
        """
        Execute the EMT ringdown simulation and the modal extraction pipeline.

        :return: None.
        """
        self.tic()
        self.report_text("Compiling and configuring...")

        time_step: float = float(self._emt_options.time_step)
        ringdown_time: float = float(self._era_options.get_t_ringdown())
        observable_names: List[str] = extract_observable_names(self._problem)

        if self._era_options.get_verbose() > 0:
            print('-> Executing EMT transient for frequency-zooming ERA analysis...')
        else:
            pass

        try:
            solver: StructuralVectorizedSolver = StructuralVectorizedSolver(
                problem=self._problem,
                t0=0.0,
                t_end=ringdown_time,
                h=time_step,
                method=self._emt_options.integration_method,
                verbose=self._era_options.get_verbose() > 0,
            )
            time_vector: Vec
            dense_signal: Mat
            time_vector, dense_signal = simulate_emt_state_history(
                solver=solver,
                n_states=self._problem.get_states_number(),
            )
            nominal_frequency_hz: float = resolve_nominal_frequency_hz(
                explicit_nominal_frequency_hz=self._era_options.get_nominal_frequency_hz(),
                fallback_nominal_frequency_hz=float(self._grid.fBase),
            )

            if self._era_options.get_verbose() > 0:
                print('-> Executing multi-band forward-backward TLS matrix pencil...')
            else:
                pass

            extracted_results: EraMatrixPencilResults = extract_matrix_pencil_results_from_data(
                time_data=np.asarray(time_vector, dtype=np.float64),
                y_data=dense_signal,
                era_options=self._era_options,
                nominal_frequency_hz=nominal_frequency_hz,
                observable_names=observable_names,
            )
            self._results = extracted_results
            self.results = extracted_results
        except (AttributeError, TypeError, ValueError, RuntimeError, NotImplementedError, la.LinAlgError):
            empty_results: EraMatrixPencilResults = build_empty_era_results(observable_names=observable_names)
            self._results = empty_results
            self.results = empty_results

        self.toc()
